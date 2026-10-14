"""Make the consequential-mutation surface enumerable instead of assumed.

`CLAUDE.md` states the invariant in the present tense:

```text
A consequential effect still routes through the governance check (the
chokepoint). No module or implementation path bypasses it.
```

Nothing verified that. `policy_gate.enforce_consequential` was imported by two
modules, so an import-graph audit reported the module as reachable and healthy,
while the parameter that triggers the call (`policy_client`) had no non-test
caller and `HttpPolicyClient` was never instantiated outside tests. Each mutation
entry point defends itself with its own local checks — signed previews,
confirmation phrases, optimistic concurrency, idempotency keys, admission state
machines — and no two of them share a guard.

That paragraph was true when it was written on 2026-08-31 and stopped being true
the next day. `4d3e99c3` wired `HttpPolicyClient` into `cockpit_shell.create_app`
from `MVP_POLICY_API_URL` / `MVP_POLICY_API_KEY`, behind a
`require_policy_client` dependency that answers 503 when enforcement is
`required` and no decision point is configured — so the Knowledge update route
fails closed, and disabling the gate is an explicitly declared value rather than
a default. `human_access.bind_oidc_identity` was wired second, on the same
arrangement.

The sentence that motivates this entire document went stale within a day, and
three passes over the entries did not catch it, because every one of them was
reading entry points and none was reading this. A record rots at its premises as
readily as at its rows.

Local defence is not the problem. The problem is that a new entry point can be
added tomorrow inheriting none of it, with no check noticing.

## Where the review stands

All ninety-two entry points have been read individually. The first batches were
chosen because nothing in production reached them — answerable without unwinding
a call graph, and the cheapest end of the backlog rather than the most urgent
one. From `knowledge.py` onward every entry point is live: each sits behind a
route a key holder can call today.

One is not: `cli.main` opens its own connection and asks for no key at all.
Recorded there, because "the write surface is behind an API key" is a true
statement about the routes and a false one about the system.

No entry point is recorded as `gate_required_not_wired` any longer. All five
that once carried that regime are now either wired or closed by a local fix
that made the chokepoint the wrong tool for the specific finding.

`bind_oidc_identity`, `store_reviewed_dossier`, `publish_knowledge`,
`apply_edit_request` and `act_working_information` are wired.
`complete_edit_request` — recorded alongside `apply_edit_request` because
both write the same `status` column with nothing to decide it — was closed
by a local status guard instead: it fixes the specific finding (a rejected
request could be silently returned to `proposed`), not a missing decision
point, and needed no chokepoint call.

Two of the five wired entries share the same shape once read in order to
wire them: neither `bind_oidc_identity` nor `store_reviewed_dossier` had a
production caller at all. `bind_oidc_identity` left `human_oidc_bindings` —
the table every authenticated request resolves against — reachable only from
outside the product; `store_reviewed_dossier`
left a Project's whole Architecture Project Understanding baseline the same
way. Wiring `store_reviewed_dossier` did not have to invent a content binding:
`_normalize_dossier` already folds `review_ref` into the same structure as the
dossier it accompanies before the existing idempotency digest is computed, so
the decision expectation reuses that digest — covering this exact `review_ref`
bundled with this exact dossier, though still not verifying `review_ref`
names a review that actually happened.

`act_working_information` was the opposite shape: a live route, correctly
guarded on everything the module itself could check, that discarded the one
thing it could not check locally — who the caller was. The route already
resolved a real identity from `X-Pantheon-Actor` and dropped it as `_actor`;
it now threads through and becomes the decision's `decided_by`. The table
still has no actor column; the decision record is where that identity lives
now, not the row.

## The first write of a projection was not serialised, and now is

Recorded because all three `information_projection` entries share it, and
because the first version of those records named the row lock and
`expected_revision` as effective guards without qualification.

`_metadata_row(..., lock=True)` runs `SELECT ... FOR UPDATE` and, when no
projection-metadata row exists yet, returns a synthetic dictionary carrying
`revision: 0`. `FOR UPDATE` locks rows, not keys: a row that does not exist
cannot be locked. So two concurrent first mutations both read revision 0, both
pass the `expected_revision` check, and both compute `resulting_revision = 1`.

For `update_projection_metadata` that is a lost update — the second
`ON CONFLICT DO UPDATE` overwrites every field the first wrote. For the link
paths the metadata survives, but the event log gains two events both declaring
`0 -> 1`, describing a linear history that did not happen.

The pattern is used correctly everywhere else: eleven other modules raise a
not-found error when the locked row is missing. This is the one place where the
row is optional by design, and the optional case is where the token is invented.

Closed in 552e67e7, with the repair this section proposed:
`_advance_metadata_revision` carries the expected revision into the upsert's
conflict clause and requires `rowcount == 1`. On a genuine first write exactly
one racer's INSERT succeeds; the loser conflicts, its guarded UPDATE matches
nothing, and it fails as stale instead of overwriting.

The section is kept rather than deleted. The three entries were cleared on a
lock that was not taken, and a reader of this inventory is entitled to know that
happened and how it was found.

They were then wrong in the other direction: after 552e67e7 the three entries
went on describing the race as live, and the guard lists were refreshed while the
explanations beside them were not. A record can rot toward either verdict, and
only the entry's own text says which reading is current.

## Where the actor label is strongest, and what that still is not

Six modules record an actor nobody verified. `entity_relations` is where this
codebase pushes hardest against that, and reading it clarifies the whole axis.

```text
agency_classification   _validate_actor, defaulted        a caller omits it and passes
agency_information      actor_kind literal at the route   body-proof, module still trusts it
execution_results       trigger: claim needs a human      a second Python caller cannot pass
entity_relations        CHECK: only a proposal may be     no row can say Hermes canonized
                        attributed to a non-human
```

The last is the strongest form available, and it is worth being exact about
what it buys. None of these verifies that the label is true: a caller
presenting `human` passes every one of them. What the constraint guarantees is
that the audit trail can never hold the contradiction — no stored row can say
Hermes canonized a relation.

That is internal consistency of the record. It is real, it is rare, and it is
not the same as knowing who acted. `canonize_relation`'s docstring says "Hermes
cannot reach this"; what holds is "no record can say Hermes reached this".

## The net was under-counting, and it under-counted the worst cases

The tenth batch found this by accident, reading `work_issues.py`:
`transition_issue` was not in this inventory at all. Nor were twelve others.

Discovery saw a public function only if its name began with one of five verbs
or its own body contained a literal SQL write. Neither signal sees a public
function that delegates its write to a private helper in the same module —
which is a normal way to write this codebase, and is how the following are
written:

```text
work_issues.transition_issue          the only general status move
work_issues.close_issue               the only path to done
entity_relations.canonize_relation    canonization, by name
entity_relations.reject_relation      entity_relations.retire_relation
source_intake.exclude_source          restore_source, link_project,
                                      unlink_project, update_metadata,
                                      suggest_projects
hermes_runtime_return.record_external_runtime_return
apu_cross_family.create_decision_request
```

Thirteen entry points, and the miss was not random: it fell on functions whose
names are verbs of consequence. A third signal now catches them: discovery follows calls, so a public function
counts if a write is reachable from it through any chain of named functions,
across modules included.

That signal was itself wrong twice before it was right, which is worth keeping.
The first version intersected each function's calls with *private* helpers in
its own module, and still missed `create_scoped_issue` — the entry point of
`POST /work/issues`, which delegates to two *public* functions in another
module. The second version walked whole subtrees and caught every
`install_*_routes` and `create_app` in the package, because those *define*
route handlers that call writers rather than calling writers themselves:
eighteen wiring functions, the opposite failure and just as useless. The net
that holds counts a function's own calls, nested definitions excluded, and
follows them to a fixpoint.

Worth being precise about how this instrument failed, because it is the same
failure it exists to find. Two tests guarded discovery: one asserts every
discovered entry point is declared, the other that discovery is not vacuous.
Both passed throughout. Neither could fail for something the net never saw.
**The control verified its output and never its coverage.**

## What happened to this record the day after it was written

Five of the findings above were repaired within a day — `revoke_grant`,
`record_claim`, `resolve_request`, `suggest_projects` and the Information
projection race. **None of the repairs touched this file**, so for a day the
inventory recorded three gates that were closed and two defects that were fixed,
while every test here passed.

They passed because they check that each entry point is declared and never that
the declaration is still true. That is the failure this inventory exists to
record, committed by the inventory: a record describing a state the code has
left.

`test_a_pending_gate_still_points_at_the_code_that_needs_it` is the repair, and
it is deliberately the pattern this review recommended everywhere else — the one
`apu_write_preparation.append_authorization` already uses. Each pending gate
names a literal fragment of the code that makes it pending, and the test asks
for the verdict back when that fragment goes. A verdict bound to a content, not
to a name.

## Attribution is a separate axis from authorization

Four modules now show the same split, and it is not the gate's to fix. The
authorization is verified — a key comparison, a principal lookup, a dependency
that cannot be reached from a request body. The attribution is not.

```text
agency_classification     X-Pantheon-Human-Actor   asserted, persisted as updated_by
agency_information        X-Pantheon-Actor         asserted, required, then discarded
knowledge                 created_by               a body field, persisted verbatim
knowledge_edit_variants   X-Pantheon-Human-Actor   asserted, persisted; kind is a literal
decision_requests         X-Pantheon-Human-Actor   asserted — and so is its assurance level
information_projection    X-Pantheon-Actor         asserted, persisted into the event log
hermes_execution          X-Pantheon-Human-Actor   asserted — but the key decides the side
```

The last line is the one exception found so far, and it is an exception of
authorization rather than attribution. Admission and revocation take the editor
key with a human actor; launch reservation, runtime start and result return take
the Hermes key with a Hermes actor. The name in the header is still unverified,
but no key can play both sides: Hermes cannot admit its own handoff, and a human
editor cannot forge the runtime callback.

The last line is the one that settles the question. `decision_requests` is the
only module that models the distinction: `identity_assurance` is mandatory and
takes `declared` or `authenticated`, and `authenticated` requires an
`authenticated_principal` with `user_id` and `identity_provider`. Both arrive in
the request body. So the party asserting the name also chooses the assurance
level describing that assertion, and supplies the principal said to back it.
Nothing authenticates any of it.

The concept the other four modules lack already exists here. What it lacks is a
source of truth: an assurance level is only worth what produced it.

Two are worth reading twice. All four Information routes refuse a request
without `X-Pantheon-Actor` and none of them uses the value: the parameter is
named `_actor`, and `agency_information_cards` has no actor column to put it in.
The header is enforced as though it mattered and stored nowhere.

And in `knowledge_edit_variants` the review event log — the record of who chose,
who refused and who applied — takes its `actor` from that header and its
`actor_kind` from a literal written at each of its four `_insert_event` sites,
one `system` and three `human`. Both halves of the attribution are decided by the
code path rather than observed from the caller.

## What keeps being wrong

Four of those six were first recorded as `none`, and each correction had the same
shape: a guard was believed on the strength of what it is called rather than what
it composes to.

```text
review_ref                     reads as a reference to a review
"cannot revoke access.manage"  reads as protection of the administrator
_validate_actor                reads as a refusal of Hermes
status == "proposed"           reads as a decision already taken
```

None of the four was a slip. Each was a verdict written after reading the
function, and each was wrong one call away from where the reading stopped. The
question that finds them is not "what does this check" but "who controls each
input" — asked of every link, including the ones that look settled.

## How the surface is discovered, and why not by name

A first version of this test recognised entry points by five verb prefixes —
`apply`, `admit`, `promote`, `approve`, `commit`. A review pointed out that the
docstring then claimed far more than the code delivered, and it was right: that
net caught **8** functions while **64** other public functions write to the
database directly. Widening the verb list is not the fix either — it drags in
`create_app` and `resolve_case_ref`, which mutate nothing.

Discovery is therefore the union of two signals, neither sufficient alone:

```text
structural  a public function whose body contains an INSERT / UPDATE / DELETE
            statement — catches writers whatever they are called
verb        a public apply_/admit_/promote_/approve_/commit_ function — catches
            entry points that delegate their write and contain no SQL of their
            own, which the structural signal alone misses (two of the eight
            reviewed entries are exactly that)
```

This is a net, not a proof. It still cannot see a delegating entry point that is
named outside the verb list, and it does not follow the call graph. What it does
guarantee is that the surface it names is enumerated and cannot grow silently.

## What a declaration means

```text
gate = "enforce_consequential"    -> calls the Pantheon chokepoint
gate = "optional"                 -> chokepoint reachable but opt-in, default off
gate = "none"                     -> reviewed; module-local checks judged sufficient
gate = "gate_required_not_wired"  -> reviewed; the effect needs the chokepoint and
                                     does not reach it. A decision, not a defect
                                     list, and a debt that may not grow.
```

`none` is a conclusion, not an absence: it records that a human read the path and
judged its local chain sufficient. `unreviewed` is the absence. Keeping the two
apart is the whole point of this file — without the distinction, a path nobody
has looked at is indistinguishable from one that was cleared.

`local_guards` records what genuinely protects the path, so `"none"` is never
mistaken for `"unprotected"`. Entries carrying `_UNREVIEWED` are enumerated but
not yet individually read: their guard regime is *unknown*, which is recorded
honestly rather than assumed to be `"none"`. A test counts them, so the debt is
visible and shrinks deliberately.

## Two attribution mechanisms, and only one of them verifies

Reading the `agency_classification` cluster surfaced a repository-wide split that
no single entry owns.

```text
principal.principal_ref     35 sites   an authenticated principal context
X-Pantheon-Human-Actor      19 route dependencies across 8 modules
```

The second is a request header. `require_human_actor` is named like an
authentication check and composes to: read the header, require it non-empty.
Nothing ties the named human to a governed principal or to the party presenting
the bearer key — and the value is persisted into governed rows as `updated_by`.

So on those routes the *authorization* is verified (the bearer key) while the
*attribution* is asserted. The chokepoint would not repair that; binding the
actor to an authenticated identity would. It is recorded here because it is the
third instance in this file of the same failure shape, and the one with the
widest reach.

```text
import edge != call path
module reachable != gate invoked
local guard != central chokepoint
enumerated != reviewed
declared inventory != wired chokepoint
```

Adding an entry point without declaring it fails closed. Recording `_UNREVIEWED`
is a permitted, honest answer; recording nothing is not.
"""

from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path

MVP = Path(__file__).resolve().parents[1] / "mvp_vertical"

# Verb prefixes that name an entry point which may delegate its write.
MUTATION_PREFIXES = frozenset({"apply", "admit", "promote", "approve", "commit"})

# A statement that changes durable state, found in the function's own body.
SQL_WRITE = re.compile(r"\b(INSERT\s+INTO|UPDATE\s+[\w.\"]+\s+SET|DELETE\s+FROM)\b", re.IGNORECASE)

# Enumerated by the net below, but not yet individually read. Its guard regime is
# unknown — not assumed absent.
_UNREVIEWED = {"gate": "unreviewed", "local_guards": None}

INVENTORY: dict[tuple[str, str], dict[str, object]] = {
    ("agency_change_candidate_review.py", "request_project_candidate_revision"): {
        "gate": "none",
        "local_guards": ("actor required", "idempotency_key at least 8 characters", "note length bounded", "annotations normalized", "an idempotency key already used on another candidate conflicts", "row lock", "status must be pending_review", "actor_kind literal human", "the event payload records the non-equivalences as data"),
        "reviewed": (
            "Sends a candidate back for revision, which decides nothing and "
            "asks for more. Two guards are better than their neighbours\u2019: the "
            "replay check does not merely find the idempotency key, it refuses "
            "when that key already belongs to another candidate or another "
            "event type — an idempotency key cannot be smuggled across "
            "decisions. And the event payload it writes states "
            "`project_mutated`, `task_authorized` and `evidence_admitted` as "
            "False, so the non-equivalences are in the record and not only in "
            "the doctrine. "
            "The finding is the first statement in the function: "
            "`ensure_schema(conn)`, whose body is a migration followed by "
            "`conn.commit()`. This is the only write path in `mvp_vertical` that "
            "opens by committing — three functions call `ensure_schema` inline "
            "and this is the one that mutates. Under the current routes it is "
            "harmless, since `with_connection` hands out a fresh connection per "
            "request with nothing in flight. What it costs is composition: this "
            "function cannot be called inside a larger transaction without "
            "committing whatever that transaction had open, which is exactly "
            "the property `apu_cross_family.create_decision_request` relies on "
            "in its own composition."
        ),
    },
    ("agency_change_candidates.py", "apply_project_candidate"): {
        "gate": "none",
        "local_guards": ("human actor", "status", "base revision staleness", "idempotency"),
        "reviewed": (
            "A reviewed candidate is applied to a project only from a declared human actor, against the base revision it was prepared on. Staleness is refused rather than merged."
        ),
    },
    ("agency_change_candidates.py", "create_project_candidate"): {
        "gate": "none",
        "local_guards": ("proposer required", "proposer_kind vocabulary", "base_revision at least 1", "idempotency_key at least 8 characters", "base_revision must equal the Project current revision", "changes computed as a diff against the live Project", "status written as the literal pending_review", "an idempotency key carrying another proposal digest conflicts"),
        "reviewed": (
            "The admitted path for a non-human proposal, and the contrast with "
            "its own module\u2019s neighbours is the point. `agency_data.create_project` "
            "and `update_project` refuse `hermes` outright with "
            "`GovernanceGateRequired`; this one accepts it as a `proposer_kind` "
            "and can reach exactly one status, the literal `\u2019pending_review\u2019` in "
            "the INSERT. A runtime may say what it thinks should change and "
            "cannot say that it has changed. "
            "It also does not accept the change wholesale: `_proposal_changes` "
            "diffs the proposed attributes against the live Project, so what is "
            "stored is what would actually differ. And the idempotency check "
            "compares the proposal digest, so reusing a key for a different "
            "proposal conflicts rather than returning the old candidate. "
            "The finding is a read outside the write. "
            "`agency_data.get_project` and the `base_revision` comparison run "
            "before `conn.transaction()` opens, with no lock, so the Project can "
            "advance in between and the candidate is stored against a revision "
            "that is already stale. Recorded rather than escalated, and the "
            "reason is in the row: `base_revision` is persisted, not consumed, "
            "so the staleness survives into the data where an applier can still "
            "catch it. A check that loses what it read would be the defect; "
            "this one keeps it."
        ),
    },
    ("agency_change_candidates.py", "reject_project_candidate"): {
        "gate": "none",
        "local_guards": ("actor and reason both required non-empty", "row lock", "status must be pending_review", "status written as a literal", "actor_kind literal human in the event", "idempotency with the expected event type"),
        "reviewed": (
            "Rejects a proposed change, which is safety-increasing, and refuses "
            "to do it silently: the reason is required and stored. The replay "
            "lookup runs outside the transaction, which elsewhere in this review "
            "has been a finding — here it is not. A racing duplicate blocks on "
            "the row lock and then meets `status != pending_review`, so the "
            "second one conflicts rather than rejecting twice; the outside read "
            "is a shortcut, not the decision. "
            "The finding is one rung down from `entity_relations`. `actor_kind` "
            "is the literal `\u2019human\u2019` in this function, but "
            "`agency_change_candidate_events` only CHECKs the vocabulary "
            "`(human, hermes, system)`. So nothing below Python stops a "
            "rejection being attributed to Hermes — only this one literal in "
            "this one function does. Where `entity_relations` can say no stored "
            "row contradicts the doctrine, this module can only say no current "
            "caller does."
        ),
    },
    ("agency_claims.py", "record_claim"): {
        "gate": "none",
        "local_guards": ("status and certainty constrained by CHECK constraints", "verified requires an execution_result candidate carrying a review_disposition_id", "value must match the reviewed candidate, enforced by a trigger", "backing_ref must be one of the candidate basis_refs, enforced by a trigger", "append-only with supersedes"),
        "reviewed": (
            "Recorded as `gate_required_not_wired` when a direct Claim could "
            "carry `status=\"verified\"` with nothing having verified it: "
            "`validate_agency_project_claim_candidate_ref` returns early unless "
            "`source_kind` is `execution_result`, so the derivation triggers "
            "never saw the direct path. Closed in b201a019, which refuses "
            "`verified` unless the Claim comes from an execution_result "
            "candidate carrying a `review_disposition_id` — the status now "
            "requires the human review it asserts. The docstring's own boundary "
            "holds again: it records an assertion, and the one status that is a "
            "conclusion rather than an assertion has to be earned."
        ),
    },
    ("agency_classification.py", "archive_category"): {
        "gate": "none",
        "local_guards": (
            "route rejects the Hermes bearer key outright, and 503s if the editor and Hermes keys are identical — the only verified refusal of Hermes on this path",
            "_validate_actor rejects an actor_kind outside human or system, but the label is caller-supplied and defaults to human, so it refuses nothing on a direct call",
            "expected_revision optimistic concurrency, StaleCategoryWrite on mismatch",
            "refuses an already archived Category",
        ),
        "reviewed": (
            "Classification, not a professional act: it approves nothing, admits no Evidence and reaches nothing external. The protection is route-borne, not module-borne: the API route is the sole production caller and rejects the Hermes bearer key, "
            "while _validate_actor only checks a label the caller supplies and which defaults to human. A first review of this entry called those two independent layers; they are not, and the correction matters because a second production caller would inherit none of the route's refusal. Attribution is the module's other weak point: see the docstring."
        ),
    },
    ("agency_classification.py", "assign_category"): {
        "gate": "none",
        "local_guards": (
            "route rejects the Hermes bearer key outright, and 503s if the editor and Hermes keys are identical — the only verified refusal of Hermes on this path",
            "_validate_actor rejects an actor_kind outside human or system, but the label is caller-supplied and defaults to human, so it refuses nothing on a direct call",
            "required assignment, category and entity identifiers",
            "entity_type checked against a controlled set",
        ),
        "reviewed": (
            "Classification, not a professional act: it approves nothing, admits no Evidence and reaches nothing external. The protection is route-borne, not module-borne: the API route is the sole production caller and rejects the Hermes bearer key, "
            "while _validate_actor only checks a label the caller supplies and which defaults to human. A first review of this entry called those two independent layers; they are not, and the correction matters because a second production caller would inherit none of the route's refusal. Attribution is the module's other weak point: see the docstring."
        ),
    },
    ("agency_classification.py", "create_category"): {
        "gate": "none",
        "local_guards": (
            "route rejects the Hermes bearer key outright, and 503s if the editor and Hermes keys are identical — the only verified refusal of Hermes on this path",
            "the sole production caller passes actor_kind as a literal, so a request body cannot set it",
            "_validate_actor rejects an actor_kind outside human or system, but the label is caller-supplied and defaults to human, so it refuses nothing on a direct call",
            "required category_id and title, non-negative sort_order",
        ),
        "reviewed": (
            "Classification, not a professional act: it approves nothing, admits no Evidence and reaches nothing external. The protection is route-borne, not module-borne: the API route is the sole production caller and rejects the Hermes bearer key, "
            "while _validate_actor only checks a label the caller supplies and which defaults to human. A first review of this entry called those two independent layers; they are not, and the correction matters because a second production caller would inherit none of the route's refusal. Attribution is the module's other weak point: see the docstring."
        ),
    },
    ("agency_classification.py", "retire_category_assignment"): {
        "gate": "none",
        "local_guards": (
            "route rejects the Hermes bearer key outright, and 503s if the editor and Hermes keys are identical — the only verified refusal of Hermes on this path",
            "_validate_actor rejects an actor_kind outside human or system, but the label is caller-supplied and defaults to human, so it refuses nothing on a direct call",
            "expected_revision optimistic concurrency, StaleCategoryAssignmentWrite on mismatch",
            "refuses an already retired CategoryAssignment",
        ),
        "reviewed": (
            "Classification, not a professional act: it approves nothing, admits no Evidence and reaches nothing external. The protection is route-borne, not module-borne: the API route is the sole production caller and rejects the Hermes bearer key, "
            "while _validate_actor only checks a label the caller supplies and which defaults to human. A first review of this entry called those two independent layers; they are not, and the correction matters because a second production caller would inherit none of the route's refusal. Attribution is the module's other weak point: see the docstring."
        ),
    },
    ("agency_classification.py", "update_category"): {
        "gate": "none",
        "local_guards": (
            "route rejects the Hermes bearer key outright, and 503s if the editor and Hermes keys are identical — the only verified refusal of Hermes on this path",
            "the sole production caller passes actor_kind as a literal",
            "_validate_actor rejects an actor_kind outside human or system, but the label is caller-supplied and defaults to human, so it refuses nothing on a direct call",
            "expected_revision optimistic concurrency, StaleCategoryWrite on mismatch",
            "refuses an empty change set",
        ),
        "reviewed": (
            "Classification, not a professional act: it approves nothing, admits no Evidence and reaches nothing external. The protection is route-borne, not module-borne: the API route is the sole production caller and rejects the Hermes bearer key, "
            "while _validate_actor only checks a label the caller supplies and which defaults to human. A first review of this entry called those two independent layers; they are not, and the correction matters because a second production caller would inherit none of the route's refusal. Attribution is the module's other weak point: see the docstring."
        ),
    },
    ("agency_data.py", "create_project"): {
        "gate": "none",
        "local_guards": ("_validate_actor", "Hermes refused with GovernanceGateRequired", "project_id, code and display_name required", "tags, contacts and attributes normalized", "idempotency with payload digest", "pre-existence check", "event written in the same transaction"),
        "reviewed": (
            "Creates the Agency Project other tables carry foreign keys to. It "
            "refuses Hermes explicitly and by name — `GovernanceGateRequired`, "
            "not a generic error — so a bounded capability, not a direct call, "
            "is what a runtime would have to go through. "
            "The finding repeats one recorded a few entries earlier in this "
            "batch, which is what makes it worth stating as a shape rather than "
            "an incident. The pre-existence `SELECT` takes no lock, so two "
            "concurrent first creations both see nothing. `project_id` is the "
            "primary key and `code` is UNIQUE, so the race is closed below "
            "Python — but neither `UniqueViolation` is caught, so a collision "
            "on the concurrent path surfaces as a raw database exception where "
            "the sequential path raises `AgencyDataError(\"Agency Project "
            "already exists\")`. Same non-uniform error surface as "
            "`contradictory_review_store.persist_candidate`. The data is safe in "
            "both; the contract is not. "
            "Also worth recording because a reader would expect otherwise: "
            "`status` and `phase` are nullable TEXT with no CHECK, so a Project "
            "carries whatever status string it was given. What the schema does "
            "pin is `owner_system`, `CHECK (owner_system = \u2019postgres\u2019)` — a "
            "Project row cannot claim to be owned elsewhere."
        ),
    },
    ("agency_data.py", "update_project"): {
        "gate": "none",
        "local_guards": ("_validate_actor", "Hermes refused with GovernanceGateRequired", "PROJECT_MUTABLE_FIELDS allowlist, unknown fields refused by name", "an empty change refused", "expected_revision at least 1", "row lock", "revision compared under the lock", "AND revision = %s in the UPDATE with rowcount != 1", "idempotency with payload digest"),
        "reviewed": (
            "Edits an Agency Project, and carries the concurrency shape the "
            "Information projection had to be repaired into: the revision is "
            "compared under the row lock *and* carried into the UPDATE\u2019s own "
            "`WHERE`, with `rowcount != 1` raising `StaleProjectWrite`. Either "
            "layer alone would be defensible; both together mean a lost update "
            "has no path, and this one already had it. "
            "The assignment list is built by f-string interpolation of field "
            "names into SQL, which is the first thing a reader should flag. "
            "What makes it safe is the order: `set(changes) - "
            "PROJECT_MUTABLE_FIELDS` refuses anything outside a module-level "
            "literal set before a single name reaches the string. The guard is "
            "the allowlist, not the formatting, and it has to come first. "
            "Values stay parameterised throughout."
        ),
    },
    ("agency_information.py", "act_working_information"): {
        "gate": "enforce_consequential",
        "local_guards": ("actor_kind must be human, no default", "row lock", "working status only", "expected_revision", "supersede and install in one transaction", "decision_id required and bound to the content digest"),
        "reviewed": (
            "This is the act. It supersedes the currently acted version of a "
            "governed Information series and installs a new one, in one "
            "transaction, and the acted row is what `card_scope` and "
            "`hermes_scoped_context` read. The module states its own gravity — "
            "'only a human may act an Information version' — and enforced it by "
            "comparing a string the caller passes; the route passed it correctly "
            "already, from a dependency rather than the body. Two things made it "
            "a gate requirement anyway: the effect is a change to canonical "
            "agency state, and nothing recorded who performed it. `acted_at` is "
            "written; the acting party was not, because the table has no actor "
            "column. The route already discarded a real identity — "
            "`X-Pantheon-Actor`, resolved by `require_agency_actor` — as `_actor`; "
            "it now threads through as `actor` and becomes the decision's "
            "`decided_by`, which is where that identity lives now: the "
            "decision record, not the row. The digest binds `information_id` "
            "and `expected_revision` to the working row's content fields "
            "(excluding `status`/`acted_at`/`revision`/`updated_at`, which this "
            "act is what changes), so a decision cannot be replayed against a "
            "different card under the same identifiers. It does not verify the "
            "content is fit to be acted — only that the decision was taken over "
            "this exact content."
        ),
    },
    ("agency_information.py", "create_information"): {
        "gate": "none",
        "local_guards": ("actor_kind human or system, no default", "new rows must start draft or in_progress", "source ref/note validation", "handwritten allowlist, validated against the field registry"),
        "reviewed": (
            "Creates a draft, which approves nothing and supersedes nothing, and "
            "`actor_kind` carries no default, so a direct caller has to state its "
            "claim rather than inherit one. Corrected on review: this record said "
            "the field allowlist was derived from the schema rather than written "
            "out twice. Neither half was true. The set passed to `_schema_values` "
            "is seventeen names spelled out at the call site, duplicating the keys "
            "of the dict directly above it, and `_schema_values` only forwards "
            "whatever allowlist its caller hands it to `normalize_declared_fields`, "
            "which checks the field registry — not any declared view. A `create` "
            "view does exist and today matches the handwritten set exactly, minus "
            "`project_id`, which is a path parameter; nothing holds them in step. "
            "`update_working_information` next door does derive its allowlist, via "
            "`_editable_fields()` and the `edit` view, so the two paths differ in "
            "kind and only one of them was read correctly the first time."
        ),
    },
    ("agency_information.py", "derive_working_version"): {
        "gate": "none",
        "local_guards": ("row lock", "base must be the acted version", "source ref/note validation", "new row forced to draft"),
        "reviewed": (
            "Derives a new draft from the acted version; the status is a literal in "
            "the INSERT, so the caller cannot ask for anything else. One "
            "inconsistency worth naming rather than filing: `actor_kind` defaults "
            "to `human` here while the other three in this module require it. That "
            "is the shape corrected in the classification cluster — a default "
            "turning a claim into an inheritance — and it is the one entry point "
            "here where a future direct caller would pass the check by omission."
        ),
    },
    ("agency_information.py", "update_working_information"): {
        "gate": "none",
        "local_guards": ("hermes requires hermes_admitted, never passed by any route", "working status only", "expected_revision plus a rowcount check", "editable-field allowlist", "status restricted to working values"),
        "reviewed": (
            "Edits a working version only: an acted or superseded row is refused "
            "outright. Concurrency is checked twice — the locked read compares "
            "`expected_revision`, and the UPDATE carries the revision in its WHERE "
            "clause and asserts `rowcount == 1`, so a race that slips past the "
            "first check still cannot write. Hermes is refused unconditionally in "
            "production because `hermes_admitted` is a parameter no route passes."
        ),
    },
    ("apu_mapping_reviews.py", "append_mapping_review"): {
        "gate": "none",
        "local_guards": ("action vocabulary", "the mapping candidate must exist in that execution result", "select_existing_object requires a selected ref", "append-only", "idempotency"),
        "reviewed": (
            "Records a human review of one Hermes mapping candidate. It reads the "
            "execution result and refuses a mapping_ref that is not in it, so a "
            "review cannot be recorded against a mapping that was never produced. "
            "Its output is what `prepare_write_command` later reads for the "
            "target, which is why that function does not need to accept one."
        ),
    },
    ("apu_owner.py", "apply_source_match"): {
        "gate": "none",
        "local_guards": ("prior authorization id", "exact command shape", "idempotency"),
        "reviewed": (
            "Applies a match that a prior authorization already decided; the command shape is checked exactly, so this records a decision rather than taking one."
        ),
    },
    ("apu_owner.py", "store_reviewed_dossier"): {
        "gate": "enforce_consequential",
        "local_guards": (
            "required project_id, review_ref, actor and idempotency_key",
            "payload digest compared on replay, refusing a reused key with different content",
            "normalization before write",
            "chokepoint before the write, expectation bound to a digest that folds review_ref into the dossier as one unit",
            "the only production path refuses to open a connection without a decision point",
        ),
        "reviewed": (
            "Installs canonical APU state. First reviewed as none on the reasoning that "
            "review_ref carries a review that already happened, so the consequence gate "
            "belonged at that review rather than at its recording. That was wrong, and a "
            "review caught it: review_ref passes through _required only — a non-empty "
            "string. No lookup, foreign key, signature or any other check ties it to a "
            "completed governed review, and no table of such reviews exists to point at. "
            "Wired. Wiring it found the same shape as `bind_oidc_identity`: the function "
            "had no production caller at all — thirteen test modules called it and "
            "nothing else did, so a Project's whole Architecture Project Understanding "
            "baseline could only be installed by writing to the database directly. "
            "`_normalize_dossier` already folds `review_ref` into the same structure as "
            "the stable objects, representations and claims before "
            "`payload_digest = _digest(dossier)` is computed, so the fix does not have "
            "to invent a binding: the decision expectation's `expected_digest` is that "
            "same `payload_digest`, which covers this exact `review_ref` bundled with "
            "this exact dossier as one unit. That still does not verify `review_ref` "
            "names a review that actually happened — nothing in this repository can, "
            "absent the table that would let it — but it closes the gap this entry "
            "originally named: a decision taken over one dossier/review_ref pairing "
            "cannot be replayed against a different one. The scope is the Project, "
            "matching what the write installs. `cli store-reviewed-dossier` is the new "
            "production path and the composition point that makes the gate mandatory: "
            "it refuses to open a connection unless a decision point is configured or "
            "`MVP_POLICY_ENFORCEMENT=disabled` is declared by name, the same "
            "arrangement `bind-oidc-identity` and `cockpit_shell` already use."
        ),
    },
    ("apu_write_preparation.py", "append_authorization"): {
        "gate": "none",
        "local_guards": ("action vocabulary", "command payload revalidated", "authorization bound to the command payload digest", "command row locked before the event is written", "append-only event", "idempotency with payload digest"),
        "reviewed": (
            "Records a human authorization, or a rejection, of a prepared "
            "command. The row it writes carries `command_payload_digest` taken "
            "from the stored command, and `apply_authorized_write_command` "
            "refuses to act unless that digest still equals the command being "
            "applied. This is the one place in the codebase where an approval is "
            "a first-class stored object bound to the content it approves, rather "
            "than a reference someone supplied. Updated on review: it now takes "
            "the command row `FOR UPDATE` before writing, which is the half of "
            "the apply-path repair that lives here. A lock one writer takes "
            "alone orders nothing."
        ),
    },
    ("apu_write_preparation.py", "apply_authorized_write_command"): {
        "gate": "none",
        "local_guards": ("reviewed command chain", "command row locked, then the whole chain read inside the transaction that applies", "latest authorization must be authorize_application", "authorization must cover the exact command payload digest", "stored index vs embedded effect", "owner and object revision freshness", "idempotency"),
        "reviewed": (
            "The strongest local chain in the inventory, and this record "
            "understated why. Beyond the reviewed command, the stored index "
            "agreeing with the embedded effect and both revisions still being "
            "fresh, `_latest_application_authorization` requires that the most "
            "recent authorization is `authorize_application` — so a later "
            "rejection blocks the apply — and that its "
            "`command_payload_digest` equals the command's own. An "
            "authorization here covers a specific content, not a name. That is "
            "what the eight `gate_required_not_wired` entries lack: they accept "
            "a claim that a decision happened, while this one refuses to act "
            "unless the recorded decision covers the bytes being applied. "
            "Corrected on review, then repaired: the digest binding held under "
            "concurrency and the ordering did not. "
            "`_latest_application_authorization` ran an unlocked SELECT over the "
            "authorization events and the delegation to `apu_owner."
            "apply_source_match` followed outside any shared transaction, with no "
            "`FOR UPDATE` on the command row, so a rejection committing between "
            "the read and the write did not block the apply. Same class as the "
            "first-write race `information_projection` carried until 552e67e7 "
            "closed it: a check that reads outside the transaction that acts. "
            "Now closed on both sides. `_lock_write_command` takes the command "
            "row — append-only, so the lock never changes it and serves only as "
            "the mutex — and the whole chain, the authorization read included, "
            "runs inside the transaction that delegates. `append_authorization` "
            "takes the same row before writing its event, which is what makes "
            "the lock mean anything: the finding was not that a lock was "
            "missing on one side but that neither side had one to share."
        ),
    },
    ("apu_write_preparation.py", "prepare_write_command"): {
        "gate": "none",
        "local_guards": ("target taken from the latest selected review, not from the caller", "selected object must still be among the mapping candidates", "target APU object must exist and not be retired", "owner and object revisions captured into the command", "stable command id derived from the whole chain", "idempotency"),
        "reviewed": (
            "Builds the command a human will later authorize. It does not accept "
            "the target: it reads the latest selected mapping review and takes "
            "`selected_stable_object_ref` from there, then refuses if that object "
            "is no longer among the mapping's candidates or has been retired. The "
            "command id is derived from the execution result, the result and "
            "mapping refs and the review id, so the same chain always produces the "
            "same command."
        ),
    },
    ("contradictory_review_store.py", "persist_candidate"): {
        "gate": "none",
        "local_guards": ("project_id and submitted_by required", "authority ceiling: is_evidence, is_approval, is_zeus_closure and is_task_authorization must each be exactly False", "status vocabulary", "deterministic review id", "an existing row must match both the project and the report digest"),
        "reviewed": (
            "Persists a compiled contradictory-review report, and carries a "
            "guard shape that appears nowhere else in this inventory: an "
            "authority ceiling. Before storing anything it reads the report\u2019s "
            "own `authority` block and refuses unless `is_evidence`, "
            "`is_approval`, `is_zeus_closure` and `is_task_authorization` are "
            "each exactly `False`. The store refuses to hold a report that "
            "claims to be Evidence or an approval — `memory != Evidence` "
            "enforced at the point of writing rather than asserted in a name. "
            "The finding is small and is about the error surface. The existence "
            "check runs outside the transaction with no lock, so two concurrent "
            "first writes of the same review id both see nothing. The primary "
            "key on `review_id` closes the race below Python — but the "
            "`UniqueViolation` it raises is not caught here, so a legitimate "
            "concurrent replay surfaces as a raw database exception instead of "
            "the `ContradictoryReviewConflict` the same collision produces on "
            "the sequential path. The data is safe; the contract is not "
            "uniform."
        ),
    },
    ("decision_requests.py", "cancel_request"): {
        "gate": "none",
        "local_guards": ("rationale required", "row lock", "status must be pending", "expected_revision in the WHERE clause", "idempotency with payload digest", "event records the actor"),
        "reviewed": (
            "Withdraws a pending request, which decides nothing and is "
            "safety-decreasing only in the sense that a question goes unanswered. "
            "It insists on a rationale, refuses a request that is no longer "
            "pending, and records the cancelling actor and an event. The actor is "
            "the `X-Pantheon-Human-Actor` header value, as everywhere else."
        ),
    },
    ("decision_requests.py", "create_request"): {
        "gate": "none",
        "local_guards": ("status is a literal in the INSERT", "decision_type, priority and response_mode checked against frozensets", "blocking requires a WorkIssue", "evidence ref and digest required together", "projection validated against the decision_request contract", "idempotency with payload digest"),
        "reviewed": (
            "Creates a pending request: it asks for a decision, it does not take "
            "one. The INSERT writes `status` as a literal `'pending'`, so no "
            "caller can create a request that arrives already resolved — the same "
            "shape `create_variant_request` uses and `knowledge.create_edit_request` "
            "does not. The projection is validated against the `decision_request` "
            "contract on read."
        ),
    },
    ("decision_requests.py", "resolve_request"): {
        "gate": "none",
        "local_guards": ("row lock", "status must be pending", "expected_revision in the WHERE clause", "response validated against the request's mode and options", "unique decision identity", "idempotency with payload digest", "decision record and status transition in one transaction", "authenticated assurance unreachable from the route"),
        "reviewed": (
            "Recorded as `gate_required_not_wired` when the caller chose both "
            "the name and the assurance level describing it — a governed "
            "decision record could read `identity_assurance: authenticated` on "
            "a decision nothing authenticated. Closed by typing "
            "`authenticated_principal` as `None` on the route body, so the "
            "module's own requirement that an authenticated assurance carry a "
            "principal can no longer be met and the persisted level is always "
            "`declared`. Closed by removing the capability rather than by "
            "sourcing it, and the route says so: 'this editor-key route has no "
            "authenticated-principal source. Keep the persisted assurance honest "
            "until a real identity provider is composed.' `decided_by` is still "
            "the header value, which is the attribution axis this review records "
            "across seven modules and does not escalate — but `declared` is now "
            "a truthful label for it."
        ),
    },
    ("document_revision_discussion.py", "create_comment"): {
        "gate": "none",
        "local_guards": ("revision must exist", "body and anchor normalized", "a reply may only target a comment on the same exact revision", "idempotency with payload digest", "insert and read in one transaction"),
        "reviewed": (
            "Appends a comment to one exact professional revision. The scope "
            "guard is the one worth naming: a reply whose parent belongs to "
            "another revision raises `CrossRevisionReply`, so a discussion "
            "cannot be stitched across two versions of a document and read as "
            "one thread. "
            "What makes this entry unusual is that the module says what it is "
            "not doing, in the code: *Existence only. Authorization is "
            "deliberately outside this persistence owner.* Nothing here checks "
            "that `created_by` may comment on that revision — and the comment "
            "makes that a stated boundary rather than a gap someone has to "
            "find. That is the opposite of the failure this review keeps "
            "recording, and it is worth saying so. The obligation is real and "
            "it is deferred to the route; a reader of this entry should treat "
            "it as an open question about the route, not a closed one about "
            "the module."
        ),
    },
    ("entity_relations.py", "propose_relation"): {
        "gate": "none",
        "local_guards": ("_actor(proposing=True) admits Hermes for the proposal and nothing else", "relation_type vocabulary", "entity_type checked against ADMITTED_ENTITY_TYPES", "self-edge refused", "partial unique index on the open edge", "idempotency with payload digest", "event written in the same transaction"),
        "reviewed": (
            "Writes a proposal, which is a candidate and decides nothing, and "
            "`_actor` is where this module states the boundary in one place: "
            "proposing admits Hermes, canonizing and rejecting and retiring do "
            "not. The finding is what `_entity_ref` checks. It validates the "
            "endpoint's *type* against `ADMITTED_ENTITY_TYPES` and never its "
            "existence, and `015_entity_relations.sql` cannot help: `project_id` "
            "carries a foreign key to `agency_projects`, but `from_entity_id` and "
            "`to_entity_id` are plain TEXT under a type CHECK, because the ids "
            "are polymorphic and no single foreign key can reach them. So a "
            "relation may be proposed between ids that name nothing at either "
            "end. Recorded rather than escalated: a proposal is a claim, and the "
            "act that would make it true is reviewed separately — see the "
            "addendum on `canonize_relation`, which does not check existence "
            "either."
        ),
    },
    ("execution_results.py", "append_review_disposition"): {
        "gate": "none",
        "local_guards": ("disposition vocabulary", "result row locked FOR UPDATE across checks and replay", "result_kind must match the disposition family", "claim-bearing dispositions require reviewer_kind human", "a database trigger enforces the same", "idempotency with payload digest"),
        "reviewed": (
            "The first guard in this review enforced below Python. "
            "`accepted_for_claim` and `selected_for_change_candidate` are refused "
            "for a non-human reviewer by this function *and* by "
            "`validate_execution_result_review_disposition`, a trigger on the "
            "table. That answers the weakness recorded against "
            "`agency_classification._validate_actor`, which was not a second "
            "layer because a direct caller inherited its default: a trigger is a "
            "second layer, because a second Python caller cannot route around it. "
            "The route passes `reviewer_kind=\"human\"` as a literal behind the "
            "editor key. The immutable result row is locked before the checks and "
            "kept locked through the replay lookup, so a replay cannot bypass the "
            "semantic checks for its family."
        ),
    },
    ("execution_results.py", "store_execution_result"): {
        "gate": "none",
        "local_guards": ("Hermes bearer key on the route", "authority block must equal the module constant exactly", "producer, results and refs required", "idempotency with payload digest"),
        "reviewed": (
            "Stores a returned execution result as a candidate. The record is "
            "refused unless its `authority` block equals the module's own "
            "constant, so a runtime cannot return a result that describes its own "
            "authority differently from the one the store recognises — the "
            "boundary is compared, not read from the payload."
        ),
    },
    ("hermes_execution.py", "admit_handoff"): {
        "gate": "none",
        "local_guards": ("human actor", "read_only effect only", "Task Contract and Context Pack identity", "TTL bounds", "idempotency"),
        "reviewed": (
            "Admits an external execution handoff bounded to a read_only effect, tied to a Task Contract and Context Pack identity and a TTL. Admission of a read_only effect is not authorization of a consequential one."
        ),
    },
    ("hermes_execution.py", "record_external_runtime_start"): {
        "gate": "none",
        "local_guards": ("Hermes key and Hermes actor on the route", "admission locked", "state must be admitted or launch_reserved", "exact launch reservation match", "work-issue version pinned to the admitted or reserved version", "run linkage asserts rowcount == 1", "idempotent on the same run_id"),
        "reviewed": (
            "Records that an external runtime started against an admission. It "
            "is reached with a different key from admission: the route takes "
            "`require_hermes_key` and `require_hermes_actor`, while admission and "
            "revocation take the editor key and a human actor. Corrected on "
            "review: that separation is a configuration property, not an enforced "
            "one. Both dependencies compare the bearer against their own key and "
            "nothing else, and `create_app` accepts an editor key equal to the "
            "Hermes key, so one credential can admit a handoff and record its "
            "runtime start. The `editor_match and hermes_match` refusal exists "
            "three times in this codebase — `agency_data_api`, "
            "`agency_classification_api`, `cockpit_shell` — and covers none of the "
            "execution routes, which is where the doctrine needs it most. The "
            "regime stays `none`: what collapses is segregation of duties, not the "
            "read_only bound on the effect, and the collapsed holder is the editor "
            "key holder who could already admit. The repair is one place — refuse "
            "equal keys when the app is constructed. "
            "The callback's `expected_issue_version` must equal the version the "
            "admission or reservation pinned. Worth quoting: the response carries "
            "its own non-equivalences as data — `runtime start recorded != "
            "Evidence`, `launch reservation != dispatch`, `running != task "
            "success`. The code states what it does not mean."
        ),
    },
    ("hermes_execution.py", "revoke_admission"): {
        "gate": "none",
        "local_guards": ("editor key and human actor on the route", "human actor and reason required", "admission locked", "state must be admitted", "idempotency checked across admission, actor and reason"),
        "reviewed": (
            "Withdraws an admission, which is safety-increasing, and records the "
            "reason as an event rather than mutating the admission row. The "
            "replay check compares admission, actor and reason together, so one "
            "idempotency key cannot carry a different revocation."
        ),
    },
    ("hermes_handoff_store.py", "submit_handoff"): {
        "gate": "none",
        "local_guards": ("human actor required", "preview must carry execution_authorized false", "requested_effect must be read_only", "immutable basis assembled and stored", "owner reads inside the write transaction", "idempotency with request digest"),
        "reviewed": (
            "Submits a handoff request. Two refusals are structural rather than "
            "advisory: the preview must say `execution_authorized: false`, and the "
            "effect must be `read_only`. Owner reads run inside the same explicit "
            "transaction as the write, which the source comment explains. On "
            "`preview_digest` the protection is route-borne, not module-borne, "
            "and this record first overstated that. `submit_handoff` does not "
            "recompute the digest from the preview it is handed, so a direct "
            "Python caller could fabricate one — but the sole production caller "
            "rebuilds the preview server-side with `prepare()`, and "
            "`hermes_handoff_preview.build_preview` sets "
            "`preview[\"preview_digest\"] = _digest(preview)` over that "
            "server-built content. The client's `expected_preview_digest` is only "
            "compared, to reject a stale scope with 409. So the chain every later "
            "stage relies on — the immutable basis at admission, the re-derivation "
            "in `get_execution_envelope` — is anchored to a computed value on the "
            "one path that exists today, and to an argument if a second caller is "
            "ever added."
        ),
    },
    ("hermes_launch_context.py", "reserve_launch"): {
        "gate": "none",
        "local_guards": ("Hermes key and actor on the route", "REPEATABLE READ isolation", "admission locked FOR UPDATE", "one reservation per admission", "idempotency checked across admission and actor"),
        "reviewed": (
            "Reserves exactly one launch against an admission and freezes its "
            "bootstrap context. It raises the transaction isolation to REPEATABLE "
            "READ and locks the admission, so two runtimes cannot both reserve. "
            "The docstring names the thing a caller would otherwise assume: a "
            "replay of the same idempotency key returns the same immutable "
            "reservation and is not permission to submit Hermes again."
        ),
    },
    ("hermes_result_candidate.py", "create_result_candidate"): {
        "gate": "none",
        "local_guards": ("Hermes key and actor on the route", "candidate payload normalized", "at least one trace_ref required", "summary bounded", "result digest over the whole material", "idempotency"),
        "reviewed": (
            "Persists what the runtime returned as a candidate. Nothing here "
            "admits Evidence, validates Knowledge or authorizes a task; the "
            "requirement of at least one `trace_ref` means a candidate cannot "
            "arrive with nothing to check it against."
        ),
    },
    ("human_access.py", "bind_oidc_identity"): {
        "gate": "enforce_consequential",
        "local_guards": ("refuses a disabled principal", "required issuer, subject and bound_by", "BindingConflict when the identity is bound to another principal", "idempotent within the same principal", "chokepoint before the write, with an expectation bound to binding_digest", "the only production path refuses to open a connection without a decision point"),
        "reviewed": (
            "The moment an external identity becomes able to act as a governed "
            "principal, and the root of trust for every route behind "
            "`require_principal`: `resolve_principal_context` resolves each "
            "authenticated request against the row this writes. "
            "Wired. It was recorded as needing the chokepoint, and reading it "
            "again to wire it found something the entry had not said — the "
            "function had no production caller at all. Seven test modules called "
            "it and nothing else did, so `human_oidc_bindings` could only be "
            "populated from outside the product, and the whole principal regime "
            "resolved against a table nothing in it wrote. "
            "The authority is not a grant, and that is the repository\u2019s own "
            "decision rather than a gap here. "
            "`033_human_project_access_management.sql` says "
            "`project.access.manage` \"does not encode professional role, "
            "approval, Decision, Evidence or IdP invitation authority\" and "
            "\"remains a locally provisioned bootstrap capability\". The table "
            "could not express the permission in any case: "
            "`human_resource_grants.project_id` is NOT NULL against "
            "`agency_projects`, so every grant is project-scoped, and a "
            "project-scoped grant minting a system-wide identity would be an "
            "escalation. "
            "So the authority is the chokepoint. `enforce_consequential` runs "
            "before the write with a `decision_expectation` whose "
            "`expected_digest` is `binding_digest(...)` over the principal, "
            "issuer, subject and validity — the decision covers this exact "
            "binding rather than naming it, which is the "
            "`append_authorization` shape this review recommended everywhere "
            "else. The scope is `human_principal`, not a borrowed project, "
            "because a binding is not project-scoped. "
            "`policy_client` is optional here, exactly the shape this inventory "
            "recorded as unenforced. What makes it bite is composition: the one "
            "production path, `cli.bind-oidc-identity`, refuses to open a "
            "connection unless a decision point is configured or "
            "`MVP_POLICY_ENFORCEMENT=disabled` is declared by name. Same "
            "arrangement as `cockpit_shell.require_policy_client`, and tested "
            "by removing it."
        ),
    },
    ("human_access.py", "create_principal"): {
        "gate": "none",
        "local_guards": ("required principal_ref", "recorded created_by actor", "idempotent ON CONFLICT insert"),
        "reviewed": "Creates a governed identity; it authorizes nothing on its own — grant_access does. The actor who created it is recorded. No runtime caller at review time.",
    },
    ("human_access.py", "disable_principal"): {
        "gate": "none",
        "local_guards": ("existence check", "idempotent when already disabled"),
        "reviewed": "Withdraws the ability to act, so the direction is safety-increasing and the local chain is thin by design. Recorded as reviewed with one finding: unlike create_principal it records no actor, so a disabling leaves no trace of who did it.",
    },
    ("human_access.py", "grant_access"): {
        "gate": "none",
        "local_guards": (
            "route requires an authenticated principal holding project.access.manage",
            "granted_by is taken from the authenticated session, never from the request body",
            "route refuses to delegate project.access.manage, so a grant cannot escalate",
            "a document grant requires the target to already hold active project.read",
            "refuses a disabled principal",
            "resource_type and action checked against controlled vocabularies",
            "project existence and document-belongs-to-project checked",
            "idempotent on an identical active grant",
        ),
        "reviewed": (
            "An authorization boundary, and the reflex after the store_reviewed_dossier "
            "correction is to escalate it too. The distinguishing fact is that the actor "
            "here is verified rather than asserted: granted_by comes from the "
            "authenticated session and the caller must already hold project.access.manage, "
            "checked against the database. store_reviewed_dossier failed on exactly the "
            "opposite — a review_ref nothing verifies. The route also caps escalation by "
            "refusing to delegate the manage right at all, and the codebase names the "
            "effect technical_project_access_granted, distinguishing it from a "
            "professional one. Cleared on the chain, not on the category."
        ),
    },
    ("human_access.py", "revoke_grant"): {
        "gate": "none",
        "local_guards": ("refuses to revoke project.access.manage remotely", "refuses to revoke project.read while the principal holds active project.access.manage", "idempotent when already revoked"),
        "reviewed": (
            "Recorded as `gate_required_not_wired` for an administrator "
            "lockout: the route refused to revoke a `project.access.manage` "
            "grant but not the paired `project.read` grant a manager needs to "
            "pass its own check, so one manager could lock another out. Closed "
            "in 2f9fcfbd, which refuses to revoke `project.read` while that "
            "principal still holds an active `project.access.manage`. The "
            "symmetric guard the first one only looked like."
        ),
    },
    ("human_access.py", "revoke_oidc_binding"): {
        "gate": "none",
        "local_guards": ("required binding_id", "raises on unknown binding", "idempotent when already revoked"),
        "reviewed": "Withdraws an ability, so it is safety-increasing. Same finding as disable_principal: no actor is recorded on the revocation.",
    },
    ("information_projection.py", "add_document_link"): {
        "gate": "none",
        "local_guards": ("actor_kind human or system, no default", "Information and Document existence checked", "link role vocabulary", "row lock once the metadata row exists", "expected_revision, compare-and-swap on the write itself", "idempotency with payload digest", "event derived from the write's own result"),
        "reviewed": (
            "Links a Document to an Information card: metadata about what backs a "
            "card, not a change to what the card says. Both endpoints are checked "
            "to exist before the write. `observed_version` and `observed_digest` "
            "are caller-supplied and unverified against the Document, which the "
            "names say plainly — they record what the linker saw, not a validated "
            "fact, and this review has recorded the opposite naming twice. "
            "Notable in the other direction: the upsert returns `(xmax = 0)` and "
            "the event type is chosen from that, so `document_link_added` versus "
            "`document_link_updated` reflects what the statement did rather than "
            "what a preceding SELECT predicted. The comment says a prior version "
            "got this wrong and left the history describing a creation that never "
            "happened. That is a record derived from an effect instead of "
            "asserted beside it. Corrected twice on review: this entry first "
            "named the row lock and `expected_revision` as unqualified guards "
            "while `FOR UPDATE` could not lock a row that did not exist yet, so "
            "two concurrent first writes both logged `0 -> 1`; 552e67e7 closed "
            "that by carrying the expected revision into the upsert's conflict "
            "clause, and this entry then went on describing it as open. Both "
            "readings are kept in the docstring section, because the record was "
            "wrong in each direction in turn."
        ),
    },
    ("information_projection.py", "remove_document_link"): {
        "gate": "none",
        "local_guards": ("actor_kind human or system, no default", "row lock once the metadata row exists", "expected_revision, compare-and-swap on the write itself", "rowcount == 1 or the link did not exist", "idempotency with payload digest"),
        "reviewed": (
            "Unlinks a Document from an Information card, withdrawing a "
            "projection rather than changing governed content. The DELETE asserts "
            "`rowcount == 1`, so removing a link that was not there is an error "
            "rather than a silent success — the event log cannot record a removal "
            "that removed nothing. Corrected twice on review: the row lock and "
            "`expected_revision` were first recorded as unqualified, then as "
            "holding only once the metadata row existed, which stopped being "
            "true when 552e67e7 moved the revision check into the upsert's own "
            "conflict clause. The guard list above is the current reading."
        ),
    },
    ("information_projection.py", "update_projection_metadata"): {
        "gate": "none",
        "local_guards": ("actor_kind human or system, no default", "media-type vocabulary", "contact refs resolved against their tables", "row lock once the metadata row exists", "expected_revision, compare-and-swap on the write itself", "idempotency with payload digest"),
        "reviewed": (
            "Edits projection metadata — dates, media types, contact references. "
            "`projection != persistence` and `projection != governed identity` "
            "both apply: none of this changes what the Information says or who "
            "may act on it. Contact references are resolved against their tables "
            "rather than stored as free strings. Corrected twice on review: this "
            "was the path where the first-write race cost a lost update rather "
            "than just a false history line, and it is the path 552e67e7 "
            "repaired most directly — the upsert now names `expected_revision` "
            "in its `WHERE` and raises unless it changed exactly one row, so the "
            "loser of a first-write race fails as stale instead of overwriting."
        ),
    },
    ("knowledge.py", "apply_edit_request"): {
        "gate": "enforce_consequential",
        "local_guards": ("request row locked before status/admission checks", "transaction owned before the first database read", "Knowledge row re-read under lock", "version and selection digest", "single transaction with audit", "idempotency", "stale conflict transition only updates a still-proposed request", "recompile source_documents and compilation-binding rows locked in stable order through admission and persistence", "recompile source-context digest, frozen-content integrity and allowed current source refs are rechecked after those locks", "chokepoint after all staleness checks, expectation bound to a digest of the exact replacement, recompile context and provenance when present", "unconditional: apply always needs a decision, not just a review_status=\"reviewed\" claim"),
        "reviewed": (
            "Wired, at the point this entry itself named: `create_edit_request` "
            "accepts `replacement_markdown` from its caller and sets `proposed` on "
            "the spot, and `complete_edit_request` sets `proposed` with no status "
            "guard (see that entry — closed separately, by a local fix rather than "
            "this gate). Nothing upstream has to decide anything for a request to "
            "arrive here `proposed`. This is the point where the Knowledge Markdown "
            "actually changes, so this is where the chokepoint belongs, not either "
            "of those. "
            "The gate call sits after the re-read under lock, once `item[\"version\"]` "
            "and `_digest(selected)` are confirmed to still match the request — so "
            "the decision the PDP validates covers `{request_id, knowledge_id, "
            "base_version, selected_text_digest, replacement_markdown}`, the exact "
            "replacement about to be spliced in, not a name. Scope is the "
            "Knowledge item's Project. A refusal propagates past the "
            "`_EditRequestConflict` handler untouched — refusal is not staleness, "
            "so the request stays `proposed` and retryable once a real decision "
            "exists, rather than being marked `conflict`. "
            "Two production adapters reach this function: the direct "
            "`apply_intelligent_edit` route and `apply_selected_variant`. Both "
            "thread `policy_client` through. The owner now opens its transaction "
            "before its first database read; this matters with psycopg "
            "autocommit=False, because reading first would make the apparent "
            "transaction a savepoint that an API connection close could roll back."
        ),
    },
    ("knowledge.py", "complete_edit_request"): {
        "gate": "none",
        "local_guards": ("non-empty replacement", "Hermes bearer key on the route", "request row locked across terminal-status check and proposal transition", "version comparison against base_version", "status must be queued_for_hermes, or an identical replay of the same proposed replacement", "recompile proposals must match the frozen source-context digest", "replacement source refs must stay inside the bounded context and retain a current primary-source chunk", "ordinary edits cannot replace provenance"),
        "reviewed": (
            "Corrected. Reads as Hermes filling in the proposal it was queued for. "
            "It took no actor, no idempotency key, wrote no event, and guarded no "
            "status: it set `replacement_markdown` and a status on whatever "
            "request_id it was given. `knowledge_edit_variants.reject_request` "
            "moves a request to `rejected` and records a human rejection event; "
            "that rejection does not revise the Knowledge item, so the version "
            "still equalled base_version, so this function returned the request "
            "to `proposed` — and the editor-keyed apply route would then apply "
            "it. The party whose proposal was rejected could un-reject it, "
            "leaving no trace beside the rejection event. "
            "This is a missing local check, not a missing decision point: "
            "`queued_for_hermes` is the only status any code path ever sets it "
            "to from, and nothing transitions a request back to it once it "
            "leaves — `knowledge_edit_variants.py` treats `{queued_for_hermes, "
            "proposed}` as the only live pair throughout. The function now "
            "refuses unless the request is in that one status, with an "
            "idempotent exception for replaying the identical replacement "
            "already recorded. `apply_edit_request` is still where the actual "
            "Markdown change is decided; this closes the one path that could "
            "reach it carrying a decision that had already been withdrawn."
        ),
    },
    ("knowledge.py", "create_edit_request"): {
        "gate": "none",
        "local_guards": ("instruction kind and non-empty instruction", "row lock", "base_version equality", "selected text matched against the live snapshot", "idempotency with payload digest"),
        "reviewed": (
            "Writes a request row, which is a candidate and not itself consequential, "
            "and its concurrency guards are unusually tight — the selection range and "
            "the selected text are both checked against the locked snapshot. The "
            "finding is what it can set that row to: passing `replacement_markdown` "
            "on creation skips `queued_for_hermes` and writes `proposed` directly, so "
            "the editor key alone produces the text, the status that reads as a "
            "decision, and then the apply. `requested_by` is an unverified body "
            "string. Recorded at the apply, which is where the Knowledge changes, "
            "rather than duplicated here."
        ),
    },
    ("knowledge.py", "create_recompile_request"): {
        "gate": "none",
        "local_guards": (
            "Knowledge source state must require recompilation",
            "bounded recompile context must be complete and not source-blocked",
            "full Markdown snapshot and exact base_version are delegated to create_edit_request",
            "recompile_context_digest freezes the source-state candidate basis",
            "idempotency is enforced by the existing edit-request owner",
            "the outer transaction starts before source-context reads so the request commits rather than remaining inside an implicit-read savepoint",
            "replay returns the durable request even after Knowledge/source state later changes",
        ),
        "reviewed": (
            "Creates no Knowledge revision and authorizes no effect. It is a thin "
            "candidate constructor over `create_edit_request`: first it computes the "
            "bounded source context, refuses a current or incomplete Knowledge item, "
            "then records a full-document edit request tied to the exact Knowledge "
            "version and source-context digest. The live route requires the editor "
            "key, while `requested_by` remains asserted attribution. Hermes can only "
            "fill the resulting proposal; the existing `apply_edit_request` "
            "chokepoint remains the place where Markdown and, for a recompile, exact "
            "source provenance may change."
        ),
    },
    ("knowledge.py", "publish_knowledge"): {
        "gate": "enforce_consequential",
        "local_guards": ("non-empty knowledge_id, title and Markdown", "family membership", "expected_version must be 0", "idempotency", "chokepoint, only when review_status=\"reviewed\" is requested, expectation bound to the publish digest"),
        "reviewed": (
            "The route guard was a bearer-token comparison, and the body was "
            "passed through with `**body.model_dump()`. Three of those fields "
            "are claims about people: `created_by`, `actor_kind` — which accepts "
            "`hermes` — and `review_status`, which accepts `reviewed`. The "
            "function checked each only against a set of permitted strings. A "
            "holder of the editor key could therefore publish a Knowledge item "
            "that already read as professionally reviewed, attributed to "
            "anyone. `schema conformance != professional approval` is the "
            "invariant, and membership in REVIEW_STATUSES was exactly the "
            "conformance being mistaken for it. "
            "Wired, narrowly. Candidate publication — `generated_unreviewed`, "
            "`needs_review`, `superseded` — asserts nothing a reader would take "
            "as a professional claim, so it needs no decision point and gates "
            "none of those three; wiring the whole function would have refused "
            "ordinary candidate work whenever no PDP happened to be configured, "
            "which the finding never asked for. Only a request that asserts "
            "`review_status=\"reviewed\"` at publication routes through the "
            "chokepoint, with the decision bound to the publish payload digest "
            "— the same `pdigest` the idempotency replay already used, so the "
            "decision covers this exact title, family, Markdown and chunk set, "
            "not the word \"reviewed\" alone. `created_by` and `actor_kind` "
            "remain unverified caller claims on the candidate path — a holder "
            "of the editor key can still attribute an unreviewed publication "
            "to anyone — which is outside what this gate was scoped to close: "
            "the finding this entry recorded was the false professional claim, "
            "not the unverified authorship a candidate publication always "
            "carries."
        ),
    },
    ("knowledge.py", "revise_knowledge"): {
        "gate": "none",
        "local_guards": ("expected_version optimistic concurrency", "actor_kind membership", "idempotency with payload digest", "optional provenance rebind resolves only current chunks in the primary Project and retains a primary-source chunk", "Markdown and provenance rebind share one transaction", "base and resulting content/provenance snapshots are persisted in knowledge_events", "knowledge_events is append-only at the PostgreSQL layer"),
        "reviewed": (
            "The revision primitive, not an entry point: its own route, "
            "`PUT /knowledge/{knowledge_id}`, is retired and raises 410. It holds as "
            "`none` only because both live callers are themselves recorded — "
            "`knowledge_update.apply_knowledge_update`, behind the signed preview and "
            "confirmation phrase, and `apply_edit_request`, recorded above as needing "
            "the gate. Worth naming plainly: the 410 says direct revision is retired "
            "in favour of the signed routes, and the edit-request pair reaches this "
            "same function on the same editor key with no signature, no confirmation "
            "phrase and no project scope. The retirement is a property of the route, "
            "not of the module."
        ),
    },
    ("knowledge_edit_variants.py", "apply_selected_variant"): {
        "gate": "none",
        "local_guards": ("top-level transaction owns request lock before variant validation", "status and selected_variant_id checked under that lock", "variant ownership", "replacement prepared with selected_variant_id/status predicate", "request lock is retained across delegated Knowledge apply", "Knowledge revision and variant_applied audit commit inside the same outer transaction", "idempotent replay when already applied"),
        "reviewed": (
            "The consequential write remains delegated to "
            "`knowledge.apply_edit_request`, but candidate preparation is no longer "
            "a separately committed transaction. `apply_selected_variant` locks the "
            "request row first, resolves the immutable variant currently selected, "
            "prepares exactly that replacement with a selected-id/status predicate, "
            "and keeps the lock while the Knowledge owner applies it. The delegated "
            "owner may use a savepoint here because this wrapper deliberately owns "
            "the top-level transaction. A competing select/reject/apply therefore "
            "cannot change the selection between review and persistence, and the "
            "`variant_applied` event cannot name a different candidate from the "
            "Markdown that actually committed. If the delegated owner detects stale "
            "Knowledge, the wrapper catches that signal inside the outer transaction "
            "long enough to commit the owner's conflict transition, then re-raises it."
        ),
    },
    ("knowledge_edit_variants.py", "create_variant_request"): {
        "gate": "none",
        "local_guards": ("transaction owned before first database read", "status and replacement_markdown are literals in the INSERT", "locked snapshot with base_version equality", "selection range and text matched against the snapshot", "idempotency with payload digest"),
        "reviewed": (
            "The same table as `knowledge.create_edit_request`, and the "
            "instructive contrast with it: here the INSERT writes "
            "`replacement_markdown` as a literal NULL and the status as a literal "
            "`queued_for_hermes`, so this creation path cannot manufacture a "
            "`proposed` request. The shortcut recorded against the other path is "
            "not a shape the codebase lacks a fix for; it is one this module "
            "already closes."
        ),
    },
    ("knowledge_edit_variants.py", "project_execution_result_variant"): {
        "gate": "none",
        "local_guards": ("transaction owned before the Execution Result read", "status must be queued_for_hermes or proposed", "scope currency re-checked under lock", "candidate payload validated against the contract", "conflict persisted in a fresh top-level transaction after rollback", "idempotency with projection digest"),
        "reviewed": (
            "Projects a Hermes candidate and declares its authority as data: "
            "CANDIDATE_AUTHORITY sets selects_variant, applies_edit, "
            "validates_knowledge, admits_evidence, promotes_memory and "
            "authorizes_task all False. It refuses any status outside "
            "`{queued_for_hermes, proposed}`, matching the terminal-status guard "
            "now enforced by `complete_edit_request`; a rejected request cannot "
            "receive a projection or be reopened through Hermes. The "
            "staleness conflict is written in its own transaction after the "
            "attempt unwinds, so discovering it does not depend on the attempt "
            "committing."
        ),
    },
    ("knowledge_edit_variants.py", "reject_request"): {
        "gate": "none",
        "local_guards": ("transaction owned before idempotency lookup", "status must be queued_for_hermes or proposed", "row lock", "non-empty reason", "idempotency with payload digest", "event records the refusal"),
        "reviewed": (
            "Refuses an edit, which is safety-increasing, and records why. The "
            "request row is locked and only queued_for_hermes or proposed may "
            "transition to rejected. The former reopen defect is closed in "
            "`knowledge.complete_edit_request`: Hermes may complete only a request "
            "still queued_for_hermes, with a narrow identical-proposal replay "
            "exception after it is already proposed. A rejected request is now "
            "terminal on both the variant and direct proposal paths."
        ),
    },
    ("knowledge_edit_variants.py", "select_variant"): {
        "gate": "none",
        "local_guards": ("transaction owned before idempotency lookup", "status must be proposed", "row lock", "variant ownership", "idempotency with payload digest", "event records the selection"),
        "reviewed": (
            "Records the human choice between two candidates; it mutates no "
            "Knowledge and the event says so explicitly "
            "(`knowledge_mutated: False`). Both halves of the attribution it "
            "writes are unverified, though: `actor` is the "
            "`X-Pantheon-Human-Actor` header value, and `actor_kind` is a literal "
            "at the call site — as it is at every site in this module. Corrected "
            "on review: that was first written as six event writes, five `human` "
            "and one `system`, which counted `actor_kind=` matches rather than "
            "reading what each call was to. There are four `_insert_event` sites, "
            "one `system` for the projection and three `human` for selection, "
            "rejection and application; the remaining two literals are passed into "
            "`knowledge.apply_edit_request`. Six literals, four of them in the "
            "audit log. The point is unchanged and the count was not checked: the "
            "column records the kind the code path intends, never the kind of the "
            "caller observed."
        ),
    },
    ("knowledge_update.py", "apply_knowledge_update"): {
        "gate": "optional",
        "local_guards": ("signed preview", "exact confirmation phrase", "expected_version and base digest", "idempotency"),
        "reviewed": (
            "The one path with the chokepoint reachable. Its local chain is a signed preview, an exact confirmation phrase, optimistic concurrency and idempotency; the gate is opt-in and off by default, which is why the regime is optional rather than covered."
        ),
    },
    ("project_document_admission.py", "admit_source_as_revision"): {
        "gate": "none",
        "local_guards": ("explicit target document", "exact capture identity", "idempotency"),
        "reviewed": (
            "Admits a captured source as a revision of an explicitly named target document, keyed on the exact capture identity. Admission is not a currentness or authority claim, which are owned elsewhere."
        ),
    },
    ("project_document_currentness.py", "record_version_event"): {
        "gate": "none",
        "local_guards": ("refuses hermes actors outright", "refuses any consequential authority status", "refuses a system actor setting anything authoritative", "controlled vocabulary on event type, status, effect class and authority", "required actor and idempotency_key"),
        "reviewed": "The clearest case in the codebase of a path that enforces the doctrine without calling the chokepoint: it raises GovernanceGateRequired rather than deciding, so a consequential authority transition cannot pass through it at all.",
    },
    ("project_documents.py", "create_document"): {
        "gate": "none",
        "local_guards": ("_validate_actor refuses hermes with GovernanceGateRequired", "required parent project, type, title and idempotency_key", "payload digest with idempotent replay"),
        "reviewed": "Creates a document shell; authority and currentness are owned elsewhere and refused here. No runtime caller at review time.",
    },
    ("project_documents.py", "link_revision"): {
        "gate": "none",
        "local_guards": ("_validate_actor", "document row locked", "technical source version must belong to the same project", "identical source_digest reuses or conflicts on differing metadata", "version_seq computed under the document lock", "supersession: target must exist, share the document, precede the new revision, and not already have a successor", "idempotency with payload digest"),
        "reviewed": (
            "Links one technical version into a logical Project Document, and "
            "the supersession chain is where the care went: the superseded "
            "revision must exist, belong to this document, precede the new one, "
            "and not already have a successor. Four conditions to keep a chain a "
            "chain, and the last is the one a reader would forget. "
            "The concurrency is clean, which is worth recording in a review that "
            "has found the opposite repeatedly: the document row is locked "
            "first, and both the duplicate lookup and "
            "`MAX(version_seq) + 1` run under that lock, so two concurrent links "
            "cannot compute the same sequence number. `CrossProjectSource` "
            "refuses a technical version from another project scope. "
            "The finding is a silence. Relinking bytes already present returns "
            "the existing revision with `duplicate_reused` set and writes no "
            "event, so the log shows the first link and nothing about the "
            "second attempt. Nothing changed, so nothing is wrong — but the "
            "history cannot answer whether anyone tried."
        ),
    },
    ("project_documents.py", "record_issuer_reference"): {
        "gate": "none",
        "local_guards": ("_validate_actor refuses hermes with GovernanceGateRequired", "basis_kind checked against a controlled vocabulary", "opaque reference validation", "revision existence check", "payload digest with idempotent replay"),
        "reviewed": "Records an observation about a revision, not an authority claim about it.",
    },
    ("source_intake.py", "create_source"): {
        "gate": "none",
        "local_guards": ("_validate_actor", "source_kind vocabulary", "five required identity fields", "checksum must be a 64-character SHA-256 hex digest when present", "project_link_status written as the literal unassigned", "idempotency with payload digest", "UniqueViolation converted to a module error"),
        "reviewed": (
            "Admits a Source. The guard worth naming is the literal: "
            "`project_link_status` is written as `\u2019unassigned\u2019` in the INSERT, "
            "so intake cannot arrive already claiming a project no matter what "
            "the caller passes. `declared_project_name` is free text beside it "
            "and stays a declaration — the name says so, and the column that "
            "would make it a link is not reachable from here. "
            "The finding is the checksum. It is optional, and when present only "
            "its shape is checked: sixty-four hexadecimal characters. Nothing "
            "reads `raw_source_ref` to verify the digest describes those bytes. "
            "So a Source may carry no checksum at all, or a well-formed one that "
            "belongs to different content. Same axis as `observed_digest` on the "
            "Information projection: it records what the intaker said."
        ),
    },
    ("source_intake.py", "relate_contained_source"): {
        "gate": "none",
        "local_guards": ("_validate_actor", "both Sources must exist, _source_row raises", "CHECK (source_id <> target_source_id) below Python", "UNIQUE on the triple", "idempotency with payload digest"),
        "reviewed": (
            "Records that one Source contains another. Stronger than it looks "
            "from Python: `009_source_intake_admission.sql` gives "
            "`agency_source_relations` foreign keys on both ends and "
            "`CHECK (source_id <> target_source_id)`, so the self-containment "
            "this function refuses is refused again below it, where a second "
            "Python caller cannot route around it. "
            "The finding is what neither layer refuses: a cycle. A contains B and "
            "B contains A are both storable, and nothing walks the graph. "
            "Recorded rather than escalated — containment is a structural note "
            "about Sources, not governed identity, so a cycle is a data-quality "
            "defect and not an authority one. Also worth being exact: the event "
            "carries `expected_revision=0, resulting_revision=0`, so the "
            "Source\u2019s own revision does not move when a relation is added."
        ),
    },
    ("email_action_adapter.py", "archive_email_to_authorized_root"): {
        "gate": "none",
        "local_guards": (
            "production route requires the editor key and a non-empty asserted human actor",
            "production route resolves the exact destination from the producer-owned project catalogue; no client filesystem path is accepted",
            "archived-project writes require an explicit confirmation flag",
            "delegates exact RAW retention to storage_retention with the server-verified digest",
            "delegates Source creation to source_intake, which writes project_link_status=unassigned",
            "visible materialization rechecks containment below the already-authorized root and refuses traversal/symlink destinations",
        ),
        "reviewed": (
            "Composes the email archive effect after destination authorization. It is "
            "not the owner of Project identity or policy selection: the HTTP route "
            "resolves one exact active/archive filesystem target from the persisted "
            "producer catalogue before this function is called. The SQL side is the "
            "existing Storage Object plus Source owners, and the filesystem side is "
            "a derived working projection. No governed Project link, Evidence row or "
            "direct Hindsight write is created."
        ),
    },
    ("email_action_adapter.py", "retain_and_admit_raw_email"): {
        "gate": "none",
        "local_guards": (
            "NormalizedEmail carries a server-verified RAW SHA-256",
            "retain_exact_bytes rehashes the supplied bytes against that digest",
            "Source identity is deterministic from provider_account_ref + gmail_message_id",
            "source_intake.create_source is idempotency/payload-digest protected",
            "declared_project_name is null and Source intake writes project_link_status=unassigned",
        ),
        "reviewed": (
            "Creates the two durable records needed for an exact received email: a "
            "verified Storage Object and an unassigned Gmail Source. The provider "
            "message identity is kept separate from thread continuity and from the "
            "visible AFFAIRES bundle. It cannot arrive already linked to a Project."
        ),
    },
    ("storage_retention.py", "retain_exact_bytes"): {
        "gate": "none",
        "local_guards": (
            "content must be bytes",
            "SHA-256 is recomputed before staging",
            "optional expected digest must match exactly",
            "delegates to retain_exact_file through an fsync'd temporary file",
            "temporary staging is removed in finally",
        ),
        "reviewed": (
            "In-memory convenience wrapper over the same exact-byte Storage Object "
            "owner. It creates no Source, Project, document version or professional "
            "authority; its durable effect is limited to verified byte retention."
        ),
    },
    ("storage_retention.py", "retain_exact_file"): {
        "gate": "none",
        "local_guards": (
            "source path must be an existing file",
            "complete SHA-256 and byte size are computed before retention",
            "optional expected digest and size fail closed on mismatch",
            "content-addressed copy is atomically published and fully reverified",
            "Storage Object/location registration uses conflict-do-nothing plus exact read-back checks",
            "no document-version binding is created",
        ),
        "reviewed": (
            "Generalizes the pre-existing retention primitive below document-version "
            "identity. The retained object is exact byte identity only. It deliberately "
            "does not create a Source, Project Document, Evidence item or access scope."
        ),
    },
    ("storage_retention.py", "retain_document_version"): {
        "gate": "none",
        "local_guards": ("bytes verified against the recorded source_digest and byte_size before anything is stored", "object identity derived from the content digest", "every INSERT is ON CONFLICT DO NOTHING followed by a read-back and an equality check", "byte size of an existing object must match", "location must read back verified and full_sha256", "a version already bound to another Storage Object conflicts"),
        "reviewed": (
            "Retains the exact bytes of a technical document version, and it is "
            "the direct counter-example to `source_intake.create_source`. There "
            "a checksum is optional and only its shape is checked; here "
            "`_retain_exact_copy` is given `expected_digest` and `expected_size` "
            "read from the stored version and verifies the bytes against them "
            "before a row is written. The Storage Object\u2019s identity is then "
            "derived from that digest, so the row cannot name content it does "
            "not hold. "
            "The concurrency shape is a third pattern beside the row-lock "
            "compare-and-swap and the digest-bound approval this review has been "
            "tracking: it takes no locks at all. Every write is "
            "`ON CONFLICT DO NOTHING` followed by a read-back that must equal "
            "what was intended — object, byte size, location status, "
            "verification method, binding. That is sound *because* identity is "
            "the content: two racers computing the same digest are writing the "
            "same row, and a racer computing a different one fails the read-back "
            "rather than overwriting. The literals matter too — "
            "`location_status=\u2019verified\u2019` and "
            "`verification_method=\u2019full_sha256\u2019` are written by this function "
            "and then asserted back, so no caller supplies the claim that the "
            "bytes were verified. "
            "The finding is small and outside the transaction: "
            "`_retain_exact_copy` writes the copy to the retention root before "
            "`conn.transaction()` opens, so a transaction that fails afterwards "
            "leaves the file behind. Content-addressed, so the orphan is inert "
            "and a retry reuses it; it is disk, not authority."
        ),
    },
    ("store.py", "ingest"): {
        "gate": "none",
        "local_guards": ("assert_source_in_scope per source, inside the loop", "resolve_source_within contains the path under the root", "subject tags refused for sources outside this ingestion", "every chunk stamped with contract id, contract digest, ingestion id and source digest", "the DELETE is scoped to one source_digest, so other digests stay indexed", "a conversion failure records the failed extraction before re-raising", "conversions prepared outside one atomic write transaction"),
        "reviewed": (
            "The ingestion. Its perimeter guard is inside the loop, not before "
            "it — `assert_source_in_scope` runs for every source, with a comment "
            "calling it the effect boundary — and `resolve_source_within` "
            "contains the resolved path under the root, so a declared "
            "`source_ref` cannot walk out of it. Re-ingesting is idempotent "
            "without being destructive: the DELETE is scoped to "
            "`(dossier, source_ref, source_digest)`, so replaying one immutable "
            "digest refreshes only itself and older digests at the same path "
            "stay indexed for exact governed retrieval. A conversion failure "
            "records the failed extraction and then re-raises, so the capture "
            "stays truthful about what could not be read. "
            "The finding was a parameter that asserted a guard the function did "
            "not have, and it is closed. `replace_dossier` was accepted, "
            "documented as retained for API compatibility, and referenced "
            "exactly zero times in the body — while both callers passed "
            "`replace_dossier=False`, and a reader at either call site would "
            "conclude the dossier was being protected from replacement. It was "
            "protected, but by the digest-scoped DELETE. The review\u2019s own "
            "recurring shape reduced to its smallest form: a name carrying a "
            "guarantee that no code behind it provides — and it worked, in that "
            "the `intake_document` entry in this same file recorded the "
            "guarantee as real before this entry disproved it. The parameter is "
            "removed and both call sites updated. "
            "Also worth recording: `conn.commit()` runs before the write "
            "transaction opens, to end the read transaction psycopg started for "
            "the cache lookups. Documented, and the third entry point in this "
            "inventory that commits its caller\u2019s connection."
        ),
    },
    ("apu_cross_family.py", "create_decision_request"): {
        "gate": "none",
        "local_guards": ("request_id and created_by required", "APU-scoped request requires project_ref", "scope_refs immutable across a replay", "foreign key and CHECK violations on the scope insert converted to module errors", "one transaction"),
        "reviewed": (
            "Wraps `decision_requests.create_request` and adds the APU scope "
            "refs beside it. The guard worth naming is the immutability check: "
            "if the request already existed, the stored scope refs must equal "
            "the ones being replayed, or the call conflicts. A replay cannot "
            "quietly widen what a Decision Request is about. The scope insert "
            "catches `ForeignKeyViolation` and `CheckViolation` and converts "
            "them, which means the existence of what the scope points at is "
            "enforced below Python, not here. "
            "Worth being exact about the surface: everything but `request_id`, "
            "`project_ref` and `created_by` passes through `**kwargs` "
            "unexamined, so this function\u2019s own validation is those three and "
            "the scope; the rest is `create_request`\u2019s, reviewed separately."
        ),
    },
    ("entity_relations.py", "canonize_relation"): {
        "gate": "none",
        "local_guards": ("separate route with the editor key and a human actor", "actor_kind literal at the route", "_actor refuses any kind but human, no default", "relation locked", "status must be proposed", "expected_revision", "idempotency with payload digest", "a CHECK constraint refuses a non-human actor_kind on any event that is not a proposal"),
        "reviewed": (
            "The act the doctrine names, and the most layered guard in this "
            "codebase. The route is separate from the Hermes proposal route and "
            "passes `actor_kind=\"human\"` as a literal; `_actor(..., "
            "proposing=False)` accepts only `human` and has no default; and "
            "`agency_entity_relation_events_hermes_proposes_only` — "
            "`CHECK (actor_kind = 'human' OR event_type = 'relation_proposed')` — "
            "refuses to store any other event kind attributed to Hermes. "
            "Worth being exact about what that buys, because the docstring says "
            "'Hermes cannot reach this' and that is not quite the property. None "
            "of the three layers verifies that the label is true; a caller "
            "presenting `human` passes all of them. What the constraint "
            "guarantees is that the audit trail can never contain the "
            "contradiction: no row can say Hermes canonized anything. That is "
            "internal consistency of the record, which is real and rare — and it "
            "is not the same as knowing who acted. "
            "Second finding, added while reviewing `propose_relation`: this "
            "entry recorded the actor axis in detail and said nothing about the "
            "endpoints. `_decide` moves the status and checks "
            "`expected_revision`; it does not verify that either entity exists. "
            "Nor could `015_entity_relations.sql` help — the ids are "
            "polymorphic, so `from_entity_id` and `to_entity_id` carry a type "
            "CHECK and no foreign key. The act the doctrine names as making a "
            "relation true can therefore canonize an edge between two ids that "
            "name nothing. The record was not wrong here; it was incomplete, "
            "which a reader of a governance record cannot tell apart."
        ),
    },
    ("entity_relations.py", "reject_relation"): {
        "gate": "none",
        "local_guards": ("same three layers as canonize_relation", "status must be proposed", "closes the relation and frees the edge", "expected_revision", "idempotency with payload digest"),
        "reviewed": (
            "Refuses a proposal, which is safety-increasing, and shares "
            "`_decide` with canonization and retirement so the optimistic lock, "
            "the replay check and the audit record are identical across all "
            "three. The source says why that matters: a reader of the history is "
            "entitled to assume the three decisions were recorded the same way."
        ),
    },
    ("entity_relations.py", "retire_relation"): {
        "gate": "none",
        "local_guards": ("same three layers as canonize_relation", "status must be canonical", "retires rather than deletes", "records retired_by and retired_at", "expected_revision", "idempotency with payload digest"),
        "reviewed": (
            "Withdraws a relation that had been made canonical. It moves the row "
            "to `retired` and stamps `retired_by`, rather than deleting: the "
            "relation that was once true stays readable as having been true and "
            "withdrawn."
        ),
    },
    ("hermes_runtime_return.py", "record_external_runtime_return"): {
        "gate": "none",
        "local_guards": ("run joined to this admission, not merely to this run_id", "normalized return shape", "outcome and payload must correspond, in both directions", "trace summary validated against the persisted run", "Work Issue version, on the running path", "candidate source_refs bounded by the admitted Context Pack", "replay must match the stored return exactly", "one transaction", "the return enumerates what did not happen"),
        "reviewed": (
            "The Hermes boundary itself: the point where an external runtime\u2019s "
            "output enters governed state, and the most guarded intake in the "
            "inventory. Three of its guards are worth naming precisely. "
            "`_run_for_admission` joins `r.admission_ref = %s`, so a run "
            "belonging to another admission is refused rather than a wrong "
            "run_id merely missing. The outcome/payload correspondence is "
            "checked in both directions — a `result_candidate` without the "
            "outcome and the outcome without the payload both raise. And "
            "`_validate_candidate_sources` bounds what comes back by what went "
            "out: `returned - admitted` must be empty against the Context Pack, "
            "so Hermes cannot cite a source it was not given. The return value "
            "then states the non-equivalences as data — `evidence_admitted`, "
            "`external_effect_authorized` and `project_mutated` all False. "
            "The finding is a guard narrower than its name. The Work Issue "
            "version check reads `if issue[\"version\"] != expected_issue_version "
            "and run[\"status\"] == \"running\"`, so a stale expected version is "
            "not refused on the replay path. That path has its own stricter "
            "check — the stored normalized return must equal the one being "
            "replayed — so this is defensible; recording it flatly as "
            "optimistic concurrency would not be. The actor is `actor.strip()`, "
            "unverified, as everywhere."
        ),
    },
    ("source_intake.py", "exclude_source"): {
        "gate": "none",
        "local_guards": ("actor_kind required, no default, Hermes refused by name", "row lock", "expected_revision checked on the read and repeated in the UPDATE WHERE", "rowcount == 1", "idempotency with payload digest", "event carries a result snapshot", "reversible by restore_source"),
        "reviewed": (
            "Marks a Source excluded from project work. It withdraws material "
            "from consideration rather than admitting any, and it is reversible: "
            "`restore_source` exists and refuses anything that is not excluded. "
            "The row is not deleted and the exclusion is an event."
        ),
    },
    ("source_intake.py", "link_project"): {
        "gate": "none",
        "local_guards": ("actor_kind required, no default, Hermes refused by name", "row lock", "expected_revision checked on the read and repeated in the UPDATE WHERE", "rowcount == 1", "idempotency with payload digest", "event carries a result snapshot", "link status set alongside the project id"),
        "reviewed": (
            "Attaches a Source to a Project. `workspace folder != governed "
            "identity` is the neighbouring invariant and it holds here too: a "
            "link says which Project a Source belongs to, not that anything in it "
            "has been admitted."
        ),
    },
    ("source_intake.py", "restore_source"): {
        "gate": "none",
        "local_guards": ("actor_kind required, no default, Hermes refused by name", "row lock", "expected_revision checked on the read and repeated in the UPDATE WHERE", "rowcount == 1", "idempotency with payload digest", "event carries a result snapshot", "refuses any Source that is not excluded", "restores to unassigned, not to the previous project"),
        "reviewed": (
            "Undoes an exclusion. Worth noting what it does not do: it returns "
            "the Source to `unassigned` with a null project, not to whatever "
            "project it had before. Restoring does not re-establish a link that "
            "a human has to make again."
        ),
    },
    ("source_intake.py", "suggest_projects"): {
        "gate": "none",
        "local_guards": ("actor_kind required, no default, Hermes refused by name", "row lock", "expected_revision checked on the read and repeated in the UPDATE WHERE", "rowcount == 1", "idempotency with payload digest", "event carries a result snapshot", "refuses a Source that is still linked", "every candidate Project must exist", "at least one candidate required"),
        "reviewed": (
            "Corrected on review, and the first version was the inverse of the "
            "truth. It said the suggestion lands in its own column and does not "
            "touch `project_id` or `project_link_status`. The assignment dict "
            "reads `{\"candidate_project_refs\": ..., \"project_link_status\": "
            "\"suggested\", \"project_id\": None}` — so suggesting on a Source "
            "that is already linked **unlinks it**, and nothing refuses that or "
            "asks for it. A suggestion cannot become a link by being written, "
            "which is what I meant; what it could do was remove one. Closed in "
            "2222a020: a Source whose `project_link_status` is `linked`, or "
            "whose `project_id` is set, is refused outright — an explicit "
            "unlink is now required first. A suggestion can no longer change a "
            "link in either direction. Candidate Projects are checked to exist "
            "before the write."
        ),
    },
    ("source_intake.py", "unlink_project"): {
        "gate": "none",
        "local_guards": ("actor_kind required, no default, Hermes refused by name", "row lock", "expected_revision checked on the read and repeated in the UPDATE WHERE", "rowcount == 1", "idempotency with payload digest", "event carries a result snapshot", "clears the project id and the link status together"),
        "reviewed": (
            "Detaches a Source from its Project, clearing `project_id` and "
            "setting `project_link_status` to `unassigned` in the same "
            "assignment, so the two cannot disagree."
        ),
    },
    ("source_intake.py", "update_metadata"): {
        "gate": "none",
        "local_guards": ("actor_kind required, no default, Hermes refused by name", "row lock", "expected_revision checked on the read and repeated in the UPDATE WHERE", "rowcount == 1", "idempotency with payload digest", "event carries a result snapshot", "field allowlist checked against METADATA_FIELDS", "at least one change required", "checksum must be a 64-character hexadecimal digest"),
        "reviewed": (
            "Edits Source metadata behind a real allowlist — unknown fields are "
            "named in the error rather than silently dropped — and validates a "
            "supplied checksum as a SHA-256 digest by length and alphabet. That "
            "is a format check, not a verification: nothing recomputes the digest "
            "from the bytes, so it records what the intaker asserted. The field "
            "is named `checksum` rather than something that claims verification, "
            "which is the naming this review has twice recorded the absence of."
        ),
    },
    ("apu_mapping_converter.py", "convert_and_store"): {
        "gate": "none",
        "local_guards": ("reads an existing Execution Result", "derives the candidate rather than accepting one", "storage guards inherited from store_execution_result"),
        "reviewed": (
            "Fourteen lines: read an Execution Result, derive a mapping candidate "
            "from it, store that as another Execution Result. It accepts no "
            "payload, so nothing a caller supplies reaches the stored candidate "
            "except the two refs, and every storage guard is "
            "`execution_results.store_execution_result`\u2019s. "
            "The finding is what it does not carry: the module contains no "
            "occurrence of `actor`, `actor_kind` or any producer field. A "
            "conversion records nobody. That reads as harmless — a derivation "
            "makes no new claim — until it is followed: the mapping result this "
            "writes is what `prepare_write_command` reads to build a command, "
            "and that command is what a human later authorizes into canonical "
            "APU state. Nothing in that chain can say who converted."
        ),
    },
    ("cli.py", "main"): {
        "gate": "none",
        "local_guards": ("argparse required arguments", "each subcommand delegates to a module that carries the real guards", "no guard of its own"),
        "reviewed": (
            "An argparse dispatcher. It holds no guard of its own — every "
            "check belongs to what it calls: `store.ingest`, "
            "`store.intake_document`, "
            "`storage_retention.retain_document_version`, and the file-writing "
            "`decide` and `register` subcommands. Discovery caught it because a "
            "write is reachable through the dispatch, which is correct and "
            "worth keeping rather than filtering out. "
            "What the entry is for is the thing every other entry lets pass "
            "unstated: this is the one mutation path in the inventory that no "
            "route protects. It opens its own connection with "
            "`store.connect()` / `storage_retention.connect()` and asks for no "
            "editor key, no Hermes key and no principal. Shell access and "
            "database credentials are the whole admission check. That is what a "
            "CLI is, and it is not a defect — but the sentence \"the write "
            "surface is behind an API key\" is a claim about the routes, and "
            "this record should not let it read as a claim about the system."
        ),
    },
    ("human_revision_upload.py", "upload_revision"): {
        "gate": "none",
        "local_guards": ("three require_access checks against a real principal: project.read, document.read, document.revision.submit", "document must belong to the requested Project", "stream bounded by max_bytes", "checksum computed from the bytes and passed down, not declared", "actor_kind literal human throughout", "the three access checks re-run after conversion and retention", "the returned authority block states what was and was not done"),
        "reviewed": (
            "The only entry point in this inventory that authorizes a named "
            "principal rather than a shared key. Three `require_access` checks "
            "— `project.read`, `document.read`, `document.revision.submit` — "
            "then a scope check that the Document belongs to the Project asked "
            "for. Everywhere else in this review the actor is a header value "
            "nobody verified; here there is a principal and a grant. "
            "It also closes, in composition, the finding recorded against "
            "`source_intake.create_source`. That function accepts a declared "
            "checksum and only checks its shape; this caller computes the digest "
            "from the bytes it just published and passes that. The module-level "
            "gap is real and this path does not walk into it. "
            "Two deliberate choices are documented in the code and worth "
            "recording as choices rather than defects. The filesystem and "
            "database stages are explicitly not one transaction — "
            "`conn.commit()` twice, `conn.rollback()` on failure — because a "
            "preserved Source and an exact technical capture stay truthful even "
            "if analysis fails afterwards. And the three access checks are run "
            "again after conversion and retention, with the reason beside them: "
            "access revoked during a long conversion should stop professional "
            "admission without erasing intake stages that already happened. "
            "That is the opposite decision from the APU application repair — "
            "there the window between the check and the act was closed with a "
            "lock; here it is left open on purpose and re-checked at the end, "
            "because the stages in between are meant to survive. Both are "
            "right, and the difference is what each window costs."
        ),
    },
    ("project_change_variants.py", "select_variant_for_change_candidate"): {
        "gate": "none",
        "local_guards": ("execution result row locked FOR UPDATE, shared by every sibling variant", "result_kind and schema_ref must be canonical", "payload validated against the canonical variant contract", "execution and variant must name the same Project", "sibling scope validated", "a sibling already selected in this request scope conflicts", "Project revision must equal the variant base_revision", "reviewer_kind and proposer_kind literals", "UniqueViolation converted to the scope conflict"),
        "reviewed": (
            "Selects one variant out of a set and turns it into a "
            "ChangeCandidate. The lock is the design: `FOR UPDATE` on the "
            "*execution result* row, not on the item, so every sibling variant "
            "of one execution contends on the same row — which is what makes "
            "`_candidate_for_scope` meaningful, since two concurrent selections "
            "of different siblings cannot both pass a check that only one may "
            "pass. The comment says so beside the code. Second place in this "
            "inventory where the lock ordering is both right and explained. "
            "It also converts `UniqueViolation` into "
            "`ProjectChangeVariantConflict`, which sharpens a finding recorded "
            "twice elsewhere in this batch: `agency_data.create_project` and "
            "`contradictory_review_store.persist_candidate` let the same "
            "exception escape raw. The repository knows how to close that "
            "surface. It is not that the pattern is unknown; it is that it is "
            "applied unevenly. "
            "The finding was a defect in the replay branch, and it is "
            "repaired:\n"
            "    _selection_row(conn, replayed[\"source_review_disposition_id\"] "
            "and selection_key)\n"
            "`_selection_row` looked a disposition up by `idempotency_key`, so "
            "the expression tested the stored disposition id, discarded it, and "
            "passed this call\u2019s `selection_key` instead — correct only when a "
            "replay reused the original key. `_candidate_for_source` matches on "
            "`source_result_id`, so a second call for the same result with a "
            "different key reached this branch, found no row under "
            "`{new_key}:selection`, and raised `variant selection disposition "
            "was not retained` about a disposition that exists. The falsy branch "
            "reached the same error through `idempotency_key = NULL`. "
            "`_selection_row_by_id` now looks it up by the id the candidate row "
            "already carries, and refuses a candidate with no disposition rather "
            "than querying on NULL."
        ),
    },
    ("project_claim_candidates.py", "create_claim_from_candidate"): {
        "gate": "none",
        "local_guards": ("candidate row locked FOR UPDATE before the existing-Claim lookup", "execution project_ref must equal the candidate payload project_ref", "_validate_candidate_unit", "backing ref selected against the project", "source_backed and verified both require a selected basis_ref", "candidate_ref carries the review disposition", "delegates to record_claim, whose errors are converted"),
        "reviewed": (
            "Turns a reviewed candidate into a ProjectClaim, and it is the "
            "counter-example this inventory needed. The APU application path "
            "read its decision outside the transaction that acted, and was "
            "repaired in this repository; this function had the same problem to "
            "solve and solved it, with the reasoning in a comment beside the "
            "code: it takes `FOR UPDATE` on the candidate row first, and only "
            "then looks for an existing Claim, because under READ COMMITTED the "
            "second statement takes a fresh snapshot and therefore sees a Claim "
            "committed while this transaction was waiting on the lock. Lock, "
            "then read the decision under it. Same repository, same class of "
            "problem, done right and written down. "
            "It also fits the guard `b201a019` added downstream: it supplies "
            "`candidate_ref` with the `review_disposition_id` that "
            "`record_claim` now requires before it will store `verified`. "
            "The finding is what it does not police. `status` and `certainty` "
            "are caller-supplied and pass through: only two status values earn "
            "a local check here — `source_backed` and `verified` must have a "
            "selected basis_ref — and the vocabulary itself is `record_claim`\u2019s "
            "to enforce, not this function\u2019s. `certainty` defaults to the "
            "payload\u2019s and can be overridden by the caller with anything "
            "non-empty."
        ),
    },
    ("store.py", "intake_document"): {
        "gate": "none",
        "local_guards": ("assert_source_in_scope before anything else", "parse_document_name", "delegates a single source"),
        "reviewed": (
            "A scoping wrapper over `ingest`, and the order matters: "
            "`assert_source_in_scope(contract, source_ref)` is the first "
            "statement, so a path outside the Task Contract perimeter never "
            "reaches the ingestion. It then delegates with exactly one source. "
            "Every other guard is `ingest`\u2019s. "
            "Corrected on review, and the correction is the finding. This entry "
            "read that it delegates with `replace_dossier=False`, \"which is "
            "what keeps a single-document intake from clearing the dossier it "
            "lands in\" — a guarantee taken from the flag\u2019s name at the call "
            "site. The next entry read `ingest` and found the parameter was "
            "never referenced in its body. So this record carried the finding "
            "and the belief the finding falsifies, in one file, written the "
            "same day. The flag is now removed and the protection named where "
            "it actually lives: the DELETE is scoped to one `source_digest`."
        ),
    },
    ("work_issue_scopes.py", "create_scoped_issue"): {
        "gate": "none",
        "local_guards": ("at least one scope", "exactly one primary scope", "duplicate endpoints refused", "scope vocabularies", "issue and every scope written in one transaction", "idempotency", "scope endpoints validated by a trigger"),
        "reviewed": (
            "Found only after the discovery closure was made transitive: it "
            "delegates to `work_issues.create_issue` and `add_scope`, both "
            "public and one of them in another module, so the one-hop signal "
            "never saw it — and it is the entry point of `POST /work/issues`. "
            "The composition is what it should be: the issue and all its scopes "
            "commit together, exactly one scope is primary, duplicate endpoints "
            "are refused, and the two functions it calls carry their own "
            "reviewed guards."
        ),
    },
    ("work_issue_scopes.py", "add_scope"): {
        "gate": "none",
        "local_guards": ("scope type and role vocabularies", "issue locked", "expected_version", "idempotency keyed on event type and payload", "event records the link"),
        "reviewed": (
            "Records which entities a Work Issue concerns. A scope link says what "
            "the issue is about; it grants nothing and admits nothing. The "
            "entity_type and scope_role vocabularies are closed frozensets and the "
            "endpoint is validated by a database trigger — "
            "`validate_work_issue_scope_endpoint` refuses an unknown project or "
            "decision reference, so a dangling scope cannot be stored even by a "
            "caller that skips this module."
        ),
    },
    ("work_issue_scopes.py", "replace_primary_scope"): {
        "gate": "none",
        "local_guards": ("replacement normalized to the primary role", "issue locked", "expected_version", "retire and add in one transaction", "idempotency with payload digest"),
        "reviewed": (
            "Swaps the primary scope in one transaction, so an issue is never left "
            "without one or holding two. The replacement's role is a literal "
            "`primary` inside the function, not a caller argument."
        ),
    },
    ("work_issue_scopes.py", "retire_scope"): {
        "gate": "none",
        "local_guards": ("issue locked", "expected_version", "idempotency keyed on event type and payload", "retirement rather than deletion, enforced by a trigger"),
        "reviewed": (
            "Withdraws a scope link. It retires rather than deletes, and that is "
            "not a convention this function is trusted to keep: "
            "`guard_work_issue_scope_link_mutation` refuses the DELETE outright — "
            "'WorkIssue scope links are retained; retire instead of deleting'. "
            "Third guard in this review enforced below Python."
        ),
    },
    ("work_issues.py", "add_comment"): {
        "gate": "none",
        "local_guards": ("idempotency replay", "row lock", "optimistic expected_version check", "event trail recording the author"),
        "reviewed": "A comment on a Work Issue is not a professional effect; the concurrency and trail guarantees are the right level for it.",
    },
    ("work_issues.py", "close_issue"): {
        "gate": "none",
        "local_guards": ("to_status and actor_kind are literals inside the function", "issue locked", "expected_version", "ALLOWED_TRANSITIONS confines done to review", "close_reason required", "idempotency"),
        "reviewed": (
            "Newly discovered by the delegation signal added in this batch. It is "
            "the only path to `done`, and it does not take the target from its "
            "caller: `to_status=\"done\"` and `actor_kind=\"human\"` are literals in "
            "the body, and `ALLOWED_TRANSITIONS` permits `done` only out of "
            "`review`. Its route adds the editor key and a human actor."
        ),
    },
    ("work_issues.py", "create_issue"): {
        "gate": "none",
        "local_guards": ("origin and status are literals in the INSERT", "requested_effect constrained by a SQL CHECK", "idempotency", "event records the creator"),
        "reviewed": (
            "Creates an open issue: `origin` is a literal `'human'` and `status` a "
            "literal `'open'` in the INSERT, so neither can be asked for. "
            "`requested_effect` is caller-supplied and this module does not check "
            "it — the column's CHECK constraint does, against the five permitted "
            "effects. That matters more than it looks: `hermes_execution."
            "admit_handoff` refuses anything but `read_only`, reading this column, "
            "so the constraint that bounds the whole Hermes boundary is enforced "
            "in SQL rather than here."
        ),
    },
    ("work_issues.py", "record_hermes_return"): {
        "gate": "none",
        "local_guards": ("outcome vocabulary", "summary and trace_refs required", "run must be the issue's own running run, locked", "target status derived from a table, not from the caller", "expected_version", "idempotency"),
        "reviewed": (
            "Where Hermes reports what it produced — and the clearest expression "
            "in this codebase of what Hermes may not do. The caller names an "
            "outcome; the resulting issue status is looked up in "
            "`RETURN_TO_ISSUE_STATUS`, whose whole range is `review` and "
            "`waiting`. Hermes cannot name `done` because it never names a status "
            "at all. The run must exist, belong to this issue and be `running`, "
            "read `FOR UPDATE`."
        ),
    },
    ("work_issues.py", "start_hermes_run"): {
        "gate": "none",
        "local_guards": ("issue must be assigned to hermes", "Task Contract and Context Pack must match the issue's", "status must be open or waiting", "requested_effect copied from the governed row", "expected_version", "idempotency"),
        "reviewed": (
            "The counterpart to `hermes_execution.record_external_runtime_start`. "
            "Its refusals compare the caller's Task Contract and Context Pack refs "
            "against the issue's own, and the run's `requested_effect` is copied "
            "from `issue[\"requested_effect\"]` rather than taken as an argument — "
            "so the bound on what the run may do comes from the governed row, not "
            "from whoever starts it. `actor_kind` is a literal `hermes`."
        ),
    },
    ("work_issues.py", "transition_issue"): {
        "gate": "none",
        "local_guards": ("issue locked", "ALLOWED_TRANSITIONS", "expected_version", "idempotency"),
        "reviewed": (
            "Newly discovered by the delegation signal added in this batch, and "
            "the one that most deserved finding: it takes both `to_status` and "
            "`actor_kind` from its caller, and it is how an issue moves. Its sole "
            "production route passes `to_status=\"in_progress\"` and "
            "`actor_kind=\"human\"` as literals behind the editor key and a human "
            "actor, and `ALLOWED_TRANSITIONS` refuses any move the state machine "
            "does not permit. Route-borne again: a second caller would choose both "
            "values freely, within the state machine."
        ),
    },
}


def _writes_durable_state(node: ast.AST) -> bool:
    return any(
        isinstance(child, ast.Constant)
        and isinstance(child.value, str)
        and SQL_WRITE.search(child.value)
        for child in ast.walk(node)
    )


def _own_calls(node: ast.AST) -> tuple[set[str], set[tuple[str, str]]]:
    """This function's own calls: bare names and `module.attr`, nested defs excluded.

    Excluding nested bodies is what separates a delegator from a wiring
    function. `install_*_routes` and `create_app` *define* route handlers that
    call writers; they do not call them. Walking into those bodies made every
    installer in the package look like a mutation entry point — eighteen of
    them — which is the opposite failure to the one this signal was added for,
    and just as useless.
    """
    bare: set[str] = set()
    qualified: set[tuple[str, str]] = set()
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name):
                bare.add(func.id)
            elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                qualified.add((func.value.id, func.attr))
        stack.extend(ast.iter_child_nodes(child))
    return bare, qualified


def _module_functions() -> dict[str, dict[str, ast.AST]]:
    """Every module-level function under mvp_vertical, keyed by module stem."""
    out: dict[str, dict[str, ast.AST]] = {}
    for path in sorted(MVP.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        out[path.stem] = {
            node.name: node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
    return out


def _writer_closure(modules: dict[str, dict[str, ast.AST]]) -> set[tuple[str, str]]:
    """(module, function) pairs that write, directly or through any call chain.

    A first version of this intersected each function's calls with *private*
    helpers in its own module. That missed `create_scoped_issue`, the entry
    point of a live route, because it delegates to two *public* functions in
    another module. Discovery is not a one-hop question: a mutation entry point
    is any public function from which a write is reachable, however many named
    functions lie between it and the SQL.
    """
    writers = {
        (mod, name)
        for mod, funcs in modules.items()
        for name, node in funcs.items()
        if _writes_durable_state(node)
    }
    changed = True
    while changed:
        changed = False
        for mod, funcs in modules.items():
            for name, node in funcs.items():
                if (mod, name) in writers:
                    continue
                bare, qualified = _own_calls(node)
                if any((mod, callee) in writers for callee in bare) or any(
                    (other, attr) in writers for other, attr in qualified
                ):
                    writers.add((mod, name))
                    changed = True
    return writers


def _discovered() -> set[tuple[str, str]]:
    """Return every public mutation entry point the net can see under mvp_vertical."""
    modules = _module_functions()
    writers = _writer_closure(modules)
    found: set[tuple[str, str]] = set()
    for path in sorted(MVP.rglob("*.py")):
        for name in modules[path.stem]:
            if name.startswith("_"):
                continue
            by_verb = name.split("_")[0] in MUTATION_PREFIXES
            if by_verb or (path.stem, name) in writers:
                found.add((str(path.relative_to(MVP)), name))
    return found



def test_every_mutation_entry_point_is_declared() -> None:
    undeclared = sorted(_discovered() - set(INVENTORY))
    assert not undeclared, (
        "a consequential mutation entry point exists without a declared guard "
        "regime; add it to INVENTORY with the guard it actually performs "
        f"(_UNREVIEWED is an honest answer, silence is not): {undeclared}"
    )


def test_the_inventory_does_not_describe_functions_that_no_longer_exist() -> None:
    stale = sorted(set(INVENTORY) - _discovered())
    assert not stale, f"INVENTORY describes entry points that were removed or renamed: {stale}"


def test_both_discovery_signals_carry_weight() -> None:
    """Neither signal alone would enumerate the surface.

    The structural signal misses entry points that delegate their write; the verb
    signal misses writers named outside the verb list. Dropping either would
    silently shrink what this guard sees, so both are asserted to still matter.
    """
    verb_only, sql_only = set(), set()
    for path in sorted(MVP.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_"):
                continue
            key = (str(path.relative_to(MVP)), node.name)
            by_verb = node.name.split("_")[0] in MUTATION_PREFIXES
            by_sql = _writes_durable_state(node)
            if by_verb and not by_sql:
                verb_only.add(key)
            elif by_sql and not by_verb:
                sql_only.add(key)

    assert verb_only, "no delegating entry point found; the verb signal has stopped earning its place"
    assert sql_only, "no direct writer found outside the verb list; the structural signal has stopped earning its place"


GATE_REGIMES = {
    "enforce_consequential",
    "optional",
    "none",
    "gate_required_not_wired",
    "unreviewed",
}


def test_every_declared_entry_point_states_a_guard_regime() -> None:
    for key, record in INVENTORY.items():
        assert record["gate"] in GATE_REGIMES, key
        if record["gate"] == "unreviewed":
            assert record["local_guards"] is None, (
                f"{key} is recorded as unreviewed but names local guards; either it was "
                "reviewed, or the guards are a guess"
            )
        else:
            assert record["local_guards"], (
                f"{key} declares no guard at all; a reviewed mutation path must state what "
                "protects it, even when the central chokepoint is not invoked"
            )


def test_a_reviewed_entry_records_why_it_was_cleared() -> None:
    """A verdict without a reason is not a review.

    `none` is the easiest value to write and the hardest to audit later. Requiring
    the reasoning keeps it from becoming the default a future reader cannot
    distinguish from a shrug.
    """
    for key, record in INVENTORY.items():
        if record["gate"] == "unreviewed":
            continue
        assert record.get("reviewed"), (
            f"{key} carries a verdict with no recorded reasoning; say what was read "
            "and why the regime is right"
        )


def test_a_required_gate_that_is_not_wired_stays_visible_and_does_not_grow() -> None:
    """A path known to need the chokepoint, recorded rather than quietly deferred.

    This is the honest state for an effect whose review concluded it is
    consequential while nothing routes it through the gate. It is not the same as
    `none`, and collapsing the two would lose the only record that the decision
    was ever taken.
    """
    pending = [key for key, record in INVENTORY.items() if record["gate"] == "gate_required_not_wired"]
    assert len(pending) <= 0, (
        f"{len(pending)} entry points are known to need the chokepoint and do not reach "
        "it; the ceiling is 0. Wire it, or move the ceiling deliberately and say why."
    )


def test_the_unreviewed_debt_is_visible_and_does_not_grow() -> None:
    """Enumerated is not reviewed, and the gap is now closed rather than bounded.

    The widened net enumerated 64 entry points that had not been read
    individually. The net was widened in the tenth batch and found 13 more, so
    the enumerated total is 92, and all 92 have now been read. Reviewing one
    means replacing `_UNREVIEWED` with its real guard regime and the reasoning
    behind it.

    The ceiling is 0, which changes what this test is for. It was a bound on a
    shrinking backlog; it is now the rule that a new mutation entry point is
    read when it is added, not after. Raising it is a decision someone has to
    take deliberately and say why.
    """
    unreviewed = [key for key, record in INVENTORY.items() if record["gate"] == "unreviewed"]
    assert not unreviewed, (
        f"{len(unreviewed)} entry points are unreviewed: {sorted(unreviewed)}. Every "
        "enumerated entry point has been read; a new one is reviewed when it is "
        "added, not added to a backlog."
    )



def _gate_closure(modules: dict[str, dict[str, ast.AST]]) -> set[tuple[str, str]]:
    """(module, function) pairs from which `enforce_consequential` is reachable.

    The mirror of `_writer_closure`, and asked for the opposite reason: that one
    finds the functions that write, this one finds the functions that are gated.
    A pending verdict is a claim that a given entry point is in the first set and
    not in this one, so this is what makes the claim checkable.
    """
    reached: set[tuple[str, str]] = set()
    changed = True
    while changed:
        changed = False
        for mod, funcs in modules.items():
            for name, node in funcs.items():
                if (mod, name) in reached:
                    continue
                bare, qualified = _own_calls(node)
                if (
                    "enforce_consequential" in bare
                    or any(attr == "enforce_consequential" for _, attr in qualified)
                    or any((mod, callee) in reached for callee in bare)
                    or any((other, attr) in reached for other, attr in qualified)
                ):
                    reached.add((mod, name))
                    changed = True
    return reached


def _normalized_function(module_file: str, function: str) -> str | None:
    """The function as the parser sees it: formatting and comments removed.

    `ast.unparse` is what makes the digest below usable. Re-wrapping a line or
    rewriting a comment leaves it unchanged; changing what the function does
    does not.
    """
    tree = ast.parse((MVP / module_file).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function:
            return ast.unparse(node)
    return None


def test_a_pending_gate_is_still_absent_from_the_code_it_names() -> None:
    """A verdict is bound to a content, not to a name.

    Four entries in this inventory went stale within a day. `revoke_grant`,
    `record_claim` and `resolve_request` had their gaps closed in code while
    their records still read `gate_required_not_wired`, and the entries for
    `suggest_projects` and the Information projection still described defects
    that had been repaired. Every test here passed throughout, because they
    check that each entry point is declared and never that the declaration is
    still true.

    That is the failure this inventory exists to record, committed by the
    inventory. The repair is the pattern the review found in
    `apu_write_preparation.append_authorization` and recommended everywhere
    else: bind the record to the thing it describes.

    The first version of this test bound each verdict to a literal fragment the
    entry point contains, and got the polarity wrong. `gate_required_not_wired`
    is a claim about what the code does *not* do, and a fragment the function
    keeps — its `def` line, a parameter name, a check it already performs —
    survives the repair. Wiring the gate into `bind_oidc_identity` would have
    left `def bind_oidc_identity(` exactly where it was and this test green:
    the anchor proved the function still existed, which was never in doubt.
    That is the same mistake the review kept finding in the code — a guard
    asserted from what something is named rather than from what it composes to
    — committed one more time, in the test written to stop it.

    So assert the absence instead, twice over. The gate must still not be
    reachable from the entry point, which fails the moment someone wires it.
    And the function's body, normalized through the parser, must still digest to
    what was read when the verdict was taken, which fails for a repair made by
    any other means — validating the `review_ref`, guarding the status, taking
    the actor. Either failure asks the same question: this was recorded as
    unguarded, the code has moved, is the verdict still true?

    A body that moves for an unrelated reason is a false alarm, and that is the
    intended cost: re-reading six known-defective functions is cheaper than a
    governance record nobody can trust.
    """
    gated = _gate_closure(_module_functions())
    for key, record in INVENTORY.items():
        module_file, function = key
        if record["gate"] != "gate_required_not_wired":
            assert "unguarded_body" not in record, (
                f"{key} carries an unguarded-body digest without a pending gate; "
                "drop it or restore the regime"
            )
            continue

        digest = record.get("unguarded_body")
        assert digest, (
            f"{key} is recorded as needing the chokepoint without pinning the "
            "body that makes it so; record the digest of the function as read"
        )

        stem = Path(module_file).stem
        assert (stem, function) not in gated, (
            f"{key} is recorded as gate_required_not_wired, but "
            "`enforce_consequential` is now reachable from it. The gap was "
            "closed and the verdict is stale: re-read the entry point and "
            "record what it is now."
        )

        source = _normalized_function(module_file, function)
        assert source is not None, (
            f"{key} is recorded as gate_required_not_wired, but the function is "
            "gone. Either it was removed or it was renamed; say which."
        )
        current = hashlib.sha256(source.encode("utf-8")).hexdigest()
        assert current == digest, (
            f"{key} is recorded as gate_required_not_wired against a body that "
            f"has since changed:\n    recorded {digest}\n    current  {current}\n"
            "Re-read the entry point. If the gap is closed, replace the verdict; "
            "if it is not, re-pin the digest and say in `reviewed` what moved."
        )


def test_discovery_is_not_vacuous() -> None:
    assert len(_discovered()) >= 91


def _claimed_covered() -> set[tuple[str, str]]:
    return {key for key, record in INVENTORY.items() if record["gate"] == "enforce_consequential"}


def test_a_coverage_claim_requires_a_client_that_can_exist() -> None:
    """No entry point may claim a call that nothing can reach."""
    sources = "\n".join(path.read_text(encoding="utf-8") for path in MVP.rglob("*.py"))
    if "HttpPolicyClient(" not in sources:
        assert not _claimed_covered(), (
            "an entry point claims it routes through the chokepoint while "
            f"HttpPolicyClient is never instantiated: {sorted(_claimed_covered())}"
        )


def test_a_coverage_claim_is_backed_by_a_real_call() -> None:
    """A claim of coverage is checked against the entry point, not its module.

    The first version asked whether the *module* contained the string
    `enforce_consequential(`. That is the polarity error `Pantheon-Next#928` fixed on the
    pending side, made on the covered side: a module can gate one function and
    leave the neighbour beside it ungated, and this would have called both
    covered. `_gate_closure` already answers the real question — it is the same
    walk `_writer_closure` does, seeded on the gate — so ask it.
    """
    gated = _gate_closure(_module_functions())
    for module, function in sorted(_claimed_covered()):
        assert (Path(module).stem, function) in gated, (
            f"{module}::{function} is recorded as routing through the "
            "chokepoint, but `enforce_consequential` is not reachable from it. "
            "Either the call was removed, or it sits in a neighbour and this "
            "entry point never had it."
        )
