/* Pantheon Control — vérification de surface d'exposition (read-only).
   Reflet fidèle de mcp-server verify_exposure(evidence) : classe une preuve
   fournie (portée réseau, auth, périmètre) en verdict, sans rien ouvrir ni
   décider. La logique suit le contrat Python (source de vérité) ; toute
   divergence doit être corrigée côté JS. La page n'ouvre aucun port, n'accède à
   aucun NAS, n'émet rien et ne décide rien. */

const EXPOSURE_VERDICT_TONE = { guarded:'green', degraded:'yellow', exposed:'red', unknown:'blue' };

const EXPOSURE_REACH_STATE = [
  ['inconnu','Portée non fournie'],
  ['local','Local'],
  ['vpn','VPN / privé'],
  ['public','Public'],
];
const EXPOSURE_TRISTATE = [
  ['inconnu','Non fourni'],
  ['oui','Oui'],
  ['non','Non'],
];

let exposureVerifyState = { component:'', reach:'inconnu', auth:'inconnu', scope:'inconnu' };

function verifyExposureVerdict(s){
  const gaps = [];

  let reachContained = null;
  if(s.reach === 'local' || s.reach === 'vpn') reachContained = true;
  else if(s.reach === 'public') reachContained = false;
  else gaps.push('portée réseau non fournie');

  let authenticated = null;
  if(s.auth === 'oui') authenticated = true;
  else if(s.auth === 'non') authenticated = false;
  else gaps.push('authentification non fournie');

  let scoped = null;
  if(s.scope === 'oui') scoped = true;
  else if(s.scope === 'non') scoped = false;
  else gaps.push('périmètre non fourni');

  let verdict;
  if(reachContained === false && authenticated === false){ verdict = 'exposed'; gaps.push('accessible publiquement sans authentification'); }
  else if(authenticated && scoped && reachContained) verdict = 'guarded';
  else if(authenticated === false || scoped === false || reachContained === false) verdict = 'degraded';
  else verdict = 'unknown';

  return { component:(s.component || '').trim() || 'composant', reachContained, authenticated, scoped, verdict, gaps };
}

function exposureSelectHtml(id, label, opts, cur){
  return '<label>'+label+'<select id="xp_'+id+'" onchange="updateExposureVerify()">'+
    opts.map(([v,t])=>'<option value="'+v+'"'+(v===cur?' selected':'')+'>'+t+'</option>').join('')+'</select></label>';
}

function renderExposureVerifier(){
  return '<div class="card wide"><h3>Vérification d’exposition '+chip('read-only','blue')+'</h3>'+
    '<p>Renseigne la preuve déjà recueillie (portée réseau, authentification, périmètre). La page la classe en verdict comme le tool <code>verify_exposure</code> : la surface est-elle exposée sans garde. Elle n’ouvre aucun port, n’accède à aucun NAS, n’émet rien et ne décide rien.</p>'+
    '<div class="grid formgrid">'+
      '<label>Composant<input id="xp_component" placeholder="ex. openwebui" oninput="updateExposureVerify()"></label>'+
      exposureSelectHtml('reach','Portée réseau',EXPOSURE_REACH_STATE,exposureVerifyState.reach)+
      exposureSelectHtml('auth','Authentification',EXPOSURE_TRISTATE,exposureVerifyState.auth)+
      exposureSelectHtml('scope','Périmètre limité',EXPOSURE_TRISTATE,exposureVerifyState.scope)+
    '</div><div id="exposureVerifyResult" class="panel-mini"></div></div>';
}

function updateExposureVerify(){
  ['component','reach','auth','scope'].forEach(id=>{
    const el = document.getElementById('xp_'+id);
    if(el) exposureVerifyState[id] = el.value;
  });
  renderExposureVerifyResult();
}

function renderExposureVerifyResult(){
  const el = document.getElementById('exposureVerifyResult');
  if(!el) return;
  const v = verifyExposureVerdict(exposureVerifyState);
  const tri = b => b === true ? 'oui' : (b === false ? 'non' : 'inconnu');
  const gaps = v.gaps.length ? '<ul>'+v.gaps.map(g=>'<li>'+g+'</li>').join('')+'</ul>' : 'Aucun — preuve suffisante.';
  el.innerHTML = '<h3>'+v.component+' '+chip(v.verdict, EXPOSURE_VERDICT_TONE[v.verdict])+'</h3>'+
    kv('Portée contenue', tri(v.reachContained))+kv('Authentifié', tri(v.authenticated))+kv('Périmètre limité', tri(v.scoped))+
    kv('Capability gaps', gaps)+
    '<p style="margin-top:10px"><button onclick="prepareExposureVerify()">Consigner le verdict (candidat)</button></p>';
}

function prepareExposureVerify(){
  const v = verifyExposureVerdict(exposureVerifyState);
  if(typeof toast === 'function') toast('Verdict '+v.verdict+' consigné (candidat)', EXPOSURE_VERDICT_TONE[v.verdict]);
}
