"""Base class for all SVG circuit components."""

from abc import ABC, abstractmethod
from typing import ClassVar
from xml.sax.saxutils import escape


class Component(ABC):
    """
    Base class for all circuit symbols.

    Each component renders its body in a CELL×CELL local coordinate space.
    Components are connection-agnostic: they draw the symbol only.
    Placement, orientation, scale, and wire routing are the Diagram's responsibility.

    render() returns raw SVG elements — no outer <g transform>.
    """

    CELL: ClassVar[int] = 120

    @abstractmethod
    def render(self, style, **kwargs) -> str:
        """Return SVG body content (no wrapping <g>)."""
        ...

    # ── SVG helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _path(d: str, style, dasharray: str = "") -> str:
        dash = f' stroke-dasharray="{dasharray}"' if dasharray else ""
        return (
            f'<path d="{d}" fill="none"'
            f' stroke="{style.stroke_color}"'
            f' stroke-width="{style.stroke_width}"{dash}/>'
        )

    @staticmethod
    def _rect(x: float, y: float, w: float, h: float, style) -> str:
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}"'
            f' fill="none" stroke="{style.stroke_color}"'
            f' stroke-width="{style.stroke_width}"/>'
        )

    @staticmethod
    def _line(x1: float, y1: float, x2: float, y2: float,
              style, dasharray: str = "") -> str:
        dash = f' stroke-dasharray="{dasharray}"' if dasharray else ""
        return (
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"'
            f' fill="none" stroke="{style.stroke_color}"'
            f' stroke-width="{style.stroke_width}"{dash}/>'
        )

    @staticmethod
    def _circle(cx: float, cy: float, r: float, style,
                filled: bool = False) -> str:
        fill = style.stroke_color if filled else "none"
        return (
            f'<circle cx="{cx}" cy="{cy}" r="{r}"'
            f' fill="{fill}" stroke="{style.stroke_color}"'
            f' stroke-width="{style.stroke_width}"/>'
        )

    @staticmethod
    def _text(x: float, y: float, text: str, style,
              anchor: str = "middle") -> str:
        safe_text = escape(str(text))
        return (
            f'<text x="{x}" y="{y}" text-anchor="{anchor}"'
            f' font-family="{style.font_family}"'
            f' font-size="{style.font_size}"'
            f' fill="{style.label_color}">{safe_text}</text>'
        )
