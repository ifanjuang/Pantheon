/* Pantheon Control — vérification d'observabilité (read-only).
   Reflet fidèle de mcp-server verify_observability(evidence) : classe une preuve
   fournie (signaux présents, fraîcheur, erreurs) en verdict, sans rien interroger
   ni décider. La logique suit le contrat Python (source de vérité) ; toute
   divergence doit être corrigée côté JS. La page n'interroge aucun backend de
   métriques, n'accède à aucun NAS et ne décide rien. */

const OBS_VERDICT_TONE = { observable:'green', degraded:'yellow', blind:'muted', unknown:'blue' };

const OBS_SIGNAL_STATE = [
  ['inconnu','Inventaire de signaux non fourni'],
  ['tous','Tous les signaux attendus sont présents'],
  ['partiel','Au moins un signal attendu est absent'],
  ['aucun','Aucun signal présent (aveugle)'],
];
const OBS_FRESH_STATE = [
  ['inconnu','Fraîcheur non fournie'],
  ['oui','Données fraîches'],
  ['non','Données périmées'],
];
const OBS_ERRORS_STATE = [
  ['inconnu','Niveau d’erreurs non fourni'],
  ['ok','Erreurs sous le seuil'],
  ['depasse','Erreurs au-dessus du seuil'],
];

let obsVerifyState = { component:'', signals:'inconnu', fresh:'inconnu', errors:'inconnu' };

function verifyObservabilityVerdict(s){
  const gaps = [];

  let hasAny = null;
  let signalsPresent = null;
  if(s.signals === 'aucun'){ hasAny = false; signalsPresent = false; gaps.push('aucun signal présent'); }
  else if(s.signals === 'partiel'){ hasAny = true; signalsPresent = false; gaps.push('signal attendu absent'); }
  else if(s.signals === 'tous'){ hasAny = true; signalsPresent = true; }
  else gaps.push('inventaire de signaux non fourni');

  let fresh = null;
  if(s.fresh === 'oui') fresh = true;
  else if(s.fresh === 'non'){ fresh = false; gaps.push('données périmées'); }
  else gaps.push('fraîcheur non fournie');

  let errorsOk = null;
  if(s.errors === 'ok') errorsOk = true;
  else if(s.errors === 'depasse'){ errorsOk = false; gaps.push('erreurs au-dessus du seuil'); }
  else gaps.push('niveau d’erreurs non fourni');

  let verdict;
  if(hasAny === false) verdict = 'blind';
  else if(signalsPresent && fresh && errorsOk) verdict = 'observable';
  else if(signalsPresent === false || fresh === false || errorsOk === false) verdict = 'degraded';
  else verdict = 'unknown';

  return { component:(s.component || '').trim() || 'composant', hasAny, signalsPresent, fresh, errorsOk, verdict, gaps };
}

function obsKv(label, value){ return '<div class="kv"><span>'+label+'</span><b>'+value+'</b></div>'; }

function obsSelectHtml(id, label, opts, cur){
  return '<label>'+label+'<select id="obs_'+id+'" onchange="updateObsVerify()">'+
    opts.map(([v,t])=>'<option value="'+v+'"'+(v===cur?' selected':'')+'>'+t+'</option>').join('')+'</select></label>';
}

function renderObservabilityVerifier(){
  return '<div class="panel"><h3>Vérification d’observabilité '+chip('read-only','blue')+'</h3>'+
    '<p>Renseigne la preuve déjà recueillie (signaux, fraîcheur, erreurs). La page la classe en verdict comme le tool <code>verify_observability</code> : peut-on seulement voir le service. Elle n’interroge aucun backend, n’accède à aucun NAS et ne décide rien.</p>'+
    '<div class="grid formgrid">'+
      '<label>Composant<input id="obs_component" placeholder="ex. hermes" oninput="updateObsVerify()"></label>'+
      obsSelectHtml('signals','Signaux',OBS_SIGNAL_STATE,obsVerifyState.signals)+
      obsSelectHtml('fresh','Fraîcheur',OBS_FRESH_STATE,obsVerifyState.fresh)+
      obsSelectHtml('errors','Erreurs',OBS_ERRORS_STATE,obsVerifyState.errors)+
    '</div><div id="obsVerifyResult" class="panel-mini"></div></div>';
}

function updateObsVerify(){
  ['component','signals','fresh','errors'].forEach(id=>{
    const el = document.getElementById('obs_'+id);
    if(el) obsVerifyState[id] = el.value;
  });
  renderObsVerifyResult();
}

function renderObsVerifyResult(){
  const el = document.getElementById('obsVerifyResult');
  if(!el) return;
  const v = verifyObservabilityVerdict(obsVerifyState);
  const tri = b => b === true ? 'oui' : (b === false ? 'non' : 'inconnu');
  const gaps = v.gaps.length ? '<ul>'+v.gaps.map(g=>'<li>'+g+'</li>').join('')+'</ul>' : 'Aucun — preuve suffisante.';
  el.innerHTML = '<h3>'+v.component+' '+chip(v.verdict, OBS_VERDICT_TONE[v.verdict])+'</h3>'+
    obsKv('Signaux présents', tri(v.signalsPresent))+obsKv('Données fraîches', tri(v.fresh))+obsKv('Erreurs sous seuil', tri(v.errorsOk))+
    obsKv('Capability gaps', gaps)+
    '<p style="margin-top:10px"><button class="primary" onclick="prepareObsVerify()">Consigner le verdict (candidat)</button></p>';
}

function prepareObsVerify(){
  const v = verifyObservabilityVerdict(obsVerifyState);
  if(typeof toast === 'function') toast('Verdict '+v.verdict+' consigné (candidat)', OBS_VERDICT_TONE[v.verdict]);
}
