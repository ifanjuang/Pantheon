"""Read-only doctor checks.

Mirrors the governance CI so Hermes, OpenWebUI or the dashboard can ask
"are the checks green?" without running CI. The doctor verifies, cites and
flags; it never edits, fixes or decides.
"""

from __future__ import annotations

import re
from pathlib import Path

from .repo import find_repo_root

try:  # optional; the doctor degrades gracefully without them
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

try:
    import jsonschema  # type: ignore
except Exception:  # pragma: no cover
    jsonschema = None

MANDATORY_FILES = [
    "README.md",
    "CLAUDE.md",
    "VERSION",
    "CHANGELOG.md",
    "docs/governance/README.md",
    "docs/governance/STATUS.md",
    "docs/governance/ROADMAP.md",
    "docs/governance/GLOSSARY.md",
    "docs/governance/AUTHORITY_INDEX.md",
    "docs/governance/MODULES.md",
    "docs/governance/MEMORY.md",
    "docs/governance/APPROVALS.md",
    "docs/governance/TASK_CONTRACTS.md",
    "docs/governance/EVIDENCE_PACK.md",
]

FORBIDDEN_PHRASES = [
    "Pantheon executes",
    "Pantheon Agent Runtime",
    "Pantheon tool runtime",
    "automatic memory promotion",
    "hidden workflow runtime",
    "provider router",
    "scheduler",
    "queue",
]

# Same negation grammar as .github/workflows/governance-ci.yml.
NEGATION = re.compile(
    r"\b("
    r"must not|do not|does not|did not|is not|are not|will not|would not|"
    r"cannot|can ?not|may not|should not|shall not|must never|never|none of|"
    r"without|forbidden|prohibited|refus(e|es|ed|al|ing)?|reject(s|ed|ion|ing)?|disallowed|denied|excluded|"
    r"incompatible|"
    r"intentionally absent|voluntarily not|not implemented|not migrated|"
    r"non implémenté|absent|avoid(s|ed|ing)?|"
    r"belongs outside|outside pantheon|on the hermes side|"
    r"stays? on the|remains? on the|stays? outside|remains? outside|"
    r"external (execution|runtime|tool|action|capability|capabilities)|"
    r"runtime state|boundary rule|stub present|"
    r"hermes-side|hermes side|"
    r"risky capabilities|risks?:|drift|"
    r"requires? (a |an )?task contract|task contract requirement|requires? approval|"
    r"remove(s|d|al)?|reformulate|transform or remove|"
    r"\bno\b|"
    r"governance[- ]only|governance-first|read[- ]only|policy[- ]gated|"
    r"not (recreate|implement|introduce|expose|grant|run|execute|"
    r"approve|own|migrate|install|schedule|queue|route|promote|"
    r"a |an |another |the )"
    r")",
    re.IGNORECASE,
)

QUEUE_OK = re.compile(
    r"review[- ]?queue|decision queue|impact[- ]?queue|"
    r"queue of governed decisions|governed (review|decision) queue",
    re.IGNORECASE,
)

RETIRED_VOCABULARY = re.compile(r"Canonical Memory|Memory Candidate")
RETIRED_OK = re.compile(
    r"formerly|former name|in place of|replaces the former|the former term",
    re.IGNORECASE,
)

CHECK_STATUSES = {"pass", "fail", "not_run", "capability_gap"}


def _result(
    check: str,
    status: str,
    *,
    mandatory: bool = True,
    message: str,
    expected: int = 0,
    evaluated: int = 0,
    passed: int = 0,
    failed: int = 0,
    not_run: int = 0,
    **details: object,
) -> dict:
    """Return one stable, explicit Doctor check result.

    ``ok`` is retained for existing MCP consumers, but is derived exclusively
    from the explicit status. Informational checks remain visible without
    affecting the aggregate result.
    """
    if status not in CHECK_STATUSES:
        raise ValueError(f"unknown Doctor check status: {status}")
    return {
        "check": check,
        "status": status,
        "mandatory": mandatory,
        "informational": not mandatory,
        "ok": status == "pass",
        "message": message,
        "counts": {
            "expected": expected,
            "evaluated": evaluated,
            "passed": passed,
            "failed": failed,
            "not_run": not_run,
        },
        **details,
    }


def _section_context(lines: list[str], idx: int) -> str:
    start = 0
    for i in range(idx, -1, -1):
        if re.match(r"^#{1,6}\s", lines[i]):
            start = i
            break
    return "\n".join(lines[start : idx + 1])


def check_mandatory_files(root: Path | None = None) -> dict:
    root = root or find_repo_root()
    missing = [f for f in MANDATORY_FILES if not (root / f).is_file()]
    present = len(MANDATORY_FILES) - len(missing)
    return _result(
        "mandatory_files",
        "pass" if not missing else "fail",
        message=(
            "All mandatory governance files are present."
            if not missing
            else f"{len(missing)} mandatory governance file(s) are missing."
        ),
        expected=len(MANDATORY_FILES),
        evaluated=len(MANDATORY_FILES),
        passed=present,
        failed=len(missing),
        missing=missing,
    )


def check_runtime_phrases(root: Path | None = None) -> dict:
    root = root or find_repo_root()
    governance_dir = root / "docs" / "governance"
    if not governance_dir.is_dir():
        return _result(
            "runtime_phrases",
            "not_run",
            message="Required docs/governance corpus is missing.",
            expected=1,
            not_run=1,
            violations=[],
        )

    documents = sorted(governance_dir.rglob("*.md"))
    documents = [md for md in documents if "reference_reviews/" not in md.as_posix()]
    if not documents:
        return _result(
            "runtime_phrases",
            "not_run",
            message="Required docs/governance corpus contains no Markdown documents.",
            expected=1,
            not_run=1,
            violations=[],
        )

    failures = []
    read_failures = []
    evaluated = 0
    for md in documents:
        try:
            lines = md.read_text(encoding="utf-8").splitlines()
        except Exception as exc:
            read_failures.append(
                {"file": str(md.relative_to(root)), "message": f"read failed: {exc}"}
            )
            continue
        evaluated += 1
        head = "\n".join(lines[:3])
        for i, line in enumerate(lines):
            for phrase in FORBIDDEN_PHRASES:
                if re.search(r"\b" + re.escape(phrase) + r"\b", line, re.IGNORECASE):
                    ctx = _section_context(lines, i)
                    if NEGATION.search(ctx):
                        continue
                    if phrase == "queue" and (
                        QUEUE_OK.search(line) or QUEUE_OK.search(ctx) or QUEUE_OK.search(head)
                    ):
                        continue
                    failures.append(
                        {"file": str(md.relative_to(root)), "line": i + 1, "phrase": phrase}
                    )
    all_failures = [*read_failures, *failures]
    failed_documents = {item["file"] for item in all_failures}
    return _result(
        "runtime_phrases",
        "pass" if not all_failures and evaluated == len(documents) else "fail",
        message=(
            "Governance runtime-language corpus was fully evaluated."
            if not all_failures and evaluated == len(documents)
            else "Governance runtime-language corpus contains violations or unreadable files."
        ),
        expected=len(documents),
        evaluated=len(documents),
        passed=len(documents) - len(failed_documents),
        failed=len(failed_documents),
        violations=all_failures,
    )


def check_retired_vocabulary(root: Path | None = None) -> dict:
    """Full-corpus scan for retired Registre Probatoire vocabulary.

    Informational: the CI guards new diffs; the doctor reports the remaining
    legacy occurrences (the issue #90 worklist). It never blocks.
    """
    root = root or find_repo_root()
    docs_dir = root / "docs"
    if not docs_dir.is_dir():
        return _result(
            "retired_vocabulary",
            "not_run",
            mandatory=False,
            message="Optional docs corpus is missing; vocabulary scan did not run.",
            expected=1,
            not_run=1,
            remaining_occurrences=0,
            occurrences=[],
        )
    documents = sorted(docs_dir.rglob("*.md"))
    if not documents:
        return _result(
            "retired_vocabulary",
            "not_run",
            mandatory=False,
            message="Optional docs corpus contains no Markdown documents.",
            expected=1,
            not_run=1,
            remaining_occurrences=0,
            occurrences=[],
        )
    hits = []
    read_failures = []
    for md in documents:
        try:
            lines = md.read_text(encoding="utf-8").splitlines()
        except Exception as exc:
            read_failures.append(
                {"file": str(md.relative_to(root)), "message": f"read failed: {exc}"}
            )
            continue
        for i, line in enumerate(lines):
            if RETIRED_VOCABULARY.search(line) and not RETIRED_OK.search(line):
                hits.append({"file": str(md.relative_to(root)), "line": i + 1})
    status = "fail" if read_failures else "pass"
    return _result(
        "retired_vocabulary",
        status,
        mandatory=False,
        message=(
            f"Vocabulary worklist contains {len(hits)} occurrence(s)."
            if not read_failures
            else "Vocabulary worklist could not read the full docs corpus."
        ),
        expected=len(documents),
        evaluated=len(documents),
        passed=len(documents) - len(read_failures),
        failed=len(read_failures),
        remaining_occurrences=len(hits),
        occurrences=hits,
        read_failures=read_failures,
    )


def evaluate_impact_review(data: dict) -> list[str]:
    """Apply the cascade rule to one impact_review instance.

    The rule is declarative and read-only: it never edits the review or the
    targets. It flags, it does not fix.

    - A critical-severity impact must route to arbitration. It must never be
      silently downgraded (supersede/archive/revoke/obsolete) in place.
    - A resolved review must carry a recorded decision for every target.
    """
    violations: list[str] = []
    impacted = data.get("impacted") or []
    for item in impacted:
        if not isinstance(item, dict):
            continue
        target = item.get("target_id", "?")
        severity = item.get("severity", "none")
        impact_status = item.get("impact_status", "")
        if severity == "critical" and impact_status != "critical_arbitration":
            violations.append(
                f"critical impact on {target} must be 'critical_arbitration', "
                f"found '{impact_status}' (no silent downgrade)"
            )
    if data.get("status") == "resolved":
        for item in impacted:
            if isinstance(item, dict) and item.get("decision", "pending") == "pending":
                violations.append(
                    f"impact review resolved while {item.get('target_id', '?')} "
                    f"decision is still pending"
                )
    return violations


def check_cascade_rule(root: Path | None = None) -> dict:
    """Validate impact_review instances against the schema and the cascade rule.

    Read-only. Scans known example/instance locations, validates each against
    `schemas/impact_review.schema.yaml` when jsonschema is available, then
    applies the declarative cascade rule.
    """
    root = root or find_repo_root()
    if yaml is None:
        return _result(
            "cascade_rule",
            "capability_gap",
            message="Required validator PyYAML is unavailable.",
            expected=1,
            not_run=1,
            violations=[],
        )
    if jsonschema is None:
        return _result(
            "cascade_rule",
            "capability_gap",
            message="Required validator jsonschema is unavailable.",
            expected=1,
            not_run=1,
            violations=[],
        )

    schema_path = root / "schemas" / "impact_review.schema.yaml"
    if not schema_path.is_file():
        return _result(
            "cascade_rule",
            "not_run",
            message="Required impact-review schema is missing.",
            expected=1,
            not_run=1,
            violations=[],
        )
    try:
        schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
    except Exception as exc:
        return _result(
            "cascade_rule",
            "fail",
            message="Impact-review schema is unreadable or invalid.",
            expected=1,
            evaluated=1,
            failed=1,
            violations=[{"file": str(schema_path.relative_to(root)), "message": str(exc)}],
        )

    scan_dirs = [root / "schemas" / "examples", root / "docs" / "examples"]
    existing_dirs = [directory for directory in scan_dirs if directory.is_dir()]
    if not existing_dirs:
        return _result(
            "cascade_rule",
            "not_run",
            message="No required example corpus is available for cascade evaluation.",
            expected=1,
            not_run=1,
            violations=[],
        )

    violations: list[dict] = []
    checked = 0
    parse_failures = 0
    for directory in existing_dirs:
        for path in sorted(directory.rglob("*.y*ml")):
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception as exc:
                parse_failures += 1
                violations.append(
                    {"file": str(path.relative_to(root)), "message": f"YAML parse failed: {exc}"}
                )
                continue
            if not isinstance(data, dict) or "impact_review_id" not in data:
                continue
            checked += 1
            rel = str(path.relative_to(root))
            try:
                jsonschema.validate(instance=data, schema=schema)
            except Exception as exc:  # validation error
                violations.append({"file": rel, "message": f"schema invalid: {getattr(exc, 'message', str(exc))}"})
                continue
            for message in evaluate_impact_review(data):
                violations.append({"file": rel, "message": message})

    if checked == 0 and parse_failures == 0:
        return _result(
            "cascade_rule",
            "not_run",
            message="No impact-review instance was discovered in the required corpus.",
            expected=1,
            not_run=1,
            instances_checked=0,
            violations=[],
        )
    failed_files = {item["file"] for item in violations}
    expected = checked + parse_failures
    return _result(
        "cascade_rule",
        "pass" if not violations else "fail",
        message=(
            f"{checked} impact-review instance(s) passed schema and cascade validation."
            if not violations
            else "Cascade evaluation found invalid or unreadable content."
        ),
        expected=expected,
        evaluated=expected,
        passed=expected - len(failed_files),
        failed=len(failed_files),
        instances_checked=checked,
        violations=violations,
    )


REGISTER_KEY_TO_SCHEMA = {
    "candidate_id": "register_candidate.schema.yaml",
    "link_id": "register_link.schema.yaml",
    "impact_review_id": "impact_review.schema.yaml",
}

VERTICAL_KEY_TO_SCHEMA = {
    "contract_id": "task_contract.schema.yaml",
    "workflow_id": "workflow_manifest.schema.yaml",
    "decision_id": "policy_decision.schema.yaml",
    "answer_id": "answer_status.schema.yaml",
    "candidate_id": "register_candidate.schema.yaml",
    "evidence_pack_id": "evidence_pack.schema.yaml",
}


def check_register_instances(root: Path | None = None) -> dict:
    """Validate Registre Probatoire instances as a coherent dossier.

    Read-only. For each instance under ``docs/examples/cascade_register/`` it
    validates against the matching schema, verifies ``link_ids`` referential
    integrity (a candidate may only reference a known ``register_link``), and
    applies the cascade rule via :func:`evaluate_impact_review`.

    This is the single source of truth reused by the governance CI script. It
    flags, cites and reports; it never edits, fixes or decides.
    """
    root = root or find_repo_root()
    if yaml is None:
        return _result(
            "register_instances",
            "capability_gap",
            message="Required validator PyYAML is unavailable.",
            expected=1,
            not_run=1,
            violations=[],
        )
    if jsonschema is None:
        return _result(
            "register_instances",
            "capability_gap",
            message="Required validator jsonschema is unavailable.",
            expected=1,
            not_run=1,
            violations=[],
        )

    instances_dir = root / "docs" / "examples" / "cascade_register"
    if not instances_dir.is_dir():
        return _result(
            "register_instances",
            "not_run",
            message="Required cascade-register instance directory is missing.",
            expected=1,
            not_run=1,
            instances_checked=0,
            violations=[],
        )
    instance_paths = sorted(instances_dir.rglob("*.y*ml"))
    if not instance_paths:
        return _result(
            "register_instances",
            "not_run",
            message="Required cascade-register corpus contains no YAML instances.",
            expected=1,
            not_run=1,
            instances_checked=0,
            violations=[],
        )

    schemas: dict[str, dict] = {}
    schema_violations: list[dict] = []
    missing_schemas: list[str] = []
    for key, name in REGISTER_KEY_TO_SCHEMA.items():
        schema_path = root / "schemas" / name
        if not schema_path.is_file():
            missing_schemas.append(str(schema_path.relative_to(root)))
            continue
        try:
            schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator.check_schema(schema)
            schemas[key] = schema
        except Exception as exc:
            schema_violations.append(
                {"file": str(schema_path.relative_to(root)), "message": f"schema invalid: {exc}"}
            )
    if missing_schemas:
        return _result(
            "register_instances",
            "not_run",
            message="One or more required register schemas are missing.",
            expected=len(REGISTER_KEY_TO_SCHEMA),
            evaluated=len(schemas),
            passed=len(schemas),
            not_run=len(missing_schemas),
            instances_checked=0,
            missing_schemas=missing_schemas,
            violations=[],
        )
    if schema_violations:
        return _result(
            "register_instances",
            "fail",
            message="One or more required register schemas are invalid.",
            expected=len(REGISTER_KEY_TO_SCHEMA),
            evaluated=len(REGISTER_KEY_TO_SCHEMA),
            passed=len(schemas),
            failed=len(schema_violations),
            instances_checked=0,
            violations=schema_violations,
        )

    violations: list[dict] = []
    checked = 0
    known_link_ids: set[str] = set()
    candidate_link_refs: list[tuple[str, str]] = []

    for path in instance_paths:
        rel = str(path.relative_to(root))
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            violations.append({"file": rel, "message": f"YAML parse failed: {exc}"})
            continue
        if not isinstance(data, dict):
            violations.append({"file": rel, "message": "instance must be a YAML mapping"})
            continue
        key = next((k for k in REGISTER_KEY_TO_SCHEMA if k in data), None)
        if key is None:
            violations.append({"file": rel, "message": "instance has no recognized register identity key"})
            continue
        checked += 1

        try:
            jsonschema.validate(instance=data, schema=schemas[key])
        except Exception as exc:  # validation error
            violations.append(
                {"file": rel, "message": f"schema invalid: {getattr(exc, 'message', str(exc))}"}
            )
            continue

        if key == "link_id":
            known_link_ids.add(data["link_id"])
        elif key == "candidate_id":
            for ref in data.get("link_ids", []):
                candidate_link_refs.append((rel, ref))
        elif key == "impact_review_id":
            for message in evaluate_impact_review(data):
                violations.append({"file": rel, "message": message})

    for rel, ref in candidate_link_refs:
        if ref not in known_link_ids:
            violations.append({"file": rel, "message": f"link_ids references unknown register_link '{ref}'"})

    status = "fail" if violations else ("pass" if checked > 0 else "not_run")
    failed_files = {item["file"] for item in violations}
    return _result(
        "register_instances",
        status,
        message=(
            f"{checked} register instance(s) passed schema and coherence validation."
            if status == "pass"
            else (
                "No register instance was successfully evaluated."
                if status == "not_run"
                else "Register-instance validation found invalid or incoherent content."
            )
        ),
        expected=len(instance_paths),
        evaluated=len(instance_paths),
        passed=len(instance_paths) - len(failed_files),
        failed=len(failed_files),
        instances_checked=checked,
        violations=violations,
    )


def check_vertical_slice(root: Path | None = None) -> dict:
    """Validate the architecture_devis_reprise governed vertical slice.

    Read-only. For each instance under ``docs/examples/vertical_devis_reprise/``
    it validates against the matching spine schema (task contract, forged
    workflow manifest with its two gates, evidence pack, answer status, register
    candidate, gate decision) and checks a few end-to-end coherence invariants:
    the register candidate is scoped to a project (evidence log by project); a
    required post-execution evidence gate carries verification (V) and certainty
    (E); the answer status references the dossier's evidence pack and register
    candidate. It proves the governance loop is coherent end-to-end; the runtime
    execution (Hermes, OpenWebUI) still lives outside. It flags and cites; it
    never edits, fixes, executes or decides.
    """
    root = root or find_repo_root()
    if yaml is None:
        return _result(
            "vertical_slice",
            "capability_gap",
            message="Required validator PyYAML is unavailable.",
            expected=1,
            not_run=1,
            violations=[],
        )
    if jsonschema is None:
        return _result(
            "vertical_slice",
            "capability_gap",
            message="Required validator jsonschema is unavailable.",
            expected=1,
            not_run=1,
            violations=[],
        )

    instances_dir = root / "docs" / "examples" / "vertical_devis_reprise"
    if not instances_dir.is_dir():
        return _result(
            "vertical_slice",
            "not_run",
            message="Required vertical-slice instance directory is missing.",
            expected=1,
            not_run=1,
            instances_checked=0,
            violations=[],
        )
    instance_paths = sorted(instances_dir.rglob("*.y*ml"))
    if not instance_paths:
        return _result(
            "vertical_slice",
            "not_run",
            message="Required vertical-slice corpus contains no YAML instances.",
            expected=1,
            not_run=1,
            instances_checked=0,
            violations=[],
        )

    schemas: dict[str, dict] = {}
    schema_violations: list[dict] = []
    missing_schemas: list[str] = []
    for key, name in VERTICAL_KEY_TO_SCHEMA.items():
        schema_path = root / "schemas" / name
        if not schema_path.is_file():
            missing_schemas.append(str(schema_path.relative_to(root)))
            continue
        try:
            schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator.check_schema(schema)
            schemas[key] = schema
        except Exception as exc:
            schema_violations.append(
                {"file": str(schema_path.relative_to(root)), "message": f"schema invalid: {exc}"}
            )
    if missing_schemas:
        return _result(
            "vertical_slice",
            "not_run",
            message="One or more required vertical-slice schemas are missing.",
            expected=len(VERTICAL_KEY_TO_SCHEMA),
            evaluated=len(schemas),
            passed=len(schemas),
            not_run=len(missing_schemas),
            instances_checked=0,
            missing_schemas=missing_schemas,
            violations=[],
        )
    if schema_violations:
        return _result(
            "vertical_slice",
            "fail",
            message="One or more required vertical-slice schemas are invalid.",
            expected=len(VERTICAL_KEY_TO_SCHEMA),
            evaluated=len(VERTICAL_KEY_TO_SCHEMA),
            passed=len(schemas),
            failed=len(schema_violations),
            instances_checked=0,
            violations=schema_violations,
        )

    violations: list[dict] = []
    checked = 0
    docs: dict[str, dict] = {}

    for path in instance_paths:
        rel = str(path.relative_to(root))
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            violations.append({"file": rel, "message": f"YAML parse failed: {exc}"})
            continue
        if not isinstance(data, dict):
            violations.append({"file": rel, "message": "instance must be a YAML mapping"})
            continue
        key = next((k for k in VERTICAL_KEY_TO_SCHEMA if k in data), None)
        if key is None:
            violations.append({"file": rel, "message": "instance has no recognized vertical-slice identity key"})
            continue
        checked += 1
        docs[key] = data
        try:
            jsonschema.validate(instance=data, schema=schemas[key])
        except Exception as exc:
            violations.append(
                {"file": rel, "message": f"schema invalid: {getattr(exc, 'message', str(exc))}"}
            )

    register = docs.get("candidate_id")
    if register is not None and register.get("scope", {}).get("scope_type") != "project":
        violations.append(
            {"file": "register_candidate", "message": "vertical-slice register candidate must be scoped to a project (evidence log by project)"}
        )

    workflow = docs.get("workflow_id")
    answer = docs.get("answer_id")
    gate = (workflow or {}).get("governed_composition", {}).get("gates", {}).get("post_execution_evidence", {})
    if gate.get("required") is True and answer is not None:
        if not answer.get("verification_level"):
            violations.append({"file": "answer_status", "message": "required evidence gate but answer status omits verification (V)"})
        if not answer.get("certainty_support"):
            violations.append({"file": "answer_status", "message": "required evidence gate but answer status omits certainty (E)"})

    evidence = docs.get("evidence_pack_id")
    if answer is not None and evidence is not None:
        if evidence.get("evidence_pack_id") not in (answer.get("evidence_refs") or []):
            violations.append({"file": "answer_status", "message": "answer status does not reference the dossier evidence pack"})
    if answer is not None and register is not None:
        if register.get("candidate_id") not in (answer.get("register_refs") or []):
            violations.append({"file": "answer_status", "message": "answer status does not reference the dossier register candidate"})

    missing_kinds = sorted(set(VERTICAL_KEY_TO_SCHEMA) - set(docs))
    if missing_kinds:
        violations.append(
            {"file": str(instances_dir.relative_to(root)), "message": f"required instance kinds missing: {', '.join(missing_kinds)}"}
        )

    status = "fail" if violations else ("pass" if checked > 0 else "not_run")
    failed_files = {item["file"] for item in violations if item["file"] != str(instances_dir.relative_to(root))}
    return _result(
        "vertical_slice",
        status,
        message=(
            f"{checked} vertical-slice instance(s) passed schema and coherence validation."
            if status == "pass"
            else (
                "No vertical-slice instance was successfully evaluated."
                if status == "not_run"
                else "Vertical-slice validation found missing, invalid or incoherent content."
            )
        ),
        expected=len(instance_paths) + len(missing_kinds),
        evaluated=len(instance_paths),
        passed=len(instance_paths) - len(failed_files),
        failed=len(failed_files),
        not_run=len(missing_kinds),
        instances_checked=checked,
        missing_instance_kinds=missing_kinds,
        violations=violations,
    )


def run_all(root: Path | None = None) -> dict:
    root = root or find_repo_root()
    checks = [
        check_mandatory_files(root),
        check_runtime_phrases(root),
        check_retired_vocabulary(root),
        check_cascade_rule(root),
        check_register_instances(root),
        check_vertical_slice(root),
    ]
    blocking = [c for c in checks if c["mandatory"]]
    status_counts = {status: 0 for status in CHECK_STATUSES}
    for check in checks:
        status_counts[check["status"]] += 1
    item_counts = {
        key: sum(check["counts"][key] for check in checks)
        for key in ("expected", "evaluated", "passed", "failed", "not_run")
    }
    return {
        "ok": all(c["status"] == "pass" for c in blocking),
        "status": "pass" if all(c["status"] == "pass" for c in blocking) else "fail",
        "summary": {
            "checks": {
                "expected": len(checks),
                "evaluated": sum(c["status"] in {"pass", "fail"} for c in checks),
                "passed": status_counts["pass"],
                "failed": status_counts["fail"],
                "not_run": status_counts["not_run"],
                "capability_gap": status_counts["capability_gap"],
                "mandatory": len(blocking),
            },
            "items": item_counts,
        },
        "checks": checks,
        "authority_note": (
            "Doctor checks verify and cite; they do not edit, fix or decide. "
            "A healthy result requires every mandatory check to run and pass. "
            "Informational checks report state without blocking."
        ),
    }
