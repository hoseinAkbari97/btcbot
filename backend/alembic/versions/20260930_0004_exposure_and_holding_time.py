"""Separate capital exposure from account risk, and persist holding time.

Revision ID: 20260930_0004
Revises: 20260930_0003
Create Date: 2026-09-30

Two corrections to the ledger, both about the same failure: a reader
reconstructing a quantity that was never recorded.

``capital_fraction`` was previously lost. A stop-defined trade recorded the
fraction of the account *at risk*, and an allocation-sized trade recorded only
a label saying "allocation" — so the exposure each trade actually committed was
unrecoverable. Downstream, money management needs precisely that number, and
"1% of capital" must never be re-read as "1% of the account at risk".

``holding_seconds`` likewise: bars held is timeframe-dependent, so a
holding-time distribution built from one timeframe cannot be compared against
another without being converted to wall-clock first.

Both are additive and nullable, so rows written before this revision still
load. They are deliberately not backfilled — the missing values are gone, and
deriving an exposure for a historical trade from its price and size would be an
inference presented as a record.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260930_0004"
down_revision: str | None = "20260930_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "backtest_trades",
        sa.Column("capital_fraction", sa.Numeric(18, 8), nullable=True),
    )
    op.add_column(
        "backtest_trades",
        sa.Column("holding_seconds", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("backtest_trades", "holding_seconds")
    op.drop_column("backtest_trades", "capital_fraction")