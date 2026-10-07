# Build realfit.json: everything the test-fit presentation needs, in 50 mm drawing units.
import sys, json, re, math, collections, string
sys.path.insert(0,'.')
from geo import *
from shapely.geometry import Point, Polygon, LineString, box
from shapely.prepared import prep
UNIT=50.0; XO=-177000; YO=-373500
def T(x,y): return ((x-XO)/UNIT, (YO-y)/UNIT)
def r0(v): return int(round(v))
POS=json.load(open('dxf_pos.json'))
# ---------- zones ----------
ZP=[Polygon(p).buffer(0) for p in Z['zones']]
NB_ORDER=[3,7,6,2,1,0]          # zone index (0-based) west→east: zone4, zone8, zone7, zone3, zone2, zone1
RC=[4,5]                        # zone5 (west reception), zone6 (east reception)
z4=ZP[3]; z5=ZP[4]
TSW=PLATE_P.intersection(box(-137400,-409100,-108202,-391300)).difference(z4).difference(z5)
TSW=max((TSW.geoms if hasattr(TSW,'geoms') else [TSW]), key=lambda g:g.area)
TSC=box(-49516,-391100,-33600,-384950).difference(unary_union(ZP))
TSC=max((TSC.geoms if hasattr(TSC,'geoms') else [TSC]), key=lambda g:g.area)
AREAS=[('N%02d'%(i+1),ZP[z]) for i,z in enumerate(NB_ORDER)]+[('R1',ZP[4]),('R2',ZP[5]),('TW',TSW),('TC',TSC)]
PREP=[(k,prep(g)) for k,g in AREAS]
def area_of(x,y):
    p=Point(x,y)
    for k,g in PREP:
        if g.contains(p): return k
    return 'X'
# ---------- layer groups ----------
PART={'OB-I-PART-GLS','OB-I-PART-GYP','OB-I-PART-SOF','I_PAR_PA_IN_GL','I-PART-GLSS','SKV_GLASS PARTITION','I-PART-GYP','I-PART-GYP-100MM','A-WALL-EL3','OB-A-WALL','I_WALL_WA_CS_BR_100'}
GREEN={'OB_Plants','Plants','AVA - PLANTS','I-MISC-PLNT','SKV-AI-PLANT','A-PLANTS'}
CORE={'A-WALL'}; COLS={'S-COLS'}; STRS={'S-STRS','S-STRS-MBND'}
CORED={'G-IMPT','A-DOOR','A-DOOR-FRAM','A-DOOR-HDLN','A-DOOR-GLAZ','A-DOORWIN','A-DOOR-OPNG','P-SANR-FIXT','A-FLOR-HRAL','A-FLOR-HRAL-MBND'}
SKIP={'A-GENM','A-FLOR','A-FLOR-OTLN','A-FLOR-OVHD','A-DETL','A-DETL-GENF','A-DETL-THIN','OB-I-BLK-TAGS','Defpoints','AI-ANNO-DIM','A-ANNO-NOTE','G-ANNO-TEXT','I-PART-TEXT','A-AREA-IDEN','A-DOOR-IDEN','A-GENM-IDEN','Q-SPCQ','None','HATCH-PLINES','N-HATCH','Lag 1','OB-I-SHADE60','OB-I-SHADE40','OB-I-ELEV-1','OB-I-MLWK-HIDN','OB-I-MLWK-OVHD','A-SYM-FURN','h','HATCH','pline','TEXT1','RAILING'}
def pts_of(d):
    n=list(map(int,re.findall(r'-?\d+',d))); return [(n[i],-n[i+1]) for i in range(0,len(n),2)]
groups=collections.defaultdict(lambda: collections.defaultdict(list))
seen=set()
stats=collections.Counter()
for lay,ds in D['layers'].items():
    if lay in SKIP or lay.startswith('I_FUR_') and any(s in lay for s in ('LENGTH','WIDTH','POSITION')): continue
    if lay in PART: g='part'
    elif lay in GREEN: g='green'
    elif lay in CORE: g='core'
    elif lay in COLS: g='cols'
    elif lay in STRS: g='stair'
    elif lay in CORED: g='cored'
    else: g='furn'
    for d in ds:
        P=pts_of(d)
        if len(P)<2: continue
        xs=[p[0] for p in P]; ys=[p[1] for p in P]
        ext=max(max(xs)-min(xs),max(ys)-min(ys))
        if g in ('furn','green') and ext<120: stats['tiny']+=1; continue
        if ext>150000: stats['frame']+=1; continue
        if g=='part' and ext<60: continue
        tol={'furn':30,'green':60,'part':15,'core':15,'cored':40,'cols':10,'stair':20}[g]
        ls=LineString(P).simplify(tol)
        Q=[T(x,y) for x,y in ls.coords]
        key=tuple((r0(a*2),r0(b*2)) for a,b in Q)    # dedupe identical lines across duplicate layers
        if g=='part':
            k2=key if key<key[::-1] else key[::-1]
            if k2 in seen: stats['dup']+=1; continue
            seen.add(k2)
        cx=sum(xs)/len(xs); cy=sum(ys)/len(ys)
        a=area_of(cx,cy) if g in ('furn','part','green') else 'S'
        groups[g][a].append(Q)
        stats[g]+=1
print(stats)
def enc(polys, prec=1):
    # relative path, integers in 50mm units (prec 1) ; keeps file small
    out=[]
    for Q in polys:
        x0,y0=r0(Q[0][0]),r0(Q[0][1]); s=f'M{x0} {y0}'; px,py=x0,y0
        for x,y in Q[1:]:
            xi,yi=r0(x),r0(y); dx,dy=xi-px,yi-py
            if dx==0 and dy==0: continue
            s+=f'l{dx} {dy}'; px,py=xi,yi
        if s.count('l'): out.append(s)
    return ''.join(out)
G={g:{a:enc(v) for a,v in d.items()} for g,d in groups.items()}
for g in G: print(g,{a:len(s) for a,s in G[g].items()})
# ---------- columns: cluster the S-COLS segments ----------
segs=[[p for p in Q] for Q in groups['cols']['S']]
cl=[]
for Q in segs:
    xs=[p[0] for p in Q]; ys=[p[1] for p in Q]; bb=[min(xs),min(ys),max(xs),max(ys)]
    for c in cl:
        if bb[0]<=c[2]+3 and bb[2]>=c[0]-3 and bb[1]<=c[3]+3 and bb[3]>=c[1]-3:
            c[0]=min(c[0],bb[0]); c[1]=min(c[1],bb[1]); c[2]=max(c[2],bb[2]); c[3]=max(c[3],bb[3]); break
    else: cl.append(bb)
cols=[[round(c[0],1),round(c[1],1),round(c[2]-c[0],1),round(c[3]-c[1],1)] for c in cl if 4<c[2]-c[0]<40 and 4<c[3]-c[1]<40]
print('cols',len(cols))
# ---------- texts ----------
TX=[(lay,x,y,re.sub(r'\s+',' ',t).strip()) for lay,x,y,t,h,r in D['texts']]
# stairs: label + bbox of stair geometry around it
stairs=[]
for lay,x,y,t in TX:
    m=re.fullmatch(r'ST(\d)',t)
    if lay=='A-AREA-IDEN' and m:
        near=[p for d in D['layers']['S-STRS'] for p in [pts_of(d)] if abs(sum(q[0] for q in p)/len(p)-x)<7000 and abs(sum(q[1] for q in p)/len(p)-y)<6000]
        xs=[q[0] for p in near for q in p]; ys=[q[1] for p in near for q in p]
        a=T(min(xs)-300,max(ys)+300); b=T(max(xs)+300,min(ys)-300)
        stairs.append({'id':m.group(1),'x':round(a[0],1),'y':round(a[1],1),'w':round(b[0]-a[0],1),'h':round(b[1]-a[1],1),'lx':round(T(x,y)[0],1),'ly':round(T(x,y)[1],1)})
stairs.sort(key=lambda s:s['x'])
print('stairs',[(s['id'],s['x'],s['w'],s['h']) for s in stairs])
# ---------- rooms from labels ----------
KINDS=[(r'QUICK SPRINT (\d+) PAX','sprint'),(r'COLLABORATION HUDDLE (\d+) PAX','huddle'),(r'DEPARTMENTAL ROOMS (\d+) PAX','dept'),(r'BOARDROOM (\d+) PAX','board'),
       (r'THE HATCHERY (\d+) PAX','hatchery'),(r'VISITOR HUB (\d+) PAX','visitor'),(r'^(\d+) PAX - \d+','duo'),(r'EXECUTIVE CORNER CABIN','cabin'),(r'ZEN ROOM','zen'),
       (r'^PB \d+','booth'),(r'PRAYER ROOM','prayer'),(r"MOTHER'S ROOM",'mother'),(r'RECEPTION & WAITING LOUNGE','reception'),(r'STUDIO','studio'),
       (r'SERVER ROOM|UPS & ELECTRICAL ROOM|BATTERY ROOM|HUB ROOM|STORE ROOM|MAIL ROOM|RAIN COAT','support'),(r'COFFEE POINT','coffee')]
rooms=[]; seenlab=set()
for lay,x,y,t in TX:
    if lay!='OB-I-ANNO-TEXT': continue
    for pat,k in KINDS:
        m=re.search(pat,t)
        if m:
            if (t,round(x/500),round(y/500)) in seenlab: break
            seenlab.add((t,round(x/500),round(y/500)))
            seats=int(m.group(1)) if m.groups() else {'booth':1,'cabin':4,'zen':4,'prayer':6,'mother':2,'reception':12,'studio':4}.get(k,0)
            u,v=T(x,y); rooms.append({'k':k,'t':string.capwords(t.lower()).replace('Pax','pax'),'x':round(u,1),'y':round(v,1),'s':seats,'a':area_of(x,y)})
            break
print('rooms',collections.Counter(r['k'] for r in rooms))
# room footprints: enclosed cells of partitions + core walls (door gaps closed by buffering)
lines=[LineString([(a*UNIT+XO, YO-b*UNIT) for a,b in Q]) for a_ in groups['part'].values() for Q in a_]+[LineString(p) for p in paths('A-WALL') if len(p)>1]
lines.append(PLATE_P.exterior)
bu=unary_union([l.buffer(480) for l in lines])
cells=[Polygon(h).buffer(480) for g in (bu.geoms if hasattr(bu,'geoms') else [bu]) for h in g.interiors]
cells=[c for c in cells if 1.2e6<c.area<160e6]
pc=[(c,prep(c)) for c in cells]
for r in rooms:
    x=r['x']*UNIT+XO; y=YO-r['y']*UNIT; p=Point(x,y)
    best=None
    for c,pp in pc:
        if pp.contains(p) and (best is None or c.area<best.area): best=c
    if best is not None and best.area< (60e6 if r['k'] not in ('board','dept','reception','studio') else 160e6):
        mr=best.minimum_rotated_rectangle
        r['poly']=[[round(a,1),round(b,1)] for a,b in (T(*q) for q in list(mr.exterior.coords)[:-1])]
        r['m2']=round(best.area/1e6,1)
print('rooms with footprint',sum(1 for r in rooms if 'poly' in r),'of',len(rooms))
# ---------- desks ----------
DESK={'rytu':3,'WS 1500x750mm':1,'WS 1500x750mm 2':1,'rhrt':1,'4PAX WITH PLANTER':4}
desks=[]
for name,n in DESK.items():
    for x,y,rot in POS.get(name,[]):
        u,v=T(x,y); desks.append([round(u,1),round(v,1),n,area_of(x,y),1 if n==4 else 0])
print('desks',sum(d[2] for d in desks), collections.Counter(d[3] for d in desks for _ in range(d[2])))
# desk cluster centres (rytu insert point is a corner: use the block centre in world space if possible)
# pantry points: cluster microwave tags
mw=[(x,y) for x,y,r in POS.get('EQ_PA_MO_0635X0535_01',[])]
pant=[]
for x,y in mw:
    for c in pant:
        if math.dist(c['p'],(x,y))<6000: c['n']+=1; break
    else: pant.append({'p':(x,y),'n':1})
pantries=[{'x':round(T(*c['p'])[0],1),'y':round(T(*c['p'])[1],1),'a':area_of(*c['p']),'n':c['n']} for c in pant]
print('pantry points',len(pantries),collections.Counter(p['a'] for p in pantries))
# training / town-hall seating, café seats
def cnt(names):
    c=collections.Counter()
    for nm in names:
        for x,y,r in POS.get(nm,[]): c[area_of(x,y)]+=1
    return c
train={}; cafe=cnt(['PANTRY CHAIRS 3','Chair_Cafe-Generic - CH-23-V289','CH_CR_TA_01','CH_CF_PC_01'])
bench=cnt(['Bench - Day Dinning-V295'])
print('training',train,'cafe chairs',cafe,'benches',bench)
# ---------- fire egress routes ----------
routes=[]
for P in Z['loop']:
    a,b=P[0],P[-1]
    def dstair(p):
        u,v=T(*p); return min(math.dist((u,v),(s['x']+s['w']/2,s['y']+s['h']/2)) for s in stairs)
    if dstair(a)<dstair(b): P=P[::-1]
    Q=[T(x,y) for x,y in P]
    L=sum(math.dist(P[i],P[i+1]) for i in range(len(P)-1))/1000
    end=Q[-1]; st=min(stairs,key=lambda s:math.dist(end,(s['x']+s['w']/2,s['y']+s['h']/2)))
    routes.append({'pts':[[round(x,1),round(y,1)] for x,y in Q],'m':round(L,1),'to':st['id'],'a':area_of(*P[0])})
print('routes',[(r['a'],r['to'],r['m']) for r in routes])
# ---------- polygons ----------
def poly(g): return [[round(a,1),round(b,1)] for a,b in (T(x,y) for x,y in list(g.exterior.coords)[:-1])]
out={'unit':UNIT/1000,'plate':poly(PLATE_P),
     'terraces':[poly(box(-108202,-409079,-82552,-399528)),poly(box(-27327,-409079,-1602,-399528))],
     'cutout':poly(box(-45300,-390500,-37300,-385600)),
     'areas':{k:poly(g) for k,g in AREAS},'areaM2':{k:round(g.area/1e6,1) for k,g in AREAS},'plateM2':round(PLATE_P.area/1e6,1),
     'g':G,'cols':cols,'stairs':stairs,'rooms':rooms,'desks':desks,'pantries':pantries,'routes':routes,
     'seats':{'training':dict(train),'cafe':dict(cafe),'bench':dict(bench)}}
json.dump(out,open('realfit.json','w'),separators=(',',':'))
import os; print('realfit.json bytes',os.path.getsize('realfit.json'))
# ---------- extras: label points, daylight band, daylight desks ----------
from shapely.ops import polylabel
out=json.load(open('realfit.json'))
lab={}
for k,g in AREAS:
    p=polylabel(g,tolerance=200); lab[k]=[round(v,1) for v in T(p.x,p.y)]
out['lab']=lab
inner=PLATE_P.buffer(-6000, join_style=2)
ig=max((inner.geoms if hasattr(inner,'geoms') else [inner]), key=lambda g:g.area)
out['plateIn']=poly(ig)
ext=PLATE_P.exterior
# façade = the whole plate edge, including the glass facing the two terraces
fac=PLATE_P.exterior
day=tot=0
for d in desks:
    x=d[0]*UNIT+XO; y=YO-d[1]*UNIT; tot+=d[2]
    if fac.distance(Point(x,y))<=6000: day+=d[2]
out['daylight']=round(100*day/tot); print('daylight desks %d of %d'%(day,tot))
# ---------- lift lobbies: two facing rows of passenger lifts with the lobby between them ----------
doors=[(x,y) for nm,ps in POS.items() if nm.startswith('Lift Door') for x,y,r in ps]
pas=sorted((x,y) for nm,ps in POS.items() if 'Passenger' in nm for x,y,r in ps)
cols=[]
for x,y in pas:
    if cols and abs(cols[-1]['x']-x)<1000: cols[-1]['ys'].append(y)
    else: cols.append({'x':x,'ys':[y]})
lifts=[]
for c0,c1 in zip(cols,cols[1:]):
    if not 4000<c1['x']-c0['x']<9000: continue
    ys=c0['ys']+c1['ys']; dx=[x for x,y in doors if c0['x']<x<c1['x'] and min(ys)-2000<y<max(ys)+2000]
    if not dx: continue
    (u0,v0),(u1,v1)=T(min(dx),max(ys)+1500),T(max(dx),min(ys)-1500)
    lifts.append({'x':round((u0+u1)/2,1),'y':round((v0+v1)/2,1),'w':round(u1-u0,1),'h':round(v1-v0,1),'n':len(ys),'a':area_of((min(dx)+max(dx))/2,sum(ys)/len(ys))})
lifts.sort(key=lambda l:l['x'])
out['lifts']=lifts; print('lift lobbies',lifts)
out['len']=round((PLATE_P.bounds[2]-PLATE_P.bounds[0])/1000,1); out['depth']=round((PLATE_P.bounds[3]-PLATE_P.bounds[1])/1000,1)
json.dump(out,open('realfit.json','w'),separators=(',',':'))
print('labels',lab,'daylight %',out['daylight'],'size',out['len'],out['depth'])
