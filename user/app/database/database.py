from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlmodel import create_engine, text

from user.app.config import get_settings


settings = get_settings()
DATABASE_URL = settings.DATABASE_URL

engine = AsyncEngine(
    create_engine(url=settings.DATABASE_URL, echo=True)
)

SessionLocal = sessionmaker(engine)


async def init_db():
    async with engine.begin() as conn:
        stmt = text("SELECT 'Hello';")
        result = await conn.execute(stmt)
        print(result.all())


class Base(DeclarativeBase):
    pass
