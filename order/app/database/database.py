from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, text

from ..config import get_settings


settings = get_settings()
DATABASE_URL = settings.DATABASE_URL


engine = create_async_engine(url=settings.DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        stmt = text("SELECT 'Hello from order db';")
        result = await conn.execute(stmt)
        print(f"Database connection test result: {result.all()}")


async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
