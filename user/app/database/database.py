from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine, text

from user.app.config import get_settings


settings = get_settings()
DATABASE_URL = settings.DATABASE_URL

engine = AsyncEngine(
    create_engine(url=settings.DATABASE_URL, echo=True)
)


async def init_db():
    async with engine.begin() as conn:
        stmt = text("SELECT 'Hello';")
        result = await conn.execute(stmt)
        print(result.all())


async def get_session():
    SessionLocal = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        yield session
