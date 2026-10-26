import pcbnew,sys
from shapely.geometry import LineString,Point,Polygon
T=pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1])
ct=[p for f in b.GetFootprints() if f.GetReference() in('T1','T2','T3','T4','J30') for p in f.Pads() if p.GetNetCode()>0]
ctn={p.GetNetCode() for p in ct}
res={}
for t in b.GetTracks():
  if t.GetNetCode() in ctn: continue
  n=t.GetNetname().split('/')[-1]
  if t.GetClass()=='PCB_VIA': g=Point(T(t.GetPosition().x),T(t.GetPosition().y)).buffer(T(t.GetWidth(pcbnew.F_Cu))/2); L='all'
  else: g=LineString([(T(t.GetStart().x),T(t.GetStart().y)),(T(t.GetEnd().x),T(t.GetEnd().y))]).buffer(T(t.GetWidth())/2); L=b.GetLayerName(t.GetLayer())
  for p in ct:
    if L!='all' and not p.IsOnLayer(t.GetLayer()): continue
    o=p.GetEffectivePolygon(pcbnew.B_Cu).Outline(0)
    d=g.distance(Polygon([(T(o.CPoint(i).x),T(o.CPoint(i).y)) for i in range(o.PointCount())]))
    k=(n,p.GetParentFootprint().GetReference()+'.'+p.GetNumber())
    if d<res.get(k,(99,))[0]: res[k]=(d,L,t.GetNetClassName())
for k,v in sorted(res.items(),key=lambda x:x[1][0])[:15]: print(round(v[0],3),k,v[1],v[2])
for n in ('BUS_VC_TAP','GEN_VC_P'): print(n,'min',round(min(v[0] for k,v in res.items() if k[0]==n),3))
