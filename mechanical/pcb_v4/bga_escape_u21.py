#!/usr/bin/env python3
"""Planned escape for U21 (SN65DSI83, nFBGA-64, 0.5 mm pitch).  Run before handroute_v4.

Why it is not 100 % dog-bone: ball sites are on a 0.5 mm lattice.  Any through via
(>= 0.35 mm) leaves < 0.15 mm to a via on an orthogonally adjacent site, so vias can
only sit on a checkerboard.  The DSI P balls H2..H7 (column H, boxed in by column J)
and the LVDS P balls C8..G8 (row 8, boxed in by row 9) are 6 + 5 consecutive balls,
each needing a layer change.  Alternating "via in pad" / "dog-bone to the empty
interior site" is the densest legal pattern; the G7/G8 corner forces H7 and G8 into
pads, which forces H2 too.  Result: 8 vias in pad, 5 dog-bones.

  via-in-pad (filled+capped, JLC POFV): H2 (0.30/0.15), H3 H5 H7 C8 E8 G8 E6 (0.35/0.20)
  dog-bone (0.40/0.20, tented, normal): H4->G4, H6->G6, D8->D7, F8->F7, GND E4->E3
"""
import sys, pcbnew
FM, mm = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
u = b.FindFootprintByReference("U21")
PADS = {p.GetNumber(): (mm(p.GetPosition().x), mm(p.GetPosition().y), p.GetNetCode()) for p in u.Pads()}
A1 = PADS["A1"]
def V(x, y): return pcbnew.VECTOR2I(FM(float(x)), FM(float(y)))
class _P:
    def __init__(s, k): s.k = k
    def GetPosition(s): return V(*PADS[s.k][:2])
    def GetNetCode(s): return PADS[s.k][2]
pad = {k: _P(k) for k in PADS}
def site(name):           # ball-lattice coordinate even where no ball exists
    col = "ABCDEFGHJ".index(name[0]); row = int(name[1:]) - 1
    return V(A1[0] + 0.5 * col, A1[1] + 0.5 * row)
def via(pos, net, d, dr):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pos); v.SetWidth(FM(d))
    v.SetDrill(FM(dr)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(net); v.SetLocked(True); b.Add(v)
def trk(a, c, net, w=0.11):
    t = pcbnew.PCB_TRACK(b); t.SetStart(a); t.SetEnd(c); t.SetWidth(FM(w)); t.SetLayer(pcbnew.B_Cu)
    t.SetNetCode(net); t.SetLocked(True); b.Add(t)
# drop the old automatic GND fan-out inside the array (it blocked G4)
xs = [v[0] for v in PADS.values()]; ys = [v[1] for v in PADS.values()]
for t in list(b.GetTracks()):
    ends = [t.GetPosition()] if t.Type() == pcbnew.PCB_VIA_T else [t.GetStart(), t.GetEnd()]
    inside = any(min(xs)-0.05 < mm(p.x) < max(xs)+0.05 and min(ys)-0.05 < mm(p.y) < max(ys)+0.05 for p in ends)
    if t.GetNetname() == "GND" and inside and not t.IsLocked():
        b.Delete(t)
VIP = {"H2": (0.30, 0.15), "H3": (0.35, 0.2), "H5": (0.35, 0.2), "H7": (0.35, 0.2),
       "C8": (0.35, 0.2), "E8": (0.35, 0.2), "G8": (0.35, 0.2), "E6": (0.35, 0.2)}
for n, (d, dr) in VIP.items():
    via(pad[n].GetPosition(), pad[n].GetNetCode(), d, dr)
DOG = {"H4": "G4", "H6": "G6", "D8": "D7", "F8": "F7", "E4": "E3"}
for n, s in DOG.items():
    net = pad[n].GetNetCode(); w = 0.11 if n != "E4" else 0.2
    trk(pad[n].GetPosition(), site(s), net, w); via(site(s), net, 0.40, 0.20)
# GND interior balls tied on B.Cu to the E3 via
g = PADS["E4"][2]
trk(pad["E4"].GetPosition(), pad["F4"].GetPosition(), g, 0.2); trk(pad["F4"].GetPosition(), pad["F5"].GetPosition(), g, 0.2)
b.Save(sys.argv[2]); b = pcbnew.LoadBoard(sys.argv[2]); b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(sys.argv[2]); print("U21 escape: %d via-in-pad, %d dog-bone" % (len(VIP), len(DOG)))
