"""
Grid connection diagram (esquema de conexión a red).

Grid layout
───────────
Main AC bus:  column 1, centre x = 1.5  (flows top → bottom)
PV branch:    column 3, centre x = 3.5  (flows top → bottom)
SPD branch:   column 4.5 (side tap off PV branch)

Junction between buses: horizontal wire at y = R_IGA + 1  (IGA bottom = PV MCB bottom)
"""

from ..components import (
    CircuitBreaker, Differential, FVGenerator, Ground,
    GridSymbol, Meter, SurgeArrester, ZeroInjection,
)
from ..core.config import ACConfig, DiagramStyle
from ..core.diagram import Diagram

# Row anchors — main bus
R_GRID   = 0      # GridSymbol
R_METER  = 1.5    # Bidirectional meter
R_ICP    = 3.0    # ICP breaker
R_IGA    = 4.5    # IGA breaker — junction row with PV branch
R_ZI     = 6.0    # Zero-injection device
R_LOADS  = 7.5    # Arrow → house loads
R_GND    = 9.0    # Ground

# Row anchors — PV branch (same junction row as IGA)
R_PV_GEN  = 0      # FVGenerator
R_PV_MCB1 = 1.5    # I.MAG CC
R_PV_LDIF = 3.0    # LDIF II differential
R_PV_MCB2 = 4.5    # I.MAG output — bottom lands at R_IGA + 1 = 5.5

# Junction y (IGA bottom = PV MCB2 bottom)
JUNCTION_Y = R_IGA + 1  # = 5.5

BUS_MAIN = 1.5
BUS_PV   = 3.5
SPD_X    = 5.0    # SPD side-branch centre x (placed at col 4.5)


class GridConnectionDiagram:

    def __init__(self, config: ACConfig, style: DiagramStyle):
        self.cfg = config
        self.style = style

    def render(self) -> str:
        cfg = self.cfg

        d = Diagram(cols=6.5, rows=R_GND + 1.5, style=self.style)

        # ── CGMP section box ──────────────────────────────────────────────
        d.box(0.8, R_ICP - 0.2, 2.3, R_IGA + 1.2, title="CGMP")

        # ── PV branch section box ─────────────────────────────────────────
        d.box(2.7, R_PV_GEN - 0.2, 5.8, R_PV_MCB2 + 1.2,
              title="GENERADOR FOTOVOLTAICO")

        # ── Main bus: GridSymbol ──────────────────────────────────────────
        d.place(GridSymbol(), 1, R_GRID,
                voltage="1N 230VAC", frequency="50Hz  TT")
        # GridSymbol visual bottom at y=74/120 ≈ 0.62 of cell → wire from row 1.0
        d.wire(BUS_MAIN, R_GRID + 1.0, BUS_MAIN, R_METER)

        # ── Meter ─────────────────────────────────────────────────────────
        d.place(Meter(), 1, R_METER, orientation=90,
                label="Contador Bidireccional", label_pos="right")
        d.wire(BUS_MAIN, R_METER + 1, BUS_MAIN, R_ICP)

        # ── ICP ───────────────────────────────────────────────────────────
        d.place(CircuitBreaker(), 1, R_ICP, orientation=90,
                label="ICP", label_pos="right")
        d.wire(BUS_MAIN, R_ICP + 1, BUS_MAIN, R_IGA)

        # ── IGA ───────────────────────────────────────────────────────────
        d.place(CircuitBreaker(), 1, R_IGA, orientation=90,
                label="IGA", label_pos="right")
        # Junction dot at IGA bottom (= PV branch connection point)
        d.dot(BUS_MAIN, JUNCTION_Y)
        d.wire(BUS_MAIN, JUNCTION_Y, BUS_MAIN, R_ZI)

        # ── Zero-injection device (optional) ─────────────────────────────
        if cfg.has_zero_injection:
            d.place(ZeroInjection(), 1, R_ZI, orientation=90,
                    label_pos="right",
                    model=cfg.zero_injection_model or "")
            d.wire(BUS_MAIN, R_ZI + 1, BUS_MAIN, R_LOADS)
        else:
            d.wire(BUS_MAIN, R_ZI, BUS_MAIN, R_LOADS)

        # ── Arrow → house loads ───────────────────────────────────────────
        d.wire(BUS_MAIN, R_LOADS, BUS_MAIN, R_LOADS + 0.5)
        d.label(BUS_MAIN + 0.15, R_LOADS + 0.35, "Circuito vivienda existente",
                anchor="start")
        d.wire(BUS_MAIN, R_LOADS + 0.5, BUS_MAIN, R_GND)

        # ── Ground ────────────────────────────────────────────────────────
        d.place(Ground(), 1, R_GND, label="PE")

        # ─────────────────────────────────────────────────────────────────
        # PV branch
        # ─────────────────────────────────────────────────────────────────

        # ── FV Generator ─────────────────────────────────────────────────
        d.place(FVGenerator(), 3, R_PV_GEN, label="")
        d.wire(BUS_PV, R_PV_GEN + 1.0, BUS_PV, R_PV_MCB1)

        # ── I.MAG CC (first breaker) ──────────────────────────────────────
        d.place(CircuitBreaker(), 3, R_PV_MCB1, orientation=90,
                label="I.MAG CC", label_pos="right")
        d.wire(BUS_PV, R_PV_MCB1 + 1, BUS_PV, R_PV_LDIF)

        # ── LDIF II (differential) ────────────────────────────────────────
        d.place(Differential(), 3, R_PV_LDIF, orientation=90,
                label=f"LDIF II  {cfg.rcd_i:.0f}A {cfg.rcd_sensitivity}",
                label_pos="right")
        d.wire(BUS_PV, R_PV_LDIF + 1, BUS_PV, R_PV_MCB2)

        # ── I.MAG output (second breaker + SPD tap) ───────────────────────
        d.dot(BUS_PV, R_PV_MCB2)
        # SPD horizontal branch at the top of this breaker
        d.wire(BUS_PV, R_PV_MCB2, SPD_X, R_PV_MCB2)
        d.place(SurgeArrester(), 4.5, R_PV_MCB2, label="SPD", label_pos="right")
        d.wire(SPD_X, R_PV_MCB2 + 1, SPD_X, R_PV_MCB2 + 1.5)
        d.place(Ground(), 4.5, R_PV_MCB2 + 1.5, label="PE")

        d.place(CircuitBreaker(), 3, R_PV_MCB2, orientation=90,
                label=f"I.MAG  {cfg.mcb_i:.0f}A", label_pos="right")

        # ── PV → IGA junction: vertical then horizontal ───────────────────
        d.wire(BUS_PV, R_PV_MCB2 + 1, BUS_PV, JUNCTION_Y)
        d.wire(BUS_PV, JUNCTION_Y, BUS_MAIN, JUNCTION_Y)
        d.label((BUS_MAIN + BUS_PV) / 2, JUNCTION_Y - 0.12, cfg.cable_section)

        return d.render()
