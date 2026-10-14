from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import getpass


ROOT = Path(__file__).resolve().parents[1]
OBSERVER = ROOT / "deployment" / "ubuntu" / "observe-hermes-runtime"
def _text() -> str:
    return OBSERVER.read_text(encoding="utf-8")


def test_runtime_observer_is_shell_syntax_valid() -> None:
    assert OBSERVER.exists()
    subprocess.run(["bash", "-n", str(OBSERVER)], check=True)


def test_runtime_observer_reads_native_service_and_runtime_version() -> None:
    text = _text()

    assert 'HERMES_SERVICE="${HERMES_SERVICE:-pantheon-hermes-native.service}"' in text
    assert 'systemctl show "$HERMES_SERVICE"' in text
    assert 'recorded_version' in text
    assert 'native_service:' in text
    assert 'observation_source:"native_systemd_and_profile_snapshot"' in text
    assert 'run_hermes --version' in text


def test_runtime_observer_targets_post_1057_profile_surface() -> None:
    text = _text()

    assert 'PROFILE_ROOT="$HERMES_HOME/profiles/$PROFILE"' in text
    assert 'profile_host_observation="not_observable"' in text
    assert 'profile_root_present=null' in text
    assert 'host_observation:$profile_host_observation' in text
    assert 'visible_to_service:$profile_visible_to_service' in text
    assert 'config_digest' in text
    assert 'soul_digest' in text
    assert 'profile_snapshot_digest' in text
    assert 'no_bundled_skills_marker' in text
    assert 'local_skills:$profile_skills' in text
    assert 'skill_md_digest' in text

    # The pre-#1057 external skill projection path is no longer the owner of
    # the effective governed profile surface.
    assert "/opt/pantheon-skills" not in text
    assert "hermes-governed-skills" not in text
    assert "RELEASE_HERMES_GOVERNED_SKILLS" not in text
    assert "skills.external_dirs" not in text
    assert "docker" not in text.lower()


def test_runtime_observer_remains_observation_only() -> None:
    text = _text()

    forbidden = (
        "systemctl start",
        "systemctl restart",
        "systemctl stop",
        "config set",
        "profile create",
        "plugin install",
        "skill install",
        "/v1/runs",
    )
    for token in forbidden:
        assert token not in text

    assert 'write_effect:false' in text
    assert 'activation_changed:false' in text
    assert 'authority_effect:"none"' in text
    assert 'technical_receipt_is_evidence:false' in text
    assert '"profile snapshot != profile route active for a run"' in text
    assert '"profile-local skill != skill used"' in text
    assert '"runtime observation != Evidence"' in text


def test_runtime_observer_does_not_dump_secrets_or_environment() -> None:
    text = _text()

    assert "env |" not in text
    assert "printenv" not in text
    assert "secrets.env" not in text


def test_runtime_observer_builds_bounded_receipt_from_native_profile(tmp_path: Path) -> None:
    """Drive the observer against fake systemd and Hermes executables."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_systemctl = fake_bin / "systemctl"
    fake_systemctl.write_text(
        """#!/usr/bin/env bash
set -eu
case " $* " in
  *" --property=ActiveState "*) printf 'active\\n' ;;
  *" --property=SubState "*) printf 'running\\n' ;;
  *" --property=ExecMainStartTimestamp "*) printf 'Sat 2026-10-10 10:00:00 CEST\\n' ;;
  *) printf 'unexpected fake systemctl call: %s\\n' "$*" >&2
  exit 64
  ;;
esac
""",
        encoding="utf-8",
    )
    fake_systemctl.chmod(0o755)
    fake_hermes = fake_bin / "hermes"
    fake_hermes.write_text(
        """#!/usr/bin/env bash
set -eu
if [[ "${1:-}" == --version ]]; then
  printf '0.0.0-fixture\\n'
elif [[ "${1:-}" == -p && "${3:-}" == config ]]; then
  printf '"auto"\\n'
elif [[ "${1:-}" == -p && "${3:-}" == tools ]]; then
  printf 'enabled skills\\nenabled code_execution\\ndisabled delegation\\nenabled clarify\\n'
elif [[ "${1:-}" == -p && "${3:-}" == bundles ]]; then
  printf 'private-bundle-name-should-never-appear\\n'
else
  exit 64
fi
""",
        encoding="utf-8",
    )
    fake_hermes.chmod(0o755)

    config_root = tmp_path / "etc-pantheon"
    config_root.mkdir()
    (config_root / "versions.env").write_text(
        "HERMES_VERSION=0.0.0-fixture\n", encoding="utf-8"
    )

    state_root = tmp_path / "state"
    profile = state_root / "hermes" / "profiles" / "pantheon-governed"
    skill = profile / "skills" / "pantheon-governed-method"
    skill.mkdir(parents=True)
    (profile / "config.yaml").write_text("tools:\n  tool_search:\n    enabled: auto\n", encoding="utf-8")
    (profile / "SOUL.md").write_text("governed profile\n", encoding="utf-8")
    (skill / "SKILL.md").write_text("# governed method\n", encoding="utf-8")
    (profile / "skills" / ".no-bundled-skills").touch()

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{fake_bin}:{env['PATH']}",
            "CONFIG_ROOT": str(config_root),
            "STATE_ROOT": str(state_root),
            "HERMES_USER": getpass.getuser(),
            "HERMES_USER_HOME": str(tmp_path),
            "HERMES_BIN": str(fake_hermes),
        }
    )
    completed = subprocess.run(
        [str(OBSERVER)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    receipt = json.loads(completed.stdout)

    assert receipt["native_service"]["active"] is True
    assert receipt["native_service"]["active_state"] == "active"
    assert receipt["native_service"]["sub_state"] == "running"
    assert receipt["deployment"]["recorded_version"] == "0.0.0-fixture"
    assert receipt["deployment"]["recorded_version_matches_runtime"] is True
    assert receipt["profile"]["host_root_present"] is True
    assert receipt["profile"]["host_observation"] == "observed_present"
    assert receipt["profile"]["visible_to_service"] is True
    assert receipt["profile"]["snapshot_digest"].startswith("sha256:")
    assert receipt["profile"]["no_bundled_skills_marker"] is True
    assert [item["name"] for item in receipt["profile"]["local_skills"]] == [
        "pantheon-governed-method"
    ]
    assert receipt["runtime_version"] == {"status": "observed", "value": "0.0.0-fixture"}
    assert receipt["native_capabilities"] == {
        "requested": False,
        "status": "not_requested",
        "tool_search_mode": None,
        "configured_cli_toolsets": {},
        "bundles_list": "not_requested",
    }

    capabilities_run = subprocess.run(
        [str(OBSERVER), "--capabilities"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    capabilities = json.loads(capabilities_run.stdout)
    assert capabilities["native_capabilities"] == {
        "requested": True,
        "status": "attempted",
        "tool_search_mode": "auto",
        "configured_cli_toolsets": {
            "skills": "configured_enabled",
            "clarify": "configured_enabled",
            "code_execution": "configured_enabled",
            "delegation": "configured_disabled",
            "cronjob": "unknown",
        },
        "bundles_list": "command_available",
    }
    assert "private-bundle-name-should-never-appear" not in capabilities_run.stdout
    assert receipt["write_effect"] is False
    assert receipt["activation_changed"] is False
    assert receipt["authority_effect"] == "none"
    assert receipt["technical_receipt_is_evidence"] is False
