from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MCP_DIR = ROOT / "mcp-server"
sys.path.insert(0, str(MCP_DIR))

from pantheon_mcp import request_handling  # noqa: E402


SOUL = ROOT / "templates/hermes/profiles/pantheon-governed/SOUL.append.md"


def test_governed_profile_consumes_policy_metathought_as_attention_only() -> None:
    text = SOUL.read_text(encoding="utf-8")
    signal = request_handling.RITE_ATTENTION_SIGNALS["tests_pass_completion"]

    assert "handling.metathoughts" in text
    assert "⚙ Hermes · Attention gouvernée" in text
    assert signal["question"] in text
    assert signal["effect"] == "attention_only"
    assert "attention_only" in text
    assert "question ≠ symptôme confirmé ≠ Rite activé" in text

    assert "Do not convert `related_rite` into an activated Rite" in text
    assert "do not call `delegate_task` solely because a metathought is present" in text
    assert "`pantheon-activity-projection` skill" in text
