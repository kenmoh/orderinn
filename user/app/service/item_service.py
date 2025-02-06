import datetime

from beanie import DeleteRules, PydanticObjectId, WriteRules
from sqlalchemy.ext.asyncio import AsyncSession
from beanie.odm.operators.find.logical import Or, And

from ..models.user_model import User

from ..models.item_model import ItemStock, Item
from ..schemas.item_schema import (
    CreateItemReturnSchema,
    CreateItemSchema,
    InventorySchecma,
    ItemStockSchema,
)
from ..utils.utils import ServicePermissionError, UserRole, Permission, Resource


class ItemService:
    def has_permission(
        self, role_permissions: list, resource: Resource, operation: Permission
    ) -> bool:
        """
        Check if the user role has permission to operate on a resource.

        Args:
            role_permissions (list): The list of role permissions from the user data.
            resource (str): The resource to check permissions for (e.g., 'user', 'item').
            operation (str): The operation to check (e.g., 'create', 'read', 'update', 'delete').

        Returns:
            bool: True if the user has the permission, False otherwise.
        """
        for permission in role_permissions:
            if permission.resource == resource and operation in permission.permission:
                return True
        return False

    # def check_authorization_for_item(
    #     self, role: UserRole, permissions: list[Permission], resources: list[Resource]
    # ) -> bool:
    #     """
    #     Check if user has required role and permission for a resource
    #     Returns True if authorized, False otherwise
    #     """

    #     required_resource = [
    #         "Resource.PAYMENT",
    #         "Resource.USER",
    #         "Resource.STOCK",
    #         "Resource.ITEM",
    #         "Resource.ORDER",
    #     ]

    #     required_permission = [
    #         "Permission.READ",
    #         "Permission.DELETE",
    #         "Permission.CREATE",
    #         "Permission.UPDATE",
    #     ]

    #     # Check if user has the required role, permission and resource
    #     return (
    #         role
    #         and (permissions == required_permission)
    #         and (resources == required_resource)
    #     )

    async def get_company_items(self, company_id: PydanticObjectId):
        return await Item.find(Item.company_id == company_id).to_list()

    async def get_item(self, item_id: PydanticObjectId):
        item = await Item.find_one(Item.id == item_id)
        if not item:
            raise ServicePermissionError("Item not found.")

        return item

    async def create_item(
        self,
        current_user: User,
        role_permission: UserRole,
        resource: Resource,
        operation: Permission,
        item: CreateItemSchema,
    ) -> CreateItemReturnSchema:
        """
        Creates a new item along with its inventory for a given company.

        Args:
            company_id (str): The UUID of the company.
            role (str): The role of the user attempting to create the item.
            resources (str): The resource being accessed.
            permissions (str): The permission level required to create the item.
            item (CreateItemSchema): The schema containing item details.

        Returns:
            Item: The newly created item if successful.
            str: "Permission denied!" if the user lacks the necessary permissions.

        Raises:
            HTTPException: If there is an error during item creation.
        """

        if not self.has_permission(
            role_permissions=role_permission, resource=resource, operation=operation
        ):
            raise ServicePermissionError("Permission deinied!")

        company_id = (
            current_user.company_id if current_user.company_id else current_user.id
        )

        new_item = Item(
            company_id=company_id,
            name=item.name,
            user_id=current_user.id,
            category=item.category,
            description=item.description,
            price=item.price,
            image_url=item.image_url,
            unit=item.unit,
            reorder_point=item.reorder_point,
        )

        return await new_item.save()

    async def update_item(
        self,
        item_id: PydanticObjectId,
        current_user: User,
        role_permission: UserRole,
        resource: Resource,
        operation: Permission,
        item: CreateItemSchema,
    ) -> CreateItemReturnSchema:
        """
        Update an existing item in the database.

        Args:
            item_id (int): The ID of the item to update.
            company_id (uuid.UUID): The UUID of the company that owns the item.
            role (str): The role of the user attempting to update the item.
            resource (str): The resource being accessed.
            permission (str): The permission level required to update the item.
            item (UpdateItemSchema): The schema containing the updated item data.
            db (AsyncSession): The asynchronous database session.

        Returns:
            Item: The updated item if the update is successful.
            str: An error message if the update is not authorized or the item does not belong to the company.
        """
        db_item: Item = await Item.find(
            Item.id == item_id,
            Item.company_id == current_user.company_id,
            Item.user_id == current_user.id,
        ).first_or_none()
        if not db_item:
            raise ServicePermissionError("Item not found")

        if not self.has_permission(
            role_permissions=role_permission, resource=resource, operation=operation
        ):
            raise ServicePermissionError("Permission deinied!")

        db_item.name = item.name
        db_item.category = item.category
        db_item.price = item.price
        db_item.image_url = item.image_url
        db_item.description = item.description
        db_item.unit = item.unit
        db_item.reorder_point = item.reorder_point

        return await db_item.save()

    async def delete_item(
        self,
        item_id: int,
        current_user: User,
        role_permission: UserRole,
        resource: Resource,
        operation: Permission,
    ):
        """
        Delete an item from the db
        """
        try:
            company_id = (
                current_user.company_id if current_user.company_id else current_user.id
            )

            db_item: Item = await Item.find(
                Item.id == item_id,
                Item.company_id == company_id,
                Item.user_id == current_user.id,
                fetch_links=True,
            ).first_or_none()

            if not db_item:
                raise ServicePermissionError("You can only delete item you created.")

            if not self.has_permission(
                role_permissions=role_permission, resource=resource, operation=operation
            ):
                raise ServicePermissionError("Permission deinied!")

            await db_item.delete(link_rule=DeleteRules.DELETE_LINKS)

        except Exception as e:
            raise ValueError("Failed to delete", str(e))


class InventoryService:
    async def get_inventories(self, company_id: str, db: AsyncSession):
        """
        Retrieve all inventories with associated item details for a specific company.

        Args:
            company_id (str): The unique identifier of the company
            db (AsyncSession): The database session for executing queries

        Returns:
            list[dict]: A list of dictionaries containing inventory details:
                - item_id (int): The unique identifier of the item
                - quantity (int): Current stock quantity
                - company_id (str): The company identifier
                - name (str): Item name
                - price (float): Item price
                - unit (str): Unit of measurement
                - category (str): Item category
                - updated_at (datetime): Last update timestamp

        """

    async def get_inventory(
        self,
        item_id: PydanticObjectId,
        current_user: User,
    ) -> InventorySchecma:
        """
        Retrieve inventory for an item.

        Args:
            item_id: The ID of the item to retrieve
            current_user: The current user making the request

        Returns:
            InventorySchema: The inventory data

        Raises:
            ServicePermissionError: If item not found or user doesn't have access

        """
        company_id = (
            current_user.company_id if current_user.company_id else current_user.id
        )
        item_inventory = await Item.find(
            Item.id == item_id, Item.company_id == company_id, fetch_links=True
        ).first_or_none()

        if not item_inventory:
            raise ServicePermissionError("Item not found")

        try:
            inventory = InventorySchecma(
                id=item_inventory.id,
                name=item_inventory.name,
                description=item_inventory.description,
                price=item_inventory.price,
                image_url=item_inventory.image_url,
                category=item_inventory.category,
                quantity=item_inventory.quantity,
                unit=item_inventory.unit,
                reorder_point=item_inventory.reorder_point,
                stocks=[
                    ItemStockSchema(quantity=stock.quantity, notes=stock.notes)
                    for stock in item_inventory.stocks
                ],
            )

            return inventory
        except Exception as e:
            raise ValueError(f"Failed to retrieve inventory: {str(e)}")

    async def add_new_stock(
        self,
        item_id: PydanticObjectId,
        current_user: User,
        role_permission: UserRole,
        resource: Resource,
        operation: Permission,
        stock: ItemStockSchema,
    ) -> ItemStockSchema:
        # Get MongoDB client
        """
        Add new stock to inventory
        Args:
            inventory_id (int): The ID of the inventory to which the stock will be added.
            user_id (str): The ID of the user adding the stock.
            company_id (str): The ID of the company to which the inventory belongs.
            role (str): The role of the user adding the stock.
            resource (str): The resource being accessed.
            permission (str): The permission level of the user.
            stock (AddStockSchema): The schema containing the stock details to be added.
            db (AsyncSession): The database session for executing queries.
        Returns:
            Stock: The newly added stock object if successful.
            str: An error message if authorization fails or if the inventory does not belong to the company.
        Raises:
            SQLAlchemyError: If there is an error committing the transaction to the database.
        """
        item: Item = await Item.find(Item.id == item_id).first_or_none()

        if not item:
            raise ServicePermissionError("Item not found.")

        if not ItemService().has_permission(
            role_permissions=role_permission, operation=operation, resource=resource
        ):
            raise ServicePermissionError("Permission denied.")

        new_stock = ItemStock(
            user_id=current_user.id,
            item_id=item.id,
            company_id=current_user.company_id
            if current_user.company_id
            else current_user.id,
            notes=stock.notes,
            quantity=stock.quantity,
        )
        # await new_stock.save()

        item.quantity += new_stock.quantity
        item.stocks.append(new_stock)
        await item.save(link_rule=WriteRules.WRITE)

        return new_stock

    async def update_stock(
        self,
        item_id: PydanticObjectId,
        stock_id: PydanticObjectId,
        current_user: User,
        role_permission: UserRole,
        resource: Resource,
        operation: Permission,
        stock: ItemStockSchema,
    ):
        """
        Updates the stock information for a given inventory and stock ID.

        Args:
            inventory_id (str): The ID of the inventory to update.
            user_id (str): The UUID of the user performing the update.
            stodk_id (str): The ID of the stock to update.
            role (str): The role of the user.
            resource (str): The resource being accessed.
            permission (str): The permission level of the user.

        Returns:
            Stock: The updated stock object if successful.
            str: 'Permission denied!' if the user does not have the required permissions.
        """
        company_id = (
            current_user.company_id if current_user.company_id else current_user.id
        )
        item = await Item.find(
            Item.id == item_id, Item.company_id == company_id
        ).first_or_none()
        existing_stock: ItemStock = await ItemStock.find(
            ItemStock.id == stock_id, ItemStock.user_id == current_user.id
        ).first_or_none()

        # Remove existing stock quantity from item quantity
        item.quantity -= existing_stock.quantity

        if not ItemService().has_permission(
            role_permissions=role_permission, resource=resource, operation=operation
        ):
            raise ServicePermissionError("Permission denied.")

        try:
            existing_stock.quantity = stock.quantity
            existing_stock.notes = stock.notes
            existing_stock.updated_at = datetime.datetime.now()

            await existing_stock.save()

            item.quantity += existing_stock.quantity

            await item.save()

            return existing_stock
        except Exception as e:
            raise e
