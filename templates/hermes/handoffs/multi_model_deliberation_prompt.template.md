# Multi-model deliberation prompt

Template status: candidate only. External Hermes input; inactive in Pantheon Next.

Use with the named `pantheon-deliberation` MoA preset in a fresh Hermes session
after the configuration, model passports, data class and budget are reviewed.
Replace every `REQUIRED` marker from the handoff template before running.

## Pass 1 — independent review and dissent map

```text
Treat this as a bounded Pantheon Deliberation Candidate, not as authority.

Work Issue: REQUIRED
Task Contract: REQUIRED_WHEN_APPLICABLE
Subject: REQUIRED
Question: REQUIRED
Frozen input revision: REQUIRED
Included scope: REQUIRED
Excluded scope: REQUIRED
Permitted data class: REQUIRED

Each reference model must analyse the same frozen input independently. Seek
material blind spots rather than stylistic variety. The acting aggregator must
preserve stable slot identifiers, failures and minority positions. Do not infer
truth from agreement and do not act on the result.

Return only a Deliberation Candidate matching
templates/hermes/returns/deliberation_candidate.template.yaml, including:
- agreements;
- material dissent;
- unsupported claims and evidence gaps;
- doctrine or scope conflicts;
- tests that could discriminate between competing claims;
- limitations and failed or excluded model slots;
- the remaining human decision;
- the recommended next procedure.

No repository write, external effect, approval, issue closure, doctrine
mutation or memory promotion is authorized.
```

## Pass 2 — optional challenge

Run this only when pass 1 retains material disagreement or uncertainty.

```text
Challenge the preceding Deliberation Candidate against the same frozen input.
Look specifically for false consensus, shared prompt assumptions, missing
evidence, lost minority positions and tests that would actually change the
conclusion. Preserve unresolved dissent. Return a revised Deliberation
Candidate with passes_completed: 2. Stop after this pass.
```
