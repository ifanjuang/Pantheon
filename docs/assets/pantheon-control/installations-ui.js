/* Pantheon Control — rendu Installations & bootstrap.
   Prépare des demandes candidates. Aucun changement système réel. */

let nasProfile = {...NAS_PROFILE_DEFAULT};
let selectedModuleId = MODULE_CATALOG[0].id;
let selectedTarget = MODULE_TARGETS[0];

function installLayerCard(l){
  return '<div class="card"><h3>'+l.id+' · '+l.titre+' '+chip(l.etat[0],l.etat[1])+'</h3>'+ 
    '<p>'+l.dependances+'</p>'+kv('Exécution', l.owner)+kv('Rôle Pantheon', l.pantheon)+kv('Prochaine action', l.next)+
    '<p style="margin-top:10px"><button onclick="prepareInstallStep(this,\''+safeName(l.id)+'\')">Préparer étape</button></p></div>';
}

function installProfileCard(p){
  const tone = p.score === 'Recommandé' ? 'green' : (p.score === 'À vérifier' || p.score === 'À prouver' ? 'yellow' : 'blue');
  return '<div class="card"><h3>'+p.nom+' '+chip(p.score,tone)+'</h3><p>'+p.role+'</p>'+kv('Risque', p.risque)+kv('Note', p.notes)+'</div>';
}

function prepareInstallStep(btn, id){
  btn.textContent = 'Demande préparée ✓'; btn.disabled = true;
  const out = document.getElementById('installOut');
  if(out) out.textContent = 'Étape '+id+' : plan candidat, preflight, rollback et décision humaine à préparer. Aucun changement réel.\n\n'+out.textContent;
  toast('Étape '+id+' préparée','blue');
}

function nasFieldHtml(f){
  const [id,label,type,meta] = f;
  if(type === 'select'){
    return '<label>'+label+'<select id="nas_'+id+'" onchange="updateNasProfile()">'+meta.map(v=>'<option value="'+v+'">'+v+'</option>').join('')+'</select></label>';
  }
  return '<label>'+label+'<input id="nas_'+id+'" placeholder="'+meta+'" oninput="updateNasProfile()"></label>';
}

function scoreNasProfile(p){
  const unknowns = Object.keys(p).filter(k => !p[k] || p[k] === 'inconnu' || p[k] === 'inconnue').length;
  const hasGateway = p.reverse_proxy === 'oui' || p.vpn === 'oui';
  const hasSubstrate = p.containers === 'oui' || p.vm === 'oui';
  const hasGpu = p.gpu === 'GPU exploitable';
  const hasNpu = p.npu === 'oui';
  const hasBackup = p.backup === 'oui';
  const ramStrong = p.ram === '16 Go' || p.ram === '32 Go +';

  if(unknowns >= 5) return {profil:'NAS stockage + cockpit statique', statut:['Profil prudent','blue'], risque:'Faible', reco:'Trop d’inconnues. Utiliser le NAS comme stockage, documentation statique et éventuelle redirection privée.'};
  if(!hasBackup) return {profil:'Baseline à sécuriser', statut:['Bloqué sauvegarde','red'], risque:'Élevé', reco:'Clarifier backup/snapshot avant tout substrat ou runtime.'};
  if(hasGpu && hasSubstrate && ramStrong) return {profil:'NAS runtime GPU candidat', statut:['À prouver','yellow'], risque:'Élevé', reco:'Possible seulement après preuve drivers, visibilité container/VM, benchmark petit modèle et contrôle thermique.'};
  if((hasNpu || p.gpu === 'iGPU média') && hasSubstrate) return {profil:'NAS preprocessing candidat', statut:['À vérifier','yellow'], risque:'Moyen', reco:'Bon candidat OCR léger, vision ou média si le support runtime est prouvé. Pas runtime LLM par défaut.'};
  if(hasGateway && !hasSubstrate) return {profil:'NAS passerelle / redirection', statut:['Candidat','blue'], risque:'Moyen', reco:'Utiliser comme point d’entrée contrôlé vers une machine de calcul externe. Garder runtime interne.'};
  if(hasSubstrate && ramStrong) return {profil:'NAS runtime léger', statut:['À prouver','yellow'], risque:'Moyen', reco:'Possible pour cockpit, petits services, index léger. Calcul IA lourd à déléguer.'};
  if(hasGateway) return {profil:'NAS stockage + gateway', statut:['Recommandé','green'], risque:'Faible à moyen', reco:'Stockage, cockpit statique et redirection sécurisée. Calcul délégué.'};
  return {profil:'NAS stockage + cockpit statique', statut:['Recommandé','green'], risque:'Faible', reco:'Posture par défaut : stockage, sauvegarde, docs et cockpit statique.'};
}

function updateNasProfile(){
  NAS_PROFILE_FIELDS.forEach(([id])=>{
    const el = document.getElementById('nas_'+id);
    if(el) nasProfile[id] = el.value;
  });
  renderNasResult();
  renderModulePlan();
}

function renderNasResult(){
  const r = scoreNasProfile(nasProfile);
  const el = document.getElementById('nasResult');
  if(!el) return;
  el.innerHTML = '<h3>'+r.profil+' '+chip(r.statut[0],r.statut[1])+'</h3>'+kv('Risque', r.risque)+kv('Recommandation', r.reco)+
    '<p style="margin-top:10px"><button onclick="prepareNasProfile()">Préparer profil candidat</button></p>';
}

function prepareNasProfile(){
  const r = scoreNasProfile(nasProfile);
  const out = document.getElementById('installOut');
  const title = (nasProfile.vendor || 'NAS')+' '+(nasProfile.model || '').trim();
  if(out) out.textContent = 'Profil machine candidat — '+title.trim()+' : '+r.profil+' / '+r.risque+'. '+r.reco+' Aucun changement réel.\n\n'+out.textContent;
  toast('Profil NAS candidat préparé','blue');
}

function renderNasClassifier(){
  return '<div class="card wide"><h3>Fiche machine / NAS</h3><p>Renseigne ce qui est connu. Le résultat reste local à la page et sert uniquement à préparer un profil candidat.</p>'+ 
    '<div class="grid formgrid">'+NAS_PROFILE_FIELDS.map(nasFieldHtml).join('')+'</div>'+ 
    '<div id="nasResult" class="panel-mini"></div></div>';
}

function moduleById(id){ return MODULE_CATALOG.find(m=>m.id===id) || MODULE_CATALOG[0]; }
function toneForRisk(r){ return r === 'élevé' ? 'red' : (r === 'moyen' ? 'yellow' : 'green'); }

function modulePlannerHtml(){
  return '<div class="card wide"><h3>Planificateur de module</h3><p>Choisis un module et une cible. Pantheon produit seulement un plan candidat : dépendances, checks et blocages possibles.</p>'+ 
    '<div class="grid formgrid">'+
      '<label>Module<select id="moduleSelect" onchange="updateModulePlan()">'+MODULE_CATALOG.map(m=>'<option value="'+m.id+'">'+m.nom+'</option>').join('')+'</select></label>'+ 
      '<label>Cible<select id="targetSelect" onchange="updateModulePlan()">'+MODULE_TARGETS.map(t=>'<option value="'+t+'">'+t+'</option>').join('')+'</select></label>'+ 
    '</div><div id="modulePlan" class="panel-mini"></div></div>';
}

function scoreModulePlan(m, target, machineScore){
  const targetLower = target.toLowerCase();
  const needsRuntime = ['hermes','ollama','ocr','vectordb','memory','graphrag','langgraph','langflow','observability'].includes(m.id);
  const needsCompute = ['ollama','ocr','graphrag','langgraph'].includes(m.id);
  const targetNasWeak = targetLower.includes('stockage') || targetLower.includes('gateway');
  const targetGpu = targetLower.includes('gpu');
  const targetExternal = targetLower.includes('compute externe');

  if(m.id === 'static_cockpit') return {etat:['Plan simple','green'], blocage:'Aucun blocage majeur si contenu lecture seule.', action:'Préparer publication statique et vérifier absence de données secrètes.'};
  if(m.id === 'substrate') return {etat:['À cadrer','yellow'], blocage:'Dépend du NAS/OS, backup et accès admin.', action:'Préparer preflight substrat et rollback avant toute action.'};
  if(needsCompute && targetNasWeak) return {etat:['Cible déconseillée','red'], blocage:'Cible stockage/gateway trop faible pour ce module.', action:'Rediriger vers compute externe ou prouver GPU/NPU avant plan.'};
  if(needsCompute && targetGpu) return {etat:['À prouver','yellow'], blocage:'GPU/NPU annoncé mais non prouvé.', action:'Exiger drivers, visibilité runtime, benchmark petit modèle et contrôle thermique.'};
  if(needsRuntime && targetNasWeak && !targetExternal) return {etat:['À éviter','red'], blocage:'Le module demande un runtime ; la cible doit rester stockage/gateway.', action:'Préférer compute externe et garder le NAS comme routeur/stockage.'};
  if(m.id === 'hermes' && !targetExternal) return {etat:['Candidat sensible','yellow'], blocage:'Hermes peut exécuter des actions ; admission et périmètre requis.', action:'Préparer installation candidate puis admission limitée.'};
  if(machineScore.statut[0].includes('Bloqué')) return {etat:['Bloqué baseline','red'], blocage:'Backup/snapshot non confirmé.', action:'Résoudre baseline avant tout plan module.'};
  return {etat:['Plan candidat','blue'], blocage:'Aucun blocage automatique dans la maquette.', action:'Préparer preflight, rollback, health check et décision humaine.'};
}

function updateModulePlan(){
  const ms = document.getElementById('moduleSelect');
  const ts = document.getElementById('targetSelect');
  if(ms) selectedModuleId = ms.value;
  if(ts) selectedTarget = ts.value;
  renderModulePlan();
}

function renderModulePlan(){
  const el = document.getElementById('modulePlan');
  if(!el) return;
  const m = moduleById(selectedModuleId);
  const machineScore = scoreNasProfile(nasProfile);
  const plan = scoreModulePlan(m, selectedTarget, machineScore);
  el.innerHTML = '<h3>'+m.nom+' '+chip(plan.etat[0],plan.etat[1])+'</h3>'+ 
    kv('Couche', m.couche)+kv('Cible', selectedTarget)+kv('Risque module', m.risk)+kv('Dépendances', m.depends)+kv('Checks', m.checks)+kv('Blocage', plan.blocage)+kv('Action', plan.action)+
    '<p style="margin-top:10px"><button onclick="prepareModulePlan()">Préparer plan candidat</button></p>';
}

function prepareModulePlan(){
  const m = moduleById(selectedModuleId);
  const machineScore = scoreNasProfile(nasProfile);
  const plan = scoreModulePlan(m, selectedTarget, machineScore);
  const out = document.getElementById('installOut');
  if(out) out.textContent = 'Plan module candidat — '+m.nom+' → '+selectedTarget+' : '+plan.etat[0]+'. '+plan.action+' Aucun changement réel.\n\n'+out.textContent;
  toast('Plan module candidat préparé','blue');
}

/* Reflet fidèle de mcp-server verify_install(evidence) : classe une preuve
   fournie en verdict, sans rien sonder ni décider. La logique suit le contrat
   Python (source de vérité) ; toute divergence doit être corrigée côté JS. */
let verifyState = { component:'', installed:'inconnu', reachable:'inconnu', status_code:'', checks:'inconnu' };

function verifyInstallVerdict(s){
  const gaps = [];

  let installed = null;
  if(s.installed === 'oui') installed = true;
  else if(s.installed === 'non') installed = false;
  else gaps.push('preuve d’installation absente (renseigner « Installé »)');

  let answers = null;
  if(s.reachable === 'oui' || s.reachable === 'non'){
    const reachable = s.reachable === 'oui';
    const code = (s.status_code || '').trim();
    if(code === '') answers = reachable;
    else { const n = Number(code); answers = reachable && Number.isInteger(n) && n >= 200 && n < 300; }
  } else {
    gaps.push('sonde santé absente (renseigner « Répond » / code HTTP)');
  }

  let checksGreen = null;
  if(s.checks === 'verts') checksGreen = true;
  else if(s.checks === 'rouge'){ checksGreen = false; gaps.push('au moins un check attendu n’est pas vert'); }
  else gaps.push('résultats de checks non fournis');

  let verdict;
  if(installed === false) verdict = 'absent';
  else if(installed && answers && checksGreen) verdict = 'green';
  else if(installed && (answers === false || checksGreen === false)) verdict = 'degraded';
  else verdict = 'unknown';

  return { component:(s.component || '').trim() || 'composant', installed, answers, checksGreen, verdict, gaps };
}

function verifyFieldHtml(){
  const sel = (id,label,opts,cur)=> '<label>'+label+'<select id="vf_'+id+'" onchange="updateVerify()">'+
    opts.map(o=>{ const [v,t] = Array.isArray(o)?o:[o,o]; return '<option value="'+v+'"'+(v===cur?' selected':'')+'>'+t+'</option>'; }).join('')+'</select></label>';
  return '<label>Composant<input id="vf_component" placeholder="ex. hermes, cockpit statique" oninput="updateVerify()"></label>'+
    sel('installed','Installé',VERIFY_TRISTATE,verifyState.installed)+
    sel('reachable','Répond (health)',VERIFY_TRISTATE,verifyState.reachable)+
    '<label>Code HTTP (optionnel)<input id="vf_status_code" placeholder="ex. 200" oninput="updateVerify()"></label>'+
    sel('checks','Checks',VERIFY_CHECKS_STATE,verifyState.checks);
}

function renderVerifier(){
  return '<div class="card wide"><h3>Vérification d’installation</h3><p>Renseigne la preuve déjà recueillie (installation, liveness, checks). La page la classe en verdict comme le tool <code>verify_install</code> ; elle ne sonde rien, n’installe rien et ne décide rien.</p>'+
    '<div class="grid formgrid">'+verifyFieldHtml()+'</div>'+
    '<div id="verifyResult" class="panel-mini"></div></div>';
}

function updateVerify(){
  ['component','installed','reachable','status_code','checks'].forEach(id=>{
    const el = document.getElementById('vf_'+id);
    if(el) verifyState[id] = el.value;
  });
  renderVerifyResult();
}

function renderVerifyResult(){
  const el = document.getElementById('verifyResult');
  if(!el) return;
  const v = verifyInstallVerdict(verifyState);
  const tri = b => b === true ? 'oui' : (b === false ? 'non' : 'inconnu');
  const gaps = v.gaps.length ? '<ul>'+v.gaps.map(g=>'<li>'+g+'</li>').join('')+'</ul>' : 'Aucun — preuve suffisante.';
  el.innerHTML = '<h3>'+v.component+' '+chip(v.verdict, VERIFY_VERDICT_TONE[v.verdict])+'</h3>'+
    kv('Installé', tri(v.installed))+kv('Répond', tri(v.answers))+kv('Checks verts', tri(v.checksGreen))+
    kv('Capability gaps', gaps)+
    '<p style="margin-top:10px"><button onclick="prepareVerify()">Consigner le verdict (candidat)</button></p>';
}

function prepareVerify(){
  const v = verifyInstallVerdict(verifyState);
  const out = document.getElementById('installOut');
  if(out) out.textContent = 'Vérification d’installation — '+v.component+' : verdict '+v.verdict+
    (v.gaps.length ? ' ('+v.gaps.length+' capability gap'+(v.gaps.length>1?'s':'')+')' : '')+
    '. Lecture seule, aucun changement réel ; le gate et l’humain décident.\n\n'+out.textContent;
  toast('Verdict '+v.verdict+' consigné (candidat)', VERIFY_VERDICT_TONE[v.verdict]);
}

function renderInstallationsPage(){
  const html = panel(
    'Limite',
    '<p>Cette page ne lance aucune installation. Elle rend visible la chaîne d’amorçage avant Hermes : dépendances, états, blocages, rôles et prochaines actions.</p>',
    'Avant Hermes, Pantheon ne peut pas demander à Hermes d’installer Hermes.'
  )+
  '<h3 class="chapter">Vérification d’installation</h3>'+renderVerifier()+
  '<h3 class="chapter">Profil machine / NAS</h3>'+renderNasClassifier()+
  '<h3 class="chapter">Plan module</h3>'+modulePlannerHtml()+
  '<h3 class="chapter">Chaîne bootstrap</h3>'+ 
  '<div class="grid">'+INSTALL_LAYERS.map(installLayerCard).join('')+'</div>'+ 
  '<h3 class="chapter">Profils recommandés</h3>'+ 
  '<div class="grid">'+INSTALL_PROFILES.map(installProfileCard).join('')+'</div>'+ 
  panel('États possibles','<p>'+INSTALL_STATES.map(s=>chip(s,'muted')).join('')+'</p>')+
  panel('Demandes candidates','<pre id="installOut">Aucune demande.</pre>');
  setTimeout(()=>{ renderVerifyResult(); renderNasResult(); renderModulePlan(); }, 0);
  return html;
}
