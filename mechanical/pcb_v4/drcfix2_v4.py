"""Second DRC pass: HV tap resistors, ADE_CS1_N exit from U7.28, refill zones.  python3 drcfix2_v4.py in out"""
import sys, pcbnew
sys.argv_=sys.argv; import importlib
FM=pcbnew.FromMM; P=lambda x,y: pcbnew.VECTOR2I(FM(x),FM(y))
src,dst=sys.argv[1:3]; b=pcbnew.LoadBoard(src)
def drag_fp(fp, dx, dy):
    n=0
    for p in fp.Pads():
        bb=p.GetBoundingBox(); bb.Inflate(FM(0.05))
        for t in b.GetTracks():
            if t.GetClass()=="PCB_VIA" or t.GetNetCode()!=p.GetNetCode() or not p.IsOnLayer(t.GetLayer()): continue
            for e in ("Start","End"):
                q=getattr(t,"Get"+e)()
                if bb.Contains(q): getattr(t,"Set"+e)(pcbnew.VECTOR2I(q.x+FM(dx),q.y+FM(dy))); n+=1
    fp.SetPosition(pcbnew.VECTOR2I(fp.GetPosition().x+FM(dx),fp.GetPosition().y+FM(dy))); return n
for r,dx,dy in (("R443",0.35,-0.15),("R439",0,-0.4),("R425",0,0.15)):
    print(r,drag_fp(b.FindFootprintByReference(r),dx,dy))
u7=b.FindFootprintByReference("U7"); p28=[p for p in u7.Pads() if p.GetNumber()=="28"][0]
net=p28.GetNet(); print("U7.28", p28.GetNetname(), p28.GetPosition().x/1e6, p28.GetPosition().y/1e6)
assert p28.GetNetname().endswith("ADE_CS1_N")
dead=[t for t in b.GetTracks() if t.GetClass()=="PCB_TRACK" and t.GetNetCode()==net.GetNetCode() and t.GetLayer()==pcbnew.B_Cu
      and 159.6<min(t.GetStart().x,t.GetEnd().x)/1e6 and max(t.GetStart().y,t.GetEnd().y)/1e6<73.45 and max(t.GetStart().x,t.GetEnd().x)/1e6<159.95]
print("del",len(dead))
for t in dead: b.Delete(t)
x=p28.GetPosition().x/1e6
for a,c in (((x,73.105),(x,73.6)),((x,73.6),(159.85,73.6)),((159.85,73.6),(159.655,73.405))):
    t=pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(FM(0.15)); t.SetLayer(pcbnew.B_Cu); t.SetNet(net); b.Add(t)
b.Save(dst)
b=pcbnew.LoadBoard(dst); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(dst)
b.BuildConnectivity(); print("unconnected", b.GetConnectivity().GetUnconnectedCount(True))
