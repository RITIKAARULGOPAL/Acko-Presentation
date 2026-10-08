import json, re
from shapely.geometry import LineString, Polygon, MultiLineString
from shapely.ops import polygonize, unary_union
D=json.load(open('dxf_mid.json'))
def paths(layer):
    out=[]
    for d in D['layers'].get(layer,[]):
        nums=list(map(int,re.findall(r'-?\d+',d)))
        pts=[(nums[i],-nums[i+1]) for i in range(0,len(nums),2)]
        out.append(pts)
    return out
Z=json.load(open('zones.json'))
import math
def qarc(p0,c,p1,n=8):
    return [((1-t)**2*p0[0]+2*(1-t)*t*c[0]+t*t*p1[0], (1-t)**2*p0[1]+2*(1-t)*t*c[1]+t*t*p1[1]) for t in [i/n for i in range(1,n)]]
PLATE=[(-168520,-375779),(68098,-375779),(68098,-409079),(-1602,-409079),(-1602,-399528),(-27327,-399528),(-27327,-409079),(-82552,-409079),(-82552,-399528),(-108202,-399528),(-108202,-409079),(-144367,-409079),(-170714,-380825)]+qarc((-170714,-380825),(-174300,-376990),(-168520,-375779))
# the drawing's own glazing line (AC_GLAZING), when it has one, is the floor plate
_G=[p for p in paths('AC_GLAZING') if len(p)>=4]
if _G:
    PLATE=max(_G,key=lambda p:Polygon(p).buffer(0).area)
    if PLATE[0]==PLATE[-1]: PLATE=PLATE[:-1]
PLATE_P=Polygon(PLATE).buffer(0)
def zpoly(i):
    p=Z['zones'][i]; return Polygon(p).buffer(0)
