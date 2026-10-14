"""Shared stable identity primitive for bounded Pantheon projections.

EntityRef carries only a stable entity type and entity identifier. It does not
validate that the referenced owner exists, resolve scope, grant access, establish
truth or authorize an effect. Those responsibilities remain in their domains.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


class EntityRefError(ValueError):
    """A caller supplied an incomplete or structurally invalid entity reference."""


@dataclass(frozen=True, slots=True)
class EntityRef:
    entity_id: str
    entity_type: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
        *,
        label: str = "entity",
    ) -> "EntityRef":
        if not isinstance(value, Mapping):
            raise EntityRefError(f"{label} must be an object")
        entity_id = str(value.get("entity_id") or "").strip()
        entity_type = str(value.get("entity_type") or "").strip()
        if not entity_id or not entity_type:
            raise EntityRefError(
                f"{label} requires stable entity_id and entity_type"
            )
        return cls(entity_id=entity_id, entity_type=entity_type)

    @property
    def key(self) -> tuple[str, str]:
        return self.entity_type, self.entity_id

    def as_dict(self) -> dict[str, str]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
        }


def unique_entity_refs(
    values: Sequence[Mapping[str, Any]],
    *,
    label: str,
    limit: int | None = None,
) -> list[EntityRef]:
    """Normalize and deduplicate references while preserving first-seen order."""

    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise EntityRefError(f"{label} must be an array")
    if limit is not None and len(values) > limit:
        raise EntityRefError(f"{label} exceeds {limit} entries")

    output: list[EntityRef] = []
    seen: set[tuple[str, str]] = set()
    for raw in values:
        ref = EntityRef.from_mapping(raw, label=label)
        if ref.key in seen:
            continue
        seen.add(ref.key)
        output.append(ref)
    return output
