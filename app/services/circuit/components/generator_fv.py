
from ..core.component import Component


class FVGenerator(Component):

    PORTS = {"out": (60, 120)}

    def render(self, style, label: str = "GENERADOR FV",
               sublabel: str = "", **kwargs) -> str:
        c = ""
        c += self._circle(60, 62, 25, style)
        c += self._line(60, 87, 60, 120, style)
        c += self._text(60, 66, "G", style)
        if label:
            c += self._text(60, 14, label, style)
        if sublabel:
            c += self._text(60, 28, sublabel, style)
        return c
