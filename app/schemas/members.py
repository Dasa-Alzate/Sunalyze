"""Esquemas de validacion de invitaciones y gestion de miembros (pydantic v2)."""

from typing import Literal
from pydantic import BaseModel, EmailStr


class InviteSchema(BaseModel):
    email: EmailStr
    role: Literal['admin', 'member'] = 'member'


class ChangeRoleSchema(BaseModel):
    role: Literal['owner', 'admin', 'member']


class SwitchWorkspaceSchema(BaseModel):
    org_id: int
