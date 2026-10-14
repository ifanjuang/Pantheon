"""A module-scoped database connection must not hold an idle transaction.

psycopg opens a transaction implicitly on the first statement and holds it —
with every lock it took — until commit, rollback or close. A function-scoped
fixture releases that at the end of each test. A *module*-scoped one does not:
it keeps the read locks of its last statement for the whole module.

That is invisible until some other suite runs TRUNCATE, which needs ACCESS
EXCLUSIVE and therefore waits. Serial runs are not immune: the module-scoped
connection is still open while later modules execute. Before this rule the full
suite did not finish at all — a retrieval connection sat `idle in transaction`
while the Information/Source truncations waited behind it. With it, the same
suite completes in under a minute with no skips.

The fix each fixture applies is `autocommit = True`: statements outside an
explicit transaction commit and release immediately, and code that needs
atomicity keeps using `conn.transaction()`.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"

_CONNECT = re.compile(r"\b(?:store|agency_data|psycopg)\.connect\(")


def _module_scoped_connection_fixtures() -> list[tuple[str, str]]:
    """(file, fixture) pairs whose scope is module/session and that open a connection."""
    found: list[tuple[str, str]] = []
    for path in sorted(TESTS.glob("test_*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            decorators = " ".join(ast.unparse(d) for d in node.decorator_list)
            if "fixture" not in decorators:
                continue
            if not re.search(r'scope\s*=\s*["\'](module|session|package)["\']', decorators):
                continue
            body = ast.unparse(node)
            if _CONNECT.search(body):
                found.append((path.name, node.name))
    return found


@pytest.mark.parametrize(
    ("filename", "fixture"),
    _module_scoped_connection_fixtures() or [("<none>", "<none>")],
    ids=lambda value: value,
)
def test_module_scoped_connection_declares_autocommit(filename: str, fixture: str) -> None:
    if filename == "<none>":
        pytest.skip("no module-scoped connection fixture in the suite")

    tree = ast.parse((TESTS / filename).read_text(encoding="utf-8"))
    node = next(
        item
        for item in ast.walk(tree)
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == fixture
    )
    body = ast.unparse(node)

    assert "autocommit = True" in body, (
        f"{filename}::{fixture} opens a connection at module scope without "
        "autocommit. It will hold the implicit transaction of its last statement "
        "— and its locks — for the whole module, and any TRUNCATE elsewhere in "
        "the suite will wait behind it."
    )


@pytest.mark.parametrize(
    ("filename", "fixture"),
    _module_scoped_connection_fixtures() or [("<none>", "<none>")],
    ids=lambda value: value,
)
def test_module_scoped_connection_closes_on_failure(filename: str, fixture: str) -> None:
    """`yield` then `close()` skips the close when setup between them raises."""
    if filename == "<none>":
        pytest.skip("no module-scoped connection fixture in the suite")

    tree = ast.parse((TESTS / filename).read_text(encoding="utf-8"))
    node = next(
        item
        for item in ast.walk(tree)
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == fixture
    )
    has_try_finally = any(
        isinstance(item, ast.Try) and item.finalbody for item in ast.walk(node)
    )
    assert has_try_finally, (
        f"{filename}::{fixture} must close its connection in a finally block, "
        "so a leaked connection cannot outlive the module."
    )
