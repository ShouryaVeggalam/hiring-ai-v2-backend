"""Initial schema — all Celestra Hiring AI tables.

Revision ID: 001
Revises:
Create Date: 2026-06-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tables are created via Base.metadata.create_all in dev.
    # Run `alembic revision --autogenerate -m "initial"` against a live DB
    # to regenerate this migration from the ORM models.
    pass


def downgrade() -> None:
    pass
