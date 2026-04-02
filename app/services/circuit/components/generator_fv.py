"""Photovoltaic generator symbol (generador fotovoltaico)."""

from ..component import Component


class FVGenerator(Component):
    """
    PV generator symbol: circle with 'G'.
    Designed for the top of a vertical PV branch.
    """

    def render(self, style, label: str = "GENERADOR FV",
               sublabel: str = "", **kwargs) -> str:
        c = ""
        c += self._circle(60, 44, 28, style)
        c += self._text(60, 50, "G", style)
        if label:
            c += self._text(60, 10, label, style)
        if sublabel:
            c += self._text(60, 22, sublabel, style)
        return c
