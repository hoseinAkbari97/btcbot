"""Expand the trade ledger into the authoritative research record.

Revision ID: 20260930_0003
Revises: 20260930_0002
Create Date: 2026-09-30

Every column added here is nullable or defaulted, so runs stored before this
revision still load. Backfilling the one column that can be recovered without
the data (``sizing_model``) would be a guess: a legacy trade has no recorded
brackets, so whether it was sized by stop or by allocation is genuinely
unknown, and the honest default is to say so rather than to assert ``stop_risk``.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260930_0003"
down_revision: str | None = "20260930_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # -- timing provenance ---------------------------------------------------
    # The three moments that differ: when the signal was produced, when the
    # order was placed, when it filled. The gap between them is latency, and it
    # is the difference between a backtest that is honest and one that is not.
    op.add_column("backtest_trades", sa.Column("signal_time", sa.DateTime(timezone=True)))
    op.add_column("backtest_trades", sa.Column("order_time", sa.DateTime(timezone=True)))
    op.add_column("backtest_trades", sa.Column("fill_time", sa.DateTime(timezone=True)))

    # -- risk semantics ------------------------------------------------------
    # Distinguishing "1% of capital committed" from "1% of the account at risk"
    # is the entire point of `sizing_model`, so a row written before this
    # revision is marked `unknown` rather than assumed to be risk-sized: its
    # brackets were never recorded, and asserting a guess would be worse than
    # admitting the gap.
    op.add_column(
        "backtest_trades",
        sa.Column("notional_value", sa.Numeric(28, 10), server_default="0", nullable=False),
    )
    op.add_column("backtest_trades", sa.Column("risk_fraction", sa.Numeric(18, 8)))
    op.add_column("backtest_trades", sa.Column("risk_amount", sa.Numeric(28, 10)))
    op.add_column(
        "backtest_trades",
        sa.Column("sizing_model", sa.String(24), server_default="unknown", nullable=False),
    )

    # -- costs, itemised rather than summed ---------------------------------
    # Server defaults populate existing rows with 0, which keeps the
    # reconciliation identity `fees + spread + slippage == gross - net` true for
    # them instead of leaving them unbookable.
    op.add_column(
        "backtest_trades",
        sa.Column("spread_cost", sa.Numeric(28, 10), server_default="0", nullable=False),
    )
    op.add_column(
        "backtest_trades",
        sa.Column("slippage_cost", sa.Numeric(28, 10), server_default="0", nullable=False),
    )
    op.add_column(
        "backtest_trades",
        sa.Column("latency_cost", sa.Numeric(28, 10), server_default="0", nullable=False),
    )
    op.add_column(
        "backtest_trades",
        sa.Column("other_costs", sa.Numeric(28, 10), server_default="0", nullable=False),
    )

    # -- both R multiples and both excursions -------------------------------
    # Gross R overstates the edge; net R is what the Monte Carlo project should
    # consume. Both are stored so a reader can see the size of the gap.
    op.add_column("backtest_trades", sa.Column("gross_r", sa.Numeric(18, 6)))
    op.add_column("backtest_trades", sa.Column("net_r", sa.Numeric(18, 6)))
    op.add_column("backtest_trades", sa.Column("mae", sa.Numeric(18, 6)))
    op.add_column("backtest_trades", sa.Column("mae_price", sa.Numeric(28, 10)))
    op.add_column("backtest_trades", sa.Column("mfe", sa.Numeric(18, 6)))
    op.add_column("backtest_trades", sa.Column("mfe_price", sa.Numeric(28, 10)))

    # -- provenance ----------------------------------------------------------
    op.add_column(
        "backtest_trades",
        sa.Column("strategy_name", sa.String(64), server_default="", nullable=False),
    )
    op.add_column(
        "backtest_trades",
        sa.Column("strategy_version", sa.String(32), server_default="1", nullable=False),
    )
    op.add_column(
        "backtest_trades",
        sa.Column("market_regime", sa.String(24), server_default="", nullable=False),
    )
    op.add_column(
        "backtest_trades",
        sa.Column("strategy_context", sa.JSON(), server_default="{}", nullable=False),
    )

    # -- reproducibility -----------------------------------------------------
    # ``random_seed`` is new here. ``dataset_version`` is *not*: 0002 already
    # created it on ``backtest_runs``, and adding it again aborts the upgrade
    # with "duplicate column name" on every database. It is deliberately left
    # alone — re-creating a provenance column that the ledger needs would be
    # the wrong way to silence the error.
    op.add_column("backtest_runs", sa.Column("random_seed", sa.Integer()))


def downgrade() -> None:
    op.drop_column("backtest_runs", "random_seed")
    for column in (
        "strategy_context",
        "market_regime",
        "strategy_version",
        "strategy_name",
        "mfe_price",
        "mfe",
        "mae_price",
        "mae",
        "net_r",
        "gross_r",
        "other_costs",
        "latency_cost",
        "slippage_cost",
        "spread_cost",
        "sizing_model",
        "risk_amount",
        "risk_fraction",
        "notional_value",
        "fill_time",
        "order_time",
        "signal_time",
    ):
        op.drop_column("backtest_trades", column)
