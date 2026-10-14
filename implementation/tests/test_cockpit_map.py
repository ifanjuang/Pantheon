"""Executable and boundary checks for the read-only Cockpit knowledge-map lens."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAP_DIR = ROOT / "mvp_vertical" / "cockpit" / "map"
SCRIPTS = sorted(MAP_DIR.glob("*.js"))
FORBIDDEN = ("fetch(", "XMLHttpRequest", "WebSocket", "localStorage", "sessionStorage")


def _node() -> str:
    executable = shutil.which("node")
    if executable is None:  # pragma: no cover - depends on the runner image
        pytest.skip("Node.js is unavailable")
    return executable


def _run_node(source: str) -> None:
    result = subprocess.run(
        [_node(), "-e", source],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def _loader(*names: str) -> str:
    paths = [str(MAP_DIR / name) for name in names]
    return f"""
const fs = require('fs');
const vm = require('vm');
global.window = global;
for (const path of {json.dumps(paths)}) {{
  vm.runInThisContext(fs.readFileSync(path, 'utf8'), {{ filename: path }});
}}
"""


def test_map_scripts_present() -> None:
    names = {p.name for p in SCRIPTS}
    assert {
        "map_graph_model.js", "map_layouts.js", "map_view.js",
        "map_tokens.js", "map_corroboration.js", "map_bundle.js", "map_mount.js",
    } <= names


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda path: path.name)
def test_map_javascript_parses(script: Path) -> None:
    result = subprocess.run(
        [_node(), "--check", str(script)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda path: path.name)
def test_map_lens_is_read_only(script: Path) -> None:
    source = script.read_text(encoding="utf-8")
    for token in FORBIDDEN:
        assert token not in source, f"{script.name} must stay read-only (found {token!r})"


def test_map_declares_boundary_invariants() -> None:
    readme = (MAP_DIR / "README.md").read_text(encoding="utf-8")
    for invariant in ("map view != data model", "projection != authority", "read-only"):
        assert invariant in readme, f"README must declare invariant: {invariant!r}"


def test_map_modules_expose_globals() -> None:
    expected = {
        "map_graph_model.js": "window.PantheonMapGraphModel",
        "map_layouts.js": "window.PantheonMapLayouts",
        "map_view.js": "window.PantheonMapView",
        "map_tokens.js": "window.PantheonMapTokens",
        "map_corroboration.js": "window.PantheonMapCorroboration",
        "map_bundle.js": "window.PantheonMapBundle",
        "map_mount.js": "window.PantheonMapMount",
    }
    for name, symbol in expected.items():
        source = (MAP_DIR / name).read_text(encoding="utf-8")
        assert symbol in source, f"{name} must expose {symbol}"


def test_projection_graph_exposure_is_read_only_hook() -> None:
    source = (ROOT / "mvp_vertical" / "cockpit" / "projection" / "cockpit_projection.js").read_text(encoding="utf-8")
    assert "window.PantheonCockpitGraph = Object.freeze(" in source
    assert "pantheon:graph-updated" in source


def test_map_binding_is_read_only_and_parses() -> None:
    binding = ROOT / "mvp_vertical" / "cockpit" / "map_binding.js"
    assert binding.exists()
    source = binding.read_text(encoding="utf-8")
    for token in FORBIDDEN:
        assert token not in source, f"map_binding.js must stay read-only (found {token!r})"
    result = subprocess.run([_node(), "--check", str(binding)], check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_projection_passes_through_corroboration_refs() -> None:
    source = (ROOT / "mvp_vertical" / "cockpit" / "projection" / "cockpit_projection.js").read_text(encoding="utf-8")
    assert "corroboration_refs" in source
    assert "contradiction_refs" in source


def test_live_bootstrap_loads_map_modules() -> None:
    source = (ROOT / "mvp_vertical" / "cockpit" / "live_bootstrap.js").read_text(encoding="utf-8")
    for script in ("map/map_view.js", "map/map_mount.js", "map_binding.js"):
        assert script in source, f"live_bootstrap must load {script}"


def test_graph_model_handles_orphans_cycles_deduplication_and_immutability() -> None:
    _run_node(_loader("map_graph_model.js") + r"""
const assert = require('assert');
const tags = ['structure'];
const cards = new Map([
  ['a', {entity_id:'a', entity_type:'information', subject_tags:tags, series_id:'s'}],
  ['b', {entity_id:'b', entity_type:'information', subject_tags:['structure'], series_id:'s', base_acted_id:'a'}],
  ['c', {entity_id:'c', entity_type:'document', subject_tags:['cctp']}],
  ['missing-id', null],
]);
const children = new Map([
  ['a', ['b', 'ghost', 'b']],
  ['b', ['a']],
  ['ghost', ['a']],
]);
const cardsBefore = JSON.stringify([...cards]);
const childrenBefore = JSON.stringify([...children]);
const graph = PantheonMapGraphModel.build(cards, children);
assert.deepStrictEqual(graph.nodes.map(n => n.id), ['a','b','c']);
assert.strictEqual(graph.links.filter(x => x.kind === 'lineage' && x.source === 'a' && x.target === 'b').length, 1);
assert.strictEqual(graph.links.filter(x => x.kind === 'containment' && x.source === 'a' && x.target === 'b').length, 1);
assert.strictEqual(graph.links.some(x => x.source === 'ghost' || x.target === 'ghost'), false);
assert.strictEqual(graph.links.some(x => x.source === x.target), false);
assert.strictEqual(JSON.stringify([...cards]), cardsBefore);
assert.strictEqual(JSON.stringify([...children]), childrenBefore);
graph.nodes[0].subject_tags.push('mutated-output');
assert.deepStrictEqual(tags, ['structure']);
""")


def test_graph_model_accepts_object_inputs_and_falls_back_to_map_key_identity() -> None:
    _run_node(_loader("map_graph_model.js") + r"""
const assert = require('assert');
const graph = PantheonMapGraphModel.build(
  {alpha:{entity_type:'knowledge', title:'Alpha'}, beta:{entity_id:'beta', entity_type:'document'}},
  {alpha:['beta']},
);
assert.deepStrictEqual(graph.nodes.map(n => n.id), ['alpha','beta']);
assert.deepStrictEqual(graph.links, [{source:'alpha', target:'beta', kind:'containment'}]);
""")


def test_all_layouts_are_deterministic_finite_and_do_not_mutate_nodes() -> None:
    _run_node(_loader("map_layouts.js") + r"""
const assert = require('assert');
const nodes = Array.from({length:37}, (_, i) => ({id:`n${i}`, subject:`s${i%5}`, family:`f${i%3}`}));
const before = JSON.stringify(nodes);
const opts = {width:900, height:560, groupOf:n => n.subject};
for (const name of PantheonMapLayouts.names) {
  const first = PantheonMapLayouts.layout(name, nodes, opts);
  const second = PantheonMapLayouts.layout(name, nodes, opts);
  assert.deepStrictEqual(first, second, `${name} must be deterministic`);
  assert.deepStrictEqual(Object.keys(first).sort(), nodes.map(n => n.id).sort());
  for (const point of Object.values(first)) {
    assert(Number.isFinite(point.x) && Number.isFinite(point.y), `${name} emitted non-finite coordinates`);
  }
}
assert.strictEqual(JSON.stringify(nodes), before);
assert.deepStrictEqual(
  PantheonMapLayouts.layout('unknown-layout', nodes, opts),
  PantheonMapLayouts.layout('cluster', nodes, opts),
);
for (const name of PantheonMapLayouts.names) {
  assert.deepStrictEqual(PantheonMapLayouts.layout(name, [], opts), {});
}
""")


def test_renderer_can_destroy_and_remount_without_retained_nodes() -> None:
    view_path = json.dumps(str(MAP_DIR / "map_view.js"))
    _run_node(_loader("map_graph_model.js", "map_layouts.js") + rf"""
const assert = require('assert');
class FakeNode {{
  constructor(name) {{ this.name=name; this.children=[]; this.attrs={{}}; this.style={{}}; this._text=''; this.innerHTML=''; }}
  setAttribute(k,v) {{ this.attrs[k]=String(v); }}
  append(...nodes) {{ this.children.push(...nodes); }}
  appendChild(node) {{ this.children.push(node); return node; }}
  set textContent(value) {{ this._text=String(value); if (value === '') this.children=[]; }}
  get textContent() {{ return this._text; }}
}}
global.document = {{ createElementNS(_ns, name) {{ return new FakeNode(name); }} }};
const viewPath = {view_path};
vm.runInThisContext(fs.readFileSync(viewPath, 'utf8'), {{ filename: viewPath }});
const tokens = {{
  subjectColor:()=> '#000', subjectIconKey:()=>null, statusColor:()=> '#000',
  originStroke:()=>({{stroke:'#000',dash:''}}), radius:()=>9,
}};
const svg = new FakeNode('svg');
const data = {{cards:new Map(), children:new Map()}};
const first = PantheonMapView.create(svg, data, {{tokens}});
assert(svg.children.length > 0);
first.destroy();
assert.strictEqual(svg.children.length, 0);
const second = PantheonMapView.create(svg, data, {{tokens}});
assert(svg.children.length > 0);
second.destroy();
assert.strictEqual(svg.children.length, 0);
""")
