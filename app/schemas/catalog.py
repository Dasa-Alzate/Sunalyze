"""Esquemas de validacion de catalogos y equipos."""

from typing import Optional

from pydantic import BaseModel, Field


class CatalogSchema(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str = Field(default='', max_length=255)


class PanelSchema(BaseModel):
    """Rangos físicos de un panel para altas y ediciones.

    Todos los campos son opcionales para admitir ediciones parciales (PATCH):
    solo se valida lo que llega. tcp y tcv no acotan el signo porque los
    coeficientes de temperatura suelen ser negativos (%/°C).
    """
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
