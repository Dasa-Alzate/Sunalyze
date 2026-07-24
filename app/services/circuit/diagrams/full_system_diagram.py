
from ..components import (
    Battery, CircuitBreaker, Differential, Fuse, Ground, GridSymbol,
    Inverter, Meter, SurgeArrester,
)
from ..core.config import ACConfig, DCConfig, DiagramStyle
from ..core.diagram import Diagram


class FullSystemDiagram:
    """Esquema general CA/CC de una instalación de autoconsumo.

    Flujo de izquierda a derecha: campo fotovoltaico → cuadro de protección CC
    (fusibles por string + SPD tapeado al bus) → inversor → cuadro de protección
    CA (magnetotérmico + SPD tapeado) → cuadro de la vivienda (contador
    bidireccional hacia red, diferencial y salida a cargas). Todos los símbolos
    quedan conectados a la línea y contenidos dentro de su cuadro.
    """

    def __init__(self, dc: DCConfig, ac: ACConfig, style: DiagramStyle):
        self.dc = dc
        self.ac = ac
        self.style = style

    def render(self) -> str:
        dc = self.dc
        ac = self.ac
        N = max(1, dc.num_strings)

        step = 1.0
        row0 = 0.7
        rows = [row0 + i * step for i in range(N)]
        last = rows[-1]
        y_dc = (row0 + last) / 2

        bus_x = 3.4
        y_spd_cc = last + 1.15
        dc_box_bottom = y_spd_cc + 1.5

        d = Diagram(cols=13.0, rows=max(dc_box_bottom + 0.4, 6.5), style=self.style)

        d.box(0.1, 0.1, 4.4, dc_box_bottom, title="CUADRO PROTECCIÓN CC")

        for i, row in enumerate(rows):
            yc = row + 0.5
            d.label(0.25, yc - 0.06,
                    f"String #{i + 1} · {dc.panels_per_string}p", anchor="start")
            d.wire(0.9, yc, 1.4, yc)
            d.place(Fuse(), 1.4, row, label=f"{dc.fuse_i:.0f}A", label_pos="above")
            d.wire(2.4, yc, bus_x, yc)
            d.dot(bus_x, yc)

        d.wire(bus_x, rows[0] + 0.5, bus_x, last + 0.5)

        d.dot(bus_x, y_dc)
        d.wire(bus_x, y_dc, 4.7, y_dc)

        d.wire(bus_x, last + 0.5, bus_x, y_spd_cc)
        d.place(SurgeArrester(), bus_x - 0.5, y_spd_cc, label="SPD CC", label_pos="right")

        d.place_scaled(Inverter(), 4.7, y_dc - 1.1, 1.8, 2.2,
                       label=ac.inverter_model[:16], label_pos="below")
        inv_right = 4.7 + 1.8

        if ac.has_battery:
            y_bat = dc_box_bottom + 0.4
            d.dot(bus_x, y_dc)
            d.wire(4.7, y_dc + 0.7, 4.7, y_bat)
            d.wire(4.7, y_bat, 5.2, y_bat)
            d.place_scaled(Battery(), 5.2, y_bat - 0.5, 1.4, 1.4,
                           label=(ac.battery_model[:14] or "Batería"), label_pos="below")

        d.wire(inv_right, y_dc, 7.0, y_dc)

        ac_box_top = y_dc - 1.2
        ac_box_bottom = y_dc + 1.9
        d.box(6.7, ac_box_top, 9.5, ac_box_bottom, title="CUADRO PROTECCIÓN AC")

        d.place(CircuitBreaker(), 7.0, y_dc - 0.5,
                label=f"MCB {ac.mcb_i:.0f}A", label_pos="above")
        d.wire(8.0, y_dc, 9.5, y_dc)

        spd_ac_x = 8.6
        d.dot(spd_ac_x, y_dc)
        d.wire(spd_ac_x, y_dc, spd_ac_x, y_dc + 0.85)
        d.place(SurgeArrester(), spd_ac_x - 0.5, y_dc + 0.85, label="SPD CA", label_pos="right")

        house_bus = 10.6
        d.wire(9.5, y_dc, house_bus, y_dc)
        d.dot(house_bus, y_dc)

        house_top = y_dc - 2.6
        house_bottom = y_dc + 2.9
        d.box(9.9, house_top, 12.9, house_bottom, title="CUADRO VIVIENDA")

        d.place(GridSymbol(), house_bus - 0.5, house_top + 0.1,
                voltage="RED", frequency=f"{'3F' if ac.phases == 3 else '1F'} 230/400V")
        d.wire(house_bus, house_top + 1.2, house_bus, y_dc - 1.5)
        d.place(Meter(), house_bus - 0.5, y_dc - 1.5,
                label="Contador bidireccional", label_pos="right")
        d.wire(house_bus, y_dc - 0.5, house_bus, y_dc)

        d.wire(house_bus, y_dc, house_bus, y_dc + 0.6)
        d.place(Differential(), house_bus - 0.5, y_dc + 0.6,
                label=f"ID {ac.rcd_i:.0f}A", label_pos="right",
                sensitivity=ac.rcd_sensitivity)
        d.wire(house_bus, y_dc + 1.6, house_bus, y_dc + 2.2)
        d.label(house_bus, y_dc + 2.45, "Cargas vivienda")

        d.wire(2.0, dc_box_bottom, 2.0, dc_box_bottom + 0.9)
        d.place(Ground(), 1.5, dc_box_bottom + 0.9, label="Toma de tierra")

        d.label(bus_x + 0.15, y_dc - 0.12, dc.cable_section, anchor="start")
        d.label((inv_right + 7.0) / 2, y_dc - 0.12, ac.cable_section)

        return d.render()
