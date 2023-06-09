"""Add facility type

Revision ID: f25a8a9225d2
Revises: 1bca19294bf2
Create Date: 2023-06-17 13:27:10.937280

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f25a8a9225d2"
down_revision = "1bca19294bf2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "facility_type",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("facility_type_pkey")),
    )
    op.add_column("facility", sa.Column("type_id", sa.Uuid(), nullable=False))
    op.create_foreign_key(
        op.f("facility_type_id_fkey"),
        "facility",
        "facility_type",
        ["type_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_column("facility", "public")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "facility",
        sa.Column("public", sa.BOOLEAN(), autoincrement=False, nullable=False),
    )
    op.drop_constraint(
        op.f("facility_type_id_fkey"), "facility", type_="foreignkey"
    )
    op.drop_column("facility", "type_id")
    op.drop_table("facility_type")
    # ### end Alembic commands ###
