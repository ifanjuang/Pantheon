"""Install the bounded read-only Document Structure route."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, FastAPI, HTTPException

from . import document_structure_read


def install_document_structure_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    require_read_key: Callable,
) -> None:
    """Expose the current persisted structure without adding a write surface."""

    @app.get("/documents/{document_id}/structure")
    def document_structure(
        document_id: str,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        try:
            return with_connection(
                lambda conn: document_structure_read.get_document_structure(
                    conn, document_id
                )
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
