/* =====================================================================
   CONCEPTUAL AXO (test fit 03)
   Rendered stills (renders/axo-<view>-<style>.webp) and the live three.js model
   (tools/axo, global AckoAxo). Both are built from tools/axo/axo.json.
   ===================================================================== */
const AXO_IMG=/*AXO_IMG*/null, AXO_DATA=/*AXO_DATA*/null, AXO_LAB=/*AXO_LAB*/null;
const AX3_VIEWS=[['floor','Whole floor'],['west','West'],['middle','Middle'],['east','East']];
const AX3_STYLES=[['ref','Reference'],['nb','Neighbourhoods']];
const AX3={mode:'still',view:'floor',style:'ref',live:null};
const ax3=$('#sc-axo3');
$('#ax3-view').innerHTML=AX3_VIEWS.map(([v,n])=>`<button type="button" role="radio" data-v="${v}" aria-checked="false">${n}</button>`).join('');
$('#ax3-style').innerHTML=AX3_STYLES.map(([v,n])=>`<button type="button" role="radio" data-s="${v}" aria-checked="false">${n}</button>`).join('');
function ax3Sync(){
  ax3.dataset.mode=AX3.mode;
  $$('#ax3-view button').forEach(b=>b.setAttribute('aria-checked',String(b.dataset.v===AX3.view)));
  $$('#ax3-style button').forEach(b=>b.setAttribute('aria-checked',String(b.dataset.s===AX3.style)));
  const im=$('#ax3-img'), src=AXO_IMG&&AXO_IMG[AX3.mode==='exploded'?'exploded-layers':AX3.view+'-'+AX3.style];
  if(src&&im.getAttribute('src')!==src) im.src=src;
  im.alt=`Axonometric of ${AX3.view==='floor'?'the whole floor':'the '+AX3.view+' end'}${AX3.view==='middle'?' of the floor':''}, ${AX3.style==='nb'?'coloured by neighbourhood':'in the reference colours'}`.replace('the middle end','the middle');
  if(AX3.mode==='exploded') im.alt='Exploded axonometric: shell and core at the base, the neighbourhoods and the loop above, the fit-out on top';
  if(AX3.live) AX3.live.setStyle(AX3.style);
  ax3Labels();
}
/* exploded view: layer names on the left and a pill per neighbourhood, placed from the render's own anchor points */
function ax3Labels(){
  const ov=$('#ax3-ovl');
  if(AX3.mode!=='exploded'||!AXO_LAB){ ov.innerHTML=''; return; }
  const st=$('.ax3-stage').getBoundingClientRect(); if(!st.width) return;
  if(st.width<700){ ov.innerHTML=''; return; }      // too narrow for the callouts: the caption names the layers
  const s=Math.min(st.width/AXO_LAB.w,st.height/AXO_LAB.h), ox=(st.width-AXO_LAB.w*s)/2, oy=(st.height-AXO_LAB.h*s)/2;
  ov.innerHTML=AXO_LAB.labels.map(l=>{
    const x=ox+l.x*s, y=oy+l.y*s;
    if(!l.k.startsWith('nb:')) return `<div class="ol ll" data-x="${(x-12).toFixed(1)}" data-y="${y.toFixed(1)}" style="transform:translate(${(x-12).toFixed(1)}px,${y.toFixed(1)}px)"><div class="ll-in"><b>${l.t}</b><i></i></div></div>`;
    const id=l.k.slice(3), nb=NBS.find(b=>b.id===id);
    const pill=nb?`<div class="ol-n">${nb.name}</div><div class="ol-s">${nb.team}</div>`:`<div class="ol-n">${l.t}</div>`;
    return `<div class="ol zl${nb?'':' sm'}" data-x="${x.toFixed(1)}" data-y="${y.toFixed(1)}" style="--c:${nb?`var(${nb.c})`:'var(--brand)'}"><div class="ol-pill">${pill}</div><div class="ol-stem"></div></div>`;
  }).join('');
  // layer names: keep them on screen, first by shortening the leader line, then by sliding right
  $$('.ol.ll',ov).forEach(el=>{
    const box=$('.ll-in',el), line=$('i',box);
    let x=+el.dataset.x, over=box.offsetWidth-x+6;
    if(over>0){ const cut=Math.min(over,line.offsetWidth-12); line.style.width=(line.offsetWidth-cut)+'px'; over-=cut; if(over>0) x+=over; el.style.transform=`translate(${x}px,${el.dataset.y}px)`; }
  });
  // lift each pill on its stem, west to east, raising it until it clears the pills already placed
  const placed=[];
  $$('.ol.zl',ov).sort((a,b)=>a.dataset.x-b.dataset.x).forEach(el=>{
    const x=+el.dataset.x, y=+el.dataset.y, p=$('.ol-pill',el), w=p.offsetWidth+8, h=p.offsetHeight+6;
    let lift=el.classList.contains('sm')?20:30;
    const hits=()=>placed.some(r=>x-w/2<r.x+r.w/2&&x+w/2>r.x-r.w/2&&y-lift-h<r.y&&y-lift>r.y-r.h);
    while(hits()&&lift<300) lift+=12;
    placed.push({x,y:y-lift,w,h});
    el.style.transform=`translate(${x}px,${(y-lift).toFixed(1)}px)`;
    $('.ol-stem',el).style.height=lift+'px';
  });
}
new ResizeObserver(ax3Labels).observe($('.ax3-stage'));
function ax3Enter(mode){
  AX3.mode=mode; ax3.dataset.mode=mode;
  if(mode==='live'&&!AX3.live&&!ax3.dataset.fail){
    try{
      AX3.live=AckoAxo.createAxo($('#ax3-cv'),AXO_DATA,{interactive:true,style:AX3.style,view:AX3.view,shadowMap:4096});
      new ResizeObserver(()=>AX3.live&&AX3.live.resize()).observe($('#ax3-cv'));
    }catch(e){ ax3.dataset.fail='1'; AX3.live=null; }
  } else if(mode==='live'&&AX3.live) AX3.live.resize();
  ax3Sync();
}
$('#ax3-view').addEventListener('click',e=>{ const b=e.target.closest('button'); if(!b) return; AX3.view=b.dataset.v; if(AX3.live&&AX3.mode==='live') AX3.live.setView(AX3.view); ax3Sync(); });
$('#ax3-style').addEventListener('click',e=>{ const b=e.target.closest('button'); if(!b) return; AX3.style=b.dataset.s; ax3Sync(); });
$('#ax3-reset').addEventListener('click',()=>{ if(AX3.live) AX3.live.setView(AX3.view); });
/* hover a space in the live model to name it */
$('#ax3-cv').addEventListener('pointermove',e=>{
  if(!AX3.live||e.pointerType!=='mouse'||e.buttons){ if(tip.dataset.id==='ax3') hideTip(); return; }
  const r=AX3.live.pick(e.clientX,e.clientY);
  if(!r){ if(tip.dataset.id==='ax3') hideTip(); return; }
  tip.innerHTML=`<div class="tip-h" style="--c:var(--brand)"><i class="sw"></i>${r.name}</div><div class="tip-s">${[r.nb,r.m2?fmt(m2ft(r.m2))+' sq ft':''].filter(Boolean).join(' · ')||'Test fit 03'}</div>`;
  tip.dataset.id='ax3'; tip.hidden=false;
  const w=tip.offsetWidth, h=tip.offsetHeight;
  tip.style.left=Math.min(innerWidth-w-12,e.clientX+16)+'px'; tip.style.top=Math.max(12,Math.min(innerHeight-h-12,e.clientY+16))+'px';
});
$('#ax3-cv').addEventListener('pointerleave',()=>{ if(tip.dataset.id==='ax3') hideTip(); });
