/* =====================================================================
   PROJECT CONTENT
   The plan comes from the test-fit DXF (ACKO_Testfit_02_5.10.26). Everything in RF
   (outline, cores, partitions, furniture, rooms, desks, egress routes, zones) was
   read from that drawing. Names, teams and colours below are still placeholders.
   ===================================================================== */
const RF=/*REALFIT*/null;
const PROJECT={ floor:'Test fit 02', site:'Bengaluru', source:'ACKO_Testfit_02_5.10.26.dxf' };
const NBS=[
  {id:'N01',name:'Neighbourhood 01',team:'Engineering',          c:'--n1',pos:'West end, by Stair 1'},
  {id:'N02',name:'Neighbourhood 02',team:'Product & Design',     c:'--n2',pos:'West-centre'},
  {id:'N03',name:'Neighbourhood 03',team:'Data & Analytics',     c:'--n3',pos:'Centre, by the lifts'},
  {id:'N04',name:'Neighbourhood 04',team:'Claims',               c:'--n4',pos:'East-centre, by Stair 4'},
  {id:'N05',name:'Neighbourhood 05',team:'Customer Experience',  c:'--n5',pos:'East, around Stair 5'},
  {id:'N06',name:'Neighbourhood 06',team:'Sales & Partnerships', c:'--n6',pos:'East end'},
];
/* the shared spaces everyone uses */
const SHARED=[
  {id:'TW',name:'Café and dining',            short:'Café',       sub:'West, beside Stair 1 and Stair 2'},
  {id:'R1',name:'Reception and visitor hub',  short:'Reception',  sub:'West reception, beside the west terrace'},
  {id:'TC',name:'Lobby',                      short:'Lobby',      sub:'Centre, by the lifts'},
  {id:'R2',name:'Reception and waiting lounge',short:'Reception', sub:'East reception, beside the east terrace'},
];

/* =====================================================================
   GEOMETRY (drawing units; 1 unit = 50 mm)
   ===================================================================== */
const U=RF.unit, SQFT=10.7639;
const toM=u=>u*U, m2ft=m=>m*SQFT;
const fmt=n=>Math.round(n).toLocaleString('en-IN');
const bounds=pts=>{ const xs=pts.map(p=>p[0]), ys=pts.map(p=>p[1]); return {x0:Math.min(...xs),y0:Math.min(...ys),x1:Math.max(...xs),y1:Math.max(...ys)}; };
const PB=bounds(RF.plate);
const PADX=150, PADY=170;
const VBX=Math.floor(PB.x0-PADX), VBY=Math.floor(PB.y0-PADY), VBW=Math.ceil(PB.x1-PB.x0+2*PADX), VBH=Math.ceil(PB.y1-PB.y0+2*PADY);
const VB=`${VBX} ${VBY} ${VBW} ${VBH}`;
const PW=1600, PH=Math.round(PW*VBH/VBW), PS=PW/VBW;   // plan box in px, px per unit
const AREA_IDS=['N01','N02','N03','N04','N05','N06','R1','R2','TW','TC'];
const isNB=a=>/^N\d\d$/.test(a), isTS=a=>a==='TW'||a==='TC'||a==='R1'||a==='R2';
const ctxOf=a=>isNB(a)?a:isTS(a)?'TS':null;   // neighbourhood id, 'TS' for the shared spaces, null elsewhere
const PD=pts=>'M'+pts.map(p=>p[0]+' '+p[1]).join('L')+'Z';
const centroid=pts=>{ let a=0,cx=0,cy=0; pts.forEach((p,i)=>{ const q=pts[(i+1)%pts.length], f=p[0]*q[1]-q[0]*p[1]; a+=f; cx+=(p[0]+q[0])*f; cy+=(p[1]+q[1])*f; }); a/=2; return {x:cx/(6*a),y:cy/(6*a)}; };
const ROUTES=RF.routes.map(r=>Object.assign({},r,{nb:isNB(r.a)?r.a:nearestNB(r.pts[0])}));
function nearestNB(p){ let best=null,bd=1e9; NBS.forEach(nb=>{ const l=RF.lab[nb.id], d=Math.hypot(l[0]-p[0],l[1]-p[1]); if(d<bd){bd=d;best=nb.id;} }); return best; }
const STAIRS=RF.stairs;
const polyM2=p=>Math.abs(p.reduce((a,q,i)=>{ const r=p[(i+1)%p.length]; return a+q[0]*r[1]-r[0]*q[1]; },0)/2)*U*U;

/* ---------- svg string helpers ---------- */
const r1=n=>Math.round(n*10)/10;
const dk=k=>k?` data-k="${k}"`:'';
const R=(r,c,k,rx)=>`<rect x="${r1(r.x)}" y="${r1(r.y)}" width="${r1(r.w)}" height="${r1(r.h)}"${rx?` rx="${rx}"`:''} class="${c}"${dk(k)}/>`;
const C=(p,rad,c,k)=>`<circle cx="${r1(p.x)}" cy="${r1(p.y)}" r="${rad}" class="${c}"${dk(k)}/>`;
const L=(a,b,c,k)=>`<line x1="${r1(a.x)}" y1="${r1(a.y)}" x2="${r1(b.x)}" y2="${r1(b.y)}" class="${c}"${dk(k)}/>`;
const T=(x,y,t,c,extra)=>`<text x="${r1(x)}" y="${r1(y)}" class="${c}"${extra||''}>${t}</text>`;
const PA=(d,c,k,extra)=>`<path d="${d}" class="${c}"${dk(k)}${extra||''}/>`;
const DRAW=(d,c,delay)=>`<path d="${d}" pathLength="1" class="${c} draw" style="--d:${delay}s"/>`;
const G=(grp,area)=>(RF.g[grp]||{})[area]||'';

/* ---------- kit per area, counted from the drawing ---------- */
const KIND_ORDER=['desk','cabin','sprint','dept','huddle','hatchery','duo','booth','pantry','zen','prayer','mother','cafe','reception','lobby','visitor','board','studio'];
function kitOf(a){
  const k={desk:0,deskSeats:0,table4:0,green:0};
  RF.desks.forEach(d=>{ if(d[3]===a){ k.desk+=d[2]; if(d[4]) k.table4++; } });
  RF.rooms.forEach(r=>{ if(r.a===a){ k[r.k]=(k[r.k]||0)+1; k[r.k+'Seats']=(k[r.k+'Seats']||0)+r.s; } });
  RF.pantries.forEach(p=>{ if(p.a===a) k.pantry=(k.pantry||0)+1; });
  return k;
}
const KITS={}; AREA_IDS.concat(['X']).forEach(a=>KITS[a]=kitOf(a));
const sumK=(ids,key)=>ids.reduce((s,a)=>s+(KITS[a][key]||0),0);
const NB_IDS=NBS.map(n=>n.id), ALL_IDS=AREA_IDS.concat(['X']);
const nbIndex=id=>NB_IDS.indexOf(id);
const nbName=id=>NBS[nbIndex(id)].name;
const TOT={
  desks:sumK(ALL_IDS,'desk'), sprint:sumK(ALL_IDS,'sprint'), huddle:sumK(ALL_IDS,'huddle'), dept:sumK(ALL_IDS,'dept'), board:sumK(ALL_IDS,'board'),
  hatchery:sumK(ALL_IDS,'hatchery'), visitor:sumK(ALL_IDS,'visitor'), duo:sumK(ALL_IDS,'duo'), booth:sumK(ALL_IDS,'booth'), zen:sumK(ALL_IDS,'zen'),
  cabin:sumK(ALL_IDS,'cabin'), pantry:RF.pantries.length, daylight:RF.daylight,
  plateM2:RF.plateM2, longest:Math.max(...RF.routes.map(r=>r.m)), shortest:Math.min(...RF.routes.map(r=>r.m)),
};
TOT.meet=TOT.sprint+TOT.huddle+TOT.dept+TOT.board+TOT.hatchery+TOT.visitor;
const M2=RF.areaM2, nbM2=NB_IDS.reduce((s,a)=>s+M2[a],0), tsM2=M2.TW+M2.TC+M2.R1+M2.R2;
const AREA=[
  {label:'Neighbourhoods',m2:nbM2,c:null},
  {label:'Receptions',m2:M2.R1+M2.R2,c:'var(--brand-2)'},
  {label:'Café and lobby',m2:M2.TW+M2.TC,c:'var(--brand)'},
  {label:'Cores, corridors and other',m2:RF.plateM2-nbM2-tsM2,c:'var(--ink-3)'},
];

/* ---------- clickable spaces (each opens its renders) ---------- */
const SP=[];
const ROOM_SIZE={booth:[30,24],duo:[50,50],sprint:[64,70],huddle:[96,90],dept:[130,110],board:[160,120],hatchery:[110,90],visitor:[56,56],zen:[60,60],cabin:[80,80],prayer:[70,70],mother:[50,50],studio:[80,70]};
function addSP(o){ o.i=SP.length; SP.push(o); return o; }
const rectPts=(x,y,w,h)=>[[x-w/2,y-h/2],[x+w/2,y-h/2],[x+w/2,y+h/2],[x-w/2,y+h/2]];
/* whole-area hits first, so the rooms inside sit on top of them */
[['TW','cafe'],['TC','lobby'],['R1','reception'],['R2','reception']].forEach(([a,k])=>addSP({k,nb:'TS',area:a,seats:0,pts:RF.areas[a],big:true}));
RF.desks.forEach(d=>{ const ctx=ctxOf(d[3]); if(ctx) addSP({k:'desk',nb:ctx,area:d[3],seats:d[2],pts:rectPts(d[0],d[1],d[4]?50:48,d[4]?50:48),x:d[0],y:d[1]}); });
RF.pantries.forEach(p=>{ const ctx=ctxOf(p.a); if(ctx) addSP({k:'pantry',nb:ctx,area:p.a,seats:0,pts:rectPts(p.x,p.y,90,64),x:p.x,y:p.y}); });
RF.rooms.forEach(r=>{ const ctx=ctxOf(r.a); if(!ctx||!ROOM_SIZE[r.k]) return; const sz=ROOM_SIZE[r.k]; addSP({k:r.k,nb:ctx,area:r.a,seats:r.s,t:r.t,pts:r.poly||rectPts(r.x,r.y,sz[0],sz[1]),x:r.x,y:r.y,m2:r.m2}); });
const hitsFor=a=>SP.filter(s=>s.area===a).map(s=>`<polygon points="${s.pts.map(p=>r1(p[0])+','+r1(p[1])).join(' ')}" class="hit${s.big?' big':''}" data-sp="${s.i}" data-k="${s.k}"/>`).join('');
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
/* furthest any desk is from a meeting space, a phone booth and a pantry in the same neighbourhood */
function reach(a){
  const pts=k=>SP.filter(s=>s.area===a&&k.includes(s.k)).map(s=>({x:s.x,y:s.y}));
  const desks=pts(['desk']), sets=[pts(['sprint','huddle','dept','hatchery']),pts(['booth','duo']),pts(['pantry'])].filter(s=>s.length);
  let worst=0; desks.forEach(d=>sets.forEach(s=>{ worst=Math.max(worst,Math.min(...s.map(p=>dist(p,d)))); }));
  return toM(worst);
}
