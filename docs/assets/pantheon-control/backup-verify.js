/* Pantheon Control — vérification de sauvegarde / récupérabilité (read-only).
   Reflet fidèle de mcp-server verify_backup(evidence) : classe une preuve fournie
   (sauvegarde présente, fraîcheur, restauration démontrée) en verdict, sans rien
   exécuter ni décider. La logique suit le contrat Python (source de vérité) ;
   toute divergence doit être corrigée côté JS. La page ne lance aucune sauvegarde
   ni restauration, n'accède à aucun NAS et ne décide rien. */

const BACKUP_VERDICT_TONE = { protected:'green', degraded:'yellow', unprotected:'muted', unknown:'blue' };

const BACKUP_TRISTATE = [
  ['inconnu','Non fourni'],
  ['oui','Oui'],
  ['non','Non'],
];

let backupVerifyState = { component:'', present:'inconnu', recent:'inconnu', restore:'inconnu' };

function verifyBackupVerdict(s){
  const gaps = [];

  let present = null;
  if(s.present === 'oui') present = true;
  else if(s.present === 'non') present = false;
  else gaps.push('présence de sauvegarde non fournie');

  let recent = null;
  if(s.recent === 'oui') recent = true;
  else if(s.recent === 'non'){ recent = false; gaps.push('sauvegarde périmée'); }
  else gaps.push('fraîcheur non fournie');

  let restoreVerified = null;
  if(s.restore === 'oui') restoreVerified = true;
  else if(s.restore === 'non'){ restoreVerified = false; gaps.push('restauration non démontrée'); }
  else gaps.push('preuve de restauration non fournie');

  let verdict;
  if(present === false) verdict = 'unprotected';
  else if(present && recent && restoreVerified) verdict = 'protected';
  else if(present && (recent === false || restoreVerified === false)) verdict = 'degraded';
  else verdict = 'unknown';

  return { component:(s.component || '').trim() || 'composant', present, recent, restoreVerified, verdict, gaps };
}

function backupSelectHtml(id, label, cur){
  return '<label>'+label+'<select id="bk_'+id+'" onchange="updateBackupVerify()">'+
    BACKUP_TRISTATE.map(([v,t])=>'<option value="'+v+'"'+(v===cur?' selected':'')+'>'+t+'</option>').join('')+'</select></label>';
}

function renderBackupVerifier(){
  return '<div class="card wide"><h3>Vérification de sauvegarde '+chip('read-only','blue')+'</h3>'+
    '<p>Renseigne la preuve déjà recueillie (sauvegarde présente, récente, restauration testée). La page la classe en verdict comme le tool <code>verify_backup</code> : si ça meurt, peut-on restaurer. Elle ne lance aucune sauvegarde ni restauration, n’accède à aucun NAS et ne décide rien.</p>'+
    '<div class="grid formgrid">'+
      '<label>Composant<input id="bk_component" placeholder="ex. registre-probatoire" oninput="updateBackupVerify()"></label>'+
      backupSelectHtml('present','Sauvegarde présente',backupVerifyState.present)+
      backupSelectHtml('recent','Récente',backupVerifyState.recent)+
      backupSelectHtml('restore','Restauration démontrée',backupVerifyState.restore)+
    '</div><div id="backupVerifyResult" class="panel-mini"></div></div>';
}

function updateBackupVerify(){
  ['component','present','recent','restore'].forEach(id=>{
    const el = document.getElementById('bk_'+id);
    if(el) backupVerifyState[id] = el.value;
  });
  renderBackupVerifyResult();
}

function renderBackupVerifyResult(){
  const el = document.getElementById('backupVerifyResult');
  if(!el) return;
  const v = verifyBackupVerdict(backupVerifyState);
  const tri = b => b === true ? 'oui' : (b === false ? 'non' : 'inconnu');
  const gaps = v.gaps.length ? '<ul>'+v.gaps.map(g=>'<li>'+g+'</li>').join('')+'</ul>' : 'Aucun — preuve suffisante.';
  el.innerHTML = '<h3>'+v.component+' '+chip(v.verdict, BACKUP_VERDICT_TONE[v.verdict])+'</h3>'+
    kv('Sauvegarde présente', tri(v.present))+kv('Récente', tri(v.recent))+kv('Restauration démontrée', tri(v.restoreVerified))+
    kv('Capability gaps', gaps)+
    '<p style="margin-top:10px"><button onclick="prepareBackupVerify()">Consigner le verdict (candidat)</button></p>';
}

function prepareBackupVerify(){
  const v = verifyBackupVerdict(backupVerifyState);
  if(typeof toast === 'function') toast('Verdict '+v.verdict+' consigné (candidat)', BACKUP_VERDICT_TONE[v.verdict]);
}
