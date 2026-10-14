#!/usr/bin/env python3
"""Every property CLAUDE.md asserts in the present tense names a control.

CLAUDE.md states properties as facts about the repository. Two blocks state them
in a form a machine can enumerate: the `!=` invariants under *Core
non-equivalences*, and the list of components the governance core must not
recreate under *Non-negotiable boundaries*.

Asserting a property is not holding it. This check requires each asserted
property to name the control that fails when it stops being true, and refuses
three ways of losing that link:

    a property asserted in CLAUDE.md with no entry here
    an entry whose property is no longer asserted in CLAUDE.md
    an entry naming a control that does not exist

What it deliberately does not do is take the registry's word for how strong a
control is. Each entry declares a binding, and the check reads the control's own
source to see whether that declaration is supportable:

    behavioural   exercises executable code, or reads source structurally
    schema        validates instances against a governed contract
    documentary   reads prose and checks that the wording is still there
    none          nothing controls this property

`documentary` is the floor and is always accepted; a documentary control fails
when the sentence changes, not when the property stops being true, and saying so
is the point of the report. Claiming `behavioural` or `schema` requires evidence
in the control's source, so the declaration cannot be inflated. The count of
uncontrolled properties is capped and may not grow silently.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
DOCTRINE = ROOT / "CLAUDE.md"
REGISTRY = ROOT / ".github" / "asserted-properties.json"

BINDINGS = ("behavioural", "schema", "documentary", "none")

IMPLEMENTATION_PACKAGES = {"mvp_vertical", "pantheon_mcp"}
SCHEMA_LIBRARIES = {"jsonschema"}


# ---------------------------------------------------------------------------
# What CLAUDE.md asserts
# ---------------------------------------------------------------------------

_NON_EQUIVALENCE = re.compile(r"^([^\n`|]+?)\s*!=\s*([^\n`|]+)$", re.M)


def asserted_properties(text: str) -> dict[str, str]:
    """Claim -> claim class, for the two enumerable blocks."""
    claims: dict[str, str] = {}

    for match in _NON_EQUIVALENCE.finditer(text):
        claims[re.sub(r"\s+", " ", match.group(0).strip())] = "non_equivalence"

    _, _, after = text.partition("## Non-negotiable boundaries")
    section, _, _ = after.partition("The in-repo zones")
    for match in re.finditer(r"^- (.+?)\.?;?$", section, re.M):
        claims[match.group(1).strip().rstrip(";.")] = "forbidden_component"

    return claims


# ---------------------------------------------------------------------------
# What a control actually does
# ---------------------------------------------------------------------------


def control_signals(path: Path) -> set[str]:
    """Read the control's source to see what kind of evidence it can produce."""
    signals: set[str] = set()
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return signals

    if path.suffix == ".py":
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            tree = None
        if tree is not None:
            modules: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules.add(node.module.split(".")[0])
            if modules & IMPLEMENTATION_PACKAGES:
                signals.add("imports_implementation")
            if modules & SCHEMA_LIBRARIES:
                signals.add("validates_schema")
            if "ast" in modules or "*.py" in source or 'rglob("*.py")' in source:
                signals.add("reads_source")
        if "spec_from_file_location" in source:
            signals.add("imports_implementation")

    if ".md" in source or "docs/governance" in source:
        signals.add("reads_prose")

    return signals


def supportable(binding: str, signals: set[str]) -> bool:
    """Whether the control's source supports the strength the entry declares."""
    if binding == "behavioural":
        return bool(signals & {"imports_implementation", "reads_source"})
    if binding == "schema":
        return "validates_schema" in signals
    return True


def defines(path: Path, name: str) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError):
        return False
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
        for node in ast.walk(tree)
    )


# ---------------------------------------------------------------------------
# The check
# ---------------------------------------------------------------------------


def verify(claims: dict[str, str], registry: dict) -> tuple[list[str], list[dict]]:
    errors: list[str] = []
    entries = registry.get("properties", [])
    rows: list[dict] = []

    declared = {str(entry.get("claim", "")) for entry in entries}
    for claim in sorted(set(claims) - declared):
        errors.append(
            f"CLAUDE.md asserts {claim!r} and nothing here names a control for it"
        )
    for claim in sorted(declared - set(claims)):
        errors.append(
            f"{claim!r} has an entry here but CLAUDE.md no longer asserts it"
        )

    for entry in entries:
        claim = str(entry.get("claim", ""))
        binding = str(entry.get("binding", ""))
        if binding not in BINDINGS:
            errors.append(f"{claim!r}: binding must be one of {', '.join(BINDINGS)}")
            continue

        controls = entry.get("controls", [])
        if binding == "none":
            if controls:
                errors.append(f"{claim!r}: declared uncontrolled but names controls")
            if not entry.get("why"):
                errors.append(f"{claim!r}: an uncontrolled property must say why")
            rows.append({"claim": claim, "kind": claims.get(claim, "?"), "binding": binding, "controls": []})
            continue

        if not controls:
            errors.append(f"{claim!r}: binding {binding!r} names no control")
            continue

        signals: set[str] = set()
        for control in controls:
            relative = str(control.get("path", ""))
            path = ROOT / relative
            if not path.is_file():
                errors.append(f"{claim!r}: control does not exist: {relative}")
                continue
            name = control.get("name")
            if name and not defines(path, str(name)):
                errors.append(f"{claim!r}: {relative} does not define {name}")
                continue
            signals |= control_signals(path)

        if not supportable(binding, signals):
            errors.append(
                f"{claim!r}: declared {binding!r}, but its controls show no such "
                f"evidence in their source (observed: {sorted(signals) or 'nothing'})"
            )

        rows.append(
            {
                "claim": claim,
                "kind": claims.get(claim, "?"),
                "binding": binding,
                "controls": [str(control.get("path", "")) for control in controls],
            }
        )

    ceiling = registry.get("uncontrolled_ceiling")
    uncontrolled = [row for row in rows if row["binding"] == "none"]
    if isinstance(ceiling, int) and len(uncontrolled) > ceiling:
        errors.append(
            f"{len(uncontrolled)} uncontrolled properties exceed the declared "
            f"ceiling of {ceiling}; lower the debt or move the ceiling deliberately"
        )

    return errors, rows


def render(rows: list[dict], ceiling: int | None) -> str:
    counts = {binding: 0 for binding in BINDINGS}
    for row in rows:
        counts[row["binding"]] += 1

    out = [
        "# Asserted properties and their controls",
        "",
        f"{len(rows)} properties asserted in the present tense in `CLAUDE.md`.",
        "",
        f"- behavioural: **{counts['behavioural']}**",
        f"- schema: **{counts['schema']}**",
        f"- documentary: **{counts['documentary']}**",
        f"- uncontrolled: **{counts['none']}**"
        + (f" (ceiling {ceiling})" if ceiling is not None else ""),
        "",
        "A documentary control fails when the wording changes, not when the "
        "property stops being true. The split is the point of this report: it "
        "says where the doctrine is held by a contract and where it is held by "
        "a sentence.",
        "",
        "| Property | Class | Binding | Controls |",
        "|---|---|---|---|",
    ]
    for row in sorted(rows, key=lambda item: (item["kind"], item["claim"])):
        controls = ", ".join(f"`{item}`" for item in row["controls"]) or "—"
        out.append(
            f"| {row['claim']} | {row['kind']} | {row['binding']} | {controls} |"
        )
    out.append("")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--doctrine", type=Path, default=DOCTRINE)
    args = parser.parse_args()

    claims = asserted_properties(args.doctrine.read_text(encoding="utf-8"))
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    errors, rows = verify(claims, registry)

    report = render(rows, registry.get("uncontrolled_ceiling"))
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(report + "\n")

    if errors:
        print("\nAsserted properties are not all bound to a control:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
