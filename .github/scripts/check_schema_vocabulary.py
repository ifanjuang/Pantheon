#!/usr/bin/env python3
"""Read-only governance check: one canonical vocabulary, one value set.

The E/V/K/C axes, the governed scope types and the Pantheon Roles are governance
vocabulary. They are declared once — in ``schemas/shared_axes.schema.yaml`` and
``schemas/shared_defs.schema.yaml`` — and then repeated inline across the
schemas that use them, because no root schema currently ``$ref``s the shared
files.

``check_axis_vocabulary.py`` catches axis-*letter* confusion (a C used where a K
belongs) by scanning text. It never compares the value *sets*, so a schema can
quietly ship a seventh approval level, drop a scope type or omit a canonical
Pantheon Role and stay green.

This check compares the sets. Any enum that substantially overlaps a canonical
vocabulary must equal it exactly. A deliberate divergence is not forbidden — it
must be declared in ``ACCEPTED_DIVERGENCES`` with the reason, so it is a
reviewed decision rather than a copy-paste accident.

The script is read-only. It reads schemas, compares vocabularies and reports.
"""

from __future__ import annotations

from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "schemas"

# Where each canonical vocabulary is declared. The declaration is the authority;
# every substantially-overlapping enum in the corpus must match it.
CANONICAL_SOURCES = {
    "approval (C axis)": ("shared_axes.schema.yaml", ("$defs", "approval", "enum")),
    "certainty (E axis)": ("shared_axes.schema.yaml", ("$defs", "certainty", "enum")),
    "verification (V axis)": ("shared_axes.schema.yaml", ("$defs", "verification", "enum")),
    "consequence (K axis)": ("shared_axes.schema.yaml", ("$defs", "consequence", "enum")),
    "scope_type": ("shared_defs.schema.yaml", ("$defs", "scope_type", "enum")),
    "Pantheon Role": ("shared_defs.schema.yaml", ("$defs", "pantheon_role", "enum")),
}

# An enum sharing at least this fraction of its values with a canonical set is
# treated as an instance of that vocabulary rather than an unrelated one.
OVERLAP_THRESHOLD = 0.6

# Divergences reviewed and accepted, keyed by "vocabulary|schema|json-pointer".
# Each entry states why the value set legitimately differs. Removing an entry
# turns the divergence back into a failure.
ACCEPTED_DIVERGENCES: dict[str, str] = {
    "approval (C axis)|module_manifest.schema.yaml|/properties/governance/properties/"
    "approval_behavior/enum": (
        "Declares the approval a module requires, and adds 'none' for a module that "
        "requires no approval at all. Overlaps C0 ('read-only or analytical work', "
        "APPROVALS.md) and is a candidate for reconciliation under the vocabulary "
        "convergence work; recorded here so it cannot spread silently."
    ),
    "scope_type|register_candidate.schema.yaml|/properties/proposed_durability/enum": (
        "Expresses how long a Register Candidate should persist, not where it applies, "
        "and reuses the scope vocabulary with 'session' spelled 'session_only'. The same "
        "file's /properties/scope/properties/scope_type uses the canonical spelling, so "
        "the two differ by one token inside one schema. Reconciling durability and scope "
        "is a governance decision, not a rename; recorded until it is taken."
    ),
}


def load(rel: str) -> dict:
    return yaml.safe_load((SCHEMA_ROOT / rel).read_text(encoding="utf-8"))


def dig(document: dict, path: tuple[str, ...]):
    node = document
    for key in path:
        node = node[key]
    return node


def canonical_vocabularies() -> dict[str, tuple[str, ...]]:
    resolved: dict[str, tuple[str, ...]] = {}
    for name, (rel, path) in CANONICAL_SOURCES.items():
        try:
            resolved[name] = tuple(str(value) for value in dig(load(rel), path))
        except (OSError, KeyError, TypeError) as error:
            raise SystemExit(f"canonical vocabulary '{name}' is unreadable in {rel}: {error}")
    return resolved


def iter_enums(node, pointer: str = ""):
    """Yield (json-pointer, values) for every enum in a schema document."""
    if isinstance(node, dict):
        if isinstance(node.get("enum"), list):
            yield f"{pointer}/enum", tuple(str(value) for value in node["enum"])
        for key, value in node.items():
            yield from iter_enums(value, f"{pointer}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from iter_enums(value, f"{pointer}/{index}")


def schema_files() -> list[Path]:
    return sorted(
        path
        for path in SCHEMA_ROOT.rglob("*.yaml")
        if "examples" not in path.relative_to(SCHEMA_ROOT).parts
    )


def overlap(values: tuple[str, ...], canonical: tuple[str, ...]) -> float:
    left, right = set(values), set(canonical)
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def main() -> int:
    canonical = canonical_vocabularies()
    problems: list[str] = []
    matched = 0
    accepted = 0

    for path in schema_files():
        rel = path.relative_to(SCHEMA_ROOT).as_posix()
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            problems.append(f"{rel}: unreadable schema: {error}")
            continue

        for pointer, values in iter_enums(document):
            for name, expected in canonical.items():
                if tuple(values) == expected:
                    matched += 1
                    break
                if overlap(values, expected) < OVERLAP_THRESHOLD:
                    continue

                key = f"{name}|{rel}|{pointer}"
                if key in ACCEPTED_DIVERGENCES:
                    accepted += 1
                    break

                extra = sorted(set(values) - set(expected))
                missing = sorted(set(expected) - set(values))
                detail = []
                if extra:
                    detail.append(f"adds {extra}")
                if missing:
                    detail.append(f"drops {missing}")
                problems.append(
                    f"{rel}{pointer}: diverges from the canonical {name} "
                    f"({', '.join(detail)}). Align it, or declare the divergence in "
                    f"ACCEPTED_DIVERGENCES with its reason."
                )
                break

    if problems:
        print("Schema vocabulary check failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1

    print(
        f"OK: {matched} enum(s) match a canonical vocabulary, "
        f"{accepted} reviewed divergence(s) declared, across "
        f"{len(schema_files())} schema files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
