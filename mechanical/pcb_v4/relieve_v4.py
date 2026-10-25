#!/usr/bin/env python3
"""Congestion relief around the SN65DSI83 (U21) BGA and the CM5 DF40 connectors (U9/U10).
  * small B-side passives (0402/0603/0805 R/C) near U21 / CM5 connectors flip to F.Cu at the same XY when their
    F courtyard is free (F faces the display: TFT rear is >= ~2.3 mm away even under the source-PCB band, so
    <=1 mm chips are fine; nothing tall moves). U21 VCC/VCORE decaps stay on B under the BGA.
  * parts in the U21 escape fan (x 162..172 east of the DSI columns, LVDS rows south) are pushed out radially
  * adds the DNP REFCLK oscillator option Y4/R531/C286 on F above U21 ball H2
  * starts from the copper-free refined board (genctl_v4_ref) with src positions, then classes/planes/fan-out
python3 relieve_v4.py in.kicad_pcb out.kicad_pcb [radius_u21=14] [cm5_margin=6]
"""
import sys, math, pcbnew
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import route_v4 as RV
MM, TM = pcbnew.FromMM, pcbnew.ToMM
src, dst = sys.argv[1], sys.argv[2]
RU = float(sys.argv[3]) if len(sys.argv) > 3 else 14.0
CMM = float(sys.argv[4]) if len(sys.argv) > 4 else 6.0
REF = "/workspace/genctl/layout_prep/v4/pcb_v4/genctl_v4_ref.kicad_pcb"   # same placement, no copper/planes yet
_s = pcbnew.LoadBoard(src)
pos = {f.GetReference(): (f.GetPosition().x, f.GetPosition().y, f.IsFlipped(), f.GetOrientationDegrees()) for f in _s.GetFootprints()}
del _s
b = pcbnew.LoadBoard(REF)
FD = pcbnew.FLIP_DIRECTION_LEFT_RIGHT if hasattr(pcbnew, "FLIP_DIRECTION_LEFT_RIGHT") else False
for f in b.GetFootprints():
    q = pos.get(f.GetReference())
    if not q: continue
    if f.IsFlipped() != q[2]: f.Flip(f.GetPosition(), FD)
    f.SetPosition(pcbnew.VECTOR2I(q[0], q[1])); f.SetOrientationDegrees(q[3])
RV.setup_classes(b); RV.setup_planes(b)
fps = {f.GetReference(): f for f in b.GetFootprints()}
U = fps["U21"]; ux, uy = TM(U.GetPosition().x), TM(U.GetPosition().y)
cms = [fps[r] for r in ("U9", "U10")]
def bbox(f):
    bb = f.GetCourtyard(f.GetSide() and pcbnew.B_CrtYd or pcbnew.F_CrtYd).BBox() if False else f.GetBoundingBox(False)
    return (TM(bb.GetLeft()), TM(bb.GetTop()), TM(bb.GetRight()), TM(bb.GetBottom()))
def ov(a, c, m=0.25): return not (a[2] + m <= c[0] or c[2] + m <= a[0] or a[3] + m <= c[1] or c[3] + m <= a[1])
cmbox = [tuple(v + s * CMM for v, s in zip(bbox(f), (-1, -1, 1, 1))) for f in cms]
small = lambda f: any(k in f.GetFPIDAsString() for k in ("_0402_", "_0603_", "_0805_")) and f.GetReference()[0] in "RC"
def near(f):
    x, y = TM(f.GetPosition().x), TM(f.GetPosition().y)
    if math.hypot(x - ux, y - uy) < RU: return True
    return any(c[0] <= x <= c[2] and c[1] <= y <= c[3] for c in cmbox)
keepB = lambda f: math.hypot(TM(f.GetPosition().x) - ux, TM(f.GetPosition().y) - uy) < 5 and \
    any(p.GetNetname() in ("+1V8_DSI", "DSI83_VCORE") for p in f.Pads())
Ffix = [bbox(f) for f in b.GetFootprints() if not f.IsFlipped()]
flipped = []
for f in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
    if not (f.IsFlipped() and small(f) and near(f)) or keepB(f) or f.IsLocked(): continue
    x = TM(f.GetPosition().x)
    if x < 74: continue                                    # never touch the HV / isolated side
    f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT if hasattr(pcbnew, "FLIP_DIRECTION_LEFT_RIGHT") else False)
    r = bbox(f)
    if any(ov(r, q) for q in Ffix):
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT if hasattr(pcbnew, "FLIP_DIRECTION_LEFT_RIGHT") else False); continue
    Ffix.append(r); flipped.append(f.GetReference())
# REFCLK oscillator option on F above ball H2 (via-in-pad brings REFCLK through)
def addfp(lib, name, ref, val, x, y, rot, nets):
    f = pcbnew.FootprintLoad("/usr/share/kicad/footprints/%s.pretty" % lib, name)
    f.SetReference(ref); f.SetValue(val); f.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y))); f.SetOrientationDegrees(rot)
    b.Add(f)
    for p in f.Pads():
        n = nets.get(p.GetNumber())
        if n:
            ni = b.FindNet(n)
            if ni is None: ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni)
            p.SetNet(ni)
    try: f.SetDNP(True)
    except Exception: pass
    return f
have = set(fps)
h2x, h2y = ux + 1.5, uy - 1.5
if "Y4" not in have:
    addfp("Oscillator", "Oscillator_SMD_Abracon_ASDMB-4Pin_2.5x2.0mm", "Y4", "25MHz", h2x + 1.0, h2y - 4.2, 0,
          {"1": "+1V8_DSI", "4": "+1V8_DSI", "2": "GND", "3": "DSI83_REFCLK_OSC"})
    addfp("Resistor_SMD", "R_0603_1608Metric", "R531", "22R", h2x + 1.0, h2y - 1.9, 0, {"1": "DSI83_REFCLK_OSC", "2": "DSI83_REFCLK"})
    addfp("Capacitor_SMD", "C_0603_1608Metric", "C286", "100n", h2x + 4.0, h2y - 4.2, 90, {"1": "+1V8_DSI", "2": "GND"})
RV.fanout(b); RV.fill(b); b.Save(dst)
print("flipped to F: %d %s" % (len(flipped), " ".join(flipped)))
