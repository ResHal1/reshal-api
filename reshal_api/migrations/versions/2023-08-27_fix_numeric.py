"""Fix numeric

Revision ID: 97546f26a816
Revises: 4e6465dec8ea
Create Date: 2023-08-27 13:04:39.961470

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "97546f26a816"
down_revision = "4e6465dec8ea"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "reservation",
        "price",
        type_=sa.Numeric(precision=12, scale=2),
        existing_type=sa.Numeric(precision=12, scale=0),
        nullable=False,
    )
    op.alter_column(
        "facility",
        "price",
        type_=sa.Numeric(precision=12, scale=2),
        existing_type=sa.Numeric(precision=12, scale=0),
        nullable=False,
    )
    op.alter_column(
        "payment",
        "price",
        type_=sa.Numeric(precision=12, scale=2),
        existing_type=sa.Numeric(precision=12, scale=0),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "reservation",
        "price",
        type_=sa.Numeric(precision=12, scale=0),
        existing_type=sa.Numeric(precision=12, scale=2),
        nullable=False,
    )
    op.alter_column(
        "facility",
        "price",
        type_=sa.Numeric(precision=12, scale=0),
        existing_type=sa.Numeric(precision=12, scale=2),
        nullable=False,
    )
    op.alter_column(
        "payment",
        "price",
        type_=sa.Numeric(precision=12, scale=0),
        existing_type=sa.Numeric(precision=12, scale=2),
        nullable=False,
    )
