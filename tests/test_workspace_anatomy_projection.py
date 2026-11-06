"""The Workspace Cockpit reads the Anatomy projection a Project owner published, and nothing else."""

import importlib.util
import json
from pathlib import Path
from threading import Thread
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "implementation/workspace_cockpit/anatomy_projection.py"


def load():
    spec = importlib.util.spec_from_file_location("anatomy_projection", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def publish(directory: Path, code: str = "DEMO", **overrides) -> Path:
    room = {
        "object_id": "obj.room", "object_family": "spatial", "display_name": "Séjour", "internal_code": "R1",
        "attribute_claims": [{"attribute_key": "space.area", "value": {"value_type": "number", "value": 21.5, "unit": "m2"},
                              "certainty": "E3", "proof_status": "candidate", "source_representation_refs": ["rep.room"]}],
        "relations": [], "private_field": "never forwarded",
    }
    level = {
        "object_id": "obj.level", "object_family": "spatial", "display_name": "RDC", "internal_code": "RDC",
        "attribute_claims": [],
        "relations": [{"relation_type": "spatial.contains", "subject_ref": {"entity_id": "obj.level"},
                       "object_ref": {"entity_id": "obj.room"}, "qualifier": {"ouvrage_state": "projected"}}],
    }
    document = {
        "schema": "pantheon.anatomy.v1",
        "generated_at": "2026-11-06T09:00:00+00:00",
        "project": {"project_id": "demo", "code": code, "display_name": "Démo"},
        "anatomy": {
            "summary": {"stable_object_count": 2},
            "structure": {"objects": [level, room]},
            "sources": [{"representation_id": "rep.room", "source_kind": "document", "context": {"page": 2},
                         "mapped_object_refs": []}],
            "phases": {"status": "no_phase_declared"},
        },
        **overrides,
    }
    path = directory / f"{code}.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_published_projection_is_rebuilt_to_what_the_card_shows(tmp_path):
    m = load()
    publish(tmp_path)
    result = m.read_anatomy(tmp_path, "DEMO")
    assert result["available"] and result["project"]["code"] == "DEMO"
    room = next(item for item in result["objects"] if item["id"] == "obj.room")
    assert room["attributes"][0] == {
        "key": "space.area", "value": 21.5, "unit": "m2", "certainty": "E3", "proof_status": "candidate",
        "assertion_mode": None, "object_ref": None, "subject_ref": None, "qualifier": {}, "sources": ["rep.room"],
    }
    assert "private_field" not in room
    level = next(item for item in result["objects"] if item["id"] == "obj.level")
    assert level["relations"][0]["qualifier"] == {"ouvrage_state": "projected"}
    assert result["sources"]["rep.room"] == {"page": 2, "kind": "document", "identity_pending": True}


def test_unconfigured_missing_or_invalid_requests_are_refused_quietly(tmp_path):
    m = load()
    assert m.read_anatomy(None, "DEMO")["error"] == "anatomy_not_configured"
    assert m.read_anatomy(tmp_path, "DEMO")["error"] == "no_anatomy"
    for code in ("../etc/passwd", "a/b", "", ".hidden"):
        assert m.read_anatomy(tmp_path, code)["error"] == "invalid_code"


def test_a_file_that_is_not_the_published_projection_is_unreadable(tmp_path):
    m = load()
    publish(tmp_path, schema="other.v1")
    assert m.read_anatomy(tmp_path, "DEMO")["error"] == "anatomy_unreadable"
    publish(tmp_path, project={"code": "OTHER"})
    assert m.read_anatomy(tmp_path, "DEMO")["error"] == "anatomy_unreadable"
    (tmp_path / "DEMO.json").write_text("x" * (m.MAX_BYTES + 1))
    assert m.read_anatomy(tmp_path, "DEMO")["error"] == "anatomy_unreadable"


def test_cockpit_http_anatomy(tmp_path):
    publish(tmp_path)
    spec = importlib.util.spec_from_file_location("test_anatomy_server", ROOT / "implementation/workspace_cockpit/server.py")
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)

    class Handler(server.CockpitHandler):
        anatomy_dir = tmp_path

    http = server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{http.server_port}/workspace/api/anatomy?code=DEMO") as response:
            result = json.load(response)
            assert result["available"] and len(result["objects"]) == 2
            assert response.headers["Cache-Control"] == "no-store"
        with urlopen(f"http://127.0.0.1:{http.server_port}/workspace/api/anatomy?code=..%2Fsecret") as response:
            assert json.load(response)["error"] == "invalid_code"
    finally:
        http.shutdown()
        thread.join(2)
        http.server_close()
