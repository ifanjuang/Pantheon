from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


LAB_DIR = Path(__file__).resolve().parents[1] / "labs" / "hermes_runtime_efficiency"
if str(LAB_DIR) not in sys.path:
    sys.path.insert(0, str(LAB_DIR))


def _load(name: str, filename: str):
    path = LAB_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


NATIVE = _load("pantheon_native_run_1047", "native_run.py")
FIXTURES = _load("pantheon_build_fixtures_1047", "build_fixtures.py")
EVALUATE = _load("pantheon_evaluate_fixture_1047", "evaluate_fixture.py")


def test_native_observation_maps_hermes_usage_and_session_metrics() -> None:
    usage = {
        "input_tokens": 12000,
        "output_tokens": 900,
        "api_calls": 5,
        "model": "qwen3.5:27b",
        "provider": "ollama",
        "completed": True,
        "failed": False,
    }
    meta = {
        "case_id": "C2-native-01",
        "variant": "native",
        "runtime_identity": "hermes-agent:v2026.9.11",
        "profile_identity": "pantheon-governed",
        "settings": {"reasoning": "default", "profile": "pantheon-governed"},
        "large_tool_threshold_chars": 100,
    }
    quality = {
        "source_recall_checks": 1,
        "source_recall_passes": 1,
        "source_recall_check_ids": ["C2:marker"],
        "required_quality_checks": {"marker_exact": True},
    }
    session = {
        "messages": [
            {
                "role": "assistant",
                "tool_calls": [
                    {"id": "1", "function": {"name": "terminal"}},
                    {"id": "2", "function": {"name": "read_file"}},
                ],
            },
            {"role": "tool", "content": "x" * 150},
            {"role": "tool", "content": "short"},
        ]
    }

    result = NATIVE.build_observation(
        usage=usage,
        meta=meta,
        quality=quality,
        session=session,
        elapsed_seconds=12.5,
    )

    assert result["model_identity"] == "ollama:qwen3.5:27b"
    assert result["llm_turns"] == 5
    assert result["tool_calls"] == 2
    assert result["large_tool_result_count"] == 1
    assert result["large_tool_result_chars"] == 150
    assert result["elapsed_seconds"] == 12.5
    assert result["result_status"] == "complete"
    assert result["settings_digest"].startswith("sha256:")


def test_session_tool_count_falls_back_to_tool_rows() -> None:
    result = NATIVE.session_metrics(
        {"messages": [{"role": "tool", "content": "a"}, {"role": "tool", "content": "b"}]},
        large_tool_threshold_chars=None,
    )
    assert result == {
        "tool_calls": 2,
        "large_tool_result_count": None,
        "large_tool_result_chars": None,
    }


def test_fixture_builder_is_deterministic_and_keeps_c1_sizes(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    FIXTURES.build_all(left)
    FIXTURES.build_all(right)

    for size in FIXTURES.C1_SIZES:
        left_doc = left / "C1-large-context" / f"document_{size}.md"
        right_doc = right / "C1-large-context" / f"document_{size}.md"
        assert len(left_doc.read_text(encoding="utf-8")) == size
        assert left_doc.read_bytes() == right_doc.read_bytes()


def _write_answer(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_c1_and_c2_exact_answers_pass(tmp_path: Path) -> None:
    FIXTURES.build_all(tmp_path)

    c1 = tmp_path / "C1-large-context"
    answer1 = tmp_path / "c1-answer.json"
    expected1 = json.loads((c1 / "manifest.json").read_text(encoding="utf-8"))["expected"]
    _write_answer(answer1, expected1)
    quality1 = EVALUATE.evaluate("C1-100000-native-01", c1, answer1)
    assert quality1["source_recall_passes"] == quality1["source_recall_checks"] == 6
    assert all(quality1["required_quality_checks"].values())

    c2 = tmp_path / "C2-large-tool-output"
    answer2 = tmp_path / "c2-answer.json"
    expected2 = json.loads((c2 / "manifest.json").read_text(encoding="utf-8"))["expected"]
    _write_answer(answer2, expected2)
    quality2 = EVALUATE.evaluate("C2-native-01", c2, answer2)
    assert quality2["source_recall_passes"] == quality2["source_recall_checks"] == 5
    assert all(quality2["required_quality_checks"].values())


def test_c3_quality_uses_tests_and_immutable_fixture_hashes(tmp_path: Path) -> None:
    FIXTURES.build_all(tmp_path)
    c3 = tmp_path / "C3-edit-validate"
    fixed_task = """def normalize_name(value: str) -> str:
    return ' '.join(value.split()).lower()


def compute_penalty(days: int) -> int:
    first = min(days, 15) * 70
    second = min(max(days - 15, 0), 15) * 84
    third = max(days - 30, 0) * 105
    return first + second + third


def classify_status(done: bool, blocked: bool) -> str:
    if blocked:
        return 'blocked'
    return 'done' if done else 'open'
"""
    (c3 / "task.py").write_text(fixed_task, encoding="utf-8")
    answer = tmp_path / "c3-answer.txt"
    answer.write_text("complete\n", encoding="utf-8")

    quality = EVALUATE.evaluate("C3-native-01", c3, answer)

    assert quality["source_recall_checks"] == 0
    assert quality["source_recall_passes"] == 0
    assert quality["source_recall_check_ids"] == []
    assert quality["required_quality_checks"] == {
        "tests_pass": True,
        "immutable_fixture_files_unchanged": True,
    }


def test_c4_professional_checks_are_deterministic(tmp_path: Path) -> None:
    FIXTURES.build_all(tmp_path)
    c4 = tmp_path / "C4-agency-source-task"
    answer = tmp_path / "c4-answer.json"
    _write_answer(
        answer,
        {
            "penalty_eur": 3885,
            "delay_days": 45,
            "contradiction_sources": ["SRC-SITE-REPORT", "SRC-INSPECTION"],
            "obsolete_source_id": "SRC-EMAIL-OLD",
            "missing_information": "No approved extension-of-time decision is present.",
            "source_locators": [
                "SRC-CCAP",
                "SRC-PLANNING",
                "SRC-SITE-REPORT",
                "SRC-INSPECTION",
                "SRC-EMAIL-OLD",
                "SRC-MISSING",
            ],
        },
    )

    quality = EVALUATE.evaluate("C4-native-01", c4, answer)

    assert quality["source_recall_passes"] == quality["source_recall_checks"] == 6
    assert all(quality["required_quality_checks"].values())
