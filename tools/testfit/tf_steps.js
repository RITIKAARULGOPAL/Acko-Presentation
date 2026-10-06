/* =====================================================================
   STEPS
   ===================================================================== */
const CH=['Introduction','The idea','The floor','Daylight','Fire and egress','Carving the floor','The layout','Town Square','Sharing out','Axonometric','Neighbourhoods','By the numbers'];
const pad=n=>String(n).padStart(2,'0');
const eyebrow=s=>`<p class="eyebrow">${pad(s.ch)} · ${CH[s.ch]}${s.sub?` · ${s.sub}`:''}</p>`;
const nbSw=i=>`style="--c:var(${NBS[i].c})"`;
const RHINT=t=>`<p class="rhint"><svg viewBox="0 0 16 16" aria-hidden="true"><rect x="1.5" y="4" width="13" height="9" rx="2"/><circle cx="8" cy="8.5" r="2.4"/><path d="M5.5 4l1-1.6h3L10.5 4"/></svg>${t}</p>`;
const listJoin=a=>a.length<2?a.join(''):a.slice(0,-1).join(', ')+' and '+a[a.length-1];
const tsK=k=>sumK(['TW','TC','R1','R2'],k);
const ROUTE_ROWS=()=>ROUTES.slice().sort((a,b)=>b.m-a.m);

const STEPS=[
  {id:'cover',ch:0,scene:'cover',full:true},
  {id:'idea',ch:1,scene:'concept',cap:s=>`${eyebrow(s)}<h2>An office that works like a city</h2>
    <p>Large floors feel anonymous. Cities stay human through neighbourhoods: places small enough to know your neighbours, with daily needs close by, linked by streets to a shared square. We planned Acko's floor the same way.</p>
    <ul class="analogy">${[
      ['city','The city','The floor',`One ${RF.len.toFixed(0)} m floor for ${TOT.desks} people`],
      ['street','The loop','Circulation','Corridors that are also the escape routes'],
      ['square','Town Square','Shared amenities','Café, receptions, lobby and atrium'],
      ['nb','Neighbourhood','A team zone','Daily needs within a short walk'],
      ['home','Home','Your desk','Near daylight, a few steps from your team'],
    ].map(([p,a,b2,c])=>`<li><button type="button" class="an" data-part="${p}"><span class="an-c">${a}</span><span class="an-ar">→</span><span class="an-o">${b2}<small>${c}</small></span></button></li>`).join('')}</ul>`,
    wire:wireIdea},
  {id:'loop',ch:1,sub:'The loop',scene:'loop',cap:s=>`${eyebrow(s)}<h2>And a loop that never ends</h2>
    <p>Acko's logo is drawn as a loop. We took it as a planning idea: the main corridors run as loops with no dead ends, everything shared sits along them, and the neighbourhoods open off them.</p>
    <ul class="analogy">${[
      ['loop','The loop','The main corridor','One continuous path, no dead ends'],
      ['exits','Endless','Two ways out','From any point, two ways to a stair'],
      ['square','Along it','Town Square','Café, receptions and lobby'],
      ['nb','Off it','Neighbourhoods','Six team zones, each opening onto it'],
    ].map(([p,a,b2,c])=>`<li><button type="button" class="an" data-part="${p}"><span class="an-c">${a}</span><span class="an-ar">→</span><span class="an-o">${b2}<small>${c}</small></span></button></li>`).join('')}</ul>`,
    wire:()=>wireParts('#loopsvg')},
  {id:'shell',ch:2,scene:'plan',flags:'shell grid',wide:true,cap:s=>`${eyebrow(s)}<h2>A long, narrow floor</h2>
    <p>The floor runs ${RF.len.toFixed(0)} m from end to end and only ${RF.depth.toFixed(0)} m deep, with a slanted west end. Cores with lifts, toilets and stairs line the north façade, and two double-height atria cut into the south.</p>
    <dl class="facts"><dt>Floor plate</dt><dd>${fmt(m2ft(RF.plateM2))} sq ft (${fmt(RF.plateM2)} m²)</dd><dt>Size</dt><dd>${RF.len.toFixed(1)} × ${RF.depth.toFixed(1)} m</dd><dt>Fire stairs</dt><dd>${STAIRS.length} (Stair 1 to Stair ${STAIRS.length})</dd><dt>Atria</dt><dd>2 on the south façade</dd></dl>`},
  {id:'light',ch:3,scene:'plan',flags:'shell light',wide:true,cap:s=>`${eyebrow(s)}<h2>Most of the floor is far from glass</h2>
    <p>Daylight reaches about 6 m in from a façade. On a ${RF.depth.toFixed(0)} m deep floor with cores along one side, that band is precious, so desks were pulled towards it and rooms pushed into the middle.</p>
    <ul class="legend"><li><i class="lg lg-sun"></i>6 m daylight band along the façade</li></ul>
    <p class="note">${TOT.daylight}% of workstations in the test fit sit inside the band.</p>`},
  {id:'exits',ch:4,sub:'Exits',scene:'plan',flags:'shell exits rings',wide:true,cap:s=>`${eyebrow(s)}<h2>${['No','One','Two','Three','Four','Five','Six','Seven'][STAIRS.length]||STAIRS.length} ways out</h2>
    <p>Five fire stairs sit in the cores along the north façade, from Stair 1 at the west to Stair 5 at the east. The rings mark 15, 30 and 45 m from each stair.</p>
    <ul class="legend"><li><i class="lg lg-exit"></i>Fire exit stair</li><li><i class="lg lg-ring"></i>Distance from the stair</li></ul>`},
  {id:'routes',ch:4,sub:'Egress routes',scene:'plan',flags:'shell exits routes',wide:true,cap:s=>`${eyebrow(s)}<h2>Tracing the escape routes</h2>
    <p>The ${ROUTES.length} egress routes from the test fit, measured along the drawn path from the far point to the stair. They run from ${TOT.shortest.toFixed(0)} m to ${TOT.longest.toFixed(0)} m.</p>
    <table class="rt"><tbody>${ROUTE_ROWS().map(r=>`<tr${r.m===TOT.longest?' class="max"':''}><td>${nbName(r.nb)}</td><td>Stair ${r.to}</td><td>${r.m.toFixed(1)} m</td></tr>`).join('')}</tbody></table>
    <p class="note">Travel distances still to be checked against NBC with the fire consultant.</p>`},
  {id:'parcels',ch:5,scene:'plan',flags:'shell zones labels',wide:true,cap:s=>`${eyebrow(s)}<h2>Six neighbourhoods and a Town Square</h2>
    <p>The floor is carved into six team neighbourhoods, from the slanted west end to the east. Between them sits what everyone shares: the café, two receptions above the atria, and the lobby around the central cut-out.</p>
    <ul class="nbl">${NBS.map((nb,i)=>`<li ${nbSw(i)}><i class="sw"></i><span style="display:flex;flex-direction:column;min-width:0"><b>${nb.name}</b><span>${fmt(m2ft(M2[nb.id]))} sq ft · ${KITS[nb.id].desk} desks</span></span></li>`).join('')}</ul>`},
  {id:'layout',ch:6,scene:'plan',flags:'shell furn rlabels spaces',wide:true,cap:s=>`${eyebrow(s)}<h2>The test-fit layout</h2>
    <p>${TOT.desks} workstations, ${TOT.sprint} quick sprint rooms, ${TOT.huddle} collaboration huddles, ${TOT.dept} departmental rooms, ${TOT.booth} phone booths, ${TOT.duo} two-person rooms and ${TOT.zen} zen rooms, all read from the drawing.</p>
    <dl class="facts"><dt>Density</dt><dd>${fmt(m2ft(RF.plateM2)/TOT.desks)} sq ft per workstation</dd><dt>In daylight</dt><dd>${TOT.daylight}% within 6 m of the façade</dd></dl>${RHINT('Click any room or desk cluster to see its light and dark renders.')}`},
  {id:'carved',ch:6,sub:'Neighbourhoods',scene:'plan',flags:'shell furn zones labels hover spaces',wide:true,cap:s=>`${eyebrow(s)}<h2>Carved into neighbourhoods</h2>
    <p>Each colour is one team's neighbourhood. Hover a neighbourhood to see who works there. Click a room for its renders, or the open floor to open the neighbourhood.</p>${areaBar()}`},
  {id:'town-square',ch:7,scene:'plan',flags:'shell furn zones labels rlabels ts-focus hover spaces',wide:true,cap:s=>`${eyebrow(s)}<h2>One square, spread along the floor</h2>
    <p>On a floor this long, the Town Square can't be one room. It is a chain of shared places along the middle: the café at the west, a reception over each atrium, and the lobby around the central cut-out.</p>
    <ul class="tsl">${[['cafe','Café and dining',`${fmt(m2ft(M2.TW))} sq ft`],['visitor','West reception',`${KITS.R1.visitor||0} visitor hubs`],['reception','East reception',`waiting lounge · ${KITS.R2.sprint||0} quick sprints`],['lobby','Lobby and atrium',`${fmt(m2ft(M2.TC))} sq ft`]].map(([k,n,v])=>`<li><button type="button" class="tsb" data-k="${k}"><span>${n}</span><span>${v}</span></button></li>`).join('')}</ul>${RHINT('Click a space, or a row above, for its renders.')}`,
    wire:wireTS},
  {id:'sharing',ch:8,scene:'alloc',cap:s=>`${eyebrow(s)}<h2>What each neighbourhood got</h2>
    <p>Every space in the test fit, counted from the drawing and split by neighbourhood. Each one has its own desks, meeting rooms, phone booths and a pantry, so daily needs stay inside it.</p>
    <p class="note">The brief column fills in once Acko's numbers are added. Then each row can show the brief against the plan.</p>`},
  {id:'axo',ch:9,scene:'plan',flags:'shell furn zones labels axo hover spaces',wide:true,cap:s=>`${eyebrow(s)}<h2>The same plan in three dimensions</h2>
    <p>The colours carry through, so each neighbourhood reads the same in plan and in 3D. Hover a neighbourhood for its details. Click a room for its renders.</p>
    <p class="note">This model is generated from the test-fit drawing. Rendered axonometric views will sit alongside it.</p>`},
  {id:'exploded',ch:9,sub:'Exploded',scene:'plan',flags:'shell furn zones labels axo explode spaces',wide:true,cap:s=>`${eyebrow(s)}<h2>How the layers stack</h2>
    <p>Shell and core at the base, then the neighbourhoods and the Town Square, then the fit-out. Each layer follows from the one below it.</p>`},
  {id:'neighbourhoods',ch:10,scene:'overview',cap:s=>`${eyebrow(s)}<h2>Six neighbourhoods, each complete</h2>
    <p>Every neighbourhood has its own workstations, quick sprint rooms, collaboration huddles, phone booths and a pantry point. They differ in size and mix, from ${Math.min(...NB_IDS.map(a=>KITS[a].desk))} to ${Math.max(...NB_IDS.map(a=>KITS[a].desk))} desks.</p>
    <p class="hint">Select a neighbourhood, or press → to walk through all six.</p>`},
  ...NBS.map((nb,i)=>({id:nb.id.toLowerCase(),ch:10,sub:`${i+1} of 6`,scene:'dive',cap:s=>capDive(s,i),wire:()=>wireDive(i),enter:()=>renderDive(i)})),
  {id:'numbers',ch:11,scene:'numbers',cap:s=>`${eyebrow(s)}<h2>One floor, six neighbourhoods, one square</h2>
    <p>Every number here is read from the test-fit drawing. The final figures will follow the approved layout.</p>`,enter:countUp},
];

function capDive(s,i){
  const nb=NBS[i], id=nb.id, k=KITS[id], kit=kitFor(id), cats=new Set(kit.map(it=>it.c));
  const kp=`<svg class="kp" viewBox="${PB.x0-30} ${PB.y0-30} ${PB.x1-PB.x0+60} ${PB.y1-PB.y0+60}" aria-label="Key plan">${PA(PD(RF.plate),'kp-plate')}${SHARED.map(t=>PA(PD(RF.areas[t.id]),'kp-ts')).join('')}${NBS.map((n,j)=>`<path d="${PD(RF.areas[n.id])}" class="kp-nb${j===i?' on':''}" style="--c:var(${n.c})" data-go-nb="${j}" tabindex="0" role="button" aria-label="Open ${n.name}"><title>${n.name}</title></path>`).join('')}</svg>`;
  const meetSeats=(k.sprintSeats||0)+(k.deptSeats||0)+(k.huddleSeats||0)+(k.hatcherySeats||0);
  const r=reach(id);
  return `<div style="--c:var(${nb.c});display:contents">${eyebrow(s)}${kp}
    <h2 class="dv-title" style="--c:var(${nb.c})">${nb.name}</h2>
    <p class="team">${nb.team} · ${nb.pos}</p>
    <p>${fmt(m2ft(M2[id]))} sq ft with ${k.desk} workstations${k.table4?` (including ${k.table4} four-seat collaboration tables)`:''}, ${listJoin(kit.filter(it=>it.k!=='desk').map(it=>{ const n=k[it.k]; return it.k==='hatchery'?'The Hatchery':`${n} ${n===1?it.one:it.n.toLowerCase()}`; }))}.</p>
    <dl class="stats" style="--c:var(${nb.c})"><div><dt>Desks</dt><dd>${k.desk}</dd></div><div><dt>Area</dt><dd>${fmt(m2ft(M2[id]))}<small>sq ft</small></dd></div><div><dt>Meeting seats</dt><dd>${meetSeats}</dd></div></dl>
    <div class="chips" style="--c:var(${nb.c})" aria-label="Self-sustaining checklist">${CATS.map(c=>`<button type="button" class="chip${cats.has(c)?'':' off'}" data-cat="${c}"><i>${cats.has(c)?'✓':'·'}</i>${c}</button>`).join('')}</div>
    <ul class="kit" style="--c:var(${nb.c})">${kit.map((it,n)=>`<li><button type="button" class="kr" data-k="${it.k}" data-cat="${it.c}"><span class="kn"><i class="kb">${n+1}</i>${it.n}${canRender(it.k)?'<svg class="cam" viewBox="0 0 16 16" aria-label="has renders"><rect x="1.5" y="4" width="13" height="9" rx="2"/><circle cx="8" cy="8.5" r="2.4"/><path d="M5.5 4l1-1.6h3L10.5 4"/></svg>':''}</span><span class="kc">${it.c}</span><span class="kv">${it.v(k)}</span></button></li>`).join('')}</ul>
    ${r?`<p class="sustain" style="--c:var(${nb.c})"><span>From any desk, a meeting room, a phone booth and the pantry are all within <b>${r.toFixed(0)} m</b> in a straight line. Daily needs stay inside the neighbourhood.</span></p>`:''}${RHINT('Click a space, a number or a row with a camera to see its renders.')}</div>`;
}
