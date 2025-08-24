"""Seed default statuses: busy, inprogress, complete

Revision ID: 9f3a8c2f1b23
Revises: f1a2b3c4d5e6
Create Date: 2025-08-23 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f3a8c2f1b23"
# Merge the two heads (6e59f2b68414 and 7a1c9d0b1add)
down_revision: Union[str, Sequence[str], None] = ("6e59f2b68414", "7a1c9d0b1add")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    meta = sa.MetaData()
    status = sa.Table("status", meta, autoload_with=bind)

    existing = {row[0] for row in bind.execute(sa.select(status.c.description))}
    for desc in ["busy", "inprogress", "complete"]:
        if desc not in existing:
            bind.execute(
                sa.insert(status).values(description=desc, usrid="system", tmstamp=sa.func.now())
            )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("DELETE FROM status WHERE description IN (:a, :b, :c)").bindparams(
            a="busy", b="inprogress", c="complete"
        )
    )
