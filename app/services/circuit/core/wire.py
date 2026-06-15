"""Wire element for circuit diagrams."""

from dataclasses import dataclass


@dataclass
class Wire:
    """
    A straight wire segment between two grid coordinates.

    Coordinates are multiples of 0.5:
      - Integer (e.g. 2):   exact grid boundary — component edge or corner.
      - Half-integer (e.g. 1.5): centre of that grid cell.

    A Wire draws a single straight line. Use multiple wires for L-shaped routes.
    """

    x1: float
    y1: float
    x2: float
    y2: float
