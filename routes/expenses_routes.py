# Aquí van las rutas de gastos de un grupo (/api/groups/{group_id}/expenses)
import aiomysql
from fastapi import APIRouter, Depends

from controllers import expenses_controller
from core.permissions import is_group_creator, is_group_member
from db.config import get_connection
from models.expense_model import Expense, ExpenseCreate
from models.user_model import User

router = APIRouter()


# Obtener los gastos del grupo con sus repartos: GET /api/groups/{group_id}/expenses
# Los ven todos los miembros, también con el grupo cerrado.
@router.get("/{group_id}/expenses", status_code=200, response_model=list[Expense])
async def get_group_expenses(
    group_id: int,
    current_user: User = Depends(is_group_member),
    conn: aiomysql.Connection = Depends(get_connection),
):
    return await expenses_controller.get_expenses(conn, group_id)


# Crear un gasto: POST /api/groups/{group_id}/expenses
# Solo el creador, y con el grupo activo. 201 con el gasto y sus repartos.
@router.post("/{group_id}/expenses", status_code=201, response_model=Expense)
async def create_expense(
    group_id: int,
    expense: ExpenseCreate,
    current_user: User = Depends(is_group_creator),
    conn: aiomysql.Connection = Depends(get_connection),
):
    return await expenses_controller.create_expense(conn, group_id, expense)
