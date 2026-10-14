import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "templates/hermes/dashboard-plugins/pantheon-modules/dashboard/dist"
CONTROL = ROOT / "docs/assets/pantheon-control"
PREVIEW = CONTROL / "hermes-preview"


def test_public_preview_uses_exact_native_plugin_bundle():
    assert (PREVIEW / "plugin-index.js").read_bytes() == (PLUGIN / "index.js").read_bytes()
    assert (PREVIEW / "plugin-style.css").read_bytes() == (PLUGIN / "style.css").read_bytes()


def test_preview_is_explicitly_synthetic_and_mutations_are_disabled():
    html = (CONTROL / "hermes-modules.html").read_text(encoding="utf-8")
    sdk = (PREVIEW / "demo-sdk.js").read_text(encoding="utf-8")
    assert "DÉMO — DONNÉES ENTIÈREMENT FICTIVES" in html
    assert "plugin-index.js" in html
    assert "plugin-style.css" in html
    assert "disabled: true" in sdk
    assert "meta.synthetic must be true" in sdk
    assert "mutation Hermes désactivée" in sdk
    assert 'fetch("hermes-modules-demo.json"' in sdk
    assert 'fetch("../hermes-modules-demo.json"' not in sdk
    assert 'mode: "demo"' in sdk


def test_operation_cards_are_operator_friendly_by_default():
    plugin = (PLUGIN / "index.js").read_text(encoding="utf-8")
    assert "Contrôle de qualité de la recherche" in plugin
    assert "Configurée en essai limité, actuellement désactivée." in plugin
    assert "Configuration à valider" in plugin
    assert "Détails techniques" in plugin
    assert 'React.createElement("dd", { className: "pm-mono" }, item.schedule)' in plugin
    assert 'React.createElement("p", { className: "pm-native-name" }, item.jobName)' not in plugin
    assert 'const [expandedOperation, setExpandedOperation] = useState("");' in plugin
    assert 'hidden: !props.expanded' in plugin
    assert '"aria-expanded": props.expanded ? "true" : "false"' in plugin
    assert 'props.expanded ? "Masquer les détails" : "Afficher les détails"' in plugin
    assert 'current === item.id ? "" : item.id' in plugin


def test_fixture_covers_every_governed_night_operation():
    data = json.loads((CONTROL / "hermes-modules-demo.json").read_text(encoding="utf-8"))
    assert data["meta"]["synthetic"] is True
    jobs = {job["name"]: job for job in data["payloads"]["jobs"]}
    expected = {
        "pantheon-night:backup-preflight": 7,
        "pantheon-night:pdf-ingestion-vectorization": 7,
        "pantheon-night:retrieval-quality-review": 7,
        "pantheon-night:memory-consolidation-review": 4,
        "pantheon-night:contradiction-drift-review": 7,
        "pantheon-night:morning-decision-digest": 7,
    }
    assert {name: jobs[name]["repeat"]["times"] for name in expected} == expected
    assert all(job["enabled"] is False and job["state"] == "paused" for job in jobs.values())


def test_duplicate_preview_renderer_was_removed():
    assert not (CONTROL / "hermes-modules-adapter.js").exists()
    assert not (CONTROL / "hermes-modules.css").exists()
    assert not (CONTROL / "pages/hermes-modules.js").exists()
