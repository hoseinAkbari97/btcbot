"""The migrations and the ORM models must not drift apart.

A column that only one of the two knows about is a column that will fail at
runtime, in production, on the path nobody tested. This reads every migration
file, collects the columns it creates or adds, and diffs them against what the
models declare.

The migrations are read with :mod:`ast` rather than executed. Executing them
would need a live PostgreSQL server and the Alembic package, neither of which
belongs in a unit test; and the question being asked — *do the two lists of
column names agree* — is a question about the source text, not about a
resulting database. What the test cannot check is the correctness of a column's
*type*, which still needs a real ``alembic upgrade`` against a real database.
"""

from __future__ import annotations

import ast
import sqlite3
from pathlib import Path
from typing import Any

# Importing the package registers every table on ``Base.metadata``.
import app.models  # noqa: F401
from alembic import command
from alembic.config import Config
from app.core.config import get_settings
from app.models.base import Base

VERSIONS_DIR = Path(__file__).resolve().parents[1] / "alembic" / "versions"


def _string_arg(call: ast.Call, position: int) -> str | None:
    if len(call.args) <= position:
        return None
    node = call.args[position]
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _resolve(node: ast.AST, assignments: dict[str, ast.AST]) -> list[ast.AST]:
    """Expand a call's arguments, inlining any module-level tuples it splices.

    Migrations declare reusable column groups (``*timestamps``, ``*COSTS``) as
    module constants and splice them into the call. Walking the raw call would
    miss every one of them, so each starred name is resolved back to its
    assignment and walked too.
    """
    if isinstance(node, ast.Call):
        expanded: list[ast.AST] = []
        for arg in node.args:
            if isinstance(arg, ast.Starred):
                expanded.extend(_resolve(assignments.get(arg.value.id, arg), assignments))
            else:
                expanded.extend(_resolve(arg, assignments))
        return [node, *expanded]
    if isinstance(node, ast.Tuple | ast.List | ast.Set):
        expanded = []
        for element in node.elts:
            expanded.extend(_resolve(element, assignments))
        return expanded
    return [node]


def _migrated_columns() -> dict[str, set[str]]:
    """Map every table name to the columns the migration chain declares for it.

    Walks the files in revision order so that a later ``add_column`` accumulates
    onto a table an earlier ``create_table`` opened, which is how the real
    chain behaves.
    """
    tables: dict[str, set[str]] = {}
    for path in sorted(VERSIONS_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        # Module-level names the call arguments may reference.
        assignments = {
            node.targets[0].id: node.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr == "create_table":
                table = _string_arg(node, 0)
                if not table:
                    continue
                for child in _resolve(node, assignments):
                    if (
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Attribute)
                        and child.func.attr == "Column"
                    ):
                        name = _string_arg(child, 0)
                        if name:
                            tables.setdefault(table, set()).add(name)
            elif node.func.attr == "add_column":
                table = _string_arg(node, 0)
                if not table:
                    continue
                for child in _resolve(node, assignments)[1:]:
                    if (
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Attribute)
                        and child.func.attr == "Column"
                    ):
                        name = _string_arg(child, 0)
                        if name:
                            tables.setdefault(table, set()).add(name)
    return tables


def test_migration_chain_is_linear_and_terminates_at_one_head() -> None:
    """Two heads, or a missing ``down_revision``, silently forks the chain.

    Either way ``alembic upgrade head`` stops being unambiguous, and the
    database that gets built is not the one anyone reviewed.
    """
    revisions: dict[str, str | None] = {}
    for path in sorted(VERSIONS_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        found: dict[str, str | None] = {}
        for node in tree.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.target.id == "revision" and isinstance(node.value, ast.Constant):
                    found["revision"] = node.value.value
                if node.target.id == "down_revision":
                    value = node.value
                    found["down_revision"] = (
                        value.value
                        if isinstance(value, ast.Constant)
                        else None  # e.g. down_revision = None for the first
                    )
        assert "revision" in found, f"{path.name} declares no revision id"
        assert "down_revision" in found, (
            f"{path.name} declares no down_revision; omitting it starts a parallel chain"
        )
        revisions[found["revision"]] = found["down_revision"]

    parents = [parent for parent in revisions.values() if parent is not None]
    assert len(set(parents)) == len(parents), (
        "two revisions declare the same parent: the chain forks"
    )
    for revision, parent in revisions.items():
        assert parent is None or parent in revisions, f"{revision} revises unknown {parent!r}"
    roots = [revision for revision, parent in revisions.items() if parent is None]
    assert len(roots) == 1, f"expected exactly one root revision, found {roots}"


def test_migrated_schema_matches_the_models() -> None:
    """Every model column is migrated, and every migrated column is a model column.

    Both directions matter. A missing model column is a runtime ``INSERT``
    error; a migrated column the models do not know about is how a renamed or
    dropped field silently stops being written while still looking fine.
    """
    migrated = _migrated_columns()
    differences: list[str] = []

    for table_name, table in Base.metadata.tables.items():
        if table_name not in migrated:
            differences.append(f"table {table_name!r} is declared but never migrated")
            continue
        for column_name in table.columns.keys():
            if column_name not in migrated[table_name]:
                differences.append(
                    f"{table_name}.{column_name} is declared in the models but never migrated"
                )
    for table_name, columns in migrated.items():
        if table_name not in Base.metadata.tables:
            continue
        for column_name in columns:
            if column_name not in Base.metadata.tables[table_name].columns:
                differences.append(
                    f"{table_name}.{column_name} is migrated but absent from the models"
                )

    assert not differences, "schema drift:\n  " + "\n  ".join(differences)


def test_every_migration_offers_a_downgrade() -> None:
    """A migration without ``downgrade()`` cannot be rolled back."""
    for path in sorted(VERSIONS_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        functions = {
            node.name for node in tree.body if isinstance(node, ast.FunctionDef)
        }
        assert "upgrade" in functions, f"{path.name} has no upgrade()"
        assert "downgrade" in functions, f"{path.name} has no downgrade()"


def test_no_migration_adds_a_column_an_earlier_one_already_created() -> None:
    """A repeated ``add_column`` aborts the upgrade partway through.

    The other tests in this module compare the *union* of every column any
    migration mentions against the models. A duplicate is invisible to that
    comparison — both migrations name the same column, the set is unchanged,
    and every assertion passes. Only running the chain catches it.

    This is not hypothetical: migration 0003 re-added ``dataset_version``,
    which 0002 had already created on ``backtest_runs``, so ``alembic upgrade
    head`` failed on every fresh database and the defect sat undetected behind
    a fully green suite.
    """
    created: dict[str, dict[str, str]] = {}
    duplicates: list[str] = []

    for path in sorted(VERSIONS_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            # Both `create_table("t", Column(...))` and
            # `add_column("t", Column(...))` name their table first.
            if node.func.attr not in {"create_table", "add_column"} or not node.args:
                continue
            table = _string_arg(node, 0)
            if table is None or table == "":
                continue
            for child in node.args[1:]:
                for column in ast.walk(child):
                    if (
                        isinstance(column, ast.Call)
                        and isinstance(column.func, ast.Attribute)
                        and column.func.attr == "Column"
                    ):
                        name = _string_arg(column, 0)
                        if not name:
                            continue
                        if name in created.setdefault(table, {}):
                            duplicates.append(
                                f"{path.name} adds {table}.{name}, already "
                                f"created by {created[table][name]}"
                            )
                        else:
                            created[table][name] = path.name

    assert not duplicates, "duplicate column migrations:\n  " + "\n  ".join(duplicates)


def _migrate(monkeypatch: Any, database: Path, revision: str) -> None:
    """Run Alembic against an isolated SQLite file, not the configured DB."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database}")
    get_settings.cache_clear()
    config = Config(str(VERSIONS_DIR.parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(VERSIONS_DIR.parent))
    try:
        command.upgrade(config, revision)
    finally:
        get_settings.cache_clear()


def _tables(database: Path) -> set[str]:
    with sqlite3.connect(database) as connection:
        return {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }


def test_stage3e_upgrade_builds_a_fresh_sqlite_database(
    monkeypatch: Any, tmp_path: Path
) -> None:
    """The new constraint must be created inline: SQLite cannot ALTER it in."""
    database = tmp_path / "fresh.sqlite"
    _migrate(monkeypatch, database, "head")

    tables = _tables(database)
    assert {"experiments", "evaluation_reports", "backtest_runs"} <= tables

    with sqlite3.connect(database) as connection:
        experiment_ddl = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'experiments'"
        ).fetchone()[0]
        experiment_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(experiments)")
        }
        report_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(evaluation_reports)")
        }

    assert "uq_experiments_idempotency_key UNIQUE (idempotency_key)" in experiment_ddl
    assert "FOREIGN KEY(backtest_run_id)" in experiment_ddl
    assert "FOREIGN KEY(evaluation_report_id)" in experiment_ddl
    assert {
        "configuration",
        "configuration_fingerprint",
        "idempotency_key",
        "status",
        "failure_stage",
        "failure_reason",
        "backtest_run_id",
        "evaluation_report_id",
    } <= experiment_columns
    assert {"report", "report_digest", "input_fingerprint", "run_id"} <= report_columns


def test_stage3e_upgrade_and_downgrade_preserve_existing_data(
    monkeypatch: Any, tmp_path: Path
) -> None:
    """Upgrading an existing database must not reset unrelated research data."""
    database = tmp_path / "existing.sqlite"
    _migrate(monkeypatch, database, "20261003_0005")
    assert "experiments" not in _tables(database)

    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO markets (id, name, venue, market_type, timezone) "
            "VALUES (?, ?, ?, ?, ?)",
            ("market-1", "Spot", "fixture", "spot", "UTC"),
        )
        connection.commit()

    _migrate(monkeypatch, database, "head")
    assert {"experiments", "evaluation_reports"} <= _tables(database)
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT name FROM markets WHERE id = ?", ("market-1",)
        ).fetchone()[0] == "Spot"

    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database}")
    get_settings.cache_clear()
    config = Config(str(VERSIONS_DIR.parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(VERSIONS_DIR.parent))
    try:
        command.downgrade(config, "20261003_0005")
    finally:
        get_settings.cache_clear()

    assert "experiments" not in _tables(database)
    assert "evaluation_reports" not in _tables(database)
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT name FROM markets WHERE id = ?", ("market-1",)
        ).fetchone()[0] == "Spot"


def test_stage3g_upgrade_builds_the_engine_equity_point_table(
    monkeypatch: Any, tmp_path: Path
) -> None:
    """The exact engine series needs an append-only run child table."""
    database = tmp_path / "fresh.sqlite"
    _migrate(monkeypatch, database, "head")

    assert "backtest_equity_points" in _tables(database)
    with sqlite3.connect(database) as connection:
        ddl = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' "
            "AND name = 'backtest_equity_points'"
        ).fetchone()[0]
        point_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(backtest_equity_points)")
        }
        run_columns = {row[1] for row in connection.execute("PRAGMA table_info(backtest_runs)")}
        trade_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(backtest_trades)")
        }

    # `bar_index`, not timestamp, is the event key: duplicate close times are
    # legitimate for candles from different sources.
    assert "uq_backtest_equity_points_run_bar UNIQUE (run_id, bar_index)" in ddl
    assert "FOREIGN KEY(run_id)" in ddl and "ON DELETE CASCADE" in ddl
    assert {
        "run_id",
        "bar_index",
        "timestamp",
        "equity",
        "cash",
        "unrealized",
        "position_side",
        "drawdown",
    } <= point_columns
    assert "accounting_model_version" in run_columns
    assert {
        "entry_fee",
        "exit_fee",
        "raw_exit_price",
        "entry_concession",
        "exit_concession",
    } <= trade_columns


def test_stage3g_upgrade_preserves_history_and_downgrade_removes_only_new_data(
    monkeypatch: Any, tmp_path: Path
) -> None:
    """Historical runs stay readable and are never backfilled or invented."""
    database = tmp_path / "existing.sqlite"
    _migrate(monkeypatch, database, "20261125_0006")
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO backtest_runs (id, strategy_name, symbol, timeframe, "
            "period_start, period_end, candle_count, initial_capital, final_equity, "
            "fee_rate, spread_rate, slippage_rate, latency_bars, cost_scale, "
            "parameters, metrics) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "run-1",
                "buy_and_hold",
                "BTCUSDT",
                "5m",
                "2024-01-01T00:00:00+00:00",
                "2024-01-01T00:10:00+00:00",
                3,
                10000,
                10000,
                0,
                0,
                0,
                1,
                1,
                "{}",
                "{}",
            ),
        )
        connection.execute(
            "INSERT INTO backtest_trades (id, run_id, sequence, side, entry_time, "
            "entry_price, exit_time, exit_price, size, gross_pnl, fees, net_pnl, "
            "bars_held, exit_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "trade-1",
                "run-1",
                0,
                "long",
                "2024-01-01T00:00:00+00:00",
                100,
                "2024-01-01T00:05:00+00:00",
                100,
                1,
                0,
                0,
                0,
                1,
                "end_of_data",
            ),
        )
        connection.commit()

    _migrate(monkeypatch, database, "head")
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT strategy_name FROM backtest_runs WHERE id = ?", ("run-1",)
        ).fetchone()[0] == "buy_and_hold"
        assert connection.execute(
            "SELECT COUNT(*) FROM backtest_trades WHERE run_id = ?", ("run-1",)
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT accounting_model_version FROM backtest_runs WHERE id = ?", ("run-1",)
        ).fetchone()[0] is None
        assert connection.execute(
            "SELECT entry_fee FROM backtest_trades WHERE id = ?", ("trade-1",)
        ).fetchone()[0] is None
        assert connection.execute(
            "SELECT COUNT(*) FROM backtest_equity_points WHERE run_id = ?", ("run-1",)
        ).fetchone()[0] == 0

    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database}")
    get_settings.cache_clear()
    config = Config(str(VERSIONS_DIR.parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(VERSIONS_DIR.parent))
    try:
        command.downgrade(config, "20261125_0006")
    finally:
        get_settings.cache_clear()

    assert "backtest_equity_points" not in _tables(database)
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT id FROM backtest_runs WHERE id = ?", ("run-1",)
        ).fetchone()[0] == "run-1"
        assert connection.execute(
            "SELECT id FROM backtest_trades WHERE id = ?", ("trade-1",)
        ).fetchone()[0] == "trade-1"


def test_stage3h_upgrade_builds_the_run_manifest_table(
    monkeypatch: Any, tmp_path: Path
) -> None:
    """Exactly one immutable manifest per run is enforced by the schema."""
    database = tmp_path / "fresh.sqlite"
    _migrate(monkeypatch, database, "head")

    assert "run_manifests" in _tables(database)
    with sqlite3.connect(database) as connection:
        ddl = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'run_manifests'"
        ).fetchone()[0]
        columns = {row[1] for row in connection.execute("PRAGMA table_info(run_manifests)")}

    assert "uq_run_manifests_run_id UNIQUE (run_id)" in ddl
    assert "FOREIGN KEY(run_id)" in ddl and "ON DELETE CASCADE" in ddl
    assert "FOREIGN KEY(experiment_id)" in ddl
    assert {
        "id",
        "run_id",
        "experiment_id",
        "schema_version",
        "manifest_fingerprint",
        "manifest",
        "created_at",
    } <= columns


def test_stage3h_upgrade_preserves_history_and_downgrade_removes_only_new_table(
    monkeypatch: Any, tmp_path: Path
) -> None:
    """Old runs get no manifest and no invented provenance."""
    database = tmp_path / "existing.sqlite"
    _migrate(monkeypatch, database, "20261128_0007")
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO backtest_runs (id, strategy_name, symbol, timeframe, "
            "period_start, period_end, candle_count, initial_capital, final_equity, "
            "fee_rate, spread_rate, slippage_rate, latency_bars, cost_scale, "
            "parameters, metrics) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "run-legacy",
                "buy_and_hold",
                "BTCUSDT",
                "5m",
                "2024-01-01T00:00:00+00:00",
                "2024-01-01T00:10:00+00:00",
                3,
                10000,
                10000,
                0,
                0,
                0,
                1,
                1,
                "{}",
                "{}",
            ),
        )
        connection.commit()

    _migrate(monkeypatch, database, "head")
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT id FROM backtest_runs WHERE id = ?", ("run-legacy",)
        ).fetchone()[0] == "run-legacy"
        assert connection.execute("SELECT COUNT(*) FROM run_manifests").fetchone()[0] == 0

    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database}")
    get_settings.cache_clear()
    config = Config(str(VERSIONS_DIR.parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(VERSIONS_DIR.parent))
    try:
        command.downgrade(config, "20261128_0007")
    finally:
        get_settings.cache_clear()

    assert "run_manifests" not in _tables(database)
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT id FROM backtest_runs WHERE id = ?", ("run-legacy",)
        ).fetchone()[0] == "run-legacy"
