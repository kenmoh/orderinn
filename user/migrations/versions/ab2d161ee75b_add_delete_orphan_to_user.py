"""add delete orphan to user

Revision ID: ab2d161ee75b
Revises: d9b71f9f94df
Create Date: 2025-01-01 18:02:17.509809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "ab2d161ee75b"
down_revision: Union[str, None] = "d9b71f9f94df"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user",
        sa.Column("full_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.drop_index("ix_user_company_name", table_name="user")
    op.create_index(op.f("ix_user_company_name"), "user", ["company_name"], unique=True)
    op.create_unique_constraint(None, "user", ["email"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "user", type_="unique")
    op.drop_index(op.f("ix_user_company_name"), table_name="user")
    op.create_index("ix_user_company_name", "user", ["company_name"], unique=False)
    op.drop_column("user", "full_name")
    # ### end Alembic commands ###
