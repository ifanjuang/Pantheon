# Hermes Integration Models — Reconciliation

Status: active support doctrine — integration boundary reconciliation.
Boundary profile: candidate_support_note.

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`: the Pantheon policy service is the bounded PDP interface, Hermes/the external runtime enforces consequential effects as PEP, optional compatible runtime clients expose runtime interaction only, Pantheon Cockpit projects governed state, and the human decides consequential effects when required.

Two Hermes-integration models now exist in the candidates. They are **layers,
not competitors**. This note fixes how they compose so neither is mistaken for
the other and neither bypasses the chokepoint.

## The two models

### 1. Effect-centred chokepoint (per effect, synchronous)

The layer that decides whether one specific consequential effect may happen.

```text
consequential effect
  → PEP normalises it to request + gate_signals; derives a PEP-owned
    decision_expectation (required_ceiling / scope / object_identity / expected_digest)
  → PDP preflight (eligibility, missing gates, V0 effect flags)
  → PDP validate_decision (scope, ceiling, expiry, object identity, digest,
    human signer, and — when configured — human issuer authentication)
  → executor runs the effect only behind an allow verdict; fail-closed otherwise
```

Implemented: `mcp-server` (`evaluate_preflight`, `validate_decision`),
`pantheon-mvp` `policy_gate` (`enforce_consequential`, `governed_effect`),
hardened by the Paperless intake PEP. Governed by `HERMES_INTEGRATION.md`
(the chokepoint) and `UNIFORM_CAPABILITY_GOVERNANCE.md`.

### 2. Work-Issue-centred execution admission bridge (per run, asynchronous)

The layer that decides whether Hermes may **start a bounded run** for a Work
Issue, and observes what comes back.

```text
handoff preview → human Work Issue → human bounded Execution Admission
  (requested_effect, exact Work Issue version, explicit ttl, expires_at)
  → admission_id
  → [optional append-only human revocation before consumption]
  → external delivery — outside Pantheon
  → Hermes pulls the exact envelope, starts itself, posts a start callback
  → Hermes posts a normalised return callback (result_candidate / partial / failed / capability_gap)
```

Documented: `HERMES_EXECUTION_ADMISSION_BRIDGE.md` (candidate), implemented in
`pantheon-mvp` Cockpit V2. Explicitly no queue, scheduler, dispatcher or
Cockpit-invoked runtime start.

## How they compose

```text
Execution Admission  = bounded permission to START a run
                       (which Work Issue, which version, for how long, at what effect class)
Chokepoint           = per-effect policy gate DURING the run
                       (is this specific consequential effect allowed?)
```

An admitted run is permission to begin work; it is **not** permission for any
consequential effect the run may attempt. Every such effect still routes through
the chokepoint. A `read_only` admission means the run may not attempt a
consequential effect at all, and the chokepoint enforces that structurally
(`external_effect_allowed = false`, `canonical_effect_allowed = false` under V0).

```text
admission granted            != effect authorized
admitted run                 -> still blocked at the chokepoint for any consequential effect
read_only admission          -> consequential effects refused; not merely discouraged
runtime-start callback       != a command to start (observation only)
Hermes returned              != Work Issue resolved
runtime return               != Evidence admitted
```

## Two distinct human decisions

The models carry two different human decisions; do not collapse them.

```text
Execution Admission        = a human admits a bounded run for a Work Issue (run-scoped)
Validated decision reference = a human authorises one specific consequential effect (effect-scoped)
```

The issuer authenticated at the chokepoint (when a key registry is configured)
and the human who granted an admission may be the same person or not; each is
recorded on its own object. Neither is an approval by itself.

## Shared invariants

```text
Pantheon governs; it does not queue, schedule, dispatch or route providers.
Hermes pulls, self-starts and executes; it enforces the chokepoint verdict.
No consequential effect reaches the world without passing the chokepoint.
An admission bounds a run; the chokepoint bounds each effect.
Human issuer authentication proves who decided, never that the effect is permitted.
```

## Open, shared across both models

```text
authenticated human issuer  -> now available at the chokepoint when an issuer key
                               registry is configured; the admission side does not
                               yet bind an authenticated issuer to the admission act
live Hermes delivery binding -> not implemented in either model
runtime cancellation after consumption -> not implemented
```

## Final rule

```text
Admission answers "may a bounded run start?".
The chokepoint answers "may this effect happen?".
Both remain candidates; the human decides; Pantheon never becomes the runtime.
```
