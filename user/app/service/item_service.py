from operator import ne
from appwrite.id import ID
from appwrite.exception import AppwriteException
from appwrite.query import Query
from appwrite.role import Role
from appwrite.permission import Permission

from app.schemas.item_schemas import CreateItemSchema
from app.utils import appwrite
from app.schemas.user_schemas import CreateteamSchema


def create_item(item: CreateItemSchema, user_id: str):
    try:
        new_item = appwrite.database.create_document(
            database_id=appwrite.DATABASE_ID,
            collection_id=appwrite.COLLECTION_ID,
            document_id=ID.unique(),
            data={
                "companyId": user_id,
                "name": item.name,
                "description": item.description,
                "sides": item.sides,
                "price": item.price,
                "imageUrl": item.image_url,
                # 'category': item.category,
                "preparationTime": item.preparation_time,
            },
        )
        return new_item
    except AppwriteException as e:
        raise e


def update_item_permission(
    item_id: str, item: CreateItemSchema, user_id: str, team: CreateteamSchema
):
    try:
        new_item = appwrite.database.create_document(
            database_id=appwrite.DATABASE_ID,
            collection_id=appwrite.COLLECTION_ID,
            document_id=ID.unique(),
            data={
                "companyId": user_id,
                "name": item.name,
                "description": item.description,
                "sides": item.sides,
                "price": item.price,
                "imageUrl": item.image_url,
                # 'category': item.category,
                "preparationTime": item.preparation_time,
            },
        )
        return new_item
    except AppwriteException as e:
        raise e


def get_items():
    try:
        items = appwrite.database.list_documents(
            database_id=appwrite.DATABASE_ID, collection_id=appwrite.COLLECTION_ID
        )
        return items
    except AppwriteException as e:
        raise e


def get_company_items(company_id: str):
    try:
        return appwrite.database.list_documents(
            database_id=appwrite.DATABASE_ID,
            collection_id=appwrite.COLLECTION_ID,
            queries=[Query.equal("companyId", company_id)],
        )

    except AppwriteException as e:
        raise e


def get_inventory():
    try:
        return appwrite.database.list_documents(
            database_id=appwrite.DATABASE_ID,
            collection_id="6766ed2f0032abb1aa56",
        )

    except AppwriteException as e:
        raise e


def get_item(item_id: str):
    try:
        return appwrite.database.get_document(
            database_id=appwrite.DATABASE_ID,
            collection_id=appwrite.COLLECTION_ID,
            document_id=item_id,
            # queries=[Query.equal('document_id', item_id)]
        )

    except AppwriteException as e:
        raise e


def create_stock():
    try:
        new_stock = appwrite.database.create_document(
            database_id=appwrite.DATABASE_ID,
            collection_id="6766f693000ec2328ef2",
            document_id=ID.unique(),
            data={
                # 'userId': '6766fd1c002a325eba36',
                "itemId": "6766fd1c002a325eba36",
                "name": "Steak",
                "quantity": 133,
            },
        )
        existing_stock: dict = appwrite.database.get_document(
            database_id=appwrite.DATABASE_ID,
            collection_id="6766ed2f0032abb1aa56",
            document_id=new_stock["itemId"],
        )

        documnets: list = existing_stock.get("stock", [])
        documnets.append(new_stock)

        quantity = sum([item["quantity"] for item in documnets])

        appwrite.database.update_document(
            database_id=appwrite.DATABASE_ID,
            collection_id="6766ed2f0032abb1aa56",
            document_id=new_stock["itemId"],
            data={"stock": documnets, "quantity": quantity},
        )

        return new_stock
    except AppwriteException as e:
        raise e
