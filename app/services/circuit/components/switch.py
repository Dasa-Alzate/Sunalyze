"""Fuse (fusible) circuit symbol — IEC 60617."""

from ..component import Component


class Switch(Component):
    """
    IEC 60617 fuse symbol: conductor through a rectangular cartridge.
    Faithful to assets/unifilar/fuse.svg.
    """

    def render(self, style, label: str = "", **kwargs) -> str:
        c = ""
        c += self._line(0, 60, 50, 60, style)
        c += self._line(50, 60, 70, 45, style)
        c += self._line(70, 60, 120, 60, style)
        if label:
            c += self._text(60, 90, label, style)
        return c
