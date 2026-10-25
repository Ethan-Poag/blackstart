import pcbnew,sys,collections
from shapely.geometry import box,Point,LineString,Polygon
from shapely.strtree import STRtree
TM=pcbnew.ToMM
def P(v):return (TM(v.x),TM(v.y))
def analyze(b,detail=False):
    LAYS=list(b.GetEnabledLayers().CuStack())
    items=[];geo=collections.defaultdict(list)  # per (net,layer)
    def add(i,n,L,g):geo[(n,L)].append((g,i))
    for f in b.GetFootprints():
        for p in f.Pads():
            n=p.GetNetCode()
            if n<=0:continue
            i=len(items);items.append(("pad",n,f.GetReference()+"."+p.GetNumber(),P(p.GetPosition())))
            bb=p.GetBoundingBox();g=box(TM(bb.GetLeft()),TM(bb.GetTop()),TM(bb.GetRight()),TM(bb.GetBottom()))
            for L in LAYS:
                if p.IsOnLayer(L):add(i,n,L,g)
    for t in b.GetTracks():
        n=t.GetNetCode()
        if n<=0:continue
        i=len(items)
        if t.GetClass()=="PCB_VIA":
            items.append(("via",n,"",P(t.GetPosition())));g=Point(P(t.GetPosition())).buffer(TM(t.GetWidth(pcbnew.F_Cu))/2)
            for L in LAYS:add(i,n,L,g)
        else:
            items.append(("trk",n,"",P(t.GetStart())));add(i,n,t.GetLayer(),LineString([P(t.GetStart()),P(t.GetEnd())]).buffer(max(TM(t.GetWidth())/2,0.01)))
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetCode()<=0:continue
        for L in LAYS:
            if not z.IsOnLayer(L):continue
            ps=z.GetFilledPolysList(L)
            for k in range(ps.OutlineCount()):
                o=ps.Outline(k);pts=[P(o.CPoint(j)) for j in range(o.PointCount())]
                if len(pts)<3:continue
                hs=[]
                for h in range(ps.HoleCount(k)):
                    hh=ps.Hole(k,h);hs.append([P(hh.CPoint(j)) for j in range(hh.PointCount())])
                g=Polygon(pts,hs).buffer(0)
                i=len(items);items.append(("zone",z.GetNetCode(),z.GetNetname(),pts[0]));add(i,z.GetNetCode(),L,g)
    par=list(range(len(items)))
    def fd(x):
        while par[x]!=x:par[x]=par[par[x]];x=par[x]
        return x
    for key,l in geo.items():
        gs=[g for g,_ in l];tr=STRtree(gs)
        for a,(g,i) in enumerate(l):
            for j in tr.query(g,predicate="intersects"):
                ra,rb=fd(i),fd(l[j][1])
                if ra!=rb:par[ra]=rb
    comps=collections.defaultdict(set)
    for i,it in enumerate(items):
        if it[0]=="pad":comps[it[1]].add(fd(i))
    names={c:n.GetNetname() for c,n in b.GetNetsByNetcode().items()}
    per={names[n]:len(s)-1 for n,s in comps.items() if len(s)>1}
    return per,items,fd
if __name__=="__main__":
    b=pcbnew.LoadBoard(sys.argv[1]);per,_,_=analyze(b)
    b.BuildConnectivity();print("uf sum",sum(per.values()),"kicad",b.GetConnectivity().GetUnconnectedCount(True))
    for n,k in sorted(per.items(),key=lambda x:-x[1])[:int(sys.argv[2]) if len(sys.argv)>2 else 20]:print(k,n[-50:])
