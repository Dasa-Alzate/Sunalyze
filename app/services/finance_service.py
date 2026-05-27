"""Orquestación del módulo financiero: CRUD de escenarios + cálculo por proyecto.

Capa de dominio (sin HTTP) que envuelve el motor puro `app.services.finance` y
resuelve, a partir del proyecto, la producción anual y el ratio de autoconsumo
cuando no se pasan explícitamente. Todo va scoped por `org_id` (sin IDOR).
"""

from app.extensions import db
from app.models.project import Project
from app.models.financial_scenario import FinancialScenario
from app.errors import NotFound, ValidationError
from app.services.finance import compute
from app.services.finance.engine import _gross_capex
from app.services.subsidies import SubsidyService


class FinanceService:

    @staticmethod
    def _project_or_404(org_id, project_id):
        project = Project.query.get(project_id)
        if not project or project.org_id != org_id:
            raise NotFound('Proyecto no encontrado.')
        return project

    @staticmethod
    def resolve_production(project, production_kwh_year=None):
        if production_kwh_year is not None:
            return float(production_kwh_year)
        resultados = project.resultados or {}
        annual = resultados.get('annual_production')
        if annual is None:
            raise ValidationError(
                'No hay producción anual: ejecuta el análisis del proyecto o '
                'indica production_kwh_year.'
            )
        return float(annual)

    @staticmethod
    def resolve_self_consumption_ratio(project, self_consumption_ratio=None):
        if self_consumption_ratio is not None:
            return float(self_consumption_ratio)
        resultados = project.resultados or {}
        battery = resultados.get('battery') or {}
        if battery.get('estimated_self_consumption_pct') is not None:
            return float(battery['estimated_self_consumption_pct']) / 100.0
        if project.autoconsumo is not None:
            return float(project.autoconsumo) / 100.0
        return None

    @staticmethod
    def resolve_subsidies(project, assumptions, ccaa=None, municipio=None):
        capex_with_vat = _gross_capex(assumptions) * (1.0 + float(assumptions.iva_pct))
        return SubsidyService.applicable(
            project=project,
            capex=capex_with_vat,
            system_kwp=getattr(project, 'kwp', None),
            ccaa=ccaa,
            municipio=municipio,
        )

    @classmethod
    def compute_for_project(cls, org_id, project_id, assumptions,
                            production_kwh_year=None, self_consumption_ratio=None,
                            apply_subsidies=False, ccaa=None, municipio=None):
        project = cls._project_or_404(org_id, project_id)
        production = cls.resolve_production(project, production_kwh_year)
        ratio = cls.resolve_self_consumption_ratio(project, self_consumption_ratio)
        incentives = [i.model_dump() for i in assumptions.incentives]
        if apply_subsidies:
            incentives = incentives + cls.resolve_subsidies(
                project, assumptions, ccaa=ccaa, municipio=municipio)
        return compute(
            assumptions,
            production,
            self_consumption_ratio=ratio,
            incentives=incentives,
        )

    @classmethod
    def list_scenarios(cls, org_id, project_id):
        cls._project_or_404(org_id, project_id)
        scenarios = (FinancialScenario.query
                     .filter_by(org_id=org_id, project_id=project_id)
                     .order_by(FinancialScenario.is_default.desc(),
                               FinancialScenario.created_at.desc())
                     .all())
        return [s.to_dict() for s in scenarios]

    @classmethod
    def get_scenario(cls, org_id, project_id, scenario_id):
        scenario = FinancialScenario.query.get(scenario_id)
        if (not scenario or scenario.org_id != org_id
                or scenario.project_id != project_id):
            raise NotFound('Escenario no encontrado.')
        return scenario

    @classmethod
    def _unset_other_defaults(cls, org_id, project_id, keep_id=None):
        others = FinancialScenario.query.filter_by(
            org_id=org_id, project_id=project_id, is_default=True).all()
        for other in others:
            if keep_id is None or other.id != keep_id:
                other.is_default = False

    @classmethod
    def create_scenario(cls, org_id, project_id, data, created_by=None):
        cls._project_or_404(org_id, project_id)
        results = cls.compute_for_project(
            org_id, project_id, data.assumptions,
            production_kwh_year=data.production_kwh_year,
            self_consumption_ratio=data.self_consumption_ratio,
            apply_subsidies=data.apply_subsidies,
            ccaa=data.ccaa, municipio=data.municipio,
        )
        scenario = FinancialScenario(
            org_id=org_id, project_id=project_id, name=data.name,
            is_default=data.is_default, created_by=created_by,
        )
        scenario.assumptions = data.assumptions.model_dump()
        scenario.results = results
        if data.is_default:
            cls._unset_other_defaults(org_id, project_id)
        db.session.add(scenario)
        db.session.commit()
        return scenario

    @classmethod
    def update_scenario(cls, org_id, project_id, scenario_id, data):
        scenario = cls.get_scenario(org_id, project_id, scenario_id)
        if data.name is not None:
            scenario.name = data.name
        if data.assumptions is not None:
            results = cls.compute_for_project(
                org_id, project_id, data.assumptions,
                production_kwh_year=data.production_kwh_year,
                self_consumption_ratio=data.self_consumption_ratio,
                apply_subsidies=data.apply_subsidies,
                ccaa=data.ccaa, municipio=data.municipio,
            )
            scenario.assumptions = data.assumptions.model_dump()
            scenario.results = results
        if data.is_default is not None:
            scenario.is_default = data.is_default
            if data.is_default:
                cls._unset_other_defaults(org_id, project_id, keep_id=scenario.id)
        db.session.commit()
        return scenario

    @classmethod
    def delete_scenario(cls, org_id, project_id, scenario_id):
        scenario = cls.get_scenario(org_id, project_id, scenario_id)
        db.session.delete(scenario)
        db.session.commit()
