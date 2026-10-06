from typing import Optional

from pydantic import BaseModel, Field


class ElectricityPlanUpdateSchema(BaseModel):
    model_config = {'extra': 'ignore'}

    comercializadora: Optional[str] = Field(default=None, min_length=1, max_length=80)
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=120)
    peaje: Optional[str] = Field(default=None, min_length=1, max_length=20)
    precio_punta: Optional[float] = Field(default=None, ge=0, le=5)
    precio_llano: Optional[float] = Field(default=None, ge=0, le=5)
    precio_valle: Optional[float] = Field(default=None, ge=0, le=5)
    precio_excedente: Optional[float] = Field(default=None, ge=0, le=5)
    precio_potencia_p1_dia: Optional[float] = Field(default=None, ge=0, le=5)
    precio_potencia_p2_dia: Optional[float] = Field(default=None, ge=0, le=5)
    impuesto_electricidad: Optional[float] = Field(default=None, ge=0, le=1)
    iva_pct: Optional[float] = Field(default=None, ge=0, le=100)
    alquiler_contador_mes: Optional[float] = Field(default=None, ge=0, le=100)


class ElectricityPlanCreateSchema(ElectricityPlanUpdateSchema):
    comercializadora: str = Field(min_length=1, max_length=80)
    nombre: str = Field(min_length=1, max_length=120)
