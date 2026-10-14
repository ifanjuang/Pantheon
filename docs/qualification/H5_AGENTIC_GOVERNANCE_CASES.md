# H5 — Agentic capability, execution and governance qualification cases

Status: H5 qualification support — non-authoritative scenario corpus.
Parent: Pantheon-Next#607.

These cases extend H5 with failure modes observed in real agentic systems. They do not introduce new Pantheon states or owners by themselves. Each case must first be represented using existing provenance, temporal context, scopes, Evidence boundaries, approvals, Capability Slots, bindings and execution states. A schema extension is justified only when a case cannot be represented truthfully without semantic collapse.

## Existing boundaries reused

The active doctrine already requires, among others:

```text
installed != approved
healthy != safe
binding_selected != dependency_adopted
runtime_success != Evidence
capability_visible != capability_enabled
sandbox_enabled != production_approved
update_available != update_authorized
trace_record != proof
```

The Hermes run junction additionally preserves distributed ambiguity:

```text
submission_unknown != retry instruction
registration_unknown != queue item
inconclusive != pass
Hermes completed != Evidence
```

## Qualification cases

### Disponible ≠ approuvé

A skill may be discovered, installed, healthy and technically executable while remaining unavailable for governed task execution until the required governance posture and scope are satisfied.

Expected representation: binding/install/health/activation state + governance gate. No approval inference from installation or health.

### Approuvé ≠ compatible avec l’environnement courant

Historical approval of a skill version remains valid in its original context, while the current candidate binding may be ineligible because worker OS, GUI, network, credentials or other execution requirements are not satisfied.

Expected representation: immutable/historical approval context + current compatibility/qualification observation. Do not revoke history merely because the current environment is incompatible.

### Compatible ≠ adopté

Satisfying a Capability Slot makes a binding a candidate. It does not make the external dependency adopted or production-selected.

Expected representation: capability compatibility/coverage + binding candidate posture, distinct from dependency adoption.

### Succès répétés ≠ Evidence

Repeated successful runtime observations may improve operational qualification and produce metrics/provenance, but never become métier Evidence or human validation by accumulation.

### Succès technique ≠ résultat valide

Hermes and its tools may complete successfully while the returned content is incorrect, incomplete or irrelevant.

Expected representation: successful runtime status + candidate result + unresolved/rejected review posture. No Evidence or professional validity inference.

### Timeout du demandeur ≠ état distant connu

A local caller timeout while an external worker may still run is a distributed-ambiguity condition.

Expected representation: local timeout/unknown submission or reconciliation posture, preserving known remote identifiers when available. No automatic terminal remote failure and no automatic retry.

### Résultat tardif après annulation

A remote result may arrive after task/admission cancellation or expiry.

Expected representation: immutable late runtime event/result provenance. It must not reactivate the task, renew admission, alter prior authorization or create a new effect permission.

### Nouvelle révision ≠ approbation héritée

A new skill/artifact revision preserves lineage to the previous approved revision but must independently satisfy the required approval/adoption gates.

### Même identité déclarée, contenu différent

An upstream source may republish the same logical name/version while bytes or digest differ.

Expected representation: declared upstream identity plus exact artifact digest/version observation. Digest divergence must remain visible and must prevent silent equivalence with the previously qualified artifact.

### Signature valide ≠ confiance métier

A valid cryptographic signature establishes integrity/origin only to the extent of the trust chain. It does not establish contextual safety, suitability, adoption, approval, Evidence or professional validity.

### Source externe devenue inaccessible

Loss of the upstream repository/catalog does not erase historical qualification, provenance, versions, decisions or Evidence references. Current freshness/verifiability/availability may degrade independently.

### Substitution de provider dans un même Capability Slot

A replacement provider may satisfy the same abstract Capability Slot when substitution is permitted, but it does not inherit the former provider's adoption, trust, Evidence, qualification or approval history.

### Capability partiellement satisfaite

A candidate may cover only part of a Slot's requirements.

Expected representation: explicit covered requirements + unmet requirements/capability gaps + provenance. Do not collapse partial coverage into one ambiguous compatible boolean.

### Conflit entre fraîcheur et approbation

An older approved revision and a newer unapproved but technically improved revision may coexist.

Expected representation: independent revision lineage, freshness/update posture and approval state. Neither recency nor approval alone implies automatic selection when required constraints conflict.

### Découverte externe ≠ vérité

An external catalog's declared capabilities remain retrieved/source-attributed data. Direct inspection or runtime observation may disagree without either observation silently rewriting the other.

### Skill supprimé, historique conservé

Removal/suspension prevents new execution selection but preserves historical tasks, execution returns, provenance, Evidence references, approvals/decisions and lineage needed to interpret the past.

### Environnement modifié entre sélection et exécution

Binding selection records a past decision. Before launch, the runtime environment must be requalified for required constraints. Credential expiry, network loss, worker change, missing capability or tool-surface drift can make the selected binding currently ineligible without rewriting the selection event.

### Réévaluation sans réécriture de l’histoire

A skill may accumulate later failures and lose current qualification/trust. Historical observations, approvals and decisions remain preserved with their original temporal basis; current qualification changes append rather than rewrite history.

## Cross-case assertions

Every executable H5 test derived from this corpus must preserve:

```text
availability != approval
approval != current compatibility
compatibility != adoption
selection != launch-time eligibility
signature validity != métier trust
runtime success != result validity
runtime success != Evidence
local timeout != remote terminal state
late result != task reactivation
new revision != inherited approval
same declared version != same bytes
provider substitution != inherited qualification
partial coverage != compatible=true
external declaration != verified observation
removed != historical erasure
current re-evaluation != historical rewrite
```

## First mapping result

No new universal status is justified by this corpus at H5 planning time.

Existing doctrine already covers most separations through:

- Capability Slot/binding candidate posture;
- install, health, update, activation and governance status;
- launch/tool-surface qualification;
- immutable admission/reservation/run correlation;
- one-shot reconciliation and explicit inconclusive outcomes;
- Evidence/Decision/approval boundaries;
- provenance and temporal history.

The H5 implementation work should test five pressure points particularly carefully before any schema extension:

1. current environment compatibility at launch time;
2. partial Capability Slot requirement coverage;
3. exact artifact identity/digest divergence under identical declared identity;
4. cryptographic integrity versus contextual trust/adoption;
5. late remote result after cancellation/expiry without authorization resurrection.

## Non-goals

This corpus does not create a provider router, plugin manager, trust engine, autonomous updater, automatic approval system, reliability-to-Evidence promotion rule, scheduler, retry queue or new Pantheon runtime.
