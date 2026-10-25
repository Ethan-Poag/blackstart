"""Fix the 36 DRC errors on genctl_v4_handrouted (see drc_handrouted.json).
python3 drcfix_v4.py in.kicad_pcb drc.json out.kicad_pcb"""
import sys, json, math, shutil, pcbnew
FM=pcbnew.FromMM; TM=lambda v: v/1e6
src, drcf, dst = sys.argv[1:4]
b = pcbnew.LoadBoard(src); d = json.load(open(drcf))
def item(u):
    x=b.GetItem(pcbnew.KIID(u)); return x.Cast() if x else None
def drag_fp(fp, dx, dy):
    """move footprint and drag track endpoints / vias that sit in its pads"""
    moved=set()
    pads=[(p, p.GetBoundingBox()) for p in fp.Pads()]
    for t in b.GetTracks():
        for p,bb in pads:
            if t.GetNetCode()!=p.GetNetCode(): continue
            if t.GetClass()=="PCB_VIA":
                continue
            if not p.IsOnLayer(t.GetLayer()): continue
            for end in ("Start","End"):
                pt=getattr(t,"Get"+end)()
                if bb.Contains(pt) and (id(t),end) not in moved:
                    getattr(t,"Set"+end)(pcbnew.VECTOR2I(pt.x+FM(dx),pt.y+FM(dy))); moved.add((id(t),end))
    fp.SetPosition(pcbnew.VECTOR2I(fp.GetPosition().x+FM(dx), fp.GetPosition().y+FM(dy)))
    return len(moved)
def segdist(p,a,c):
    ax,ay,cx,cy,px,py=a.x,a.y,c.x,c.y,p.x,p.y; L=(cx-ax)**2+(cy-ay)**2
    t=0 if L==0 else max(0,min(1,((px-ax)*(cx-ax)+(py-ay)*(cy-ay))/L))
    return ax+t*(cx-ax), ay+t*(cy-ay)
def nearest(it, p):
    if it.GetClass()=="PCB_TRACK": return segdist(p,it.GetStart(),it.GetEnd())
    q=it.GetPosition(); return q.x,q.y
def move_via(v, dx, dy):
    p=v.GetPosition(); n=0
    for t in b.GetTracks():
        if t.GetClass()=="PCB_VIA" or t.GetNetCode()!=v.GetNetCode(): continue
        for end in ("Start","End"):
            if getattr(t,"Get"+end)()==p:
                getattr(t,"Set"+end)(pcbnew.VECTOR2I(p.x+dx,p.y+dy)); n+=1
    v.SetPosition(pcbnew.VECTOR2I(p.x+dx,p.y+dy)); return n
def shift_track(t, dx, dy):
    for end in ("Start","End"):
        p=getattr(t,"Get"+end)()
        # skip endpoints anchored in a pad/via: stretch instead
        anchored=any(pd.GetNetCode()==t.GetNetCode() and pd.IsOnLayer(t.GetLayer()) and pd.GetBoundingBox().Contains(p) for fp in b.GetFootprints() for pd in fp.Pads() if fp.GetBoundingBox().Contains(p)) \
            or any(v.GetClass()=="PCB_VIA" and v.GetPosition()==p for v in b.GetTracks())
        if anchored: continue
        for o in b.GetTracks():
            if o is t or o.GetClass()=="PCB_VIA" or o.GetNetCode()!=t.GetNetCode() or o.GetLayer()!=t.GetLayer(): continue
            for e2 in ("Start","End"):
                if getattr(o,"Get"+e2)()==p: getattr(o,"Set"+e2)(pcbnew.VECTOR2I(p.x+dx,p.y+dy))
        getattr(t,"Set"+end)(pcbnew.VECTOR2I(p.x+dx,p.y+dy))
log=[]
# 1. Y4/C54 collision: slide C54 up 1.3 mm (its +3V3 track stretches to the existing via)
c54=b.FindFootprintByReference("C54"); log.append(("C54 up 1.3", drag_fp(c54,0,-1.3)))
# 2. HV 3 mm: R443 / R422
hv={"R443":(-0.35,0.15),"R422":(-0.45,0.0)}
for r,(dx,dy) in hv.items(): log.append((r,dx,dy,drag_fp(b.FindFootprintByReference(r),dx,dy)))
# 3. small clearances
for v in d["violations"]:
    if v["type"]!="clearance" or "3.0000" in v["description"]: continue
    req=float(v["description"].split("clearance ")[1].split(" mm")[0]); act=float(v["description"].split("actual ")[1].split(" mm")[0])
    k=FM(req-act+0.02)
    its=[item(i["uuid"]) for i in v["items"]]
    if any(x is None for x in its): log.append(("missing",v["description"])); continue
    vias=[x for x in its if x.GetClass()=="PCB_VIA"]; trks=[x for x in its if x.GetClass()=="PCB_TRACK"]
    if vias: mv=vias[0]; oth=[x for x in its if x is not mv][0]
    elif trks: mv=trks[0]; oth=[x for x in its if x is not mv][0]
    else: continue
    ref=mv.GetPosition() if mv.GetClass()=="PCB_VIA" else pcbnew.VECTOR2I(*[int(c) for c in segdist(oth.GetPosition(),mv.GetStart(),mv.GetEnd())])
    nx,ny=nearest(oth,ref) if oth.GetClass()=="PCB_TRACK" else (oth.GetPosition().x,oth.GetPosition().y)
    ux,uy=ref.x-nx,ref.y-ny; L=math.hypot(ux,uy) or 1
    dx,dy=int(k*ux/L),int(k*uy/L)
    if mv.GetClass()=="PCB_VIA": move_via(mv,dx,dy)
    else: shift_track(mv,dx,dy)
    log.append((mv.GetClass(),mv.GetNetname()[-12:],round(TM(dx),3),round(TM(dy),3)))
b.Save(dst)
# 4. restore U21 VIP board minimums lost when handroute rewrote the .pro
pe=json.load(open("genctl_v4_escaped.kicad_pro")); po=json.load(open(src.replace(".kicad_pcb",".kicad_pro")))
for kk in ("min_through_hole_diameter","min_via_annular_width","min_via_diameter"):
    po["board"]["design_settings"]["rules"][kk]=pe["board"]["design_settings"]["rules"][kk]
json.dump(po,open(dst.replace(".kicad_pcb",".kicad_pro"),"w"),indent=2)
shutil.copy(src.replace(".kicad_pcb",".kicad_dru"), dst.replace(".kicad_pcb",".kicad_dru")) if src!=dst else None
for l in log: print(l)
