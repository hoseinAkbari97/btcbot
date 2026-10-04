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
from pathlib import Path

import sqlalchemy as sa

# Importing the package registers every table on ``Base.metadata``.
import app.models  # noqa: F401
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
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
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
    assert len(set(parents)) == len(parents), "two revisions declare the same parent: the chain forks"
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
