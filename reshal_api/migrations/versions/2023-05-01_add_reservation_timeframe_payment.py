"""Add reservation,timeframe,payment

Revision ID: affbfd1377cb
Revises: 2e5d61721feb
Create Date: 2023-05-01 11:23:37.474858

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "affbfd1377cb"
down_revision = "2e5d61721feb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    payment_status = postgresql.ENUM(
        "paid", "pending", "cancelled", "failed", name="paymentstatus"
    )
    payment_status.create(op.get_bind())
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "payment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("payment_pkey")),
    )
    op.create_table(
        "reservation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("facility_id", sa.Uuid(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("payment_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["facility_id"],
            ["facility.id"],
            name=op.f("reservation_facility_id_fkey"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"],
            ["payment.id"],
            name=op.f("reservation_payment_id_fkey"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("reservation_user_id_fkey"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            "user_id",
            "payment_id",
            name=op.f("reservation_pkey"),
        ),
    )
    op.create_table(
        "timeframe",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("facility_id", sa.Uuid(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["facility_id"],
            ["facility.id"],
            name=op.f("timeframe_facility_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", "facility_id", name=op.f("timeframe_pkey")),
    )
    # ### end Alembic commands ###
    op.create_unique_constraint("reservation_id_uq", "reservation", ["id"])
    op.create_unique_constraint("uq_timeframe_id", "timeframe", ["id"])
    op.add_column(
        "payment",
        sa.Column(
            "reservation_id",
            sa.Uuid(),
            sa.ForeignKey("reservation.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "payment",
        sa.Column("status", sa.Enum(name="paymentstatus"), nullable=False),
    )
    op.add_column(
        "reservation",
        sa.Column(
            "timeframe_id",
            sa.Uuid(),
            sa.ForeignKey("timeframe.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_constraint(
        "reservation_payment_id_fkey",
        "reservation",
        type_="foreignkey",
    )
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("payment")
    op.drop_table("reservation")
    op.drop_table("timeframe")
    # ### end Alembic commands ###
    sa.Enum(name="paymentstatus").drop(op.get_bind(), checkfirst=False)
