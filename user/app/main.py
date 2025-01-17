from contextlib import asynccontextmanager
from fastapi import FastAPI

from ..app.routes.auth_router import login_router
from ..app.routes import user_routes
from ..app.database.database import init_user_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server starting...")
    await init_user_db()

    yield
    init_user_db().close()
    print("Print server stopped.")


app = FastAPI(
    lifespan=lifespan,
    title="OrderInn User API",
    description="OrderInn API",
    version="0.1.0",
    docs_url="/",
)


@app.get("/", tags=["Health"])
def read_root():
    return {"Hello": "World"}


app.include_router(login_router)
app.include_router(user_routes.user_router)
