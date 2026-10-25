#!/usr/bin/env python3
"""Re-assign the 32 divider-string resistors to the 32 slots they already occupy (slots are known-clear:
line-potential R1 slots keep the 3 mm rule, so R1s only swap among R1 slots), minimising the length of the
HV_LINE_DIV nodes (terminal->R1->R2->R3->R4) plus a little tap-to-ADE length.  Simulated annealing on swaps.
Module use: reassign(board)."""
import math, random, sys, pcbnew
sys.path.insert(0, "/workspace/genctl/layout_prep"); sys.path.insert(0, "/workspace/genctl/layout_prep/v4")
import hv
TM, FM = pcbnew.ToMM, pcbnew.FromMM
def reassign(b, iters=200000, seed=1, log=print):
    ch = hv.chains(b); fps = {f.GetReference(): f for f in b.GetFootprints()}
    pads = {}
    for f in b.GetFootprints():
        for p in f.Pads(): pads.setdefault(p.GetNetname(), []).append((f.GetReference(), TM(p.GetPosition().x), TM(p.GetPosition().y)))
    slot = {}   # ref -> (x, y, rot)
    for _, c, _ in ch:
        for r in c: f = fps[r]; slot[r] = (TM(f.GetPosition().x), TM(f.GetPosition().y), f.GetOrientationDegrees())
    chains = [c for _, c, _ in ch]; members = set(slot)
    # move far-away line-potential (R1) slots to the nearest clear spot by their terminal (3.0 mm to everything)
    import numpy as np
    HVB = (-3.745, 11.0, 60.0, 162.0); G = 0.25
    nx, ny = int((HVB[2] - HVB[0]) / G), int((HVB[3] - HVB[1]) / G)
    def gi(x, y): return int((x - HVB[0]) / G), int((y - HVB[1]) / G)
    def crt(f):
        c = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
        bb = c.BBox() if c.OutlineCount() else f.GetBoundingBox(False)
        return (TM(bb.GetLeft()), TM(bb.GetTop()), TM(bb.GetRight()), TM(bb.GetBottom()))
    occ = np.zeros((ny, nx), np.int32)
    def mark(r, v):
        x0, y0 = gi(r[0], r[1]); x1, y1 = gi(r[2], r[3])
        occ[max(0, y0):max(0, min(ny, y1 + 1)), max(0, x0):max(0, min(nx, x1 + 1))] += v
    for f in b.GetFootprints():
        th = any(p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) for p in f.Pads())
        if f.IsFlipped() or th: mark(crt(f), 1)
    for line, c, nodes in ch:
        t = [(TM(p.GetPosition().x), TM(p.GetPosition().y)) for p in b.GetPads() if p.GetNetname() == line and p.GetParentFootprint().GetReference().startswith("J")]
        if not t: continue
        tx, ty = max(p[0] for p in t), sum(p[1] for p in t) / len(t)
        r1 = c[0]; x, y, rot = slot[r1]
        if math.hypot(x - tx, y - ty) < 15: continue
        f = fps[r1]; old = crt(f); mark(old, -1)
        s = np.zeros((ny + 1, nx + 1), np.int64); s[1:, 1:] = (occ > 0).cumsum(0).cumsum(1)
        best = None
        for yy in np.arange(HVB[1] + 4, HVB[3] - 4, 0.25):
            for xx in np.arange(12.0, 56.0, 0.25):
                for rr in (0, 90):
                    hw, hh = (2.305, 1.155) if rr == 0 else (1.155, 2.305)
                    a0, b0 = gi(xx - hw - 2.6, yy - hh - 2.6); a1, b1 = gi(xx + hw + 2.6, yy + hh + 2.6)
                    if a0 < 0 or b0 < 0 or a1 >= nx or b1 >= ny: continue
                    if s[b1 + 1, a1 + 1] - s[b0, a1 + 1] - s[b1 + 1, a0] + s[b0, a0] > 0: continue
                    d = math.hypot(xx - tx, yy - ty)
                    if best is None or d < best[0]: best = (d, xx, yy, rr)
        if best and best[0] < math.hypot(x - tx, y - ty) - 5:
            slot[r1] = (float(best[1]), float(best[2]), float(best[3]))
            hw, hh = (2.305, 1.155) if best[3] == 0 else (1.155, 2.305)
            mark((best[1] - hw, best[2] - hh, best[1] + hw, best[2] + hh), 1)
            log("R1 slot of %s moved %s -> (%.1f, %.1f)" % (line.split("/")[-1], r1, best[1], best[2]))
        else: mark(old, 1)
    term = []; tap = []
    for line, c, nodes in ch:
        t = [(x, y) for r, x, y in pads[line] if r.startswith("J")]
        term.append((max(p[0] for p in t), sum(p[1] for p in t) / len(t)) if t else None)
        a = [(x, y) for r, x, y in pads.get(nodes[-1], []) if r not in members]
        tap.append((sum(p[0] for p in a) / len(a), sum(p[1] for p in a) / len(a)) if a else None)
    R1 = [c[0] for c in chains]; RX = [r for c in chains for r in c[1:]]
    # slots that can host a line-potential R1: 2.6 mm courtyard margin to every other part, not next to an ADE9000
    sat_all = np.zeros((ny + 1, nx + 1), np.int64); sat_all[1:, 1:] = (occ > 0).cumsum(0).cumsum(1)
    ade = [(TM(fps[u].GetPosition().x), TM(fps[u].GetPosition().y)) for u in ("U71", "U72")]
    r1ok = set()
    for r in slot: mark(crt(fps[r]), -1)          # divider parts may sit 1.5 mm from line copper (kicad_dru)
    for r in slot:
        cr = crt(fps[r]); mark(cr, -1)
        sa = np.zeros((ny + 1, nx + 1), np.int64); sa[1:, 1:] = (occ > 0).cumsum(0).cumsum(1)
        a0, b0 = gi(cr[0] - 2.6, cr[1] - 2.6); a1, b1 = gi(cr[2] + 2.6, cr[3] + 2.6)
        clear = a0 >= 0 and b0 >= 0 and a1 < nx and b1 < ny and sa[b1 + 1, a1 + 1] - sa[b0, a1 + 1] - sa[b1 + 1, a0] + sa[b0, a0] == 0
        mark(cr, 1)
        if clear and min(math.hypot(slot[r][0] - ax_, slot[r][1] - ay_) for ax_, ay_ in ade) > 9: r1ok.add(r)
    for r in slot: mark(crt(fps[r]), 1)
    log("R1-capable slots:", len(r1ok))
    pos = {r: slot[r][:2] for r in slot}       # current assignment ref -> slot position key
    owner = {r: r for r in slot}               # ref -> slot ref it sits in
    D = lambda a, c: math.hypot(a[0] - c[0], a[1] - c[1])
    def ccost(i):
        c = chains[i]; p = [slot[owner[r]][:2] for r in c]
        s = sum(D(p[k], p[k + 1]) for k in range(3))
        if term[i]: s += D(term[i], p[0])
        if tap[i]: s += 0.3 * D(tap[i], p[3])
        if owner[c[0]] not in r1ok: s += 500.0
        return s
    cidx = {r: i for i, c in enumerate(chains) for r in c}
    cost = [ccost(i) for i in range(len(chains))]; tot0 = sum(cost)
    rnd = random.Random(seed); T0 = 20.0
    best = (sum(cost), dict(owner))
    for it in range(iters):
        T = T0 * (1 - it / iters) + 0.01
        a, c = rnd.sample(R1 + RX, 2)
        if (a in R1 and owner[c] not in r1ok) or (c in R1 and owner[a] not in r1ok): continue
        ia, ic = cidx[a], cidx[c]
        old = cost[ia] + (cost[ic] if ic != ia else 0)
        owner[a], owner[c] = owner[c], owner[a]
        na = ccost(ia); nc = ccost(ic) if ic != ia else 0
        dlt = na + nc - old
        if dlt < 0 or rnd.random() < math.exp(-dlt / T):
            cost[ia] = na
            if ic != ia: cost[ic] = nc
            if sum(cost) < best[0]: best = (sum(cost), dict(owner))
        else:
            owner[a], owner[c] = owner[c], owner[a]
    owner = best[1]
    for r in slot:
        x, y, rot = slot[owner[r]]
        f = fps[r]; f.SetOrientationDegrees(rot); f.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y)))
    # orient pads along the string (shared node toward the previous element)
    for (line, c, nodes), t in zip(ch, term):
        prev = t or slot[owner[c[0]]][:2]
        for i, r in enumerate(c):
            f = fps[r]; want = line if i == 0 else nodes[i - 1]
            pw = [p for p in f.Pads() if p.GetNetname() == want]
            if not pw: continue
            p = pw[0]; po = [q for q in f.Pads() if q.GetNumber() != p.GetNumber()][0]
            if D((TM(p.GetPosition().x), TM(p.GetPosition().y)), prev) > D((TM(po.GetPosition().x), TM(po.GetPosition().y)), prev):
                f.SetOrientationDegrees(f.GetOrientationDegrees() + 180)
            q = [q for q in f.Pads() if q.GetNetname() != want][0]; prev = (TM(q.GetPosition().x), TM(q.GetPosition().y))
    log("hv string slot reassignment: cost %.0f -> %.0f mm" % (tot0, best[0]))
    return best[0]
if __name__ == "__main__":
    b = pcbnew.LoadBoard(sys.argv[1]); reassign(b); b.Save(sys.argv[2])
