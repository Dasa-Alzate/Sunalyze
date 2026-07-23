
from ..core.component import Component


class Battery(Component):

    PORTS = {"in": (60, 0), "out": (60, 0)}

    def render(self, style, label: str = "", **kwargs) -> str:
        c = ""
        c += self._rect(0, 0, 120, 120, style)

        c += self._line(60, 0, 60, 30, style)

        for i, y in enumerate((42, 70)):
            c += self._line(35, y, 85, y, style)
            c += self._line(50, y + 12, 70, y + 12, style)

        c += self._line(86, 36, 96, 36, style)
        c += self._line(91, 31, 91, 41, style)

        if label:
            c += self._text(60, 115, label, style)
        return c
