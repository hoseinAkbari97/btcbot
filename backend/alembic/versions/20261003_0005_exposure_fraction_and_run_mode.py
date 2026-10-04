"""Record exposure sizing and the run mode that governed a backtest.

Revision ID: 20261003_0005
Revises: 20260930_0004
Create Date: 2026-10-03

Two gaps in provenance for existing rows.

``exposure_fraction`` completes the separation of sizing vocabulary that
migration 0004 began with ``capital_fraction``. A position may be sized from a
stop distance, from a share of capital, or from a notional exposure budget;
only the third has an exposure fraction distinct from the capital fraction, and
without its own column the distinction has to be re-inferred from
``sizing_model`` at every read. Nullable, and deliberately left empty for rows
sized any other way rather than backfilled — a value copied from
``capital_fraction`` would be an inference wearing a record's clothes.

``run_mode`` records whether the run actually went through the risk engine.
The engine already refuses to construct in simulation, paper or live mode
without one, so this column does not protect against a live risk bypass. It
answers a narrower question a reader of the ledger will ask regardless: was this
backtest run under research controls, with risk deliberately disabled so that a
control experiment could measure the unfiltered signal? That distinction has to
be recoverable, and a run with no mode recorded cannot be assumed either way.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261003_0005"
down_revision: str | None = "20260930_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "backtest_trades",
        sa.Column("exposure_fraction", sa.Numeric(18, 8), nullable=True),
    )
    op.add_column(
        "backtest_runs",
        sa.Column("mode", sa.String(16), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("backtest_runs", "mode")
    op.drop_column("backtest_trades", "exposure_fraction")