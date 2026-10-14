"""Project explicit Hermes subagent lifecycle events into a bounded runtime view.

This projector consumes only public ``subagent.start`` and ``subagent.complete``
Runs SSE events.  Parent/child relations are retained only when Hermes reports
them explicitly; ordering is never upgraded into causality.  The output is
transient presentation data, not a Pantheon Role, Role Signal, Evidence,
approval, execution authority or persistence contract.
"""

from __future__ import annotations

from typing import Any


MAX_SUBAGENTS = 100
MAX_TEXT_CHARS = 500
MAX_ID_CHARS = 200
MAX_FILE_REFS = 64
MAX_FILE_REF_CHARS = 500
_SUBAGENT_EVENTS = {"subagent.start", "subagent.complete"}
_NUMERIC_FIELDS = (
    "depth",
    "task_index",
    "task_count",
    "tool_count",
    "duration_seconds",
    "input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "api_calls",
    "cost_usd",
)

# A figure is only a display label for an explicitly declared, bounded
# delegation.  It is neither a separate agent identity nor a source of
# authority.  Keeping the allow-list here prevents a prompt or an upstream
# free-text field from inventing a person in the cockpit.
DELEGATION_FIGURES = {
    "palamede": {"name": "Palamède", "mission": "analyse factuelle"},
    "ariane": {"name": "Ariane", "mission": "chronologie des échanges"},
    "diomede": {"name": "Diomède", "mission": "vérification"},
    "antigone": {"name": "Antigone", "mission": "lacunes et contradictions"},
}


class HermesRuntimeTopologyProjectionError(ValueError):
    """A public subagent event cannot be projected without crossing a boundary."""


def _bounded(value: Any, *, limit: int = MAX_TEXT_CHARS) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    if not text:
        return None
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _identifier(name: str, value: Any) -> str | None:
    text = _bounded(value, limit=MAX_ID_CHARS)
    if text is None:
        return None
    if any(ord(char) < 32 for char in text):
        raise HermesRuntimeTopologyProjectionError(f"{name} contains control characters")
    return text


def _file_refs(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise HermesRuntimeTopologyProjectionError("subagent file references must be lists")
    if len(value) > MAX_FILE_REFS:
        raise HermesRuntimeTopologyProjectionError(
            f"subagent file references exceed {MAX_FILE_REFS} entries"
        )
    output: list[str] = []
    for item in value:
        text = _bounded(item, limit=MAX_FILE_REF_CHARS)
        if text:
            output.append(text)
    return output


class HermesRuntimeTopologyProjector:
    """Project one run's explicit Hermes subagent lifecycle into display nodes."""

    def __init__(self, run_id: str) -> None:
        self.run_id = str(run_id or "").strip()
        if not self.run_id:
            raise HermesRuntimeTopologyProjectionError("run_id is required")
        self._subagent_ids: set[str] = set()
        self._figures: dict[str, dict[str, str]] = {}

    def _figure(self, event: dict[str, Any], *, subagent_id: str) -> dict[str, str] | None:
        """Return only an explicitly declared, known delegation figure.

        A completion may omit the field: it inherits the declaration observed
        at start.  Supplying a different value is rejected rather than being
        silently rewritten into a plausible narrative.
        """

        declared = event.get("delegation_figure")
        remembered = self._figures.get(subagent_id)
        if declared is None:
            return remembered
        key = _bounded(declared, limit=80)
        if key is None or key.casefold() not in DELEGATION_FIGURES:
            raise HermesRuntimeTopologyProjectionError(
                "delegation_figure must be one of the declared Pantheon figures"
            )
        figure = dict(DELEGATION_FIGURES[key.casefold()])
        if remembered is not None and remembered != figure:
            raise HermesRuntimeTopologyProjectionError(
                "delegation_figure changed during one subagent lifecycle"
            )
        self._figures[subagent_id] = figure
        return figure

    def feed(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        if not isinstance(event, dict):
            raise HermesRuntimeTopologyProjectionError("Hermes event must be an object")
        event_type = str(event.get("event") or "")
        if event_type not in _SUBAGENT_EVENTS:
            return []
        observed_run_id = str(event.get("run_id") or self.run_id).strip()
        if observed_run_id != self.run_id:
            raise HermesRuntimeTopologyProjectionError(
                "Hermes subagent event crossed the requested run boundary"
            )

        subagent_id = _identifier("subagent_id", event.get("subagent_id"))
        if not subagent_id:
            raise HermesRuntimeTopologyProjectionError(
                "Hermes subagent lifecycle event requires subagent_id"
            )
        self._subagent_ids.add(subagent_id)
        if len(self._subagent_ids) > MAX_SUBAGENTS:
            raise HermesRuntimeTopologyProjectionError(
                f"subagent count exceeds {MAX_SUBAGENTS} for one run"
            )
        figure = self._figure(event, subagent_id=subagent_id)

        phase = "started" if event_type == "subagent.start" else "completed"
        metrics = {
            key: event[key]
            for key in _NUMERIC_FIELDS
            if event.get(key) is not None and isinstance(event.get(key), (int, float))
        }
        projection = {
            "event": "runtime.subagent",
            "phase": phase,
            "runtime_node_id": f"{self.run_id}:subagent:{subagent_id}",
            "run_id": self.run_id,
            "timestamp": event.get("timestamp"),
            "subagent_id": subagent_id,
            "parent_id": _identifier("parent_id", event.get("parent_id")),
            "delegation_id": _identifier("delegation_id", event.get("delegation_id")),
            "child_session_id": _identifier("child_session_id", event.get("child_session_id")),
            "goal": _bounded(event.get("goal")),
            "summary": _bounded(event.get("summary")),
            "status": _bounded(event.get("status"), limit=120),
            "model": _bounded(event.get("model"), limit=160),
            "metrics": metrics,
            "files": {
                "read": _file_refs(event.get("files_read")),
                "written": _file_refs(event.get("files_written")),
            },
            "source_event": event_type,
            "relation_basis": "explicit_runtime_ids",
            "projection": "derived_transient",
            "persistence": "none",
            "authority_effect": "none",
            "governed_identity": False,
            "figure": figure,
            "figure_basis": (
                "explicit_delegation_metadata" if figure is not None else "not_declared"
            ),
            "private_reasoning_included": False,
        }
        return [projection]
