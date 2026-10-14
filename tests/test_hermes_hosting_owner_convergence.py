from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_distribution_locks_use_current_hosting_owners() -> None:
    locks = (
        "templates/hermes/distribution/distribution-lock.example.yaml",
        "implementation/hermes/distribution/pantheon-standard.lock.yaml",
    )

    for relative in locks:
        text = _read(relative)
        assert "HERMES_CODE_HOSTING_BOUNDARY.md" not in text
        assert "NEXT_MVP_REPOSITORY_PLACEMENT.md" in text
        assert "HERMES_INTEGRATION.md" in text


def test_materialized_distribution_preserves_runtime_authority_boundaries() -> None:
    materialized = _read("implementation/hermes/distribution/pantheon-standard.lock.yaml")

    assert "installation_state: not_observed" in materialized
    assert "activation_state: not_activated" in materialized
    assert "task_authorization_state: not_authorized" in materialized
    assert "admits_evidence: false" in materialized
