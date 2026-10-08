/* =====================================================================
   CONCEPTUAL AXO (test fit 03)
   Rendered stills (renders/axo-<view>-<style>.webp) and the live three.js model
   (tools/axo, global AckoAxo). Both are built from tools/axo/axo.json.
   ===================================================================== */
const AXO_IMG=/*AXO_IMG*/null, AXO_DATA=/*AXO_DATA*/null;
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
  const im=$('#ax3-img'), src=AXO_IMG&&AXO_IMG[AX3.view+'-'+AX3.style];
  if(src&&im.getAttribute('src')!==src) im.src=src;
  im.alt=`Axonometric of ${AX3.view==='floor'?'the whole floor':'the '+AX3.view+' end'}${AX3.view==='middle'?' of the floor':''}, ${AX3.style==='nb'?'coloured by neighbourhood':'in the reference colours'}`.replace('the middle end','the middle');
  if(AX3.live) AX3.live.setStyle(AX3.style);
}
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
