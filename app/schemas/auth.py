"""Esquemas de validacion de los endpoints de autenticacion (pydantic v2).

La politica de contrasena sigue OWASP ASVS 4.0 V2.1: longitud minima 12,
maxima 128, sin reglas de composicion obligatorias (2.1.9) y rechazo de las
contrasenas filtradas/triviales mas comunes (subconjunto local de 2.1.7).
"""

from pydantic import BaseModel, EmailStr, Field, field_validator

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128

_BREACHED_PASSWORDS = frozenset({
    '123456789012', '123456789', 'password', 'password1', 'password123',
    'qwertyuiop', 'qwerty123456', '111111111111', '000000000000',
    'iloveyou1234', 'administrator', 'letmein12345', 'contrasena12',
})


def _check_password(value):
    if len(value) < PASSWORD_MIN_LENGTH:
        raise ValueError(f'La contraseña debe tener al menos {PASSWORD_MIN_LENGTH} caracteres.')
    if len(value) > PASSWORD_MAX_LENGTH:
        raise ValueError(f'La contraseña no puede superar {PASSWORD_MAX_LENGTH} caracteres.')
    if value.lower() in _BREACHED_PASSWORDS:
        raise ValueError('Esa contraseña es demasiado común. Elige otra.')
    if len(set(value)) <= 2:
        raise ValueError('Esa contraseña es demasiado común. Elige otra.')
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
