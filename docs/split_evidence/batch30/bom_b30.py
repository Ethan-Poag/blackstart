"""Batch 30: refresh the priced split BOM for the stock/price re-check (J2, U5, U15/U16, U21, RV1-RV6) and the
off-board CT pigtail/gland rows. Prices/stock from /workspace/m7/split/bom/lcsc_prices.csv (live 2026-11-22 ~12:08 HST);
Sourcing text from the schematic Sourcing field (netlist). Then cross-check PCB rows vs the netlist and re-total."""
import csv,json,re,sys,collections,subprocess
sys.path.insert(0,'/workspace/m7/split/tools'); import bom_from_sch as B
P='/workspace/review/bom_split/'; CHK='2026-11-22 ~12:08 HST (Batch 30, m7-split)'
NET={'main':'/tmp/b30/genctl.new.xml','meter':'/tmp/b30/genctl_meter.new.xml'}
for k,p in (('main','genctl'),('meter','genctl_meter')):
    subprocess.run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',NET[k],'/workspace/m7/split/'+p+'.kicad_sch'],check=True,capture_output=True)
PR=B.prices(); KEYS={'C5199898','C2870127','C2653785','C2871688','C3260792'}
out={}
for board,src in (('main','BOM_main.pre_b30.csv'),('meter','BOM_daughter.pre_b30.csv')):
    C=B.load({'main':'genctl','meter':'genctl_meter'}[board],'kicad-cli',NET[board])
    rows=list(csv.DictReader(open(P+src))); F=list(rows[0].keys()); new=[]
    for r in rows:
        if r['section']=='PCB (JLC SMT/THT)' and r['LCSC'] in KEYS:
            pr=PR.get((board,r['LCSC'])) or PR.get(('',r['LCSC'])); q=int(r['qty'])
            r.update(stock=pr['stock'],unit_price_qty1=pr['unit_qty1'],unit_price_qty10=pr['unit_qty10'],price_source=pr['source'],checked=CHK)
            r['ext_qty1']=f"{float(r['unit_price_qty1'])*q:.2f}"; r['ext_qty10']=f"{float(r['unit_price_qty10'])*q:.2f}"
            r['notes']=C[r['ref'].split(',')[0]]['src']+' | earlier note: '+r['notes']
        if r['ref']=='J30 CT pigtails (Batch 29)':
            r.update(ref='CT pigtail set (Batch 29/30)',value='4 continuous loops of UL1015 14 AWG 600 V 105 C (221 F) wire, factory-threaded once through T1-T4 (ZMCT103C, 5 mm window), 8 ends x ~0.75 m (6 m) + 8 insulated ferrules + cable ties; J30 = site-supplied shorting-type CT block (not priced)',unit_price_qty1='6.00',unit_price_qty10='6.00',ext_qty1='6.00',ext_qty10='6.00',price_source='ESTIMATE (wire ~1 USD/m, not quoted)',checked=CHK,notes='Batch 30: gland split out to its own row. Install rules INSTALL_SAFETY.md; per-board megger BENCH_12V_TEST B30-1.')
            new.append(r)
            g={f:'' for f in F}; g.update(ref='CT cable gland (Batch 30)',value='one M25 cable gland for the 8 CT pigtail leads (bundle ~11-13 mm; M20 marginal), multi-hole/split insert, IP54+, nylon; near the old J30 left-edge spot, away from J32/SELV',qty='1',unit_price_qty1='4.00',unit_price_qty10='4.00',ext_qty1='4.00',ext_qty10='4.00',price_source='ESTIMATE (not quoted)',checked=CHK,notes='Was "1 grommet" inside the $7 pigtail estimate. Size per Mechanical ZMCT103C_fit.md (M25).',section=r['section'])
            new.append(g); continue
        new.append(r)
    out[board]=(F,new)
for board,name in (('main','BOM_main.csv'),('meter','BOM_daughter.csv')):
    F,rows=out[board]; w=csv.DictWriter(open(P+name,'w',newline=''),fieldnames=F); w.writeheader(); w.writerows(rows)
mism=[]
for board,name,proj in (('main','BOM_main.csv','genctl'),('meter','BOM_daughter.csv','genctl_meter')):
    C=B.load(proj,'kicad-cli',NET[board]); seen=collections.Counter()
    for r in csv.DictReader(open(P+name)):
        if r['section']!='PCB (JLC SMT/THT)': continue
        refs=[x.strip() for x in r['ref'].split(',')]
        if int(r['qty'])!=len(refs): mism.append((name,r['ref'][:30],'qty'))
        for ref in refs:
            seen[ref]+=1; c=C.get(ref)
            if not c: mism.append((name,ref,'not in netlist')); continue
            if c['dnp'] or not c['inbom']: mism.append((name,ref,'DNP'))
            if c['value'] not in set(r['value'].split(' / ')): mism.append((name,ref,'value'))
            if c['fp'] not in set(r['footprint'].split(' / ')): mism.append((name,ref,'fp'))
            rl=r['LCSC'].strip() if re.match(r'^C\d+$',r['LCSC'].strip()) else ''
            if rl!=c['lcsc'] and not (r['MPN']=='228EMVARGBFR' and c['lcsc']=='C6077135'): mism.append((name,ref,'LCSC'))
            if c['mpn']!=r['MPN']: mism.append((name,ref,'MPN'))
    want={k for k,c in C.items() if c['inbom'] and not c['dnp']}
    mism+=[(name,k,'missing') for k in sorted(want-set(seen))]+[(name,k,'dup') for k,n in seen.items() if n>1]
    print(name,'PCB refs',sum(seen.values()),'fitted',len(want))
for m in mism: print('MISMATCH',m)
print('crosscheck mismatches',len(mism))
def tot(lst,sec=None): return (round(sum(float(r['ext_qty1'] or 0) for r in lst if sec is None or r['section']==sec),2),round(sum(float(r['ext_qty10'] or 0) for r in lst if sec is None or r['section']==sec),2))
M=out['main'][1]; D=out['meter'][1]; old=json.load(open(P+'totals.pre_b30.json'))
res={'main_pcb_parts':tot(M,'PCB (JLC SMT/THT)'),'main_offboard':tot(M,'Off-board controller'),'harness':tot(M,'Harness J31-J32'),'main_total':tot(M),
     'daughter_pcb_parts':tot(D,'PCB (JLC SMT/THT)'),'daughter_offboard':tot(D,'Off-board daughter'),'daughter_total':tot(D)}
res['controller_total']=(round(res['main_total'][0]+res['daughter_total'][0],2),round(res['main_total'][1]+res['daughter_total'][1],2))
res['rev4c_csv_sum']=old['rev4c_csv_sum']
res['pcb_refs']=[sum(int(r['qty']) for r in M if r['section']=='PCB (JLC SMT/THT)'),sum(int(r['qty']) for r in D if r['section']=='PCB (JLC SMT/THT)')]; res['pcb_refs'].append(sum(res['pcb_refs']))
res['batch30_delta']={k:(round(res[k][0]-old[k][0],2),round(res[k][1]-old[k][1],2)) for k in ('main_pcb_parts','main_offboard','main_total','daughter_pcb_parts','daughter_offboard','daughter_total','controller_total')}
json.dump(res,open(P+'totals.json','w'),indent=1); print(json.dumps(res,indent=1))
