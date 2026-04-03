"""DC/AC inverter circuit symbol."""

from ..component import Component


class Inverter(Component):
    """
    DC/AC inverter symbol.
    Rectangle with a diagonal divider; DC bars on the left half,
    """

    def render(self, style, label: str = "", **kwargs) -> str:
        c = ""
        c += self._rect(0, 0, 120, 120, style)
        c += self._line(0, 120, 120, 0, style)

        # DC side: horizontal bars
        c += self._line(20, 35, 68, 35, style)
        c += self._line(20, 44, 38, 44, style)
        c += self._line(50, 44, 68, 44, style)

        # AC side: sine wave
        c += self._path(
            "M 52,85 C 52,85 63.5,67 75,85 C 86.5,103 100,85 100,85",
            style,
        )

        if label:
            c += self._text(60, 130, label, style)
        return c
