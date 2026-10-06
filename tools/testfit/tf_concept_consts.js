  /* the idea diagrams stay schematic: a generic floor, not the test fit */
  const PLATE={x:50,y:50,w:1100,h:600}, NB_W=350, NB_H=210, CORE={x:500,y:290,w:200,h:120};
  const NBS=[{x:50,y:50,c:'--n1'},{x:425,y:50,c:'--n2'},{x:800,y:50,c:'--n3'},{x:50,y:440,flip:true,c:'--n4'},{x:425,y:440,flip:true,c:'--n5'},{x:800,y:440,flip:true,c:'--n6'}];
  const STREETS=[{x:50,y:260,w:1100,h:30,cls:'main'},{x:50,y:410,w:1100,h:30,cls:'main'},{x:400,y:50,w:25,h:210,cls:'up'},{x:775,y:50,w:25,h:210,cls:'up'},{x:400,y:440,w:25,h:210,cls:'down'},{x:775,y:440,w:25,h:210,cls:'down'},{x:130,y:290,w:36,h:120,cls:'conn'},{x:1034,y:290,w:36,h:120,cls:'conn'}];
  const TS_ZONES=[{x:236,y:290,w:264,h:120},{x:764,y:290,w:200,h:120}];
  const STAIRS=[{x:50,y:290,w:80,h:120},{x:1070,y:290,w:80,h:120},{x:660,y:290,w:40,h:120}];
  const LOOP='M166 275H1034Q1052 275 1052 293V407Q1052 425 1034 425H166Q148 425 148 407V293Q148 275 166 275Z';
