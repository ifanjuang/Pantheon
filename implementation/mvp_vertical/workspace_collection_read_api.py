"""Read-only Cockpit HTTP surface for filesystem workspace Card collections."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Mapping

from fastapi import Depends, FastAPI, HTTPException, Query

from . import workspace_collection_read


def install_workspace_collection_read_routes(
    app: FastAPI,
    *,
    workspace_roots: Mapping[str, str | Path] | None,
    require_read_key: Callable,
) -> None:
    """Mount the bounded read surface over an explicit server-side root mapping."""
    configured_roots = (
        workspace_roots
        if workspace_roots is not None
        else workspace_collection_read.parse_workspace_roots_config(
            os.getenv("MVP_WORKSPACE_ROOTS_JSON")
        )
    )
    roots = workspace_collection_read.prepare_workspace_roots(configured_roots)
    app.state.workspace_roots = roots

    @app.get("/cockpit/workspace-collections")
    def get_workspace_catalog(
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        return workspace_collection_read.get_workspace_catalog(roots)

    @app.get("/cockpit/workspace-collections/{workspace_ref}")
    def get_workspace_collection(
        workspace_ref: str,
        path: str = Query(default="", max_length=4096),
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        try:
            return workspace_collection_read.get_workspace_collection(
                roots,
                workspace_ref,
                path,
            )
        except (
            workspace_collection_read.WorkspaceNotFound,
            workspace_collection_read.WorkspacePathNotFound,
        ) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except workspace_collection_read.WorkspaceCollectionReadError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
