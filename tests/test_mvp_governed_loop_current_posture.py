from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "docs/governance/MVP_GOVERNED_TASK_LOOP.md"


def test_mvp_loop_declares_current_partial_posture_without_adoption() -> None:
    text = LOOP.read_text(encoding="utf-8")

    assert "Status: candidate support doctrine" in text
    assert "co-located candidate implementation exists" in text
    assert "documented non-implemented" not in text
    assert "implementation_present != adopted" in text
    assert "synthetic_demonstration != real_dossier_acceptance" in text
    assert "runtime_success != authorization" in text
    assert "memory != Evidence" in text
    assert "not real-dossier acceptance" in text


def test_mvp_loop_current_implementation_owners_remain_present() -> None:
    required = (
        "implementation/mvp_vertical/contract.py",
        "implementation/mvp_vertical/runner.py",
        "implementation/mvp_vertical/terminal_gate_standin.py",
        "implementation/mvp_vertical/register.py",
        "schemas/mvp_governed_loop_objects.schema.yaml",
    )

    for relative in required:
        assert (ROOT / relative).is_file(), relative


def test_mvp_loop_no_longer_describes_an_external_schema_owner() -> None:
    text = LOOP.read_text(encoding="utf-8")

    assert "external binding vendors the schema" not in text.lower()
    assert "pantheon_contracts" in text
    assert "No second vocabulary owner is needed" in text
