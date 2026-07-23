
from ..core.component import Component


class Meter(Component):

    def render(self, style, label: str = "", **kwargs) -> str:
        c = ""
        c += self._line(60, 0, 60, 28, style)
        c += self._line(60, 92, 60, 120, style)
        c += self._rect(10, 28, 100, 64, style)
        c += self._text(60, 56, "kWh", style)

        c += self._path("M 28,40 L 46,40 L 42,36", style)
        c += self._path("M 42,44 L 46,40", style)

        c += self._path("M 74,76 L 92,76 L 88,72", style)
        c += self._path("M 88,80 L 92,76", style)

        if label:
            c += self._text(60, 104, label, style)
        return c
