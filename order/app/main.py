from contextlib import asynccontextmanager
from fastapi import FastAPI

from ..app.database.database import init_db
from ..app.routes import order_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server starting...")
    await init_db()
    yield
    print("Print server stopped.")


app = FastAPI(
    lifespan=lifespan,
    title="OrderInn Order API",
    description="OrderInn API",
    version="0.1.0",
    docs_url="/",
)


@app.get("/", tags=["Health"])
def read_root():
    return {"Hello": "World"}


app.include_router(order_routes.order_router)
