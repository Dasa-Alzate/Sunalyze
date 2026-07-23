
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CircuitConfigSchema(BaseModel):
    panel_model: Optional[str] = Field(default=None, min_length=1, max_length=120)
    panel_voc: Optional[float] = Field(default=None, gt=0, le=2000)
    panel_isc: Optional[float] = Field(default=None, gt=0, le=500)
    panels_per_string: Optional[int] = Field(default=None, ge=1, le=100)
    num_strings: Optional[int] = Field(default=None, ge=1, le=100)
    dc_fuse_i: Optional[float] = Field(default=None, gt=0, le=500)
    dc_switch_v: Optional[float] = Field(default=None, gt=0, le=2000)
    dc_cable_section: Optional[str] = Field(default=None, min_length=1, max_length=120)
    inverter_model: Optional[str] = Field(default=None, min_length=1, max_length=120)
    inverter_power: Optional[float] = Field(default=None, gt=0, le=10000)
    inverter_output_i: Optional[float] = Field(default=None, gt=0, le=2000)
    ac_phases: Optional[int] = None
    ac_mcb_i: Optional[float] = Field(default=None, gt=0, le=2000)
    ac_rcd_i: Optional[float] = Field(default=None, gt=0, le=2000)
    ac_cable_section: Optional[str] = Field(default=None, min_length=1, max_length=120)

    @field_validator('ac_phases')
    @classmethod
    def _phases_in_set(cls, value):
        if value is not None and value not in (1, 3):
            raise ValueError('debe ser 1 o 3')
        return value
