from contextlib import asynccontextmanager
from fastapi import FastAPI

from ..app.routes import auth_router
from ..app.routes import user_routes
from ..app.database.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server starting...")
    await init_db()

    yield
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


app.include_router(auth_router.login_router)
app.include_router(user_routes.user_router)


# @app.post("/init-permissions")
# async def initialize_role_permissions(session: Session = Depends(init_db)):
#     """Initialize all role-based permissions"""
#     try:
#         # Define permissions matrix
#         await init_role_permissions(session=session)
#     except Exception as e:
#         print(e)
