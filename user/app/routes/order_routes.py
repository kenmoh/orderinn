from fastapi import APIRouter, status

order_router = APIRouter(tags=["Order"], prefix="/api/v1")


@order_router.get("/orders", status_code=status.HTTP_200_OK)
async def all_orders():
    return {"Orders": "All Orders"}
