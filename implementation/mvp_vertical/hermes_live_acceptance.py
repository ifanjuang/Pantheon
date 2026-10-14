"""Operator-only live acceptance for the governed Hermes Runs binding.

The default posture is observation only. A live run is permitted only for an
already-created synthetic Execution Admission whose immutable handoff question
contains the reviewed acceptance marker and explicitly asks for the two Pantheon
context tools. This module never installs/enables a plugin, approves a Hermes
runtime prompt, stops a run, retries an ambiguous launch, schedules work or
changes production activation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterable
from urllib.parse import quote

from .hermes_run_binding import (
    ExternalHermesRunBinding,
    HermesLaunchReplayRequiresReconciliation,
    HermesRunRegistrationUnknown,
    HermesRunSubmissionUnknown,
)
from .hermes_role_stage_projection import HermesRoleStageProjector
from .hermes_runs_observer import HermesRunsApiObserver

SYNTHETIC_MARKER = "PANTHEON_HERMES_LIVE_ACCEPTANCE_V1"
CONTEXT_TOOLS = ("pantheon_context_manifest", "pantheon_context_entity")
MAX_EVENT_COUNT = 1_000


class HermesLiveAcceptanceError(RuntimeError):
    pass


class HermesLiveAcceptanceRefused(HermesLiveAcceptanceError):
    pass


@dataclass(frozen=True)
class EventCollection:
    events: list[dict[str, Any]]
    stream_complete: bool
    diagnostic: str | None = None
    role_stages: list[dict[str, Any]] = field(default_factory=list)


class PantheonLiveAcceptanceInspector:
    """Read-only inspection/probe client for one bounded Pantheon admission."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        actor: str,
        *,
        timeout: float = 10.0,
        client: Any | None = None,
    ) -> None:
        self._base_url = base_url.strip().rstrip("/")
        self._api_key = api_key.strip()
        self._actor = actor.strip()
        self._timeout = timeout
        self._client = client
        if not self._base_url or not self._api_key or not self._actor:
            raise HermesLiveAcceptanceError(
                "Pantheon base_url, api_key and actor are required for live acceptance"
            )

    def _request(self, path: str, *, allow_refusal: bool = False) -> tuple[int, dict[str, Any]]:
        client = self._client
        owns = client is None
        if owns:
            import httpx

            client = httpx.Client(timeout=self._timeout)
        try:
            response = client.get(
                self._base_url + path,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "X-Pantheon-Hermes-Actor": self._actor,
                    "Accept": "application/json",
                },
                timeout=self._timeout,
            )
            try:
                payload = response.json()
            except Exception as exc:
                raise HermesLiveAcceptanceError(
                    f"Pantheon acceptance surface returned invalid JSON: {path}"
                ) from exc
            if not isinstance(payload, dict):
                raise HermesLiveAcceptanceError(
                    f"Pantheon acceptance surface must return an object: {path}"
                )
            if not allow_refusal:
                try:
                    response.raise_for_status()
                except Exception as exc:
                    raise HermesLiveAcceptanceError(
                        f"Pantheon acceptance surface refused: {path}"
                    ) from exc
            return int(response.status_code), payload
        finally:
            if owns:
                client.close()

    def execution_envelope(self, admission_id: str) -> dict[str, Any]:
        _, payload = self._request(
            f"/v1/hermes/execution-admissions/{quote(admission_id, safe='')}"
        )
        return payload

    def active_manifest(self, admission_id: str) -> dict[str, Any]:
        _, payload = self._request(
            f"/v1/hermes/execution-admissions/{quote(admission_id, safe='')}/active-context"
        )
        return payload

    def probe_out_of_scope(
        self,
        *,
        admission_id: str,
        entity_type: str,
        entity_id: str,
    ) -> dict[str, Any]:
        status, payload = self._request(
            "/v1/hermes/execution-admissions/"
            f"{quote(admission_id, safe='')}/active-context/entities/"
            f"{quote(entity_type, safe='')}/{quote(entity_id, safe='')}",
            allow_refusal=True,
        )
        detail = str(payload.get("detail") or "")
        return {
            "http_status": status,
            "refused": status >= 400,
            "scope_refusal_verified": (
                status == 409 and "outside the exact admitted Context Pack" in detail
            ),
            "detail": detail[:500],
        }

    def probe_context_closed(self, admission_id: str) -> dict[str, Any]:
        status, payload = self._request(
            f"/v1/hermes/execution-admissions/{quote(admission_id, safe='')}/active-context",
            allow_refusal=True,
        )
        detail = str(payload.get("detail") or "")
        return {
            "http_status": status,
            "closed": status == 409 and "requires a running Hermes run" in detail,
            "detail": detail[:500],
        }


class HermesRunEventInspector:
    """Read one known run's status and finite SSE event stream; never stops/approves."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = 90.0,
        client: Any | None = None,
    ) -> None:
        self._base_url = base_url.strip().rstrip("/")
        self._api_key = api_key.strip()
        self._timeout = timeout
        self._client = client
        if not self._base_url or not self._api_key:
            raise HermesLiveAcceptanceError("Hermes base_url and api_key are required")

    def status(self, run_id: str) -> dict[str, Any]:
        client = self._client
        owns = client is None
        if owns:
            import httpx

            client = httpx.Client(timeout=self._timeout)
        try:
            response = client.get(
                f"{self._base_url}/v1/runs/{quote(run_id, safe='')}",
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise HermesLiveAcceptanceError("Hermes run status must be an object")
            return payload
        except HermesLiveAcceptanceError:
            raise
        except Exception as exc:
            raise HermesLiveAcceptanceError("cannot read Hermes run status") from exc
        finally:
            if owns:
                client.close()

    def collect_events(self, run_id: str) -> EventCollection:
        client = self._client
        owns = client is None
        if owns:
            import httpx

            client = httpx.Client(timeout=self._timeout)
        events: list[dict[str, Any]] = []
        role_stages: list[dict[str, Any]] = []
        projector = HermesRoleStageProjector(run_id)
        try:
            with client.stream(
                "GET",
                f"{self._base_url}/v1/runs/{quote(run_id, safe='')}/events",
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line or line.startswith(":") or not line.startswith("data:"):
                        continue
                    raw = line.removeprefix("data:").strip()
                    try:
                        event = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        raise HermesLiveAcceptanceError(
                            "Hermes run event stream contained invalid JSON"
                        ) from exc
                    if not isinstance(event, dict):
                        raise HermesLiveAcceptanceError(
                            "Hermes run event stream contained a non-object event"
                        )
                    events.append(event)
                    role_stages.extend(projector.feed(event))
                    if len(events) > MAX_EVENT_COUNT:
                        raise HermesLiveAcceptanceError(
                            f"Hermes run event stream exceeds {MAX_EVENT_COUNT} events"
                        )
                    if event.get("event") in {
                        "run.completed",
                        "run.failed",
                        "run.cancelled",
                        "approval.request",
                    }:
                        return EventCollection(
                            events=events,
                            stream_complete=event.get("event") != "approval.request",
                            diagnostic=(
                                "run requires human runtime approval; acceptance helper does not approve"
                                if event.get("event") == "approval.request"
                                else None
                            ),
                            role_stages=role_stages,
                        )
            return EventCollection(
                events=events,
                stream_complete=True,
                role_stages=role_stages,
            )
        except HermesLiveAcceptanceError:
            raise
        except Exception as exc:
            return EventCollection(
                events=events,
                stream_complete=False,
                diagnostic=f"event stream incomplete: {type(exc).__name__}",
                role_stages=role_stages,
            )
        finally:
            if owns:
                client.close()


def _validate_synthetic_envelope(
    envelope: dict[str, Any],
    *,
    marker: str = SYNTHETIC_MARKER,
) -> dict[str, str]:
    question = str(envelope.get("question") or "")
    context_pack = envelope.get("context_pack") or {}
    if not isinstance(context_pack, dict):
        raise HermesLiveAcceptanceRefused("execution envelope has no Context Pack object")
    root = context_pack.get("root_entity") or {}
    if not isinstance(root, dict):
        raise HermesLiveAcceptanceRefused("execution envelope has no root entity")
    root_id = str(root.get("entity_id") or "").strip()
    root_type = str(root.get("entity_type") or "").strip()
    if marker not in question:
        raise HermesLiveAcceptanceRefused(
            f"synthetic acceptance question must contain marker {marker!r}"
        )
    if "synthetic" not in root_id.casefold():
        raise HermesLiveAcceptanceRefused(
            "synthetic acceptance root entity_id must contain 'synthetic'"
        )
    missing_tools = [tool for tool in CONTEXT_TOOLS if tool not in question]
    if missing_tools:
        raise HermesLiveAcceptanceRefused(
            "synthetic acceptance question must explicitly request: "
            + ", ".join(missing_tools)
        )
    if not root_id or not root_type:
        raise HermesLiveAcceptanceRefused("synthetic acceptance root identity is incomplete")
    return {"entity_id": root_id, "entity_type": root_type}


def _tool_event_assessment(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    started: set[str] = set()
    completed: set[str] = set()
    tool_errors: set[str] = set()
    terminal_event: str | None = None
    for event in events:
        event_type = str(event.get("event") or "")
        tool = str(event.get("tool") or "").strip()
        if event_type == "tool.started" and tool:
            started.add(tool)
        elif event_type == "tool.completed" and tool:
            completed.add(tool)
            if event.get("error") is True:
                tool_errors.add(tool)
        if event_type in {"run.completed", "run.failed", "run.cancelled"}:
            terminal_event = event_type
    return {
        "started_tools": sorted(started),
        "completed_tools": sorted(completed),
        "tool_errors": sorted(tool_errors),
        "required_tools_started": all(tool in started for tool in CONTEXT_TOOLS),
        "required_tools_completed": all(tool in completed for tool in CONTEXT_TOOLS),
        "required_tools_error_free": all(tool not in tool_errors for tool in CONTEXT_TOOLS),
        "terminal_event": terminal_event,
    }


def _ambiguous_receipt(
    *,
    admission_id: str,
    observation: dict[str, Any],
    reason: str,
    launch_reservation_id: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    return {
        "object_type": "hermes_live_binding_acceptance_receipt",
        "synthetic": True,
        "marker": SYNTHETIC_MARKER,
        "admission_id": admission_id,
        "run_id": run_id,
        "launch_reservation_id": launch_reservation_id,
        "live_run_attempted": True,
        "observation": observation,
        "target_binding_status": "inconclusive",
        "distributed_ambiguity": True,
        "ambiguity_reason": reason,
        "operator_reconciliation_required": True,
        "automatic_retry_performed": False,
        "automatic_stop_performed": False,
        "automatic_approval_performed": False,
        "technical_receipt_is_evidence": False,
        "activation_changed": False,
        "production_authorization": False,
        "non_equivalences": [
            "ambiguous submission != retry instruction",
            "known run_id != Pantheon registration success",
            "technical receipt != Evidence",
        ],
    }


class HermesLiveBindingAcceptance:
    """Orchestrate one explicit synthetic target proof with no hidden retries."""

    def __init__(
        self,
        *,
        observer: HermesRunsApiObserver,
        binding: ExternalHermesRunBinding,
        pantheon: PantheonLiveAcceptanceInspector,
        hermes: HermesRunEventInspector,
    ) -> None:
        self._observer = observer
        self._binding = binding
        self._pantheon = pantheon
        self._hermes = hermes

    def observe_only(self) -> dict[str, Any]:
        observation = self._observer.observe()
        return {
            "object_type": "hermes_live_binding_acceptance_receipt",
            "synthetic": True,
            "live_run_attempted": False,
            "observation": observation,
            "target_binding_status": "not_run",
            "technical_receipt_is_evidence": False,
            "activation_changed": False,
            "production_authorization": False,
        }

    def run_live(
        self,
        *,
        admission_id: str,
        idempotency_key: str,
        ack: str,
    ) -> dict[str, Any]:
        if ack != "SYNTHETIC_ONLY":
            raise HermesLiveAcceptanceRefused(
                "live Hermes acceptance requires explicit ack SYNTHETIC_ONLY"
            )
        if not admission_id.startswith("admission-"):
            raise HermesLiveAcceptanceRefused("a concrete Pantheon admission_id is required")
        if len(idempotency_key.strip()) < 8:
            raise HermesLiveAcceptanceRefused("idempotency_key must contain at least 8 characters")

        observation = self._observer.observe()
        if observation.get("runs_api_status") != "compatible":
            raise HermesLiveAcceptanceRefused("Hermes Runs API is not compatible")
        if observation.get("safety_status") != "qualified":
            raise HermesLiveAcceptanceRefused(
                "Hermes concrete tool surface is not qualified for synthetic launch"
            )

        envelope = self._pantheon.execution_envelope(admission_id)
        root = _validate_synthetic_envelope(envelope)

        try:
            receipt = self._binding.launch(
                admission_id=admission_id,
                idempotency_key=idempotency_key,
            )
        except HermesRunSubmissionUnknown as exc:
            return _ambiguous_receipt(
                admission_id=admission_id,
                observation=observation,
                reason="Hermes run submission outcome is unknown; explicit reconciliation required",
                launch_reservation_id=exc.launch_reservation_id,
            )
        except HermesRunRegistrationUnknown as exc:
            return _ambiguous_receipt(
                admission_id=admission_id,
                observation=observation,
                reason="Hermes returned run_id but Pantheon start registration is unknown",
                launch_reservation_id=exc.launch_reservation_id,
                run_id=exc.run_id,
            )
        except HermesLaunchReplayRequiresReconciliation:
            return _ambiguous_receipt(
                admission_id=admission_id,
                observation=observation,
                reason="launch reservation replay requires explicit reconciliation; resubmission forbidden",
            )

        run_id = str(receipt.get("run_id") or "")
        if not run_id:
            raise HermesLiveAcceptanceError("launch receipt contains no Hermes run_id")

        status_after_start = self._hermes.status(run_id)
        session_echo_verified = status_after_start.get("session_id") == admission_id

        manifest = self._pantheon.active_manifest(admission_id)
        manifest_entities = manifest.get("entities") or []
        manifest_root_present = any(
            isinstance(item, dict)
            and item.get("entity_id") == root["entity_id"]
            and item.get("entity_type") == root["entity_type"]
            for item in manifest_entities
        )
        outside_probe = self._pantheon.probe_out_of_scope(
            admission_id=admission_id,
            entity_type=root["entity_type"],
            entity_id=f"{root['entity_type']}:synthetic-outside-scope-probe",
        )

        event_collection = self._hermes.collect_events(run_id)
        event_assessment = _tool_event_assessment(event_collection.events)
        final_status = self._hermes.status(run_id)
        runtime_status = str(final_status.get("status") or "").strip().lower()

        reconciliation: dict[str, Any] | None = None
        post_return_context: dict[str, Any] | None = None
        if runtime_status in {"completed", "failed"}:
            reconciliation = self._binding.reconcile_once(
                launch_receipt=receipt,
                idempotency_key=f"{idempotency_key}:reconcile",
            )
            post_return_context = self._pantheon.probe_context_closed(admission_id)

        checks = {
            "runs_api_compatible": observation.get("runs_api_status") == "compatible",
            "tool_surface_qualified": observation.get("safety_status") == "qualified",
            "session_echo_verified": session_echo_verified,
            "manifest_root_present": manifest_root_present,
            "out_of_scope_refusal_verified": outside_probe["scope_refusal_verified"] is True,
            "required_context_tools_started": event_assessment["required_tools_started"],
            "required_context_tools_completed": event_assessment["required_tools_completed"],
            "required_context_tools_error_free": event_assessment["required_tools_error_free"],
            "runtime_completed": runtime_status == "completed",
            "return_reconciled": bool(
                reconciliation and reconciliation.get("pantheon_return_recorded") is True
            ),
            "active_context_closed_after_return": bool(
                post_return_context and post_return_context.get("closed") is True
            ),
        }

        if not event_collection.stream_complete:
            target_status = "inconclusive"
        elif all(checks.values()):
            target_status = "pass"
        else:
            target_status = "fail"

        return {
            "object_type": "hermes_live_binding_acceptance_receipt",
            "synthetic": True,
            "marker": SYNTHETIC_MARKER,
            "admission_id": admission_id,
            "run_id": run_id,
            "live_run_attempted": True,
            "observation": observation,
            "launch_receipt": {
                key: receipt.get(key)
                for key in (
                    "launch_reservation_id",
                    "snapshot_id",
                    "snapshot_digest",
                    "run_id",
                    "session_id",
                    "runtime_start_recorded",
                    "automatic_retry_performed",
                    "provider_routing_performed",
                    "model_override_performed",
                )
            },
            "status_after_start": {
                key: status_after_start.get(key)
                for key in ("run_id", "status", "session_id", "model")
            },
            "checks": checks,
            "outside_scope_probe": outside_probe,
            "event_assessment": event_assessment,
            "event_stream_complete": event_collection.stream_complete,
            "event_stream_diagnostic": event_collection.diagnostic,
            "final_runtime_status": runtime_status,
            "reconciliation": reconciliation,
            "post_return_context_probe": post_return_context,
            "target_binding_status": target_status,
            "source_contract_session_task_mapping": "verified_upstream_source_not_target_proof",
            "technical_receipt_is_evidence": False,
            "activation_changed": False,
            "plugin_installation_changed": False,
            "plugin_enablement_changed": False,
            "automatic_retry_performed": False,
            "automatic_stop_performed": False,
            "automatic_approval_performed": False,
            "production_authorization": False,
            "non_equivalences": [
                "synthetic acceptance pass != production adoption",
                "session echo != Evidence",
                "tool call success != professional validation",
                "runtime completion != Evidence",
                "plugin installed != approved",
                "binding healthy != binding activated",
            ],
        }
