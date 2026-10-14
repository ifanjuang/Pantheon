"""Acceptance tests for the read-only workspace -> Card/Collection seam."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from mvp_vertical.cockpit_composed import create_composed_cockpit_app


ROOT = Path(__file__).resolve().parents[1]
DATA_LOADER = ROOT / "mvp_vertical" / "cockpit" / "data" / "cockpit_data_loader.js"
ASSEMBLER = ROOT / "mvp_vertical" / "cockpit" / "projection" / "child_collection_assembler.js"


def _forbidden_connection():
    raise AssertionError("workspace projection must not open a database connection")


def _workspace(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "_VAULT.md").write_text("control", encoding="utf-8")
    (root / "_KEEP.md").write_text("visible underscore file", encoding="utf-8")
    (root / ".obsidian").mkdir()
    (root / ".secret.md").write_text("hidden", encoding="utf-8")

    project_a = root / "Affaires" / "Projet-A"
    (project_a / "Notes").mkdir(parents=True)
    (project_a / "Documents").mkdir()
    (project_a / "Projet.md").write_text("Projet A", encoding="utf-8")
    (project_a / "Notes" / "question.md").write_text("Question", encoding="utf-8")
    (project_a / "Documents" / "piece.md").write_text("Pièce", encoding="utf-8")

    project_b = root / "Affaires" / "Projet-B"
    (project_b / "Chantier").mkdir(parents=True)
    (project_b / "Photos").mkdir()
    (project_b / "Projet.md").write_text("Projet B", encoding="utf-8")

    (root / "Recherche").mkdir()
    (root / "Recherche" / "essai.md").write_text("Essai", encoding="utf-8")
    # Invalid UTF-8 on purpose: collection projection must never parse file bytes.
    (root / "Recherche" / "binary-file.bin").write_bytes(b"\xff\xfe\x00\x81")

    (root / "Nomenclature").mkdir()
    (root / "Nomenclature" / "IA.md").write_text("Index", encoding="utf-8")
    (root / "Nomenclature" / "tags.json").write_text(
        '{"not":"a Tag Registry mutation"}',
        encoding="utf-8",
    )
    return root


def _client(workspace_roots: dict[str, Path]) -> TestClient:
    return TestClient(
        create_composed_cockpit_app(
            connect_fn=_forbidden_connection,
            initialize_fn=None,
            api_key="read-key",
            workspace_roots=workspace_roots,
        )
    )


def _get(client: TestClient, workspace_ref: str, path: str = ""):
    return client.get(
        f"/cockpit/workspace-collections/{workspace_ref}",
        params={"path": path} if path else None,
        headers={"Authorization": "Bearer read-key"},
    )


def _by_title(body: dict) -> dict[str, dict]:
    return {item["title"]: item for item in body["collection"]["items"]}


def test_workspace_root_is_generic_read_only_projection_without_control_or_hidden_entries(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path / "fixture-workspace")
    client = _client({"primary": root})

    response = _get(client, "primary")
    assert response.status_code == 200
    body = response.json()
    assert body["cards_are_projections"] is True
    assert body["collection"]["state"] == "loaded"
    assert body["collection"]["can_add"] is False

    items = body["collection"]["items"]
    assert [item["title"] for item in items] == [
        "Affaires",
        "Nomenclature",
        "Recherche",
        "_KEEP.md",
    ]
    assert "_VAULT.md" not in _by_title(body)
    assert ".obsidian" not in _by_title(body)
    assert ".secret.md" not in _by_title(body)

    for title in ("Affaires", "Nomenclature", "Recherche"):
        card = _by_title(body)[title]
        assert card["entity_type"] == "workspace_entry"
        assert card["role"] == "container"
        assert card["category"] == "Dossier"
        assert card["workspace_entry_kind"] == "directory"
        assert card["child_collection"]["state"] == "available"
        assert card["child_collection"]["load_action"]["kind"] == "collection_read"
        assert card["child_collection"]["load_action"]["href"].startswith(
            "/cockpit/workspace-collections/primary?path="
        )

    underscore = _by_title(body)["_KEEP.md"]
    assert underscore["entity_type"] == "workspace_entry"
    assert underscore["role"] == "entity"
    assert underscore["category"] == "Fichier"
    assert "child_collection" not in underscore

    serialized = json.dumps(body, ensure_ascii=False)
    assert str(root) not in serialized
    assert "project_id" not in serialized
    assert "source_entity_ref" not in serialized
    assert "knowledge_id" not in serialized


def test_arbitrary_nested_shapes_files_and_empty_directories_project_without_business_inference(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path / "fixture-workspace")
    client = _client({"primary": root})

    affaires = _get(client, "primary", "Affaires")
    assert affaires.status_code == 200
    projects = _by_title(affaires.json())
    assert set(projects) == {"Projet-A", "Projet-B"}
    assert all(item["entity_type"] == "workspace_entry" for item in projects.values())
    assert all(item["category"] == "Dossier" for item in projects.values())
    assert all("source_project_id" not in item for item in projects.values())

    project_a = _get(client, "primary", "Affaires/Projet-A")
    assert project_a.status_code == 200
    a_items = _by_title(project_a.json())
    assert set(a_items) == {"Documents", "Notes", "Projet.md"}
    assert a_items["Projet.md"]["workspace_entry_kind"] == "file"
    assert "child_collection" not in a_items["Projet.md"]

    project_b = _get(client, "primary", "Affaires/Projet-B")
    assert project_b.status_code == 200
    b_items = _by_title(project_b.json())
    assert set(b_items) == {"Chantier", "Photos", "Projet.md"}
    assert b_items["Chantier"]["child_collection"]["state"] == "available"

    empty = _get(client, "primary", "Affaires/Projet-B/Chantier")
    assert empty.status_code == 200
    assert empty.json()["collection"]["state"] == "empty"
    assert empty.json()["collection"]["items"] == []

    research = _get(client, "primary", "Recherche")
    assert research.status_code == 200
    research_items = _by_title(research.json())
    assert set(research_items) == {"binary-file.bin", "essai.md"}
    assert research_items["binary-file.bin"]["workspace_entry_kind"] == "file"

    nomenclature = _get(client, "primary", "Nomenclature")
    assert nomenclature.status_code == 200
    assert set(_by_title(nomenclature.json())) == {"IA.md", "tags.json"}


def test_workspace_projection_identity_is_path_stable_workspace_scoped_and_rename_sensitive(
    tmp_path: Path,
) -> None:
    first = _workspace(tmp_path / "first")
    second = _workspace(tmp_path / "second")
    client = _client({"first": first, "second": second})

    first_a = _get(client, "first", "Recherche").json()
    first_b = _get(client, "first", "Recherche").json()
    second_a = _get(client, "second", "Recherche").json()

    first_id = _by_title(first_a)["essai.md"]["entity_id"]
    assert _by_title(first_b)["essai.md"]["entity_id"] == first_id
    assert _by_title(second_a)["essai.md"]["entity_id"] != first_id

    (first / "Recherche" / "essai.md").rename(first / "Recherche" / "renamed.md")
    renamed = _get(client, "first", "Recherche").json()
    assert "essai.md" not in _by_title(renamed)
    assert _by_title(renamed)["renamed.md"]["entity_id"] != first_id


def test_workspace_route_requires_read_key_and_fails_closed_on_invalid_paths(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path / "fixture-workspace")
    client = _client({"primary": root})

    unauthorized = client.get("/cockpit/workspace-collections/primary")
    assert unauthorized.status_code == 401

    assert _get(client, "missing").status_code == 404
    assert _get(client, "primary", "../outside").status_code == 422
    assert _get(client, "primary", "/etc").status_code == 422
    assert _get(client, "primary", "C:/Windows/System32").status_code == 422
    assert _get(client, "primary", r"Affaires\Projet-A").status_code == 422
    assert _get(client, "primary", "Recherche/essai.md").status_code == 422
    assert _get(client, "primary", "does-not-exist").status_code == 404


def test_symlinks_are_not_exposed_and_direct_symlink_navigation_is_refused(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path / "fixture-workspace")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("secret", encoding="utf-8")
    link = root / "linked-outside"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):  # pragma: no cover - platform policy
        pytest.skip("symlink creation unavailable on this runner")

    client = _client({"primary": root})
    root_body = _get(client, "primary").json()
    assert "linked-outside" not in _by_title(root_body)

    direct = _get(client, "primary", "linked-outside")
    assert direct.status_code == 422
    assert "symlink" in direct.json()["detail"]


def _run_node(body: str) -> subprocess.CompletedProcess[str]:
    node = shutil.which("node")
    if node is None:  # pragma: no cover - runner dependent
        pytest.skip("Node.js is unavailable; generic workspace collection check skipped")
    return subprocess.run(
        [node, "--input-type=module", "-e", body],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_existing_generic_collection_read_and_registration_accept_workspace_entry_cards() -> None:
    result = _run_node(
        f"""
        globalThis.window = {{
          fetch() {{ throw new Error("unexpected default fetch"); }},
          PantheonDecisionRequestProjection: {{
            normalize(value) {{ return value; }},
            rootCard() {{ return {{ entity_id: "space:decisions" }}; }},
          }},
          PantheonProjectAnatomyProjection: {{ projectCards() {{ return null; }} }},
          PantheonGlobalDecisionRequests: [],
          PantheonProjectDecisionRequests: [],
        }};
        await import({json.dumps(DATA_LOADER.as_uri())});
        await import({json.dumps(ASSEMBLER.as_uri())});

        const parentId = "workspace-entry:parent";
        const collectionId = `children:${{parentId}}`;
        const parent = {{
          entity_id: parentId,
          entity_type: "workspace_entry",
          child_collection: {{
            state: "available",
            collection_id: collectionId,
            load_action: {{
              kind: "collection_read",
              href: "/cockpit/workspace-collections/demo?path=Recherche",
            }},
            can_add: false,
          }},
        }};
        const responsePayload = {{
          cards_are_projections: true,
          collection: {{
            collection_id: collectionId,
            parent_entity_id: parentId,
            state: "loaded",
            can_add: false,
            items: [{{
              entity_id: "workspace-entry:file",
              entity_type: "workspace_entry",
              role: "entity",
              family: "information",
              title: "essai.md",
            }}],
          }},
        }};

        const fetchImpl = async (path, options = {{}}) => {{
          if (path !== "/cockpit/workspace-collections/demo?path=Recherche") throw new Error("workspace href changed");
          if (options.headers?.Authorization !== "Bearer read-key") throw new Error("read key missing");
          return {{ ok: true, async json() {{ return responsePayload; }} }};
        }};
        const loader = window.PantheonCockpitDataLoader.create({{ fetchImpl }});
        const loaded = await loader.loadChildCollection(parent.child_collection.load_action, "read-key");

        const cards = new Map([[parentId, parent]]);
        const children = new Map();
        const context = {{
          state: {{ cards, children }},
          putCard(model) {{ cards.set(model.entity_id, model); return model.entity_id; }},
          setChildren(parentEntityId, ids) {{ children.set(parentEntityId, ids.slice()); }},
        }};
        const ids = window.PantheonChildCollectionAssembler.registerLoadedCollection(
          parentId,
          loaded,
          context,
        );
        if (ids.length !== 1 || ids[0] !== "workspace-entry:file") throw new Error("workspace Card not registered");
        if (cards.get("workspace-entry:file")?.entity_type !== "workspace_entry") throw new Error("workspace type was routed away");
        if (cards.get(parentId)?.child_collection?.state !== "loaded") throw new Error("parent was not marked loaded");
        if (children.get(parentId)?.[0] !== "workspace-entry:file") throw new Error("workspace relation not registered");
        """
    )
    assert result.returncode == 0, result.stderr
