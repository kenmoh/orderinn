from fastapi import APIRouter, Depends, status, HTTPException
import httpx

from ..auth.auth import get_current_user
from ..models.user_model import User
from ..service.order_service import OrderService
from ..schemas.order_schema import ItemSchema, OrderReturnSchema

order_router = APIRouter(tags=["Order"], prefix="/api/v1")

ORDER_SERVICE_URL = "127.0.0.5000"

order_service = OrderService()


@order_router.get("/orders", status_code=status.HTTP_200_OK)
async def all_orders():
    async with httpx.AsyncClient() as client:
        response = client.get(f"{ORDER_SERVICE_URL}/orders")
        return response.json()


@order_router.post("/orders", status_code=status.HTTP_200_OK)
async def create_orders(
    items: list[ItemSchema], current_user: User = Depends(get_current_user)
) -> OrderReturnSchema:
    try:
        return await order_service.create_order(
            company_id="6794411fc5636dba82ad25ad",
            room_no="310",
            items=items,
            current_user=current_user,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
