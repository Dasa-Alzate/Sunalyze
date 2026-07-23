
from .core.config import SystemConfig, DCConfig, ACConfig, DiagramStyle
from .core.plan_sheet import wrap_plan_sheet, fit_to_mm
from .diagrams import DCStringsDiagram, GridConnectionDiagram, FullSystemDiagram
from .diagrams.registry import (
    TEMPLATES, list_templates, render_template, template_label, template_orientation,
)


class CircuitService:

    @staticmethod
    def generate_cc_vertical(config: SystemConfig) -> str:
        return DCStringsDiagram(config.dc, config.style).render()

    @staticmethod
    def generate_grid_connection(config: SystemConfig) -> str:
        return GridConnectionDiagram(config.ac, config.style).render()

    @staticmethod
    def generate_full_system(config: SystemConfig) -> str:
        return FullSystemDiagram(config.dc, config.ac, config.style).render()

    @staticmethod
    def list_templates() -> list[dict]:
        return list_templates()

    @staticmethod
    def generate_template(name: str, config: SystemConfig) -> str:
        return render_template(name, config)

    @staticmethod
    def has_template(name: str) -> bool:
        return name in TEMPLATES

    @staticmethod
    def wrap_sheet(svg: str, name: str, title: str = '', fields=None) -> str:
        return wrap_plan_sheet(
            svg,
            title=title or template_label(name).upper(),
            orientation=template_orientation(name),
            fields=fields,
        )

    @staticmethod
    def fit_to_mm(svg: str, max_w_mm: float, max_h_mm: float) -> str:
        return fit_to_mm(svg, max_w_mm, max_h_mm)

    @staticmethod
    def config_from_dict(data: dict, style: DiagramStyle | None = None) -> SystemConfig:
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
            has_fuses=str(data.get('has_fuses', 'true')).strip().lower()
            not in ('false', '0', 'no', ''),
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
