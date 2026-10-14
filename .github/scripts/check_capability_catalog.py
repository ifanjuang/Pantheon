#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "catalog"
SCHEMAS = CATALOG / "schemas"
KIND_DIRS = {
    "Capability": CATALOG / "capabilities",
    "Resource": CATALOG / "resources",
}
SCHEMA_FILES = {
    "Capability": SCHEMAS / "capability.schema.json",
    "Resource": SCHEMAS / "resource.schema.json",
}
FORBIDDEN_KEYS = {"password", "token", "client_secret", "api_key", "credentials"}
SECRET_VALUE = re.compile(r"(?:sk-|ya29\.|ghp_|xox[baprs]-|-----BEGIN [A-Z ]+ PRIVATE KEY-----)", re.I)


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("manifest root must be an object")
    return value


def walk(node: Any, path: str = "$"):
    if isinstance(node, dict):
        for key, value in node.items():
            yield path, str(key), value
            yield from walk(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk(value, f"{path}[{index}]")


def fail(errors: list[str], path: Path, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {message}")


def main() -> int:
    errors: list[str] = []
    records: dict[str, dict[str, dict[str, Any]]] = {kind: {} for kind in KIND_DIRS}

    validators = {
        kind: Draft202012Validator(
            json.loads(schema_path.read_text(encoding="utf-8")),
            format_checker=FormatChecker(),
        )
        for kind, schema_path in SCHEMA_FILES.items()
    }

    for kind, directory in KIND_DIRS.items():
        for path in sorted(directory.glob("*.yaml")):
            try:
                doc = load_yaml(path)
            except Exception as exc:
                fail(errors, path, f"invalid YAML: {exc}")
                continue

            for error in sorted(validators[kind].iter_errors(doc), key=lambda e: list(e.path)):
                location = ".".join(str(part) for part in error.path) or "$"
                fail(errors, path, f"schema {location}: {error.message}")

            doc_kind = doc.get("kind")
            if doc_kind != kind:
                fail(errors, path, f"kind is {doc_kind!r}, expected {kind!r}")
                continue
            record_id = doc.get("metadata", {}).get("id")
            if not isinstance(record_id, str):
                continue
            if record_id in records[kind]:
                fail(errors, path, f"duplicate {kind} id {record_id!r}")
            records[kind][record_id] = doc

            for node_path, key, value in walk(doc):
                if key.lower() in FORBIDDEN_KEYS:
                    fail(errors, path, f"raw secret-like key forbidden at {node_path}.{key}")
                if isinstance(value, str) and SECRET_VALUE.search(value):
                    fail(errors, path, f"raw secret-like value forbidden at {node_path}.{key}")
                if isinstance(value, str) and value.endswith(":latest"):
                    fail(errors, path, f"unversioned image tag forbidden at {node_path}.{key}")

            serialized = json.dumps(doc, ensure_ascii=False).lower()
            if '"approved": true' in serialized or '"activation": "automatic"' in serialized:
                fail(errors, path, "manifest may not self-approve or activate automatically")

    capabilities = records["Capability"]
    resources = records["Resource"]

    for capability_id, capability in capabilities.items():
        candidates = capability["spec"]["candidate_resources"]
        for resource_id in candidates["preferred"] + candidates["alternatives"]:
            if resource_id not in resources:
                errors.append(f"Capability {capability_id}: unknown candidate resource {resource_id}")

    if errors:
        print(f"FAIL: capability catalog has {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"OK: validated {len(capabilities)} capabilities and {len(resources)} resources.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
