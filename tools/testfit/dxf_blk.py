import sys, pickle, collections
import ezdxf
doc=ezdxf.readfile(sys.argv[1])
msp=doc.modelspace()
res={}
for name in ('thh','gj','base'):
    ins=[e for e in msp.query('INSERT') if e.dxf.name==name][0]
    ents=[]
    for v in ins.virtual_entities():
        t=v.dxftype()
        if t=='LWPOLYLINE':
            ents.append(('LWP',v.dxf.layer,v.closed,[(round(x),round(y)) for x,y,*_ in v.get_points()]))
        elif t=='POLYLINE':
            ents.append(('PL',v.dxf.layer,v.is_closed,[(round(p.x),round(p.y)) for p in v.points()]))
        elif t=='LINE':
            ents.append(('LINE',v.dxf.layer,False,[(round(v.dxf.start.x),round(v.dxf.start.y)),(round(v.dxf.end.x),round(v.dxf.end.y))]))
        elif t in ('MTEXT','TEXT'):
            ents.append(('TXT',v.dxf.layer,False,[(round(v.dxf.insert.x),round(v.dxf.insert.y))], v.plain_text() if t=='MTEXT' else v.dxf.text))
        else:
            ents.append((t,v.dxf.layer,False,[]))
    res[name]=ents
    c=collections.Counter((e[0],e[1]) for e in ents)
    print('==',name,len(ents),c.most_common(25))
texts=[]
for e in msp.query('MTEXT TEXT'):
    texts.append((e.dxf.layer,round(e.dxf.insert.x),round(e.dxf.insert.y),(e.plain_text() if e.dxftype()=='MTEXT' else e.dxf.text)))
res['texts']=texts
pickle.dump(res,open(sys.argv[2],'wb'))
for name in ('thh','gj'):
    for e in res[name]:
        if e[0] in('LWP','PL') : print(name,e[0],e[1],'closed' if e[2] else 'open',len(e[3]),e[3][:4])
        elif e[0]=='TXT': print(name,'TXT',e[1],e[3],e[4][:60])
