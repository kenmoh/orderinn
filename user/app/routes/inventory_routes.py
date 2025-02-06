from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from user.app.utils.utils import Permission, Resource

from ..auth.auth import get_current_user
from ..models.user_model import User
from ..service.item_service import InventoryService
from ..schemas.item_schema import (
    InventorySchecma,
    ItemStockReturnSchema,
    ItemStockSchema,
)

inventory_router = APIRouter(tags=["Inventory"], prefix="/api/v1")


inventory_service = InventoryService()

# ================= Item inventory =====================


@inventory_router.get("/{item_id}/item-inventory", status_code=status.HTTP_200_OK)
async def get_item_inventory(
    item_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
) -> InventorySchecma:
    """
    - Retrieve inventory for an item.

    - Args:
        - item_id: The ID of the item to retrieve
        - current_user: The current user making the request

    - Returns:
        - InventorySchema: The inventory data

    - Raises:
        - ServicePermissionError: If item not found or user doesn't have access

    """
    try:
        return await inventory_service.get_inventory(
            item_id=item_id,
            current_user=current_user,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@inventory_router.post("/{item_id}/item-inventory", status_code=status.HTTP_201_CREATED)
async def add_new_stock(
    item_id: PydanticObjectId,
    stock: ItemStockSchema,
    current_user: User = Depends(get_current_user),
) -> ItemStockReturnSchema:
    try:
        return await inventory_service.add_new_stock(
            item_id=item_id,
            current_user=current_user,
            stock=stock,
            operation=Permission.CREATE,
            resource=Resource.STOCK,
            role_permission=current_user.role_permissions,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@inventory_router.patch(
    "/{item_id}/item-inventory", status_code=status.HTTP_202_ACCEPTED
)
async def update_stock(
    item_id: PydanticObjectId,
    stock_id: PydanticObjectId,
    stock: ItemStockSchema,
    current_user: User = Depends(get_current_user),
) -> ItemStockReturnSchema:
    try:
        return await inventory_service.update_stock(
            stock_id=stock_id,
            item_id=item_id,
            current_user=current_user,
            stock=stock,
            operation=Permission.UPDATE,
            resource=Resource.STOCK,
            role_permission=current_user.role_permissions,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
