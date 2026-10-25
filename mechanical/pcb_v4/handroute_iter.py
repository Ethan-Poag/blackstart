#!/usr/bin/env python3
"""Rip-up-and-retry driver: re-run handroute_v4 with previously failed jobs promoted to the front."""
import json, subprocess, sys, os, shutil
src, dst = sys.argv[1], sys.argv[2]; passes = int(sys.argv[3]) if len(sys.argv) > 3 else 5
prio = []; best = None
for k in range(passes):
    json.dump(prio, open("/tmp/hr_prio.json", "w"))
    out = dst + f".pass{k}.kicad_pcb"
    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__) or ".", "handroute_v4.py"), src, out],
                   env=dict(os.environ, PRIO="/tmp/hr_prio.json"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    r = json.load(open(out + ".route.json")); f = r["failed"]
    print(f"pass {k}: {len(f)} failed {f}", flush=True)
    if best is None or len(f) < best[0]: best = (len(f), out)
    if not f: break
    prio = f + [p for p in prio if p not in f]
shutil.copy(best[1], dst); shutil.copy(best[1] + ".route.json", dst + ".route.json")
print("best:", best)
