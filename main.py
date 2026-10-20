import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.config import close_pool, create_pool
from routes import groups_routes, users_routes, auth_routes, health_routes

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Al arrancar: se crea el pool de conexiones con MySQL.
    # Si falla (contraseña mal, MySQL apagado...), la app no llega a arrancar.
    await create_pool()
    yield
    # Al apagar (Ctrl+C): se cierra el pool.
    await close_pool()


# levantamos el servidor de FastAPI
app = FastAPI(title="A Pachas API", version="0.1.0", lifespan=lifespan)

# CORS: orígenes que pueden llamar a la API desde el navegador (el front de Angular).
# Se leen del .env, separados por comas.
origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    # Authorization es imprescindible: el interceptor de Angular envía ahí el token
    allow_headers=["Authorization", "Content-Type"],
)

# Rutas
# Estado de la conexión con la bases de datos
app.include_router(health_routes.router, prefix="/api/health", tags=["Health"])
# Autenticación de usuarios (registro y login)
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Auth"])
# Obtiene el usuario logado
app.include_router(users_routes.router, prefix="/api/users", tags=["Users"])
# Obtiene toda la información de los grupos
app.include_router(groups_routes.router, prefix="/api/groups", tags=["Groups"])