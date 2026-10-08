import re, json, sys
SRC,OUT=sys.argv[1],sys.argv[2]   # template (index.html) and output
s=open(SRC).read()
def between(a,b,src=None,inc_a=True):
    src=src or s; i=src.index(a); j=src.index(b,i)
    return src[i if inc_a else i+len(a):j]
def rep(src,a,b,cnt=1):
    n=src.count(a); assert n==cnt,(n,a[:100]); return src.replace(a,b)
head_css=s[:s.index('</style>')]
body=s[s.index('</style>'):s.index('<script>')]
script=s[s.index('<script>'):]
prelude=script[:script.index('/* =====================================================================\n   PROJECT CONTENT')]
city=between('function buildCity(){','/* the loop: a ring stretches')
loopf=between('function buildLoop(){','/* the brief as Acko gave it')
renders=between('/* =====================================================================\n   RENDERS','/* =====================================================================\n   STEPS',script)
engine=script[script.index('/* =====================================================================\n   ENGINE'):]
# ---------- CSS ----------
css_add=open('tf_css.css').read()
head_css=rep(head_css,'<title>Acko Neighbourhood Office</title>','<title>Acko Test Fit 02</title>')
head_css+=css_add
# ---------- body ----------
body=rep(body,'<p class="eyebrow">Acko · Workplace design narrative</p>','<p class="eyebrow">Acko · Test fit 02 · Workplace design narrative</p>')
body=rep(body,'<p class="lede">How a bare floor plate became six self-sustaining neighbourhoods around one shared Town Square.</p>','<p class="lede">How a long, narrow floor became six self-sustaining neighbourhoods linked by shared spaces.</p>')
body=rep(body,'<span class="draft" title="Floor plate, names and numbers are sample data">Draft · sample data</span>','<span class="draft" title="Plan from the test-fit drawing; names and teams are placeholders">Draft · test fit 02</span>')
body=re.sub(r'  <section class="scene" id="sc-brief".*?</section>\n','',body)
body=rep(body,'looping around the Town Square','looping around the shared spaces')
body=rep(body,'  <section class="scene" id="sc-alloc"','''  <section class="scene" id="sc-site" aria-label="The site: Regalium, Koramangala"><svg id="sitesvg" class="dsvg" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Map of the site and the streets around it"></svg><p class="m-attr" id="m-attr"></p></section>
  <section class="scene" id="sc-climate" aria-label="Sun path and wind"><svg id="climsvg" class="dsvg" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Sun path and wind rose over the floor plate"></svg></section>
  <section class="scene" id="sc-alloc"''')
# the conceptual axo (tools/axo): a scene for the stills and the live model, and the three.js bundle before the main script
body=rep(body,'  <section class="scene" id="sc-overview"','''  <section class="scene" id="sc-axo3" data-mode="still" aria-label="Conceptual axonometric, test fit 03"><div class="ax3-stage"><span class="ax3-tag">Test fit 03</span><img id="ax3-img" alt="" decoding="async"><canvas id="ax3-cv" aria-label="Interactive 3D model of the floor"></canvas><div class="ax3-ovl" id="ax3-ovl" aria-hidden="true"></div></div><div class="ax3-bar"><div class="seg" id="ax3-view" role="radiogroup" aria-label="View"></div><div class="seg" id="ax3-style" role="radiogroup" aria-label="Colours"></div><button type="button" class="ax3-reset" id="ax3-reset">Reset view</button></div></section>
  <section class="scene" id="sc-overview"''')
import os, base64
AXD=os.path.join(os.path.dirname(os.path.abspath(SRC)),'tools','axo')
body+='<script>'+open(os.path.join(AXD,'axo.bundle.js')).read().strip()+'</script>\n'
# ---------- script ----------
concept="const {buildCity,buildLoop}=(function(){\n"+open('tf_concept_consts.js').read()+(city+loopf).replace("'TOWN SQUARE'","'SHARED SPACES'")+"  return {buildCity,buildLoop};\n})();\n"
data=open('tf_data.js').read().replace('/*REALFIT*/null',open('realfit.json').read())
data+=open('tf_site.js').read().replace('/*SITE*/null',open('site.json').read())
plan=open('tf_plan.js').read().replace('/*CONCEPT*/',concept)
steps=open('tf_steps.js').read()
# axo stills: <repo>/renders/axo-<view>-<style>.webp, and the model data, embedded
AXI={}
for f in sorted(os.listdir(os.path.join(os.path.dirname(os.path.abspath(SRC)),'renders'))):
    m=re.match(r'^axo-([a-z]+)-([a-z]+)\.webp$',f)
    if m: AXI[m.group(1)+'-'+m.group(2)]='data:image/webp;base64,'+base64.b64encode(open(os.path.join(os.path.dirname(os.path.abspath(SRC)),'renders',f),'rb').read()).decode()
print('axo stills',sorted(AXI))
axo=open('tf_axo.js').read().replace('/*AXO_IMG*/null',json.dumps(AXI,sort_keys=True)).replace('/*AXO_DATA*/null',open(os.path.join(AXD,'axo.json')).read().strip())
LAB=os.path.join(os.path.dirname(os.path.abspath(SRC)),'renders','axo-exploded-layers.json')
axo=axo.replace('/*AXO_LAB*/null',open(LAB).read().strip() if os.path.exists(LAB) else 'null')
# renders: real kinds
renders=rep(renders,renders[renders.index('const NB_KINDS='):renders.index('const canRender=')],
"""const SPACE_NAMES={desk:'Workstations',garden:'Acker Garden · Work Arena',cabin:'Executive cabin',sprint:'Quick sprint room',dept:'Departmental room',huddle:'Collaboration huddle',hatchery:'The Hatchery',duo:'Two-person room',booth:'Phone booth',pantry:'Pantry point',zen:'Zen room',prayer:'Prayer room',mother:"Mother's room",cafe:'Café and dining',reception:'Reception',lobby:'Lobby',visitor:'Visitor hub',board:'Boardroom',studio:'Studio'};
/* which sample interior stands in for each space until the real renders arrive */
const SCENE_OF={garden:'huddle',sprint:'meeting',dept:'board',hatchery:'huddle',duo:'focus',prayer:'zen',mother:'zen',lobby:'reception',visitor:'meeting',studio:'meeting'};
const ACCENT={N01:'#ff7a59',N02:'#f0b43a',N03:'#2ec4b6',N04:'#58a9ff',N05:'#ef72b2',N06:'#a3d977',TS:'#7c5cff'};
""")
renders=rep(renders,"const canRender=k=>NB_KINDS.includes(k)||TS_KINDS.includes(k);","const canRender=k=>!!SPACE_NAMES[k];")
# real renders: <repo>/renders/<key>-<light|dark>.<ext>, or n03-<key>-… for one neighbourhood, embedded so the file stays self-contained
RD=os.path.join(os.path.dirname(os.path.abspath(SRC)),'renders'); REN={}
for f in sorted(os.listdir(RD)) if os.path.isdir(RD) else []:
    m=re.match(r'^(?:(n\d\d)-)?([a-z]+)-(light|dark)\.(jpe?g|png|webp)$',f)
    if not m: continue
    key=(m.group(1).upper()+':' if m.group(1) else '')+m.group(2)
    mime={'jpg':'jpeg','jpeg':'jpeg','png':'png','webp':'webp'}[m.group(4)]
    REN.setdefault(key,{})[m.group(3)]='data:image/%s;base64,%s'%(mime,base64.b64encode(open(os.path.join(RD,f),'rb').read()).decode())
ren_old=renders[renders.index('const RENDERS={'):renders.index('};',renders.index('const RENDERS={'))+3]
renders=rep(renders,ren_old,'const RENDERS='+json.dumps(REN,sort_keys=True)+';\n')
print('renders',{k:sorted(v) for k,v in REN.items()})
renders=rep(renders,"(SCENE[k]||SCENE.meeting)();","(SCENE[SCENE_OF[k]||k]||SCENE.meeting)();")
# engine edits
e=engine
e=rep(e,"loop:$('#sc-loop'),brief:$('#sc-brief'),alloc:$('#sc-alloc')","loop:$('#sc-loop'),site:$('#sc-site'),climate:$('#sc-climate'),alloc:$('#sc-alloc')")
e=rep(e,"plan:$('#sc-plan'),","plan:$('#sc-plan'),axo3:$('#sc-axo3'),")
e=rep(e,"  buildPlan(); buildCover(); buildCity(); buildLoop(); buildBrief(); buildAlloc(); buildOverview(); buildNumbers();",
"""  $('svg defs').insertAdjacentHTML('beforeend',`<clipPath id="clip-rf"><path d="${PD(RF.plate)}"/></clipPath>`);
  buildPlan(); buildCover(); buildCity(); buildLoop(); buildSite(); buildClimate(); buildAlloc(); buildOverview(); buildNumbers();""")
e=rep(e,"  document.body.classList.toggle('full',!!s.full);","  document.body.classList.toggle('full',!!s.full);\n  document.body.classList.toggle('wide',!!s.wide);\n  document.body.classList.toggle('tall',!!s.tall);")
e=rep(e,"  if(st.width) $('#plan-fit').style.setProperty('--fit',Math.min(st.width/1280,st.height/780)*.97);\n  const ax=$('#dv-axo').getBoundingClientRect();\n  if(ax.width) $('#axo-fit').style.setProperty('--fit',Math.min((ax.width-24)/470,(ax.height-60)/290));",
"  if(st.width) $('#plan-fit').style.setProperty('--fit',Math.min(st.width/PW,st.height/PH)*.97);\n  const ax=$('#dv-axo').getBoundingClientRect();\n  if(ax.width) $('#axo-fit').style.setProperty('--fit',Math.min((ax.width-24)/(AX.w*.95),(ax.height-60)/(AX.h*1.15)));")
e=re.sub(r"function wireDD\(\)\{.*?\n\}\n","",e,flags=re.S)
e=re.sub(r"function wireShared\(\)\{.*?\n\}\n","",e,flags=re.S)
tip_old=e[e.index("function ctxInfo(ctx){"):e.index("function showTip(")]
e=rep(e,tip_old,open('tf_tips.js').read())
e=rep(e,"const z=e.target.closest('.zone'); if(z&&SCENES.plan.classList.contains('f-hover')&&e.pointerType==='mouse') showTip(z.dataset.nb,e.clientX,e.clientY); else hideTip(); });",
        "const z=e.target.closest('.zone'); if(z&&SCENES.plan.classList.contains('f-hover')&&e.pointerType==='mouse') showTip(z.dataset.ts||z.dataset.nb,e.clientX,e.clientY); else hideTip(); });")
e=rep(e,"e.target.closest('rect[data-go-nb]')","e.target.closest('[data-go-nb]:not(button)')")
sm_old=e[e.index("function spaceMeta(ctx,k){"):e.index("function setImg(")]
e=rep(e,sm_old,"""function spaceMeta(ctx,k){
  const inst=SP.filter(x=>inCtx(x,ctx)&&x.k===k); if(!inst.length) return '';
  if(k==='desk') return `${inst.reduce((a,x)=>a+x.seats,0)} workstations in ${inst.length} clusters`;
  if(inst.every(x=>x.big)){ const side=inst.map(x=>({R1:'west',R2:'east'})[x.area]).filter(Boolean); return [side.length>1?side.join(' and ').replace(/^./,c=>c.toUpperCase()):'', `${fmt(inst.reduce((a,x)=>a+m2ft(x.m2||M2[x.area]),0))} sq ft`].filter(Boolean).join(' · '); }
  const where=ctx==='TS'?'the shared spaces':'this neighbourhood', seats=inst.map(x=>x.seats).filter(Boolean), lo=Math.min(...seats), hi=Math.max(...seats);
  return [inst.length>1?`${inst.length} in ${where}`:'', seats.length?(lo===hi?`${lo} ${lo===1?'seat':'seats'}${inst.length>1?' each':''}`:`${lo} to ${hi} seats`):''].filter(Boolean).join(' · ');
}
""")
e=rep(e,"RV.ctx=ctx||sp.nb; RV.list=(RV.ctx==='TS'?TS_KINDS:NB_KINDS).filter(k=>SP.some(x=>inCtx(x,RV.ctx)&&x.k===k));",
        "RV.ctx=ctx||sp.nb; RV.list=KIND_ORDER.filter(k=>canRender(k)&&SP.some(x=>inCtx(x,RV.ctx)&&x.k===k));")
out=head_css+body+prelude+data+plan+renders+axo+steps+e
open(OUT,'w').write(out)
print('written',len(out))
