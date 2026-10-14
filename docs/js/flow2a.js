responsive("#flow2a","0 0 1000 1320","0 0 420 900",function(a){
  // desktop
  function card(x,y,w,h,fill,stroke,kicker,title,sub,o){o=o||{};a.box(x,y,w,h,fill,{rx:o.rx==null?18:o.rx,stroke:stroke,sw:o.sw||1.7,dash:o.dash});var cx=x+w/2;if(kicker)a.T(cx,y+25,kicker,{a:"middle",fill:"rgba(10,14,22,.58)",fs:o.kfs||11,w:900,ls:1.6});a.T(cx,y+(kicker?55:42),title,{a:"middle",fill:o.titleFill||"#0a0e16",fs:o.tfs||25,w:900});if(sub)a.T(cx,y+h-20,sub,{a:"middle",fill:o.subFill||"rgba(10,14,22,.72)",fs:o.sfs||13})}
  function pill(x,y,w,t){a.box(x,y,w,48,"#bcd8fb",{rx:14,stroke:"#5f83b8",sw:1.6});a.T(x+w/2,y+30,t,{a:"middle",fill:"#15324f",fs:15,w:800})}
  a.box(0,0,1000,1320,"#0b111d",{rx:20});
  a.box(30,30,940,1260,"rgba(255,255,255,.015)",{rx:38,stroke:"rgba(255,255,255,.18)",sw:1.8});
  a.T(500,92,"ENTRÉES · SORTIES · MÉMOIRE",{a:"middle",fill:"#bcd8fb",fs:34,w:900,ls:.5});
  a.T(500,128,"la décision humaine reste hors exécution",{a:"middle",fill:"#9aa6ba",fs:18});
  [["texte",126],["voix",318],["photo",510],["fichiers",702]].forEach(function(d){pill(d[1],160,172,d[0])});
  a.Ln(500,208,500,270,"#aebbcd",{m:"ag",sw:2.4});
  a.box(210,285,580,675,"rgba(143,198,255,.025)",{rx:30,stroke:"rgba(143,198,255,.82)",sw:1.6,dash:"7 8"});
  a.T(500,332,"PÉRIMÈTRE DE TRAVAIL IA",{a:"middle",fill:"#bcd8fb",fs:24,w:900,ls:.3});
  a.T(500,362,"corpus · contexte · workflow · résultat candidat",{a:"middle",fill:"#c6cfde",fs:16});
  card(280,395,440,110,"#bcd8fb","#5f83b8","MATIÈRE","Corpus","mémoire · web · base · templates",{tfs:30});
  card(280,570,440,70,"#e8edf5","#9aa6b3","","Contexte — strict nécessaire","",{tfs:22});
  card(280,705,440,96,"#ffcf8f","#c98f3f","ATELIER","Workflow IA","",{titleFill:"#3a2a12",tfs:28});
  card(280,860,440,90,"#fde68a","#cbb23f","","Résultat candidat qualifié","sources · preuves · statut",{dash:"7 6",titleFill:"#4a3f12",tfs:23});
  a.Ln(500,505,500,568,"#aebbcd",{m:"ag",sw:2.4});
  a.Ln(500,640,500,703,"#aebbcd",{m:"ag",sw:2.4});
  a.Ln(500,801,500,858,"#aebbcd",{m:"ag",sw:2.4});
  a.Ln(500,950,500,995,"#aebbcd",{m:"ag",sw:2.4});
  a.T(525,982,"sortie du module IA",{fill:"#9aa6ba",fs:14});
  card(210,1000,580,115,"#e2e8f0","#9aa6b3","HUMAIN · ARBITRAGE","Décision","valider · refuser · demander reprise · transmettre",{tfs:30,sfs:14});
  a.Ln(340,1115,290,1178,"#3fae6d",{m:"agg",sw:2.6});
  a.Ln(660,1115,710,1178,"#3fae6d",{m:"agg",sw:2.6});
  card(120,1180,330,90,"#86efac","#3fae6d","","Action externe","transmission · envoi · dépôt",{titleFill:"#11371f",tfs:24,sfs:13});
  card(550,1180,330,90,"#86efac","#3fae6d","","Mémoire","seuil Cerbère · candidate → canonique",{titleFill:"#11371f",tfs:24,sfs:13});
  a.P("M210,1042 H92 V450 H275","#e0a64a",{sw:2.5,dash:"8 8",m:"aa"});
  a.T(82,755,"refus → reprise",{fill:"#e0a64a",fs:21,w:800,rot:-90});
  a.P("M715,1225 H908 V450 H725","#3fae6d",{sw:2.5,dash:"7 8",m:"agg"});
  a.T(925,820,"remontée au corpus",{fill:"#3fae6d",fs:20,w:800,rot:90});
},function(a){
  // mobile — cardKicker/cardPlain : positions proportionnelles à h pour éviter les superpositions
  function cardKicker(x,y,w,h,fill,stroke,kicker,title,sub,o){o=o||{};a.box(x,y,w,h,fill,{rx:o.rx==null?14:o.rx,stroke:stroke,sw:o.sw||1.7,dash:o.dash});var cx=x+w/2;a.T(cx,y+h*0.28,kicker,{a:"middle",fill:"rgba(10,14,22,.58)",fs:o.kfs||8,w:400,ls:1.6});a.T(cx,y+h*(sub?0.56:0.60),title,{a:"middle",fill:o.titleFill||"#0a0e16",fs:o.tfs||14,w:400});if(sub)a.T(cx,y+h*0.84,sub,{a:"middle",fill:o.subFill||"rgba(10,14,22,.72)",fs:o.sfs||7.5,w:400})}
  function cardPlain(x,y,w,h,fill,stroke,title,sub,o){o=o||{};a.box(x,y,w,h,fill,{rx:o.rx==null?14:o.rx,stroke:stroke,sw:o.sw||1.7,dash:o.dash});var cx=x+w/2;if(sub){a.T(cx,y+h*0.40,title,{a:"middle",fill:o.titleFill||"#0a0e16",fs:o.tfs||12,w:400});a.T(cx,y+h*0.76,sub,{a:"middle",fill:o.subFill||"rgba(10,14,22,.72)",fs:o.sfs||7.5,w:400})}else{a.T(cx,y+h/2+4,title,{a:"middle",fill:o.titleFill||"#0a0e16",fs:o.tfs||12,w:400})}}
  function pill(x,y,w,t){a.box(x,y,w,48,"#bcd8fb",{rx:14,stroke:"#5f83b8",sw:1.6});a.T(x+w/2,y+30,t,{a:"middle",fill:"#15324f",fs:15,w:800})}
  a.box(0,0,420,900,"#0b111d",{rx:16});
  a.box(14,14,392,872,"rgba(255,255,255,.015)",{rx:24,stroke:"rgba(255,255,255,.16)",sw:1.4});
  a.T(210,48,"ENTRÉES · SORTIES · MÉMOIRE",{a:"middle",fill:"#bcd8fb",fs:18,w:900});
  a.T(210,71,"la décision humaine reste hors exécution",{a:"middle",fill:"#9aa6ba",fs:10.5});
  [["texte",32],["voix",122],["photo",212],["fichiers",302]].forEach(function(d){pill(d[1],92,74,d[0])});
  a.Ln(210,140,210,176,"#aebbcd",{m:"ag",sw:2});
  a.box(84,184,252,430,"rgba(143,198,255,.025)",{rx:20,stroke:"rgba(143,198,255,.82)",sw:1.3,dash:"6 7"});
  a.T(210,214,"PÉRIMÈTRE DE TRAVAIL IA",{a:"middle",fill:"#bcd8fb",fs:13,w:900});
  a.T(210,233,"corpus · contexte · workflow · candidat",{a:"middle",fill:"#c6cfde",fs:9});
  cardKicker(110,255,200,62,"#bcd8fb","#5f83b8","MATIÈRE","Corpus","mémoire · web · base · templates",{kfs:8,tfs:16,sfs:7.4});
  cardPlain(110,352,200,42,"#e8edf5","#9aa6b3","Contexte — strict nécessaire","",{tfs:10.6});
  cardKicker(110,430,200,52,"#ffcf8f","#c98f3f","ATELIER","Workflow IA","",{kfs:8,titleFill:"#3a2a12",tfs:14});
  cardPlain(110,520,200,54,"#fde68a","#cbb23f","Résultat candidat qualifié","sources · preuves · statut",{dash:"6 5",titleFill:"#4a3f12",tfs:11.6,sfs:7.8});
  a.Ln(210,317,210,350,"#aebbcd",{m:"ag",sw:1.8});a.Ln(210,394,210,428,"#aebbcd",{m:"ag",sw:1.8});a.Ln(210,482,210,518,"#aebbcd",{m:"ag",sw:1.8});a.Ln(210,574,210,636,"#aebbcd",{m:"ag",sw:1.8});
  a.T(218,620,"sortie du module IA",{fill:"#9aa6ba",fs:8});
  cardKicker(65,640,290,66,"#e2e8f0","#9aa6b3","HUMAIN · ARBITRAGE","Décision","valider · refuser · demander reprise · transmettre",{kfs:8,tfs:17,sfs:7.7});
  a.Ln(132,706,118,742,"#3fae6d",{m:"agg",sw:2});a.Ln(288,706,302,742,"#3fae6d",{m:"agg",sw:2});
  cardPlain(28,744,176,58,"#86efac","#3fae6d","Action externe","transmission · envoi · dépôt",{titleFill:"#11371f",tfs:13,sfs:7.5});
  cardPlain(216,744,176,58,"#86efac","#3fae6d","Mémoire","seuil Cerbère · candidate → canonique",{titleFill:"#11371f",tfs:13,sfs:7.4});
  a.P("M66,672 H35 V300 H108","#e0a64a",{sw:1.7,dash:"6 6",m:"aa"});a.T(28,500,"refus → reprise",{fill:"#e0a64a",fs:9,w:800,rot:-90});
  a.P("M304,802 H388 V300 H312","#3fae6d",{sw:1.7,dash:"6 6",m:"agg"});a.T(398,540,"remontée au corpus",{fill:"#3fae6d",fs:9,w:800,rot:90});
});
