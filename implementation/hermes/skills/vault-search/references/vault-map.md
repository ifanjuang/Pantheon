# Carte des sources agency

## VAULT_AFFAIRES

Serveur MCP Hermes : `hindsight-project` (`recall_project_memory`)

Banque Hindsight : `VAULT_AFFAIRES`

Contenu attendu : affaires, projets, appels d'offres, clients, missions,
chantiers, contrats, factures et pièces administratives associées.

Outils actuellement autorisés : `recall`, `reflect`, `list_documents`,
`get_document`, `list_operations`, `get_operation`, `list_tags`.

### Structure projet attendue — provisoire

Les projets devraient être recensés dans un dossier dont le segment se nomme
`_Projets` ou `Projets`, avec une fiche principale `.md` ou `.json` contenant
les informations essentielles. La casse, le préfixe `_` et la position exacte
dans l'arborescence ne sont pas encore stabilisés : les découvrir au lieu de les
coder en dur.

Autour d'un projet, les catégories suivantes sont prévues :

- `Plans` : représentations et pièces graphiques ;
- `Dossiers` : ensembles de pièces ou livrables ;
- `Admin` : éléments administratifs ;
- `Archives` : versions anciennes ou périmées, utilisables pour l'historique.

Ces catégories décrivent une intention de classement, pas encore une structure
contractuelle. Ne pas déduire la validité, l'approbation ou la version applicable
du seul nom du dossier. Rechercher d'abord une source hors `Archives`; si la
seule information disponible est archivée, la qualifier comme potentiellement
obsolète.

Les fiches projet peuvent être en Markdown ou JSON alors que les plans et autres
pièces restent en PDF. Une représentation Markdown indexée par Hindsight ne
remplace pas le fichier source et ne prouve pas que son contenu graphique a été
lu.

Une mention de ville n'est une localisation de projet que si le texte la relie
au site, aux travaux, à l'opération, à la mission ou au dossier. Une adresse de
contact ne suffit pas.

Le libellé usuel d'un même projet peut provenir du client, de la rue, de la
commune, d'un code, de l'opération ou du dossier. Résoudre ces alias à partir de
leur cooccurrence dans les documents et conserver le chemin documentaire comme
ancrage vérifiable. Une commune seule peut désigner plusieurs projets.

## VAULT_DOCUMENTAIRES

Serveur MCP Hermes : `vault-read` pour les sources accessibles localement

Banque Hindsight : `VAULT_DOCUMENTAIRES`

Contenu attendu : références techniques, documentation, méthodes, doctrine et
documents utilisés pour étayer une analyse.

Outils actuellement autorisés : `recall`, `reflect`, `list_documents`,
`get_document`, `list_tags`.

Pour une affirmation technique, citer le document et la page ou section quand
le résultat les fournit. Distinguer le texte source de son interprétation.

## Banque hermes

Cette banque contient la mémoire opérationnelle et conversationnelle de Hermes.
Elle peut aider l'agent à conserver son contexte, mais ne constitue pas un vault
métier et ne prouve aucun fait relatif à une affaire ou à une documentation.

Elle peut servir d'indice pour retrouver le dernier projet explicitement discuté
lorsqu'un nouveau message emploie « ce projet », « le dossier » ou une autre
référence implicite. En cas d'ambiguïté entre plusieurs projets, demander à
l'utilisateur au lieu de choisir selon la seule similarité sémantique.

## MCP Notion

Notion représente potentiellement l'état en direct, tandis que Hindsight
représente l'état indexé. Interroger Notion seulement si la demande porte sur une
modification récente ou si l'utilisateur demande explicitement la source live.
Ne pas fusionner silencieusement les deux états; dater ou qualifier la source.

## Questions transversales

- Affaire seule : rechercher uniquement `VAULT_AFFAIRES`.
- Référence seule : rechercher uniquement `VAULT_DOCUMENTAIRES`.
- Conformité ou comparaison affaire/référence : rechercher d'abord l'affaire,
  puis la documentation utile, avec un `recall` maximum dans chaque vault.
- Synchronisation : vérifier les opérations disponibles et comparer avec la
  source live seulement si la demande le justifie.
