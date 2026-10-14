from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "deployment" / "ubuntu" / "configure-hermes-reconciliation-profile"


def _text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_reconciliation_profile_configurator_is_shell_syntax_valid() -> None:
    assert SCRIPT.exists()
    subprocess.run(["bash", "-n", str(SCRIPT)], check=True)


def test_reconciliation_profile_configurator_keeps_activation_separate() -> None:
    text = _text()
    assert 'PROFILE="${HERMES_RECONCILIATION_PROFILE:-reconciliation}"' in text
    assert 'hermes profile create "$PROFILE" --no-skills --no-alias' in text
    assert "gateway start" not in text
    assert "gateway.multiplex_profiles" not in text
    assert "profile configured; no gateway was started and no routing was changed" in text


def test_reconciliation_profile_configurator_enforces_no_tool_boundary() -> None:
    text = _text()
    assert "config set platform_toolsets.api_server '[\"no_mcp\"]'" in text
    assert "config set --force plugins.enabled '[]'" in text
    assert "config set --force mcp_servers '{}'" in text
    assert "config set context.engine compressor" in text
    assert "config set tools.tool_search.enabled false" in text
    assert 'toolsets = get("/v1/toolsets")' in text
    assert 'if row["enabled"]' in text
    assert 'toolsets.get("object") != "list"' in text
    assert 'toolsets.get("platform") != "api_server"' in text
    assert 'not isinstance(toolsets.get("data"), list)' in text
    assert 'rows = toolsets["data"]' in text
    assert "malformed /v1/toolsets row" in text
    assert "reconciliation profile exposes enabled toolsets" in text


def test_reconciliation_profile_configurator_keeps_memory_packet_local() -> None:
    text = _text()
    assert 'config set memory.provider ""' in text
    assert "memories/MEMORY.md memories/USER.md MEMORY.md USER.md" in text
    assert '[[ -f "$root/.no-bundled-skills" ]]' in text
    assert 'test -f "$root/skills/.no-bundled-skills"' not in text
    assert "dedicated profile carries built-in memory content" in text
    assert '''[[ "$provider" == '""' || "$provider" == "null" ]]''' in text
    assert "external memory provider must be disabled" in text


def test_reconciliation_profile_configurator_requires_separate_secret_and_runtime_contract() -> None:
    text = _text()
    assert "HERMES_RECONCILIATION_API_KEY" in text
    assert 'if [[ -n "$default_key" && "$API_KEY" == "$default_key" ]]' in text
    assert 'HERMES_ENV_FILE="${HERMES_ENV_FILE:-/etc/pantheon-hermes-native.env}"' in text
    assert 'read_env_value "$HERMES_ENV_FILE" API_SERVER_KEY systemd' in text
    assert 'read_env_value "$root/.env" API_SERVER_KEY dotenv' in text
    assert 'if "\\\\" in candidate:' in text
    assert "sed -n 's/^API_SERVER_KEY=//p'" not in text
    assert "docker exec" not in text
    assert "reconciliation API key must differ from the default Hermes API key" in text
    assert '--runtime-url requires HERMES_RECONCILIATION_API_KEY' in text
    assert 'features.get("responses_api") is not True' in text
    assert 'session_delete.get("method") != "DELETE"' in text
    assert '"/api/sessions/{session_id}"' in text
    assert "configured != activated; runtime observed != task authorized; reconciliation output != Evidence" in text


def test_reconciliation_key_reader_handles_quotes_and_rejects_escapes() -> None:
    text = _text()
    start = text.index("read_env_value() {")
    end = text.index("\n}\n", start) + 2
    reader = text[start:end]

    def read_value(content: str, format_name: str) -> subprocess.CompletedProcess[str]:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as env_file:
            env_file.write(content)
            env_file.flush()
            command = f'{reader}\nread_env_value "$1" API_SERVER_KEY "$2"'
            return subprocess.run(
                ["bash", "-c", command, "bash", env_file.name, format_name],
                text=True,
                capture_output=True,
                check=False,
            )

    systemd_value = read_value('API_SERVER_KEY="contract-test-token"\n', "systemd")
    dotenv_value = read_value("API_SERVER_KEY='contract-test-token'\n", "dotenv")
    escaped_value = read_value("API_SERVER_KEY=contract\\ test\\ token\n", "systemd")

    assert systemd_value.returncode == 0
    assert systemd_value.stdout == "contract-test-token"
    assert dotenv_value.returncode == 0
    assert dotenv_value.stdout == "contract-test-token"
    assert escaped_value.returncode == 2
    assert escaped_value.stdout == ""
