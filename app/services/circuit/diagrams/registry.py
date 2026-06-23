"""Named diagram template registry.

Each template is a builder ``builder(config: SystemConfig) -> svg_str``. The
registry exposes the four named solar templates plus the three building-block
diagrams, all keyed by a stable name with a human label.
"""

from ..core.config import SystemConfig
from .dc_strings_diagram import DCStringsDiagram
from .full_system_diagram import FullSystemDiagram
from .grid_connection_diagram import GridConnectionDiagram
from .solar_diagram import SolarDiagram


def _solar_basico(config: SystemConfig) -> str:
    return SolarDiagram(config, has_fuses=False, has_battery=False).render()


def _solar_con_baterias(config: SystemConfig) -> str:
    return SolarDiagram(config, has_fuses=True, has_battery=True).render()


def _solar_sin_fusibles(config: SystemConfig) -> str:
    return SolarDiagram(config, has_fuses=False, has_battery=False).render()


def _solar_con_fusibles(config: SystemConfig) -> str:
    return SolarDiagram(config, has_fuses=True, has_battery=False).render()


def _cc_strings(config: SystemConfig) -> str:
    return DCStringsDiagram(config.dc, config.style).render()


def _grid_connection(config: SystemConfig) -> str:
    return GridConnectionDiagram(config.ac, config.style).render()


def _full_system(config: SystemConfig) -> str:
    return FullSystemDiagram(config.dc, config.ac, config.style).render()


TEMPLATES = {
    "solar-basico": {
        "label": "Solar básico",
        "builder": _solar_basico,
    },
    "solar-con-baterias": {
        "label": "Solar con baterías",
        "builder": _solar_con_baterias,
    },
    "solar-sin-fusibles": {
        "label": "Solar sin fusibles",
        "builder": _solar_sin_fusibles,
    },
    "solar-con-fusibles": {
        "label": "Solar con fusibles",
        "builder": _solar_con_fusibles,
    },
    "cc-strings": {
        "label": "Esquema CC (strings)",
        "builder": _cc_strings,
    },
    "grid-connection": {
        "label": "Conexión a red",
        "builder": _grid_connection,
    },
    "full-system": {
        "label": "Sistema completo",
        "builder": _full_system,
    },
}


def list_templates() -> list[dict]:
    """Return [{name, label}, ...] for every registered template."""
    return [{"name": name, "label": spec["label"]} for name, spec in TEMPLATES.items()]


def render_template(name: str, config: SystemConfig) -> str:
    """Render a named template to SVG. Raises KeyError if unknown."""
    return TEMPLATES[name]["builder"](config)
