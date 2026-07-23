
import os
import re
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

_HEX_COLOR = re.compile(r'^#[0-9a-fA-F]{3,8}$')
_PREFIX = re.compile(r'^[A-Z0-9-]{1,8}$')


class OrgBrandingSchema(BaseModel):
    logo_path: Optional[str] = Field(default=None, max_length=500)
    primary_color: Optional[str] = Field(default=None, max_length=20)
    footer_text: Optional[str] = Field(default=None, max_length=300)
    project_prefix: Optional[str] = Field(default=None, max_length=8)

    @field_validator('logo_path')
    @classmethod
    def logo_path_is_safe_relative(cls, v):
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
        if v is None:
            return v
        candidate = v.strip()
        if not candidate:
            return None
        if not _HEX_COLOR.match(candidate):
            raise ValueError('El color debe ser hexadecimal, p. ej. #1a1a1a.')
        return candidate

    @field_validator('project_prefix')
    @classmethod
    def project_prefix_is_slug(cls, v):
        if v is None:
            return v
        candidate = v.strip().upper()
        if not candidate:
            return None
        if not _PREFIX.match(candidate):
            raise ValueError('El prefijo solo admite letras, números y guiones (máx. 8).')
        return candidate
