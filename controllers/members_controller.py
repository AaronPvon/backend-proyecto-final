import aiomysql
from fastapi import HTTPException

from controllers import users_controller
from models.group_model import UserSummary
from models.member_model import GroupInvitation

# =====================================================================
# Invitaciones desde el grupo (las gestiona el creador)
# =====================================================================


async def invite_user(conn: aiomysql.Connection, group_id: int, login: str) -> GroupInvitation:
    """Invita a un usuario (por email o nickname exacto) al grupo.
    - No existe: 404.
    - Ya es miembro (accepted), incluido el propio creador: 409.
    - Ya tiene una invitación pendiente: 409.
    - Salió del grupo (left): su fila vuelve a pending.
    - Nunca estuvo: se crea su fila como pending.
    """
    user = await users_controller.get_summary_by_login(conn, login)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    async with conn.cursor() as cursor:
        await cursor.execute(
            "SELECT status FROM group_members WHERE group_id = %s AND user_id = %s",
            (group_id, user.id),
        )
        row = await cursor.fetchone()

        if row and row["status"] == "accepted":
            raise HTTPException(status_code=409, detail="El usuario ya es miembro del grupo")
        if row and row["status"] == "pending":
            raise HTTPException(status_code=409, detail="El usuario ya tiene una invitación pendiente")

        if row:
            # salió del grupo: se le vuelve a invitar sobre la misma fila
            await cursor.execute(
                "UPDATE group_members SET status = 'pending' "
                "WHERE group_id = %s AND user_id = %s AND status = 'left'",
                (group_id, user.id),
            )
            # 0 filas: otra petición le ha reinvitado justo a la vez
            if cursor.rowcount == 0:
                raise HTTPException(status_code=409, detail="El usuario ya tiene una invitación pendiente")
        else:
            try:
                await cursor.execute(
                    "INSERT INTO group_members (group_id, user_id, status) VALUES (%s, %s, 'pending')",
                    (group_id, user.id),
                )
            except aiomysql.IntegrityError as e:
                # 1062: otra petición ha creado la invitación justo a la vez (clave primaria repetida)
                if e.args[0] == 1062:
                    raise HTTPException(status_code=409, detail="El usuario ya tiene una invitación pendiente")
                raise

        # la fecha de la invitación es updated_at (ver models/member_model.py)
        await cursor.execute(
            "SELECT updated_at FROM group_members WHERE group_id = %s AND user_id = %s",
            (group_id, user.id),
        )
        invited = await cursor.fetchone()

    return GroupInvitation(user=user, invited_at=invited["updated_at"])


async def get_group_invitations(conn: aiomysql.Connection, group_id: int) -> list[GroupInvitation]:
    """Invitaciones pendientes del grupo, las más recientes primero."""
    async with conn.cursor() as cursor:
        await cursor.execute(
            "SELECT u.id, u.name, u.lastname, u.nickname, gm.updated_at AS invited_at "
            "FROM group_members gm "
            "JOIN users u ON u.id = gm.user_id "
            "WHERE gm.group_id = %s AND gm.status = 'pending' "
            "ORDER BY gm.updated_at DESC, u.id",
            (group_id,),
        )
        rows = await cursor.fetchall()
    return [
        GroupInvitation(
            user=UserSummary(id=row["id"], name=row["name"], lastname=row["lastname"], nickname=row["nickname"]),
            invited_at=row["invited_at"],
        )
        for row in rows
    ]


async def cancel_invitation(conn: aiomysql.Connection, group_id: int, user_id: int) -> None:
    """Anula una invitación pendiente: borra la fila.
    El AND status = 'pending' es imprescindible: sin él, "anular la invitación"
    de un miembro accepted sin gastos lo borraría del grupo.
    """
    async with conn.cursor() as cursor:
        await cursor.execute(
            "DELETE FROM group_members "
            "WHERE group_id = %s AND user_id = %s AND status = 'pending'",
            (group_id, user_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Invitación no encontrada")