"""Magnetothermic circuit breaker (magnetotérmico / MCB) circuit symbol."""

from ..core.component import Component


class CircuitBreaker(Component):
    """
    Magnetothermic circuit breaker (IGA / PIA / MCB).
    Rectangle body with a thermal bimetal zigzag and a magnetic release bar.
    """

    def render(self, style, label: str = "", **kwargs) -> str:
        c = ""
        c += self._rect(10, 20, 100, 80, style)

        # Thermal bimetal zigzag (left half)
        c += self._path("M 32,35 L 42,50 L 32,65 L 42,80", style)

        # Magnetic release: vertical bar + horizontal trip bar (right half)
        c += self._line(75, 30, 75, 90, style)
        c += self._line(65, 60, 88, 60, style)
        c += self._line(71, 56, 79, 64, style)
        c += self._line(0, 60, 10, 60, style)
        c += self._line(110, 60, 120, 60, style)
        
        if label:
            c += self._text(60, 115, label, style)
        return c
