from sqlmodel import Session, create_engine
from app.models.users import init_role_permissions
from app.config import get_settings

settings = get_settings()
DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL)


def populate_data():
    with Session(engine) as session:
        init_role_permissions(session)


if __name__ == "__main__":
    populate_data()
