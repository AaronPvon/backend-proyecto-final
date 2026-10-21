# Aquí van las rutas de invitaciones y miembros de un grupo (/api/groups/{group_id}/...)
import aiomysql
from fastapi import APIRouter, Depends

from controllers import members_controller
from core.permissions import is_group_creator, is_group_member, can_leave_group
from db.config import get_connection
from models.member_model import GroupInvitation, InvitationCreate
from models.user_model import User

router = APIRouter()


# Obtener las invitaciones pendientes del grupo: GET /api/groups/{group_id}/invitations
# Las ven todos los miembros.
@router.get("/{group_id}/invitations", status_code=200, response_model=list[GroupInvitation])
async def get_group_invitations(
    group_id: int,
    current_user: User = Depends(is_group_member),
    conn: aiomysql.Connection = Depends(get_connection),
):
    return await members_controller.get_group_invitations(conn, group_id)


# Invitar a un usuario por email o nickname: POST /api/groups/{group_id}/invitations
# Solo el creador, y con el grupo activo.
@router.post("/{group_id}/invitations", status_code=201, response_model=GroupInvitation)
async def create_invitation(
    group_id: int,
    invitation: InvitationCreate,
    current_user: User = Depends(is_group_creator),
    conn: aiomysql.Connection = Depends(get_connection),
):
    return await members_controller.invite_user(conn, group_id, invitation.login)


# Anular una invitación pendiente: DELETE /api/groups/{group_id}/invitations/{user_id}
# Solo el creador, y con el grupo activo. 204 = hecho, sin contenido.
@router.delete("/{group_id}/invitations/{user_id}", status_code=204)
async def delete_invitation(
    group_id: int,
    user_id: int,
    current_user: User = Depends(is_group_creator),
    conn: aiomysql.Connection = Depends(get_connection),
):
    await members_controller.cancel_invitation(conn, group_id, user_id)


# Salir del grupo: POST /api/groups/{group_id}/leave
# El propio miembro, con el grupo activo y saldo 0. El creador no puede salir.
@router.post("/{group_id}/leave", status_code=204)
async def leave_group(
    group_id: int,
    current_user: User = Depends(can_leave_group),
    conn: aiomysql.Connection = Depends(get_connection),
):
    await members_controller.remove_member(conn, group_id, current_user.id)
 
 
# Expulsar a un miembro: DELETE /api/groups/{group_id}/members/{user_id}
# Solo el creador, con el grupo activo, y el miembro tiene que tener saldo 0.
@router.delete("/{group_id}/members/{user_id}", status_code=204)
async def delete_member(
    group_id: int,
    user_id: int,
    current_user: User = Depends(is_group_creator),
    conn: aiomysql.Connection = Depends(get_connection),
):
    await members_controller.remove_member(conn, group_id, user_id)