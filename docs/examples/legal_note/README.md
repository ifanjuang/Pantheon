# Example — Legal Note from an Incomplete or Contradictory Case File

Status: fictional professional example — educational support only.

Doctrine status: draft under elaboration.

This legal example is a working draft intended to be refined through consultation with legal professionals.

It must not be treated as a finalized professional doctrine, legal advice, procedural recommendation or compliance position.

This example illustrates how Pantheon Next may frame AI-assisted preparation of a legal working note.

It does not replace a lawyer’s professional judgment, source verification, confidentiality duties or responsibility.

## Scenario

A law firm needs to prepare a strategy note from:

- an opposing brief;
- a disputed contract;
- client exhibits;
- email correspondence;
- possible case-law references.

The risk is not only that an AI may write something false.

The risk is that it may write something plausible, smooth over contradictions or present an unchecked source as authority.

## User request

```text
From the opposing brief, the disputed contract and my exhibits, prepare a strategy note for the hearing.
```

## Mission sheet — Task Contract excerpt

```text
Mission        : Strategy note — hearing preparation
Scope          : Case [CASE-MASKED], client [CLIENT-MASKED]
Allowed        : client exhibits P-01 to P-08
                 opposing brief
                 disputed contract
                 verified official sources only for legal references
Forbidden      : other firm cases
                 unrelated client material
                 unverified case-law as authority
Output         : candidate strategy note + contradiction table
Approval       : lawyer review required before use or transmission
Memory         : no firm memory without explicit approval
```

## Evidence Pack excerpt

```text
Sources used:
- opposing brief [PDF, 52 p.]
- contract [DATE-MASKED]
- exhibits P-01 to P-08
- official legal source query [to verify]

Assumptions:
- exhibit numbering supplied by the user is correct
- contract version appears to be the latest supplied version
- one possible legal reference is not validated yet

Contradictions:
- opposing brief §17 alleges delivery on [DATE]
- exhibit P-03 suggests delivery occurred later
- exhibit P-05 may support notice, but proof of receipt is missing

Risk notes:
- do not cite unverified case-law as authority
- do not smooth factual contradictions
- do not treat draft strategy as client advice before lawyer review
```

## Candidate deliverable excerpt

```text
## Strategy note — candidate

### 1. Factual contradiction to preserve

The opposing brief states that delivery occurred on [DATE].
Exhibit P-03 appears to show a delivery slip dated [DATE + 15 days].
This contradiction should remain visible and must not be summarized away.

Status: strong point if exhibit authenticity and chronology are confirmed.

### 2. Possible argument — contractual non-performance

Source:
- exhibit P-03, p. 4
- exhibit P-05, email exchange of [DATE]

Limit:
- proof of receipt is missing.

Status: candidate argument, lawyer review required.

### 3. Legal reference

Reference placeholder: [CASE-LAW-TO-VERIFY]

Status: not usable until verified on an authoritative source.
```

## User Decision Gate

A User Decision Gate is needed if the user asks to send or rely on the note while a legal reference remains unverified.

```text
Conflict:
The note is readable, but one authority is not verified.

Options:
1. remove the reference;
2. keep it marked as unverified;
3. verify before use;
4. block transmission.
```

## Memory rule

Possible Register Candidate:

```text
Case [CASE-MASKED] contains a preserved contradiction between opposing brief §17 and exhibit P-03.
```

This must remain scoped to the case.

It must not become general firm memory.

## Why this example matters

The useful distinction is:

```text
well-written note ≠ verified legal analysis
source found ≠ authority
candidate strategy ≠ advice sent to client
role agreement ≠ approval
```

## Professional review needed

This draft should be reviewed with legal practitioners before being presented as a stable use-case doctrine.

Expected review points:

- professional secrecy and confidentiality boundaries;
- source verification standards;
- case-law citation policy;
- admissible and inadmissible source categories;
- transmission thresholds;
- memory retention limits for legal matters.
