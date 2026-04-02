"""kWh bidirectional energy meter symbol (contador bidireccional)."""

from ..component import Component


class Meter(Component):
    """
    kWh bidirectional energy meter.
    Rectangle with 'kWh' label and bidirectional arrows.
    """

    def render(self, style, label: str = "", **kwargs) -> str:
        c = ""
        c += self._rect(10, 28, 100, 64, style)
        c += self._text(60, 56, "kWh", style)

        # Import arrow (→)
        c += self._path("M 28,40 L 46,40 L 42,36", style)
        c += self._path("M 42,44 L 46,40", style)

        # Export arrow (←)
        c += self._path("M 74,76 L 92,76 L 88,72", style)
        c += self._path("M 88,80 L 92,76", style)

        if label:
            c += self._text(60, 104, label, style)
        return c
