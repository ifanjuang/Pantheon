#!/usr/bin/env python3
"""Export canonical external qualification pins as environment variables.

The registry is qualification input only. Exporting a pin does not install,
activate, authorize, admit Evidence, or assert that a component is deployed.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / "qualification" / "external-pins.json"
_SAFE_ENV = re.compile(r"^[A-Z][A-Z0-9_]*$")


def load_registry(path: Path = REGISTRY) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_id") != "pantheon.external_qualification_pins":
        raise ValueError("unexpected external qualification pin schema")
    return data


def exports_for(pin_id: str, pin: dict) -> dict[str, str]:
    prefix = pin.get("env_prefix")
    if not isinstance(prefix, str) or not _SAFE_ENV.fullmatch(prefix):
        raise ValueError(f"invalid env_prefix for {pin_id!r}")

    out: dict[str, str] = {f"{prefix}_PIN_ID": pin_id}
    fields = {
        "version": "VERSION",
        "ref": "REF",
        "repository": "REPOSITORY",
        "image": "IMAGE",
        "digest": "DIGEST",
        "package": "PACKAGE",
        "source_pin": "SOURCE_PIN",
        "release_tag": "RELEASE_TAG",
        "protocol_version": "PROTOCOL_VERSION",
    }
    for field, suffix in fields.items():
        value = pin.get(field)
        if value is not None:
            out[f"{prefix}_{suffix}"] = str(value)

    aliases = pin.get("aliases") or {}
    if not isinstance(aliases, dict):
        raise ValueError(f"aliases must be an object for {pin_id!r}")
    for field, names in aliases.items():
        if field not in fields:
            raise ValueError(f"unsupported alias field {field!r} for {pin_id!r}")
        value = pin.get(field)
        if value is None:
            raise ValueError(f"alias field {field!r} is absent for {pin_id!r}")
        if not isinstance(names, list) or not names:
            raise ValueError(f"alias list required for {pin_id!r}.{field}")
        for name in names:
            if not isinstance(name, str) or not _SAFE_ENV.fullmatch(name):
                raise ValueError(f"invalid alias env name for {pin_id!r}: {name!r}")
            out[name] = str(value)
    return out


def selected_exports(component_ids: list[str], *, path: Path = REGISTRY) -> dict[str, str]:
    data = load_registry(path)
    pins = data.get("pins")
    if not isinstance(pins, dict):
        raise ValueError("pins must be an object")

    selected = component_ids or sorted(pins)
    result: dict[str, str] = {}
    for pin_id in selected:
        if pin_id not in pins:
            raise KeyError(f"unknown qualification pin: {pin_id}")
        for name, value in exports_for(pin_id, pins[pin_id]).items():
            if name in result and result[name] != value:
                raise ValueError(f"conflicting export {name}")
            result[name] = value
    return result


def _write_github_env(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for name in sorted(values):
            value = values[name]
            if "\n" in value or "\r" in value:
                raise ValueError(f"multiline value forbidden for {name}")
            handle.write(f"{name}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("components", nargs="*", help="pin ids to export; all when omitted")
    parser.add_argument("--github-env", type=Path, help="append NAME=value entries to this GitHub Actions env file")
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    args = parser.parse_args()

    values = selected_exports(args.components, path=args.registry)
    if args.github_env:
        _write_github_env(args.github_env, values)
    else:
        for name in sorted(values):
            print(f"{name}={values[name]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
