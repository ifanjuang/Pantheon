# Governed execution and readiness

Read the portions relevant to policy routing, complex task state, source
receipts, production, verification or final readiness.

## Frame and admit

Preserve requested effect, audience, scope and output. Use
`pantheon-request-intake` only to produce supported candidate conditions,
coordination relations and observable completion requirements. Inventory
available and missing working material without declaring it true or Evidence.

## Qualify through Pantheon policy

For non-trivial professional factual work, route before material source access:

```text
route_governed_request(request YAML or plain request text, source_limit <= 3)
-> read_doctrine(exact selected key) when the route selects doctrine
-> source-preflight receipt
```

Do not call `classify_request`, `find_relevant_sources` or `list_sources` on the
normal answer path; reserve them for administration, compatibility or diagnosis.
Invoke only one deferred MCP function per `tool_call` and sequence dependent
policy calls.

Use only the justified subset of:

```text
route_governed_request
evaluate_preflight
prepare_task_contract_skeleton
prepare_evidence_pack_skeleton
plan_context_pack
validate_context_pack
```

Candidate preparation is not execution; validation is not authorization.

## Adaptive task flow

Use direct work for a simple question, compact milestones for a bounded material
request, and a Task Contract with optional Kanban projection only when at least
two material complexity signals exist: independent subgoals, dependencies,
several deliverables, cross-session work, a human decision gate or an external
effect boundary. Kanban is a projection, never a second source of truth.

## Compose, produce and test

Select at most one primary method, one guardrail method and one verification
method. Load specialist skills only on their exact trigger. Preserve provenance,
assumptions, contradictions and sourced-versus-derived status.

Test observable completion requirements: exact source opened, components
reconciled, requested coverage present, artifact rendered, relevant tests passed,
wording reviewed or gate opened. `Looks correct` is not a test. If a material
condition changes, return to framing or qualification without rerunning policy
after every routine call.

## Source-preflight receipt

For a material professional factual answer, use
`templates/hermes/returns/source_preflight_receipt.template.yaml`. Record required
source families, actual route/tool, exact source and locator, observed metadata,
memory-only leads, Context Pack validation when applicable, family completion
and an observed trace reference when available.

A family is incomplete when only snippets, memory, model recall or a guessed
filename were observed. If the exact source cannot be opened, use
`needs_user_input` or `blocked`.

## Status

Judge the result the user requested, not whether the method merely ran:

- `ready`: produced, checked and usable for the bounded declared use;
- `ready_with_limits`: usable with explicit bounded limits;
- `needs_revision`: produced but a defect prevents declared use;
- `needs_user_input`: a required decision or datum is unavailable to tools;
- `blocked`: a required technical, access or authority dependency is unavailable.

Attach only the smallest useful result, sources, limitations and next safe
action. A readiness result never authorizes transmission or another external
effect.
