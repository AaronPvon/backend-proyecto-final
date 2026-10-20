# Aquí van las rutas de grupos (/api/groups)
from typing import Literal

import aiomysql
from fastapi import APIRouter, Depends

from controllers import groups_controller
from core.auth import get_current_user
from core.permissions import is_group_member
from db.config import get_connection
from models.group_model import GroupCreate, Balance, Group, GroupDetail
from models.user_model import User

router = APIRouter()


# Obtener los grupos del usuario logado: GET /api/groups?status=active|closed
# Aquí no hay un grupo concreto: basta con saber quién es el usuario (get_current_user).
# La ruta es "" y no "/" para que responda en /api/groups, sin barra final.
@router.get("", status_code=200, response_model=list[Group])
async def get_user_groups(
    status: Literal["active", "closed"] = "active",
    current_user: User = Depends(get_current_user),
    conn: aiomysql.Connection = Depends(get_connection),
):
    return await groups_controller.get_user_groups(conn, current_user.id, status)

# Crear un grupo: POST /api/groups
# Cualquier usuario logado puede crear todos los grupos que necesite.
# 201 = creado. Devuelve el detalle, con el creador como único miembro.
@router.post("", status_code=201, response_model=GroupDetail)
async def create_group(
    group: GroupCreate,
    current_user: User = Depends(get_current_user),
    conn: aiomysql.Connection = Depends(get_connection),
):
    return await groups_controller.create_group(conn, current_user.id, group)

# Obtener el detalle de un grupo: GET /api/groups/{group_id}
# is_group_member responde 404 si el grupo no existe o el usuario no es miembro.
@router.get("/{group_id}", status_code=200, response_model=GroupDetail)
async def get_group_by_id(
    group_id: int,
    current_user: User = Depends(is_group_member),
    conn: aiomysql.Connection = Depends(get_connection),
):
    return await groups_controller.get_detail(conn, group_id)


# Obtener los saldos de un grupo: GET /api/groups/{group_id}/balances
@router.get("/{group_id}/balances", status_code=200, response_model=list[Balance])
async def get_group_balances(
    group_id: int,
    current_user: User = Depends(is_group_member),
    conn: aiomysql.Connection = Depends(get_connection),
):
    return await groups_controller.get_balances(conn, group_id)