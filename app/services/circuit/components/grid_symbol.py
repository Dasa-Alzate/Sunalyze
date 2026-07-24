
from ..core.component import Component


class GridSymbol(Component):

    PORTS = {"out": (60, 120)}

    def render(self, style, voltage: str = "1N 230VAC",
               frequency: str = "50Hz TT", label: str = "", **kwargs) -> str:
        c = ""
        c += self._circle(60, 58, 24, style)
        c += self._text(60, 63, "~", style)
        c += self._line(60, 82, 60, 120, style)
        if voltage:
            c += self._text(60, 14, voltage, style)
        if frequency:
            c += self._text(60, 30, frequency, style)
        return c
