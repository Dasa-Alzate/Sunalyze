"""Seeder del dataset de demo local (`flask seed demo`).

Construye un entorno realista para desarrollo: cuenta superadmin, catálogos
de equipos, plantillas oficiales, flags activados para la org, y tres
proyectos en distintos puntos del flujo (borrador, en_revision y aprobado
con instalación de posventa, lecturas, mantenimiento y escenario financiero).
Idempotente: si la org ya tiene proyectos, no duplica el dataset.
"""

import hashlib
from datetime import date, timedelta

from app.extensions import db
from app.models.user import User
from app.models.membership import Membership
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.battery import Battery
from app.models.project import Project

DEMO_EMAIL = 'sunalize_test@sunalize.com'
DEMO_PASSWORD = 'test123'
DEMO_PREFIX = 'DEMO'

_DEMO_FLAGS = ('finance', 'posventa', 'templates', 'advanced_analysis')

_MONTHLY_IRRADIANCE = [98.0, 112.0, 156.0, 178.0, 205.0, 224.0,
                       236.0, 214.0, 172.0, 138.0, 104.0, 92.0]
_MONTHLY_PRODUCTION = [412.0, 468.0, 652.0, 745.0, 858.0, 937.0,
                       988.0, 896.0, 720.0, 578.0, 435.0, 385.0]
_ANNUAL_PRODUCTION = sum(_MONTHLY_PRODUCTION)

_READING_FACTORS = [0.94, 1.03, 0.98, 1.06, 0.97, 1.01]


class DemoSeeder:

    @classmethod
    def seed(cls):
        from app.utils.data_loader import load_initial_data, ensure_marketplace
        from app.services.document_bank import DocumentBankSeeder
        from app.services.flag_service import FlagService

        from app.models.catalog import Catalog

        report = {}
        activated = (Catalog.query
                     .filter(Catalog.org_id.is_(None), Catalog.is_official.is_(True),
                             Catalog.is_active.is_(False))
                     .update({'is_active': True}, synchronize_session=False))
        db.session.commit()
        report['catalogos_activados'] = activated
        load_initial_data()
        ensure_marketplace()
        report['documentos'] = DocumentBankSeeder.seed()
        FlagService.ensure_defaults()

        user = cls._ensure_user()
        ensure_marketplace()
        org_id = Membership.query.filter_by(user_id=user.id).first().org_id
        for key in _DEMO_FLAGS:
            FlagService.enable_for_org(key, org_id, created_by=user.id)

        from app.services.org_service import OrgService
        OrgService.update_branding(org_id, {'project_prefix': DEMO_PREFIX})

        if Project.query.filter_by(org_id=org_id).first():
            report['dataset'] = 'la org ya tiene proyectos; no se duplica'
            return report

        panel = Panel.query.first()
        inverter = Inverter.query.first()
        battery = Battery.query.first()

        aprobado = cls._project_aprobado(org_id, user, panel, inverter, battery)
        cls._legalize(aprobado, user, until='aprobado')
        cls._posventa(org_id, aprobado)
        cls._finanzas(org_id, aprobado, user)

        en_revision = cls._project_en_revision(org_id, user, panel, inverter)
        cls._legalize(en_revision, user, until='en_revision')

        cls._project_borrador(org_id, user, panel)
        cls._actividad_extra(org_id, user, aprobado)

        report['dataset'] = 'creado: 3 proyectos, instalación de posventa y finanzas'
        return report

    @staticmethod
    def _ensure_user():
        from app.services.auth_service import AuthService
        user = User.query.filter_by(email=DEMO_EMAIL).first()
        if not user:
            user, _ = AuthService.register(
                DEMO_EMAIL, DEMO_PASSWORD, 'Sunalize', 'Test', 'Sunalize Test')
        user.is_superadmin = True
        user.email_verified = True
        db.session.commit()
        return user

    @staticmethod
    def _record(action, user, org_id, entity_id):
        from app.services.audit_service import AuditService
        AuditService.record(action, actor=user, org_id=org_id,
                            entity_type='project', entity_id=entity_id)
        db.session.commit()

    @classmethod
    def _project_aprobado(cls, org_id, user, panel, inverter, battery):
        project = Project(
            org_id=org_id,
            serial_seq=Project.next_serial_seq(org_id),
            cliente='Villa Turquesa — Fam. Navarro',
            direccion='Camí de la Mar 12',
            localidad='Alicante',
            latitud=38.352, longitud=-0.493,
            necesidad=7600.0, autoconsumo=90.0,
            coplanar=False,
            panel_id=panel.id, inverter_id=inverter.id,
            battery_id=battery.id, battery_quantity=2,
            cups='ES0021000000000001JN',
            compania='Iberdrola',
            potencia_contratada=5.75,
            tipo_voltaje='monofasico',
            referencia_catastral='9872023VH5797S0001WX',
        )
        project.resultados = cls._resultados(inverter, battery)
        db.session.add(project)
        db.session.commit()
        cls._record('project.create', user, org_id, project.id)
        return project

    @classmethod
    def _project_en_revision(cls, org_id, user, panel, inverter):
        project = Project(
            org_id=org_id,
            serial_seq=Project.next_serial_seq(org_id),
            cliente='Nave Agrícola Hnos. Serrano',
            direccion='Partida La Alcoraya, s/n',
            localidad='Elche',
            latitud=38.269, longitud=-0.712,
            necesidad=18500.0, autoconsumo=80.0,
            coplanar=True, inclinacion=15.0, azimut=195.0,
            panel_id=panel.id, inverter_id=inverter.id,
            compania='Endesa',
            potencia_contratada=15.0,
            tipo_voltaje='trifasico',
        )
        resultados = cls._resultados(inverter, battery=None, scale=2.3)
        project.resultados = resultados
        db.session.add(project)
        db.session.commit()
        cls._record('project.create', user, org_id, project.id)
        return project

    @classmethod
    def _project_borrador(cls, org_id, user, panel):
        project = Project(
            org_id=org_id,
            serial_seq=Project.next_serial_seq(org_id),
            cliente='Chalet Los Almendros',
            localidad='San Vicente del Raspeig',
            latitud=38.396, longitud=-0.525,
            necesidad=4200.0, autoconsumo=90.0,
            panel_id=panel.id,
        )
        db.session.add(project)
        db.session.commit()
        cls._record('project.create', user, org_id, project.id)
        return project

    @staticmethod
    def _resultados(inverter, battery, scale=1.0):
        resultados = {
            'total_field_power': round(5.4 * scale, 2),
            'cell_amount': int(12 * scale),
            'max_cell_amount': int(14 * scale),
            'annual_production': round(_ANNUAL_PRODUCTION * scale, 1),
            'annual_irradiance_kWh_m2': 1940.0,
            'optimal_irradiance': 2210.0,
            'beta_optimal': 35.0,
            'coldest_temperature': -1.2,
            'coldest_day_v_max': 598.4,
            'altitude': 25.0,
            'cell_area': round(26.2 * scale, 1),
            'total_y': 0.171,
            'irradiance_factor_loss': 3.1,
            'temp_power_loss': 6.8,
            'cell_temp': 43.5,
            'sec_energy': round(_ANNUAL_PRODUCTION * scale, 1),
            'sec_net_energy': round(_ANNUAL_PRODUCTION * scale * 0.9, 1),
            'panel_protection_v': 720.0,
            'panel_protection_i': 15.0,
            'monthly_irradiance': _MONTHLY_IRRADIANCE,
            'monthly_production': [round(v * scale, 1) for v in _MONTHLY_PRODUCTION],
            'selected_inverter': {
                'id': inverter.id, 'nombre': inverter.nombre,
                'power': inverter.power, 'vmax': inverter.vmax, 'y': inverter.y,
            },
        }
        if battery is not None:
            resultados['battery'] = {
                'battery_id': battery.id,
                'nombre': battery.nombre,
                'quantity': 2,
                'bank_capacity_kwh': round(battery.capacity_kwh * 2, 1),
                'bank_usable_kwh': round(battery.capacity_kwh * 2 * 0.9, 1),
                'recommended_usable_kwh': 8.5,
                'estimated_self_consumption_pct': 88.0,
                'annual_battery_contribution_kwh': 1450.0,
                'method_note': 'Estimación por perfil de consumo residencial y ciclo diario.',
            }
        return resultados

    @staticmethod
    def _legalize(project, user, until):
        from app.services.legalization_service import LegalizationService
        sha = hashlib.sha256(f'sunalyze-demo-memoria-{project.id}'.encode()).hexdigest()
        LegalizationService.sign_memoria(project, user, sha, 183_512,
                                         note='Memoria técnica firmada (demo)')
        LegalizationService.transition(project, user, 'en_revision',
                                       note='Expediente completo, pasa a revisión')
        if until == 'en_revision':
            return
        LegalizationService.transition(project, user, 'presentado',
                                       note='Presentado en sede electrónica de industria')
        LegalizationService.transition(project, user, 'aprobado',
                                       note='Resolución favorable del expediente')

    @staticmethod
    def _posventa(org_id, project):
        from app.services.installation_service import InstallationService
        installation = InstallationService.create_from_project(org_id, project.id)
        today = date.today()
        installation.commissioned_at = today - timedelta(days=210)
        installation.warranty_until = today + timedelta(days=1620)
        installation.notes = 'Instalación entregada y monitorizada (dataset de demo).'
        db.session.commit()

        first = today.replace(day=1)
        months = []
        cursor = first
        for _ in range(6):
            cursor = (cursor - timedelta(days=1)).replace(day=1)
            months.append(cursor)
        for month, factor in zip(reversed(months), _READING_FACTORS):
            expected = _MONTHLY_PRODUCTION[month.month - 1]
            InstallationService.add_reading(installation, {
                'period': month.strftime('%Y-%m'),
                'actual_kwh': round(expected * factor, 1),
            })

        InstallationService.add_visit(installation, {
            'kind': 'preventivo',
            'status': 'realizada',
            'done_at': today - timedelta(days=45),
            'technician': 'Laura Pertegaz',
            'notes': 'Limpieza del campo FV y revisión de strings; todo correcto.',
        })
        InstallationService.add_incident(installation, {
            'title': 'Caída puntual de producción por sombra de grúa en obra vecina',
            'severity': 'media',
            'status': 'resuelta',
        })
        InstallationService.add_incident(installation, {
            'title': 'Revisar apriete de conectores MC4 en string 2',
            'severity': 'baja',
            'status': 'abierta',
        })
        return installation

    @staticmethod
    def _finanzas(org_id, project, user):
        from app.schemas.finance import ScenarioCreate, FinancialAssumptions
        from app.services.finance_service import FinanceService
        data = ScenarioCreate(
            name='Contado',
            assumptions=FinancialAssumptions(
                capex_total=8900.0,
                tariff_eur_kwh=0.16,
                annual_consumption_kwh=7600.0,
                om_cost_eur_year=90.0,
            ),
            is_default=True,
        )
        return FinanceService.create_scenario(org_id, project.id, data,
                                              created_by=user.id)

    @staticmethod
    def _actividad_extra(org_id, user, project):
        from app.services.audit_service import AuditService
        from app.services.notification_service import NotificationService
        AuditService.record('project.update', actor=user, org_id=org_id,
                            entity_type='project', entity_id=project.id,
                            payload={'estado': 'aprobado'})
        NotificationService.notify([user.id], 'project.shared', actor=None,
                                   org_id=org_id, entity_type='project',
                                   entity_id=project.id,
                                   payload={'cliente': project.cliente})
        db.session.commit()
