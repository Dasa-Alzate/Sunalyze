"""Validación de entrada para perfiles de consumo."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

PROFILE_KINDS = ('annual', 'day', 'daytypes', 'week', 'month', 'seasonal')


class ConsumptionProfileCreateSchema(BaseModel):
    model_config = {'extra': 'ignore'}
    name: str = Field(min_length=1, max_length=150)
    kind: str
    payload: dict

    @field_validator('name', mode='before')
    @classmethod
    def _strip(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator('kind')
    @classmethod
    def _known_kind(cls, value):
        if value not in PROFILE_KINDS:
            raise ValueError(f'kind debe ser uno de {PROFILE_KINDS}')
        return value


class ConsumptionProfileUpdateSchema(BaseModel):
    model_config = {'extra': 'ignore'}
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)

    @field_validator('name', mode='before')
    @classmethod
    def _strip(cls, value):
        return value.strip() if isinstance(value, str) else value
