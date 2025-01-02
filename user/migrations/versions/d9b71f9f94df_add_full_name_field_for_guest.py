"""add full_name field for guest

Revision ID: d9b71f9f94df
Revises: f181d3139464
Create Date: 2025-01-01 14:30:57.895801

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "d9b71f9f94df"
down_revision: Union[str, None] = "f181d3139464"
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
    op.create_index(op.f("ix_user_full_name"), "user", ["full_name"], unique=False)
    op.create_unique_constraint(None, "user", ["email"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "user", type_="unique")
    op.drop_index(op.f("ix_user_full_name"), table_name="user")
    op.drop_index(op.f("ix_user_company_name"), table_name="user")
    op.create_index("ix_user_company_name", "user", ["company_name"], unique=False)
    op.drop_column("user", "full_name")
    # ### end Alembic commands ###