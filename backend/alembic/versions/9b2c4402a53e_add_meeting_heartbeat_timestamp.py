"""add meeting heartbeat timestamp

Revision ID: 9b2c4402a53e
Revises: 6e302dbb626f
Create Date: 2026-11-03 18:58:56.957533

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b2c4402a53e'
down_revision: Union[str, Sequence[str], None] = '6e302dbb626f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "meetings",
        sa.Column(
            "last_heartbeat_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    


def downgrade() -> None:
    op.drop_column("meetings", "last_heartbeat_at")