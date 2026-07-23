
from ..components import (
    CircuitBreaker, Differential, FVGenerator, Ground,
    GridSymbol, Meter, SurgeArrester, ZeroInjection,
)
from ..core.config import ACConfig, DiagramStyle
from ..core.diagram import Diagram

R_GRID   = 0
R_METER  = 1.5
R_ICP    = 3.0
R_IGA    = 4.5
R_ZI     = 6.0
R_LOADS  = 7.5
R_GND    = 9.0

R_PV_GEN  = 0
R_PV_MCB1 = 1.5
R_PV_LDIF = 3.0
R_PV_MCB2 = 4.5

JUNCTION_Y = R_IGA + 1

BUS_MAIN = 1.5
BUS_PV   = 3.5
SPD_X    = 5.0


class GridConnectionDiagram:

    def __init__(self, config: ACConfig, style: DiagramStyle):
        self.cfg = config
        self.style = style

    def render(self) -> str:
        cfg = self.cfg

        d = Diagram(cols=6.5, rows=R_GND + 1.5, style=self.style)

        d.box(0.8, R_ICP - 0.2, 2.3, R_IGA + 1.2, title="CGMP")

        d.box(2.7, R_PV_GEN - 0.2, 5.8, R_PV_MCB2 + 1.2,
              title="GENERADOR FOTOVOLTAICO")

        d.place(GridSymbol(), 1, R_GRID,
                voltage="1N 230VAC", frequency="50Hz  TT")
        d.wire(BUS_MAIN, R_GRID + 1.0, BUS_MAIN, R_METER)

        d.place(Meter(), 1, R_METER, orientation=90,
                label="Contador Bidireccional", label_pos="right")
        d.wire(BUS_MAIN, R_METER + 1, BUS_MAIN, R_ICP)

        d.place(CircuitBreaker(), 1, R_ICP, orientation=90,
                label="ICP", label_pos="right")
        d.wire(BUS_MAIN, R_ICP + 1, BUS_MAIN, R_IGA)

        d.place(CircuitBreaker(), 1, R_IGA, orientation=90,
                label="IGA", label_pos="right")
        d.dot(BUS_MAIN, JUNCTION_Y)
        d.wire(BUS_MAIN, JUNCTION_Y, BUS_MAIN, R_ZI)

        if cfg.has_zero_injection:
            d.place(ZeroInjection(), 1, R_ZI, orientation=90,
                    label_pos="right",
                    model=cfg.zero_injection_model or "")
            d.wire(BUS_MAIN, R_ZI + 1, BUS_MAIN, R_LOADS)
        else:
            d.wire(BUS_MAIN, R_ZI, BUS_MAIN, R_LOADS)

        d.wire(BUS_MAIN, R_LOADS, BUS_MAIN, R_LOADS + 0.5)
        d.label(BUS_MAIN + 0.15, R_LOADS + 0.35, "Circuito vivienda existente",
                anchor="start")
        d.wire(BUS_MAIN, R_LOADS + 0.5, BUS_MAIN, R_GND)

        d.place(Ground(), 1, R_GND, label="PE")

        d.place(FVGenerator(), 3, R_PV_GEN, label="")
        d.wire(BUS_PV, R_PV_GEN + 1.0, BUS_PV, R_PV_MCB1)

        d.place(CircuitBreaker(), 3, R_PV_MCB1, orientation=90,
                label="I.MAG CC", label_pos="right")
        d.wire(BUS_PV, R_PV_MCB1 + 1, BUS_PV, R_PV_LDIF)

        d.place(Differential(), 3, R_PV_LDIF, orientation=90,
                label=f"LDIF II  {cfg.rcd_i:.0f}A {cfg.rcd_sensitivity}",
                label_pos="right")
        d.wire(BUS_PV, R_PV_LDIF + 1, BUS_PV, R_PV_MCB2)

        spd_tap = R_PV_MCB2 - 0.25
        d.dot(BUS_PV, spd_tap)
        d.wire(BUS_PV, spd_tap, SPD_X, spd_tap)
        d.place(SurgeArrester(), 4.5, spd_tap, label="SPD", label_pos="right")
        d.wire(SPD_X, spd_tap + 1, SPD_X, spd_tap + 1.5)
        d.place(Ground(), 4.5, spd_tap + 1.5, label="PE")

        d.place(CircuitBreaker(), 3, R_PV_MCB2, orientation=90,
                label=f"I.MAG  {cfg.mcb_i:.0f}A", label_pos="right")

        d.wire(BUS_PV, R_PV_MCB2 + 1, BUS_PV, JUNCTION_Y)
        d.wire(BUS_PV, JUNCTION_Y, BUS_MAIN, JUNCTION_Y)
        d.label((BUS_MAIN + BUS_PV) / 2, JUNCTION_Y - 0.12, cfg.cable_section)

        return d.render()
