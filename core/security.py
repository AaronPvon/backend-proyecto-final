import os
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from dotenv import load_dotenv
from jose import JWTError, jwt

# cargar las variables de entorno
load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# sin clave no se pueden firmar tokens: la app no debe arrancar
if not SECRET_KEY:
    raise RuntimeError("Falta la variable JWT_SECRET_KEY en el .env")

# hasher de Argon2id con los parámetros por defecto de argon2-cffi
# (t=3, m=65536, p=4), los mismos de los hashes de los datos de prueba
ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Devuelve el hash Argon2id de la contraseña, que es lo que se guarda en password_hash."""
    return ph.hash(password)


def verify_password(plaintext_password: str, hashed_password: str) -> bool:
    """Comprueba si la contraseña en texto plano corresponde al hash guardado.
    argon2-cffi no devuelve False cuando no coincide: lanza una excepción.
    Se captura para devolver True o False. También se devuelve False si el
    hash guardado está dañado, para que el login no responda con un error 500.
    """
    try:
        # ojo: verify recibe primero el hash y después la contraseña
        return ph.verify(hashed_password, plaintext_password)
    except (VerificationError, InvalidHashError):
        return False


def create_token(user_id: int) -> str:
    """Crea el token de sesión del usuario.
    Solo lleva dos datos:
    - sub: id del usuario, como texto (el estándar JWT exige que sea texto).
    - exp: fecha de caducidad. Tiene que llamarse exactamente "exp" para que
      python-jose rechace el token cuando caduque.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    data_to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(data_to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decodifica el token y devuelve su contenido (payload).
    Devuelve None si el token no es válido: caducado, manipulado o firmado
    con otra clave. Responder 401 es trabajo de core/auth.py.
    """
    try:
        # algorithms como lista cerrada: no se acepta ningún otro algoritmo
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None