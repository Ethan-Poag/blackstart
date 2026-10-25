import pcbnew, math, re, collections
import sys; b=pcbnew.LoadBoard(sys.argv[1])
TM=pcbnew.ToMM
fps={f.GetReference():f for f in b.GetFootprints()}
pw=re.compile(r"^(GND.*|\+.*|VBAT.*|CM5_3V3|CM5_5V|.*VISO.*|VDDA|CHASSIS|DSI83_VCORE|SC_TOP|.*VCC.*)$")
nets=collections.defaultdict(list)
for f in fps.values():
    for p in f.Pads():
        n=p.GetNetname()
        if n: nets[n].append((f.GetReference(),p))
def d(a,c): return math.hypot(TM(a.x-c.x),TM(a.y-c.y))
# small parts: for each non-power net the part touches, nearest pad of a non-small part
small=re.compile(r"^(R|C|FB)\d+$")
rows=[]
for ref,f in fps.items():
    if not small.match(ref): continue
    best=None
    for p in f.Pads():
        n=p.GetNetname()
        if not n or n.startswith("GND"): continue
        for r2,p2 in nets[n]:
            if r2==ref or small.match(r2): continue
            dd=d(p.GetPosition(),p2.GetPosition())
            if best is None or dd<best[0]: best=(dd,n,r2)
    if best: rows.append((best[0],ref,best[1],best[2],f.GetValue(),bool(pw.match(best[1]))))
rows.sort(reverse=True)
import statistics
for lab,sel in (("decap/power",[r for r in rows if r[5] and r[1].startswith("C")]),("signal passives",[r for r in rows if not r[5]])):
    v=[r[0] for r in sel]
    print(lab,len(v),"median %.1f mm  p90 %.1f  max %.1f"%(statistics.median(v),sorted(v)[int(.9*len(v))-1],max(v)),"  >5mm:",sum(x>5 for x in v)," >10mm:",sum(x>10 for x in v))
print("farthest decaps:")
for r in [r for r in rows if r[5] and r[1].startswith("C")][:10]: print("  %s %s -> %s pad on %s: %.1f mm"%(r[1],r[4],r[3],r[2],r[0]))
print("farthest signal passives:")
for r in [r for r in rows if not r[5]][:12]: print("  %s %s -> %s on %s: %.1f mm"%(r[1],r[4],r[3],r[2],r[0]))
# longest signal nets by bbox half-perimeter
h=[]
for n,l in nets.items():
    if pw.match(n) or len(l)<2 or n.startswith("unconnected"): continue
    xs=[TM(p.GetPosition().x) for _,p in l]; ys=[TM(p.GetPosition().y) for _,p in l]
    h.append(((max(xs)-min(xs))+(max(ys)-min(ys)),n,len(l),sorted({r for r,_ in l})[:5]))
h.sort(reverse=True)
print("longest signal nets (HPWL):")
for x in h[:15]: print("  %.0f mm %s pads=%d %s"%x)
print("median net HPWL %.1f mm over %d nets"%(statistics.median([x[0] for x in h]),len(h)))
