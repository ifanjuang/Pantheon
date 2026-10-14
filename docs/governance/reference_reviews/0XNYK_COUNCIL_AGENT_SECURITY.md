# 0xNyk Council and agent-security — bounded Pantheon distillation

Status: external reference review / candidate patterns only.

Reviewed upstream references:

```text
0xNyk/council-of-high-intelligence
observed head = dd09e28e9522f20f99dbbd7b8128eb307a0ea7e8
latest observed commits after the functional work are star-history maintenance

0xNyk/agent-security
observed head = a8ca700f52613e2baf508c7e6f91d9bcaf52c56e
```

Pantheon baseline for this review:

```text
Pantheon-Next/main = d49c7b71c11f3927461fcc4540d4a11081b0b2ff
Hermes             = v0.21.3 / v2026.9.14
```

This review does not select either repository as a dependency. It does not add a
runtime, agent team, provider router, security authority, PEP, installer or
automatic skill admission path.

## Objective

Extract only mechanisms that close a demonstrated Pantheon gap or provide a
useful qualification hypothesis while preserving existing owners.

The two useful families are:

```text
Council
-> deliberation method candidate

agent-security
-> deterministic pre-vetting pattern candidate
```

The repositories themselves are not the architecture.

## Current-owner gap analysis

### Council

Pantheon already owns the important authority boundaries:

- Governance College preserves distinct review pressures and disagreement;
- User Decision Gate keeps consequential unresolved tension human-owned;
- Hermes remains the single external execution runtime;
- merged PR Pantheon-Next#1108 defines the pairwise qualification method for direct,
  delegation, goal-style iteration and Kanban; issue Pantheon-Next#1093 owns the empirical follow-up;
- Result Candidates remain candidates rather than Decisions or Evidence.

Therefore a Council runtime, MCP server, provider router, voting authority,
persona roster or fifth execution strategy would duplicate existing owners.

The narrower gap is procedural: bounded delegation does not itself require
independent problem restatement, method-diverse analysis, anonymized
cross-review, explicit revision after objections, or a synthesis that preserves
unresolved disagreement and kill criteria.

Candidate method:

```text
admitted hard/ambiguous question
        |
        v
independent problem restatement
        |
        +--> material framing divergence -> surface ambiguity
        |
        v
independent bounded analyses
(structural / empirical / adversarial, chosen for the task)
        |
        v
anonymized cross-review
(strongest objection / unsupported assumption / missing evidence)
        |
        v
revision only when a concrete flaw is identified
        |
        v
independent synthesis
        |
        v
convergences
unresolved disagreements
uncertainties
acceptable compromises
kill criteria
concrete next step
```

This is a **Method / Skill candidate**, not a new Hermes execution strategy.
It should be composed from already-qualified Hermes primitives. It must not be
added to Pantheon-Next#1093's direct/delegation/goal/Kanban comparison as a fifth mode.

A later implementation is justified only after Pantheon-Next#1093 establishes the relevant
primitive behavior and a small A/B qualification shows that this composition
materially improves difficult reasoning compared with simpler bounded
delegation.

Do not use numerical confidence, weighted LLM voting or majority agreement as
governance status.

```text
Council member != Pantheon Role
Council synthesis != Pantheon Decision
Council FACT label != Evidence
Council consensus != authorization
Council runtime success != authorization
```

### agent-security

Pantheon already owns external-tool policy, capability qualification,
consequential-effect authority and the Pantheon-owned effect chokepoint.

The useful gap is earlier and narrower: an external repository, Skill or
package can be subjected to deterministic static tripwires before deeper
boundary review or any execution. The latest observed upstream head adds a
network-free `WORM` class for committed-config JavaScript worm shapes; this
strengthens the concrete pre-vet example without changing its claim ceiling.

Candidate placement:

```text
external candidate
        |
        v
deterministic static pre-vet
(no candidate execution)
        |
        +--> known severe pattern -> reject / manual security review
        |
        v
WATCHLIST / boundary review
        |
        v
qualification
        |
        v
Capability / binding decision
```

The pre-vet may look for known leak/dropper shapes, suspicious outbound
behavior, credential exposure patterns and prompt-injection/covert-action
shapes in fetched content. It should emit findings and coverage limits rather
than a safety verdict.

The claim ceiling is mandatory:

```text
no tripwire matched != safe
static vet passed != admitted
admitted != authorized
content scan clean != trusted instruction
unknown != safe
```

The upstream scripts are not selected as Pantheon dependencies by this review.
Before implementation, compare their exact checks against current repository,
Skill and external-tool admission tests. Reuse existing scanners where coverage
already exists; add only missing deterministic checks.

This pre-vet is defense in depth. It is never the Pantheon effect PEP and never
authorizes runtime use.

## Deliberation output placement

If the Council method is later qualified, its structured output should remain a
Result Candidate or review aid. For a consequential unresolved choice, the
useful projection is:

```text
convergences
unresolved disagreements
uncertainties
acceptable compromises
kill criteria
missing evidence
        |
        v
existing Decision Request / User Decision Gate
        |
        v
human decision
```

Do not widen Decision semantics merely to store a Council transcript. Preserve
only fields that materially help the existing review owner; raw reasoning and
hidden chain-of-thought are not governance artifacts.

## Qualification plan

### Q-Council

Use 2–3 difficult cases where independent perspectives plausibly matter.

Compare:

```text
simpler qualified Hermes tactic
vs
same tactic + bounded Council method
```

Hold task, admitted context, model/provider envelope and review criteria
constant where technically possible.

Retain the method only if it produces a repeatable material gain in findings,
assumption detection, uncertainty handling or decision usefulness that
justifies its coordination cost.

### Q-Vet

Build a small deterministic corpus containing:

- benign external Skill/repository fixtures;
- known tripwire fixtures;
- split/cross-file or obfuscated cases expected to remain undetected;
- untrusted-content injection fixtures;
- explicit UNKNOWN/coverage-limit cases.

The qualification succeeds only if the scanner's result vocabulary cannot be
misread as admission, trust or safety proof.

## Explicitly rejected imports

Do not import:

- Council MCP/runtime as a Pantheon runtime;
- Agno/LangGraph Council orchestration;
- historical-persona agents as Pantheon Roles;
- provider/model routing from Council;
- weighted voting or uncalibrated confidence as decision authority;
- agent-security as a security authority or PEP;
- automatic install/admission after a clean scan;
- GitHub guard semantics as a replacement for repository governance;
- any scanner claim that CLEAN means safe.

## Convergence rule

Implement nothing new merely because the external repository has it.

```text
existing Pantheon owner fully covers mechanism
-> no change

existing owner partially covers mechanism
-> strengthen that owner/test

real procedural gap + measurable value
-> smallest Method/Skill or deterministic check

new runtime/authority required only to copy upstream
-> reject
```

## Status

```text
Council repository dependency          = not selected
Council runtime/MCP                    = rejected for Pantheon placement
Council bounded Method/Skill           = candidate, qualification required
agent-security repository dependency   = not selected
deterministic external pre-vet         = candidate, gap comparison required
effect PEP ownership                   = unchanged
Decision authority                     = unchanged
Evidence authority                     = unchanged
```
