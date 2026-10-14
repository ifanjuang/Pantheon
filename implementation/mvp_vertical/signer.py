"""Shared human-signer discipline (adoption review, Gate 5).

The system may never sign a governed human act — neither a decision at the
terminal gate nor a retention authorization at the register seam. Both reuse
the *same* discipline from here, so the denylist has a single source of truth:

    - a signer is required (no default, no empty string);
    - a signer that IS the system (case-insensitive) is refused;
    - the signer is only ever a *declared* string, never an authenticated
      principal — that is the future cockpit's job:

          declared_identity != authenticated_principal

``normalize_human_signer`` raises a plain ``ValueError`` with a reason; each
caller wraps it in its own refusal type (``GateRefusal``, ``RegisterRefusal``)
so callers keep their own error surface.
"""

from __future__ import annotations

import datetime as _dt

# The only identity assurance a stand-in can honestly emit: a declared string,
# never an authenticated principal. Claiming "authenticated" is the future
# cockpit's job, from its session — not this repository's.
IDENTITY_ASSURANCE = "declared"

# Identities that ARE the system and can never be a human signer. A signer
# matching any of these (case-insensitive) is a system-signer attempt.
SYSTEM_IDENTITIES = frozenset({
    "system", "runner", "hermes", "mvp-vertical", "mvp_vertical", "gate",
    "terminal_gate_standin", "openwebui", "cockpit", "ai", "assistant", "claude",
})


def normalize_human_signer(name: str, *, field: str = "decided_by") -> str:
    """Return the cleaned human signer, or raise ValueError with a reason.

    Callers wrap the ValueError in their own refusal type. This is Gate 5 made
    structural: the system may never sign; a human must.
    """
    signer = (name or "").strip()
    if not signer:
        raise ValueError(f"{field} is required: the system may not sign; a human must")
    if signer.lower() in SYSTEM_IDENTITIES:
        raise ValueError(f"{field}={signer!r} is a system identity; only a human may sign")
    return signer


def now_micro() -> str:
    """UTC timestamp with microsecond precision — fine enough that two distinct
    human acts never share a timestamp, so their content digests differ."""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
