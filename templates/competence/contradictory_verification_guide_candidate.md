# Contradictory Verification Guide Candidate

Status: candidate Guide de compétence.

Authority status: non-canonical support resource.

Runtime status: non-executable.

This guide distills practical verification patterns that may support the governed rite `AUTOCRITIQUE_CONTRADICTOIRE` and a future bounded Hermes skill projection.

It does not define Pantheon Role authority, approve outputs, execute checks, install a skill, select a runtime, dispatch tools, create Evidence, mutate doctrine or authorize external action.

```text
Guide describes.
Rite governs.
Task Contract bounds.
Hermes may execute externally.
Trace records observations.
ZEUS states procedure.
The human decides when consequential.
```

## Intended use

Use this guide when a Task Contract has already authorized work associated with `AUTOCRITIQUE_CONTRADICTOIRE` and the reviewer needs an operational checklist proportionate to the selected rite mode.

The guide may support:

- review of a declared code or configuration change;
- review of a document candidate before delivery;
- review of an architecture or doctrine proposal;
- review of a data transformation or calculation;
- review of a completion report whose claims can be observed.

## Non-use

Do not use this guide to:

- trigger the rite automatically;
- infer authorization from a report or user-interface state;
- expand task scope silently;
- repair defects during an independent verdict;
- weaken tests or expected outcomes to obtain a pass;
- convert runtime success into Evidence;
- approve, send, publish, merge, deploy or canonize.

## Operational sequence

### 1. Read the boundary

Read the Task Contract before reviewing the candidate.

Identify:

```text
intent
included scope
excluded scope
selected rite mode
review posture
admitted inputs
allowed observations
allowed outputs
forbidden outputs
approval ceiling
stop condition
```

If a required boundary is absent, record the gap. Do not invent authority.

### 2. Freeze the candidate

Identify the exact candidate or completion state being reviewed.

Examples:

```text
commit or diff range
document revision
calculation table
rendered interface
API response
completion report
```

A moving target weakens review. Record any change that occurs after the review starts.

### 3. Extract material claims

Convert the candidate or report into a concise list of claims.

Separate:

```text
fact
fresh observation
interpretation
recommendation
completion claim
untouched-area claim
```

Ignore stylistic statements unless wording changes professional, legal, contractual, evidentiary or approval meaning.

### 4. Establish actual change or state

When applicable, inspect the actual artifact or change set before relying on its narrative.

Examples:

- inspect the diff and changed files;
- open the produced document or interface;
- inspect the calculated values and admitted inputs;
- compare a generated output with the source material;
- verify that allegedly untouched areas are absent from the change set.

### 5. Reproduce material checks

When authorized and proportionate, reproduce the checks supporting material completion claims.

Examples:

- re-run the named test, build or lint command;
- repeat a calculation;
- query the named endpoint with the admitted parameters;
- render or open the produced artifact;
- compare observed output with the declared expected result.

Do not substitute code reading or confidence for execution when the claim is expressly about a successful run.

If a check cannot be run, record:

```text
check
reason unavailable
impact on the claim
possible next allowed action
```

### 6. Search for contradictions and review frauds

Inspect for patterns such as:

- weakened or skipped checks;
- changed expected values that conceal a specification conflict;
- completion claimed without fresh observation;
- changes outside the authorized scope;
- outward action without authorization;
- implementation that satisfies a test while contradicting doctrine or specification;
- scratch files, debug output or residual artifacts;
- polished wording that conceals uncertainty or unsupported claims.

A finding must point to an observation or admitted source. Suspicion alone is not a finding.

### 7. Check analogous occurrences

When a structural defect is found and the Task Contract permits the search, define the wrong construct precisely and search the authorized scope for analogous occurrences.

Record:

```text
searched_construct
search_scope
other_occurrences
unsearched_areas
```

Do not modify other occurrences under the original task unless that modification is explicitly authorized.

### 8. Reconcile claims

For every material claim, record:

```text
claim
observation_or_source
support_status
limit
next_allowed_action
```

Use only:

```text
supported
partially_supported
contradicted
not_observed
not_verifiable
```

These are review statuses, not approval or Evidence statuses.

### 9. Close without repairing

In `independent_review`, do not repair the candidate while delivering the verdict.

Name the correction path and return it for a separate bounded task, Task Contract revision, task split, User Decision Gate or ZEUS procedure status.

In `self_review`, a separately authorized correction may occur, but the report must distinguish:

```text
what was initially observed
what was corrected
what was re-observed afterward
```

### 10. Produce a compact review

Recommended output:

```text
rite_id: AUTOCRITIQUE_CONTRADICTOIRE
selected_mode:
review_posture:
candidate_reviewed:
claims:
observations_performed:
unobserved_or_unverifiable:
contradictions:
analogous_occurrence_check:
risk_notes:
correction_path:
Evidence_Pack_impact:
User_Decision_Gate:
ZEUS_status_candidate:
next_allowed_action:
```

The output is a Rite Review Card candidate or supporting note. ZEUS closure remains separate.

## Mode adaptation

### Light

- identify the main unsupported or overconfident claim;
- separate fact from interpretation;
- avoid runtime reproduction unless one cheap decisive check is already admitted;
- return one or two findings and the next allowed action.

### Standard

- reconcile all material claims;
- inspect admitted sources and produced artifacts;
- reproduce accessible decisive checks when proportionate;
- expose every material `not_observed` or `not_verifiable` item.

### Full

- prefer independent review where feasible;
- reproduce material completion claims;
- reconcile the report with the actual diff or artifact state;
- perform an analogous occurrence check when a structural defect may recur;
- state unsearched areas and environment limits;
- keep repair outside the verdict.

## Stop conditions

Stop and return a bounded review when:

- required scope or authorization is missing;
- the candidate changes materially during review;
- the runtime or credentials required for a material check are unavailable;
- the task requires access outside the admitted boundary;
- repeated checks cannot distinguish implementation failure from specification conflict;
- repair would be required to continue an independent verdict;
- another rite appears necessary;
- a consequential decision requires a human gate.

## External inspiration

This guide may be compared with external agent-discipline and adversarial-verification methods, including the Fable Method repository.

Pantheon distills only compatible verification practices.

```text
external method != adopted dependency
repository claim != validated benchmark
installed skill != approved competence
runtime success != Evidence
```

No external package, skill or runtime is adopted by this guide.
