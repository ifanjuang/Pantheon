# Exemple — Composition gouvernée : candidature marché public (DC1/DC2)

Status: fictional professional example — documented, non-implemented.
Boundary profile: documentation_only.

Deuxième exemple bout-en-bout de la composition gouvernée, sur un **autre** dossier
que le CERFA. Objectif : montrer que la même mécanique (registre → forge → deux
portes → boucle CBR) **se réutilise** d'un métier à l'autre, en repiochant les mêmes
capacités et en n'ajoutant qu'une déclaration spécifique.

À lire après [`governed_composition_cerfa/`](../governed_composition_cerfa/), qui
détaille la mécanique. Ici on insiste sur la **réutilisation** et sur ce qui change.

Doctrine : `CAPABILITY_REGISTRY.md`, `WORKFLOW_SCHEMA.md` (*Governed composition*),
`REQUEST_LIFECYCLE.md`, `EVIDENCE_PACK.md`.

## 0. Demande et cap

```text
Demande : « Monte le dossier de candidature pour l'appel d'offres Y. »
```

MÈTIS pose le cap :

```text
cap                : produire DC1 + DC2 préremplis, pièces de candidature vérifiées,
                     points douteux annotés — NON déposé, NON signé
demande réelle     : un dossier recevable, pas « remplir un PDF »
points de vigilance: validité des attestations (fiscales/sociales), capacités
                     financières, références datées, identité du groupement
limite de responsabilité : aucun dépôt sur la plateforme, aucune signature
```

## 1. RETRIEVE — réutilisation du registre

La plupart des capacités sont **les mêmes** que pour le CERFA — c'est tout l'intérêt :

```text
réutilisées telles quelles :
  classify-document      (ici : DC1, DC2, et pièces attendues au règlement de consultation)
  fetch-form-template    (DC1/DC2 = formulaires officiels à champs)
  resolve-known          (raison sociale, SIRET, CA, effectifs depuis la base entreprise)
  retrieve-source        (formulaires à jour, seuils, mentions — sources datées)
  verify-entity          (identité du candidat / des co-traitants)
  fill-fields            (claim = valeur + source + date + statut)
  raise-doubt            (weak / unverified / contradicted → question)
  render-annotated       (PDF annoté « à vérifier ici »)
  save-provenance        (Evidence Pack candidat)
```

Une seule **nouvelle** déclaration est nécessaire — preuve que le registre s'enrichit
de façon ciblée et gouvernée :

```yaml
- id: check-attestation-validity
  purpose: vérifier qu'une attestation (fiscale, sociale, assurance) est présente
           et NON périmée à la date de remise
  inputs: [piece, date_limite_remise]
  outputs: [statut_validite, date_emission, date_expiration, source]
  risk_class: high          # une attestation périmée = candidature irrecevable
  authority: signale; ne régularise pas, ne génère pas l'attestation
  depends_on: [classify-document]
  status: candidate         # entre comme candidate, à revue par domaine (marchés publics)
```

## 2. REUSE — Héphaïstos forge la recette

```text
Workflow Manifest (candidat)  id: candidature-AO-Y
cap: DC1/DC2 + pièces vérifiés, annotés, NON déposés

  classify-document            (liste les pièces exigées par le règlement de consultation)
        │
  fetch-form-template          (DC1, DC2)
        │
  ┌──────── fan-out par champ / par pièce ────────┐
  │  resolve-known                                │
  │     └─ si absent → retrieve-source            │
  │  verify-entity        (candidat + co-traitants)│
  │  check-attestation-validity  (par attestation) │  ← capacité nouvelle
  └────────────────────────────────────────────────┘
        │
  fill-fields ──► raise-doubt
        │              │
  render-annotated ◄───┘
        │
  save-provenance

statut de la recette : candidate
```

Topologie quasi identique au CERFA : **seul le fan-out gagne une branche**
(`check-attestation-validity`). La réutilisation est la règle, l'ajout l'exception.

## 3. PORTE 1 — éligibilité (ZEUS)

```text
scope             : dossier AO-Y uniquement                         ✓
autorité/étape    : aucune étape ne dépose / ne signe               ✓
risque            : check-attestation-validity = high → candidat + relecture ✓
limite de respons.: pas de dépôt plateforme, pas de signature       ✓
décision ZEUS     : allow (éligible)
```

## 4. Exécution — Hermès, dehors

Renvoie DC1/DC2 candidats, `claim_ledger`, statut de chaque pièce, PDF annoté,
Evidence Pack candidat. Pantheon ne dépose rien, ne route rien.

## 5. REVISE — relire le cap

```text
constat : le règlement exige une candidature en GROUPEMENT conjoint, non prévu au cap.
```

Changement matériel de destination (ajouter co-traitants, DC1 groupement) → MÈTIS
*propose*, **révision gouvernée** du Task Contract (`TASK_CONTRACT_REVISIONS.md`), on
interroge l'utilisateur avant d'étendre le cap. Pas de pivot silencieux.

## 6. PORTE 2 — l'evidence avant la vérité

```text
DC2 "chiffre d'affaires 3 ans" : source=liasses fiscales  statut=supported    ✓
attestation fiscale            : expire AVANT la remise    statut=contradicted ✗ → question
attestation sociale (URSSAF)   : valide à la date          statut=supported    ✓
référence "projet similaire"   : non datée                 statut=unverified   ✗ → question
SIRET co-traitant              : verify-entity OK           statut=supported    ✓
```

L'attestation périmée n'est pas « corrigée » en douce : elle remonte comme **point
bloquant à traiter par l'humain**. Pas de preuve, pas de vérité.

## 7. RETAIN

- La recette `candidature-AO-Y` a tenu → **candidate réutilisable** pour « monter une
  candidature marché public », après revue par domaine.
- `check-attestation-validity`, validée en revue, **enrichit le registre** et devient
  disponible pour d'autres recettes (elle resservira au prochain AO).
- CHARON archive un DC1 de version périmée ; CERBÈRE filtre une référence ancienne.

## Ce que ce second exemple ajoute

```text
même registre, même forge, mêmes portes  → la mécanique est métier-agnostique
8 capacités réutilisées + 1 nouvelle      → l'enrichissement est ciblé et gouverné
le fan-out gagne une branche              → la topologie s'adapte sans tout refaire
```

C'est la démonstration de la **modularité** : ajouter un métier, c'est surtout
réutiliser ; ce qu'on déclare en plus entre comme candidat, gouverné, réutilisable.

## Boundary

Exemple fictif, documenté, non implémenté. Aucun dépôt, aucune signature, aucune
promotion mémoire automatique. La forge propose une structure ; l'exécution reste
externe sous Task Contract ; la porte est une décision de gouvernance.

```text
HÉPHAÏSTOS forge la recette.
PANTHEON gouverne le cap, la preuve et le statut.
Le runtime exécute dehors.
L'humain engage.
```
