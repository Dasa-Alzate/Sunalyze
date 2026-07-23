
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


class LocaleSchema(BaseModel):
    locale: str = Field(min_length=2, max_length=10)
