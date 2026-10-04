"""Create Phase 3/4 backtest schema.

Revision ID: 20260930_0002
Revises: 20260922_0001
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260930_0002"
down_revision: str | None = "20260922_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

timestamps = (
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
)


def upgrade() -> None:
    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("strategy_name", sa.String(64), nullable=False),
        sa.Column("strategy_version", sa.String(32)),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("timeframe", sa.String(8), nullable=False),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_sources.id")),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("candle_count", sa.Integer(), nullable=False),
        sa.Column("initial_capital", sa.Numeric(28, 10), nullable=False),
        sa.Column("final_equity", sa.Numeric(28, 10), nullable=False),
        sa.Column("fee_rate", sa.Numeric(18, 10), nullable=False),
        sa.Column("spread_rate", sa.Numeric(18, 10), nullable=False),
        sa.Column("slippage_rate", sa.Numeric(18, 10), nullable=False),
        sa.Column("latency_bars", sa.Integer(), nullable=False),
        sa.Column("cost_scale", sa.Numeric(8, 4), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("dataset_version", sa.String(128)),
        sa.Column("feature_version", sa.String(64)),
        sa.Column("model_version", sa.String(64)),
        sa.Column("git_commit", sa.String(40)),
        sa.Column("notes", sa.Text()),
        *timestamps,
    )
    op.create_index(
        "ix_backtest_runs_symbol_timeframe_created",
        "backtest_runs",
        ["symbol", "timeframe", "created_at"],
    )
    op.create_index(
        "ix_backtest_runs_strategy_created",
        "backtest_runs",
        ["strategy_name", "created_at"],
    )

    op.create_table(
        "backtest_trades",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("backtest_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("side", sa.String(8), nullable=False),
        sa.Column("entry_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("entry_price", sa.Numeric(28, 10), nullable=False),
        sa.Column("exit_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exit_price", sa.Numeric(28, 10), nullable=False),
        sa.Column("size", sa.Numeric(38, 18), nullable=False),
        sa.Column("stop_price", sa.Numeric(28, 10)),
        sa.Column("target_price", sa.Numeric(28, 10)),
        sa.Column("gross_pnl", sa.Numeric(28, 10), nullable=False),
        sa.Column("fees", sa.Numeric(28, 10), nullable=False),
        sa.Column("net_pnl", sa.Numeric(28, 10), nullable=False),
        sa.Column("r_multiple", sa.Numeric(18, 6)),
        sa.Column("bars_held", sa.Integer(), nullable=False),
        sa.Column("exit_reason", sa.String(32), nullable=False),
        *timestamps,
    )
    op.create_index("ix_backtest_trades_run", "backtest_trades", ["run_id", "id"])


def downgrade() -> None:
    op.drop_index("ix_backtest_trades_run", table_name="backtest_trades")
    op.drop_table("backtest_trades")
    op.drop_index("ix_backtest_runs_strategy_created", table_name="backtest_runs")
    op.drop_index("ix_backtest_runs_symbol_timeframe_created", table_name="backtest_runs")
    op.drop_table("backtest_runs")