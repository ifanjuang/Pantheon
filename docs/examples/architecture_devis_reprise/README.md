# Example — Architecture / MOE — Recovery Quote and Dangerous Client Validation

Status: fictional professional example — educational support only.

This example is the recommended first demo for a practitioner.

It shows why Pantheon Next is useful when a raw AI answer would produce a clean, polite and potentially dangerous professional message.

It is not legal advice.

It is not technical validation.

It is not insurance advice.

It does not replace the architect’s judgment, site knowledge, contractual analysis or professional liability review.

## Related simulation example

For the same fictional dossier with a dedicated pre-execution simulation step, read:

- [`PRE_EXECUTION_SIMULATION_EXAMPLE.md`](PRE_EXECUTION_SIMULATION_EXAMPLE.md)

That companion file stress-tests a candidate client email before transmission and shows how simulation can reveal risk without authorizing delivery.

## Why a practitioner may care

The professional problem is simple:

```text
The client wants a quick answer.
The dossier is incomplete.
A well-written email may accidentally validate too much.
```

This is the kind of situation where raw AI is dangerous because it optimizes for a fluent answer.

Pantheon should optimize for reviewable friction.

The value is not that Pantheon writes a better email.

The value is that Pantheon may refuse to treat the email as safe to send.

## Scenario

A project has a failing or defaulting contractor.

A new company proposes a recovery quote.

The client asks the architect / MOE to prepare an email validating or responding to the quote.

The dossier is sensitive because:

- previous works may not have been received;
- the quote may include works outside the initial CCTP;
- site conditions may be uncertain;
- the contractor’s failure may affect responsibility and sequencing;
- a poorly worded email could be interpreted as professional validation;
- the architect’s DET mission may have limits.

## User request

```text
Prepare an email to the client validating the recovery quote.
```

## Raw AI answer — unsafe version

A generic assistant may produce something like this:

```text
Hello [CLIENT],

After reviewing the recovery quote, I confirm that it appears consistent with the works to be completed.
You may approve it so the new company can proceed quickly.

Best regards,
[ARCHITECT]
```

This answer is fluent.

It is also professionally dangerous.

It may imply:

- global technical validation;
- acceptance of the recovery quote;
- indirect approval of scope and price;
- confusion between payment, progress, reception and validation;
- silence about missing contradictory verification;
- silence about items outside the initial CCTP.

## Pantheon interpretation

The request must not be treated as a simple drafting task.

It contains professional-risk tension:

```text
reply quickly to the client
vs.
avoid validating works, scope, price, responsibility or reception status too early
```

Pantheon should reclassify the request:

```text
simple email writing
→ sensitive client-facing communication
→ User Decision Gate candidate
```

## Mission sheet — Task Contract excerpt

```text
Mission        : Review recovery quote and prepare client-facing response
Scope          : Project [PROJECT-MASKED], recovery quote [QUOTE-ID-MASKED]
Allowed        : recovery quote
                 initial CCTP
                 contract / mission limits
                 site reports and meeting minutes
                 previous payment and progress records
                 photographs or constat if available
Forbidden      : other client dossiers
                 assumptions about hidden defects not documented
                 definitive legal or insurance conclusions
Expected       : internal risk note + candidate client email
Approval       : architect review required before transmission
Memory         : no durable memory unless validated and scoped to project
```

## Governance College status

| Role | Status | Finding |
|---|---|---|
| ATHENA | `ok_with_reserve` | The task must be split into quote review, risk note and possible email. |
| ARGOS | `source_insufficient` | CCTP, site reports, quote breakdown and reception status must be checked before validation. |
| THEMIS | `risk_detected` | A validation email may create ambiguity around scope, responsibility or reception. |
| APOLLO | `ok_with_reserve` | A clear email can be written, but clarity does not remove the risk. |
| HEPHAISTOS | `produced_candidate` | Internal note and neutral email can be prepared as candidates. |
| IRIS | `transmission_blocked` | External send should wait for explicit approval. |
| ZEUS | `human_decision_required` | Safe procedure is clarification or internal note, not global validation. |

## Source and evidence review

| Item | Status | Comment |
|---|---|---|
| Initial CCTP | Required | Needed to compare initial scope and recovery quote. |
| Recovery quote | Required | Must be separated into in-scope, out-of-scope and unclear items. |
| Site reports / meeting minutes | Required | Needed to understand execution history and reservations. |
| Reception status | Critical uncertainty | If no reception occurred, avoid wording that implies acceptance. |
| Contractor default context | Required | Must be described factually, not over-interpreted. |
| Client request | Required | Clarifies whether the client asks for technical opinion, validation or negotiation wording. |
| Insurance / legal position | Not assumed | Must be referred to competent adviser if needed. |

## Useful tensions

| Tension | Pantheon handling |
|---|---|
| The client wants a quick answer. | Produce a candidate email, but mark it as requiring architect review. |
| The quote may be partly valid. | Split into categories instead of approving globally. |
| Prior works may not be received. | Avoid language implying reception, acceptance or validation. |
| Some items may be corrective works. | Ask whether they are included, additional, remedial or uncertain. |
| The architect has DET limits. | Make mission boundary explicit before advising beyond scope. |

## User Decision Gate

Pantheon should block direct transmission and ask the professional to choose a procedure.

```text
Transmission blocked pending decision.

Object of conflict:
The client asks for validation of a recovery quote, but the dossier does not yet establish
which items are in-scope, additional, remedial, technically verified or linked to reception status.

Role positions:
- ATHENA: split the task before writing.
- ARGOS: source gap on CCTP comparison and reception status.
- THEMIS: validation wording may create professional or contractual ambiguity.
- APOLLO: a clear email is possible, but not enough to make it safe.
- HEPHAISTOS: internal note and neutral clarification email can be prepared.
- IRIS: external transmission blocked until decision.
- ZEUS: human decision required.

Severity:
high

Options:
1. Prepare a neutral clarification email, not a validation.
2. Prepare an internal note only.
3. Block response until missing sources are checked.
4. Prepare two variants for architect review.

Recommended procedure:
Option 1 or 2. Do not send a global validation email in the current state.
```

## Evidence Pack excerpt

```text
Evidence Pack — Recovery quote review

Sources used:
- recovery quote [QUOTE-ID-MASKED]
- CCTP [VERSION-MASKED]
- site report [CR-XX]
- contractor default note [DATE-MASKED]

Assumptions:
- no formal reception identified in supplied documents
- some quote items appear outside the initial CCTP, to verify
- site condition requires contradictory verification before firm position

Contradictions / gaps:
- quote item 2.3 described as reprise, but no matching reservation found
- quote item 4.1 may be improvement rather than recovery
- payment history does not establish reception or validation

Risk note:
- do not state that the quote is accepted or technically validated
- do not state that previous works are received
- recommend neutral wording and request missing checks
```

## Candidate deliverable — internal note

```text
The recovery quote should not be approved globally at this stage.

Suggested classification:

1. Items apparently within initial scope
   - to compare against CCTP and remaining balance.

2. Items possibly outside initial scope
   - to request clarification and separate pricing.

3. Items requiring site verification
   - to be checked contradictorily before recommendation.

4. Items with responsibility or insurance implications
   - to avoid validating in client email without further advice.
```

## Candidate deliverable — neutral client email

```text
Subject: Recovery quote — points to clarify before position

Hello [CLIENT],

I have reviewed the recovery quote as a working document.

At this stage, I would avoid treating it as globally validated. Several items need to be separated before a position can be taken:

1. items that appear to correspond to the initial scope;
2. items that may be additional or outside the initial CCTP;
3. items that require site verification before confirmation;
4. items whose wording may affect the handling of previous works.

I suggest we ask the company for a clarified breakdown before any approval, separating recovery works, additional works and items requiring verification.

This review does not constitute reception of previous works, validation of hidden conditions or global approval of the quote.

Best regards,
[ARCHITECT]
```

## Decision effects

| Option | Effect on output | Effect on evidence | Effect on memory | Effect on transmission |
|---|---|---|---|---|
| Neutral clarification email | Candidate email allowed | Evidence gap remains visible | No memory by default | Possible after architect review |
| Internal note only | No client-facing output | Evidence gap preserved | No memory by default | No external effect |
| Block until sources checked | No output yet | Source request becomes next step | No memory | No external effect |
| Two variants | Variants for review | Risks shown per variant | No memory | Transmission still blocked |

## What Pantheon prevents

This example matters because the risk is not only hallucination.

The risk is premature professional commitment.

Pantheon helps avoid:

- a polite validation email that goes too far;
- confusion between draft, opinion, approval, reception and memory;
- hidden source gaps;
- lost contradictions;
- external transmission without decision;
- memory promotion based on an unresolved dossier state.

## Memory rule

Possible Register Candidate:

```text
Project [PROJECT-MASKED] has unresolved recovery quote classification issues as of [DATE].
```

This must not become a Registre Probatoire entry unless:

- project scope is confirmed;
- source documents are linked;
- architect approves retention;
- memory is scoped to the project only.

## Final reading

A practitioner should be able to understand this in one line:

```text
Pantheon stops the AI from turning a well-written draft into a risky professional act.
```

The professional remains responsible for the final position.
