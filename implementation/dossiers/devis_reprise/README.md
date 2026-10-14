# Agency — premier essai Hermes natif sur devis de reprise

Statut : protocole opérateur avec **sources fictives** (Pantheon-Next#827, Pantheon-Next#1168). Aucun essai Linux n'est attesté par ce fichier. Il complète le banc natif Pantheon-Next#1047, sans nouveau runner, classificateur, registre ou outil d'autorisation.

Le Task Contract (`task_contract.yaml`) borne les sources possibles. Pour le **comparatif professionnel Pantheon-Next#827**, la sélection et la grille humaine existent déjà dans `implementation/tests/fixtures/professional_quote_review_cases.yaml` : seules ses `declared_source_refs`, sous-ensemble du Task Contract, sont copiées. L'email appartient au Task Contract, mais pas à cette comparaison de devis. L'ancien indice A est un contrôle négatif exclu. Le runbook historique `docs/examples/vertical_devis_reprise/` utilise un autre exemple : ne pas mélanger leurs identifiants.

## 1. Vérifier le Hermes réellement installé sur Linux

```bash
command -v hermes
hermes --version
PROFILE=pantheon-governed  # ou le profil effectivement observé
hermes -p "$PROFILE" config get tools.tool_search.enabled --json
hermes -p "$PROFILE" tools list --platform cli
hermes -p "$PROFILE" bundles list
```

Une commande manquante ou une sortie inconnue signifie **non vérifié**, pas désactivé. Conserver localement les détails de configuration/outils, sans publier de secrets. L'observateur `deployment/ubuntu/observe-hermes-runtime` concerne le **conteneur Docker** et ne décrit pas automatiquement cette installation native.

## 2. Exécuter deux essais comparables, sans effet externe

Avant `-z`, vérifier que le profil et l'environnement d'essai ne donnent accès à **aucun outil à effet externe** ni dossier client. Hermes `-z` peut contourner des demandes d'approbation ; `--in` sélectionne un répertoire de travail, **ce n'est pas une sandbox de sécurité**. Ne rien lancer si ces préconditions ne sont pas établies.

Depuis la racine du dépôt, **dans le même shell que le choix du profil**, après ce contrôle :

```bash
set -Eeuo pipefail
: "${PROFILE:?sélectionner et vérifier d'abord le profil Hermes}"
OUT="$HOME/pantheon-qualification/agency-devis-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
for ARM in direct skill_preloaded; do
  RUN="$OUT/$ARM"
  WORK="$RUN/workspace"
  mkdir -p "$WORK"

  # Utiliser la sélection du seul oracle Pantheon-Next#827, bornée par le Task Contract.
  python3 - "$WORK" <<'PY'
from pathlib import Path
from shutil import copy2
from sys import argv
import yaml

root = Path.cwd() / "implementation"
source_dir = (root / "dossiers/devis_reprise/sources").resolve()
contract = yaml.safe_load((root / "dossiers/devis_reprise/task_contract.yaml").read_text(encoding="utf-8"))
oracle = yaml.safe_load((root / "tests/fixtures/professional_quote_review_cases.yaml").read_text(encoding="utf-8"))
allowed = {row["source_ref"] for row in contract["scope"]["declared_sources"]}
selected = oracle["declared_source_refs"]
if not selected or len(selected) != len(set(selected)) or not set(selected) <= allowed:
    raise ValueError("oracle selection is missing, duplicated or out of Task Contract")
if set(selected) & set(oracle["control_source_refs"]):
    raise ValueError("oracle control source must never enter this review")
for source_ref in selected:
    ref = Path(source_ref)
    if ref.is_absolute() or ".." in ref.parts:
        raise ValueError("invalid declared source")
    source = (root / ref).resolve(strict=True)
    if not source.is_relative_to(source_dir):
        raise ValueError("out-of-scope source")
    copy2(source, Path(argv[1]) / source.name)
PY

  SKILL_ARGS=()
  if [ "$ARM" = skill_preloaded ]; then
    # Uniquement si le Skill est installé et admis pour ce test synthétique.
    SKILL_ARGS=(--skills construction-cost-review)
  fi
  PROMPT="Analyse uniquement les sources fictives sélectionnées dans le répertoire de travail pour comparer le devis Q-2026-041 au CCTP et à la DPGF révision B. Rédige une note de revue, avec fichier et clause ou poste précis pour chaque constat, et distingue cohérences, écarts et informations manquantes. Ne valide aucun devis, ne consulte aucun autre dossier et n'effectue aucune action externe."

  /usr/bin/time -f '%e' -o "$RUN/elapsed.txt" \
    hermes -p "$PROFILE" --in "$WORK" -z "$PROMPT" \
    "${SKILL_ARGS[@]}" --usage-file "$RUN/usage.json" \
    > "$RUN/answer.txt" 2> "$RUN/stderr.log"
done
```

Les deux bras utilisent **exactement la même consigne**. Le second demande le préchargement natif via `--skills` (confirmé dans la CLI Hermes v0.21.6), sans créer de bundle Pantheon. Si le Skill est absent, ne pas remplacer son échec par un résultat supposé comparable. Consulter les traces de session natives pour confirmer le chargement réel. L'essai doit conserver le même modèle, profil, réglages, jeu de sources et état initial ; si ce n'est pas possible, classer la comparaison comme non concluante.

## 3. Relire la qualité avant les tokens

La grille unique est `implementation/tests/fixtures/professional_quote_review_cases.yaml` : confronter chaque constat aux `case_id`, `source_refs`, `required_observations` et `forbidden_claims` existants, y compris les contrôles négatifs (quantités cohérentes, ancien indice A) et le pare-vapeur non tranchable. L'[issue Pantheon-Next#827](https://github.com/ifanjuang/Pantheon-Next/issues/827) suit la décision humaine. Ne pas calculer un écart financier comme directement comparable entre périmètres différents, ni transformer l'oracle en verdict professionnel.

Pour chaque bras : noter les constats exacts sourcés, les omissions, les faux positifs, les inventions, les refus/limites, puis relever `input_tokens`, `output_tokens`, `api_calls` et `elapsed.txt`. Le mécanisme de conversion des mesures natives est déjà dans `implementation/labs/hermes_runtime_efficiency/native_run.py` ; son évaluateur C4 historique traite **un autre corpus**, donc ne pas y injecter ce devis sans grille adaptée.

Ne conserver les fichiers et exports de session que localement ; ne pas publier les configurations, sorties potentiellement sensibles ou chemins privés. **Terminé seulement après un run réellement observé**, revue architecte et classification `native_sufficient / gap / inconclusive` dans Pantheon-Next#827 et Pantheon-Next#1168.
