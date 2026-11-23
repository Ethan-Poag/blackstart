import sys,re,json,collections
sys.path.insert(0,'/workspace/review/springy/blocks')
from parse_net import load
comps,nets=load('/tmp/blk/genctl.net')
bucket=json.load(open('/workspace/review/springy/blocks/bucket_per_part.json'))
pn=collections.defaultdict(set)
PWR=re.compile(r'^(GND|\+|VBAT_P$|VBAT$|VMID|GND_)')
for n in nets:
    nm=n['name'].lstrip('/').split('/')[-1]
    if PWR.match(nm) or len(n['nodes'])>40: continue
    for r,p in n['nodes']: pn[r].add(nm)
def card(ref):
    ns=pn[ref]; hits=collections.Counter()
    for nm in ns:
        m=re.search(r'\bDI(\d+)',nm)
        if m: hits['DI-8 (DI5-12)' if int(m.group(1))>=5 else 'MB:DI1-4']+=1
        m=re.search(r'\bAI(\d)',nm)
        if m: hits['AI-4 (AI3-6)' if int(m.group(1))>=3 else 'MB:AI1-2']+=1
        m=re.search(r'AUX(\d+)',nm)
        if m: hits['HSO-5 A (AUX1-5)' if int(m.group(1))<=5 else 'HSO-5 B (AUX6-10)']+=1
        if re.search(r'GCB|MCB',nm): hits['BRK-4']+=1
    if hits:
        top=hits.most_common()
        if len(top)>1 and top[0][1]==top[1][1]: return 'SHARED:'+'+'.join(sorted(k for k,v in top if v==top[0][1]))
        return top[0][0]
    return 'MB:'+bucket.get(ref,'?')
res=collections.defaultdict(list)
for r in comps: res[card(r)].append(r)
for k in sorted(res): print(f'{k:45s} {len(res[k]):4d}  {" ".join(sorted(res[k])[:14])}')
json.dump({k:sorted(v) for k,v in res.items()},open('assign.json','w'),indent=0)
for k in res:
  if k.startswith('SHARED'):
    for r in res[k]: print(r,comps[r]['value'],sorted(pn[r])[:8])
