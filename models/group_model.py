from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# datos del formulario de creación de un grupo
class GroupCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    # mismos límites que DECIMAL(10,2): 10 cifras en total, 2 de ellas decimales
    budget: Optional[Decimal] = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    # lista cerrada de monedas permitidas; para añadir otra, basta con incluirla aquí
    currency: Literal["EUR", "USD"] = "EUR"

    @field_validator("title", mode="before")
    @classmethod
    def strip_spaces(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    # una descripción en blanco se guarda como NULL
    @field_validator("description", mode="before")
    @classmethod
    def empty_description_to_none(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value

    # "eur" se acepta y se guarda como "EUR"
    @field_validator("currency", mode="before")
    @classmethod
    def currency_to_upper(cls, value):
        if isinstance(value, str):
            return value.strip().upper()
        return value


# datos básicos de un usuario dentro de un grupo (creador y miembros).
# No incluye el email: los compañeros de grupo no necesitan verlo.
class UserSummary(BaseModel):
    id: int
    name: str
    lastname: str
    nickname: str


# cada grupo del listado "Mis grupos"
class Group(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    budget: Optional[Decimal] = None
    currency: str
    status: Literal["active", "closed"]
    closed_at: Optional[datetime] = None
    created_at: datetime
    creator: UserSummary


# detalle de un grupo: lo mismo que en el listado, más los miembros y el total gastado
class GroupDetail(Group):
    members: list[UserSummary]
    total_spent: Decimal


# saldo de un miembro: positivo, le deben; negativo, debe
class Balance(BaseModel):
    user_id: int
    name: str
    lastname: str
    nickname: str
    status: Literal["accepted", "left"]
    balance: Decimal