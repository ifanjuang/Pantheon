from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_REVIEW = ROOT / "docs" / "governance" / "HERMES_RUNTIME_SURFACE_REVIEW.md"
RUN_BINDING = ROOT / "implementation" / "mvp_vertical" / "hermes_run_binding.py"
LAUNCH_CONTEXT = ROOT / "implementation" / "mvp_vertical" / "hermes_launch_context.py"
EXECUTION = ROOT / "implementation" / "mvp_vertical" / "hermes_execution.py"
LAUNCH_SQL = (
    ROOT
    / "implementation"
    / "mvp_vertical"
    / "sql"
    / "hermes"
    / "007_run_launch_reservations.sql"
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_hermes_021_session_identity_is_fresh_one_shot_host_correlation() -> None:
    review = _text(RUNTIME_REVIEW)
    binding = _text(RUN_BINDING)
    launch = _text(LAUNCH_CONTEXT)
    execution = _text(EXECUTION)
    launch_sql = _text(LAUNCH_SQL)

    assert "session_correlation: fresh_one_shot_execution_admission" in review
    assert "session_correlation_reuse: forbidden" in review
    assert "session correlation != transcript reuse" in review
    assert "Pantheon admission freshness != proof of empty external session state" in review

    # The current Context Bridge needs Hermes' host task_id to remain the exact
    # Pantheon admission identity, so removing session_id is not a valid 0.21 fix.
    assert "submitted = self._hermes.submit(input_text=input_text, session_id=admission_id)" in binding
    assert 'admission_id = f"admission-{uuid.uuid4().hex}"' in execution

    # Pantheon can use that fresh identity only once through its governed launch
    # seam. A replayed reservation is explicitly stopped before another Hermes POST.
    assert 'if reservation.get("replayed") is True:' in binding
    assert "automatic Hermes submission retry is forbidden" in binding
    assert "execution admission already has a launch reservation; automatic retry is forbidden" in launch
    assert "admission_id TEXT NOT NULL UNIQUE" in launch_sql


def test_runtime_review_does_not_confuse_session_field_presence_with_transcript_reuse() -> None:
    review = _text(RUNTIME_REVIEW)

    assert "session_id purpose: host task correlation" in review
    assert "session_id source: fresh Execution Admission identity" in review
    assert "second Pantheon launch for same admission: forbidden" in review
    assert "previous_response_id: omitted" in review
    assert "X-Hermes-Session-Key: absent" in review
    assert "runtime transcript reuse: forbidden" in review
    assert "governed transcript-reuse `session_id`" not in review
