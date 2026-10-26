"""M7 mover: move listed passives next to the pad they serve; rip up their unlocked copper.
usage: mover.py in out plan.txt   (plan lines: REF ANCHORREF ANCHORPAD)"""
import pcbnew,sys,math,json
from shapely.geometry import box,Point,LineString,Polygon
TM=pcbnew.ToMM
def P(v):return (TM(v.x),TM(v.y))
b=pcbnew.LoadBoard(sys.argv[1])
plan=[l.split() for l in open(sys.argv[3]) if l.strip() and not l.startswith('#')]
fps={f.GetReference():f for f in b.GetFootprints()}
ol=pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ol)
o=ol.Outline(0); outline=Polygon([P(o.CPoint(i)) for i in range(o.PointCount())]).buffer(-0.6)
keep=[]
for z in b.Zones():
    if z.GetIsRuleArea():
        oo=z.Outline().Outline(0); keep.append((Polygon([P(oo.CPoint(i)) for i in range(oo.PointCount())]),z))
ISO=box(-3,12,59.3,162)
def crt(f):
    s=f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    if s.OutlineCount()==0:
        bb=f.GetBoundingBox(False); return box(TM(bb.GetLeft()),TM(bb.GetTop()),TM(bb.GetRight()),TM(bb.GetBottom()))
    oo=s.Outline(0); return Polygon([P(oo.CPoint(i)) for i in range(oo.PointCount())]).buffer(0)
def padg(p,L):
    s=p.GetEffectivePolygon(L); oo=s.Outline(0); return Polygon([P(oo.CPoint(i)) for i in range(oo.PointCount())]).buffer(0)
nc={ni.GetNetCode():ni.GetNetClassName() for ni in b.GetNetsByName().values()}
movers={r[0] for r in plan}
import os;RIPLOCK=os.environ.get('RIPLOCK')=='1'
PLANE={ni.GetNetCode() for ni in b.GetNetsByName().values() if ni.GetNetname() in ('GND','GND_AC','+3V3_SAFE','+3V3_AC')}
def touching(f):
    """unlocked/locked tracks+vias touching pads of f (per own net)"""
    out=[]
    for p in f.Pads():
        if p.GetNetCode()<=0: continue
        for t in b.GetTracks():
            if t.GetNetCode()!=p.GetNetCode(): continue
            pts=[t.GetPosition()] if t.GetClass()=="PCB_VIA" else [t.GetStart(),t.GetEnd()]
            if any(p.HitTest(q) for q in pts): out.append(t)
    return out
def ripnet_from(f):
    """remove unlocked copper electrically reachable from f's pads (flood through unlocked items only, stop at other pads)"""
    rm={}
    for p in f.Pads():
        n=p.GetNetCode()
        if n<=0 or nc.get(n,'') in(): continue
        its=[t for t in b.GetTracks() if t.GetNetCode()==n and (RIPLOCK or not t.IsLocked())]
        if n in PLANE: continue
        others=[q for q in b.GetPads() if q.GetNetCode()==n and q.GetParentFootprint().GetReference()!=f.GetReference()]
        front=[p.GetPosition()];seen=set()
        while front:
            q=front.pop()
            for t in its:
                if t.m_Uuid.AsString() in seen: continue
                if t.GetClass()=="PCB_VIA": ends=[t.GetPosition()]; hit=(t.GetPosition()-q).EuclideanNorm()<t.GetWidth(pcbnew.F_Cu)//2+1000 or p.HitTest(t.GetPosition())
                else:
                    ends=[t.GetStart(),t.GetEnd()]
                    hit=any((e-q).EuclideanNorm()<max(t.GetWidth()//2,20000) for e in ends) or any(p.HitTest(e) for e in ends)
                if hit:
                    seen.add(t.m_Uuid.AsString()); rm[t.m_Uuid.AsString()]=t
                    for e in ends:
                        if not any(o2.HitTest(e) for o2 in others): front.append(e)
    return list(rm.values())
CRT={}
def crtc(f):
    r=f.GetReference()
    if r not in CRT: CRT[r]=crt(f)
    return CRT[r]
def obstacles(skip,rmids=()):
    C=[];CU={pcbnew.F_Cu:[],pcbnew.B_Cu:[]};TH=[]
    for f in list(fps.values()):
        if f.GetReference()==skip: continue
        C.append((f.IsFlipped(),crtc(f)))
        for p in f.Pads():
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH,pcbnew.PAD_ATTRIB_NPTH):
                TH.append(Point(P(p.GetPosition())).buffer(TM(max(p.GetSize().x,p.GetSize().y))/2+0.3))
            for L in CU:
                if p.IsOnLayer(L) and p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD: CU[L].append((padg(p,L),p.GetNetCode()))
    for t in b.GetTracks():
        if t.m_Uuid.AsString() in rmids: continue
        if t.GetClass()=="PCB_VIA":
            g=Point(P(t.GetPosition())).buffer(TM(t.GetWidth(pcbnew.F_Cu))/2)
            for L in CU: CU[L].append((g,t.GetNetCode()))
        elif t.GetLayer() in CU:
            CU[t.GetLayer()].append((LineString([P(t.GetStart()),P(t.GetEnd())]).buffer(TM(t.GetWidth())/2),t.GetNetCode()))
    return C,CU,TH
def legal(f,iso,C,CU,TH):
    c=crt(f); sd=f.IsFlipped()
    if not outline.contains(c): return False
    if iso and not ISO.contains(c): return False
    if not iso and (c.bounds[0]<73.6 and c.bounds[1]<175): return False
    for kz,z in keep:
        if kz.intersects(c) and (z.GetDoNotAllowFootprints() or z.GetDoNotAllowPads() or z.GetDoNotAllowTracks()): return False
    if any(s==sd and c.intersects(g) for s,g in C): return False
    if any(c.intersects(g) for g in TH): return False
    L=pcbnew.B_Cu if sd else pcbnew.F_Cu
    for p in f.Pads():
        hv=nc.get(p.GetNetCode(),'').startswith('HV')
        pg=padg(p,L).buffer(3.1 if hv else 0.2)
        for g,n in CU[L]:
            if n!=p.GetNetCode() and pg.intersects(g):
                return False
            if n!=p.GetNetCode() and nc.get(n,'').startswith('HV') and padg(p,L).buffer(3.1).intersects(g): return False
    return True
log=[]
for ref,aref,apad in plan:
    f=fps[ref];a=fps[aref]
    ap=[p for p in a.Pads() if p.GetNumber()==apad][0]
    net=ap.GetNetCode()
    mine=[p for p in f.Pads() if p.GetNetCode()==net]
    if not mine: log.append((ref,'SKIP no pad on anchor net')); print(ref,'no shared net'); continue
    if any(nc.get(p.GetNetCode(),'').startswith('HV') for p in f.Pads()): log.append((ref,'SKIP HV-class part')); print(ref,'HV part, not moved'); continue
    t0=touching(f)
    if any(t.IsLocked() for t in t0) and not RIPLOCK: log.append((ref,'SKIP locked copper on pad')); print(ref,'locked copper'); continue
    ox,oy=P(f.GetPosition()); oang=f.GetOrientationDegrees()
    iso=ox<60
    d0=math.hypot(*(TM(x) for x in (mine[0].GetPosition()-ap.GetPosition())))
    rm=ripnet_from(f)
    C,CU,TH=obstacles(ref,{t.m_Uuid.AsString() for t in rm})
    tx,ty=P(ap.GetPosition());best=None
    for r in [x*0.25 for x in range(2,81)]:
        n=max(8,int(2*math.pi*r/0.35))
        cands=[]
        for k in range(n):
            x=tx+r*math.cos(2*math.pi*k/n); y=ty+r*math.sin(2*math.pi*k/n)
            for ang in (0,90,180,270):
                f.SetPosition(pcbnew.VECTOR2I_MM(x,y)); f.SetOrientationDegrees(ang)
                dd=min(math.hypot(*(TM(v) for v in (q.GetPosition()-ap.GetPosition()))) for q in mine)
                cands.append((dd,x,y,ang))
        cands.sort()
        for dd,x,y,ang in cands[:60]:
            f.SetPosition(pcbnew.VECTOR2I_MM(x,y)); f.SetOrientationDegrees(ang)
            if legal(f,iso,C,CU,TH): best=(dd,x,y,ang);break
        if best: break
    if not best or best[0]>=d0:
        f.SetPosition(pcbnew.VECTOR2I_MM(ox,oy)); f.SetOrientationDegrees(oang)
        log.append((ref,'FAIL no legal spot',round(d0,1))); print(ref,'FAIL',round(d0,1)); continue
    f.SetPosition(pcbnew.VECTOR2I_MM(best[1],best[2])); f.SetOrientationDegrees(best[3])
    for t in rm: b.Delete(t)
    CRT.pop(ref,None)
    log.append((ref,aref,apad,round(d0,1),round(best[0],1),len(rm)))
    print(ref,'->',aref,apad,'%.1f -> %.1f mm, ripped %d'%(d0,best[0],len(rm)),flush=True)
b.Save(sys.argv[2]); json.dump(log,open(sys.argv[2]+'.move.json','w'))
