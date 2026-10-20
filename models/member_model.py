from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from models.group_model import UserSummary


# datos para invitar a un usuario: su email o su nickname en el mismo campo,
# igual que en el login. La búsqueda es por coincidencia exacta.
class InvitationCreate(BaseModel):
    login: str = Field(min_length=1, max_length=255)

    @field_validator("login", mode="before")
    @classmethod
    def strip_spaces(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


# una invitación vista desde el grupo: a quién se invitó y cuándo.
# invited_at sale de group_members.updated_at: si se reinvita a alguien que
# salió del grupo, su fila pasa de left a pending y created_at sería la fecha
# de la primera invitación.
class GroupInvitation(BaseModel):
    user: UserSummary
    invited_at: datetime


# una invitación vista desde el invitado: lo que necesita para decidir si acepta
# (y, tras aceptar, el group_id y el título para el mensaje con enlace al grupo)
class UserInvitation(BaseModel):
    group_id: int
    title: str
    description: Optional[str] = None
    creator: UserSummary
    invited_at: datetime