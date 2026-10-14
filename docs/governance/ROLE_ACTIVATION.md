# Role Activation

Status: active support doctrine — role, domain and skill activation semantics only.
Boundary profile: active_support_doctrine.

This document defines how Pantheon Next varies the participation of Pantheon Roles, professional domain packs and candidate skills for a session, task, dossier or project.

It does not add agents, a role runtime, a skill runtime, a marketplace, a UI, an approval engine, a memory engine or an execution path.

```text
Hermes clients handle runtime interaction.
Hermes Agent executes externally.
Pantheon Cockpit exposes governed projections.
Pantheon Next governs consequential status.
The human decides where a gate requires it.
```

## Purpose

Activation is a governance eligibility/attention concept, not a runtime switch.

```text
role active != agent started
domain enabled != professional authority
skill eligible != task authorized
task authorized != approved
projection visible != persistence
runtime success != authorization
```

This document owns only the activation semantics for roles, domain packs and candidate skills. Canonical Role identity remains in `AGENTS.md`; capability eligibility/binding remains with the existing capability owners; Task Contract and approval owners remain authoritative for task execution and consequence.

## 1. Role participation

A Pantheon Role is a governance viewpoint, not an autonomous worker.

A role may be:

```text
active
standby
disabled_by_user
disabled_by_scope
not_relevant
mandatory_for_risk
blocked
suspended
```

`active` means its governance pressure is materially relevant to the current review. `standby` means it remains available without producing visible output by default. Deactivation does not delete doctrine and does not prevent mandatory reactivation when a governed risk trigger appears.

Activating a role may:

- include its review angle;
- request its structured signals;
- expose a relevant warning or tension;
- make a gate/review requirement visible;
- cause Zeus to include that viewpoint in a workflow proposal.

Activating a role must not:

- start an autonomous agent;
- execute retrieval or tools;
- authorize an effect;
- approve an output;
- promote memory;
- create professional authority.

MNEMOSYNE follows the same rule. Its participation frames continuity, historical reuse, version/currentness and retention questions. Actual retrieval remains external execution under Task Contract, and retrieved material remains non-authoritative until qualified through its applicable source/Evidence owners.

## 2. Domain-pack participation

A professional domain pack is governed configuration: vocabulary, source expectations, Evidence expectations, risk triggers, review constraints, templates and delivery gates.

A domain pack may be:

```text
inactive
watch
candidate
sandbox_enabled
project_enabled
dossier_enabled
domain_enabled
organization_enabled
suspended
rejected
```

Enabling a domain pack may:

- apply domain-specific source and Evidence expectations;
- make selected roles mandatory for known risks;
- make existing preparation/projection templates applicable;
- make compatible skill candidates eligible for Task Contract consideration;
- raise approval or delivery requirements.

It does not validate professional correctness, source validity, regulatory currency, external transmission, memory retention or skill execution.

Professional domains default to draft-only until the applicable human professional review.

## 3. Skill eligibility

A skill candidate is a bounded capability candidate normally executed outside Pantheon by Hermes Agent or another admitted external executor.

A candidate skill may be:

```text
unavailable
detected
watch
candidate
sandbox_enabled
project_enabled
dossier_enabled
task_authorized
suspended
rejected
```

Eligibility means the skill may be considered for a Task Contract. A task-authorized skill may execute only within the Task Contract's declared scope, allowed tools, FOR/NOT FOR limits, Evidence requirements, memory rule and approval ceiling.

```text
detected != admitted
eligible != task_authorized
task_authorized != approved
execution completed != professional validation
```

No activation state installs a skill or creates a plugin marketplace.

## 4. Activation classes

Use existing object owners rather than product-specific activation classes:

```text
governance_role
professional_domain_pack
skill_candidate
evidence_policy_pack
memory_policy_pack
approval_gate_pack
external_tool_candidate
```

Client-specific template packs are not a governance activation class. Runtime-facing presentation remains with the applicable Hermes/client owner; governed status/review/navigation composition remains with Pantheon Cockpit and existing Card projection owners.

## 5. Status correspondence

The vocabularies are intentionally related but not identical because they describe different objects.

| Generic idea | Role | Domain | Skill |
|---|---|---|---|
| absent / irrelevant | `not_relevant` | `inactive` | `unavailable` |
| observed | `standby` | `watch` | `detected` |
| under review | `standby` | `candidate` | `candidate` |
| limited use | `active` | `sandbox_enabled` | `sandbox_enabled` |
| project scope | `active` | `project_enabled` | `project_enabled` |
| dossier scope | `active` | `dossier_enabled` | `dossier_enabled` |
| task requires it | `mandatory_for_risk` | applicable enabled state | `task_authorized` |
| blocked | `blocked` / `suspended` | `suspended` | `suspended` |
| refused | `blocked` | `rejected` | `rejected` |

A client or Cockpit projection may display these states, but display labels are projections of the governed state rather than a separate activation vocabulary owner.

## 6. Mandatory role triggers

Some risks require a governance viewpoint even when it would otherwise remain silent.

```yaml
mandatory_role_triggers:
  ATHENA:
    - complex_task
    - architecture_decision
    - scope_split_required
    - multi_step_workflow

  ARGOS:
    - factual_claim
    - external_reference
    - legal_or_regulatory_source
    - source_required
    - evidence_gap
    - source_freshness_risk
    - provenance_unclear

  MNEMOSYNE:
    - memory_recall_requested
    - prior_decision_reuse
    - project_history_reuse
    - duplicate_or_supersession_risk
    - remembered_version_or_index_reuse
    - cross_scope_memory_risk
    - memory_candidate
    - memory_promotion

  THEMIS:
    - approval_required
    - legal_or_professional_risk
    - external_effect
    - protected_file
    - memory_promotion
    - policy_conflict
    - liability_risk

  APOLLO:
    - public_readme
    - client_explanation
    - unclear_output
    - narrative_or_editorial_work
    - delivery_quality_required

  HEPHAISTOS:
    - patch_candidate
    - file_creation
    - template_creation
    - implementation_candidate
    - artifact_fabrication

  IRIS:
    - external_transmission
    - client_delivery
    - public_output
    - handoff_required
    - recipient_specific_format

  ZEUS:
    - always_procedural
```

These are governance-review triggers, not runtime dispatch instructions. A trigger may make a Role viewpoint mandatory; it does not start a Hermes profile.

ARGOS owns source identity/provenance/freshness questions. MNEMOSYNE owns continuity/current-state/reuse questions. Both may participate when the same date or version affects both concerns.

## 7. Readiness and workflow proposal

Roles may emit short readiness signals. Zeus may use them to compose the smallest safe workflow proposal.

Example shape:

```yaml
role_signal:
  role: MNEMOSYNE
  status: standby
  reason: no_prior_state_reuse_or_retention_impact
  mandatory_trigger_detected: false
  recommended_involvement: activate_if_history_version_or_retention_becomes_material
  risk_if_inactive: stale_or_wrong_scope_reuse
```

A session brief may state active/standby/mandatory roles, enabled domains, eligible skills, proposed review sequence and whether a User Decision Gate is required.

Zeus composes procedure. Zeus does not run a workflow, decide truth, execute tools or approve consequence.

## 8. Domain-pack contract

A domain pack should declare only domain-specific configuration and references to existing owners.

```yaml
domain_id: architecture
status: candidate
scope: project
mandatory_roles:
  - ATHENA
  - ARGOS
  - THEMIS
optional_roles:
  - APOLLO
  - HEPHAISTOS
  - IRIS
  - MNEMOSYNE
required_evidence:
  - source_status
  - scope_status
  - assumptions
  - limitations
approval_gates:
  - professional_review_required_before_external_reliance
memory_policy:
  - memory_candidate_only_by_default
skill_candidates: []
templates: []
```

Templates remain preparation/projection resources owned by their applicable existing client/Cockpit/Card owners. A domain pack does not create a UI template subsystem.

A domain pack may make a skill eligible; it may never authorize the skill by itself.

```text
domain enabled
-> skill candidate eligible
-> Task Contract may authorize skill for this task
-> Hermes Agent executes if allowed
-> Result/Evidence candidates return
-> Pantheon reviews governed status
```

## 9. Skill candidate contract

A candidate should declare enough structure for bounded Task Contract use.

```yaml
skill_id: architecture_devis_analysis_candidate
status: candidate
owner_layer: hermes
requires_domain:
  - architecture
for:
  - compare_quotes_against_project_scope
  - identify_missing_items
  - flag_cost_or_scope_risks
not_for:
  - final_contractual_decision
  - legal_liability_opinion
  - automatic_client_instruction
required_inputs:
  - task_contract
  - selected_sources
  - project_scope
  - evidence_requirements
required_outputs:
  - analysis_candidate
  - assumptions
  - evidence_notes
  - missing_information
  - approval_implications
approval_ceiling: candidate_only
memory: memory_candidate_only_if_explicit
```

Illustrative candidate names are not installed skills or approved capabilities.

## 10. Cross-domain work

Several domains may be enabled when a task genuinely crosses professional boundaries. Cross-domain participation increases Evidence, scope and approval pressure; it does not merge professional authorities.

For construction-dispute or contractual-risk work, for example, architecture and legal domain packs may both apply while ARGOS/THEMIS/ZEUS become mandatory and the relevant source-freshness, jurisdiction, professional-review and transmission gates remain explicit.

MNEMOSYNE becomes relevant only when prior positions, versions, history or retention are material.

## 11. Disable effects

Disabling a domain or skill must have visible governed effects.

A disabled architecture domain may block architecture skill candidates, architecture-specific templates and architecture-domain external-transmission preparation while preserving generic governance/Evidence review.

A disabled legal domain may block legal skill candidates and legal-domain output preparation while preserving generic source/risk review.

THEMIS may remain inactive only when no approval, professional, external-effect or protected-file risk exists; risk triggers reactivate it.

MNEMOSYNE may remain inactive only when no recall, prior-state reuse, version/supersession issue, memory candidate or retention question exists; those conditions reactivate it.

## 12. Memory boundary

Role, domain and skill activation do not promote memory.

MNEMOSYNE may frame retrieval, detect supersession and propose a retention destination. A durable claim still follows existing Register Candidate/Evidence/approval owners.

```text
runtime recall != truth
repeated observation != governed memory
memory candidate != Registre Probatoire entry
activation != retention authorization
```

Cross-project or Project-to-Agency retention requires explicit scope review and any required anonymization/approval.

## 13. Projection boundary

Pantheon Cockpit and existing Card projection owners may expose, where useful:

- active, standby, disabled and mandatory roles;
- enabled/suspended domains;
- eligible, blocked and task-authorized skill candidates;
- readiness signals;
- Zeus workflow proposal;
- Effective Policy;
- dependency blockers and User Decision Gates.

Hermes Web/dashboard or compatible clients may expose runtime interaction and runtime controls.

Neither client nor Cockpit projection may make a Role autonomous, make a domain authoritative, install/authorize a skill, approve a professional output, promote memory or bypass a mandatory gate.

```text
projection != persistence
client selected != governance authority
```

## 14. Hermes execution boundary

Hermes Agent may execute a candidate skill only when all applicable admission conditions are satisfied:

- required domain state is eligible;
- Task Contract authorizes the capability for the task;
- FOR/NOT FOR and scope are explicit;
- allowed tools are declared;
- Evidence return is required;
- approval ceiling is explicit;
- memory rule is explicit.

Role activation never grants filesystem, vector-store, connector, provider or memory access. Provider/binding selection remains separate from authority.

## 15. Relationships to existing owners

- `AGENTS.md` — canonical Pantheon Role registry and authority boundaries.
- `GOVERNANCE_COLLEGE.md` — why separated governance viewpoints exist.
- `ROLE_SIGNALS.md` — structured Role Signals; a signal never self-activates or authorizes.
- `MODULE_ACTIVATION.md` — generic activation/task-authorization semantics.
- `UNIFORM_CAPABILITY_GOVERNANCE.md` and capability binding owners — capability identity, binding and eligibility.
- `DOMAIN_PACK_SPEC.md` — general professional domain-pack contract.
- `TASK_CONTRACTS.md` — task authorization/perimeter.
- `APPROVALS.md` and `USER_DECISION_GATE.md` — consequential approval/decision paths.
- `MEMORY.md` and Register contracts — durable governed retention.
- `HERMES_INTEGRATION.md` — external execution boundary.
- `PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md` and Card owners — governed projections.

No product-specific transition document is required by role/domain/skill activation.

## Forbidden drift

Role, domain or skill activation must never become:

- autonomous role agents or hidden multi-agent runtime;
- profession-specific AI authority;
- skill marketplace or automatic installer;
- provider/router selection authority;
- automatic approval or external effect;
- automatic memory promotion;
- a second generic chat/runtime UI inside Pantheon;
- a Pantheon execution runtime.

## Final rule

```text
Use Roles to reveal material tensions.
Use domain packs to constrain professional context.
Make skills eligible only for bounded Task Contract consideration.
Execute externally through admitted runtime capabilities.
Project governed state without transferring authority.
Validate nothing by activation alone.
```
