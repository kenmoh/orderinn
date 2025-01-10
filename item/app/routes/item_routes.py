from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.utils import Permission, Resource, UserRole, validate_token
from ..service.item_service import ItemService, StockAndInventoryService
from ..database.database import get_db
from ..schema.item_schemas import AddStockSchema, CreateItemSchema, InventoryReturnSchema, UpdateItemSchema

item_router = APIRouter(tags=["Item"], prefix="/api/v1/items")

item_service = ItemService()
inventory_service = StockAndInventoryService()


# =============== ITEM ===============
@item_router.get("/{company_id}", status_code=status.HTTP_200_OK)
async def get_items(
    company_id: str, db: AsyncSession = Depends(get_db)
) -> list[CreateItemSchema]:
    try:
        return await item_service.get_items(company_id=company_id, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@item_router.get("/{item_id}/item", status_code=status.HTTP_200_OK)
async def get_item(
    item_id: int, db: AsyncSession = Depends(get_db)
) -> CreateItemSchema:
    try:
        return await item_service.get_item(item_id=item_id, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@item_router.post("/{company_id}/create-item", status_code=status.HTTP_201_CREATED)
async def create_item(
    item: CreateItemSchema,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(validate_token),

) -> CreateItemSchema:

    try:
        return await item_service.create_item_with_inventory(
            company_id=user['id'],
            role=user['role'],
            resources=user['resources'],
            permissions=user['permissions'],
            db=db,
            item=item,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@item_router.patch("/{company_id}/update-item/{item_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_item(
    company_id: str,
    item_id: int,
    role: UserRole,
    permission: Permission,
    resource: Resource,
    item: UpdateItemSchema,
    db: AsyncSession = Depends(get_db),
) -> CreateItemSchema:
    try:
        return await item_service.update_item(
            item_id=item_id,
            company_id=company_id,
            role=role,
            resource=resource,
            permission=permission,
            db=db,
            item=item,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@item_router.delete("/{company_id}/delete-item/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    company_id: str,
    item_id: int,
    role: UserRole,
    permission: Permission,
    resource: Resource,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await item_service.delete_item(
            item_id=item_id,
            company_id=company_id,
            role=role,
            resource=resource,
            permission=permission,
            db=db
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =============== INVENTORY AND STOCL=K ===============
@item_router.get('/{company_id}/inventory', status_code=status.HTTP_200_OK)
async def get_company_inventories(company_id: str, db: AsyncSession = Depends(get_db)) -> list[InventoryReturnSchema]:
    try:
        return await inventory_service.get_inventories(company_id=company_id, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@item_router.get('/{company_id}/inventory/{item_id}', status_code=status.HTTP_200_OK)
async def get_company_inventory(company_id: str, inventory_id: int, db: AsyncSession = Depends(get_db)) -> InventoryReturnSchema:
    try:
        return await inventory_service.get_inventory(company_id=company_id, inventory_id=inventory_id, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@item_router.post('/{company_id}/new-stock/{inventory_id}', status_code=status.HTTP_201_CREATED)
async def add_new_stock(inventory_id: int, user_id: str, company_id: str, role: UserRole, resource: Resource, permission: Permission, stock: AddStockSchema, db: AsyncSession = Depends(get_db)) -> AddStockSchema:
    try:
        return await inventory_service.add_new_stock(
            company_id=company_id,
            inventory_id=inventory_id,
            user_id=user_id,
            db=db,
            role=role,
            permission=permission,
            resource=resource,
            stock=stock
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@item_router.patch('/{compnay_id}/update-stock/{stock_id}', status_code=status.HTTP_202_ACCEPTED)
async def update_stock(user_id: str, inventory_id: int, stock_id: str, role: UserRole, resource: Resource, permission: Permission, stock: AddStockSchema, db: AsyncSession = Depends(get_db)):

    try:
        return await inventory_service.update_stock(
            inventory_id=inventory_id,
            user_id=user_id,
            stock_id=stock_id,
            db=db,
            role=role,
            permission=permission,
            resource=resource,
            stock=stock
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
