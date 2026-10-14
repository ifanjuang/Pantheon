# Exemple — Composition gouvernée bout-en-bout (CERFA forgé par Héphaïstos)

Status: fictional professional example — documented, non-implemented.
Boundary profile: documentation_only.

Cet exemple montre la **mécanique** de la composition gouvernée : comment, à partir
d'une demande, Héphaïstos *forge* une recette (un Workflow Manifest candidat) en
puisant dans le registre de capacités, comment les deux portes encadrent
l'exécution, et comment la boucle retrieve/reuse/revise/retain garde le cap.

Pour le détail métier du dossier CERFA (sources, minimisation, questions,
contrôle qualité, trace), voir l'exemple narratif voisin
[`architecture_cerfa_workflow/`](../architecture_cerfa_workflow/). Ici on regarde
*comment la recette est fabriquée et gouvernée*, pas le contenu du formulaire.

Doctrine de référence : `CAPABILITY_REGISTRY.md`, `WORKFLOW_SCHEMA.md`
(section *Governed composition*), `REQUEST_LIFECYCLE.md`, `EVIDENCE_PACK.md`.

## 0. La demande et le cap

```text
Demande : « Prépare le CERFA pour le projet X. »
```

La demande est claire en surface mais conséquente (effet réglementaire, données
client). MÈTIS pose le cap :

```text
cap                : obtenir un CERFA prérempli, vérifié, annoté sur les points
                     douteux — NON déposé, NON signé
demande réelle     : conduire le dossier, pas « cocher des cases »
points de vigilance: surfaces, ERP, stationnement, version de PLU, identité MOA
limite de responsabilité : aucune transmission ni signature par le système
```

Le cap vit dans le Task Contract. Il pourra être relu (étape 5).

## 1. RETRIEVE — le registre de capacités

Le registre déclare des capacités par leurs **métadonnées de gouvernance seules**.
L'exécutable vit ailleurs (runtime). Extrait des déclarations utiles ici :

```yaml
- id: classify-document
  purpose: identifier de quel formulaire / CERFA il s'agit
  inputs: [dossier_projet]
  outputs: [type_formulaire]
  risk_class: low
  authority: lecture seule
  depends_on: []

- id: fetch-form-template
  purpose: récupérer le gabarit du formulaire (docx/pdf, à champs ou plat)
  inputs: [type_formulaire]
  outputs: [gabarit, field_map]
  risk_class: low
  authority: lecture seule
  depends_on: [classify-document]

- id: resolve-known
  purpose: répondre un champ depuis la base projet
  inputs: [field, dossier_projet]
  outputs: [valeur_candidate, source, date]
  risk_class: medium
  authority: propose une valeur candidate
  depends_on: []

- id: retrieve-source
  purpose: récupérer une valeur depuis une source datée (géoportail, service-public)
  inputs: [field]
  outputs: [valeur_candidate, source, date]
  risk_class: medium
  authority: lecture seule, source datée obligatoire
  depends_on: []

- id: verify-entity
  purpose: recouper l'identité d'une société / personne (societe.com, annuaire)
  inputs: [entite]
  outputs: [statut_verif, source, date]
  risk_class: medium
  authority: lecture seule
  depends_on: []

- id: fill-fields
  purpose: remplir les champs supportés (claim = valeur + source + date + statut)
  inputs: [field_map, valeurs_candidates]
  outputs: [formulaire_candidat, claim_ledger]
  forbidden: [soumettre, signer]
  risk_class: high
  authority: produit un candidat uniquement
  depends_on: [fetch-form-template, resolve-known, retrieve-source, verify-entity]

- id: raise-doubt
  purpose: marquer weak / unverified / contradicted et formuler la question
  inputs: [claim_ledger]
  outputs: [points_a_verifier, questions]
  risk_class: low
  authority: signale, ne tranche pas
  depends_on: [fill-fields]

- id: render-annotated
  purpose: produire le PDF/docx annoté « à vérifier ici »
  inputs: [formulaire_candidat, points_a_verifier]
  outputs: [livrable_candidat]
  forbidden: [transmettre]
  risk_class: medium
  authority: produit un candidat uniquement
  depends_on: [fill-fields, raise-doubt]

- id: save-provenance
  purpose: constituer l'Evidence Pack candidat (qui, d'où, quand)
  inputs: [claim_ledger]
  outputs: [evidence_pack_candidat]
  risk_class: low
  authority: trace, ne promeut pas en mémoire
  depends_on: [fill-fields]
```

La récupération part d'une graine (« préparer un formulaire de projet ») puis
**remonte les dépendances déclarées** — elle ne fait pas du *matching* de mots-clés.

## 2. REUSE — Héphaïstos forge le Workflow Manifest candidat

Héphaïstos assemble la recette. Topologie : séquence + **fan-out par champ** pour la
résolution (selon `EVIDENCE_TOPOLOGY`).

```text
Workflow Manifest (candidat)  id: cerfa-projet-X
cap: CERFA prérempli, vérifié, annoté, NON déposé

  classify-document
        │
  fetch-form-template
        │
  ┌──────── fan-out, pour chaque champ ────────┐
  │  resolve-known                             │
  │     └─ si absent → retrieve-source         │
  │  verify-entity (champs d'identité)         │
  └────────────────────────────────────────────┘
        │
  fill-fields ──► raise-doubt
        │              │
  render-annotated ◄───┘
        │
  save-provenance

statut de la recette : candidate  (dynamic_runtime_tool_candidate)
```

Chaque étape porte une **signature** (entrées / sorties autorisées / sorties
interdites / risque / autorité) — c'est un contrat de gouvernance lisible *sans
exécuter*. Règle dure : **forgé ≠ autorisé**.

## 3. PORTE 1 — éligibilité avant exécution (ZEUS)

Avant toute exécution externe, ZEUS arbitre l'éligibilité de la recette :

```text
scope            : périmètre dossier X uniquement              ✓
autorité/étape   : aucune étape ne soumet/signe/transmet       ✓
classe de risque : fill-fields = high → candidat + relecture   ✓
limite de respons.: pas de dépôt, pas de signature             ✓
minimisation     : données minimisées avant moteur externe     ✓ (cf. exemple narratif)
décision ZEUS    : allow (éligible) → l'exécution peut être autorisée hors Pantheon
```

Une recette inéligible (ex. une étape « déposer le CERFA ») ne passe pas la porte.

## 4. Exécution — Hermès, hors Pantheon

Le runtime déroule la recette sous Task Contract et renvoie :

```text
- formulaire_candidat        (CERFA prérempli)
- claim_ledger               (chaque champ : valeur + source + date + statut)
- points_a_verifier + questions
- livrable_candidat          (PDF annoté)
- evidence_pack_candidat
```

Pantheon ne planifie pas, ne relance pas, ne route pas. Il a fourni le cadre ; il
recevra des candidats.

## 5. REVISE — relire le cap quand les réponses arrivent

Pendant la résolution, une réponse change la donne :

```text
constat : l'usage + les surfaces suggèrent un ERP non prévu au cap initial.
```

- ajustement mineur, dans le périmètre → MÈTIS note et continue (réversible, tracé) ;
- **changement matériel de destination** (ajouter les pièces ERP) → MÈTIS *propose*,
  et c'est une **révision gouvernée** du Task Contract (`TASK_CONTRACT_REVISIONS.md`),
  pas un pivot silencieux. Ici : on pose la question à l'architecte avant d'étendre
  le cap.

## 6. PORTE 2 — l'evidence avant la vérité

À la sortie, chaque *claim* doit être soutenu (`EVIDENCE_PACK.md`) :

```text
champ "surface plancher"   : valeur=…  source=plan_PC2  date=…  statut=supported   ✓
champ "adresse MOA"        : 2 valeurs divergentes               statut=contradicted ✗ → question
champ "n° SIRET"           : verify-entity OK                     statut=supported   ✓
champ "zone PLU"           : source=géoportail (datée)            statut=supported   ✓
champ "stationnement"      : absent au plan, exigé au règlement   statut=unverified  ✗ → question
```

Un claim non soutenu **ne devient pas une vérité** : il est rendu comme *point à
vérifier*, pas comme valeur sûre. Pas de preuve, pas de vérité.

## 7. RETAIN — ce qui peut être réutilisé

- La recette `cerfa-projet-X` a tenu → elle devient une **candidate réutilisable**
  pour « préparer un CERFA », *après* revue par domaine (archi), jamais par dépôt
  automatique.
- Une nouvelle source datée découverte (un portail réglementaire utile) peut
  **enrichir le registre** — comme candidate, gouvernée.
- CERBÈRE filtre ce qui revient du passé ; CHARON archive une version supersédée
  (gabarit CERFA périmé) sans la détruire.
- Aucune mémoire durable sans validation explicite.

## Ce que l'exemple démontre

```text
registre   → quelles capacités existent et ce qu'elles peuvent faire
forge      → comment Héphaïstos les compose pour CE cap
porte 1    → la recette est-elle éligible (ZEUS) ?
exécution  → Hermès déroule, dehors
porte 2    → chaque claim est-il soutenu (evidence) ?
boucle CBR → le cap est relu ; la recette qui tient devient réutilisable
humain     → corrige, complète, décide d'envoyer ou non
```

Le différenciateur : ce n'est pas « composer pour agir vite », c'est **composer pour
agir juste et révisable** — cap métier tenu, responsabilité bornée, tout en candidat
jusqu'à décision.

## Boundary

Exemple fictif, documenté, non implémenté. Aucune exécution, aucun dépôt, aucune
signature, aucune promotion mémoire automatique. La forge propose une structure de
gouvernance ; l'exécution reste externe sous Task Contract ; la porte est une
décision de gouvernance, jamais un mécanisme automatique.

```text
HÉPHAÏSTOS forge la recette.
PANTHEON gouverne le cap, la preuve et le statut.
Le runtime exécute dehors.
L'humain engage.
```
