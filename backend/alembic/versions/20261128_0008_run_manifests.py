"""Add immutable per-run provenance manifests.

Revision ID: 20261128_0008
Revises: 20261128_0007
Create Date: 2026-11-28

Runs written before this revision get no manifest. Verifiers must report that
state as unavailable; no manifest is synthesized from today's code or data.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261128_0008"
down_revision: str | None = "20261128_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The uniqueness constraint is inline because SQLite cannot add UNIQUE after
    # the table exists. It is what enforces one immutable manifest per run.
    op.create_table(
        "run_manifests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("backtest_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "experiment_id",
            sa.String(36),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("schema_version", sa.String(16), nullable=False),
        sa.Column("manifest_fingerprint", sa.String(64), nullable=False),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("run_id", name="uq_run_manifests_run_id"),
    )
    op.create_index(
        "ix_run_manifests_experiment_id", "run_manifests", ["experiment_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_run_manifests_experiment_id", table_name="run_manifests")
    op.drop_table("run_manifests")
