"""Surge arrester / overvoltage protector (descargador de sobretensiones) symbol."""

from ..core.component import Component


class SurgeArrester(Component):
    """
    Surge arrester (varistor / SPD) symbol.
    Downward-pointing triangle (arrester body) connected to a ground symbol.
    Oriented vertically: top is the live connection, bottom is earth.
    """

    PORTS = {"in": (60, 0), "pe": (60, 120)}

    def render(self, style, label: str = "", **kwargs) -> str:
        c = ""

        # Arrester body: downward-pointing triangle
        c += self._path("M 60,25 L 25,75 L 95,75 Z", style)
        c += self._line(25, 75, 95, 75, style)

        # Internal wire from triangle base to ground bars
        c += self._line(60, 75, 60, 82, style)

        # Ground bars
        c += self._line(40, 82, 80, 82, style)
        c += self._line(47, 90, 73, 90, style)
        c += self._line(54, 98, 66, 98, style)

        c += self._rect(0, 0, 120, 120, style)

        if label:
            c += self._text(60, 115, label, style)
        return c
