"""DC switch disconnector (seccionador de CC) circuit symbol."""

from ..component import Component


class SwitchDC(Component):
    """
    DC switch disconnector / interruptor seccionador fotovoltaico.
    Rectangle body with a diagonal cut indicating the open-contact position.
    """

    def render(self, style, label: str = "", **kwargs) -> str:
        c = ""
        c += self._rect(10, 30.5, 100, 59, style)
        c += self._path("M 10,30.5 L 40,60 L 10,89.5", style)
        c += self._line(0, 60, 10, 60, style)
        c += self._line(110, 60, 120, 60, style)
        if label:
            c += self._text(65, 105, label, style)
        return c
