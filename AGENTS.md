# Comportamiento (común)

Compórtate como un programador web fullstack junior, antes de hacer nada, reflexiona y redacta por pasos todo lo que vas a hacer, para entenderlo y para darte el okey para proceder con el código. Con cualquier duda siempre preguntarás, no darás nada por hecho.

Este es el `AGENTS.md` del **back-end**. El proyecto tiene dos repositorios, cada uno con su propio `AGENTS.md`: [backend-proyecto-final](https://github.com/AaronPvon/backend-proyecto-final) y [frontend-proyecto-final](https://github.com/AaronPvon/frontend-proyecto-final).

Toda decisión nueva que se tome sobre el proyecto se documentará en el `AGENTS.md` del repositorio afectado. Las secciones marcadas con **(común)** están en los dos archivos y deben ser idénticas: si cambia una de ellas, se actualiza en los dos repositorios.

# Objetivo (común)

Desarrollar una aplicación web (SPA) con un front-end desarrollado en [Angular v22](https://angular.dev/events/v22) y un back-end formado por una API REST creada con Python y FastAPI que se conecta a una base de datos MySQL 8.

El back-end en Python con FastAPI y la base de datos MySQL son obligatorios: es lo que exige el proyecto y son las herramientas aprendidas. No se sustituyen por otras.

# Definición del Proyecto (común)

Nombre de la app: "A Pachas"

Aplicación para dividir gastos compartidos que se adapte a cualquier situación: una cena de amigos, un regalo de cumpleaños, un viaje, los gastos de una casa compartida, etc.

El proyecto se basa en el enunciado "Compartir gastos" (`docs/Compartir_gastos.pdf`, copiado en los dos repositorios). En caso de conflicto entre el enunciado y este archivo, prevalece el enunciado, salvo que aquí se documente expresamente otra decisión.

La gestión de pagos reales (transferencias, Bizum, etc.) se realiza fuera de la aplicación. La app solo registra y calcula.

## Repositorios del proyecto (común)

El proyecto se divide en dos repositorios:

- Back-end: [backend-proyecto-final](https://github.com/AaronPvon/backend-proyecto-final). API REST con FastAPI en la raíz del repositorio (sin carpeta `backend/`) y carpeta `database/` con el script y el diagrama.
- Front-end: [frontend-proyecto-final](https://github.com/AaronPvon/frontend-proyecto-final). Proyecto de Angular en la raíz del repositorio.

En local, los dos repositorios están dentro de una carpeta de trabajo `proyecto_final/` (`proyecto_final/backend/` y `proyecto_final/frontend/`, cada una con su propio `.git`). Esa carpeta no es un repositorio: no contiene archivos del proyecto.

```
backend-proyecto-final/
├── README.md
├── AGENTS.md
├── docs/              # Compartir_gastos.pdf (enunciado)
├── database/          # a_pachas.sql y diagrama_er.mermaid
└── (main.py, core/, db/, models/, controllers/, routes/...)

frontend-proyecto-final/
├── README.md
├── AGENTS.md
├── docs/              # Compartir_gastos.pdf (enunciado)
└── (proyecto de Angular: src/, public/, package.json...)
```

- Cada repositorio tiene su `README.md` y su `AGENTS.md`, y es autosuficiente. Los dos README enlazan al otro repositorio.
- Cada README repite la descripción, las funcionalidades y la autoría, y explica solo la puesta en marcha de su parte. El del back explica también cómo crear el usuario de MySQL `a_pachas_user` (`CREATE USER` + `GRANT ALL PRIVILEGES ON a_pachas_db.*`).
- El `AGENTS.md` y el `README.md` generales (del antiguo repositorio único) se reparten entre los dos repositorios y se borran, para que no haya tres versiones que se desincronicen.

## Conceptos clave (común)

- **Grupo**: conjunto de usuarios que comparten gastos. Tiene título, descripción, presupuesto opcional y moneda.
- **Creador**: usuario que crea el grupo. Es el único que lo gestiona (ver Roles y permisos). No existen varios administradores por grupo.
- **Miembro**: usuario con estado `accepted` en un grupo. El creador siempre es miembro de sus grupos.
- **Gasto**: dinero que un miembro ha pagado en nombre del grupo (antes llamado "pago").
- **Reparto**: parte de un gasto que corresponde a cada participante.
- **Liquidación**: transferencia entre dos miembros para saldar una deuda (ej. un Bizum de Luis a Ana).
- **Saldo**: lo que cada miembro debe o le deben dentro del grupo. Se calcula, no se guarda.
- **Presupuesto**: cantidad objetivo opcional del grupo (antes llamado "total"). Es solo informativo y no afecta a ningún cálculo.
- **Estado del grupo**: `active` (se puede gestionar) o `closed` (solo lectura). Los grupos nunca se borran.

## Principios del ciclo de vida (común)

Todo el ciclo de vida de grupos y miembros se resume en estas reglas:

1. Los grupos nunca se borran. Solo el creador los cierra (con aviso si hay saldos pendientes) y los reabre.
2. El creador nunca sale de sus grupos. Si quiere desentenderse de uno, lo cierra.
3. Un miembro sale del grupo, por voluntad propia o expulsado, solo si su saldo es 0. Después pasa a `left` y deja de ver el grupo.
4. Las invitaciones pendientes, rechazadas o anuladas se borran.
5. Solo los miembros `accepted` ven el grupo, esté activo o cerrado.

## Roles y permisos (común)

Solo existe un gestor por grupo: su creador. El resto de miembros únicamente visualizan los datos.

| Acción                                       | Creador                    | Miembro              | Invitado pendiente |
| -------------------------------------------- | -------------------------- | -------------------- | ------------------ |
| Editar el grupo                              | Sí                         | No                   | No                 |
| Cerrar y reabrir el grupo                    | Sí                         | No                   | No                 |
| Invitar usuarios                             | Sí                         | No                   | No                 |
| Expulsar miembros (solo con saldo 0)         | Sí                         | No                   | No                 |
| Abandonar el grupo                           | No (lo cierra en su lugar) | Sí, solo con saldo 0 | No                 |
| Crear, editar y eliminar gastos              | Sí                         | No                   | No                 |
| Registrar, editar y eliminar liquidaciones   | Sí                         | No                   | No                 |
| Ver gastos, repartos, liquidaciones y saldos | Sí                         | Sí                   | No                 |
| Ver título, descripción y creador del grupo  | Sí                         | Sí                   | Sí                 |
| Aceptar o rechazar la invitación             | —                          | —                    | Sí                 |

Un usuario con estado `left` no tiene ningún permiso sobre el grupo y no lo ve.

Si un usuario pide un grupo del que no es miembro (o del que salió, `left`), la API responde 404 y no 403, igual que si el grupo no existiera. Así, quien vaya probando ids no puede saber qué grupos existen.

Un invitado `pending` también recibe 404 en todos los endpoints de grupo. El título, la descripción y el creador del grupo, que sí puede ver, los recibe a través de `GET /api/invitations`, que es donde los necesita para decidir si acepta.

En un grupo cerrado nadie puede hacer cambios: solo se permite visualizar. La única excepción es que el creador puede reabrirlo.

Los permisos se comprueban siempre en la API, no solo en el front-end, centralizados en una única función de permisos que tenga en cuenta también el estado del grupo.

## Reglas de negocio (común)

### Usuarios

- El email y el nickname son únicos.
- El nickname tiene entre 3 y 50 caracteres y solo puede contener letras sin tildes ni ñ (`A-Z`, `a-z`), números, `_`, `.` y `-` (patrón `^[A-Za-z0-9_.-]{3,50}$`). Nunca puede contener `@`, para que no se confunda con un email en el login.
- La contraseña debe tener entre 8 y 128 caracteres. El máximo no es una regla de seguridad para el usuario, sino una protección del servidor: calcular un hash Argon2 es lento a propósito. Por el momento no se exigen más reglas.
- En el login solo se exige que la contraseña no llegue vacía (y el máximo de 128), para que los usuarios con contraseñas antiguas puedan entrar si algún día cambian las reglas.
- Al registrarse se quitan los espacios del principio y del final del nombre, los apellidos y el nickname, pero nunca de la contraseña.
- Las reglas del nickname y de la contraseña se validan solo en la API (modelos Pydantic), no con `CHECK` en la base de datos.
- El login se hace con email o nickname (en el mismo campo) y contraseña. Si el usuario no existe o la contraseña es incorrecta, la API devuelve el mismo error, para no revelar qué cuentas existen.
- La contraseña nunca se guarda en claro: se almacena su hash con Argon2id (librería argon2-cffi). No es reversible. Se mantiene Argon2id aunque en un ejercicio de clase se usó bcrypt, porque está decidido desde el inicio y los hashes de los datos de prueba son Argon2id.
- La eliminación de cuenta queda fuera del alcance inicial (ver Funcionalidades futuras).

### Grupos

- El título es obligatorio (entre 1 y 100 caracteres) y la descripción opcional (máximo 1000). Se quitan los espacios del principio y del final, y una descripción en blanco se guarda como `NULL`.
- La moneda se elige de una lista cerrada: `EUR` (por defecto) o `USD`. Se valida solo en la API; la columna sigue siendo `CHAR(3)`, así que para añadir otra moneda basta con incluirla en la lista del modelo.
- Los datos de usuario que se muestran dentro de un grupo (creador, miembros y saldos) son id, nombre, apellidos y nickname. Nunca el email: los compañeros de grupo no necesitan verlo.

### Invitaciones

- Cualquier usuario puede crear todos los grupos que necesite.
- Al crear un grupo, el creador se añade automáticamente como miembro con estado `accepted`.
- El creador invita a usuarios registrados buscándolos por email o nickname. La búsqueda es por coincidencia exacta, para no permitir listar usuarios.
- Si no existe ningún usuario con ese email o nickname, la API responde 404 "Usuario no encontrado". Es un riesgo aceptado: permite comprobar si un email está registrado, pero hay que haber iniciado sesión, solo se comprueba un valor exacto cada vez y no se obtiene ningún dato de la cuenta. Se descartó responder siempre lo mismo sin crear la invitación, porque la lista de invitaciones pendientes del grupo, que ven todos los miembros, lo delataría igualmente, y el creador no sabría que se ha equivocado al escribir el email.
- La invitación crea una fila en `group_members` con estado `pending`.
- Si el invitado acepta, su estado pasa a `accepted`. Si la rechaza, la fila se borra.
- La fecha de una invitación (`invited_at`) es el `updated_at` de su fila en `group_members`, no el `created_at`: al reinvitar a alguien que salió, la fila pasa de `left` a `pending` y `created_at` sería la fecha de la primera invitación.
- Respuestas: invitar devuelve 201 con la invitación; aceptar, rechazar, anular, salir y expulsar devuelven 204 sin contenido. Tras aceptar, el front-end muestra un mensaje con un enlace al grupo (con el `group_id` y el título que ya tiene de la lista de invitaciones), para que el usuario elija si entra o no.
- Una invitación pendiente no tiene gastos ni repartos asociados, por lo que se puede borrar sin descuadrar nada.
- Anular o rechazar una invitación borra la fila solo si su estado es `pending` (`DELETE ... AND status = 'pending'`): así nunca se puede borrar por esta vía a un miembro `accepted`.
- Si dos peticiones invitan a la vez al mismo usuario, la clave primaria de `group_members` impide la segunda fila, y su error 1062 se responde con el mismo 409 de invitación pendiente.
- Se puede volver a invitar a cualquier usuario que no sea miembro: si rechazó, se crea una invitación nueva; si salió del grupo (`left`), su fila vuelve a `pending`.
- Solo los miembros `accepted` participan en gastos, repartos y liquidaciones.
- Todos los miembros `accepted` pueden ver las invitaciones pendientes de su grupo (`GET /api/groups/{group_id}/invitations`). Solo el creador puede crearlas y anularlas.

### Salida y expulsión de miembros

- Abandonar el grupo y ser expulsado son la misma operación con distinto protagonista, y siguen la misma regla: el saldo del miembro debe ser exactamente 0.
- Por dentro comparten la misma función del controlador, pero tienen rutas distintas porque sus permisos son distintos: `POST /api/groups/{group_id}/leave` (el propio miembro) y `DELETE /api/groups/{group_id}/members/{user_id}` (el creador).
- Si el saldo no es 0, la app impide la operación e indica el saldo pendiente. Primero hay que saldar cuentas: el creador registra la liquidación y después ya se puede salir o expulsar.
- Errores: 404 "Miembro no encontrado" si la persona que sale no es miembro `accepted`; 409 "El creador no puede salir del grupo; puede cerrarlo"; 409 "El saldo del miembro no es 0 (-108.33 EUR). Hay que saldar las cuentas antes de que salga del grupo", con el saldo y la moneda del grupo.
- Al salir o ser expulsado, el estado del miembro pasa a `left`. Su fila se conserva porque sus gastos y repartos antiguos la referencian.
- Un miembro `left` deja de ver el grupo.
- El creador no puede abandonar ni ser expulsado de sus grupos.

### Cierre y reapertura del grupo

- Los grupos nunca se eliminan físicamente, ni ellos ni sus miembros, gastos, repartos o liquidaciones.
- Solo el creador puede cerrar el grupo. Pasa a estado `closed` y se guarda la fecha en `closed_at`.
- Si en ese momento hay saldos pendientes (algún saldo distinto de cero), la app muestra antes un aviso y pide confirmación. Si el creador confirma, el grupo se cierra igualmente.
- Al cerrar el grupo, las invitaciones pendientes se borran.
- Un grupo cerrado queda en solo lectura: la API rechaza cualquier creación, edición o borrado de gastos, repartos, liquidaciones, invitaciones, salidas y expulsiones.
- Los miembros `accepted` siguen viendo el grupo cerrado con todo su historial y sus saldos.
- El creador puede reabrir un grupo cerrado: vuelve a estado `active` y `closed_at` pasa a `NULL`.

### Gastos y repartos

- Solo el creador del grupo registra, edita y elimina gastos.
- Cada gasto indica quién lo pagó (`paid_by`), que debe ser un miembro `accepted`. Si el pagador o algún participante no es miembro `accepted`, la API responde 422 ("El pagador debe ser miembro del grupo" o "Todos los participantes deben ser miembros del grupo").
- Hay tres modos de reparto:
  1. **Iguales entre todos**: el importe se divide a partes iguales entre todos los miembros `accepted` (en la interfaz aparecen todos marcados por defecto).
  2. **Iguales entre algunos**: el importe se divide a partes iguales solo entre los participantes seleccionados.
  3. **Personalizado**: se introduce a mano la cantidad de cada participante. La interfaz puede permitir introducir porcentajes, que se convierten a importes antes de guardar.
- Los modos 1 y 2 se guardan con `split_type = 'equal'` y el modo 3 con `split_type = 'custom'`.
- En todos los modos, el backend calcula y guarda la parte de cada participante en `expense_shares`. El cálculo de saldos no depende del modo.
- La fecha del gasto (`expense_date`) es la de hoy por defecto y se puede cambiar a una fecha pasada, nunca futura (422). Puede ser distinta de la fecha en que se registra: por ejemplo, los gastos de un viaje que se apuntan al volver.
- Ninguna parte puede ser de 0 €. En el modo personalizado, cada parte debe ser mayor que 0. En el modo igual, si a algún participante le tocara 0 € (por ejemplo, 0,02 € entre 3), la API responde 422 "El importe es demasiado pequeño para repartirlo entre N personas".
- Los gastos en los que aparece un miembro `left` (como pagador o como participante) no se pueden editar ni borrar: 409 "El gasto incluye a alguien que ya no es miembro del grupo y no se puede modificar". Si se pudieran, el saldo de ese ex miembro dejaría de ser 0 y, como ya no es miembro, no podría saldarlo.
- La API valida, dentro de una transacción, que la suma de las partes sea exactamente igual al importe del gasto.
- Al crear un gasto, los participantes se envían en una sola lista `shares` para los dos tipos de reparto: con `split_type = 'equal'`, cada parte lleva solo el `user_id` (la API calcula los importes); con `split_type = 'custom'`, el `user_id` y su `amount`. Un participante no puede aparecer dos veces.
- En los repartos iguales no exactos, cada participante recibe primero la parte redondeada hacia abajo al céntimo, y los céntimos sobrantes se reparten de uno en uno empezando por el participante con menor `user_id`. Ejemplos: 10 € entre 3 → 3,34 + 3,33 + 3,33; 20 € entre 3 → 6,67 + 6,67 + 6,66.

### Liquidaciones

- Solo el creador del grupo registra, edita y elimina liquidaciones.
- Una liquidación indica quién paga (`from_user_id`), quién cobra (`to_user_id`) y el importe. Ambos deben ser miembros `accepted` y distintos entre sí.

### Saldos

El saldo de cada miembro se calcula con una consulta, nunca se guarda:

```
saldo = (suma de gastos que ha pagado)
      − (suma de sus partes en expense_shares)
      + (suma de liquidaciones que ha enviado)
      − (suma de liquidaciones que ha recibido)
```

Saldo positivo: le deben dinero. Saldo negativo: debe dinero.

### Presupuesto

- Es opcional. Si existe, debe ser mayor que 0 y tener como máximo 2 decimales y 10 cifras en total (como `DECIMAL(10,2)`): un importe con más decimales se rechaza en lugar de redondearse.
- Si existe, la vista del grupo muestra el gasto acumulado frente al presupuesto (por ejemplo, con una barra de progreso).

## Back-End

- Base de datos MySQL 8 llamada `a_pachas_db`, motor InnoDB, charset `utf8mb4` con collation `utf8mb4_0900_ai_ci`. Esta collation no distingue mayúsculas ni tildes, así que `Ana@example.com` y `ana@example.com` cuentan como el mismo email a efectos de unicidad.
- `a_pachas.sql` empieza con `SET NAMES utf8mb4` y se carga con `--default-character-set=utf8mb4`. Si el cliente de MySQL usa `latin1` por defecto, sin esto las tildes y la ñ se guardan mal codificadas ("García" pasa a ser "GarcÃ­a").
- Las restricciones se crean con nombre propio (`pk_`, `fk_`, `uq_`, `ck_` + tabla + campo) para que los errores de MySQL sean fáciles de identificar.
- API REST con Python y FastAPI.
- Versión de Python: 3.13 (estable). En local se usa la 3.13.16. El entorno virtual se llama `.venv` (en la raíz del repositorio) y se crea siempre con esta versión: en Windows, `py -3.13 -m venv .venv`.
- Librerías del back-end (elegidas por ser las vistas en clase):
  - **aiomysql**: conexión asíncrona a MySQL con consultas SQL directas y parametrizadas, sin ORM.
  - **python-jose**: creación y verificación de tokens JWT para la autenticación.
  - **argon2-cffi**: hash de contraseñas con Argon2id.
  - **python-dotenv**: lectura de las variables de entorno desde el archivo `.env`.
- Importes siempre como `DECIMAL(10,2)`, nunca `FLOAT`.
- Nombres de tablas y columnas en inglés, en `snake_case`.
- Los identificadores son `INT AUTO_INCREMENT`. Se valoró usar ids alfanuméricos (UUID o un id público aleatorio) para que no se puedan adivinar, pero se descartó: la protección real son la autenticación y la función de permisos, los UUID obligarían a rehacer el modelo y harían peor el rendimiento de MySQL, y la regla de reparto de céntimos se basa en el orden de `user_id`.

### Estructura del back-end

Sigue la organización de carpetas vista en clase:

```
backend-proyecto-final/   # raíz del repositorio del back
├── README.md
├── AGENTS.md
├── docs/                  # Compartir_gastos.pdf (enunciado)
├── database/              # a_pachas.sql y diagrama_er.mermaid
├── .env                   # no se sube al repositorio
├── .env.example
├── .gitignore
├── requirements.txt
├── main.py                # crea la app, CORS, lifespan (pool) y registra las rutas
├── core/
│   ├── security.py        # variables del JWT, hash y verificación de contraseñas, crear y decodificar tokens
│   ├── auth.py            # get_current_user: lee el token de cada petición protegida
│   └── permissions.py     # función única de permisos
├── db/
│   └── config.py          # load_dotenv, creación y cierre del pool, get_connection
├── models/                # modelos Pydantic de entrada y salida (no son tablas, no hay ORM): user_model.py...
├── controllers/           # consultas SQL y lógica de cada modelo de datos
└── routes/                # un fichero por ruta (health_routes.py, auth_routes.py...); reciben la petición y llaman al controlador
```

- Las rutas no contienen SQL ni lógica de negocio: validan la entrada con los modelos, llaman al controlador y devuelven la respuesta. No hay excepciones: incluso el `SELECT 1` de `GET /api/health` está en `controllers/health_controller.py`.
- La ruta raíz de cada router se declara como `""` y no como `"/"`. Con `"/"`, el endpoint queda en `/api/health/` (con barra final) y FastAPI responde con una redirección 307 a quien llama a `/api/health`.
- Los controladores contienen las consultas SQL y la lógica de cada modelo. El cálculo de saldos está en el controlador de grupos y el reparto de céntimos en el de gastos.
- Como en clase, los controladores reciben la conexión como primer parámetro y lanzan `HTTPException` con el código y el mensaje adecuados.
- A diferencia del ejercicio de clase, los controladores no envuelven todo en un `try/except Exception`: ese patrón captura también las `HTTPException` y las convierte en un 500 (un login incorrecto acababa respondiendo 500), y además envía al cliente el mensaje interno del error. Solo se capturan errores concretos y esperados, como el `IntegrityError` 1062 de un duplicado; cualquier otro error sale como 500 genérico, sin detalles.
- `core/auth.py` y `core/permissions.py` se añaden a la estructura de clase: el primero protege las rutas privadas y el segundo centraliza los permisos, como exige la sección Roles y permisos.
- A diferencia del `dependencies.py` de clase, que lo reunía todo, la autenticación ("¿quién eres?", `get_current_user`) va en `core/auth.py` y la autorización ("¿qué puedes hacer en este grupo?") en `core/permissions.py`. Las dependencias de permisos (`is_group_member` y, más adelante, `is_group_creator`) están en `permissions.py` junto a `check_group_access`, para que toda la lógica de permisos de grupo esté en un solo archivo y la puedan usar todos los archivos de rutas que cuelgan de `/api/groups/{group_id}`.
- La app se arranca desde la raíz del repositorio del back con `uvicorn main:app --reload`.
- Como en el ejercicio de clase, `main.py` registra cada router con `app.include_router(...)`, indicando ahí su prefijo (que empieza por `/api`) y su etiqueta para Swagger.
- CORS permite los orígenes de `CORS_ORIGINS`, todos los métodos y las cabeceras `Authorization` y `Content-Type`. No usa `allow_credentials`, porque el token viaja en la cabecera y no en cookies.

### Variables de entorno

| Variable             | Ejemplo                 | Descripción                                                          |
| -------------------- | ----------------------- | -------------------------------------------------------------------- |
| `DB_HOST`            | `localhost`             | Servidor de MySQL.                                                   |
| `DB_PORT`            | `3306`                  | Puerto de MySQL.                                                     |
| `DB_USER`            | `a_pachas_user`         | Usuario de MySQL con permisos sobre `a_pachas_db`.                   |
| `DB_PASSWORD`        |                         | Contraseña de ese usuario.                                           |
| `DB_NAME`            | `a_pachas_db`           | Nombre de la base de datos.                                          |
| `DB_POOL_MIN`        | `1`                     | Conexiones mínimas del pool.                                         |
| `DB_POOL_MAX`        | `10`                    | Conexiones máximas del pool.                                         |
| `JWT_SECRET_KEY`     |                         | Clave para firmar los tokens. Distinta en cada entorno.              |
| `JWT_ALGORITHM`      | `HS256`                 | Algoritmo de firma de los tokens.                                    |
| `JWT_EXPIRE_MINUTES` | `60`                    | Minutos de validez de cada token.                                    |
| `CORS_ORIGINS`       | `http://localhost:4200` | Orígenes permitidos por CORS, separados por comas si hay más de uno. |

- Se usa el prefijo `DB_` para las variables de la base de datos, aunque en el ejercicio de clase eran `MYSQL_*`, porque así está documentado desde el inicio.
- `JWT_SECRET_KEY` se genera con `python -c "import secrets; print(secrets.token_hex(32))"`.
- `load_dotenv()` se llama en `main.py`, `core/security.py` y `db/config.py`. Llamarlo varias veces no tiene efecto, y así cada archivo es independiente y no depende del orden de los imports.

### Conexión con la base de datos

- Se usa un pool de conexiones de aiomysql, creado una sola vez al arrancar la app (en el `lifespan` de FastAPI) y cerrado al apagarla.
- La dependencia `get_connection` presta una conexión del pool en cada petición (`async with pool.acquire()`) y la devuelve al terminar, aunque haya un error.
- Las filas se leen con `DictCursor`, como diccionarios.
- A diferencia del ejercicio de clase, que abría una conexión nueva en cada llamada (`aiomysql.connect`) y dejaba el cierre en manos de quien la usaba, aquí el pool reutiliza las conexiones y garantiza que se devuelven.
- El resto de módulos nunca importa el pool directamente: siempre piden la conexión con `Depends(get_connection)`.
- El pool trabaja con `autocommit=True` y `charset="utf8mb4"`. Con `autocommit=False`, InnoDB dejaría una transacción abierta tras cada `SELECT` y una conexión reutilizada podría leer datos desactualizados. Por eso una consulta suelta no necesita `commit()`.
- Patrón de transacción: `await conn.begin()`, los `INSERT`/`UPDATE` dentro de un `try`, `await conn.commit()` al final y, en el `except Exception`, `await conn.rollback()` seguido de `raise`. Ese `except` no contradice la regla de capturar solo errores concretos: no oculta el error ni lo convierte en un 500 con detalles, solo garantiza que nunca queda una transacción a medias.
- Las operaciones que dependen de los saldos bloquean la fila del grupo dentro de su transacción (`SELECT ... FROM expense_groups WHERE id = %s FOR UPDATE`): salir y expulsar (fase 3), y crear, editar y borrar gastos (fase 4) y liquidaciones (fase 5). Así no puede registrarse un gasto o una liquidación entre la comprobación del saldo de un miembro y su salida, y las cuentas nunca se descuadran.
- Las operaciones de varios pasos usan transacciones explícitas (`begin`, `commit` y `rollback` si algo falla): crear un grupo con su creador, crear o editar un gasto con sus repartos, cerrar un grupo y borrar sus invitaciones pendientes, y salir o expulsar a un miembro tras comprobar su saldo.
- Todas las consultas son parametrizadas (`%s`), nunca con f-strings.
- Los importes se manejan como `Decimal` en Python, nunca como `float`.
- En el JSON, los importes viajan como texto (`"176.66"`), que es como Pydantic serializa los `Decimal`. Así son exactos; el front-end los convierte a número solo para mostrarlos, porque en JavaScript los decimales en coma flotante no son exactos.
- Los errores de duplicado de MySQL (`IntegrityError` 1062) se traducen a un 409, usando el nombre de la restricción (`uq_users_email`, `uq_users_nickname`) para saber qué campo está repetido.
- El paquete `cryptography` es necesario para que aiomysql se autentique en MySQL 8 (`caching_sha2_password`). Se instala con `python-jose[cryptography]` y debe figurar en el `requirements.txt`. Sin él, la conexión solo funciona mientras MySQL tenga la contraseña en caché: tras reiniciar MySQL, o con una contraseña incorrecta, la app no arranca.

### Autenticación

- `POST /api/auth/login` recibe JSON: `{"login": "<email o nickname>", "password": "..."}` y devuelve `{"access_token": "...", "token_type": "bearer"}`.
- No se usa el formulario OAuth2 de FastAPI, que obligaría al front-end a enviar el login como formulario con un campo `username`.
- Las rutas privadas se protegen con `HTTPBearer` (`fastapi.security`), que lee la cabecera `Authorization: Bearer <token>` y muestra el botón "Authorize" en Swagger.
- El hash y la verificación de contraseñas se ejecutan con `run_in_threadpool` (`fastapi.concurrency`). Argon2 tarda unos 180 ms a propósito y, ejecutado directamente, bloquearía la app entera mientras tanto.
- Si el usuario del login no existe, la contraseña se verifica igualmente contra un hash falso (`DUMMY_HASH`), para que la respuesta tarde lo mismo y no se pueda averiguar qué cuentas existen midiendo el tiempo.
- Credenciales incorrectas: 401 "Credenciales incorrectas" (no 404, como en el ejercicio de clase).
- `get_current_user` decodifica el token, comprueba que no ha caducado y busca el usuario en la base de datos. Si algo falla, devuelve 401.
- `HTTPBearer` se usa con `auto_error=False` y el 401 lo lanza `get_current_user`, para que la respuesta sea siempre 401 (según la versión, FastAPI puede responder 403 si falta la cabecera). Mensajes: "No autenticado" si falta la cabecera y "Token no válido o caducado" en el resto de casos, siempre con la cabecera `WWW-Authenticate: Bearer`.
- Se comprueba que el usuario del token sigue existiendo: un token válido de un usuario dado de baja no debe funcionar.
- `get_current_user` y la ruta comparten la misma conexión del pool, porque FastAPI reutiliza las dependencias dentro de una misma petición.
- El token solo contiene `sub` (id del usuario, como texto) y `exp` (caducidad). La caducidad debe ir en el campo estándar `exp`: python-jose no valida otros nombres (en el ejercicio de clase se usaba `expire` y el token no caducaba nunca). Un JWT está firmado, no cifrado: su contenido se puede leer, así que nunca lleva datos sensibles.
- De momento no hay refresh token: al caducar el token (60 minutos) hay que volver a iniciar sesión.

### API

- Todas las rutas de la API llevan el prefijo `/api` y sus nombres están en inglés.
- Orden de desarrollo:
  1. Base y autenticación: `GET /api/health`, `POST /api/auth/register`, `POST /api/auth/login` y `GET /api/users/me`.
  2. Grupos en modo lectura: `GET /api/groups?status=active|closed`, `GET /api/groups/{id}` y `GET /api/groups/{id}/balances`. Aquí se crea `core/permissions.py`. Después, `POST /api/groups`.
  3. Invitaciones y miembros: invitar, aceptar, rechazar, salir y expulsar.
  4. Gastos con los tres modos de reparto.
  5. Liquidaciones.
  6. Cierre y reapertura de grupos.
- Cada parte del grupo tiene su propio endpoint, en lugar de devolverlo todo en `GET /api/groups/{id}`: el detalle (datos, creador, miembros y total gastado), `/balances` (saldos), `/expenses` (gastos con sus repartos, fase 4) y `/settlements` (liquidaciones, fase 5). Así cada fase añade su endpoint sin modificar los anteriores, y tras un cambio el front-end solo vuelve a pedir lo que ha cambiado. Al abrir la página del grupo, Angular lanza las peticiones a la vez (`forkJoin`).
- Los permisos de grupo siguen el patrón de dependencias de clase (`is_admin`, `is_owner_user`): una función única, `check_group_access`, en `core/permissions.py`, y dependencias que la llaman (`is_group_member` y, desde la fase 3, `is_group_creator`). Errores, comprobados en este orden: 404 "Grupo no encontrado" si no existe o el usuario no es miembro `accepted`; 403 "Solo el creador del grupo puede hacer esto" si es miembro pero no el creador e intenta gestionar; 409 "El grupo está cerrado" si es el creador e intenta cambiar algo en un grupo cerrado. La comprobación de miembro va siempre primero, para no revelar a quien no lo es si el grupo existe o está cerrado.
- La consulta que usa `check_group_access` (`get_access_info`) está en `controllers/groups_controller.py`, siguiendo la regla de que el SQL va siempre en los controladores.
- La acción `leave` (salir del grupo) exige ser miembro `accepted` y que el grupo esté activo, pero no ser el creador. Los permisos responden "¿puede quien hace la petición actuar en este grupo, en su estado actual?"; las reglas sobre la persona que sale (ser miembro, no ser el creador y tener saldo 0) las comprueba el controlador, en la función que comparten salir y expulsar.
- Con los datos de prueba, `GET /api/groups/{id}/balances` debe dar los mismos saldos que la consulta de comprobación del script: en "Viaje a Lisboa", Ana +176,66, Luis −108,33 y Marta −68,33; en "Piso compartido", Luis +10, Marta 0 y Pablo −10.

- Rutas de invitaciones y miembros (fase 3):
  - `routes/members_routes.py` (prefijo `/api/groups`): `GET /{group_id}/invitations` (miembros), `POST /{group_id}/invitations` (creador, body `{"login": "<email o nickname>"}`, 201 con la invitación), `DELETE /{group_id}/invitations/{user_id}` (creador, anula, 204), `POST /{group_id}/leave` (miembro, 204) y `DELETE /{group_id}/members/{user_id}` (creador, expulsa, 204).
  - `routes/invitations_routes.py` (prefijo `/api/invitations`): `GET ""` (mis invitaciones pendientes), `POST /{group_id}/accept` (aceptar, 204) y `DELETE /{group_id}` (rechazar, 204).

- Rutas de gastos (fase 4), en `routes/expenses_routes.py` (etiqueta `Expenses`, prefijo `/api/groups`): `GET /{group_id}/expenses` (miembros, también con el grupo cerrado) y `POST /{group_id}/expenses` (creador y grupo activo, 201 con el gasto).
- Cada gasto se devuelve con su pagador (`paid_by`) y sus repartos (`shares`), con el usuario anidado como `UserSummary`, igual que el creador de un grupo. El listado va de la fecha del gasto más reciente a la más antigua (y, en la misma fecha, del último registrado al primero).
- `get_expenses` hace dos consultas en total (los gastos y todos sus repartos), no una por gasto, y admite un `expense_id` opcional con la misma condición `(%s IS NULL OR e.id = %s)` que `get_balances`: así `create_expense` devuelve el gasto creado con la misma consulta que el listado.
- Las reglas que dependen de varios campos del formulario (participantes repetidos, importes según el tipo de reparto y suma de las partes en `custom`) se validan en el modelo con un `model_validator`, y Pydantic responde 422 con una lista de errores. Las que necesitan la base de datos (pagador y participantes `accepted`) y el reparto de céntimos están en el controlador, que responde 422 con un texto.
- `create_expense` bloquea la fila del grupo (`FOR UPDATE`) y vuelve a comprobar con ella bloqueada que el grupo sigue activo.

### Despliegue

- Durante el desarrollo, la app se ejecuta en local: MySQL 8 en `localhost` (gestionado con MySQL Workbench), con la base de datos creada a partir de `database/a_pachas.sql` y sus datos de prueba.
- La API se conecta con el usuario `a_pachas_user`, que en local tiene todos los permisos sobre `a_pachas_db` (puede ejecutar el script de creación). En el cloud se le darán solo los permisos de lectura y escritura de datos.
- Más adelante, la app se desplegará en un cloud de prácticas.
- Las credenciales y URLs (base de datos, clave de los tokens, origen permitido por CORS) irán en variables de entorno, nunca en el código, para poder cambiar de entorno sin tocarlo.
- En local, las variables de entorno se leen de un archivo `.env` que no se sube al repositorio (se incluye en `.gitignore`). Se proporciona un `.env.example` con los nombres de las variables, sin valores reales.

### Modelo de datos

```
users
  id              INT PK AUTO_INCREMENT
  name            VARCHAR(100) NOT NULL
  lastname        VARCHAR(150) NOT NULL
  nickname        VARCHAR(50)  NOT NULL UNIQUE
  email           VARCHAR(255) NOT NULL UNIQUE
  password_hash   VARCHAR(255) NOT NULL
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
  deleted_at      DATETIME NULL                 -- reservado para la futura eliminación de cuenta

expense_groups
  id              INT PK AUTO_INCREMENT
  title           VARCHAR(100) NOT NULL
  description     TEXT NULL
  budget          DECIMAL(10,2) NULL            -- presupuesto/objetivo opcional
  currency        CHAR(3) NOT NULL DEFAULT 'EUR'
  status          ENUM('active','closed') NOT NULL DEFAULT 'active'
  closed_at       DATETIME NULL
  created_by      INT NOT NULL FK → users.id    -- creador y único gestor
  created_at, updated_at

group_members
  group_id        INT FK → expense_groups.id ON DELETE RESTRICT  ┐ PK compuesta
  user_id         INT FK → users.id                             ┘
  status          ENUM('pending','accepted','left') NOT NULL DEFAULT 'pending'
  created_at, updated_at

expenses
  id              INT PK AUTO_INCREMENT
  group_id        INT NOT NULL FK → expense_groups.id ON DELETE RESTRICT
  paid_by         INT NOT NULL
  title           VARCHAR(100) NOT NULL
  description     TEXT NULL
  amount          DECIMAL(10,2) NOT NULL CHECK (amount > 0)
  split_type      ENUM('equal','custom') NOT NULL DEFAULT 'equal'
  expense_date    DATE NOT NULL
  created_at, updated_at
  FK (group_id, paid_by) → group_members(group_id, user_id)

expense_shares
  expense_id      INT FK → expenses.id ON DELETE CASCADE  ┐ PK compuesta
  user_id         INT FK → users.id                       ┘
  amount          DECIMAL(10,2) NOT NULL CHECK (amount >= 0)

settlements
  id              INT PK AUTO_INCREMENT
  group_id        INT NOT NULL FK → expense_groups.id ON DELETE RESTRICT
  from_user_id    INT NOT NULL                  -- quien paga la deuda
  to_user_id      INT NOT NULL                  -- quien la cobra
  amount          DECIMAL(10,2) NOT NULL CHECK (amount > 0)
  created_at, updated_at
  CHECK (from_user_id <> to_user_id)
  FK (group_id, from_user_id) → group_members(group_id, user_id)
  FK (group_id, to_user_id)   → group_members(group_id, user_id)
```

### Descripción de las tablas

#### `users`

Usuarios registrados en la app. Cada fila es una cuenta con sus datos personales y de acceso.

| Campo           | Descripción                                                                                                   |
| --------------- | ------------------------------------------------------------------------------------------------------------- |
| `id`            | Identificador único del usuario.                                                                              |
| `name`          | Nombre del usuario. Se usa, por ejemplo, en el saludo de la página de inicio.                                 |
| `lastname`      | Apellidos del usuario.                                                                                        |
| `nickname`      | Alias único. Sirve para iniciar sesión y para que el creador de un grupo lo encuentre al invitarle.           |
| `email`         | Correo único. Igual que el nickname, sirve para iniciar sesión y para invitarle a grupos.                     |
| `password_hash` | Hash de la contraseña. La contraseña original nunca se guarda.                                                |
| `created_at`    | Fecha de registro.                                                                                            |
| `updated_at`    | Fecha de la última modificación de los datos del usuario.                                                     |
| `deleted_at`    | Fecha de eliminación de la cuenta (borrado lógico). Siempre `NULL` hasta que se implemente esa funcionalidad. |

#### `expense_groups`

Grupos de gastos. Cada fila es un grupo con su información general y su estado.

| Campo         | Descripción                                                                                                            |
| ------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `id`          | Identificador único del grupo.                                                                                         |
| `title`       | Título del grupo (ej. "Viaje a Lisboa").                                                                               |
| `description` | Descripción u objetivo del grupo. Opcional.                                                                            |
| `budget`      | Presupuesto u objetivo de gasto. Opcional y solo informativo: no interviene en el cálculo de saldos.                   |
| `currency`    | Moneda del grupo en formato ISO de tres letras (por defecto `EUR`). Todos los importes del grupo están en esta moneda. |
| `status`      | Estado del grupo: `active` (se puede gestionar) o `closed` (solo lectura).                                             |
| `closed_at`   | Fecha en que se cerró el grupo. `NULL` mientras está activo.                                                           |
| `created_by`  | Usuario que creó el grupo, que es también su único gestor.                                                             |
| `created_at`  | Fecha de creación del grupo.                                                                                           |
| `updated_at`  | Fecha de la última modificación del grupo.                                                                             |

#### `group_members`

Relación entre usuarios y grupos (tabla intermedia de la relación N:M). Cada fila indica que un usuario está invitado a un grupo, es miembro de él o lo fue.

| Campo        | Descripción                                                                                                                                |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `group_id`   | Grupo al que pertenece la relación. Junto con `user_id` forma la clave primaria, por lo que un usuario solo aparece una vez en cada grupo. |
| `user_id`    | Usuario al que pertenece la relación.                                                                                                      |
| `status`     | Situación del usuario en el grupo: `pending` (invitado, aún no ha respondido), `accepted` (miembro) o `left` (salió o fue expulsado).      |
| `created_at` | Fecha de la invitación o, en el caso del creador, de la creación del grupo.                                                                |
| `updated_at` | Fecha del último cambio de estado (aceptar, salir, ser reinvitado...).                                                                     |

#### `expenses`

Gastos del grupo. Cada fila es un gasto que un miembro pagó en nombre del grupo (ej. la cena, la gasolina, el alojamiento).

| Campo          | Descripción                                                                                                                                                                                                  |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `id`           | Identificador único del gasto.                                                                                                                                                                               |
| `group_id`     | Grupo al que pertenece el gasto.                                                                                                                                                                             |
| `paid_by`      | Miembro que adelantó el dinero.                                                                                                                                                                              |
| `title`        | Concepto del gasto (ej. "Cena del sábado").                                                                                                                                                                  |
| `description`  | Detalle adicional del gasto. Opcional.                                                                                                                                                                       |
| `amount`       | Importe total del gasto. Siempre mayor que 0.                                                                                                                                                                |
| `split_type`   | Cómo se repartió: `equal` (a partes iguales, entre todos o entre algunos) o `custom` (importes personalizados). Sirve para que el formulario de edición sepa cómo mostrarse; el cálculo de saldos no lo usa. |
| `expense_date` | Fecha en que se produjo el gasto, que puede ser distinta de la fecha en que se registró.                                                                                                                     |
| `created_at`   | Fecha en que se registró el gasto en la app.                                                                                                                                                                 |
| `updated_at`   | Fecha de la última modificación del gasto.                                                                                                                                                                   |

#### `expense_shares`

Repartos de cada gasto. Cada fila indica cuánto le corresponde pagar a un participante de un gasto concreto. La suma de las partes de un gasto es siempre igual a su importe.

| Campo        | Descripción                                                                     |
| ------------ | ------------------------------------------------------------------------------- |
| `expense_id` | Gasto al que pertenece el reparto. Junto con `user_id` forma la clave primaria. |
| `user_id`    | Participante al que corresponde esta parte.                                     |
| `amount`     | Parte del gasto que le corresponde a ese participante. Puede ser 0.             |

Ejemplo: una cena de 30 € pagada por Ana y repartida entre Ana, Luis y Marta genera una fila en `expenses` (30 €, `paid_by` = Ana) y tres filas en `expense_shares` (10 € cada una).

#### `settlements`

Liquidaciones entre miembros. Cada fila registra una transferencia hecha fuera de la app para saldar una deuda (ej. un Bizum). No es un gasto del grupo: solo mueve saldo de un miembro a otro.

| Campo          | Descripción                                                       |
| -------------- | ----------------------------------------------------------------- |
| `id`           | Identificador único de la liquidación.                            |
| `group_id`     | Grupo en el que se salda la deuda.                                |
| `from_user_id` | Miembro que paga la deuda.                                        |
| `to_user_id`   | Miembro que recibe el dinero. Siempre distinto de `from_user_id`. |
| `amount`       | Importe transferido. Siempre mayor que 0.                         |
| `created_at`   | Fecha en que se registró la liquidación.                          |
| `updated_at`   | Fecha de la última modificación de la liquidación.                |

Siguiendo el ejemplo anterior: cuando Luis le hace un Bizum de 10 € a Ana, se registra una fila con `from_user_id` = Luis, `to_user_id` = Ana y `amount` = 10, y los saldos de ambos se compensan.

Notas del modelo:

- Las claves foráneas compuestas hacia `group_members` garantizan que solo los miembros de un grupo pueden pagar o liquidar en él. Que además tengan estado `accepted` lo comprueba la API.
- Esas mismas claves foráneas (con el comportamiento por defecto, `RESTRICT`) impiden borrar la fila de un miembro que tenga gastos o liquidaciones. Por eso solo se borran filas en estado `pending`, y quien sale del grupo pasa a `left` en lugar de borrarse.
- Las claves foráneas hacia `expense_groups` usan `ON DELETE RESTRICT`: un borrado físico accidental de un grupo falla en lugar de llevarse sus datos. El cierre se hace siempre cambiando `status`.
- `expense_shares` mantiene `ON DELETE CASCADE` respecto a `expenses`: cuando el creador borra un gasto de un grupo activo, se borran también sus repartos.
- No se guarda quién registró cada gasto o liquidación porque siempre es el creador del grupo.
- `expense_groups` tiene dos `CHECK` adicionales: `budget` debe ser mayor que 0 si existe, y `closed_at` tiene valor si y solo si `status = 'closed'`.
- Las claves foráneas compuestas permiten que un usuario `pending` o `left` figure como pagador o en una liquidación. Impedirlo es responsabilidad de la API, que solo admite miembros `accepted`.

### Cambios respecto a la propuesta inicial

- `groups` pasa a llamarse `expense_groups` (`GROUPS` es palabra reservada en MySQL 8).
- `users_groups` pasa a llamarse `group_members`, con clave primaria compuesta y estado (`pending`, `accepted`, `left`). Se elimina el campo `creator`: el creador se guarda en `expense_groups.created_by`.
- `payments` pasa a llamarse `expenses`. Se elimina la referencia redundante `id_user` + `id_user_group` y se sustituye por `group_id` + `paid_by`.
- `groups.total` pasa a ser `budget`, opcional.
- `password` pasa a ser `password_hash`.
- `modified_at` pasa a ser `updated_at`.
- `quantity` pasa a ser `amount`, de tipo `DECIMAL(10,2)`.
- Se añaden las tablas `expense_shares` (repartos) y `settlements` (liquidaciones).
- Se añaden restricciones `UNIQUE` en email y nickname, y `CHECK` en los importes.
- Se añaden `status` y `closed_at` a `expense_groups`: los grupos se cierran en lugar de borrarse.

# Funcionalidades futuras (común)

No se implementan todavía, pero el diseño debe permitir añadirlas sin rehacer el modelo.

- **Mensajería asíncrona entre los miembros de un grupo** ("should have" del enunciado). Tabla prevista:
  ```
  group_messages
    id          INT PK AUTO_INCREMENT
    group_id    INT NOT NULL FK → expense_groups.id ON DELETE RESTRICT
    user_id     INT NOT NULL
    content     TEXT NOT NULL
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    FK (group_id, user_id) → group_members(group_id, user_id)
  ```
- **Eliminación de cuenta.** Regla prevista: solo se podrá eliminar la cuenta con saldo 0 en todos los grupos activos; se hará con borrado lógico (`deleted_at`), y los grupos que haya creado el usuario se cerrarán automáticamente.
- Simplificación de deudas: calcular el mínimo número de transferencias para dejar todos los saldos a cero.
- Recuperación de contraseña y página de perfil.
- **Invitaciones a personas sin cuenta**: una tabla nueva (`group_invitations`) con el email invitado, que se asocia al usuario cuando se registra con ese email. Evitaría revelar si un email está registrado y permitiría invitar a amigos que aún no tienen cuenta. Requiere verificación de email (sin ella, cualquiera podría registrarse con el email de otro y quedarse con sus invitaciones), así que conviene hacerlo junto con la recuperación de contraseña, que también necesita enviar emails. Solo por email, nunca por nickname.
- Instalación de la app en el móvil (PWA).

# Decisiones pendientes (común)

- Qué cloud de prácticas se usará, ya que condiciona la configuración del despliegue.

# Estado actual

## Planificación de la entrega (común)

Cambio de planificación por la fecha de entrega (23/10/2026, antes de las 00:00):

- Se alterna back-end y front-end, priorizando los requisitos mínimos del enunciado.
- Estilos del front-end: Tailwind CSS y CSS propio.
- Alcance de la entrega: front-end de autenticación, grupos (listado, creación y detalle con saldos), invitaciones y gastos (listado y creación); back-end de la fase 4 reducida (`GET` y `POST /api/groups/{group_id}/expenses`).
- Quedan pendientes para después de la entrega: editar y borrar gastos, liquidaciones (fase 5), cierre y reapertura (fase 6), salir y expulsar desde la interfaz. El filtro de grupos cerrados se adelantó y ya está hecho (bloque 2 del front-end).
- Durante la entrega se prueba directamente en Swagger y en el navegador, sin scripts de pruebas temporales.
- Proyecto separado en dos repositorios (`backend-proyecto-final` y `frontend-proyecto-final`), cada uno con su `README.md` y su `AGENTS.md` (ver Repositorios del proyecto). ✅ Completado.

## Back-end

Fase de análisis completada y modelo de datos definido (versión 5). Librerías del back-end elegidas. Entorno de desarrollo local preparado: la base de datos `a_pachas_db` está creada en MySQL 8 (`localhost`) con los datos de prueba y el usuario `a_pachas_user`.

Diseño técnico del back-end decidido: estructura de carpetas, variables de entorno, gestión de la conexión con aiomysql, autenticación y orden de desarrollo de la API.

Generados y probados en MySQL 8.0:

- `database/a_pachas.sql`: creación de la base de datos y las tablas, datos de prueba y consulta de comprobación de saldos. Es un script de desarrollo: borra y recrea las tablas en cada ejecución.
- `database/diagrama_er.mermaid`: diagrama entidad-relación actualizado, que sustituye al `bbdd_proyecto.png` inicial.

Datos de prueba: cuatro usuarios (Ana, Luis, Marta y Pablo, todos con la contraseña `Pachas123!`, hasheada con Argon2id), un grupo activo con los tres modos de reparto y una invitación pendiente, y un grupo cerrado con un miembro `left` y un saldo pendiente.

Fase 1 del back-end (`health`, registro, login y usuario actual) ✅ completada, paso a paso:

1. Preparación del entorno (`requirements.txt`, `.gitignore`, `.env.example`, carpetas y entorno virtual con Python 3.13). Versiones del `requirements.txt` fijadas con `pip freeze`. ✅ Completado.
2. `db/config.py`: pool de conexiones. Probado con `test_db.py` (script temporal, ya borrado). ✅ Completado.
3. `main.py`: app, lifespan y CORS. Probado el arranque, el apagado y el fallo al arrancar con la contraseña incorrecta (error 1045). ✅ Completado.
4. `routes/health_routes.py` y `controllers/health_controller.py`. Probado en Swagger, también con MySQL parado y recuperado. ✅ Completado.
5. `core/security.py`: hash y verificación de contraseñas, `create_token` y `decode_token` (nombres de clase). Probado con `test_security.py` (12 pruebas, script temporal ya borrado). ✅ Completado.
6. `models/user_model.py`: modelos `User`, `UserCreate`, `UserLogin` y `Token` (nombres de clase). `User` nunca incluye la contraseña. Probado con `test_models.py` (23 pruebas, script temporal ya borrado). ✅ Completado.
7. `controllers/auth_controller.py` (`register`, `login`) y `controllers/users_controller.py` (`get_by_id`, `get_by_login`), con el reparto de clase. Probado con `test_controllers.py` (15 pruebas contra MySQL, script temporal ya borrado). ✅ Completado.
8. `routes/auth_routes.py`: registro (`create_user`, 201) y login (`login`), con los nombres de clase y `response_model`. Probado en Swagger. ✅ Completado.
9. `core/auth.py`: `get_current_user`. Probado en Swagger junto con el paso 10. ✅ Completado.
10. `routes/users_routes.py`: `GET /api/users/me` (`get_logged_user`, siguiendo el patrón `get_` de clase). Probado en Swagger: con token, sin token, token manipulado y caducado. ✅ Completado.
11. Pruebas finales en Swagger: recorrido completo desde la base de datos recién cargada (health, registro con tildes, login con nickname y con email, `/me` con y sin token). ✅ Completado.

Fase 2 del back-end (grupos en modo lectura, permisos y creación de grupos) ✅ completada, paso a paso:

1. `models/group_model.py`: `GroupCreate`, `UserSummary`, `Group`, `GroupDetail` y `Balance`. Probado con `test_group_models.py` (26 pruebas, script temporal ya borrado). ✅ Completado.
2. `core/permissions.py`: `check_group_access` (acciones `view` y `manage`) y la dependencia `is_group_member`. La consulta de acceso (`get_access_info`) va en `controllers/groups_controller.py`. Probado con `test_permissions.py` (13 casos con los datos de prueba, script temporal ya borrado). ✅ Completado.
3. `controllers/groups_controller.py`: `get_user_groups` (activos por `created_at` y cerrados por `closed_at`, los más recientes primero), `get_detail` (miembros por orden alfabético y total gastado) y `get_balances` (miembros `accepted` y `left`, por `user_id`). Probado con `test_groups_controller.py` (24 pruebas, script temporal ya borrado). ✅ Completado.
4. `routes/groups_routes.py`: `GET /api/groups`, `GET /api/groups/{group_id}` y `GET /api/groups/{group_id}/balances` (`get_user_groups`, `get_group_by_id` y `get_group_balances`, con el patrón `get_` de clase). El listado usa `get_current_user`; el detalle y los saldos, `is_group_member`. ✅ Completado.
5. Pruebas en Swagger con los cuatro usuarios de prueba: filtro de estado, invitado `pending` y miembro `left` (404), saldos esperados, sin token (401) y sin emails en las respuestas. ✅ Completado.
6. `POST /api/groups` (`create_group`, 201): crear el grupo y añadir al creador como `accepted`, en una transacción. Probado también el `rollback` con un trigger provisional que hacía fallar el segundo `INSERT`. Probado en Swagger. ✅ Completado.

Fase 3 del back-end (invitaciones y miembros) ✅ completada, en dos bloques (A: invitaciones; B: salidas y expulsiones), paso a paso:

1. `models/member_model.py`: `InvitationCreate`, `GroupInvitation` y `UserInvitation`. Probado con `test_member_models.py` (9 pruebas, script temporal ya borrado). ✅ Completado.
2. `core/permissions.py`: acción `leave` (miembro `accepted` y grupo activo) y dependencias `is_group_creator` (`manage`) y `can_leave_group` (`leave`). Probado con `test_permissions.py` (21 pruebas, script temporal ya borrado). ✅ Completado.
3. Bloque A, en dos partes:
   - 3a. Invitaciones desde el grupo: `invite_user`, `get_group_invitations` y `cancel_invitation` en `controllers/members_controller.py`, y `create_invitation` (201), `get_group_invitations` y `delete_invitation` (204) en `routes/members_routes.py` (etiqueta `Members`, prefijo `/api/groups`). Se añade `get_summary_by_login` a `users_controller.py`. Probado en Swagger (21 pruebas con los cuatro usuarios de prueba y un usuario nuevo). ✅ Completado.
   - 3b. Invitaciones desde el invitado: `get_user_invitations`, `accept_invitation` y `reject_invitation` en `controllers/members_controller.py`, y `get_user_invitations`, `accept_invitation` (204) y `reject_invitation` (204) en `routes/invitations_routes.py` (etiqueta `Invitations`, prefijo `/api/invitations`). No usan los permisos de grupo: cada consulta lleva `WHERE user_id = <usuario logado>`, así que cada usuario solo gestiona sus invitaciones y cualquier otra da 404. Probado en Swagger (23 pruebas, con un usuario nuevo que rechaza). ✅ Completado.
4. Bloque B: `remove_member` en `controllers/members_controller.py` (función compartida, en una transacción que bloquea el grupo), y `leave_group` (`POST /api/groups/{group_id}/leave`, 204) y `delete_member` (`DELETE /api/groups/{group_id}/members/{user_id}`, 204) en `routes/members_routes.py`. `get_balances` admite un `user_id` opcional para el saldo de un solo miembro. Probado también el bloqueo `FOR UPDATE`. Probado en Swagger (23 pruebas: salidas no permitidas, salida correcta, reinvitación y expulsiones). ✅ Completado.

Fase 4 del back-end (gastos y repartos), parte de la entrega completada, paso a paso:

1. `models/expense_model.py` (`ShareCreate`, `ExpenseCreate`, `ExpenseShare` y `Expense`) y la función `split_equally` (reparto de céntimos) en `controllers/expenses_controller.py`. ✅ Completado.
2. Listar y crear gastos: `get_expenses` y `create_expense` en `controllers/expenses_controller.py`, y `get_group_expenses` y `create_expense` (201) en `routes/expenses_routes.py`. Probado contra MySQL 8 con los datos de prueba (37 pruebas: repartos de céntimos, los tres modos, validaciones 422, permisos 403/404/409 y saldos que siguen sumando 0). ✅ Completado.
3. Editar y borrar gastos (`PUT` y `DELETE /api/groups/{group_id}/expenses/{expense_id}`). ⏳ Después de la entrega.
