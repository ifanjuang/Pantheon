from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


LAB = Path(__file__).resolve().parents[1] / "labs" / "hermes_runtime_efficiency" / "clm_shadow_rank.py"
CORPUS = Path(__file__).resolve().parents[1] / "labs" / "hermes_runtime_efficiency" / "clm_shadow_cases.json"
PIN_REGISTRY = Path(__file__).resolve().parents[1] / "qualification" / "external-pins.json"
SPEC = importlib.util.spec_from_file_location("pantheon_clm_shadow_rank_1047", LAB)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

CLMShadowQualificationError = MODULE.CLMShadowQualificationError
ShadowCase = MODULE.ShadowCase
build_orderings = MODULE.build_orderings
is_loopback_base_url = MODULE.is_loopback_base_url
load_cases = MODULE.load_cases
load_runtime_metadata = MODULE.load_runtime_metadata
run_shadow = MODULE.run_shadow
CANONICAL_PIN = MODULE.load_qualification_pin(PIN_REGISTRY)


def _write_runtime_metadata(tmp_path: Path, **overrides) -> Path:
    raw = {
        "clm_git_ref": CANONICAL_PIN["ref"],
        "clm_package_version": CANONICAL_PIN["version"],
        "encoder_model": CANONICAL_PIN["encoder_model"],
        "encoder_revision": CANONICAL_PIN["encoder_revision"],
        "head_sha256": CANONICAL_PIN["head_sha256"],
        "vllm_version": CANONICAL_PIN["vllm_version"],
        "clm_head_device_name": "cpu",
        "encoder_device_name": "NVIDIA GeForce RTX 4090",
        "encoder_placement": "remote",
        "encoder_transport": "ssh_local_forward",
        "encoder_endpoint": "http://127.0.0.1:18090/v1/embeddings",
        "encoder_node_label": "gpu-node/WSL",
    }
    raw.update(overrides)
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    return path


def _write_one_case(tmp_path: Path) -> Path:
    raw = {
        "schema_id": MODULE.SCHEMA_ID,
        "revision": 1,
        "status": "synthetic_qualification_fixture",
        "cases": [
            {
                "case_id": "case-1",
                "category": "control",
                "context": "An exact source is available but has not yet been read.",
                "question": "What should happen next?",
                "candidates": ["Read the source.", "Guess the answer.", "Ignore the source."],
                "expected_candidates": ["Read the source."],
            }
        ],
    }
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    return path


def test_committed_corpus_is_valid_and_unique() -> None:
    metadata, cases = load_cases(CORPUS)

    assert metadata["schema_id"] == MODULE.SCHEMA_ID
    assert len(cases) == 12
    assert len({case.case_id for case in cases}) == len(cases)
    assert {case.category for case in cases} >= {
        "control",
        "identity",
        "source_authority",
        "evidence",
        "authorization",
        "persistence",
        "observation",
        "provenance",
        "conflict",
        "context_sufficiency",
    }



def test_optional_agency_french_corpus_is_independent_and_usable() -> None:
    """Pantheon-Next#1166 uses the existing Pantheon-Next#1047 runner; the 12-case reference stays frozen."""
    fr_metadata, french_cases = load_cases(CORPUS.with_name("clm_shadow_cases_fr.json"))
    _, reference_cases = load_cases(CORPUS)

    assert fr_metadata["status"] == "synthetic_qualification_fixture"
    assert len(french_cases) == 10
    assert {case.category for case in french_cases} == {
        "email", "document_version", "context_selection"
    }
    assert {case.case_id for case in french_cases}.isdisjoint(
        {case.case_id for case in reference_cases}
    )
    assert all(len(case.candidates) == 4 for case in french_cases)
    assert all(len(case.expected_candidates) == 1 for case in french_cases)
    assert any(
        case.candidates[0] not in case.expected_candidates
        for case in french_cases
    )
    assert all(
        any(char in case.context for char in "éèàùç")
        for case in french_cases
    )


def test_case_validation_rejects_duplicate_or_external_expected_candidates() -> None:
    with pytest.raises(CLMShadowQualificationError, match="unique"):
        ShadowCase.from_mapping(
            {
                "case_id": "x",
                "category": "control",
                "context": "c",
                "question": "q",
                "candidates": ["a", "a"],
                "expected_candidates": ["a"],
            }
        )

    with pytest.raises(CLMShadowQualificationError, match="drawn from candidates"):
        ShadowCase.from_mapping(
            {
                "case_id": "x",
                "category": "control",
                "context": "c",
                "question": "q",
                "candidates": ["a", "b"],
                "expected_candidates": ["c"],
            }
        )


def test_runtime_metadata_requires_exact_clm_and_head_identities(tmp_path: Path) -> None:
    path = _write_runtime_metadata(tmp_path)
    loaded = load_runtime_metadata(path)
    assert loaded["clm_git_ref"] == CANONICAL_PIN["ref"]
    assert loaded["head_sha256"] == CANONICAL_PIN["head_sha256"]

    bad_ref = _write_runtime_metadata(tmp_path, clm_git_ref="main")
    with pytest.raises(CLMShadowQualificationError, match="40-character git SHA"):
        load_runtime_metadata(bad_ref)

    bad_head = _write_runtime_metadata(tmp_path, head_sha256="not-a-digest")
    with pytest.raises(CLMShadowQualificationError, match="SHA-256"):
        load_runtime_metadata(bad_head)



def test_runtime_topology_requires_loopback_and_matching_transport(tmp_path: Path) -> None:
    good = load_runtime_metadata(_write_runtime_metadata(tmp_path))
    MODULE.validate_runtime_topology(good)

    bad_transport = load_runtime_metadata(
        _write_runtime_metadata(tmp_path, encoder_transport="loopback_direct")
    )
    with pytest.raises(CLMShadowQualificationError, match="ssh_local_forward"):
        MODULE.validate_runtime_topology(bad_transport)

    bad_endpoint = load_runtime_metadata(
        _write_runtime_metadata(
            tmp_path,
            encoder_endpoint="http://gpu-node:8090/v1/embeddings",
        )
    )
    with pytest.raises(CLMShadowQualificationError, match="loopback"):
        MODULE.validate_runtime_topology(bad_endpoint)

    local = load_runtime_metadata(
        _write_runtime_metadata(
            tmp_path,
            encoder_placement="local",
            encoder_transport="loopback_direct",
            encoder_endpoint="http://127.0.0.1:8090/v1/embeddings",
            encoder_node_label="linux-local",
        )
    )
    MODULE.validate_runtime_topology(local)


def test_runtime_must_match_canonical_clm_pin(tmp_path: Path) -> None:
    good = _write_runtime_metadata(tmp_path)
    runtime = load_runtime_metadata(good)
    pin = CANONICAL_PIN
    MODULE.validate_runtime_against_pin(runtime, pin)

    for field, value in (
        ("clm_git_ref", "a" * 40),
        ("encoder_revision", "e" * 40),
        ("head_sha256", "f" * 64),
        ("vllm_version", "0.29.0"),
    ):
        bad = _write_runtime_metadata(tmp_path, **{field: value})
        with pytest.raises(CLMShadowQualificationError, match="canonical contrastive-lm qualification pin"):
            MODULE.validate_runtime_against_pin(load_runtime_metadata(bad), pin)


def test_quantized_runtime_receipt_is_exact_and_pinned(tmp_path: Path) -> None:
    quantized = load_runtime_metadata(
        _write_runtime_metadata(
            tmp_path,
            encoder_placement="local",
            encoder_transport="loopback_direct",
            encoder_endpoint="http://127.0.0.1:8091/v1/embeddings",
            encoder_node_label="linux-local",
            encoder_backend="llama.cpp",
            encoder_backend_version=CANONICAL_PIN["experimental_encoder_backend_version"],
            encoder_backend_ref=CANONICAL_PIN["experimental_encoder_backend_ref"],
            encoder_artifact_repository=CANONICAL_PIN["experimental_quantized_encoder_repository"],
            encoder_artifact_revision=CANONICAL_PIN["experimental_quantized_encoder_revision"],
            encoder_artifact_file=CANONICAL_PIN["experimental_q8_file"],
            encoder_artifact_sha256=CANONICAL_PIN["experimental_q8_sha256"],
            encoder_quantization="Q8_0",
            encoder_pooling="last",
        )
    )
    MODULE.validate_runtime_topology(quantized)
    MODULE.validate_runtime_against_pin(quantized, CANONICAL_PIN)

    bad_artifact = dict(quantized)
    bad_artifact["encoder_artifact_sha256"] = "f" * 64
    with pytest.raises(CLMShadowQualificationError, match="canonical contrastive-lm qualification pin"):
        MODULE.validate_runtime_against_pin(bad_artifact, CANONICAL_PIN)


def test_partial_quantized_runtime_receipt_fails_closed(tmp_path: Path) -> None:
    path = _write_runtime_metadata(
        tmp_path,
        encoder_backend="llama.cpp",
        encoder_quantization="Q8_0",
    )
    with pytest.raises(CLMShadowQualificationError, match="quantized runtime metadata missing exact fields"):
        load_runtime_metadata(path)


def test_candidate_orderings_are_deterministic_and_bounded() -> None:
    candidates = ("a", "b", "c", "d")
    first = build_orderings(candidates, 4)
    second = build_orderings(candidates, 4)

    assert first == second
    assert first[0] == ["a", "b", "c", "d"]
    assert ["d", "c", "b", "a"] in first
    assert len(first) == 4
    assert len({tuple(item) for item in first}) == 4


def test_loopback_is_default_boundary() -> None:
    assert is_loopback_base_url("http://127.0.0.1:8700")
    assert is_loopback_base_url("http://localhost:8700")
    assert is_loopback_base_url("http://[::1]:8700")
    assert not is_loopback_base_url("https://example.com")
    assert not is_loopback_base_url("file:///tmp/clm")


def test_shadow_run_records_ranking_without_selecting_or_authorizing(monkeypatch, tmp_path: Path) -> None:
    cases = _write_one_case(tmp_path)
    runtime = _write_runtime_metadata(tmp_path)

    monkeypatch.setattr(
        MODULE,
        "observe_server",
        lambda base_url, model, api_key, timeout: {
            "health": {"ok": True, "embedder": True},
            "models": [model],
            "health_elapsed_ms": 1.0,
            "models_elapsed_ms": 1.0,
        },
    )

    def fake_request(base_url, path, *, method="GET", body=None, api_key=None, timeout=120.0):
        assert path == "/v1/rank"
        assert method == "POST"
        assert body["model"] == "clm-latest"
        assert body["temperature"] == 1.0
        answers = body["answers"]
        fixed = ["Read the source.", "Guess the answer.", "Ignore the source."]
        ranked = [
            {
                "rank": index + 1,
                "candidate": candidate,
                "prob": [0.8, 0.15, 0.05][index],
            }
            for index, candidate in enumerate(fixed)
        ]
        assert set(answers) == {row["candidate"] for row in ranked}
        return {"model": "clm-latest", "ranked": ranked}, {"x-clm-latency-ms": "4.2"}, 5.0

    monkeypatch.setattr(MODULE, "_request_json", fake_request)

    report = run_shadow(
        cases_path=cases,
        runtime_metadata_path=runtime,
        pin_registry_path=PIN_REGISTRY,
        base_url="http://127.0.0.1:8700",
        model="clm-latest",
        api_key=None,
        timeout=10.0,
        max_orderings=3,
        allow_remote=False,
    )

    assert report["status"] == "shadow_observation_only"
    assert report["runtime_metadata"]["encoder_placement"] == "remote"
    assert report["runtime_metadata"]["encoder_transport"] == "ssh_local_forward"
    assert report["runtime_metadata"]["encoder_node_label"] == "gpu-node/WSL"
    assert report["summary"]["expected_top1_all_orderings_rate"] == 1.0
    assert report["summary"]["top_candidate_order_stable_rate"] == 1.0
    assert report["cases"][0]["orderings_observed"] == 3
    assert report["authority"] == {
        "qualification_lab_only": True,
        "installs_runtime": False,
        "changes_runtime_configuration": False,
        "selects_hermes_action": False,
        "dispatches_task": False,
        "authorizes_effect": False,
        "admits_evidence": False,
        "owns_persistence": False,
    }
    assert "CLM rank != Hermes decision" in report["non_equivalences"]
    assert "CLM rank != Pantheon authorization" in report["non_equivalences"]


def test_order_sensitive_ranker_is_exposed_not_hidden(monkeypatch, tmp_path: Path) -> None:
    cases = _write_one_case(tmp_path)
    runtime = _write_runtime_metadata(tmp_path)

    monkeypatch.setattr(
        MODULE,
        "observe_server",
        lambda *args, **kwargs: {
            "health": {"ok": True, "embedder": True},
            "models": ["clm-latest"],
            "health_elapsed_ms": 1.0,
            "models_elapsed_ms": 1.0,
        },
    )

    def order_sensitive(base_url, path, *, method="GET", body=None, api_key=None, timeout=120.0):
        answers = body["answers"]
        ranked = [
            {"rank": index + 1, "candidate": candidate, "prob": 1.0 / (index + 2)}
            for index, candidate in enumerate(answers)
        ]
        return {"model": "clm-latest", "ranked": ranked}, {}, 2.0

    monkeypatch.setattr(MODULE, "_request_json", order_sensitive)

    report = run_shadow(
        cases_path=cases,
        runtime_metadata_path=runtime,
        pin_registry_path=PIN_REGISTRY,
        base_url="http://127.0.0.1:8700",
        model="clm-latest",
        api_key=None,
        timeout=10.0,
        max_orderings=3,
        allow_remote=False,
    )

    assert report["summary"]["top_candidate_order_stable_rate"] == 0.0
    assert report["cases"][0]["top_candidate_order_stable"] is False


def test_remote_endpoint_fails_closed_without_explicit_override(tmp_path: Path) -> None:
    with pytest.raises(CLMShadowQualificationError, match="remote CLM endpoint refused"):
        run_shadow(
            cases_path=_write_one_case(tmp_path),
            runtime_metadata_path=_write_runtime_metadata(tmp_path),
            pin_registry_path=PIN_REGISTRY,
            base_url="https://example.com",
            model="clm-latest",
            api_key=None,
            timeout=1.0,
            max_orderings=1,
            allow_remote=False,
        )


def test_lab_has_no_product_import_or_effect_path() -> None:
    source = LAB.read_text(encoding="utf-8")
    forbidden = (
        "mvp_vertical",
        "psycopg",
        "subprocess",
        "send_email",
        "execute_effect",
        "write_command",
    )
    for token in forbidden:
        assert token not in source

    assert MODULE.AUTHORITY["selects_hermes_action"] is False
    assert MODULE.AUTHORITY["dispatches_task"] is False
    assert MODULE.AUTHORITY["authorizes_effect"] is False
    assert MODULE.AUTHORITY["admits_evidence"] is False
