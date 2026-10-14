"""Declarative Agency Data schema registry and bounded field validation.

Schemas describe business fields and named projections. They are not an
authorization engine: mutation routes, lifecycle rules and Pantheon governance
remain authoritative.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

SCHEMA_ROOT = Path(__file__).resolve().parent / "agency_schema"
SCHEMA_PATHS = {
    "project": SCHEMA_ROOT / "project.json",
    "information": SCHEMA_ROOT / "information.json",
}
DEFAULT_VIEWS = {
    "project": "cockpit_back",
    "information": "cockpit_back",
}

PROJECT_SCHEMA_PATH = SCHEMA_PATHS["project"]
INFORMATION_SCHEMA_PATH = SCHEMA_PATHS["information"]
DEFAULT_PROJECT_VIEW = DEFAULT_VIEWS["project"]
DEFAULT_INFORMATION_VIEW = DEFAULT_VIEWS["information"]


class AgencySchemaError(ValueError):
    pass


def _entity_label(entity_type: str) -> str:
    return {
        "project": "Project",
        "information": "Information",
    }.get(entity_type, entity_type.title())


def _validate_registry(raw: dict[str, Any], *, entity_type: str) -> dict[str, Any]:
    label = _entity_label(entity_type)
    if raw.get("entity_type") != entity_type:
        raise AgencySchemaError(f"{label} schema must declare entity_type={entity_type}")
    if not isinstance(raw.get("version"), int) or raw["version"] < 1:
        raise AgencySchemaError(f"{label} schema version must be a positive integer")

    fields = raw.get("fields")
    if not isinstance(fields, list) or not fields:
        raise AgencySchemaError(f"{label} schema must declare fields")

    seen: set[str] = set()
    for index, field in enumerate(fields):
        if not isinstance(field, dict):
            raise AgencySchemaError(f"{label} schema field {index + 1} must be an object")
        key = str(field.get("key") or "").strip()
        if not key:
            raise AgencySchemaError(f"{label} schema field {index + 1} requires a key")
        if key in seen:
            raise AgencySchemaError(f"duplicate {label} schema field: {key}")
        seen.add(key)
        storage = field.get("storage")
        if storage not in {"core", "attributes", "projection", "system"}:
            raise AgencySchemaError(f"unsupported storage for {label} field {key}")
        semantics = field.get("semantics")
        if semantics is not None and semantics not in {
            "identity",
            "descriptive",
            "classification",
            "state",
            "claim",
            "derived",
            "system",
        }:
            raise AgencySchemaError(f"unsupported semantics for {label} field {key}")
        if storage == "projection":
            if semantics != "claim" or not str(field.get("claim_type") or "").strip():
                raise AgencySchemaError(
                    f"Project projection field {key} must declare semantics=claim and claim_type"
                )
            if field.get("mutable") is not False:
                raise AgencySchemaError(f"Project claim projection field {key} must be immutable in Project editor")
        if field.get("hermes_mode") not in {"no", "candidate", "auto", "bounded", "system"}:
            raise AgencySchemaError(f"unsupported hermes_mode for {label} field {key}")
        field_type = field.get("type")
        if field_type not in {
            "string",
            "enum",
            "number",
            "integer",
            "boolean",
            "string_list",
            "object_list",
            "date",
            "datetime",
        }:
            raise AgencySchemaError(f"unsupported type for {label} field {key}: {field_type}")
        if field_type == "enum" and not isinstance(field.get("values"), list):
            raise AgencySchemaError(f"enum {label} field {key} must declare values")

    views = raw.get("views")
    if not isinstance(views, dict) or not views:
        raise AgencySchemaError(f"{label} schema must declare named views")
    for view_name, view in views.items():
        if not isinstance(view_name, str) or not view_name.strip():
            raise AgencySchemaError(f"{label} schema view names must be non-empty strings")
        if not isinstance(view, dict):
            raise AgencySchemaError(f"{label} schema view {view_name} must be an object")
        view_fields = view.get("fields")
        if not isinstance(view_fields, list) or not view_fields:
            raise AgencySchemaError(f"{label} schema view {view_name} must declare fields")
        view_seen: set[str] = set()
        for field_key in view_fields:
            if not isinstance(field_key, str) or not field_key.strip():
                raise AgencySchemaError(f"{label} schema view {view_name} contains an invalid field key")
            if field_key not in seen:
                raise AgencySchemaError(
                    f"{label} schema view {view_name} references unknown field {field_key}"
                )
            if field_key in view_seen:
                raise AgencySchemaError(
                    f"{label} schema view {view_name} repeats field {field_key}"
                )
            view_seen.add(field_key)

    default_view = DEFAULT_VIEWS.get(entity_type)
    if default_view and default_view not in views:
        raise AgencySchemaError(f"{label} schema must declare default view {default_view}")
    return raw


@lru_cache(maxsize=None)
def _schema_cached(entity_type: str) -> dict[str, Any]:
    path = SCHEMA_PATHS.get(entity_type)
    if path is None:
        raise AgencySchemaError(f"unsupported Agency schema entity type: {entity_type}")
    label = _entity_label(entity_type)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgencySchemaError(f"unable to load {label} schema: {exc}") from exc
    return _validate_registry(raw, entity_type=entity_type)


def get_entity_registry(entity_type: str) -> dict[str, Any]:
    return deepcopy(_schema_cached(entity_type))


def get_entity_schema(entity_type: str, view_name: str | None = None) -> dict[str, Any]:
    schema = deepcopy(_schema_cached(entity_type))
    if view_name is None:
        return schema

    name = str(view_name or "").strip()
    view = schema["views"].get(name)
    if view is None:
        raise AgencySchemaError(f"unknown {_entity_label(entity_type)} schema view: {name}")

    by_key = {field["key"]: field for field in schema["fields"]}
    schema["fields"] = [by_key[key] for key in view["fields"]]
    schema["resolved_view"] = {
        "name": name,
        "purpose": view.get("purpose"),
        "field_count": len(view["fields"]),
        "authorization_inferred": False,
    }
    return schema


def get_entity_view(entity_type: str, view_name: str) -> dict[str, Any]:
    schema = _schema_cached(entity_type)
    name = str(view_name or "").strip()
    view = schema["views"].get(name)
    if view is None:
        raise AgencySchemaError(f"unknown {_entity_label(entity_type)} schema view: {name}")
    return deepcopy(view)


def entity_record_for_view(entity_type: str, record: dict[str, Any], view_name: str) -> dict[str, Any]:
    """Project one record through a declared view without granting read/write authority.

    ``record['claim_values']`` is a read-only semantic projection populated by the
    Agency ProjectClaim adapter. It is deliberately distinct from ``attributes``.
    """
    schema = get_entity_schema(entity_type, view_name)
    attributes = record.get("attributes") or {}
    if not isinstance(attributes, dict):
        attributes = {}
    claim_values = record.get("claim_values") or {}
    if not isinstance(claim_values, dict):
        claim_values = {}

    projected: dict[str, Any] = {}
    for field in schema["fields"]:
        key = field["key"]
        storage = field.get("storage")
        if storage == "attributes":
            projected[key] = attributes.get(key)
        elif storage == "projection":
            projected[key] = claim_values.get(field.get("claim_type") or key)
        else:
            projected[key] = record.get(key)
    return projected


def _normalize_date(value: Any, *, entity_type: str, key: str) -> str:
    label = _entity_label(entity_type)
    if isinstance(value, date):
        return value.isoformat()
    if not isinstance(value, str):
        raise AgencySchemaError(f"{label} field {key} must be an ISO date")
    text = value.strip()
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise AgencySchemaError(f"{label} field {key} must be an ISO date") from exc


def normalize_field_value(entity_type: str, field: dict[str, Any], value: Any) -> Any:
    key = field["key"]
    label = _entity_label(entity_type)
    if value is None:
        if field.get("nullable", False) or not field.get("required", False):
            return None
        raise AgencySchemaError(f"{label} field {key} may not be null")

    field_type = field.get("type")
    if field_type in {"string", "enum"}:
        if not isinstance(value, str):
            raise AgencySchemaError(f"{label} field {key} must be a string")
        text = value.strip()
        if not text and field.get("required", False):
            raise AgencySchemaError(f"{label} field {key} may not be empty")
        if field_type == "enum" and text not in set(field.get("values") or []):
            raise AgencySchemaError(
                f"{label} field {key} must be one of: {', '.join(field.get('values') or [])}"
            )
        return text
    if field_type == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise AgencySchemaError(f"{label} field {key} must be numeric")
        return value
    if field_type == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise AgencySchemaError(f"{label} field {key} must be an integer")
        return value
    if field_type == "boolean":
        if not isinstance(value, bool):
            raise AgencySchemaError(f"{label} field {key} must be boolean")
        return value
    if field_type == "string_list":
        if not isinstance(value, list):
            raise AgencySchemaError(f"{label} field {key} must be a list")
        output: list[str] = []
        seen: set[str] = set()
        for item in value:
            if not isinstance(item, str):
                raise AgencySchemaError(f"{label} field {key} must contain strings only")
            text = item.strip()
            if not text or text.casefold() in seen:
                continue
            seen.add(text.casefold())
            output.append(text)
        return output
    if field_type == "object_list":
        if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
            raise AgencySchemaError(f"{label} field {key} must contain objects only")
        return deepcopy(value)
    if field_type == "date":
        return _normalize_date(value, entity_type=entity_type, key=key)
    if field_type == "datetime":
        return value

    raise AgencySchemaError(f"unsupported {label} field type for {key}: {field_type}")


def normalize_declared_fields(
    entity_type: str,
    values: dict[str, Any],
    *,
    allowed_fields: set[str] | None = None,
    require_mutable: bool = False,
) -> dict[str, Any]:
    if not isinstance(values, dict):
        raise AgencySchemaError(f"{_entity_label(entity_type)} values must be an object")
    registry = _schema_cached(entity_type)
    fields = {field["key"]: field for field in registry["fields"]}
    unknown = sorted(set(values) - set(fields))
    if unknown:
        raise AgencySchemaError(
            f"unsupported {_entity_label(entity_type)} field(s): " + ", ".join(unknown)
        )

    normalized: dict[str, Any] = {}
    for key, value in values.items():
        field = fields[key]
        if allowed_fields is not None and key not in allowed_fields:
            raise AgencySchemaError(f"{_entity_label(entity_type)} field {key} is not allowed here")
        if require_mutable and field.get("mutable") is False:
            raise AgencySchemaError(f"{_entity_label(entity_type)} field {key} is immutable")
        normalized[key] = normalize_field_value(entity_type, field, value)
    return normalized


# ---- Project compatibility façade -------------------------------------------------

def get_project_registry() -> dict[str, Any]:
    return get_entity_registry("project")


def get_project_schema(view_name: str | None = DEFAULT_PROJECT_VIEW) -> dict[str, Any]:
    return get_entity_schema("project", view_name)


def get_project_view(view_name: str) -> dict[str, Any]:
    return get_entity_view("project", view_name)


def project_record_for_view(record: dict[str, Any], view_name: str) -> dict[str, Any]:
    return entity_record_for_view("project", record, view_name)


def _project_attribute_fields() -> dict[str, dict[str, Any]]:
    return {
        field["key"]: field
        for field in _schema_cached("project")["fields"]
        if field.get("storage") == "attributes"
    }


def project_claim_fields() -> dict[str, dict[str, Any]]:
    return {
        field["claim_type"]: deepcopy(field)
        for field in _schema_cached("project")["fields"]
        if field.get("storage") == "projection" and field.get("semantics") == "claim"
    }


def normalize_project_attributes(attributes: dict[str, Any] | None) -> dict[str, Any]:
    if attributes is None:
        return {}
    if not isinstance(attributes, dict):
        raise AgencySchemaError("Project attributes must be an object")
    fields = _project_attribute_fields()
    unknown = sorted(set(attributes) - set(fields))
    if unknown:
        raise AgencySchemaError("unsupported Project attribute field(s): " + ", ".join(unknown))
    return {
        key: normalize_field_value("project", fields[key], value)
        for key, value in attributes.items()
    }


# ---- Information façade -----------------------------------------------------------
def get_information_registry() -> dict[str, Any]:
    return get_entity_registry("information")


def get_information_schema(view_name: str | None = DEFAULT_INFORMATION_VIEW) -> dict[str, Any]:
    return get_entity_schema("information", view_name)


def get_information_view(view_name: str) -> dict[str, Any]:
    return get_entity_view("information", view_name)


def information_record_for_view(record: dict[str, Any], view_name: str) -> dict[str, Any]:
    return entity_record_for_view("information", record, view_name)
