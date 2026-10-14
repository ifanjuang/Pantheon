"""CLI `register` subcommand (Block 3). DB-free: drives cli.main() directly.

The decision the CLI reads must be a real, gate-produced decision_record — the
hardened register seam refuses anything else — so the fixture records one
through the gate on a schema-valid candidate stream.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from mvp_vertical import cli
from mvp_vertical.terminal_gate_standin import record_decision


REQUEST_REF = "mvp.test.tc"
REQUEST_SCOPE_DIGEST = "sha256:" + "4" * 64


def _approved_decision(tmp_path: Path) -> tuple[Path, dict]:
    candidates = [
        {"object_type": "result_candidate", "object_id": "mvp.test.tc.rc-001",
         "result_candidate_id": "mvp.test.tc.rc-001", "applies_to": "mvp.test.tc",
         "status": "draft_to_review", "request_ref": REQUEST_REF,
         "request_scope_digest": REQUEST_SCOPE_DIGEST,
         "body": "…", "external_action_authorized": False},
        {"object_type": "evidence_pack_candidate", "object_id": "mvp.test.tc.ep-001",
         "evidence_pack_id": "mvp.test.tc.ep-001", "applies_to": "mvp.test.tc",
         "supports": "mvp.test.tc.rc-001", "status": "candidate",
         "request_ref": REQUEST_REF, "request_scope_digest": REQUEST_SCOPE_DIGEST,
         "evidence_items": [{"claim": "…", "source_ref": "s.md", "support_status": "sourced_not_verified"}],
         "possible_decisions": ["approve", "refuse", "request_revision", "request_more_evidence"]},
    ]
    rec = record_decision(candidates, decision="approve", decided_by="Camille")
    path = tmp_path / "decision.yaml"
    path.write_text(yaml.safe_dump(rec), encoding="utf-8")
    return path, rec


def test_register_cli_emits_a_candidate(tmp_path, monkeypatch):
    dpath, rec = _approved_decision(tmp_path)
    out = tmp_path / "register.yaml"
    monkeypatch.setattr(sys, "argv", [
        "mvp-vertical", "register", "--decision-record", str(dpath),
        "--retention-authorized", "--authorized-by", "Camille",
        "--statement", "Le lot 06 est limité à T2.",
        "--scope", "devis_reprise", "--output", str(out),
    ])
    assert cli.main() == 0
    reg = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert reg["object_type"] == "register_candidate"
    assert reg["created_because_of"] == rec["decision_id"]
    assert reg["not_memory_until_admitted"] is True
    # the human retention authorization rides the candidate, declared not authenticated
    assert reg["retention_authorization"]["authorized_by"] == "Camille"
    assert reg["retention_authorization"]["identity_assurance"] == "declared"


def test_register_cli_refuses_without_authorization(tmp_path, monkeypatch, capsys):
    dpath, _ = _approved_decision(tmp_path)
    monkeypatch.setattr(sys, "argv", [
        "mvp-vertical", "register", "--decision-record", str(dpath),
        "--authorized-by", "Camille",
        "--statement", "x", "--scope", "y",  # no --retention-authorized
    ])
    assert cli.main() == 1  # clean refusal, not a crash
    assert "register refused" in capsys.readouterr().err


def test_register_cli_refuses_a_system_authorizer(tmp_path, monkeypatch, capsys):
    # Gate 5, reused at the retention seam: the system may not authorize memory.
    dpath, _ = _approved_decision(tmp_path)
    monkeypatch.setattr(sys, "argv", [
        "mvp-vertical", "register", "--decision-record", str(dpath),
        "--retention-authorized", "--authorized-by", "system",
        "--statement", "x", "--scope", "y",
    ])
    assert cli.main() == 1
    assert "register refused" in capsys.readouterr().err
