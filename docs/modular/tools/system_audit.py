"""Full-system netlist audit, modular build vs the locked baseline.
Joins mainboard + ENGINE + DI-8 (LV1) + AI-4 (LV2) + HSO-5 #1 AUX1-5 (LV3) + HSO-5 #2 AUX6-10 (LV4) + BRK-4 (LV5) + HV meter (J31<->J32 harness)
through their mating connectors, maps every baseline (ref,pin) to its new home and compares connectivity component by component.
Every split/merge must be explained by a recorded intentional change; every slot/harness contact is checked for orphans."""
import os,sys,re,json,csv,collections,subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0,os.path.join(R,'cards','tools')); sys.path.insert(0,'/workspace/review/springy/blocks')
import srcdb
from parse_net import load as ln
from partition import ASSIGN
def short(n): return n.rsplit('/',1)[-1] if n.startswith('/') else n
OUT='/tmp/sysaudit'; os.makedirs(OUT,exist_ok=True)
def export(sch,name):
    p=os.path.join(OUT,name+'.net'); subprocess.run(['kicad-cli','sch','export','netlist','-o',p,sch],check=True,capture_output=True); return ln(p)
NEW={'MB':export(os.path.join(R,'genctl.kicad_sch'),'mb'),'MTR':export(os.path.join(R,'genctl_meter.kicad_sch'),'mtr')}
CARDS={'ENG':'engine','DI8':'di8','AI4':'ai4','HSO5a':'hso5','HSO5b':'hso5','BRK4':'brk4'}
for b,c in CARDS.items():
    if b=='HSO5b': NEW[b]=NEW['HSO5a']; continue
    NEW[b]=export(os.path.join(R,'cards',c,c+'.kicad_sch'),c)
SLOT={'DI8':'LV1','AI4':'LV2','HSO5a':'LV3','HSO5b':'LV4','BRK4':'LV5','ENG':'ENGINE'}
# ---------- union-find over system nodes ----------
par={}
def f(x):
    while par.setdefault(x,x)!=x: par[x]=par[par[x]]; x=par[x]
    return x
def u(a,b): par[f(a)]=f(b)
netof={}; names={}
for b,(comps,nets) in NEW.items():
    for n in nets:
        key=(b,'net',n['name']); f(key); names[key]=n['name']
        for r,p in n['nodes']: netof[(b,r,p)]=key; u((b,r,p),key)
def slot_ref(b):
    comps,_=NEW[b]
    js=[r for r,c in comps.items() if c['value']=='DIN41612_C96']
    assert len(js)==1,(b,js); return js[0]
mbc,_=NEW['MB']
src=srcdb.load('genctl')
import json as J
mbslot={}
inst=collections.defaultdict(dict)
for line in open(os.path.join(R,'backplane.kicad_sch')):
    pass
# slot connector refs on the mainboard: J40..J47 = LV1..LV8, J48 = ENGINE (cards/tools/mainboard.py creation order)
mbslot={f'LV{i}':f'J{39+i}' for i in range(1,9)}; mbslot['ENGINE']='J48'
pairs=[]
def pins_of(b,ref):
    return sorted({p for (bb,r,p) in netof if bb==b and r==ref})
allpins=[f'{row}{i}' for row in 'abc' for i in range(1,33)]
for b,s in SLOT.items():
    cj=slot_ref(b)
    for p in allpins: pairs.append((('MB',mbslot[s],p),(b,cj,p),f'{s}:{b}'))
for p in [str(i) for i in range(1,17)]: pairs.append((('MB','J31',p),('MTR','J32',p),'J31-J32 harness'))
for a,c,_ in pairs:
    if a in netof and c in netof: u(a,c)
# ---------- baseline system ----------
bpar={}
def bf(x):
    while bpar.setdefault(x,x)!=x: bpar[x]=bpar[bpar[x]]; x=bpar[x]
    return x
def bu(a,b): bpar[bf(a)]=bf(b)
BASE={'MB':srcdb.load('genctl')[1],'MTR':srcdb.load('genctl_meter')[1]}
bnet={}
for b,nets in BASE.items():
    for n in nets:
        key=(b,'net',n['name']); bf(key)
        for r,p in n['nodes']: bnet[(b,r,p)]=key; bu((b,r,p),key)
for i in range(1,17):
    a,c=('MB','J31',str(i)),('MTR','J32',str(i))
    if a in bnet and c in bnet: bu(a,c)
# ---------- node map baseline -> new ----------
rw=json.load(open(os.path.join(R,'docs/modular/mainboard_rework.json')))
REMOVED=set(rw['removed_p1'])|set(rw['removed_p2'])
refmap={c:json.load(open(os.path.join(R,'cards',c,'refmap.json'))) for c in set(CARDS.values())}
comps0,nets0=srcdb.load('genctl')[:2]
pins0=collections.defaultdict(dict)
for n in nets0:
    for r,p in n['nodes']: pins0[r][p]=n['name']
# HSO_B -> HSO_A pairing (same circuit, AUX index +5): iterative structural match
A=[r for r,v in ASSIGN.items() if v=='HSO_A']; Bp=[r for r,v in ASSIGN.items() if v=='HSO_B']
def shift(n): return re.sub(r'AUX(\d+)',lambda m:'AUX%d'%(int(m.group(1))+5),short(n))
bind={}   # baseline HSO_A net -> HSO_B net
pairAB={}
for it in range(6):
    sigB=collections.defaultdict(list)
    for r in Bp:
        if r in pairAB.values(): continue
        sigB[(comps0[r]['value'],tuple(sorted((p,short(n) if not short(n).startswith(('Net-','unconnected')) else '*') for p,n in pins0[r].items())))].append(r)
    for a in A:
        if a in pairAB: continue
        s=(comps0[a]['value'],tuple(sorted((p,shift(n) if not short(n).startswith(('Net-','unconnected')) else '*') for p,n in pins0[a].items())))
        cand=sigB.get(s,[])
        cand=[b for b in cand if all(bind.get(na) in (None,pins0[b].get(p)) for p,na in pins0[a].items())]
        if len(cand)==1:
            pairAB[a]=cand[0]
            for p,na in pins0[a].items(): bind[na]=pins0[cand[0]][p]
    if len(pairAB)==len(A): break
# ambiguous ones: bind via already-bound auto nets
for it in range(6):
    for a in A:
        if a in pairAB: continue
        cand=[b for b in Bp if b not in pairAB.values() and comps0[b]['value']==comps0[a]['value'] and set(pins0[b])==set(pins0[a])
              and all((bind.get(na)==pins0[b][p]) if na in bind else (shift(na)==short(pins0[b][p]) if not short(na).startswith(('Net-','unconnected')) else True) for p,na in pins0[a].items())]
        if len(cand)==1:
            pairAB[a]=cand[0]
            for p,na in pins0[a].items(): bind[na]=pins0[cand[0]][p]
BtoA={b:a for a,b in pairAB.items()}
unpairedB=[b for b in Bp if b not in BtoA]
def where(b,r):
    if b=='MTR': return ('MTR',r)
    if r in REMOVED: return None
    v=ASSIGN.get(r)
    if r in BtoA: return ('HSO5b',refmap['hso5'][BtoA[r]])
    for bd,c in CARDS.items():
        if bd=='HSO5b': continue
        if r in refmap[c]: return (bd,refmap[c][r])
    if (('MB',r) and any(k[0]=='MB' and k[1]==r for k in [])): pass
    return ('MB',r)
mbrefs=set(mbc)
nmap={}; missing=[]
for (b,r,p),key in bnet.items():
    w=where(b,r)
    if w is None: continue
    if w[0]=='MB' and r not in mbrefs: missing.append(r); continue
    nmap[(b,r,p)]=(w[0],w[1],p)
# ---------- intentional records ----------
intent={}   # baseline node -> reason
for k,v in rw['ov'].items():
    r,p=k.split('.'); intent[('MB',r,p)]=f'mainboard edit -> {v or "NC"}'
for c in set(CARDS.values()):
    fn=os.path.join(R,'cards',c,'net_changes.csv')
    if not os.path.exists(fn): continue
    for row in csv.DictReader(open(fn)):
        if row['baseline_ref']!='(rename)': intent[('MB',row['baseline_ref'],row['pin'])]=f'{c}: {row["why"]}'
        if c=='hso5' and row['baseline_ref'] in pairAB: intent[('MB',pairAB[row['baseline_ref']],row['pin'])]=f'hso5 #2: {row["why"]}'
acc_replaced=collections.defaultdict(set)
for c in set(CARDS.values()):
    for row in csv.DictReader(open(os.path.join(R,'cards',c,'net_accounting.csv'))):
        if row['how'].startswith(('replaced','slot')): acc_replaced[c].add(row['net'])
SLOT_RAIL={'VBAT_P':'VBAT_FIELD','+3V3_SAFE':'+3V3_SLOT','+5V':'+5V_SLOT','OUT_FAULT_N':'CARD_FAULT_N'}
# ---------- compare ----------
groupsB=collections.defaultdict(set)   # baseline system net -> new system nets of its mapped nodes
for bn,nn in nmap.items(): groupsB[bf(bn)].add(f(nn))
groupsN=collections.defaultdict(set)
for bn,nn in nmap.items(): groupsN[f(nn)].add(bf(bn))
def bname(k): return short(k[2]) if k[1]=='net' else str(k)
def nname(k):
    # readable name of a new system net: board-level names joined
    ns=sorted({f'{b}:{short(names[x])}' for x in names if f(x)==k for b in [x[0]]})
    return ' = '.join(ns[:4])+(' ...' if len(ns)>4 else '')
# components of the bipartite baseline<->new relation
adj=collections.defaultdict(set)
for bn,nn in nmap.items():
    a=('B',bf(bn)); c=('N',f(nn)); adj[a].add(c); adj[c].add(a)
seen=set(); comps=[]
for x in adj:
    if x in seen: continue
    st=[x]; g=set()
    while st:
        y=st.pop()
        if y in g: continue
        g.add(y); st+=list(adj[y]-g)
    seen|=g; comps.append(g)
same=0; changes=[]; unexplained=[]
nodes_by_B=collections.defaultdict(list)
for bn,nn in nmap.items(): nodes_by_B[bf(bn)].append(bn)
LVSIG=set()
for row in csv.DictReader(open(os.path.join(R,'docs/modular/slot_pinout_LV.csv'))):
    LVSIG|={row['row_a'],row['row_b'],row['row_c']}
intent[('MTR','J32','12')]='HV meter: J32.12 GND -> MTR_ID_SCL (meter ID EEPROM, cards/tools/meter_eeprom.py)'
for pn in ('12','13','14'): intent[('MB','U47',pn)]='engine card: glow driver U47 supply moved VBAT_P -> VBAT_ESTOP (MODULAR_ARCHITECTURE 9.4 / 9.7-2, re-rated 7.6 A path)'
intent[('MTR','J32','16')]='HV meter: J32.16 spare -> MTR_ID_SDA'
CARDOF={'ENG':'engine','DI8':'di8','AI4':'ai4','HSO5a':'hso5','HSO5b':'hso5','BRK4':'brk4'}
acc_how={}
for c in set(CARDS.values()):
    for row in csv.DictReader(open(os.path.join(R,'cards',c,'net_accounting.csv'))): acc_how[(c,row['net'])]=row['how']
def reason(bn):
    if bn in intent: return intent[bn]
    w=nmap[bn]; card=CARDOF.get(w[0])
    if not card: return None
    nm=short(names[netof[w]]) if w in netof else ''
    how=acc_how.get((card,nm),'')
    if how.startswith(('replaced','intentional')): return f'{card} card: {nm} {how.split(":")[0]} (net_accounting.csv)'
    if card!='engine' and nm in LVSIG: return f'{card} card: universal LV slot signal {nm} -> per-slot backplane net'
    return None
def explain(pieces):
    """pieces: list of (label, [baseline nodes]); at most one piece may lack a reason (it is the home connection)"""
    out=[]; bad=0
    for lab,nodes in pieces:
        rs=[reason(x) for x in nodes]
        out.append((lab,nodes,rs))
    unexp=[o for o in out if any(r is None for r in o[2])]
    if len(unexp)>1:
        # the largest unexplained piece is home; the others are unexplained
        unexp.sort(key=lambda o:-len(o[1])); return out,unexp[1:],unexp[0]
    return out,[],(unexp[0] if unexp else None)
for g in comps:
    Bs=[k for t,k in g if t=='B']; Ns=[k for t,k in g if t=='N']
    if len(Bs)==1 and len(Ns)==1: same+=1; continue
    done=set()
    for bk in Bs:   # splits of a baseline net
        pieces=collections.defaultdict(list)
        for bn in nodes_by_B[bk]: pieces[f(nmap[bn])].append(bn)
        if len(pieces)<2: continue
        out,bad,home=explain([(nk,v) for nk,v in pieces.items()])
        for nk,nodes,rs in out:
            if home and nk==home[0]: continue
            rec=dict(baseline=bname(bk),new=nname(nk),kind='split',nodes=' '.join(f'{b}:{r}.{p}' for b,r,p in nodes[:6])+(' ...' if len(nodes)>6 else ''),n=len(nodes),why='; '.join(sorted({r for r in rs if r})))
            (unexplained if any(o[0]==nk for o in bad) else changes).append(rec); done|=set(nodes)
    for nk in Ns:   # merges into a new net
        contrib=collections.defaultdict(list)
        for bn,nn in nmap.items():
            if f(nn)==nk: contrib[bf(bn)].append(bn)
        if len(contrib)<2: continue
        out,bad,home=explain([(bk,v) for bk,v in contrib.items()])
        for bk,nodes,rs in out:
            if home and bk==home[0]: continue
            if set(nodes)<=done: continue
            rec=dict(baseline=bname(bk),new=nname(nk),kind='merge',nodes=' '.join(f'{b}:{r}.{p}' for b,r,p in nodes[:6])+(' ...' if len(nodes)>6 else ''),n=len(nodes),why='; '.join(sorted({r for r in rs if r})))
            (unexplained if any(o[0]==bk for o in bad) else changes).append(rec)
# ---------- orphan check on every mating contact ----------
orph=[]; cls=collections.Counter()
def others(node):
    if node not in netof: return 0
    k=netof[node]; return sum(1 for x,v in netof.items() if v==k and x!=node)
cache={}
cnt_by_net=collections.Counter(netof.values())
for a,c,lab in pairs:
    ma=cnt_by_net[netof[a]]-1 if a in netof else -1
    mc=cnt_by_net[netof[c]]-1 if c in netof else -1
    na=short(names[netof[a]]) if a in netof else 'NC'; nc=short(names[netof[c]]) if c in netof else 'NC'
    if ma<=0 and mc<=0: cls['both open/NC']+=1; continue
    if ma>0 and mc>0: cls['wired both sides']+=1; continue
    if ma<=0 and re.match(r'SLOT_ID',nc): cls['ID strap open (card pull-up = 1)']+=1; continue
    if mc<=0 and lab.startswith('LV'): cls['slot signal unused by this card (card NC)']+=1; continue
    orph.append((lab,a[2],na,ma,nc,mc))
res=dict(same=same,changes=len(changes),unexplained=len(unexplained),orphans=len(orph),missing_mb_refs=sorted(set(missing)),unpaired_hso_b=[b for b in unpairedB if b not in REMOVED],contacts=dict(cls))
print(json.dumps(res,indent=1))
for x in unexplained[:40]: print('UNEXPLAINED',x)
for o in orph[:40]: print('ORPHAN',o)
with open(os.path.join(R,'docs/modular/system_net_changes.csv'),'w',newline='') as fh:
    w=csv.writer(fh); w.writerow(['kind','baseline_net','new_system_net','baseline_nodes','count','why'])
    for x in sorted(changes,key=lambda d:d['baseline']): w.writerow([x['kind'],x['baseline'],x['new'],x['nodes'],x['n'],x['why']])
    for x in unexplained: w.writerow([x['kind'],x['baseline'],x['new'],x['nodes'],x['n'],'UNEXPLAINED'])
json.dump(res,open(os.path.join(R,'docs/modular/system_audit.json'),'w'),indent=1)
