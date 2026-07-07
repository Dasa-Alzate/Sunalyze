"""Esquemas de validación de la organización."""

import os
import re
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

_HEX_COLOR = re.compile(r'^#[0-9a-fA-F]{3,8}$')


class OrgBrandingSchema(BaseModel):
    logo_path: Optional[str] = Field(default=None, max_length=500)
    primary_color: Optional[str] = Field(default=None, max_length=20)
    footer_text: Optional[str] = Field(default=None, max_length=300)

    @field_validator('logo_path')
    @classmethod
    def logo_path_is_safe_relative(cls, v):
        """`logo_path` es una ruta relativa segura bajo el dir de branding.

        Rechaza esquemas (`http/https/file/data`), rutas absolutas, backslashes y
        cualquier componente `..`, cerrando SSRF/LFI en el render del PDF (defensa en
        profundidad junto al url_fetcher restringido de WeasyPrint).
        """
        if v is None:
            return v
        candidate = v.strip()
        if not candidate:
            return None
        if urlparse(candidate).scheme:
            raise ValueError('El logo debe ser una ruta relativa, no una URL.')
        if candidate.startswith('/') or candidate.startswith('\\') or '\\' in candidate:
            raise ValueError('El logo debe ser una ruta relativa segura.')
        if os.path.isabs(candidate):
            raise ValueError('El logo debe ser una ruta relativa segura.')
        parts = candidate.split('/')
        if any(part == '..' for part in parts):
            raise ValueError('El logo no puede contener «..».')
        return candidate

    @field_validator('primary_color')
    @classmethod
    def primary_color_is_hex(cls, v):
        """Acepta solo un color hexadecimal CSS (`#RGB`..`#RRGGBBAA`)."""
        if v is None:
            return v
        candidate = v.strip()
        if not candidate:
            return None
        if not _HEX_COLOR.match(candidate):
            raise ValueError('El color debe ser hexadecimal, p. ej. #1a1a1a.')
        return candidate
