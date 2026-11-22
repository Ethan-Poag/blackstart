#!/usr/bin/env python3
"""Per-board BOMs generated from the COMMITTED schematics, and a cross-check against the netlists.

Two KiCad projects since the split: genctl (main board) and genctl_meter (HV metering daughter board).

  python3 tools/bom_from_sch.py            # check: regenerate in memory, diff against the files on disk,
                                           #        and cross-check every BOM row against the netlists
  python3 tools/bom_from_sch.py --write    # (re)write the files below, then run the same check
  options: --kicad-cli PATH, --net-main F.xml, --net-meter F.xml (use existing kicadxml netlists)

Files written (all from the netlist; nothing hand-edited):
  bom/genctl_main_bom.csv, bom/genctl_meter_bom.csv   priced per-board BOMs (fitted groups, then DNP groups, then TOTAL);
                                                       'Sourcing' = the symbol's Sourcing field (e.g. CONSIGN plan, Batch 29)
  bom/harness_bom.csv                                  J31-J32 harness (off-board, from HARNESS below)
  docs/genctl_bom.csv, docs/genctl_meter_bom.csv       Refs,Value,Footprint,MPN,LCSC,Qty,DNP (refs compressed to ranges)
  mechanical/bom.csv, mechanical/bom_meter.csv         Reference,Value,Footprint,QUANTITY (all on-board parts incl. DNP)
Prices come from bom/lcsc_prices.csv (board = main/meter or empty for both; key = LCSC code, or MPN:<mpn> when the part has no LCSC code).
bom/off_board_external_bom.csv is not touched and not checked (historic off-board/estimate rows).
Cross-check: every ref in every written CSV is compared with the netlist (value, footprint, MPN, LCSC, DNP),
Qty must equal the ref count, and every on-board BOM ref must appear exactly once. Exit code 1 on any mismatch."""
import csv,io,os,re,sys,subprocess,tempfile,collections
import xml.etree.ElementTree as ET
here=os.path.dirname(os.path.abspath(__file__)); root=os.path.dirname(here)
PROJECTS=[('main','genctl'),('meter','genctl_meter')]
OUT={'main':dict(bom='bom/genctl_main_bom.csv',docs='docs/genctl_bom.csv',mech='mechanical/bom.csv'),
     'meter':dict(bom='bom/genctl_meter_bom.csv',docs='docs/genctl_meter_bom.csv',mech='mechanical/bom_meter.csv')}
PRICES='bom/lcsc_prices.csv'; HARNESS_CSV='bom/harness_bom.csv'
HARNESS=[  # J31 (main) <-> J32 (meter), ~80 mm, pin n to pin n. Prices: LCSC detail API 2026-11-21 11:14 PM HST.
 dict(Item='HARNESS-1',Qty='2',Description='Micro-Fit 3.0 2x8 receptacle housing',MPN='43025-1600',Manufacturer='Molex',LCSC='C293527',unit1='0.4429',unit10='0.4429',note='LCSC 5+ break, MOQ 5'),
 dict(Item='HARNESS-2',Qty='32',Description='Micro-Fit 3.0 crimp terminal 20-24 AWG (2x16)',MPN='43030-0001',Manufacturer='Molex',LCSC='C259786',unit1='0.0475',unit10='0.0152',note='qty1 buys the 100-piece minimum (1.52 USD); 100+ break'),
 dict(Item='HARNESS-3',Qty='1',Description='Hook-up wire 22-24 AWG UL1007, 16 x ~80 mm',MPN='',Manufacturer='',LCSC='',unit1='0.50',unit10='0.50',note='ESTIMATE'),
]
def nat(r):
    m=re.match(r'([A-Za-z#]+)(\d+)(.*)',r); return (m.group(1),int(m.group(2)),m.group(3)) if m else (r,0,'')
def compress(refs):
    refs=sorted(refs,key=nat); out=[]; i=0
    while i<len(refs):
        j=i
        while j+1<len(refs):
            x,y=nat(refs[j]),nat(refs[j+1])
            if y[0]==x[0] and y[1]==x[1]+1 and not x[2] and not y[2]: j+=1
            else: break
        if j-i>=2: out.append(f'{refs[i]}-{refs[j]}')
        else: out.extend(refs[i:j+1])
        i=j+1
    return ','.join(out)
def expand(s):
    out=[]
    for t in [x.strip() for x in s.split(',') if x.strip()]:
        m=re.match(r'^([A-Za-z#]+)(\d+)-([A-Za-z#]+)?(\d+)$',t)
        if m: out+= [f'{m.group(1)}{n}' for n in range(int(m.group(2)),int(m.group(4))+1)]
        else: out.append(t)
    return out
def lcsc_ok(x): return bool(re.match(r'^C\d+$',(x or '').strip()))
def load(project,cli,net=None):
    if not net:
        net=os.path.join(tempfile.mkdtemp(),project+'.xml')
        subprocess.run([cli,'sch','export','netlist','--format','kicadxml','-o',net,os.path.join(root,project+'.kicad_sch')],check=True,capture_output=True)
    comps={}
    for c in ET.parse(net).getroot().iter('comp'):
        ref=c.get('ref')
        if ref.startswith('#'): continue
        f={x.get('name'):(x.text or '').strip() for x in c.iter('field')}
        props={p.get('name'):p.get('value') for p in c.iter('property')}
        comps[ref]=dict(value=c.findtext('value') or '',fp=c.findtext('footprint') or '',lcsc=f.get('LCSC','') if lcsc_ok(f.get('LCSC','')) else '',
                        mpn=f.get('MPN',''),man=f.get('Manufacturer',''),src=f.get('Sourcing',''),dnp='dnp' in props,inbom='exclude_from_bom' not in props)
    return comps
def groups(comps):
    g=collections.OrderedDict()
    for ref in sorted(comps,key=nat):
        c=comps[ref]
        if not c['inbom']: continue
        k=(c['dnp'],c['lcsc'],c['mpn'],c['value'],c['fp'],c['man'])
        g.setdefault(k,[]).append(ref)
    return sorted(g.items(),key=lambda kv:(kv[0][0],nat(kv[1][0])))
def pkey(lcsc,mpn): return lcsc if lcsc else 'MPN:'+mpn.upper()
def prices():
    P={}
    p=os.path.join(root,PRICES)
    if os.path.exists(p):
        for r in csv.DictReader(open(p,encoding='utf-8')): P[(r['board'],r['key'])]=r
    return P
def csvtext(header,rows):
    o=io.StringIO(); w=csv.writer(o,quoting=csv.QUOTE_ALL,lineterminator='\n'); w.writerow(header); [w.writerow(r) for r in rows]; return o.getvalue()
def f2(x):
    try: return float(x)
    except (TypeError,ValueError): return None
def build(comps,P,board):
    G=groups(comps); bom=[]; docs=[]; mech=[]; t1=t10=0.0; unpriced=[]
    for (dnp,lcsc,mpn,val,fp,man),refs in G:
        n=len(refs); pr=(P.get((board,pkey(lcsc,mpn))) or P.get(('',pkey(lcsc,mpn))) or {}) if (lcsc or mpn) else {}
        u1,u10=f2(pr.get('unit_qty1')),f2(pr.get('unit_qty10'))
        e1=e10=''
        if not dnp:
            if u1 is None or u10 is None: unpriced.append(','.join(refs))
            else: e1=f'{u1*n:.2f}'; e10=f'{u10*n:.2f}'; t1+=u1*n; t10+=u10*n
        bom.append([compress(refs),str(n),val,fp,mpn,man,lcsc or pr.get('lcsc_note',''),pr.get("class",""),pr.get('unit_qty1',''),pr.get('unit_qty10',''),
                    '' if dnp else e1,'' if dnp else e10,pr.get('source',''),'DNP' if dnp else '',comps[refs[0]]['src']])
        docs.append([compress(refs),val,fp,mpn,lcsc,str(n),'DNP' if dnp else ''])
        mech.append([compress(refs),val,fp,str(n)])
    bom.append([f'TOTAL {board} board parts (fitted rows only; unpriced: {len(unpriced)})','','','','','','','','','',f'{t1:.2f}',f'{t10:.2f}','sum(qty x unit) over priced fitted rows; qty10 = per-board cost at 10 boards','',''])
    H=['Refs','Qty','Value','Footprint','MPN','Manufacturer','LCSC','JLC class','Unit USD qty1','Unit USD qty10','Ext USD qty1','Ext USD qty10','Price source','DNP','Sourcing']
    return {OUT[board]['bom']:csvtext(H,bom),OUT[board]['docs']:csvtext(['Refs','Value','Footprint','MPN','LCSC','Qty','DNP'],docs),
            OUT[board]['mech']:csvtext(['Reference','Value','Footprint','QUANTITY'],mech)},(round(t1,2),round(t10,2)),unpriced
def harness():
    rows=[];t1=t10=0.0
    for h in HARNESS:
        q=int(h['Qty']); e1=float(h['unit1'])*q; e10=float(h['unit10'])*q; t1+=e1; t10+=e10
        rows.append([h['Item'],h['Qty'],h['Description'],h['MPN'],h['Manufacturer'],h['LCSC'],h['unit1'],h['unit10'],f'{e1:.2f}',f'{e10:.2f}',h['note']])
    rows.append(['TOTAL harness','','','','','','','',f'{t1:.2f}',f'{t10:.2f}','one harness per controller'])
    return csvtext(['Item','Qty','Description','MPN','Manufacturer','LCSC','Unit USD qty1','Unit USD qty10','Ext USD qty1','Ext USD qty10','Notes'],rows),(round(t1,2),round(t10,2))
def crosscheck(path,text,comps,kind):
    """Compare one written CSV with the netlist, ref by ref. Returns a list of mismatch strings."""
    bad=[]; seen=collections.Counter()
    for r in list(csv.DictReader(io.StringIO(text))):
        refcol='Refs' if 'Refs' in r else 'Reference'
        if r[refcol].startswith('TOTAL'): continue
        refs=expand(r[refcol]); q=r.get('Qty',r.get('QUANTITY'))
        if str(len(refs))!=q: bad.append(f'{path}: {r[refcol]} qty {q} != {len(refs)} refs')
        for ref in refs:
            seen[ref]+=1; c=comps.get(ref)
            if c is None: bad.append(f'{path}: {ref} not in netlist'); continue
            if not c['inbom']: bad.append(f'{path}: {ref} is exclude_from_bom')
            if r['Value']!=c['value']: bad.append(f'{path}: {ref} value {r["Value"]!r} != {c["value"]!r}')
            if r['Footprint']!=c['fp']: bad.append(f'{path}: {ref} footprint {r["Footprint"]!r} != {c["fp"]!r}')
            if 'MPN' in r and r['MPN']!=c['mpn']: bad.append(f'{path}: {ref} MPN {r["MPN"]!r} != {c["mpn"]!r}')
            if 'LCSC' in r and (r['LCSC'] if lcsc_ok(r['LCSC']) else '')!=c['lcsc']: bad.append(f'{path}: {ref} LCSC {r["LCSC"]!r} != {c["lcsc"]!r}')
            if 'DNP' in r and (r['DNP']=='DNP')!=c['dnp']: bad.append(f'{path}: {ref} DNP flag {r["DNP"]!r} != {c["dnp"]}')
    want={k for k,c in comps.items() if c['inbom']}
    for k in sorted(want-set(seen),key=nat): bad.append(f'{path}: {k} missing')
    for k,n in seen.items():
        if n>1: bad.append(f'{path}: {k} listed {n} times')
    return bad,len(seen)
def main():
    a=sys.argv[1:]; cli=a[a.index('--kicad-cli')+1] if '--kicad-cli' in a else 'kicad-cli'
    nets={'main':a[a.index('--net-main')+1] if '--net-main' in a else None,'meter':a[a.index('--net-meter')+1] if '--net-meter' in a else None}
    P=prices(); files={}; tot={}; mism=[]; allunp=[]
    C={b:load(p,cli,nets[b]) for b,p in PROJECTS}
    for b,p in PROJECTS:
        fl,t,unp=build(C[b],P,b); files.update(fl); tot[b]=t; allunp+=[(b,u) for u in unp]
    h,tot['harness']=harness(); files[HARNESS_CSV]=h
    if '--write' in a:
        for k,v in files.items(): open(os.path.join(root,k),'w',encoding='utf-8',newline='').write(v)
    for k,v in files.items():
        p=os.path.join(root,k); disk=open(p,encoding='utf-8').read() if os.path.exists(p) else None
        if disk!=v: mism.append(f'{k}: file on disk differs from the netlist-generated content (run --write)')
    for b,_ in PROJECTS:
        for kind in ('bom','docs','mech'):
            k=OUT[b][kind]; p=os.path.join(root,k)
            text=open(p,encoding='utf-8').read() if os.path.exists(p) else files[k]
            bad,n=crosscheck(k,text,C[b],kind); mism+=bad
            print(f'{k:28s} refs checked {n:5d}  mismatches {len(bad)}')
    for b,u in allunp: print(f'UNPRICED {b}: {u}')
    for m in mism: print('MISMATCH',m)
    print('TOTALS (USD, qty1 / qty10 per board):',tot)
    print('SUMMARY mismatches %d'%len(mism)); sys.exit(1 if mism else 0)
if __name__=='__main__': main()
