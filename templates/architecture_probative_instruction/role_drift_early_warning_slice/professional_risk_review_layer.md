# Professional Risk Review Layer — Role Drift Early Warning

Status: template — candidate review layer, documented non-implemented.

This layer adds professional-risk review angles to role-drift situations.

It is not legal advice, not insurer advice, not a claim declaration, not an admission, not a finding of responsibility and not an external communication.

## 1. Public reference sources

Use these as review references, not as automatic rules:

```text
MAF — Devoir de conseil:
https://www.maf.fr/actualite/ce-quil-faut-savoir-sur-le-devoir-de-conseil

MAF — Défaut d'exécution sur chantier:
https://www.maf.fr/contrats-et-juridique/je-constate-un-defaut-dexecution-sur-un-chantier-que-faire

MAF — Défaillance d'entreprise:
https://www.maf.fr/node/1082

MAF — Coût des travaux:
https://www.maf.fr/actualite/architectes-ne-vous-engagez-pas-sur-le-cout-des-travaux

MAF — Synthèse chantier:
https://www.maf.fr/actualite/la-synthese-la-mission-qui-implique-larchitecte-dans-le-chantier

MAF — Périmètre d'intervention:
https://www.maf.fr/actualite/cas-de-sinistre-le-perimetre-dintervention-de-larchitecte

MAF — Déclaration de sinistre:
https://www.maf.fr/sinistres-et-incidents/quand-dois-je-declarer-un-sinistre

Conseil d'Etat — 22 December 2023 — no. 472699:
https://www.conseil-etat.fr/fr/arianeweb/CE/analyse/2023-12-22/472699

Conseil d'Etat — 10 December 2020 — no. 432783:
https://www.conseil-etat.fr/fr/arianeweb/CE/analyse/2020-12-10/432783

Cour de cassation — 3 February 1999 — no. 97-13.427:
https://www.courdecassation.fr/decision/60794cc79ba5988459c46f21
```

## 2. Review angles

```text
duty_to_warn:
  Was the project owner clearly warned, in writing, early enough?

reception_and_reserves:
  Are visible or known open items identified before reception?

contractor_execution:
  Are contractor-side defects, delays or unfinished items recorded in project follow-up?

contractor_default:
  Has the project owner been advised to preserve rights and follow the contract path?

cost_and_budget:
  Has the agency avoided firm cost guarantees where only estimates or uncertain renovation conditions exist?

synthesis_scope:
  Is the expected coordination only project coherence, or a full synthesis mission requiring contract scope?

mission_perimeter:
  Could a review, payment situation or instruction silently extend the MOE mission beyond contract scope?

professional_notice_trigger:
  Does the situation require senior review or contact with the professional insurer / counsel before any detailed answer?
```

## 3. Typical architect error patterns to screen

```text
late_written_warning;
oral_warning_without_written_trace;
unclear_email_on_important_point;
reception_without_reserve_advice;
contractor_defect_not_recorded;
contractor_default_not_escalated;
quote_review_becomes_full_consultation;
synthesis_expected_without_mission;
financial_situation_review_outside_scope;
firm_cost_commitment_in_renovation;
reply_to_challenge_without_source_pack;
```

## 4. Gate rule

```text
If any review angle is positive or uncertain:
  output_status = needs_human_arbitrage or blocked
  source_completion_required = true
  external_transmission_allowed = false
```

## 5. Required output cartouche

```text
professional_risk_review:
  sources_consulted:
  review_angles_positive:
  review_angles_uncertain:
  source_pack_complete: yes | no | partial
  dates_verified: yes | no | partial
  human_review_required: yes
  external_transmission_allowed: no by default
```

## 6. Boundary

```text
Public legal or insurer references inform caution.
They do not decide responsibility.
They do not approve a response.
They do not replace professional review.
```
