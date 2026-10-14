#!/usr/bin/env python3
"""Variant-production fixture layered on the qualified Hermes runtime laboratory.

The inherited fixture still proves progressive discovery, admitted context reads
and outside-scope refusal. This layer changes only the synthetic task wording,
final provider output and bounded Pantheon return receipt so the real qualified
Hermes run produces two typed Project change alternatives.
"""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

import hermes_runtime_lab_fixture as base

TASK_CONTRACT_REF = "task-contract-hermes-020-variant-lab"
EXECUTION_RESULT_ID = "execution-result.hermes-020-variant-lab"
RESULT_IDS = ["result.variant.zinc", "result.variant.ardoise"]
REQUEST_SCOPE_DIGEST = "sha256:" + "4" * 64


def _qualified_hermes_version() -> str:
    value = os.environ.get("HERMES_VERSION", "").strip()
    if not value:
        raise RuntimeError("HERMES_VERSION was not supplied by the qualification registry")
    return value


class VariantLabState(base.LabState):
    def __init__(self, journal: Path) -> None:
        super().__init__(journal)
        self.execution_result_returns: list[dict[str, Any]] = []

    def note_execution_result(self, value: dict[str, Any]) -> None:
        results = value.get("results") or []
        sanitized = {
            "execution_result_id": value.get("execution_result_id"),
            "task_contract_ref": value.get("task_contract_ref"),
            "project_ref": value.get("project_ref"),
            "producer_version": (value.get("producer") or {}).get("version"),
            "result_ids": [item.get("result_id") for item in results if isinstance(item, dict)],
            "result_kinds": [item.get("result_kind") for item in results if isinstance(item, dict)],
            "variant_labels": [
                (item.get("payload") or {}).get("variant_label")
                for item in results
                if isinstance(item, dict)
            ],
            "review_dispositions_present": bool(value.get("review_dispositions")),
        }
        with self.lock:
            self.execution_result_returns.append(sanitized)

    def snapshot(self) -> dict[str, Any]:
        value = super().snapshot()
        with self.lock:
            value["execution_result_returns"] = list(self.execution_result_returns)
        return value


def _authority() -> dict[str, bool]:
    return {
        "creates_change_candidate": False,
        "selects_variant": False,
        "applies_project_change": False,
        "creates_project_claim": False,
        "adopts_project_truth": False,
        "creates_decision": False,
        "admits_evidence": False,
        "authorizes_effect": False,
    }


def _result_authority() -> dict[str, bool]:
    return {
        "is_fact": False,
        "is_evidence": False,
        "is_decision": False,
        "is_memory": False,
        "is_apu_write": False,
        "authorizes_external_effect": False,
    }


def _variant_payload(label: str, title: str, material: str) -> dict[str, Any]:
    return {
        "candidate_kind": "project_change_variant",
        "request_ref": "variant-request.project-lab.couverture",
        "request_scope_digest": REQUEST_SCOPE_DIGEST,
        "project_ref": base.PROFILE_ENTITY_ID,
        "base_revision": 1,
        "target_schema_id": "agency.project.v2",
        "variant_label": label,
        "variant_title": title,
        "proposed_attributes": {
            "architectural_style": f"Volumétrie en L sous couverture {material}.",
            "programme_summary": f"Projet laboratoire avec couverture {material}.",
        },
        "rationale": f"Alternative {title} produite pour comparaison humaine.",
        "assumptions": ["La structure porteuse reste compatible."],
        "compatibility_findings": [
            {
                "status": "uncertain",
                "subject": "prescription urbanistique",
                "detail": "Le matériau exact reste à vérifier par le professionnel.",
            }
        ],
        "open_questions": ["Quel vieillissement de surface est attendu ?"],
        "basis_refs": [
            {
                "entity_type": base.PROFILE_ENTITY_TYPE,
                "entity_id": base.PROFILE_ENTITY_ID,
                "observed_revision": 1,
            }
        ],
        "limitations": ["Aucun chiffrage comparatif validé."],
        "authority": _authority(),
    }


def _execution_result() -> dict[str, Any]:
    return {
        "execution_result_id": EXECUTION_RESULT_ID,
        "task_contract_ref": TASK_CONTRACT_REF,
        "project_ref": base.PROFILE_ENTITY_ID,
        "producer": {
            "capability": "compare_project_variants",
            "implementation": "hermes.skill.project-variants",
            "version": _qualified_hermes_version(),
        },
        "produced_at": "2026-08-07T00:00:00+00:00",
        "authority": _result_authority(),
        "results": [
            {
                "result_id": RESULT_IDS[0],
                "result_kind": "project_change_variant",
                "schema_ref": "schemas/project_change_variant_candidate.schema.yaml",
                "payload": _variant_payload(
                    "option-zinc",
                    "Couverture zinc anthracite",
                    "zinc anthracite",
                ),
            },
            {
                "result_id": RESULT_IDS[1],
                "result_kind": "project_change_variant",
                "schema_ref": "schemas/project_change_variant_candidate.schema.yaml",
                "payload": _variant_payload(
                    "option-ardoise",
                    "Couverture ardoise naturelle",
                    "ardoise naturelle",
                ),
            },
        ],
        "clarification_requests": [],
    }


def _provider_envelope() -> str:
    return json.dumps(
        {
            "kind": "pantheon_project_change_variants",
            "summary": (
                "LAB_ACCEPTANCE_COMPLETED: two Project change alternatives produced; "
                "neither selected nor applied."
            ),
            "execution_result": _execution_result(),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


class Handler(base.Handler):
    server_version = "PantheonHermesVariantLab/1"

    @property
    def state(self) -> VariantLabState:
        return self.server.lab_state  # type: ignore[attr-defined]

    def do_POST(self) -> None:  # noqa: N802
        path = unquote(urlsplit(self.path).path)
        admission_prefix = f"/hermes/execution-admissions/{base.ADMISSION_ID}/"
        is_return = path.startswith(admission_prefix) and "/runs/" in path and path.endswith("/return")
        is_reservation = path == admission_prefix + "launch-reservations"
        if not (is_return or is_reservation):
            super().do_POST()
            return

        try:
            body = self._read_json()
        except Exception as exc:
            self._journal()
            self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        self._journal(body)
        if not self._pantheon_auth_ok():
            self._send(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            return
        with self.state.lock:
            self.state.pantheon_writes.append(path)

        if is_reservation:
            self._send(
                HTTPStatus.CREATED,
                {
                    "launch_reservation_id": "launch-reservation-hermes-020-variant-lab",
                    "snapshot_id": "launch-snapshot-hermes-020-variant-lab",
                    "snapshot_digest": "sha256:" + "2" * 64,
                    "work_issue_version": 1,
                    "replayed": False,
                    "snapshot": {
                        "kind": "hermes_launch_context_snapshot",
                        "question": (
                            "Read the admitted manifest and project, verify the outside project "
                            "is refused, then produce exactly two structured roof alternatives."
                        ),
                        "field_projection_version": "hermes-020-variant-lab",
                        "entities": [
                            {
                                "entity_type": base.PROFILE_ENTITY_TYPE,
                                "entity_id": base.PROFILE_ENTITY_ID,
                            }
                        ],
                    },
                },
            )
            return

        execution_result = body.get("execution_result")
        normalized = body.get("normalized_return")
        result_candidate = body.get("result_candidate")
        if not isinstance(execution_result, dict):
            self._send(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": "execution_result required"})
            return
        results = execution_result.get("results")
        valid = (
            execution_result.get("execution_result_id") == EXECUTION_RESULT_ID
            and execution_result.get("task_contract_ref") == TASK_CONTRACT_REF
            and execution_result.get("project_ref") == base.PROFILE_ENTITY_ID
            and (execution_result.get("producer") or {}).get("version")
            == _qualified_hermes_version()
            and isinstance(results, list)
            and len(results) == 2
            and [item.get("result_id") for item in results] == RESULT_IDS
            and all(item.get("result_kind") == "project_change_variant" for item in results)
            and [
                (item.get("payload") or {}).get("variant_label") for item in results
            ]
            == ["option-zinc", "option-ardoise"]
            and not execution_result.get("review_dispositions")
            and isinstance(normalized, dict)
            and normalized.get("result_refs") == RESULT_IDS
            and isinstance(result_candidate, dict)
            and result_candidate.get("result_type")
            == "project_change_variant_execution_result"
        )
        if not valid:
            self._send(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                {"error": "structured Project variant return is invalid"},
            )
            return
        self.state.note_execution_result(execution_result)
        self._send(
            HTTPStatus.OK,
            {
                "runtime_return_recorded": True,
                "work_issue": {"version": 3},
                "execution_result_stored": True,
                "variant_selected": False,
                "result_accepted": False,
                "decision_created": False,
                "evidence_admitted": False,
                "project_mutated": False,
                "external_effect_authorized": False,
            },
        )

    def _handle_chat(self, body: dict[str, Any]) -> None:
        messages = body.get("messages")
        if not isinstance(messages, list):
            self._send(HTTPStatus.BAD_REQUEST, {"error": "messages required"})
            return
        available = set(base._tool_metadata(body)["tool_names"])
        if not base.BRIDGE_TOOLS.issubset(available):
            self._send(
                HTTPStatus.BAD_REQUEST,
                {
                    "error": "Hermes progressive disclosure bridge is incomplete",
                    "available_tool_names": sorted(available),
                    "required_tool_names": sorted(base.BRIDGE_TOOLS),
                },
            )
            return

        results = base._tool_result_messages(messages)
        step = len(results)
        with self.state.lock:
            self.state.provider_calls += 1

        if step == 0:
            response = base._tool_call_message(
                step,
                "tool_search",
                {"queries": ["pantheon context manifest", "pantheon context entity"], "limit": 5},
            )
        elif step == 1:
            response = base._tool_call_message(
                step,
                "tool_describe",
                {"names": ["pantheon_context_manifest"]},
            )
        elif step == 2:
            response = base._tool_call_message(
                step,
                "tool_call",
                {"name": "pantheon_context_manifest", "arguments": {}},
            )
        elif step == 3:
            response = base._tool_call_message(
                step,
                "tool_describe",
                {"names": ["pantheon_context_entity"]},
            )
        elif step == 4:
            response = base._tool_call_message(
                step,
                "tool_call",
                {
                    "name": "pantheon_context_entity",
                    "arguments": {
                        "entity_type": base.PROFILE_ENTITY_TYPE,
                        "entity_id": base.PROFILE_ENTITY_ID,
                    },
                },
            )
        elif step == 5:
            response = base._tool_call_message(
                step,
                "tool_call",
                {
                    "name": "pantheon_context_entity",
                    "arguments": {
                        "entity_type": base.PROFILE_ENTITY_TYPE,
                        "entity_id": base.OUTSIDE_ENTITY_ID,
                    },
                },
            )
        else:
            search_result = str(results[0].get("content", "")) if len(results) > 0 else ""
            manifest_result = str(results[2].get("content", "")) if len(results) > 2 else ""
            admitted_result = str(results[4].get("content", "")) if len(results) > 4 else ""
            refused_result = str(results[5].get("content", "")) if len(results) > 5 else ""
            checks = {
                "search_found_manifest": "pantheon_context_manifest" in search_result,
                "search_found_entity": "pantheon_context_entity" in search_result,
                "manifest_returned": "active_context_manifest" in manifest_result,
                "admitted_entity_returned": base.PROFILE_ENTITY_ID in admitted_result,
                "outside_entity_refused": (
                    "HTTP 404" in refused_result or "outside" in refused_result
                ),
            }
            if not all(checks.values()):
                self._send(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "progressive tool checks failed", "checks": checks},
                )
                return
            response = {
                "id": "chatcmpl-hermes-020-variant-lab-final",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "lab-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": _provider_envelope(),
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 40, "total_tokens": 50},
            }
        self._send_completion(body, response)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9010)
    parser.add_argument("--journal", type=Path, required=True)
    args = parser.parse_args()

    state = VariantLabState(args.journal)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.lab_state = state  # type: ignore[attr-defined]
    print(
        f"Hermes Project variant lab fixture listening on http://{args.host}:{args.port}",
        flush=True,
    )
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
