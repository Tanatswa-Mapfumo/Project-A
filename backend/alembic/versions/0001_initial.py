"""Initial schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-08

The schema is created from the SQLAlchemy metadata of the app models so it can
never drift from the code (see DECISIONS.md).
"""

import app.db.models  # noqa: F401 - register all models
from alembic import op
from app.db.base import Base

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
