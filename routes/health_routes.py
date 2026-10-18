import aiomysql
from fastapi import APIRouter, Depends

from controllers import health_controller
from db.config import get_connection

router = APIRouter()


# GET /api/health: comprueba que la API está viva y que llega a la base de datos.
# La ruta es "" y no "/" para que responda en /api/health, sin barra final.
@router.get("")
async def health(conn: aiomysql.Connection = Depends(get_connection)):
    await health_controller.check_database(conn)
    return {"status": "ok", "database": "ok"}