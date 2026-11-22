"""Batch 29: regenerate the priced split BOM (PCB rows) from the m7-split netlists, one file per board.
PCB rows are grouped per board by LCSC code (or MPN when there is none); refs/qty/values/footprints come from the
netlist. Prices and sourcing fields come from the previous rows (same key) or, for new parts, from
/workspace/m7/split/bom/lcsc_prices.csv (JLC API live 2026-11-22). Off-board and harness rows are carried over.
Then every PCB row is cross-checked against the netlist (ref set, values, footprints, LCSC, qty)."""
import csv,json,re,sys,collections
sys.path.insert(0,'/workspace/m7/split/tools'); import bom_from_sch as B
P='/workspace/review/bom_split/'; CHK='2026-11-22 HST (Batch 29, m7-split)'
NET={'main':'/workspace/review/fix29/b29_genctl.xml','meter':'/workspace/review/fix29/b29_genctl_meter.xml'}
PR=B.prices()
REFRESH={'C22414694','C5216434','C141570'}
def key_of_row(r):
    l=r['LCSC'].strip(); return l if re.match(r'^C\d+$',l) else ('C6077135' if r['MPN']=='228EMVARGBFR' else 'MPN:'+r['MPN'].strip().upper())
out={}; report={}
for board,src,proj in (('main','BOM_main.pre_b29.csv','genctl'),('meter','BOM_daughter.pre_b29.csv','genctl_meter')):
    old=list(csv.DictReader(open(P+src))); F=list(old[0].keys())+(['footprint'] if 'footprint' not in old[0] else [])
    oldpcb={key_of_row(r):r for r in old if r['section']=='PCB (JLC SMT/THT)'}
    C=B.load(proj,'kicad-cli',NET[board])
    G=collections.OrderedDict()
    for ref in sorted(C,key=B.nat):
        c=C[ref]
        if not c['inbom'] or c['dnp']: continue
        G.setdefault(B.pkey(c['lcsc'],c['mpn']),[]).append(ref)
    rows=[]; added=[]; changed=[]
    for k,refs in G.items():
        vals=list(dict.fromkeys(C[r]['value'] for r in refs)); fps=list(dict.fromkeys(C[r]['fp'] for r in refs))
        if k in oldpcb:
            n=dict(oldpcb[k]); oq=int(n['qty'])
            if set(x.strip() for x in n['ref'].split(','))!=set(refs) or n['value']!=' / '.join(vals): changed.append((k,oq,len(refs))); n['checked']=CHK
            if k in REFRESH:
                pr=PR.get((board,k)) or PR.get(('',k)); n.update(stock=pr['stock'],unit_price_qty1=pr['unit_qty1'],unit_price_qty10=pr['unit_qty10'],price_source=pr['source'],checked=CHK)
                n['notes']=(C[refs[0]]['src'] or n['notes'])
        else:
            pr=PR.get((board,k)) or PR.get(('',k)); c=C[refs[0]]
            n={f:'' for f in F}; n.update(MPN=c['mpn'],manufacturer=c['man'],LCSC=c['lcsc'],JLC_class=pr['class'],stock=pr['stock'],unit_price_qty1=pr['unit_qty1'],unit_price_qty10=pr['unit_qty10'],price_source=pr['source'],checked=CHK,notes=('Batch 29: new part. '+c['src']).strip(),section='PCB (JLC SMT/THT)'); added.append(k)
        n['ref']=','.join(refs); n['qty']=str(len(refs)); n['value']=' / '.join(vals); n['footprint']=' / '.join(fps)
        q=len(refs); n['ext_qty1']=f"{float(n['unit_price_qty1'])*q:.2f}"; n['ext_qty10']=f"{float(n['unit_price_qty10'])*q:.2f}"
        rows.append(n)
    removed=[(k,oldpcb[k]['ref'][:40]) for k in oldpcb if k not in G]
    for r in old:
        if r['section']=='PCB (JLC SMT/THT)': continue
        r=dict(r); r.setdefault('footprint','')
        if r['ref']=='J30 mate':
            r.update(ref='J30 CT pigtails (Batch 29)',value='4 CT loops of UL1015 14 AWG 600 V 105 C wire, factory-threaded once through T1-T4 (ZMCT103C, 5 mm window), 8 ends x ~0.75 m (6 m) + 8 ferrules + 1 grommet; J30 itself = site CT shorting/test terminal block in the genset panel (site-supplied, not priced)',MPN='',manufacturer='',LCSC='',JLC_class='',stock='',qty='1',unit_price_qty1='7.00',unit_price_qty10='7.00',ext_qty1='7.00',ext_qty10='7.00',price_source='ESTIMATE (wire ~1 USD/m, not quoted)',checked=CHK,notes='Batch 29 (pass-3 B1): replaces the J30 Kefa plug C2974987; the board header C441294 is gone. Never open a CT loop or disconnect J30 with the generator live (INSTALL_SAFETY.md).',footprint='')
        if r['ref']=='coating': r['notes']=r['notes'].replace('J28/J29/J30','J28/J29')+' | Batch 29: J30 no longer on the board'
        rows.append(r)
    if board=='main':
        n={f:'' for f in F}; n.update(ref='PCBA (Batch 29)',value='extended-part loading fee: net 0. RT2010BKD07100RL C876535 (new extended) replaces AR06BTCV1000 C319961 (extended, now unused); TPS3431SDRBR C702145 replaces TPS3431SQDRBRQ1 C2878091 (both consigned); RT0603BRD07100KL C122538 / RT0603BRD0718KL C309650 already on this order; 2.7k C13167, 1n C1588, 1k C21190 are Basic',manufacturer='JLCPCB',qty='1',unit_price_qty1='0.00',unit_price_qty10='0.00',ext_qty1='0.00',ext_qty10='0.00',price_source='JLC PCBA fee table (Oct 22, 2026): $3.07 per unique extended part per order',checked=CHK,notes='Consignment handling (TPS1HTC30A x16, TPS3431SDRBR, SQD40P10 x2) is not priced: JLC global-sourcing/consignment fees not quoted',section='Off-board controller'); rows.append(n)
    out[board]=(F,rows); report[board]=dict(added=added,removed=removed,changed=changed)
for board,name in (('main','BOM_main.csv'),('meter','BOM_daughter.csv')):
    F,rows=out[board]; w=csv.DictWriter(open(P+name,'w',newline=''),fieldnames=F); w.writeheader(); w.writerows(rows)
# ---- cross-check vs netlist ----
mism=[]
for board,name,proj in (('main','BOM_main.csv','genctl'),('meter','BOM_daughter.csv','genctl_meter')):
    C=B.load(proj,'kicad-cli',NET[board]); seen=collections.Counter()
    for r in csv.DictReader(open(P+name)):
        if r['section']!='PCB (JLC SMT/THT)': continue
        refs=[x.strip() for x in r['ref'].split(',')]
        if int(r['qty'])!=len(refs): mism.append((name,r['ref'][:30],'qty'))
        vals=set(r['value'].split(' / ')); fps=set(r['footprint'].split(' / '))
        for ref in refs:
            seen[ref]+=1; c=C.get(ref)
            if not c: mism.append((name,ref,'not in netlist')); continue
            if c['dnp'] or not c['inbom']: mism.append((name,ref,'DNP/excluded but listed'))
            if c['value'] not in vals: mism.append((name,ref,'value',c['value'],r['value']))
            if c['fp'] not in fps: mism.append((name,ref,'footprint',c['fp'],r['footprint']))
            rl=r['LCSC'].strip() if re.match(r'^C\d+$',r['LCSC'].strip()) else ''
            if rl!=c['lcsc'] and not (r['MPN']=='228EMVARGBFR' and c['lcsc']=='C6077135'): mism.append((name,ref,'LCSC',c['lcsc'],r['LCSC']))
            if c['mpn']!=r['MPN']: mism.append((name,ref,'MPN',c['mpn'],r['MPN']))
    want={k for k,c in C.items() if c['inbom'] and not c['dnp']}
    mism+= [(name,k,'missing') for k in sorted(want-set(seen))]+[(name,k,'dup') for k,n in seen.items() if n>1]
    print(name,'PCB refs',sum(seen.values()),'fitted in netlist',len(want))
for m in mism: print('MISMATCH',m)
print('crosscheck mismatches',len(mism))
# ---- totals ----
def tot(lst,sec=None):
    return (round(sum(float(r['ext_qty1'] or 0) for r in lst if sec is None or r['section']==sec),2),round(sum(float(r['ext_qty10'] or 0) for r in lst if sec is None or r['section']==sec),2))
M=out['main'][1]; D=out['meter'][1]; old=json.load(open(P+'totals.pre_b29.json'))
res={'main_pcb_parts':tot(M,'PCB (JLC SMT/THT)'),'main_offboard':tot(M,'Off-board controller'),'harness':tot(M,'Harness J31-J32'),'main_total':tot(M),
     'daughter_pcb_parts':tot(D,'PCB (JLC SMT/THT)'),'daughter_offboard':tot(D,'Off-board daughter'),'daughter_total':tot(D)}
res['controller_total']=(round(res['main_total'][0]+res['daughter_total'][0],2),round(res['main_total'][1]+res['daughter_total'][1],2))
res['rev4c_csv_sum']=old['rev4c_csv_sum']
res['pcb_refs']=[sum(int(r['qty']) for r in M if r['section']=='PCB (JLC SMT/THT)'),sum(int(r['qty']) for r in D if r['section']=='PCB (JLC SMT/THT)')]; res['pcb_refs'].append(sum(res['pcb_refs']))
res['batch29_delta']={k:(round(res[k][0]-old[k][0],2),round(res[k][1]-old[k][1],2)) for k in ('main_pcb_parts','main_offboard','main_total','daughter_pcb_parts','daughter_total','controller_total')}
res['batch29_changes']=report
json.dump(res,open(P+'totals.json','w'),indent=1); print(json.dumps({k:v for k,v in res.items() if k!='batch29_changes'},indent=1)); print(json.dumps(report,indent=1))
