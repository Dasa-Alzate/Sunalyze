"""Connection-point geometry for circuit components.

A component declares its connection points (ports) in local 120x120 cell
coordinates. The diagram places a component with an orientation in
{0, 90, 180, 270} degrees clockwise, applied as a rotation around the cell
centre (60, 60) -- the same transform the renderer emits as
``rotate(orientation, 60, 60)``. ``rotate_point`` reproduces that transform so
a declared port can be resolved to its on-screen location, letting wires snap
to component edges regardless of orientation.
"""

from typing import Dict, Tuple

CELL: int = 120
CENTER: float = CELL / 2

Point = Tuple[float, float]


def rotate_point(x: float, y: float, orientation: int) -> Point:
    """Rotate a local point clockwise around the cell centre (60, 60)."""
    o = orientation % 360
    cx = cy = CENTER
    if o == 0:
        return (x, y)
    if o == 90:
        return (cx - (y - cy), cy + (x - cx))
    if o == 180:
        return (cx - (x - cx), cy - (y - cy))
    if o == 270:
        return (cx + (y - cy), cy - (x - cx))
    raise ValueError(f"orientation must be one of 0/90/180/270, got {orientation}")


def transform_ports(
    ports: Dict[str, Point], orientation: int
) -> Dict[str, Point]:
    """Return ports transformed by orientation, in local cell coordinates."""
    return {name: rotate_point(x, y, orientation) for name, (x, y) in ports.items()}
