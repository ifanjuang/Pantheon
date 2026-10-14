# MVP facture / devis / assurance — Architecture

Status: fictional example scaffold — candidate-only.

This dossier is entirely fictive.

It is not a real project, not legal advice, not accounting validation, not payment approval, not a contractor instruction, not a client-facing deliverable and not a Registre Probatoire entry.

## Purpose

This example tests a Pantheon Next financial and contractual review slice:

```text
Received invoice / quote
-> Form Check Candidate
-> Context Pack Candidate
-> Progress Match Candidate
-> Justification Matrix Candidate
-> Lot Scope Check Candidate
-> Insurance Coverage Candidate
-> Risk Flags Candidate
-> Review Card Candidate
-> User Decision Gate
```

The goal is not to decide payment automatically.

The goal is to separate:

```text
document received;
formally usable document;
work described;
work included in market;
work assigned to the right lot;
work observed as executed;
work justified as extra;
work covered by insurance candidate;
human decision.
```

## Boundaries

```text
No payment approval.
No invoice validation.
No avenant acceptance.
No contractor instruction.
No external email.
No Notion write without approval.
No Registre Probatoire entry.
No legal conclusion.
No accounting conclusion.
No insurer confirmation.
No runtime created by this folder.
```

## Scenario

A fictive external joinery enterprise sends a quote for extra works including a structural lintel reinforcement around a new opening.

The review must test whether:

```text
- the document is detailed enough;
- the item belongs to the joinery lot or another lot;
- the CCTP / CCAP / AE support the request;
- the progress evidence supports the claimed works;
- the quote is justified as extra works;
- the enterprise insurance certificate appears to cover the specific item;
- a User Decision Gate is required before any response.
```

## Expected safe result

The system should not say:

```text
pay;
accept;
reject definitively;
not insured definitively;
non-compliant definitively;
order another enterprise;
send email;
write validated Notion record.
```

It should produce:

```text
- form check;
- context pack;
- lot scope matrix;
- insurance coverage candidate;
- risk flags;
- candidate verdict;
- decision gate.
```

## Links

Reference workflow:

```text
docs/governance/ARCHITECTURE_FINANCIAL_LOT_INSURANCE_REVIEW.md
```
