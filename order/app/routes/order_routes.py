import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from ..service.order_services import OrderService
from ..database.database import get_db
from ..schema.schemas import ItemSchema, OrderReturnSchema, PaymentProvider, PaymentType


order_service = OrderService()
order_router = APIRouter(tags=["Order"], prefix="/api/v1/order")


@order_router.post("/orders", status_code=status.HTTP_200_OK)
async def get_orders():
    return {"message": 'Hello from order service.'}


@order_router.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order(
    guest_id: str,
    company_id: str,
    room_number: str,
    sk: str,
    customer_email: EmailStr,
    payment_provider: PaymentProvider,
    payment_type: PaymentType,
    items: list[ItemSchema],
    db: AsyncSession = Depends(get_db),
) -> OrderReturnSchema:
    try:
        return await order_service.create_order(
            guest_id=guest_id,
            company_id=company_id,
            room_number=room_number,
            sk=sk,
            payment_provider=payment_provider,
            payment_type=payment_type,
            items=items,
            db=db,
            customer_email=customer_email,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
