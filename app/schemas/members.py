
from typing import Literal
from pydantic import BaseModel, EmailStr


class InviteSchema(BaseModel):
    email: EmailStr
    role: Literal['admin', 'member'] = 'member'


class ChangeRoleSchema(BaseModel):
    role: Literal['owner', 'admin', 'member']


class SwitchWorkspaceSchema(BaseModel):
    org_id: int
