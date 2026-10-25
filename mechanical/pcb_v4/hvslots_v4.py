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
    term = []; tap = []
    for line, c, nodes in ch:
        t = [(x, y) for r, x, y in pads[line] if r.startswith("J")]
        term.append((max(p[0] for p in t), sum(p[1] for p in t) / len(t)) if t else None)
        a = [(x, y) for r, x, y in pads.get(nodes[-1], []) if r not in members]
        tap.append((sum(p[0] for p in a) / len(a), sum(p[1] for p in a) / len(a)) if a else None)
    R1 = [c[0] for c in chains]; RX = [r for c in chains for r in c[1:]]
    pos = {r: slot[r][:2] for r in slot}       # current assignment ref -> slot position key
    owner = {r: r for r in slot}               # ref -> slot ref it sits in
    D = lambda a, c: math.hypot(a[0] - c[0], a[1] - c[1])
    def ccost(i):
        c = chains[i]; p = [slot[owner[r]][:2] for r in c]
        s = sum(D(p[k], p[k + 1]) for k in range(3))
        if term[i]: s += D(term[i], p[0])
        if tap[i]: s += 0.3 * D(tap[i], p[3])
        return s
    cidx = {r: i for i, c in enumerate(chains) for r in c}
    cost = [ccost(i) for i in range(len(chains))]; tot0 = sum(cost)
    rnd = random.Random(seed); T0 = 20.0
    best = (sum(cost), dict(owner))
    for it in range(iters):
        T = T0 * (1 - it / iters) + 0.01
        grp = R1 if rnd.random() < 0.2 else RX
        a, c = rnd.sample(grp, 2)
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
