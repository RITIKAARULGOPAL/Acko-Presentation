# Flatten model space into per-layer SVG path data (DXF coords, mm), plus texts and insert records.
import sys, time, json, collections, math
import ezdxf
from ezdxf import disassemble, path as zpath
t=time.time()
doc=ezdxf.readfile(sys.argv[1]); print('load %.1fs'%(time.time()-t))
msp=doc.modelspace()
YMIN,YMAX=float(sys.argv[3]),float(sys.argv[4])
layers=collections.defaultdict(list)
texts=[]; inserts=[]
def keep(y): return YMIN<=y<=YMAX
# record top-level and nested inserts with their world position (for furniture counting)
def walk(entity, depth, owner_layer):
    pass
t=time.time()
n=0; skipped=collections.Counter()
for e in disassemble.recursive_decompose(msp):
    t_=e.dxftype()
    lay=e.dxf.layer
    if t_ in ('TEXT','MTEXT','ATTRIB'):
        try:
            p=e.dxf.insert
            if keep(p.y):
                txt=e.plain_text() if t_=='MTEXT' else e.dxf.text
                h=e.dxf.char_height if t_=='MTEXT' else e.dxf.height
                texts.append([lay,round(p.x),round(p.y),txt,round(h or 0),round(e.dxf.get('rotation',0) or 0,1)])
        except Exception as ex: skipped['text']+=1
        continue
    if t_ in ('HATCH','SOLID','WIPEOUT','DIMENSION','ATTDEF','POINT','VIEWPORT','IMAGE','3DFACE','MESH','3DSOLID','REGION','BODY','LEADER','MLEADER','OLE2FRAME','ACAD_TABLE'):
        skipped[t_]+=1; continue
    try:
        p=zpath.make_path(e)
    except Exception:
        skipped['nopath:'+t_]+=1; continue
    if not len(p) and not p.has_sub_paths:
        # could be a single point path
        pass
    pts=list(p.flattening(distance=20))
    if len(pts)<2: continue
    ys=[q.y for q in pts]
    if not keep(sum(ys)/len(ys)): continue
    d='M'+' L'.join('%d %d'%(round(q.x),round(-q.y)) for q in pts)
    layers[lay].append(d); n+=1
print('decompose %.1fs, %d paths'%(time.time()-t,n), skipped.most_common(12))
json.dump({'layers':layers,'texts':texts},open(sys.argv[2],'w'))
print({k:len(v) for k,v in sorted(layers.items(),key=lambda kv:-len(kv[1]))})
