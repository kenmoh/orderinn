# import asyncio
# from sqlmodel import select, delete
# from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# from app.config import get_settings
# from app.models.users import RolePermission, UserRole, Resource, Permission

# settings = get_settings()
# DATABASE_URL = settings.DATABASE_URL

# engine = create_async_engine(url=settings.DATABASE_URL, echo=True)
# SessionLocal = async_sessionmaker(
#     bind=engine, class_=AsyncSession, expire_on_commit=False
# )


# async def init_role_permissions(session: AsyncSession):
#     """
#     Initialize role-based permissions in the database.
#     This function defines what each role can do with each resource.
#     """
#     print("Initializing role permissions...")

#     # Define permissions matrix
#     permissions_matrix = {
#         UserRole.SUPER_ADMIN: {
#             Resource.USER: [
#                 Permission.CREATE,
#                 Permission.READ,
#                 Permission.UPDATE,
#                 Permission.DELETE,
#             ],
#             Resource.ITEM: [Permission.READ],
#             Resource.ORDER: [Permission.READ],
#             Resource.INVENTORY: [Permission.READ],
#             Resource.PAYMENT: [Permission.READ],
#         },
#         UserRole.HOTEL_OWNER: {
#             Resource.USER: [
#                 Permission.CREATE,
#                 Permission.READ,
#                 Permission.UPDATE,
#                 Permission.DELETE,
#             ],
#             Resource.ITEM: [
#                 Permission.CREATE,
#                 Permission.READ,
#                 Permission.UPDATE,
#                 Permission.DELETE,
#             ],
#             Resource.ORDER: [Permission.READ, Permission.UPDATE],
#             Resource.STOCK: [
#                 Permission.READ,
#                 Permission.UPDATE,
#                 Permission.DELETE,
#                 Permission.CREATE,
#             ],
#             Resource.INVENTORY: [
#                 Permission.CREATE,
#                 Permission.READ,
#                 Permission.UPDATE,
#                 Permission.DELETE,
#             ],
#             Resource.PAYMENT: [Permission.READ],
#         },
#         UserRole.MANAGER: {
#             Resource.USER: [Permission.READ],
#             Resource.ITEM: [Permission.CREATE, Permission.READ],
#             Resource.ORDER: [Permission.READ, Permission.UPDATE],
#             Resource.INVENTORY: [Permission.READ],
#             Resource.STOCK: [Permission.READ, Permission.CREATE, Permission.UPDATE],
#             Resource.PAYMENT: [Permission.READ],
#         },
#         UserRole.CHEF: {
#             Resource.ITEM: [Permission.READ, Permission.UPDATE],
#             Resource.ORDER: [Permission.READ, Permission.UPDATE],
#             Resource.STOCK: [Permission.READ, Permission.CREATE, Permission.UPDATE],
#             Resource.INVENTORY: [Permission.READ],
#         },
#         UserRole.WAITER: {
#             Resource.ITEM: [Permission.READ, Permission.UPDATE],
#             Resource.ORDER: [Permission.READ, Permission.UPDATE],
#             Resource.STOCK: [Permission.READ, Permission.CREATE, Permission.UPDATE],
#             Resource.INVENTORY: [Permission.READ],
#         },
#         UserRole.LAUNDRY_ATTENDANT: {
#             Resource.ITEM: [Permission.READ],
#             Resource.STOCK: [Permission.READ, Permission.CREATE, Permission.UPDATE],
#             Resource.ORDER: [Permission.READ, Permission.UPDATE],
#             Resource.INVENTORY: [Permission.READ],
#         },
#         UserRole.GUEST: {
#             Resource.ITEM: [Permission.READ],
#             Resource.ORDER: [Permission.READ, Permission.CREATE],
#         },
#     }
#     # Clear existing permissions
#     await session.execute(delete(RolePermission))
#     await session.commit()  # Ensure the deletion is committed
#     print("Cleared existing permissions.")

#     # Fetch all existing permissions to avoid duplicates
#     result = await session.execute(select(RolePermission))
#     existing_permissions = result.scalars().all()
#     existing_permissions_set = {
#         (perm.role, perm.resource, perm.permission) for perm in existing_permissions
#     }

#     # Add missing permissions
#     for role, resources in permissions_matrix.items():
#         for resource, permissions in resources.items():
#             for permission in permissions:
#                 if (role, resource, permission) not in existing_permissions_set:
#                     role_permission = RolePermission(
#                         role=role, resource=resource, permission=permission
#                     )
#                     session.add(role_permission)
#                     print(
#                         f"Added permission: {role} - {resource} - {permission}"
#                     )
#     await session.commit()
#     print("Role permissions initialized.")


# async def main():
#     async with SessionLocal() as session:
#         await init_role_permissions(session)


# if __name__ == "__main__":
#     asyncio.run(main())


{
    "id": "user_uuid",
    "role": "HOTEL_OWNER",
    "company_id": "company_uuid",
    "resource": ["USER"],
    "permissions": ["CREATE", "READ", "UPDATE", "DELETE"],
}


names = "Ken, Moh, Ken"

names_list = [name.strip() for name in names.split(",")]

new_names = ", ".join(names_list)

print(new_names)
# print(names.split(',').join(','))
