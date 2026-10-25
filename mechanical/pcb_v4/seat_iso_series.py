#!/usr/bin/env python3
"""Move the MCU-side isolator series resistors (R413-R419) out of the HV box onto the
LV side of the barrier, next to the U69/U70 side-1 pin they feed (x > 73 mm).
Usage: python3 seat_iso_series.py in.kicad_pcb out.kicad_pcb"""
import sys, pcbnew
mm, FM = pcbnew.ToMM, pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
def cy(f):
    c = f.GetCourtyard(pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu)
    bb = c.BBox() if c.OutlineCount() else f.GetBoundingBox(False)
    return (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom()))
def side(f): return f.IsFlipped()
moving = [f"R{n}" for n in range(413, 420)]
others = [f for f in b.GetFootprints() if f.GetReference() not in moving]
rects = [(cy(f), side(f)) for f in others]
placed = []
def clash(r, s):
    for (q, qs) in rects + placed:
        if qs != s: continue
        if r[0] < q[2] + 0.25 and r[2] > q[0] - 0.25 and r[1] < q[3] + 0.25 and r[3] > q[1] - 0.25: return True
    return False
for ref in moving:
    f = b.FindFootprintByReference(ref)
    # isolator pin on the same net as one of this resistor's pads
    nets = {p.GetNetname() for p in f.Pads()}
    tgt = [p for u in ("U69", "U70") for p in b.FindFootprintByReference(u).Pads() if p.GetNetname() in nets]
    ty = mm(tgt[0].GetPosition().y) if tgt else mm(f.GetPosition().y)
    best = None
    for rot in (0, 90):
        f.SetOrientationDegrees(rot if not f.IsFlipped() else 180 - rot if rot else 180)
        for dx in [x * 0.25 for x in range(0, 40)]:
            for dy in sorted([y * 0.25 for y in range(-24, 25)], key=abs):
                f.SetPosition(pcbnew.VECTOR2I(FM(75.0 + dx), FM(ty + dy)))
                r = cy(f)
                if r[0] < 73.6 or not clash(r, side(f)):
                    if r[0] >= 73.6:
                        best = (dx + abs(dy), rot, 75.0 + dx, ty + dy); break
            if best: break
        if best: break
    f.SetOrientationDegrees(best[1] if not f.IsFlipped() else (180 - best[1] if best[1] else 180))
    f.SetPosition(pcbnew.VECTOR2I(FM(best[2]), FM(best[3])))
    placed.append((cy(f), side(f)))
    print(ref, "->", round(best[2], 2), round(best[3], 2), "rot", best[1])
b.Save(sys.argv[2])
