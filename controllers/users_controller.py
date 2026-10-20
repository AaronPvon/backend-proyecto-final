import aiomysql

from models.user_model import User

from models.group_model import UserSummary


async def get_by_id(conn: aiomysql.Connection, user_id: int) -> User | None:
    """Devuelve el usuario con ese id, o None si no existe o está dado de baja."""
    async with conn.cursor() as cursor:
        await cursor.execute(
            "SELECT id, name, lastname, nickname, email, created_at "
            "FROM users "
            "WHERE id = %s AND deleted_at IS NULL",
            (user_id,),
        )
        row = await cursor.fetchone()
    return User(**row) if row else None


async def get_by_login(conn: aiomysql.Connection, login: str) -> dict | None:
    """Busca un usuario por email o nickname y devuelve su id y su hash.
    Es solo para el login: el hash nunca sale de los controladores.
    Como el nickname no puede contener @, un mismo texto nunca coincide
    con el email de un usuario y el nickname de otro.
    """
    async with conn.cursor() as cursor:
        await cursor.execute(
            "SELECT id, password_hash "
            "FROM users "
            "WHERE (email = %s OR nickname = %s) AND deleted_at IS NULL",
            (login, login),
        )
        return await cursor.fetchone()

async def get_summary_by_login(conn: aiomysql.Connection, login: str) -> UserSummary | None:
    """Busca un usuario por email o nickname exacto y devuelve sus datos básicos (sin email).
    Se usa para invitar a un usuario a un grupo. No devuelve el hash, a
    diferencia de get_by_login, que es solo para el login.
    """
    async with conn.cursor() as cursor:
        await cursor.execute(
            "SELECT id, name, lastname, nickname "
            "FROM users "
            "WHERE (email = %s OR nickname = %s) AND deleted_at IS NULL",
            (login, login),
        )
        row = await cursor.fetchone()
    return UserSummary(**row) if row else None