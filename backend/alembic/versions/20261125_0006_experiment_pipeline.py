"""Create the Stage 3E experiment and evaluation report tables.

Revision ID: 20261125_0006
Revises: 20261003_0005
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261125_0006"
down_revision: str | None = "20261003_0005"
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
    # Created first: experiments.evaluation_report_id references this table.
    op.create_table(
        "evaluation_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("experiment_id", sa.String(36)),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("backtest_runs.id"),
            nullable=False,
        ),
        sa.Column("report", sa.JSON(), nullable=False),
        sa.Column("report_digest", sa.String(64), nullable=False),
        sa.Column("config_fingerprint", sa.String(64), nullable=False),
        sa.Column("input_fingerprint", sa.String(64), nullable=False),
        sa.Column("method_version", sa.String(32), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True)),
        *timestamps,
    )
    op.create_index("ix_evaluation_reports_run", "evaluation_reports", ["run_id"])
    op.create_index(
        "ix_evaluation_reports_experiment", "evaluation_reports", ["experiment_id"]
    )

    op.create_table(
        "experiments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("strategy_name", sa.String(64), nullable=False),
        sa.Column("strategy_version", sa.String(32)),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("timeframe", sa.String(8), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("initial_capital", sa.Numeric(28, 10), nullable=False),
        sa.Column(
            "accounting_currency", sa.String(8), server_default="USDT", nullable=False
        ),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("configuration_fingerprint", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.Column(
            "parent_experiment_id", sa.String(36), sa.ForeignKey("experiments.id")
        ),
        sa.Column("status", sa.String(24), server_default="DRAFT", nullable=False),
        sa.Column("failure_stage", sa.String(32)),
        sa.Column("failure_reason", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("dataset_version", sa.String(128)),
        sa.Column("engine_version", sa.String(40)),
        sa.Column("random_seed", sa.Integer()),
        sa.Column("backtest_run_id", sa.String(36), sa.ForeignKey("backtest_runs.id")),
        sa.Column(
            "evaluation_report_id",
            sa.String(36),
            sa.ForeignKey("evaluation_reports.id"),
        ),
        *timestamps,
    )
    op.create_index(
        "ix_experiments_strategy_created", "experiments", ["strategy_name", "created_at"]
    )
    op.create_index(
        "ix_experiments_symbol_timeframe_created",
        "experiments",
        ["symbol", "timeframe", "created_at"],
    )
    op.create_index("ix_experiments_status_created", "experiments", ["status", "created_at"])
    op.create_unique_constraint(
        "uq_experiments_idempotency_key", "experiments", ["idempotency_key"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_experiments_idempotency_key", "experiments", type_="unique")
    op.drop_index("ix_experiments_status_created", table_name="experiments")
    op.drop_index("ix_experiments_symbol_timeframe_created", table_name="experiments")
    op.drop_index("ix_experiments_strategy_created", table_name="experiments")
    op.drop_table("experiments")
    op.drop_index("ix_evaluation_reports_experiment", table_name="evaluation_reports")
    op.drop_index("ix_evaluation_reports_run", table_name="evaluation_reports")
    op.drop_table("evaluation_reports")
