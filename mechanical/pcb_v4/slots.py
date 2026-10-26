"""Add 2.0 mm routed slots between adjacent J28/J29 pins (sheet sec.2 'J28/J29 headers'). Refuses if any copper crosses a slot.
usage: slots.py in out"""
import pcbnew,sys
from shapely.geometry import box,Point,LineString,Polygon
T=pcbnew.ToMM;FM=pcbnew.FromMM
b=pcbnew.LoadBoard(sys.argv[1])
rects=[]
for r in ('J28','J29'):
    f=b.FindFootprintByReference(r)
    ys=sorted({round(T(p.GetPosition().y),3) for p in f.Pads() if p.GetNumber()})
    for a,c in zip(ys,ys[1:]):
        m=(a+c)/2; rects.append((r,box(2.0,m-1.0,12.5,m+1.0)))
bad=0
for r,g in rects:
    hit=[]
    for t in b.GetTracks():
        if t.GetClass()=='PCB_VIA': gg=Point(T(t.GetPosition().x),T(t.GetPosition().y)).buffer(T(t.GetWidth(pcbnew.F_Cu))/2+0.3)
        else: gg=LineString([(T(t.GetStart().x),T(t.GetStart().y)),(T(t.GetEnd().x),T(t.GetEnd().y))]).buffer(T(t.GetWidth())/2+0.3)
        if gg.intersects(g): hit.append((t.GetNetname().split('/')[-1],b.GetLayerName(t.GetLayer()),t.IsLocked()))
    for f in b.GetFootprints():
        for p in f.Pads():
            if Point(T(p.GetPosition().x),T(p.GetPosition().y)).buffer(T(max(p.GetSize().x,p.GetSize().y))/2+0.3).intersects(g): hit.append((f.GetReference()+'.'+p.GetNumber(),'pad'))
    print(r,[round(x,2) for x in g.bounds],'conflicts',hit); bad+=bool(hit)
if len(sys.argv)>2 and not bad:
    for r,g in rects:
        x0,y0,x1,y1=g.bounds
        s=pcbnew.PCB_SHAPE(b);s.SetShape(pcbnew.SHAPE_T_RECT);s.SetLayer(pcbnew.Edge_Cuts);s.SetWidth(FM(0.05))
        s.SetStart(pcbnew.VECTOR2I(FM(x0),FM(y0)));s.SetEnd(pcbnew.VECTOR2I(FM(x1),FM(y1)));b.Add(s)
    b.Save(sys.argv[2]);print('slots added',len(rects))
