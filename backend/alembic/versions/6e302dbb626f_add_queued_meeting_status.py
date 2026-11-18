"""add queued meeting status

Revision ID: 6e302dbb626f
Revises: 9c837039a8e6
Create Date: 2026-11-03 18:06:30.561851

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '6e302dbb626f'
down_revision: Union[str, Sequence[str], None] = '9c837039a8e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None




def upgrade() -> None:
    op.execute(
        "ALTER TYPE meeting_status ADD VALUE IF NOT EXISTS 'QUEUED'"
    )


def downgrade() -> None:
    # PostgreSQL does not support simply dropping an enum value.
    # A safe downgrade requires rebuilding the enum type and
    # ensuring no meetings still use QUEUED.
    raise NotImplementedError(
        "Downgrading the QUEUED meeting status requires "
        "an explicit enum migration."
    )