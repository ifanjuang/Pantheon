# Condition vocabulary

Use only trigger names accepted by `docs/governance/ROLE_ACTIVATION.md` and the
current Pantheon request surface. Common material conditions include
`source_required`, `factual_claim`, `external_reference`, `evidence_gap`,
`memory_recall_requested`, `memory_candidate`, `memory_promotion`,
`approval_required`, `legal_or_professional_risk`, `external_transmission`,
`external_effect`, `client_delivery`, `unclear_output` and
`delivery_quality_required`.

## Distinctions

`memory_recall_requested` and `prior_decision_reuse` retrieve what is already
retained. A request to make something persistent, canonical or official needs
`memory_candidate`, `memory_promotion` and `approval_required`; this describes
a gate, not approval.

Preparing, rewriting or formatting a message is not an external effect. Actual
sending, publishing, submission or another action outside the conversation
needs `external_transmission` and `external_effect`; add `client_delivery` for
a client recipient.

Use coordination only for an observed dependency or stop condition:
`requires`, `independent`, `synthesize`, `branch_on`, `repeat_until`. Describe
relations, never worker topology. Prefer observable completion requirements
such as `tests_pass`, `requested_fact_resolved`, `inconsistencies_identified`
or `response_candidate_ready`.
