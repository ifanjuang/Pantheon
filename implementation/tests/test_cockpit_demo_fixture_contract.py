import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
FIXTURE = COCKPIT / "demo-data.json"
BOOTSTRAP = COCKPIT / "demo_bootstrap.js"


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_demo_fixture_projects_have_stable_identity_and_payloads() -> None:
    fixture = _fixture()
    projects = fixture["projects"]
    payloads = fixture["project_payloads"]

    project_ids = [project["project_id"] for project in projects]
    assert len(project_ids) == len(set(project_ids))
    assert set(project_ids) == set(payloads)

    for project in projects:
        assert project["code"]
        assert project["display_name"]
        assert project["attributes"]
        assert isinstance(project.get("claim_values", {}), dict)
        assert isinstance(project.get("claim_refs", {}), dict)


def test_demo_claim_provenance_resolves_to_project_information() -> None:
    fixture = _fixture()

    for project in fixture["projects"]:
        information_ids = {
            item["information_id"]
            for item in fixture["project_payloads"][project["project_id"]]["information"]
        }
        for refs in project.get("claim_refs", {}).values():
            for ref in refs:
                backing_ref = ref["backing_ref"]
                assert backing_ref["entity_type"] == "information"
                assert backing_ref["entity_id"] in information_ids
                assert ref["provenance"]["source_ref"]


def test_demo_keeps_acted_and_working_information_distinct() -> None:
    fixture = _fixture()
    statuses = {
        item["status"]
        for payload in fixture["project_payloads"].values()
        for item in payload["information"]
    }

    assert "acted" in statuses
    assert "in_progress" in statuses


def test_demo_bootstrap_targets_an_existing_project_and_remains_read_only() -> None:
    fixture = _fixture()
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    codes = {project["code"] for project in fixture["projects"]}

    assert 'projectInput.value = "VALLONS"' in bootstrap
    assert "VALLONS" in codes
    assert 'method !== "GET"' in bootstrap
    assert "écriture désactivée" in bootstrap


def test_removed_knowledge_updates_script_is_not_referenced() -> None:
    references = []
    for path in COCKPIT.rglob("*"):
        if path.suffix not in {".html", ".js"} or not path.is_file():
            continue
        if "knowledge_updates.js" in path.read_text(encoding="utf-8"):
            references.append(path.relative_to(ROOT).as_posix())

    assert references == []


def test_selected_project_projection_surfaces_operational_context_without_new_authority() -> None:
    source = (COCKPIT / "projection" / "cockpit_projection.js").read_text(encoding="utf-8")

    assert "function projectContextRows()" in source
    assert '"Situation en cours"' in source
    assert '"Dernière base ACTÉE"' in source
    assert '"Suites à donner"' in source
    assert '"Revue humaine"' in source
    assert "state.information" in source
    assert "state.workIssues" in source
    assert "state.changeCandidates" in source
