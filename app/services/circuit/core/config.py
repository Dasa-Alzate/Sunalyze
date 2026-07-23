
from dataclasses import dataclass, field


@dataclass
class DiagramStyle:
    stroke_color: str = "#131316"
    stroke_width: float = 1.5
    font_family: str = "monospace"
    font_size: int = 10
    label_color: str = "#444444"

    CELL: int = 120


@dataclass
class DCConfig:
    panel_model: str
    panel_voc: float
    panel_isc: float
    panels_per_string: int
    num_strings: int
    fuse_i: float
    switch_v: float
    cable_section: str
    has_fuses: bool = True


@dataclass
class ACConfig:
    inverter_model: str
    inverter_power: float
    inverter_output_i: float
    phases: int
    mcb_i: float
    rcd_i: float
    rcd_sensitivity: str
    cable_section: str
    has_zero_injection: bool = False
    zero_injection_model: str = ""
    has_battery: bool = False
    battery_model: str = ""


@dataclass
class SystemConfig:
    dc: DCConfig
    ac: ACConfig
    style: DiagramStyle = field(default_factory=DiagramStyle)
