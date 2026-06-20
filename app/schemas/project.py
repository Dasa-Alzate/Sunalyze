"""Esquemas de validacion de creacion y actualizacion de proyectos.

Tipa y acota los campos que llegan en el body de POST/PATCH de proyecto, que
antes se volcaban crudos al modelo sin comprobar tipo ni rango. Todos los campos
son opcionales en la actualizacion; en la creacion solo `cliente` es obligatorio.
Las rutas aplican el resultado con model_dump(exclude_unset=True), de modo que un
campo no enviado conserva su valor actual y no se pisan opcionales.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ProjectUpdateSchema(BaseModel):
    model_config = {'extra': 'ignore'}

    cliente: Optional[str] = Field(default=None, min_length=1, max_length=150)
    direccion: Optional[str] = Field(default=None, max_length=255)
    localidad: Optional[str] = Field(default=None, max_length=120)

    latitud: Optional[float] = Field(default=None, ge=-90, le=90)
    longitud: Optional[float] = Field(default=None, ge=-180, le=180)
    necesidad: Optional[float] = Field(default=None, ge=0, le=1000000000)
    autoconsumo: Optional[float] = Field(default=None, ge=0, le=1000000000)
    coplanar: Optional[bool] = None
    inclinacion: Optional[float] = Field(default=None, ge=0, le=90)
    azimut: Optional[float] = Field(default=None, ge=-180, le=180)

    panel_id: Optional[int] = Field(default=None, gt=0)
    inverter_id: Optional[int] = Field(default=None, gt=0)
    battery_id: Optional[int] = Field(default=None, gt=0)
    battery_quantity: Optional[int] = Field(default=None, ge=1, le=10000)

    referencia_catastral: Optional[str] = Field(default=None, max_length=40)
    cups: Optional[str] = Field(default=None, max_length=40)
    compania: Optional[str] = Field(default=None, max_length=80)
    potencia_contratada: Optional[float] = Field(default=None, gt=0, le=1000000)
    tipo_voltaje: Optional[str] = Field(default=None, max_length=20)

    resultados: Optional[dict] = None

    @field_validator('*', mode='before')
    @classmethod
    def _empty_to_none(cls, value):
        """Normaliza cadenas vacias o solo-espacios a None (opcional ausente)."""
        if isinstance(value, str) and value.strip() == '':
            return None
        return value


class ProjectCreateSchema(ProjectUpdateSchema):
    cliente: str = Field(min_length=1, max_length=150)
