# Rite Trigger Catalogue

Status: candidate support doctrine — first deterministic attention signal
implemented in the bounded MCP request-handling projection; the wider catalogue
remains candidate / to verify.
Boundary profile: candidate_support_note.

Distilled from the external deterministic-metacognition pattern reviewed in
`../reference_reviews/SELF_INSPECT_MCP.md`, importing none of it.

This note owns the bounded `signal -> metathought question` catalogue. The first
served signal is a read-only policy projection only; it does not add a runtime,
classifier, scheduler, trigger engine, approval engine, Rite executor or
automatic memory promotion engine.

## Intent

The rites are excellent doctrine but they live as prose. This catalogue expresses
the *front edge* of the rites — the moment a methodological symptom may be
present — as a compact, deterministic `signal -> metathought question` table that
Pantheon owns and bounded external surfaces may serve.

A metathought is a question, never a verdict. It surfaces an assumption, a drift
or an over-confidence for governed attention. It does not answer, approve, block
or trigger.

```text
The catalogue asks.
ZEUS decides whether a rite follows.
The human decides what to do with the answer.
```

## Relationship to existing rite doctrine

This catalogue does not replace `RITE_SELECTION_MATRIX.md`; it sits one step
earlier and finer-grained.

```text
Signal      a detectable surface cue in the work
-> Question a metathought that redirects attention (mode_light)
-> Symptom  if confirmed, RITE_SELECTION_MATRIX maps it to a candidate rite
-> ZEUS     decides whether the rite is allowed (RITE_INVOCATION_POLICY)
```

All existing guardrails still hold: a signal suggests, it does not trigger; the
anti-chaining rule, the rite budget and the closure statuses are unchanged. A
surfaced question is `mode_light` by default and may resolve the tension without
any full rite at all.

## Catalogue shape (owned spec)

The catalogue is a flat, reviewable spec. Each row:

```text
signal_id
signal_cues          observable surface cues (deterministic, no LLM judgement)
metathought          the question to surface
attention_failure    the named failure it guards against
related_rite         the rite it may lead to, if confirmed
default_mode         mode_light unless escalated
escalation_note      when to consider a full rite or a User Decision Gate
```

A default question remains a catalogue candidate. The first implementation does
not emit a universal fallback when no signal matches.

## Starter catalogue

| signal | metathought (the question) | attention failure | related rite |
|---|---|---|---|
| Explicit completion requirement `tests_pass` (`tests_pass_completion`) | "What would passing these tests still not establish?" | `tests_pass_treated_as_claim_proven` | `AUTOCRITIQUE_CONTRADICTOIRE.md` |
| First framing reused unchanged across several steps | "Is this still the same problem, or did the first framing harden into an assumption?" | commitment to first interpretation | `PREMISSES_CACHEES.md` |
| A preference or constraint appears that the user never stated | "Which of these is stated, and which did I infer?" | invented user preference | `PREMISSES_CACHEES.md` |
| Scope grew without an explicit decision | "Did the cap change, or did scope drift under it?" | scope / goal drift | MÈTIS — `REQUEST_LIFECYCLE.md` |
| A draft reads as smooth and convincing | "If a third party wrote this, which claim would I challenge first?" | premature satisfaction | `AUTOCRITIQUE_CONTRADICTOIRE.md` |
| Confidence is high but sources were not compared | "Do the sources actually agree, and are they fresh?" | unwarranted confidence | `CONCORDANCE_DES_SOURCES.md` |
| Retrieved text is being treated as proof | "Is this retrieved, or is it evidence I can cite?" | retrieval mistaken for evidence | `CONCORDANCE_DES_SOURCES.md` |
| Many local corrections, worsening coherence | "Are these fixes improving the whole, or only the part?" | Hydre-like proliferation | `REFONDATION_DE_SESSION.md` |
| About to deliver something with external effect | "What is the one thing that, if wrong here, would matter most?" | premature delivery | `AUTOCRITIQUE_CONTRADICTOIRE.md` |
| (no signal matched) | "What am I assuming that I have not named?" | universal default candidate | — |

The cues column should be expressed as deterministic, observable patterns, not
as a model judgement, so selection stays explainable and driftable.

## Implemented first slice

The bounded MCP request-handling projection currently implements only
`tests_pass_completion`.

Observable input:

```yaml
completion_requirements:
  - tests_pass
```

Projected attention output:

```yaml
metathoughts:
  - signal_id: tests_pass_completion
    signal_source: completion_requirements:tests_pass
    question: What would passing these tests still not establish?
    attention_failure: tests_pass_treated_as_claim_proven
    related_rite: autocritique_contradictoire
    default_mode: mode_light
    effect: attention_only
```

This projection deliberately does **not** set a `rite_candidate` merely because
`tests_pass` is present. A later observed symptom, the existing Rite selection
policy and ZEUS remain responsible for deciding whether a Rite is appropriate.

```text
metathought emitted != symptom confirmed
symptom confirmed != Rite activated
Rite candidate != Rite authorized
Rite authorized != runtime delegated
runtime delegated != approval
```

The existing `AUTOCRITIQUE_CONTRADICTOIRE` Hermes delegation binding remains a
separate bounded execution candidate. This front edge does not call
`delegate_task` and does not infer a Hermes worker from a Rite or Role.

## Execution boundary

The current first slice follows these rules:

```text
1. This document remains the governance owner for the served question.
2. Selection is deterministic: exact completion criterion -> exact question.
3. Regression tests drift-check the served question against this owner.
4. The MCP request-handling surface returns attention data only.
5. It never approves, blocks, triggers a Rite, dispatches a Role, delegates a
   subagent or writes memory.
6. Other starter-catalogue rows remain documented candidates until separately
   qualified.
```

Acceptance for any further promotion:

```text
the catalogue surfaces a QUESTION only, never a verdict;
selection is deterministic and explainable;
no signal auto-triggers a rite or chains rites;
the rite budget, anti-chaining and ZEUS closure statuses still apply;
nothing here promotes memory or grants approval.
```

## Forbidden drift

```text
no automatic self-correction loop (self-learning is rejected)
no auto-triggered rite or rite chain from a signal
no LLM-judge selection presented as deterministic
no question turned into an approval, a block or proof
no catalogue treated as a Registre Probatoire entry
no scheduler, queue or trigger engine inside Pantheon
no Role identity inferred from a runtime worker
```

## Open questions

```text
Which additional signals are reliably detectable without a model judgement?
Should a machine-readable table be introduced only after a second implemented
signal proves that a separate data form reduces rather than duplicates doctrine?
Should the default question ever be served, or only explicit deterministic cues?
Which rite modes should future signals default to?
How should a confirmed symptom be represented without turning the front edge
into an automatic Rite selector?
```

## Current repo state

Implemented first slice only:

- `mcp-server/pantheon_mcp/request_handling.py` emits the bounded
  `tests_pass_completion` question from an explicit `tests_pass` completion
  requirement;
- `mcp-server/tests/test_rite_attention_projection.py` verifies positive,
  negative, coexistence and doctrine-drift cases;
- the signal has `attention_only` effect and does not create a `rite_candidate`;
- no general trigger engine, machine-readable catalogue, automatic Rite
  activation, subagent dispatch, persistence or memory effect is added;
- all other starter-catalogue signals remain documented non-implemented
  candidates.
