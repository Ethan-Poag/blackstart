"""Check the drawn mainboard sheets against the intended pin->net map built by mainboard.py (every pin of every part on the regenerated sheets)."""
import os,sys,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,'/workspace/review/springy/blocks')
import mainboard as M
from parse_net import load
comps,nets=load(sys.argv[1] if len(sys.argv)>1 else '/tmp/sysaudit/mb.net')
pn={}
for n in nets:
    for r,p in n['nodes']: pn[(r,p)]=n['name']
def short(n): return n.rsplit('/',1)[-1] if n.startswith('/') else n
bad=0; nets_seen=collections.defaultdict(set); checked=0
for f,c in M.cards.items():
    for p in c.parts:
        for k,v in p['pn'].items():
            got=pn.get((p['ref'],k)); checked+=1
            if v is None:
                if got and not got.startswith('unconnected-'): bad+=1; print('should be NC',p['ref'],k,got)
                continue
            if got is None: bad+=1; print('missing',p['ref'],k,v); continue
            nets_seen[v].add(got)
            if short(got)!=v and not got.startswith('Net-('): pass
for v,g in nets_seen.items():
    if len(g)>1: bad+=1; print('net split',v,g)
inv=collections.defaultdict(set)
for v,g in nets_seen.items():
    for x in g: inv[x].add(v)
for x,vs in inv.items():
    if len(vs)>1: bad+=1; print('nets merged',x,vs)
print('mainboard drawn-vs-intended: pins checked',checked,'errors',bad)
