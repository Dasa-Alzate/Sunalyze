
from typing import Literal, Optional
from pydantic import BaseModel, Field


class TransitionSchema(BaseModel):
    to_estado: Literal['borrador', 'en_revision', 'presentado', 'aprobado', 'rechazado']
    note: Optional[str] = Field(default=None, max_length=500)


class SignMemoriaSchema(BaseModel):
    pdf_sha256: str = Field(min_length=64, max_length=64, pattern=r'^[0-9a-fA-F]{64}$')
    pdf_size_bytes: int = Field(ge=0)
    note: Optional[str] = Field(default=None, max_length=500)
