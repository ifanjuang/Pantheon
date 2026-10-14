from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


class FixtureEvaluationError(ValueError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FixtureEvaluationError(f"cannot load JSON: {path}") from exc
    if not isinstance(value, dict):
        raise FixtureEvaluationError(f"expected JSON object: {path}")
    return value


def _answer_json(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8").strip()
    try:
        value = json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        raise FixtureEvaluationError("answer must be strict JSON for this fixture") from exc
    if not isinstance(value, dict):
        raise FixtureEvaluationError("answer must be a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evaluate_keyed_answer(
    answer: dict[str, Any], expected: dict[str, Any], *, prefix: str
) -> tuple[int, int, list[str], dict[str, bool]]:
    check_ids = [f"{prefix}:{key}" for key in expected]
    passed = sum(answer.get(key) == value for key, value in expected.items())
    checks = {
        "strict_expected_values": passed == len(expected),
        "answer_has_only_expected_keys": set(answer) == set(expected),
    }
    return len(expected), passed, check_ids, checks


def _evaluate_c1(workspace: Path, answer_path: Path) -> dict[str, Any]:
    manifest = _load_json(workspace / "manifest.json")
    answer = _answer_json(answer_path)
    expected = manifest["expected"]
    checks, passes, ids, quality = _evaluate_keyed_answer(answer, expected, prefix="C1")
    return {
        "source_recall_checks": checks,
        "source_recall_passes": passes,
        "source_recall_check_ids": ids,
        "required_quality_checks": {
            **quality,
            "contradiction_preserved": answer.get("contradiction_a") == "DELAY_DAYS:14"
            and answer.get("contradiction_b") == "DELAY_DAYS:21",
        },
        "notes": ["Synthetic large-text proxy; not proof of Pantheon scoped-context admission."],
    }


def _evaluate_c2(workspace: Path, answer_path: Path) -> dict[str, Any]:
    manifest = _load_json(workspace / "manifest.json")
    answer = _answer_json(answer_path)
    expected = manifest["expected"]
    checks, passes, ids, quality = _evaluate_keyed_answer(answer, expected, prefix="C2")
    return {
        "source_recall_checks": checks,
        "source_recall_passes": passes,
        "source_recall_check_ids": ids,
        "required_quality_checks": quality,
        "notes": ["Synthetic deterministic 250k-character tool-output fixture."],
    }


def _evaluate_c3(workspace: Path, _answer_path: Path) -> dict[str, Any]:
    manifest = _load_json(workspace / "manifest.json")
    expected_hashes = manifest.get("immutable_sha256") or {}
    immutable_ok = all(
        (workspace / rel).is_file() and _sha256(workspace / rel) == digest
        for rel, digest in expected_hashes.items()
    )
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
        check=False,
    )
    return {
        "source_recall_checks": 0,
        "source_recall_passes": 0,
        "source_recall_check_ids": [],
        "required_quality_checks": {
            "tests_pass": completed.returncode == 0,
            "immutable_fixture_files_unchanged": immutable_ok,
        },
        "notes": [
            f"Post-run pytest exit code: {completed.returncode}",
            "Source recall is not applicable to C3; zero checks are recorded explicitly.",
            "Fixture integrity checks cover test_task.py and prompt.txt; task.py is intentionally mutable.",
        ],
    }


def _evaluate_c4(workspace: Path, answer_path: Path) -> dict[str, Any]:
    manifest = _load_json(workspace / "manifest.json")
    answer = _answer_json(answer_path)
    expected = manifest["expected"]
    contradiction = answer.get("contradiction_sources")
    locators = answer.get("source_locators")
    contradiction_ok = isinstance(contradiction, list) and set(contradiction) == set(expected["contradiction_sources"])
    locators_ok = isinstance(locators, list) and set(expected["required_source_locators"]).issubset(set(locators))
    missing = answer.get("missing_information")
    missing_ok = isinstance(missing, str) and "extension" in missing.lower() and "approv" in missing.lower()

    checks = [
        ("penalty", answer.get("penalty_eur") == expected["penalty_eur"]),
        ("delay_days", answer.get("delay_days") == expected["delay_days"]),
        ("contradiction", contradiction_ok),
        ("obsolete_source", answer.get("obsolete_source_id") == expected["obsolete_source_id"]),
        ("source_locators", locators_ok),
        ("missing_approval", missing_ok),
    ]
    return {
        "source_recall_checks": len(checks),
        "source_recall_passes": sum(passed for _name, passed in checks),
        "source_recall_check_ids": [f"C4:{name}" for name, _passed in checks],
        "required_quality_checks": {
            "penalty_correct": checks[0][1],
            "delay_correct": checks[1][1],
            "contradiction_preserved": contradiction_ok,
            "obsolete_source_not_promoted": checks[3][1],
            "source_locators_recoverable": locators_ok,
            "missing_approval_identified": missing_ok,
        },
        "notes": ["Synthetic agency-style case; no client data or governed Evidence is used."],
    }


def evaluate(case_id: str, workspace: Path, answer_path: Path) -> dict[str, Any]:
    if case_id.startswith("C1-"):
        return _evaluate_c1(workspace, answer_path)
    if case_id.startswith("C2-"):
        return _evaluate_c2(workspace, answer_path)
    if case_id.startswith("C3-"):
        return _evaluate_c3(workspace, answer_path)
    if case_id.startswith("C4-"):
        return _evaluate_c4(workspace, answer_path)
    raise FixtureEvaluationError(f"unsupported case_id: {case_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministically evaluate one synthetic Pantheon-Next#1047 result")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--answer", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = evaluate(args.case_id, args.workspace, args.answer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
