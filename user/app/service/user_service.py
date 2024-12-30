from sqlmodel import select, desc
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.users import User
from app.schemas.user_schema import CreateUserSchema


class UserService:
    async def get_users(self, session: AsyncSession):
        stmt = select(User).order_by(desc(User.created_at))
        return await session.exec(stmt).all()

    async def get_user(self, user_id: int, session: AsyncSession):
        stmt = select(User).where(User.id == user_id)
        return await session.exec(stmt).first()

    async def create_user(self, user_data: CreateUserSchema, session: AsyncSession):

        new_user = User(**user_data.model_dump())
        session.add(new_user)
        await session.commit()
        return new_user

    async def delete_user(self, user_id: int, session: AsyncSession):
        user = self.get_user(user_id, session)
        if user is not None:
            await session.delete(user)
            await session.commit()
