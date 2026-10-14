from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class NativeRunError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise NativeRunError(f"cannot load JSON: {path}") from exc
    if not isinstance(value, dict):
        raise NativeRunError(f"expected JSON object: {path}")
    return value


def _load_single_session(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError as exc:
        raise NativeRunError(f"cannot load session export: {path}") from exc
    if len(lines) != 1:
        raise NativeRunError("session export must contain exactly one JSONL record")
    try:
        value = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        raise NativeRunError("session export contains invalid JSON") from exc
    if not isinstance(value, dict):
        raise NativeRunError("session export record must be a JSON object")
    return value


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise NativeRunError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_int(value: Any, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise NativeRunError(f"{field} must be a non-negative integer or null")
    return value


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _content_chars(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        return len(value)
    return len(json.dumps(value, ensure_ascii=False, sort_keys=True))


def session_metrics(
    session: dict[str, Any] | None,
    *,
    large_tool_threshold_chars: int | None,
) -> dict[str, int | None]:
    if session is None:
        return {
            "tool_calls": None,
            "large_tool_result_count": None,
            "large_tool_result_chars": None,
        }
    messages = session.get("messages")
    if not isinstance(messages, list):
        raise NativeRunError("session export messages must be a list")

    assistant_tool_calls = 0
    tool_rows = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        if message.get("role") == "assistant" and isinstance(message.get("tool_calls"), list):
            assistant_tool_calls += len(message["tool_calls"])
        if message.get("role") == "tool":
            tool_rows.append(message)

    # Older/session-specific exports can omit assistant tool_calls while keeping tool rows.
    tool_calls = assistant_tool_calls if assistant_tool_calls else len(tool_rows)
    if large_tool_threshold_chars is None:
        large_count = None
        large_chars = None
    else:
        if large_tool_threshold_chars <= 0:
            raise NativeRunError("large_tool_threshold_chars must be positive when supplied")
        sizes = [_content_chars(row.get("content")) for row in tool_rows]
        large = [size for size in sizes if size >= large_tool_threshold_chars]
        large_count = len(large)
        large_chars = sum(large)

    return {
        "tool_calls": tool_calls,
        "large_tool_result_count": large_count,
        "large_tool_result_chars": large_chars,
    }


def _elapsed_seconds(path: Path | None) -> float | None:
    if path is None:
        return None
    try:
        value = float(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError) as exc:
        raise NativeRunError(f"cannot parse elapsed seconds: {path}") from exc
    if value < 0 or value != value or value in (float("inf"), float("-inf")):
        raise NativeRunError("elapsed seconds must be finite and non-negative")
    return value


def build_observation(
    *,
    usage: dict[str, Any],
    meta: dict[str, Any],
    quality: dict[str, Any],
    session: dict[str, Any] | None = None,
    elapsed_seconds: float | None = None,
) -> dict[str, Any]:
    case_id = _require_text(meta.get("case_id"), "case_id")
    variant = _require_text(meta.get("variant"), "variant")
    runtime_identity = _require_text(meta.get("runtime_identity"), "runtime_identity")

    explicit_model = meta.get("model_identity")
    if explicit_model is None:
        model = usage.get("model")
        provider = usage.get("provider")
        if isinstance(model, str) and model.strip():
            model_identity = f"{provider}:{model}" if isinstance(provider, str) and provider.strip() else model.strip()
        else:
            model_identity = None
    else:
        model_identity = _require_text(explicit_model, "model_identity")

    profile_identity = meta.get("profile_identity")
    if profile_identity is not None:
        profile_identity = _require_text(profile_identity, "profile_identity")

    settings_digest = meta.get("settings_digest")
    settings = meta.get("settings")
    if settings_digest is not None:
        settings_digest = _require_text(settings_digest, "settings_digest")
    elif settings is not None:
        if not isinstance(settings, dict):
            raise NativeRunError("settings must be an object when used to derive settings_digest")
        settings_digest = canonical_digest(settings)

    threshold = meta.get("large_tool_threshold_chars")
    threshold = _optional_int(threshold, "large_tool_threshold_chars")
    metrics = session_metrics(session, large_tool_threshold_chars=threshold)

    failed = bool(usage.get("failed"))
    completed = usage.get("completed") is True
    if failed:
        result_status = "failed"
    elif completed:
        result_status = "complete"
    else:
        result_status = "unknown"

    source_checks = quality.get("source_recall_checks")
    source_passes = quality.get("source_recall_passes")
    source_ids = quality.get("source_recall_check_ids")
    required_quality = quality.get("required_quality_checks") or {}
    if not isinstance(required_quality, dict):
        raise NativeRunError("required_quality_checks must be an object")

    notes = []
    for source in (meta.get("notes"), quality.get("notes")):
        if source is None:
            continue
        if not isinstance(source, list) or not all(isinstance(item, str) and item.strip() for item in source):
            raise NativeRunError("notes must be lists of non-empty strings")
        notes.extend(item.strip() for item in source)

    observation = {
        "case_id": case_id,
        "variant": variant,
        "runtime_identity": runtime_identity,
        "model_identity": model_identity,
        "profile_identity": profile_identity,
        "settings_digest": settings_digest,
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "llm_turns": usage.get("api_calls"),
        "tool_calls": metrics["tool_calls"],
        "elapsed_seconds": elapsed_seconds,
        "max_context_tokens": meta.get("max_context_tokens"),
        "repeated_context_tokens": meta.get("repeated_context_tokens"),
        "large_tool_result_count": metrics["large_tool_result_count"],
        "large_tool_result_chars": metrics["large_tool_result_chars"],
        "source_recall_checks": source_checks,
        "source_recall_passes": source_passes,
        "source_recall_check_ids": source_ids,
        "required_quality_checks": required_quality,
        "result_status": result_status,
        "retrieved_refs": quality.get("retrieved_refs"),
        "admitted_refs": quality.get("admitted_refs"),
        "used_refs": quality.get("used_refs"),
        "notes": notes,
    }

    # Import the existing owner only as a validator, never as execution/runtime wiring.
    from compare import RunObservation

    return RunObservation.from_mapping(observation).as_jsonable()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build one Pantheon-Next#1047 observation from native Hermes run artifacts")
    parser.add_argument("--usage", type=Path, required=True)
    parser.add_argument("--meta", type=Path, required=True)
    parser.add_argument("--quality", type=Path, required=True)
    parser.add_argument("--session", type=Path)
    parser.add_argument("--elapsed-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    observation = build_observation(
        usage=_load_json(args.usage),
        meta=_load_json(args.meta),
        quality=_load_json(args.quality),
        session=_load_single_session(args.session),
        elapsed_seconds=_elapsed_seconds(args.elapsed_file),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(observation, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
