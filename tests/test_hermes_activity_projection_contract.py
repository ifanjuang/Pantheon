from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "templates/hermes/skills/pantheon-activity-projection/SKILL.md"
SOUL_APPEND = ROOT / "templates/hermes/profiles/pantheon-governed/SOUL.append.md"
CONFIGURE = ROOT / "deployment/ubuntu/configure-hermes-activity-projection"


def test_activity_projection_skill_has_bounded_visible_contract() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "name: pantheon-activity-projection" in text
    assert "status: candidate_template_only" in text
    assert "governed_by: docs/governance/CONVERSATION_ACTIVITY_PROJECTION.md" in text
    assert "trace_reference:" not in text
    assert "summary rationale != hidden chain-of-thought" in text
    assert "one compact initial plan" in text
    assert "only meaningful milestones" in text
    assert "do not invent one merely" in text
    assert "Pantheon Roles are governance jurisdictions, not runtime identities" in text
    assert "Use `⚙ Hermes` for observable runtime milestones" in text
    assert "Posture: Ulysse" in text
    assert "Posture: Nestor" in text
    assert "Posture: Dédale" in text
    assert "Posture: Cassandre" in text
    assert "posture selected != Pantheon Role activated" in text
    assert "complex-presentation.md" in text
    for legacy_label in (
        "🦉 Athena", "🔎 Argos", "⚖ Themis", "☀ Apollo",
        "🛠 Hephaistos", "📨 Iris", "⚡ Zeus", "🧠 Mnemosyne",
    ):
        assert legacy_label not in text


def test_governed_profile_supplement_requires_progress_without_private_reasoning() -> None:
    text = SOUL_APPEND.read_text(encoding="utf-8")
    assert "You are direct, calm and professionally precise" in text
    assert "Do not expose private reasoning" in text
    assert "load `pantheon-governed-method` before material\nwork" in text
    assert "`pantheon-activity-projection` when progress should be visible" in text
    assert "skills own procedure" in text
    assert "Pantheon viewpoints and delegated-intervenant labels are optional observable\nlabels, never agents, permissions or decorative prose" in text
    assert "retrieved source material, derived calculations, candidate\noutputs and authorization separate" in text
    assert len(text.split()) < 400


def test_governed_profile_supplement_bounds_professional_answers() -> None:
    text = SOUL_APPEND.read_text(encoding="utf-8")
    for block in ("**Réponse**", "**Conditions**", "**Vigilance**", "**Sources**", "**Et ensuite**"):
        assert block in text
    assert "search the admitted sources\nbefore answering" in text
    assert "Put quotation marks only around a `quote` returned by a tool" in text
    assert "Never write a standard, article, edition, page or value not read" in text
    assert "`assumption_only`" in text and "never `validated_for_scope`" in text
    assert "at most four follow-ups drawn from this answer's own" in text
    assert "« Autre / reformuler »" in text
    assert "Use `clarify` only after the answer is shown" in text
    assert "about six tool calls\nbefore a first answer" in text and "never item by item" in text
    assert "under 200 words besides Sources" in text
    assert "« schéma illustratif »" in text and "no dimension not read" in text


def test_linux_configurator_is_idempotent_and_keeps_a_backup() -> None:
    text = CONFIGURE.read_text(encoding="utf-8")
    subprocess.run(["bash", "-n", str(CONFIGURE)], check=True)
    assert "--check" in text and "--apply" in text
    assert "BEGIN PANTHEON ACTIVITY PROJECTION" in text
    assert "backups/hermes-activity-" in text
    assert "diff -qr" in text
    assert "systemctl restart pantheon-hermes-native.service" in text
    assert "docker restart pantheon-hermes" not in text
    assert "projection != persistence" in text
    assert "check_profile_display" in text
    assert "apply_profile_display" in text
    assert 'config set display.interim_assistant_messages true' in text
    assert 'config set display.show_reasoning false' in text
    assert 'config set plugins.stream_reasoning_deltas false' in text
    assert 'tools enable --platform cli skills delegation' in text
    assert 'for toolset in delegation skills' in text
    assert 'for attempt in 1 2 3' in text
    for skill in (
        "administrative-form-review",
        "contract-clause-review",
        "construction-cost-review",
        "construction-schedule-review",
        "external-commitment-guard",
        "project-context",
        "vault-search",
        "pantheon-activity-projection",
        "pantheon-governed-method",
        "pantheon-request-intake",
        "site-report-review",
        "source-research",
        "technical-standard-review",
    ):
        assert skill in text
    assert "rsync -a --delete --exclude '__pycache__/'" in text
    assert "--with-vault-adapter" in text
    assert "optional contextual adapter" in text
    assert 'die "--bind-local-mcp requires --with-vault-adapter"' in text


def test_whatsapp_governed_routing_is_explicit_scoped_and_non_destructive() -> None:
    text = CONFIGURE.read_text(encoding="utf-8")
    assert "--route-whatsapp" in text
    assert "--whatsapp-chat-id" in text
    assert "--all-authorized-whatsapp" in text
    assert '--route-whatsapp requires --whatsapp-chat-id or --all-authorized-whatsapp' in text
    assert '[$route] + map(select(.name != "pantheon-governed-whatsapp"))' in text
    assert 'map(select(.name != "pantheon-governed-whatsapp")) + [$route]' in text
    assert 'if index($profile) then . else . + [$profile] end' in text
    assert 'if ((update_allowlist == 1))' in text
    assert '. == null or . == "null"' in text
    assert 'refusing to replace it' in text
    assert 'Config key not set: $key' in text
    assert 'cp -a "$CONFIG_TARGET" "$backup_root/config.yaml"' in text


def test_whatsapp_projection_uses_supported_config_not_a_provider_patch() -> None:
    text = CONFIGURE.read_text(encoding="utf-8")
    assert "config set gateway.multiplex_profiles true" in text
    assert 'config set gateway.profile_routes "$merged_routes"' in text
    assert "config set display.platforms.whatsapp.show_reasoning false" in text
    assert "config set display.platforms.whatsapp.interim_assistant_messages true" in text
    assert "config set display.platforms.whatsapp.tool_progress new" in text
    assert 'config set plugins.stream_reasoning_deltas false' in text
    assert "no provider patch" in text


def test_governed_local_mcp_binding_is_explicit_filtered_and_fail_closed() -> None:
    text = CONFIGURE.read_text(encoding="utf-8")
    assert "--bind-local-mcp" in text
    assert "get_profile_optional_config_json default mcp_servers" in text
    for server in ("docling", "hindsight-project", "pantheon-policy"):
        assert server in text
    assert '"Doclin"' not in text
    assert "required local Hindsight bindings are absent; refusing partial inheritance" in text
    assert 'del(."hindsight-affaires", ."hindsight-documentaires", ."hindsight-memory")' in text
    assert 'config set --force mcp_servers "$merged"' in text
    assert 'tools enable --platform cli hindsight-project:recall_project_memory' in text
    assert 'cp -a "$PROFILE_CONFIG_TARGET" "$backup_root/profile-config.yaml"' in text
    for tool in (
        "route_governed_request",
        "evaluate_preflight",
        "prepare_task_contract_skeleton",
        "prepare_evidence_pack_skeleton",
        "plan_context_pack",
        "validate_context_pack",
    ):
        assert tool in text
    assert '"list_sources"' not in text
    assert '"prompts": false' in text
    assert '"resources": false' in text
    assert '"enabled": false' in text
    assert 'supports_parallel_tool_calls = false' in text


def test_docling_mcp_introspection_tools_are_hidden_from_governed_profile() -> None:
    text = CONFIGURE.read_text(encoding="utf-8")
    assert "DOCLING_TOOLS_JSON=" in text
    assert '.docling.tools = (' in text
    assert '"get_overview_of_document_anchors"' in text
    assert '"search_for_text_in_document_anchors"' in text
    assert '"get_text_of_document_item_at_anchor"' in text
    assert '"export_docling_document_to_markdown"' not in text
    assert '.docling.tools.include == $docling_tools' in text
    assert '.docling.tools.prompts == false' in text
    assert '.docling.tools.resources == false' in text


def test_hindsight_legacy_bindings_are_removed_from_governed_profile() -> None:
    text = CONFIGURE.read_text(encoding="utf-8")
    assert 'has("hindsight-affaires") | not' in text
    assert 'has("hindsight-documentaires") | not' in text
    assert 'has("hindsight-memory") | not' in text
    assert '."hindsight-affaires".tools.include' not in text
    assert '."hindsight-documentaires".tools.include' not in text
    assert 'HINDSIGHT_PROJECT_TOOLS_JSON=' in text
    assert '["recall_project_memory","hindsight_project_list"]' in text
    assert 'has("hindsight-project")' in text
    assert '."hindsight-project".tools.include == $project_tools' in text
    assert 'HINDSIGHT_PROJECT_MCP_URL="http://127.0.0.1:8022/mcp"' in text


def test_curated_default_capabilities_remain_bounded_and_searchable() -> None:
    text = CONFIGURE.read_text(encoding="utf-8")
    assert "--with-curated-default-skills" in text
    for skill in (
        "obsidian",
        "pdf",
        "docx",
        "xlsx",
        "powerpoint",
        "google-workspace",
        "grounded-citations",
    ):
        assert skill in text
    assert 'HERMES_SKILLS_ROOT="${HERMES_SKILLS_ROOT:-$HERMES_ROOT/skills}"' in text
    assert "from the native Hermes skill tree under HERMES_HOME/skills" in text
    assert 'rsync -a -- "$source/" "$target/"' in text
    assert 'flat_name="$HERMES_SKILLS_ROOT/$name"' in text
    assert "docker cp" not in text
    assert 'source="$flat_name"' in text
    assert 'source="$CURATED_STAGE_ROOT/$name"' in text
    assert 'source="$HERMES_ROOT/skills/$path"' not in text
    assert "tools.tool_search.enabled off" in text
    assert ".no-bundled-skills" in text
    assert "deferred tool discovery" in text


def test_optional_runtime_dependencies_are_preflighted_before_profile_mutation() -> None:
    text = CONFIGURE.read_text(encoding="utf-8")
    preflight = text.index("preflight_optional_dependencies")
    backup = text.index('stamp="$(date -u +%Y%m%dT%H%M%SZ)"')
    first_profile_install = text.index('install -d -m 0755 "$PROFILE_ROOT/skills"')
    assert preflight < backup < first_profile_install
    assert "prepare_local_mcp_selection" in text
    assert "stage_curated_default_skills" in text
    assert "preflight_whatsapp_runtime" in text
    assert '[[ -n "$LOCAL_MCP_SELECTED" ]] || die "local MCP bindings were not preflighted"' in text
    assert '[[ -n "$CURATED_STAGE_ROOT" ]] || die "curated skills were not staged"' in text


def test_work_postures_never_become_runtime_or_governance_branch_keys() -> None:
    posture_names = ("Ulysse", "Nestor", "Dédale", "Cassandre")
    executable_roots = (
        ROOT / "implementation" / "mvp_vertical",
        ROOT / "implementation" / "hermes" / "plugins",
        ROOT / "mcp-server" / "pantheon_mcp",
    )
    schema_root = ROOT / "schemas"

    checked = []
    for executable_root in executable_roots:
        if not executable_root.exists():
            continue
        for path in sorted(executable_root.rglob("*.py")):
            checked.append(path)
            text = path.read_text(encoding="utf-8")
            for posture in posture_names:
                assert posture not in text, (
                    f"presentation posture {posture!r} leaked into executable "
                    f"runtime/governance code: {path.relative_to(ROOT)}"
                )

    if schema_root.exists():
        for suffix in ("*.yaml", "*.yml", "*.json"):
            for path in sorted(schema_root.rglob(suffix)):
                checked.append(path)
                text = path.read_text(encoding="utf-8")
                for posture in posture_names:
                    assert posture not in text, (
                        f"presentation posture {posture!r} leaked into a governed "
                        f"schema: {path.relative_to(ROOT)}"
                    )

    assert checked
