"""Esquemas de validación de la gestión de flags."""

from typing import Optional
from pydantic import BaseModel, Field


class FlagSchema(BaseModel):
    key: str = Field(min_length=2, max_length=80, pattern=r'^[a-z][a-z0-9_]*$')
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str = Field(default='', max_length=255)
    default_enabled: bool = False


class OverrideSchema(BaseModel):
    scope: str
    scope_id: Optional[int] = None
    enabled: bool = True


class ClearOverrideSchema(BaseModel):
    scope: str
    scope_id: Optional[int] = None
