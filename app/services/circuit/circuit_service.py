"""Circuit diagram service — orchestrates DC and AC unifilar generation."""

from .config import SystemConfig, DCConfig, ACConfig, DiagramStyle
from .diagrams import DCStringsDiagram, GridConnectionDiagram, FullSystemDiagram


class CircuitService:
    """
    Generates SVG unifilar diagrams for photovoltaic installations.

    Usage:
        config = CircuitService.config_from_dict(data, style=None)
        svg_cc = CircuitService.generate_cc_vertical(config)
        svg_grid = CircuitService.generate_grid_connection(config)
        svg_full = CircuitService.generate_full_system(config)
    """

    @staticmethod
    def generate_cc_vertical(config: SystemConfig) -> str:
        """DC strings vertical diagram — N strings, fuses, MCB, SPD, inverter top-to-bottom."""
        return DCStringsDiagram(config.dc, config.style).render()

    @staticmethod
    def generate_grid_connection(config: SystemConfig) -> str:
        """Grid connection diagram — PV branch connecting to AC main bus + house."""
        return GridConnectionDiagram(config.ac, config.style).render()

    @staticmethod
    def generate_full_system(config: SystemConfig) -> str:
        """Full system overview — CC panel / inverter / AC panel / house panel."""
        return FullSystemDiagram(config.dc, config.ac, config.style).render()

    @staticmethod
    def config_from_dict(data: dict, style: DiagramStyle | None = None) -> SystemConfig:
        """
        Build a SystemConfig from a flat dictionary (e.g. request.form or JSON).

        Expected keys (all required unless noted):
            panel_model, panel_voc, panel_isc,
            panels_per_string, num_strings,
            dc_fuse_i, dc_switch_v, dc_cable_section,
            inverter_model, inverter_power, inverter_output_i,
            ac_phases, ac_mcb_i, ac_rcd_i, ac_rcd_sensitivity, ac_cable_section,
            ac_has_zero_injection (optional, bool), ac_zero_injection_model (optional)
        """
        def _float(key: str, default: float = 0.0) -> float:
            try:
                return float(data.get(key, default))
            except (ValueError, TypeError):
                return default

        def _int(key: str, default: int = 1) -> int:
            try:
                return int(data.get(key, default))
            except (ValueError, TypeError):
                return default

        dc = DCConfig(
            panel_model=data.get('panel_model', ''),
            panel_voc=_float('panel_voc'),
            panel_isc=_float('panel_isc'),
            panels_per_string=_int('panels_per_string'),
            num_strings=_int('num_strings'),
            fuse_i=_float('dc_fuse_i'),
            switch_v=_float('dc_switch_v'),
            cable_section=data.get('dc_cable_section', ''),
        )

        ac = ACConfig(
            inverter_model=data.get('inverter_model', ''),
            inverter_power=_float('inverter_power'),
            inverter_output_i=_float('inverter_output_i'),
            phases=_int('ac_phases'),
            mcb_i=_float('ac_mcb_i'),
            rcd_i=_float('ac_rcd_i'),
            rcd_sensitivity=data.get('ac_rcd_sensitivity', '30 mA'),
            cable_section=data.get('ac_cable_section', ''),
            has_zero_injection=bool(data.get('ac_has_zero_injection', False)),
            zero_injection_model=data.get('ac_zero_injection_model', ''),
            has_battery=bool(data.get('has_battery', False)),
            battery_model=data.get('battery_model', ''),
        )

        return SystemConfig(dc=dc, ac=ac, style=style or DiagramStyle())
