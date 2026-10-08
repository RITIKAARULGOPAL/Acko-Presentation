/* =====================================================================
   GREEN ZONES: a carbon-responsive green zone analyzer on the test fit
   Layout → space classification → occupancy → footfall → dwell → relative carbon impact
   → biophilic priority → green zone identification → plant quantity → plant type → placement → green score.
   Geometry (spaces, keep-clear mask, free floor, candidate spots) comes from the drawing via gz_extract.py.
   Everything below it runs here, so every assumption can be overridden and the proposal recomputes.
   ===================================================================== */
const GZD=RF.gz;
const GZ_CATS={work:'Work',collab:'Collaboration',social:'Social',arrival:'Arrival',move:'Movement',support:'Support'};
const GZ_CAT_ORDER=['work','collab','social','arrival','move','support'];
/* per space type: who uses it and how. Every value is a planning estimate, editable in the Assumptions step.
   occ: where occupancy comes from · visits: entries or uses per person per day · util: share of capacity actually used
   dwell: average minutes per visit · act: activity factor (metabolic and equipment load) · int: building-services intensity
   (HVAC, lighting, equipment) · soc: social / collaborative importance 0–100 · priv: privacy level */
const GZ_DEF0={
  open:     {n:'Open workstations',   occ:'desks',  visits:2,   util:.70, dwell:180, act:1.0, int:1.0, soc:35,  priv:'Semi-open'},
  cabin:    {n:'Private office',      occ:'seats',  visits:2,   util:.60, dwell:150, act:1.0, int:1.1, soc:20,  priv:'Private'},
  booth:    {n:'Phone booth',         occ:'seats',  visits:4,   util:.50, dwell:20,  act:.8,  int:1.0, soc:5,   priv:'Private'},
  zen:      {n:'Zen room',            occ:'seats',  visits:2,   util:.40, dwell:25,  act:.6,  int:.9,  soc:15,  priv:'Private'},
  meeting:  {n:'Meeting room',        occ:'seats',  visits:3,   util:.55, dwell:50,  act:1.2, int:1.2, soc:55,  priv:'Semi-private'},
  huddle:   {n:'Collaboration huddle',occ:'seats',  visits:3,   util:.50, dwell:45,  act:1.2, int:1.2, soc:65,  priv:'Semi-private'},
  collab:   {n:'Collaboration zone',  occ:'seats',  visits:3,   util:.60, dwell:40,  act:1.1, int:1.0, soc:90,  priv:'Open'},
  event:    {n:'Training / event',    occ:'seats',  visits:1,   util:.40, dwell:90,  act:1.2, int:1.3, soc:70,  priv:'Semi-private'},
  cafe:     {n:'Café and dining',     occ:'all',    visits:1.2, util:.70, dwell:30,  act:1.3, int:1.3, soc:100, priv:'Public'},
  pantry:   {n:'Coffee corner',       occ:'served', visits:3,   util:.90, dwell:6,   act:1.2, int:1.2, soc:85,  priv:'Open'},
  reception:{n:'Reception',           occ:'arrive', visits:1.3, util:.85, dwell:4,   act:1.0, int:1.0, soc:75,  priv:'Public'},
  lobby:    {n:'Lift lobby',          occ:'arrive', visits:2.5, util:.85, dwell:1.5, act:.9,  int:.9,  soc:40,  priv:'Public'},
  corridor: {n:'Main circulation',    occ:'all',    visits:12,  util:.70, dwell:.6,  act:.8,  int:.8,  soc:30,  priv:'Public'},
  wellness: {n:'Wellbeing room',      occ:'seats',  visits:1,   util:.30, dwell:20,  act:.6,  int:.9,  soc:10,  priv:'Private'},
  wash:     {n:'Toilets',             occ:'none',   visits:0,   util:0,   dwell:0,   act:0,   int:0,   soc:0,   priv:'Private'},
  ahu:      {n:'AHU / services',      occ:'none',   visits:0,   util:0,   dwell:0,   act:0,   int:0,   soc:0,   priv:'Restricted'},
  stair:    {n:'Fire stair',          occ:'none',   visits:0,   util:0,   dwell:0,   act:0,   int:0,   soc:0,   priv:'Restricted'},
  tech:     {n:'Server / utility',    occ:'none',   visits:0,   util:0,   dwell:0,   act:0,   int:0,   soc:0,   priv:'Restricted'},
  oos:      {n:'Base building',       occ:'none',   visits:0,   util:0,   dwell:0,   act:0,   int:0,   soc:0,   priv:'Restricted'},
};
const GZ_G0={density:12.5, share:1.0, visitors:.05, wF:25, wD:25, wC:20, wL:15, wS:10, wV:5,
  mVL:.5, mL:.75, mM:1, mH:1.2, mVH:1.4, spS:.30, spM:.60, spL:1.20, spLin:.50, reach:8};
const GZ_TYPES={
  node:{n:'Green Node',d:'High footfall and high visibility',rec:'Large planters, statement plants, cluster planting',h:'Tall · 1.5–2.5 m',mix:[15,45,25,15],maxR:1.2,cap:[3,8]},
  island:{n:'Green Island',d:'High dwell in a social or collaborative space',rec:'Medium plants, planter clusters, biophilic furniture',h:'Medium · 0.9–1.5 m',mix:[25,50,15,10],maxR:1.5,cap:[4,12]},
  edge:{n:'Green Edge',d:'Along a workstation or collaboration boundary',rec:'Linear planters, low planting, green dividers',h:'Low · 0.4–0.9 m',mix:[15,30,0,55],maxL:6,cap:[4,12],lin:1},
  threshold:{n:'Green Threshold',d:'Between two different workplace conditions',rec:'Medium-height planting, green screens, transition planting',h:'Screen · 1.2–1.6 m',mix:[10,40,10,40],maxL:4,cap:[3,8],lin:1},
  pocket:{n:'Green Pocket',d:'Residual or under-used floor',rec:'Small planting clusters, vertical planting',h:'Low to vertical · 0.4–2 m',mix:[40,45,0,15],maxR:.9,cap:[2,5]},
  feature:{n:'Green Feature',d:'High visibility and high design importance',rec:'Large specimen plant, feature planter or vertical garden',h:'Specimen · 2–3 m',mix:[0,35,45,20],maxR:1.8,cap:[3,7]},
};
const GZ_TYPE_ORDER=['feature','node','island','edge','threshold','pocket'];
const GZ_SIZES=[['small','Small','desk plants, small planters'],['medium','Medium','floor plants, planter clusters'],['large','Large','feature planting'],['linear','Linear / screen','planter edges, green dividers']];
const GZ_FOOT=[.10,.35,.80,.25];          // floor area each plant size takes, m²
const GZ_CLASSES=[[25,'Very Low','mVL'],[40,'Low','mL'],[60,'Moderate','mM'],[80,'High','mH'],[101,'Very High','mVH']];
const gzClass=p=>GZ_CLASSES.find(c=>Math.round(p)<=c[0])||GZ_CLASSES[4];
const GZ_KEY='acko-gz-v1';
const gzM=u=>u*U, gzU=m=>m/U;     // plan units ↔ metres
let GZ=null;                         // the analysis, rebuilt by gzRun()
const GZS={view:'class',sel:null,mode:'select',addT:'auto',vb:null,lay:{keep:false,free:false,plants:true,routes:false},
  st:{defs:{},sp:{},g:{},pin:{},del:[],add:[],seq:0}};
function gzLoad(){ try{ const s=JSON.parse(localStorage.getItem(GZ_KEY)||'null'); if(s&&s.defs) GZS.st=Object.assign(GZS.st,s); }catch(e){} }
function gzSave(){ try{ localStorage.setItem(GZ_KEY,JSON.stringify(GZS.st)); }catch(e){} }
const gzDef=k=>Object.assign({},GZ_DEF0[k],GZS.st.defs[k]||{});
const gzG=()=>Object.assign({},GZ_G0,GZS.st.g);
const gzEsc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]);

/* ---------- geometry helpers ---------- */
function gzInRing(x,y,r){ let ins=false; for(let i=0,j=r.length-1;i<r.length;j=i++){ const a=r[i],b=r[j]; if(((a[1]>y)!==(b[1]>y))&&(x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])) ins=!ins; } return ins; }
const gzInRings=(x,y,rings)=>rings.reduce((ins,r)=>gzInRing(x,y,r)?!ins:ins,false);   // even-odd over outer rings and holes
const gzRD=rings=>rings.map(r=>'M'+r.map(p=>p[0]+' '+p[1]).join('L')+'Z').join('');
const GZ_SP=GZD.spaces, GZ_SPI={}; GZ_SP.forEach(s=>GZ_SPI[s.id]=s);
const gzSpaceAt=(x,y)=>GZ_SP.find(s=>gzInRings(x,y,s.rings));
const gzFree=(x,y)=>gzInRings(x,y,GZD.free);
const gzKeep=(x,y)=>gzInRings(x,y,GZD.keep);
const gzP95=a=>{ const v=a.filter(x=>x>0).sort((p,q)=>p-q); return v.length?v[Math.min(v.length-1,Math.floor(.95*(v.length-1)))]:1; };
const gzN=(v,ref)=>ref>0?Math.min(100,100*v/ref):0;

/* ---------- 2 · 3 · 4 · 5 · 6: classify, occupancy, footfall, dwell, carbon index, priority ---------- */
function gzSpaces(){
  const g=gzG(), head=Math.round(GZD.headcount*g.share);
  const arr=GZ_SP.filter(s=>s.k==='lobby'||s.k==='reception'), pan=GZ_SP.filter(s=>s.k==='pantry');
  return GZ_SP.map(s=>{
    const d=gzDef(s.k), ov=GZS.st.sp[s.id]||{};
    let occ=0, src='estimate', why='';
    if(d.occ==='desks'){ occ=Math.round(s.desks*g.share); src=s.desks?'drawing':'estimate'; why=`${s.desks} workstations in the drawing`; if(!s.desks){ occ=Math.round(s.m2/10); why='no desks drawn: 1 person per 10 m²'; } }
    else if(d.occ==='seats'){ occ=s.seats; src=s.seats?'drawing':'estimate'; why=s.seats?`${s.seats} seats in the drawing`:''; if(!s.seats){ occ=Math.max(1,Math.round(s.m2/(s.k==='collab'?3:2.5))); why=`no seats drawn: 1 per ${s.k==='collab'?3:2.5} m²`; } }
    else if(d.occ==='served'){ const nbDesks=GZ_SP.filter(x=>x.nb===s.nb&&x.k==='open').reduce((a,x)=>a+x.desks,0), here=pan.filter(x=>x.nb===s.nb).length||1; occ=Math.round((s.nb!=='X'&&nbDesks?nbDesks:GZD.headcount/pan.length)*g.share/here); why=s.nb!=='X'&&nbDesks?`people in ${nbName(s.nb)} sharing ${here} coffee corner${here>1?'s':''}`:'floor headcount shared by every coffee corner'; }
    else if(d.occ==='arrive'){ const tot=arr.reduce((a,x)=>a+x.m2,0)||1; occ=Math.round(head*(1+g.visitors)*s.m2/tot); why=`headcount plus ${Math.round(g.visitors*100)}% visitors, shared by the ${arr.length} arrival spaces by area`; }
    else if(d.occ==='all'){ occ=head; why=s.k==='cafe'?`the whole floor eats and meets here (${s.seats} seats in the drawing)`:'every person on the floor passes along it'; }
    if(ov.occ!=null){ occ=+ov.occ; src='designer'; why='set by the designer'; }
    const dwell=ov.dwell!=null?+ov.dwell:d.dwell, visits=ov.visits!=null?+ov.visits:d.visits;
    const foot=occ*visits*d.util, hrs=foot*dwell/60, cii=hrs*d.act*d.int;
    return {s, d, id:s.id, occ, src, why, visits, util:d.util, dwell, foot, hrs, ciiRaw:cii, sup:s.c==='support'||d.occ==='none', ov};
  });
}
function gzScore(rows){
  const g=gzG(), live=rows.filter(r=>!r.sup&&r.s.m2>0);
  /* each driver is half intensity (per m², counting at least 25 m² so a tiny room cannot dominate) and half volume,
     square-root compressed against the busiest space on the floor */
  const A=r=>Math.max(25,r.s.m2), mx=(f)=>Math.max(...live.map(f))||1;
  const blend=(vol)=>{ const iv=r=>vol(r)/A(r), mi=mx(iv), mv=mx(vol); return r=>50*Math.sqrt(iv(r)/mi)+50*Math.sqrt(vol(r)/mv); };
  const bF=blend(r=>r.foot), bD=blend(r=>r.hrs), bC=blend(r=>r.ciiRaw), rv=mx(r=>r.s.vis);
  const W=g.wF+g.wD+g.wC+g.wL+g.wS+g.wV||1;
  rows.forEach(r=>{
    if(r.sup){ Object.assign(r,{nF:0,nD:0,cii:0,nL:0,nS:0,nV:0,raw:0}); return; }
    r.nF=bF(r); r.nD=bD(r); r.cii=bC(r); r.nL=Math.min(100,r.s.day*100); r.nS=r.d.soc; r.nV=100*Math.sqrt(r.s.vis/rv);
    r.raw=(g.wF*r.nF+g.wD*r.nD+g.wC*r.cii+g.wL*r.nL+g.wS*r.nS+g.wV*r.nV)/W;
  });
  const top=Math.max(...rows.map(r=>r.raw))||1;
  rows.forEach(r=>{ r.prio=r.sup?0:100*r.raw/top; r.cls=r.sup?null:gzClass(r.prio); });
}

/* ---------- 7 · 9: green zone opportunities and their typology ---------- */
const GZ_TRANS=[['work','collab'],['work','social'],['arrival','work'],['move','social'],['social','work'],['arrival','collab'],['move','collab']];
function gzTypeOf(c,host,R){
  const hc=host.s.c, nb=c.nbr.map(id=>R[id]).filter(Boolean), other=[...new Set(nb.map(r=>r.s.c))].filter(x=>x!==hc&&x!=='support');
  const trans=other.some(o=>GZ_TRANS.some(([a,b])=>(a===hc&&b===o)||(a===o&&b===hc)));
  const long=c.L>=2.5*Math.max(c.W,.3)&&c.W>=.45;
  if(c.vnorm>=70&&host.prio>=55&&c.m2>=2.5&&['arrival','social','collab','move'].includes(hc)) return ['feature','Seen from '+gzSeen(c)+', in a high-priority space'];
  if(c.node<=5&&host.nF>=55&&['arrival','social','move','collab'].includes(hc)) return ['node',`${c.node.toFixed(1)} m from a ${({turn:'corridor junction','reception':'reception','cafe':'café','lobby':'lift lobby'})[c.nodek]||c.nodek.replace('-mouth',' entrance').replace('cafe','café')}, high footfall`];
  if(trans&&c.node<=6&&(long||c.m2<=4)) return ['threshold',`Where ${GZ_CATS[hc].toLowerCase()} meets ${other.map(o=>GZ_CATS[o].toLowerCase()).join(' and ')}, beside the way through`];
  if(long&&(hc==='work'||hc==='collab'||trans)) return ['edge',`A ${c.L.toFixed(1)} m strip along the ${trans?`${GZ_CATS[other[0]].toLowerCase()} boundary`:hc==='work'?'workstations':'collaboration space'}`];
  if(c.m2>=1.5&&c.r>=.55&&['social','collab','work','arrival'].includes(hc)&&host.nD>=40) return ['island',`Open floor in a long-dwell ${GZ_CATS[hc].toLowerCase()} space`];
  return ['pocket',c.walls>=2?'A corner left over between walls and furniture':'Residual floor that circulation does not need'];
}
function gzSeen(c){ const v=c.vby||{}, n={arrival:'reception and the lifts',social:'the café and breakout',circulation:'the main circulation',workstations:'workstations',meeting:'meeting rooms'}; const top=Object.entries(v).sort((a,b)=>b[1]-a[1]).slice(0,2).map(e=>n[e[0]]); return top.length?listJoin(top):'nearby spaces'; }
/* the footprint a zone of n plants needs, kept inside its spot */
function gzFit(z,T){
  const mix=z.mix, need=mix.reduce((a,n,i)=>a+n*GZ_FOOT[i],0);
  if(T.lin){ const g=gzG(), len=mix[0]*g.spS+mix[1]*g.spM+mix[2]*g.spL+mix[3]*g.spLin; return {len:Math.max(.6,len), depth:z.t==='threshold'?.5:.45, area:Math.max(.6,len)*(z.t==='threshold'?.5:.45)}; }
  const r=Math.sqrt(need/Math.PI); return {r:Math.max(.35,r), area:Math.PI*Math.max(.35,r)**2};
}
function gzCapacity(c,t,host){
  const T=GZ_TYPES[t], aisle=host.s.k==='open'||host.s.c==='move'?.3:.1;
  if(T.lin){ const len=Math.min(T.maxL,(c.seg?Math.hypot(c.seg[1][0]-c.seg[0][0],c.seg[1][1]-c.seg[0][1])*U:c.L)-.4); return len>=.8?Math.max(1,Math.floor(len/.55)):0; }
  const r=Math.min(T.maxR,c.r-aisle); return r>=.25?Math.max(1,Math.floor(Math.PI*r*r/.3)):0;
}
function gzMix(n,t,k){
  const m=GZ_TYPES[t].mix.slice();
  const sh=(from,to,p)=>{ const d=Math.min(m[from],p); m[from]-=d; m[to]+=d; };
  if(k==='reception'||k==='lobby') sh(0,2,10); else if(k==='open') { sh(2,0,10); } else if(k==='cafe'){ sh(0,1,5); sh(0,2,5); }
  else if(k==='corridor') sh(2,3,10); else if(['booth','zen','cabin','wellness'].includes(k)) sh(1,0,15);
  const raw=m.map(p=>n*p/100), out=raw.map(Math.floor); let left=n-out.reduce((a,b)=>a+b,0);
  raw.map((v,i)=>[v-Math.floor(v),i]).sort((a,b)=>b[0]-a[0]).forEach(([f,i])=>{ if(left>0&&m[i]>0){ out[i]++; left--; } });
  if(left>0) out[1]+=left;
  return out;
}
function gzLight(day,fd){ return day>=.45||fd<=6?['living','Living plants: good daylight']:day>=.2||fd<=9?['living-low','Living, low-light species']:['preserved','Low-light or preserved / artificial planting']; }
function gzMaint(n,light){ const w=n*(light==='preserved'?.35:light==='living-low'?1.2:1); return w<6?'Low':w<14?'Medium':'High'; }

/* ---------- 10 · 16: quantities and the selection ---------- */
function gzRun(){
  const g=gzG(), rows=gzSpaces(); gzScore(rows);
  const R={}; rows.forEach(r=>R[r.id]=r);
  rows.forEach(r=>{ const mult=r.sup?0:g[r.cls[2]]; r.area=r.s.c==='move'||r.s.k==='lobby'?Math.max(0,r.s.m2-(r.s.keepM2||0)):r.s.m2; r.base=r.sup?0:r.area/g.density; r.target=r.sup?0:Math.round(r.base*mult); r.mult=mult; r.placed=0; r.zones=[]; });
  const rv=gzP95(GZD.cands.map(c=>c.vis));
  const cands=GZD.cands.map((c,i)=>Object.assign({},c,{i,vnorm:gzN(c.vis,rv)}));
  cands.forEach(c=>{
    let host=R[c.h]; if(!host||host.sup){ c.score=-1; return; }
    c.nbr.map(id=>R[id]).filter(r=>r&&!r.sup&&r.s.m2<40&&r.prio>host.prio+10&&r.s.c!=='work').forEach(r=>{ if(r.prio>host.prio) host=r; });
    c.host=host; c.hh=host.id;
    [c.t,c.why]=gzTypeOf(c,host,R); c.cap=gzCapacity(c,c.t,host);
    const nodeB=Math.max(0,100-c.node*15), resid=c.t==='pocket'?100:0, maint=(1-Math.min(1,host.s.day*2))*10;
    c.score=.45*host.prio+.2*c.vnorm+.15*Math.min(100,(1-Math.min(1,c.fd/12))*100)+.1*nodeB+.05*resid+(c.t==='feature'?6:0)-maint;
  });
  const zones=[], del=new Set(GZS.st.del);
  const far=(x,y,h)=>zones.every(z=>{ const d=Math.hypot(z.x-x,z.y-y)*U; return d>=(z.h===h?6:3); });
  const mk=(c,o)=>{ const host=R[o.h||c.hh||c.h]; return {id:o.id,ci:c?c.i:null,x:o.x,y:o.y,h:host.id,t:o.t,why:o.why,ang:o.ang!=null?o.ang:(c?c.ang:0),seg:c&&o.x===c.x&&o.y===c.y?c.seg:null,c,manual:!!o.manual,pinned:!!o.pinned,nOv:o.n}; };
  /* designer zones first: pinned (moved or retyped) auto zones and added ones */
  Object.entries(GZS.st.pin).forEach(([ci,o])=>{ const c=cands[+ci]; if(c&&!del.has(+ci)&&c.host&&!c.host.sup) zones.push(mk(c,Object.assign({id:'c'+ci,x:c.x,y:c.y,t:c.t,why:c.why,pinned:true},o))); });
  GZS.st.add.forEach(o=>{ const sp=gzSpaceAt(o.x,o.y); if(sp&&R[sp.id]&&!R[sp.id].sup) zones.push(mk(null,Object.assign({},o,{h:sp.id,manual:true,why:o.why||'Placed by the designer'}))); });
  zones.forEach(z=>{ z.host=R[z.h]; });
  /* the rest, best spot first: high-priority space, seen, near daylight and footfall; never two zones crowding each other */
  cands.filter(c=>c.score>0&&c.cap>0&&!del.has(c.i)&&!GZS.st.pin[c.i]).sort((a,b)=>b.score-a.score).forEach(c=>{
    const host=c.host, have=zones.filter(z=>z.h===host.id), left=host.target-have.reduce((a,z)=>a+(z.n||0),0);
    if(left<=0||have.length>=Math.max(1,Math.round(host.s.m2/90))||!far(c.x,c.y,host.id)) return;
    if(host.cls[1]==='Very Low'&&c.t!=='pocket') return;
    const z=mk(c,{id:'c'+c.i,x:c.x,y:c.y,t:c.t,why:c.why}); z.host=host; z.auto=true; const T_=GZ_TYPES[c.t]; z.n=Math.min(c.cap,T_.cap[1],c.t==='feature'||c.t==='node'?Math.max(left,T_.cap[0]):left); if(z.n<Math.min(2,GZ_TYPES[c.t].cap[0],left)) return; zones.push(z);
  });
  /* plant counts, mix and footprint for every zone */
  zones.forEach((z,j)=>{
    const host=z.host, T=GZ_TYPES[z.t];
    if(z.nOv!=null) z.n=Math.max(1,Math.round(z.nOv));
    else if(z.n==null){ const left=Math.max(0,host.target-host.placed); z.n=Math.max(T.cap[0],Math.min(T.cap[1],left||T.cap[0])); }
    host.placed+=z.n; host.zones.push(z);
    z.mix=gzMix(z.n,z.t,host.s.k); Object.assign(z,gzFit(z,T));
    const fd=Math.min(host.s.fd,z.c?z.c.fd:host.s.fd), day=z.c?Math.max(0,1-fd/12):host.s.day;
    [z.light,z.lightN]=gzLight(Math.max(day,host.s.day*.5),fd); z.maint=gzMaint(z.n,z.light); z.dens=z.n/z.area; z.fd=fd;
    z.ok=gzFree(z.x,z.y)&&!gzKeep(z.x,z.y); z.vis=z.c?z.c.vnorm:host.nV;
  });
  zones.sort((a,b)=>a.x-b.x).forEach((z,j)=>z.no='G'+String(j+1).padStart(2,'0'));
  /* workstation remainder: desk-top plants, which need no floor */
  rows.forEach(r=>{ r.desk=r.s.k==='open'?Math.min(Math.max(0,r.target-r.placed),Math.round(r.occ/3)):0; });
  GZ={rows,R,cands,zones,g,...gzTotals(rows,zones)};
  return GZ;
}
/* ---------- 11 · 12 · 13: mix, green area, scores ---------- */
function gzTotals(rows,zones){
  const g=gzG(), live=rows.filter(r=>!r.sup), usable=GZD.usableM2;
  const mix=[0,0,0,0]; zones.forEach(z=>z.mix.forEach((n,i)=>mix[i]+=n)); const desk=rows.reduce((a,r)=>a+r.desk,0); mix[0]+=desk;
  const gArea=zones.reduce((a,z)=>a+z.area,0), placed=zones.reduce((a,z)=>a+z.n,0), target=live.reduce((a,r)=>a+r.target,0);
  const foot=live.reduce((a,r)=>a+r.foot,0), hrs=live.reduce((a,r)=>a+r.hrs,0), am=live.reduce((a,r)=>a+r.s.m2,0)||1;
  const cii=live.reduce((a,r)=>a+r.cii*r.s.m2,0)/am, opp=live.reduce((a,r)=>a+r.prio*r.s.m2,0)/am;
  /* the biophilic workplace score rewards placing plants where they matter, not placing more of them */
  const pw=live.filter(r=>r.target>0), sp=pw.reduce((a,r)=>a+r.prio,0)||1;
  const cover=pw.reduce((a,r)=>a+r.prio*Math.min(1,(r.placed+r.desk*.5)/r.target),0)/sp;
  const dk=RF.desks, rch=gzU(g.reach); let seen=0, tot=0;
  dk.forEach(d=>{ tot+=d[2]; if(zones.some(z=>Math.hypot(z.x-d[0],z.y-d[1])<=rch)) seen+=d[2]; });
  const reach=tot?seen/tot:0;
  const visW=placed?zones.reduce((a,z)=>a+z.n*z.vis,0)/placed/100:0;
  const dayFit=placed?zones.reduce((a,z)=>a+z.n*(z.fd<=6?1:z.light==='preserved'?.6:.4),0)/placed:0;
  const conflicts=zones.filter(z=>!z.ok).length, over=target?Math.max(0,(placed+desk)/target-1.3):0;
  const score=Math.max(0,Math.min(100,100*(.4*cover+.3*reach+.15*visW+.15*dayFit)-5*conflicts-50*over));
  return {mix,desk,gArea,placed,target,foot,hrs,cii,opp,cover,reach,visW,dayFit,conflicts,score,usable,cov:100*gArea/usable,avgDwell:foot?hrs*60/foot:0};
}

/* ---------- the plan ---------- */
const GZ_VIEWS=[['class','Spaces'],['foot','Footfall'],['dwell','Dwell'],['carbon','Carbon index'],['prio','Priority'],['prop','Green zones']];
const GZ_METRIC={foot:{k:'nF',hue:'--gz-foot',n:'Footfall',u:r=>`${fmt(r.foot)} visits a day · ${(r.foot/r.s.m2).toFixed(1)} per m²`},
  dwell:{k:'nD',hue:'--gz-dwell',n:'Dwell',u:r=>`${fmt(r.hrs)} person-hours a day · ${r.dwell<2?r.dwell.toFixed(1):Math.round(r.dwell)} min a visit`},
  carbon:{k:'cii',hue:'--gz-carbon',n:'Relative Carbon Impact Index',u:r=>`${Math.round(r.cii)} / 100 relative index`},
  prio:{k:'prio',hue:'--gz-prio',n:'Biophilic Priority',u:r=>`${Math.round(r.prio)} / 100 · ${r.cls?r.cls[1]:'excluded'}`}};
function gzHeat(v){ return `color-mix(in oklab, var(--h) ${Math.round(8+v*.82)}%, var(--slab))`; }
function gzBase(){
  return PA(PD(RF.plate),'slab')+`<g class="gz-shell">${PA(G('cored','S'),'rf-cored')}${PA(G('stair','S'),'rf-stair')}${PA(G('core','S'),'rf-core')}${RF.cols.map(c=>R({x:c[0],y:c[1],w:c[2],h:c[3]},'col')).join('')}</g>`;
}
function gzFit_(){ return ALL_IDS.map(a=>PA(G('furn',a),'rf-furn')).join(''); }
function gzParts(){ return ALL_IDS.map(a=>PA(G('part',a),'rf-part')).join(''); }
function gzGreen(){ return ALL_IDS.map(a=>PA(G('green',a),'rf-green')).join(''); }
function gzSpaceLayer(){
  const v=GZS.view, M=GZ_METRIC[v];
  return GZ.rows.map(r=>{
    const s=r.s; let fill, cls='gz-sp';
    if(v==='class'||v==='prop'||v==='dash'||v==='db'||v==='assume') fill=v==='class'?`var(--gzc-${s.c})`:'transparent', cls+=v==='class'?' cat':' bare';
    else if(r.sup) { fill='transparent'; cls+=' sup'; }
    else fill=gzHeat(r[M.k]);
    return `<path d="${gzRD(s.rings)}" class="${cls}${GZS.sel&&GZS.sel.sp===s.id?' on':''}" data-sid="${s.id}" style="fill:${fill}" fill-rule="evenodd"/>`;
  }).join('');
}
function gzZoneSVG(z){
  const mn=GZS.mn||26, T=GZ_TYPES[z.t], u=m=>Math.max(gzU(m),0), cls=`gz-z t-${z.t}${z.ok?'':' bad'}${GZS.sel&&GZS.sel.z===z.id?' on':''}`;
  let shape='';
  if(T.lin){
    const a=z.ang*Math.PI/180, hl=Math.max(u(z.len)/2,mn*1.2), dx=Math.cos(a)*hl, dy=-Math.sin(a)*hl, w=u(z.depth);
    shape=`<line class="gz-zl" x1="${r1(z.x-dx)}" y1="${r1(z.y-dy)}" x2="${r1(z.x+dx)}" y2="${r1(z.y+dy)}" style="stroke-width:${r1(Math.max(w,mn*.8))}"/>`;
    if(z.t==='threshold'){ const n=Math.max(2,Math.round(z.len/.6)); for(let i=0;i<=n;i++){ const f=i/n*2-1, px=z.x+dx*f, py=z.y+dy*f, nx=-Math.sin(a)*w*.9, ny=-Math.cos(a)*w*.9; shape+=`<line class="gz-tick" x1="${r1(px-nx)}" y1="${r1(py-ny)}" x2="${r1(px+nx)}" y2="${r1(py+ny)}"/>`; } }
  } else {
    const r=Math.max(u(z.r),mn);
    if(z.t==='node') shape=`<circle class="gz-zf" cx="${r1(z.x)}" cy="${r1(z.y)}" r="${r1(r)}"/>`+[0,1,2].map(i=>{ const a=i*2.094+.5; return `<circle class="gz-dot" cx="${r1(z.x+Math.cos(a)*r*.45)}" cy="${r1(z.y+Math.sin(a)*r*.45)}" r="${r1(r*.28)}"/>`; }).join('');
    else if(z.t==='island') shape=`<rect class="gz-zf" x="${r1(z.x-r)}" y="${r1(z.y-r*.8)}" width="${r1(2*r)}" height="${r1(1.6*r)}" rx="${r1(r*.7)}"/>`;
    else if(z.t==='pocket') shape=`<path class="gz-zf" d="M${r1(z.x)} ${r1(z.y-r)}L${r1(z.x+r)} ${r1(z.y)}L${r1(z.x)} ${r1(z.y+r)}L${r1(z.x-r)} ${r1(z.y)}Z"/>`;
    else { const pts=[]; for(let i=0;i<10;i++){ const a=-Math.PI/2+i*Math.PI/5, rr=i%2?r*.5:r*1.1; pts.push(`${r1(z.x+Math.cos(a)*rr)} ${r1(z.y+Math.sin(a)*rr)}`); } shape=`<path class="gz-zf" d="M${pts.join('L')}Z"/>`; }
  }
  return `<g class="${cls}" data-zid="${z.id}" tabindex="0" role="button" aria-label="${z.no} ${T.n}, ${z.n} plants, ${gzEsc(z.host.s.n)}">${shape}<circle class="gz-hit" cx="${r1(z.x)}" cy="${r1(z.y)}" r="${r1(Math.max(T.lin?u(z.len)/2:u(z.r||1)*1.2,mn*1.5))}"/>${z.ok?'':`<text class="gz-warn" x="${r1(z.x+mn*1.4)}" y="${r1(z.y-mn*.6)}">!</text>`}<text class="gz-no" x="${r1(z.x)}" y="${r1(z.y-Math.max(T.lin?mn:u(z.r||1),mn)-mn*.45)}">${z.no}</text></g>`;
}
function gzDraw(){
  if(!GZ) return; const svg=$('#gzsvg'); if(!svg) return;
  const v=GZS.view, L=GZS.lay, bb=svg.getBoundingClientRect(), vb=GZS.vb||[VBX,VBY,VBW,VBH];
  const ppu=bb.width&&bb.height?Math.min(bb.width/vb[2],bb.height/vb[3]):.27; GZS.mn=7/ppu; svg.style.setProperty('--fs',r1(11.5/ppu)+'px');
  svg.dataset.view=v; svg.style.setProperty('--h',`var(${(GZ_METRIC[v]||{}).hue||'--gz-prio'})`);
  $('#gz-sp').innerHTML=gzSpaceLayer();
  $('#gz-keep').innerHTML=L.keep?`<path d="${gzRD(GZD.keep)}" fill-rule="evenodd" class="gz-keepp"/>`:'';
  $('#gz-free').innerHTML=L.free?`<path d="${gzRD(GZD.free)}" fill-rule="evenodd" class="gz-freep"/>`:'';
  $('#gz-routes').innerHTML=L.routes?RF.routes.map(r=>`<path class="gz-route" d="M${r.pts.map(p=>p.join(' ')).join('L')}"/>`).join(''):'';
  $('#gz-exist').style.display=L.plants?'':'none';
  $('#gz-zones').innerHTML=v==='prop'||v==='dash'?GZ.zones.map(gzZoneSVG).join(''):'';
  $('#gz-lbl').innerHTML=v==='class'||GZ_METRIC[v]?GZ.rows.filter(r=>r.s.m2>=40&&!r.sup).map(r=>T(r.s.lab[0],r.s.lab[1]+5,v==='class'?'':Math.round(r[(GZ_METRIC[v]||{}).k]||0),'gz-val')).join(''):'';
  $$('#gz-bar [data-v]').forEach(b=>b.classList.toggle('on',b.dataset.v===v||(v==='dash'&&b.dataset.v==='prop')));
  $$('#gz-bar [data-l]').forEach(b=>b.setAttribute('aria-pressed',L[b.dataset.l]?'true':'false'));
  $$('#gz-bar [data-m]').forEach(b=>b.setAttribute('aria-pressed',GZS.mode===b.dataset.m?'true':'false'));
  $('#gz-edit').hidden=!(v==='prop'||v==='dash');
  $('#gz-leg').innerHTML=gzLegend();
  $('#gz-banner').hidden=v!=='carbon';
  gzCard(); gzKPI();
}
function gzLegend(){
  const v=GZS.view;
  if(v==='class') return GZ_CAT_ORDER.map(c=>`<span><i class="sw" style="background:var(--gzc-${c})"></i>${GZ_CATS[c]}</span>`).join('');
  if(GZ_METRIC[v]) return `<span class="gz-ramp" style="--h:var(${GZ_METRIC[v].hue})"><b>${GZ_METRIC[v].n}</b><i></i><small>low</small><small>high</small></span>${v==='prio'?GZ_CLASSES.map(c=>`<small class="gz-cls">${c[1]} ≤ ${Math.min(100,c[0])}</small>`).join(''):''}<span class="gz-est">normalised to this floor · estimates</span>`;
  return GZ_TYPE_ORDER.map(t=>`<span class="gz-lt"><svg viewBox="-12 -12 24 24" aria-hidden="true">${gzGlyph(t)}</svg>${GZ_TYPES[t].n}</span>`).join('')+`<span class="gz-lt"><svg viewBox="-12 -12 24 24" aria-hidden="true"><circle r="8" class="gz-bad-g"/><text y="4" class="gz-warn" style="font-size:11px">!</text></svg>Conflicts with clearance</span>`;
}
function gzGlyph(t){
  return {node:'<circle r="9" class="gz-zf"/><circle cx="-3" cy="-2" r="2.5" class="gz-dot"/><circle cx="3" cy="-2" r="2.5" class="gz-dot"/><circle cx="0" cy="4" r="2.5" class="gz-dot"/>',
    island:'<rect x="-10" y="-7" width="20" height="14" rx="7" class="gz-zf"/>',edge:'<line x1="-10" y1="0" x2="10" y2="0" class="gz-zl" style="stroke-width:6"/>',
    threshold:'<line x1="-10" y1="0" x2="10" y2="0" class="gz-zl" style="stroke-width:5"/><path d="M-8 -6V6M-3 -6V6M3 -6V6M8 -6V6" class="gz-tick"/>',
    pocket:'<path d="M0 -8L8 0L0 8L-8 0Z" class="gz-zf"/>',feature:'<path d="M0 -11L2.6 -3.6L10.5 -3.4L4.2 1.4L6.5 9L0 4.5L-6.5 9L-4.2 1.4L-10.5 -3.4L-2.6 -3.6Z" class="gz-zf"/>'}[t];
}
function gzKPI(){
  const k=$('#gz-kpi'); if(!k||!GZ) return;
  k.innerHTML=`<span><b>${Math.round(GZ.score)}</b>/100 biophilic score</span><span><b>${fmt(GZ.placed+GZ.desk)}</b> plants · ${GZ.zones.length} zones</span><span><b>${GZ.cov.toFixed(1)}%</b> green coverage</span>`;
}
const gzSrc=s=>`<i class="gz-src s-${s}" title="${({drawing:'Read from the drawing',estimate:'Estimate: inferred, not measured',designer:'Set by the designer'})[s]}">${({drawing:'dwg',estimate:'est.',designer:'set'})[s]}</i>`;
function gzCard(){
  const el=$('#gz-card'); if(!el) return;
  const sel=GZS.sel; if(!sel){ el.hidden=true; return; }
  if(sel.z){ const z=GZ.zones.find(x=>x.id===sel.z); if(!z){ GZS.sel=null; el.hidden=true; return; } el.hidden=false; el.innerHTML=gzZoneCard(z); return; }
  const r=GZ.R[sel.sp]; if(!r){ el.hidden=true; return; } el.hidden=false; el.innerHTML=gzSpaceCard(r);
}
function gzZoneCard(z){
  const r=z.host, T=GZ_TYPES[z.t], mx=z.mix.map((n,i)=>n?`${n} ${GZ_SIZES[i][1].toLowerCase()}`:'').filter(Boolean).join(' + ');
  return `<div class="gz-ch"><span class="gz-tag"><svg viewBox="-12 -12 24 24" aria-hidden="true">${gzGlyph(z.t)}</svg>${z.no}</span><button type="button" class="gz-x" data-act="close" aria-label="Close">×</button></div>
  <p class="gz-zn">Zone: ${gzEsc(r.s.n)}</p>
  <dl class="gz-dl"><dt>Footfall</dt><dd>${fmt(r.foot)}/day ${gzSrc(r.src==='designer'?'designer':'estimate')}</dd><dt>Average dwell</dt><dd>${r.dwell<2?r.dwell.toFixed(1):Math.round(r.dwell)} min ${gzSrc(r.ov.dwell!=null?'designer':'estimate')}</dd>
  <dt>Relative carbon impact</dt><dd>${Math.round(r.cii)}/100</dd><dt>Biophilic priority</dt><dd>${Math.round(r.prio)}/100 · ${r.cls[1]}</dd>
  <dt>Recommended green zone</dt><dd><select data-act="type" aria-label="Green zone type">${GZ_TYPE_ORDER.map(t=>`<option value="${t}"${t===z.t?' selected':''}>${GZ_TYPES[t].n}</option>`).join('')}</select></dd>
  <dt>Recommended plants</dt><dd><input type="number" min="1" max="60" step="1" value="${z.n}" data-act="n" aria-label="Plants in this zone"></dd>
  <dt>Plant mix</dt><dd>${mx}</dd><dt>Planting</dt><dd>${T.rec}</dd><dt>Height</dt><dd>${T.h}</dd>
  <dt>${T.lin?'Planter length':'Zone area'}</dt><dd>${T.lin?`${z.len.toFixed(1)} m (plants × spacing)`:`${z.area.toFixed(1)} m²`}</dd><dt>Density</dt><dd>${z.dens.toFixed(1)} plants/m²</dd>
  <dt>Light</dt><dd>${z.lightN} · ${z.fd.toFixed(0)} m from the glass</dd><dt>Maintenance</dt><dd>${z.maint}</dd></dl>
  <p class="gz-why"><b>Reason:</b> ${gzReason(z)}</p>
  ${z.ok?'':`<p class="gz-bad-n">⚠ This spot is inside the circulation keep-clear zone (${GZD.clear.toFixed(1)} m corridors, doors, escape routes or furniture). Move it onto the free floor.</p>`}
  <div class="gz-acts"><button type="button" data-act="del">Delete zone</button>${z.pinned||z.manual?'<button type="button" data-act="unpin">Back to automatic</button>':''}</div>`;
}
function gzReason(z){
  const r=z.host, f=r.nF>=60?'high':r.nF>=35?'moderate':'low', d=r.nD>=60?'high':r.nD>=35?'moderate':'low';
  const soc=r.d.soc>=70?' and strong social activity':r.d.soc>=50?' and regular collaboration':'';
  return `${f[0].toUpperCase()+f.slice(1)} footfall, ${d} dwell time${soc} make this a ${r.cls[1].toLowerCase()}-priority biophilic zone. ${z.why}.`;
}
function gzSpaceCard(r){
  const s=r.s, d=r.d, num=(k,v,step,lab)=>`<input type="number" step="${step}" min="0" value="${v}" data-sp="${k}" aria-label="${lab}">`;
  return `<div class="gz-ch"><span class="gz-tag sp" style="--c:var(--gzc-${s.c})">${GZ_CATS[s.c]}</span><button type="button" class="gz-x" data-act="close" aria-label="Close">×</button></div>
  <p class="gz-zn">${gzEsc(s.n)}</p><p class="gz-sub">${d.n} · ${fmt(s.m2)} m² · ${s.nb!=='X'&&isNB(s.nb)?nbName(s.nb):'shared'} · ${d.priv}</p>
  ${r.sup?`<p class="gz-sub">Support space: excluded from planting (services, cores, toilets, stairs).</p>`:`<dl class="gz-dl">
  <dt>Occupancy</dt><dd>${num('occ',r.occ,1,'Occupancy')} ${gzSrc(r.src)}</dd>
  <dt>Visits / person / day</dt><dd>${num('visits',r.visits,.1,'Visits per person per day')} ${gzSrc(r.ov.visits!=null?'designer':'estimate')}</dd>
  <dt>Average dwell, min</dt><dd>${num('dwell',r.dwell,.5,'Average dwell in minutes')} ${gzSrc(r.ov.dwell!=null?'designer':'estimate')}</dd>
  <dt>Utilisation</dt><dd>${Math.round(r.util*100)}% ${gzSrc('estimate')}</dd>
  <dt>Daily footfall</dt><dd>${fmt(r.foot)}</dd><dt>Occupancy hours</dt><dd>${fmt(r.hrs)} a day</dd>
  <dt>Relative carbon impact</dt><dd>${Math.round(r.cii)}/100</dd><dt>Daylight</dt><dd>${Math.round(s.day*100)}% within 6 m of glass</dd>
  <dt>Visibility</dt><dd>${Math.round(r.nV)}/100</dd><dt>Existing planting</dt><dd>${s.plants||'none'} ${gzSrc('drawing')}</dd>
  <dt>Biophilic priority</dt><dd><b>${Math.round(r.prio)}</b>/100 · ${r.cls[1]}</dd><dt>Recommended plants</dt><dd>${r.target} <small>(${fmt(r.area)} m²${r.area<r.s.m2?' outside the clear width':''} ÷ ${r.g?r.g.density:gzG().density} × ${r.mult})</small>${r.desk?` · ${r.desk} on desks`:''}</dd></dl>
  <p class="gz-sub">${gzEsc(r.why)}</p>${Object.keys(r.ov).length?'<div class="gz-acts"><button type="button" data-act="spreset">Reset this space</button></div>':''}`}`;
}

/* ---------- dashboard, database and assumptions panels ---------- */
function gzPanel(){
  const p=$('#gz-panel'); if(!p||!GZ) return; const v=GZS.view;
  p.hidden=!['dash','db','assume'].includes(v); if(p.hidden) return;
  if(v==='dash') p.innerHTML=gzDash(); else if(v==='db') p.innerHTML=gzDB(); else p.innerHTML=gzAssume();
}
function gzTile(n,v,s){ return `<div class="gz-tile"><dt>${n}</dt><dd>${v}</dd>${s?`<small>${s}</small>`:''}</div>`; }
function gzDash(){
  const G_=GZ, live=G_.rows.filter(r=>!r.sup);
  const tiles=[gzTile('Floor area',`${fmt(RF.plateM2)} m²`,`${fmt(G_.usable)} m² usable`),gzTile('Headcount',fmt(GZD.headcount*G_.g.share),'from workstations'),
    gzTile('Daily footfall',fmt(G_.foot),'visits, estimate'),gzTile('Average dwell',`${Math.round(G_.avgDwell)} min`,'per visit, estimate'),
    gzTile('Relative carbon impact',`${Math.round(G_.cii)}/100`,'floor average, relative'),gzTile('Biophilic workplace score',`<b>${Math.round(G_.score)}</b>/100`,`opportunity ${Math.round(G_.opp)}/100`),
    gzTile('Recommended plants',fmt(G_.target),`${fmt(G_.placed)} in zones + ${fmt(G_.desk)} on desks`),gzTile('Green zone area',`${G_.gArea.toFixed(1)} m²`,`${G_.zones.length} zones`),gzTile('Green coverage',`${G_.cov.toFixed(1)}%`,'of usable floor')];
  const zr=G_.zones.map(z=>`<tr data-zid="${z.id}" tabindex="0"><td>${z.no}</td><td>${gzEsc(z.host.s.n)}</td><td>${GZ_TYPES[z.t].n.replace('Green ','')}</td><td>${fmt(z.host.foot)}</td><td>${z.host.dwell<2?z.host.dwell.toFixed(1):Math.round(z.host.dwell)} min</td><td>${Math.round(z.host.cii)}</td><td>${Math.round(z.host.prio)}</td><td>${z.n}</td></tr>`).join('');
  const where=i=>{ const c={}; G_.zones.forEach(z=>{ if(z.mix[i]) c[z.host.d.n]=(c[z.host.d.n]||0)+z.mix[i]; }); if(i===0&&G_.desk) c['Open workstations (on desks)']=(c['Open workstations (on desks)']||0)+G_.desk; return Object.entries(c).sort((a,b)=>b[1]-a[1]).slice(0,3).map(e=>e[0]).join(', ')||'—'; };
  /* shares are of the floor planting in zones; desk-top plants in the work arenas are listed on their own */
  const zm=G_.mix.map((n,i)=>i===0?n-G_.desk:n), tot=zm.reduce((a,b)=>a+b,0)||1, rng=['25–35%','40–50%','10–15%','15–20%'];
  const mr=GZ_SIZES.map(([k,n,d],i)=>`<tr><td>${n}<small>${d}</small></td><td>${fmt(zm[i])}</td><td>${Math.round(100*zm[i]/tot)}% <small>guide ${rng[i]}</small></td><td>${where(i).replace(/Open workstations \(on desks\),? ?/,'')||'—'}</td></tr>`).join('')
    +(G_.desk?`<tr><td>Desk-top<small>small plants on desks and storage</small></td><td>${fmt(G_.desk)}</td><td><small>outside the floor mix</small></td><td>Open workstations</td></tr>`:'');
  return `<div class="gz-cols"><section><h3>Floor summary</h3><dl class="gz-tiles">${tiles.join('')}</dl><p class="gz-disc">${GZ_DISC}</p>
  <h3>Plant mix</h3><table class="gz-t"><thead><tr><th>Type</th><th>Quantity</th><th>Share</th><th>Recommended location</th></tr></thead><tbody>${mr}</tbody></table></section>
  <section><h3>Green zone summary</h3><div class="gz-scroll"><table class="gz-t gz-zt"><thead><tr><th>#</th><th>Zone</th><th>Type</th><th>Footfall</th><th>Dwell</th><th>Carbon index</th><th>Priority</th><th>Plants</th></tr></thead><tbody>${zr}</tbody></table></div></section>
  <section><h3>Design recommendations</h3><ol class="gz-rec">${gzRecs().map(t=>`<li>${t}</li>`).join('')}</ol>
  <div class="gz-acts"><button type="button" data-act="csv">Export zones (CSV)</button><button type="button" data-act="json">Export analysis (JSON)</button></div></section></div>`;
}
function gzDB(){
  const rows=GZ.rows.slice().sort((a,b)=>b.prio-a.prio||a.s.n.localeCompare(b.s.n));
  const circ=r=>{ const f=r.foot/r.s.m2; return r.sup?'—':f>=4?'High':f>=1.2?'Medium':'Low'; };
  return `<h3>Spatial database · ${GZ.rows.length} spaces read from the drawing's space layers</h3><div class="gz-scroll tall"><table class="gz-t gz-db"><thead><tr><th>Zone</th><th>Type</th><th>Category</th><th>Area m²</th><th>Occupancy</th><th>Dwell min</th><th>Visits/p/day</th><th>Footfall/day</th><th>Daylight</th><th>Circulation</th><th>Privacy</th><th>Existing plants</th><th>Priority</th><th>Planting intensity</th></tr></thead><tbody>${rows.map(r=>`<tr data-sid="${r.id}" tabindex="0"><td>${gzEsc(r.s.n)}</td><td>${r.d.n}</td><td>${GZ_CATS[r.s.c]}</td><td>${r.s.m2.toFixed(1)}</td><td>${r.sup?'—':`${fmt(r.occ)} ${gzSrc(r.src)}`}</td><td>${r.sup?'—':r.dwell<2?r.dwell.toFixed(1):Math.round(r.dwell)}</td><td>${r.sup?'—':r.visits}</td><td>${r.sup?'—':fmt(r.foot)}</td><td>${Math.round(r.s.day*100)}%</td><td>${circ(r)}</td><td>${r.d.priv}</td><td>${r.s.plants||0}</td><td>${r.sup?'—':Math.round(r.prio)}</td><td>${r.sup?'None (support)':r.cls[1]}</td></tr>`).join('')}</tbody></table></div><p class="gz-disc">Occupancy marked <i class="gz-src s-drawing">dwg</i> is counted from desks and seats in the drawing. <i class="gz-src s-estimate">est.</i> values are planning estimates from the assumptions, never measurements. Click a row to see the space on the plan.</p>`;
}
function gzAssume(){
  const g=gzG(), cell=(k,f,v,step)=>`<input type="number" step="${step}" min="0" value="${v}" data-def="${k}" data-f="${f}" aria-label="${GZ_DEF0[k].n} ${f}"${GZS.st.defs[k]&&GZS.st.defs[k][f]!=null?' class="ov"':''}>`;
  const types=Object.keys(GZ_DEF0).filter(k=>GZ_DEF0[k].occ!=='none');
  const gl=(f,n,step,u)=>`<label class="gz-gl"><span>${n}</span><input type="number" step="${step}" min="0" value="${g[f]}" data-g="${f}"${GZS.st.g[f]!=null?' class="ov"':''}>${u?`<small>${u}</small>`:''}</label>`;
  return `<div class="gz-cols two"><section><h3>Activity by space type <small>estimates · edit any value</small></h3><div class="gz-scroll tall"><table class="gz-t gz-as"><thead><tr><th>Space type</th><th>Visits / person / day</th><th>Utilisation</th><th>Dwell, min</th><th>Activity factor</th><th>Services intensity</th><th>Social 0–100</th></tr></thead><tbody>${types.map(k=>{ const d=gzDef(k); return `<tr><td>${d.n}</td><td>${cell(k,'visits',d.visits,.1)}</td><td>${cell(k,'util',d.util,.05)}</td><td>${cell(k,'dwell',d.dwell,.5)}</td><td>${cell(k,'act',d.act,.1)}</td><td>${cell(k,'int',d.int,.1)}</td><td>${cell(k,'soc',d.soc,5)}</td></tr>`; }).join('')}</tbody></table></div></section>
  <section><h3>Floor settings</h3><div class="gz-gls">${gl('share','People per desk',.05,'1 = one desk each')}${gl('visitors','Visitors',.01,'share of headcount')}${gl('density','Planting density',.5,'m² per plant (10–15)')}${gl('reach','Visual reach',.5,'m from a desk')}</div>
  <h3>Priority weights <small>% · normalised to their sum</small></h3><div class="gz-gls">${gl('wF','Footfall',1)}${gl('wD','Dwell time',1)}${gl('wC','Carbon index',1)}${gl('wL','Daylight',1)}${gl('wS','Social importance',1)}${gl('wV','Visibility',1)}</div>
  <h3>Quantity multipliers <small>by priority class</small></h3><div class="gz-gls">${gl('mVL','Very low',.05)}${gl('mL','Low',.05)}${gl('mM','Moderate',.05)}${gl('mH','High',.05)}${gl('mVH','Very high',.05)}</div>
  <h3>Plant spacing <small>m, for planter lengths</small></h3><div class="gz-gls">${gl('spS','Small',.05)}${gl('spM','Medium',.05)}${gl('spL','Large',.05)}${gl('spLin','Linear',.05)}</div>
  <p class="gz-disc">Circulation rules come from the drawing and are fixed here: ${GZD.clear.toFixed(1)} m clear corridors (the drawing's "${Math.round(GZD.clear*1000)}MM WIDE CORRIDOR" note), ${GZD.doorClr} m in front of doors, ${GZD.routeClr.toFixed(2)} m each side of escape routes, ${GZD.furnClr} m around furniture. Change them in <code>gz_extract.py</code> and rebuild.</p>
  <div class="gz-acts"><button type="button" data-act="reset">Reset all assumptions</button><button type="button" data-act="resetz">Reset zone edits</button><button type="button" data-act="json">Export (JSON)</button><label class="gz-imp"><input type="file" accept=".json,application/json" data-act="import">Import (JSON)</label></div></section></div>`;
}
const GZ_DISC='The Relative Carbon Impact Index compares activity intensity between spaces for design planning. It is not a measurement of emissions and not a carbon-offset calculation.';
function gzRecs(){
  const G_=GZ, z=G_.zones, R_=G_.rows.filter(r=>!r.sup), out=[];
  const top=R_.slice().sort((a,b)=>b.prio-a.prio).slice(0,3);
  out.push(`Concentrate planting in ${listJoin(top.map(r=>gzEsc(r.s.n)))}: they score highest for footfall, dwell and social use (priority ${top.map(r=>Math.round(r.prio)).join(', ')}).`);
  const feat=z.filter(x=>x.t==='feature'||x.t==='node');
  if(feat.length) out.push(`Use large specimen or statement planting at ${listJoin(feat.slice(0,4).map(x=>x.no))}, the most visible spots from ${gzSeen(feat[0].c||{vby:{}})}. A few large plants here do more than many small ones spread around.`);
  const edges=z.filter(x=>x.t==='edge'||x.t==='threshold');
  if(edges.length) out.push(`Run linear planters or green screens (${edges.reduce((a,x)=>a+x.len,0).toFixed(1)} m in total) at ${listJoin(edges.slice(0,5).map(x=>x.no))} to mark the change from workstations to collaboration and social spaces without walls.`);
  const open=R_.filter(r=>r.s.k==='open'); const desk=open.reduce((a,r)=>a+r.desk,0);
  if(desk) out.push(`In the work arenas, put ${desk} small plants on desks and storage tops instead of floor planters: there the floor is needed for chairs and aisles. Keep floor planting to islands and edges.`);
  const corr=G_.rows.find(r=>r.s.k==='corridor');
  out.push(`Do not plant in the main corridors or on the escape routes: ${GZD.clear.toFixed(1)} m clear width is kept everywhere, plus ${GZD.doorClr} m in front of doors and the sight lines at every junction. That rules out ${Math.round(GZD.keepWhy.find(k=>k[0]==='escape routes')[1]+GZD.keepWhy.find(k=>k[0]==='corridor clear width')[1])} m² of circulation${corr?` (the corridor carries ${fmt(corr.foot)} trips a day)`:''}.`);
  const day=z.filter(x=>x.light==='living'); if(day.length) out.push(`Daylight supports living plants at ${day.length} zones within 6 m of the glass (${listJoin(day.slice(0,4).map(x=>x.no))}). Put the high-light species and the largest specimens there.`);
  const dark=z.filter(x=>x.light==='preserved'); if(dark.length) out.push(`${listJoin(dark.slice(0,4).map(x=>x.no))} sit deep in the plan, far from the glass: use low-light species with grow lights, or preserved / artificial planting to keep maintenance low.`);
  const sup=G_.rows.filter(r=>r.sup); out.push(`Leave toilets, AHU and server rooms, stairs and the base-building cores (${fmt(sup.reduce((a,r)=>a+r.s.m2,0))} m²) unplanted, apart from small preserved accents in the toilets if wanted.`);
  const focus=R_.filter(r=>['booth','zen','cabin'].includes(r.s.k)); if(focus.length) out.push(`Keep focus rooms and phone booths to low-density planting (a desk plant or a small wall planter), so they stay calm and easy to clean.`);
  if(GZD.existing) out.push(`The drawing already shows ${GZD.existing} plants. They are kept, and the proposal only adds planting where it is missing.`);
  return out.slice(0,10);
}

/* ---------- interaction ---------- */
function gzSetView(v){ GZS.view=v; if(v!=='prop'&&v!=='dash'&&GZS.sel&&GZS.sel.z) GZS.sel=null; gzDraw(); gzPanel(); }
function gzRecalc(){
  const a=document.activeElement, key=a&&a.dataset&&(a.dataset.def?`[data-def="${a.dataset.def}"][data-f="${a.dataset.f}"]`:a.dataset.g?`[data-g="${a.dataset.g}"]`:a.dataset.sp?`#gz-card [data-sp="${a.dataset.sp}"]`:a.dataset.act==='n'||a.dataset.act==='type'?`#gz-card [data-act="${a.dataset.act}"]`:null);
  gzRun(); gzDraw(); gzPanel(); gzSave();
  if(key){ const el=$('#sc-green '+key); if(el) el.focus({preventScroll:true}); }
}
function gzPt(e){ const svg=$('#gzsvg'), p=svg.createSVGPoint(); p.x=e.clientX; p.y=e.clientY; const q=p.matrixTransform(svg.getScreenCTM().inverse()); return [q.x,q.y]; }
function gzVB(){ const v=GZS.vb||[VBX,VBY,VBW,VBH]; $('#gzsvg').setAttribute('viewBox',v.map(n=>r1(n)).join(' ')); }
function gzZoom(f,cx,cy){
  const v=GZS.vb||[VBX,VBY,VBW,VBH]; if(cx==null){ cx=v[0]+v[2]/2; cy=v[1]+v[3]/2; }
  let w=Math.max(VBW/12,Math.min(VBW,v[2]/f)), h=w*VBH/VBW;
  GZS.vb=w>=VBW?null:[Math.max(VBX,Math.min(VBX+VBW-w,cx-(cx-v[0])*w/v[2])),Math.max(VBY,Math.min(VBY+VBH-h,cy-(cy-v[1])*h/v[3])),w,h]; gzVB(); gzDraw();
}
function gzFocus(z){ const w=VBW/4, h=w*VBH/VBW; GZS.vb=[Math.max(VBX,Math.min(VBX+VBW-w,z.x-w/2)),Math.max(VBY,Math.min(VBY+VBH-h,z.y-h/2)),w,h]; gzVB(); }
let gzRO=null;
function gzPin(z,o){
  if(z.manual){ const a=GZS.st.add.find(x=>x.id===z.id); if(a) Object.assign(a,o); }
  else GZS.st.pin[z.ci]=Object.assign({t:z.t,x:z.x,y:z.y},GZS.st.pin[z.ci]||{},o);
}
function gzExport(kind){
  const G_=GZ; let blob,name;
  if(kind==='csv'){
    const h=['zone','space','space type','category','green zone type','x_m','y_m','plants','small','medium','large','linear','planter_length_m','zone_area_m2','height','density_per_m2','maintenance','light','footfall_per_day','avg_dwell_min','relative_carbon_index','biophilic_priority','priority_class','clearance_ok','source'];
    const rows=G_.zones.map(z=>[z.no,z.host.s.n,z.host.d.n,GZ_CATS[z.host.s.c],GZ_TYPES[z.t].n,(z.x*U).toFixed(2),(z.y*U).toFixed(2),z.n,...z.mix,GZ_TYPES[z.t].lin?z.len.toFixed(2):'',z.area.toFixed(2),GZ_TYPES[z.t].h,z.dens.toFixed(2),z.maint,z.lightN,Math.round(z.host.foot),r1(z.host.dwell),Math.round(z.host.cii),Math.round(z.host.prio),z.host.cls[1],z.ok?'yes':'NO',z.manual?'designer':z.pinned?'designer-edited':'automatic']);
    blob=new Blob([[h,...rows].map(r=>r.map(c=>/[",\n]/.test(String(c))?`"${String(c).replace(/"/g,'""')}"`:c).join(',')).join('\n')],{type:'text/csv'}); name='acko-green-zones.csv';
  } else {
    const data={tool:'Acko green zone analyzer',source:PROJECT.source,note:GZ_DISC,state:GZS.st,
      floor:{score:Math.round(G_.score),opportunity:Math.round(G_.opp),plants_recommended:G_.target,plants_in_zones:G_.placed,plants_on_desks:G_.desk,green_area_m2:+G_.gArea.toFixed(1),coverage_pct:+G_.cov.toFixed(2),footfall_per_day:Math.round(G_.foot),avg_dwell_min:Math.round(G_.avgDwell),relative_carbon_index:Math.round(G_.cii)},
      spaces:G_.rows.map(r=>({id:r.id,name:r.s.n,type:r.s.k,category:r.s.c,m2:r.s.m2,occupancy:r.occ,occupancy_source:r.src,visits:r.visits,utilisation:r.util,dwell_min:r.dwell,footfall:Math.round(r.foot),occupancy_hours:+r.hrs.toFixed(1),relative_carbon_index:Math.round(r.cii),daylight:r.s.day,priority:Math.round(r.prio),class:r.cls?r.cls[1]:'support',plants:r.target})),
      zones:G_.zones.map(z=>({no:z.no,type:z.t,space:z.host.s.n,x_m:+(z.x*U).toFixed(2),y_m:+(z.y*U).toFixed(2),plants:z.n,mix:Object.fromEntries(GZ_SIZES.map(([k],i)=>[k,z.mix[i]])),area_m2:+z.area.toFixed(2),length_m:GZ_TYPES[z.t].lin?+z.len.toFixed(2):null,clearance_ok:z.ok}))};
    blob=new Blob([JSON.stringify(data,null,1)],{type:'application/json'}); name='acko-green-zones.json';
  }
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name; document.body.appendChild(a); a.click(); setTimeout(()=>{ URL.revokeObjectURL(a.href); a.remove(); },500);
}
function wireGreen(){
  const sc=$('#sc-green'), svg=$('#gzsvg');
  let drag=null;
  sc.addEventListener('click',e=>{
    const v=e.target.closest('[data-v]'); if(v){ gzSetView(v.dataset.v); return; }
    const l=e.target.closest('[data-l]'); if(l){ GZS.lay[l.dataset.l]=!GZS.lay[l.dataset.l]; gzDraw(); return; }
    const m=e.target.closest('[data-m]'); if(m){ GZS.mode=m.dataset.m; sc.classList.toggle('gz-adding',GZS.mode==='add'); gzDraw(); return; }
    const zb=e.target.closest('[data-zoom]'); if(zb){ const k=zb.dataset.zoom; if(k==='fit'){ GZS.vb=null; gzVB(); gzDraw(); } else gzZoom(k==='in'?1.6:1/1.6); return; }
    const act=e.target.closest('[data-act]'); if(act&&act.tagName==='BUTTON'){ gzAct(act.dataset.act); return; }
    const tr=e.target.closest('tr[data-zid],tr[data-sid]');
    if(tr){ if(tr.dataset.zid){ GZS.sel={z:tr.dataset.zid}; const z=GZ.zones.find(x=>x.id===tr.dataset.zid); if(z) gzFocus(z); } else { GZS.sel={sp:tr.dataset.sid}; } gzDraw(); return; }
  });
  sc.addEventListener('change',e=>{
    const t=e.target;
    /* the assumptions table keeps its fields (and focus): only the analysis, plan and totals refresh */
    if(t.dataset.def){ const k=t.dataset.def; (GZS.st.defs[k]=GZS.st.defs[k]||{})[t.dataset.f]=+t.value; t.classList.add('ov'); gzRun(); gzDraw(); gzSave(); return; }
    if(t.dataset.g){ GZS.st.g[t.dataset.g]=+t.value; t.classList.add('ov'); gzRun(); gzDraw(); gzSave(); return; }
    if(t.dataset.sp&&GZS.sel&&GZS.sel.sp){ (GZS.st.sp[GZS.sel.sp]=GZS.st.sp[GZS.sel.sp]||{})[t.dataset.sp]=+t.value; gzRecalc(); return; }
    if(t.dataset.act==='type'||t.dataset.act==='n'){ const z=GZ.zones.find(x=>x.id===GZS.sel.z); if(z){ gzPin(z,t.dataset.act==='type'?{t:t.value}:{n:+t.value}); gzRecalc(); } return; }
    if(t.dataset.act==='import'&&t.files&&t.files[0]){ t.files[0].text().then(s=>{ try{ const d=JSON.parse(s), st=d.state||d; if(st&&st.defs){ GZS.st=Object.assign({defs:{},sp:{},g:{},pin:{},del:[],add:[],seq:0},st); gzRecalc(); } }catch(err){ alert('That file is not a green zone export.'); } }); }
  });
  svg.addEventListener('pointerdown',e=>{
    const g=e.target.closest('[data-zid]');
    if(GZS.mode==='add'&&(GZS.view==='prop'||GZS.view==='dash')){
      const [x,y]=gzPt(e), sp=gzSpaceAt(x,y);
      if(!sp||GZ.R[sp.id].sup){ gzToast(sp?'Support spaces are not planted.':'Place zones inside the floor.'); return; }
      const t=GZS.addT==='auto'?gzAutoType(x,y,sp):GZS.addT, id='m'+(++GZS.st.seq);
      GZS.st.add.push({id,x:r1(x),y:r1(y),t,ang:0}); GZS.sel={z:id}; GZS.mode='select'; sc.classList.remove('gz-adding'); gzRecalc();
      if(!gzFree(x,y)) gzToast('Placed, but this spot is inside the circulation keep-clear zone.'); return;
    }
    if(g&&(GZS.view==='prop'||GZS.view==='dash')){
      const z=GZ.zones.find(x=>x.id===g.dataset.zid); if(!z) return;
      e.preventDefault(); svg.setPointerCapture(e.pointerId); const [x,y]=gzPt(e); drag={z,dx:z.x-x,dy:z.y-y,ox:z.x,oy:z.y,moved:false}; GZS.sel={z:z.id}; return;
    }
    const s=e.target.closest('[data-sid]'); if(s&&GZS.view!=='prop'){ GZS.sel={sp:s.dataset.sid}; gzDraw(); return; }
    if(!g&&!s){ GZS.sel=null; gzDraw(); }
    else if(!g&&s&&GZS.view==='prop'){ GZS.sel=null; gzDraw(); }
  });
  svg.addEventListener('pointermove',e=>{
    if(drag){ const [x,y]=gzPt(e); drag.moved=true; drag.z.x=x+drag.dx; drag.z.y=y+drag.dy; const ok=gzFree(drag.z.x,drag.z.y); const el=$(`[data-zid="${drag.z.id}"]`,svg); if(el){ el.setAttribute('transform',`translate(${r1(drag.z.x-drag.ox)} ${r1(drag.z.y-drag.oy)})`); el.classList.toggle('bad',!ok); } return; }
    gzHover(e);
  });
  const end=()=>{ if(!drag) return; const d=drag; drag=null; if(d.moved){ gzPin(d.z,{x:r1(d.z.x),y:r1(d.z.y)}); gzRecalc(); if(!gzFree(d.z.x,d.z.y)) gzToast('This spot blocks circulation: it is inside the keep-clear zone.'); } else gzDraw(); };
  svg.addEventListener('pointerup',end); svg.addEventListener('pointercancel',end);
  svg.addEventListener('pointerleave',()=>{ $('#gz-tip').hidden=true; });
  svg.addEventListener('keydown',e=>{ const g=e.target.closest('[data-zid]'); if(g&&(e.key==='Enter'||e.key===' ')){ e.preventDefault(); e.stopPropagation(); GZS.sel={z:g.dataset.zid}; gzDraw(); } if(g&&(e.key==='Delete'||e.key==='Backspace')){ e.preventDefault(); e.stopPropagation(); GZS.sel={z:g.dataset.zid}; gzAct('del'); } });
  $('#gz-addt').addEventListener('change',e=>{ GZS.addT=e.target.value; });
}
function gzAutoType(x,y,sp){
  let best=null,bd=1e9; GZ.cands.forEach(c=>{ const d=Math.hypot(c.x-x,c.y-y); if(c.t&&d<bd){ bd=d; best=c; } });
  return best&&bd*U<4?best.t:(GZ.R[sp.id].s.c==='work'?'edge':GZ.R[sp.id].s.c==='move'?'pocket':'island');
}
function gzAct(a){
  const sel=GZS.sel, z=sel&&sel.z&&GZ.zones.find(x=>x.id===sel.z);
  if(a==='close'){ GZS.sel=null; gzDraw(); return; }
  if(a==='del'&&z){ if(z.manual) GZS.st.add=GZS.st.add.filter(x=>x.id!==z.id); else { delete GZS.st.pin[z.ci]; GZS.st.del.push(z.ci); } GZS.sel=null; gzRecalc(); return; }
  if(a==='unpin'&&z){ if(z.manual) GZS.st.add=GZS.st.add.filter(x=>x.id!==z.id); else delete GZS.st.pin[z.ci]; GZS.sel=null; gzRecalc(); return; }
  if(a==='spreset'&&sel&&sel.sp){ delete GZS.st.sp[sel.sp]; gzRecalc(); return; }
  if(a==='reset'){ GZS.st.defs={}; GZS.st.sp={}; GZS.st.g={}; gzRecalc(); return; }
  if(a==='resetz'){ GZS.st.pin={}; GZS.st.del=[]; GZS.st.add=[]; GZS.sel=null; gzRecalc(); return; }
  if(a==='csv'||a==='json') gzExport(a);
}
function gzToast(t){ const el=$('#gz-toast'); el.textContent=t; el.hidden=false; clearTimeout(gzToast.t); gzToast.t=setTimeout(()=>el.hidden=true,3200); }
function gzHover(e){
  const tip=$('#gz-tip'); if(e.pointerType!=='mouse'){ tip.hidden=true; return; }
  const z=e.target.closest('[data-zid]'), s=e.target.closest('[data-sid]');
  let h='';
  if(z){ const o=GZ.zones.find(x=>x.id===z.dataset.zid); if(o) h=`<b>${o.no} · ${GZ_TYPES[o.t].n}</b><span>${gzEsc(o.host.s.n)} · ${o.n} plants</span>`; }
  else if(s){ const r=GZ.R[s.dataset.sid], M=GZ_METRIC[GZS.view]; if(r) h=`<b>${gzEsc(r.s.n)}</b><span>${r.sup?'Support space · not planted':M?M.u(r):`${GZ_CATS[r.s.c]} · ${r.s.m2.toFixed(0)} m² · priority ${Math.round(r.prio)}`}</span>`; }
  if(!h){ tip.hidden=true; return; }
  const b=$('#sc-green').getBoundingClientRect(); tip.innerHTML=h; tip.hidden=false;
  tip.style.transform=`translate(${Math.min(e.clientX-b.left+14,b.width-250)}px,${e.clientY-b.top+16}px)`;
}
function buildGreen(){
  gzLoad(); gzRun();
  const sc=$('#sc-green');
  sc.innerHTML=`<div class="gz-bar" id="gz-bar" role="toolbar" aria-label="Green zone analysis">
    <div class="gz-seg" role="group" aria-label="Analysis layer">${GZ_VIEWS.map(([k,n])=>`<button type="button" data-v="${k}">${n}</button>`).join('')}</div>
    <div class="gz-seg sm" role="group" aria-label="Overlays"><button type="button" data-l="keep" aria-pressed="false" title="Circulation keep-clear zone">Keep-clear</button><button type="button" data-l="free" aria-pressed="false" title="Floor left for planting">Free floor</button><button type="button" data-l="routes" aria-pressed="false">Escape routes</button><button type="button" data-l="plants" aria-pressed="true">Existing plants</button></div>
    <div class="gz-seg sm" id="gz-edit" role="group" aria-label="Edit zones"><button type="button" data-m="select" aria-pressed="true" title="Click a zone to inspect it, drag to move it">Select / move</button><button type="button" data-m="add" aria-pressed="false" title="Click on the plan to add a zone">+ Add zone</button><select id="gz-addt" aria-label="Type of new zone"><option value="auto">Type: automatic</option>${GZ_TYPE_ORDER.map(t=>`<option value="${t}">${GZ_TYPES[t].n}</option>`).join('')}</select></div>
    <div class="gz-seg sm" role="group" aria-label="Zoom"><button type="button" data-zoom="out" aria-label="Zoom out">−</button><button type="button" data-zoom="fit">Fit</button><button type="button" data-zoom="in" aria-label="Zoom in">+</button></div>
    <div class="gz-kpi" id="gz-kpi" aria-live="polite"></div></div>
  <div class="gz-main"><svg id="gzsvg" class="dsvg" viewBox="${VB}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Floor plan with the green zone analysis">
    ${gzBase()}<g id="gz-sp"></g><g class="gz-furn">${gzFit_()}</g><g id="gz-exist">${gzGreen()}</g><g class="gz-parts">${gzParts()}</g><g id="gz-free"></g><g id="gz-keep"></g><g id="gz-routes"></g><g id="gz-lbl"></g><g id="gz-zones"></g></svg>
    <p class="gz-banner" id="gz-banner" hidden>Relative design-planning index · not measured emissions · not a carbon offset</p>
    <div class="gz-leg" id="gz-leg"></div><aside class="gz-card" id="gz-card" hidden aria-live="polite"></aside><div class="gz-tip" id="gz-tip" hidden></div><div class="gz-toast" id="gz-toast" role="status" hidden></div></div>
  <div class="gz-panel" id="gz-panel" hidden></div>`;
  wireGreen(); gzDraw();
  gzRO=new ResizeObserver(()=>{ if(sc.classList.contains('on')) gzDraw(); }); gzRO.observe($('.gz-main',sc));
}
function gzEnter(v){ return ()=>{ if(!GZ) return; GZS.view=v; if(GZS.sel&&GZS.sel.z&&v!=='prop'&&v!=='dash') GZS.sel=null; $('#sc-green').dataset.view=v; gzDraw(); gzPanel(); }; }
function gzFlow(){
  const st=['Layout','Space classification','Occupancy','Footfall','Dwell time','Relative carbon impact','Biophilic priority','Green zone identification','Plant quantity','Plant type','Placement','Green score'];
  return `<ol class="gz-flow">${st.map(s=>`<li>${s}</li>`).join('')}</ol>`;
}
function gzTop(k,n){ return GZ.rows.filter(r=>!r.sup).sort((a,b)=>b[k]-a[k]).slice(0,n); }
