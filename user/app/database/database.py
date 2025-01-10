
import urllib.parse
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, text

from ..models.user_model import Outlet, QRCode, User

from ..config import get_settings


settings = get_settings()
DATABASE_URL = settings.DATABASE_URL
USERNAME = urllib.parse.quote_plus(settings.USERNAME)
PASSWORD = urllib.parse.quote_plus(settings.PASSWORD)


engine = create_async_engine(url=settings.DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def init_user_db():
    client = AsyncIOMotorClient(
        f"mongodb+srv://{USERNAME}:{PASSWORD}@orderinn.p98d4.mongodb.net/")
    await init_beanie(database=client.orderinn, document_models=[User, QRCode, Outlet])


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        stmt = text("SELECT 'Hello';")
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


# async def get_db() -> AsyncGenerator[AsyncSession, None]:
#     """Dependency for getting async database session."""
#     async with SessionLocal() as session:
#         try:
#             yield session
#         except Exception:
#             await session.rollback()
#             raise
#         finally:
#             await session.close()

# async def get_db():
#     async with SessionLocal() as session:
#         yield session
