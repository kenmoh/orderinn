from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from user.app.utils.utils import Permission, Resource

from ..auth.auth import get_current_user
from ..models.user_model import User
from ..service.item_service import ItemService
from ..schemas.item_schema import CreateItemReturnSchema, CreateItemSchema

item_router = APIRouter(tags=["Item"], prefix="/api/v1")

item_service = ItemService()


# ================= Item =====================


@item_router.get("/{company_id}/items", status_code=status.HTTP_200_OK)
async def get_items(
    comapny_id: PydanticObjectId, current_user: User = Depends(get_current_user)
) -> list[CreateItemReturnSchema]:
    try:
        return await item_service.get_company_items(company_id=comapny_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@item_router.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item(
    item: CreateItemSchema, current_user: User = Depends(get_current_user)
) -> CreateItemReturnSchema:
    try:
        return await item_service.create_item(
            current_user=current_user,
            item=item,
            operation=Permission.CREATE,
            resource=Resource.ITEM,
            role_permission=current_user.role_permissions,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@item_router.patch("/{item_id}/items", status_code=status.HTTP_202_ACCEPTED)
async def update_company_item(
    item_id: PydanticObjectId,
    item: CreateItemSchema,
    current_user: User = Depends(get_current_user),
) -> CreateItemReturnSchema:
    try:
        return await item_service.update_item(
            item_id=item_id,
            current_user=current_user,
            item=item,
            operation=Permission.UPDATE,
            resource=Resource.ITEM,
            role_permission=current_user.role_permissions,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@item_router.get("/items/{item_id}", status_code=status.HTTP_200_OK)
async def get_item(
    item_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
) -> CreateItemReturnSchema:
    try:
        await item_service.get_item(
            item_id=item_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@item_router.delete("/{item_id}/items", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company_item(
    item_id: PydanticObjectId,
    current_user: User = Depends(get_current_user),
):
    try:
        await item_service.delete_item(
            item_id=item_id,
            current_user=current_user,
            operation=Permission.DELETE,
            resource=Resource.ITEM,
            role_permission=current_user.role_permissions,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
