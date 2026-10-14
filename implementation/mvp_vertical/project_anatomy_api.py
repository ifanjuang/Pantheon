"""Read-only API routes for the Project Anatomy Cockpit projection."""

from __future__ import annotations

from typing import Callable

from fastapi import Depends, FastAPI, HTTPException

from . import apu_owner, project_anatomy_projection


def install_project_anatomy_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    require_read_key: Callable,
) -> None:
    """Install the bounded read-only Project Anatomy projection route."""

    @app.get("/agency/projects/{project_id}/project-anatomy")
    def get_project_anatomy(
        project_id: str,
        _authorized: None = Depends(require_read_key),
    ) -> dict:
        try:
            projection = with_connection(
                lambda conn: project_anatomy_projection.get_project_anatomy_projection(
                    conn,
                    project_id=project_id,
                )
            )
        except apu_owner.ApuOwnerNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except apu_owner.ApuOwnerConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except apu_owner.ApuOwnerError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        return {
            "system_of_record": "postgres",
            "project_id": project_id,
            "authorization_inferred": False,
            "project_anatomy": projection,
        }
