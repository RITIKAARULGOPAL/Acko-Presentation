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
# ---------- script ----------
concept="const {buildCity,buildLoop}=(function(){\n"+open('tf_concept_consts.js').read()+(city+loopf).replace("'TOWN SQUARE'","'SHARED SPACES'")+"  return {buildCity,buildLoop};\n})();\n"
data=open('tf_data.js').read().replace('/*REALFIT*/null',open('realfit.json').read())
plan=open('tf_plan.js').read().replace('/*CONCEPT*/',concept)
steps=open('tf_steps.js').read()
# renders: real kinds
renders=rep(renders,renders[renders.index('const NB_KINDS='):renders.index('const canRender=')],
"""const SPACE_NAMES={desk:'Workstations',cabin:'Executive cabin',sprint:'Quick sprint room',dept:'Departmental room',huddle:'Collaboration huddle',hatchery:'The Hatchery',duo:'Two-person room',booth:'Phone booth',pantry:'Pantry point',zen:'Zen room',prayer:'Prayer room',mother:"Mother's room",cafe:'Café and dining',reception:'Reception',lobby:'Lobby',visitor:'Visitor hub',board:'Boardroom',studio:'Studio'};
/* which sample interior stands in for each space until the real renders arrive */
const SCENE_OF={sprint:'meeting',dept:'board',hatchery:'huddle',duo:'focus',prayer:'zen',mother:'zen',lobby:'reception',visitor:'meeting',studio:'meeting'};
const ACCENT={N01:'#ff7a59',N02:'#f0b43a',N03:'#2ec4b6',N04:'#58a9ff',N05:'#ef72b2',N06:'#a3d977',TS:'#7c5cff'};
""")
renders=rep(renders,"const canRender=k=>NB_KINDS.includes(k)||TS_KINDS.includes(k);","const canRender=k=>!!SPACE_NAMES[k];")
renders=rep(renders,"(SCENE[k]||SCENE.meeting)();","(SCENE[SCENE_OF[k]||k]||SCENE.meeting)();")
# engine edits
e=engine
e=rep(e,"loop:$('#sc-loop'),brief:$('#sc-brief'),alloc:$('#sc-alloc')","loop:$('#sc-loop'),alloc:$('#sc-alloc')")
e=rep(e,"  buildPlan(); buildCover(); buildCity(); buildLoop(); buildBrief(); buildAlloc(); buildOverview(); buildNumbers();",
"""  $('svg defs').insertAdjacentHTML('beforeend',`<clipPath id="clip-rf"><path d="${PD(RF.plate)}"/></clipPath>`);
  buildPlan(); buildCover(); buildCity(); buildLoop(); buildAlloc(); buildOverview(); buildNumbers();""")
e=rep(e,"  document.body.classList.toggle('full',!!s.full);","  document.body.classList.toggle('full',!!s.full);\n  document.body.classList.toggle('wide',!!s.wide);")
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
  if(inst.every(x=>x.big)){ const side=inst.map(x=>({R1:'west',R2:'east'})[x.area]).filter(Boolean); return [side.length>1?side.join(' and ').replace(/^./,c=>c.toUpperCase()):'', `${fmt(inst.reduce((a,x)=>a+m2ft(M2[x.area]),0))} sq ft`].filter(Boolean).join(' · '); }
  const where=ctx==='TS'?'the shared spaces':'this neighbourhood', seats=inst.map(x=>x.seats).filter(Boolean), lo=Math.min(...seats), hi=Math.max(...seats);
  return [inst.length>1?`${inst.length} in ${where}`:'', seats.length?(lo===hi?`${lo} ${lo===1?'seat':'seats'}${inst.length>1?' each':''}`:`${lo} to ${hi} seats`):''].filter(Boolean).join(' · ');
}
""")
e=rep(e,"RV.ctx=ctx||sp.nb; RV.list=(RV.ctx==='TS'?TS_KINDS:NB_KINDS).filter(k=>SP.some(x=>inCtx(x,RV.ctx)&&x.k===k));",
        "RV.ctx=ctx||sp.nb; RV.list=KIND_ORDER.filter(k=>canRender(k)&&SP.some(x=>inCtx(x,RV.ctx)&&x.k===k));")
out=head_css+body+prelude+data+plan+renders+steps+e
open(OUT,'w').write(out)
print('written',len(out))
