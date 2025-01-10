from contextlib import asynccontextmanager
from fastapi import FastAPI

from .database.database import init_db
from .routes.item_routes import item_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server starting...")
    await init_db()
    yield
    print("Print server stopped.")


app = FastAPI(
    lifespan=lifespan,
    title="OrderInn Item API",
    description="OrderInn API",
    version="0.1.0",
    docs_url="/",
)


@app.get("/", tags=["Health"])
def read_root() -> dict:
    return {"Hello": "World"}


app.include_router(item_router)
