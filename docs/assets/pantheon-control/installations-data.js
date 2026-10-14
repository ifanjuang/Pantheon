/* Pantheon Control — données candidates pour Installations & bootstrap.
   Documenté non implémenté. Aucun service, conteneur, paquet, port ou runtime n’est créé. */

const INSTALL_LAYERS = [
  {id:'L0', titre:'Accès humain / baseline', etat:['À confirmer','yellow'], dependances:'Machine choisie, accès admin, réseau, stockage, sauvegarde.', owner:'Humain', pantheon:'Checklist, risque, décision candidate.', next:'Confirmer accès, sauvegarde et périmètre.'},
  {id:'L1', titre:'Support bootstrap', etat:['À préparer','blue'], dependances:'Guide, bundle local, dépôt Git, package vendeur ou dossier local.', owner:'Humain / outil vendeur', pantheon:'Plan candidat, preflight, rollback, état attendu.', next:'Choisir support : manuel, bundle, outil vendeur.'},
  {id:'L2', titre:'Capacité machine / NAS', etat:['À classifier','yellow'], dependances:'OS, CPU, RAM, stockage, réseau, conteneurs, VM, GPU/NPU/iGPU.', owner:'Humain', pantheon:'Classification NAS-0 à NAS-6, rôle recommandé.', next:'Renseigner profil matériel.'},
  {id:'L3', titre:'Substrat services', etat:['Absent','muted'], dependances:'Natif, conteneur, VM, système NAS ou service manager.', owner:'Humain / installateur externe', pantheon:'Plan candidat, ports, volumes, secrets, rollback.', next:'Décider si substrat nécessaire.'},
  {id:'L4', titre:'Surface statique minimale', etat:['Candidate','blue'], dependances:'HTML statique, docs locales, NAS static host, GitHub Pages ou LAN privé.', owner:'Hébergement statique', pantheon:'Afficher état installation sans prétendre qu’un runtime existe.', next:'Publier ou pointer une page statique.'},
  {id:'L5', titre:'Hermes candidat', etat:['Non installé','muted'], dependances:'Substrat existant, volumes, logs, secrets, health check.', owner:'Humain / bootstrap / substrat', pantheon:'Plan d’installation candidat et statut après résultat.', next:'Préparer plan Hermes après substrat.'},
  {id:'L6', titre:'Surface d’exposition', etat:['Non installée','muted'], dependances:'OpenWebUI ou surface équivalente, auth, scope, réseau.', owner:'Humain / substrat', pantheon:'Préciser local, VPN, public read-only, approvals requis.', next:'Décider surface après Hermes ou statique.'},
  {id:'L7', titre:'Modules runtime', etat:['Bloqué','red'], dependances:'Hermes ou installateur externe, health checks, ressources.', owner:'Hermes autorisé / humain', pantheon:'Préparer candidats : OCR, modèles, vector DB, mémoire, GraphRAG, LangGraph.', next:'Attendre runtime ou installateur externe.'},
  {id:'L8', titre:'Admission & task authorization', etat:['Non applicable','muted'], dependances:'Modules installés, manifest, passport, preflight, Task Contract.', owner:'Pantheon + humain', pantheon:'Gouverner admission, scope, approval, statut.', next:'Seulement après installation vérifiée.'},
];

const INSTALL_PROFILES = [
  {nom:'NAS stockage + cockpit statique', score:'Recommandé', role:'Stockage, sauvegarde, documentation, redirection contrôlée.', risque:'Faible', notes:'Point de départ le plus sûr si le NAS est inconnu.'},
  {nom:'NAS passerelle / redirection', score:'Candidat', role:'Reverse proxy, accès privé, sous-domaines, routage vers compute.', risque:'Moyen', notes:'Ne doit pas exposer les runtimes internes publiquement.'},
  {nom:'NAS runtime léger', score:'À prouver', role:'Petits services, inventaire, index léger, health checks.', risque:'Moyen', notes:'Dépend fortement CPU/RAM/I/O et support conteneurs.'},
  {nom:'NAS GPU/NPU', score:'À vérifier', role:'OCR, vision, embeddings ou inference locale si support réel.', risque:'Élevé', notes:'GPU présent ne veut pas dire LLM prêt. Drivers et benchmarks requis.'},
  {nom:'NAS + compute externe', score:'Recommandé', role:'NAS stocke et route ; workstation/mini-PC/GPU exécute.', risque:'Faible à moyen', notes:'Sépare stockage durable et calcul volatil.'},
];

const INSTALL_STATES = ['absent','unknown','detected','planned','ready_for_manual_install','ready_for_handoff','installed_unverified','healthy','blocked','rolled_back','retired'];

/* Contrat de vérification d'installation — reflet read-only du tool mcp-server
   `verify_install(evidence)`. La source de vérité est ce contrat Python ; ce
   bloc n'en est que l'affichage cockpit. La page ne sonde rien, n'accède à aucun
   NAS, n'installe rien et ne décide rien : elle classe une preuve fournie en
   verdict (green / degraded / absent / unknown) avec ses capability gaps, comme
   le ferait le tool. Le gate et l'humain décident.

   Forme de preuve (toutes les valeurs sont fournies, jamais sondées) :
     { component, installed, health:{reachable,status_code}, checks:[{name,status}], expected_checks } */
const VERIFY_VERDICT_TONE = { green:'green', degraded:'yellow', absent:'muted', unknown:'blue' };

const VERIFY_TRISTATE = ['inconnu','oui','non'];

const VERIFY_CHECKS_STATE = [
  ['inconnu','Résultats de checks non fournis'],
  ['verts','Tous les checks attendus sont verts'],
  ['rouge','Au moins un check n’est pas vert'],
];

const NAS_PROFILE_FIELDS = [
  ['vendor','Marque','text','Synology / QNAP / Unraid / TrueNAS / autre'],
  ['model','Modèle','text','Modèle exact si connu'],
  ['ram','RAM estimée','select',['inconnue','≤ 4 Go','8 Go','16 Go','32 Go +']],
  ['containers','Conteneurs','select',['inconnu','non','oui']],
  ['vm','VM','select',['inconnu','non','oui']],
  ['gpu','GPU / iGPU','select',['inconnu','aucun','iGPU média','GPU exploitable']],
  ['npu','NPU / accélérateur IA','select',['inconnu','non','oui']],
  ['reverse_proxy','Reverse proxy / gateway','select',['inconnu','non','oui']],
  ['vpn','VPN / accès privé','select',['inconnu','non','oui']],
  ['backup','Backup / snapshot','select',['inconnu','non','oui']],
];

const NAS_PROFILE_DEFAULT = {
  vendor:'', model:'', ram:'inconnue', containers:'inconnu', vm:'inconnu', gpu:'inconnu', npu:'inconnu', reverse_proxy:'inconnu', vpn:'inconnu', backup:'inconnu'
};

const MODULE_TARGETS = [
  'NAS stockage / cockpit statique',
  'NAS gateway / redirection',
  'NAS runtime léger',
  'NAS GPU/NPU candidat',
  'Compute externe',
  'À déterminer'
];

const MODULE_CATALOG = [
  {id:'substrate', nom:'Substrat services', couche:'L3', poids:'fondation', depends:'accès admin, sauvegarde, rôle machine', checks:'rollback, logs, ressources, ports, volumes', default_target:'NAS ou compute', risk:'moyen'},
  {id:'static_cockpit', nom:'Cockpit statique', couche:'L4', poids:'léger', depends:'hébergement statique ou fichiers locaux', checks:'page reachable, aucune donnée secrète, lecture seule', default_target:'NAS stockage / cockpit statique', risk:'faible'},
  {id:'hermes', nom:'Hermes Agent', couche:'L5', poids:'runtime', depends:'substrat, volumes, logs, secrets, health check', checks:'service, version, logs, périmètre actions', default_target:'Compute externe', risk:'élevé'},
  {id:'exposure', nom:'Surface d’exposition', couche:'L6', poids:'surface', depends:'auth, réseau, scope, runtime ou statique', checks:'local/VPN/public read-only, boutons non exécutifs', default_target:'NAS gateway / redirection', risk:'moyen'},
  {id:'ollama', nom:'Runtime modèles locaux', couche:'L7', poids:'compute', depends:'Hermes ou installateur externe, CPU/GPU/RAM, stockage modèles', checks:'petit modèle, thermique, fallback, logs', default_target:'Compute externe', risk:'élevé'},
  {id:'ocr', nom:'OCR / extraction', couche:'L7', poids:'compute', depends:'fichiers, runtime, CPU/GPU/NPU éventuel', checks:'échantillon PDF/image, temps, qualité, traces', default_target:'Compute externe', risk:'moyen'},
  {id:'vectordb', nom:'Vector DB', couche:'L7', poids:'données', depends:'stockage persistant, backup, réseau interne', checks:'persistance, accès interne, export, rollback', default_target:'Compute externe', risk:'moyen'},
  {id:'memory', nom:'Mémoire runtime', couche:'L7', poids:'mémoire', depends:'runtime, règles mémoire, stockage, isolation', checks:'non canonique, effacement, namespace, logs', default_target:'Compute externe', risk:'élevé'},
  {id:'graphrag', nom:'GraphRAG tooling', couche:'L7', poids:'indexation', depends:'corpus, compute, vector/index store, extraction', checks:'sortie candidate, sources, coût, non-validation automatique', default_target:'Compute externe', risk:'élevé'},
  {id:'langgraph', nom:'LangGraph durable', couche:'L7', poids:'orchestration', depends:'runtime, checkpoint store, handoff Hermes', checks:'interruptions, reprise, human-in-loop, statut', default_target:'Compute externe', risk:'élevé'},
  {id:'langflow', nom:'Langflow designer', couche:'L7', poids:'design', depends:'surface protégée, stockage flows, pas runtime canonique', checks:'export, version, permissions, séparation design/exécution', default_target:'Compute externe', risk:'moyen'},
  {id:'observability', nom:'Observabilité', couche:'L7', poids:'logs', depends:'services à observer, stockage traces, auth', checks:'logs, métriques, confidentialité, rétention', default_target:'Compute externe', risk:'moyen'},
];
