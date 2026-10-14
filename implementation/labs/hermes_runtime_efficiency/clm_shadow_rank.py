#!/usr/bin/env python3
"""Passive CLM shadow-ranking qualification for Pantheon issue Pantheon-Next#1047.

This lab calls a local CLM /v1/rank endpoint and records what CLM ranked.
It never selects or executes a Hermes action and it creates no Pantheon authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_ID = "pantheon.clm_shadow_rank_cases"
REPORT_SCHEMA_ID = "pantheon.clm_shadow_rank_report"
REPORT_REVISION = 1
DEFAULT_PIN_REGISTRY = Path(__file__).resolve().parents[2] / "qualification" / "external-pins.json"

AUTHORITY = {
    "qualification_lab_only": True,
    "installs_runtime": False,
    "changes_runtime_configuration": False,
    "selects_hermes_action": False,
    "dispatches_task": False,
    "authorizes_effect": False,
    "admits_evidence": False,
    "owns_persistence": False,
}

QUANTIZED_RUNTIME_FIELDS = (
    "encoder_backend",
    "encoder_backend_version",
    "encoder_backend_ref",
    "encoder_artifact_repository",
    "encoder_artifact_revision",
    "encoder_artifact_file",
    "encoder_artifact_sha256",
    "encoder_quantization",
    "encoder_pooling",
)

REQUIRED_RUNTIME_FIELDS = (
    "clm_git_ref",
    "clm_package_version",
    "encoder_model",
    "encoder_revision",
    "head_sha256",
    "vllm_version",
    "clm_head_device_name",
    "encoder_device_name",
    "encoder_placement",
    "encoder_transport",
    "encoder_endpoint",
    "encoder_node_label",
)


class CLMShadowQualificationError(ValueError):
    pass


@dataclass(frozen=True)
class ShadowCase:
    case_id: str
    category: str
    context: str
    question: str
    candidates: tuple[str, ...]
    expected_candidates: tuple[str, ...]

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "ShadowCase":
        required = ("case_id", "category", "context", "question", "candidates", "expected_candidates")
        missing = [key for key in required if key not in raw]
        if missing:
            raise CLMShadowQualificationError(f"case missing fields: {', '.join(missing)}")
        candidates = raw["candidates"]
        expected = raw["expected_candidates"]
        if not isinstance(candidates, list) or len(candidates) < 2:
            raise CLMShadowQualificationError("candidates must be a list of at least two strings")
        if not all(isinstance(item, str) and item.strip() for item in candidates):
            raise CLMShadowQualificationError("candidates must be non-empty strings")
        if len(set(candidates)) != len(candidates):
            raise CLMShadowQualificationError("candidates must be unique")
        if not isinstance(expected, list) or not expected:
            raise CLMShadowQualificationError("expected_candidates must be a non-empty list")
        if not set(expected).issubset(candidates):
            raise CLMShadowQualificationError("expected_candidates must be drawn from candidates")
        for key in ("case_id", "category", "context", "question"):
            if not isinstance(raw[key], str) or not raw[key].strip():
                raise CLMShadowQualificationError(f"{key} must be a non-empty string")
        return cls(
            case_id=raw["case_id"],
            category=raw["category"],
            context=raw["context"],
            question=raw["question"],
            candidates=tuple(candidates),
            expected_candidates=tuple(expected),
        )


def load_cases(path: Path) -> tuple[dict[str, Any], list[ShadowCase]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CLMShadowQualificationError(f"cannot read case corpus: {exc}") from exc
    if raw.get("schema_id") != SCHEMA_ID or raw.get("revision") != 1:
        raise CLMShadowQualificationError("unsupported shadow case corpus schema/revision")
    cases_raw = raw.get("cases")
    if not isinstance(cases_raw, list) or not cases_raw:
        raise CLMShadowQualificationError("case corpus must contain a non-empty cases list")
    cases = [ShadowCase.from_mapping(item) for item in cases_raw]
    ids = [case.case_id for case in cases]
    if len(set(ids)) != len(ids):
        raise CLMShadowQualificationError("case_id values must be unique")
    return raw, cases


def load_runtime_metadata(path: Path) -> dict[str, str]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CLMShadowQualificationError(f"cannot read runtime metadata: {exc}") from exc
    if not isinstance(raw, dict):
        raise CLMShadowQualificationError("runtime metadata must be a JSON object")
    missing = [key for key in REQUIRED_RUNTIME_FIELDS if not isinstance(raw.get(key), str) or not raw[key].strip()]
    if missing:
        raise CLMShadowQualificationError(f"runtime metadata missing exact fields: {', '.join(missing)}")
    if len(raw["clm_git_ref"]) != 40 or any(c not in "0123456789abcdef" for c in raw["clm_git_ref"].lower()):
        raise CLMShadowQualificationError("clm_git_ref must be an exact 40-character git SHA")
    if len(raw["head_sha256"]) != 64 or any(c not in "0123456789abcdef" for c in raw["head_sha256"].lower()):
        raise CLMShadowQualificationError("head_sha256 must be an exact SHA-256 digest")

    quantized_present = [key for key in QUANTIZED_RUNTIME_FIELDS if key in raw]
    if quantized_present:
        missing_quantized = [
            key
            for key in QUANTIZED_RUNTIME_FIELDS
            if not isinstance(raw.get(key), str) or not raw[key].strip()
        ]
        if missing_quantized:
            raise CLMShadowQualificationError(
                "quantized runtime metadata missing exact fields: "
                + ", ".join(missing_quantized)
            )
        if raw["encoder_backend"] != "llama.cpp":
            raise CLMShadowQualificationError(
                "quantized encoder backend must be llama.cpp"
            )
        if raw["encoder_pooling"] != "last":
            raise CLMShadowQualificationError(
                "quantized encoder pooling must be last"
            )
        if raw["encoder_quantization"] not in {"Q8_0", "Q4_K_M"}:
            raise CLMShadowQualificationError(
                "quantized encoder must be one of: Q8_0, Q4_K_M"
            )
        backend_ref = raw["encoder_backend_ref"].lower()
        if len(backend_ref) != 40 or any(c not in "0123456789abcdef" for c in backend_ref):
            raise CLMShadowQualificationError(
                "encoder_backend_ref must be an exact 40-character git SHA"
            )
        artifact_revision = raw["encoder_artifact_revision"].lower()
        if len(artifact_revision) != 40 or any(c not in "0123456789abcdef" for c in artifact_revision):
            raise CLMShadowQualificationError(
                "encoder_artifact_revision must be an exact 40-character revision"
            )
        artifact_sha = raw["encoder_artifact_sha256"].lower()
        if len(artifact_sha) != 64 or any(c not in "0123456789abcdef" for c in artifact_sha):
            raise CLMShadowQualificationError(
                "encoder_artifact_sha256 must be an exact SHA-256 digest"
            )
    return {key: str(value) for key, value in raw.items()}



def validate_runtime_topology(runtime_metadata: dict[str, str]) -> None:
    placement = runtime_metadata["encoder_placement"]
    transport = runtime_metadata["encoder_transport"]
    endpoint = runtime_metadata["encoder_endpoint"]

    if placement not in {"local", "remote"}:
        raise CLMShadowQualificationError(
            "encoder_placement must be one of: local, remote"
        )
    expected_transport = {
        "local": "loopback_direct",
        "remote": "ssh_local_forward",
    }[placement]
    if transport != expected_transport:
        raise CLMShadowQualificationError(
            f"encoder_transport must be {expected_transport!r} for {placement!r} placement"
        )

    parsed = urllib.parse.urlparse(endpoint)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or parsed.path != "/v1/embeddings"
    ):
        raise CLMShadowQualificationError(
            "encoder_endpoint must be a loopback http /v1/embeddings endpoint"
        )


def load_qualification_pin(path: Path) -> dict[str, str]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CLMShadowQualificationError(f"cannot read qualification pin registry: {exc}") from exc
    if raw.get("schema_id") != "pantheon.external_qualification_pins":
        raise CLMShadowQualificationError("unexpected external qualification pin schema")
    pin = (raw.get("pins") or {}).get("contrastive-lm")
    if not isinstance(pin, dict):
        raise CLMShadowQualificationError("contrastive-lm qualification pin is missing")
    required = (
        "repository",
        "version",
        "ref",
        "encoder_model",
        "encoder_revision",
        "head_repository",
        "head_revision",
        "head_file",
        "head_sha256",
        "vllm_version",
        "api_surface",
        "experimental_quantized_encoder_repository",
        "experimental_quantized_encoder_revision",
        "experimental_q8_file",
        "experimental_q8_sha256",
        "experimental_q4_file",
        "experimental_q4_sha256",
        "experimental_encoder_backend_repository",
        "experimental_encoder_backend_version",
        "experimental_encoder_backend_ref",
    )
    missing = [
        key
        for key in required
        if not isinstance(pin.get(key), str) or not pin[key].strip()
    ]
    if missing:
        raise CLMShadowQualificationError(
            f"contrastive-lm qualification pin missing fields: {', '.join(missing)}"
        )
    if pin["repository"] != "Contrastive-LM/CLM":
        raise CLMShadowQualificationError(
            "contrastive-lm qualification pin repository is unexpected"
        )
    if pin["api_surface"] != "/v1/rank":
        raise CLMShadowQualificationError(
            "contrastive-lm qualification pin must select /v1/rank"
        )
    for field in (
        "ref",
        "encoder_revision",
        "head_revision",
        "experimental_quantized_encoder_revision",
        "experimental_encoder_backend_ref",
    ):
        value = pin[field]
        if len(value) != 40 or any(
            char not in "0123456789abcdef" for char in value.lower()
        ):
            raise CLMShadowQualificationError(
                f"contrastive-lm pin {field} must be an exact 40-character git SHA"
            )
    for field in ("head_sha256", "experimental_q8_sha256", "experimental_q4_sha256"):
        digest = pin[field]
        if len(digest) != 64 or any(
            char not in "0123456789abcdef" for char in digest.lower()
        ):
            raise CLMShadowQualificationError(
                f"contrastive-lm pin {field} must be an exact SHA-256 digest"
            )
    return {
        key: str(value)
        for key, value in pin.items()
        if isinstance(value, (str, int, float, bool))
    }

def validate_runtime_against_pin(runtime_metadata: dict[str, str], pin: dict[str, str]) -> None:
    mismatches: list[str] = []
    if runtime_metadata["clm_git_ref"] != pin["ref"]:
        mismatches.append("clm_git_ref")
    if runtime_metadata["clm_package_version"] != pin["version"]:
        mismatches.append("clm_package_version")
    if runtime_metadata["encoder_model"] != pin["encoder_model"]:
        mismatches.append("encoder_model")
    if runtime_metadata["encoder_revision"] != pin["encoder_revision"]:
        mismatches.append("encoder_revision")
    if runtime_metadata["head_sha256"] != pin["head_sha256"]:
        mismatches.append("head_sha256")
    if runtime_metadata["vllm_version"] != pin["vllm_version"]:
        mismatches.append("vllm_version")

    if any(key in runtime_metadata for key in QUANTIZED_RUNTIME_FIELDS):
        if runtime_metadata["encoder_placement"] != "local":
            mismatches.append("encoder_placement")
        if runtime_metadata["encoder_transport"] != "loopback_direct":
            mismatches.append("encoder_transport")
        if runtime_metadata["encoder_backend"] != "llama.cpp":
            mismatches.append("encoder_backend")
        if runtime_metadata["encoder_backend_version"] != pin["experimental_encoder_backend_version"]:
            mismatches.append("encoder_backend_version")
        if runtime_metadata["encoder_backend_ref"] != pin["experimental_encoder_backend_ref"]:
            mismatches.append("encoder_backend_ref")
        if runtime_metadata["encoder_artifact_repository"] != pin["experimental_quantized_encoder_repository"]:
            mismatches.append("encoder_artifact_repository")
        if runtime_metadata.get("encoder_artifact_revision") != pin["experimental_quantized_encoder_revision"]:
            mismatches.append("encoder_artifact_revision")
        quantization = runtime_metadata["encoder_quantization"]
        if quantization == "Q8_0":
            expected_file = pin["experimental_q8_file"]
            expected_sha = pin["experimental_q8_sha256"]
        elif quantization == "Q4_K_M":
            expected_file = pin["experimental_q4_file"]
            expected_sha = pin["experimental_q4_sha256"]
        else:
            expected_file = ""
            expected_sha = ""
            mismatches.append("encoder_quantization")
        if runtime_metadata["encoder_artifact_file"] != expected_file:
            mismatches.append("encoder_artifact_file")
        if runtime_metadata["encoder_artifact_sha256"] != expected_sha:
            mismatches.append("encoder_artifact_sha256")
        if runtime_metadata["encoder_pooling"] != "last":
            mismatches.append("encoder_pooling")
    if mismatches:
        raise CLMShadowQualificationError(
            "runtime metadata does not match canonical contrastive-lm qualification pin: "
            + ", ".join(mismatches)
        )


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corpus_sha256(path: Path) -> str:
    return file_sha256(path)


def is_loopback_base_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme in {"http", "https"} and parsed.hostname in {"127.0.0.1", "localhost", "::1"}


def build_orderings(candidates: tuple[str, ...], limit: int) -> list[list[str]]:
    if limit < 1:
        raise CLMShadowQualificationError("max_orderings must be >= 1")
    raw: list[list[str]] = [list(candidates), list(reversed(candidates))]
    for offset in range(1, len(candidates)):
        raw.append(list(candidates[offset:] + candidates[:offset]))
    out: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for order in raw:
        key = tuple(order)
        if key not in seen:
            seen.add(key)
            out.append(order)
        if len(out) >= limit:
            break
    return out


def _request_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    api_key: str | None = None,
    timeout: float = 120.0,
) -> tuple[dict[str, Any], dict[str, str], float]:
    url = base_url.rstrip("/") + path
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            response_headers = {k.lower(): v for k, v in response.headers.items()}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        raise CLMShadowQualificationError(f"CLM request failed for {path}: {exc}") from exc
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    if not isinstance(payload, dict):
        raise CLMShadowQualificationError(f"CLM {path} response must be a JSON object")
    return payload, response_headers, elapsed_ms


def observe_server(base_url: str, model: str, api_key: str | None, timeout: float) -> dict[str, Any]:
    health, _, health_elapsed = _request_json(base_url, "/health", api_key=api_key, timeout=timeout)
    if health.get("ok") is not True or health.get("embedder") is not True:
        raise CLMShadowQualificationError("CLM health must report ok=true and embedder=true")
    if health.get("mock") is True:
        raise CLMShadowQualificationError("mock CLM server is not admissible for shadow qualification")
    models, _, models_elapsed = _request_json(base_url, "/v1/models", api_key=api_key, timeout=timeout)
    names = [item.get("name") for item in models.get("models", []) if isinstance(item, dict)]
    if model not in names:
        raise CLMShadowQualificationError(f"requested model {model!r} not exposed by CLM")
    return {
        "health": health,
        "models": names,
        "health_elapsed_ms": round(health_elapsed, 3),
        "models_elapsed_ms": round(models_elapsed, 3),
    }


def _parse_ranked(payload: dict[str, Any], candidates: list[str]) -> list[dict[str, Any]]:
    ranked = payload.get("ranked")
    if not isinstance(ranked, list) or len(ranked) != len(candidates):
        raise CLMShadowQualificationError("rank response must contain one ranked row per candidate")
    names: list[str] = []
    parsed: list[dict[str, Any]] = []
    for expected_rank, row in enumerate(ranked, start=1):
        if not isinstance(row, dict):
            raise CLMShadowQualificationError("ranked rows must be objects")
        candidate = row.get("candidate")
        prob = row.get("prob")
        rank = row.get("rank")
        if candidate not in candidates or rank != expected_rank:
            raise CLMShadowQualificationError("ranked response has invalid candidate/rank")
        if not isinstance(prob, (int, float)) or isinstance(prob, bool) or not math.isfinite(float(prob)):
            raise CLMShadowQualificationError("ranked probability must be finite")
        names.append(candidate)
        parsed.append({"rank": rank, "candidate": candidate, "prob": float(prob)})
    if set(names) != set(candidates) or len(set(names)) != len(candidates):
        raise CLMShadowQualificationError("ranked response must contain each candidate exactly once")
    return parsed


def run_shadow(
    *,
    cases_path: Path,
    runtime_metadata_path: Path,
    pin_registry_path: Path,
    base_url: str,
    model: str,
    api_key: str | None,
    timeout: float,
    max_orderings: int,
    allow_remote: bool,
) -> dict[str, Any]:
    if not allow_remote and not is_loopback_base_url(base_url):
        raise CLMShadowQualificationError("remote CLM endpoint refused; use loopback or explicitly pass --allow-remote")
    corpus_meta, cases = load_cases(cases_path)
    runtime_metadata = load_runtime_metadata(runtime_metadata_path)
    validate_runtime_topology(runtime_metadata)
    qualification_pin = load_qualification_pin(pin_registry_path)
    validate_runtime_against_pin(runtime_metadata, qualification_pin)
    server = observe_server(base_url, model, api_key, timeout)

    observations: list[dict[str, Any]] = []
    for case in cases:
        runs: list[dict[str, Any]] = []
        for ordering in build_orderings(case.candidates, max_orderings):
            payload, headers, transport_ms = _request_json(
                base_url,
                qualification_pin["api_surface"],
                method="POST",
                body={
                    "context": case.context,
                    "question": case.question,
                    "answers": ordering,
                    "model": model,
                    "temperature": 1.0,
                },
                api_key=api_key,
                timeout=timeout,
            )
            ranked = _parse_ranked(payload, ordering)
            latency_header = headers.get("x-clm-latency-ms")
            clm_latency_ms = None
            if latency_header is not None:
                try:
                    clm_latency_ms = float(latency_header)
                except ValueError:
                    raise CLMShadowQualificationError("X-CLM-Latency-Ms must be numeric") from None
            top = ranked[0]["candidate"]
            runs.append(
                {
                    "input_order": ordering,
                    "top_candidate": top,
                    "expected_top1_match": top in case.expected_candidates,
                    "ranked": ranked,
                    "clm_latency_ms": clm_latency_ms,
                    "transport_elapsed_ms": round(transport_ms, 3),
                }
            )
        tops = [run["top_candidate"] for run in runs]
        observations.append(
            {
                "case_id": case.case_id,
                "category": case.category,
                "expected_candidates": list(case.expected_candidates),
                "orderings_observed": len(runs),
                "top_candidate_order_stable": len(set(tops)) == 1,
                "expected_top1_all_orderings": all(run["expected_top1_match"] for run in runs),
                "runs": runs,
            }
        )

    total = len(observations)
    expected_all = sum(1 for item in observations if item["expected_top1_all_orderings"])
    stable = sum(1 for item in observations if item["top_candidate_order_stable"])
    return {
        "schema_id": REPORT_SCHEMA_ID,
        "revision": REPORT_REVISION,
        "status": "shadow_observation_only",
        "corpus": {
            "schema_id": corpus_meta["schema_id"],
            "revision": corpus_meta["revision"],
            "sha256": corpus_sha256(cases_path),
            "case_count": total,
        },
        "runtime_metadata": runtime_metadata,
        "qualification_pin": {
            "repository": qualification_pin["repository"],
            "version": qualification_pin["version"],
            "ref": qualification_pin["ref"],
            "encoder_model": qualification_pin["encoder_model"],
            "encoder_revision": qualification_pin["encoder_revision"],
            "head_repository": qualification_pin["head_repository"],
            "head_revision": qualification_pin["head_revision"],
            "head_file": qualification_pin["head_file"],
            "head_sha256": qualification_pin["head_sha256"],
            "vllm_version": qualification_pin["vllm_version"],
            "api_surface": qualification_pin["api_surface"],
            "experimental_quantized_encoder_repository": qualification_pin["experimental_quantized_encoder_repository"],
            "experimental_quantized_encoder_revision": qualification_pin["experimental_quantized_encoder_revision"],
            "experimental_q8_file": qualification_pin["experimental_q8_file"],
            "experimental_q8_sha256": qualification_pin["experimental_q8_sha256"],
            "experimental_q4_file": qualification_pin["experimental_q4_file"],
            "experimental_q4_sha256": qualification_pin["experimental_q4_sha256"],
            "experimental_encoder_backend_repository": qualification_pin["experimental_encoder_backend_repository"],
            "experimental_encoder_backend_version": qualification_pin["experimental_encoder_backend_version"],
            "experimental_encoder_backend_ref": qualification_pin["experimental_encoder_backend_ref"],
            "registry_sha256": file_sha256(pin_registry_path),
        },
        "server_observation": server,
        "model": model,
        "summary": {
            "case_count": total,
            "expected_top1_all_orderings_count": expected_all,
            "expected_top1_all_orderings_rate": expected_all / total,
            "top_candidate_order_stable_count": stable,
            "top_candidate_order_stable_rate": stable / total,
        },
        "cases": observations,
        "authority": dict(AUTHORITY),
        "non_equivalences": [
            "CLM rank != Hermes decision",
            "CLM rank != Pantheon authorization",
            "expected fixture match != professional truth",
            "shadow observation != Evidence",
            "runtime success != model qualification",
            "model qualification != activation",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", type=Path)
    parser.add_argument("--runtime-metadata", required=True, type=Path)
    parser.add_argument("--pin-registry", type=Path, default=DEFAULT_PIN_REGISTRY)
    parser.add_argument("--base-url", default=os.environ.get("CLM_BASE_URL", "http://127.0.0.1:8700"))
    parser.add_argument("--model", default="clm-latest")
    parser.add_argument("--api-key-env", default="CLM_API_KEY")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--max-orderings", type=int, default=4)
    parser.add_argument("--allow-remote", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env) if args.api_key_env else None
    try:
        report = run_shadow(
            cases_path=args.cases,
            runtime_metadata_path=args.runtime_metadata,
            pin_registry_path=args.pin_registry,
            base_url=args.base_url,
            model=args.model,
            api_key=api_key,
            timeout=args.timeout,
            max_orderings=args.max_orderings,
            allow_remote=args.allow_remote,
        )
    except CLMShadowQualificationError as exc:
        parser.error(str(exc))
    encoded = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
