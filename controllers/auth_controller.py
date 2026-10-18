import aiomysql
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool

from controllers.users_controller import get_by_id, get_by_login
from core.security import create_token, hash_password, verify_password
from models.user_model import Token, User, UserCreate, UserLogin

# Hash falso para que el login tarde lo mismo exista o no el usuario.
# Si el usuario no existe, se verifica la contraseña contra este hash:
# así nadie puede averiguar qué cuentas existen midiendo el tiempo de respuesta.
DUMMY_HASH = hash_password("contraseña-que-nunca-se-usa")


async def register(conn: aiomysql.Connection, user: UserCreate) -> User:
    """Crea el usuario y lo devuelve (sin contraseña)."""
    # Argon2 es lento a propósito: se calcula en otro hilo para no bloquear la app
    hashed_pass = await run_in_threadpool(hash_password, user.password)

    try:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO users (name, lastname, nickname, email, password_hash) "
                "VALUES (%s, %s, %s, %s, %s)",
                (user.name, user.lastname, user.nickname, user.email, hashed_pass),
            )
            new_id = cursor.lastrowid
    except aiomysql.IntegrityError as e:
        # 1062 = valor duplicado; el mensaje incluye el nombre de la restricción
        if e.args[0] == 1062:
            if "uq_users_email" in e.args[1]:
                raise HTTPException(status_code=409, detail="El email ya está registrado")
            if "uq_users_nickname" in e.args[1]:
                raise HTTPException(status_code=409, detail="El nickname ya está en uso")
        # cualquier otro error de integridad no es esperable: que siga su curso (500)
        raise

    # con autocommit=True el INSERT ya está guardado: no hace falta commit()
    return await get_by_id(conn, new_id)


async def login(conn: aiomysql.Connection, user_login: UserLogin) -> Token:
    """Comprueba las credenciales y devuelve el token de sesión."""
    user = await get_by_login(conn, user_login.login)

    # si el usuario no existe, se verifica igualmente contra el hash falso
    hashed_pass = user["password_hash"] if user else DUMMY_HASH
    valid = await run_in_threadpool(verify_password, user_login.password, hashed_pass)

    # mismo error si no existe o si la contraseña no coincide
    if not user or not valid:
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=create_token(user["id"]))