# Hermes-first / NeMo Fabric-ready interoperability

Status: candidate interoperability note. No NeMo Fabric installation or activation is claimed.

## Selection

Use **native Hermes first** for task-scoped context, Skills, tools and execution. Keep NVIDIA NeMo Fabric as an **optional replaceable adapter** if it offers demonstrated interoperability or observability gains. Pantheon defines Task Contract, Context Pack, source/admission and consequential-effect governance; it must not duplicate Hermes or Fabric execution machinery.

Existing owners:
- `docs/governance/HERMES_INTEGRATION.md` — runtime placement, security and release posture;
- `docs/governance/CONTEXT_PACKS.md` and `TASK_CONTRACTS.md` — scoped inputs/admission;
- `docs/domain-packs/architecture/SOURCE_POLICY.md` — professional source consultation;
- `templates/hermes/skills/project-context/` — agency source selection;
- `docs/architecture/HERMES_IMPROVEMENT_PATH.md` and Pantheon-Next#1093 — comparisons of direct, delegation and Kanban;
- PR Pantheon-Next#1152 — ephemeral source-context lease, separate from this Fabric question.

## Replaceable mapping

| Pantheon / existing owner | Fabric candidate |
|---|---|
| Admitted task and Context Pack | Exact run input and `instructions.system` |
| Selected model / execution parameters | `FabricConfig.models` and runtime settings |
| Existing Hermes Skill set | `FabricConfig.skills` |
| Admitted tool surfaces | Fabric MCP/tool mapping |
| Runtime observation | Fabric result and optional telemetry |

This mapping does not make Fabric a source of project identity, authority, Evidence or persistence. Different organizations use their own configuration and data access; the architecture Domain Pack remains reusable across agencies. The actual runtime profile, workspace and permissions must be evaluated separately from governance identity.

The upstream Hermes adapter is `nvidia.fabric.hermes`; NVIDIA documents `Fabric.plan()` and `Fabric.doctor()` for compatibility inspection. Their outcome is technical information, not an activation decision.

## What to qualify if considering Fabric

- **Instructions:** Fabric can replace, not append, `instructions.system`. Confirm that the effective admitted instructions are present.
- **Runtime settings:** the documented adapter has set `HERMES_YOLO_MODE=1` and `HERMES_ACCEPT_HOOKS=1` by default if absent. Observe the effective tool/credential restrictions on the tested version, especially for consequential effects.
- **Sessions:** the integration can reuse Hermes `AIAgent`/`SessionDB` across calls. Verify an appropriate reset or isolation between unrelated organization/project tasks.
- **Compatibility:** pin the exact lab versions and run `Fabric.plan()`/`Fabric.doctor()`; upstream Relay, Python and Hermes assumptions may change.

Upstream references:
- https://github.com/NVIDIA/NeMo-Fabric
- https://github.com/NVIDIA/NeMo-Fabric/blob/main/docs/integrations/harness/hermes.mdx

## Decision path

1. Qualify native Hermes on representative agency work using the existing Skills and the task-context selection reference; observe sources, quality, cumulative tokens and latency.
2. Compare direct versus delegated tactics through existing Pantheon-Next#1093 instead of imposing a universal execution strategy.
3. **Only if a gap remains**, compare a Fabric lab to direct Hermes using equivalent inputs and effective permissions. A simple read-only lab is sufficient to start; expand to consequential scenarios only under existing admission.
4. Adopt an adapter only when its benefits outweigh the integration cost and Hermes direct remains available as a fallback.

This document neither creates a runtime preset system nor imposes a new governance checklist. Runtime changes, external effects and adoption remain with their existing owners. Actual Fabric compatibility and savings are unverified.
