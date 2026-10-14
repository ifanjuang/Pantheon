from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "docs" / "qualification" / "H5_AGENTIC_GOVERNANCE_CASES.md"
BINDINGS = ROOT / "docs" / "governance" / "HERMES_CAPABILITY_BINDINGS.md"
CONTROL = ROOT / "docs" / "governance" / "PANTHEON_CONTROL_PLANE_BOUNDARY.md"
RUNS = ROOT / "docs" / "governance" / "HERMES_RUN_LAUNCH_JUNCTION.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_h5_agentic_case_inventory_is_complete():
    text = _text(CASES)
    expected = [
        "Disponible ≠ approuvé",
        "Approuvé ≠ compatible avec l’environnement courant",
        "Compatible ≠ adopté",
        "Succès répétés ≠ Evidence",
        "Succès technique ≠ résultat valide",
        "Timeout du demandeur ≠ état distant connu",
        "Résultat tardif après annulation",
        "Nouvelle révision ≠ approbation héritée",
        "Même identité déclarée, contenu différent",
        "Signature valide ≠ confiance métier",
        "Source externe devenue inaccessible",
        "Substitution de provider dans un même Capability Slot",
        "Capability partiellement satisfaite",
        "Conflit entre fraîcheur et approbation",
        "Découverte externe ≠ vérité",
        "Skill supprimé, historique conservé",
        "Environnement modifié entre sélection et exécution",
        "Réévaluation sans réécriture de l’histoire",
    ]
    missing = [case for case in expected if case not in text]
    assert not missing, f"missing H5 agentic cases: {missing}"


def test_existing_capability_doctrine_preserves_core_non_equivalences():
    text = _text(BINDINGS) + "\n" + _text(CONTROL)
    expected = [
        "installed != approved",
        "healthy != safe",
        "binding_selected != dependency_adopted",
        "runtime_success != evidence",
        "update_available != update_authorized",
        "capability_visible != capability_enabled",
        "sandbox_enabled != production_approved",
    ]
    missing = [invariant for invariant in expected if invariant not in text]
    assert not missing, f"missing capability/control invariants: {missing}"


def test_run_junction_preserves_distributed_ambiguity_without_retry_inference():
    text = _text(RUNS)
    expected = [
        "submission_unknown != retry instruction",
        "registration_unknown != queue item",
        "inconclusive != pass",
        "no automatic second POST",
        "explicit operator reconciliation required",
        "Hermes completed != Evidence",
    ]
    missing = [invariant for invariant in expected if invariant not in text]
    assert not missing, f"missing distributed-ambiguity invariants: {missing}"


def test_h5_cases_do_not_propose_forbidden_runtime_layers():
    text = _text(CASES).lower()
    forbidden_assertions = [
        "pantheon becomes a provider router",
        "pantheon becomes a plugin manager",
        "pantheon becomes a scheduler",
        "pantheon becomes a retry queue",
        "runtime success becomes evidence",
        "signature valid means approved",
    ]
    present = [item for item in forbidden_assertions if item in text]
    assert not present, f"forbidden H5 architecture assertion(s): {present}"


def test_agentic_pressure_points_are_explicit_before_schema_extension():
    text = _text(CASES)
    expected = [
        "current environment compatibility at launch time",
        "partial Capability Slot requirement coverage",
        "exact artifact identity/digest divergence under identical declared identity",
        "cryptographic integrity versus contextual trust/adoption",
        "late remote result after cancellation/expiry without authorization resurrection",
    ]
    missing = [item for item in expected if item not in text]
    assert not missing, f"missing H5 pressure points: {missing}"
