"""Esquemas de validación de la organización."""

from typing import Optional

from pydantic import BaseModel, Field


class OrgBrandingSchema(BaseModel):
    logo_path: Optional[str] = Field(default=None, max_length=500)
    primary_color: Optional[str] = Field(default=None, max_length=20)
    footer_text: Optional[str] = Field(default=None, max_length=300)
