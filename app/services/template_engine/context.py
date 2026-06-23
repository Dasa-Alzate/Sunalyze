"""Construcción del contexto de render desde un Project y su resolver seguro.

El resolver solo lee atributos presentes en la whitelist del catálogo de variables. Una ruta
fuera de la whitelist o sobre una entidad ausente produce TemplateError; jamás se usa `getattr`
sobre nombres no autorizados, de modo que no hay vía hacia dunders ni objetos internos.
"""

from .errors import TemplateError
from .catalog import whitelist


def build_context(project, user=None, org=None):
    """Arma el dict de entidades de render.

    Incluye project, panel, inverter, battery, wire, user, org, finance y las entidades de
    posventa (installation, maintenance, incident). Todas las opcionales son None-safe: si la
    instalación, su última visita o una incidencia abierta no existen, la entidad es None y sus
    variables resuelven a vacío (placeholder), sin romper el render. La batería y el cableado
    siguen el mismo patrón.
    """
    panel = getattr(project, 'panel', None)
    inverter = getattr(project, 'inverter', None)
    battery = getattr(project, 'battery', None)
    wire = _project_wire(panel)
    if org is None:
        org = _project_org(project)
    installation = _project_installation(project)
    return {
        'project': project,
        'panel': panel,
        'inverter': inverter,
        'battery': battery,
        'wire': wire,
        'user': user,
        'org': org,
        'finance': _project_finance(project),
        'installation': installation,
        'maintenance': _latest_maintenance(installation),
        'incident': _relevant_incident(installation),
    }


class _FinanceView:
    """Vista plana del dict `results` de un escenario, con los atributos del catálogo finance."""

    def __init__(self, results):
        capex = results.get('capex') or {}
        metrics = results.get('metrics') or {}
        incentives = results.get('incentives') or {}
        self.net_capex = capex.get('net_eur')
        self.annual_saving_year1_eur = results.get('annual_saving_year1_eur')
        self.payback_years = metrics.get('payback_simple_years')
        self.payback_discounted_years = metrics.get('payback_discounted_years')
        self.irr = metrics.get('irr')
        self.npv = metrics.get('npv_eur')
        self.lcoe = metrics.get('lcoe_eur_kwh')
        self.co2_avoided_year = metrics.get('co2_avoided_year1_kg')
        self.incentives_total = incentives.get('total_eur')


def _project_finance(project):
    if project is None:
        return None
    try:
        from app.models.financial_scenario import FinancialScenario
    except Exception:
        return None
    project_id = getattr(project, 'id', None)
    org_id = getattr(project, 'org_id', None)
    if project_id is None:
        return None
    try:
        scenario = (FinancialScenario.query
                    .filter_by(org_id=org_id, project_id=project_id)
                    .order_by(FinancialScenario.is_default.desc(),
                              FinancialScenario.created_at.desc())
                    .first())
    except Exception:
        return None
    if scenario is None or scenario.results is None:
        return None
    return _FinanceView(scenario.results)


def _project_installation(project):
    if project is None:
        return None
    try:
        from app.models.installation import Installation
    except Exception:
        return None
    project_id = getattr(project, 'id', None)
    org_id = getattr(project, 'org_id', None)
    if project_id is None:
        return None
    try:
        return (Installation.query
                .filter_by(org_id=org_id, project_id=project_id)
                .first())
    except Exception:
        return None


def _latest_maintenance(installation):
    if installation is None:
        return None
    visits = getattr(installation, 'maintenance_visits', None) or []
    return visits[0] if visits else None


def _relevant_incident(installation):
    if installation is None:
        return None
    incidents = getattr(installation, 'incidents', None) or []
    for inc in incidents:
        if getattr(inc, 'status', None) != 'resuelta':
            return inc
    return incidents[0] if incidents else None


def _project_wire(panel):
    catalog = getattr(panel, 'catalog', None) if panel is not None else None
    if catalog is None:
        return None
    try:
        from app.models.wire import Wire
        return Wire.query.filter_by(catalog_id=catalog.id).order_by(Wire.id).first()
    except Exception:
        return None


def _project_org(project):
    org_id = getattr(project, 'org_id', None)
    if org_id is None:
        return None
    try:
        from app.models.organization import Organization
        return Organization.query.get(org_id)
    except Exception:
        return None


class ContextResolver:
    """Resuelve rutas `entidad.atributo` contra el contexto, respetando la whitelist."""

    def __init__(self, context, allowed=None, presentation=None):
        self.context = context
        self.allowed = allowed if allowed is not None else whitelist()
        self.presentation = presentation

    def resolve(self, path):
        parts = path.split('.')
        if len(parts) != 2:
            raise TemplateError(
                f"Ruta de variable inválida: '{path}'. Use 'entidad.atributo'."
            )
        entity_name, attr = parts
        if entity_name not in self.allowed:
            raise TemplateError(f"Entidad desconocida: '{entity_name}'.")
        if attr not in self.allowed[entity_name]:
            raise TemplateError(
                f"Atributo no disponible: '{entity_name}.{attr}'."
            )
        entity = self.context.get(entity_name)
        if entity is None:
            return None
        return getattr(entity, attr, None)
