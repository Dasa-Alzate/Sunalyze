
from ..core.component import Component


class GridSymbol(Component):

    PORTS = {"out": (60, 120)}

    def render(self, style, voltage: str = "1N 230VAC",
               frequency: str = "50Hz TT", label: str = "", **kwargs) -> str:
        c = ""
        c += self._circle(60, 44, 30, style)
        c += self._text(60, 50, "~", style)
        if voltage:
            c += self._text(60, 10, voltage, style)
        if frequency:
            c += self._text(60, 24, frequency, style)
        return c
