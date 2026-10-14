---
name: pantheon-request-intake
description: "Use before Pantheon request classification to translate raw user language into the smallest supported request candidate: intent, material conditions, optional relations and observable completion requirements. It never derives K/V/C, approval, truth or authorization."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  governed_by: docs/governance/REQUEST_LIFECYCLE.md
  policy_contract: mcp-server/docs/HERMES_INTEGRATION_CONTRACT.md
---

# Pantheon request intake

Return a request candidate, never K/V/C. Prefer the smallest sufficient
candidate supported by the user's request, then call `classify_request`.
Pantheon, not Hermes, returns `PROCEED`, `CONSULT` or `GATE`.

```text
semantic candidate != truth
condition candidate != consequence classification
coordination relation != dispatch
completion requirement != approval
Hermes interpretation != Pantheon decision
```

## Candidate

```yaml
intent: "..."
requested_transformation: optional
conditions: []
coordination: {requires: [], independent: [], synthesize: false, branch_on: [], repeat_until: []}
completion_requirements: []
```

Emit a condition only when it materially changes meaning, source need,
responsibility, authorization, continuity, retention or the next legitimate
transition. Do not emit a condition merely because a word appears in the
request. Do not choose a topology or reconsult after every internal step.

Read [references/condition-vocabulary.md](references/condition-vocabulary.md)
when a condition, memory direction, external effect or coordination relation is
unclear. Condition names remain owned by
`docs/governance/ROLE_ACTIVATION.md`; this skill does not create synonyms or a
shadow policy table.

```text
request candidate != task dispatch
draft != external effect
memory recall != memory promotion
```
