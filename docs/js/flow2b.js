responsive("#flow2b","0 0 960 700","0 0 380 662",function(a){
  // desktop
  a.box(0,0,960,700,"#0b111d",{rx:16});
  a.T(480,36,"DANS « WORKFLOW IA » — RÔLES · WORKFLOWS · SKILLS",{a:"middle",fill:"#f0b46a",fs:15,w:800});
  a.T(480,58,"Des rôles de jugement (pas des agents autonomes) qui produisent des candidats sous Task Contract",{a:"middle",fill:"#9aa6ba",fs:11});
  a.T(40,96,"LE COLLÈGE — qui fait quoi",{fill:"#8aa0b8",fs:11,w:800,ls:1.4});
  [["MÈTIS","tient le cap",37],["ATHENA","planifie",165],["ARGOS","sources & preuves",293],["HÉPHAÏSTOS","construit",421],["THÉMIS","risque · veto",549],["APOLLON","qualité",677],["IRIS","formule · transmet",805]].forEach(function(d){a.box(d[2],106,118,58,"#cdbdf0",{rx:11,stroke:"#7a66b8",sw:1});a.T(d[2]+59,132,d[0],{a:"middle",fill:"#2c2150",fs:11,w:800});a.T(d[2]+59,150,d[1],{a:"middle",fill:"#4b3d80",fs:9,w:600})});
  [[155,163],[283,291],[411,419],[539,547],[667,675],[795,803]].forEach(function(d){a.Ln(d[0],135,d[1],135,"#9a86c8",{sw:1.6,m:"ap"})});
  a.P("M864,164 Q480,210 96,164","#9a86c8",{sw:2,dash:"7 5",m:"ap",cls:"flow"});
  a.T(480,199,"↻ itération bornée — ZEUS renvoie à MÈTIS tant que le cap ou la preuve manquent",{a:"middle",fill:"#b7a6e0",fs:10,w:700});
  a.box(37,220,886,24,"none",{rx:9,stroke:"#d8b24a",sw:1.3,dash:"5 4"});a.T(480,236,"ZEUS — arbitre le cap et le statut, sur preuve",{a:"middle",fill:"#e0c067",fs:11,w:700});
  a.T(40,290,"WORKFLOWS — jamais automatique par naissance · durable par preuve",{fill:"#8aa0b8",fs:11,w:800,ls:1});
  a.T(40,310,"Un workflow gagne en autorité par la preuve, pas par défaut — et reste désactivable à tout moment.",{fill:"#9fb0c2",fs:11});
  [["off",40,56,0],["draft",124,64,0],["shadow",216,80,0],["assist",324,70,0],["propose",422,84,0],["durable",534,90,1]].forEach(function(d){a.box(d[1],322,d[2],26,d[3]?"#16271d":"#1e2a37",{rx:9,stroke:d[3]?"#58c489":"#3a4a5d",sw:1});a.T(d[1]+d[2]/2,339,d[0],{a:"middle",fill:d[3]?"#8fe6a8":"#9fb0c2",fs:11,w:d[3]?700:400})});
  [[96,122],[188,214],[296,322],[394,420],[506,532]].forEach(function(d){a.Ln(d[0],335,d[1],335,"#8b98a6",{sw:1.5,m:"gg"})});
  a.T(40,378,"off : existe mais ne fait rien · shadow : observe et trace ce qu'il aurait fait · durable : de confiance, prouvé",{fill:"#7f8b99",fs:10.5});
  a.T(40,424,"SKILLS — les capacités des agents Hermes",{fill:"#8aa0b8",fs:11,w:800,ls:1});
  a.T(40,446,"Les compétences concrètes que les agents Hermes mobilisent pour exécuter : lire un document (OCR),",{fill:"#c5d0db",fs:11.5});
  a.T(40,463,"extraire une donnée, comparer deux pièces, rédiger une synthèse.",{fill:"#c5d0db",fs:11.5});
  a.T(40,484,"Elles appartiennent au runtime d'exécution (Hermes). Pantheon n'en installe ni n'en exécute aucune :",{fill:"#9fb0c2",fs:11});
  a.T(40,501,"il en gouverne le cycle — proposée → testée → activée → désactivable — et les garde candidates.",{fill:"#9fb0c2",fs:11});
  [["OCR",40,70],["extraction",122,104],["comparaison",238,118],["rédaction",368,100],["classement",480,104]].forEach(function(d){a.box(d[1],516,d[2],26,"#a8d8e8",{rx:9,stroke:"#5f93b8",sw:1});a.T(d[1]+d[2]/2,533,d[0],{a:"middle",fill:"#123047",fs:10.5,w:700})});
  a.box(596,516,96,26,"none",{rx:9,stroke:"#5f93b8",dash:"4 3"});a.T(644,533,"candidates",{a:"middle",fill:"#8fb6cc",fs:10.5,w:600});
  a.Ln(40,566,920,566,"rgba(255,255,255,.1)",{sw:1});
  a.T(480,596,"Le Collège produit un Résultat candidat + un Evidence Pack (preuve auditable).",{a:"middle",fill:"#cdeedd",fs:11.5,w:700});
  a.T(480,615,"Il ne décide pas · ne canonise pas · ne transmet pas — c'est l'humain qui tranche, hors cadre.",{a:"middle",fill:"#7f9d8c",fs:10.5});
  a.box(332,632,140,28,"#2a2417",{rx:9,stroke:"#e0a64a"});a.T(402,650,"Task Contract",{a:"middle",fill:"#e0b84a",fs:10.5,w:700});a.box(488,632,140,28,"#16271d",{rx:9,stroke:"#58c489"});a.T(558,650,"Evidence Pack",{a:"middle",fill:"#8fe6a8",fs:10.5,w:700});
},function(a){
  // mobile
  a.box(0,0,380,662,"#0b111d",{rx:16});
  a.T(190,22,"« WORKFLOW IA »",{a:"middle",fill:"#f0b46a",fs:13,w:800});
  a.T(190,39,"rôles · workflows · skills",{a:"middle",fill:"#9aa6ba",fs:9});
  a.T(16,62,"LE COLLÈGE",{fill:"#8aa0b8",fs:9.5,w:800,ls:1.2});
  [["MÈTIS","tient le cap",16,70],["ATHENA","planifie",196,70],["ARGOS","sources & preuves",16,120],["HÉPHAÏSTOS","construit",196,120],["THÉMIS","risque · veto",16,170],["APOLLON","qualité",196,170],["IRIS","formule · transmet",16,220]].forEach(function(d){a.box(d[2],d[3],168,42,"#cdbdf0",{rx:10,stroke:"#7a66b8",sw:1});a.T(d[2]+84,d[3]+18,d[0],{a:"middle",fill:"#2c2150",fs:10.5,w:800});a.T(d[2]+84,d[3]+33,d[1],{a:"middle",fill:"#4b3d80",fs:8,w:600})});
  a.T(190,284,"↻ ZEUS renvoie à MÈTIS si cap / preuve manquent",{a:"middle",fill:"#b7a6e0",fs:8.3,w:600});
  a.box(16,294,348,24,"none",{rx:9,stroke:"#d8b24a",sw:1.3,dash:"5 4"});a.T(190,310,"ZEUS — arbitre, sur preuve",{a:"middle",fill:"#e0c067",fs:10,w:700});
  a.T(16,344,"WORKFLOWS — durable par preuve",{fill:"#8aa0b8",fs:9.5,w:800,ls:1});
  [["off",16,354,46,0],["draft",70,354,56,0],["shadow",134,354,72,0],["assist",214,354,62,0],["propose",16,384,76,0],["durable",100,384,80,1]].forEach(function(d){a.box(d[1],d[2],d[3],24,d[4]?"#16271d":"#1e2a37",{rx:9,stroke:d[4]?"#58c489":"#3a4a5d",sw:1});a.T(d[1]+d[3]/2,d[2]+16,d[0],{a:"middle",fill:d[4]?"#8fe6a8":"#9fb0c2",fs:10,w:d[4]?700:400})});
  a.T(16,430,"jamais automatique ; durable = de confiance, prouvé",{fill:"#7f8b99",fs:8.5});
  a.T(16,460,"SKILLS — capacités des agents Hermes",{fill:"#8aa0b8",fs:9.5,w:800,ls:1});
  a.T(16,478,"gouvernées comme candidates (Hermes exécute)",{fill:"#9fb0c2",fs:8.8});
  [["OCR",16,490,56],["extraction",80,490,92],["comparaison",180,490,104],["rédaction",16,520,84],["classement",108,520,92]].forEach(function(d){a.box(d[1],d[2],d[3],24,"#a8d8e8",{rx:9,stroke:"#5f93b8",sw:1});a.T(d[1]+d[3]/2,d[2]+16,d[0],{a:"middle",fill:"#123047",fs:9.5,w:700})});
  a.box(208,520,96,24,"none",{rx:9,stroke:"#5f93b8",dash:"4 3"});a.T(256,536,"candidates",{a:"middle",fill:"#8fb6cc",fs:9.5,w:600});
  a.T(190,572,"Produit un Résultat candidat + Evidence Pack.",{a:"middle",fill:"#cdeedd",fs:9.3,w:700});
  a.T(190,587,"L'humain tranche, hors cadre.",{a:"middle",fill:"#7f9d8c",fs:8.8});
  a.box(44,600,140,26,"#2a2417",{rx:9,stroke:"#e0a64a"});a.T(114,617,"Task Contract",{a:"middle",fill:"#e0b84a",fs:10,w:700});a.box(196,600,140,26,"#16271d",{rx:9,stroke:"#58c489"});a.T(266,617,"Evidence Pack",{a:"middle",fill:"#8fe6a8",fs:10,w:700});
});
