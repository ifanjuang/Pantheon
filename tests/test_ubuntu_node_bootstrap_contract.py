from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deployment" / "ubuntu"
INSTALL = DEPLOY / "install-node"
UPDATE = DEPLOY / "update-node"
SKILL_SYNC = DEPLOY / "sync-hermes-governed-skills"
RELEASE = DEPLOY / "release.env"
README = DEPLOY / "README.md"
HERMES_LOCAL_COMPOSE = DEPLOY / "compose.hermes-local.yaml"
WORKSPACE_COCKPIT_COMPOSE = DEPLOY / "compose.workspace-cockpit-local.yaml"
WORKSPACE_COCKPIT_TAILSCALE = DEPLOY / "compose.workspace-cockpit-tailscale.yaml"
CONFIGURE_DOCLING = DEPLOY / "configure-docling-local"
CONFIGURE_WORKSPACE_COCKPIT = DEPLOY / "configure-workspace-cockpit-local"
CONFIGURE_AFFAIRES_NAS_MOUNT = DEPLOY / "configure-affaires-nas-mount"
CONFIGURE_HERMES_ACTIVITY = DEPLOY / "configure-hermes-activity-projection"
def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_bootstrap_scripts_are_shell_syntax_valid() -> None:
    scripts = (
        INSTALL,
        UPDATE,
        SKILL_SYNC,
        CONFIGURE_DOCLING,
        CONFIGURE_WORKSPACE_COCKPIT,
        CONFIGURE_AFFAIRES_NAS_MOUNT,
        CONFIGURE_HERMES_ACTIVITY,
    )
    for script in scripts:
        assert script.exists()
        subprocess.run(["bash", "-n", str(script)], check=True)


def test_docling_native_service_binds_to_loopback() -> None:
    text = _text(CONFIGURE_DOCLING)
    assert "docling-mcp-server --transport streamable-http --host 127.0.0.1 --port 8020" in text
    assert "docling-mcp-server --transport streamable-http --host 0.0.0.0" not in text


def test_governed_projection_keeps_delegation_explicit_and_bounded() -> None:
    text = _text(CONFIGURE_HERMES_ACTIVITY)
    assert "--enable-bounded-delegation requires --enable-clarify" in text
    assert "max_concurrent_children: 1" in text
    assert "max_iterations: 12" in text
    assert "child_timeout_seconds: 180" in text
    assert "max_spawn_depth: 1" in text
    assert "orchestrator_enabled: false" in text
    assert "inherit_mcp_toolsets: false" in text
    assert "subagent_auto_approve: false" in text
    assert 'config set --force delegation "$updated"' in text
    assert "tools enable --platform cli skills delegation" in text


def test_affaires_mount_configuration_is_generic_and_keeps_secrets_external() -> None:
    text = _text(CONFIGURE_AFFAIRES_NAS_MOUNT)
    assert "--source //HOST/SHARE" in text
    assert "--prefix-path RELATIVE/PATH" in text
    assert "credentials file must be owned by root with mode 0600" in text
    assert "Options=credentials=%s" in text
    assert "Type=cifs" in text
    assert "prefixpath=%s" in text
    assert "nosuid,nodev,noexec" in text
    assert "No hostname, share, project name or folder name is built into this script" in text


def test_workspace_cockpit_compose_is_read_only_and_loopback_only() -> None:
    text = _text(WORKSPACE_COCKPIT_COMPOSE)
    assert 'WORKSPACE_COCKPIT_BIND:-127.0.0.1' in text
    assert "read_only: true" in text
    assert "no-new-privileges:true" in text
    assert "cap_drop:" in text and "- ALL" in text
    assert "group_add:" in text
    assert "${AFFAIRES_GID:?set AFFAIRES_GID to the Linux-mounted NAS AFFAIRES group id}" in text
    affaires_mount = "${PROJECTS_ROOT:?set PROJECTS_ROOT to the Linux-mounted NAS AFFAIRES path}:/workspace/affaires:ro"
    assert text.count(affaires_mount) == 2
    assert "workspace-producer:" in text
    assert 'entrypoint: ["/opt/hermes/.venv/bin/python", "/app/producer_daemon.py"]' in text
    assert "--projection-only" in text
    assert "workspace-cockpit-state:/state:ro" in text
    assert "/srv/pantheon/obsidian" not in text
    assert '127.0.0.1:${ROLE_TRACE_ATTACH_PORT:-8190}:8190' in text
    assert "HERMES_ROLE_TRACE_API_KEY" in text
    assert "ROLE_TRACE_ATTACH_KEY" in text
    assert "ROLE_TRACE_READ_KEY" in text
    assert "WORKSPACE_HINDSIGHT_URL" in text
    assert "WORKSPACE_HINDSIGHT_BANK_ID" in text
    assert "WORKSPACE_HINDSIGHT_MAX_FILE_MB" in text
    assert "WORKSPACE_HINDSIGHT_SETTLE_OBSERVATIONS" in text
    assert "WORKSPACE_HINDSIGHT_SOURCE_KIND" in text
    assert "WORKSPACE_EXCLUDED_FOLDERS" in text
    assert "network_mode: host" in text
    assert "Affaires=/workspace/affaires" in text
    assert 'WORKSPACE_RECONCILE_SECONDS:-3600' in text
    assert 'WORKSPACE_HINDSIGHT_BANK_ID:-PROJECTS' in text
    assert 'WORKSPACE_HINDSIGHT_SETTLE_OBSERVATIONS:-2' in text
    assert 'WORKSPACE_HINDSIGHT_SOURCE_KIND:-project-sync' in text


def test_workspace_cockpit_systemd_installer_keeps_cockpit_optional() -> None:
    text = _text(CONFIGURE_WORKSPACE_COCKPIT)
    assert "--enable-producer" in text
    assert "--enable-cockpit" in text
    assert "Requires=pantheon-affaires-producer.service" in text
    assert "systemctl enable --now pantheon-affaires-producer.service" in text
    assert "systemctl enable pantheon-workspace-cockpit.service" in text
    assert "systemctl restart pantheon-workspace-cockpit.service" in text
    assert "if ((ENABLE_PRODUCER)); then" in text
    assert "if ((ENABLE_COCKPIT)); then" in text


def test_hindsight_file_retain_runtime_posture_is_explicit() -> None:
    text = _text(HERMES_LOCAL_COMPOSE)
    assert "HINDSIGHT_API_FILE_PARSER: markitdown" in text
    assert "HINDSIGHT_API_RETAIN_MISSION:" in text
    assert "revision/index/version token" in text
    assert "revision-history or revision-table entries" in text
    assert "Never infer document chronology" in text
    assert "preserve an unresolved reference instead of guessing" in text
    assert 'HINDSIGHT_API_FILE_DELETE_AFTER_RETAIN: "true"' in text
    assert 'HINDSIGHT_API_FILE_PARSER_MARKITDOWN_OCR_ENABLED: "false"' in text
    assert 'HINDSIGHT_API_STORE_DOCUMENT_TEXT: "true"' in text
    assert "shm_size: 1gb" in text


def test_local_hindsight_limits_llm_concurrency_for_single_ollama_model() -> None:
    text = _text(HERMES_LOCAL_COMPOSE)
    assert 'HINDSIGHT_API_WORKER_MAX_SLOTS: "2"' in text
    assert 'HINDSIGHT_API_WORKER_CONSOLIDATION_RESERVED_SLOTS: "1"' in text
    assert 'HINDSIGHT_API_LLM_MAX_CONCURRENT: "1"' in text
    assert 'HINDSIGHT_API_RETAIN_LLM_MAX_CONCURRENT: "1"' in text
    assert 'HINDSIGHT_API_CONSOLIDATION_LLM_MAX_CONCURRENT: "1"' in text
    assert 'HINDSIGHT_API_MENTAL_MODEL_REFRESH_LLM_MAX_CONCURRENT: "1"' in text


def test_workspace_cockpit_remote_access_uses_pinned_userspace_tailscale() -> None:
    release = _text(RELEASE)
    compose = _text(WORKSPACE_COCKPIT_TAILSCALE)
    assert "RELEASE_TAILSCALE_IMAGE=tailscale/tailscale:v" in release
    assert "${RELEASE_TAILSCALE_IMAGE:" in compose
    assert 'TS_USERSPACE: "true"' in compose
    assert "/dev/net/tun" not in compose
    assert "network_mode: host" not in compose
    assert "TS_AUTHKEY" not in compose
    assert "pantheon-cockpit-tailscale-state" in compose


def test_install_defaults_fail_private_and_keep_optional_services_inactive() -> None:
    text = _text(INSTALL)
    assert 'NODE_BIND_ADDRESS="127.0.0.1"' in text
    assert 'defaults: Ollama API bind=$NODE_BIND_ADDRESS' in text
    assert 'defaults: Hermes bind=$NODE_BIND_ADDRESS' not in text
    assert "ENABLE_HINDSIGHT=0" in text
    assert "livesync" not in text.lower()
    assert "couchdb" not in text.lower()
    assert "installed != activated" in text
    assert "activated != task-authorized" in text
    assert "require_native_runtimes" in text
    assert "pantheon-hermes-native.service" in text
    assert "ensure_docker" not in text
    assert "docker compose" not in text
    assert "write_compose" not in text
    assert "start_containers" not in text


def test_install_service_users_can_traverse_managed_runtime_paths() -> None:
    text = _text(INSTALL)
    assert 'install -d -m 0711 "$APP_ROOT"' in text
    assert 'install -d -m 0711 "$AI_ROOT/models" "$AI_ROOT/cache"' in text
    assert 'install -d -m 0755 "$UV_PYTHON_INSTALL_DIR"' in text
    assert 'UV_PYTHON_INSTALL_DIR="$APP_ROOT/python"' in text
    assert "export UV_PYTHON_INSTALL_DIR" in text
    assert 'Environment="OLLAMA_MODELS=$AI_ROOT/models/ollama"' in text
    assert '"$APP_ROOT/uv/bin/uv" python install "$POLICY_PYTHON"' in text
    assert '"$APP_ROOT/uv/bin/uv" venv --python "$managed_python" "$STATE_ROOT/policy-venv"' in text


def test_active_node_profile_excludes_comfyui_but_keeps_policy_python() -> None:
    install = _text(INSTALL)
    update = _text(UPDATE)
    release = _text(RELEASE)
    readme = _text(README)

    for text, path in (
        (install, INSTALL),
        (update, UPDATE),
        (release, RELEASE),
        (readme, README),
    ):
        assert "comfyui" not in text.lower(), path

    # The active install profile has no ComfyUI checkout, venv, service,
    # output/cache directories, or PyTorch-specific release pins.
    for absent in (
        "install_comfyui",
        "Comfy-Org/ComfyUI",
        "comfyui.service",
        "comfyui-output",
        "cache/huggingface",
        "TORCH_VERSION",
        "TORCHVISION_VERSION",
        "TORCHAUDIO_VERSION",
        "TORCH_INDEX",
    ):
        assert absent.lower() not in install.lower()
        assert absent.lower() not in release.lower()

    # The updater exposes only the remaining supported component families and
    # has no checkout, dependency, service, or restart path for ComfyUI.
    for absent in (
        "comfyui",
        "torch",
        "systemctl stop comfyui",
        "systemctl restart comfyui",
    ):
        assert absent.lower() not in update.lower()

    assert "RELEASE_POLICY_PYTHON=" in _text(RELEASE)
    assert "RELEASE_POLICY_PYTHON:?release.env missing RELEASE_POLICY_PYTHON" in _text(INSTALL)

    install_help = subprocess.run(["bash", str(INSTALL), "--help"], text=True, capture_output=True)
    update_help = subprocess.run(["bash", str(UPDATE), "--help"], text=True, capture_output=True)
    assert install_help.returncode == 0
    assert update_help.returncode == 0
    assert "--comfy-bind" not in install_help.stdout
    assert "--component all|pantheon|ollama" in update_help.stdout

    rejected_install = subprocess.run(
        ["bash", str(INSTALL), "--comfy-bind", "127.0.0.1"],
        text=True,
        capture_output=True,
    )
    rejected_update = subprocess.run(
        ["bash", str(UPDATE), "--component", "comfyui", "--check"],
        text=True,
        capture_output=True,
    )
    assert rejected_install.returncode != 0
    assert "unknown argument: --comfy-bind" in rejected_install.stderr
    assert rejected_update.returncode != 0
    assert "unsupported component: comfyui" in rejected_update.stderr


def test_install_apply_requires_reviewed_ubuntu_and_immutable_pantheon_commit() -> None:
    text = _text(INSTALL)
    assert '--apply is reviewed only for Ubuntu $TARGET_UBUNTU; detected $OS_VERSION' in text
    assert '[[ "$RESOLVED_PANTHEON_COMMIT" =~ ^[0-9a-f]{40}$ ]]' in text
    assert "PANTHEON_COMMIT must resolve to a full 40-character lowercase commit SHA" in text
    assert "--apply will refuse this host" in text


def test_release_lock_has_no_floating_latest_or_unconsumed_runtime_pin() -> None:
    text = _text(RELEASE)

    assert ":latest" not in text
    assert "RELEASE_LIVESYNC" not in text
    assert "RELEASE_COUCHDB" not in text
    # Hindsight is managed as a native service; image pins remain in the
    # external qualification catalog and are not deployment inputs here.
    assert "RELEASE_HINDSIGHT_IMAGE=" not in text

def test_release_lock_curates_governed_hermes_skills_without_exposing_all_templates() -> None:
    text = _text(RELEASE)
    line = next(
        line for line in text.splitlines()
        if line.startswith("RELEASE_HERMES_GOVERNED_SKILLS=")
    )
    for name in (
        "project-context",
        "pantheon-activity-projection",
        "pantheon-request-intake",
        "source-research",
    ):
        assert name in line
    assert "templates/hermes/skills" not in line


def test_bootstrap_scripts_have_one_reviewed_target_owner() -> None:
    """Scripts must consume release.env, not carry a second pin set in fallbacks."""
    for script in (INSTALL, UPDATE):
        text = _text(script)
        assert 'RELEASE_LOCK="$SCRIPT_DIR/release.env"' in text
        assert 'source "$RELEASE_LOCK"' in text
        assert "reviewed deployment lock is missing" in text
        assert "RELEASE_HINDSIGHT_IMAGE:-" not in text
        assert "RELEASE_LIVESYNC" not in text
        assert "RELEASE_COUCHDB" not in text


def test_bootstrap_scripts_fail_closed_when_release_lock_is_missing(tmp_path: Path) -> None:
    for source in (INSTALL, UPDATE):
        script = tmp_path / source.name
        shutil.copy2(source, script)
        result = subprocess.run(
            ["bash", str(script), "--doctor" if source == INSTALL else "--check"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode != 0
        assert "reviewed deployment lock is missing" in result.stderr


def test_governed_skill_sync_uses_target_checkout_and_read_only_external_dir() -> None:
    text = _text(SKILL_SYNC)
    assert 'RELEASE_LOCK="$CHECKOUT/deployment/ubuntu/release.env"' in text
    assert 'RELEASE_HERMES_GOVERNED_SKILLS' in text
    assert 'HOST_SKILLS_ROOT="$STATE_ROOT/hermes-governed-skills"' in text
    assert 'HERMES_USER="${HERMES_USER:-pantheon-hermes}"' in text
    assert 'HERMES_HOME="$STATE_ROOT/hermes"' in text
    assert '"$HERMES_BIN" "$@"' in text
    assert 'config get skills.external_dirs --json' in text
    assert 'config set skills.external_dirs "$merged"' in text
    assert 'find "$src" -type l' in text
    assert 'find "$stage" -type d -exec chmod 0555' in text
    assert 'find "$stage" -type f -exec chmod 0444' in text
    assert 'docker ' not in text
    assert "hermes profile create" not in text
    assert "available skill != skill used" in text
    assert "projection != persistence" in text


def test_governed_skill_sync_keeps_rollback_for_any_failure() -> None:
    text = _text(SKILL_SYNC)
    cleanup = text.split("cleanup() {", 1)[1].split('\nstage="$(mktemp', 1)[0]
    assert 'original_dirs=""' in text
    assert "profile_config_touched=0" in text
    assert "profile_restore_failed=0" in text
    assert 'config set skills.external_dirs "$original_dirs"' in text
    assert 'mv "$old" "$HOST_SKILLS_ROOT"' in text
    assert "leaving the new skill projection in place because profile rollback failed" in text
    assert "if ((status != 0)); then" in cleanup
    assert 'else\n    rm -rf "$old"' in cleanup
    assert 'restart_attempted=1\n  systemctl restart pantheon-hermes-native.service' in text


def test_pantheon_update_rolls_back_package_link_and_hermes_projection() -> None:
    text = _text(UPDATE)
    assert 'trap update_exit EXIT' in text
    assert 'PANTHEON_TRANSACTION_ACTIVE=1' in text
    assert 'PANTHEON_PACKAGE_INSTALL_ATTEMPTED=1' in text
    assert 'PANTHEON_LINK_SWITCH_ATTEMPTED=1' in text
    assert 'PANTHEON_SKILLS_SYNC_ATTEMPTED=1' in text
    assert 'PANTHEON_VERSION_WRITE_ATTEMPTED=1' in text
    assert '"$PANTHEON_PREVIOUS_CHECKOUT/mcp-server"' in text
    assert '"$PANTHEON_PREVIOUS_CURRENT_LINK" "$PANTHEON_ROOT/current"' in text
    assert '"$checkpoint/hermes-pantheon-governed/config.yaml"' in text
    assert '"$checkpoint/hermes-governed-skills" "$projection"' in text
    assert 'set_version PANTHEON_COMMIT "$PANTHEON_PREVIOUS_COMMIT_RECORD"' in text
    assert 'Pantheon rollback is incomplete; retain and inspect checkpoint' in text


def test_policy_package_validation_never_launches_the_stdio_server() -> None:
    # The entry point ignores --help and serves stdio MCP, which blocks an
    # unattended update; validation imports the package against one checkout.
    for script in (INSTALL, UPDATE):
        text = _text(script)
        assert 'pantheon-mcp-server" --help' not in text
        assert 'PANTHEON_REPO_PATH="$1"' in text
        assert "</dev/null >/dev/null" in text
    assert 'validate_policy_package "$target"' in _text(INSTALL)
    update = _text(UPDATE)
    assert 'validate_policy_package "$target"' in update
    assert 'validate_policy_package "$PANTHEON_PREVIOUS_CHECKOUT"' in update


def test_release_and_policy_package_stay_readable_by_service_users() -> None:
    # Hermes runs the policy MCP as its own user from the pinned release; a
    # restrictive root umask must not leave either unreadable to it.
    install = _text(INSTALL)
    update = _text(UPDATE)
    assert 'install -d -m 0755 "$PANTHEON_ROOT"' in install
    assert 'install -d -m 0750 "$CONFIG_ROOT"\n' in install
    for text in (install, update):
        assert 'chmod -R u+rwX,go+rX,go-w "$1" "$STATE_ROOT/policy-venv"' in text
        assert text.index('publish_release_readable "$target"') < text.index('validate_policy_package "$target"')
    assert 'publish_release_readable "$PANTHEON_PREVIOUS_CHECKOUT"' in update
    readme = _text(README)
    assert "command: /srv/pantheon/policy-venv/bin/pantheon-mcp-server" in readme
    assert "PANTHEON_REPO_PATH: /opt/pantheon/current" in readme


def test_private_repository_can_use_a_local_operator_checkout() -> None:
    for script in (INSTALL, UPDATE):
        text = _text(script)
        assert "git -c safe.directory='*' \"$@\"" in text
        assert 'if [[ -d "$source" ]]' in text
    assert "PANTHEON_REPOSITORY_OVERRIDE=<local operator checkout>" in _text(UPDATE)


def test_install_and_pantheon_update_sync_governed_skills_without_creating_profile() -> None:
    install = _text(INSTALL)
    update = _text(UPDATE)
    call = 'bash "$SCRIPT_DIR/sync-hermes-governed-skills"'
    assert call in install
    assert call in update
    assert "hermes profile create" not in install
    assert "hermes profile create" not in update


def test_updater_checkpoints_governed_skill_projection_before_mutation() -> None:
    text = _text(UPDATE)
    assert '$STATE_ROOT/hermes/profiles/pantheon-governed/config.yaml' in text
    assert '$checkpoint/hermes-pantheon-governed/config.yaml' in text
    assert '$STATE_ROOT/hermes-governed-skills' in text
    assert '$checkpoint/hermes-governed-skills' in text


def test_updater_never_follows_main_or_silently_updates_stateful_services() -> None:
    text = _text(UPDATE)
    assert "git pull" not in text
    assert "PANTHEON_COMMIT_OVERRIDE" in text
    assert "docker " not in text
    assert "retire_legacy_workspace_sync_runtime" not in text
    assert "--component all|pantheon|ollama" in text
    assert "available upstream != qualified for this node" in text
    assert "successful update != activation or task authorization" in text
    assert 'install -d -m 0700 "$checkpoint"' in text
    assert "umask 077" in text


def test_operator_readme_preserves_authority_and_storage_boundaries() -> None:
    text = _text(README)
    assert "Hermes execution itself does not make a NAS an authority dependency." in text
    assert "The selected professional Workspace path uses the reviewed NAS `/AFFAIRES` tree as its source filesystem" in text
    assert "filesystem mirror != governed identity" in text
    assert "installed != activated" in text
    assert "Syncthing" in text and "optional" in text


def test_ollama_keeps_the_shared_model_resident_between_bursts() -> None:
    text = _text(INSTALL)
    assert 'Environment="OLLAMA_KEEP_ALIVE=30m"' in text
    assert 'Environment="OLLAMA_MAX_LOADED_MODELS=1"' in text
    assert 'Environment="OLLAMA_CONTEXT_LENGTH=32768"' in text


def test_docling_ocr_is_opt_in() -> None:
    text = CONFIGURE_DOCLING.read_text(encoding="utf-8")
    assert "OCR=false" in text and "--ocr) OCR=true" in text
    assert "DOCLING_MCP_DO_OCR=$OCR" in text


def test_uv_installs_copy_instead_of_hard_linking_the_shared_cache() -> None:
    # A chown of one venv must not re-own files shared with Hermes' venv (seen on a node).
    for name in ("configure-docling-local", "configure-vault-read-local",
                 "configure-hindsight-project-router-local", "install-node", "update-node"):
        assert "export UV_LINK_MODE=copy" in (DEPLOY / name).read_text(encoding="utf-8"), name
    router = (DEPLOY / "configure-hindsight-project-router-local").read_text(encoding="utf-8")
    assert router.index("pip install --reinstall") < router.index('chown -R "$SERVICE_USER')
