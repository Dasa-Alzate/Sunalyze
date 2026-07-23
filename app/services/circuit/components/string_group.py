
from ..core.component import Component


class StringGroup(Component):

    PORTS = {"out": (120, 60), "in": (0, 60)}

    def render(self, style, label: str = "", index: int = 1,
               panels: int = 0, voltage: float = 0.0, **kwargs) -> str:
        c = ""

        c += self._rect(9.98, 30.5, 100, 60, style)

        c += self._line(110, 60, 120, 60, style)

        c += self._path(
            "M 10.024,30.472 L 40.036,60.457 L 10.154,89.995 L 9.978,90.033",
            style,
        )

        title = label or f"String {index}"
        c += self._text(60, 22, title, style)

        if panels and voltage:
            c += self._text(60, 108, f"{panels}p  ×  {voltage:.0f} V", style)

        return c
