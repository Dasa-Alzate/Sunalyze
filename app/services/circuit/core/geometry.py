
from typing import Dict, Tuple

CELL: int = 120
CENTER: float = CELL / 2

Point = Tuple[float, float]


def rotate_point(x: float, y: float, orientation: int) -> Point:
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
    return {name: rotate_point(x, y, orientation) for name, (x, y) in ports.items()}
