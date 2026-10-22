from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from models.group_model import UserSummary


# parte de un participante en el formulario de un gasto.
# En el reparto igual (equal) no lleva importe, porque lo calcula la API;
# en el personalizado (custom), cada parte lleva el suyo.
class ShareCreate(BaseModel):
    user_id: int
    # mismos límites que DECIMAL(10,2). Ninguna parte puede ser de 0 €.
    amount: Optional[Decimal] = Field(default=None, gt=0, max_digits=10, decimal_places=2)


# datos del formulario de creación de un gasto
class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    # miembro que pagó; que sea miembro accepted lo comprueba el controlador
    paid_by: int
    # hoy por defecto; puede ser una fecha pasada, nunca futura
    expense_date: date = Field(default_factory=date.today)
    # equal: modos "iguales entre todos" e "iguales entre algunos"; custom: personalizado
    split_type: Literal["equal", "custom"] = "equal"
    # una sola lista para los dos modos: los participantes, con importe solo en custom
    shares: list[ShareCreate] = Field(min_length=1)

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

    @field_validator("expense_date")
    @classmethod
    def not_in_the_future(cls, value):
        if value > date.today():
            raise ValueError("La fecha del gasto no puede ser futura")
        return value

    # reglas que dependen de varios campos a la vez: se comprueban con el modelo completo
    @model_validator(mode="after")
    def check_shares(self):
        user_ids = [share.user_id for share in self.shares]
        if len(user_ids) != len(set(user_ids)):
            raise ValueError("Un participante no puede aparecer dos veces en el reparto")

        if self.split_type == "equal":
            if any(share.amount is not None for share in self.shares):
                raise ValueError(
                    "En el reparto a partes iguales las partes no llevan importe: lo calcula la API"
                )
        else:
            if any(share.amount is None for share in self.shares):
                raise ValueError("En el reparto personalizado cada parte tiene que llevar su importe")
            total = sum(share.amount for share in self.shares)
            if total != self.amount:
                raise ValueError(
                    f"La suma de las partes ({total}) no coincide con el importe del gasto ({self.amount})"
                )
        return self


# parte de un gasto que corresponde a un participante
class ExpenseShare(BaseModel):
    user: UserSummary
    amount: Decimal


# cada gasto del grupo, con quién lo pagó y cómo se repartió
class Expense(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    amount: Decimal
    split_type: Literal["equal", "custom"]
    expense_date: date
    created_at: datetime
    paid_by: UserSummary
    shares: list[ExpenseShare]
