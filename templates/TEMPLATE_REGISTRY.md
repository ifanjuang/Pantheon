# Template Registry

Status: candidate support note — mixed external installation status.

This registry lists the current declarative templates under `templates/`. Their
presence does not install, execute, deploy or authorize any runtime, client,
skill, flow, MCP service, policy gateway, trace backend or prompt runtime. The
Pantheon activity projection has a separate explicit Ubuntu configurator; that
external installation exception is identified on its own row.

```text
Hermes Web/dashboard -> selected external chat/session/runtime interaction baseline
Hermes Agent         -> external execution runtime
Pantheon             -> governance and authority
Pantheon Cockpit     -> governed Cards/navigation/decision/status projections
```

## Current templates

| Template | Path | Owner layer | Surface | Status |
|---|---|---|---|---|
| General template scaffold | `templates/README.md` | Pantheon | template index | non-executable |
| Template model | `templates/TEMPLATE_MODEL.md` | Pantheon | template discipline | documented non-implemented |
| Hermes template index | `templates/hermes/README.md` | Hermes | execution template index | non-executable |
| Task Contract handoff | `templates/hermes/handoffs/task_contract_handoff.template.yaml` | Hermes | handoff candidate | non-executable |
| Evidence Pack candidate return | `templates/hermes/returns/evidence_pack_candidate.template.yaml` | Hermes | return envelope candidate | non-executable |
| Source preflight receipt | `templates/hermes/returns/source_preflight_receipt.template.yaml` | Hermes | source-consultation trace candidate | non-executable; not Evidence |
| Pantheon request intake skill candidate | `templates/hermes/skills/pantheon-request-intake/SKILL.md` | Hermes | semantic intake skill candidate | non-executable |
| Pantheon governed method skill candidate | `templates/hermes/skills/pantheon-governed-method/SKILL.md` | Hermes | generalist method coordination skill candidate | externally installable; no workflow engine |
| Pantheon activity projection skill candidate | `templates/hermes/skills/pantheon-activity-projection/SKILL.md` | Hermes | conversation projection skill candidate | externally installable; no persistence |
| External commitment guard skill candidate | `templates/hermes/skills/external-commitment-guard/SKILL.md` | Hermes | external-effect guard skill candidate | externally installable; authorizes no effect |
| Construction cost review skill candidate | `templates/hermes/skills/construction-cost-review/SKILL.md` | Hermes | estimates, offers and lot coverage | externally installable; no financial approval |
| Site report review skill candidate | `templates/hermes/skills/site-report-review/SKILL.md` | Hermes | site observations and report continuity | externally installable; no instruction or transmission |
| Administrative form review skill candidate | `templates/hermes/skills/administrative-form-review/SKILL.md` | Hermes | sourced field preparation | externally installable; no signature or filing |
| Technical standard review skill candidate | `templates/hermes/skills/technical-standard-review/SKILL.md` | Hermes | exact-edition applicability review | externally installable; bounded conclusions only |
| Construction schedule review skill candidate | `templates/hermes/skills/construction-schedule-review/SKILL.md` | Hermes | works sequencing and replanning | externally installable; no contractor instruction |
| Agency project context skill candidate | `templates/hermes/skills/project-context/SKILL.md` | Hermes | skill candidate | externally installable; no authority |
| Source research skill candidate | `templates/hermes/skills/source-research/SKILL.md` | Hermes | skill candidate | non-executable |
| Source research summary Workflow Manifest | `templates/source_research_summary_workflow_manifest.template.yaml` | Pantheon | workflow governance candidate | non-executable |
| Visual focus skill candidate | `templates/hermes/skills/visual-focus/SKILL.md` | Hermes | skill candidate | non-executable |
| Diagram projection skill candidate | `templates/hermes/skills/diagram-projection/SKILL.md` | Hermes | editorial diagram projection candidate | non-executable; external renderer unbound at runtime |
| Checkpoint manifest | `templates/hermes/run_manifests/checkpoint_manifest.template.yaml` | Hermes | run manifest candidate | non-executable |
| Devis reprise run manifest | `templates/hermes/run_manifests/devis_reprise_run_manifest.template.yaml` | Hermes | run manifest candidate | non-executable |
| Context Pack preparation flow | `templates/langflow/flows/context_pack_preparation_flow.template.yaml` | Langflow | deterministic flow candidate | non-executable |
| Pantheon trace metadata | `templates/langfuse/trace_metadata/pantheon_trace_metadata.template.yaml` | Langfuse | trace metadata candidate | non-executable |
| MCP capability passport | `templates/mcp_capability_passport.yaml` | Pantheon | MCP policy template | non-executable |
| MCP external tool review | `templates/mcp_external_tool_review.md` | Pantheon | MCP policy review template | non-executable |
| Provenance links | `templates/provenance/provenance_links.template.yaml` | provenance support | provenance link candidate | non-executable |
| Prompt template index | `templates/prompt_templates/README.md` | Pantheon / Hermes | prompt template group | non-executable |
| Evidence extraction prompt | `templates/prompt_templates/evidence_extraction.template.md` | Pantheon / Hermes | evidence candidate extraction | non-executable |
| DCE review prompt | `templates/prompt_templates/dce_review.template.md` | Pantheon / Hermes | professional review candidate | non-executable |
| Visa review prompt | `templates/prompt_templates/visa_review.template.md` | Pantheon / Hermes | professional review candidate | non-executable |
| Client email prompt | `templates/prompt_templates/client_email.template.md` | Pantheon / Hermes | drafting candidate | non-executable |
| Decision record prompt | `templates/prompt_templates/decision_record.template.md` | Pantheon | decision record candidate | non-executable |

The former `templates/openwebui/` namespace is retired. Generic execution handoffs remain under the existing Hermes template owner; governed product projections remain under Pantheon Cockpit. No replacement client-specific template layer is introduced.

## Boundary rules

```text
Template does not mean implementation.
Trace does not mean Evidence Pack.
Manifest does not mean scheduler.
Skill candidate does not mean installed skill unless an explicit external configurator is applied.
Flow candidate does not mean deployment.
MCP passport does not mean tool authorization.
Provenance link does not mean proof.
Prompt template does not mean system prompt deployment.
Draft does not mean signed position.
```
