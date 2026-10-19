# Aquí van las rutas de usuarios (/api/users)
from fastapi import APIRouter, Depends

from core.auth import get_current_user
from models.user_model import User

router = APIRouter()

# Obtener el usuario logado: GET /api/users/me
# No necesita controlador: get_current_user ya ha buscado al usuario en la base de datos.
@router.get("/me", status_code=200, response_model=User)
async def get_logged_user(current_user: User = Depends(get_current_user)):
    return current_user