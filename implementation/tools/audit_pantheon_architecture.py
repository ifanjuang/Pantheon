#!/usr/bin/env python3
"""Report-only monorepo-zone architecture convergence audit for Pantheon."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

ARCHITECTURE_SUFFIXES = {
    ".py", ".json", ".yaml", ".yml", ".md", ".sql", ".js", ".css",
    ".html", ".toml", ".sh",
}
EXCLUDED_PARTS = {
    ".git", ".pytest_cache", ".venv", "venv", "__pycache__", "node_modules",
    "dist", "build",
}
HISTORICAL_PARTS = {"ai_logs", "archive", "archives", "history"}
REFERENCE_PARTS = {"vendor", "vendored", "fixtures", "examples", "templates", "demo"}
INSTANCE_PARTS = {"dossiers", "instances", "samples"}
PROJECTION_PARTS = {"cockpit", "openwebui"}
GUARD_PARTS = {".github", "tools"}
ADAPTER_PARTS = {
    "hermes", "paperless", "openwebui", "adapters", "adapter", "gateway",
    "client", "plugins", "skills",
}
GENERATION_PATH_TOKEN = re.compile(r"(?:^|[_./-])v\d+(?:$|[_./-])", re.IGNORECASE)
VERSION_REF_TOKEN = re.compile(r"/v\d+(?=/|\b)", re.IGNORECASE)
COMPATIBILITY_PATH_TOKEN = re.compile(
    r"(?:^|[_./-])(?:legacy|compat(?:ibility)?|deprecated|old)(?:$|[_./-])",
    re.IGNORECASE,
)
GENERIC_STEMS = {
    "readme", "index", "__init__", "changelog", "cli", "plugin", "skill",
    "task_contract", "pyproject", "config", "settings", "main", "server",
}
PRIORITY_ORDER = {f"P{number}": number for number in range(6)}
ROUTE_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}
RUNTIME_IMPORTS = {
    "scheduler": {"sched", "schedule", "apscheduler"},
    "queue": {"queue", "celery", "rq", "dramatiq"},
}
RUNTIME_NAME_PATTERNS = {
    "provider_router": re.compile(
        r"^(?:provider_?router|route_?provider|provider_?routing)$", re.I
    ),
    "plugin_manager": re.compile(r"^(?:plugin_?manager|manage_?plugins)$", re.I),
    "memory_engine": re.compile(r"^(?:memory_?engine|run_?memory_?engine)$", re.I),
    "automatic_approval": re.compile(
        r"^(?:auto(?:matic)?_?approv(?:e|al)|approval_?engine)$", re.I
    ),
    "scheduler": re.compile(r"^(?:scheduler|schedule_?task|schedule_?job)$", re.I),
    "queue": re.compile(r"^(?:queue|enqueue|dequeue|task_?queue|job_?queue)$", re.I),
}


@dataclass(frozen=True)
class ZoneSpec:
    name: str
    role: str
    owner_identity: str
    root: Path


@dataclass(frozen=True)
class ConceptRule:
    concept_id: str
    label: str
    semantic_owner: str
    implementation_owner: str | None
    runtime_owner: str | None
    projection_owner: str | None
    patterns: tuple[str, ...]
    max_identity_implementations: int = 6


@dataclass(frozen=True)
class OwnershipRegistry:
    registry_id: str
    revision: int
    concepts: tuple[ConceptRule, ...]


@dataclass(frozen=True)
class PythonSurface:
    module: str | None = None
    imports: tuple[str, ...] = ()
    public_symbols: tuple[str, ...] = ()
    routes: tuple[str, ...] = ()
    versioned_routes: tuple[str, ...] = ()
    version_references: tuple[str, ...] = ()
    runtime_boundary_terms: tuple[str, ...] = ()
    has_main: bool = False
    parse_error: str | None = None


@dataclass(frozen=True)
class Artifact:
    zone: str
    zone_role: str
    owner_identity: str
    path: str
    suffix: str
    stem: str
    lines: int
    bytes: int
    meaningful: bool
    digest: str
    posture: str
    generation_named: bool
    compatibility_named: bool
    concepts_content: tuple[str, ...]
    concepts_identity: tuple[str, ...]
    python_module: str | None = None
    imports: tuple[str, ...] = ()
    public_symbols: tuple[str, ...] = ()
    routes: tuple[str, ...] = ()
    versioned_routes: tuple[str, ...] = ()
    version_references: tuple[str, ...] = ()
    runtime_boundary_terms: tuple[str, ...] = ()
    has_main: bool = False
    parse_error: str | None = None


@dataclass(frozen=True)
class Finding:
    finding_id: str
    priority: str
    category: str
    subject: str
    owner_dimension: str | None
    owner: str | None
    recommendation: str
    artifacts: tuple[str, ...]
    review_state: str = "unreviewed"


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


def load_registry(path: Path) -> OwnershipRegistry:
    payload = json.loads(path.read_text(encoding="utf-8"))
    revision = int(payload["revision"])
    if revision < 1:
        raise ValueError("ownership registry revision must be positive")
    concepts: list[ConceptRule] = []
    seen: set[str] = set()
    for item in payload.get("concepts", []):
        concept_id = item["id"]
        if concept_id in seen:
            raise ValueError(f"duplicate concept id: {concept_id}")
        seen.add(concept_id)
        patterns = tuple(item.get("patterns", [re.escape(concept_id)]))
        for pattern in patterns:
            re.compile(pattern, re.IGNORECASE)
        semantic_owner = item.get("semantic_owner", item.get("canonical_owner"))
        if not semantic_owner:
            raise ValueError(f"concept {concept_id} has no semantic owner")
        concepts.append(
            ConceptRule(
                concept_id=concept_id,
                label=item.get("label", concept_id),
                semantic_owner=semantic_owner,
                implementation_owner=item.get("implementation_owner"),
                runtime_owner=item.get("runtime_owner"),
                projection_owner=item.get("projection_owner"),
                patterns=patterns,
                max_identity_implementations=int(
                    item.get(
                        "max_identity_implementations",
                        item.get("max_active_implementations", 6),
                    )
                ),
            )
        )
    if not concepts:
        raise ValueError("ownership registry must declare at least one concept")
    return OwnershipRegistry(payload["registry_id"], revision, tuple(concepts))


def iter_artifacts(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in ARCHITECTURE_SUFFIXES
        and not any(part in EXCLUDED_PARTS for part in path.parts)
    )


def classify_posture(spec: ZoneSpec, path: str, suffix: str) -> str:
    parts = {part.lower() for part in Path(path).parts}
    name = Path(path).name.lower()
    stem = Path(path).stem.lower()
    if parts & HISTORICAL_PARTS or name.startswith("changelog"):
        return "history"
    if parts & REFERENCE_PARTS:
        return "reference"
    if parts & INSTANCE_PARTS:
        return "instance"
    if "tests" in parts or name.startswith("test_"):
        return "test"
    if "migrations" in parts or ("sql" in parts and re.match(r"^\d+[_-]", stem)):
        return "migration"
    if parts & GUARD_PARTS:
        return "guard"
    if parts & PROJECTION_PARTS or suffix in {".js", ".css", ".html"}:
        return "projection"
    if spec.role == "governance" and (
        "schemas" in parts or "governance" in parts or "authority" in parts
    ):
        return "authority"
    if (
        spec.role == "implementation"
        and suffix in {".md", ".yaml", ".yml", ".json"}
        and ("contract" in stem or "schema" in stem)
    ):
        return "implementation_contract"
    if suffix in {".py", ".sql", ".sh"} or name.startswith(
        ("compose.", "docker-compose")
    ):
        return "implementation"
    return "documentation"


def module_name(root: Path, path: Path) -> str:
    relative = path.relative_to(root).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


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


def inspect_python(root: Path, path: Path, text: str) -> PythonSurface:
    relative = path.relative_to(root).as_posix()
    try:
        tree = ast.parse(text, filename=relative)
    except SyntaxError as exc:
        return PythonSurface(
            module=module_name(root, path),
            parse_error=f"{exc.msg} at line {exc.lineno}",
        )

    imports: set[str] = set()
    public: set[str] = set()
    routes: set[str] = set()
    versioned_routes: set[str] = set()
    version_refs: set[str] = set()
    runtime_terms: set[str] = set()
    has_main = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add("." * node.level + (node.module or ""))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                public.add(node.name)
            for category, pattern in RUNTIME_NAME_PATTERNS.items():
                if pattern.match(node.name):
                    runtime_terms.add(category)
        elif isinstance(node, ast.If):
            test = node.test
            if (
                isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == "__name__"
                and any(_string(comp) == "__main__" for comp in test.comparators)
            ):
                has_main = True
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name in ROUTE_METHODS and node.args:
                route = _string(node.args[0])
                if route is not None:
                    routes.add(f"{name.upper()} {route}")
                    if VERSION_REF_TOKEN.search(route):
                        versioned_routes.add(route)
            if name == "APIRouter":
                for keyword in node.keywords:
                    if keyword.arg == "prefix":
                        prefix = _string(keyword.value)
                        if prefix and VERSION_REF_TOKEN.search(prefix):
                            versioned_routes.add(prefix)
            if name:
                for category, pattern in RUNTIME_NAME_PATTERNS.items():
                    if pattern.match(name):
                        runtime_terms.add(category)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            version_refs.update(VERSION_REF_TOKEN.findall(node.value))

    imported_roots = {
        name.lstrip(".").split(".", 1)[0] for name in imports if name
    }
    for category, roots in RUNTIME_IMPORTS.items():
        if imported_roots & roots:
            runtime_terms.add(category)

    route_refs = {
        ref
        for route in versioned_routes
        for ref in VERSION_REF_TOKEN.findall(route)
    }
    return PythonSurface(
        module=module_name(root, path),
        imports=tuple(sorted(imports)),
        public_symbols=tuple(sorted(public)),
        routes=tuple(sorted(routes)),
        versioned_routes=tuple(sorted(versioned_routes)),
        version_references=tuple(sorted(version_refs - route_refs)),
        runtime_boundary_terms=tuple(sorted(runtime_terms)),
        has_main=has_main,
    )


def _concept_hits(text: str, rules: Iterable[ConceptRule]) -> tuple[str, ...]:
    return tuple(
        sorted(
            rule.concept_id
            for rule in rules
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in rule.patterns)
        )
    )


def inspect_artifact(
    spec: ZoneSpec,
    path: Path,
    registry: OwnershipRegistry,
) -> Artifact:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    relative = path.relative_to(spec.root).as_posix()
    suffix = path.suffix.lower()
    posture = classify_posture(spec, relative, suffix)
    python = inspect_python(spec.root, path, text) if suffix == ".py" else PythonSurface()
    identity_text = "\n".join((relative.replace("/", " "), *python.public_symbols))
    version_refs = python.version_references
    if suffix != ".py":
        version_refs = tuple(sorted(set(VERSION_REF_TOKEN.findall(text))))
    return Artifact(
        zone=spec.name,
        zone_role=spec.role,
        owner_identity=spec.owner_identity,
        path=relative,
        suffix=suffix,
        stem=path.stem.lower(),
        lines=len(text.splitlines()),
        bytes=len(raw),
        meaningful=bool(text.strip()),
        digest=hashlib.sha256(raw).hexdigest(),
        posture=posture,
        generation_named=bool(GENERATION_PATH_TOKEN.search(relative)),
        compatibility_named=bool(COMPATIBILITY_PATH_TOKEN.search(relative)),
        concepts_content=_concept_hits(text, registry.concepts),
        concepts_identity=_concept_hits(identity_text, registry.concepts),
        python_module=python.module,
        imports=python.imports,
        public_symbols=python.public_symbols,
        routes=python.routes,
        versioned_routes=python.versioned_routes,
        version_references=version_refs,
        runtime_boundary_terms=python.runtime_boundary_terms,
        has_main=python.has_main,
        parse_error=python.parse_error,
    )


def _assigned_zone(path: Path, specs: list[ZoneSpec]) -> ZoneSpec:
    candidates = [
        spec for spec in specs if path == spec.root or path.is_relative_to(spec.root)
    ]
    if not candidates:
        raise ValueError(f"artifact is outside declared audit zones: {path}")
    return max(candidates, key=lambda spec: len(spec.root.parts))


def build_inventory(
    specs: list[ZoneSpec],
    registry: OwnershipRegistry,
) -> list[Artifact]:
    roots = [spec.root for spec in specs]
    if len(roots) != len(set(roots)):
        raise ValueError("audit zones must not share the same physical root")
    paths = sorted(
        {path.resolve() for spec in specs for path in iter_artifacts(spec.root)},
        key=lambda item: str(item),
    )
    return [
        inspect_artifact(_assigned_zone(path, specs), path, registry)
        for path in paths
    ]


def exact_duplicates(records: list[Artifact]) -> list[list[Artifact]]:
    groups: dict[str, list[Artifact]] = defaultdict(list)
    for record in records:
        if record.meaningful:
            groups[record.digest].append(record)
    return [
        sorted(group, key=lambda item: (item.zone, item.path))
        for group in groups.values()
        if len(group) > 1
    ]


def repeated_stems(records: list[Artifact]) -> list[list[Artifact]]:
    groups: dict[str, list[Artifact]] = defaultdict(list)
    for record in records:
        if (
            record.meaningful
            and record.stem not in GENERIC_STEMS
            and len(record.stem) >= 8
        ):
            groups[record.stem].append(record)
    return [
        sorted(group, key=lambda item: (item.zone, item.path))
        for group in groups.values()
        if len({item.zone for item in group}) > 1
        and (
            any(item.concepts_identity for item in group)
            or len({item.digest for item in group}) == 1
        )
    ]


def incoming_import_counts(records: list[Artifact]) -> dict[tuple[str, str], int]:
    by_repo: dict[str, set[str]] = defaultdict(set)
    for record in records:
        if record.python_module:
            by_repo[record.zone].add(record.python_module)
    counts = {
        (zone, module): 0
        for zone, modules in by_repo.items()
        for module in modules
    }
    for record in records:
        for imported in record.imports:
            normalized = imported.lstrip(".")
            for module in by_repo.get(record.zone, set()):
                if normalized == module or normalized.startswith(module + "."):
                    counts[(record.zone, module)] += 1
    return counts


def _refs(records: Iterable[Artifact]) -> tuple[str, ...]:
    return tuple(sorted(f"{item.zone}:{item.path}" for item in records))


def _finding(
    *,
    priority: str,
    category: str,
    subject: str,
    owner_dimension: str | None,
    owner: str | None,
    recommendation: str,
    artifacts: tuple[str, ...],
) -> Finding:
    identity = json.dumps(
        [priority, category, subject, owner_dimension, owner, artifacts],
        separators=(",", ":"),
    )
    return Finding(
        finding_id=hashlib.sha256(identity.encode()).hexdigest()[:12],
        priority=priority,
        category=category,
        subject=subject,
        owner_dimension=owner_dimension,
        owner=owner,
        recommendation=recommendation,
        artifacts=artifacts,
    )


def build_findings(
    specs: list[ZoneSpec],
    records: list[Artifact],
    registry: OwnershipRegistry,
) -> list[Finding]:
    findings: list[Finding] = []

    generation_groups: dict[str, list[Artifact]] = defaultdict(list)
    for record in records:
        if not record.generation_named:
            continue
        if record.posture in {"history", "migration", "reference"}:
            generation_groups["P5"].append(record)
        elif record.posture in {
            "documentation", "authority", "test", "guard", "instance"
        }:
            generation_groups["P4"].append(record)
        else:
            generation_groups["P1"].append(record)
    for priority, group in sorted(
        generation_groups.items(), key=lambda item: PRIORITY_ORDER[item[0]]
    ):
        findings.append(
            _finding(
                priority=priority,
                category="generation_named_paths",
                subject=f"{len(group)} paths named by generation",
                owner_dimension=None,
                owner=None,
                recommendation=(
                    "Rename active architecture paths by responsibility; preserve only "
                    "historical and ordered migration identifiers."
                ),
                artifacts=_refs(group),
            )
        )

    route_records = [
        record
        for record in records
        if record.versioned_routes
        and record.posture in {"implementation", "projection"}
    ]
    if route_records:
        findings.append(
            _finding(
                priority="P1",
                category="internal_versioned_routes",
                subject=f"{len(route_records)} active files declare versioned routes",
                owner_dimension="implementation",
                owner="implementation",
                recommendation=(
                    "Expose stable responsibility-based routes and isolate external "
                    "protocol versions inside adapters."
                ),
                artifacts=_refs(route_records),
            )
        )

    reference_records = [
        record
        for record in records
        if record.version_references
        and not record.versioned_routes
        and record.posture not in {"history", "migration"}
    ]
    if reference_records:
        findings.append(
            _finding(
                priority="P4",
                category="version_references",
                subject=(
                    f"{len(reference_records)} files reference versioned endpoints "
                    "or protocols"
                ),
                owner_dimension=None,
                owner=None,
                recommendation=(
                    "Classify each reference as external protocol, test fixture or stale "
                    "internal identity; do not propagate external versions into domain names."
                ),
                artifacts=_refs(reference_records),
            )
        )

    active_compat = [
        record
        for record in records
        if record.compatibility_named
        and record.posture in {
            "implementation", "projection", "implementation_contract"
        }
    ]
    if active_compat:
        findings.append(
            _finding(
                priority="P2",
                category="active_compatibility_paths",
                subject=f"{len(active_compat)} active compatibility-labelled paths",
                owner_dimension="implementation",
                owner="implementation",
                recommendation=(
                    "Name consumers and a removal condition, then converge on one path."
                ),
                artifacts=_refs(active_compat),
            )
        )

    misplaced_governance = [
        record
        for record in records
        if record.zone_role == "implementation"
        and record.path.startswith("docs/governance/")
    ]
    if misplaced_governance:
        findings.append(
            _finding(
                priority="P2",
                category="governance_in_implementation_zone",
                subject=(
                    f"{len(misplaced_governance)} governance-path artifacts in "
                    "implementation zone"
                ),
                owner_dimension="semantic",
                owner="governance-core",
                recommendation=(
                    "Move semantic doctrine to the governance-core zone or rename the file as "
                    "implementation documentation that explicitly conforms upstream."
                ),
                artifacts=_refs(misplaced_governance),
            )
        )

    runtime_records = [
        record
        for record in records
        if record.runtime_boundary_terms
        and record.posture in {"implementation", "projection"}
    ]
    if runtime_records:
        findings.append(
            _finding(
                priority="P0",
                category="runtime_constructs",
                subject=(
                    f"{len(runtime_records)} executable files contain runtime-owned "
                    "constructs"
                ),
                owner_dimension="runtime",
                owner="Hermes/external runtime",
                recommendation=(
                    "Verify actual execution ownership. Keep only bounded clients, "
                    "observations and admission seams in Pantheon zones."
                ),
                artifacts=_refs(runtime_records),
            )
        )

    for group in exact_duplicates(records):
        postures = {item.posture for item in group}
        zones = {item.zone for item in group}
        if postures & {"reference", "history"}:
            priority = "P4"
            recommendation = (
                "Keep one canonical source and treat other copies as pinned references "
                "with drift detection."
            )
        elif len(zones) == 1:
            priority = "P2"
            recommendation = (
                "Redirect consumers to one active artifact, then remove the duplicate "
                "after dependency checks."
            )
        else:
            priority = "P3"
            recommendation = (
                "Select the owner and replace secondary copies with generated or pinned "
                "conformance artifacts."
            )
        findings.append(
            _finding(
                priority=priority,
                category="exact_duplicate",
                subject=f"exact duplicate ({len(group)} artifacts)",
                owner_dimension=None,
                owner=None,
                recommendation=recommendation,
                artifacts=_refs(group),
            )
        )

    for group in repeated_stems(records):
        findings.append(
            _finding(
                priority="P4",
                category="repeated_concept_name",
                subject=f"repeated concept filename: {group[0].stem}",
                owner_dimension=None,
                owner=None,
                recommendation=(
                    "Confirm definition versus implementation versus projection; "
                    "consolidate competing definitions or rename by responsibility."
                ),
                artifacts=_refs(group),
            )
        )

    for rule in registry.concepts:
        authority = [
            record
            for record in records
            if record.posture == "authority"
            and rule.concept_id in record.concepts_identity
        ]
        wrong = [
            record for record in authority if record.owner_identity != rule.semantic_owner
        ]
        if wrong:
            findings.append(
                _finding(
                    priority="P0",
                    category="semantic_owner_conflict",
                    subject=rule.label,
                    owner_dimension="semantic",
                    owner=rule.semantic_owner,
                    recommendation=(
                        "Keep lifecycle, status and authority semantics in the semantic "
                        "owner; convert other artifacts to conformance or implementation "
                        "contracts."
                    ),
                    artifacts=_refs(wrong),
                )
            )

        implementation_identity = [
            record
            for record in records
            if rule.concept_id in record.concepts_identity
            and record.posture in {
                "implementation", "projection", "implementation_contract"
            }
            and (
                rule.implementation_owner is None
                or record.owner_identity == rule.implementation_owner
            )
        ]
        if len(implementation_identity) > rule.max_identity_implementations:
            findings.append(
                _finding(
                    priority="P2",
                    category="implementation_identity_fragmentation",
                    subject=(
                        f"{rule.label}: {len(implementation_identity)} "
                        "responsibility-named implementation artifacts"
                    ),
                    owner_dimension="implementation",
                    owner=rule.implementation_owner,
                    recommendation=(
                        "Consolidate behind one application service or adapter while "
                        "retaining only genuinely distinct invariants."
                    ),
                    artifacts=_refs(implementation_identity),
                )
            )

    incoming = incoming_import_counts(records)
    orphan_candidates = [
        record
        for record in records
        if record.posture == "implementation"
        and record.python_module
        and incoming.get((record.zone, record.python_module), 0) == 0
        and not record.routes
        and not record.has_main
        and not record.path.endswith("/__init__.py")
        and not any(
            part.lower() in ADAPTER_PARTS for part in Path(record.path).parts
        )
        and not record.path.startswith("scripts/")
    ]
    if orphan_candidates:
        findings.append(
            _finding(
                priority="P3",
                category="python_no_detected_consumer",
                subject=(
                    f"{len(orphan_candidates)} Python modules have no detected importer, "
                    "route or main entry"
                ),
                owner_dimension="implementation",
                owner="implementation",
                recommendation=(
                    "Verify dynamic loading, packaging entry points and deployment "
                    "references before merge or removal."
                ),
                artifacts=_refs(orphan_candidates),
            )
        )

    parse_errors = [record for record in records if record.parse_error]
    if parse_errors:
        findings.append(
            _finding(
                priority="P0",
                category="python_parse_error",
                subject=f"{len(parse_errors)} Python files could not be parsed",
                owner_dimension=None,
                owner=None,
                recommendation=(
                    "Correct syntax or explicitly exclude generated/non-Python fixtures."
                ),
                artifacts=_refs(parse_errors),
            )
        )

    return sorted(
        findings,
        key=lambda finding: (
            PRIORITY_ORDER[finding.priority],
            finding.category,
            finding.subject,
            finding.artifacts,
        ),
    )


def concept_matrix(
    records: list[Artifact],
    registry: OwnershipRegistry,
) -> dict[str, dict[str, object]]:
    matrix: dict[str, dict[str, object]] = {}
    for rule in registry.concepts:
        matches = [
            record
            for record in records
            if rule.concept_id in record.concepts_content
        ]
        counts: dict[str, Counter[str]] = defaultdict(Counter)
        for item in matches:
            counts[item.zone][item.posture] += 1
        matrix[rule.concept_id] = {
            "label": rule.label,
            "semantic_owner": rule.semantic_owner,
            "implementation_owner": rule.implementation_owner,
            "runtime_owner": rule.runtime_owner,
            "projection_owner": rule.projection_owner,
            "zones": {
                zone: dict(sorted(postures.items()))
                for zone, postures in sorted(counts.items())
            },
        }
    return matrix


def render_markdown(
    specs: list[ZoneSpec],
    records: list[Artifact],
    registry: OwnershipRegistry,
    findings: list[Finding] | None = None,
) -> str:
    findings = findings if findings is not None else build_findings(
        specs, records, registry
    )
    counts = Counter(finding.priority for finding in findings)
    matrix = concept_matrix(records, registry)
    lines = [
        "# Pantheon architecture convergence inventory",
        "",
        "> Report-only: a finding is not deletion proof or an authority decision.",
        "",
        "## Zones",
        "",
    ]
    lines.extend(
        f"- **{spec.name}** — {spec.role} — owner identity `{spec.owner_identity}` — `{spec.root}`" for spec in specs
    )
    lines.extend(
        [
            "",
            "## Registry",
            "",
            f"- ID: `{registry.registry_id}`",
            f"- Revision: **{registry.revision}**",
            f"- Governed concepts: **{len(registry.concepts)}**",
            "",
            "## Summary",
            "",
            f"- Architecture artifacts: **{len(records)}**",
            f"- Findings: **{len(findings)}**",
        ]
    )
    lines.extend(
        f"- {priority}: **{counts.get(priority, 0)}**"
        for priority in PRIORITY_ORDER
    )
    lines.extend(["", "## Prioritized findings", ""])
    if not findings:
        lines.append("None detected.")
    for finding in findings:
        owner = ""
        if finding.owner:
            owner = (
                f" — {finding.owner_dimension} owner `{finding.owner}`"
            )
        lines.append(
            f"- **{finding.priority} · {finding.category} · "
            f"{finding.finding_id}** — {finding.subject}{owner}"
        )
        lines.append(f"  - Recommendation: {finding.recommendation}")
        lines.extend(f"  - `{artifact}`" for artifact in finding.artifacts[:30])
        if len(finding.artifacts) > 30:
            lines.append(f"  - … {len(finding.artifacts) - 30} more")

    lines.extend(["", "## Concept ownership matrix", ""])
    for concept_id, entry in matrix.items():
        owners = [f"semantic `{entry['semantic_owner']}`"]
        if entry["implementation_owner"]:
            owners.append(f"implementation `{entry['implementation_owner']}`")
        if entry["runtime_owner"]:
            owners.append(f"runtime `{entry['runtime_owner']}`")
        if entry["projection_owner"]:
            owners.append(f"projection `{entry['projection_owner']}`")
        lines.append(
            f"- **{entry['label']}** (`{concept_id}`) — " + ", ".join(owners)
        )
        for zone, postures in entry["zones"].items():
            lines.append(
                f"  - `{zone}`: "
                + ", ".join(
                    f"{posture}={count}"
                    for posture, count in postures.items()
                )
            )

    lines.extend(
        [
            "",
            "## Decision vocabulary",
            "",
            "- `retain`: unique responsibility, correctly placed.",
            "- `simplify`: preserve semantics, reduce wrappers or repeated validation.",
            "- `merge`: converge competing active paths.",
            "- `move`: transfer responsibility to its owner.",
            "- `vendor/reference only`: pinned copy with drift detection.",
            "- `deprecate`: bounded transition with consumers and removal condition.",
            "- `remove`: no consumer, authority, deployment or compatibility obligation remains.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def json_payload(
    specs: list[ZoneSpec],
    records: list[Artifact],
    registry: OwnershipRegistry,
    findings: list[Finding],
) -> dict[str, object]:
    return {
        "registry": {
            "registry_id": registry.registry_id,
            "revision": registry.revision,
            "concepts": [asdict(rule) for rule in registry.concepts],
        },
        "zones": [
            {"name": spec.name, "role": spec.role, "owner_identity": spec.owner_identity, "root": str(spec.root)}
            for spec in specs
        ],
        "artifacts": [asdict(record) for record in records],
        "findings": [asdict(finding) for finding in findings],
        "concept_matrix": concept_matrix(records, registry),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--zone",
        action="append",
        type=zone_spec,
        required=True,
        help="repeat NAME=ROLE=OWNER=PATH",
    )
    parser.add_argument("--authority-registry", type=Path, required=True)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on-generation-names", action="store_true")
    parser.add_argument(
        "--fail-on-priority",
        action="append",
        choices=tuple(PRIORITY_ORDER),
    )
    args = parser.parse_args()

    registry = load_registry(args.authority_registry.resolve())
    records = build_inventory(args.zone, registry)
    findings = build_findings(args.zone, records, registry)
    rendered = (
        json.dumps(
            json_payload(args.zone, records, registry, findings),
            indent=2,
            sort_keys=True,
        )
        + "\n"
        if args.format == "json"
        else render_markdown(args.zone, records, registry, findings)
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    if args.fail_on_generation_names and any(
        record.generation_named or record.versioned_routes for record in records
    ):
        return 1
    fail_priorities = set(args.fail_on_priority or [])
    return 1 if fail_priorities & {finding.priority for finding in findings} else 0


if __name__ == "__main__":
    raise SystemExit(main())
