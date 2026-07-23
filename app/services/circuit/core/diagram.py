
from dataclasses import dataclass, field
from xml.sax.saxutils import escape

from .box_area import BoxArea
from .config import DiagramStyle
from .geometry import CELL as _CELL, transform_ports
from .wire import Wire


@dataclass
class _PlacedComponent:
    component: object
    gx: float
    gy: float
    orientation: int = 0
    label: str = ""
    label_pos: str = "below"
    kwargs: dict = field(default_factory=dict)
    w_cells: float = 1.0
    h_cells: float = 1.0


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

    def __init__(
        self,
        cols: float,
        rows: float,
        style: DiagramStyle | None = None,
        padding: int = 20,
    ):
        self.style = style or DiagramStyle()
        self._C = self.style.CELL
        self._pad = padding
        self._w = int(cols * self._C + 2 * padding)
        self._h = int(rows * self._C + 2 * padding)

        self._comps:  list[_PlacedComponent] = []
        self._wires:  list[Wire]             = []
        self._boxes:  list[BoxArea]          = []
        self._dots:   list[_Dot]             = []
        self._labels: list[_FreeLabel]       = []

    def place(
        self,
        component,
        gx: float,
        gy: float,
        orientation: int = 0,
        label: str = "",
        label_pos: str = "below",
        **kwargs,
    ) -> "_PlacedComponent":
        pc = _PlacedComponent(
            component, gx, gy, orientation, label, label_pos, kwargs
        )
        self._comps.append(pc)
        return pc

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
    ) -> "_PlacedComponent":
        pc = _PlacedComponent(
            component, gx, gy, 0, label, label_pos, kwargs, w_cells, h_cells
        )
        self._comps.append(pc)
        return pc

    def wire(self, x1: float, y1: float, x2: float, y2: float) -> "Diagram":
        self._wires.append(Wire(x1, y1, x2, y2))
        return self

    def dot(self, gx: float, gy: float) -> "Diagram":
        self._dots.append(_Dot(gx, gy))
        return self

    def box(
        self, x1: float, y1: float, x2: float, y2: float, title: str = ""
    ) -> "Diagram":
        self._boxes.append(BoxArea(x1, y1, x2, y2, title))
        return self

    def label(
        self, gx: float, gy: float, text: str, anchor: str = "middle"
    ) -> "Diagram":
        self._labels.append(_FreeLabel(gx, gy, text, anchor))
        return self

    def port(self, placement: "_PlacedComponent", name: str) -> tuple[float, float]:
        comp = placement.component
        try:
            local = comp.connection_points(placement.orientation)
        except AttributeError:
            local = transform_ports(getattr(comp, "PORTS", {}), placement.orientation)
        if name not in local:
            raise KeyError(
                f"{type(comp).__name__} has no port '{name}'; available: {sorted(local)}"
            )
        lx, ly = local[name]
        gx = placement.gx + (lx / _CELL) * placement.w_cells
        gy = placement.gy + (ly / _CELL) * placement.h_cells
        return gx, gy

    def connect(
        self,
        placement_a: "_PlacedComponent",
        port_a: str,
        placement_b: "_PlacedComponent",
        port_b: str,
    ) -> "Diagram":
        x1, y1 = self.port(placement_a, port_a)
        x2, y2 = self.port(placement_b, port_b)
        self._wires.append(Wire(x1, y1, x2, y2))
        return self

    def render(self) -> str:
        s = self._C
        p = self._pad
        st = self.style
        elements: list[str] = []

        def px(gx: float) -> float:
            return gx * s + p

        def py(gy: float) -> float:
            return gy * s + p

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

        for w in self._wires:
            elements.append(
                f'<line x1="{px(w.x1)}" y1="{py(w.y1)}"'
                f' x2="{px(w.x2)}" y2="{py(w.y2)}"'
                f' stroke="{st.stroke_color}"'
                f' stroke-width="{st.stroke_width}" fill="none"/>'
            )

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

        for d in self._dots:
            elements.append(
                f'<circle cx="{px(d.gx)}" cy="{py(d.gy)}" r="3.5"'
                f' fill="{st.stroke_color}"/>'
            )

        for fl in self._labels:
            elements.append(
                self._svg_text(px(fl.gx), py(fl.gy), fl.text, st, fl.anchor)
            )

        fs = st.font_size
        xs = [0.0, float(self._w)]
        ys = [0.0, float(self._h)]

        def acc(x, y):
            xs.append(x)
            ys.append(y)

        for ba in self._boxes:
            acc(px(ba.x1), py(ba.y1))
            acc(px(ba.x2), py(ba.y2))
        for w in self._wires:
            acc(px(w.x1), py(w.y1))
            acc(px(w.x2), py(w.y2))
        for d in self._dots:
            acc(px(d.gx), py(d.gy))
        for fl in self._labels:
            half = len(str(fl.text)) * fs * 0.62 / 2
            acc(px(fl.gx) - half, py(fl.gy) - fs)
            acc(px(fl.gx) + half, py(fl.gy))
        for pc in self._comps:
            cpx, cpy = px(pc.gx), py(pc.gy)
            pw, ph = pc.w_cells * s, pc.h_cells * s
            acc(cpx, cpy)
            acc(cpx + pw, cpy + ph)
            if pc.label:
                box_w, box_h = (ph, pw) if pc.orientation in (90, 270) else (pw, ph)
                lx, ly, anch = self._label_anchor(cpx, cpy, box_w, box_h, pc.label_pos)
                tw = len(str(pc.label)) * fs * 0.62
                if anch == "start":
                    acc(lx + tw, ly)
                elif anch == "end":
                    acc(lx - tw, ly)
                else:
                    acc(lx - tw / 2, ly)
                    acc(lx + tw / 2, ly)
                acc(lx, ly)

        margin = 10.0
        vb_x = round(min(xs) - margin, 1)
        vb_y = round(min(ys) - margin, 1)
        vb_w = round(max(xs) - vb_x + margin, 1)
        vb_h = round(max(ys) - vb_y + margin, 1)

        body_str = "\n  ".join(elements)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg"'
            f' width="{vb_w}" height="{vb_h}"'
            f' viewBox="{vb_x} {vb_y} {vb_w} {vb_h}">\n'
            f'  <style>text {{ font-family: monospace; }}</style>\n'
            f'  {body_str}\n'
            f'</svg>'
        )

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
