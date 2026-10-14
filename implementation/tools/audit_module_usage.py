#!/usr/bin/env python3
"""Build a report-only Python module usage inventory for Pantheon zones.

The report corrects a known limitation of the broad architecture inventory: Python
relative imports such as ``from . import agency_directory`` and
``from .app_lifecycle import install`` must be resolved against the importing
package before a module can be described as unreferenced.

A ``candidate_unreferenced`` result is not deletion proof. It is reserved for an
implementation module for which no static Python importer, route, main entry,
package entry, dynamic module reference or non-historical configuration reference
was found. Runtime/deployment review and an explicit human decision remain required
before removal.

Test modules and tooling are classified separately. A test file is not dead code
because no other test imports it, and an unreferenced maintenance script requires
an operational review rather than automatic deletion.

Module reachability is not call reachability
--------------------------------------------
The module layer answers "is this module referenced?". That question cannot see a
symbol that is imported everywhere and called nowhere — the state the policy
chokepoint was in while the inventory reported no unreferenced module at all.

The symbol layer answers the narrower question "is this path taken?". For every
module-level function and class in a zone it records who calls it and whether a
call chain reaches it from an entry point (a route handler, a registered
callback, a ``__main__`` guard, or anything executed at import time).

Call resolution is by bare symbol name: a call to ``foo()`` matches every symbol
named ``foo`` in the zone. That over-connects the graph, so the analysis errs
towards declaring a symbol reachable. ``never_called`` and
``runtime_called_unreached`` are therefore conservative — a symbol lands there
only when *no* name in the zone reaches it — while ``entry_reachable`` is the
weaker claim and is not proof that a deployed run takes the path.

A required-call registry pins the states that are supposed to hold. An entry that
expects anything other than ``entry_reachable`` must say what blocks it, so a
known dead path stays declared rather than becoming invisible again.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

PYTHON_EXCLUDED_PARTS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}
TEXT_REFERENCE_SUFFIXES = {".toml", ".yaml", ".yml", ".json", ".sh"}
ROUTE_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}
HISTORICAL_PARTS = {"ai_logs", "archive", "archives", "history"}
REFERENCE_PARTS = {"vendor", "vendored"}

# A decorator that only shapes the object it wraps does not register it with a
# runtime, so it is not on its own evidence that something reaches the symbol.
NON_REGISTERING_DECORATORS = {
    "abstractmethod",
    "cache",
    "cached_property",
    "classmethod",
    "dataclass",
    "final",
    "lru_cache",
    "override",
    "property",
    "runtime_checkable",
    "staticmethod",
    "total_ordering",
    "wraps",
}
SYMBOL_STATES = (
    "entry_reachable",
    "runtime_called_unreached",
    "test_called_only",
    "never_called",
)


@dataclass(frozen=True)
class ZoneSpec:
    name: str
    role: str
    owner_identity: str
    root: Path


@dataclass
class ModuleRecord:
    zone: str
    zone_role: str
    owner_identity: str
    module: str
    path: str
    posture: str
    imports: list[str] = field(default_factory=list)
    imported_by_runtime: list[str] = field(default_factory=list)
    imported_by_tests: list[str] = field(default_factory=list)
    config_references: list[str] = field(default_factory=list)
    dynamic_references: list[str] = field(default_factory=list)
    route_count: int = 0
    has_main: bool = False
    package_entry: bool = False
    parse_error: str | None = None
    usage_state: str = "unknown"
    removal_candidate: bool = False
    limits: list[str] = field(default_factory=list)


@dataclass
class SymbolRecord:
    zone: str
    module: str
    path: str
    symbol: str
    name: str
    kind: str
    line: int
    entry_seed: bool = False
    seed_reason: str | None = None
    called_by_runtime: list[str] = field(default_factory=list)
    called_by_tests: list[str] = field(default_factory=list)
    reachability: str = "never_called"


def zone_spec(value: str) -> ZoneSpec:
    try:
        name, role, owner_identity, raw_root = value.split("=", 3)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected NAME=ROLE=OWNER=PATH") from exc
    root = Path(raw_root).expanduser().resolve()
    if not root.is_dir():
        raise argparse.ArgumentTypeError(f"zone root does not exist: {root}")
    if not name or not role or not owner_identity:
        raise argparse.ArgumentTypeError("zone name, role and owner identity are required")
    return ZoneSpec(
        name=name,
        role=role,
        owner_identity=owner_identity,
        root=root,
    )


def _iter_python(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.py")
        if path.is_file()
        and not any(part in PYTHON_EXCLUDED_PARTS for part in path.parts)
    )


def _module_name(root: Path, path: Path) -> str:
    parts = list(path.relative_to(root).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _posture(root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    parts = {part.lower() for part in relative.parts}
    if parts & HISTORICAL_PARTS:
        return "history"
    if parts & REFERENCE_PARTS:
        return "reference"
    if "tests" in parts or path.name.startswith("test_"):
        return "test"
    if "migrations" in parts:
        return "migration"
    if "tools" in parts or "scripts" in parts or ".github" in parts:
        return "tooling"
    return "implementation"


def _package_for(module: str, path: Path) -> str:
    if path.name == "__init__.py":
        return module
    return module.rsplit(".", 1)[0] if "." in module else ""


def _relative_base(package: str, level: int, module: str | None) -> str:
    parts = package.split(".") if package else []
    climb = max(level - 1, 0)
    if climb > len(parts):
        return module or ""
    prefix = parts[: len(parts) - climb] if climb else parts
    if module:
        prefix.extend(module.split("."))
    return ".".join(part for part in prefix if part)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _inspect_python(
    root: Path,
    path: Path,
) -> tuple[list[str], int, bool, list[str], str | None]:
    module = _module_name(root, path)
    package = _package_for(module, path)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        return [], 0, False, [], str(exc)

    imports: set[str] = set()
    dynamic: set[str] = set()
    routes = 0
    has_main = path.name == "__main__.py"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = _relative_base(package, node.level, node.module)
            else:
                base = node.module or ""
            if node.module:
                if base:
                    imports.add(base)
            else:
                for alias in node.names:
                    if alias.name != "*":
                        imports.add(
                            ".".join(part for part in (base, alias.name) if part)
                        )
        elif isinstance(node, ast.If):
            if (
                isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name)
                and node.test.left.id == "__name__"
                and any(
                    _string(item) == "__main__" for item in node.test.comparators
                )
            ):
                has_main = True
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            if (
                name in ROUTE_METHODS
                and node.args
                and _string(node.args[0]) is not None
            ):
                routes += 1
            if name in {"import_module", "find_spec"} and node.args:
                value = _string(node.args[0])
                if value:
                    dynamic.add(value)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value.strip()
            if re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+", value):
                dynamic.add(value)

    return sorted(imports), routes, has_main, sorted(dynamic), None


def _names_used(node: ast.AST) -> tuple[set[str], set[str]]:
    """Names this subtree calls, and names it mentions without calling.

    The second set is what stops the analysis from mistaking live code for dead
    code. A request body model appears only as a route handler's annotation, a
    setuptools command subclass only as a ``cmdclass`` dict value, and a
    registered callback only as an argument. None of them is ever called by
    name, and all of them are reached.
    """
    called: set[str] = set()
    referenced: set[str] = set()
    call_targets: set[int] = set()

    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            name = _call_name(sub.func)
            if name:
                called.add(name)
            call_targets.add(id(sub.func))

    for sub in ast.walk(node):
        if id(sub) in call_targets:
            continue
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
            referenced.add(sub.id)
        elif isinstance(sub, ast.Attribute) and isinstance(sub.ctx, ast.Load):
            referenced.add(sub.attr)

    return called, referenced


def _signature_nodes(statement: ast.AST) -> list[ast.AST]:
    """The parts of a definition that sit outside its body but still use names.

    Annotations live here, and they are the only place a request body model is
    ever mentioned.
    """
    nodes: list[ast.AST] = []
    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
        nodes.append(statement.args)
        if statement.returns is not None:
            nodes.append(statement.returns)
    elif isinstance(statement, ast.ClassDef):
        nodes.extend(statement.bases)
        nodes.extend(keyword.value for keyword in statement.keywords)
    return nodes


def _registering_decorator(node: ast.AST) -> str | None:
    """The decorator that hands this symbol to a runtime, if any."""
    decorators = getattr(node, "decorator_list", [])
    for decorator in decorators:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        name = _call_name(target)
        if not name or name in NON_REGISTERING_DECORATORS:
            continue
        if isinstance(target, ast.Attribute) or isinstance(decorator, ast.Call):
            return name
    return None


def _collect_symbols(
    root: Path,
    path: Path,
) -> tuple[list[dict], set[str], set[str]]:
    """Module-level symbols with the names they reach, plus import-time names."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError):
        return [], set(), set()

    symbols: list[dict] = []
    module_called: set[str] = set()
    module_referenced: set[str] = set()

    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for decorator in statement.decorator_list:
                called, referenced = _names_used(decorator)
                module_called |= called
                module_referenced |= referenced
            body_called: set[str] = set()
            body_referenced: set[str] = set()
            for child in list(statement.body) + _signature_nodes(statement):
                called, referenced = _names_used(child)
                body_called |= called
                body_referenced |= referenced
            symbols.append(
                {
                    "name": statement.name,
                    "kind": "class" if isinstance(statement, ast.ClassDef) else "function",
                    "line": statement.lineno,
                    "calls": sorted(body_called | body_referenced),
                    "decorator": _registering_decorator(statement),
                }
            )
            continue
        called, referenced = _names_used(statement)
        module_called |= called
        module_referenced |= referenced

    return symbols, module_called, module_referenced


def _classify_symbols(
    spec: ZoneSpec,
    posture_by_module: dict[str, str],
    relative_by_module: dict[str, str],
    path_by_module: dict[str, Path],
) -> list[SymbolRecord]:
    collected: dict[str, list[dict]] = {}
    runtime_import_time: set[str] = set()
    test_import_time: set[str] = set()

    for module, path in path_by_module.items():
        symbols, module_called, module_referenced = _collect_symbols(spec.root, path)
        collected[module] = symbols
        seen = module_called | module_referenced
        if posture_by_module[module] == "test":
            test_import_time |= seen
        else:
            runtime_import_time |= seen

    defined: dict[str, list[SymbolRecord]] = defaultdict(list)
    order: list[SymbolRecord] = []
    for module, symbols in collected.items():
        if posture_by_module[module] == "test":
            continue
        for entry in symbols:
            symbol = SymbolRecord(
                zone=spec.name,
                module=module,
                path=relative_by_module[module],
                symbol=f"{module}:{entry['name']}",
                name=entry["name"],
                kind=entry["kind"],
                line=entry["line"],
            )
            if entry["decorator"]:
                symbol.entry_seed = True
                symbol.seed_reason = f"registered by @{entry['decorator']}"
            elif entry["name"] in runtime_import_time:
                symbol.entry_seed = True
                symbol.seed_reason = "reached at import time or handed over as a value"
            defined[entry["name"]].append(symbol)
            order.append(symbol)

    # Call edges, resolved by bare name. Over-connecting keeps the dead-path
    # verdicts conservative; see the module docstring.
    edges: dict[str, set[str]] = defaultdict(set)
    for module, symbols in collected.items():
        is_test = posture_by_module[module] == "test"
        for entry in symbols:
            caller = f"{module}:{entry['name']}"
            for called in entry["calls"]:
                for target in defined.get(called, ()):
                    if is_test:
                        target.called_by_tests.append(caller)
                    else:
                        target.called_by_runtime.append(caller)
            if not is_test:
                edges[entry["name"]].update(entry["calls"])

    reachable: set[str] = set()
    frontier = [symbol.name for symbol in order if symbol.entry_seed]
    while frontier:
        name = frontier.pop()
        if name in reachable:
            continue
        reachable.add(name)
        frontier.extend(edges.get(name, ()))

    for symbol in order:
        symbol.called_by_runtime = sorted(set(symbol.called_by_runtime))
        symbol.called_by_tests = sorted(set(symbol.called_by_tests))
        if symbol.name in reachable:
            symbol.reachability = "entry_reachable"
        elif symbol.called_by_runtime:
            symbol.reachability = "runtime_called_unreached"
        elif symbol.called_by_tests:
            symbol.reachability = "test_called_only"
        else:
            symbol.reachability = "never_called"

    return sorted(order, key=lambda item: (item.path, item.line))


def inspect_zone_symbols(spec: ZoneSpec) -> list[SymbolRecord]:
    """The symbol layer on its own, without the module-level reference scan."""
    path_by_module = {
        _module_name(spec.root, path): path for path in _iter_python(spec.root)
    }
    posture = {
        module: _posture(spec.root, path) for module, path in path_by_module.items()
    }
    relative = {
        module: path.relative_to(spec.root).as_posix()
        for module, path in path_by_module.items()
    }
    return _classify_symbols(spec, posture, relative, path_by_module)


def _local_targets(imported: str, local_modules: set[str]) -> set[str]:
    return {
        module
        for module in local_modules
        if imported == module or imported.startswith(module + ".")
    }


def _configuration_references(
    spec: ZoneSpec,
    path_by_module: dict[str, Path],
) -> dict[str, list[str]]:
    references: dict[str, list[str]] = defaultdict(list)
    needles: dict[str, tuple[str, ...]] = {}
    for module, python_path in path_by_module.items():
        relative = python_path.relative_to(spec.root).as_posix()
        without_suffix = relative.removesuffix(".py")
        needles[module] = tuple(
            value
            for value in {
                module,
                relative,
                without_suffix,
                module.replace(".", "/") + ".py",
            }
            if value
        )

    for path in sorted(spec.root.rglob("*")):
        if (
            not path.is_file()
            or path.suffix.lower() not in TEXT_REFERENCE_SUFFIXES
            or any(part in PYTHON_EXCLUDED_PARTS for part in path.parts)
            or {part.lower() for part in path.parts} & HISTORICAL_PARTS
        ):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        relative = path.relative_to(spec.root).as_posix()
        for module, module_needles in needles.items():
            for needle in module_needles:
                if "/" in needle:
                    found = needle in text
                else:
                    found = bool(
                        re.search(
                            rf"(?<![\w.]){re.escape(needle)}(?![\w.])",
                            text,
                        )
                    )
                if found:
                    references[module].append(relative)
                    break
    return references


def inspect_zone_with_symbols(
    spec: ZoneSpec,
) -> tuple[list[ModuleRecord], list[SymbolRecord]]:
    paths = _iter_python(spec.root)
    path_by_module = {_module_name(spec.root, path): path for path in paths}
    local_modules = {module for module in path_by_module if module}
    records: dict[str, ModuleRecord] = {}
    imports_by_module: dict[str, list[str]] = {}
    dynamic_by_module: dict[str, list[str]] = {}

    for module, path in path_by_module.items():
        imports, route_count, has_main, dynamic, parse_error = _inspect_python(
            spec.root, path
        )
        relative = path.relative_to(spec.root).as_posix()
        records[module] = ModuleRecord(
            zone=spec.name,
            zone_role=spec.role,
            owner_identity=spec.owner_identity,
            module=module,
            path=relative,
            posture=_posture(spec.root, path),
            imports=imports,
            route_count=route_count,
            has_main=has_main,
            package_entry=path.name in {"__main__.py", "setup.py"},
            parse_error=parse_error,
            limits=[
                "static usage evidence != runtime deployment proof",
                "candidate_unreferenced != deletion authorization",
            ],
        )
        imports_by_module[module] = imports
        dynamic_by_module[module] = dynamic

    for importer, imported_names in imports_by_module.items():
        importer_record = records[importer]
        for imported in imported_names:
            for target in _local_targets(imported, local_modules):
                target_record = records[target]
                if importer_record.posture == "test":
                    target_record.imported_by_tests.append(importer)
                else:
                    target_record.imported_by_runtime.append(importer)

    for importer, referenced_names in dynamic_by_module.items():
        for referenced in referenced_names:
            for target in _local_targets(referenced, local_modules):
                records[target].dynamic_references.append(importer)

    config = _configuration_references(spec, path_by_module)
    for module, paths_for_module in config.items():
        records[module].config_references.extend(paths_for_module)

    for module, record in records.items():
        path = path_by_module[module]
        if path.name == "__init__.py":
            record.usage_state = "package_initializer"
        elif record.parse_error:
            record.usage_state = "parse_error"
        elif record.posture == "test":
            record.usage_state = "test_module"
        elif record.route_count or record.has_main or record.package_entry:
            record.usage_state = "active_entrypoint"
        elif record.imported_by_runtime:
            record.usage_state = "active_imported"
        elif record.dynamic_references or record.config_references:
            record.usage_state = "active_dynamic_or_configured"
        elif record.imported_by_tests:
            record.usage_state = "test_only"
        elif record.posture in {"history", "reference", "migration"}:
            record.usage_state = record.posture
        elif record.posture == "tooling":
            record.usage_state = "tooling_unreferenced_review"
        else:
            record.usage_state = "candidate_unreferenced"
            record.removal_candidate = True

        record.imported_by_runtime = sorted(set(record.imported_by_runtime))
        record.imported_by_tests = sorted(set(record.imported_by_tests))
        record.dynamic_references = sorted(set(record.dynamic_references))
        record.config_references = sorted(set(record.config_references))

    symbols = _classify_symbols(
        spec,
        {module: record.posture for module, record in records.items()},
        {module: record.path for module, record in records.items()},
        path_by_module,
    )
    return sorted(records.values(), key=lambda item: item.path), symbols


def inspect_zone(spec: ZoneSpec) -> list[ModuleRecord]:
    return inspect_zone_with_symbols(spec)[0]


@dataclass(frozen=True)
class RequiredCallFinding:
    entry_id: str
    symbol: str
    expected: str
    observed: str
    detail: str


def load_required_call_paths(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("paths", [])
    if not isinstance(entries, list):
        raise ValueError(f"{path}: 'paths' must be a list")
    return entries


def check_required_call_paths(
    entries: list[dict],
    symbols: list[SymbolRecord],
) -> list[RequiredCallFinding]:
    """Compare each declared path against what the call graph actually shows.

    Divergence fails in both directions. A path that was supposed to be taken
    and is not is the failure this check exists for; a path declared dead that
    has since come alive is a declaration nobody updated, and leaving it stale
    is how the next dead path becomes invisible.
    """
    by_symbol = {symbol.symbol: symbol for symbol in symbols}
    findings: list[RequiredCallFinding] = []

    for entry in entries:
        entry_id = str(entry.get("id", "<unnamed>"))
        symbol_ref = str(entry.get("symbol", ""))
        expected = str(entry.get("expected_state", ""))

        if expected not in SYMBOL_STATES:
            findings.append(
                RequiredCallFinding(
                    entry_id, symbol_ref, expected, "-",
                    f"expected_state must be one of {', '.join(SYMBOL_STATES)}",
                )
            )
            continue
        if expected != "entry_reachable" and not entry.get("blocked_by"):
            findings.append(
                RequiredCallFinding(
                    entry_id, symbol_ref, expected, "-",
                    "a path declared as not taken must name what blocks it "
                    "('blocked_by'), so the gap stays visible",
                )
            )
            continue

        symbol = by_symbol.get(symbol_ref)
        if symbol is None:
            findings.append(
                RequiredCallFinding(
                    entry_id, symbol_ref, expected, "absent",
                    "no module-level symbol with this name exists in the zone",
                )
            )
            continue
        if symbol.reachability != expected:
            findings.append(
                RequiredCallFinding(
                    entry_id, symbol_ref, expected, symbol.reachability,
                    f"declared {expected}, observed {symbol.reachability}",
                )
            )

    return findings


def render_markdown(
    specs: list[ZoneSpec],
    records: list[ModuleRecord],
    symbols: list[SymbolRecord] | None = None,
    findings: list[RequiredCallFinding] | None = None,
) -> str:
    counts: dict[str, int] = defaultdict(int)
    for record in records:
        counts[record.usage_state] += 1
    candidates = [record for record in records if record.removal_candidate]
    test_only = [record for record in records if record.usage_state == "test_only"]
    tooling_review = [
        record
        for record in records
        if record.usage_state == "tooling_unreferenced_review"
    ]

    lines = [
        "# Pantheon Python module usage inventory",
        "",
        "> Report-only: static usage evidence is not deletion proof or an authority decision.",
        "",
        "## Zones",
        "",
    ]
    lines.extend(
        f"- **{spec.name}** — {spec.role} — owner identity `{spec.owner_identity}` — `{spec.root}`" for spec in specs
    )
    lines.extend(["", "## Summary", ""])
    lines.extend(
        f"- {state}: **{count}**" for state, count in sorted(counts.items())
    )
    lines.extend(["", "## Candidate unreferenced implementation modules", ""])
    if not candidates:
        lines.append("None detected.")
    for record in candidates:
        lines.append(f"- `{record.zone}:{record.path}` (`{record.module}`)")

    lines.extend(["", "## Test-only implementation modules", ""])
    if not test_only:
        lines.append("None detected.")
    for record in test_only:
        lines.append(
            f"- `{record.zone}:{record.path}` — imported by "
            + ", ".join(f"`{item}`" for item in record.imported_by_tests)
        )

    lines.extend(["", "## Tooling requiring operational review", ""])
    if not tooling_review:
        lines.append("None detected.")
    for record in tooling_review:
        lines.append(f"- `{record.zone}:{record.path}` (`{record.module}`)")

    symbols = symbols or []
    if symbols:
        symbol_counts: dict[str, int] = defaultdict(int)
        for symbol in symbols:
            symbol_counts[symbol.reachability] += 1
        unreached = [
            symbol
            for symbol in symbols
            if symbol.reachability == "runtime_called_unreached"
        ]
        lines.extend(
            [
                "",
                "## Symbol call reachability",
                "",
                "Module reachability cannot see a symbol that is imported everywhere and called nowhere. This layer answers whether the path is taken.",
                "",
            ]
        )
        lines.extend(
            f"- {state}: **{count}**" for state, count in sorted(symbol_counts.items())
        )
        lines.extend(
            [
                "",
                "Call edges are resolved by bare symbol name, which over-connects the graph. `never_called` and `runtime_called_unreached` are therefore conservative; `entry_reachable` is the weaker claim and is not proof that a deployed run takes the path.",
                "",
                "### Called by runtime code but not reachable from an entry point",
                "",
            ]
        )
        if not unreached:
            lines.append("None detected.")
        for symbol in unreached:
            lines.append(
                f"- `{symbol.zone}:{symbol.path}:{symbol.line}` `{symbol.symbol}` — "
                + "called by "
                + ", ".join(f"`{item}`" for item in symbol.called_by_runtime)
            )

    if findings is not None:
        lines.extend(["", "## Required call paths", ""])
        if not findings:
            lines.append("Every declared path holds.")
        for finding in findings:
            lines.append(
                f"- **{finding.entry_id}** `{finding.symbol}`: {finding.detail}"
            )

    lines.extend(
        [
            "",
            "## Review rule",
            "",
            "A module may be removed only after runtime/deployment references are checked, its consumers are proven absent, the change passes full CI, and an explicit human decision reviews the removal. A candidate state alone never authorizes deletion.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--zone",
        action="append",
        type=zone_spec,
        required=True,
        help="NAME=ROLE=OWNER=PATH (repeatable)",
    )
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument(
        "--required-call-paths",
        type=Path,
        default=None,
        help="JSON registry of call paths whose reachability state is declared; "
        "the run fails when an observed state diverges from its declaration",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    records: list[ModuleRecord] = []
    symbols: list[SymbolRecord] = []
    for spec in args.zone:
        zone_records, zone_symbols = inspect_zone_with_symbols(spec)
        records.extend(zone_records)
        symbols.extend(zone_symbols)

    findings: list[RequiredCallFinding] | None = None
    if args.required_call_paths is not None:
        findings = check_required_call_paths(
            load_required_call_paths(args.required_call_paths), symbols
        )
    payload = {
        "schema_id": "pantheon.module_usage_inventory",
        "revision": 1,
        "zones": [
            {"name": spec.name, "role": spec.role, "owner_identity": spec.owner_identity, "root": str(spec.root)}
            for spec in args.zone
        ],
        "summary": {
            "modules": len(records),
            "candidate_unreferenced": sum(
                item.removal_candidate for item in records
            ),
            "test_only": sum(
                item.usage_state == "test_only" for item in records
            ),
            "test_modules": sum(
                item.usage_state == "test_module" for item in records
            ),
            "tooling_unreferenced_review": sum(
                item.usage_state == "tooling_unreferenced_review"
                for item in records
            ),
            "symbols": len(symbols),
            "symbols_never_called": sum(
                item.reachability == "never_called" for item in symbols
            ),
            "symbols_runtime_called_unreached": sum(
                item.reachability == "runtime_called_unreached" for item in symbols
            ),
            "symbols_test_called_only": sum(
                item.reachability == "test_called_only" for item in symbols
            ),
        },
        "modules": [asdict(record) for record in records],
        "symbols": [asdict(symbol) for symbol in symbols],
        "required_call_findings": (
            [asdict(finding) for finding in findings] if findings is not None else []
        ),
        "limits": [
            "static usage evidence != runtime deployment proof",
            "candidate_unreferenced != deletion authorization",
            "tooling reference absence != deletion authorization",
            "CI success != semantic or operational authority",
            "import reachability != call reachability",
            "entry_reachable != a deployed run takes the path",
        ],
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.write_text(
        render_markdown(args.zone, records, symbols, findings),
        encoding="utf-8",
    )

    if findings:
        print("Declared call paths diverge from the call graph:", file=sys.stderr)
        for finding in findings:
            print(
                f"- {finding.entry_id} ({finding.symbol}): {finding.detail}",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
