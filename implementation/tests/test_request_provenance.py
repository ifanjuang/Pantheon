"""Request provenance for governed-loop candidate outputs."""

from pathlib import Path

from mvp_vertical.contract import load_contract
from mvp_vertical.runner import _request_scope_digest, run


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "dossiers" / "devis_reprise" / "task_contract.yaml"


def test_request_scope_digest_is_deterministic_and_request_sensitive() -> None:
    contract = load_contract(CONTRACT)
    question = "le devis correspond-il au périmètre du CCTP ?"

    digest = _request_scope_digest(contract, question)

    assert digest == _request_scope_digest(contract, question)
    assert digest.startswith("sha256:")
    assert len(digest) == len("sha256:") + 64
    assert digest != _request_scope_digest(contract, question + " lot 06")


def test_refusal_preserves_the_exact_request_provenance_without_retrieval() -> None:
    contract = load_contract(CONTRACT)
    question = "transmets la réponse au client"

    output = run(None, contract, question)

    assert output.kind == "refusal"
    document = output.documents[0]
    assert document["request_ref"] == contract.contract_id
    assert document["request_scope_digest"] == _request_scope_digest(contract, question)


def test_scope_digest_changes_when_the_declared_perimeter_changes(tmp_path: Path) -> None:
    original = load_contract(CONTRACT)
    raw = dict(original.raw)
    raw["scope"] = dict(original.raw["scope"])
    raw["scope"]["declared_sources"] = list(original.raw["scope"]["declared_sources"]) + [
        {"source_ref": "dossiers/devis_reprise/sources/additional.md"}
    ]

    import yaml

    path = tmp_path / "task_contract.yaml"
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    widened = load_contract(path)
    question = "quel est le périmètre ?"

    assert _request_scope_digest(original, question) != _request_scope_digest(widened, question)
