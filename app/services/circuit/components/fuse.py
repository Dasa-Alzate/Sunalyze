"""Fuse (fusible) circuit symbol — IEC 60617."""

from ..component import Component


class Fuse(Component):
    """
    IEC 60617 fuse symbol: conductor through a rectangular cartridge.
    """

    def render(self, style, label: str = "", **kwargs) -> str:
        c = ""
        c += self._line(0, 60, 120, 60, style)
        c += self._rect(10.5, 45.5, 99, 29, style)
        if label:
            c += self._text(60, 90, label, style)
        return c
