"""Solar panel (FV module) circuit symbol."""

from ..component import Component


class SolarPanel(Component):
    """
    Photovoltaic module symbol.
    Grid of cells representing the panel face.
    """

    def render(self, style, label: str = "", model: str = "", **kwargs) -> str:
        c = ""
        c += self._rect(5, 5, 80, 110, style)

        # Cell grid (4×4 cells)
        cell_w, cell_h = 18, 23
        for col in range(4):
            for row in range(4):
                cx = 7 + col * (cell_w + 2)
                cy = 8 + row * (cell_h + 2)
                c += self._rect(cx, cy, cell_w, cell_h, style)

        # + / - polarity marks
        c += self._text(98, 36, "+", style)
        c += self._text(98, 76, "−", style)

        if model:
            c += self._text(45, 125, model[:14], style)
        if label:
            c += self._text(45, 138, label, style)
        return c
