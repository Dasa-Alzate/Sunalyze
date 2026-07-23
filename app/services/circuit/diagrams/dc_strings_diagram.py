
from ..components import (
    CircuitBreaker, Fuse, Ground, Inverter, StringGroup, Switch,
)
from ..core.config import DCConfig, DiagramStyle
from ..core.diagram import Diagram


class DCStringsDiagram:

    def __init__(self, config: DCConfig, style: DiagramStyle):
        self.cfg = config
        self.style = style

    def render(self) -> str:
        cfg = self.cfg
        N = max(1, cfg.num_strings)

        BUS = 1.5

        R_FUSE   = N + 0.5
        R_MCB    = N + 2.0
        R_SPD    = N + 3.5
        R_SWITCH = N + 5.0
        R_INV    = N + 6.5
        R_GND    = N + 8.0

        d = Diagram(cols=4, rows=R_GND + 1.5, style=self.style)

        d.box(0, 0, 4, R_GND + 1.4)

        for i in range(N):
            d.place(
                StringGroup(), 0, i,
                index=i + 1,
                panels=cfg.panels_per_string,
                voltage=cfg.panel_voc,
            )
            d.wire(1.0, i + 0.5, BUS, i + 0.5)
            d.dot(BUS, i + 0.5)

        if N > 1:
            d.wire(BUS, 0.5, BUS, N - 0.5)

        d.wire(BUS, N - 0.5, BUS, R_FUSE)

        d.place(Fuse(), 1, R_FUSE, orientation=90,
                label=f"Fusible  {cfg.fuse_i:.1f} A", label_pos="right")
        d.wire(BUS, R_FUSE + 1, BUS, R_MCB)

        d.place(CircuitBreaker(), 1, R_MCB, orientation=90,
                label=f"I.Magnet. CC  {cfg.switch_v:.0f} V", label_pos="right")
        d.wire(BUS, R_MCB + 1, BUS, R_SPD)

        d.dot(BUS, R_SPD)
        d.wire(BUS, R_SPD, 2.5, R_SPD)
        d.wire(2.5, R_SPD, 2.5, R_SPD + 1.1)
        d.place(Ground(), 2, R_SPD + 1, label="PE")

        d.wire(BUS, R_SPD, BUS, R_SWITCH)

        d.place(Switch(), 1, R_SWITCH, orientation=90,
                label="Seccionador CC", label_pos="right")
        d.wire(BUS, R_SWITCH + 1, BUS, R_INV)

        d.place(Inverter(), 1, R_INV, label_pos="right")
        d.wire(BUS, R_INV + 1, BUS, R_GND)

        d.place(Ground(), 1, R_GND, label="Tierra general")

        d.label(BUS + 0.1, (R_FUSE + R_MCB) / 2 + 0.5, cfg.cable_section,
                anchor="start")

        return d.render()
