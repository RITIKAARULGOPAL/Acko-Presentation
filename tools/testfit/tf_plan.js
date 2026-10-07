
/* ---------- plan layers ---------- */
const svgWrap=inner=>`<svg class="dsvg" viewBox="${VB}" preserveAspectRatio="xMidYMid meet" aria-hidden="true">${inner}</svg>`;
const lyr=(cls,z,inner,style)=>`<div class="lyr ${cls}" style="--z:${z}px;${style||''}">${svgWrap(inner)}</div>`;
const nbAttr=a=>{ const ctx=ctxOf(a)||'X'; return `data-nb="${ctx}" data-area="${a}"`; };
const byArea=fn=>ALL_IDS.map(a=>{ const s=fn(a); return s?`<g ${nbAttr(a)}>${s}</g>`:''; }).join('');
const TERRACES=RF.terraces.map(p=>({pts:p,c:centroid(p),m2:polyM2(p)}));
function xPath(p){ const b=bounds(p); return `M${b.x0} ${b.y0}L${b.x1} ${b.y1}M${b.x1} ${b.y0}L${b.x0} ${b.y1}`; }
function shellSVG(){
  let s=PA(PD(RF.plate),'slab');
  TERRACES.forEach(a=>{ s+=PA(PD(a.pts),'terrace'); });
  s+=PA(PD(RF.cutout),'void')+PA(xPath(RF.cutout),'void-x');
  s+=`<g class="corefade">${PA(G('cored','S'),'rf-cored')}${PA(G('stair','S'),'rf-stair')}${PA(G('core','S'),'rf-core')}</g>`;
  s+=RF.cols.map(c=>R({x:c[0],y:c[1],w:c[2],h:c[3]},'col')).join('');
  s+=DRAW(PD(RF.plate),'s-plate',0);
  let lb=STAIRS.map(st=>T(st.x+st.w/2,st.y+st.h+34,'STAIR '+st.id,'lbl-shell')).join('');
  TERRACES.forEach(a=>{ lb+=T(a.c.x,a.c.y+10,'TERRACE','lbl-shell'); });
  return s+`<g class="lbls">${lb}</g>`;
}
const SHELL_COPY=PA(G('core','S'),'xw');
function siteSVG(){
  const light=`<path class="daylight" d="${PD(RF.plate)} ${PD(RF.plateIn)}"/>`+T(PB.x0+700,PB.y0+70,'6 m DAYLIGHT BAND','ann sunc')+T((PB.x0+PB.x1)/2,PB.y1+110,`${RF.len.toFixed(1)} m façade to façade · ${RF.depth.toFixed(1)} m deep`,'ann',' text-anchor="middle"');
  let grid=`<path class="dimline" d="M${PB.x0} ${PB.y0-70}H${PB.x1}M${PB.x0} ${PB.y0-95}V${PB.y0-45}M${PB.x1} ${PB.y0-95}V${PB.y0-45}"/>`+T((PB.x0+PB.x1)/2,PB.y0-88,`${RF.len.toFixed(1)} m`,'ann',' text-anchor="middle"');
  grid+=`<path class="dimline" d="M${PB.x1+70} ${PB.y0}V${PB.y1}M${PB.x1+45} ${PB.y0}H${PB.x1+95}M${PB.x1+45} ${PB.y1}H${PB.x1+95}"/>`+T(PB.x1+125,(PB.y0+PB.y1)/2,`${RF.depth.toFixed(1)} m`,'ann',` text-anchor="middle" transform="rotate(90 ${PB.x1+125} ${(PB.y0+PB.y1)/2})"`);
  let rings=`<g clip-path="url(#clip-rf)">`;
  STAIRS.forEach(st=>{ const cx=st.x+st.w/2, cy=st.y+st.h/2; rings+=`<circle cx="${cx}" cy="${cy}" r="${45/U}" class="ring-f"/>`; [15,30,45].forEach(m=>{ rings+=`<circle cx="${cx}" cy="${cy}" r="${m/U}" class="ring"/>`; }); });
  rings+=`</g>`;
  const s1=STAIRS[0]; [15,30,45].forEach(m=>{ rings+=T(s1.x+s1.w/2-m/U+6,s1.y+s1.h/2-14,`${m} m`,'ann firec'); });
  let exits='';
  STAIRS.forEach(st=>{ exits+=R(st,'exit-r')+T(st.x+st.w/2,st.y+st.h/2+14,`EXIT ${st.id}`,'exit-t'); });
  let routes='';
  ROUTES.forEach(r=>{
    const d='M'+r.pts.map(p=>p.join(' ')).join('L'), o=r.pts[0];
    const up=o[1]<(PB.y0+PB.y1)/2;
    routes+=`<path class="route" d="${d}"/>`+C({x:o[0],y:o[1]},11,'route-o')+T(o[0]+18,up?o[1]+50:o[1]-26,`${r.m.toFixed(1)} m`,'route-t');
  });
  return `<g class="gx g-light">${light}</g><g class="gx g-grid">${grid}</g><g class="gx g-rings">${rings}</g><g class="gx g-exits">${exits}</g><g class="gx g-routes">${routes}</g>`;
}
function zonesSVG(){
  let s=NBS.map((nb,i)=>`<path d="${PD(RF.areas[nb.id])}" class="zone" data-nb="${nb.id}" style="--c:var(${nb.c});--d:${i*.12}s"/>`).join('');
  s+=SHARED.map((t,i)=>`<path d="${PD(RF.areas[t.id])}" class="zone ts${t.id[0]==='R'?' rc':''}" data-nb="TS" data-ts="${t.id}" style="--d:${.8+i*.1}s"/>`).join('');
  return s;
}
function textSVG(){
  const rl=(a,t,dy)=>T(RF.lab[a][0],RF.lab[a][1]+(dy||0),t,'rlabel');
  let s=`<g data-nb="TS">${rl('TW','CAFÉ AND DINING',-60)}${rl('TC','LOBBY',-40)}${rl('R1','RECEPTION',-50)}${rl('R2','RECEPTION',-50)}${TERRACES.map(a=>T(a.c.x,a.c.y+10,'TERRACE','rlabel')).join('')}</g>`;
  return s;
}
const LABELS=[];
const LABEL_NUDGE={N02:[-120,0],N03:[190,0]};   // keep neighbouring pills apart (drawing units)
function labelSet(){
  NBS.forEach((nb,i)=>{ const l=RF.lab[nb.id], n=LABEL_NUDGE[nb.id]||[0,0]; LABELS.push({key:nb.id,x:l[0]+n[0],y:l[1]+n[1],h:60,g:'g-zones',kind:'zl',nb:nb.id,c:`var(${nb.c})`,d:.3+i*.12,html:`<div class="ol-n">${nb.name}</div><div class="ol-s">${nb.team}</div>`}); });
  LABELS.push({key:'TS',x:RF.lab.TW[0],y:RF.lab.TW[1]+30,h:60,g:'g-zones',kind:'zl',nb:'TS',c:'var(--brand)',d:1,html:'<div class="ol-n">Shared spaces</div><div class="ol-s">café and dining</div>'});
  [['R1','Reception','visitor hub'],['R2','Reception','waiting lounge'],['TC','Lobby','by the lifts']].forEach(([a,n,sub],j)=>{ const l=RF.lab[a]; LABELS.push({key:a,x:l[0],y:l[1],h:44,g:'g-zones',kind:'zl sm',nb:'TS',c:'var(--brand)',d:1.1+j*.1,html:`<div class="ol-n">${n}</div><div class="ol-s">${sub}</div>`}); });
  [['Fit-out','g-fit'],['Neighbourhoods','g-zones'],['Shell and core','g-shell']].forEach(([t,g])=>LABELS.push({key:'L-'+g,x:PB.x0+40,y:PB.y0+40,h:0,g,kind:'ll',html:t}));
}
const anchor=(key,p,x,y,h,cls)=>`<i class="anc ${cls||''}" data-a="${key}" data-p="${p}" style="left:${r1(x)}px;top:${r1(y)}px;--h:${h}px"></i>`;
const px=(x,y)=>[(x-VBX)*PS,(y-VBY)*PS];
function anchorsHTML(){ return LABELS.map(l=>{ const [ax,ay]=px(l.x,l.y); return anchor(l.key,'lift',ax,ay,l.h,l.g)+(l.kind.startsWith('zl')?anchor(l.key,'foot',ax,ay,2,l.g):''); }).join(''); }
function overlayHTML(){
  return LABELS.map(l=>l.kind.startsWith('zl')
    ?`<div class="ol ${l.kind}" data-ol="${l.key}" data-nb="${l.nb}" style="--c:${l.c};--d:${l.d}s"><div class="ol-pill">${l.html}</div><div class="ol-stem"></div></div>`
    :`<div class="ol ll" data-ol="${l.key}"><div class="ll-in"><b>${l.html}</b><i></i></div></div>`).join('');
}
/* keep overlay labels glued to their 3D anchors while the camera moves */
function linkOverlay(host,ovl,space){
  return $$('[data-ol]',ovl).map(el=>({el,stem:$('.ol-stem',el),lift:$(`.anc[data-a="${el.dataset.ol}"][data-p="lift"]`,space),foot:$(`.anc[data-a="${el.dataset.ol}"][data-p="foot"]`,space),host}));
}
let LINKS=[], DLINKS=[], trackUntil=0, tracking=false;
function place(list){
  if(!list.length) return;
  const h=list[0].host.getBoundingClientRect();
  list.forEach(o=>{ if(!o.lift) return; const a=o.lift.getBoundingClientRect(); o.el.style.transform=`translate(${(a.left-h.left).toFixed(1)}px,${(a.top-h.top).toFixed(1)}px)`; if(o.foot&&o.stem){ const f=o.foot.getBoundingClientRect(); o.stem.style.height=Math.max(0,f.top-a.top).toFixed(1)+'px'; } });
}
function placeAll(){ if(SCENES.plan.classList.contains('on')) place(LINKS); if(SCENES.dive.classList.contains('on')) place(DLINKS); }
function follow(ms){ trackUntil=Math.max(trackUntil,performance.now()+ms); if(tracking) return; tracking=true; const loop=()=>{ placeAll(); if(performance.now()<trackUntil) requestAnimationFrame(loop); else tracking=false; }; requestAnimationFrame(loop); }
function buildPlan(){
  const N=7, out=[], pf=$('#plan-fit');
  pf.style.cssText=`width:${PW}px;height:${PH}px;margin:${-PH/2}px 0 0 ${-PW/2}px`;
  out.push(lyr('g-shell base',0,shellSVG()));
  for(let i=0;i<N;i++) out.push(lyr('g-shell sc'+(i===N-1?' top':''),.2,SHELL_COPY,`--i:${i}`));
  out.push(lyr('g-shell site',.5,siteSVG()));
  out.push(lyr('g-zones zones',1.5,zonesSVG()));
  out.push(lyr('g-fit furn',2,byArea(a=>PA(G('furn',a),'rf-furn')+PA(G('green',a),'rf-green'))));
  out.push(lyr('g-fit hits',2.2,AREA_IDS.map(a=>`<g ${nbAttr(a)} style="--c:${isNB(a)?`var(${NBS[nbIndex(a)].c})`:'var(--brand)'}">${hitsFor(a)}</g>`).join('')));
  for(let i=0;i<N;i++) out.push(lyr('g-fit wc'+(i===N-1?' top':''),2.5,byArea(a=>PA(G('part',a),'rf-part')),`--i:${i}`));
  out.push(lyr('g-fit text',4,textSVG()));
  labelSet();
  out.push(anchorsHTML());
  $('#plan3d').innerHTML=out.join('');
  $('#ovl').innerHTML=overlayHTML();
  LINKS=linkOverlay($('#sc-plan'),$('#ovl'),$('#plan3d'));
}

/* ---------- cover, concept, overview, numbers ---------- */
function buildCover(){
  const svg=$('#cover-bg'); svg.setAttribute('viewBox',VB);
  const z=NBS.map((nb,i)=>`<path d="${PD(RF.areas[nb.id])}" class="zone" style="--c:var(${nb.c});--d:${1.6+i*.15}s;fill-opacity:.18;transform:none"/>`).join('')
    +SHARED.map(t=>`<path d="${PD(RF.areas[t.id])}" class="zone ts" style="--d:2.6s;fill-opacity:.2;transform:none"/>`).join('');
  svg.innerHTML=PA(PD(RF.plate),'slab')+PA(G('core','S'),'rf-core')+RF.cols.map(c=>R({x:c[0],y:c[1],w:c[2],h:c[3]},'col')).join('')+DRAW(PD(RF.plate),'s-plate',0)+z;
  $('#cover-meta').textContent=`${PROJECT.floor} · ${PROJECT.site} · ${fmt(m2ft(RF.plateM2))} sq ft · ${TOT.desks} workstations · 6 neighbourhoods`;
}
/*CONCEPT*/
function vbOf(id,pad){ const b=bounds(RF.areas[id]); pad=pad==null?40:pad; return [Math.floor(b.x0-pad),Math.floor(b.y0-pad),Math.ceil(b.x1-b.x0+2*pad),Math.ceil(b.y1-b.y0+2*pad)]; }
function nbMini(i,extra){
  const nb=NBS[i], v=vbOf(nb.id), vb=v.join(' ');
  return `<svg class="dsvg" viewBox="${vb}" preserveAspectRatio="xMidYMid meet" aria-hidden="true" style="--c:var(${nb.c});--hl:var(${nb.c})"><svg x="${v[0]}" y="${v[1]}" width="${v[2]}" height="${v[3]}" viewBox="${vb}" overflow="hidden">${PA(PD(RF.plate),'slab')}${PA(PD(RF.plate),'plate-o')}${PA(G('core','S'),'rf-core mini')}${RF.cols.map(c=>R({x:c[0],y:c[1],w:c[2],h:c[3]},'col on')).join('')}${PA(PD(RF.areas[nb.id]),'zone-mini')}${extra&&extra.under||''}${PA(G('furn',nb.id),'rf-furn')}${PA(G('green',nb.id),'rf-green')}${PA(G('part',nb.id),'rf-part')}${extra&&extra.over||''}</svg></svg>`;
}
function kitLine(k){ const meet=(k.sprint||0)+(k.dept||0); return [`${k.desk} desks`, meet?`${meet} meeting`:'', k.huddle?`${k.huddle} huddle${k.huddle>1?'s':''}`:'', k.booth?`${k.booth} booths`:''].filter(Boolean).join(' · '); }
function buildOverview(){
  $('#ov-grid').innerHTML=NBS.map((nb,i)=>{ const k=KITS[nb.id]; return `<button class="ov-card" type="button" data-go-nb="${i}" style="--c:var(${nb.c});--d:${i*.08}s"><div class="ov-h"><span class="ov-n">${nb.name}</span><span class="ov-id">${fmt(m2ft(M2[nb.id]))} sq ft</span></div>${nbMini(i)}<div class="ov-t">${nb.team} · ${nb.pos}</div><div class="ov-k">${kitLine(k)}</div></button>`; }).join('');
}
function buildNumbers(){
  const tiles=[
    [TOT.desks,'','Workstations, incl. 4-seat collaboration tables'],[6,'','Self-contained neighbourhoods'],[TOT.meet,'','Meeting and collaboration rooms'],
    [TOT.booth+TOT.duo,'','Phone booths and 2-pax rooms'],[TOT.daylight,'%','Workstations within 6 m of the façade'],[Math.round(m2ft(RF.plateM2)),'sq ft','Floor plate'],
  ];
  $('#nums').innerHTML=`<div class="tiles">${tiles.map(([v,u,l],i)=>`<div class="tile" style="--d:${i*.08}s"><b><span data-count="${v}">${fmt(v)}</span>${u?`<small>${u}</small>`:''}</b><span>${l}</span></div>`).join('')}</div>${areaBar()}<div class="thanks"><h3>Thank you</h3><p>Officebanao × Acko · Test fit 02 · Draft for discussion</p></div>`;
}
function areaBar(){
  const pct=m=>100*m/RF.plateM2;
  let track='';
  NBS.forEach(nb=>{ track+=`<i style="--c:var(${nb.c});width:${pct(M2[nb.id]).toFixed(2)}%"></i>`; });
  AREA.slice(1).forEach(a=>{ track+=`<i style="--c:${a.c};width:${pct(a.m2).toFixed(2)}%"></i>`; });
  const key=AREA.map(a=>`<b>${pct(a.m2).toFixed(1)}%</b><span>${a.label}</span><em>${fmt(m2ft(a.m2))} sq ft</em>`).join('');
  return `<div class="abar" role="img" aria-label="Area split: ${AREA.map(a=>`${a.label} ${pct(a.m2).toFixed(1)} percent`).join(', ')}"><div class="abar-t">${track}</div><div class="abar-k">${key}</div></div>`;
}
/* what each neighbourhood got, counted from the drawing; the brief column waits for Acko's numbers */
const BRIEF={desk:null,sprint:null,dept:null,huddle:null,duo:null,booth:null,pantry:null,zen:null,cabin:null};
const MATRIX=[
  ['desk','Workstations'],['sprint','Quick sprint rooms'],['dept','Departmental rooms'],['huddle','Collaboration huddles'],
  ['duo','2-pax rooms'],['booth','Phone booths'],['pantry','Pantry points'],['zen','Zen rooms'],['cabin','Executive cabins'],
];
function buildAlloc(){
  const tsIds=['TW','TC','R1','R2'];
  const head=`<tr><th class="am-i">Space</th><th class="am-b">Brief</th>${NBS.map((nb,i)=>`<th class="am-nb${i?'':' ps'}" style="--c:var(${nb.c})"><span>${nb.name}</span><small>${nb.id} · ${fmt(m2ft(M2[nb.id]))} sq ft</small></th>`).join('')}<th class="am-ts ps">Shared spaces<small>café, lobby, receptions</small></th><th class="am-t">Total</th></tr>`;
  const body=MATRIX.map(([k,name])=>{
    const vals=NB_IDS.map(a=>KITS[a][k]||0), ts=sumK(tsIds,k), x=KITS.X[k]||0, tot=vals.reduce((s,v)=>s+v,0)+ts+x;
    const max=Math.max(...vals), b=BRIEF[k];
    return `<tr data-row="${k}"><td class="am-i">${name}</td><td class="am-b">${b==null?'<span class="na">to add</span>':fmt(b)}</td>${vals.map((v,i)=>`<td class="${i?'':'ps '}${v===0?'zero':''}" style="--c:var(${NBS[i].c})"><span class="cell" style="--f:${max?(v/max).toFixed(2):0}">${v||'–'}</span></td>`).join('')}<td class="am-ts ps">${ts||'–'}</td><td class="am-t">${fmt(tot)}${x?`<small> incl. ${x} elsewhere</small>`:''}</td></tr>`;
  }).join('');
  $('#am').innerHTML=`<table class="am tf"><thead>${head}</thead><tbody>${body}</tbody></table>`;
  $('#am').className='alloc m-ach';
}

/* ---------- deep dive ---------- */
const KIT=[
  {k:'desk',n:'Workstations',one:'workstation',c:'Work',v:k=>k.desk},
  {k:'cabin',n:'Executive cabins',one:'executive cabin',c:'Work',v:k=>k.cabin},
  {k:'sprint',n:'Quick sprint rooms',one:'quick sprint room',c:'Meet',v:k=>`${k.sprint} · ${k.sprintSeats} seats`},
  {k:'dept',n:'Departmental rooms',one:'departmental room',c:'Meet',v:k=>`${k.dept} · ${k.deptSeats} seats`},
  {k:'board',n:'Boardroom',one:'boardroom',c:'Meet',v:k=>`${k.boardSeats} seats`},
  {k:'huddle',n:'Collaboration huddles',one:'collaboration huddle',c:'Collaborate',v:k=>`${k.huddle} · ${k.huddleSeats} seats`},
  {k:'hatchery',n:'The Hatchery',one:'The Hatchery',c:'Collaborate',v:k=>`${k.hatcherySeats} seats`},
  {k:'studio',n:'Studio',one:'studio',c:'Collaborate',v:k=>k.studio},
  {k:'duo',n:'Two-person rooms',one:'two-person room',c:'Focus',v:k=>k.duo},
  {k:'booth',n:'Phone booths',one:'phone booth',c:'Focus',v:k=>k.booth},
  {k:'pantry',n:'Pantry points',one:'pantry point',c:'Recharge',v:k=>k.pantry},
  {k:'zen',n:'Zen rooms',one:'zen room',c:'Recharge',v:k=>k.zen},
  {k:'mother',n:"Mother's room",one:"mother's room",c:'Recharge',v:k=>k.mother},
  {k:'prayer',n:'Prayer room',one:'prayer room',c:'Recharge',v:k=>k.prayer},
];
const CATS=['Work','Meet','Collaborate','Focus','Recharge'];
const kitFor=id=>KIT.filter(it=>(KITS[id][it.k]||0)>0);
function kitPoints(id){
  const pts={};
  KIT.forEach(it=>{ const s=SP.filter(x=>x.area===id&&x.k===it.k); if(!s.length) return;
    if(it.k==='desk'){ const c={x:s.reduce((a,x)=>a+x.x,0)/s.length,y:s.reduce((a,x)=>a+x.y,0)/s.length}; pts.desk=s.reduce((b,x)=>dist(x,c)<dist(b,c)?x:b,s[0]); }
    else pts[it.k]={x:s[0].x,y:s[0].y}; });
  return pts;
}
let DIVE_NB=null, AX={w:420,h:280};
function renderDive(i){
  const nb=NBS[i], id=nb.id, pts=kitPoints(id), kit=kitFor(id);
  const v=vbOf(id), vb=v.join(' ');
  const num=k=>kit.findIndex(it=>it.k===k)+1;
  const marks=kit.map(it=>pts[it.k]?`<g class="km" data-k="${it.k}" transform="translate(${r1(pts[it.k].x)} ${r1(pts[it.k].y)})"><circle r="17"/><text y="6.5">${num(it.k)}</text></g>`:'').join('');
  DIVE_NB=id;
  $('#dv-plan-svg').innerHTML=nbMini(i,{over:hitsFor(id)+marks});
  const k=Math.min(440/v[2],300/v[3]); AX={w:Math.round(v[2]*k),h:Math.round(v[3]*k)};
  $('#axo-fit').style.cssText=`width:${AX.w}px;height:${AX.h}px;margin:${-AX.h/2}px 0 0 ${-AX.w/2}px`;
  const sv=inner=>`<svg class="dsvg" viewBox="${vb}" aria-hidden="true">${inner}</svg>`;
  const lay=(cls,z,inner,st)=>`<div class="lyr ${cls}" style="--z:${z}px;${st||''}">${sv(inner)}</div>`;
  let h=lay('',0,PA(PD(RF.plate),'slab')+PA(PD(RF.areas[id]),'zone-mini'));
  h+=lay('',2,PA(G('furn',id),'rf-furn')+PA(G('green',id),'rf-green'));
  h+=lay('',2.2,hitsFor(id));
  for(let j=0;j<7;j++) h+=lay('dwc'+(j===6?' top':''),0,PA(G('part',id),'rf-part'),`--i:${j}`);
  kit.forEach(it=>{ const p=pts[it.k]; if(!p) return; const ax=(p.x-v[0])*k, ay=(p.y-v[1])*k; h+=anchor('k-'+it.k,'lift',ax,ay,34)+anchor('k-'+it.k,'foot',ax,ay,4); });
  const ax=$('#axo3d'); ax.innerHTML=h; ax.style.cssText=`--c:var(${nb.c});--hl:var(${nb.c})`;
  const ovl=$('#dv-ovl'); ovl.style.cssText=`--c:var(${nb.c});--hl:var(${nb.c})`;
  ovl.innerHTML=kit.map(it=>pts[it.k]?`<div class="om" data-ol="k-${it.k}" data-k="${it.k}"><b>${num(it.k)}</b><div class="ol-stem"></div></div>`:'').join('');
  DLINKS=linkOverlay($('#dv-axo'),ovl,ax);
  const dive=$('#dive'); dive.classList.remove('dv-go'); void dive.offsetWidth; requestAnimationFrame(()=>dive.classList.add('dv-go'));
  fit(); follow(2600);
}
