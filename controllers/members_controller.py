import aiomysql
from fastapi import HTTPException

from controllers import users_controller, groups_controller
from models.group_model import UserSummary
from models.member_model import UserInvitation, GroupInvitation

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

# =====================================================================
# Invitaciones desde el invitado (cada usuario gestiona las suyas)
#
# No usan los permisos de grupo, porque el invitado aún no es miembro.
# Las protege que todas las consultas llevan WHERE user_id = <usuario logado>:
# cada uno solo ve y toca sus invitaciones; cualquier otra da 404.
# =====================================================================
 
 
async def get_user_invitations(conn: aiomysql.Connection, user_id: int) -> list[UserInvitation]:
    """Invitaciones pendientes del usuario, las más recientes primero.
    g.status = 'active' es una precaución: al cerrar un grupo se borran sus
    invitaciones pendientes, así que nunca debería haber una en un grupo cerrado.
    """
    async with conn.cursor() as cursor:
        await cursor.execute(
            "SELECT g.id AS group_id, g.title, g.description, "
            "       u.id AS creator_id, u.name AS creator_name, "
            "       u.lastname AS creator_lastname, u.nickname AS creator_nickname, "
            "       gm.updated_at AS invited_at "
            "FROM group_members gm "
            "JOIN expense_groups g ON g.id = gm.group_id "
            "JOIN users u ON u.id = g.created_by "
            "WHERE gm.user_id = %s AND gm.status = 'pending' AND g.status = 'active' "
            "ORDER BY gm.updated_at DESC, g.id",
            (user_id,),
        )
        rows = await cursor.fetchall()
    return [
        UserInvitation(
            group_id=row["group_id"],
            title=row["title"],
            description=row["description"],
            creator=UserSummary(
                id=row["creator_id"],
                name=row["creator_name"],
                lastname=row["creator_lastname"],
                nickname=row["creator_nickname"],
            ),
            invited_at=row["invited_at"],
        )
        for row in rows
    ]
 
 
async def accept_invitation(conn: aiomysql.Connection, group_id: int, user_id: int) -> None:
    """Acepta la invitación: pending pasa a accepted.
    Solo cambia la fila si la invitación es del usuario, está pendiente y el
    grupo está activo. Si no cambia ninguna, 404 (no existe, es de otro o ya
    es miembro: la misma respuesta en todos los casos).
    """
    async with conn.cursor() as cursor:
        await cursor.execute(
            "UPDATE group_members gm "
            "JOIN expense_groups g ON g.id = gm.group_id "
            "SET gm.status = 'accepted' "
            "WHERE gm.group_id = %s AND gm.user_id = %s "
            "  AND gm.status = 'pending' AND g.status = 'active'",
            (group_id, user_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Invitación no encontrada")
 
 
async def reject_invitation(conn: aiomysql.Connection, group_id: int, user_id: int) -> None:
    """Rechaza la invitación: borra la fila.
    El AND status = 'pending' impide que un miembro se borre a sí mismo del
    grupo por esta vía.
    """
    async with conn.cursor() as cursor:
        await cursor.execute(
            "DELETE FROM group_members "
            "WHERE group_id = %s AND user_id = %s AND status = 'pending'",
            (group_id, user_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Invitación no encontrada")


# =====================================================================
# Salidas y expulsiones
#
# Abandonar el grupo y ser expulsado son la misma operación con distinto
# protagonista: comparten esta función. Los permisos de quien hace la
# petición los comprueban las dependencias (can_leave_group, is_group_creator);
# aquí se comprueban las reglas sobre la persona que sale.
# =====================================================================
 
 
async def remove_member(conn: aiomysql.Connection, group_id: int, user_id: int) -> None:
    """Saca a un miembro del grupo (pasa a left) si su saldo es exactamente 0.
    - No es miembro accepted (no existe, pending o left): 404.
    - Es el creador: 409 (no puede salir; puede cerrar el grupo).
    - Su saldo no es 0: 409 con el saldo pendiente.
    Su fila se conserva, porque sus gastos y repartos antiguos la referencian.
    """
    await conn.begin()
    try:
        async with conn.cursor() as cursor:
            # 1. bloquear la fila del grupo hasta el final de la transacción:
            #    nadie puede registrar a la vez un gasto o una liquidación en el grupo
            #    entre la comprobación del saldo y la salida
            await cursor.execute(
                "SELECT currency, created_by FROM expense_groups WHERE id = %s FOR UPDATE",
                (group_id,),
            )
            group = await cursor.fetchone()
            if group is None:
                raise HTTPException(status_code=404, detail="Grupo no encontrado")
 
            # 2. la persona que sale tiene que ser miembro accepted y no el creador
            await cursor.execute(
                "SELECT status FROM group_members WHERE group_id = %s AND user_id = %s",
                (group_id, user_id),
            )
            member = await cursor.fetchone()
            if member is None or member["status"] != "accepted":
                raise HTTPException(status_code=404, detail="Miembro no encontrado")
            if user_id == group["created_by"]:
                raise HTTPException(
                    status_code=409,
                    detail="El creador no puede salir del grupo; puede cerrarlo",
                )
 
            # 3. su saldo tiene que ser exactamente 0
            balances = await groups_controller.get_balances(conn, group_id, user_id)
            balance = balances[0].balance
            if balance != 0:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"El saldo del miembro no es 0 ({balance} {group['currency']}). "
                        "Hay que saldar las cuentas antes de que salga del grupo"
                    ),
                )
 
            # 4. pasa a left
            await cursor.execute(
                "UPDATE group_members SET status = 'left' "
                "WHERE group_id = %s AND user_id = %s AND status = 'accepted'",
                (group_id, user_id),
            )
        await conn.commit()
    except Exception:
        # no se oculta el error: se deshace la transacción y se vuelve a lanzar
        await conn.rollback()
        raise