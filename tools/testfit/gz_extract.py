# Green zone analysis input → realfit.json['gz'], in 50 mm plan units.
# Reads the AC_ space layers (the drawing's own space classification), the furniture, doors, partitions,
# escape routes and existing planting, and works out:
#   spaces     one record per AC_ space: type, outline, m², occupancy read from the drawing, daylight, visibility
#   keep       the circulation keep-clear mask (nothing may be planted here)
#   free       the floor left over where planting can go
#   cands      candidate green-zone spots cut from the free floor, with the facts the typology needs
# The scoring itself (footfall, dwell, carbon index, priority, plant counts) runs in the page (tf_green.js),
# so the designer can override every assumption and see the result straight away.
import sys, json, re, math, collections
sys.path.insert(0,'.')
from geo import *
from shapely.geometry import Point, Polygon, LineString, MultiPolygon, box
from shapely.ops import unary_union, polylabel, nearest_points
from shapely.prepared import prep
from shapely import STRtree
import numpy as np
UNIT=50.0; XO=-177000; YO=-373500
M=1000.0                                  # mm per metre
def T(x,y): return ((x-XO)/UNIT, (YO-y)/UNIT)
def Ti(u,v): return (u*UNIT+XO, YO-v*UNIT)
RF=json.load(open('realfit.json')); POS=json.load(open('dxf_pos.json'))

# ---------- project standards (from the drawing where it gives them) ----------
NOTES=[t for lay,x,y,t,h,r in D['texts'] if 'CORRIDOR' in t.upper()]
mw=[int(m.group(1)) for t in NOTES for m in [re.search(r'(\d{3,4})\s*MM\s*WIDE\s*CORRIDOR',t.upper())] if m]
CLEAR=(max(mw) if mw else 1500)/M         # required clear corridor width, m (the drawing notes "1500MM WIDE CORRIDOR")
PLANTER=0.6                               # depth of a floor planter, m
DOOR_CLR=1.2                              # kept clear in front of every door, m
FURN_CLR=0.6                              # around furniture: chairs pulled out, desks and storage opened, m
ROUTE_CLR=max(1.0,CLEAR/2+0.25)           # each side of an escape-route centreline
TURN_CLR=1.5                              # sight triangle at corridor turns and junctions
print('clear corridor width %.2f m (from %s)'%(CLEAR,'drawing note' if mw else 'default'),'notes',len(NOTES))

# ---------- the spaces ----------
# layer → (type, category); category follows the brief: work, collab, social, arrival, move, support
AC={'AC_PHONE_BOOTH':('booth','work'),'AC_ZEN_ROOM':('zen','work'),'AC_EXECUTIVE_CORNER_CABIN':('cabin','work'),
    'AC_PRAYER_ROOM':('wellness','support'),"AC_MOTHER'S_ROOM":('wellness','support'),
    'AC_QUICK_SPIRIT':('meeting','collab'),'AC_DEPARTMENTAL_ROOMS':('meeting','collab'),'AC_BOARD_ROOM':('meeting','collab'),
    'AC_THE_HATCHERY':('meeting','collab'),'AC_VISITOR_HUB':('meeting','collab'),'AC_THE_STUDIO_ROOM':('meeting','collab'),
    'AC_COLLAB_HUDDLE':('huddle','collab'),'AC_TRAINING_ROOM':('event','social'),
    'AC_LIFT_LOBBY':('lobby','arrival'),'AC_RECEPTION':('reception','arrival'),
    'AC_WASHROOM':('wash','support'),'AC_AHU':('ahu','support'),'AC_FIRE_EXIT_STAIRCASE':('stair','support'),
    'AC_HUB_ROOM':('tech','support'),'AC_UPS_SERVER_BATTERY_BMS_ROOM':('tech','support'),'AC_OUT_OF_SCOPE':('oos','support'),
    'AC_COFFEE_CORNER':('pantry','social'),'AC_CAFETERIA':('cafe','social'),'AC_COLLAB':('collab','collab'),
    'AC_CORRIDOR':('corridor','move'),'AC_WORKHALL':('open','work')}
MARKED={'AC_LIFT_LOBBY','AC_WASHROOM','AC_FIRE_EXIT_STAIRCASE','AC_AHU','AC_STRENGTHEN_SLAB'}   # layers that also carry numbered marker circles
def acp(l,minm2=0.3):
    out,seen=[],set()
    for g in (Polygon(p).buffer(0) for p in paths(l) if len(p)>=3):
        k=tuple(round(v/100) for v in g.bounds)
        if g.area>minm2*1e6 and k not in seen: seen.add(k); out.append(g)
    return out
def parts(g): return [h for h in (g.geoms if hasattr(g,'geoms') else [g]) if h.geom_type=='Polygon' and not h.is_empty]
def biggest(g): return max(parts(g),key=lambda h:h.area)
# each m² belongs to one space: enclosed rooms first, the open work arenas last (they are drawn around the rooms)
raw=[]; taken=Polygon()
for lay,(k,c) in AC.items():
    for g in acp(lay,5 if lay in MARKED else 0.2):
        g=g.intersection(PLATE_P).difference(taken)
        if g.is_empty or g.area<0.5e6: continue
        taken=taken.union(g); raw.append((lay,k,c,g))
print('spaces',len(raw),collections.Counter(k for l,k,c,g in raw))

def plan_ring(g,tol=40):
    g=g.simplify(tol); return [[round(a,1),round(b,1)] for a,b in (T(*q) for q in list(g.exterior.coords)[:-1])]
def plan_rings(g,tol=40):
    out=[]
    for h in parts(g.simplify(tol)):
        out.append([[round(a,1),round(b,1)] for a,b in (T(*q) for q in list(h.exterior.coords)[:-1])])
        for i in h.interiors: out.append([[round(a,1),round(b,1)] for a,b in (T(*q) for q in list(i.coords)[:-1])])
    return out

# neighbourhoods (plan units → mm) to tag each space
NBP={a:Polygon([Ti(*p) for p in pts]).buffer(0) for a,pts in RF['areas'].items()}
def nb_of(g):
    best,ba='X',0
    for a,p in NBP.items():
        x=g.intersection(p).area
        if x>ba: best,ba=a,x
    return best if ba>0.25*g.area else 'X'

# occupancy read from the drawing: desks, room labels, chairs
desks=[(Point(Ti(d[0],d[1])),d[2]) for d in RF['desks']]
rooms=[r for r in RF['rooms'] if r.get('ac')]
SEATW={'CH_CF_PC_01':1,'Traning room seating':1,'CH_MR_TA_01':1,'PANTRY CHAIRS 3':1,'CH_CR_TA_01':1,'Chair_Cafe-Generic - CH-23-V289':1,
       'Bench - Day Dinning-V295':3,'SE_CF_04_0900_01':4,'SE_CF_04_1200X0750_01':4,'COCO-CHAIR1':1,'fixed seating':4,'Stool_ CH-10_Howe 40-10426538':1,
       'FURNITURE-CHAIR-ZODI':1,'steelcase-task chair-flat29-flat1-flat1':1,'Outline 3 seater Plan':3,'Outline Chair Plan':1,'chair_Eames-OrganicChair':1,'CH_CA_LO_01':1}
chairs=[(Point(x,y),w) for nm,w in SEATW.items() for x,y,r in POS.get(nm,[])]
PLANTB=['TREE12','TREE_P03','Clump of Trees or Bushes - plan','tree 26','4PAX WITH PLANTER']
plant_pts=[(Point(x,y),nm) for nm in PLANTB for x,y,r in POS.get(nm,[])]

# ---------- geometry for clearances, sightlines and daylight ----------
def dec(s):
    """the compact relative paths in realfit.json back into polylines (mm)"""
    out=[]
    for m in re.finditer(r'M(-?\d+) (-?\d+)((?:l-?\d+ -?\d+)*)',s):
        x,y=int(m.group(1)),int(m.group(2)); P=[(x,y)]
        for a,b in re.findall(r'l(-?\d+) (-?\d+)',m.group(3)): x+=int(a); y+=int(b); P.append((x,y))
        out.append([Ti(u,v) for u,v in P])
    return out
def lines_of(grp): return [LineString(p) for a,s in RF['g'].get(grp,{}).items() for p in dec(s) if len(p)>1]
FURN=lines_of('furn'); GREEN=lines_of('green')
# furniture footprints: each piece's own outline filled in (long lines such as floor finishes stay lines)
def footprint(l):
    x0,y0,x1,y1=l.bounds
    return l.convex_hull if max(x1-x0,y1-y0)<=4000 else l
FURNP=[footprint(l) for l in FURN]
OPAQUE={'OB-I-PART-GYP','I-PART-GYP','I-PART-GYP-100MM','A-WALL-EL3','OB-A-WALL','I_WALL_WA_CS_BR_100','OB-I-PART-SOF','A-WALL'}
WALLS=[LineString(p) for l in OPAQUE for p in paths(l) if len(p)>1]
GLASS=[LineString(p) for l in ('OB-I-PART-GLS','I_PAR_PA_IN_GL','I-PART-GLSS','SKV_GLASS PARTITION') for p in paths(l) if len(p)>1]
DOORS=[LineString(p) for l in ('OB-I-DOOR-SWG','OB-I-DOOR-GLS','I-DOOR','A-DOOR','A-DOOR-OPNG') for p in paths(l) if len(p)>1]
ROUTES=[LineString([Ti(*q) for q in r['pts']]) for r in RF['routes']]
FACADE=PLATE_P.exterior
print('furniture',len(FURN),'walls',len(WALLS),'glass',len(GLASS),'doors',len(DOORS),'existing plant lines',len(GREEN),'plant blocks',len(plant_pts))

# ---------- spaces ----------
NICE={'open':'Work arena','corridor':'Corridor','pantry':'Coffee corner','lobby':'Lift lobby','reception':'Reception','cafe':'Café and dining',
      'wash':'Washrooms','ahu':'AHU room','stair':'Fire stair','tech':'Technical room','oos':'Base building (out of scope)','collab':'Acker Garden · Work Arena',
      'event':'Training room','booth':'Phone booth','zen':'Zen room','cabin':'Executive cabin','wellness':'Wellbeing room','huddle':'Collaboration huddle','meeting':'Meeting room'}
day6=PLATE_P.intersection(FACADE.buffer(6000))
# existing planting drawn as linework: one clump per touching group (a planter, a pot, a plant), blocks counted separately
GCLUMP=[h for h in parts(unary_union([l.buffer(150,resolution=2) for l in GREEN])) if h.area>0.05e6]
GCLUMP=[h for h in GCLUMP if not any(h.contains(p) for p,nm in plant_pts)]
spaces=[]; SPG={}
for i,(lay,k,c,g) in enumerate(raw):
    sid='S%03d'%(i+1); pg=prep(g)
    nd=sum(n for p,n in desks if pg.contains(p))
    seats=sum(w for p,w in chairs if pg.contains(p))
    rm=[r for r in rooms if r['ac']==lay and pg.contains(Point(Ti(r['x'],r['y'])))]
    name=rm[0]['t'] if len(rm)==1 else NICE.get(k,k.title())
    if len(rm)==1 and rm[0]['s']: seats=max(seats,rm[0]['s'])
    pl=sum(1 for p,nm in plant_pts if pg.contains(p))+sum(1 for h in GCLUMP if pg.contains(h.centroid))
    lp=polylabel(biggest(g),tolerance=300)
    sp={'id':sid,'k':k,'c':c,'ac':lay,'n':name,'nb':nb_of(g),'m2':round(g.area/1e6,1),'rings':plan_rings(g),'lab':[round(v,1) for v in T(lp.x,lp.y)],
        'desks':nd,'seats':seats,'plants':pl,'day':round(g.intersection(day6).area/g.area,2),'fd':round(FACADE.distance(lp)/M,1)}
    spaces.append(sp); SPG[sid]=g
# number the repeated names west → east (Work arena 1, 2 …), and add the side to the two receptions and lobbies
for nm in {s['n'] for s in spaces}:
    same=sorted([s for s in spaces if s['n']==nm],key=lambda s:s['lab'][0])
    if len(same)>1:
        for j,s in enumerate(same): s['n']=f"{nm} {j+1}" if s['k'] not in ('reception','lobby','cafe') else f"{nm} ({['west','east'][min(j,1)] if len(same)==2 else j+1})"
print('desks placed in spaces',sum(s['desks'] for s in spaces),'of',sum(d[2] for d in RF['desks']),'· seats',sum(s['seats'] for s in spaces))

# ---------- the keep-clear mask ----------
usable=unary_union([g for (lay,k,c,g) in raw if c!='support']).buffer(0)
corr=unary_union([g for (lay,k,c,g) in raw if k=='corridor']).buffer(0)
open_r=(PLANTER+CLEAR)/2*M
corr_narrow=corr.difference(corr.buffer(-open_r).buffer(open_r))          # corridor too narrow for a planter beside the clear width
turns=[]
for r in ROUTES:
    cs=list(r.coords)
    for a,b,c_ in zip(cs,cs[1:],cs[2:]):
        h1=math.atan2(b[1]-a[1],b[0]-a[0]); h2=math.atan2(c_[1]-b[1],c_[0]-b[0])
        if abs((h2-h1+math.pi)%(2*math.pi)-math.pi)>math.radians(25): turns.append(Point(b))
for i,a in enumerate(ROUTES):
    for b in ROUTES[i+1:]:
        x=a.intersection(b)
        for g in (x.geoms if hasattr(x,'geoms') else [x]):
            if g.geom_type=='Point': turns.append(g)
lifts=[box(*Ti(l['x']-l['w']/2,l['y']+l['h']/2),*Ti(l['x']+l['w']/2,l['y']-l['h']/2)) for l in RF['lifts']]
stairs=[box(*Ti(s['x'],s['y']+s['h']),*Ti(s['x']+s['w'],s['y'])) for s in RF['stairs']]
cols=[box(*Ti(c[0],c[1]+c[3]),*Ti(c[0]+c[2],c[1])) for c in RF['cols']]
entries=[Polygon([Ti(*q) for q in p]).buffer(0) for p in RF.get('dd',{}).get('entries',[]) if len(p)>=3]
support=unary_union([g for (lay,k,c,g) in raw if c=='support'])
KEEP=[('furniture and its use zone',unary_union([g.buffer(FURN_CLR*M,resolution=3) for g in FURNP])),
      ('existing planting',unary_union([l.buffer(300,resolution=4) for l in GREEN]+[p.buffer(600) for p,nm in plant_pts])),
      ('door swings',unary_union([l.buffer(DOOR_CLR*M,resolution=4) for l in DOORS])),
      ('escape routes',unary_union([r.buffer(ROUTE_CLR*M) for r in ROUTES])),
      ('corridor clear width',corr_narrow),
      ('sightlines at junctions',unary_union([p.buffer(TURN_CLR*M) for p in turns])),
      ('lifts, stairs and entrances',unary_union([g.buffer(1500) for g in lifts+stairs+entries])),
      ('columns and cores',unary_union([g.buffer(300) for g in cols]+[l.buffer(400) for l in lines_of('core')+lines_of('stair')])),
      ('services and support rooms',support.buffer(1000)),
      ('façade cleaning strip',FACADE.buffer(300))]
keep=unary_union([g for n,g in KEEP]).intersection(PLATE_P)
free=usable.difference(keep).buffer(-300).buffer(300,join_style=2)      # drop slivers narrower than 0.6 m
free=unary_union([h for h in parts(free) if h.area>0.5e6])
for s in spaces:
    g=SPG[s['id']]; s['keepM2']=round(g.intersection(keep).area/1e6,1); s['freeM2']=round(g.intersection(free).area/1e6,1)
print('usable %.0f m², keep-clear %.0f m², free %.0f m²'%(usable.area/1e6,keep.intersection(usable).area/1e6,free.area/1e6))

# ---------- candidates: free floor cut into planter-sized pieces ----------
TILE=5000
pieces=[]
for h in parts(free):
    if h.area<=12e6: pieces.append(h); continue
    x0,y0,x1,y1=h.bounds
    for gx in np.arange(x0,x1,TILE):
        for gy in np.arange(y0,y1,TILE):
            q=h.intersection(box(gx,gy,gx+TILE,gy+TILE))
            pieces+= [p for p in parts(q) if p.area>0.5e6]
# sightlines: viewpoints weighted by who looks from there
vp=[]
for s in spaces:
    g=SPG[s['id']]; lp=Point(Ti(*s['lab']))
    if s['k'] in ('reception','lobby'): vp.append((lp,3.0,'arrival'))
    elif s['k'] in ('cafe','pantry','collab','event'): vp.append((lp,2.0,'social'))
    elif s['c']=='collab': vp.append((lp,0.6,'meeting'))
for r in ROUTES:
    for d in np.arange(0,r.length,6000): vp.append((r.interpolate(d),1.0,'circulation'))
for p,n in desks[::3]: vp.append((p,0.25,'workstations'))
VPT=[v[0] for v in vp]; VW=np.array([v[1] for v in vp]); VK=[v[2] for v in vp]
wall_tree=STRtree(WALLS)
def vis(pt,reach=30000):
    """weighted count of viewpoints that can see pt (glass partitions are see-through)"""
    near=[i for i,v in enumerate(VPT) if 300<v.distance(pt)<reach]
    if not near: return 0.0,{}
    ls=[LineString([pt,VPT[i]]) for i in near]
    hit=wall_tree.query(ls,predicate='intersects')
    blocked=set(hit[0].tolist()) if len(hit) else set()
    seen=[near[j] for j in range(len(near)) if j not in blocked]
    by=collections.Counter(VK[i] for i in seen)
    return float(VW[seen].sum()) if seen else 0.0, dict(by)
sp_tree=STRtree([SPG[s['id']] for s in spaces]); SPI=[s['id'] for s in spaces]
nodes=[(p,'turn') for p in turns]+[(Point(Ti(*s['lab'])),s['k']) for s in spaces if s['k'] in ('reception','cafe','lobby')]
# where the café, receptions and lobbies open onto circulation: their outline where it meets a corridor or route
for s in spaces:
    if s['k'] in ('cafe','reception','lobby','collab','pantry','event'):
        b=SPG[s['id']].boundary.intersection(corr.buffer(600).union(unary_union([r.buffer(800) for r in ROUTES])))
        for g in (b.geoms if hasattr(b,'geoms') else [b]):
            if not g.is_empty and g.length>800: nodes.append((g.interpolate(0.5,normalized=True),s['k']+'-mouth'))
cands=[]
for h in pieces:
    p=polylabel(h,tolerance=100)
    if not h.contains(p): p=h.representative_point()
    r=h.exterior.distance(p)
    mrr=h.minimum_rotated_rectangle; cs=list(mrr.exterior.coords)
    e1=math.dist(cs[0],cs[1]); e2=math.dist(cs[1],cs[2])
    L,W=max(e1,e2),min(e1,e2); a,b=(cs[0],cs[1]) if e1>=e2 else (cs[1],cs[2])
    ang=math.degrees(math.atan2(-(b[1]-a[1]),b[0]-a[0]))        # plan y points down
    host=[SPI[i] for i in sp_tree.query(p,predicate='within')] or [SPI[i] for i in sp_tree.query(p.buffer(1500),predicate='intersects')]
    if not host: continue
    host=host[0]
    near=sorted({SPI[i] for i in sp_tree.query(h.buffer(1500),predicate='intersects')}-{host})
    walls=sum(1 for i in wall_tree.query(h.buffer(400),predicate='intersects'))
    v,vby=vis(p)
    nd=min((p.distance(n)/M,k) for n,k in nodes) if nodes else (99,'')
    # the long axis through the label point, clipped to the piece: where a linear planter would run
    dx,dy=math.cos(math.radians(ang)),-math.sin(math.radians(ang))
    axis=LineString([(p.x-dx*L,p.y-dy*L),(p.x+dx*L,p.y+dy*L)]).intersection(h)
    seg=max([g for g in (axis.geoms if hasattr(axis,'geoms') else [axis]) if g.geom_type=='LineString'],key=lambda g:g.length,default=None)
    c={'x':round(T(p.x,p.y)[0],1),'y':round(T(p.x,p.y)[1],1),'h':host,'nbr':near,'m2':round(h.area/1e6,2),'r':round(r/M,2),'L':round(L/M,2),'W':round(W/M,2),'ang':round(ang,1),
       'fd':round(FACADE.distance(p)/M,1),'walls':walls,'vis':round(v,2),'vby':vby,'node':round(nd[0],1),'nodek':nd[1],
       'ring':plan_ring(h,60)}
    if seg is not None and seg.length>600: c['seg']=[[round(v,1) for v in T(*q)] for q in (seg.coords[0],seg.coords[-1])]
    cands.append(c)
# visibility of each space: its candidates' mean, else a few samples inside it
for s in spaces:
    cs=[c['vis'] for c in cands if c['h']==s['id']]
    if not cs:
        g=SPG[s['id']]; pts=[Point(Ti(*s['lab']))]
        cs=[vis(q)[0] for q in pts]
    s['vis']=round(sum(cs)/len(cs),2)
print('candidates',len(cands),'in',len({c['h'] for c in cands}),'spaces')
# safety: no candidate label point may sit in the keep-clear mask
kp=prep(keep)
bad=[c for c in cands if kp.contains(Point(Ti(c['x'],c['y'])))]
assert not bad, ('candidates in the keep-clear mask',len(bad))
RF['gz']={'clear':CLEAR,'clearSrc':'drawing' if mw else 'default','planter':PLANTER,'doorClr':DOOR_CLR,'furnClr':FURN_CLR,'routeClr':ROUTE_CLR,
          'spaces':spaces,'cands':cands,'free':plan_rings(free,40),'keep':plan_rings(keep.intersection(usable.buffer(500)),60),
          'keepWhy':[[n,round(g.intersection(usable).area/1e6,1)] for n,g in KEEP],'usableM2':round(usable.area/1e6,1),'freeM2':round(free.area/1e6,1),
          'headcount':sum(d[2] for d in RF['desks']),'existing':len(plant_pts)+len(GCLUMP),
          'turns':[[round(v,1) for v in T(p.x,p.y)] for p in turns]}
json.dump(RF,open('realfit.json','w'),separators=(',',':'))
import os; print('realfit.json with gz',os.path.getsize('realfit.json'),'bytes; gz',len(json.dumps(RF['gz'],separators=(',',':'))))
