from typing import List

from pydantic import BaseModel, Field, field_validator


class BudgetItemSchema(BaseModel):
    capitulo: int = Field(ge=1, le=4)
    descripcion: str = Field(min_length=1, max_length=200)
    unidad: str = Field(default='ud', max_length=10)
    cantidad: float = Field(default=1, ge=0, le=1_000_000)
    precio_unitario: float = Field(default=0, ge=0, le=10_000_000)
    orden: int = Field(default=0, ge=0, le=10_000)


class BudgetPayloadSchema(BaseModel):
    iva_pct: float = Field(default=21)
    items: List[BudgetItemSchema] = Field(default_factory=list, max_length=200)

    @field_validator('iva_pct')
    @classmethod
    def _iva(cls, v):
        if v not in (0, 4, 10, 21):
            raise ValueError('IVA inválido: usa 0, 4, 10 o 21.')
        return v
