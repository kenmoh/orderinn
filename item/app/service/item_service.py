import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload

from ..models.models import Item, Inventory, Stock
from ..schema.item_schemas import AddStockSchema, CreateItemSchema, UpdateItemSchema
from ..utils.utils import ServicePermissionError, UserRole, Permission, Resource


class ItemService:
    def check_authorization_for_item(
        self, role: UserRole, permissions: list[Permission], resources: list[Resource]
    ) -> bool:
        """
        Check if user has required role and permission for a resource
        Returns True if authorized, False otherwise
        """
        # return (
        #     role == UserRole.HOTEL_OWNER
        #     and permissions == Permission.CREATE
        #     and resources == Resource.ITEM
        # )

        required_role = 'UserRole.HOTEL_OWNER'
        required_resource = ['Resource.PAYMENT', 'Resource.USER',
                             'Resource.INVENTORY', 'Resource.STOCK', 'Resource.ITEM', 'Resource.ORDER']

        required_permission = [
            'Permission.READ', 'Permission.DELETE', 'Permission.CREATE', 'Permission.UPDATE']

        print(role == required_role)
        print(resources == required_resource)
        print(permissions == required_permission)

        # Check if user has the required role, permission and resource
        return (
            role == required_role and (permissions == required_permission) and (
                resources == required_resource)
        )

    async def get_items(self, company_id: uuid.UUID, db: AsyncSession):
        stmt = select(Item).where(Item.company_id == company_id)
        items = await db.execute(stmt)
        return items.scalars().all()

    async def get_item(self, item_id: int, db: AsyncSession):
        stmt = select(Item).where(Item.id == item_id)
        item = await db.execute(stmt)
        return item.scalar_one_or_none()

    async def create_item_with_inventory(
        self,
        company_id: uuid.UUID,
        role: str,
        resources: str,
        permissions: str,
        item: CreateItemSchema,
        db: AsyncSession,
    ):
        """
        Creates a new item along with its inventory for a given company.

        Args:
            company_id (uuid.UUID): The UUID of the company.
            role (str): The role of the user attempting to create the item.
            resources (str): The resource being accessed.
            permissions (str): The permission level required to create the item.
            item (CreateItemSchema): The schema containing item details.
            db (AsyncSession): The asynchronous database session.

        Returns:
            Item: The newly created item if successful.
            str: "Permission denied!" if the user lacks the necessary permissions.

        Raises:
            HTTPException: If there is an error during item creation.
        """

        if not self.check_authorization_for_item(
            role=role, resources=resources, permissions=permissions
        ):
            raise ServicePermissionError("Permission denied!")

        try:
            async with db.begin():
                new_item = Item(
                    company_id=company_id,
                    name=item.name,
                    category=item.category,
                    description=item.description,
                    price=item.price,
                    # quantity=item.quantity,
                    unit=item.unit,
                    reorder_point=item.reorder_point,
                    image_url=item.image_url,
                )

                db.add(new_item)
                await db.flush()

                item_inventory = Inventory(
                    item_id=new_item.id, quantity=0)

                db.add(item_inventory)
                await db.commit()
                db.refresh(new_item)
                db.refresh(item_inventory)

                return new_item

        except Exception as e:
            raise ValueError(str(e))

    async def update_item(
        self,
        item_id: int,
        company_id: str,
        role: str,
        resource: str,
        permission: str,
        item: UpdateItemSchema,
        db: AsyncSession,
    ):
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
        stmt = select(Item).where(Item.id == item_id)
        result = await db.execute(stmt)
        db_item: Item = result.scalar_one_or_none()

        if not self.check_authorization_for_item(
            role=role, resource=resource, permission=permission
        ):
            raise ServicePermissionError("Permission denied!")

        if db_item.company_id != company_id:
            raise ServicePermissionError("You can only update your item!")

        db_item.category = item.category
        db_item.name = item.name
        db_item.description = item.description
        db_item.price = item.price
        db_item.unit = item.unit
        db_item.reorder_point = item.reorder_point
        db_item.image_url = item.image_url

        await db.commit()
        db.refresh(db_item)

        return db_item

    async def delete_item(
        self,
        item_id: int,
        company_id: str,
        role: str,
        resource: str,
        permission: str,
        db: AsyncSession,
    ):
        stmt = select(Item).where(Item.id == item_id)
        result = await db.execute(stmt)
        db_item: Item = await result.scalar_one_or_none()

        if not self.check_authorization_for_item(
            role=role, resource=resource, permission=permission
        ):
            raise ServicePermissionError("Permission!")

        if db_item.company_id != company_id:
            raise ServicePermissionError("You can only delete your item!")

        if db_item:
            await db.delete(db_item)
            await db.commit()


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

        stmt = (
            select(Inventory)
            .join(Item)
            .where(Item.company_id == company_id)
            .options(selectinload(Inventory.item))
        )
        inventories = await db.execute(stmt)
        company_inventories: Inventory = inventories.unique().scalars().all()

        return [
            {
                # "id": inventory.id,
                "item_id": inventory.item_id,
                "quantity": inventory.quantity,
                "company_id": inventory.item.company_id,
                "name": inventory.item.name,
                "price": inventory.item.price,
                "unit": inventory.item.unit,
                "category": inventory.item.category,
                "updated_at": inventory.updated_at,
            }
            for inventory in company_inventories
        ]

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

        stmt = (
            select(Inventory)
            .join(Item)
            .where(Inventory.id == inventory_id, Item.company_id == company_id)
            .options(selectinload(Inventory.item))
        )

        result = await db.execute(stmt)
        inventory = result.unique().scalar_one_or_none()

        if not inventory:
            return None

        return {
            # "id": inventory.id,
            "item_id": inventory.item_id,
            "quantity": inventory.quantity,
            "company_id": inventory.item.company_id,
            "name": inventory.item.name,
            "price": inventory.item.price,
            "unit": inventory.item.unit,
            "category": inventory.item.category,
            "updated_at": inventory.updated_at,
        }

    def check_authorization_for_stock(
        self, role: str, permission: str, resource: str
    ) -> bool:
        """
        Check if user has required role and permission for a resource
        Returns True if authorized, False otherwise
        """
        return (
            role
            == (
                UserRole.HOTEL_OWNER
                or UserRole.CHEF
                or UserRole.LAUNDRY_ATTENDANT
                or UserRole.MANAGER
                or UserRole.WAITER
            )
            and permission == Permission.CREATE
            and resource == Resource.STOCK
        )

    async def add_new_stock(
        self,
        inventory_id: int,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
        role: str,
        resource: str,
        permission: str,
        stock: AddStockSchema,
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

        if not self.check_authorization_for_stock(
            role=role, resource=resource, permission=permission
        ):
            raise ServicePermissionError('Permission denied!')

        try:
            async with db.begin():
                stmt = (
                    select(Inventory)
                    .join(Item)
                    .where(Inventory.id == inventory_id, Item.company_id == company_id)
                )
                inventory = await db.execute(stmt)
                inventory = await inventory.scalar_one_or_none()

                if not inventory:
                    raise ValueError("Inventory not found")

                # Create new stock
                new_stock = Stock(
                    inventory_id=inventory_id,
                    quantity=stock.quantity,
                    user_id=user_id,
                    notes=stock.notes,
                )

                # Update inventory quantity
                inventory.quantity += stock.quantity

                db.add(new_stock)
                await db.flush()
                await db.refresh(new_stock)

                return {
                    "id": new_stock.id,
                    "quantity": new_stock.quantity,
                    "inventory_id": new_stock.inventory_id,
                    "notes": new_stock.notes,
                    "created_at": new_stock.created_at,
                }

        except Exception as e:
            raise ValueError(str(e))

    async def update_stock(
        self,
        inventory_id: int,
        user_id: int,
        stock_id: int,
        role: str,
        resource: str,
        permission: str,
        stock: AddStockSchema,
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

        if not self.check_authorization_for_stock(
            role=role, resource=resource, permission=permission
        ):
            return "Permission denied!"

        try:
            async with db.begin():
                # Get stock and inventory in a single query
                stmt = (
                    select(Stock)
                    .join(Inventory)
                    .where(
                        Stock.id == stock_id,
                        Stock.user_id == user_id,
                        Stock.inventory_id == inventory_id,
                    )
                )
                result = await db.execute(stmt)
                existing_stock: Stock = await result.scalar_one_or_none()

                if not existing_stock:
                    raise ValueError("Stock not found")

                # Calculate quantity difference
                quantity_diff = stock.quantity - existing_stock.quantity

                # Update stock

                existing_stock.quantity = stock.quantity
                existing_stock.user_id = user_id
                existing_stock.notes = stock.notes
                existing_stock.updated_at = datetime.datetime.now()

                # Update inventory quantity
                existing_stock.inventory.quantity += quantity_diff

                await db.flush()
                await db.refresh(existing_stock)

                return {
                    "id": existing_stock.id,
                    "quantity": existing_stock.quantity,
                    "inventory_id": existing_stock.inventory_id,
                    "updated_at": existing_stock.updated_at,
                }

        except Exception as e:
            raise ValueError(str(e))
