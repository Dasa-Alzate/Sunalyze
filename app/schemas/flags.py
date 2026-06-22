"""Esquemas de validación de la gestión de flags."""

from typing import Optional
from pydantic import BaseModel, Field


class FlagSchema(BaseModel):
    key: str = Field(min_length=2, max_length=80, pattern=r'^[a-z][a-z0-9_]*$')
    nombre: str = Field(min_length=1, max_length=120)
    titulo: str = Field(default='', max_length=150)
    descripcion: str = Field(default='', max_length=500)
    default_enabled: bool = False
    is_visible: bool = False
    image_path: Optional[str] = Field(default=None, max_length=255)
    thumbnail_path: Optional[str] = Field(default=None, max_length=255)
    help_url: Optional[str] = Field(default=None, max_length=255)
    price: Optional[float] = Field(default=None, ge=0)


class OverrideSchema(BaseModel):
    scope: str
    scope_id: Optional[int] = None
    enabled: bool = True


class ClearOverrideSchema(BaseModel):
    scope: str
    scope_id: Optional[int] = None
