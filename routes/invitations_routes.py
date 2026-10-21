# Aquí van las rutas de las invitaciones del usuario logado (/api/invitations)
# No usan los permisos de grupo: el invitado todavía no es miembro.
# Cada usuario solo ve y gestiona sus propias invitaciones.
import aiomysql
from fastapi import APIRouter, Depends

from controllers import members_controller
from core.auth import get_current_user
from db.config import get_connection
from models.member_model import UserInvitation
from models.user_model import User

router = APIRouter()


# Obtener mis invitaciones pendientes: GET /api/invitations
@router.get("", status_code=200, response_model=list[UserInvitation])
async def get_user_invitations(
    current_user: User = Depends(get_current_user),
    conn: aiomysql.Connection = Depends(get_connection),
):
    return await members_controller.get_user_invitations(conn, current_user.id)


# Aceptar una invitación: POST /api/invitations/{group_id}/accept
# 204 = hecho, sin contenido. El front muestra un mensaje con enlace al grupo.
@router.post("/{group_id}/accept", status_code=204)
async def accept_invitation(
    group_id: int,
    current_user: User = Depends(get_current_user),
    conn: aiomysql.Connection = Depends(get_connection),
):
    await members_controller.accept_invitation(conn, group_id, current_user.id)


# Rechazar una invitación: DELETE /api/invitations/{group_id}
@router.delete("/{group_id}", status_code=204)
async def reject_invitation(
    group_id: int,
    current_user: User = Depends(get_current_user),
    conn: aiomysql.Connection = Depends(get_connection),
):
    await members_controller.reject_invitation(conn, group_id, current_user.id)