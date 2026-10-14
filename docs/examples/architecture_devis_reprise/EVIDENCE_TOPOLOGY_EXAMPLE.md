# Evidence Topology Example — Architecture / MOE

Status: fictional example — educational support only.
Boundary profile: documentation_only.

This example applies `docs/governance/EVIDENCE_TOPOLOGY.md` to an architecture / maîtrise d’œuvre dossier.

It is not legal advice.

It is not technical validation.

It is not a reception decision.

It is not a liability opinion.

It is not an implementation file.

## Scenario

A fictitious architect is asked to review whether a recovery quote can be discussed after a contractor failure.

The dossier contains:

- a recovery quote;
- a CCTP excerpt;
- one site report;
- client emails;
- photos;
- a note about missing reception;
- a draft response requested by the client.

The professional risk is high enough that the system must not produce a smooth client-facing validation from partial evidence.

## Topology decision

Selected topology:

```text
fanout_extract_then_single_synthesis
```

Reason:

```text
Several sources can be extracted separately, but the final reasoning must compare them in one consolidated context.
```

Rejected topologies:

```text
summary_only_multi_agent_supervisor
persistent_role_team_handoff_without_artifacts
bounded_swarm_as_authority
single_worker_final_client_email
```

## Why not pure single-context from the start

The file set may be too large for immediate synthesis.

Parallel extraction is useful for:

- quote line items;
- CCTP clauses;
- site observations;
- client statements;
- photo descriptions;
- missing-source list.

But extraction is not conclusion.

The final synthesis must still compare all selected Evidence Items together.

## Why not multi-agent conclusion

A quote extractor may see the price but not the CCTP.

A CCTP extractor may see the clause but not the site condition.

A photo reviewer may see visible defects but not contractual scope.

A mail reviewer may see client pressure but not technical proof.

Therefore, no worker may conclude:

```text
the quote is valid
the works are accepted
the architect should approve
the client can be told this is safe
```

## Task Contract sketch

```yaml
task_contract:
  intent: "Prepare an internal review note on a fictitious recovery quote."
  scope:
    included:
      - recovery_quote
      - cctp_excerpt
      - site_report
      - client_emails
      - photos
      - missing_reception_note
    excluded:
      - final_quote_validation
      - reception_decision
      - legal_liability_conclusion
      - client_facing_transmission
      - memory_promotion

  reasoning_topology:
    selected: fanout_extract_then_single_synthesis
    reason: many_sources_but_unified_professional_reasoning_required
    handoff_policy: evidence_items_only
    synthesis_policy: single_primary_reasoning_context_after_extraction

  expected_outputs:
    - internal_review_note_candidate
    - contradiction_ledger
    - missing_source_list
    - evidence_pack_candidate
    - user_decision_gate_request_if_needed

  forbidden_outputs:
    - client_validation_email
    - final_quote_approval
    - reception_status_decision
    - professional_liability_opinion
    - canonical_memory
```

## Extraction lanes

### Quote extraction

Output expected:

- line item;
- amount;
- described work;
- assumption;
- exclusion;
- uncertainty;
- source locator.

Forbidden:

- saying the quote is acceptable;
- saying the price is fair;
- drafting approval wording.

### CCTP extraction

Output expected:

- relevant clause;
- scope of work;
- tolerance or specification;
- missing clause;
- contradiction candidate;
- source locator.

Forbidden:

- concluding contractual liability;
- widening scope beyond the excerpt.

### Site report extraction

Output expected:

- dated observation;
- author or source;
- site condition;
- reserve or uncertainty;
- missing verification.

Forbidden:

- treating an observation as reception;
- treating silence as acceptance.

### Email extraction

Output expected:

- client request;
- pressure or urgency;
- instruction status;
- unclear approval wording;
- external transmission risk.

Forbidden:

- treating client pressure as technical validation;
- producing a client-facing reply without approval.

### Photo extraction

Output expected:

- visible element;
- limitation of visual inspection;
- need for contradiction or site verification;
- link to quote or CCTP item when possible.

Forbidden:

- concluding hidden technical cause;
- replacing expert site review.

## Evidence Item example

```yaml
evidence_item:
  evidence_id: ei-arch-quote-cctp-001
  claim: "Recovery quote item 4 appears broader than the CCTP excerpt currently in scope."
  source_type: quote_and_cctp_comparison
  source_ref:
    quote: "fictional-doc://quote#item-4"
    cctp: "fictional-doc://cctp#section-3.2"
  scope_of_support: "Supports a clarification need, not a final rejection."
  confidence: medium
  limitations:
    - "Full CCTP not in scope."
    - "Later client instruction not confirmed."
  open_questions:
    - "Was item 4 requested after the CCTP was issued?"
  scope_warnings:
    - "Do not draft validation wording from this item alone."
```

## Consolidated synthesis requirements

The synthesis must produce:

- a neutral internal note;
- a contradiction ledger;
- missing source list;
- risk wording;
- approval gap;
- suggested User Decision Gate options.

The synthesis must not produce:

- a final professional decision;
- a client-facing validation;
- a legal conclusion;
- a reception conclusion;
- a memory promotion.

## User Decision Gate trigger

A User Decision Gate is required if the user asks to:

- send the note to the client;
- validate the quote;
- characterize reception status;
- assert professional liability;
- rely on photos alone;
- reuse the conclusion as future memory.

Gate options:

```text
continue as internal note
request missing source
narrow the conclusion
prepare cautious client-facing draft for review
block transmission
prepare professional/legal consultation question
```

## Memory boundary

Allowed:

```text
No memory output by default.
```

Possible only after review:

```text
Register Candidate about this dossier's evidence pattern.
```

Forbidden:

```text
broad rule about all recovery quotes
project memory from unverified client email
canonical memory from worker summary
professional doctrine from one dossier
```

## Final rule

```text
Extract in parallel when useful.
Conclude only from consolidated evidence.
Transmit only after approval.
Remember only after governed review.
```
