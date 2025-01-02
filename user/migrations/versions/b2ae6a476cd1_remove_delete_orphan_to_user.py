"""remove delete orphan to user

Revision ID: b2ae6a476cd1
Revises: ab2d161ee75b
Create Date: 2025-01-01 18:08:03.952439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "b2ae6a476cd1"
down_revision: Union[str, None] = "ab2d161ee75b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "userrolepermission_user_id_fkey", "userrolepermission", type_="foreignkey"
    )
    op.create_foreign_key(
        None, "userrolepermission", "user", ["user_id"], ["id"], ondelete="CASCADE"
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "userrolepermission", type_="foreignkey")
    op.create_foreign_key(
        "userrolepermission_user_id_fkey",
        "userrolepermission",
        "user",
        ["user_id"],
        ["id"],
    )
    # ### end Alembic commands ###
