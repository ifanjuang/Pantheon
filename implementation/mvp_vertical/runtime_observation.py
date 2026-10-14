"""Common factual envelope for adapter and runtime observations.

The envelope validates only provenance-like observation metadata and preserves
adapter-owned payload fields. It does not define a global health/status ontology,
establish truth, authorize effects, activate bindings or admit Evidence.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any


class RuntimeObservationError(ValueError):
    """An observation is missing its minimal factual envelope."""


_COMMON_FIELDS = {"source", "observation_source", "observed_at"}


def _required_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeObservationError(f"{field} must be a non-empty string")
    return value.strip()


def _observed_at(value: Any) -> str:
    raw = _required_string(value, field="observed_at")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeObservationError("observed_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeObservationError("observed_at must include an explicit UTC offset")
    return raw


@dataclass(frozen=True, slots=True)
class RuntimeObservation:
    source: str
    observation_source: str
    observed_at: str
    payload: dict[str, Any]

    @classmethod
    def from_flat_mapping(
        cls,
        value: Mapping[str, Any],
        *,
        label: str = "runtime observation",
    ) -> "RuntimeObservation":
        if not isinstance(value, Mapping):
            raise RuntimeObservationError(f"{label} must be an object")
        return cls.from_payload(
            source=value.get("source"),
            observation_source=value.get("observation_source"),
            observed_at=value.get("observed_at"),
            payload={key: item for key, item in value.items() if key not in _COMMON_FIELDS},
            label=label,
        )

    @classmethod
    def from_payload(
        cls,
        *,
        source: Any,
        observation_source: Any,
        observed_at: Any,
        payload: Mapping[str, Any],
        label: str = "runtime observation",
    ) -> "RuntimeObservation":
        if not isinstance(payload, Mapping):
            raise RuntimeObservationError(f"{label}.payload must be an object")
        collisions = sorted(_COMMON_FIELDS.intersection(payload))
        if collisions:
            raise RuntimeObservationError(
                f"{label}.payload repeats envelope fields: {', '.join(collisions)}"
            )
        return cls(
            source=_required_string(source, field=f"{label}.source"),
            observation_source=_required_string(
                observation_source,
                field=f"{label}.observation_source",
            ),
            observed_at=_observed_at(observed_at),
            payload=deepcopy(dict(payload)),
        )

    def as_flat_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "observation_source": self.observation_source,
            "observed_at": self.observed_at,
            **deepcopy(self.payload),
        }


def normalize_runtime_observation(
    value: Mapping[str, Any],
    *,
    label: str = "runtime observation",
) -> dict[str, Any]:
    """Validate the common envelope while preserving local fields unchanged."""
    return RuntimeObservation.from_flat_mapping(value, label=label).as_flat_dict()


def wrap_runtime_observation(
    *,
    source: Any,
    observation_source: Any,
    observed_at: Any,
    payload: Mapping[str, Any],
    label: str = "runtime observation",
) -> dict[str, Any]:
    """Wrap a raw adapter payload in the factual envelope without interpreting it."""
    return RuntimeObservation.from_payload(
        source=source,
        observation_source=observation_source,
        observed_at=observed_at,
        payload=payload,
        label=label,
    ).as_flat_dict()


def normalize_runtime_observations(
    values: Sequence[Mapping[str, Any]],
    *,
    label: str = "runtime observations",
) -> list[dict[str, Any]]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise RuntimeObservationError(f"{label} must be an array")
    return [
        normalize_runtime_observation(value, label=f"{label}[{index}]")
        for index, value in enumerate(values)
    ]
