"""
DC strings vertical diagram (esquema unifilar CC — strings → inversor).

Grid layout
───────────
Column 0:        N string groups, one per row.
Column 1 (x=1):  Components on the vertical collection bus.
x=1.5:           Centre of the bus (integer boundary between col 1 and col 2).
Column 2:        SPD side-branch.

Rows 0..N-1:     Strings.
Row N onwards:   Protection chain — Fuse, MCB, SPD tap, Switch, Inverter, Ground.
"""

from ..components import (
    CircuitBreaker, Fuse, Ground, Inverter, StringGroup, Switch,
)
from ..config import DCConfig, DiagramStyle
from ..diagram import Diagram


class DCStringsDiagram:

    def __init__(self, config: DCConfig, style: DiagramStyle):
        self.cfg = config
        self.style = style

    def render(self) -> str:
        cfg = self.cfg
        N = max(1, cfg.num_strings)

        # ── Vertical bus x-coordinate (centre of column 1) ────────────────
        BUS = 1.5

        # ── Component rows below the string bus ───────────────────────────
        R_FUSE   = N + 0.5
        R_MCB    = N + 2.0
        R_SPD    = N + 3.5   # SPD tap level
        R_SWITCH = N + 5.0
        R_INV    = N + 6.5
        R_GND    = N + 8.0

        d = Diagram(cols=4, rows=R_GND + 1.5, style=self.style)

        # ── Dashed outer border ───────────────────────────────────────────
        d.box(0, 0, 4, R_INV + 1.4)

        # ── Strings + horizontal wires to bus ─────────────────────────────
        for i in range(N):
            # String occupies cell (0, i); its right edge is at x=1.0, centre y=i+0.5
            d.place(
                StringGroup(), 0, i,
                index=i + 1,
                panels=cfg.panels_per_string,
                voltage=cfg.panel_voc,
            )
            # Wire: string right edge → bus
            d.wire(1.0, i + 0.5, BUS, i + 0.5)
            d.dot(BUS, i + 0.5)

        # ── Vertical collection bus ───────────────────────────────────────
        if N > 1:
            d.wire(BUS, 0.5, BUS, N - 0.5)

        # Wire from bus bottom to first protection component
        d.wire(BUS, N - 0.5, BUS, R_FUSE)

        # ── Fuse ──────────────────────────────────────────────────────────
        # orientation=90: component rotated CW so left→bottom, right→top
        d.place(Fuse(), 1, R_FUSE, orientation=90,
                label=f"Fusible  {cfg.fuse_i:.1f} A", label_pos="right")
        d.wire(BUS, R_FUSE + 1, BUS, R_MCB)

        # ── Magnetotérmico CC ─────────────────────────────────────────────
        d.place(CircuitBreaker(), 1, R_MCB, orientation=90,
                label=f"I.Magnet. CC  {cfg.switch_v:.0f} V", label_pos="right")
        d.wire(BUS, R_MCB + 1, BUS, R_SPD)

        # ── SPD tap ───────────────────────────────────────────────────────
        d.dot(BUS, R_SPD)
        # Horizontal branch to SPD (placed at column 2, same row)
        d.wire(BUS, R_SPD, 2.5, R_SPD)
        d.wire(2.5, R_SPD, 2.5, R_SPD + 1.1)
        d.place(Ground(), 2, R_SPD + 1, label="PE")

        # Main bus continues after tap
        d.wire(BUS, R_SPD, BUS, R_SWITCH)

        # ── DC Switch ─────────────────────────────────────────────────────
        d.place(Switch(), 1, R_SWITCH, orientation=90,
                label="Seccionador CC", label_pos="right")
        d.wire(BUS, R_SWITCH + 1, BUS, R_INV)

        # ── Inverter ──────────────────────────────────────────────────────
        d.place(Inverter(), 1, R_INV, label_pos="right")
        d.wire(BUS, R_INV + 1, BUS, R_GND)

        # ── Ground ────────────────────────────────────────────────────────
        d.place(Ground(), 1, R_GND, label="Tierra general")

        # ── Cable section annotation ──────────────────────────────────────
        d.label(BUS + 0.1, (R_FUSE + R_MCB) / 2 + 0.5, cfg.cable_section,
                anchor="start")

        return d.render()
