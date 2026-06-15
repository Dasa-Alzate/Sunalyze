"""Circuit diagram generators and named-template registry."""

from .dc_strings_diagram import DCStringsDiagram
from .full_system_diagram import FullSystemDiagram
from .grid_connection_diagram import GridConnectionDiagram
from .registry import TEMPLATES, list_templates, render_template
from .solar_diagram import SolarDiagram

__all__ = [
    "DCStringsDiagram",
    "GridConnectionDiagram",
    "FullSystemDiagram",
    "SolarDiagram",
    "TEMPLATES",
    "list_templates",
    "render_template",
]
