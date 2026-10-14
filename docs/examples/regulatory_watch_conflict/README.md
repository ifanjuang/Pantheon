# Example — Regulatory Watch Conflict — Active Dossier Assumption Review

Status: fictional professional example — educational support only.

This example illustrates how Pantheon Next may frame a watch alert when a new external source may contradict an assumption used in active professional dossiers.

It is not legal advice.

It is not regulatory advice.

It is not medical, technical, accounting, tax or professional advice.

It does not replace professional review.

## Why a practitioner may care

The professional problem is simple:

```text
A dossier was prepared under one assumption.
A new regulation, case law item, official doctrine, technical standard or recommendation appears.
The professional needs to know whether active dossiers are affected.
```

Raw AI may produce a confident summary of the new text.

That is not enough.

Pantheon should ask a more useful question:

```text
Does this new source create a review obligation for one or more active dossiers?
```

## Scenario

An office maintains several active dossiers.

A new external source appears:

- regulation;
- decree;
- official guidance;
- case law;
- professional recommendation;
- technical standard;
- internal office doctrine update.

The source may affect assumptions used in active work.

The risk is not only missing the update.

The risk is applying it too broadly, too early or to the wrong dossier.

## User request

```text
Check whether this new regulation affects any active dossiers.
```

## Raw AI answer — unsafe version

A generic assistant may answer:

```text
This new regulation changes the applicable rule. You should update all relevant dossiers accordingly.
```

This answer is dangerous because it may ignore:

- date of entry into force;
- transitional provisions;
- project phase;
- contract date;
- filing date;
- jurisdiction or territorial scope;
- dossier-specific exceptions;
- whether the source is final, draft, commentary or binding text;
- whether the office already has an approved doctrine.

## Pantheon interpretation

The request must not be treated as a simple research task.

It contains a freshness and applicability tension:

```text
new source detected
vs.
not every new source applies to every active dossier
```

Pantheon should reclassify the request:

```text
regulatory summary
→ watch alert
→ affected-assumption review
→ User Decision Gate if impact is uncertain or material
```

## Mission sheet — Task Contract excerpt

```text
Mission        : Watch alert — active dossier impact review
Scope          : Active dossiers tagged [DOMAIN-MASKED]
New source     : [SOURCE-ID-MASKED], observed on [DATE]
Allowed        : new source text
                 existing dossier assumptions
                 approved office doctrine
                 dossier dates and phase metadata
                 prior Evidence Packs linked to the assumption
Forbidden      : automatic rewriting of active dossiers
                 automatic client notification
                 automatic memory promotion
Expected       : watch alert + affected assumptions + review options
Approval       : professional decision required before update or transmission
Memory         : new source may become Evidence Candidate, not a Registre Probatoire entry by default
```

## Governance College status

| Role | Status | Finding |
|---|---|---|
| ATHENA | `ok_with_reserve` | The task must be split into source classification, affected-assumption scan and dossier review. |
| ARGOS | `source_required` | Source type, date, version and authority must be verified. |
| THEMIS | `risk_detected` | Applying the update too broadly may create wrong advice or unnecessary changes. |
| APOLLO | `ok_with_reserve` | A clear alert can be prepared, but it must distinguish suspected impact and confirmed impact. |
| HEPHAISTOS | `produced_candidate` | Watch alert and review checklist can be prepared as candidates. |
| IRIS | `transmission_blocked` | Do not notify clients until applicability is reviewed. |
| ZEUS | `user_clarification_required` | Ask whether to review all dossiers, only high-risk dossiers or only one named dossier first. |

## Watch alert format

```text
Watch Alert — Possible contradiction with active dossier assumptions

New source:
[SOURCE-ID-MASKED]

Source status:
observed / retrieved / version-to-confirm / authority-to-confirm

Possible affected assumption:
[ASSUMPTION-ID-MASKED]

Affected dossiers:
- [DOSSIER-A] — high likelihood, review needed
- [DOSSIER-B] — medium likelihood, phase/date check needed
- [DOSSIER-C] — low likelihood, archive note only

Applicability status:
not confirmed

Recommended next step:
review entry-into-force date, transitional provisions and dossier-specific dates before updating any output.
```

## User Decision Gate

Pantheon should ask the professional for a bounded decision before changing dossiers.

```text
Decision required.

Object of conflict:
A new source may contradict an assumption used in active dossiers, but applicability is not confirmed.

Role positions:
- ATHENA: split review by source status, assumption and dossier phase.
- ARGOS: verify source authority, version and date.
- THEMIS: avoid broad application before applicability review.
- APOLLO: prepare a clear watch alert with confidence levels.
- HEPHAISTOS: prepare candidate update notes only.
- IRIS: block client-facing transmission until approval.
- ZEUS: user decision required on review scope.

Options:
1. Review only high-risk active dossiers.
2. Review one named dossier first.
3. Create a watch note and defer updates.
4. Mark as not applicable with reasons.
5. Request external professional verification.

Recommended procedure:
Start with high-risk active dossiers or one named dossier. Do not update all dossiers automatically.
```

## Evidence Pack excerpt

```text
Evidence Pack — Watch alert

New source:
- [SOURCE-ID-MASKED]
- observed on [DATE]
- authority status: to verify
- version status: to verify

Existing assumption potentially affected:
- [ASSUMPTION-ID-MASKED]
- used in dossier [DOSSIER-A], [DOSSIER-B]

Open questions:
- entry into force date?
- transitional provisions?
- applies to already filed dossiers?
- applies to signed contracts?
- applies to current project phase?
- conflicts with approved office doctrine?

Risk note:
- do not update active dossier conclusions automatically
- do not notify clients before applicability review
- preserve current assumption as possibly superseded, not revoked
```

## Candidate output — watch note

```text
A new external source may affect assumption [ASSUMPTION-ID-MASKED].

Current status:
review needed, not confirmed impact.

Affected dossiers:
1. [DOSSIER-A]
   Reason: same topic and active phase.
   Required check: date of applicability and filing status.

2. [DOSSIER-B]
   Reason: similar assumption, but contract date may exclude application.
   Required check: transitional rules.

3. [DOSSIER-C]
   Reason: low likelihood; archive note recommended.

No client-facing update should be sent until professional validation.
```

## Decision effects

| Option | Effect on dossier | Effect on evidence | Effect on memory | Effect on transmission |
|---|---|---|---|---|
| Review high-risk dossiers | Creates review tasks | Source becomes Evidence Candidate | No memory yet | No client notice yet |
| Review one named dossier | Narrow impact analysis | Evidence linked to one dossier | Scoped candidate possible | No client notice yet |
| Defer updates | Keeps alert open | Watch note retained | No canonical change | No external effect |
| Mark not applicable | Requires reason | Evidence Pack records rejection | May record scoped note | No external effect |
| External verification | Escalates to specialist | Adds expert source later | Deferred | No external effect |

## Memory rule

A new regulation or external source must not become a Registre Probatoire entry by being observed.

Possible Register Candidate:

```text
Source [SOURCE-ID-MASKED] may affect assumption [ASSUMPTION-ID-MASKED] for dossiers tagged [DOMAIN-MASKED]. Applicability not confirmed as of [DATE].
```

This must not become a Registre Probatoire entry unless:

- source authority is verified;
- applicability is reviewed;
- scope is explicit;
- affected dossiers are identified;
- professional approval is recorded;
- obsolete or superseded assumptions are marked, not silently overwritten.

## Final reading

A practitioner should be able to understand this in one line:

```text
Pantheon does not just find new rules; it checks whether a new rule should disturb an active dossier.
```

The professional remains responsible for the final interpretation and decision.
