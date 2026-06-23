"""Configuration dataclasses for circuit diagram generation."""

from dataclasses import dataclass, field


@dataclass
class DiagramStyle:
    """Visual style constants for SVG circuit diagrams."""
    stroke_color: str = "#131316"
    stroke_width: float = 1.5
    font_family: str = "monospace"
    font_size: int = 10
    label_color: str = "#444444"

    # Layout constants (px)
    CELL: int = 120     # Component cell size (each component fits in CELL×CELL)


@dataclass
class DCConfig:
    """Parameters for the DC unifilar diagram."""
    panel_model: str
    panel_voc: float        # V open-circuit per panel
    panel_isc: float        # A short-circuit current per panel
    panels_per_string: int
    num_strings: int
    fuse_i: float           # String fuse current rating (A) — typically Isc × 1.25
    switch_v: float         # DC switch voltage rating (V)
    cable_section: str      # e.g. "6 mm²"
    has_fuses: bool = True


@dataclass
class ACConfig:
    """Parameters for the AC unifilar diagram."""
    inverter_model: str
    inverter_power: float       # kW
    inverter_output_i: float    # A — rated output current
    phases: int                 # 1 or 3
    mcb_i: float                # Magnetotérmico current rating (A)
    rcd_i: float                # Diferencial current rating (A)
    rcd_sensitivity: str        # e.g. "30 mA"
    cable_section: str          # e.g. "6 mm²"
    has_zero_injection: bool = False
    zero_injection_model: str = ""
    has_battery: bool = False
    battery_model: str = ""


@dataclass
class SystemConfig:
    """Full system configuration for both diagrams."""
    dc: DCConfig
    ac: ACConfig
    style: DiagramStyle = field(default_factory=DiagramStyle)
