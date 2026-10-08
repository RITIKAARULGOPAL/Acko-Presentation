function ctxInfo(ctx){ if(ctx==='TS') return {name:'Shared spaces',sub:'Used by everyone',c:'var(--brand)'}; const nb=NBS.find(n=>n.id===ctx); return {name:nb.name,sub:nb.team,c:`var(${nb.c})`}; }
const areaName=a=>isNB(a)?nbName(a):((SHARED.find(t=>t.id===a)||{}).name||'');
function tipHTML(id){
  if(id.startsWith('sp')){ const sp=SP[+id.slice(2)], info=ctxInfo(sp.nb); return `<div class="tip-h" style="--c:${info.c}"><i class="sw"></i>${SPACE_NAMES[sp.k]}</div><div class="tip-s">${areaName(sp.area)}${sp.seats?` · ${sp.seats} ${sp.seats===1?'seat':'seats'}`:''}</div>${sp.t&&sp.k!=='booth'?`<div class="tip-s">${sp.t}</div>`:''}<div class="tip-f">Click to view light and dark renders →</div>`; }
  const sh=SHARED.find(t=>t.id===id);
  if(sh||id==='TS'){ const t=sh||SHARED[0], k=KITS[t.id];
    const rows=[['Area',`${fmt(m2ft(M2[t.id]))} sq ft`]].concat([['visitor','Visitor hubs'],['board','Boardroom'],['sprint','Quick sprints'],['pantry','Coffee corners'],['studio','Studio']].filter(([kk])=>k[kk]).map(([kk,n])=>[n,k[kk]]));
    return `<div class="tip-h" style="--c:var(--brand)"><i class="sw"></i>${t.name}</div><div class="tip-s">Shared spaces · ${t.sub}</div><dl class="tip-g">${rows.map(([a,b])=>`<dt>${a}</dt><dd>${b}</dd>`).join('')}</dl>`; }
  const i=NBS.findIndex(n=>n.id===id); if(i<0) return '';
  const nb=NBS[i], k=KITS[id];
  return `<div class="tip-h" style="--c:var(${nb.c})"><i class="sw"></i>${nb.name}</div><div class="tip-s">${nb.team} · ${nb.pos}</div><dl class="tip-g"><dt>Workstations</dt><dd>${k.desk}</dd><dt>Area</dt><dd>${fmt(m2ft(M2[id]))} sq ft</dd><dt>Meeting rooms</dt><dd>${(k.sprint||0)+(k.dept||0)}</dd><dt>Huddles</dt><dd>${k.huddle||0}</dd><dt>Booths and 2-pax</dt><dd>${(k.booth||0)+(k.duo||0)}</dd></dl><div class="tip-f">Click to open →</div>`;
}
