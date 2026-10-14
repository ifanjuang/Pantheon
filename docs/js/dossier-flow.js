(function(){
  if(typeof d3==='undefined') return;
  var svg=d3.select('#dossierFlow'); if(svg.empty()) return;
  var col={pieces:"#8fc6ff",corpus:"#b7d8ff",context:"#dbeafe",work:"#ffcf8f",output:"#fde68a",decision:"#e2e8f0",memory:"#86efac"};
  function node(a,c,x,y,w,h,role,title,sub){a.box(x,y,w,h,c,{rx:15,stroke:"rgba(255,255,255,.18)",sw:1.4});var cx=x+w/2;a.T(cx,y+18,role,{a:"middle",fill:"rgba(10,14,22,.62)",fs:9.5,w:900,ls:1});a.T(cx,y+40,title,{a:"middle",fill:"#0a0e16",fs:15,w:900});a.T(cx,y+h-12,sub,{a:"middle",fill:"rgba(10,14,22,.72)",fs:10.5})}
  function draw(){
    var w=svg.node().parentNode.getBoundingClientRect().width, mobile=w<680;
    svg.selectAll("*").remove(); var a=mk(svg); marks(svg);
    if(mobile){
      svg.attr("viewBox","0 0 360 740");
      a.box(40,104,280,388,"rgba(253,230,138,0.05)",{rx:18,stroke:"rgba(253,230,138,0.5)",sw:1.4,dash:"6 7"});
      a.T(180,96,"cadre Pantheon · définit le corpus",{a:"middle",fill:"rgba(253,230,138,0.9)",fs:10.5,w:800});
      a.P("M312,448 L344,448 L344,150 L312,150","#e0b84a",{sw:1.8,dash:"6 6",m:"ago"});
      a.P("M50,690 L18,690 L18,150 L48,150","#3fae6d",{sw:1.8,dash:"5 6",m:"agg"});
      a.Ln(180,80,180,114,"#aebbcd",{m:"ag"});a.Ln(180,180,180,214,"#aebbcd",{m:"ag"});a.Ln(180,280,180,314,"#aebbcd",{m:"ag"});a.Ln(180,380,180,414,"#aebbcd",{m:"ag"});a.Ln(180,480,180,538,"#aebbcd",{m:"ag"});a.Ln(180,604,180,658,"#3fae6d",{m:"agg"});
      node(a,col.pieces,50,16,260,64,"ENTRÉE","Pièces","plans · CR · devis");
      node(a,col.corpus,50,116,260,64,"MATIÈRE","Corpus","classé · situé");
      node(a,col.context,50,216,260,64,"FILTRE","Contexte","strict nécessaire");
      node(a,col.work,50,316,260,64,"ATELIER","Travail IA","cherche · compare");
      node(a,col.output,50,416,260,64,"SORTIE","Résultat","sources · statut");
      node(a,col.decision,50,540,260,64,"HORS CADRE","Décision","valider · refuser");
      node(a,col.memory,50,660,260,64,"MÉMOIRE","Validée","bornée · sourcée");
    } else {
      svg.attr("viewBox","0 0 960 430");
      a.box(38,118,872,120,"rgba(253,230,138,0.05)",{rx:20,stroke:"rgba(253,230,138,0.5)",sw:1.6,dash:"6 7"});
      a.T(900,138,"CADRE PANTHEON · définit le corpus",{a:"end",fill:"rgba(253,230,138,0.9)",fs:11.5,w:800});
      a.P("M825,150 C825,50 360,50 322,146","#e0b84a",{sw:2,dash:"6 7",m:"ago"});
      a.T(575,44,"reprise · le résultat peut réalimenter le corpus",{a:"middle",fill:"#fde68a",fs:10.5,w:600});
      a.P("M160,108 L246,150","#aebbcd",{sw:2.2,m:"ag"});
      a.Ln(375,186,398,186,"#aebbcd",{sw:2.2,m:"ag"});a.Ln(550,186,573,186,"#aebbcd",{sw:2.2,m:"ag"});a.Ln(725,186,748,186,"#aebbcd",{sw:2.2,m:"ag"});
      a.Ln(825,222,825,298,"#aebbcd",{sw:2.2,m:"ag"});
      a.T(836,266,"le résultat qualifié",{fill:"#9aa6ba",fs:10});a.T(836,280,"sort vers ta décision",{fill:"#9aa6ba",fs:10});
      a.Ln(195,186,221,186,"#3fae6d",{sw:2.2,m:"agg"});a.T(158,210,"enrichit",{fill:"#3fae6d",fs:9.5});
      a.P("M760,332 C430,406 240,300 128,224","#3fae6d",{sw:2,dash:"5 6",m:"agg"});
      a.T(455,384,"le validé devient mémoire (bornée, sourcée)",{a:"middle",fill:"#3fae6d",fs:10.5,w:600});
      node(a,col.pieces,85,36,150,72,"ENTRÉE","Pièces","plans · CR · devis · mails");
      node(a,col.memory,45,150,150,72,"MÉMOIRE","Validée","bornée · sourcée");
      node(a,col.corpus,225,150,150,72,"MATIÈRE","Corpus","classé · situé");
      node(a,col.context,400,150,150,72,"FILTRE","Contexte","strict nécessaire");
      node(a,col.work,575,150,150,72,"ATELIER","Travail IA","cherche · compare");
      node(a,col.output,750,150,150,72,"SORTIE","Résultat","sources · statut");
      node(a,col.decision,750,300,150,72,"HORS CADRE","Décision","valider · refuser");
    }
  }
  draw(); var r; window.addEventListener("resize",function(){clearTimeout(r);r=setTimeout(draw,120)});
})();
