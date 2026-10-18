import aiomysql


async def check_database(conn: aiomysql.Connection):
    """Comprueba que la base de datos responde ejecutando una consulta mínima.
    Si MySQL no responde, la consulta lanza una excepción y la petición falla.
    """
    async with conn.cursor() as cur:
        await cur.execute("SELECT 1")