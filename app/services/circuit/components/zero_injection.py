"""Zero injection / network analyzer device symbol."""

from ..core.component import Component


class ZeroInjection(Component):
    """
    Zero injection device / network analyzer (analizador de red).
    Rectangle body with abbreviated label inside.
    """

    def render(self, style, label: str = "", model: str = "", **kwargs) -> str:
        c = ""
        c += self._rect(10, 22, 100, 76, style)
        c += self._text(60, 50, "DISP.", style)
        c += self._text(60, 65, "INY. 0", style)
        if label:
            c += self._text(60, 80, label[:16], style)
        if model:
            c += self._text(60, 112, model[:18], style)
        return c
