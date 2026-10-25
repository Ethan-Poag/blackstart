import pcbnew,sys,collections
from shapely.geometry import box,Point,LineString
TM=pcbnew.ToMM
def P(v):return (TM(v.x),TM(v.y))
b=pcbnew.LoadBoard(sys.argv[1]); LAYS=list(b.GetEnabledLayers().CuStack())
chg=[(l.split()[1],l.split()[2],l.split()[3]) for l in open(sys.argv[3]) if l.startswith('pad ') and len(l.split())>=5]
nets=b.GetNetsByName()
def geom(t):
    if t.GetClass()=="PCB_VIA": return Point(P(t.GetPosition())).buffer(TM(t.GetWidth(pcbnew.F_Cu))/2), LAYS
    return LineString([P(t.GetStart()),P(t.GetEnd())]).buffer(max(TM(t.GetWidth())/2,0.01)), [t.GetLayer()]
fps={f.GetReference():f for f in b.GetFootprints()}
tracks=list(b.GetTracks())
dele={}; relab=[]
for ref,num,old in chg:
    pad=[p for p in fps[ref].Pads() if p.GetNumber()==num][0]
    new=pad.GetNetname()
    if not nets.has_key(old): continue
    oc=nets[old].GetNetCode()
    cand=[(t,)+geom(t) for t in tracks if t.GetNetCode()==oc]
    bb=pad.GetBoundingBox(); pg=box(TM(bb.GetLeft()),TM(bb.GetTop()),TM(bb.GetRight()),TM(bb.GetBottom()))
    seen=set(); q=[]
    for k,(t,g,ls) in enumerate(cand):
        if g.intersects(pg) and any(pad.IsOnLayer(L) for L in ls): seen.add(k); q.append(k)
    while q:
        k=q.pop(); t,g,ls=cand[k]
        for j,(t2,g2,ls2) in enumerate(cand):
            if j not in seen and set(ls)&set(ls2) and g.intersects(g2): seen.add(j); q.append(j)
    isl=[cand[k] for k in seen]
    # other old-net pads touched
    others=[]
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetCode()!=oc: continue
            bb=p.GetBoundingBox(); g=box(TM(bb.GetLeft()),TM(bb.GetTop()),TM(bb.GetRight()),TM(bb.GetBottom()))
            if any(g.intersects(gi) and any(p.IsOnLayer(L) for L in ls) for _,gi,ls in isl): others.append(f.GetReference()+'.'+p.GetNumber())
    locked=sum(t.IsLocked() for t,_,_ in isl)
    act='relabel' if not others else 'delete'
    print(ref,num,old[-14:],'->',new[-16:],'island',len(isl),'locked',locked,'other old pads',others,act)
    for t,_,_ in isl:
        if act=='relabel': relab.append((t,pad.GetNet()))
        else: dele[t.m_Uuid.AsString()]=t
for t,n in relab: t.SetNet(n)
nd=0
for t in dele.values():
    if t.IsLocked(): print('  LOCKED item kept (needs manual check)',P(t.GetPosition()) if t.GetClass()=="PCB_VIA" else P(t.GetStart())); continue
    b.Remove(t); nd+=1
print('relabelled',len(relab),'deleted',nd)
b.Save(sys.argv[2])
