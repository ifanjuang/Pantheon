from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import httpx
import pytest


LAB_DIR = (
    Path(__file__).resolve().parents[1]
    / "labs"
    / "uhp_hermes_transport"
)
sys.path.insert(0, str(LAB_DIR))

import build_fixtures as FIXTURES  # noqa: E402
import qualification as QUAL  # noqa: E402
import uhp_client as UHP  # noqa: E402


DIGEST = "a" * 64


def _observation(*, arm: str, **overrides):
    raw = {
        "schema": QUAL.SCHEMA,
        "case_id": "T1-core-read-only",
        "arm": arm,
        "admission_id": (
            "admission-native-1141"
            if arm == "native_runs"
            else "admission-uhp-1141"
        ),
        "task_contract_ref": FIXTURES.TASK_CONTRACT_REF,
        "context_pack_ref": FIXTURES.CONTEXT_PACK_REF,
        "execution_basis_digest": DIGEST,
        "runtime_identity": "hermes-runtime-qualification",
        "hermes_identity": "hermes-agent-pinned",
        "profile_identity": "pantheon-governed",
        "model_identity": "qualification-model",
        "protocol_version": (
            None if arm == "native_runs" else "2026-09-28"
        ),
        "result_status": "complete",
        "core_conformance": (
            None if arm == "native_runs" else True
        ),
        "extended_conformance": (
            None if arm == "native_runs" else True
        ),
        "admission_correlation": "proven",
        "effective_tool_surface": "proven",
        "consequential_surface_isolated": True,
        "task_submission_count": 1,
        "automatic_retry_count": 0,
        "stream_case": False,
        "cancellation_case": False,
        "ambiguous_submission_case": False,
        "transient_file_case": False,
        "artifact_case": False,
        "elapsed_seconds": 10.0 if arm == "native_runs" else 11.0,
        "deletion_assessment_complete": arm == "uhp",
        "deletable_native_components": (
            ["native_run_submission"]
            if arm == "uhp"
            else []
        ),
        "retained_native_components": (
            ["effective_tool_surface_observer"]
            if arm == "uhp"
            else []
        ),
        "notes": ["synthetic test observation"],
    }
    raw.update(overrides)
    return raw


def test_ab_requires_distinct_one_shot_admissions_on_same_basis() -> None:
    baseline = _observation(arm="native_runs")
    candidate = _observation(
        arm="uhp",
        admission_id=baseline["admission_id"],
    )

    report = QUAL.compare_observations(
        baseline,
        candidate,
    )

    assert report["comparability"] == "fail"
    assert report["decision"] == "inconclusive"
    assert (
        "A/B arms must use distinct one-shot admission IDs"
        in report["comparability_errors"]
    )


def test_ab_rejects_execution_basis_drift() -> None:
    report = QUAL.compare_observations(
        _observation(arm="native_runs"),
        _observation(
            arm="uhp",
            execution_basis_digest="b" * 64,
        ),
    )

    assert report["comparability"] == "fail"
    assert (
        "execution_basis_digest differs between arms"
        in report["comparability_errors"]
    )


def test_retained_runtime_specific_seam_yields_partial_transport_only() -> None:
    report = QUAL.compare_observations(
        _observation(arm="native_runs"),
        _observation(arm="uhp"),
    )

    assert report["comparability"] == "pass"
    assert report["qualification_failures"] == []
    assert report["qualification_unknowns"] == []
    assert report["decision"] == "partial_transport_only"


def test_full_replacement_requires_real_deletion_and_no_retained_native_seam() -> None:
    report = QUAL.compare_observations(
        _observation(arm="native_runs"),
        _observation(
            arm="uhp",
            retained_native_components=[],
            deletable_native_components=[
                "native_run_submission",
                "native_stream_translation",
            ],
        ),
    )

    assert report["decision"] == "replace_native_binding"


def test_layer_without_deletion_is_rejected_after_complete_assessment() -> None:
    report = QUAL.compare_observations(
        _observation(arm="native_runs"),
        _observation(
            arm="uhp",
            deletable_native_components=[],
            retained_native_components=[],
        ),
    )

    assert report["decision"] == "reject"


def test_unknown_host_correlation_never_becomes_a_pass() -> None:
    report = QUAL.compare_observations(
        _observation(arm="native_runs"),
        _observation(
            arm="uhp",
            admission_correlation="unknown",
        ),
    )

    assert report["decision"] == "inconclusive"
    assert (
        "host-level Pantheon admission correlation is unknown"
        in report["qualification_unknowns"]
    )


def test_failed_host_correlation_rejects_candidate() -> None:
    report = QUAL.compare_observations(
        _observation(arm="native_runs"),
        _observation(
            arm="uhp",
            admission_correlation="not_proven",
        ),
    )

    assert report["decision"] == "reject"
    assert any(
        "admission correlation" in item
        for item in report["qualification_failures"]
    )


def test_transient_file_case_rejects_implicit_persistence() -> None:
    source_sha = "c" * 64
    report = QUAL.compare_observations(
        _observation(
            arm="native_runs",
            case_id="T6-transient-file",
            transient_file_case=True,
            transient_file_sha256=source_sha,
        ),
        _observation(
            arm="uhp",
            case_id="T6-transient-file",
            transient_file_case=True,
            transient_file_sha256=source_sha,
            transient_file_basis_bound=True,
            transient_file_expiry_fail_closed=True,
            transient_file_persisted_to_affaires=True,
            transient_file_persisted_to_hindsight=False,
            transient_file_admitted_as_source=False,
        ),
    )

    assert report["decision"] == "reject"
    assert (
        "transient_file_persisted_to_affaires must remain false "
        "for ask-only transport"
        in report["qualification_failures"]
    )


def test_artifact_case_rejects_automatic_evidence_promotion() -> None:
    artifact_sha = "d" * 64
    report = QUAL.compare_observations(
        _observation(
            arm="native_runs",
            case_id="T7-artifact",
            artifact_case=True,
            artifact_sha256=artifact_sha,
        ),
        _observation(
            arm="uhp",
            case_id="T7-artifact",
            artifact_case=True,
            artifact_sha256=artifact_sha,
            artifact_auto_promoted_to_source=False,
            artifact_auto_promoted_to_knowledge=False,
            artifact_auto_promoted_to_evidence=True,
        ),
    )

    assert report["decision"] == "reject"
    assert (
        "artifact_auto_promoted_to_evidence must remain false"
        in report["qualification_failures"]
    )


def test_fixture_generation_is_deterministic_and_non_sensitive(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    FIXTURES.build_all(first)
    FIXTURES.build_all(second)

    assert (
        (first / "manifest.json").read_bytes()
        == (second / "manifest.json").read_bytes()
    )
    eml = first / "T6-transient-file" / "synthetic.eml"
    manifest = json.loads(
        (first / "manifest.json").read_text(encoding="utf-8")
    )
    assert (
        hashlib.sha256(eml.read_bytes()).hexdigest()
        == manifest["cases"]["T6-transient-file"]["source_sha256"]
    )
    assert b"example.invalid" in eml.read_bytes()
    assert b"agency" not in eml.read_bytes()


def test_uhp_client_submits_exactly_one_responses_request_without_model_override() -> None:
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen.append((request, body))
        return httpx.Response(
            200,
            json={
                "id": "resp_1141",
                "object": "response",
                "status": "completed",
                "model": "runtime-default",
                "output": [],
                "metadata": {"session_id": "hsess1141"},
            },
        )

    client = UHP.UhpClient(
        "https://uhp.invalid",
        "lab-key",
        client=httpx.Client(
            transport=httpx.MockTransport(handler)
        ),
    )
    result = client.submit_task(
        input_value="synthetic",
        harness_id="chrn_hermes",
        idempotency_key="uhp-1141-task-1",
        metadata={
            "pantheon_qualification_case": "T1-core-read-only",
        },
    )

    assert result["id"] == "resp_1141"
    assert len(seen) == 1
    request, body = seen[0]
    assert request.url.path == "/v1/responses"
    assert request.headers["UHP-Version"] == "2026-09-28"
    assert request.headers["Idempotency-Key"] == "uhp-1141-task-1"
    assert body["metadata"]["harness_id"] == "chrn_hermes"
    assert "model" not in body
    assert "provider" not in body


def test_uhp_stream_validation_requires_monotonic_single_terminal_stream() -> None:
    good = [
        {
            "type": "response.created",
            "sequence_number": 0,
        },
        {
            "type": "response.output_text.delta",
            "sequence_number": 1,
        },
        {
            "type": "response.completed",
            "sequence_number": 2,
        },
    ]
    gap = [
        {
            "type": "response.created",
            "sequence_number": 0,
        },
        {
            "type": "response.completed",
            "sequence_number": 2,
        },
    ]

    assert UHP.UhpClient.stream_sequence_valid(good) is True
    assert UHP.UhpClient.stream_sequence_valid(gap) is False


def test_uhp_client_streams_sse_and_cancel_uses_protocol_route() -> None:
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        if request.url.path == "/v1/responses":
            body = (
                'data: {"type":"response.created","sequence_number":0}\n\n'
                'data: {"type":"response.completed","sequence_number":1,'
                '"response":{"id":"resp_1","status":"completed"}}\n\n'
            )
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                text=body,
            )
        if request.url.path == "/v1/responses/resp_1/cancel":
            return httpx.Response(
                200,
                json={
                    "id": "resp_1",
                    "object": "response",
                    "status": "cancelled",
                },
            )
        return httpx.Response(404, json={"error": {}})

    client = UHP.UhpClient(
        "https://uhp.invalid",
        "lab-key",
        client=httpx.Client(
            transport=httpx.MockTransport(handler)
        ),
    )
    events = client.stream_task(
        input_value="synthetic",
        harness_id="chrn_hermes",
        idempotency_key="stream-key-1141",
    )
    cancelled = client.cancel_response("resp_1")

    assert UHP.UhpClient.stream_sequence_valid(events) is True
    assert cancelled["status"] == "cancelled"
    assert seen == [
        ("POST", "/v1/responses"),
        ("POST", "/v1/responses/resp_1/cancel"),
    ]


def test_uhp_file_upload_uses_user_data_multipart_contract(
    tmp_path: Path,
) -> None:
    source = tmp_path / "synthetic.eml"
    source.write_bytes(b"synthetic-1141")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["content_type"] = request.headers["content-type"]
        seen["body"] = request.read()
        return httpx.Response(
            200,
            json={
                "id": "file_1141",
                "object": "file",
                "filename": "synthetic.eml",
                "bytes": len(source.read_bytes()),
            },
        )

    client = UHP.UhpClient(
        "https://uhp.invalid",
        "lab-key",
        client=httpx.Client(
            transport=httpx.MockTransport(handler)
        ),
    )
    uploaded = client.upload_file(
        source,
        media_type="message/rfc822",
    )

    assert uploaded["id"] == "file_1141"
    assert seen["path"] == "/v1/files"
    assert "multipart/form-data" in seen["content_type"]
    assert b'name="purpose"' in seen["body"]
    assert b"user_data" in seen["body"]
    assert b'filename="synthetic.eml"' in seen["body"]


def test_qualification_lab_does_not_import_product_runtime() -> None:
    python_files = list(LAB_DIR.glob("*.py"))
    assert python_files
    for path in python_files:
        source = path.read_text(encoding="utf-8")
        assert "mvp_vertical" not in source

    assert QUAL.AUTHORITY == {
        "qualification_lab_only": True,
        "dispatch_owner": False,
        "authorizes_effect": False,
        "admits_evidence": False,
        "admits_source": False,
        "owns_memory": False,
        "selects_provider": False,
        "changes_runtime_configuration": False,
    }


def test_non_finite_elapsed_time_is_rejected() -> None:
    for value in (float("inf"), float("-inf"), float("nan")):
        with pytest.raises(
            QUAL.TransportQualificationError,
            match="finite non-negative number",
        ):
            QUAL.normalize_observation(
                _observation(
                    arm="native_runs",
                    elapsed_seconds=value,
                )
            )


def test_boolean_flags_fail_closed_instead_of_coercing_strings() -> None:
    with pytest.raises(
        QUAL.TransportQualificationError,
        match="transient_file_case must be boolean",
    ):
        QUAL.normalize_observation(
            _observation(
                arm="uhp",
                transient_file_case="false",
            )
        )


def test_non_complete_native_baseline_cannot_support_transport_adoption() -> None:
    report = QUAL.compare_observations(
        _observation(
            arm="native_runs",
            result_status="partial",
        ),
        _observation(arm="uhp"),
    )

    assert report["decision"] == "inconclusive"
    assert any(
        "native baseline result_status=partial is not complete" in item
        for item in report["qualification_unknowns"]
    )


def test_transient_file_sha_must_match_between_arms() -> None:
    report = QUAL.compare_observations(
        _observation(
            arm="native_runs",
            case_id="T6-transient-file",
            transient_file_case=True,
            transient_file_sha256="1" * 64,
        ),
        _observation(
            arm="uhp",
            case_id="T6-transient-file",
            transient_file_case=True,
            transient_file_sha256="2" * 64,
            transient_file_basis_bound=True,
            transient_file_expiry_fail_closed=True,
            transient_file_persisted_to_affaires=False,
            transient_file_persisted_to_hindsight=False,
            transient_file_admitted_as_source=False,
        ),
    )

    assert report["comparability"] == "fail"
    assert "transient_file_sha256 differs between arms" in report[
        "comparability_errors"
    ]


def test_feature_perimeter_must_match_between_ab_arms() -> None:
    report = QUAL.compare_observations(
        _observation(arm="native_runs", stream_case=False),
        _observation(
            arm="uhp",
            stream_case=True,
            stream_order_valid=True,
            reconnect_read_valid=True,
        ),
    )

    assert report["comparability"] == "fail"
    assert "stream_case differs between arms" in report[
        "comparability_errors"
    ]
