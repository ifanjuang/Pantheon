from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "audit_module_usage.py"


def _load_tool():
    name = "pantheon_module_usage_audit"
    spec = importlib.util.spec_from_file_location(name, TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_relative_imports_are_resolved_before_orphan_classification(tmp_path: Path) -> None:
    audit = _load_tool()
    _write(tmp_path, "pkg/__init__.py", "from . import directory\n")
    _write(
        tmp_path,
        "pkg/api.py",
        "from .lifecycle import install\n"
        "from . import directory\n"
        "def mount(app):\n"
        "    app.get('/items')(lambda: {})\n"
        "    return install(directory)\n",
    )
    _write(tmp_path, "pkg/lifecycle.py", "def install(value):\n    return value\n")
    _write(tmp_path, "pkg/directory.py", "ITEMS = {}\n")
    _write(tmp_path, "pkg/orphan.py", "VALUE = 1\n")

    spec = audit.ZoneSpec("demo", "implementation", "demo-owner", tmp_path)
    records = {item.module: item for item in audit.inspect_zone(spec)}

    assert records["pkg.lifecycle"].usage_state == "active_imported"
    assert records["pkg.directory"].usage_state == "active_imported"
    assert records["pkg.api"].usage_state == "active_entrypoint"
    assert records["pkg.orphan"].usage_state == "candidate_unreferenced"
    assert records["pkg.orphan"].removal_candidate is True


def test_configuration_test_modules_and_test_only_usage_are_distinct(tmp_path: Path) -> None:
    audit = _load_tool()
    _write(tmp_path, "pkg/__init__.py", "")
    _write(tmp_path, "pkg/plugin.py", "def register():\n    return None\n")
    _write(tmp_path, "pkg/helper.py", "VALUE = 1\n")
    _write(tmp_path, "tests/test_consumer.py", "import pkg.helper\n")
    _write(tmp_path, "tests/test_lonely.py", "def test_ok():\n    assert True\n")
    _write(tmp_path, "plugin.yaml", "entrypoint: pkg.plugin\n")
    _write(tmp_path, "pkg/__main__.py", "print('entry')\n")

    spec = audit.ZoneSpec("demo", "implementation", "demo-owner", tmp_path)
    records = {item.module: item for item in audit.inspect_zone(spec)}

    assert records["pkg.plugin"].usage_state == "active_dynamic_or_configured"
    assert records["pkg.plugin"].removal_candidate is False
    assert records["pkg.helper"].usage_state == "test_only"
    assert records["pkg.helper"].removal_candidate is False
    assert records["tests.test_consumer"].usage_state == "test_module"
    assert records["tests.test_lonely"].usage_state == "test_module"
    assert records["tests.test_lonely"].removal_candidate is False
    assert records["pkg.__main__"].usage_state == "active_entrypoint"


def test_tooling_path_reference_is_detected_and_unreferenced_tooling_is_review_only(
    tmp_path: Path,
) -> None:
    audit = _load_tool()
    _write(
        tmp_path,
        ".github/scripts/sync_preview.py",
        "from pathlib import Path\nPath('out').mkdir(exist_ok=True)\n",
    )
    _write(
        tmp_path,
        ".github/scripts/retired_helper.py",
        "VALUE = 1\n",
    )
    _write(
        tmp_path,
        ".github/workflows/preview.yml",
        "steps:\n  - run: python .github/scripts/sync_preview.py\n",
    )

    spec = audit.ZoneSpec("demo", "governance", "demo-owner", tmp_path)
    records = {item.path: item for item in audit.inspect_zone(spec)}

    active = records[".github/scripts/sync_preview.py"]
    review = records[".github/scripts/retired_helper.py"]
    assert active.usage_state == "active_dynamic_or_configured"
    assert active.config_references == [".github/workflows/preview.yml"]
    assert review.usage_state == "tooling_unreferenced_review"
    assert review.removal_candidate is False


def test_markdown_states_that_candidate_is_not_deletion_proof(tmp_path: Path) -> None:
    audit = _load_tool()
    _write(tmp_path, "orphan.py", "VALUE = 1\n")
    spec = audit.ZoneSpec("demo", "implementation", "demo-owner", tmp_path)
    records = audit.inspect_zone(spec)

    report = audit.render_markdown([spec], records)

    assert "candidate_unreferenced" in report
    assert "not deletion proof" in report
    assert "explicit human decision" in report


# --- symbol call reachability ---------------------------------------------
#
# The module layer answers "is this module referenced?". These cover the
# narrower question it cannot answer: "is this path taken?" — the state the
# policy chokepoint was in while the inventory reported no unreferenced module.

REGISTRY = ROOT / "qualification" / "required-call-paths.json"


def _symbols(audit, root: Path) -> dict:
    spec = audit.ZoneSpec("demo", "implementation", "demo-owner", root)
    return {item.symbol: item for item in audit.inspect_zone_symbols(spec)}


def test_a_symbol_imported_everywhere_and_called_nowhere_is_visible(tmp_path: Path) -> None:
    """The exact blindness: the module reads as active, the symbol as dead."""
    audit = _load_tool()
    _write(tmp_path, "pkg/__init__.py", "")
    _write(tmp_path, "pkg/gate.py", "def enforce(value):\n    return value\n")
    _write(
        tmp_path,
        "pkg/api.py",
        "from .gate import enforce\n"
        "def mount(app):\n"
        "    app.get('/items')(lambda: {})\n",
    )

    spec = audit.ZoneSpec("demo", "implementation", "demo-owner", tmp_path)
    modules = {item.module: item for item in audit.inspect_zone(spec)}
    symbols = _symbols(audit, tmp_path)

    assert modules["pkg.gate"].usage_state == "active_imported"
    assert modules["pkg.gate"].removal_candidate is False
    assert symbols["pkg.gate:enforce"].reachability == "never_called"


def test_a_symbol_reached_only_by_tests_does_not_read_as_reached(tmp_path: Path) -> None:
    audit = _load_tool()
    _write(tmp_path, "pkg/__init__.py", "")
    _write(tmp_path, "pkg/client.py", "class HttpClient:\n    pass\n")
    _write(tmp_path, "tests/test_client.py", "from pkg.client import HttpClient\ndef test_it():\n    HttpClient()\n")

    symbols = _symbols(audit, tmp_path)
    assert symbols["pkg.client:HttpClient"].reachability == "test_called_only"
    assert symbols["pkg.client:HttpClient"].called_by_runtime == []


def test_runtime_callers_below_a_dead_root_are_reported_as_unreached(tmp_path: Path) -> None:
    audit = _load_tool()
    _write(tmp_path, "pkg/__init__.py", "")
    _write(
        tmp_path,
        "pkg/chain.py",
        "def _helper():\n    return 1\n"
        "def root():\n    return _helper()\n",
    )
    _write(tmp_path, "tests/test_chain.py", "from pkg.chain import root\ndef test_it():\n    root()\n")

    symbols = _symbols(audit, tmp_path)
    assert symbols["pkg.chain:root"].reachability == "test_called_only"
    assert symbols["pkg.chain:_helper"].reachability == "runtime_called_unreached"
    assert symbols["pkg.chain:_helper"].called_by_runtime == ["pkg.chain:root"]


def test_a_symbol_that_is_only_ever_an_annotation_is_still_reached(tmp_path: Path) -> None:
    """A request body model is never called. It is not dead code."""
    audit = _load_tool()
    _write(tmp_path, "pkg/__init__.py", "")
    _write(
        tmp_path,
        "pkg/api.py",
        "class ItemBody:\n    pass\n"
        "def register(app):\n"
        "    @app.post('/items')\n"
        "    def create(body: ItemBody):\n"
        "        return body\n",
    )
    _write(tmp_path, "pkg/main.py", "from .api import register\nregister(None)\n")

    symbols = _symbols(audit, tmp_path)
    assert symbols["pkg.api:ItemBody"].reachability == "entry_reachable"


def test_a_symbol_handed_over_as_a_value_is_reached_without_being_called(tmp_path: Path) -> None:
    audit = _load_tool()
    _write(tmp_path, "pkg/__init__.py", "")
    _write(tmp_path, "pkg/handlers.py", "def read_items():\n    return []\n")
    _write(
        tmp_path,
        "pkg/wiring.py",
        "from .handlers import read_items\n"
        "ROUTES = {'/items': read_items}\n",
    )

    symbols = _symbols(audit, tmp_path)
    assert symbols["pkg.handlers:read_items"].reachability == "entry_reachable"
    assert symbols["pkg.handlers:read_items"].seed_reason


def test_a_shaping_decorator_is_not_evidence_that_anything_reaches_the_symbol(
    tmp_path: Path,
) -> None:
    audit = _load_tool()
    _write(tmp_path, "pkg/__init__.py", "")
    _write(
        tmp_path,
        "pkg/models.py",
        "from dataclasses import dataclass\n"
        "@dataclass(frozen=True)\n"
        "class Unused:\n"
        "    value: int\n",
    )

    symbols = _symbols(audit, tmp_path)
    assert symbols["pkg.models:Unused"].reachability == "never_called"


def test_every_symbol_carries_one_of_the_declared_states() -> None:
    audit = _load_tool()
    spec = audit.ZoneSpec("implementation", "implementation", "owner", ROOT)
    symbols = audit.inspect_zone_symbols(spec)
    assert symbols
    assert {item.reachability for item in symbols} <= set(audit.SYMBOL_STATES)


# --- the required-call registry -------------------------------------------


def _entry(**overrides) -> dict:
    entry = {
        "id": "demo",
        "symbol": "pkg.gate:enforce",
        "expected_state": "entry_reachable",
        "why": "demo",
    }
    entry.update(overrides)
    return entry


def _one_dead_symbol(audit, tmp_path: Path):
    _write(tmp_path, "pkg/__init__.py", "")
    _write(tmp_path, "pkg/gate.py", "def enforce(value):\n    return value\n")
    _write(tmp_path, "pkg/api.py", "from .gate import enforce\n")
    return list(_symbols(audit, tmp_path).values())


def test_a_path_that_stops_being_taken_fails(tmp_path: Path) -> None:
    audit = _load_tool()
    symbols = _one_dead_symbol(audit, tmp_path)
    findings = audit.check_required_call_paths([_entry()], symbols)
    assert len(findings) == 1
    assert findings[0].expected == "entry_reachable"
    assert findings[0].observed == "never_called"


def test_a_path_declared_dead_that_comes_alive_also_fails(tmp_path: Path) -> None:
    """A stale declaration is how the next dead path becomes invisible."""
    audit = _load_tool()
    _write(tmp_path, "pkg/__init__.py", "")
    _write(tmp_path, "pkg/gate.py", "def enforce(value):\n    return value\n")
    _write(tmp_path, "pkg/api.py", "from .gate import enforce\nenforce(1)\n")
    symbols = list(_symbols(audit, tmp_path).values())

    findings = audit.check_required_call_paths(
        [_entry(expected_state="never_called", blocked_by="nothing calls it yet")], symbols
    )
    assert len(findings) == 1
    assert findings[0].observed == "entry_reachable"


def test_a_path_declared_not_taken_must_name_what_blocks_it(tmp_path: Path) -> None:
    audit = _load_tool()
    symbols = _one_dead_symbol(audit, tmp_path)
    findings = audit.check_required_call_paths(
        [_entry(expected_state="never_called")], symbols
    )
    assert len(findings) == 1
    assert "blocked_by" in findings[0].detail

    assert audit.check_required_call_paths(
        [_entry(expected_state="never_called", blocked_by="no runtime caller yet")], symbols
    ) == []


def test_an_entry_naming_a_symbol_that_does_not_exist_fails(tmp_path: Path) -> None:
    audit = _load_tool()
    symbols = _one_dead_symbol(audit, tmp_path)
    findings = audit.check_required_call_paths([_entry(symbol="pkg.gate:gone")], symbols)
    assert len(findings) == 1 and findings[0].observed == "absent"


def test_an_unknown_expected_state_is_refused(tmp_path: Path) -> None:
    audit = _load_tool()
    symbols = _one_dead_symbol(audit, tmp_path)
    findings = audit.check_required_call_paths(
        [_entry(expected_state="probably_fine")], symbols
    )
    assert len(findings) == 1


def test_the_declared_paths_match_the_real_implementation_zone() -> None:
    """The registry is pinned to what the zone actually does, not to intent."""
    audit = _load_tool()
    spec = audit.ZoneSpec("implementation", "implementation", "owner", ROOT)
    entries = audit.load_required_call_paths(REGISTRY)
    assert entries, "the registry must not silently empty itself"
    findings = audit.check_required_call_paths(entries, audit.inspect_zone_symbols(spec))
    assert findings == [], "\n".join(f"{f.entry_id}: {f.detail}" for f in findings)


def test_the_registry_declares_a_reason_for_every_entry() -> None:
    entries = json.loads(REGISTRY.read_text(encoding="utf-8"))["paths"]
    for entry in entries:
        assert entry.get("why"), f"{entry.get('id')}: an entry must say why it matters"
        assert entry.get("id") and entry.get("symbol")
