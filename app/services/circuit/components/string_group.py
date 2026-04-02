"""Panel string group symbol."""

from ..component import Component


class StringGroup(Component):
    """
    Panel string input symbol (seccionador de string / entrada de string FV).
    Represents each string of series-connected panels at the DC protection input.
    Based on assets/unifilar/panel.svg exact paths.
    """

    def render(self, style, label: str = "", index: int = 1,
               panels: int = 0, voltage: float = 0.0, **kwargs) -> str:
        c = ""

        # Rectangle body
        c += self._rect(9.98, 30.5, 100, 60, style)

        # Terminal
        c += self._line(110, 60, 120, 60, style)

        # Diagonal zigzag (IEC disconnector blade)
        c += self._path(
            "M 10.024,30.472 L 40.036,60.457 L 10.154,89.995 L 9.978,90.033",
            style,
        )

        # String label
        title = label or f"String {index}"
        c += self._text(60, 22, title, style)

        # Panel count × voltage info
        if panels and voltage:
            c += self._text(60, 108, f"{panels}p  ×  {voltage:.0f} V", style)

        return c
