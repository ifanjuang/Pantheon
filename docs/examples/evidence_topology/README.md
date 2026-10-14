# Evidence Topology Examples

Status: fictional examples — educational support only.

These historical examples illustrate concepts now governed by `docs/governance/EVIDENCE_TOPOLOGY.md`.

They are not current schema-conformance fixtures, runtime prompts, professional advice, approval or authority. Their older object shapes are retained as illustrative provenance unless a separate migration explicitly converts and validates them against the current schemas.

```text
Hermes clients may expose runtime interaction.
Hermes Agent executes externally under Task Contract.
Pantheon Cockpit may expose governed topology/Evidence state.
Pantheon Next governs consequential status.
```

## Purpose

The examples show why reasoning topology should be selected before external execution without treating orchestration as authority.

```text
The unit of reasoning is not the agent.
The unit of reasoning is the proof chain.
```

## Included examples

| File | Topology | Purpose |
|---|---|---|
| [`task_contract_single_primary_reasoning_context.yaml`](task_contract_single_primary_reasoning_context.yaml) | `single_primary_reasoning_context` | Historical fictional ticket illustrating consolidated reasoning across Jira, code, XML configuration and design notes. |
| [`task_contract_fanout_extract_then_single_synthesis.yaml`](task_contract_fanout_extract_then_single_synthesis.yaml) | `fanout_extract_then_single_synthesis` | Historical fictional dossier illustrating bounded parallel extraction followed by consolidated synthesis. |
| [`task_contract_persistent_role_team_handoff.yaml`](task_contract_persistent_role_team_handoff.yaml) | `persistent_role_team_handoff` | Historical fictional staged workflow illustrating artifact-bound handoffs. |
| [`evidence_pack_topology_examples.yaml`](evidence_pack_topology_examples.yaml) | Evidence Pack concept | Historical fictional material illustrating Evidence Items, Handoff Artifacts, topology records and approval gaps. |

## Reading rule

Preserve these distinctions:

```text
source != Evidence
retrieval != truth
worker output != conclusion
handoff != approval
team chat != Evidence Pack
runtime role memory != governed memory
runtime state != Pantheon persistence
```

## Current machine contract

Current machine-readable topology ownership lives in:

- `schemas/workflow_manifest.schema.yaml` — workflow-level topology, Evidence Item and Handoff Artifact requirements;
- `schemas/task_contract.schema.yaml` — task-level `reasoning_topology`;
- `schemas/evidence_pack.schema.yaml` — `evidence_items`, `handoff_artifacts` and `reasoning_topology_record`.

The YAML files in this folder predate those current shapes and must not be presented as validating against them. Schema conformance, where demonstrated by current schema examples/tests elsewhere, still does not prove Evidence sufficiency, professional correctness, runtime adoption or approval.

## Not implemented by these examples

These examples do not themselves implement:

- execution or Hermes dispatch;
- a LangGraph/swarm runtime;
- agent-to-agent messaging;
- client/Cockpit UI;
- memory promotion;
- approval automation.

They remain illustrative examples for doctrine and historical design context.
