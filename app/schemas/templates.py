"""Esquemas de validación del constructor de plantillas de documentos."""

from typing import Optional, List

from pydantic import BaseModel, Field


class TemplateCreateSchema(BaseModel):
    kind: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=150)
    description: str = Field(default='', max_length=500)
    country: Optional[str] = Field(default=None, max_length=80)
    region: Optional[str] = Field(default=None, max_length=120)
    content: Optional[list] = None


class TemplateUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, max_length=500)
    country: Optional[str] = Field(default=None, max_length=80)
    region: Optional[str] = Field(default=None, max_length=120)
    thumbnail_path: Optional[str] = Field(default=None, max_length=255)
    status: Optional[str] = Field(default=None, max_length=20)


class ContentSchema(BaseModel):
    content: list
    changelog: str = Field(default='', max_length=500)


class PreviewSchema(BaseModel):
    project_id: int


class CategorySchema(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class LabelSchema(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class FavoriteSchema(BaseModel):
    is_favorite: bool


class CategoryAssignSchema(BaseModel):
    category_id: Optional[int] = None


class LabelsAssignSchema(BaseModel):
    label_ids: List[int] = Field(default_factory=list)
