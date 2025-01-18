import uuid
from beanie import PydanticObjectId
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from beanie.odm.operators.find.logical import Or, And

from ..models.user_model import User

from ..models.item_model import ItemStock, Item
from ..schemas.item_schema import CreateItemReturnSchema, CreateItemSchema
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

    def check_authorization_for_item(
        self, role: UserRole, permissions: list[Permission], resources: list[Resource]
    ) -> bool:
        """
        Check if user has required role and permission for a resource
        Returns True if authorized, False otherwise
        """

        required_resource = [
            "Resource.PAYMENT",
            "Resource.USER",
            "Resource.STOCK",
            "Resource.ITEM",
            "Resource.ORDER",
        ]

        required_permission = [
            "Permission.READ",
            "Permission.DELETE",
            "Permission.CREATE",
            "Permission.UPDATE",
        ]

        # Check if user has the required role, permission and resource
        return (
            role
            and (permissions == required_permission)
            and (resources == required_resource)
        )

    async def get_company_items(self, company_id: PydanticObjectId):
        return await Item.find(Item.company_id == company_id).to_list()

    async def get_item(self, item_id: int, db: AsyncSession):
        stmt = select(Item).where(Item.id == item_id)
        item = await db.execute(stmt)
        return item.scalar_one_or_none()

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
            company_id = current_user.company_id if current_user.company_id else current_user.id

            db_item: Item = await Item.find(
                Item.id == item_id,
                Item.company_id == company_id,
                Item.user_id == current_user.id,
            ).first_or_none()

            if not db_item:
                raise ServicePermissionError(
                    "You can only delete item you created.")

            if not self.has_permission(
                role_permissions=role_permission, resource=resource, operation=operation
            ):
                raise ServicePermissionError("Permission deinied!")

            await db_item.delete()

        except Exception as e:
            raise ValueError('Failed to delete', str(e))from e


class StockAndInventoryService:
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
        self, inventory_id: str, company_id: str, db: AsyncSession
    ) -> dict | None:
        """
        Retrieve a single inventory with associated item details.

        Args:
            inventory_id (str): The unique identifier of the inventory
            db (AsyncSession): The database session for executing queries

        Returns:
            dict | None: Dictionary containing inventory details or None if not found:
                - item_id (int): The unique identifier of the item
                - quantity (int): Current stock quantity
                - company_id (str): The company identifier
                - name (str): Item name
                - price (float): Item price
                - unit (str): Unit of measurement
                - category (str): Item category
                - updated_at (datetime): Last update timestamp

        """

    def check_authorization_for_stock(
        self, role: str, permission: str, resource: str
    ) -> bool:
        """
        Check if user has required role and permission for a resource
        Returns True if authorized, False otherwise
        """

    async def add_new_stock(
        self,
        inventory_id: int,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
        role: str,
        resource: str,
        permission: str,
        # stock: AddStockSchema,
        db: AsyncSession,
    ):
        """
        Add new stock to inventory
        Args:
            inventory_id (int): The ID of the inventory to which the stock will be added.
            user_id (uuid.UUID): The ID of the user adding the stock.
            company_id (uuid.UUID): The ID of the company to which the inventory belongs.
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

    async def update_stock(
        self,
        inventory_id: int,
        user_id: int,
        stock_id: int,
        role: str,
        resource: str,
        permission: str,
        # stock: AddStockSchema,
        db: AsyncSession,
    ):
        """
        Updates the stock information for a given inventory and stock ID.

        Args:
            inventory_id (int): The ID of the inventory to update.
            user_id (str): The UUID of the user performing the update.
            stodk_id (int): The ID of the stock to update.
            role (str): The role of the user.
            resource (str): The resource being accessed.
            permission (str): The permission level of the user.
            stock (AddStockSchema): The new stock data to update.
            db (AsyncSession): The database session.

        Returns:
            Stock: The updated stock object if successful.
            str: 'Permission denied!' if the user does not have the required permissions.
        """
