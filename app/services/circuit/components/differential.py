
from ..core.component import Component


class Differential(Component):

    def render(self, style, label: str = "", sensitivity: str = "", **kwargs) -> str:
        c = ""
        c += self._rect(5.5, 10.5, 109, 99, style)

        c += self._line(42.7, 92.5, 35.7, 87.9, style)
        c += self._line(42.7, 87.9, 35.7, 91.9, style)
        c += self._line(39.2, 90.0, 39.5, 109.9, style)
        c += self._path("M 46.6,90.3 L 39.7,75 V 10.5", style)
        
        c += self._rect(0, 0, 120, 120, style)

        c += self._line(82.7, 92.5, 75.7, 87.9, style)
        c += self._line(82.7, 87.9, 75.7, 91.9, style)
        c += self._line(79.2, 90.0, 79.5, 109.9, style)
        c += self._path("M 86.6,90.3 L 79.7,75 V 10.5", style)

        c += self._path("M 94.5,36.3 A 34.5,10.8 0 1 1 94.4,36.2", style)

        c += self._path("M 103,75 V 35.7 L 94.5,35.7", style, dasharray="2,1")

        if sensitivity:
            c += self._text(28, 38, sensitivity, style, anchor="start")
        if label:
            c += self._text(60, 118, label, style)
        return c
