# Flatten the test-fit DXF once into a pickle: every drawable entity as a world-space polyline (mm),
# tagged with its layer and the chain of block inserts it came from, plus every insert and text.
# Usage: python3 dxf_dump.py layout.dxf dump.pkl
import sys, time, pickle, math, collections
import ezdxf
from ezdxf import path as zpath
t0=time.time()
doc=ezdxf.readfile(sys.argv[1]); print('load %.0fs'%(time.time()-t0))
msp=doc.modelspace()
SKIP={'HATCH','SOLID','WIPEOUT','DIMENSION','ATTDEF','POINT','VIEWPORT','IMAGE','3DFACE','MESH','3DSOLID','REGION','BODY','LEADER','MLEADER','OLE2FRAME','ACAD_TABLE','SEQEND','VERTEX'}
paths=[]; inserts=[]; texts=[]; skipped=collections.Counter()
def emit(e, chain):
    t=e.dxftype()
    if t in ('TEXT','MTEXT','ATTRIB'):
        try:
            p=e.dxf.insert; texts.append((e.dxf.layer,chain,p.x,p.y,e.plain_text() if t=='MTEXT' else e.dxf.text))
        except Exception: skipped['text']+=1
        return
    if t in SKIP: skipped[t]+=1; return
    try: p=zpath.make_path(e)
    except Exception: skipped['nopath:'+t]+=1; return
    for sp in (p.sub_paths() if p.has_sub_paths else [p]):
        pts=[(round(q.x),round(q.y)) for q in sp.flattening(distance=15)]
        if len(pts)>=2: paths.append((e.dxf.layer,t,chain,pts))
def walk(ins, chain, depth):
    iid=len(inserts)
    p=ins.dxf.insert
    inserts.append((iid,ins.dxf.name,ins.dxf.layer,chain,p.x,p.y,ins.dxf.get('rotation',0) or 0,ins.dxf.get('xscale',1),ins.dxf.get('yscale',1)))
    ch=chain+((iid,ins.dxf.name),)
    try: ents=list(ins.virtual_entities())
    except Exception as ex: skipped['virt:'+ins.dxf.name[:30]]+=1; return
    for v in ents:
        if v.dxftype()=='INSERT':
            if depth<6: walk(v, ch, depth+1)
        else: emit(v, ch)
    for a in getattr(ins,'attribs',[]): emit(a, ch)
t0=time.time()
for e in msp:
    if e.dxftype()=='INSERT': walk(e, (), 0)
    else: emit(e, ())
print('walk %.0fs: %d paths, %d inserts, %d texts'%(time.time()-t0,len(paths),len(inserts),len(texts)), skipped.most_common(10))
pickle.dump({'paths':paths,'inserts':inserts,'texts':texts},open(sys.argv[2],'wb'),protocol=4)
