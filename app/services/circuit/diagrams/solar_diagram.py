
from ..components import (
    Battery, CircuitBreaker, FVGenerator, Fuse, Ground, Inverter, Switch,
)
from ..core.config import DiagramStyle, SystemConfig
from ..core.diagram import Diagram


class SolarDiagram:

    def __init__(
        self,
        config: SystemConfig,
        has_fuses: bool = True,
        has_battery: bool = False,
    ):
        self.cfg = config
        self.has_fuses = has_fuses
        self.has_battery = has_battery

    def render(self) -> str:
        dc = self.cfg.dc
        ac = self.cfg.ac
        style = self.cfg.style or DiagramStyle()

        chain = [("gen", FVGenerator(), 0, "", "below",
                  {"sublabel": f"{dc.num_strings}x{dc.panels_per_string}p"})]
        if self.has_fuses:
            chain.append(("fuse", Fuse(), 90, f"Fusible  {dc.fuse_i:.1f} A", "right", {}))
        chain.append(("mcb", CircuitBreaker(), 90, "I.Magnet. CC", "right", {}))
        chain.append(("switch", Switch(), 90, "Seccionador CC", "right", {}))
        chain.append(("inv", Inverter(), 0,
                      ac.inverter_model[:14] or "Inversor", "right", {}))
        chain.append(("gnd", Ground(), 0, "Tierra general", "below", {}))

        step = 1.5
        last = len(chain) - 1
        gnd_gap = 1.5 if self.has_battery else 0.0

        def gy_of(i):
            return i * step + (gnd_gap if i == last else 0.0)

        body_rows = gy_of(last) + 1.4
        total_rows = body_rows + 0.6

        d = Diagram(cols=4, rows=total_rows, style=style)
        d.box(0, 0, 4, body_rows)

        BUS = 1.5
        placements = {}
        for i, (key, comp, orient, label, lpos, kw) in enumerate(chain):
            placements[key] = d.place(
                comp, 1, gy_of(i), orientation=orient,
                label=label, label_pos=lpos, **kw,
            )

        for i in range(last):
            d.wire(BUS, gy_of(i) + 1.0, BUS, gy_of(i + 1))

        if self.has_battery:
            inv = placements["inv"]
            _, by = d.port(inv, "ac_out")
            y_split = by + 0.7
            y_bat = y_split + 0.9
            d.dot(BUS, y_split)
            d.wire(BUS, y_split, 3.0, y_split)
            d.wire(3.0, y_split, 3.0, y_bat)
            d.place_scaled(
                Battery(), 2.5, y_bat, 1.0, 1.0,
                label=(ac.battery_model[:14] or "Bateria"), label_pos="below",
            )

        d.label(BUS + 0.1, step * 0.75, dc.cable_section, anchor="start")
        return d.render()
