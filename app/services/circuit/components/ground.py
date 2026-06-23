"""Earth / ground symbol (toma de tierra)."""

from ..core.component import Component


class Ground(Component):
    """
    Earth/ground symbol (PE — Protective Earth).
    Three decreasing horizontal lines.
    """

    PORTS = {"in": (60, 0)}

    def render(self, style, label: str = "", **kwargs) -> str:
        c = ""
        c += self._line(30, 20, 90, 20, style)
        c += self._line(38, 32, 82, 32, style)
        c += self._line(46, 44, 74, 44, style)
        if label:
            c += self._text(60, 62, label, style)
        return c
