#!/usr/bin/env python3
"""Re-seat each 600 V divider string as a COMPACT block next to its line terminal, so only the low-voltage tap
net (Default class) runs the long way to the ADE9000.  The old refine spread strings toward the ADE, which made
long HV_LINE_DIV nets (1.5 mm clearance) cross the metering area and starved AC SPI / ADE input routing.
Block shapes tried: 1x4 row, 1x4 column, 2x2 (horizontal or vertical resistors).  Spacing (unchanged rules):
1.6 mm between resistors of one string, >=3.0 mm from the line-potential resistor / between strings, 1.6 mm from other parts (as refine_v4).
Used as a module by relieve_v4.py: reseat(board)."""
import math, sys, numpy as np, pcbnew
sys.path.insert(0, "/workspace/genctl/layout_prep"); sys.path.insert(0, "/workspace/genctl/layout_prep/v4")
import hv
TM, FM = pcbnew.ToMM, pcbnew.FromMM
HVB = (-3.745, 11.0, 60.0, 162.0)
G = 0.25
def reseat(b, log=print):
    ch = hv.chains(b)
    chainset = set(r for c in ch for r in c[1])
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    nx, ny = int((HVB[2] - HVB[0]) / G), int((HVB[3] - HVB[1]) / G)
    def gi(x, y): return int((x - HVB[0]) / G), int((y - HVB[1]) / G)
    def mark(r, arr, v=1):
        x0, y0 = gi(r[0], r[1]); x1, y1 = gi(r[2], r[3])
        arr[max(0, y0):max(0, min(ny, y1 + 1)), max(0, x0):max(0, min(nx, x1 + 1))] += v
    def bbr(f):
        c = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
        bb = c.BBox() if c.OutlineCount() else f.GetBoundingBox(False)
        return (TM(bb.GetLeft()), TM(bb.GetTop()), TM(bb.GetRight()), TM(bb.GetBottom()))
    occ = np.zeros((ny, nx), np.int32)        # non-string parts
    for f in b.GetFootprints():
        if f.GetReference() in chainset: continue
        th = any(p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) for p in f.Pads())
        if not f.IsFlipped() and not th: continue         # F-side SMD does not block B-side resistors
        mark(bbr(f), occ)
    def ov(a, c, m): return not (a[2] + m <= c[0] or c[2] + m <= a[0] or a[3] + m <= c[1] or c[3] + m <= a[1])
    def sat(a):
        s = np.zeros((ny + 1, nx + 1), np.int64); s[1:, 1:] = a.cumsum(0).cumsum(1); return s
    def hit(s, r, m):
        x0, y0 = gi(r[0] - m, r[1] - m); x1, y1 = gi(r[2] + m, r[3] + m)
        if x0 < 2 or y0 < 2 or x1 >= nx - 2 or y1 >= ny - 2: return True
        return s[y1 + 1, x1 + 1] - s[y0, x1 + 1] - s[y1 + 1, x0] + s[y0, x0] > 0
    L, Wd, gap = 4.61, 2.31, 1.6
    P = L + gap; Q = Wd + gap
    shapes = {"row": [(i * P, 0, 0) for i in range(4)], "col": [(0, i * P, 90) for i in range(4)],
              "2x2h": [(0, 0, 0), (P, 0, 0), (P, Q, 0), (0, Q, 0)], "2x2v": [(0, 0, 90), (Q, 0, 90), (Q, P, 90), (0, P, 90)]}
    def rect(cx, cy, rot):
        hw, hh = (L / 2, Wd / 2) if rot == 0 else (Wd / 2, L / 2)
        return (cx - hw, cy - hh, cx + hw, cy + hh)
    pads_by_net = {}
    for f in b.GetFootprints():
        for p in f.Pads(): pads_by_net.setdefault(p.GetNetname(), []).append((f.GetReference(), TM(p.GetPosition().x), TM(p.GetPosition().y)))
    so = sat(occ)
    order = sorted(ch, key=lambda c: min([y for r, x, y in pads_by_net[c[0]] if r.startswith("J")] or [999]))
    blocks = np.zeros((ny, nx), np.int32); blocks1 = np.zeros_like(blocks)   # every string where it is now: all / line R1
    for l2, c2, _ in ch:
        for k, r2 in enumerate(c2):
            mark(bbr(fps[r2]), blocks)
            if k == 0: mark(bbr(fps[r2]), blocks1)
    out = []
    for line, chain, nodes in order + order:   # second sweep: retry after others compacted     # second sweep: strings that found no slot retry after others moved
        if len(chain) != 4: log("skip", line, chain); continue
        term = [(x, y) for r, x, y in pads_by_net[line] if r.startswith("J")]
        tx, ty = (max(p[0] for p in term), sum(p[1] for p in term) / len(term)) if term else (10, 80)
        taps = [(x, y) for r, x, y in pads_by_net.get(nodes[-1], []) if r not in chain]
        ax, ay = (sum(p[0] for p in taps) / len(taps), sum(p[1] for p in taps) / len(taps)) if taps else (45, 80)
        for k, r2 in enumerate(chain):          # lift this string
            mark(bbr(fps[r2]), blocks, -1)
            if k == 0: mark(bbr(fps[r2]), blocks1, -1)
        sb = sat(blocks > 0); sb1 = sat(blocks1 > 0); best = None
        for name, cells in shapes.items():
            for yy in np.arange(HVB[1] + 3, HVB[3] - 3, 0.5):
                for xx in np.arange(12.0, HVB[2] - 3, 0.5):
                    rs = [rect(xx + dx, yy + dy, rot) for dx, dy, rot in cells]
                    if any((hit(so, r, 3.0) or hit(sb, r, 3.0)) if i == 0 else (hit(so, r, 1.6) or hit(sb, r, 1.6) or hit(sb1, r, 3.0)) for i, r in enumerate(rs)): continue
                    r1 = rs[0]; r4 = rs[3]
                    c1 = math.hypot((r1[0] + r1[2]) / 2 - tx, (r1[1] + r1[3]) / 2 - ty)
                    c4 = math.hypot((r4[0] + r4[2]) / 2 - ax, (r4[1] + r4[3]) / 2 - ay)
                    cost = 2.0 * c1 + 0.4 * c4
                    if best is None or cost < best[0]: best = (cost, name, xx, yy, rs)
        if best:
            cost, name, xx, yy, rs = best; cells = shapes[name]
        else:   # greedy walk: each resistor in the free spot nearest the previous one (keeps every HV node short)
            name, rs, cells, prev = "walk", [], [], (tx, ty)
            for i in range(4):
                cand = None
                for yy in np.arange(HVB[1] + 3, HVB[3] - 3, 0.5):
                    for xx in np.arange(12.0, HVB[2] - 3, 0.5):
                        for rot in (0, 90):
                            r = rect(xx, yy, rot)
                            if any(ov(r, q, 1.6) for q in rs): continue
                            if (hit(so, r, 3.0) or hit(sb, r, 3.0)) if i == 0 else (hit(so, r, 1.6) or hit(sb, r, 1.6) or hit(sb1, r, 3.0)): continue
                            d = math.hypot(xx - prev[0], yy - prev[1]) + (0.3 * math.hypot(xx - ax, yy - ay) if i == 3 else 0)
                            if cand is None or d < cand[0]: cand = (d, r, rot, xx, yy)
                if not cand: break
                rs.append(cand[1]); cells.append((0, 0, cand[2])); prev = (cand[3], cand[4])
            if len(rs) < 4:
                log("NO SLOT (left in place):", line.split("/")[-1])
                for k, r2 in enumerate(chain):
                    mark(bbr(fps[r2]), blocks)
                    if k == 0: mark(bbr(fps[r2]), blocks1)
                continue
            xx, yy = rs[0][0], rs[0][1]
        for ref, (dx, dy, rot), r in zip(chain, cells, rs):
            f = fps[ref]; f.SetOrientationDegrees(rot); f.SetPosition(pcbnew.VECTOR2I(FM(float(r[0] + r[2]) / 2), FM(float(r[1] + r[3]) / 2)))
            mark(r, blocks)
            if ref == chain[0]: mark(r, blocks1)
        # orient each resistor so its pad toward the previous element carries the shared node
        prev = (tx, ty)
        for i, ref in enumerate(chain):
            f = fps[ref]
            want = line if i == 0 else nodes[i - 1]
            pw = [p for p in f.Pads() if p.GetNetname() == want]
            if pw:
                p = pw[0]; po = [q for q in f.Pads() if q is not p][0]
                if math.hypot(TM(p.GetPosition().x) - prev[0], TM(p.GetPosition().y) - prev[1]) > math.hypot(TM(po.GetPosition().x) - prev[0], TM(po.GetPosition().y) - prev[1]):
                    f.SetOrientationDegrees(f.GetOrientationDegrees() + 180)
                q = [q for q in f.Pads() if q.GetNetname() != want][0]; prev = (TM(q.GetPosition().x), TM(q.GetPosition().y))
        out.append((line.split("/")[-1], name, round(xx, 1), round(yy, 1)))
        log("hv string", line.split("/")[-1], name, "at", round(xx, 1), round(yy, 1))
    return out

if __name__ == "__main__":
    b = pcbnew.LoadBoard(sys.argv[1]); reseat(b); b.Save(sys.argv[2])
