import aiomysql
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from controllers import users_controller
from core.security import decode_token
from db.config import get_connection
from models.user_model import User

# Lee la cabecera "Authorization: Bearer <token>" y añade el botón
# "Authorize" en Swagger. Con auto_error=False, si falta la cabecera
# devuelve None y el 401 lo lanzamos nosotros (así siempre es 401).
bearer_scheme = HTTPBearer(auto_error=False)


def unauthorized(detail: str) -> HTTPException:
    """Error 401 con la cabecera WWW-Authenticate que indica el estándar."""
    return HTTPException(
        status_code=401,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    conn: aiomysql.Connection = Depends(get_connection),
) -> User:
    """Dependencia de las rutas privadas: devuelve el usuario del token o responde 401.
    FastAPI reutiliza get_connection dentro de una misma petición, así que
    esta dependencia y la ruta comparten la misma conexión del pool.
    """
    # 1. tiene que haber cabecera Authorization con formato Bearer
    if credentials is None:
        raise unauthorized("No autenticado")

    # 2. el token tiene que ser válido: ni caducado, ni manipulado, ni de otra clave
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise unauthorized("Token no válido o caducado")

    # 3. sub tiene que existir y ser un número (create_token lo guarda como texto)
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub.isdigit():
        raise unauthorized("Token no válido o caducado")

    # 4. el usuario tiene que seguir existiendo
    user = await users_controller.get_by_id(conn, int(sub))
    if user is None:
        raise unauthorized("Token no válido o caducado")

    return user