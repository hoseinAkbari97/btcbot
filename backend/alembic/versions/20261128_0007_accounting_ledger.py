"""Persist engine equity points and per-leg accounting audit fields.

Revision ID: 20261128_0007
Revises: 20261125_0006
Create Date: 2026-11-28

Historical rows are never backfilled: the new columns stay null and the new
child table stays empty for runs written by earlier revisions.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261128_0007"
down_revision: str | None = "20261125_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

timestamps = (
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.Column(
        "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
)


def upgrade() -> None:
    op.add_column("backtest_runs", sa.Column("accounting_model_version", sa.String(16)))
    # Explicit calls rather than a loop: the repository's AST parity test needs
    # to see each literal column name in the migration source.
    op.add_column("backtest_trades", sa.Column("entry_fee", sa.Numeric(28, 10)))
    op.add_column("backtest_trades", sa.Column("exit_fee", sa.Numeric(28, 10)))
    op.add_column("backtest_trades", sa.Column("raw_exit_price", sa.Numeric(28, 10)))
    op.add_column("backtest_trades", sa.Column("entry_concession", sa.Numeric(28, 10)))
    op.add_column("backtest_trades", sa.Column("exit_concession", sa.Numeric(28, 10)))

    # Constraints are inline: SQLite cannot add UNIQUE or a new FK after create.
    op.create_table(
        "backtest_equity_points",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("backtest_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("bar_index", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("equity", sa.Numeric(28, 10), nullable=False),
        sa.Column("cash", sa.Numeric(28, 10), nullable=False),
        sa.Column("unrealized", sa.Numeric(28, 10), nullable=False),
        sa.Column("position_side", sa.String(8)),
        sa.Column("drawdown", sa.Numeric(28, 10), nullable=False),
        sa.UniqueConstraint(
            "run_id", "bar_index", name="uq_backtest_equity_points_run_bar"
        ),
        *timestamps,
    )
    op.create_index(
        "ix_backtest_equity_points_run_timestamp",
        "backtest_equity_points",
        ["run_id", "timestamp"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_backtest_equity_points_run_timestamp", table_name="backtest_equity_points"
    )
    op.drop_table("backtest_equity_points")
    op.drop_column("backtest_trades", "exit_concession")
    op.drop_column("backtest_trades", "entry_concession")
    op.drop_column("backtest_trades", "raw_exit_price")
    op.drop_column("backtest_trades", "exit_fee")
    op.drop_column("backtest_trades", "entry_fee")
    op.drop_column("backtest_runs", "accounting_model_version")
