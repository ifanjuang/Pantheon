"""Producer side of human-issuer authentication for effect-bound Decisions.

The Pantheon PDP (`mcp-server` gate-validation) authenticates the human issuer by
verifying an HMAC-SHA256 signature over the bounded Decision fields against a
configured issuer key registry. This module is the matching producer.

Signing authenticates *who decided over these exact immutable bounds*. It is not
an approval and does not authorize an effect — the PDP still checks scope,
ceiling, expiry, object identity, digest and effect flags.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any

import yaml

# Must equal gate_validation._SIGNED_FIELDS in Pantheon-Next.
SIGNED_FIELDS = (
    "decision_id",
    "decided_by",
    "approval_level",
    "scope",
    "object_identity",
    "content_digest",
    "expires_at",
)
ISSUER_KEYS_ENV = "PANTHEON_DECISION_ISSUER_KEYS_PATH"


def _signing_bytes(decision: dict[str, Any]) -> bytes:
    payload = {field: decision.get(field) for field in SIGNED_FIELDS}
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sign_decision(decision: dict[str, Any], secret: str) -> str:
    """Return the issuer HMAC-SHA256 signature over the bounded fields."""
    if not isinstance(decision, dict):
        raise ValueError("decision must be a mapping")
    if not secret:
        raise ValueError("an issuer signing secret is required")
    return hmac.new(secret.encode("utf-8"), _signing_bytes(decision), hashlib.sha256).hexdigest()


def signed_decision(decision: dict[str, Any], secret: str) -> dict[str, Any]:
    """Return a copy of the Decision transport projection with a signature."""
    out = dict(decision)
    out["signature"] = sign_decision(decision, secret)
    return out


def signed_decision_payload(decision_payload: dict[str, Any], secret: str) -> dict[str, Any]:
    """Sign the ``decision`` inside a ``{decision, expectation}`` payload."""
    if not isinstance(decision_payload, dict):
        raise ValueError("decision_payload must be a mapping")
    decision = decision_payload.get("decision")
    if not isinstance(decision, dict):
        raise ValueError("decision_payload.decision must be a mapping")
    out = dict(decision_payload)
    out["decision"] = signed_decision(decision, secret)
    return out


def issuer_secret(decided_by: str, path: str | Path | None = None) -> str | None:
    """Read the shared issuer secret used by the PDP, without exposing the registry.

    The producer and validator intentionally use the same operator-configured
    registry. Missing/unreadable configuration returns ``None``: the Decision may
    still be recorded as authenticated by OIDC, but it cannot become a signed
    credential for a consequential effect.
    """
    issuer = str(decided_by or "").strip()
    if not issuer:
        return None
    raw_path = str(path).strip() if path is not None else os.getenv(ISSUER_KEYS_ENV, "").strip()
    if not raw_path:
        return None
    target = Path(raw_path)
    try:
        data = yaml.safe_load(target.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(data, dict):
        return None
    secret = data.get(issuer)
    if not isinstance(secret, (str, int)):
        return None
    value = str(secret)
    return value if value else None
