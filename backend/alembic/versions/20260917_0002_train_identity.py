"""Add train number and date uniqueness.

Revision ID: 20260917_0002
Revises: 20260917_0001
"""

from alembic import op

revision = "20260917_0002"
down_revision = "20260917_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_trains_number_date", "trains", ["train_number", "travel_date"])


def downgrade() -> None:
    op.drop_constraint("uq_trains_number_date", "trains", type_="unique")