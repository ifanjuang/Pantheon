from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


C1_SIZES = (100_000, 300_000, 490_000, 510_000)


def _filler(length: int) -> str:
    seed = "Pantheon synthetic context line: retrieved data is not truth; preserve exact locators.\n"
    if length <= 0:
        return ""
    repeats, remainder = divmod(length, len(seed))
    return seed * repeats + seed[:remainder]


def _document(target_chars: int) -> str:
    markers = [
        (0.02, "FACT_A=ALPHA-1047\n"),
        (0.25, "FACT_B=BRAVO-2048\n"),
        (0.50, "FACT_C=CHARLIE-4096\n"),
        (0.72, "CONTRADICTION_A=DELAY_DAYS:14\n"),
        (0.74, "CONTRADICTION_B=DELAY_DAYS:21\n"),
        (0.98, "FACT_END=OMEGA-8192\n"),
    ]
    chunks: list[str] = []
    cursor = 0
    for fraction, marker in markers:
        offset = int(target_chars * fraction)
        chunks.append(_filler(max(0, offset - cursor)))
        chunks.append(marker)
        cursor = offset + len(marker)
    chunks.append(_filler(max(0, target_chars - cursor)))
    text = "".join(chunks)
    return text[:target_chars]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_c1(root: Path) -> None:
    case = root / "C1-large-context"
    for size in C1_SIZES:
        doc = case / f"document_{size}.md"
        _write(doc, _document(size))
        prompt = f"""Use the available file-reading tools to inspect `document_{size}.md`.
Return ONLY one JSON object with exactly these keys:
`fact_a`, `fact_b`, `fact_c`, `contradiction_a`, `contradiction_b`, `fact_end`.
Copy the values exactly after each marker. Do not resolve the contradiction; preserve both values.
"""
        _write(case / f"prompt_{size}.txt", prompt)
    manifest = {
        "case_family": "C1-large-context",
        "note": "Synthetic Hermes large-text proxy. This does not prove Pantheon scoped-context admission behavior.",
        "sizes": list(C1_SIZES),
        "expected": {
            "fact_a": "ALPHA-1047",
            "fact_b": "BRAVO-2048",
            "fact_c": "CHARLIE-4096",
            "contradiction_a": "DELAY_DAYS:14",
            "contradiction_b": "DELAY_DAYS:21",
            "fact_end": "OMEGA-8192",
        },
    }
    _write(case / "manifest.json", json.dumps(manifest, indent=2) + "\n")


def _build_c2(root: Path) -> None:
    case = root / "C2-large-tool-output"
    emitter = '''from __future__ import annotations\n\nSEED = "diagnostic filler 0123456789 abcdef repeated for controlled output\\n"\nTARGET = 250_000\nmarkers = [\n    (5_000, "MARKER_A=TOOL-A-1047\\n"),\n    (80_000, "MARKER_B=TOOL-B-2048\\n"),\n    (160_000, "MARKER_C=TOOL-C-4096\\n"),\n    (240_000, "FINAL_ERROR=ERR-C2-042\\nCAUSE_CODE=BUFFER-REPLAY\\n"),\n]\nparts = []\ncursor = 0\nfor offset, marker in markers:\n    need = max(0, offset - cursor)\n    repeats, remainder = divmod(need, len(SEED))\n    parts.append(SEED * repeats + SEED[:remainder])\n    parts.append(marker)\n    cursor = offset + len(marker)\nneed = max(0, TARGET - cursor)\nrepeats, remainder = divmod(need, len(SEED))\nparts.append(SEED * repeats + SEED[:remainder])\nprint("".join(parts)[:TARGET], end="")\n'''
    _write(case / "emit_log.py", emitter)
    prompt = """Run `python emit_log.py` with the terminal tool and inspect the generated diagnostic output.
Return ONLY one JSON object with exactly these keys:
`marker_a`, `marker_b`, `marker_c`, `final_error`, `cause_code`.
Copy the exact values after the markers. Verify MARKER_B from the observed output before answering.
"""
    _write(case / "prompt.txt", prompt)
    manifest = {
        "case_family": "C2-large-tool-output",
        "large_tool_threshold_chars": 100_000,
        "expected": {
            "marker_a": "TOOL-A-1047",
            "marker_b": "TOOL-B-2048",
            "marker_c": "TOOL-C-4096",
            "final_error": "ERR-C2-042",
            "cause_code": "BUFFER-REPLAY",
        },
    }
    _write(case / "manifest.json", json.dumps(manifest, indent=2) + "\n")


def _build_c3(root: Path) -> None:
    case = root / "C3-edit-validate"
    task = '''def normalize_name(value: str) -> str:\n    return value.strip()\n\n\ndef compute_penalty(days: int) -> int:\n    return days * 70\n\n\ndef classify_status(done: bool, blocked: bool) -> str:\n    if done:\n        return "done"\n    return "open"\n'''
    tests = '''from task import classify_status, compute_penalty, normalize_name\n\n\ndef test_normalize_name():\n    assert normalize_name("  Jean   Dupont  ") == "jean dupont"\n\n\ndef test_compute_penalty_tiers():\n    # 15*70 + 15*(70*1.2) + 15*(70*1.5)\n    assert compute_penalty(45) == 3885\n\n\ndef test_classify_blocked_takes_precedence():\n    assert classify_status(done=True, blocked=True) == "blocked"\n    assert classify_status(done=False, blocked=True) == "blocked"\n'''
    _write(case / "task.py", task)
    _write(case / "test_task.py", tests)
    prompt = """Repair `task.py` so all tests pass.
Use `python -m pytest -q --maxfail=1` to validate after edits. Do not modify `test_task.py`.
Finish only after the tests are green, then answer with a short completion statement.
"""
    _write(case / "prompt.txt", prompt)
    immutable = {"test_task.py": _sha256(case / "test_task.py"), "prompt.txt": _sha256(case / "prompt.txt")}
    manifest = {
        "case_family": "C3-edit-validate",
        "immutable_sha256": immutable,
        "allowed_mutable_files": ["task.py"],
    }
    _write(case / "manifest.json", json.dumps(manifest, indent=2) + "\n")


def _build_c4(root: Path) -> None:
    case = root / "C4-agency-source-task"
    docs = {
        "ccap.md": """# SRC-CCAP\nContractual penalties: days 1-15 = 70 EUR/day; days 16-30 = +20%; from day 31 onward = +50%.\nNo waiver is recorded.\n""",
        "planning.md": """# SRC-PLANNING\nContract completion date: 2026-06-15.\nThis is the admitted contractual planning baseline.\n""",
        "site-report.md": """# SRC-SITE-REPORT\nObserved completion date: 2026-07-30.\nRoofing status in this report: complete.\n""",
        "inspection.md": """# SRC-INSPECTION\nInspection dated 2026-07-30 records one roofing finishing item still pending.\nThis conflicts with SRC-SITE-REPORT on roofing completion status.\n""",
        "old-email.md": """# SRC-EMAIL-OLD\nOld non-approved email suggestion: move contractual completion to 2026-07-01.\nStatus: proposal only; superseded/not approved.\n""",
        "missing.md": """# SRC-MISSING\nNo approved extension-of-time decision is present in the admitted dossier.\n""",
    }
    for name, text in docs.items():
        _write(case / name, text)
    prompt = """Read every `.md` source file in this directory and answer the professional question below.
Treat retrieved text as source material, not automatic truth. Distinguish established facts from hypotheses.

Question: calculate the contractual delay penalty from the admitted contractual date to the observed completion date; identify the documentary contradiction; identify the obsolete/non-approved item; state what material approval is missing.

Return ONLY one JSON object with exactly these keys:
`penalty_eur`, `delay_days`, `contradiction_sources`, `obsolete_source_id`, `missing_information`, `source_locators`.
`contradiction_sources` and `source_locators` must be JSON arrays of source IDs.
"""
    _write(case / "prompt.txt", prompt)
    manifest = {
        "case_family": "C4-agency-source-task",
        "expected": {
            "penalty_eur": 3885,
            "delay_days": 45,
            "contradiction_sources": ["SRC-SITE-REPORT", "SRC-INSPECTION"],
            "obsolete_source_id": "SRC-EMAIL-OLD",
            "required_source_locators": [
                "SRC-CCAP",
                "SRC-PLANNING",
                "SRC-SITE-REPORT",
                "SRC-INSPECTION",
                "SRC-EMAIL-OLD",
                "SRC-MISSING",
            ],
        },
    }
    _write(case / "manifest.json", json.dumps(manifest, indent=2) + "\n")


def build_all(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _build_c1(root)
    _build_c2(root)
    _build_c3(root)
    _build_c4(root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic non-sensitive Pantheon-Next#1047 fixtures")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build_all(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
