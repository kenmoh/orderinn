"""first migration

Revision ID: f181d3139464
Revises: 
Create Date: 2024-12-31 20:12:58.363098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "f181d3139464"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "rolepermission",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "SUPER_ADMIN",
                "HOTEL_OWNER",
                "MANAGER",
                "CHEF",
                "WAITER",
                "GUEST",
                "LAUNDRY_ATTENDANT",
                name="userrole",
            ),
            nullable=False,
        ),
        sa.Column(
            "resource",
            sa.Enum(
                "USER",
                "ITEM",
                "ORDER",
                "INVENTORY",
                "PAYMENT",
                "STOCK",
                name="resource",
            ),
            nullable=False,
        ),
        sa.Column(
            "permission",
            sa.Enum("CREATE", "READ", "UPDATE", "DELETE", name="permission"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "role", "resource", "permission", name="unique_role_resource_permission"
        ),
    )
    op.create_table(
        "user",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("password", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("company_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "SUPER_ADMIN",
                "HOTEL_OWNER",
                "MANAGER",
                "CHEF",
                "WAITER",
                "GUEST",
                "LAUNDRY_ATTENDANT",
                name="userrole",
            ),
            nullable=False,
        ),
        sa.Column("company_id", sa.Uuid(), nullable=True),
        sa.Column("is_subscribed", sa.Boolean(), nullable=True),
        sa.Column("subscription_start_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_company_id"), "user", ["company_id"], unique=False)
    op.create_index(
        op.f("ix_user_company_name"), "user", ["company_name"], unique=False
    )
    op.create_index(op.f("ix_user_id"), "user", ["id"], unique=False)
    op.create_table(
        "profile",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("address", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("cac_reg_number", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "payment_gateway_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column(
            "payment_gateway_secret", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column(
            "payment_gateway",
            sa.Enum("FLUTTERWAVE", "PAYSTACK", name="paymentgateway"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "userrolepermission",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_permission_id"],
            ["rolepermission.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "role_permission_id", name="unique_user_role_permission"
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("userrolepermission")
    op.drop_table("profile")
    op.drop_index(op.f("ix_user_id"), table_name="user")
    op.drop_index(op.f("ix_user_company_name"), table_name="user")
    op.drop_index(op.f("ix_user_company_id"), table_name="user")
    op.drop_table("user")
    op.drop_table("rolepermission")
    # ### end Alembic commands ###
