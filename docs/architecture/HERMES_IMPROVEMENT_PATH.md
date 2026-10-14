# Hermes improvement path — evaluation first, training only on a proven model gap

Status: selected architectural direction / external optimization and training tooling remain candidate and unactivated.
Boundary profile: candidate_support_note.

Date: 2026-09-06

## Objective

Keep Hermes as the single external execution runtime and improve it at the cheapest, most reversible layer first.

The selected order is:

```text
observe Hermes behavior
        |
        v
measure against bounded evaluation cases
        |
        v
classify the failure
        |
        +--> skill / prompt / tool / context / retrieval / binding
        |        |
        |        `--> fix that layer, then re-evaluate
        |
        `--> residual model limitation proven
                 |
                 v
             LlamaFactory
                 |
                 `--> optional Unsloth acceleration when compatible
                 |
                 v
          trained artifact candidate
                 |
                 v
         separate model qualification
                 |
                 v
       existing serving path only
```

This document does not create an evaluation runtime, optimizer runtime, training service, provider router, model server, deployment, dataset authority or authorization path.

## Verified repository baseline

Observed before this rewrite:

```text
Pantheon main = 232e78b1e7b9114a3f6be2e7d40c412ca33209c1
PAIR + Unsloth qualification planning = merged through Pantheon-Next#970
Hermes improvement PR Pantheon-Next#976 = 36 commits behind main before reconciliation
```

Since Pantheon-Next#976 was first written, current `main` has added further bounded Hermes-facing surfaces, including explicit PDF qualification preparation and continued Context Admission/security work. Those existing contracts and labs are useful evaluation cases. They are not replaced by a new benchmark owner here.

## Existing owners reused

The selected path reuses current responsibilities:

```text
Pantheon                 -> governance, eligibility, scope, approval and Evidence boundaries
Hermes                   -> external agent/tool execution
existing tests/labs      -> bounded executable behavior checks
PAIR                     -> physical request routing qualification across local nodes
Ollama / LM Studio       -> local model serving candidates behind PAIR
LlamaFactory             -> candidate training facade only when weight tuning is justified
Unsloth                  -> optional acceleration inside the training path when compatible
```

No second agent runtime, scheduler, provider router, evaluation service or model-serving path is added.

## The durable owner is the improvement method, not Self-Evolution

The architectural primitive is the **Hermes evaluation / improvement loop**:

```text
observe -> measure -> classify -> change one layer -> compare -> review
```

`NousResearch/hermes-agent-self-evolution`, DSPy and GEPA are possible automation mechanisms for parts of that loop. They are not the loop itself and are not required dependencies.

### Current Self-Evolution observation

Observed upstream repository: `NousResearch/hermes-agent-self-evolution`.

Observed `main` head on 2026-09-06:

```text
0a929e3aa20e15cf04dc7c28492a7d41a5139125
```

No newer commit was observed after 2026-06-17.

Upstream issue Pantheon-Next#141 remains open. It reports that the skill-evolution path can improve optimizer state while the emitted `SKILL.md` remains byte-identical to the input. Therefore:

```text
Self-Evolution role = optional future automation candidate
Self-Evolution activation = unresolved / blocked pending independent qualification
Self-Evolution dependency = not selected
```

An optimizer score is never accepted as proof that the persisted skill improved.

## Evaluation comes before optimization tooling

Pantheon should first maintain a bounded set of Hermes behavior cases assembled from already-owned contracts and qualification surfaces rather than inventing a second testing framework.

Useful categories include:

```text
structured tool calling
scope isolation
refusal / approval boundaries
Context Admission and untrusted external content
PDF/document understanding qualification
provenance preservation
retrieval behavior
memory != Evidence boundaries
provider/binding fallback behavior
professional structured extraction where a deterministic contract exists
```

The evaluation set may aggregate references to existing fixtures/tests/labs and add small synthetic cases where gaps exist. It must not duplicate the implementation owner of those checks.

```text
evaluation case != Evidence
evaluation score != professional correctness
runtime trace != Evidence
benchmark corpus != training dataset
```

## Runtime coordination strategy is an evaluation dimension

Issue Pantheon-Next#1093 records a bounded improvement question raised from current Hermes native coordination surfaces: direct execution, `delegate_task`, goal-style iteration and Kanban/task-graph execution may have different quality, cost, latency and traceability characteristics for the same admitted task.

Pantheon should not pre-emptively convert those runtime tactics into a new governed execution-mode ontology.

```text
direct / delegation / goal / Kanban
= Hermes runtime tactics

separate profile/bot envelope
= exceptional runtime-boundary choice

runtime tactic
!= Task Contract
!= Execution Admission
!= authorization
!= Pantheon Role
!= Evidence status
```

The preferred hypothesis is the least-complex sufficient strategy:

```text
one bounded pass sufficient
-> direct

independent bounded subtasks materially help
-> delegation

the same bounded task needs attempt/check/revision
-> goal-style loop

durable dependent tasks, blockers or handoffs are material
-> Kanban

persistent specialization is materially useful
and a distinct runtime boundary is demonstrated
(model/provider exposure, memory/context injection, credentials, tool surface,
private-data exposure, execution isolation, or host/deployment trust)
-> profile/bot envelope

persistent specialization without a distinct runtime boundary
-> keep the governed default; prefer Method / Skill / bounded delegation
```

This is not a fixed routing table. It is a qualification hypothesis.

Execution-strategy choice never moves the consequential-effect boundary. Before
a governed admission that may request a consequential effect is launched, the
admitted tool/capability envelope must already exclude any raw provider route or
credential that would allow Hermes to bypass the effect-specific Pantheon owner.

```text
direct / delegation / goal / Kanban
!= consequential authority

raw consequential tool / credential
-> not exposed to Hermes

governed effect request
-> terminates at Pantheon-owned effect owner / PEP

pre_tool_call
-> optional second-line runtime guard
-> never the sole PEP
```

Hermes may choose how to perform admitted work. It may not choose a path around
the effect owner, enlarge the effect ceiling or convert runtime approval into a
Pantheon Decision. A missing or bypassed runtime guard is a runtime
qualification failure, not permission to expose the raw effect.

Reuse the existing Pantheon-Next#644 / Pantheon-Next#986 live campaign and, when useful, Pantheon-Next#827 professional workloads to compare materially plausible strategies under the same task, admitted context, model/runtime envelope, toolset and review criteria. Observe useful-result quality, misses, false positives, provenance retention, tool calls, cost/token signals when available, latency, stop/blocker behavior, unnecessary decomposition and trace/readback quality.

Decision rule:

```text
Hermes strategy choice is adequate
-> no Pantheon selector

failure belongs to prompt / skill / tool / context / runtime configuration
-> fix that existing owner

repeated residual failure remains after existing owners are corrected
-> justify the smallest explicit constraint in the nearest existing owner
```

Do not add by default an `ExecutionMode` object, Pantheon dispatcher, Pantheon Kanban engine, scheduler/queue, second admission path or Bot/Profile-to-Role mapping.

## Empirical execution-strategy qualification slices

Issue Pantheon-Next#1093 owns the empirical follow-up. The objective is not to benchmark every
Hermes coordination feature or build a second evaluation runtime. It is to qualify
the smallest useful execution tactic on representative Pantheon workloads,
reusing already-merged live surfaces.

Documentation integration baseline for this qualification owner:

```text
Pantheon main = 3cccdb29aac25efc3b9fad0e4512e600f4b1343f
Hermes selected = v0.21.3 / v2026.9.14
Hermes commit = 345cd2b057a452236de401d3534b8502a7465e8d

Pantheon-Next#1109 = consequential-effect boundary invariant
Pantheon-Next#1105 Runtime Lab = bounded /v1/runs observation + technical receipts
Pantheon-Next#986 / P2 = situated professional reasoning qualification
```

The documentation integration baseline is provenance for this qualification owner,
not a permanent experimental baseline. Each empirical run must record its own exact
Pantheon ref, Hermes release/commit, model/provider, admitted capability/tool
surface and controlled input/context identity.

This qualification inherits the consequential-effect boundary defined immediately
above. Every Q1/Q2/Q3 comparison must preserve the same admitted capability and
effect boundary; the execution tactic is the variable under test.

```text
strategy under test != authorization strategy
Q1 / Q2 / Q3 tactic change != consequential-effect boundary change
strategy success != permission to expose raw consequential credentials
```

Pantheon-Next#1105-style sentinel observations remain release/lab characterization only; they
do not qualify a deployed route guard or move the Pantheon-owned effect chokepoint.

The qualification is deliberately pairwise because these tactics do not all live
at the same runtime layer:

```text
Q1 — direct vs delegate_task
same admitted task, same model/runtime envelope, same sources and review criteria
-> determine whether bounded delegation produces material quality/coverage/latency gain

Q2 — direct vs goal-style iteration
same bounded artifact or analysis with an objective verification/correction criterion
-> determine whether additional turns improve the result before looping becomes waste

Q3 — goal-style workflow without vs with Kanban projection/persistence
same durable dependent-work scenario and same attempt/check/revision workflow
with at least one real blocker/recovery point in both arms
-> vary only Kanban projection/persisted task state, dependencies and handoffs
-> determine whether that additional durable coordination materially helps
```

Q1 is first because it is technically closest to the existing live Runs/P2 path.
Do not reproduce a generic Hermes delegation benchmark. Use a small set of
representative Pantheon cases and treat upstream/community observations only
as prior context, not as local qualification.

For comparable runs, hold constant wherever the runtime surface permits:

```text
Task Contract / admitted question
Context Pack / source set
model + provider + exact runtime identity
effective profile identity + projected Skill set
effective inference settings / model_options digest
(context length, reasoning level, routing and relevant compression settings)
tool surface except the tactic under test
output contract / review criteria
same initial mutable runtime state under experiment control
(runtime/external memory, writable workspace, task artifacts and resettable caches)
fresh admission + fresh session
```

Record the effective profile identity and non-secret settings digest for every arm,
following the existing native-baseline posture rather than relying on a profile
name alone. If the effective profile, projected Skills, model options or other
controlled inference settings differ between matched arms, the comparison is
inconclusive and must not be attributed to the execution tactic.

A fresh session is not by itself a clean initial state. Before every arm and
repetition, start experiment-controlled mutable stores from the same known state,
using existing isolation/reset mechanisms such as an ephemeral namespace,
disposable workspace or equivalent reset. Record the state identity/digest where
the runtime exposes one. Do not add a Pantheon snapshot owner for this purpose.

If equal initial mutable state cannot be demonstrated for the stores that can
carry information across sessions, classify the matched comparison as
inconclusive. Q3 keeps the same initial state between arms but may intentionally
exercise persistence inside the Kanban arm; that persistence is the treatment,
not a pre-existing difference.

Each representative case uses repeated matched trials. The default minimum is
three repetitions per tactic/arm with a fresh admission and fresh session for
every repetition, unless an existing qualification owner requires more.

Run the arms as time-local matched pairs rather than as one block per tactic.
Predeclare and record a randomized or counterbalanced arm order for each pair so
provider-load drift, warm caches, throttling or other time-correlated effects are
not systematically assigned to one tactic. With an odd number of pairs, first-arm
counts may differ by at most one.

Before execution, declare the outcome-independent runtime/provider drift signals
that can invalidate a pair and their threshold or boolean trigger. Such signals
must be provider-wide or runtime-wide observations measured independently of
either tactic arm, for example an external health/status signal or an independent
control probe that crosses its predeclared threshold.

Do not use an arm-local throttle, rate-limit, timeout, provider error, latency,
quality score or other event that may have been caused by the tactic itself as a
drift exclusion signal. Those events remain part of that tactic's observed
coordination cost/outcome. A pair may be replaced only when the predeclared
independent drift rule fires. Keep the excluded pair in the run record with its
signal, threshold/trigger and exclusion reason; append the replacement rather
than erasing the observation.

For the default repeated slice:

```text
quantitative signals (latency / tool calls / token-cost signals)
-> compare the median per arm and retain the per-run values

quality / provenance / blocker behavior
-> record each repetition; any critical-boundary regression fails that arm

claimed material tactic benefit inside one case
-> must recur in the same direction across a majority of matched repetitions
   and must not be contradicted by the aggregate signal

workload-class preference
-> independent representative case is the unit of generalization
-> with the default three predeclared cases, the same tactic benefit must hold
   in at least two cases and no case may introduce a critical-boundary regression
-> do not weight a case more heavily because it has more repetitions

split / tied independent cases
-> no workload-class preference; keep the simpler tactic as the default hypothesis

single run or isolated outlier
-> inconclusive; never a workload-class strategy rule
```

Declare both the within-case aggregation rule and the cross-case generalization
rule before matched runs start so neither decision rule is chosen after observing
results.

Where qualitative P2/professional review contributes to tactic selection, present
reviewable outputs under opaque run identifiers in randomized order and remove
tactic labels, arm order and coordination metadata that are not themselves part
of the review criterion. Reviewers must score the declared rubric without knowing
which tactic produced each artifact wherever the artifact permits that blinding.

If tactic identity is intrinsically visible and cannot be blinded, the subjective
rating remains a descriptive observation but cannot by itself establish a
workload-class tactic preference. In that case, the preference must be supported
by objective checks/signals under the predeclared rule, while critical provenance,
scope, blocker and authorization regressions remain disqualifying regardless of
blinding.

Q3 requires stricter variable isolation: both arms use the same goal-style
attempt/check/revision workflow and the same task/dependency scenario. The only
intended treatment difference is the Kanban projection/persistence surface and
the durable state/handoff behavior it provides. If iteration behavior also differs,
the Q3 comparison is inconclusive because more than one execution dimension moved.

Observe at minimum:

```text
material findings found
material findings missed
false or unsupported claims
provenance retention
explicit uncertainty / blocker behavior
latency
tool calls
token/cost signals when available
delegation / iteration / task count
duplicated or unnecessary coordination
```

A more complex tactic is not preferred merely because it succeeds. It must produce
a material benefit that justifies its coordination cost and must not degrade a
critical boundary such as provenance, scope, blocker handling or authorization.

```text
same useful result + more coordination
-> simpler tactic remains preferred

materially better result or materially lower latency
with preserved boundaries
-> more complex tactic may be justified for that workload class

one successful run
!= general strategy rule
```

The Runtime Lab may establish that a tactic was actually exercised and collect
technical observations. P2/#986 may establish bounded professional-result
observations. Neither receipt is Evidence or professional truth.

```text
runtime trace != Evidence
technical receipt != Evidence
P2 result candidate != professional validation
strategy observed != strategy preferred
benchmark result != authorization
```

After forced pairwise runs, only test automatic strategy choice where Hermes
actually owns that choice. Do not pretend that direct/delegation, session goal
control and durable Kanban dispatch are one interchangeable selector surface.

If Hermes already chooses the least-complex sufficient tactic adequately, add no
Pantheon selector. If repeated residual mis-selection remains, first fix the
nearest existing Hermes prompt/Skill/tool/runtime owner. Retain the cases that
exposed the failure as regression cases, but do not qualify the correction only
by re-running cases inspected during tuning.

Before selecting a correction, freeze a held-out set for the same workload class.
After the nearest-owner correction, require both regression success on the
original cases and the same direction of improvement on the untouched held-out
cases under the same matched-run controls. A correction that helps only the cases
used to choose it is case-specific tuning, not a workload-class strategy rule.

Only a repeated residual failure that survives this held-out validation after
existing-owner corrections can justify the smallest additional constraint.

## Failure classification gate

Before changing model weights, a failure must be classified against the layers that can already explain it:

1. Skill or instruction defect.
2. Prompt/system instruction defect.
3. Tool description or tool contract defect.
4. Context Admission/context-budget defect.
5. Retrieval/ranking/provenance defect.
6. Provider/binding/routing defect.
7. Residual model capability defect.

Weight tuning is downstream of items 1–6. A model must not be trained to compensate for a defect owned elsewhere.

## One training facade: LlamaFactory

Observed upstream repository: `hiyouga/LlamaFactory`.

Latest published stable release observed for this decision:

```text
v0.9.5
7af909522a951e3ad9f022ea6f88b6755257eaa5
```

Observed upstream `main` head on 2026-09-06:

```text
dced5f8804bfbf7109ef7c14401db6bd5cce7e53
```

LlamaFactory already exposes Unsloth as an optional LoRA optimization through `use_unsloth`. Pantheon therefore does not need two competing training workflows.

Selected placement:

```text
model adaptation / fine-tuning facade
        |
        v
   LlamaFactory
        |
        +--> standard supported training path
        |
        `--> use_unsloth: true
             when the selected model/method/runtime combination is compatible
```

LlamaFactory remains replaceable and candidate. Selecting it as the preferred qualification facade does not install or authorize it.

## Unsloth is an accelerator, not a second architecture

Merged Pantheon-Next#970 retains useful Unsloth compatibility observations and a bounded direct-provider experiment. Those observations are not discarded.

The selected role is narrower:

```text
Unsloth primary role = optional VRAM-efficient LoRA/training acceleration under LlamaFactory when supported
Unsloth independent training facade = not selected
Unsloth permanent serving role = not selected
```

A future qualification may still run Unsloth directly to understand performance or compatibility. That does not create a second production path.

```text
Unsloth provider compatible != Unsloth selected for serving
Unsloth acceleration enabled != trained model qualified
```

## Serving remains separate

The serving direction remains unchanged:

```text
Pantheon governs
      |
      v
Hermes executes
      |
      v
PAIR routes one request to an eligible node
      |
      v
Ollama / LM Studio serve
      |
      v
GPU nodes
```

PAIR routing does not pool VRAM, approve a model, authorize a task or admit Evidence.

## Operational priority

The immediate priority is not training.

The merged Pantheon-Next#970 runbook already defines the bounded physical-routing work. Execute that before investing in model adaptation:

```text
Q1A -> Linux RTX 4080 isolated PAIR + Ollama observation
Q1B -> Linux RTX 4080 + Windows RTX 4090 routing / failover / rejoin
Q1C -> current Hermes container -> local PAIR ingress compatibility
```

Only after the serving path has real observations should the evaluation inventory be used to establish a Hermes/model baseline.

## Weight-tuning admission gate

If evaluation leaves a repeated residual model limitation after the other layers are corrected, a LlamaFactory qualification may be prepared.

It must capture at least:

```text
base model identity + license
training facade version/ref
whether Unsloth acceleration is enabled
training configuration
source dataset manifest and scope
train / validation / held-out separation
adapter/checkpoint identity + hash
GPU/VRAM/RAM observations
reproducibility inputs
held-out quality and refusal/regression results
structured tool-call behavior after export
export format and artifact identity
```

Project/client material is **not training data by default**. Synthetic or explicitly scoped, minimized and authorized data is the default qualification posture.

## Model adoption remains separate

A successful training run produces a model/adapter candidate only.

```text
training completed != model qualified
model qualified != model activated
model activated != task authorized
benchmark gain != professional correctness
dataset != Evidence
runtime trace != Evidence
memory != Evidence
project data available != training authorized
export succeeded != deployment selected
```

Before serving, the trained artifact requires separate qualification for its intended Hermes workload, structured tool use, refusal regressions, context behavior, provenance, licensing and rollback.

## Next bounded slices

In order:

1. Execute the existing PAIR Q1A/Q1B/Q1C hardware observations from the merged Pantheon-Next#970 runbook.
2. Inventory existing Hermes/Pantheon tests and qualification cases into one evaluation reference set without moving their ownership.
3. Measure baseline behavior on the selected local models.
4. Correct skill/prompt/tool/context/retrieval/binding defects where measured.
5. Re-evaluate.
6. Only if a residual model defect is proven, prepare one LlamaFactory training qualification; enable Unsloth only as an optional accelerator when compatible.
7. Revisit Self-Evolution only after its upstream defect is resolved or independently bounded by a reproducible fix.

Magnitude remains outside the selected path.

## Boundary

This document selects responsibility placement and evaluation order. It claims no live runtime or training result.

```text
live PAIR observations = still required
Hermes evaluation reference set = to assemble from existing owners
Self-Evolution activation = unresolved / blocked
LlamaFactory activation = not_run
Unsloth acceleration = not_run
serving topology change = none
```
