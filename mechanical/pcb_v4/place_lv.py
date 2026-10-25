#!/usr/bin/env python3
"""Milestone 6 LV passive re-placement (most-constrained-first, connectivity-weighted).
usage: place_lv.py in.kicad_pcb out.kicad_pcb
Moves R/C/FB outside the 600 V box + barrier (x>=74.5) to their owner pin. Owner = schematic-nearest
non-passive sharing a net (decap -> owner's pin on that supply). Owners processed power stages -> MCU U7 ->
bridge U21 -> rest; within an owner, decaps first (small value first), then the rest.
Legality (shapely): courtyard vs courtyards on that side (THT both), pads (+0.2) vs foreign copper on that
layer and all vias, kofp rule areas, x<74.5 forbidden, 1 mm from edge. Only UNLOCKED copper of moved parts is ripped up."""
import sys,re,math,os,collections,pcbnew
from shapely.geometry import box,Point,LineString
from shapely.strtree import STRtree
from shapely.ops import unary_union
MM=pcbnew.FromMM;TM=pcbnew.ToMM
REPO="/workspace/genctl/kicad/genctl"
b=pcbnew.LoadBoard(sys.argv[1])
PW=re.compile(r"^(GND.*|\+.*|VBAT.*|CM5_3V3|CM5_5V|.*VISO.*|VDDA|CHASSIS|DSI83_VCORE|SC_TOP|.*VCC.*)$")
SMALL=re.compile(r"^(R|C|FB)\d+$")
LVX=74.5
fps={f.GetReference():f for f in b.GetFootprints()}
def P(v):return (TM(v.x),TM(v.y))
# schematic positions for ownership
sp={}
for fn in os.listdir(REPO):
    if not fn.endswith(".kicad_sch"):continue
    t=open(os.path.join(REPO,fn)).read()
    for m in re.finditer(r'\(symbol\s*\(lib_id "[^"]+"\)\s*\(at ([-\d.]+) ([-\d.]+)[^\n]*\n(?:[^\n]*\n){0,12}?\s*\(property "Reference" "([^"]+)"',t):
        sp.setdefault(m.group(3),(fn,float(m.group(1)),float(m.group(2))))
print("sch refs",len(sp))
locked_pads=set()
tracks=list(b.GetTracks())
padat=collections.defaultdict(list)
for f in fps.values():
    for p in f.Pads(): padat[p.GetNetname()].append((f.GetReference(),p))
def touches(t,p):
    pts=[t.GetStart(),t.GetEnd()] if t.GetClass()!="PCB_VIA" else [t.GetPosition()]
    return any(p.HitTest(q) for q in pts) and (t.GetClass()=="PCB_VIA" or p.IsOnLayer(t.GetLayer()))
# movable
def audit_d(f):
    best=None
    for p in f.Pads():
        n=p.GetNetname()
        if not n or n.startswith("GND"):continue
        for r2,p2 in padat[n]:
            if r2==f.GetReference() or SMALL.match(r2):continue
            d=math.dist(P(p.GetPosition()),P(p2.GetPosition()))
            if best is None or d<best[0]:best=(d,n,r2,p2)
    return best
cand={}
for r,f in fps.items():
    if not SMALL.match(r):continue
    x,y=P(f.GetPosition())
    if x<LVX:continue
    if f.IsLocked():continue
    a=audit_d(f)
    if a is None:continue
    ispw=bool(PW.match(a[1])) and r.startswith("C")
    lim=2.5 if ispw else 4.0
    if a[0]<=lim:continue
    # parts with locked (critical hand-routed) copper stay
    if any(t.IsLocked() and any(t.GetNetCode()==p.GetNetCode() and touches(t,p) for p in f.Pads()) for t in tracks if t.GetNetCode() in {p.GetNetCode() for p in f.Pads()}):continue
    cand[r]=ispw
print("movable",len(cand),"power",sum(cand.values()))
# owner + target pad
def nonsmall_on(n): return [(r2,p2) for r2,p2 in padat[n] if not SMALL.match(r2)]
load=collections.Counter()
plan={}
for r,ispw in cand.items():
    f=fps[r];opts=[]
    for p in f.Pads():
        n=p.GetNetname()
        if not n or n.startswith("GND"):continue
        for r2,p2 in nonsmall_on(n):
            if r2.startswith(("J","H","SW","TP")) and not ispw and len(nonsmall_on(n))>1 and not all(x[0].startswith(("J","SW")) for x in nonsmall_on(n)):pass
            sd=1e3
            if r in sp and r2 in sp and sp[r][0]==sp[r2][0]: sd=math.dist(sp[r][1:],sp[r2][1:])
            if ispw and not r2.startswith(('U','L')): sd+=500
            if ispw and r2.startswith('L') and fps[r].GetValue() in ('22u','47u','10u','100u'): sd-=400
            opts.append((sd,r2,p2,p.GetNumber()))
    if not opts:continue
    opts.sort(key=lambda o:o[0])
    sd,r2,_,mypad=opts[0]
    # among owner's pads on that net pick least loaded / closest to owner pad set
    same=[o for o in opts if o[1]==r2]
    same.sort(key=lambda o:(load[(r2,o[2].GetNumber())],o[0]))
    o=same[0];load[(r2,o[2].GetNumber())]+=1
    plan[r]=(r2,o[2],o[3],ispw)
def stage(owner):
    f=fps[owner];sh=f.GetSheetname().lower()
    if owner=="U7":return 1
    if owner=="U21":return 2
    if re.match(r"^(U|L|Q)",owner) and ("power" in sh or any(PW.match(p.GetNetname()) and p.GetNetname() not in("GND",) for p in f.Pads()) and "buck" in (f.GetValue()+sh).lower()):return 0
    if "power" in sh:return 0
    return 3
def val(r):
    v=fps[r].GetValue().lower();m=re.match(r"([\d.]+)\s*([pnuµm]?)",v)
    if not m:return 1
    return float(m.group(1))*{"p":1e-12,"n":1e-9,"u":1e-6,"µ":1e-6,"m":1e-3,"":1}[m.group(2)]
order=sorted(plan,key=lambda r:(stage(plan[r][0]),plan[r][0],0 if plan[r][3] else 1,val(r)))
# ---- rip up unlocked copper of movable parts, prune dangling
mv=set(order)
def rip():
    rm=[]
    pads=[p for r in mv for p in fps[r].Pads()]
    for t in b.GetTracks():
        if t.IsLocked() or t.GetClass()=="PCB_VIA":continue
        if any(t.GetNetCode()==p.GetNetCode() and touches(t,p) for p in pads if p.GetNetCode()>0 and abs(TM(p.GetPosition().x-t.GetStart().x))<15): rm.append(t)
    for t in rm:b.Delete(t)
    # prune unlocked dangling segments/vias iteratively
    for it in range(30):
        allp=[(p,p.GetNetCode()) for f in b.GetFootprints() for p in f.Pads()]
        ends=collections.Counter()
        tl=list(b.GetTracks())
        for t in tl:
            if t.GetClass()=="PCB_VIA":ends[(t.GetNetCode(),t.GetPosition().x,t.GetPosition().y,"v")]+=0
        idx=collections.defaultdict(list)
        for t in tl:
            if t.GetClass()=="PCB_VIA":idx[t.GetNetCode()].append(("v",t))
            else: idx[t.GetNetCode()].append(("t",t))
        padsby=collections.defaultdict(list)
        for p,c in allp: padsby[c].append(p)
        kill=[]
        for t in tl:
            if t.IsLocked() or t.GetClass()=="PCB_VIA":continue
            c=t.GetNetCode()
            for e in (t.GetStart(),t.GetEnd()):
                ok=any(p.HitTest(e) and p.IsOnLayer(t.GetLayer()) for p in padsby[c])
                if not ok:
                    for k,o in idx[c]:
                        if o is t:continue
                        if k=="v" and o.HitTest(e):ok=True;break
                        if k=="t" and o.GetLayer()==t.GetLayer() and (o.GetStart()==e or o.GetEnd()==e or o.HitTest(e,0)):ok=True;break
                if not ok:kill.append(t);break
        for t in tl:
            if t.IsLocked() or t.GetClass()!="PCB_VIA":continue
            c=t.GetNetCode();pos=t.GetPosition()
            if not any(k=="t" and (o.GetStart()==pos or o.GetEnd()==pos) for k,o in idx[c]) and not any(p.HitTest(pos) for p in padsby[c]):kill.append(t)
        if not kill:break
        for t in kill:b.Delete(t)
    return len(rm)
print("ripped",rip())
# ---- obstacles
CL=0.2
def fp_rects(f,lay):
    cy=f.GetCourtyard(lay)
    if cy.OutlineCount()==0:
        bb=f.GetBoundingBox(False);return box(TM(bb.GetLeft()),TM(bb.GetTop()),TM(bb.GetRight()),TM(bb.GetBottom()))
    bb=cy.BBox();return box(TM(bb.GetLeft()),TM(bb.GetTop()),TM(bb.GetRight()),TM(bb.GetBottom()))
def is_tht(f):return any(p.GetAttribute()==pcbnew.PAD_ATTRIB_PTH for p in f.Pads())
side_of=lambda f:"B" if f.GetLayer()==pcbnew.B_Cu else "F"
crt={"F":[],"B":[]}
for r,f in fps.items():
    if r in mv:continue
    s=side_of(f);g=fp_rects(f,pcbnew.B_CrtYd if s=="B" else pcbnew.F_CrtYd)
    crt[s].append(g)
    if is_tht(f):crt["B" if s=="F" else "F"].append(g)
cu={"F":[],"B":[]};cun={"F":[],"B":[]}
def addcu(s,g,n):cu[s].append(g);cun[s].append(n)
for t in b.GetTracks():
    if t.GetClass()=="PCB_VIA":
        g=Point(P(t.GetPosition())).buffer(TM(t.GetWidth(pcbnew.F_Cu))/2)
        addcu("F",g,t.GetNetCode());addcu("B",g,t.GetNetCode())
    else:
        L=t.GetLayer()
        if L not in(pcbnew.F_Cu,pcbnew.B_Cu):continue
        g=LineString([P(t.GetStart()),P(t.GetEnd())]).buffer(TM(t.GetWidth())/2)
        addcu("F" if L==pcbnew.F_Cu else "B",g,t.GetNetCode())
for r,f in fps.items():
    if r in mv:continue
    for p in f.Pads():
        bb=p.GetBoundingBox();g=box(TM(bb.GetLeft()),TM(bb.GetTop()),TM(bb.GetRight()),TM(bb.GetBottom()))
        for s,L in (("F",pcbnew.F_Cu),("B",pcbnew.B_Cu)):
            if p.IsOnLayer(L):addcu(s,g,p.GetNetCode())
ko={"F":[],"B":[]}
for z in b.Zones():
    if z.GetIsRuleArea() and z.GetDoNotAllowFootprints():
        bb=z.GetBoundingBox();g=box(TM(bb.GetLeft()),TM(bb.GetTop()),TM(bb.GetRight()),TM(bb.GetBottom()))
        for s,L in (("F",pcbnew.F_Cu),("B",pcbnew.B_Cu)):
            if z.IsOnLayer(L):ko[s].append(g)
bb=b.GetBoardEdgesBoundingBox();BX=(TM(bb.GetLeft())+1,TM(bb.GetTop())+1,TM(bb.GetRight())-1,TM(bb.GetBottom())-1)
edge=b.GetBoardEdgesBoundingBox()
outline=pcbnew.SHAPE_POLY_SET();b.GetBoardPolygonOutlines(outline)
trees={}
def build():
    for s in "FB":trees[s]=(STRtree(crt[s]),STRtree(cu[s]),STRtree(ko[s]) if ko[s] else None)
build()
def local(f):
    rot=f.GetOrientationDegrees();pos=f.GetPosition();f.SetOrientationDegrees(0)
    L=pcbnew.B_CrtYd if side_of(f)=="B" else pcbnew.F_CrtYd
    cy=f.GetCourtyard(L);bb=cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False)
    c=P(pos);cr=(TM(bb.GetLeft())-c[0],TM(bb.GetTop())-c[1],TM(bb.GetRight())-c[0],TM(bb.GetBottom())-c[1])
    pads=[]
    for p in f.Pads():
        pb=p.GetBoundingBox();q=P(p.GetPosition())
        pads.append((p.GetNumber(),q[0]-c[0],q[1]-c[1],TM(pb.GetWidth())/2,TM(pb.GetHeight())/2,p.GetNetCode()))
    f.SetOrientationDegrees(rot);return cr,pads
def rot(x,y,a):
    c,s=math.cos(math.radians(a)),math.sin(math.radians(a));return x*c+y*s,-x*s+y*c
def shapes(cr,pads,x,y,a):
    xs=[];ys=[]
    for px,py in ((cr[0],cr[1]),(cr[2],cr[1]),(cr[0],cr[3]),(cr[2],cr[3])):
        u,v=rot(px,py,a);xs.append(u+x);ys.append(v+y)
    crt_=box(min(xs),min(ys),max(xs),max(ys))
    ps=[]
    for (num,px,py,hw,hh,nc) in pads:
        u,v=rot(px,py,a);w,h=(hw,hh) if a%180==0 else (hh,hw)
        ps.append((num,u+x,v+y,box(u+x-w,v+y-h,u+x+w,v+y+h),nc))
    return crt_,ps
def legal(s,crt_,ps):
    if crt_.bounds[0]<LVX or crt_.bounds[0]<BX[0] or crt_.bounds[1]<BX[1] or crt_.bounds[2]>BX[2] or crt_.bounds[3]>BX[3]:return False
    for corner in ((crt_.bounds[0],crt_.bounds[1]),(crt_.bounds[2],crt_.bounds[3]),(crt_.bounds[0],crt_.bounds[3]),(crt_.bounds[2],crt_.bounds[1])):
        if not outline.Contains(pcbnew.VECTOR2I(MM(corner[0]),MM(corner[1]))):return False
    T=trees[s]
    if len(T[0].query(crt_,predicate="intersects")):return False
    if T[2] is not None and len(T[2].query(crt_,predicate="intersects")):return False
    for (num,x,y,g,nc) in ps:
        for i in T[1].query(g.buffer(CL),predicate="intersects"):
            if cun[s][i]!=nc or nc==0:return False
    return True
report=[];moved=0
for r in order:
    f=fps[r];owner,tp,mypad,ispw=plan[r];s=side_of(f)
    cr,pads=local(f);tx,ty=P(tp.GetPosition())
    before=audit_d(f)[0]
    best=None
    step=0.25;R=0
    while R<=(25.0 if fps[r].GetValue() in ('22u','47u','100u','10u') or not ispw else 14.0) and best is None:
        ring=[]
        n=max(1,int(2*math.pi*R/step)) if R>0 else 1
        for k in range(n):
            ang=2*math.pi*k/n;ring.append((tx+R*math.cos(ang),ty+R*math.sin(ang)))
        for (x,y) in ring:
            for a in (0,90,180,270):
                c_,ps=shapes(cr,pads,x,y,a)
                d=min(math.dist((px,py),(tx,ty)) for (num,px,py,g,nc) in ps if num==mypad)
                if best is not None and d>=best[0]:continue
                if legal(s,c_,ps):best=(d,x,y,a,c_,ps)
        R+=step
    if best is None or best[0]>=before-0.3:
        report.append((r,owner,round(before,1),"kept" if best is None else "kept(no gain)"))
        # put it back as an obstacle
        c_,ps=shapes(cr,pads,*P(f.GetPosition()),f.GetOrientationDegrees());crt[s].append(c_)
        for (_,_,_,g,nc) in ps:addcu(s,g,nc)
        build();continue
    d,x,y,a,c_,ps=best
    f.SetPosition(pcbnew.VECTOR2I(MM(x),MM(y)));f.SetOrientationDegrees(a)
    # verify pad formula
    real={p.GetNumber():P(p.GetPosition()) for p in f.Pads()}
    for (num,px,py,g,nc) in ps:
        assert math.dist(real[num],(px,py))<0.01,(r,num,real[num],px,py)
    crt[s].append(c_)
    for (_,_,_,g,nc) in ps:addcu(s,g,nc)
    build();moved+=1
    report.append((r,owner,round(before,1),round(d,1)))
b.Save(sys.argv[2])
print("moved",moved)
import json;json.dump(report,open(sys.argv[2]+".place.json","w"))
for x in report[:15]:print(x)
