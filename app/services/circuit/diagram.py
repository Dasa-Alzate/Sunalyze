"""Grid-based SVG diagram compositor."""

from dataclasses import dataclass, field
from xml.sax.saxutils import escape

from .box_area import BoxArea
from .config import DiagramStyle
from .wire import Wire


@dataclass
class _PlacedComponent:
    component: object
    gx: float
    gy: float
    orientation: int = 0       # 0 | 90 | 180 | 270  (clockwise degrees)
    label: str = ""
    label_pos: str = "below"   # above | below | left | right
    kwargs: dict = field(default_factory=dict)
    w_cells: float = 1.0       # horizontal scale in grid cells
    h_cells: float = 1.0       # vertical scale in grid cells


@dataclass
class _Dot:
    gx: float
    gy: float


@dataclass
class _FreeLabel:
    gx: float
    gy: float
    text: str
    anchor: str = "middle"


class Diagram:
    """
    Grid-based SVG compositor.

    Grid coordinate conventions
    ───────────────────────────
    Integer  (e.g. 2):    exact grid boundary — component top-left corner,
                          or the edge where two cells meet.
    Half-int (e.g. 1.5):  centre of that grid cell.

    Example
    ───────
    d = Diagram(cols=5, rows=8)
    d.box(0, 0, 5, 8, title="CC Protection")
    d.place(Fuse(), 1, 2, orientation=90, label="F1")
    d.wire(1.5, 0, 1.5, 2)     # vertical wire to top of Fuse cell
    d.dot(1.5, 3)
    return d.render()
    """

    def __init__(
        self,
        cols: float,
        rows: float,
        style: DiagramStyle | None = None,
        padding: int = 20,
    ):
        self.style = style or DiagramStyle()
        self._C = self.style.CELL       # 120 px per grid cell
        self._pad = padding
        self._w = int(cols * self._C + 2 * padding)
        self._h = int(rows * self._C + 2 * padding)

        self._comps:  list[_PlacedComponent] = []
        self._wires:  list[Wire]             = []
        self._boxes:  list[BoxArea]          = []
        self._dots:   list[_Dot]             = []
        self._labels: list[_FreeLabel]       = []

    # ── Builder API ─────────────────────────────────────────────────────────

    def place(
        self,
        component,
        gx: float,
        gy: float,
        orientation: int = 0,
        label: str = "",
        label_pos: str = "below",
        **kwargs,
    ) -> "Diagram":
        """Place a component at grid cell (gx, gy)."""
        self._comps.append(
            _PlacedComponent(component, gx, gy, orientation, label, label_pos, kwargs)
        )
        return self

    def place_scaled(
        self,
        component,
        gx: float,
        gy: float,
        w_cells: float,
        h_cells: float,
        label: str = "",
        label_pos: str = "below",
        **kwargs,
    ) -> "Diagram":
        """Place a component scaled to (w_cells × h_cells) grid cells."""
        self._comps.append(
            _PlacedComponent(
                component, gx, gy, 0, label, label_pos, kwargs, w_cells, h_cells
            )
        )
        return self

    def wire(self, x1: float, y1: float, x2: float, y2: float) -> "Diagram":
        """Draw a wire between two grid coordinates."""
        self._wires.append(Wire(x1, y1, x2, y2))
        return self

    def dot(self, gx: float, gy: float) -> "Diagram":
        """Draw a junction dot at a grid coordinate."""
        self._dots.append(_Dot(gx, gy))
        return self

    def box(
        self, x1: float, y1: float, x2: float, y2: float, title: str = ""
    ) -> "Diagram":
        """Draw a dashed box spanning (x1,y1)→(x2,y2) in grid units."""
        self._boxes.append(BoxArea(x1, y1, x2, y2, title))
        return self

    def label(
        self, gx: float, gy: float, text: str, anchor: str = "middle"
    ) -> "Diagram":
        """Draw a free text label at a grid coordinate."""
        self._labels.append(_FreeLabel(gx, gy, text, anchor))
        return self

    # ── Render ──────────────────────────────────────────────────────────────

    def render(self) -> str:
        """Return the complete SVG string."""
        s = self._C
        p = self._pad
        st = self.style
        elements: list[str] = []

        def px(gx: float) -> float:
            return gx * s + p

        def py(gy: float) -> float:
            return gy * s + p

        # 1. Boxes (background layer — rendered first so wires appear on top)
        for ba in self._boxes:
            x, y = px(ba.x1), py(ba.y1)
            w = (ba.x2 - ba.x1) * s
            h = (ba.y2 - ba.y1) * s
            elements.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}"'
                f' fill="none" stroke="{st.stroke_color}"'
                f' stroke-width="{st.stroke_width}" stroke-dasharray="8,4"/>'
            )
            if ba.title:
                elements.append(self._svg_text(x + w / 2, y + 14, ba.title, st))

        # 2. Wires
        for w in self._wires:
            elements.append(
                f'<line x1="{px(w.x1)}" y1="{py(w.y1)}"'
                f' x2="{px(w.x2)}" y2="{py(w.y2)}"'
                f' stroke="{st.stroke_color}"'
                f' stroke-width="{st.stroke_width}" fill="none"/>'
            )

        # 3. Components
        for pc in self._comps:
            body = pc.component.render(st, **pc.kwargs)
            cpx, cpy = px(pc.gx), py(pc.gy)
            pw = pc.w_cells * s
            ph = pc.h_cells * s

            transform = f"translate({cpx},{cpy})"
            if pc.w_cells != 1.0 or pc.h_cells != 1.0:
                transform += f" scale({pc.w_cells},{pc.h_cells})"
            if pc.orientation != 0:
                half = s / 2
                transform += f" rotate({pc.orientation},{half},{half})"

            elements.append(f'<g transform="{transform}">{body}</g>')

            if pc.label:
                if pc.orientation in (90, 270):
                    box_w, box_h = ph, pw
                else:
                    box_w, box_h = pw, ph
                lx, ly, anch = self._label_anchor(
                    cpx, cpy, box_w, box_h, pc.label_pos
                )
                elements.append(self._svg_text(lx, ly, pc.label, st, anch))

        # 4. Junction dots (top layer)
        for d in self._dots:
            elements.append(
                f'<circle cx="{px(d.gx)}" cy="{py(d.gy)}" r="3.5"'
                f' fill="{st.stroke_color}"/>'
            )

        # 5. Free labels
        for fl in self._labels:
            elements.append(
                self._svg_text(px(fl.gx), py(fl.gy), fl.text, st, fl.anchor)
            )

        body_str = "\n  ".join(elements)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg"'
            f' width="{self._w}" height="{self._h}"'
            f' viewBox="0 0 {self._w} {self._h}">\n'
            f'  <style>text {{ font-family: monospace; }}</style>\n'
            f'  {body_str}\n'
            f'</svg>'
        )

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _label_anchor(
        cpx: float, cpy: float, pw: float, ph: float, pos: str
    ) -> tuple[float, float, str]:
        if pos == "above":
            return cpx + pw / 2, cpy - 6, "middle"
        if pos == "left":
            return cpx - 6, cpy + ph / 2 + 4, "end"
        if pos == "right":
            return cpx + pw + 6, cpy + ph / 2 + 4, "start"
        # below (default)
        return cpx + pw / 2, cpy + ph + 14, "middle"

    @staticmethod
    def _svg_text(
        x: float, y: float, text: str, style, anchor: str = "middle"
    ) -> str:
        safe_text = escape(str(text))
        return (
            f'<text x="{x}" y="{y}" text-anchor="{anchor}"'
            f' font-family="{style.font_family}"'
            f' font-size="{style.font_size}"'
            f' fill="{style.label_color}">{safe_text}</text>'
        )
