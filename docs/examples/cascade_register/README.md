# Dossier d'instances — cascade Registre Probatoire (exemple)

Exemple fictif et validé : un mini-dossier d'architecture qui exerce les
schémas `register_candidate`, `register_link` et `impact_review`, la règle de
cascade et les invariants de continuité d'historique des Register Candidates.

Scénario principal : le client demande d'aménager le sous-sol en cours de
projet (ERP). Valider cette preuve a des conséquences en cascade — la
classification ERP est déclassée, et les issues de secours partent en
arbitrage (critique, jamais déclassé en silence).

Deux petites séquences indépendantes complètent le corpus :

- une assertion rejetée réapparaît uniquement par une reconsideration explicite
  qui conserve le candidat rejeté dans `supersedes_candidate_id` ;
- une position approuvée remplacée reste `superseded` et son successeur
  `approved` conserve la référence vers l'historique remplacé.

La garde de non-résurrection est volontairement bornée à :

```text
même scope_type + scope_id
+ même claim après normalisation casse/espaces
```

Elle ne tente aucune équivalence sémantique et ne transforme pas Pantheon en
moteur de vérité ou de résolution automatique des contradictions.

## Fichiers

| Fichier | Schéma | Rôle |
|---|---|---|
| `candidate.p-202.yaml` | `register_candidate` | Aménagement du sous-sol (déclencheur) |
| `candidate.p-150.yaml` | `register_candidate` | Classification ERP actuelle (cible) |
| `link.p202-impacts-p150.yaml` | `register_link` | P-202 impacte P-150 (réglementaire, élevé) |
| `link.p202-impacts-issues.yaml` | `register_link` | P-202 impacte les issues de secours (critique) |
| `impact_review.erp-basement.yaml` | `impact_review` | La cascade ouverte à la validation de P-202 |
| `candidate.guard-r100-rejected.yaml` | `register_candidate` | Assertion explicitement rejetée |
| `candidate.guard-r101-reconsidered.yaml` | `register_candidate` | Réexamen explicite du rejet avec nouvelle preuve |
| `candidate.guard-s100-superseded.yaml` | `register_candidate` | Position historique remplacée |
| `candidate.guard-s101-current.yaml` | `register_candidate` | Successeur approuvé qui conserve l'historique |

## Validation

`.github/scripts/check_register_instances.py` valide chaque fichier contre son
schéma, vérifie l'intégrité des `link_ids` et applique la règle de cascade
(critique ⇒ `critical_arbitration` ; review `resolved` ⇒ décision par cible).

Le même point d'entrée exécute ensuite le contrôle déterministe de continuité
`pantheon_mcp.register_history` :

- un `supersedes_candidate_id` doit référencer un candidat existant du même
  scope et plus ancien ;
- un successeur `approved` ne peut pas laisser son prédécesseur dans un état
  actif ;
- un candidat `superseded` doit avoir un successeur `approved` dans le dossier ;
- un candidat rejeté ne peut pas réapparaître silencieusement avec le même
  scope et le même claim normalisé ; un réexamen doit préserver explicitement
  la chaîne de supersession ;
- les cycles de supersession sont refusés.

Ces contrôles sont en lecture seule : ils signalent une incohérence, mais ne
rejettent, n'approuvent, ne corrigent et ne supersèdent aucun enregistrement.

Statut : exemple — données fictives ; validation contractuelle, aucun runtime de
mémoire ou moteur d'approbation n'est introduit.
