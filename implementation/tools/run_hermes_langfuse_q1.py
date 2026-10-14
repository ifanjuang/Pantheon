from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path


def fresh_plugin(hermes_root: Path):
    sys.path.insert(0, str(hermes_root))
    sys.modules.pop("plugins.observability.langfuse", None)
    return importlib.import_module("plugins.observability.langfuse")


def main() -> None:
    hermes_root = Path(os.environ["HERMES_ROOT"]).resolve()
    plugin = fresh_plugin(hermes_root)

    # Pantheon-safe default for qualification: structural observability only.
    os.environ["HERMES_LANGFUSE_CAPTURE"] = "metadata"
    secret = "sk-proj-THIS-MUST-NOT-LEAVE-THE-PROCESS"
    payload = {
        "prompt": f"synthetic prompt {secret}",
        "tool_result": "synthetic client dossier content",
    }
    captured = plugin._capture_content(payload)
    serialized = json.dumps(captured, sort_keys=True)
    assert secret not in serialized
    assert "synthetic client dossier content" not in serialized
    assert captured.get("omitted") is True
    assert captured.get("type") == "object"

    # Missing credentials must be fail-open for Hermes execution.
    for key in (
        "HERMES_LANGFUSE_PUBLIC_KEY",
        "HERMES_LANGFUSE_SECRET_KEY",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
    ):
        os.environ.pop(key, None)
    plugin._LANGFUSE_CLIENT = None
    assert plugin._get_langfuse() is None

    # Verify self-hosted configuration is accepted without contacting a server.
    constructed = {}

    class FakeLangfuse:
        def __init__(self, **kwargs):
            constructed.update(kwargs)

        def flush(self):
            return None

    plugin.Langfuse = FakeLangfuse
    plugin._LANGFUSE_CLIENT = None
    os.environ["HERMES_LANGFUSE_PUBLIC_KEY"] = "pk-lf-synthetic-pantheon-q1"
    os.environ["HERMES_LANGFUSE_SECRET_KEY"] = "sk-lf-synthetic-pantheon-q1"
    os.environ["HERMES_LANGFUSE_BASE_URL"] = "http://127.0.0.1:3000"
    os.environ["HERMES_LANGFUSE_ENV"] = "qualification"
    os.environ["HERMES_LANGFUSE_RELEASE"] = "pantheon-q1"
    os.environ["HERMES_LANGFUSE_SAMPLE_RATE"] = "0.25"
    client = plugin._get_langfuse()
    assert client is not None
    assert constructed["base_url"] == "http://127.0.0.1:3000"
    assert constructed["environment"] == "qualification"
    assert constructed["release"] == "pantheon-q1"
    assert constructed["sample_rate"] == 0.25

    result = {
        "kind": "hermes_langfuse_q1_acceptance",
        "status": "passed",
        "capture_mode": plugin._capture_mode(),
        "content_exported": False,
        "missing_credentials_block_hermes": False,
        "self_hosted_base_url_accepted": True,
        "langfuse_is_authority": False,
        "evidence_admitted": False,
        "pantheon_state_mutated": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
