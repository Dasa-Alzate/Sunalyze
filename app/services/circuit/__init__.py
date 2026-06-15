"""Circuit diagram engine — public facade.

Domain layout:
    core/       Diagram compositor, Component base, Wire, BoxArea, config,
                style, and connection-point geometry.
    components/ The 13 parametric SVG symbols.
    diagrams/   Diagram builders (3 building blocks + named templates) and the
                template registry.
    service.py  CircuitService — orchestrates building-block generation.
"""

from .core.box_area import BoxArea
from .core.component import Component
from .core.config import ACConfig, DCConfig, DiagramStyle, SystemConfig
from .core.diagram import Diagram
from .core.geometry import rotate_point, transform_ports
from .core.wire import Wire
from .diagrams.registry import TEMPLATES, list_templates, render_template
from .service import CircuitService

__all__ = [
    "CircuitService",
    "Component",
    "Diagram",
    "Wire",
    "BoxArea",
    "SystemConfig",
    "DCConfig",
    "ACConfig",
    "DiagramStyle",
    "rotate_point",
    "transform_ports",
    "TEMPLATES",
    "list_templates",
    "render_template",
]
