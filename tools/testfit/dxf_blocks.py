import sys, collections, json
import ezdxf
from ezdxf import bbox
doc=ezdxf.readfile(sys.argv[1]); msp=doc.modelspace()
YMIN,YMAX=-418000,-368000
# count every INSERT at any depth inside the middle panel, with world position
cnt=collections.Counter(); pos=collections.defaultdict(list); lay=collections.defaultdict(collections.Counter)
def rec(ins, depth):
    for v in ins.virtual_entities():
        if v.dxftype()=='INSERT':
            p=v.dxf.insert
            cnt[(depth,v.dxf.name)]+=1
            if YMIN<p.y<YMAX: pos[v.dxf.name].append((round(p.x),round(p.y),round(v.dxf.rotation or 0)))
            lay[v.dxf.name][v.dxf.layer]+=1
            if depth<3: rec(v, depth+1)
for e in msp.query('INSERT'):
    p=e.dxf.insert
    if e.dxf.name in ('thh','gj'): continue
    cnt[(0,e.dxf.name)]+=1
    if YMIN<p.y<YMAX: pos[e.dxf.name].append((round(p.x),round(p.y),round(e.dxf.rotation or 0)))
    lay[e.dxf.name][e.dxf.layer]+=1
    if e.dxf.name!='base': rec(e,1)
sizes={}
for name in pos:
    blk=doc.blocks.get(name)
    try:
        b=bbox.extents(blk, fast=True); sizes[name]=(round(b.size.x),round(b.size.y))
    except Exception: sizes[name]=None
rows=sorted(pos.items(), key=lambda kv:-len(kv[1]))
for name,ps in rows[:70]:
    print('%-50s n=%-4d size=%-16s layers=%s'%(name[:50],len(ps),sizes.get(name),dict(lay[name].most_common(2))))
json.dump({k:v for k,v in pos.items()},open(sys.argv[2],'w'))
