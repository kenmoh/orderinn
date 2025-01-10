"""init migration

Revision ID: 3fa6c1cc135d
Revises: 
Create Date: 2025-01-03 13:18:11.699413

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "3fa6c1cc135d"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "order",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("room_number", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("total_amount", sa.Numeric(), nullable=False),
        sa.Column("payment_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "payment_status",
            sa.Enum("PENDING", "SUCCESS", "FAILED", name="paymentstatus"),
            nullable=False,
        ),
        sa.Column(
            "order_status",
            sa.Enum("PENDING", "DELIVERED", "CANCELED", name="orderstatus"),
            nullable=False,
        ),
        sa.Column("items", sa.JSON(), nullable=True),
        sa.Column("remarks", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_id"), "order", ["id"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_order_id"), table_name="order")
    op.drop_table("order")
    # ### end Alembic commands ###
