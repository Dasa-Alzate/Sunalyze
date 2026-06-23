"""BoxArea element for circuit diagrams."""

from dataclasses import dataclass


@dataclass
class BoxArea:
    """
    A dashed-border labelled region spanning grid cells.

    (x1, y1): top-left grid corner.
    (x2, y2): bottom-right grid corner.

    Coordinates follow the same 0.5-multiple convention as Wire.
    """

    x1: float
    y1: float
    x2: float
    y2: float
    title: str = ""
