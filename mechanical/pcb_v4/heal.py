import pcbnew,sys,math
TM=pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1])
ALL=list(b.GetTracks());seen=set();rm=0;dups=[]
for t in ALL:
    if t.GetClass()!='PCB_TRACK' or t.IsLocked(): continue
    k=(t.GetNetCode(),t.GetLayer(),t.GetWidth(),tuple(sorted([(t.GetStart().x,t.GetStart().y),(t.GetEnd().x,t.GetEnd().y)])))
    if k in seen: dups.append(t); rm+=1
    else: seen.add(k)
ts=[t for t in ALL if not any(t is d for d in dups)]
def anchored(t,e):
    for o in ts:
        if o is t or o.GetNetCode()!=t.GetNetCode(): continue
        if o.GetClass()=='PCB_VIA':
            if (o.GetPosition()-e).EuclideanNorm()<=o.GetWidth(pcbnew.F_Cu)//2: return True
        elif o.GetLayer()==t.GetLayer() and o.HitTest(e,0): return True
    for p in b.GetPads():
        if p.GetNetCode()==t.GetNetCode() and p.IsOnLayer(t.GetLayer()) and p.HitTest(e): return True
    return False
add=0;MAX=pcbnew.FromMM(0.45)
for t in [x for x in ts if x.GetClass()=='PCB_TRACK' and not x.IsLocked()]:
    for e in (t.GetStart(),t.GetEnd()):
        if anchored(t,e): continue
        best=None
        for o in ts:
            if o is t or o.GetNetCode()!=t.GetNetCode(): continue
            if o.GetClass()=='PCB_VIA': cands=[o.GetPosition()]
            elif o.GetLayer()==t.GetLayer(): cands=[o.GetStart(),o.GetEnd()]
            else: continue
            for c in cands:
                d=(c-e).EuclideanNorm()
                if 0<d<=MAX and (best is None or d<best[0]): best=(d,c)
        if best:
            n=pcbnew.PCB_TRACK(b);n.SetStart(e);n.SetEnd(best[1]);n.SetWidth(t.GetWidth());n.SetLayer(t.GetLayer());n.SetNetCode(t.GetNetCode());b.Add(n);ts.append(n);add+=1
print('dups removed',rm,'bridges added',add)
for d in dups: b.Remove(d)
b.Save(sys.argv[2])
