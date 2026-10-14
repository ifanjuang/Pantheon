"""Derive bounded, display-only Role stages from public Hermes Runs events.

The projector consumes only public ``message.delta`` and tool lifecycle events.
It deliberately ignores ``reasoning.available`` and never reconstructs private
reasoning.  Its output is transient presentation data, not a Role Signal,
Evidence, approval, runtime dispatch or persistence contract.
"""

from __future__ import annotations

import re
from collections import defaultdict, deque
from typing import Any


MAX_LINE_CHARS = 4_000
MAX_STAGES = 100
MAX_SUMMARY_CHARS = 500


class HermesRoleStageProjectionError(ValueError):
    """A public Runs event cannot be projected without crossing a boundary."""


ROLE_FAMILIES = {
    "athena": ("Athena", "analysis"),
    "argos": ("Argos", "sources"),
    "themis": ("Themis", "risk"),
    "apollo": ("Apollo", "quality"),
    "hephaistos": ("Hephaistos", "fabrication"),
    "iris": ("Iris", "transmission"),
    "zeus": ("Zeus", "arbitration"),
    "mnemosyne": ("Mnemosyne", "continuity"),
    "hermes": ("Hermes", "runtime"),
}

_ROLE_NAMES = "|".join(name.title() for name in ROLE_FAMILIES)
_HEADER = re.compile(
    rf"^(?:\s*#{{1,6}}\s*)?(?:[^\w\s]{{1,3}}\s*)?"
    rf"(?P<role>{_ROLE_NAMES})\s*·\s*(?P<function>[^\n]+?)\s*$",
    flags=re.IGNORECASE,
)
_FIELD = re.compile(
    r"^(?P<label>Action|Raison|But|Sources|Méthode|Skill|Outil|Résultat|"
    r"Limite|Prochaine action|Gate|Relais|→\s*Relais)\s*:\s*(?P<value>.+)$",
    flags=re.IGNORECASE,
)
_TERMINAL_EVENTS = {"run.completed", "run.failed", "run.cancelled", "run.interrupted"}


def _bounded(value: Any, *, limit: int = MAX_SUMMARY_CHARS) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _field_key(label: str) -> str:
    normalized = label.casefold().replace("→", "").strip()
    return {
        "méthode": "method",
        "résultat": "result",
        "prochaine action": "next_action",
        "relais": "handoff",
    }.get(normalized, normalized.replace(" ", "_"))


class HermesRoleStageProjector:
    """Incrementally project one Hermes run's public stream into Role stages."""

    def __init__(self, run_id: str) -> None:
        self.run_id = str(run_id or "").strip()
        if not self.run_id:
            raise HermesRoleStageProjectionError("run_id is required")
        self._line_buffer = ""
        self._sequence = 0
        self._current: dict[str, Any] | None = None
        self._tool_stages: dict[str, deque[dict[str, Any]]] = defaultdict(deque)

    def _new_stage(
        self,
        *,
        visible_role: str,
        role_family: str,
        semantic_function: str,
        timestamp: Any,
        source_event: str,
        tool: str | None = None,
    ) -> dict[str, Any]:
        if self._sequence >= MAX_STAGES:
            raise HermesRoleStageProjectionError(
                f"role stage count exceeds {MAX_STAGES} for one run"
            )
        self._sequence += 1
        stage = {
            "event": "role.stage",
            "phase": "started",
            "stage_id": f"{self.run_id}:role:{self._sequence}",
            "run_id": self.run_id,
            "sequence": self._sequence,
            "timestamp": timestamp,
            "visible_role": visible_role,
            "role_family": role_family,
            "semantic_function": _bounded(semantic_function, limit=120),
            "summary": None,
            "details": {},
            "tool": tool,
            "source_event": source_event,
            "projection": "derived_transient",
            "authority_effect": "none",
            "private_reasoning_included": False,
        }
        return stage

    @staticmethod
    def _emit(stage: dict[str, Any], phase: str, **changes: Any) -> dict[str, Any]:
        stage.update(changes)
        stage["phase"] = phase
        return dict(stage)

    def _complete_current(self, *, timestamp: Any) -> list[dict[str, Any]]:
        if self._current is None:
            return []
        stage = self._current
        self._current = None
        return [self._emit(stage, "completed", completed_at=timestamp)]

    def _consume_public_line(self, line: str, *, timestamp: Any) -> list[dict[str, Any]]:
        stripped = line.strip()
        if not stripped:
            return []
        header = _HEADER.match(stripped)
        if header:
            emitted = self._complete_current(timestamp=timestamp)
            role_key = header.group("role").casefold()
            visible_role, family = ROLE_FAMILIES[role_key]
            self._current = self._new_stage(
                visible_role=visible_role,
                role_family=family,
                semantic_function=header.group("function"),
                timestamp=timestamp,
                source_event="message.delta",
            )
            emitted.append(dict(self._current))
            return emitted
        if self._current is None or stripped.startswith("```"):
            return []

        field = _FIELD.match(stripped)
        if field:
            details = dict(self._current["details"])
            details[_field_key(field.group("label"))] = _bounded(field.group("value"))
            summary = self._current["summary"] or _bounded(field.group("value"))
            return [self._emit(self._current, "updated", details=details, summary=summary)]
        if self._current["summary"] is None:
            return [self._emit(self._current, "updated", summary=_bounded(stripped))]
        return []
    def _feed_delta(self, delta: Any, *, timestamp: Any) -> list[dict[str, Any]]:
        if not isinstance(delta, str):
            raise HermesRoleStageProjectionError("message.delta must contain text")
        self._line_buffer += delta.replace("\r\n", "\n").replace("\r", "\n")
        if len(self._line_buffer) > MAX_LINE_CHARS:
            raise HermesRoleStageProjectionError(
                f"unterminated public message line exceeds {MAX_LINE_CHARS} characters"
            )
        emitted: list[dict[str, Any]] = []
        while "\n" in self._line_buffer:
            line, self._line_buffer = self._line_buffer.split("\n", 1)
            emitted.extend(self._consume_public_line(line, timestamp=timestamp))
        return emitted

    def _feed_tool(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        event_type = str(event.get("event") or "")
        tool = _bounded(event.get("tool"), limit=160)
        if not tool:
            return []
        timestamp = event.get("timestamp")
        if event_type == "tool.started":
            stage = self._new_stage(
                visible_role="Hermes",
                role_family="runtime",
                semantic_function="Exécution",
                timestamp=timestamp,
                source_event=event_type,
                tool=tool,
            )
            stage["summary"] = f"Outil démarré : {tool}"
            self._tool_stages[tool].append(stage)
            return [dict(stage)]
        queue = self._tool_stages.get(tool)
        if not queue:
            return []
        stage = queue.popleft()
        if not queue:
            self._tool_stages.pop(tool, None)
        return [
            self._emit(
                stage,
                "completed",
                summary=(f"Outil en échec : {tool}" if event.get("error") is True else f"Outil terminé : {tool}"),
                completed_at=timestamp,
                error=event.get("error") is True,
                duration=event.get("duration"),
            )
        ]

    def feed(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """Consume one public Hermes event and return zero or more projections."""

        if not isinstance(event, dict):
            raise HermesRoleStageProjectionError("Hermes event must be an object")
        event_type = str(event.get("event") or "")
        if event_type == "reasoning.available":
            return []
        if event_type in {"tool.started", "tool.completed"}:
            return self._feed_tool(event)
        if event_type == "message.delta":
            return self._feed_delta(event.get("delta"), timestamp=event.get("timestamp"))
        if event_type in _TERMINAL_EVENTS:
            emitted: list[dict[str, Any]] = []
            if self._line_buffer:
                emitted.extend(
                    self._consume_public_line(
                        self._line_buffer, timestamp=event.get("timestamp")
                    )
                )
                self._line_buffer = ""
            emitted.extend(self._complete_current(timestamp=event.get("timestamp")))
            for queue in list(self._tool_stages.values()):
                while queue:
                    stage = queue.popleft()
                    emitted.append(
                        self._emit(
                            stage,
                            "completed",
                            summary=f"Exécution interrompue avant confirmation : {stage['tool']}",
                            completed_at=event.get("timestamp"),
                            incomplete=True,
                        )
                    )
            self._tool_stages.clear()
            return emitted
        return []
