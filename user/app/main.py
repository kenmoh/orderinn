from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, BackgroundTasks, Response
from sqlmodel import Session

from user.app.database.database import SessionLocal, init_db
# from user.app.utils.utils import check_subscriptions
from user.app.models.users import deactivate_expired_subscriptions, init_role_permissions


@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Server starting...')
    await init_db()
    yield
    print('Print server stopped.')

app = FastAPI(lifespan=lifespan,
              title="OrderInn", description="OrderInn API", version="0.1.0", docs_url="/"
              )


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/init-permissions")
async def initialize_role_permissions(session: Session = Depends(init_db)):
    """Initialize all role-based permissions"""
    try:
        # Define permissions matrix
        await init_role_permissions(session=session)
    except Exception as e:
        print(e)
