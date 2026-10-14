from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUALIFICATION = ROOT / "docs" / "governance" / "WEBCMD_BROWSER_QUALIFICATION.md"


def _text() -> str:
    return QUALIFICATION.read_text(encoding="utf-8")


def test_webcmd_remains_candidate_and_hermes_side() -> None:
    text = _text()
    assert "candidate qualification note" in text
    assert "replaceable Hermes-side browser-control implementation candidate" in text
    assert "If Hermes native browser is sufficient, keep Webcmd unselected." in text


def test_webcmd_site_memory_does_not_gain_governed_authority() -> None:
    text = _text()
    for invariant in (
        "!= Pantheon Memory",
        "!= Hindsight project/document memory",
        "!= Knowledge",
        "!= Evidence",
        "!= source authority",
        "site-memory recall != current page state",
        "runtime success != authorization",
    ):
        assert invariant in text


def test_webcmd_qualification_is_ab_against_native_browser() -> None:
    text = _text()
    assert "A — Hermes native browser capability" in text
    assert "B — Hermes + pinned Webcmd candidate" in text
    assert "first-run versus repeated-run behavior measured" in text
    assert "at least one stale-memory/failure case exercised" in text


def test_webcmd_does_not_create_parallel_runtime_or_memory_path() -> None:
    text = _text()
    for non_goal in (
        "no new Pantheon browser engine",
        "no second memory authority",
        "no automatic Webcmd -> Hindsight promotion",
        "no new MCP server solely for Webcmd",
        "no duplicate public-web evidence pipeline",
    ):
        assert non_goal in text


def test_webcmd_reuses_current_hermes_qualification_and_effect_boundaries() -> None:
    text = _text()
    for invariant in (
        "HERMES_IMPROVEMENT_PATH.md",
        "matched repeated trials",
        "equal experiment-controlled initial mutable",
        "independent cases",
        "Pantheon-owned effect boundary defined by Pantheon-Next#1109",
        "raw consequential credentials/tools are not exposed directly",
    ):
        assert invariant in text


def test_webcmd_cloud_seed_must_be_proven_disabled_for_local_arm() -> None:
    text = _text()
    assert "first access may use a Webcmd Cloud seed" in text
    assert "must prove that external seed lookup is disabled" in text
