# Example — Architecture / MOE — Pre-Execution Simulation Before Client Email

Status: fictional professional example — educational support only.
Boundary profile: documentation_only.

This example extends `docs/examples/architecture_devis_reprise/README.md` with a pre-execution simulation step.

It is not legal advice.

It is not technical validation.

It is not insurance advice.

It does not replace the architect's professional judgment, site knowledge, contractual review, contradictory verification or liability analysis.

## Purpose

The goal is to show how `PRE_EXECUTION_SIMULATION.md` can be used before sending a client-facing email that might accidentally validate a recovery quote.

The risk is not hallucination only.

The risk is that a clear draft may create professional or contractual ambiguity.

## Starting point

User request:

```text
Prepare an email to the client validating the recovery quote so the new company can start quickly.
```

Initial classification:

```text
simple drafting request
→ client-facing professional communication
→ possible external effect
→ high-risk wording
→ pre-execution simulation recommended
```

## Candidate email to test

This is not the final email.

It is the candidate to simulate before any transmission.

```text
Subject: Recovery quote — proposed next step

Hello [CLIENT],

I reviewed the recovery quote and it appears broadly consistent with the remaining works.

You may confirm your agreement so the new company can proceed, subject to the usual checks on site.

Best regards,
[ARCHITECT]
```

## Task Contract excerpt

```text
task_id: example-architecture-recovery-quote-simulation
intent: stress-test client-facing wording before transmission
scope: fictional architecture / MOE recovery quote dossier
candidate_tested: draft client email
risk_level: high
approval_ceiling: no external transmission without architect decision
memory_rule: no memory by default
simulation_required: yes
simulation_goal: detect whether the candidate email may imply validation, reception, scope approval or professional commitment
allowed_sources:
  - recovery quote excerpt [MASKED]
  - initial CCTP excerpt [MASKED]
  - meeting report excerpt [MASKED]
  - reception status note [MASKED]
excluded_sources:
  - other project dossiers
  - unverified legal conclusions
  - insurance strategy beyond provided source
expected_output:
  - Simulation Result Candidate
  - Evidence Pack simulation entry
  - User Decision Gate if material risk remains
```

## Scenario set

The scenario set is intentionally small.

Pantheon does not need a full adversarial theatre.

It needs enough pressure to reveal the material risk.

```text
scenario_1: client interprets the email as approval to sign the quote
scenario_2: company interprets the email as technical validation of its price and scope
scenario_3: later dispute argues that the architect confirmed the remaining works
scenario_4: missing reception status makes the phrase remaining works ambiguous
scenario_5: quote includes one item outside the original CCTP
```

## Simulated outcomes

| Scenario | Simulated failure mode | Severity | Governance result |
|---|---|---:|---|
| Client signs immediately | The email says broadly consistent and may confirm agreement. | high | Transmission blocked. |
| Company proceeds without clarification | Subject to usual checks is too vague to preserve scope. | high | Revise candidate. |
| Dispute over previous works | Remaining works may imply previous works are accepted as baseline. | high | Add reception reservation. |
| Reception status missing | Draft could blur progress, payment, acceptance and reception. | critical | User Decision Gate required. |
| Extra item outside CCTP | Draft does not separate in-scope and additional works. | high | Request quote breakdown. |

## Simulation Result Candidate

```text
result_status: risk_detected

summary:
The candidate email is too close to approval language. It may be read as technical validation of the recovery quote and authorization to proceed.

risks_detected:
- global validation implication
- possible approval of scope and price
- ambiguity around reception status
- missing split between initial-scope, additional, corrective and uncertain items
- external transmission risk

recommended_next_action:
Do not send this candidate.
Prepare a neutral clarification email or internal note only.
Open a User Decision Gate before any client-facing transmission.
```

## Evidence Pack simulation entry

```text
simulation_id: sim-architecture-recovery-quote-001
linked_task_contract: example-architecture-recovery-quote-simulation
simulation_goal: detect risky interpretation before client email transmission
candidate_tested: draft client email dated [DATE-MASKED]
scenario_set:
  - client signs immediately
  - company proceeds without clarification
  - later dispute over architect validation
  - missing reception status
  - quote item outside CCTP
result_status: risk_detected
risks_detected:
  - validation wording
  - reception ambiguity
  - scope ambiguity
  - external effect risk
limitations:
  - fictional example
  - no real contract reviewed
  - no real site condition assessed
approval_impact: transmission blocked pending professional decision
memory_impact: no memory by default
User_Decision_Gate_impact: required if client-facing email remains requested
recommended_next_action: revise to neutral clarification or prepare internal note only
```

## User Decision Gate

```text
Transmission blocked pending decision.

Object of conflict:
The proposed email may be read as approval of the recovery quote, but available evidence does not establish scope, reception status, technical verification or responsibility allocation.

Role positions:
- ATHENA: split the task into quote classification, source review and possible client wording.
- ARGOS: source gap on CCTP comparison and reception status.
- THEMIS: wording creates professional and contractual ambiguity.
- APOLLO: the draft is readable but too permissive.
- HEPHAISTOS: can produce a safer clarification candidate.
- IRIS: do not transmit until approval.
- ZEUS: human decision required.

Severity:
high

Options:
1. Convert the email into a neutral clarification request.
2. Produce an internal note only.
3. Block response until CCTP, quote breakdown and reception status are checked.
4. Prepare two variants for architect review, both marked not approved for transmission.

Recommended procedure:
Option 1 or 2. Do not send the tested candidate.
```

## Revised candidate after simulation

This revised draft remains a candidate.

It is still not approved for transmission.

```text
Subject: Recovery quote — clarifications needed before position

Hello [CLIENT],

I reviewed the recovery quote as a working document, but I would avoid treating it as approved at this stage.

Before any decision, the quote should be separated into:

1. items corresponding to the initial scope;
2. items that may be additional or outside the initial CCTP;
3. items requiring site verification;
4. items whose wording may affect how previous works are handled.

I suggest asking the company for a clarified breakdown before any approval.

This message does not constitute reception of previous works, technical validation of hidden conditions, global approval of the quote or authorization to proceed.

Best regards,
[ARCHITECT]
```

## Decision effects

| Decision | Output effect | Evidence effect | Memory effect | Transmission effect |
|---|---|---|---|---|
| Send original candidate | Rejected in this example | Simulation risk ignored | Invalid | Blocked |
| Send revised clarification after review | Candidate may become sendable | Simulation risk mitigated but not erased | No memory by default | Requires architect approval |
| Internal note only | No client-facing wording | Evidence preserved | No memory by default | No external effect |
| Wait for sources | No output yet | Source gap becomes next step | No memory | No external effect |

## What this example shows

```text
Simulation does not make the email safe.
Simulation reveals why the email is not safe yet.
```

The useful output is not the simulated score.

The useful output is the visible tension:

```text
fast client communication
vs.
professional and contractual ambiguity
```

## Boundary

This example does not imply:

- automatic simulation execution;
- automatic blocking engine;
- automatic approval;
- automatic email sending;
- automatic memory promotion;
- technical validation of the quote;
- legal or insurance advice;
- implementation of Future AGI;
- implementation of a Hermes simulator.

## Final reading

```text
Before a polished email leaves the cockpit, simulate how it could be used against the dossier.
Then decide with evidence, not fluency.
```
