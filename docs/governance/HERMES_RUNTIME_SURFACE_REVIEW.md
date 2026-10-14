# Hermes Runtime Surface Review

Status: candidate external-runtime review and selected qualification target — not installed, observed, activated or task-authorized.
Boundary profile: external_reference_review.
Current reviewed target: Hermes Agent 0.21.3 (`v2026.9.14`).
Qualification status: live runtime qualification remains open.
Current upstream stable requalification candidate: Hermes Agent 0.21.5 (`v2026.9.24`).

## Responsibility

This document owns release-specific Hermes runtime facts that can affect Pantheon runtime qualification.

Stable runtime/governance boundaries remain owned by `HERMES_INTEGRATION.md`. Client selection and runtime-status posture remain owned by `WHAT_RUNS.md` / `EXTERNAL_TOOLS_POLICY.md`. Optional external bindings remain owned by `HERMES_CAPABILITY_BINDINGS.md`.

Do not duplicate those owners here. A new Hermes surface belongs here only when it changes what must be observed or refused before a concrete runtime can be qualified.

## Reviewed upstream artifact

Official upstream release and tagged source reviewed on 2026-09-15:

```text
repository: NousResearch/hermes-agent
version: 0.21.3
tag: v2026.9.14
release_date: 2026-09-14
release_commit: 345cd2b057a452236de401d3534b8502a7465e8d
```

The annotated release tag resolves to the exact commit above. The upstream release notes separately say the release window was measured at commit `9b419a2d3c2657c192008e732149d61170b32c01`; that measurement commit is not the tag target and is not the qualification pin. The 0.21.0 capability review below remains the base surface review; 0.21.3 is a patch target that retains that surface and materially repairs duplicate `state.db` writer-handle behavior, remote refresh handling and multi-profile isolation.

This review is a source/release qualification input only. It does not prove that any local Hermes installation runs this artifact.

## Existing Runs bridge compatibility

The exact 0.21.0 tagged API documentation still exposes the discovery and Runs surfaces used by the Pantheon candidate bridge:

```text
GET  /v1/capabilities
GET  /v1/toolsets
POST /v1/runs
GET  /v1/runs/{run_id}
GET  /v1/runs/{run_id}/events
POST /v1/runs/{run_id}/stop
POST /v1/runs/{run_id}/approval
```

0.21.0 keeps run submission, polling, SSE events and stop semantics. It additionally documents durable idempotency keys for run creation, optional session/transcript reuse, subagent lifecycle events, and runtime-side approval continuation.

These additions do not require a new Pantheon run binding. The current binding supplies the freshly generated Pantheon Execution Admission identity as the Runs `session_id` because Hermes maps that value to the host `task_id` consumed by the existing Context Bridge. Pantheon uses that value as one-shot host correlation, not as permission to continue an earlier Hermes conversation. The admission can acquire only one immutable launch reservation; an exact reservation replay is marked as such and the external binding refuses a second Hermes submission.

```text
run_binding_change_required: false
session_correlation: fresh_one_shot_execution_admission
session_correlation_reuse: forbidden
```

Wire compatibility still requires observation against the exact installed artifact.

## Upstream stable requalification candidate — 0.21.5

Official upstream release/tag rechecked on 2026-09-26:

```text
repository: NousResearch/hermes-agent
version: 0.21.5
tag: v2026.9.24
release_date: 2026-09-24
release_commit: f97608f178d1ffeca59860195ab7da295f7c8e5f
release_window: ~460 merged PRs since v0.21.4
```

0.21.5 is the next stable **requalification candidate**. It does not silently
replace the currently reviewed/selected Pantheon target or prove either release live-qualified. Pin movement remains:

```text
stable upstream artifact
-> exact runtime qualification (Pantheon-Next#644 / H5.9b)
-> Pantheon acceptance
-> only then update the selected deployment pin
```

The release window makes several previously observed `main` behaviors stable,
including connector/webhook delivery mirrored into chat state, broader Connector
surfaces and plugin tools/skills becoming live in already-open chats. Post-release
upstream fixes additionally show concrete isolation failures around Profile-owned
interactive authorization, secret prompting, disabled-toolset fold-in,
workspace/cwd switching and delegate-session restoration. Those post-tag fixes
are observations for the next stable or an explicit target-local qualification;
they are not a reason to track upstream `main` implicitly.

No new Pantheon runtime or governance abstraction follows. Requalification must
preserve six existing boundaries regardless of Hermes implementation details:

```text
Hermes Profile A != Hermes Profile B
parent session != delegated child session
connector/webhook transcript input != Pantheon admitted input
Hermes-visible tool != Pantheon admitted Capability / Binding
Hermes runtime approval != Pantheon consequential-effect authorization
Hermes/Hindsight memory or transcript != Evidence
```

Qualification interpretation:

- Profile isolation must cover effective home, secrets, authorization context,
  workspace/cwd, tool surface and session restoration, not only the Profile name;
- a delegated child may return a Result Candidate but must not become the resumed
  interactive owner or acquire a new Pantheon identity/authority;
- transcript role, including `user`, is runtime state and never proves that the
  content crossed Pantheon Context/Execution Admission;
- dynamic MCP/plugin registration or tool availability may not widen the exact
  admitted capability/tool envelope for an already admitted run;
- Hermes approvals and hooks remain defense in depth under the effect boundary
  fixed by Pantheon-Next#1109;
- retained/recalled runtime material remains memory/context. Promotion to Evidence
  still requires the existing Pantheon Evidence path.

Owner routing remains deliberately unchanged:

```text
Pantheon-Next#644 / H5.9b -> exact Hermes runtime/Profile/context/tool requalification
Pantheon-Next#1093        -> direct/delegate/goal/Kanban empirical strategy qualification
Pantheon-Next#1109        -> consequential-effect authority invariant (merged doctrine)
Pantheon-Next#660/#1129   -> AFFAIRES source/index/Hindsight producer topology
```

For AFFAIRES specifically, the direct NAS topology now strengthens the source
boundary rather than changing Hermes ownership:

```text
NAS / AFFAIRES source
-> Workspace observes/indexes
-> Pantheon explicitly admits bounded source/context
-> Hermes may consume only that admitted material

NAS mounted/readable != Hermes globally admitted browsing surface
Hindsight retained material != professional source != Evidence
```

## Native primary-model fallback in selected 0.21.3

The exact selected 0.21.3 source already contains a first-class primary fallback chain. Its documented top-level `fallback_providers` configuration can switch to another provider/model pair after qualifying provider failures, supports custom OpenAI-compatible endpoints and applies to messaging gateway sessions as well as CLI sessions.

This corrects an older local observation that described the deployed 9B configuration as lacking a *configured* inter-model fallback. The observation remains valid for that host state; it is not evidence that the selected Hermes release lacks the mechanism.

For the agency local target, the smallest owner-preserving availability experiment is therefore:

```text
Hermes primary   -> qwen3.5:27b
Hermes fallback  -> qwen3.5:9b
PAIR             -> eligible-node routing for the model Hermes requested
Pantheon         -> observes runtime identity / preserves admission and effect boundaries
```

Pantheon must not add a provider router or inference scheduler for this need. Pantheon-Next#644 owns the real-runtime qualification: exact requested/served model, a deliberate/observed 27B failure that reaches 9B, a bounded failure when the fallback is unavailable, and confirmation that the switch does not widen source, credential, memory or consequential-effect authority.

```text
PAIR node selection != inter-model fallback
fallback success != result validity
fallback success != authorization
served model != Evidence
```

The operational target and live acceptance checklist are recorded in `docs/install/HERMES_MODEL_AVAILABILITY_TARGET.md`.

## Material 0.21.x qualification deltas

Only deltas that change trust, state, tool, execution-host or administration boundaries are retained here.


### 0.21.3 plugin control surface — exact pinned-source review

The selected release commit `345cd2b057a452236de401d3534b8502a7465e8d`
contains the plugin hooks `pre_llm_call`, `pre_tool_call`, `post_tool_call`,
`subagent_start` / `subagent_stop` and the Kanban lifecycle observers used by
the current improvement discussion. It also contains the separate
`tool_request` and `tool_execution` middleware surfaces.

The selected implementation gives `pre_tool_call` a deliberately mixed failure
contract:

- a timeout, still-running callback or callback worker-start failure is converted
  into a blocking directive;
- an ordinary callback exception is logged and skipped;
- the managed tool executor also catches a failure of the pre-tool dispatch path
  and continues with the original arguments.

Therefore the source proves a timeout-oriented fail-closed behavior, not a
Pantheon-owned universal fail-closed effect boundary.

The exact tool middleware order also matters. `tool_request` runs before the
normal Hermes policy path. `tool_execution` wraps the callback that enters that
path, so execution middleware may short-circuit without calling `next_call`.
A `pre_tool_call` hook is consequently a runtime defense-in-depth seam whose
presence and invocation must be observed on the deployed route; it is not by
itself proof that every possible effect traverses Pantheon's PEP.

The boundary it defends is explicit: it may reject an illegitimate
governed-effect request while that request is still inside the admitted Hermes
runtime/tool surface. The authoritative consequential-effect chokepoint remains
the separate Pantheon-owned effect owner / PEP described by
`HERMES_EXECUTION_ADMISSION_BRIDGE.md` and `HERMES_INTEGRATION.md`.

```text
pre_tool_call
-> secondary guard on the Hermes-side effect-request path

effect chokepoint
-> non-bypassable Pantheon-owned path to the exact consequential operation

secondary guard failure
!= chokepoint failure
!= raw consequential credential exposed
```

This document owns the release-specific guard semantics and qualification. It
does not redefine the effect chokepoint.

The `approve` directive is Hermes runtime approval. It invokes Hermes'
approval gate and may use a `rule_key` whose runtime UX supports persistent
`always` allowance. Pantheon must not use that mechanism to manufacture or
replace a canonical Pantheon Decision.

`pre_llm_call` exists as an ephemeral current-turn context injection seam. Its
availability does not justify moving Context Pack admission into Hermes; any
future use remains transport of already-admitted context only.

Qualification consequences:

```text
pre_tool_call observed != Pantheon PEP
pre_tool_call timeout fail-closed != universal hook failure fail-closed
runtime approval != Pantheon Decision
runtime always-allow != governed approval ceiling
tool middleware present != every effect traverses pre_tool_call
hook available != hook active on deployed route
```

A consequential-effect binding must therefore retain the existing Pantheon
effect owner / PDP / PEP path and independently prove its deployed runtime guard
when that guard is claimed. Loss of a required runtime guard must fail the
qualification of that consequential binding; it must not silently downgrade an
already admitted consequential task into another authorization mode. A separate
read-only or propose-only admission may still be created through its normal
governed path.

This source review does not activate any hook, install any plugin, expose any
consequential tool or qualify a local runtime.

A candidate ephemeral laboratory characterization now reuses the existing pinned-runtime
GitHub acceptance harness. It installs a lab-only synthetic effect sentinel
outside the Pantheon distribution and exercises it through the same Hermes
`/v1/runs` surface. The characterization requires both observations:

```text
pre_tool_call returns block -> synthetic effect sink remains untouched
pre_tool_call callback raises -> synthetic effect sink is touched
```

The second observation is intentionally a characterization of the selected
Hermes fail-open exception path, not a desired safety property. The sentinel
receipt explicitly records that it does not qualify Pantheon's PEP, authorize
production use or create Evidence. Passing the ephemeral laboratory characterization still
does not prove the behavior of a NAS/production target; a claimed consequential
runtime guard must be repeated against that exact deployed route.

Permanent citation ceiling:

```text
Pantheon-Next#1105 pass != deployed route guard qualified
same Hermes source commit != same deployed route behavior
ephemeral lab route != NAS / production route
```

Pantheon-Next#1105 and its generated receipts may be cited only as characterization of the
pinned Hermes release in the ephemeral GitHub lab. They must not satisfy a
target-installation, NAS, production, profile-route or consequential-guard
acceptance field. A deployed-route guard claim requires a fresh receipt bound to
the exact installed artifact identity/digest, named profile route, observed tool
surface and observation time.

### 0.21.3 state and remote-session patch

Upstream 0.21.3 removes duplicate long-lived writer handles to `state.db`, makes read-only
opens avoid unnecessary write locks, degrades damaged FTS independently from
the transcript store and hardens profile-specific database and credential
isolation. These changes directly address the warning and fragility class seen
with multiple live `SessionDB` handles; they do not justify patching the
provider or bypassing live acceptance.

Qualification consequence: select the tagged 0.21.3 artifact, keep one shared
long-lived handle per state path where the runtime supports it, verify the exact
multi-profile/database behavior on the installed artifact and retain the same
Pantheon memory, tool and authorization boundaries.

### Bot Mode and durable Bot Chats

0.21.0 ships named agent profiles, shared rosters, group chats and durable Bot Chats. These are Hermes runtime interaction and continuity surfaces, not Pantheon governed identities, dossiers, Registers or Evidence stores.

Qualification consequence: no Pantheon Bot registry or multi-agent runtime is added. Any future use must preserve:

```text
Bot identity != governed identity
Bot Chat != dossier
Bot Chat != Register
```

### `hermes peer`

0.21.0 adds direct agent-to-agent messaging across profiles/gateways with replies retained in canonical Bot Chats.

Qualification consequence: peer transport may be used by Hermes internally only after its concrete profile/tool exposure is observed. A peer message does not create a Pantheon Task Contract, governed delegation, approval or Evidence.

### Cron memory, continuity and notepads

0.21.0 adds persistent cron memory, `continuity=true`, durable job notepads and delivery into Bot Chats.

Qualification consequence: the governed runtime mode keeps memory/profile injection, the memory tool and session memory scope off. Runtime cron memory or continuity must not be promoted to Pantheon memory, Evidence or provenance by implication. Cron/jobs remain outside the admitted task path unless separately qualified.

### Subagent steering and structured output

0.21.0 adds live child listing/steering/stop, partial-result handling, JSON-schema validation and per-delegation cost reporting. Runs SSE can expose `subagent.start` and `subagent.complete` lifecycle observations.

Qualification consequence: these are execution/runtime mechanics. Structured-output validity does not prove a claim true; a child result does not become Evidence; steering a child is not a Pantheon decision. Existing run observation may record bounded child lifecycle facts without adding a Pantheon subagent owner.

### MCP command center

0.21.0 expands MCP inventory, health, import/install and usage/cost management surfaces.

Qualification consequence: catalogue/discovery/installability does not widen the admitted tool envelope. The exact enabled toolset remains the qualification boundary.

### Browser control

0.21.0 extends direct control of the Desktop browser. Tagged API docs also retain authenticated browser-extension control with explicit registration, exact controller/profile matching and fail-closed routing.

Qualification consequence: real-profile / extension / Desktop-browser control remains disabled for `pantheon-governed` unless separately qualified. Browser capability availability does not authorize a browser action or its consequence.

### Protected runtime writes and runtime approval

0.21.0 hardens writes to protected agent instruction, skill and memory files behind Hermes write approval and retains `POST /v1/runs/{run_id}/approval`.

Qualification consequence: Hermes approval is a runtime PEP mechanism only. It does not create Pantheon approval, Evidence or governed write authorization. No automatic bridge from runtime approval state into Pantheon decision state is authorized.

### Verify subsystem

0.21.0 adds run-recipe detection and environment-manifest support for technical verification workflows.

Qualification consequence: a successful build/test recipe is a technical execution observation. It may support later Evidence admission only through the existing Pantheon Evidence path; it is not Evidence or authorization by itself.

### Per-request routing and runtime session state

Tagged API docs continue to accept `model`, `provider` and `model_options` on `/v1/runs`. The exact 0.21.0 Runs handler also loads an existing Hermes session transcript when a `session_id` is supplied and neither an effective explicit history nor a `previous_response_id` supplies the conversation context. An empty `conversation_history` array is not a stateless override in this release because the handler still reaches the session-history fallback when the resulting history is empty.

The current Pantheon binding deliberately supplies `session_id = admission_id` because that is how the reviewed Hermes Runs path gives the Context Bridge its host `task_id`. The safety property is therefore not absence of the `session_id` field. It is that the identifier is a freshly generated Execution Admission identity, the Pantheon launch path is one-shot, a reservation replay cannot reach a second Hermes submission, and no prior-conversation continuation input is intentionally supplied.

```text
session_id purpose: host task correlation
session_id source: fresh Execution Admission identity
second Pantheon launch for same admission: forbidden
previous_response_id: omitted
X-Hermes-Session-Key: absent
runtime transcript reuse: forbidden
```

Pantheon-side freshness does not by itself prove the absence of arbitrary pre-existing state in an external Hermes installation. Exact target acceptance must therefore treat any observed prior transcript under the fresh synthetic admission identity as a qualification failure or unresolved runtime-state finding rather than silently accepting it as context.

Qualification consequence: the Pantheon candidate binding continues to omit provider/model overrides and must not opt into runtime transcript reuse or long-term session memory unless a separately qualified binding/profile explicitly requires it.

## Governed runtime-profile posture

The existing `pantheon-governed` posture remains the target for a Pantheon-admitted Hermes run. This is deployment configuration, not a new Pantheon identity or authority object.

```text
profile: pantheon-governed
external_memory_provider: off
built_in_memory_injection: off
built_in_user_profile_injection: off
memory_tool: off
session_memory_key: forbidden
runtime_transcript_reuse: forbidden unless separately qualified
provider_and_model_override_in_run_payload: omitted
allowed_tools: exact reviewed runtime-profile/binding envelope
skill_manage: outside admitted tool surface
peer_transport: outside admitted tool surface unless separately qualified
cron_jobs: outside governed task path unless separately qualified
real_browser_profile: disabled unless separately qualified
browser_extension_control: disabled unless separately qualified
desktop_browser_control: disabled unless separately qualified
remote_admin_update_surface: outside governed task path
terminal_environment_backend: exact observed backend required
consequential_effects: existing Pantheon policy / human gates apply
```

The existing runtime observer already records route/tool/memory posture in the candidate distribution composition. 0.21.3 does not justify a second observer, a Pantheon multi-agent runtime, a second scheduler, a second memory owner or a parallel runtime inventory path. Any missing live observation should extend an existing seam only after a concrete target proves the gap.

The earlier 0.20.6 review of Hermes automatic memory/skill background review remains a useful historical finding, but 0.21.0 changes the wider memory/continuity surface enough that its exact trigger mechanics must be re-observed before any governed profile enables `memory`, `skill_manage` or runtime learning. The current profile admits none of them, so no authority expansion is required for this target selection.

## Adjacent ownership

This release review does not reclassify external products or clients.

Use existing owners instead:

```text
runtime/client selection and current status -> WHAT_RUNS.md / EXTERNAL_TOOLS_POLICY.md
optional capability bindings               -> HERMES_CAPABILITY_BINDINGS.md
stable Hermes/Pantheon authority boundary  -> HERMES_INTEGRATION.md
technical execution receipt                -> HERMES_EXECUTION_TRACE_SUMMARY.md
```

A mobile, browser, desktop, Bot, peer, cron or messaging client may therefore evolve without requiring a new Pantheon architecture document unless it introduces a genuinely new governed consequence.

## Current repository decision

The reviewed release and candidate distribution target are aligned on 0.21.3:

```text
reviewed upstream release: 0.21.3
current candidate distribution runtime target: 0.21.3
```

The canonical external qualification pin and candidate distribution lock select Hermes 0.21.3 at the annotated release-tag commit `345cd2b057a452236de401d3534b8502a7465e8d`. This is a target-selection decision only. The candidate distribution remains default-off / not observed / not activated / not task-authorized, and its runtime artifact digest remains unset until a concrete installed artifact is observed.

```text
reviewed_runtime_target: 0.21.3
candidate_distribution_runtime_target: 0.21.3
kernel_change_required: false
run_binding_change_required: false
new_runtime_owner_required: false
new_client_owner_required: false
new_memory_owner_required: false
new_scheduler_owner_required: false
candidate_distribution_pin_change_authorized: true
target_selection_effect: candidate-only
real_instance_observation_required: true
runtime_artifact_digest_required_before_observed: true
composed_acceptance_required_before_qualified: true
installation_effect: none
activation_effect: none
task_authorization_effect: none
```

Selecting 0.21.3 as the candidate target does not qualify it. Qualification requires the exact observed 0.21.3 artifact and the checks below.

## Required live checks before qualifying 0.21.3 for the governed distribution

1. record the exact installed Hermes package/image identity and immutable digest;
2. observe the named profile route and `/v1/capabilities` / `/v1/toolsets` from that exact runtime;
3. verify active tools remain within the reviewed profile/binding envelope, including MCP, `memory`, `skill_manage`, peer and browser surfaces;
4. record the existing read-only memory-posture observation and prove memory/profile injection and the memory tool remain disabled for `pantheon-governed`;
5. verify no `X-Hermes-Session-Key`, `previous_response_id` or equivalent continuity input is supplied by the governed run client; verify that its sole Runs `session_id` is the fresh current Execution Admission identity used for host task correlation, that Pantheon has not previously launched that admission, and that a replayed reservation cannot reach another `POST /v1/runs`; any observed pre-existing Hermes transcript under that fresh synthetic identity is a qualification failure or unresolved target-state finding;
6. verify the Pantheon run payload contains no `model`, `provider` or `model_options` override;
7. record the exact terminal environment backend and its effective host/mount/network boundary;
8. confirm real-browser-profile, browser-extension-control and Desktop-browser-control paths are disabled, or run a separate explicit qualification before allowing any of them;
9. confirm remote Desktop/fleet/SSH update administration is not part of the admitted run path and cannot silently mutate the qualified runtime during acceptance;
10. execute one admitted read-only run through the existing launch/reconciliation path and exercise the existing real-runtime ambiguity/failure case;
11. observe 0.21.3 run idempotency/replay behavior and confirm a replayed runtime run is not treated as fresh Pantheon authorization;
12. if subagent lifecycle events are emitted, retain them as technical observations only and confirm they create no Evidence, decision or governed child identity by implication;
13. verify the runtime approval API and protected-file write approvals produce no Pantheon approval/write authorization state by implication;
14. if Bot/peer surfaces are enabled in the runtime installation, prove they remain outside the admitted governed tool envelope unless separately qualified;
15. if gateway/messaging/cron/continuity is selected in the deployment, exercise restart, persistence, code-skew and recovery behavior separately and retain outcomes as runtime observations only;
16. if Verify is exercised, retain detected recipes/manifests/results as technical execution material until separately admitted through Pantheon Evidence rules.

No new schema, observer or runtime owner is required by this target selection. A new protected-path invariant is justified only if live 0.21.3 acceptance exposes something the existing observer, binding or tests cannot represent.

## Local non-equivalences

The generic repository non-equivalences remain owned by `NON_EQUIVALENCE_RULES.md`. This review adds only release-sensitive distinctions needed here:

```text
release reviewed != distribution pin changed
candidate pin selected != runtime observed
candidate pin selected != runtime qualified
release reviewed != release installed
Bot identity != governed identity
Bot Chat != dossier
peer message != governed delegation
cron memory != Pantheon memory
continuity != governed provenance
runtime memory != Evidence
subagent result != Evidence
subagent steering != Pantheon decision
JSON schema valid != claim true
Verify success != Evidence
runtime approval endpoint != Pantheon approval
runtime write approval != Pantheon write authorization
MCP discovered != MCP admitted
tool admitted != effect authorized
browser available != browser action authorized
runtime replay != fresh task authorization
runtime success != Evidence
runtime success != authorization
remote admin available != update authorized
terminal backend selected != host boundary qualified
session correlation != transcript reuse
Pantheon admission freshness != proof of empty external session state
```