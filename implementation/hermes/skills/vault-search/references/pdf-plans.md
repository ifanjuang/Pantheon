# Plans et documents PDF

## Niveaux de preuve

Toujours distinguer :

1. `mentionné` — une note, un CCTP, un CERFA ou un autre document cite le plan ;
2. `fichier présent` — un PDF correspondant existe dans le vault physique ;
3. `contenu inspecté` — le PDF a été ouvert ou converti et les pages utiles ont
   réellement été examinées.

Ne pas déduire le niveau 2 ou 3 du seul niveau 1. Une référence telle que
« plans indice E » ne permet pas, à elle seule, de décrire les dessins ni de
confirmer qu'il s'agit de la dernière version applicable.

## Inventaire physique

Après confirmation du répertoire du projet, appeler
`list_vault_project_sources(project_ref, topic)` via `vault-read`. Garder
les PDF du projet seulement ; le score de chemin n'est pas une inspection.
Le script ci-dessous reste un diagnostic opérateur si la liaison MCP n'est
pas active, et non une instruction à inventer un outil terminal dans Hermes :

```bash
SKILL_ROOT="${HERMES_HOME:-$HOME/.hermes}/skills/vault-search"
python3 "$SKILL_ROOT/scripts/list_project_files.py" \
  "$VAULT_AFFAIRES_ROOT" --under chemin/du/projet --extension .pdf
```

Ne pas lancer une recherche non bornée sur tout le système. Le chemin passé à
`--under` doit provenir d'un document ou d'un alias de projet confirmé. Ajouter
`--include-archives` seulement pour une demande historique ou explicite.

## Lecture avec Docling

Le serveur MCP `Doclin` est la route locale prévue pour les PDF :

1. vérifier le cache avec `is_document_in_local_cache` ;
2. convertir si nécessaire avec `convert_document_into_docling_document` en
   transmettant `source: <chemin partagé ou URL>` ;
3. obtenir la structure avec `get_overview_of_document_anchors` ;
4. cibler les termes utiles avec `search_for_text_in_document_anchors` ;
5. lire seulement les ancres pertinentes avec
   `get_text_of_document_item_at_anchor`.

Ne pas appeler `get_prompt`, `list_prompts`, `read_resource` ou `list_resources`
pour ouvrir un PDF. Ces opérations décrivent le serveur ou ses ressources et
ne remplacent pas la conversion. Le chemin doit exister dans l'espace de
fichiers du service Docling ; un chemin d'attachement WebUI non monté n'est pas
valide.

Pour une question nécessitant la lecture graphique d'un plan, utiliser
`page_thumbnail` et une capacité visuelle si elles sont disponibles. Sinon,
indiquer que seul le texte extractible a été contrôlé. Ne pas convertir tout un
dossier quand un à trois fichiers ciblés suffisent.

## Réponse

Citer séparément la source de chaque niveau : document qui mentionne le plan,
chemin du PDF constaté, puis page ou ancre effectivement inspectée. Une date de
modification de fichier n'est pas une date d'approbation, de dépôt ou de validité.
