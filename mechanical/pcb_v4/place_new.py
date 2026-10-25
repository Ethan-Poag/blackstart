import pcbnew,sys,math
from shapely.geometry import box,Point,LineString,Polygon
from shapely.ops import unary_union
TM=pcbnew.ToMM;MM=pcbnew.FromMM
def P(v):return (TM(v.x),TM(v.y))
b=pcbnew.LoadBoard(sys.argv[1])
# (ref, anchor ref, anchor pad or None, side preference)
PLAN=[('U77','U21','H1'),('U78','U21','B1'),('U79','U21','J9'),('U80','R531','1'),
('R119','U21','H1'),('R120','U21','J1'),('R533','U21','B1'),('R113','U21','H2'),
('R532','U77','7'),('C287','U77','7'),('C288','U77','2'),('C289','U78','1'),('C290','U78','6'),('C291','U79','1'),('C292','U79','6'),('C293','U80','5')]
movers={r for r,_,_ in PLAN}
edge=None
segs=[]
for d in b.GetDrawings():
    if d.GetLayer()==pcbnew.Edge_Cuts: segs.append(d)
ol=pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ol)
o=ol.Outline(0); outline=Polygon([P(o.CPoint(i)) for i in range(o.PointCount())]).buffer(-0.6)
keep=[]
for z in b.Zones():
    if z.GetIsRuleArea():
        oo=z.Outline().Outline(0); keep.append((Polygon([P(oo.CPoint(i)) for i in range(oo.PointCount())]),z))
def crt(f,side):
    L=pcbnew.B_CrtYd if side else pcbnew.F_CrtYd
    s=f.GetCourtyard(L)
    if s.OutlineCount()==0:
        bb=f.GetBoundingBox(False); return box(TM(bb.GetLeft()),TM(bb.GetTop()),TM(bb.GetRight()),TM(bb.GetBottom()))
    oo=s.Outline(0); return Polygon([P(oo.CPoint(i)) for i in range(oo.PointCount())]).buffer(0)
def padg(p):
    s=p.GetEffectivePolygon(pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu)
    oo=s.Outline(0); return Polygon([P(oo.CPoint(i)) for i in range(oo.PointCount())]).buffer(0)
def obstacles():
    C={0:[],1:[]}; CU={pcbnew.F_Cu:[],pcbnew.B_Cu:[]}; TH=[]
    for f in b.GetFootprints():
        if f.GetReference() in movers and not placed.get(f.GetReference()): continue
        sd=1 if f.IsFlipped() else 0
        C[sd].append(crt(f,sd))
        for p in f.Pads():
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH,pcbnew.PAD_ATTRIB_NPTH):
                TH.append(Point(P(p.GetPosition())).buffer(TM(max(p.GetSize().x,p.GetSize().y))/2+0.3))
    for t in b.GetTracks():
        if t.GetClass()=="PCB_VIA":
            g=Point(P(t.GetPosition())).buffer(TM(t.GetWidth(pcbnew.F_Cu))/2)
            CU[pcbnew.F_Cu].append((g,t.GetNetCode()));CU[pcbnew.B_Cu].append((g,t.GetNetCode()))
        elif t.GetLayer() in CU:
            CU[t.GetLayer()].append((LineString([P(t.GetStart()),P(t.GetEnd())]).buffer(TM(t.GetWidth())/2),t.GetNetCode()))
    return C,CU,TH
placed={}
def legal(f,C,CU,TH):
    sd=1 if f.IsFlipped() else 0
    c=crt(f,sd)
    if not outline.contains(c): return False
    if c.bounds[0]<74.5: return False
    for kz,z in keep:
        if kz.intersects(c) and (z.GetDoNotAllowFootprints() or z.GetDoNotAllowPads()): return False
    if any(c.intersects(g) for g in C[sd]): return False
    if any(c.intersects(g) for g in TH): return False
    L=pcbnew.B_Cu if sd else pcbnew.F_Cu
    for p in f.Pads():
        pg=padg(p).buffer(0.2)
        for g,n in CU[L]:
            if n!=p.GetNetCode() and pg.intersects(g): return False
    return True
fps={f.GetReference():f for f in b.GetFootprints()}
for ref,aref,apad in PLAN:
    f=fps[ref]; a=fps[aref]
    tgt=[p for p in a.Pads() if p.GetNumber()==apad][0].GetPosition()
    tx,ty=P(tgt)
    C,CU,TH=obstacles()
    best=None
    sides=[1 if a.IsFlipped() else 0, 0 if a.IsFlipped() else 1]
    for sd in sides:
        if f.IsFlipped()!=bool(sd): f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_LEFT_RIGHT) if hasattr(pcbnew,'FLIP_DIRECTION_LEFT_RIGHT') else f.Flip(f.GetPosition(),False)
        for r in [x*0.25 for x in range(0,61)]:
            n=max(1,int(2*math.pi*r/0.5))
            for k in range(n):
                x=tx+r*math.cos(2*math.pi*k/n); y=ty+r*math.sin(2*math.pi*k/n)
                for ang in (0,90,180,270):
                    f.SetPosition(pcbnew.VECTOR2I_MM(x,y)); f.SetOrientationDegrees(ang)
                    if legal(f,C,CU,TH):
                        # cost: dist of the pad that shares net with anchor pin
                        best=(r+(0.0 if sd==sides[0] else 1.5),x,y,ang,sd); break
                if best: break
            if best: break
        if best and best[4]==sd: break
    if not best: print('FAIL',ref); continue
    _,x,y,ang,sd=best
    if f.IsFlipped()!=bool(sd): f.Flip(f.GetPosition(),False)
    f.SetPosition(pcbnew.VECTOR2I_MM(x,y)); f.SetOrientationDegrees(ang); placed[ref]=1
    print(ref,'->',round(x,2),round(y,2),ang,'B' if sd else 'F','dist',round(math.hypot(x-tx,y-ty),2))
b.Save(sys.argv[2])
