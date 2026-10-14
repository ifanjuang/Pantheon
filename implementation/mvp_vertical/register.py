"""Block 3 — Register Candidate proposal (issue #13).

The only transition into the register is:

    Decision Record + decision == approve + retention_authorized == true
        -> Register Candidate

A Register Candidate is NOT a Register Entry, and retention_authorized is NOT
memory promotion. This module produces a schema-valid ``register_candidate`` as
DATA, linked to the exact decision record and to the digests of the content the
human reviewed. It writes nothing durable and promotes no memory:

    register_candidate != register_entry
    retention_authorized != memory_promoted
    decision_recorded != consequence_executed

``statement`` (what is retained), ``scope`` (where it applies) and
``retention_authorized`` (a human authorization, distinct from the approve
decision) are supplied by the human — never fabricated here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from .contract import _schema
from .runner import _assert_no_external_authorization
from .signer import IDENTITY_ASSURANCE, normalize_human_signer, now_micro


class RegisterRefusal(ValueError):
    """The register transition preconditions are not met — not a gate-produced
    approved decision, retention not authorized by a human, or a missing
    statement/scope."""


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _validate(candidate: dict) -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - runtime dep, guard only
        raise RegisterRefusal("cannot validate register_candidate — jsonschema not installed") from exc
    try:
        jsonschema.validate(candidate, _schema())
    except jsonschema.ValidationError as exc:
        raise RegisterRefusal(
            f"register_candidate does not conform to the vendored schema: {exc.message}"
        ) from exc


def _require_gate_decision_record(decision_record: dict) -> None:
    """The register seam must not trust a hand-crafted decision_record.

    It refuses input that (a) is not a decision_record, (b) does not conform to
    the vendored schema, or (c) is missing an integrity field a real terminal
    gate always emits. The digest fields in particular bind retention to the
    exact content the human reviewed — a minimal ``{object_type: decision_record,
    decision: approve, ...}`` dict carries no such binding and is refused.

    This raises the bar structurally; it is not cryptographic provenance. The
    gate does not sign (Gate 5), so a full forgery replicating every field still
    passes — real origin awaits the future authenticated cockpit:

        declared_identity != authenticated_principal
    """
    if not isinstance(decision_record, dict) or decision_record.get("object_type") != "decision_record":
        raise RegisterRefusal("input is not a decision_record")
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - runtime dep, guard only
        raise RegisterRefusal("cannot validate decision_record — jsonschema not installed") from exc
    try:
        jsonschema.validate(decision_record, _schema())
    except jsonschema.ValidationError as exc:
        raise RegisterRefusal(
            f"decision_record does not conform to the vendored schema: {exc.message}"
        ) from exc
    # Fields a real gate always emits but the schema does not force. Their
    # absence means the record did not come through the gate.
    for field in ("decision_id", "recorded_at", "identity_assurance"):
        if not decision_record.get(field):
            raise RegisterRefusal(
                f"decision_record is missing gate-produced field {field!r}; "
                "retention accepts only a decision recorded by the terminal gate"
            )
    # The gate never signs with a system identity (Gate 5). A hand-crafted but
    # schema-valid record whose decided_by is empty or a system identity would
    # have been refused by record_decision — refuse it here too.
    try:
        normalize_human_signer(decision_record.get("decided_by"), field="decided_by")
    except ValueError as exc:
        raise RegisterRefusal(
            f"decision_record was not signed by a human ({exc}); "
            "retention accepts only a decision the gate would have recorded"
        ) from exc
    # The digests are what make retention bind to the reviewed content — they
    # must match the gate's exact shape: {algorithm: sha256, value: <64-hex>}.
    # A stub like {"value": "..."} (no algorithm) is not gate-shaped and, worse,
    # the basis builder would default its algorithm to sha256 — so refuse it.
    for field in ("candidate_digest", "evidence_pack_digest"):
        digest = decision_record.get(field)
        value = digest.get("value") if isinstance(digest, dict) else None
        if not (isinstance(digest, dict)
                and digest.get("algorithm") == "sha256"
                and isinstance(value, str)
                and len(value) == 64
                and all(c in "0123456789abcdef" for c in value)):
            raise RegisterRefusal(
                f"decision_record is missing a gate-shaped {field} "
                "(sha256 + 64-hex value); retention must bind to the exact content "
                "the human reviewed, not a hand-crafted stub"
            )
    if decision_record.get("external_action_authorized", False):
        raise RegisterRefusal(
            "decision_record carries external_action_authorized; refusing to "
            "propose retention from a record that claims an external authorization"
        )


def propose_register_candidate(
    decision_record: dict,
    *,
    retention_authorized: bool,
    statement: str,
    scope: str,
    authorized_by: str,
    rationale: str = "",
    authorized_at: str | None = None,
) -> dict:
    """Propose a register candidate from an approved decision — or refuse.

    Refuses unless the input is a *gate-produced* decision_record whose decision
    is ``approve``, ``retention_authorized`` is exactly ``True``, and a human
    (``authorized_by``, subject to the same system-signer refusal as the gate)
    authorizes retention, with a human-authored ``statement`` and ``scope``.

    Retention authorization is a distinct human act, separate from the approve
    decision, recorded inline as a ``retention_authorization`` block whose
    identity assurance is ``declared`` — never authenticated:

        retention_authorized != memory_promoted

    Returns a schema-valid register_candidate that is not memory until admitted,
    writes nothing durable, and authorizes nothing external.
    """
    # The decision_record must have come through the gate, not be hand-crafted.
    _require_gate_decision_record(decision_record)
    if decision_record.get("decision") != "approve":
        raise RegisterRefusal(
            f"only an approved decision may propose retention (decision="
            f"{decision_record.get('decision')!r})"
        )
    if retention_authorized is not True:
        raise RegisterRefusal(
            "retention_authorized must be explicitly true — retention is a human "
            "authorization, separate from the approve decision"
        )
    # Gate 5 discipline, reused: retention is a human act; the system may not
    # authorize its own memory. authorized_by must be a human, never the system.
    try:
        authorizer = normalize_human_signer(authorized_by, field="authorized_by")
    except ValueError as exc:
        raise RegisterRefusal(str(exc)) from exc

    statement = (statement or "").strip()
    scope = (scope or "").strip()
    if not statement:
        raise RegisterRefusal("statement is required: what is being registered must be human-authored")
    if not scope:
        raise RegisterRefusal("scope is required: where the statement applies")

    decision_id = decision_record.get("decision_id") or decision_record["object_id"]
    applies_to = decision_record.get("applies_to", decision_id)

    # basis links the candidate to the exact reviewed content — the decision and
    # the digests the decision recorded (integrity chain, not a memory write).
    basis = [f"decision:{decision_id}"]
    for key, label in (("candidate_digest", "candidate_digest"),
                       ("evidence_pack_digest", "evidence_pack_digest")):
        digest = decision_record.get(key)
        if isinstance(digest, dict) and digest.get("value"):
            basis.append(f"{label}:{digest.get('algorithm', 'sha256')}:{digest['value']}")

    # The retention authorization is its own human act. Its shape is the vendored
    # schema's retention_authorization def (see canonical governed-loop schema), which is
    # additionalProperties:false: exactly authorized/authorized_by/
    # identity_assurance/recorded_at/decision_id. identity_assurance is declared
    # (never authenticated), so no authenticated_principal is present — the
    # schema's conditional forbids it for declared. The human rationale, being
    # outside that strict shape, rides the register candidate at top level.
    now = authorized_at or now_micro()
    authorization = {
        "authorized": True,
        "authorized_by": authorizer,
        "identity_assurance": IDENTITY_ASSURANCE,  # declared, never authenticated
        "recorded_at": now,
        "decision_id": decision_id,
    }

    id_digest = hashlib.sha256(
        _canonical({"created_because_of": decision_id, "statement": statement, "scope": scope}).encode("utf-8")
    ).hexdigest()[:12]
    object_id = f"{applies_to}.register.{id_digest}"

    candidate = {
        "object_type": "register_candidate",
        "object_id": object_id,
        "candidate_id": object_id,
        "status": "candidate",
        "created_because_of": decision_id,
        "statement": statement,
        "scope": scope,
        "basis": basis,
        "retention_authorization": authorization,
        "retention_rationale": rationale,
        "not_memory_until_admitted": True,
        "forbidden_reuse": ["memory_promotion", "external_send", "durable_write"],
        "governance_refs": [
            "docs/governance/MVP_GOVERNED_TASK_LOOP.md",
            "docs/governance/USER_DECISION_GATE.md",
        ],
    }
    # A register candidate authorizes no external action either, and it is only
    # a candidate — never an admitted entry, never durable memory.
    _assert_no_external_authorization([candidate])
    _validate(candidate)
    return candidate


def load_decision_record(path: str | Path) -> dict:
    """Read a single decision_record document (as `decide` emits it)."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RegisterRefusal(f"{path}: not a single decision_record document")
    return data


def to_yaml(candidate: dict) -> str:
    return yaml.safe_dump(candidate, sort_keys=False, allow_unicode=True)
