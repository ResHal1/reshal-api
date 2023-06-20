"""Add price

Revision ID: c379c95dbda1
Revises: 721589165bbd
Create Date: 2023-06-20 22:29:01.896020

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c379c95dbda1"
down_revision = "721589165bbd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "facility",
        sa.Column("price", sa.Numeric(precision=12, scale=0), nullable=False),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("facility", "price")
    # ### end Alembic commands ###