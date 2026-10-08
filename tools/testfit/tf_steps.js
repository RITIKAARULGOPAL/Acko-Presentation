/* =====================================================================
   STEPS
   ===================================================================== */
const CH=['Introduction','The idea','The site','The floor','Sun and climate','Daylight','Fire and egress','Carving the floor','The layout','Shared spaces','Sharing out','Axonometric','Neighbourhoods','Green zones','By the numbers'];
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
      ['square','The square','Shared spaces','Café, receptions and lobby'],
      ['nb','Neighbourhood','A team zone','Daily needs within a short walk'],
      ['home','Home','Your desk','Near daylight, a few steps from your team'],
    ].map(([p,a,b2,c])=>`<li><button type="button" class="an" data-part="${p}"><span class="an-c">${a}</span><span class="an-ar">→</span><span class="an-o">${b2}<small>${c}</small></span></button></li>`).join('')}</ul>`,
    wire:wireIdea},
  {id:'loop',ch:1,sub:'The loop',scene:'loop',cap:s=>`${eyebrow(s)}<h2>And a loop that never ends</h2>
    <p>Acko's logo is drawn as a loop. We took it as a planning idea: the main corridors run as loops with no dead ends, everything shared sits along them, and the neighbourhoods open off them.</p>
    <ul class="analogy">${[
      ['loop','The loop','The main corridor','One continuous path, no dead ends'],
      ['exits','Endless','Two ways out','From any point, two ways to a stair'],
      ['square','Along it','Shared spaces','Café, receptions and lobby'],
      ['nb','Off it','Neighbourhoods','Six team zones, each opening onto it'],
    ].map(([p,a,b2,c])=>`<li><button type="button" class="an" data-part="${p}"><span class="an-c">${a}</span><span class="an-ar">→</span><span class="an-o">${b2}<small>${c}</small></span></button></li>`).join('')}</ul>`,
    wire:()=>wireParts('#loopsvg')},
  {id:'site',ch:2,scene:'site',enter:()=>setSiteView('city'),cap:s=>`${eyebrow(s)}<h2>Regalium, Koramangala</h2>
    <p>Acko's floor is the ${FX.floor} of Regalium, ${FX.developer}'s office and retail building on Hosur Road, between its junctions with Dr M H Marigowda Road and Sarjapur Road. Nexus mall, Jyoti Nivas College and St John's Hospital are all within a ten-minute walk.</p>
    <dl class="facts"><dt>Address</dt><dd>${FX.address.replace('Regalium Building, ','')}</dd><dt>Plus code</dt><dd>${FX.plus.split(',')[0]} · ${SITE.origin.lat.toFixed(4)}° N, ${SITE.origin.lng.toFixed(4)}° E</dd>
    <dt>Bus</dt><dd>${SITE.bus.slice(0,2).map(b=>`${b.n.replace(/St\.? Johns? Hospital/,"St John's Hospital").replace(' KSRTC Bus Stand',' bus stand')}, ${mtxt(b.walk)}`).join(' · ')}</dd>
    <dt>Metro</dt><dd>${SITE.marks.filter(m=>m.k==='metro').map(m=>`${m.n.replace(' metro','')}, ${mtxt(m.walk)}`).join(' · ')} (Yellow Line)</dd></dl>
    <ul class="legend"><li><i class="lg lg-site"></i>Regalium</li><li><i class="lg lg-ring"></i>5 and 10 minutes' walk from the gate</li><li><i class="lg lg-rail"></i>Proposed Red Line metro</li></ul>
    <p class="note">Walking distances follow the street network from the site gate. Map: ${SITE.attribution}.</p>`},
  {id:'context',ch:2,sub:'Orientation',scene:'site',enter:()=>setSiteView('near'),cap:s=>`${eyebrow(s)}<h2>Which way is north</h2>
    <p>The test-fit drawing has no north point, so we fitted the floor plate into the building's footprint from the map. Only one way round puts the slanted end beside Hosur Road, and that one puts the cores and stairs on the north side.</p>
    <p>The whole floor is turned ${UP.toFixed(1)}° east of true north, the same angle as the street grid around it. The sun and wind studies that follow use this angle.</p>
    <dl class="facts"><dt>North façade</dt><dd>faces ${Math.round(FACES.N.brg)}° · cores, lifts and stairs</dd><dt>South façade</dt><dd>faces ${Math.round(FACES.S.brg)}° · the two terraces</dd><dt>SW end</dt><dd>faces ${Math.round(FACES.W.brg)}° · onto Hosur Road</dd><dt>East end</dt><dd>faces ${Math.round(FACES.E.brg)}°</dd></dl>
    <p class="note">Worth checking with a compass on site. The footprint comes from OpenStreetMap, so it may not match the finished building exactly.</p>`},
  {id:'shell',ch:3,scene:'plan',flags:'shell grid north',wide:true,cap:s=>`${eyebrow(s)}<h2>A long, narrow floor</h2>
    <p>The floor runs ${RF.len.toFixed(0)} m from end to end and only ${RF.depth.toFixed(0)} m deep, with a slanted south-west end facing Hosur Road. Cores with lifts, toilets and stairs line the north façade, and two terraces cut into the south.</p>
    <dl class="facts"><dt>Super built-up</dt><dd>${fmt(FX.sbaSft)} sq ft</dd><dt>Carpet</dt><dd>${fmt(FX.carpetSft)} sq ft</dd><dt>Floor plate</dt><dd>${fmt(m2ft(RF.plateM2))} sq ft inside the glass (${fmt(RF.plateM2)} m²)</dd><dt>Size</dt><dd>${RF.len.toFixed(1)} × ${RF.depth.toFixed(1)} m</dd><dt>Fire stairs</dt><dd>${STAIRS.length} (Stair 1 to Stair ${STAIRS.length})</dd><dt>Terraces</dt><dd>2 on the south façade, about ${fmt(m2ft(TERRACES[0].m2))} sq ft each</dd></dl>`},
  {id:'diligence',ch:3,sub:'Due diligence',scene:'plan',flags:'shell dd comp',wide:true,tall:true,cap:s=>`${eyebrow(s)}<h2>What the building already decided</h2>
    <p>The items marked on the drawing, numbered as on the plan. The hatched cores are out of scope, and the dashed line splits the floor into two fire compartments.</p>
    <ul class="obs dd">${ddPins().map((p,i)=>`<li><button type="button" class="ob" data-pin="${i}"><span class="ob-n">${p.n}</span><span class="ob-t">${p.t}<small>${p.d}</small></span></button></li>`).join('')}</ul>
    <dl class="facts"><dt>Super built-up</dt><dd>${fmt(FX.sbaSft)} sq ft</dd><dt>Carpet</dt><dd>${fmt(FX.carpetSft)} sq ft · ${NUM.efficiency}% of super built-up</dd><dt>Headcount</dt><dd>about ${FX.headcount} · ${NUM.carpetPerHead} sq ft of carpet each</dd><dt>Test fit</dt><dd>${NUM.desks} workstations · ${NUM.spare>=0?`${NUM.spare} more than`:`${-NUM.spare} fewer than`} the headcount</dd></dl>
    ${sectionSVG()}`,
    wire:wireSiteDD},
  {id:'sun',ch:4,sub:'Sun path',scene:'climate',enter:()=>setClimate('sun'),cap:s=>`${eyebrow(s)}<h2>The sun at 13° north</h2>
    <p>Bengaluru is close enough to the equator that the midday sun is almost overhead. From ${SUN.northFrom} to ${SUN.northTo} it stands north of the building at noon. The rest of the year it swings south, down to ${SUN.arcs.find(a=>a.k==='dec').noonAlt.toFixed(0)}° on 21 December.</p>
    <p>The long façades face almost due north and south, the easiest directions to shade. The low morning and evening sun falls on the short ends and the terrace glass instead.</p>
    ${faceTable()}
    <p class="note">Hours of direct sun on the 21st of the month, and the energy on the sunniest day. Clear sky, unshaded glass. Sources: NOAA solar position and the ASHRAE clear-sky model.</p>`},
  {id:'sunday',ch:4,sub:'Morning to evening',scene:'plan',flags:'shell furn north sun',wide:true,tall:true,cap:s=>`${eyebrow(s)}<h2>Morning to evening on the layout</h2>
    ${sunCtl()}
    <div id="sun-beats">${beatsHTML()}</div>
    <div class="takes"><h3 class="take-h">What it means for the layout</h3>${sunTake()}</div>
    <ul class="legend"><li><i class="lg lg-sunp"></i>Direct sun on the floor: the stronger the colour, the more heat and glare</li></ul>
    <p class="note">${SUN.model}.</p>`,
    wire:wireSun},
  {id:'light',ch:5,scene:'plan',flags:'shell light north',wide:true,cap:s=>`${eyebrow(s)}<h2>Most of the floor is far from glass</h2>

    <p>Daylight reaches about 6 m in from a façade. On a ${RF.depth.toFixed(0)} m deep floor with cores along one side, that band is precious, so desks were pulled towards it and rooms pushed into the middle.</p>
    <ul class="legend"><li><i class="lg lg-sun"></i>6 m daylight band along the façade</li></ul>
    <p class="note">${TOT.daylight}% of workstations in the test fit sit inside the band.</p>`},
  {id:'exits',ch:6,sub:'Exits',scene:'plan',flags:'shell exits rings comp',wide:true,cap:s=>`${eyebrow(s)}<h2>${['No','One','Two','Three','Four','Five','Six','Seven'][STAIRS.length]||STAIRS.length} ways out</h2>
    <p>Five fire stairs sit in the cores along the north façade, from Stair 1 at the west to Stair 5 at the east. The rings mark 15, 30 and 45 m from each stair.</p>
    <ul class="legend"><li><i class="lg lg-exit"></i>Fire exit stair</li><li><i class="lg lg-ring"></i>Distance from the stair</li></ul>`},
  {id:'routes',ch:6,sub:'Egress routes',scene:'plan',flags:'shell exits routes',wide:true,cap:s=>`${eyebrow(s)}<h2>Tracing the escape routes</h2>
    <p>The ${ROUTES.length} egress routes from the test fit, measured along the drawn path from the far point to the stair. They run from ${TOT.shortest.toFixed(0)} m to ${TOT.longest.toFixed(0)} m.</p>
    <table class="rt"><tbody>${ROUTE_ROWS().map(r=>`<tr${r.m===TOT.longest?' class="max"':''}><td>${nbName(r.nb)}</td><td>Stair ${r.to}</td><td>${r.m.toFixed(1)} m</td></tr>`).join('')}</tbody></table>
    <p class="note">Travel distances still to be checked against NBC with the fire consultant.</p>`},
  {id:'parcels',ch:7,scene:'plan',flags:'shell zones labels',wide:true,cap:s=>`${eyebrow(s)}<h2>Six neighbourhoods and the shared spaces</h2>
    <p>The floor is carved into six team neighbourhoods, from the slanted west end to the east. Between them sit the spaces everyone shares: the café, a reception beside each terrace, and the lobby by the lifts.</p>
    <ul class="nbl">${NBS.map((nb,i)=>`<li ${nbSw(i)}><i class="sw"></i><span style="display:flex;flex-direction:column;min-width:0"><b>${nb.name}</b><span>${fmt(m2ft(M2[nb.id]))} sq ft · ${KITS[nb.id].desk} desks</span></span></li>`).join('')}</ul>`},
  {id:'layout',ch:8,scene:'plan',flags:'shell furn rlabels spaces',wide:true,cap:s=>`${eyebrow(s)}<h2>The test-fit layout</h2>
    <p>${TOT.desks} workstations, ${TOT.sprint} quick sprint rooms, ${TOT.huddle} collaboration huddles, ${TOT.dept} departmental rooms, ${TOT.booth} phone booths, ${TOT.duo} two-person rooms and ${TOT.zen} zen rooms, all read from the drawing.</p>
    <dl class="facts"><dt>Density</dt><dd>${fmt(m2ft(RF.plateM2)/TOT.desks)} sq ft per workstation</dd><dt>In daylight</dt><dd>${TOT.daylight}% within 6 m of the façade</dd></dl>${RHINT('Click any room or desk cluster to see its light and dark renders.')}`},
  {id:'spaceplan',ch:8,sub:'Space plan',scene:'plan',flags:'shell splan',wide:true,cap:s=>`${eyebrow(s)}<h2>Every space, by what it is for</h2>
    <p>Each space drawn on the layout, coloured by type. Open work arenas take the largest share. Meeting rooms, focus rooms and coffee corners are spread along the floor, and the cores and washrooms belong to the base building.</p>
    ${spaceLegend()}
    <p class="note">Areas measured from the space outlines in the drawing, each square foot counted once. The rest of the ${fmt(m2ft(RF.plateM2))} sq ft plate is walls, shafts and spaces left unmarked.</p>`},
  {id:'carved',ch:8,sub:'Neighbourhoods',scene:'plan',flags:'shell furn zones labels hover spaces',wide:true,cap:s=>`${eyebrow(s)}<h2>Carved into neighbourhoods</h2>
    <p>Each colour is one team's neighbourhood. Hover a neighbourhood to see who works there. Click a room for its renders, or the open floor to open the neighbourhood.</p>${areaBar()}`},
  {id:'shared',ch:9,scene:'plan',flags:'shell furn zones labels rlabels ts-focus hover spaces',wide:true,cap:s=>`${eyebrow(s)}<h2>Shared spaces along the floor</h2>
    <p>On a floor this long, the shared spaces can't be one room. They form a chain along the middle: the café at the west, a reception beside each terrace, and the lobby by the lifts.</p>
    <ul class="tsl">${[['cafe','Café and dining',`${fmt(m2ft(M2.TW))} sq ft`],['visitor','West reception',`${KITS.R1.visitor||0} visitor hubs`],['reception','East reception',`waiting lounge · ${KITS.R2.sprint||0} quick sprints`],['lobby','Lobby',`${fmt(m2ft(M2.TC))} sq ft`]].map(([k,n,v])=>`<li><button type="button" class="tsb" data-k="${k}"><span>${n}</span><span>${v}</span></button></li>`).join('')}</ul>${RHINT('Click a space, or a row above, for its renders.')}`,
    wire:wireTS},
  {id:'sharing',ch:10,scene:'alloc',cap:s=>`${eyebrow(s)}<h2>What each neighbourhood got</h2>
    <p>Every space in the test fit, counted from the drawing and split by neighbourhood. Each one has its own desks, meeting rooms, phone booths and a coffee corner, so daily needs stay inside it.</p>
    <p class="note">The brief column fills in once Acko's numbers are added. Then each row can show the brief against the plan.</p>`},
  {id:'axo',ch:11,scene:'plan',flags:'shell furn zones labels axo hover spaces',wide:true,cap:s=>`${eyebrow(s)}<h2>The same plan in three dimensions</h2>
    <p>The colours carry through, so each neighbourhood reads the same in plan and in 3D. Hover a neighbourhood for its details. Click a room for its renders.</p>
    <p class="note">This model is generated from the test-fit drawing. Rendered axonometric views will sit alongside it.</p>`},
  {id:'exploded',ch:11,sub:'Exploded',scene:'plan',flags:'shell furn zones labels axo explode spaces',wide:true,cap:s=>`${eyebrow(s)}<h2>How the layers stack</h2>
    <p>Shell and core at the base, then the neighbourhoods and shared spaces, then the fit-out. Each layer follows from the one below it.</p>`},
  {id:'neighbourhoods',ch:12,scene:'overview',cap:s=>`${eyebrow(s)}<h2>Six neighbourhoods, each complete</h2>
    <p>Every neighbourhood has its own workstations, quick sprint rooms, collaboration huddles, phone booths and coffee corners. They differ in size and mix, from ${Math.min(...NB_IDS.map(a=>KITS[a].desk))} to ${Math.max(...NB_IDS.map(a=>KITS[a].desk))} desks.</p>
    <p class="hint">Select a neighbourhood, or press → to walk through all six.</p>`},
  ...NBS.map((nb,i)=>({id:nb.id.toLowerCase(),ch:12,sub:`${i+1} of 6`,scene:'dive',cap:s=>capDive(s,i),wire:()=>wireDive(i),enter:()=>renderDive(i)})),
  {id:'green',ch:13,scene:'green',wide:true,enter:gzEnter('prop'),cap:s=>`${eyebrow(s)}<h2>Planting is not decoration</h2>
    <p class="gz-quote">It is spatial infrastructure, responding to how people use the workplace.</p>
    <p>So the plants are not spread evenly, one every so many square metres. This analysis reads the test fit: who uses each space, how often, for how long, in what light and in whose view. Planting goes where it does the most, and stays out of the way of circulation.</p>
    <p class="take-h">The workflow</p>${gzFlow()}
    <p class="note">${GZ.zones.length} green zones and ${fmt(GZ.placed+GZ.desk)} plants on ${fmt(GZD.usableM2)} m² of usable floor. Values not in the drawing are labelled as estimates. The carbon figure is a relative design index, not a measurement of emissions.</p>`},
  {id:'green-spaces',ch:13,sub:'Spaces',scene:'green',wide:true,enter:gzEnter('class'),cap:s=>{ const c={}; GZ.rows.forEach(r=>c[r.s.c]=(c[r.s.c]||0)+1); const seats=GZ.rows.filter(r=>r.src==='drawing'&&r.d.occ==='seats').reduce((a,r)=>a+r.occ,0);
    return `${eyebrow(s)}<h2>First, every space classified</h2>
    <p>The drawing's own space layers give ${GZ.rows.length} spaces, each with an outline and an area. Each one gets a type, a category and a record: occupancy, dwell, visits, footfall, daylight, circulation, privacy and existing planting.</p>
    <ul class="gz-cl">${GZ_CAT_ORDER.map(k=>`<li><i class="sw" style="background:var(--gzc-${k})"></i><b>${GZ_CATS[k]}</b><span>${c[k]||0} space${c[k]===1?'':'s'} · ${fmt(GZ.rows.filter(r=>r.s.c===k).reduce((a,r)=>a+r.s.m2,0))} m²</span></li>`).join('')}</ul>
    <p class="note">Occupancy comes from the drawing where it can: ${fmt(GZD.headcount)} workstations and ${fmt(seats)} seats in rooms, the café and the collaboration spaces. Coffee corners, receptions, lobbies and the corridor have no seats, so their users are estimated from the headcount and labelled as estimates. Click any space to see or override its record.</p>`; }},
  {id:'green-footfall',ch:13,sub:'Footfall',scene:'green',wide:true,enter:gzEnter('foot'),cap:s=>`${eyebrow(s)}<h2>Where people move</h2>
    <p class="gz-f">Daily footfall = occupancy × visits per person per day × utilisation</p>
    <p>Each space type has its own pattern. A reception sees everyone once or twice a day, a coffee corner a few visits per person, a workstation one or two arrivals. The plan is shaded by footfall per m², so a small, busy space reads against a large, quiet one.</p>
    <ol class="gz-top">${gzTop('nF',5).map(r=>`<li><b>${gzEsc(r.s.n)}</b><span>${fmt(r.foot)} a day · ${(r.foot/r.s.m2).toFixed(1)}/m²</span></li>`).join('')}</ol>
    <p class="note">Visits, utilisation and dwell are planning estimates by space type, editable in the Assumptions step.</p>`},
  {id:'green-dwell',ch:13,sub:'Dwell',scene:'green',wide:true,enter:gzEnter('dwell'),cap:s=>{ const f=k=>GZ.rows.filter(r=>r.s.k===k), sum=(a,k)=>a.reduce((x,r)=>x+r[k],0), rec=f('reception'), cafe=f('cafe'), work=f('open');
    const row=(n,a)=>a.length?`<li><b>${n}</b><span>${fmt(sum(a,'foot'))} visits · ${(()=>{ const m=sum(a,'hrs')*60/(sum(a,'foot')||1); return m<2?m.toFixed(1):Math.round(m); })()} min each · ${fmt(sum(a,'hrs'))} person-hours</span></li>`:'';
    return `${eyebrow(s)}<h2>Where people stay</h2>
    <p class="gz-f">Daily occupancy hours = daily footfall × average dwell per visit</p>
    <p>Footfall alone would plant the corridors. Dwell separates three kinds of space, and each needs a different planting strategy:</p>
    <ul class="gz-q">${row('High footfall, short dwell · reception',rec)}${row('High footfall and real dwell · café',cafe)}${row('Little movement, very long dwell · work arenas',work)}</ul>
    <p class="note">Shaded by person-hours per m² a day. Arrival spaces get statement planting seen in passing. Social spaces get islands to sit beside. Work arenas get planting at eye level from the desk.</p>`; }},
  {id:'green-carbon',ch:13,sub:'Carbon index',scene:'green',wide:true,enter:gzEnter('carbon'),cap:s=>`${eyebrow(s)}<h2>A relative carbon impact index</h2>
    <p class="gz-f">Relative Carbon Impact Index = footfall × dwell × activity factor × services intensity, per m², scaled 0–100 across this floor</p>
    <p>The index is highest where people gather and stay, and where equipment, cooking and air-conditioning work hardest. Those are the spaces where planting is most noticed and where the indoor environment is under the most load. Here, ${listJoin(gzTop('cii',3).map(r=>gzEsc(r.s.n)))} lead.</p>
    <p class="gz-warnp"><b>This is a design-planning comparison, not a carbon calculation.</b> It does not measure the occupants' emissions and is not a carbon-offset figure. Plants indoors do not offset an office's carbon footprint.</p>`},
  {id:'green-priority',ch:13,sub:'Priority',scene:'green',wide:true,enter:gzEnter('prio'),cap:s=>{ const g=GZ.g; return `${eyebrow(s)}<h2>Biophilic priority</h2>
    <p>Six factors, each normalised across the floor, combine into one score per space, scaled 0–100:</p>
    <ul class="gz-w">${[['Footfall',g.wF],['Dwell time',g.wD],['Carbon index',g.wC],['Daylight potential',g.wL],['Social importance',g.wS],['Visibility',g.wV]].map(([n,w])=>`<li><span>${n}</span><i style="--w:${w}"></i><b>${w}%</b></li>`).join('')}</ul>
    <ol class="gz-top">${gzTop('prio',4).map(r=>`<li><b>${gzEsc(r.s.n)}</b><span>${Math.round(r.prio)} · ${r.cls[1]}</span></li>`).join('')}</ol>
    <p class="note">Very low 0–25 · Low 26–40 · Moderate 41–60 · High 61–80 · Very high 81–100. The class sets how many plants a space gets: ${g.mL}× (low) to ${g.mVH}× (very high) of one plant per ${g.density} m².</p>`; }},
  {id:'green-zones',ch:13,sub:'Green zones',scene:'green',wide:true,enter:gzEnter('prop'),cap:s=>{ const n={}; GZ.zones.forEach(z=>n[z.t]=(n[z.t]||0)+1);
    return `${eyebrow(s)}<h2>Where the green zones go</h2>
    <p>Each spot is cut from the floor that circulation leaves free: ${GZD.clear.toFixed(1)} m clear corridors (from the drawing's note), escape routes, door swings, junction sight lines, furniture use zones, lifts, stairs and services are all kept clear. The best spots are chosen by the priority of their space, how visible they are, daylight and footfall, and are kept apart so they don't crowd.</p>
    <ul class="gz-ty">${GZ_TYPE_ORDER.map(t=>`<li><svg viewBox="-12 -12 24 24" aria-hidden="true">${gzGlyph(t)}</svg><b>${GZ_TYPES[t].n}</b><span>${n[t]||0} · ${GZ_TYPES[t].d.toLowerCase()}</span></li>`).join('')}</ul>
    ${RHINT('Click a zone for its numbers. Drag to move it, use + Add zone to place one, or delete, retype and resize it from its card. Edits are checked against the clearances.')}`; }},
  {id:'green-dashboard',ch:13,sub:'Dashboard',scene:'green',enter:gzEnter('dash'),cap:s=>`${eyebrow(s)}<h2>The green strategy in numbers</h2>
    <p>The <b>biophilic workplace score</b> rewards impact, not plant count. It weighs how well the high-priority spaces are served (40%), how many desks see greenery within ${GZ.g.reach} m (30%), how visible the zones are (15%) and how many plants have daylight (15%). Spots that block circulation lose points.</p>
    <dl class="stats gz-st"><div><dt>Score</dt><dd>${Math.round(GZ.score)}<small>/100</small></dd></div><div><dt>Plants</dt><dd>${fmt(GZ.placed+GZ.desk)}</dd></div><div><dt>Coverage</dt><dd>${GZ.cov.toFixed(1)}<small>%</small></dd></div></dl>
    <p class="note">So ten plants in the right place score higher than thirty spread evenly. The tables update as you edit zones or assumptions.</p>`},
  {id:'green-database',ch:13,sub:'Space database',scene:'green',enter:gzEnter('db'),cap:s=>`${eyebrow(s)}<h2>The spatial database</h2>
    <p>Every space with its classification, occupancy, dwell, footfall, daylight, circulation intensity, privacy, existing planting and recommended planting intensity, from the highest priority down.</p>
    <p class="note">Occupancy marked "dwg" is counted in the drawing. Everything marked "est." is an estimate, never a measurement.</p>`},
  {id:'green-assumptions',ch:13,sub:'Assumptions',scene:'green',enter:gzEnter('assume'),cap:s=>`${eyebrow(s)}<h2>Every assumption, open to the designer</h2>
    <p>Change how often a space is visited, how long people stay, the activity factors, the priority weights, the planting density or the plant spacing, and the whole analysis recomputes: scores, zones, quantities and recommendations.</p>
    <p>Edits stay in this browser. Export them as JSON to share, and import them on another machine. Zone edits (moved, added, deleted, retyped) are kept the same way.</p>
    <p class="note">Overridden values are highlighted. Reset brings back the defaults.</p>`},
  {id:'numbers',ch:14,scene:'numbers',cap:s=>`${eyebrow(s)}<h2>One floor, six neighbourhoods</h2>
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
    ${r?`<p class="sustain" style="--c:var(${nb.c})"><span>From any desk, a meeting room, a phone booth and a coffee corner are all within <b>${r.toFixed(0)} m</b> in a straight line. Daily needs stay inside the neighbourhood.</span></p>`:''}${RHINT('Click a space, a number or a row with a camera to see its renders.')}</div>`;
}
