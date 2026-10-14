"""Read-only persisted Document Structure projection and route contracts."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from mvp_vertical import document_structure_api, document_structure_read


class _Cursor:
    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, _sql, _params):
        return None

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class _Connection:
    def __init__(self, result_sets):
        self._result_sets = iter(result_sets)

    def cursor(self):
        return _Cursor(next(self._result_sets))


def _connection():
    created_at = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    return _Connection(
        [
            [
                (
                    "extraction.demo",
                    "cmp-demo",
                    "needs_review",
                    ["table_span_repaired"],
                    created_at,
                )
            ],
            [
                (
                    0,
                    "heading",
                    "Décomposition du prix",
                    1,
                    1,
                    "#/texts/0",
                    None,
                    [],
                    [],
                    None,
                ),
                (
                    1,
                    "paragraph",
                    "Les montants sont exprimés en euros.",
                    1,
                    1,
                    "#/texts/1",
                    "Décomposition du prix",
                    ["Décomposition du prix"],
                    [],
                    None,
                ),
                (
                    2,
                    "table",
                    "| Lot | HT |\n| --- | --- |\n| Maçonnerie | 10000 |",
                    2,
                    2,
                    "#/tables/0",
                    "Décomposition du prix",
                    ["Décomposition du prix"],
                    ["table_span_repaired"],
                    {"num_rows": 2, "num_cols": 2},
                ),
            ],
            [(0, 0), (0, 1), (1, 2)],
        ]
    )


def test_persisted_structure_preserves_units_fragments_and_all_chunk_links() -> None:
    projection = document_structure_read.get_document_structure(
        _connection(), "document.demo"
    )

    assert projection["structure_id"] == "cmp-demo"
    assert projection["document_ref"] == "document.demo"
    assert [unit["label"] for unit in projection["native_units"]] == [
        "Page 1",
        "Page 2",
    ]
    assert [fragment["fragment_kind"] for fragment in projection["fragments"]] == [
        "section",
        "text",
        "table",
    ]
    assert projection["fragments"][2]["table_data"] == {
        "num_rows": 2,
        "num_cols": 2,
    }
    first_chunk = projection["chunk_anchors"][0]
    expected_refs = [
        projection["fragments"][0]["fragment_id"],
        projection["fragments"][1]["fragment_id"],
    ]
    assert first_chunk["fragment_ref"] == expected_refs[0]
    assert first_chunk["fragment_refs"] == expected_refs
    assert projection["authority"] == {
        "is_source": False,
        "is_evidence": False,
        "is_memory": False,
        "is_professional_validation": False,
    }


def test_structure_route_is_read_key_protected_and_returns_projection(monkeypatch) -> None:
    app = FastAPI()

    def require_read_key(authorization: str | None = Header(default=None)) -> None:
        if authorization != "Bearer read-key":
            raise HTTPException(status_code=401, detail="invalid read API key")

    expected = {"structure_id": "cmp-demo", "fragments": []}
    monkeypatch.setattr(
        document_structure_read,
        "get_document_structure",
        lambda _conn, document_id: {**expected, "document_ref": document_id},
    )
    document_structure_api.install_document_structure_routes(
        app,
        with_connection=lambda operation: operation(object()),
        require_read_key=require_read_key,
    )
    client = TestClient(app)

    assert client.get("/documents/document.demo/structure").status_code == 401
    response = client.get(
        "/documents/document.demo/structure",
        headers={"Authorization": "Bearer read-key"},
    )
    assert response.status_code == 200
    assert response.json()["document_ref"] == "document.demo"


def test_structure_route_maps_missing_compilation_to_404(monkeypatch) -> None:
    app = FastAPI()
    monkeypatch.setattr(
        document_structure_read,
        "get_document_structure",
        lambda _conn, document_id: (_ for _ in ()).throw(
            KeyError(f"unknown compiled document: {document_id}")
        ),
    )
    document_structure_api.install_document_structure_routes(
        app,
        with_connection=lambda operation: operation(object()),
        require_read_key=lambda: None,
    )

    response = TestClient(app).get("/documents/missing/structure")
    assert response.status_code == 404
    assert "unknown compiled document" in response.json()["detail"]
