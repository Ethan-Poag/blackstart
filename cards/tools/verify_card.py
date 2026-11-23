"""Check a generated card against the locked baseline netlist.
1) every moved part keeps its baseline pin->net connectivity (modulo documented overrides)
2) every baseline net touching the card is accounted for: internal / slot connector pin / field header.
Writes cards/<name>/net_accounting.csv and unaccounted_nets.txt (must be empty)."""
import sys,os,json,subprocess,collections,csv,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from srcdb import load,short,ROOT
from sexp import parse
def card_netlist(name):
    d=os.path.join(ROOT,'cards',name); out=f'/tmp/{name}_card.net'
    subprocess.run(['kicad-cli','sch','export','netlist','-o',out,os.path.join(d,name+'.kicad_sch')],check=True,capture_output=True)
    t=parse(open(out).read())[0]; pin={}; refs={}
    for c in [x for x in t if isinstance(x,list) and x[0]=='components'][0][1:]:
        r=[x for x in c if x[0]=='ref'][0][1]
        for x in c:
            if x[0]=='property' and [y for y in x if y[0]=='name'][0][1]=='BaselineRef': refs[r]=[y for y in x if y[0]=='value'][0][1]
    allrefs=[[x for x in c if x[0]=='ref'][0][1] for c in [x for x in t if isinstance(x,list) and x[0]=='components'][0][1:]]
    dup=[r for r,k in collections.Counter(allrefs).items() if k>1]
    assert not dup,('duplicate refs',dup)
    for n in [x for x in t if isinstance(x,list) and x[0]=='nets'][0][1:]:
        nm=short([x for x in n if x[0]=='name'][0][1])
        for nd in [x for x in n if x[0]=='node']:
            pin[([y for y in nd if y[0]=='ref'][0][1],[y for y in nd if y[0]=='pin'][0][1])]=nm
    return pin,refs
def verify(name,slot_pins,field_refs,overrides,netmap):
    comps,nets,pinnet,_,_=load('genctl'); base={'nets':nets,'pinnet':pinnet}; pin,refs=card_netlist(name)
    inv={v:k for k,v in refs.items()}
    moved=set(refs.values()); errs=[]
    # 1) connectivity: baseline net <-> card net must be a 1:1 mapping over the moved pins
    #    (wired-only nets get KiCad auto names on the card; documented overrides excluded)
    fwd=collections.defaultdict(set); rev=collections.defaultdict(set)
    for (r,p),n in base['pinnet'].items():
        if r not in moved: continue
        got=pin.get((inv[r],p))
        if (r,p) in overrides:
            if got!=overrides[(r,p)]: errs.append(f'{r}.{p}: override {overrides[(r,p)]} card {got}')
            continue
        b=netmap.get(n,short(n))
        if b.startswith('unconnected-'):
            if got and not got.startswith('unconnected-'): errs.append(f'{r}.{p}: baseline NC card {got}')
            continue
        fwd[b].add(got); rev[got].add(b)
    for b,g in fwd.items():
        if len(g)!=1: errs.append(f'baseline net {b} split on card into {sorted(map(str,g))}')
    for g,b in rev.items():
        if len(b)!=1: errs.append(f'card net {g} merges baseline nets {sorted(b)}')
    named=[(b,list(g)[0]) for b,g in fwd.items() if len(g)==1 and not list(g)[0].startswith('Net-(') and not b.startswith('Net-(') and list(g)[0]!=b]
    for b,g in named: errs.append(f'baseline net {b} renamed on card to {g}')
    # 2) accounting
    rows=[]; unacc=[]
    for n in base['nets']:
        nodes=n['nodes']; on=[f'{r}.{p}' for r,p in nodes if r in moved]; off=[f'{r}.{p}' for r,p in nodes if r not in moved]
        if not on: continue
        nm=netmap.get(n['name'],short(n['name']))
        if (nm.startswith('unconnected-')): how='nc (unchanged)'
        elif not off: how='internal to card'
        elif nm in slot_pins: how='slot connector '+' '.join(sorted(slot_pins[nm],key=lambda x:(x[0],int(x[1:]))))
        elif nm in field_refs: how='card field header '+field_refs[nm]+' (mainboard terminal '+','.join(o for o in off if o.startswith('J'))+' becomes NC)'
        else: how='UNACCOUNTED'; unacc.append(nm)
        rows.append([nm,len(on),len(off),how,' '.join(off[:8])+(' ...' if len(off)>8 else '')])
    d=os.path.join(ROOT,'cards',name)
    with open(os.path.join(d,'net_accounting.csv'),'w',newline='') as f:
        w=csv.writer(f); w.writerow(['net','card_nodes','mainboard_nodes','how','mainboard_nodes_sample']); w.writerows(sorted(rows))
    open(os.path.join(d,'unaccounted_nets.txt'),'w').write(''.join(x+'\n' for x in unacc))
    print(name,'moved',len(moved),'nets',len(rows),'unaccounted',len(unacc),unacc,'connectivity errors',len(errs)); [print(' ',e) for e in errs[:20]]
    return errs,unacc
