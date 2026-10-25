"""600 V divider-string discovery shared by refine_v4 / route_v4."""
import re
LINE = re.compile(r"(GEN|BUS)_(L\d|N)$")

def chains(b):
    pads_by_net = {}
    for f in b.GetFootprints():
        for p in f.Pads(): pads_by_net.setdefault(p.GetNetname(), []).append((f, p))
    def is_hvr(f): return f.GetReference().startswith("R") and "1206" in f.GetFPIDAsString()
    out = []
    for f in b.GetFootprints():
        if not is_hvr(f): continue
        if not any(LINE.search(p.GetNetname()) for p in f.Pads()): continue
        chain = [f.GetReference()]; nodes = []; cur = f
        prev_net = [p.GetNetname() for p in f.Pads() if LINE.search(p.GetNetname())][0]
        while True:
            nxt_net = [p.GetNetname() for p in cur.Pads() if p.GetNetname() != prev_net]
            if not nxt_net: break
            n = nxt_net[0]; nodes.append(n)
            cands = [g for g, q in pads_by_net.get(n, []) if g.GetReference() not in chain and is_hvr(g)
                     and not any(qq.GetNetname().startswith("GND") for qq in g.Pads())]
            if not cands or len(chain) > 8: break
            cur = cands[0]; chain.append(cur.GetReference()); prev_net = n
        out.append((prev_net if False else [p.GetNetname() for p in f.Pads() if LINE.search(p.GetNetname())][0], chain, nodes))
    return out

if __name__ == "__main__":
    import sys, pcbnew
    for c in chains(pcbnew.LoadBoard(sys.argv[1])): print(c[0].split('/')[-1], c[1], [x[-12:] for x in c[2]])
