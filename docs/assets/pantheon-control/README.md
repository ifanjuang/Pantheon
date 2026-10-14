# Pantheon Control — orientation vers le Cockpit candidat

Statut : **point d’orientation documentaire / non-runtime**, avec des artefacts de validation read-only conservés séparément.

Ce répertoire ne contient pas de second dashboard Pantheon. Le cockpit, ses renderers, ses données synthétiques de projet et ses scénarios de démonstration sont maintenant portés par la responsabilité d’implémentation co-localisée :

```text
Pantheon-Next/implementation/
implementation/mvp_vertical/cockpit/
```

Source candidate courante :

```text
https://github.com/ifanjuang/Pantheon/tree/main/implementation/mvp_vertical/cockpit
```

Le dépôt historique `ifanjuang/pantheon-mvp` et sa démonstration publique restent des références de provenance pour les anciens commits, PR, issues et snapshots. Ils ne constituent plus une source d’implémentation active.

Révision historique du cockpit externe observée lors du nettoyage initial :

```text
7f3faf74afd59a07a9ab6026360881eb374df905
```

## Contenu conservé ici

```text
README.md                 -> explique la frontière et le statut
index.html                -> conserve un point stable vers la source candidate co-localisée
hermes-modules.html       -> preview synthétique du renderer du plugin dashboard Hermès
hermes-modules-demo.json  -> fixture explicitement fictive du preview Hermès
hermes-preview/           -> bundle statique du preview Hermès, couvert par les tests protégés
installations-data.js
installations-ui.js
backup-verify.js
update-verify.js
exposure-verify.js
observability-verify.js   -> miroirs read-only de classificateurs, chargés uniquement par les tests de parité protégés
card_revision_proposal_lifecycle.md
                           -> spécification de gouvernance encore référencée par le modèle Work Issue
```

Le preview Hermès n’est pas le dashboard Pantheon Control. Il montre le renderer d’un plugin externe avec données fictives et mutations désactivées. Sa conservation ne prouve ni installation, ni activation, ni inventaire runtime réel.

Les six fichiers de parité ne constituent pas une interface. Ils permettent aux tests protégés de vérifier que les verdicts JavaScript restent cohérents avec les classificateurs Python read-only du MCP. Ils n’interrogent, ne modifient et n’exposent aucun environnement.

La spécification de cycle de révision reste temporairement à son chemin historique parce qu’un document de gouvernance actif la référence. Elle est conservée pour éviter une perte de doctrine ; son futur déplacement devra mettre à jour le propriétaire actif dans le même changement.

Les autres HTML, JavaScript, CSS, fixtures et renderers de l’ancien dashboard local de cette zone documentaire ont été retirés. Le candidat exécutable courant est co-localisé sous `implementation/`; l’historique de l’ancien dépôt reste consultable comme provenance, pas comme implémentation de secours.

## Responsabilités

```text
Pantheon governance      -> gouverne les contrats, statuts, preuves, gates et décisions.
Pantheon implementation  -> porte l’implémentation candidate, le cockpit et les démos projet sous implementation/.
OpenWebUI                -> expose la surface opérationnelle lorsqu’elle est installée.
Hermes                   -> exécute les handoffs autorisés et porte son dashboard natif.
Humain                   -> approuve adoption, activation et action conséquente.
```

## Limites

```text
candidate source != deployed cockpit
historical public demo != current implementation source
synthetic Hermes preview != installed Hermes dashboard
parity mirror != user-facing dashboard
co-located implementation != adoption
installed != approved
healthy != safe
runtime_success != Evidence
```