from __future__ import annotations

import ast
from pathlib import Path


MVP = Path(__file__).resolve().parents[1] / "mvp_vertical"

# This complements test_consequential_mutation_inventory.py. That inventory owns
# SQL mutation/gate review. This one covers effect mechanisms that SQL/verb
# discovery cannot see: filesystem mutation and externally effectful HTTP calls,
# including public class methods.
EFFECT_INVENTORY: dict[tuple[str, str], dict[str, str]] = {
    ("cli.py", "main"): {
        "effect": "filesystem_artifact",
        "reviewed": "operator CLI may write an explicitly requested output artifact",
    },
    ("documents.py", "DoclingServeClient.convert"): {
        "effect": "external_compute",
        "reviewed": "POSTs one already-scoped source to caller-selected Docling; conversion != Evidence",
    },
    ("human_revision_upload.py", "upload_revision"): {
        "effect": "filesystem_and_sql",
        "reviewed": "retains exact uploaded bytes before the governed revision link; digest is reverified",
    },
    ("hermes_ephemeral_context.py", "cleanup_expired"): {
        "effect": "filesystem_transient_cleanup",
        "reviewed": "deletes only local transient lease directories whose recorded expiry is already past; it touches neither AFFAIRES nor Hindsight and owns no scheduler",
    },
    ("hermes_ephemeral_context.py", "create_lease"): {
        "effect": "filesystem_transient_context",
        "reviewed": "the editor-authenticated handoff route is the production caller; the module bounds TTL/count/bytes, recomputes SHA-256 and writes only to the replaceable transient root",
    },
    ("email_action_adapter.py", "archive_email_to_authorized_root"): {
        "effect": "filesystem_and_sql",
        "reviewed": "composes verified RAW retention, unassigned Source admission and one bounded visible AFFAIRES projection only after the caller has resolved an authorized server-side root; it does not write Hindsight directly",
    },
    ("email_action_adapter.py", "create_ask_lease"): {
        "effect": "filesystem_transient_context",
        "reviewed": "reuses the Pantheon-Next#1152 bounded ephemeral lease owner with provider_item roles; lease creation is transient context preparation and does not archive or dispatch Hermes",
    },
    ("email_action_adapter.py", "materialize_visible_archive"): {
        "effect": "filesystem_workspace_email_projection",
        "reviewed": "writes one escaped HTML derivative plus exact decoded attachments below an already-authorized root, refuses traversal/symlink destinations, reuses same-digest files and never deletes older attachments",
    },
    ("email_action_adapter.py", "retain_and_admit_raw_email"): {
        "effect": "filesystem_and_sql",
        "reviewed": "retains exact RFC822 bytes through Storage Object and admits one provider-scoped Source with no Project link; thread projection and Source identity remain separate",
    },
    ("storage_retention.py", "retain_exact_bytes"): {
        "effect": "filesystem_and_sql",
        "reviewed": "stages caller bytes, recomputes SHA-256 and delegates to the exact-file retention owner; it creates a verified Storage Object/location but no document-version binding",
    },
    ("storage_retention.py", "retain_exact_file"): {
        "effect": "filesystem_and_sql",
        "reviewed": "atomically retains and fully re-verifies one digest-addressed file, then records/reuses its exact Storage Object/location without manufacturing Source or Project identity",
    },
    ("storage_retention.py", "retain_document_version"): {
        "effect": "filesystem_and_sql",
        "reviewed": "retains digest-addressed exact bytes and binds them to the technical version",
    },
    ("workspace_human_note.py", "write_workspace_human_note"): {
        "effect": "filesystem_workspace_sidecar",
        "reviewed": "editor-only route writes one managed human note fragment with optimistic digest protection",
    },
    ("workspace_markdown_write.py", "create_workspace_markdown"): {
        "effect": "filesystem_workspace_markdown",
        "reviewed": "editor-only route creates one absent bounded Markdown file and rereads exact bytes",
    },
    ("workspace_markdown_write.py", "patch_workspace_markdown"): {
        "effect": "filesystem_workspace_markdown",
        "reviewed": "editor-only route patches one unique anchor under an expected source digest",
    },
    ("policy_gate.py", "HttpPolicyClient.preflight"): {
        "effect": "external_policy_query",
        "reviewed": "POST transport queries the PDP; it does not execute the requested consequential effect",
    },
    ("policy_gate.py", "HttpPolicyClient.validate_decision"): {
        "effect": "external_policy_query",
        "reviewed": "POST transport validates a decision envelope; validation != execution",
    },
    ("capability_manager.py", "HermesCapabilityExecutor.__call__"): {
        "effect": "external_capability_operation",
        "reviewed": "native capability operation transport; governed_execute must gate consequential actions first",
    },
    ("hermes_run_binding.py", "PantheonRunBridgeClient.reserve_launch"): {
        "effect": "external_control_write",
        "reviewed": "records one immutable launch reservation through the Pantheon execution seam",
    },
    ("hermes_run_binding.py", "PantheonRunBridgeClient.materialize_ephemeral_context"): {
        "effect": "external_transient_context_read",
        "reviewed": "POST is a bounded read/materialization request; the Pantheon server requires the exact live admission and launch reservation and performs no runtime dispatch or professional persistence",
    },
    ("hermes_run_binding.py", "PantheonRunBridgeClient.record_start"): {
        "effect": "external_control_write",
        "reviewed": "records one runtime start through the Pantheon execution seam",
    },
    ("hermes_run_binding.py", "PantheonRunBridgeClient.record_return"): {
        "effect": "external_control_write",
        "reviewed": "records one normalized runtime return; runtime result remains candidate material",
    },
    ("hermes_run_binding.py", "HermesRunsHttpClient.submit"): {
        "effect": "external_runtime_execution",
        "reviewed": "POST /v1/runs creates exactly one Hermes run from an admitted reservation",
    },
    ("hermes_run_binding.py", "HermesRunsHttpClient.get_status"): {
        "effect": "external_observation",
        "reviewed": "generic HTTP transport is shared with submit, but this public method performs GET-only observation",
    },
    ("hermes_run_binding.py", "RoleTraceAttachmentClient.attach"): {
        "effect": "external_presentation_write",
        "reviewed": "best-effort display attachment; failure cannot alter or retry the already registered run",
    },
    ("hermes_cli.py", "main"): {
        "effect": "operator_output_artifact",
        "reviewed": "operator CLI may persist the exact receipt returned by its selected command; orchestration is reviewed separately below",
    },
    ("hermes_distribution.py", "main"): {
        "effect": "validation_output_artifact",
        "reviewed": "distribution validation may write an explicitly requested receipt; it installs, activates and authorizes nothing",
    },
}

# Dynamic collaborator calls cannot be proven through a same-module call graph.
# Keep the orchestrators in the same owner with required calls that demonstrate
# the effect still exists. A changed orchestration must update this record.
INDIRECT_EFFECT_INVENTORY: dict[tuple[str, str], dict[str, object]] = {
    ("capability_manager.py", "governed_execute"): {
        "effect": "external_capability_operation",
        "required_calls": {"executor"},
        "reviewed": "executor is invoked only after the shared consequential gate allows the action",
    },
    ("hermes_run_binding.py", "ExternalHermesRunBinding.launch"): {
        "effect": "external_runtime_execution",
        "required_calls": {"submit", "reserve_launch", "materialize_ephemeral_context", "record_start"},
        "reviewed": "reserve -> optional exact transient materialization -> one Hermes submit -> record start; materialization failure prevents submission and ambiguous submission never auto-retries",
    },
    ("hermes_run_binding.py", "ExternalHermesRunBinding.reconcile_once"): {
        "effect": "external_control_write",
        "required_calls": {"get_status", "record_return"},
        "reviewed": "one-shot observation may record one terminal return; no polling scheduler or retry loop",
    },
    ("hermes_cli.py", "execute"): {
        "effect": "operator_external_orchestration",
        "required_calls": {"launch", "reconcile_once"},
        "reviewed": "operator launch/reconcile commands delegate only to the bounded one-shot run binding; other commands are read-only qualification/validation",
    },
}

_FILESYSTEM_ATTRS = frozenset({"write_text", "write_bytes", "unlink", "rename", "mkdir", "rmdir", "touch"})
_OS_MUTATORS = frozenset({"write", "replace", "unlink", "remove", "rename", "mkdir", "makedirs", "rmdir"})
_SHUTIL_MUTATORS = frozenset({"copy", "copy2", "copyfile", "copyfileobj", "move", "rmtree"})
_HTTP_MUTATORS = frozenset({"post", "put", "patch", "delete", "request"})
_HTTP_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def _definitions() -> dict[tuple[str, str], tuple[ast.AST, str | None]]:
    out: dict[tuple[str, str], tuple[ast.AST, str | None]] = {}
    for path in sorted(MVP.rglob("*.py")):
        relative = str(path.relative_to(MVP))
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out[(relative, node.name)] = (node, None)
            elif isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        out[(relative, f"{node.name}.{child.name}")] = (child, node.name)
    return out


def _walk_own(node: ast.AST):
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        yield child
        stack.extend(ast.iter_child_nodes(child))


def _direct_effect(node: ast.AST) -> bool:
    for child in _walk_own(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if isinstance(func, ast.Attribute):
            attr = func.attr
            if attr in _FILESYSTEM_ATTRS:
                return True
            if isinstance(func.value, ast.Name):
                if func.value.id == "os" and attr in _OS_MUTATORS:
                    return True
                if func.value.id == "shutil" and attr in _SHUTIL_MUTATORS:
                    return True
            if attr in _HTTP_MUTATORS:
                return True
        if isinstance(func, ast.Name) and func.id in {"open", "Request"}:
            if func.id == "open" and len(child.args) >= 2:
                mode = child.args[1]
                if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
                    if any(flag in mode.value for flag in "wax+"):
                        return True
            if func.id == "Request":
                for keyword in child.keywords:
                    if keyword.arg == "method" and isinstance(keyword.value, ast.Constant):
                        if str(keyword.value.value).upper() in _HTTP_METHODS:
                            return True
    return False


def _calls(node: ast.AST, *, current_file: str, current_class: str | None) -> set[tuple[str, str]]:
    calls: set[tuple[str, str]] = set()
    for child in _walk_own(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if isinstance(func, ast.Name):
            calls.add((current_file, func.id))
        elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id in {"self", "cls"} and current_class:
                calls.add((current_file, f"{current_class}.{func.attr}"))
            else:
                calls.add((f"{func.value.id}.py", func.attr))
    return calls


def _effect_closure() -> set[tuple[str, str]]:
    definitions = _definitions()
    effectful = {key for key, (node, _) in definitions.items() if _direct_effect(node)}
    changed = True
    while changed:
        changed = False
        for key, (node, current_class) in definitions.items():
            if key in effectful:
                continue
            if _calls(node, current_file=key[0], current_class=current_class) & effectful:
                effectful.add(key)
                changed = True
    return effectful


def _public_effects() -> set[tuple[str, str]]:
    return {
        key
        for key in _effect_closure()
        if (key[1].split(".")[-1] == "__call__" or not key[1].split(".")[-1].startswith("_"))
    }


def _named_calls(node: ast.AST) -> set[str]:
    out: set[str] = set()
    for child in _walk_own(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if isinstance(func, ast.Name):
            out.add(func.id)
        elif isinstance(func, ast.Attribute):
            out.add(func.attr)
    return out


def test_every_detectable_non_sql_effect_is_reviewed() -> None:
    discovered = _public_effects()
    declared = set(EFFECT_INVENTORY)
    undeclared = sorted(discovered - declared)
    stale = sorted(declared - discovered)
    assert not undeclared, (
        "non-SQL effect entry point exists without review; classify the effect and "
        f"state what protects it: {undeclared}"
    )
    assert not stale, f"non-SQL effect inventory describes effects no longer detected: {stale}"


def test_indirect_external_orchestrators_keep_their_reviewed_effect_calls() -> None:
    definitions = _definitions()
    for key, record in INDIRECT_EFFECT_INVENTORY.items():
        assert key in definitions, f"indirect effect surface was removed or renamed: {key}"
        node, _ = definitions[key]
        observed = _named_calls(node)
        required = set(record["required_calls"])
        missing = sorted(required - observed)
        assert not missing, (
            f"{key} no longer contains the calls its external-effect review relied on: {missing}; "
            "re-read the orchestration instead of silently keeping the old verdict"
        )


def test_every_effect_record_explains_why_it_is_allowed_to_exist() -> None:
    for inventory in (EFFECT_INVENTORY, INDIRECT_EFFECT_INVENTORY):
        for key, record in inventory.items():
            assert str(record.get("effect") or "").strip(), key
            assert str(record.get("reviewed") or "").strip(), key
