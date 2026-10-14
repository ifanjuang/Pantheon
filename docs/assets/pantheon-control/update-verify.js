/* Pantheon Control — vérification de mise à jour (read-only).
   Reflet fidèle de mcp-server verify_update(evidence) : compare une version
   courante et une version disponible (toutes deux fournies) en verdict, sans
   rien aller chercher ni installer. La logique — y compris le parse/compare de
   version — suit le contrat Python (source de vérité) ; toute divergence doit
   être corrigée côté JS. La page ne récupère aucune version, n'installe rien et
   ne décide rien. */

const UPDATE_VERDICT_TONE = { current:'green', update_available:'yellow', ahead:'blue', unknown:'muted' };

let updateVerifyState = { component:'', current_version:'', available_version:'' };

function parseUpdateVersion(value){
  if(typeof value !== 'string') return null;
  let text = value.trim();
  if(!text) return null;
  text = text.replace(/^[vV]+/, '');
  text = text.split(/[-+ ]/)[0];
  let sawNumber = false;
  const out = text.split('.').map(part => { const m = part.match(/^\d+/); if(m){ sawNumber = true; return parseInt(m[0], 10); } return 0; });
  return sawNumber ? out : null;
}

function compareUpdateVersion(a, b){
  const pa = parseUpdateVersion(a), pb = parseUpdateVersion(b);
  if(pa === null || pb === null) return null;
  const n = Math.max(pa.length, pb.length);
  while(pa.length < n) pa.push(0);
  while(pb.length < n) pb.push(0);
  for(let i = 0; i < n; i++){ if(pa[i] < pb[i]) return -1; if(pa[i] > pb[i]) return 1; }
  return 0;
}

function verifyUpdateVerdict(s){
  const gaps = [];
  const current = s.current_version, available = s.available_version;
  if(!(typeof current === 'string' && current.trim())) gaps.push('version courante non fournie');
  else if(parseUpdateVersion(current) === null) gaps.push('version courante non comparable');
  if(!(typeof available === 'string' && available.trim())) gaps.push('version disponible non fournie');
  else if(parseUpdateVersion(available) === null) gaps.push('version disponible non comparable');

  const cmp = compareUpdateVersion(current, available);
  let verdict;
  if(cmp === null) verdict = 'unknown';
  else if(cmp === 0) verdict = 'current';
  else if(cmp < 0) verdict = 'update_available';
  else verdict = 'ahead';

  return { component:(s.component || '').trim() || 'composant', current_version:current || null, available_version:available || null, verdict, gaps };
}

function renderUpdateVerifier(){
  return '<div class="card wide"><h3>Vérification de mise à jour '+chip('read-only','blue')+'</h3>'+
    '<p>Renseigne la version courante et la dernière version disponible (déjà connues). La page les compare comme le tool <code>verify_update</code> : une mise à jour est-elle disponible. Elle ne récupère aucune version, n’installe rien et ne décide rien.</p>'+
    '<div class="grid formgrid">'+
      '<label>Composant<input id="up_component" placeholder="ex. hermes" oninput="updateUpdateVerify()"></label>'+
      '<label>Version courante<input id="up_current_version" placeholder="ex. 1.4.2" oninput="updateUpdateVerify()"></label>'+
      '<label>Version disponible<input id="up_available_version" placeholder="ex. 1.5.0" oninput="updateUpdateVerify()"></label>'+
    '</div><div id="updateVerifyResult" class="panel-mini"></div></div>';
}

function updateUpdateVerify(){
  ['component','current_version','available_version'].forEach(id=>{
    const el = document.getElementById('up_'+id);
    if(el) updateVerifyState[id] = el.value;
  });
  renderUpdateVerifyResult();
}

function renderUpdateVerifyResult(){
  const el = document.getElementById('updateVerifyResult');
  if(!el) return;
  const v = verifyUpdateVerdict(updateVerifyState);
  const gaps = v.gaps.length ? '<ul>'+v.gaps.map(g=>'<li>'+g+'</li>').join('')+'</ul>' : 'Aucun — preuve suffisante.';
  el.innerHTML = '<h3>'+v.component+' '+chip(v.verdict, UPDATE_VERDICT_TONE[v.verdict])+'</h3>'+
    kv('Version courante', v.current_version || 'inconnue')+kv('Version disponible', v.available_version || 'inconnue')+
    kv('Capability gaps', gaps)+
    '<p style="margin-top:10px"><button onclick="prepareUpdateVerify()">Consigner le verdict (candidat)</button></p>';
}

function prepareUpdateVerify(){
  const v = verifyUpdateVerdict(updateVerifyState);
  if(typeof toast === 'function') toast('Verdict '+v.verdict+' consigné (candidat)', UPDATE_VERDICT_TONE[v.verdict]);
}
