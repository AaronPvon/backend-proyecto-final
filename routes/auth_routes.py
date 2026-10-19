# Aquí van las rutas de registro y login (/api/auth)
import aiomysql
from fastapi import APIRouter, Depends

from controllers import auth_controller
from db.config import get_connection
from models.user_model import Token, User, UserCreate, UserLogin

router = APIRouter()


# Registro de un usuario: POST /api/auth/register
# 201 = creado. response_model=User garantiza que nunca sale la contraseña.
@router.post("/register", status_code=201, response_model=User)
async def create_user(user: UserCreate, conn: aiomysql.Connection = Depends(get_connection)):
    return await auth_controller.register(conn, user)


# Inicio de sesión: POST /api/auth/login
@router.post("/login", status_code=200, response_model=Token)
async def login(user_login: UserLogin, conn: aiomysql.Connection = Depends(get_connection)):
    return await auth_controller.login(conn, user_login)