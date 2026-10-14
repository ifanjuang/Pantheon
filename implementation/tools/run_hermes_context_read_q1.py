#!/usr/bin/env python3
"""Q1 qualification of Hermes project-context discovery and truncation.

This harness executes the exact installed Hermes ``agent.prompt_builder`` code
against synthetic workspaces. It records technical observations only; it does
not activate a runtime, authorize a task, admit Evidence, or mutate Pantheon.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


class ContextReadQ1Error(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContextReadQ1Error(message)


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _make_git_workspace(root: Path, name: str) -> tuple[Path, Path]:
    repo = root / name
    cwd = repo / "packages" / "worker"
    cwd.mkdir(parents=True)
    (repo / ".git").mkdir()
    return repo, cwd


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _context_bytes_from_prompt_size(value: dict[str, Any]) -> int:
    sections = value.get("sections")
    _require(isinstance(sections, list), "prompt-size sections missing")
    for item in sections:
        if isinstance(item, (list, tuple)) and len(item) == 3:
            label, _chars, byte_count = item
            if str(label).startswith("context ("):
                return int(byte_count)
    raise ContextReadQ1Error("prompt-size context tier missing")


def run(prompt_size_json: Path | None) -> dict[str, Any]:
    expected_commit = os.environ.get("HERMES_RELEASE_COMMIT", "").strip()
    expected_version = os.environ.get("HERMES_VERSION", "").strip()
    _require(bool(expected_commit), "HERMES_RELEASE_COMMIT is required")
    _require(bool(expected_version), "HERMES_VERSION is required")

    from agent.prompt_builder import (  # type: ignore
        CONTEXT_FILE_MAX_CHARS,
        _get_context_file_max_chars,
        build_context_files_prompt,
    )

    effective_default_cap = int(_get_context_file_max_chars(None))
    _require(
        effective_default_cap == int(CONTEXT_FILE_MAX_CHARS),
        "Q1 expected the no-context-length/no-explicit-config fallback cap",
    )

    observations: dict[str, Any] = {}

    with tempfile.TemporaryDirectory(prefix="pantheon-hermes-context-q1-") as tmp:
        root = Path(tmp)

        repo, cwd = _make_git_workspace(root, "priority")
        markers = {
            "hermes": "Q1_PRIORITY_HERMES",
            "agents": "Q1_PRIORITY_AGENTS",
            "claude": "Q1_PRIORITY_CLAUDE",
            "cursor": "Q1_PRIORITY_CURSOR",
        }
        _write(repo / "HERMES.md", markers["hermes"])
        _write(repo / "AGENTS.md", markers["agents"])
        _write(cwd / "CLAUDE.md", markers["claude"])
        _write(cwd / ".cursorrules", markers["cursor"])
        rendered = build_context_files_prompt(
            cwd=str(cwd), skip_soul=True, context_length=None
        )
        _require(markers["hermes"] in rendered, "HERMES.md was not selected")
        for key in ("agents", "claude", "cursor"):
            _require(
                markers[key] not in rendered,
                f"{key} leaked despite higher-priority HERMES.md",
            )
        observations["priority"] = {
            "selected": "HERMES.md",
            "first_found_wins": True,
            "output_digest": _sha256_text(rendered),
        }

        repo, cwd = _make_git_workspace(root, "agents-chain")
        root_marker = "Q1_AGENTS_ROOT"
        nested_marker = "Q1_AGENTS_NESTED"
        _write(repo / "AGENTS.md", root_marker)
        _write(cwd / "AGENTS.md", nested_marker)
        rendered = build_context_files_prompt(
            cwd=str(cwd), skip_soul=True, context_length=None
        )
        _require(root_marker in rendered, "root AGENTS.md missing")
        _require(nested_marker in rendered, "nested AGENTS.md missing")
        _require(
            rendered.index(root_marker) < rendered.index(nested_marker),
            "AGENTS.md chain order is not root-to-cwd",
        )
        observations["agents_chain"] = {
            "root_loaded": True,
            "nested_loaded": True,
            "order": "git_root_to_cwd",
            "output_digest": _sha256_text(rendered),
        }

        repo, cwd = _make_git_workspace(root, "claude-cwd")
        parent_marker = "Q1_CLAUDE_PARENT"
        cwd_marker = "Q1_CLAUDE_CWD"
        _write(repo / "CLAUDE.md", parent_marker)
        _write(cwd / "CLAUDE.md", cwd_marker)
        rendered = build_context_files_prompt(
            cwd=str(cwd), skip_soul=True, context_length=None
        )
        _require(cwd_marker in rendered, "cwd CLAUDE.md missing")
        _require(parent_marker not in rendered, "parent CLAUDE.md was inherited")
        observations["claude"] = {
            "cwd_loaded": True,
            "parent_loaded": False,
            "output_digest": _sha256_text(rendered),
        }

        _repo, cwd = _make_git_workspace(root, "unrecognized")
        unrecognized = {
            "README.md": "Q1_UNRECOGNIZED_README",
            "DESIGN.md": "Q1_UNRECOGNIZED_DESIGN",
            "SKILLS.md": "Q1_UNRECOGNIZED_SKILLS",
        }
        for filename, marker in unrecognized.items():
            _write(cwd / filename, marker)
        rendered = build_context_files_prompt(
            cwd=str(cwd), skip_soul=True, context_length=None
        )
        _require(
            not any(marker in rendered for marker in unrecognized.values()),
            "repository orientation file unexpectedly gained runtime context authority",
        )
        observations["unrecognized_repository_files"] = {
            "files": sorted(unrecognized),
            "loaded": False,
            "output_digest": _sha256_text(rendered),
        }

        _repo, cwd = _make_git_workspace(root, "complete")
        eof_marker = "Q1_COMPLETE_EOF"
        short_content = "Q1_COMPLETE_HEAD\n" + ("a" * 1024) + "\n" + eof_marker
        _write(cwd / "AGENTS.md", short_content)
        rendered = build_context_files_prompt(
            cwd=str(cwd), skip_soul=True, context_length=None
        )
        _require(eof_marker in rendered, "below-cap EOF sentinel missing")
        _require("[...truncated " not in rendered, "below-cap file was truncated")
        observations["below_cap"] = {
            "input_chars": len(short_content),
            "complete_read_observed": True,
            "eof_sentinel_present": True,
            "truncation_marker_present": False,
            "source_digest": _sha256_text(short_content),
            "output_digest": _sha256_text(rendered),
        }

        _repo, cwd = _make_git_workspace(root, "truncated")
        head_marker = "Q1_TRUNCATION_HEAD"
        middle_marker = "Q1_TRUNCATION_MIDDLE"
        tail_marker = "Q1_TRUNCATION_TAIL"
        total_chars = effective_default_cap + 6000
        middle_at = int(effective_default_cap * 0.8)
        prefix = head_marker + ("h" * (middle_at - len(head_marker)))
        suffix_len = total_chars - len(prefix) - len(middle_marker) - len(tail_marker)
        _require(suffix_len > 0, "invalid truncation fixture sizing")
        long_content = prefix + middle_marker + ("t" * suffix_len) + tail_marker
        _require(len(long_content) == total_chars, "truncation fixture size drift")
        _write(cwd / "AGENTS.md", long_content)
        rendered = build_context_files_prompt(
            cwd=str(cwd), skip_soul=True, context_length=None
        )
        _require(head_marker in rendered, "truncated file lost head sentinel")
        _require(tail_marker in rendered, "truncated file lost tail sentinel")
        _require(middle_marker not in rendered, "truncated file retained omitted middle")
        _require("[...truncated " in rendered, "truncation marker missing")
        observations["over_cap"] = {
            "input_chars": len(long_content),
            "effective_cap_chars": effective_default_cap,
            "complete_read_observed": False,
            "head_sentinel_present": True,
            "middle_sentinel_present": False,
            "tail_sentinel_present": True,
            "truncation_marker_present": True,
            "source_digest": _sha256_text(long_content),
            "output_digest": _sha256_text(rendered),
        }

    prompt_size_observation: dict[str, Any] | None = None
    if prompt_size_json is not None:
        value = json.loads(prompt_size_json.read_text(encoding="utf-8"))
        _require(isinstance(value, dict), "prompt-size JSON must be an object")
        context_bytes = _context_bytes_from_prompt_size(value)
        _require(context_bytes > 0, "offline prompt-size observed an empty context tier")
        system_prompt = value.get("system_prompt") or {}
        prompt_size_observation = {
            "offline_command_observed": True,
            "context_tier_bytes": context_bytes,
            "system_prompt_bytes": int(system_prompt.get("bytes") or 0),
            "network_call_required_by_command": False,
        }

    return {
        "kind": "hermes_context_read_q1_observation",
        "status": "passed",
        "hermes_version": expected_version,
        "hermes_release_commit": expected_commit,
        "upstream_owner": "agent.prompt_builder.build_context_files_prompt",
        "default_context_file_max_chars": int(CONTEXT_FILE_MAX_CHARS),
        "effective_q1_cap_chars": effective_default_cap,
        "project_context_priority": [
            ".hermes.md/HERMES.md",
            "AGENTS.override.md/AGENTS.md/agents.md",
            "CLAUDE.md/claude.md",
            ".cursorrules/.cursor/rules/*.mdc",
        ],
        "observations": observations,
        "prompt_size": prompt_size_observation,
        "interpretation": {
            "repository_orientation_surface_is_runtime_manifest": False,
            "over_cap_context_is_complete_read": False,
            "below_cap_eof_sentinel_proves_only_this_synthetic_read": True,
        },
        "authority": {
            "target_installation_observed": False,
            "production_activated": False,
            "future_tasks_authorized": False,
            "evidence_admitted": False,
            "pantheon_state_mutated": False,
            "authority_effect": "none",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prompt-size-json", type=Path)
    args = parser.parse_args()

    result = run(args.prompt_size_json)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContextReadQ1Error, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Hermes context-read Q1 refused: {exc}")
        raise SystemExit(1) from exc
