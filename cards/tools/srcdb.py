"""Read the locked baseline schematics (read-only) and the kicad-cli netlist: per ref -> units, lib symbol, properties, pin nets."""
import os,sys,re,subprocess,json,collections,functools
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0,os.path.join(ROOT,'tools'))
from sexp import parse,find,find1,Sym
MAIN_SHEETS=['power','mcu','cm5','comms','display','inputs','outputs','estop','mtr_if','frontpanel']
NET_CACHE='/tmp/cards_base'
def base_netlist(proj='genctl'):
    """Export the netlist of the LOCKED baseline (git tag) into /tmp, never the working tree."""
    os.makedirs(NET_CACHE,exist_ok=True)
    d=os.path.join(NET_CACHE,'src'); net=os.path.join(NET_CACHE,proj+'.net')
    if not os.path.exists(net):
        subprocess.run(['rm','-rf',d]); os.makedirs(d)
        subprocess.run(f'git -C {ROOT} archive baseline-2026-11-23-locked | tar -x -C {d}',shell=True,check=True)
        subprocess.run(['kicad-cli','sch','export','netlist','-o',net,os.path.join(d,proj+'.kicad_sch')],check=True,capture_output=True)
    return net,d
@functools.lru_cache(None)
def load(proj='genctl'):
    net,d=base_netlist(proj)
    sys.path.insert(0,'/workspace/review/springy/blocks')
    from parse_net import load as ln
    comps,nets=ln(net)
    pinnet={}
    for n in nets:
        for r,p in n['nodes']: pinnet[(r,p)]=n['name']
    inst=collections.defaultdict(list); libs={}
    sheets=MAIN_SHEETS if proj=='genctl' else ['ac_metering','genctl_meter']
    for s in sheets:
        t=parse(open(os.path.join(d,s+'.kicad_sch')).read())[0]
        for L in find1(t,'lib_symbols')[1:]: libs.setdefault(L[1],L)
        for x in find(t,'symbol'):
            lid=find1(x,'lib_id')[1]
            props={p[1]:p[2] for p in find(x,'property')}
            ref=props.get('Reference','')
            if ref.startswith('#'): continue
            inst[ref].append(dict(lib_id=lid,unit=int(find1(x,'unit')[1]),props=props,
                                  dnp=find1(x,'dnp') and find1(x,'dnp')[1]=='yes',sheet=s))
    return comps,nets,pinnet,inst,libs
def short(n): return n.split('/')[-1]
