#!/usr/bin/env python3
"""M6 plane fan-out: SMD pads on GND / +3V3_SAFE in the LV area (x>=74.5) that are not yet connected to their
plane get a short stub + 0.4/0.2 via (0.3/0.15 inside the U21 courtyard is NOT used here). Checked with shapely
against ALL copper on every layer it crosses (clearance 0.2 mm) and via-forbidding rule areas.
usage: fanout_lv.py in out"""
import sys,math,collections,pcbnew
from shapely.geometry import box,Point,LineString
from shapely.strtree import STRtree
MM=pcbnew.FromMM;TM=pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1])
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();con=b.GetConnectivity()
PLANE={"GND":[pcbnew.In1_Cu,pcbnew.In4_Cu],"+3V3_SAFE":[pcbnew.In3_Cu]}
zones=[z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() in PLANE]
def P(v):return (TM(v.x),TM(v.y))
CL=0.2;VD=0.4
LAYS=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu]
geo={L:[] for L in LAYS};net={L:[] for L in LAYS}
def add(L,g,n):geo[L].append(g);net[L].append(n)
for t in b.GetTracks():
    if t.GetClass()=="PCB_VIA":
        g=Point(P(t.GetPosition())).buffer(TM(t.GetWidth(pcbnew.F_Cu))/2)
        for L in LAYS:add(L,g,t.GetNetCode())
    elif t.GetLayer() in geo:
        add(t.GetLayer(),LineString([P(t.GetStart()),P(t.GetEnd())]).buffer(TM(t.GetWidth())/2),t.GetNetCode())
for f in b.GetFootprints():
    for p in f.Pads():
        bb=p.GetBoundingBox();g=box(TM(bb.GetLeft()),TM(bb.GetTop()),TM(bb.GetRight()),TM(bb.GetBottom()))
        for L in LAYS:
            if p.IsOnLayer(L):add(L,g,p.GetNetCode())
        if p.GetDrillSize().x>0:
            for L in LAYS:add(L,g,p.GetNetCode())
holes=[P(t.GetPosition()) for t in b.GetTracks() if t.GetClass()=="PCB_VIA"]
holes+= [P(p.GetPosition()) for f in b.GetFootprints() for p in f.Pads() if p.GetDrillSize().x>0]
tree={L:STRtree(geo[L]) for L in LAYS}
extra={L:[] for L in LAYS}
kov=[z for z in b.Zones() if z.GetIsRuleArea() and (z.GetDoNotAllowVias() or z.GetDoNotAllowTracks())]
outline=pcbnew.SHAPE_POLY_SET();b.GetBoardPolygonOutlines(outline)
u21=b.FindFootprintByReference("U21").GetCourtyard(pcbnew.B_CrtYd).BBox()
def clear(L,g,nc):
    for i in tree[L].query(g.buffer(CL),predicate="intersects"):
        if net[L][i]!=nc:return False
    for (h,n) in extra[L]:
        if n!=nc and h.distance(g)<CL:return False
    return True
def plane_hit(nc,x,y):
    v=pcbnew.VECTOR2I(MM(x),MM(y))
    return any(z.GetNetCode()==nc and any(z.IsOnLayer(L) and z.HitTestFilledArea(L,v) for L in PLANE[z.GetNetname()]) for z in zones)
def via_ok(x,y,nc):
    if x<74.5:return False
    v=pcbnew.VECTOR2I(MM(x),MM(y))
    if not outline.Contains(v) or u21.Contains(v):return False
    if any(z.GetLayerSet().Contains(pcbnew.F_Cu) or True for z in kov if z.Outline().Contains(v)):return False
    if any(math.dist((x,y),h)<0.65 for h in holes):return False
    g=Point(x,y).buffer(VD/2)
    return all(clear(L,g,nc) for L in LAYS) and plane_hit(nc,x,y)
def island_has_via(p):
    seen={p.m_Uuid.AsString()};q=[p];k=0
    while q and k<300:
        it=q.pop();k+=1
        for t in con.GetConnectedTracks(it):
            u=t.m_Uuid.AsString()
            if u in seen:continue
            if t.GetClass()=="PCB_VIA":return True
            seen.add(u);q.append(t)
        for pp in con.GetConnectedPads(it):
            u=pp.m_Uuid.AsString()
            if u in seen:continue
            if pp.GetDrillSize().x>0:return True
            seen.add(u);q.append(pp)
    return False
added=0;skip=0;fail=[]
for f in b.GetFootprints():
    for p in f.Pads():
        n=p.GetNetname()
        if n not in PLANE or p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD:continue
        px,py=P(p.GetPosition())
        if px<74.5:continue
        if island_has_via(p):skip+=1;continue
        L=pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu
        nc=p.GetNetCode();bb=p.GetBoundingBox();hw,hh=TM(bb.GetWidth())/2,TM(bb.GetHeight())/2
        fx,fy=P(f.GetPosition());ox,oy=px-fx,py-fy;o=math.atan2(oy,ox) if (ox or oy) else 0
        done=False
        for da in (0,45,-45,90,-90,135,-135,180):
            a=o+math.radians(da);ux,uy=math.cos(a),math.sin(a)
            for ext in (0.45,0.6,0.8,1.0,1.3,1.6):
                r=max(hw*abs(ux),hh*abs(uy))+ext
                x,y=round(px+ux*r,3),round(py+uy*r,3)
                if not via_ok(x,y,nc):continue
                st=LineString([(px,py),(x,y)]).buffer(0.125)
                if not clear(L,st,nc):continue
                v=pcbnew.PCB_VIA(b);v.SetPosition(pcbnew.VECTOR2I(MM(x),MM(y)));v.SetWidth(MM(VD));v.SetDrill(MM(0.2));v.SetNetCode(nc);b.Add(v)
                t=pcbnew.PCB_TRACK(b);t.SetStart(p.GetPosition());t.SetEnd(v.GetPosition());t.SetWidth(MM(0.25));t.SetLayer(L);t.SetNetCode(nc);b.Add(t)
                vg=Point(x,y).buffer(VD/2)
                for LL in LAYS:extra[LL].append((vg,nc))
                extra[L].append((st,nc));holes.append((x,y));added+=1;done=True;break
            if done:break
        if not done:fail.append(f"{f.GetReference()}.{p.GetNumber()}")
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity()
print("fanout added",added,"already",skip,"failed",len(fail),fail[:40])
print("unconnected",b.GetConnectivity().GetUnconnectedCount(True))
b.Save(sys.argv[2])
