#!/usr/bin/env python3
"""Place<->route iteration step: re-seat parts whose first placement made routing bad.
  * crystals + load caps tight to their IC pins (STM32 HSE/LSE, ADE9000 XI/XO)
  * each 600 V divider string laid out as a straight chain from its terminal toward its ADE9000 input
    (3.0 mm from the line-potential resistor to non-divider copper, 1.6 mm inside the string)
python3 refine_v4.py in.kicad_pcb out.kicad_pcb
"""
import sys, math, pcbnew
sys.path.insert(0, "/workspace/genctl/layout_prep"); sys.path.insert(0, "/workspace/genctl/layout_prep/v4")
import place as P, hv
TM = pcbnew.ToMM
HV = (-3.745, 11.0, 60.0, 162.0)
b = pcbnew.LoadBoard(sys.argv[1])
fps = {f.GetReference(): f for f in b.GetFootprints()}
def pad(ref, num):
    for p in fps[ref].Pads():
        if p.GetNumber() == num: return TM(p.GetPosition().x), TM(p.GetPosition().y)
def rect(f, m=0.0):
    r = P.rect_of(f); return (r[0] - m, r[1] - m, r[2] + m, r[3] + m)
def overl(a, c): return not (a[2] <= c[0] or c[2] <= a[0] or a[3] <= c[1] or c[3] <= a[1])

CRYST = [("Y1", ["C61", "C62"], ("U7", ["12", "13"])), ("Y2", ["C63", "C64"], ("U7", ["8", "9"])),
         ("Y3", ["C257", "C258"], ("U71", ["29", "30"]))]
ch = hv.chains(b)
moving = set(r for c in ch for r in c[1]) | set(y for y, cs, _ in CRYST) | set(c for _, cs, _ in CRYST for c in cs)
chainset = set(r for c in ch for r in c[1]); linefirst = set(c[1][0] for c in ch)
fixed = {r: f for r, f in fps.items() if r not in moving}
holes = [(x - 6, y - 6, x + 6, y + 6) for _, x, y in __import__("geometry").MOUNT_HOLES]
placed_rects = []   # (rect, ref)
FIX = [(rect(f2), f2.IsFlipped(), any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in f2.Pads()), any(hv.LINE.search(p.GetNetname()) for p in f2.Pads())) for f2 in fixed.values()]

def ok(f, ref):
    r = rect(f)
    # board / HV box containment
    hot = ref in chainset or ref.startswith("Y3") or ref in ("C257", "C258")
    if hot and not (r[0] >= HV[0] + 0.5 and r[2] <= HV[2] - 0.6 and r[1] >= HV[1] + 0.5 and r[3] <= HV[3] - 0.5): return False
    if not hot and (r[0] < HV[2] + 13.6): return False
    for h in holes:
        if overl(r, h): return False
    fl = f.IsFlipped(); big = (r[0] - 3, r[1] - 3, r[2] + 3, r[3] + 3)
    for r2, fl2, tht, hl in FIX:
        if fl2 != fl and not tht: continue
        if not overl(big, r2): continue
        m = 0.3
        if ref in chainset: m = 3.0 if (ref in linefirst or hl) else 1.6
        if overl((r[0] - m, r[1] - m, r[2] + m, r[3] + m), r2): return False
    for r2, o in placed_rects:
        m = 0.3
        if ref in chainset or o in chainset:
            m = 3.0 if (ref in linefirst and o in linefirst) else 1.6 if (ref in chainset and o in chainset) else (3.0 if (ref in linefirst or o in linefirst) else 1.6)
        if overl((r[0] - m, r[1] - m, r[2] + m, r[3] + m), r2): return False
    return True

def seat(ref, tx, ty, rot):
    f = fps[ref]
    for k in range(0, 400):
        rr = k * 0.25; n = max(1, int(2 * math.pi * rr / 0.25)) if rr else 1
        for i in range(n):
            a = 2 * math.pi * i / n
            for rt in (rot, rot + 90):
                P.put(f, tx + rr * math.cos(a), ty + rr * math.sin(a), rt, "B")
                if ok(f, ref):
                    placed_rects.append((rect(f), ref)); return True
    print("NO ROOM", ref); return False

# crystals first (short, sensitive), then divider strings
for y, caps, (ic, pins) in CRYST:
    pts = [pad(ic, n) for n in pins]; px = sum(p[0] for p in pts) / 2; py = sum(p[1] for p in pts) / 2
    c = fps[ic].GetPosition(); cx, cy = TM(c.x), TM(c.y)
    dx, dy = px - cx, py - cy; d = math.hypot(dx, dy) or 1; ux, uy = dx / d, dy / d
    seat(y, px + ux * 3.2, py + uy * 3.2, 0)
    yp = fps[y].GetPosition(); yx, yy = TM(yp.x), TM(yp.y)
    for i, cref in enumerate(caps):
        seat(cref, yx + ux * 2.8 + (-uy) * (1.6 if i else -1.6), yy + uy * 2.8 + ux * (1.6 if i else -1.6), 0)

pads_by_net = {}
for f in b.GetFootprints():
    for p in f.Pads(): pads_by_net.setdefault(p.GetNetname(), []).append((f.GetReference(), p))
def ade_target(tap):
    seen = {tap}; frontier = [tap]
    for _ in range(3):
        nf = []
        for n in frontier:
            for r, p in pads_by_net.get(n, []):
                if r in ("U71", "U72"): return TM(p.GetPosition().x), TM(p.GetPosition().y)
                for q in fps[r].Pads():
                    m = q.GetNetname()
                    if m not in seen and not m.startswith("GND") and not m.startswith("+"): seen.add(m); nf.append(m)
        frontier = nf
    return None
for line, chain, nodes in ch:
    term = [TM(p.GetPosition().x) for r, p in pads_by_net[line] if r.startswith("J")]
    tys = [TM(p.GetPosition().y) for r, p in pads_by_net[line] if r.startswith("J")]
    sx, sy = (max(term) + 4.0, sum(tys) / len(tys)) if term else (20, 80)
    e = ade_target(nodes[-1]) or (40, 80)
    ex, ey = e
    n = len(chain)
    ang = math.degrees(math.atan2(ey - sy, ex - sx)); rot = 0 if abs(math.cos(math.radians(ang))) > 0.7 else 90
    for i, ref in enumerate(chain):
        t = (i + 0.5) / (n + 0.5)
        seat(ref, sx + (ex - sx) * t * 0.85, sy + (ey - sy) * t * 0.85, rot)
# manual nudges found by DRC on the refined board (HV 3 mm outer rule)
NUDGE = {"R446": (0.0, 0.6), "R425": (-0.6, 0.0), "R462": (0.3, 0.0)}
for r, (dx, dy) in NUDGE.items():
    f = fps[r]; f.Move(pcbnew.VECTOR2I(pcbnew.FromMM(dx), pcbnew.FromMM(dy)))
b.Save(sys.argv[2]); print("refined", len(moving), "parts")
