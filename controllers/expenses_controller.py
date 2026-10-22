from decimal import ROUND_DOWN, Decimal

import aiomysql
from fastapi import HTTPException

from models.expense_model import Expense, ExpenseCreate, ExpenseShare
from models.group_model import UserSummary

CENT = Decimal("0.01")


def split_equally(amount: Decimal, user_ids: list[int]) -> dict[int, Decimal]:
    """Reparte un importe a partes iguales entre los participantes.
    Cada uno recibe la parte redondeada hacia abajo al céntimo, y los céntimos
    sobrantes se reparten de uno en uno empezando por el menor user_id.
    Ejemplos: 10 € entre 3 → 3.34 + 3.33 + 3.33; 20 € entre 3 → 6.67 + 6.67 + 6.66.
    Si la parte base fuera 0 (0.02 € entre 3), a alguien le tocaría 0 €: 422.
    """
    ids = sorted(user_ids)
    count = len(ids)
    base = (amount / count).quantize(CENT, rounding=ROUND_DOWN)
    if base == 0:
        raise HTTPException(
            status_code=422,
            detail=f"El importe es demasiado pequeño para repartirlo entre {count} personas",
        )
    # céntimos que quedan sin repartir: siempre menos que el número de participantes
    leftover_cents = int((amount - base * count) / CENT)
    return {user_id: base + CENT if i < leftover_cents else base for i, user_id in enumerate(ids)}


async def get_expenses(
    conn: aiomysql.Connection, group_id: int, expense_id: int | None = None
) -> list[Expense]:
    """Gastos del grupo con quién los pagó y sus repartos, los más recientes primero.
    Con expense_id, devuelve solo ese gasto (para responder tras crearlo).
    Son dos consultas en total, no una por gasto: primero los gastos y después
    todos sus repartos, que se agrupan por gasto en Python.
    La condición (%s IS NULL OR e.id = %s) es la misma idea que en get_balances.
    """
    async with conn.cursor() as cursor:
        # gastos y su pagador (columnas payer_*, porque users y expenses comparten nombres)
        await cursor.execute(
            "SELECT e.id, e.title, e.description, e.amount, e.split_type, "
            "       e.expense_date, e.created_at, "
            "       u.id AS payer_id, u.name AS payer_name, "
            "       u.lastname AS payer_lastname, u.nickname AS payer_nickname "
            "FROM expenses e "
            "JOIN users u ON u.id = e.paid_by "
            "WHERE e.group_id = %s AND (%s IS NULL OR e.id = %s) "
            "ORDER BY e.expense_date DESC, e.id DESC",
            (group_id, expense_id, expense_id),
        )
        expense_rows = await cursor.fetchall()

        # repartos de esos gastos, por participante (menor user_id primero)
        await cursor.execute(
            "SELECT es.expense_id, es.amount, u.id, u.name, u.lastname, u.nickname "
            "FROM expense_shares es "
            "JOIN expenses e ON e.id = es.expense_id "
            "JOIN users u ON u.id = es.user_id "
            "WHERE e.group_id = %s AND (%s IS NULL OR e.id = %s) "
            "ORDER BY es.expense_id, u.id",
            (group_id, expense_id, expense_id),
        )
        share_rows = await cursor.fetchall()

    # repartos agrupados por gasto: {expense_id: [ExpenseShare, ...]}
    shares_by_expense: dict[int, list[ExpenseShare]] = {}
    for row in share_rows:
        shares_by_expense.setdefault(row["expense_id"], []).append(
            ExpenseShare(
                user=UserSummary(id=row["id"], name=row["name"], lastname=row["lastname"], nickname=row["nickname"]),
                amount=row["amount"],
            )
        )

    return [
        Expense(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            amount=row["amount"],
            split_type=row["split_type"],
            expense_date=row["expense_date"],
            created_at=row["created_at"],
            paid_by=UserSummary(
                id=row["payer_id"],
                name=row["payer_name"],
                lastname=row["payer_lastname"],
                nickname=row["payer_nickname"],
            ),
            shares=shares_by_expense.get(row["id"], []),
        )
        for row in expense_rows
    ]


async def create_expense(conn: aiomysql.Connection, group_id: int, expense: ExpenseCreate) -> Expense:
    """Crea un gasto con sus repartos, en una transacción.
    - El pagador o algún participante no es miembro accepted: 422.
    - Reparto igual con una parte de 0 €: 422 (split_equally).
    - Las partes no suman el importe: 422.
    Bloquea la fila del grupo, igual que remove_member: así no puede salir un
    miembro entre la comprobación de quiénes son miembros y el INSERT.
    """
    await conn.begin()
    try:
        async with conn.cursor() as cursor:
            # 1. bloquear la fila del grupo hasta el final de la transacción.
            #    El estado se vuelve a comprobar con la fila bloqueada, por si el
            #    grupo se ha cerrado después de pasar los permisos.
            await cursor.execute(
                "SELECT status FROM expense_groups WHERE id = %s FOR UPDATE",
                (group_id,),
            )
            group = await cursor.fetchone()
            if group is None:
                raise HTTPException(status_code=404, detail="Grupo no encontrado")
            if group["status"] == "closed":
                raise HTTPException(status_code=409, detail="El grupo está cerrado")

            # 2. miembros accepted del grupo: los únicos que pagan y participan
            await cursor.execute(
                "SELECT user_id FROM group_members WHERE group_id = %s AND status = 'accepted'",
                (group_id,),
            )
            members = {row["user_id"] for row in await cursor.fetchall()}

            # 3. el pagador y los participantes tienen que ser miembros accepted
            if expense.paid_by not in members:
                raise HTTPException(status_code=422, detail="El pagador debe ser miembro del grupo")
            participant_ids = [share.user_id for share in expense.shares]
            if any(user_id not in members for user_id in participant_ids):
                raise HTTPException(
                    status_code=422, detail="Todos los participantes deben ser miembros del grupo"
                )

            # 4. parte de cada participante: la calcula la API en el modo igual
            if expense.split_type == "equal":
                shares = split_equally(expense.amount, participant_ids)
            else:
                shares = {share.user_id: share.amount for share in expense.shares}

            # la suma de las partes tiene que ser exactamente el importe del gasto
            # (el modelo ya lo comprueba en custom; aquí se garantiza en los dos modos)
            if sum(shares.values()) != expense.amount:
                raise HTTPException(
                    status_code=422,
                    detail="La suma de las partes no coincide con el importe del gasto",
                )

            # 5. el gasto y sus partes
            await cursor.execute(
                "INSERT INTO expenses (group_id, paid_by, title, description, amount, split_type, expense_date) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    group_id,
                    expense.paid_by,
                    expense.title,
                    expense.description,
                    expense.amount,
                    expense.split_type,
                    expense.expense_date,
                ),
            )
            expense_id = cursor.lastrowid

            await cursor.executemany(
                "INSERT INTO expense_shares (expense_id, user_id, amount) VALUES (%s, %s, %s)",
                [(expense_id, user_id, amount) for user_id, amount in sorted(shares.items())],
            )
        await conn.commit()
    except Exception:
        # no se oculta el error: se deshace la transacción y se vuelve a lanzar
        await conn.rollback()
        raise

    created = await get_expenses(conn, group_id, expense_id)
    return created[0]
