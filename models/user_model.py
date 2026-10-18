from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# datos del usuario que devuelve la API (registro y /api/users/me).
# No incluye la contraseña: aunque la fila de la base de datos traiga
# password_hash, Pydantic ignora los campos que no están en el modelo.
class User(BaseModel):
    id: int
    name: str
    lastname: str
    nickname: str
    email: str
    created_at: datetime


# datos del formulario de registro
class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    lastname: str = Field(min_length=1, max_length=150)
    # letras sin tildes ni ñ, números, _ . y - (nunca @), entre 3 y 50 caracteres
    nickname: str = Field(pattern=r"^[A-Za-z0-9_.-]{3,50}$")
    email: EmailStr
    # el máximo protege al servidor: calcular un hash Argon2 es lento a propósito
    password: str = Field(min_length=8, max_length=128)
    password_confirm: str

    # quita los espacios del principio y del final antes de validar la longitud.
    # A la contraseña no: los espacios forman parte de ella.
    @field_validator("name", "lastname", "nickname", mode="before")
    @classmethod
    def strip_spaces(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    # se comprueba al final, con todos los campos ya validados
    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Las contraseñas no coinciden")
        return self


# datos del formulario de login: email o nickname en el mismo campo.
# La contraseña solo se exige no vacía: si algún día cambian las reglas,
# los usuarios con contraseñas antiguas tienen que poder seguir entrando.
class UserLogin(BaseModel):
    login: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("login", mode="before")
    @classmethod
    def strip_spaces(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


# respuesta del login
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"