import os

import aiomysql
from dotenv import load_dotenv

load_dotenv()

# Variables sin las que no se puede conectar con MySQL.
REQUIRED_VARS = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]

# Pool de conexiones. Se crea al arrancar la app (lifespan de main.py)
# y se cierra al apagarla. El resto de módulos no lo importan: piden la
# conexión con Depends(get_connection).
pool = None


def check_env_vars():
    """Comprueba que el .env tiene las variables obligatorias con valor."""
    missing = [name for name in REQUIRED_VARS if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Faltan variables en el .env: {', '.join(missing)}")


async def create_pool():
    """Crea el pool de conexiones con MySQL. Se llama una sola vez al arrancar."""
    global pool
    check_env_vars()
    pool = await aiomysql.create_pool(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        minsize=int(os.getenv("DB_POOL_MIN", "1")),
        maxsize=int(os.getenv("DB_POOL_MAX", "10")),
        charset="utf8mb4",
        autocommit=True,                 # una consulta suelta se guarda sola
        cursorclass=aiomysql.DictCursor,  # las filas llegan como diccionarios
    )


async def close_pool():
    """Cierra el pool y espera a que terminen sus conexiones. Se llama al apagar."""
    if pool is not None:
        pool.close()
        await pool.wait_closed()


async def get_connection():
    """Dependencia de FastAPI: presta una conexión del pool durante una petición.
    Al terminar la petición, aunque haya un error, la conexión vuelve al pool.
    """
    async with pool.acquire() as conn:
        yield conn