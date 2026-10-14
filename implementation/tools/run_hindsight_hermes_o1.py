#!/usr/bin/env python3
"""Bounded Hermes assistant-personal + Hindsight configuration harness.

Originally introduced for O1, this helper configures an isolated Hermes profile
against an already-running Hindsight endpoint. It does not install Hindsight,
write Pantheon state, admit Evidence, or alter the governed profile.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

ASSISTANT_PROFILE = "assistant-personal"
GOVERNED_PROFILE = "pantheon-governed"
DEFAULT_BANK = "pantheon-o1-synthetic"
MARKER = "PANTHEON_O1_SYNTHETIC_MEMORY_MARKER"


class O1Error(RuntimeError):
    pass


def _write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_env(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{k}={v}\n" for k, v in values.items() if v), encoding="utf-8")
    path.chmod(0o600)


def configure(
    hermes_home: Path,
    *,
    hindsight_api_url: str,
    hindsight_api_key: str,
    provider_url: str,
    bank_id: str,
    recall_tags: list[str] | None = None,
    recall_tags_match: str = "all_strict",
) -> dict[str, Any]:
    hermes_home = hermes_home.resolve()
    profile_home = hermes_home / "profiles" / ASSISTANT_PROFILE
    governed_home = hermes_home / "profiles" / GOVERNED_PROFILE
    if not profile_home.is_dir() or not governed_home.is_dir():
        raise O1Error("assistant-personal and pantheon-governed profiles must exist")
    if recall_tags_match not in {"any", "all", "any_strict", "all_strict"}:
        raise O1Error(f"unsupported recall_tags_match: {recall_tags_match}")

    # Do not set platform_toolsets.cli=[] here: that would remove the provider's
    # explicit hindsight_* tools from the assistant CLI surface. The governed
    # profile is qualified separately and keeps its CLI toolset empty.
    _write_yaml(
        profile_home / "config.yaml",
        {
            "model": {
                "provider": "custom",
                "default": "o1-lab-model",
                "base_url": provider_url.rstrip("/") + "/v1",
                "api_mode": "chat_completions",
            },
            "memory": {
                "provider": "hindsight",
                "memory_enabled": False,
                "user_profile_enabled": False,
            },
        },
    )
    hindsight_config: dict[str, Any] = {
        "mode": "cloud",
        "api_url": hindsight_api_url.rstrip("/"),
        "bank_id": bank_id,
        "memory_mode": "tools",
        "auto_retain": False,
        "auto_recall": False,
        "retain_async": False,
        "recall_budget": "mid",
        # Hermes defaults Hindsight recall to observations. O1/O3 deliberately
        # disable consolidation/LLM and use extraction_mode=chunks, which produces
        # raw world facts. Include raw pathways explicitly for the real tool bridge.
        "recall_types": ["world", "experience"],
    }
    if recall_tags:
        hindsight_config["recall_tags"] = recall_tags
        hindsight_config["recall_tags_match"] = recall_tags_match
    _write_json(profile_home / "hindsight" / "config.json", hindsight_config)
    _write_env(
        profile_home / ".env",
        {
            "OPENAI_API_KEY": "local-o1-provider-key",
            "HINDSIGHT_API_URL": hindsight_api_url.rstrip("/"),
            "HINDSIGHT_API_KEY": hindsight_api_key,
            "HINDSIGHT_BANK_ID": bank_id,
            "HINDSIGHT_AUTO_RETAIN": "false",
            "HINDSIGHT_AUTO_RECALL": "false",
        },
    )

    return {
        "kind": "hindsight_hermes_o1_configuration",
        "assistant_profile": ASSISTANT_PROFILE,
        "governed_profile": GOVERNED_PROFILE,
        "bank_id": bank_id,
        "memory_provider": "hindsight",
        "memory_mode": "tools",
        "recall_budget": "mid",
        "recall_types": ["world", "experience"],
        "recall_tags": recall_tags or [],
        "recall_tags_match": recall_tags_match if recall_tags else None,
        "auto_retain": False,
        "auto_recall": False,
        "conversation_retention": "off",
        "assistant_memory_tools_expected": [
            "hindsight_retain",
            "hindsight_recall",
            "hindsight_reflect",
        ],
        "pantheon_write_path": False,
        "evidence_admission": False,
        "production_activation": False,
    }


def validate(artifacts: Path) -> dict[str, Any]:
    artifacts = artifacts.resolve()
    assistant_status = (artifacts / "assistant-memory-status.txt").read_text(encoding="utf-8")
    governed = json.loads((artifacts / "governed-memory-status.json").read_text(encoding="utf-8"))
    direct_recall = json.loads((artifacts / "direct-recall.json").read_text(encoding="utf-8"))
    hermes_output = (artifacts / "hermes-output.txt").read_text(encoding="utf-8")
    provider_state = json.loads((artifacts / "provider-state.json").read_text(encoding="utf-8"))
    rollback = json.loads((artifacts / "rollback.json").read_text(encoding="utf-8"))

    if "hindsight" not in assistant_status.lower():
        raise O1Error("assistant-personal did not report Hindsight as selected provider")
    if governed.get("status") != "qualified" or governed.get("active_axes") != []:
        raise O1Error("pantheon-governed memory posture is not still fully off")
    if MARKER not in json.dumps(direct_recall, ensure_ascii=False):
        raise O1Error("direct Hindsight recall did not return the synthetic marker")
    if provider_state.get("recall_tool_seen") is not True:
        raise O1Error("Hermes did not expose hindsight_recall to the model")
    if provider_state.get("marker_seen_in_tool_result") is not True:
        raise O1Error("Hermes tool result did not carry the real recalled marker")
    if "O1_HINDSIGHT_RECALL_COMPLETED" not in hermes_output:
        raise O1Error("Hermes did not complete a Hindsight recall tool cycle")
    if rollback.get("assistant_profile_removed") is not True:
        raise O1Error("assistant-personal sandbox profile was not removed")

    summary = {
        "kind": "hindsight_hermes_o1_acceptance",
        "status": "passed",
        "assistant_profile": ASSISTANT_PROFILE,
        "governed_profile": GOVERNED_PROFILE,
        "hindsight_bank": DEFAULT_BANK,
        "recall_budget": "mid",
        "recall_types": ["world", "experience"],
        "direct_recall_verified": True,
        "hermes_recall_tool_exposed": True,
        "hermes_recall_verified": True,
        "conversation_retention": "off",
        "governed_memory_posture": "qualified_off",
        "pantheon_state_mutated": False,
        "evidence_admitted": False,
        "production_activated": False,
        "rollback_verified": True,
    }
    _write_json(artifacts / "acceptance-summary.json", summary)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    cfg = sub.add_parser("configure")
    cfg.add_argument("--hermes-home", type=Path, required=True)
    cfg.add_argument("--hindsight-api-url", required=True)
    cfg.add_argument("--hindsight-api-key", default="")
    cfg.add_argument("--provider-url", required=True)
    cfg.add_argument("--bank-id", default=DEFAULT_BANK)
    cfg.add_argument("--recall-tag", action="append", default=[])
    cfg.add_argument("--recall-tags-match", default="all_strict")
    cfg.add_argument("--output", type=Path, required=True)
    val = sub.add_parser("validate")
    val.add_argument("--artifacts", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "configure":
        result = configure(
            args.hermes_home,
            hindsight_api_url=args.hindsight_api_url,
            hindsight_api_key=args.hindsight_api_key,
            provider_url=args.provider_url,
            bank_id=args.bank_id,
            recall_tags=args.recall_tag,
            recall_tags_match=args.recall_tags_match,
        )
        _write_json(args.output, result)
        return 0
    if args.command == "validate":
        print(json.dumps(validate(args.artifacts), indent=2, sort_keys=True))
        return 0
    raise O1Error(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
