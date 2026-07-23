
from typing import Optional

from pydantic import BaseModel, Field


class CatalogSchema(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str = Field(default='', max_length=255)


class PanelSchema(BaseModel):
    power: Optional[float] = Field(default=None, gt=0, le=2000)
    voc: Optional[float] = Field(default=None, ge=0, le=2000)
    vmp: Optional[float] = Field(default=None, ge=0, le=2000)
    imp: Optional[float] = Field(default=None, ge=0, le=500)
    isc: Optional[float] = Field(default=None, ge=0, le=500)
    y: Optional[float] = Field(default=None, ge=0, le=100)
    tcp: Optional[float] = Field(default=None, ge=-10, le=10)
    tcv: Optional[float] = Field(default=None, ge=-10, le=10)
    t_noct: Optional[float] = Field(default=None, gt=0, le=100)
    width: Optional[int] = Field(default=None, ge=0, le=10000)
    height: Optional[int] = Field(default=None, ge=0, le=10000)


class InverterSchema(BaseModel):
    power: Optional[float] = Field(default=None, gt=0, le=100000)
    power_max: Optional[float] = Field(default=None, gt=0, le=100000)
    vmax: Optional[float] = Field(default=None, ge=0, le=2000)
    I_max_input: Optional[float] = Field(default=None, ge=0, le=10000)
    I_max_output: Optional[float] = Field(default=None, ge=0, le=10000)
    y: Optional[float] = Field(default=None, ge=0, le=100)


class BatterySchema(BaseModel):
    capacity_kwh: Optional[float] = Field(default=None, gt=0, le=100000)
    usable_kwh: Optional[float] = Field(default=None, ge=0, le=100000)
    dod: Optional[float] = Field(default=None, ge=0, le=100)
    power_kw: Optional[float] = Field(default=None, gt=0, le=100000)
    voltage: Optional[float] = Field(default=None, gt=0, le=2000)
    round_trip_efficiency: Optional[float] = Field(default=None, ge=0, le=100)
    max_cycles: Optional[int] = Field(default=None, ge=0, le=1000000)
    width: Optional[int] = Field(default=None, ge=0, le=10000)
    height: Optional[int] = Field(default=None, ge=0, le=10000)
    depth: Optional[int] = Field(default=None, ge=0, le=10000)


class WireSchema(BaseModel):
    seccion: Optional[float] = Field(default=None, gt=0, le=10000)
    corriente: Optional[float] = Field(default=None, gt=0, le=100000)
    no_conductores: Optional[int] = Field(default=None, ge=1, le=1000)
