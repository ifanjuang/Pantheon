"""Dependency-free identity of one immutable Hermes execution basis.

The basis only states which requested effect, Task Contract, Context Pack and
preview digest belong together. Equality does not admit, authorize, reserve,
dispatch, start, accept or promote anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class HermesExecutionBasisError(ValueError):
    """An immutable Hermes basis is structurally incomplete."""


@dataclass(frozen=True, slots=True)
class HermesExecutionBasis:
    requested_effect: str
    task_contract_ref: str
    context_pack_ref: str
    preview_digest: str

    @classmethod
    def from_values(
        cls,
        *,
        requested_effect: Any,
        task_contract_ref: Any,
        context_pack_ref: Any,
        preview_digest: Any,
        label: str = "Hermes execution basis",
    ) -> "HermesExecutionBasis":
        values = {
            "requested_effect": str(requested_effect or "").strip(),
            "task_contract_ref": str(task_contract_ref or "").strip(),
            "context_pack_ref": str(context_pack_ref or "").strip(),
            "preview_digest": str(preview_digest or "").strip(),
        }
        missing = [key for key, value in values.items() if not value]
        if missing:
            raise HermesExecutionBasisError(
                f"{label} is missing: {', '.join(missing)}"
            )
        return cls(**values)

    @property
    def is_read_only(self) -> bool:
        return self.requested_effect == "read_only"
