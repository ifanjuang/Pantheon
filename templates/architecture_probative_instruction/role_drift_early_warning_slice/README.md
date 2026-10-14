# Role Drift Early Warning Slice

Status: template — candidate-only architecture probative instruction slice, documented non-implemented.
Boundary profile: non_executable_template.

This slice detects early drift in architecture projects where the practical roles of project owner, architect / MOE, contractors, AMO, BET or replacement contractors begin to blur.

It is based on anonymized ChatGPT project-context patterns from `_maf` and `_affaires` discussions. Names, emails, site addresses and identifying labels must remain masked in examples.

It is not a legal opinion, insurance act, admission, project record, proof-register entry, external communication tool or runtime.

```text
The architect reviews.
The human decides.
```

## Purpose

Some disputes become dangerous because they are detected too late.

The danger is rarely one isolated message. It is a pattern:

```text
project owner bypasses the MOE;
contractor invoices unclear extras;
works proceed without written validation;
replacement contractors are consulted after a default;
reserves, reception, payment and corrective works are mixed;
MOE is expected to continue as if the mission were unchanged;
contractor failure is not recalled early enough;
roles are not restated before conflict hardens.
```

The slice produces an early warning candidate. It does not decide responsibility.

## Core question

```text
Is this project situation beginning to create role drift, responsibility drift, approval drift or evidence gaps that should be recalled before the situation becomes contentious?
```

## Required posture

The output must distinguish:

```text
what happened;
who said it, using anonymized actor labels;
when it was said;
which source class supports it;
which role the actor had;
whether the point is verified, partial, disputed or only conversation-derived;
what should be recalled cautiously;
what must not be admitted;
what requires human review before transmission.
```

## Typical use cases

```text
project owner gives direct instructions to a contractor;
project owner modifies or negotiates a quote directly;
contractor issues unclear extras or unitemized works;
contractor delays, no-shows or fails to finish reserves;
project owner asks whether penalties were applied;
project owner alleges design or advice failure;
replacement company is consulted after default or liquidation;
reception, reserve lifting, payment and corrective works are mixed;
project-owner decisions are not documented;
additional mission or amendment is required but not framed;
works continue after a mission or contractor failure as if the original setup still applied.
```

## Outputs

```text
Early Warning Candidate
Issue / Risk Register Candidate
Role Drift Evidence Tree Candidate
Safe Reminder Candidate
Source Completion Pack
Human Review Gate
```

## Non-goals

```text
no final blame attribution;
no admission;
no legal conclusion;
no external filing;
no formal notice;
no automatic transmission;
no validated proof-register entry;
no canonical project memory;
no continuation of mission scope without amendment.
```

## Source basis levels

```text
chatgpt_project_context_candidate:
  useful for pattern extraction only; not enough for external use.

partial_project_sources:
  original project material partly inspected; still not final.

complete_project_sources:
  required source pack inspected; still requires human review before external effect.
```

## Mandatory anonymization for examples

Examples must not include real names, direct addresses, private contact details, claim identifiers or unmasked personal data.

Allowed placeholders:

```text
[Projet A]
[MOA-A]
[Entreprise-A1]
[Entreprise-A2]
[AMO-A]
[BET-A]
[Assureur]
[Ordre]
[Adresse masquee]
[Date a verifier]
```

## Verification rule

Every response candidate produced from this slice must carry:

```text
source_basis:
dates_verified: yes | no | partial
sources_verified: yes | no | partial
names_anonymized: yes | no
external_transmission_allowed: no by default
human_review_required: yes
```

## Boundary phrase

```text
A role drift warning is not a finding of fault.
A reminder of role is not an accusation.
A source candidate is not proof.
A draft is not a sent position.
```
