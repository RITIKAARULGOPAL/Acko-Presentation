/* =====================================================================
   SITE ANALYSIS · Regalium, Koramangala
   Built by tools/site/site.py from open map data (OpenStreetMap via Overture),
   NOAA weather records, the sun's geometry and the site visit.
   ===================================================================== */
const SITE=/*SITE*/null;
const SUN=SITE.sun, UP=SITE.up, FACES=SUN.faces, FX=SITE.facts, NUM=SITE.nums;
const FACE_LBL={N:'north façade',S:'south façade',E:'east end',W:'south-west end',T:'terrace glass'};
const mtxt=m=>m>=1000?`${(m/1000).toFixed(1)} km`:`${Math.round(m/10)*10} m`;
const wmin=m=>Math.max(1,Math.round(m/80));                       // walking at 80 m a minute
const comp8=b=>['north','north-east','east','south-east','south','south-west','west','north-west'][Math.round((((b%360)+360)%360)/45)%8];
const placeName=a=>isNB(a)?nbName(a):({TW:'the café',TC:'the lobby',R1:'the west reception',R2:'the east reception'})[a]||'';
const nbChip=a=>isNB(a)?`<b class="sn" style="--c:var(${NBS[nbIndex(a)].c})">${nbName(a)}</b>`:`<b class="sn ts">${placeName(a).replace(/^the /,'')}</b>`;
const facesTxt=fs=>listJoin(fs.map(f=>`the ${FACE_LBL[f]}`));
/* plan units → map metres (map centre, y down), from the fit of the plate into the footprint */
const toMap=(u,v)=>{ const t=SITE.onSite.tf; return [t[0]*u+t[1]*v+t[2], t[3]*u+t[4]*v+t[5]]; };

/* ---------- the site map: city view and the block, one SVG that zooms and turns ---------- */
const SV={city:{z:1,rot:0},near:{z:3.4,rot:-UP}};
function buildSite(){
  const W=SITE.frame.w, H=SITE.frame.h, svg=$('#sitesvg');
  svg.setAttribute('viewBox',`${-W/2} ${-H/2} ${W} ${H}`);
  const up=(x,y,inner,cls,d)=>`<g transform="translate(${x} ${y})"><g class="m-up ${cls||''}"${d!=null?` style="--d:${d}s"`:''}>${inner}</g></g>`;
  let w=`<rect class="m-ground" x="${-W}" y="${-H}" width="${2*W}" height="${2*H}"/>`;
  Object.entries(SITE.land).forEach(([k,d])=>{ w+=`<path class="m-lu m-${k}" d="${d}"/>`; });
  SITE.water.forEach(x=>{ w+=`<path class="m-water" d="${x.d}"/>`; });
  SITE.roads.forEach(rd=>{ w+=`<path class="m-road r${rd.rank}" d="${rd.d}" style="stroke-width:${rd.w}px"/>`; });
  SITE.rail.forEach(x=>{ w+=`<path class="m-rail${x.live?'':' plan'}" d="${x.d}"><title>${x.n}${x.live?'':' (proposed)'}</title></path>`; });
  const bl=f=>SITE.buildings.filter(f).map(b=>b[0]).join('');
  w+=`<path class="m-bld" d="${bl(b=>b[1]<20)}"/><path class="m-bld tall" d="${bl(b=>b[1]>=20)}"/>`;
  const [gx,gy]=SITE.gate;
  w+=`<g class="m-rings v-city">${[400,800].map(m=>`<circle cx="${gx}" cy="${gy}" r="${m}" class="m-ring"/>`).join('')}</g>`;
  w+=`<g class="m-site">${SITE.footprint.wings.map(d=>`<path class="m-wing" d="${d}"/>`).join('')}</g>`;
  const os=SITE.onSite;
  w+=`<g class="m-floor"><path class="m-plate" d="${os.plate}"/>${os.terraces.map(d=>`<path class="m-terr" d="${d}"/>`).join('')}</g>`;
  /* labels keep their size and stay upright while the map zooms and turns */
  const seen=[];
  const roadLab=(l,cls)=>`<text class="m-rl ${cls}" transform="translate(${l.x} ${l.y}) rotate(${l.a})" text-anchor="middle" dy="0.35em">${l.t.toUpperCase()}</text>`;
  SITE.labels.filter(l=>(l.rank<=1||l.t==='Jyoti Nivas College Road')&&!/u\/c/.test(l.t)).forEach(l=>{ if(seen.some(s=>Math.hypot(s.x-l.x,s.y-l.y)<80)) return; seen.push(l); w+=roadLab(l,'v-city'); });
  SITE.nearLabels.forEach(l=>{ w+=roadLab(l,'v-near'); });
  [400,800].forEach((m,i)=>{ w+=up(gx-m*.707,gy+m*.707,`<text class="m-ring-t">${wmin(m)} MIN WALK</text>`,'v-city'); });
  /* landmarks with their walking distance from the site gate */
  SITE.marks.filter(m=>m.k!=='metro').forEach((m,i)=>{
    const right=m.x<380;
    w+=up(m.x,m.y,`<circle r="7" class="m-lm m-${m.k}"/><text class="m-lt" x="${right?13:-13}" dy="-.15em" text-anchor="${right?'start':'end'}">${m.n.replace(' Koramangala','').replace(' Medical College Hospital',' Hospital')}</text><text class="m-ld" x="${right?13:-13}" dy="1.15em" text-anchor="${right?'start':'end'}">${mtxt(m.walk||m.d)} · ${wmin(m.walk||m.d)} min walk</text>`,'v-city',.6+i*.12);
  });
  /* the floor on site: façades, lift lobbies, gate */
  const AT={N:[PB.x0+(PB.x1-PB.x0)*.8,PB.y0+130],S:[PB.x0+(PB.x1-PB.x0)*.62,PB.y1+330],E:[PB.x1+620,(PB.y0+PB.y1)/2+120],W:[0,0]};
  const fl=f=>{ const F=FACES[f]; if(!F) return ''; const a=f==='W'?[F.mid[0]+F.n[0]*760,F.mid[1]+F.n[1]*760]:AT[f], p=toMap(a[0],a[1]);
    return up(p[0].toFixed(1),p[1].toFixed(1),`<text class="m-ft" text-anchor="middle">${({N:'NORTH FAÇADE',S:'SOUTH FAÇADE',E:'EAST END',W:'SW END'})[f]}</text><text class="m-fd" text-anchor="middle" dy="1.3em">faces ${Math.round(F.brg)}°</text>`,'v-near'); };
  w+=['N','S','E','W'].map(fl).join('');
  (RF.lifts||[]).forEach((l,i)=>{ const p=toMap(l.x,l.y); w+=up(p[0].toFixed(1),p[1].toFixed(1),`<circle r="5" class="m-liftc"/><text class="m-bt" y="-12" text-anchor="middle">LIFT LOBBY</text>`,'v-near'); });
  w+=up(gx,gy,`<circle r="9" class="m-gate-p"/><circle r="5" class="m-gate"/><text class="m-gt" x="12" dy=".35em">${FX.plus.split(',')[0]}</text>`,'',.3);
  const fc=[0,0];
  w+=up(fc[0],fc[1]-92,`<text class="m-st" text-anchor="middle">REGALIUM</text><text class="m-sd" text-anchor="middle" dy="1.25em">Acko · ${FX.floor}</text>`,'v-city m-site-l',.2);
  /* metro: off the map, so pinned to the edge in its direction */
  let edge='';
  SITE.marks.filter(m=>m.k==='metro').forEach((m,i)=>{
    const a=Math.atan2(m.y,m.x), hw=W/2-30, hh=H/2-30, k=Math.min(Math.abs(hw/Math.cos(a)),Math.abs(hh/Math.sin(a)));
    const ex=Math.cos(a)*k, ey=Math.sin(a)*k, right=ex>0;
    edge+=`<g class="m-edge" transform="translate(${ex.toFixed(0)} ${ey.toFixed(0)})" style="--d:${1+i*.15}s"><path class="m-arrow" d="M0 0l-9 -16h18z" transform="rotate(${(a*180/Math.PI-90).toFixed(1)})"/><text class="m-lt" x="${right?16:-16}" y="-30" text-anchor="${right?'start':'end'}">${m.n} · ${m.line}</text><text class="m-ld" x="${right?16:-16}" y="-30" dy="1.3em" text-anchor="${right?'start':'end'}">${mtxt(m.walk)} walk · about ${wmin(m.walk)} min</text></g>`;
  });
  const north=`<g class="m-north" transform="translate(${W/2-70} ${-H/2+80})"><g class="m-nrot"><circle r="34" class="n-c"/><path class="n-a" d="M0 -26L11 14L0 6L-11 14Z"/><text y="-42" class="m-nt" text-anchor="middle">N</text></g></g>`;
  const scale=`<g class="m-scale" transform="translate(${-W/2+50} ${-H/2+70})"><path class="m-sb" d="M0 0h200"/><path class="m-sb t" d="M0 -8v16M200 -8v16"/><text class="m-sbt" x="0" y="-16">0</text><text class="m-sbt" id="m-sbl" x="200" y="-16" text-anchor="middle">200 m</text></g>`;
  svg.innerHTML=`<defs><radialGradient id="m-fade" cx="50%" cy="50%" r="62%"><stop offset="70%" stop-color="#fff"/><stop offset="100%" stop-color="#000"/></radialGradient><mask id="m-mask"><rect x="${-W/2}" y="${-H/2}" width="${W}" height="${H}" fill="url(#m-fade)"/></mask></defs>
    <g mask="url(#m-mask)"><g class="m-world" id="m-world">${w}</g></g>${edge}${north}${scale}`;
  $('#m-attr').textContent=SITE.attribution;
  setSiteView('city');
}
function setSiteView(v){
  const s=SV[v], sc=$('#sc-site'); sc.dataset.view=v;
  sc.style.setProperty('--z',s.z); sc.style.setProperty('--inv',(1/s.z).toFixed(4)); sc.style.setProperty('--rot',s.rot+'deg'); sc.style.setProperty('--unrot',(-s.rot)+'deg');
  const m=v==='near'?50:200; $('#m-sbl').textContent=`${m} m`; $('#m-sbl').setAttribute('x',m*s.z);
  $$('#sitesvg .m-sb').forEach((p,i)=>p.setAttribute('d',i?`M0 -8v16M${m*s.z} -8v16`:`M0 0h${m*s.z}`));
}

/* ---------- sun path dome and wind rose ---------- */
const DOME=430;
const sterR=alt=>DOME*Math.tan((90-Math.max(alt,0))*Math.PI/360);
const dome=(az,alt)=>{ const r=sterR(alt), a=az*Math.PI/180; return [r*Math.sin(a),-r*Math.cos(a)]; };
const CLIM={view:'sun',wind:'monsoon'};
function buildClimate(){
  const svg=$('#climsvg'); svg.setAttribute('viewBox','-600 -560 1200 1120');
  let g=`<circle r="${DOME}" class="d-bg"/>`;
  [30,60].forEach(a=>{ g+=`<circle r="${sterR(a).toFixed(1)}" class="d-ring"/><text class="d-rt" x="4" y="${(-sterR(a)-6).toFixed(1)}">${a}°</text>`; });
  for(let a=0;a<360;a+=30){ const [x,y]=dome(a,0); g+=`<path class="d-spoke" d="M0 0L${x.toFixed(1)} ${y.toFixed(1)}"/>`; if(a%90){ const [tx,ty]=dome(a,-6).map(v=>v*1.06); g+=`<text class="d-az" x="${tx.toFixed(1)}" y="${ty.toFixed(1)}" text-anchor="middle" dy=".35em">${a}°</text>`; } }
  ['N','E','S','W'].forEach((t,i)=>{ const a=i*90*Math.PI/180, r=DOME+34; g+=`<text class="d-card" x="${(r*Math.sin(a)).toFixed(1)}" y="${(-r*Math.cos(a)).toFixed(1)}" text-anchor="middle" dy=".35em">${t}</text>`; });
  /* the floor at its true orientation */
  const s=DOME*.5/(PB.x1-PB.x0), cx=(PB.x0+PB.x1)/2, cy=(PB.y0+PB.y1)/2;
  const plan=`<g transform="rotate(${UP}) scale(${s.toFixed(5)}) translate(${-cx} ${-cy})"><path d="${PD(RF.plate)}" class="d-plate"/>${TERRACES.map(t=>`<path d="${PD(t.pts)}" class="d-terr"/>`).join('')}${STAIRS.map(st=>`<rect x="${st.x}" y="${st.y}" width="${st.w}" height="${st.h}" class="d-core"/>`).join('')}</g>`;
  const rot=(u,v)=>{ const a=UP*Math.PI/180, x=(u-cx)*s, y=(v-cy)*s; return [x*Math.cos(a)-y*Math.sin(a), x*Math.sin(a)+y*Math.cos(a)]; };
  let fl='';
  ['N','S','E','W'].forEach(f=>{ const F=FACES[f]; if(!F) return; const o=f==='N'||f==='S'?520:f==='E'?900:700, p=rot(F.mid[0]+F.n[0]*o,F.mid[1]+F.n[1]*o);
    fl+=`<text class="d-fl" x="${p[0].toFixed(1)}" y="${p[1].toFixed(1)}" text-anchor="middle" dy=".35em">${f==='W'?'SW':f} · ${Math.round(F.brg)}°</text>`; });
  /* sun paths, 21st of each month pair; the solstices and equinox carry the labels */
  let sun='';
  const KEY={jun:1,mar:1,dec:1};
  SUN.arcs.forEach((a,i)=>{
    const d='M'+a.pts.map(p=>dome(p[0],p[1]).map(v=>v.toFixed(1)).join(' ')).join('L');
    sun+=`<path class="d-arc a-${a.k}${KEY[a.k]?' key':''}" d="${d}" pathLength="1" style="--d:${.2+i*.1}s"><title>${a.label}: sunrise ${a.rise}, noon ${a.noon} at ${a.noonAlt}°, sunset ${a.set}</title></path>`;
    if(KEY[a.k]){
      a.hours.forEach(h=>{ const [x,y]=dome(h[0],h[1]); sun+=`<circle class="d-hr a-${a.k}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="7"/>`; if(a.k!=='mar'&&[7,9,15,17].includes(h[2])) sun+=`<text class="d-ht" x="${x.toFixed(1)}" y="${(y+(a.k==='jun'?-18:32)).toFixed(1)}" text-anchor="middle">${h[2]>12?h[2]-12+' pm':h[2]+(h[2]===12?' noon':' am')}</text>`; });
      const hp=a.k==='mar'?(a.hours.find(h=>h[2]===16)||a.hours[a.hours.length-1]):a.pts.reduce((b,p)=>p[1]>b[1]?p:b), [x,y]=dome(hp[0],hp[1]);
      sun+=`<g class="d-al" transform="translate(${x.toFixed(1)} ${(y+(a.k==='jun'?-64:a.k==='dec'?50:-50)).toFixed(1)})"><text text-anchor="middle" class="d-alt">${a.label}</text><text text-anchor="middle" class="d-als" dy="1.25em">noon ${a.noonAlt}° up, ${a.noonAz<90||a.noonAz>270?'north':'south'}</text></g>`;
    }
  });
  /* wind rose (meteorological: petals point to where the wind comes from) */
  const wind=`<g id="d-rose"></g>`;
  svg.innerHTML=`<g class="d-base">${g}</g><g class="d-planw">${plan}</g><g class="d-sun">${sun}</g><g class="d-wind">${wind}</g>`;
  drawRose();
}
function drawRose(){
  const S=SITE.wind.seasons.find(x=>x.id===CLIM.wind), max=Math.max(...SITE.wind.seasons.flatMap(x=>x.pct)), r0=DOME*.17, r1=DOME*.97;
  let h=`<circle r="${r0}" class="d-calm"/><text class="d-ct" text-anchor="middle" y="${r0*.62}">${S.calm}% calm</text>`;
  S.pct.forEach((p,i)=>{
    if(p<0.3) return;
    const a0=(i*22.5-9.5)*Math.PI/180, a1=(i*22.5+9.5)*Math.PI/180, r=r0+(r1-r0)*Math.sqrt(p/max);
    const P=(a,rr)=>`${(rr*Math.sin(a)).toFixed(1)} ${(-rr*Math.cos(a)).toFixed(1)}`;
    h+=`<path class="d-pet" d="M${P(a0,r0+3)}L${P(a0,r)}A${r.toFixed(1)} ${r.toFixed(1)} 0 0 1 ${P(a1,r)}L${P(a1,r0+3)}A${r0+3} ${r0+3} 0 0 0 ${P(a0,r0+3)}Z" style="--d:${(i*.03).toFixed(2)}s"><title>From the ${SITE.wind.dirs[i]}: ${p}% of the time, ${S.spd[i]} m/s on average</title></path>`;
    if(p>=8){ const am=(i*22.5)*Math.PI/180; h+=`<text class="d-pt" x="${((r+26)*Math.sin(am)).toFixed(1)}" y="${(-(r+26)*Math.cos(am)).toFixed(1)}" text-anchor="middle" dy=".35em">${SITE.wind.dirs[i]} ${Math.round(p)}%</text>`; }
  });
  $('#d-rose').innerHTML=h;
}
function setClimate(v){ CLIM.view=v; $('#sc-climate').dataset.view=v; }

/* ---------- plan overlays: north, the sun through the day, the due-diligence pins ---------- */
function northSVG(){
  const nx=PB.x0+150, ny=PB.y1-110;    // the empty corner below the slanted west end
  let s=`<g transform="translate(${nx} ${ny})"><g transform="rotate(${-UP})"><circle r="62" class="n-c pn"/><path class="n-a" d="M0 -48L20 26L0 12L-20 26Z"/><text y="-78" class="pn-t" text-anchor="middle">N</text></g></g>`;
  const lab=(f,x,y,t,rot)=>`<text class="ann fl-${f}" x="${r1(x)}" y="${r1(y)}"${rot!=null?` transform="rotate(${rot} ${r1(x)} ${r1(y)})"`:''} text-anchor="middle">${t}</text>`;
  const F=FACES;
  if(F.N) s+=lab('N',PB.x0+(PB.x1-PB.x0)*.36,PB.y0-30,`NORTH FAÇADE · FACES ${Math.round(F.N.brg)}° · CORES AND STAIRS`);
  if(F.S) s+=lab('S',PB.x0+(PB.x1-PB.x0)*.22,PB.y1+66,`SOUTH FAÇADE · FACES ${Math.round(F.S.brg)}°`);
  if(F.E) s+=lab('E',PB.x1+62,(PB.y0+PB.y1)/2,`EAST END · ${Math.round(F.E.brg)}°`,90);
  if(F.W){ const m=F.W.mid, a=Math.atan2(F.W.n[1],F.W.n[0])*180/Math.PI+90; s+=lab('W',m[0]+F.W.n[0]*62,m[1]+F.W.n[1]*62,`SW END · ${Math.round(F.W.brg)}° · HOSUR ROAD`,a>90?a-180:a); }
  return s;
}
const SUNS={k:'mar',i:6,play:0,timer:null};
function sunFrames(){ return SUN.day.find(d=>d.k===SUNS.k).frames; }
function drawSun(){
  const fr=sunFrames()[SUNS.i], host=$('#sun-p'); if(!host) return;
  if(!fr.p){ host.innerHTML=''; $('#sun-d').innerHTML=''; return; }
  host.innerHTML=fr.p.map(p=>`<path d="${p.d}" class="sunp${fr.low?' low':''}" style="--w:${Math.min(1,p.w/1000).toFixed(2)}"/>`).join('');
  /* the sun's direction in the plan, and rays falling on the lit side */
  const a=(fr.az-UP)*Math.PI/180, dx=Math.sin(a), dy=-Math.cos(a);
  const cx=(PB.x0+PB.x1)/2, cy=(PB.y0+PB.y1)/2, hw=(PB.x1-PB.x0)/2+95, hh=(PB.y1-PB.y0)/2+95;
  const k=Math.min(Math.abs(hw/(dx||1e-6)),Math.abs(hh/(dy||1e-6))), sx=cx+dx*k, sy=cy+dy*k;
  let rays='';
  for(let j=-2;j<=2;j++){ const ox=sx-dx*80+(-dy)*j*46, oy=sy-dy*80+dx*j*46; rays+=`<path class="sun-ray" d="M${r1(ox)} ${r1(oy)}l${r1(-dx*170)} ${r1(-dy*170)}"/>`; }
  let ic=`<circle cx="${r1(sx)}" cy="${r1(sy)}" r="30" class="sun-c"/>`;
  for(let j=0;j<8;j++){ const b=j*Math.PI/4; ic+=`<path class="sun-r" d="M${r1(sx+Math.cos(b)*44)} ${r1(sy+Math.sin(b)*44)}L${r1(sx+Math.cos(b)*62)} ${r1(sy+Math.sin(b)*62)}"/>`; }
  $('#sun-d').innerHTML=rays+ic;
}
function sunDepth(fr,f){ const F=FACES[f]; if(!F||F.brg==null) return 0; const c=Math.cos((fr.az-F.brg)*Math.PI/180); return c>0?3.25*c/Math.tan(fr.alt*Math.PI/180):0; }
function sunRead(){
  const fr=sunFrames()[SUNS.i], o=$('#sun-read'); if(!o) return;
  $('#sun-t').value=fr.t; $('#sun-t').textContent=fr.t;
  if(!fr.p){ o.innerHTML=`<b>${fr.t}</b> · the sun is down.`; return; }
  const top=fr.p.slice().sort((a,b)=>b.w-a.w)[0], lit=Object.entries(fr.lit||{}).sort((a,b)=>b[1]-a[1]).slice(0,3).map(([a])=>a);
  o.innerHTML=`<b>${fr.t}</b> · sun in the ${comp8(fr.az)} (${Math.round(fr.az)}°), ${Math.round(fr.alt)}° up · ${fr.dni} W/m² direct in a clear sky.
    ${top?`Strongest on the ${FACE_LBL[top.f]}: ${top.w} W/m² on the glass, reaching ${Math.min(RF.depth,sunDepth(fr,top.f)).toFixed(1)} m in.`:''}
    ${lit.length?`<span class="sun-in">In sun now: ${lit.map(nbChip).join(', ')}</span>`:''}${fr.low?' <span class="sun-low">Very low sun: buildings across the road will often block it.</span>':''}`;
}
/* the day in three beats, written from the numbers for the chosen date */
function sunBeats(k){
  const D=SUN.day.find(d=>d.k===k), F=D.frames.filter(f=>f.p);
  const win=(a,b)=>F.filter(f=>f.t>=a&&f.t<=b);
  const sumBy=(fs,key)=>{ const o={}; fs.forEach(f=>{ if(key==='face') f.p.forEach(p=>{ o[p.f]=(o[p.f]||0)+p.w; }); else Object.entries(f.lit||{}).forEach(([a,m])=>{ o[a]=(o[a]||0)+m; }); }); return Object.entries(o).sort((a,b)=>b[1]-a[1]); };
  const topF=fs=>sumBy(fs,'face').slice(0,2).map(([f])=>f), topA=fs=>sumBy(fs,'area').filter(([a])=>isNB(a)).slice(0,2).map(([a])=>a);
  const am=win('07:00','10:30'), md=win('11:00','13:30'), pm=win('14:00','18:30');
  const peak=fs=>fs.reduce((b,f)=>{ f.p.forEach(p=>{ if(!b||p.w>b.w) b={w:p.w,f:p.f,t:f.t,d:sunDepth(f,p.f)}; }); return b; },null);
  const noon=md.reduce((b,f)=>f.alt>b.alt?f:b,md[0]||F[0]), pk=peak(pm), mk=peak(am);
  const north=noon.az<90||noon.az>270;
  return [
    ['Morning',`From sunrise at ${D.rise} the sun comes in low from the ${comp8(am[0]?am[0].az:90)} onto ${facesTxt(topF(am))}${mk?`, up to ${mk.w} W/m² on the ${FACE_LBL[mk.f]} by ${mk.t}`:''}. ${topA(am).length?`${listJoin(topA(am).map(nbChip))} get${topA(am).length>1?'':'s'} most of it.`:''}`],
    ['Midday',`At noon the sun is ${Math.round(noon.alt)}° up ${north?'and north of the building':'to the south'}. Patches shrink to ${Math.max(...topF(md).map(f=>sunDepth(noon,f))).toFixed(1)} m or less along ${facesTxt(topF(md))}.`],
    ['Afternoon',`From 2 pm the sun swings ${comp8(pm[0]?pm[0].az:270)} and drops: ${facesTxt(topF(pm))} take the hardest sun${pk?`, ${pk.w} W/m² on the ${FACE_LBL[pk.f]} at ${pk.t}${pk.d>0.5?` and reaching ${Math.min(RF.depth,pk.d).toFixed(0)} m in`:''}`:''}. ${topA(pm).length?`${listJoin(topA(pm).map(nbChip))} feel${topA(pm).length>1?'':'s'} it most.`:''}`],
  ];
}
function sunCtl(){
  return `<div class="sunctl"><div class="tog" role="group" aria-label="Day of the year">${SUN.day.map(d=>`<button type="button" data-season="${d.k}" aria-pressed="${d.k===SUNS.k}">${d.label}</button>`).join('')}</div>
    <div class="sunrow"><button type="button" class="sun-play" aria-label="Play the day">${'<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 2.5v11l9-5.5z"/></svg>'}</button><input type="range" id="sun-range" min="0" max="${sunFrames().length-1}" step="1" value="${SUNS.i}" aria-label="Time of day"><output id="sun-t">${sunFrames()[SUNS.i].t}</output></div>
    <p class="sun-read" id="sun-read" aria-live="polite"></p></div>`;
}
function sunStop(){ clearInterval(SUNS.timer); SUNS.timer=null; const b=$('.sun-play'); if(b) b.classList.remove('on'); }
function sunPlay(){
  sunStop(); const b=$('.sun-play'); if(b) b.classList.add('on');
  if(SUNS.i>=sunFrames().length-1) SUNS.i=0;
  SUNS.timer=setInterval(()=>{ if(!$('#sun-range')){ sunStop(); return; } SUNS.i++; if(SUNS.i>=sunFrames().length){ SUNS.i=sunFrames().length-1; sunStop(); } $('#sun-range').value=SUNS.i; drawSun(); sunRead(); },380);
}
function wireSun(){
  const rg=$('#sun-range');
  rg.addEventListener('input',()=>{ sunStop(); SUNS.i=+rg.value; drawSun(); sunRead(); });
  $('.sun-play').addEventListener('click',()=>SUNS.timer?sunStop():sunPlay());
  $$('.sunctl [data-season]').forEach(b=>b.addEventListener('click',()=>{ SUNS.k=b.dataset.season; $$('.sunctl [data-season]').forEach(x=>x.setAttribute('aria-pressed',String(x===b))); $('#sun-beats').innerHTML=beatsHTML(); drawSun(); sunRead(); }));
  drawSun(); sunRead();
  if(reduce) return;
  SUNS.i=0; drawSun(); sunRead(); setTimeout(()=>{ if($('#sun-range')) sunPlay(); },900);
}
const beatsHTML=()=>sunBeats(SUNS.k).map(([h,t])=>`<p class="beat"><b>${h}.</b> ${t}</p>`).join('');

/* due diligence: the items marked 1–5 on the AC_ layers of the drawing, with the same numbers in the caption */
const DD_TXT={
  lobby:d=>[`Lift lobbies and entrances`,`${d.count} lift lobbies. The main entrances open straight from them into the receptions.`],
  wash:d=>[`Washrooms`,`${d.count} washroom blocks in the cores, ${fmt(m2ft(d.m2))} sq ft. Base building.`],
  stair:d=>[`Fire exit staircases`,`${d.count} staircases along the north cores: the five exit doors seen on site.`],
  ahu:d=>[`AHU rooms`,`${d.count} AHU rooms, ${fmt(m2ft(d.m2))} sq ft, at the core ends.`],
  slab:d=>[`Slab to be strengthened`,`${d.count} zones, ${fmt(m2ft(d.m2))} sq ft, under the heavy rooms: server, UPS and battery rooms and the large meeting rooms.`],
};
function ddPins(){
  if(!RF.dd) return [];
  return RF.dd.items.map(d=>{ const [t,dd]=(DD_TXT[d.k]||(()=>[d.k,'']))(d); return {n:d.n,t,d:dd,marks:d.marks,polys:d.polys,k:d.k}; });
}
function ddSVG(){
  if(!RF.dd) return '';
  const pins=ddPins(); let s='';
  s+=RF.dd.oos.map(p=>`<path d="${PD(p)}" class="dd-oos"/>`).join('');
  pins.forEach((p,i)=>{ s+=p.polys.map(q=>`<path d="${PD(q)}" class="dd-p dd-${p.k}" data-pin="${i}"/>`).join(''); });
  s+=RF.dd.entries.map(t=>`<path d="M${t.map(q=>q.join(' ')).join('L')}Z" class="dd-ent"/>`).join('');
  pins.forEach((p,i)=>{ p.marks.forEach((m,j)=>{ s+=`<g class="pin" data-pin="${i}" transform="translate(${r1(m[0])} ${r1(m[1])})" style="--d:${(.15+i*.12+j*.04).toFixed(2)}s"><g><circle r="34" class="pin-p"/><circle r="34" class="pin-c"/><text y="13" class="pin-t">${p.n}</text></g></g>`; }); });
  return s;
}
function compSVG(){
  if(!RF.dd||!RF.dd.comp.length) return '';
  const c=RF.dd.comp[0], top=c.reduce((b,q)=>q[1]<b[1]?q:b);
  return c.length?`<path d="M${c.map(q=>q.join(' ')).join('L')}" class="dd-comp"/>`+T(top[0]+18,PB.y0-30,'FIRE COMPARTMENT LINE','ann firec'):'';
}
function wireSiteDD(){
  const set=i=>{ $$('.pin,.dd-p').forEach(p=>p.classList.toggle('on',String(i)===p.dataset.pin)); $$('.ob').forEach(o=>o.classList.toggle('on',String(i)===o.dataset.pin)); };
  $$('.ob').forEach(o=>{ o.addEventListener('pointerenter',()=>set(o.dataset.pin)); o.addEventListener('focus',()=>set(o.dataset.pin)); o.addEventListener('pointerleave',()=>set(null)); });
  set(null);
}
/* the space plan: every AC_ polygon in the drawing, coloured by what it is for */
const SPACE_CAT={work:['Work arena','--n4'],meet:['Meeting and training','--n2'],focus:['Focus and wellbeing','--n5'],collab:['Acker Garden and collab','--n6'],
  recharge:['Café and coffee corners','--n1'],arrival:['Receptions and lift lobbies','--brand'],move:['Corridors','--ink-3'],base:['Base building and support','--line-2']};
function spacePlanSVG(){ return (RF.spaces||[]).map(s=>`<path d="${s.d}" class="sp-c sp-${s.c}" style="--c:var(${(SPACE_CAT[s.c]||['', '--ink-3'])[1]})"/>`).join(''); }
function spaceLegend(){
  const S=(RF.spaces||[]).slice().sort((a,b)=>b.m2-a.m2), tot=RF.plateM2;
  return `<ul class="spl">${S.map(s=>`<li style="--c:var(${SPACE_CAT[s.c][1]})"><i></i><span>${SPACE_CAT[s.c][0]}</span><b>${fmt(m2ft(s.m2))} sq ft</b><em>${(100*s.m2/tot).toFixed(0)}%</em></li>`).join('')}</ul>`;
}
function sectionSVG(){
  const sl=NUM.slab, bm=NUM.clearUnderBeam, k=.034, H=sl*k, y=v=>H-v*k+18;
  return `<svg class="sect" viewBox="0 0 300 ${H+44}" role="img" aria-label="Section: ${sl} mm floor to slab, ${bm} mm floor to beam bottom">
    <rect x="40" y="${y(sl)-14}" width="230" height="14" class="s-slab"/><rect x="120" y="${y(sl)}" width="44" height="${(sl-bm)*k}" class="s-beam"/>
    <path class="s-ffl" d="M40 ${y(0)}H270"/><path class="s-dim" d="M24 ${y(0)}V${y(sl)}M18 ${y(0)}h12M18 ${y(sl)}h12M196 ${y(0)}V${y(bm)}M190 ${y(0)}h12M190 ${y(bm)}h12"/>
    <text class="s-t" x="8" y="${(y(0)+y(sl))/2}" transform="rotate(-90 8 ${(y(0)+y(sl))/2})" text-anchor="middle">${fmt(sl)} to slab</text>
    <text class="s-t" x="208" y="${(y(0)+y(bm))/2}" dy=".35em">${fmt(bm)}</text><text class="s-t" x="208" y="${(y(0)+y(bm))/2+15}" dy=".35em">to beam</text>
    <text class="s-t m" x="172" y="${y(sl)+((sl-bm)*k)/2}" dy=".35em">${NUM.beamZone} beam</text><text class="s-t m" x="44" y="${y(0)+18}">FFL · screed to come</text></svg>`;
}
/* climate: rain and temperature as two small charts, each on its own axis */
function climateSVG(){
  const M=SITE.climate.months, mx=Math.max(...M.map(m=>m.rain)), w=22, gap=5, X=i=>i*(w+gap), MN=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const ty=t=>64-(t-14)/(36-14)*60;
  const lab=M.map((m,i)=>`<text x="${X(i)+w/2}" y="80" class="c-m" text-anchor="middle">${MN[i][0]}</text>`).join('');
  const hot=M.reduce((b,m,i)=>m.tmax>M[b].tmax?i:b,0), wet=M.reduce((b,m,i)=>m.rain>M[b].rain?i:b,0);
  const rain=M.map((m,i)=>{ const h=Math.max(2,m.rain/mx*58); return `<rect x="${X(i)}" y="${64-h}" width="${w}" height="${h}" rx="3" class="c-rain"><title>${MN[i]}: ${m.rain} mm of rain</title></rect>`; }).join('');
  const temp=M.map((m,i)=>`<rect x="${X(i)+w/2-5}" y="${ty(m.tmax)}" width="10" height="${ty(m.tmin)-ty(m.tmax)}" rx="5" class="c-temp"><title>${MN[i]}: ${m.tmin} to ${m.tmax} °C</title></rect>`).join('');
  return `<div class="clim"><figure><figcaption><span>Rain, mm a month</span><b>${fmt(SITE.climate.rainYear)} mm a year</b></figcaption><svg viewBox="0 -6 360 90" role="img" aria-label="Monthly rain, wettest ${MN[wet]} at ${M[wet].rain} mm">${rain}<path class="c-base" d="M0 64.5H356"/>${lab}<text class="c-v" x="${X(wet)+w/2}" y="${64-58-4}" text-anchor="middle">${M[wet].rain}</text></svg></figure>
    <figure><figcaption><span>Daily low to high, °C</span><b>hottest ${MN[hot]}, ${M[hot].tmax.toFixed(0)}°</b></figcaption><svg viewBox="0 -6 360 90" role="img" aria-label="Monthly temperature range">${[20,30].map(t=>`<path class="c-grid" d="M0 ${ty(t)}H330"/><text class="c-g" x="356" y="${ty(t)}" dy=".35em" text-anchor="end">${t}°</text>`).join('')}${temp}${lab}</svg></figure></div>`;
}
/* façade sun table: hours of direct sun on the 21st, by month (clear sky) */
function faceTable(){
  const F=['N','E','S','W'].filter(f=>FACES[f]), mon=[[6,'Jun'],[3,'Mar'],[12,'Dec']];
  const kwh=f=>Math.max(...SUN.year.map(r=>r[f][1]));
  return `<table class="ft"><thead><tr><th>Façade</th>${mon.map(([m,n])=>`<th>${n}</th>`).join('')}<th>Peak day</th></tr></thead><tbody>${F.map(f=>`<tr><td>${({N:'North',E:'East end',S:'South',W:'SW end'})[f]} <small>${Math.round(FACES[f].brg)}°</small></td>${mon.map(([m])=>{ const h=SUN.year[m-1][f][0]; return `<td class="${h?'':'zero'}" style="--f:${(SUN.year[m-1][f][1]/5.2).toFixed(2)}"><span>${h?h.toFixed(0)+' h':'–'}</span></td>`; }).join('')}<td>${kwh(f).toFixed(1)} <small>kWh/m²</small></td></tr>`).join('')}</tbody></table>`;
}
/* what the day means for the layout: direct sun reaching each neighbourhood's floor, mornings and afternoons */
function sunTake(){
  const S=SUN.areaSun, nb=NB_IDS.filter(a=>S[a]);
  const tot=(a,i)=>['mar','jun','dec'].reduce((t,k)=>t+(S[a][k]?S[a][k][i]:0),0);
  const pm=nb.slice().sort((a,b)=>tot(b,1)-tot(a,1)).slice(0,2), am=nb.slice().sort((a,b)=>tot(b,0)-tot(a,0)).filter(a=>!pm.includes(a)).slice(0,1);
  const calm=nb.filter(a=>!pm.includes(a)&&!am.includes(a)).sort((a,b)=>(tot(a,0)+tot(a,1))-(tot(b,0)+tot(b,1))).slice(0,2);
  return `<ul class="take-l">
    <li>${listJoin(pm.map(nbChip))} take the most afternoon sun. Shade their glass with external fins or blinds, and set focus desks back from it.</li>
    <li>${nbChip(am[0])} gets the most morning sun, through the east end: bright, but blinds help before 10 am.</li>
    <li>${listJoin(calm.map(nbChip))} get the least direct sun, so the steadiest daylight for focus work.</li></ul>`;
}
function wireWind(){
  $$('[data-wind]').forEach(b=>b.addEventListener('click',()=>{ CLIM.wind=b.dataset.wind; $$('[data-wind]').forEach(x=>x.setAttribute('aria-pressed',String(x===b))); drawRose(); }));
}
