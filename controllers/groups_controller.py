import aiomysql

from models.group_model import Balance, Group, GroupDetail, UserSummary

async def get_access_info(conn: aiomysql.Connection, group_id: int, user_id: int) -> dict | None:
    """Datos que necesita core/permissions.py para decidir si el usuario accede al grupo.
    Devuelve el estado del grupo, su creador y el estado del usuario en él
    (member_status), o None si el grupo no existe. Con el LEFT JOIN, si el
    grupo existe pero el usuario no tiene fila en group_members, member_status
    llega como None en lugar de no devolver nada.
    """
    async with conn.cursor() as cursor:
        await cursor.execute(
            "SELECT g.id, g.status, g.created_by, gm.status AS member_status "
            "FROM expense_groups g "
            "LEFT JOIN group_members gm ON gm.group_id = g.id AND gm.user_id = %s "
            "WHERE g.id = %s",
            (user_id, group_id),
        )
        return await cursor.fetchone()

def build_group_data(row: dict) -> dict:
    """Convierte una fila (grupo + columnas creator_*) en los datos de un Group.
    Las columnas del creador llevan el prefijo creator_ en la consulta porque
    users y expense_groups tienen columnas con el mismo nombre (id, created_at).
    """
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "budget": row["budget"],
        "currency": row["currency"],
        "status": row["status"],
        "closed_at": row["closed_at"],
        "created_at": row["created_at"],
        "creator": UserSummary(
            id=row["creator_id"],
            name=row["creator_name"],
            lastname=row["creator_lastname"],
            nickname=row["creator_nickname"],
        ),
    }
 
 
async def get_user_groups(conn: aiomysql.Connection, user_id: int, status: str) -> list[Group]:
    """Grupos en los que el usuario es miembro accepted, filtrados por estado.
    Activos: los creados más recientemente primero.
    Cerrados: los cerrados más recientemente primero.
    """
    async with conn.cursor() as cursor:
        await cursor.execute(
            "SELECT g.id, g.title, g.description, g.budget, g.currency, g.status, "
            "       g.closed_at, g.created_at, "
            "       u.id AS creator_id, u.name AS creator_name, "
            "       u.lastname AS creator_lastname, u.nickname AS creator_nickname "
            "FROM expense_groups g "
            "JOIN group_members gm ON gm.group_id = g.id AND gm.user_id = %s AND gm.status = 'accepted' "
            "JOIN users u ON u.id = g.created_by "
            "WHERE g.status = %s "
            "ORDER BY CASE WHEN g.status = 'closed' THEN g.closed_at ELSE g.created_at END DESC, g.id DESC",
            (user_id, status),
        )
        rows = await cursor.fetchall()
    return [Group(**build_group_data(row)) for row in rows]
 
 
async def get_detail(conn: aiomysql.Connection, group_id: int) -> GroupDetail | None:
    """Detalle del grupo: datos, creador, miembros accepted y total gastado."""
    async with conn.cursor() as cursor:
        # datos del grupo, su creador y el total gastado
        await cursor.execute(
            "SELECT g.id, g.title, g.description, g.budget, g.currency, g.status, "
            "       g.closed_at, g.created_at, "
            "       u.id AS creator_id, u.name AS creator_name, "
            "       u.lastname AS creator_lastname, u.nickname AS creator_nickname, "
            "       (SELECT COALESCE(SUM(e.amount), 0) FROM expenses e "
            "        WHERE e.group_id = g.id) AS total_spent "
            "FROM expense_groups g "
            "JOIN users u ON u.id = g.created_by "
            "WHERE g.id = %s",
            (group_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
 
        # miembros accepted, por orden alfabético
        await cursor.execute(
            "SELECT u.id, u.name, u.lastname, u.nickname "
            "FROM group_members gm "
            "JOIN users u ON u.id = gm.user_id "
            "WHERE gm.group_id = %s AND gm.status = 'accepted' "
            "ORDER BY u.name, u.lastname",
            (group_id,),
        )
        members = await cursor.fetchall()
 
    return GroupDetail(
        **build_group_data(row),
        members=[UserSummary(**member) for member in members],
        total_spent=row["total_spent"],
    )
 
 
async def get_balances(conn: aiomysql.Connection, group_id: int) -> list[Balance]:
    """Saldo de cada miembro (accepted y left) del grupo. Se calcula, nunca se guarda.
    saldo = pagado − su parte + liquidaciones enviadas − liquidaciones recibidas
    Positivo: le deben. Negativo: debe. Los saldos de un grupo suman 0.
    """
    async with conn.cursor() as cursor:
        await cursor.execute(
            "SELECT u.id AS user_id, u.name, u.lastname, u.nickname, gm.status, "
            # lo que ha pagado
            "    COALESCE((SELECT SUM(e.amount) FROM expenses e "
            "              WHERE e.group_id = gm.group_id AND e.paid_by = gm.user_id), 0) "
            # menos su parte de los gastos
            "  - COALESCE((SELECT SUM(es.amount) FROM expense_shares es "
            "              JOIN expenses e ON e.id = es.expense_id "
            "              WHERE e.group_id = gm.group_id AND es.user_id = gm.user_id), 0) "
            # más las liquidaciones que ha enviado
            "  + COALESCE((SELECT SUM(s.amount) FROM settlements s "
            "              WHERE s.group_id = gm.group_id AND s.from_user_id = gm.user_id), 0) "
            # menos las liquidaciones que ha recibido
            "  - COALESCE((SELECT SUM(s.amount) FROM settlements s "
            "              WHERE s.group_id = gm.group_id AND s.to_user_id = gm.user_id), 0) "
            "    AS balance "
            "FROM group_members gm "
            "JOIN users u ON u.id = gm.user_id "
            "WHERE gm.group_id = %s AND gm.status IN ('accepted', 'left') "
            "ORDER BY gm.user_id",
            (group_id,),
        )
        rows = await cursor.fetchall()
    return [Balance(**row) for row in rows]