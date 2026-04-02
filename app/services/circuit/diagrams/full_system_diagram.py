"""
Full system overview diagram (esquema general).

Grid layout (3 vertical sections, left → right)
────────────────────────────────────────────────
Col 0–3:   DC protection box  (strings + fuses + SPDs)
Col 4–5:   Inverter (2×3 cells, scaled)
Col 6–9:   AC protection box + House distribution box
"""

from ..components import (
    CircuitBreaker, Differential, Fuse, Ground, Inverter, Meter, SurgeArrester,
)
from ..config import ACConfig, DCConfig, DiagramStyle
from ..diagram import Diagram


class FullSystemDiagram:

    def __init__(self, dc: DCConfig, ac: ACConfig, style: DiagramStyle):
        self.dc = dc
        self.ac = ac
        self.style = style

    def render(self) -> str:
        dc = self.dc
        ac = self.ac
        N = dc.num_strings

        # Row height per string inside the DC box (min 0.5, max 1.0 cells)
        str_step = max(0.5, min(1.0, 5.0 / N))
        dc_rows  = N * str_step           # total rows used by strings
        y_dc_bus = dc_rows / 2 + 0.25    # mid-height bus exit row
        y_ac_bus = y_dc_bus - 0.3

        TOTAL_ROWS = max(dc_rows + 1.5, 7.0)

        d = Diagram(cols=11.0, rows=TOTAL_ROWS, style=self.style)

        # ── DC protection box ─────────────────────────────────────────────
        d.box(0.1, 0.1, 3.9, dc_rows + 0.5, title="CUADRO PROTECCIÓN CC")

        for i in range(N):
            row = i * str_step
            d.label(0.2, row + str_step * 0.4,
                    f"#{i + 1} String  {dc.panels_per_string}p", anchor="start")
            d.wire(1.0, row + str_step * 0.5, 1.5, row + str_step * 0.5)
            d.place_scaled(Fuse(), 1.5, row, 1.0, str_step,
                           label=f"{dc.fuse_i:.0f}A", label_pos="below")
            d.wire(2.5, row + str_step * 0.5, 3.5, row + str_step * 0.5)
            d.dot(3.5, row + str_step * 0.5)

        # Vertical collection bus inside DC box
        d.wire(3.5, str_step * 0.5, 3.5, dc_rows - str_step * 0.5)
        # Exit wire from DC box to inverter
        d.wire(3.5, y_dc_bus, 4.0, y_dc_bus)

        # SPDs inside DC box
        for j, spd_label in enumerate(["SPD CC 1", "SPD CC 2"]):
            sx = 0.5 + j * 1.5
            d.place_scaled(SurgeArrester(), sx, dc_rows, 0.8, 1.0,
                           label=spd_label, label_pos="below")

        # ── Inverter (2 cols × 3 rows, scaled) ───────────────────────────
        d.place_scaled(Inverter(), 4, y_dc_bus - 1.5, 2.0, 3.0,
                       label=ac.inverter_model[:14], label_pos="below")
        d.wire(6.0, y_ac_bus, 6.5, y_ac_bus)

        # ── AC protection box ─────────────────────────────────────────────
        d.box(6.4, 0.1, 9.9, 3.2, title="CUADRO PROTECCIÓN AC")

        d.wire(6.5, y_ac_bus, 6.5, 0.6)
        d.wire(6.5, 0.6, 7.0, 0.6)
        d.place(CircuitBreaker(), 7.0, 0.1,
                label=f"MCB {ac.mcb_i:.0f}A", label_pos="below")
        d.wire(8.0, 0.6, 8.5, 0.6)
        d.place(Differential(), 8.5, 0.1,
                label=f"ID {ac.rcd_i:.0f}A",
                label_pos="below",
                sensitivity=ac.rcd_sensitivity)
        d.wire(9.5, 0.6, 9.8, 0.6)

        d.place_scaled(SurgeArrester(), 7.0, 1.5, 0.8, 1.0,
                       label="SPD CA", label_pos="below")
        d.place(CircuitBreaker(), 8.5, 1.5,
                label=f"MCB {ac.mcb_i:.0f}A", label_pos="below")

        # ── House distribution box ────────────────────────────────────────
        d.box(6.4, 3.5, 10.6, 6.5, title="CUADRO CASA")

        d.wire(8.2, 3.2, 8.2, 3.5)

        for k, lbl in enumerate(["MCB", "MCB", "ID", "kWh"]):
            d.place(CircuitBreaker() if lbl in ("MCB", "ID") else Meter(),
                    6.5 + k * 1.0, 3.7, label=lbl, label_pos="below")
            d.wire(6.5 + k * 1.0 + 0.5, 4.7, 6.5 + k * 1.0 + 0.5, 5.2)
            d.label(6.5 + k * 1.0 + 0.5, 5.5, "Cargas")

        # ── Ground ────────────────────────────────────────────────────────
        d.wire(2.0, dc_rows + 1.0, 2.0, TOTAL_ROWS - 0.5)
        d.place(Ground(), 1.5, TOTAL_ROWS - 1.0, label="Toma de tierra")

        # ── Cable section annotations ─────────────────────────────────────
        d.label(3.7, y_dc_bus - 0.15, dc.cable_section, anchor="start")
        d.label(6.2, y_ac_bus - 0.15, ac.cable_section, anchor="end")

        return d.render()
