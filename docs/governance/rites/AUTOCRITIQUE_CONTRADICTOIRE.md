# Autocritique Contradictoire

Status: active doctrine - shared rite.

## Intention

Review a candidate output as if it came from a third party.

The goal is to detect smooth but fragile conclusions before they become deliverables.

Producing is not validating.

Convincing is not proving.

A completion report is a set of claims to review, not proof that the work is complete.

## Trigger conditions

Use this rite when:

- a draft appears convincing too quickly;
- output may affect professional responsibility;
- doctrine, approval, memory or external transmission is involved;
- a result must be sent, published, committed or retained;
- a claim sounds clear but lacks visible evidence;
- a technical completion claim can be checked against an observable result;
- a defect found in one location may have analogous occurrences elsewhere;
- APOLLO can make the output clearer but THEMIS may still block delivery.

## Anti-triggers

Do not use this rite when:

- the task is a low-risk formatting change;
- the output is explicitly exploratory only;
- evidence and approval are irrelevant to the next step;
- the user asked only for a private brainstorming note;
- the review would add ceremony without changing decision, evidence, risk, memory or delivery posture.

## Roles called

- THEMIS challenges risk, contradiction and approval boundary.
- APOLLO checks clarity, completeness and over-smoothing.
- ARGOS checks source support and provenance.
- ATHENA restructures after critique if required.
- ZEUS decides status and next procedure.

Role viewpoints remain governance responsibilities.

They are not runtime workers and do not imply a hidden agent debate.

## Review posture

The Task Contract should state one of two review postures when the distinction matters:

```text
self_review
independent_review
```

`self_review` is proportionate for internal, reversible and low-consequence work.

`independent_review` is preferred when:

- the result is consequential;
- a code, schema, migration or configuration change is declared complete;
- an artifact may be sent, published, committed, canonized or relied upon professionally;
- the executor may be anchored by its own implementation;
- verification requires re-running checks or inspecting effects independently.

Independent review means that the reviewer does not inherit trust from the executor's report.

It does not make the reviewer a higher authority.

```text
separate review != approval authority
independent execution != validated truth
review success != external-action authorization
```

## Procedure

1. Freeze the candidate output or declared completion state.
2. Extract explicit and implicit claims that can be supported, contradicted or left unverified.
3. Separate fact, observation, interpretation and recommendation.
4. Identify unsupported claims.
5. Identify contradictions.
6. When proportionate and authorized, verify technical claims by fresh observation rather than report wording alone.
7. When a structural defect is found, search the authorized scope for analogous occurrences.
8. Identify seductive but unsafe phrasing.
9. Identify delivery, approval and memory implications.
10. Propose corrections or blocking conditions.
11. Assign ZEUS status and the next allowed action.

## Verification by observation

When a claim is technically observable, the rite should prefer a fresh observation within the Task Contract boundary.

Examples include:

- inspect the actual diff rather than trust a summary;
- re-run the named test, build, check or query;
- open the produced document, image or interface;
- compare output values with admitted sources;
- verify that an allegedly untouched area is absent from the change set;
- confirm that a claimed artifact exists and contains the expected structure.

Reading and inference may support review, but they must not be described as execution evidence when nothing was run or observed.

```text
reported != observed
readable != verified
runtime_success != Evidence
not_observed != passed
```

If observation is unavailable because of credentials, runtime, environment or scope, the limitation remains explicit.

## Test-blindspot check

A passing test or successful check establishes only what that check actually covered. When completion depends materially on tests, the rite should ask what the passing checks do not establish before accepting the completion claim.

Review proportionally:

```text
claimed_property
checks_that_support_it
material_cases_not_covered
environment_or_fixture_limits
remaining_failure_modes
```

Useful questions include:

- does the check exercise the real component or only a mock/fixture?
- does it cover the relevant failure path, boundary condition or concurrency case?
- does it verify the semantic consequence or only syntax/build success?
- could the same defect survive in an unsearched equivalent location?
- is the tested environment materially different from the target environment?

Do not invent theoretical edge cases that cannot change the decision. Retain only blindspots material to the claimed completion, risk or consequence.

```text
tests_pass != claimed_property_proven
coverage exists != relevant case covered
mock success != provider behavior established
check success != professional approval
```

## Analogous occurrence check

A defect discovered in one place may indicate a repeated construct.

When the defect is structural and the search is proportionate, the rite may perform an `analogous_occurrence_check` within the authorized scope.

Examples:

- repeated obsolete imports;
- hard-coded routes or schema identities;
- duplicated compatibility dependencies;
- repeated unsupported claims;
- the same semantic confusion across several documents;
- equivalent unsafe configuration patterns.

The check must record:

```text
searched_construct
search_scope
other_occurrences
unsearched_areas
```

No occurrence outside the Task Contract scope may be modified by implication.

Finding another occurrence may justify a Task Contract revision or task split; it does not silently extend the current task.

## Claim reconciliation

The retained review should reconcile material claims with observations in a compact form:

```text
claim
observation_or_source
support_status
limit
next_allowed_action
```

Recommended support statuses:

```text
supported
partially_supported
contradicted
not_observed
not_verifiable
```

These are review statuses.

They are not truth, Evidence validation, approval, memory admission or permission to act.

## Independent-review integrity

During `independent_review`, the reviewer should not repair the candidate while producing the verdict.

Repair and review may occur in separate bounded tasks, but combining them destroys the independence of the review and obscures what was actually verified.

If a defect is found:

- record the defect;
- identify its consequence;
- state the correction path;
- close or escalate the rite;
- create or revise a separate Task Contract before repair when required.

## Outputs

- claim reconciliation;
- contradiction report;
- unsupported claims;
- observation notes and unavailable checks;
- test-blindspot findings when completion depends materially on tests;
- analogous occurrence findings when applicable;
- risk notes;
- correction actions;
- revised candidate if separately authorized and outside an independent-review verdict;
- Evidence Pack impact;
- User Decision Gate if the tension remains unresolved.

## Evidence Pack impact

If this rite affects a deliverable, the Evidence Pack should record:

- claim separation;
- observations actually performed;
- checks that could not be performed;
- test coverage limits material to the completion claim;
- unsupported statements;
- contradiction notes;
- analogous occurrence scope and findings when applicable;
- risk classification;
- correction path;
- approval implication;
- ZEUS status.

The Evidence Pack must not store hidden chain-of-thought, raw scratchpad or autonomous agent transcript.

A runtime observation may support an Evidence Pack Candidate.

It does not become validated Evidence automatically.

## User Decision Gate impact

Open a User Decision Gate when:

- the output may be clear but unsafe to send;
- the evidence is insufficient for delivery;
- a material claim is contradicted or not verifiable;
- role disagreement changes the outcome;
- analogous occurrences expand the meaningful scope;
- the user must choose between speed, proof, risk or external effect.

## Memory impact

The rite may propose a Register Candidate only when the review reveals a reusable scoped pattern.

The rite must not promote a Registre Probatoire entry.

## Failure modes

- style-only critique that misses substance;
- reading code or prose and calling it verified without observation;
- trusting the executor's completion report;
- treating passing tests as proof of untested properties;
- manufacturing irrelevant edge cases after the decision-relevant picture is stable;
- repairing during an independent verdict;
- searching analogues so broadly that the task scope silently expands;
- excessive caution that blocks harmless drafts;
- treating clarity as verification;
- treating critique as proof;
- hiding unresolved contradictions behind rewritten prose;
- treating a successful check as professional approval.

## Forbidden drift

This rite must not become:

- autonomous self-review loop;
- automatic approval gate;
- runtime validator owned by Pantheon;
- hidden debate;
- automatic test runner or scheduler;
- exhaustive fuzzing mandate;
- scope-expansion mechanism;
- memory promotion pipeline;
- replacement for human review.

## Final rule

A review must distinguish what was claimed, what was observed, what remains uncertain and what may happen next.

Producing is not validating.

Convincing is not proving.
