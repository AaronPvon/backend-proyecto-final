# Permisos de grupo: quién puede hacer qué en cada grupo.
# Toda la lógica está en check_group_access; las rutas la usan a través
# de dependencias, como is_admin e is_owner_user en el ejercicio de clase.
from typing import Literal

import aiomysql
from fastapi import Depends, HTTPException, Path

from controllers import groups_controller
from core.auth import get_current_user
from db.config import get_connection
from models.user_model import User


async def check_group_access(
    conn: aiomysql.Connection,
    group_id: int,
    user: User,
    action: Literal["view", "manage", "leave"],
) -> dict:
    """Función única de permisos de grupo. Si el usuario puede, devuelve los datos de acceso del grupo.
    - "view": ver el grupo. Hace falta ser miembro accepted.
    - "manage": cambiar algo. Además, hace falta ser el creador y que el grupo esté activo.
    - "leave": salir del grupo. Hace falta ser miembro accepted y que el grupo esté activo.
      Que quien sale no sea el creador lo comprueba el controlador, porque es una
      regla sobre la persona que sale, compartida con la expulsión.
    El orden de las comprobaciones importa: primero la de miembro, para no
    revelar a quien no lo es si el grupo existe o si está cerrado.
    """
    if action not in ("view", "manage", "leave"):
        raise ValueError(f"Acción de permisos desconocida: {action}")

    group = await groups_controller.get_access_info(conn, group_id, user.id)

    # 1. no existe, o el usuario no es miembro (sin fila, pending o left): 404
    if group is None or group["member_status"] != "accepted":
        raise HTTPException(status_code=404, detail="Grupo no encontrado")

    if action == "manage":
        # 2. es miembro, pero no el creador: 403
        if group["created_by"] != user.id:
            raise HTTPException(status_code=403, detail="Solo el creador del grupo puede hacer esto")
        # 3. es el creador, pero el grupo está cerrado: 409
        if group["status"] == "closed":
            raise HTTPException(status_code=409, detail="El grupo está cerrado")

    if action == "leave":
        # es miembro, pero el grupo está cerrado: 409
        if group["status"] == "closed":
            raise HTTPException(status_code=409, detail="El grupo está cerrado")

    return group


####################################################################################################
#                 LAS DEPENDENCIAS SE INCLUYEN EN LOS ARCHIVOS DE LAS RUTAS, DENTRO DE LA RUTA      #
####################################################################################################

# Dependencia para comprobar que el usuario es miembro del grupo de la URL ({group_id})
async def is_group_member(
    group_id: int = Path(...),
    user: User = Depends(get_current_user),
    conn: aiomysql.Connection = Depends(get_connection),
) -> User:
    await check_group_access(conn, group_id, user, "view")
    return user


# Dependencia para comprobar que el usuario es el creador del grupo y que está activo
async def is_group_creator(
    group_id: int = Path(...),
    user: User = Depends(get_current_user),
    conn: aiomysql.Connection = Depends(get_connection),
) -> User:
    await check_group_access(conn, group_id, user, "manage")
    return user


# Dependencia para comprobar que el usuario puede salir del grupo (miembro y grupo activo)
async def can_leave_group(
    group_id: int = Path(...),
    user: User = Depends(get_current_user),
    conn: aiomysql.Connection = Depends(get_connection),
) -> User:
    await check_group_access(conn, group_id, user, "leave")
    return user