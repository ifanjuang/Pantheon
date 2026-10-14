"""FastAPI route installer for native PostgreSQL Agency Data.

The HTTP surface is deliberately narrow: normalized reads plus explicit human
Project and Information writes with actor identity and optimistic revisions.
Hermes must use an admitted scoped capability instead of these global routes.
"""

from __future__ import annotations

import hmac
from datetime import date
from typing import Any, Callable, Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from . import agency_data, agency_directory, agency_information, agency_schema, decision_requests
from .agency_change_candidate_api import install_agency_change_candidate_routes
from .hermes_project_change_candidate_api import install_hermes_project_change_candidate_routes
from .policy_gate import PolicyClient


class ProjectContactBody(BaseModel):
    group: str = Field(default="Autres intervenants", min_length=1, max_length=120)
    name: str | None = Field(default=None, max_length=300)
    organization: str | None = Field(default=None, max_length=300)
    role: str | None = Field(default=None, max_length=300)
    email: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=4000)
    source_ref: str | None = Field(default=None, max_length=1000)


class ProjectCreateBody(BaseModel):
    project_id: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=200)
    display_name: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=10_000)
    status: str | None = Field(default=None, max_length=200)
    phase: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=500)
    primary_client: str | None = Field(default=None, max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=50)
    contacts: list[ProjectContactBody] = Field(default_factory=list, max_length=500)
    attributes: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=8, max_length=200)


class ProjectUpdateBody(BaseModel):
    expected_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=200)
    code: str | None = Field(default=None, min_length=1, max_length=200)
    display_name: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=10_000)
    status: str | None = Field(default=None, max_length=200)
    phase: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=500)
    primary_client: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = Field(default=None, max_length=50)
    contacts: list[ProjectContactBody] | None = Field(default=None, max_length=500)
    attributes: dict[str, Any] | None = None


class InformationCreateBody(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    category: str = Field(min_length=1, max_length=200)
    source_type: str = Field(min_length=1, max_length=120)
    source_ref: str | None = Field(default=None, max_length=2000)
    source_note: str | None = Field(default=None, max_length=500_000)
    source_version: str | None = Field(default=None, max_length=200)
    index_label: str = Field(min_length=1, max_length=40)
    information_date: date | None = None
    summary: str = Field(default="", max_length=20_000)
    details: str = Field(default="", max_length=500_000)
    limits: list[str] = Field(default_factory=list, max_length=20)
    type_tags: list[str] = Field(default_factory=list, max_length=50)
    subject_tags: list[str] = Field(default_factory=list, max_length=100)
    author: str | None = Field(default=None, max_length=500)
    status: Literal["draft", "in_progress"] = "draft"


class InformationDeriveBody(BaseModel):
    new_index_label: str = Field(min_length=1, max_length=40)
    source_ref: str | None = Field(default=None, max_length=2000)
    source_note: str | None = Field(default=None, max_length=500_000)
    source_version: str | None = Field(default=None, max_length=200)


class InformationUpdateBody(BaseModel):
    expected_revision: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=500)
    category: str | None = Field(default=None, min_length=1, max_length=200)
    information_date: date | None = None
    summary: str | None = Field(default=None, max_length=20_000)
    details: str | None = Field(default=None, max_length=500_000)
    limits: list[str] | None = Field(default=None, max_length=20)
    type_tags: list[str] | None = Field(default=None, max_length=50)
    subject_tags: list[str] | None = Field(default=None, max_length=100)
    author: str | None = Field(default=None, max_length=500)
    status: Literal["draft", "in_progress"] | None = None


class InformationActBody(BaseModel):
    expected_revision: int = Field(ge=1)
    # Required when Pantheon policy enforcement is active; ignored otherwise.
    human_decision_ref: str | None = Field(default=None, min_length=2, max_length=500)


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        return ""
    return authorization.removeprefix("Bearer ").strip()


def install_agency_data_routes(
    app: FastAPI,
    *,
    with_connection: Callable,
    require_read_key: Callable,
    require_writer_kind: Callable,
    require_actor: Callable,
    require_policy_client: Callable,
) -> None:
    def agency_operation(operation):
        try:
            return with_connection(operation)
        except (
            agency_data.ProjectNotFound,
            agency_directory.PersonNotFound,
            agency_directory.OrganizationNotFound,
            agency_information.InformationNotFound,
        ) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except decision_requests.DecisionRecordNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except decision_requests.DecisionRequestError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except agency_information.AgencyInformationGatePolicyUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except (
            agency_data.GovernanceGateRequired,
            agency_information.InformationGateRequired,
        ) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (
            agency_data.StaleProjectWrite,
            agency_data.IdempotencyConflict,
            agency_information.StaleInformationWrite,
        ) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (
            agency_data.AgencyDataError,
            agency_directory.AgencyDirectoryError,
            agency_information.AgencyInformationError,
        ) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    def require_global_agency_read(
        authorization: str | None = Header(default=None),
    ) -> None:
        supplied = _bearer_token(authorization)
        hermes_key = getattr(app.state, "hermes_api_key", "")
        if hermes_key and hmac.compare_digest(supplied, hermes_key):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hermes global Agency Data reads are disabled; "
                    "use an admitted scoped execution envelope"
                ),
            )
        require_read_key(authorization)

    def require_human_agency_writer(
        authorization: str | None = Header(default=None),
    ) -> Literal["human"]:
        supplied = _bearer_token(authorization)
        hermes_key = getattr(app.state, "hermes_api_key", "")
        editor_key = getattr(app.state, "editor_api_key", "")
        hermes_match = bool(hermes_key and hmac.compare_digest(supplied, hermes_key))
        editor_match = bool(editor_key and hmac.compare_digest(supplied, editor_key))
        if hermes_match and editor_match:
            raise HTTPException(
                status_code=503,
                detail="editor and Hermes Agency Data keys must be distinct",
            )
        if hermes_match:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Hermes direct Agency Data writes are disabled; "
                    "use an admitted bounded capability"
                ),
            )
        writer_kind = require_writer_kind(authorization)
        if writer_kind != "human":
            raise HTTPException(
                status_code=403,
                detail="global Agency Data writes require a human editor credential",
            )
        return "human"

    @app.get("/agency/schema/project")
    def get_project_schema(
        view: str = agency_schema.DEFAULT_PROJECT_VIEW,
        _authorized: None = Depends(require_global_agency_read),
    ) -> dict:
        try:
            schema = agency_schema.get_project_schema(view)
        except agency_schema.AgencySchemaError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "system_of_record": "postgres",
            "schema": schema,
            "authorization_inferred": False,
        }

    @app.get("/agency/projects")
    def list_projects(
        q: str | None = None,
        limit: int = 100,
        _authorized: None = Depends(require_global_agency_read),
    ) -> dict:
        projects = agency_operation(
            lambda conn: agency_data.list_projects(conn, query=q, limit=limit)
        )
        return {
            "system_of_record": "postgres",
            "scope_match": "agency_projects",
            "projects": projects,
        }

    @app.get("/agency/projects/{project_id}")
    def get_project(
        project_id: str,
        _authorized: None = Depends(require_global_agency_read),
    ) -> dict:
        project = agency_operation(lambda conn: agency_data.get_project(conn, project_id))
        return {"system_of_record": "postgres", "project": project}

    @app.get("/agency/projects/{project_id}/information")
    def list_project_information(
        project_id: str,
        _authorized: None = Depends(require_global_agency_read),
    ) -> dict:
        information = agency_operation(
            lambda conn: agency_information.list_project_information(conn, project_id)
        )
        return {
            "system_of_record": "postgres",
            "project_id": project_id,
            "information": information,
            "card_contract": {
                "entity_type": "information",
                "authorization_inferred": False,
                "front": agency_schema.get_information_schema("cockpit_front"),
                "back": agency_schema.get_information_schema("cockpit_back"),
            },
        }

    @app.get("/agency/information/{information_id}/context")
    def get_information_context(
        information_id: str,
        _authorized: None = Depends(require_global_agency_read),
    ) -> dict:
        context = agency_operation(
            lambda conn: agency_information.get_information_context(conn, information_id)
        )
        return {
            "system_of_record": "postgres",
            "information_context": context,
        }

    @app.get("/agency/people")
    def list_people(
        q: str | None = None,
        limit: int = 100,
        _authorized: None = Depends(require_global_agency_read),
    ) -> dict:
        people = agency_operation(
            lambda conn: agency_directory.list_people(conn, query=q, limit=limit)
        )
        return {
            "system_of_record": "postgres",
            "scope_match": "agency_people",
            "people": people,
        }

    @app.get("/agency/people/{person_id}")
    def get_person(
        person_id: str,
        _authorized: None = Depends(require_global_agency_read),
    ) -> dict:
        person = agency_operation(lambda conn: agency_directory.get_person(conn, person_id))
        return {"system_of_record": "postgres", "person": person}

    @app.get("/agency/organizations")
    def list_organizations(
        q: str | None = None,
        limit: int = 100,
        _authorized: None = Depends(require_global_agency_read),
    ) -> dict:
        organizations = agency_operation(
            lambda conn: agency_directory.list_organizations(conn, query=q, limit=limit)
        )
        return {
            "system_of_record": "postgres",
            "scope_match": "agency_organizations",
            "organizations": organizations,
        }

    @app.get("/agency/organizations/{organization_id}")
    def get_organization(
        organization_id: str,
        _authorized: None = Depends(require_global_agency_read),
    ) -> dict:
        organization = agency_operation(
            lambda conn: agency_directory.get_organization(conn, organization_id)
        )
        return {"system_of_record": "postgres", "organization": organization}

    @app.post("/agency/projects", status_code=201)
    def create_project(
        body: ProjectCreateBody,
        writer_kind: Literal["human"] = Depends(require_human_agency_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        values = body.model_dump()
        values["contacts"] = [item.model_dump(exclude_none=True) for item in body.contacts]
        idempotency_key = values.pop("idempotency_key")
        project = agency_operation(
            lambda conn: agency_data.create_project(
                conn,
                actor=actor,
                actor_kind=writer_kind,
                idempotency_key=idempotency_key,
                **values,
            )
        )
        return {
            "system_of_record": "postgres",
            "effect": "internal_agency_data_write",
            "approval_inferred": False,
            "project": project,
        }

    @app.patch("/agency/projects/{project_id}")
    def update_project(
        project_id: str,
        body: ProjectUpdateBody,
        writer_kind: Literal["human"] = Depends(require_human_agency_writer),
        actor: str = Depends(require_actor),
    ) -> dict:
        supplied = body.model_dump(exclude_unset=True)
        if "contacts" in supplied and supplied["contacts"] is not None:
            supplied["contacts"] = [
                item if isinstance(item, dict) else item.model_dump(exclude_none=True)
                for item in supplied["contacts"]
            ]
        expected_revision = supplied.pop("expected_revision")
        idempotency_key = supplied.pop("idempotency_key")
        project = agency_operation(
            lambda conn: agency_data.update_project(
                conn,
                project_id=project_id,
                changes=supplied,
                actor=actor,
                actor_kind=writer_kind,
                expected_revision=expected_revision,
                idempotency_key=idempotency_key,
            )
        )
        return {
            "system_of_record": "postgres",
            "effect": "internal_agency_data_write",
            "approval_inferred": False,
            "project": project,
        }

    @app.post("/agency/projects/{project_id}/information", status_code=201)
    def create_information(
        project_id: str,
        body: InformationCreateBody,
        writer_kind: Literal["human"] = Depends(require_human_agency_writer),
        _actor: str = Depends(require_actor),
    ) -> dict:
        values = body.model_dump()
        information = agency_operation(
            lambda conn: agency_information.create_information(
                conn,
                project_id=project_id,
                actor_kind=writer_kind,
                **values,
            )
        )
        return {
            "system_of_record": "postgres",
            "effect": "internal_agency_information_write",
            "approval_inferred": False,
            "information": information,
        }

    @app.post("/agency/information/{information_id}/working-version", status_code=201)
    def derive_information_working_version(
        information_id: str,
        body: InformationDeriveBody,
        writer_kind: Literal["human"] = Depends(require_human_agency_writer),
        _actor: str = Depends(require_actor),
    ) -> dict:
        information = agency_operation(
            lambda conn: agency_information.derive_working_version(
                conn,
                acted_information_id=information_id,
                actor_kind=writer_kind,
                **body.model_dump(),
            )
        )
        return {
            "system_of_record": "postgres",
            "effect": "internal_agency_information_write",
            "approval_inferred": False,
            "information": information,
        }

    @app.patch("/agency/information/{information_id}")
    def update_information(
        information_id: str,
        body: InformationUpdateBody,
        writer_kind: Literal["human"] = Depends(require_human_agency_writer),
        _actor: str = Depends(require_actor),
    ) -> dict:
        supplied = body.model_dump(exclude_unset=True)
        expected_revision = supplied.pop("expected_revision")
        information = agency_operation(
            lambda conn: agency_information.update_working_information(
                conn,
                information_id=information_id,
                changes=supplied,
                expected_revision=expected_revision,
                actor_kind=writer_kind,
            )
        )
        return {
            "system_of_record": "postgres",
            "effect": "internal_agency_information_write",
            "approval_inferred": False,
            "information": information,
        }

    @app.post("/agency/information/{information_id}/act")
    def act_information(
        information_id: str,
        body: InformationActBody,
        writer_kind: Literal["human"] = Depends(require_human_agency_writer),
        actor: str = Depends(require_actor),
        policy_client: PolicyClient | None = Depends(require_policy_client),
    ) -> dict:
        def act(conn):
            canonical_decision = {}
            if policy_client is not None:
                if not body.human_decision_ref:
                    raise decision_requests.DecisionRequestError(
                        "acting Information requires a canonical human Decision reference"
                    )
                canonical_decision = decision_requests.policy_decision_payload(
                    conn, body.human_decision_ref, expectation={}
                )
            return agency_information.act_working_information(
                conn,
                information_id=information_id,
                expected_revision=body.expected_revision,
                actor_kind=writer_kind,
                actor=actor,
                policy_client=policy_client,
                decision_payload=canonical_decision,
            )

        information = agency_operation(act)
        return {
            "system_of_record": "postgres",
            "effect": "agency_information_acted",
            "approval_inferred": False,
            "information": information,
        }

    install_agency_change_candidate_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_global_agency_read,
        require_human_writer=require_human_agency_writer,
        require_actor=require_actor,
    )
    install_hermes_project_change_candidate_routes(
        app,
        with_connection=with_connection,
    )
