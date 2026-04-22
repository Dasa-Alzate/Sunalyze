"""Esquemas de validacion de los endpoints de autenticacion (pydantic v2)."""

import re
from pydantic import BaseModel, EmailStr, Field, field_validator

_DIGIT = re.compile(r'\d')
_LETTER = re.compile(r'[A-Za-z]')


def _check_password(value):
    if len(value) < 8:
        raise ValueError('La contraseña debe tener al menos 8 caracteres.')
    if not _DIGIT.search(value) or not _LETTER.search(value):
        raise ValueError('La contraseña debe combinar letras y números.')
    return value


class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(default='', max_length=80)
    company: str = Field(default='', max_length=120)

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        return _check_password(v)


class LoginSchema(BaseModel):
    email: EmailStr
    password: str
    remember: bool = False


class ForgotSchema(BaseModel):
    email: EmailStr


class ResetSchema(BaseModel):
    token: str = Field(min_length=8)
    password: str

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        return _check_password(v)


class VerifySchema(BaseModel):
    token: str = Field(min_length=8)
