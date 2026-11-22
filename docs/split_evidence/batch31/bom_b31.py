"""Batch 31: priced split BOM update for the hardware shunt-off gating (U91/U92 74LVC08APW C6053, C320/C321 C14663,
RN1/RN2 4D03WGJ0103T5E C29718, U93 SN74LVC1G17DBVR C7836 already on the order, C322) + one JLC extended-part loading fee (C6053). Prices from bom/lcsc_prices.csv
(live 2026-11-22 ~12:37 PM HST). Cross-check PCB rows vs the netlist and re-total. Run once (copies *.pre_b31.*)."""
import csv,json,re,sys,collections,subprocess,shutil,os
sys.path.insert(0,'/workspace/m7/split/tools'); import bom_from_sch as B
P='/workspace/review/bom_split/'; CHK='2026-11-22 ~12:37 PM HST (Batch 31, m7-split)'
for a,b in (('BOM_main.csv','BOM_main.pre_b31.csv'),('BOM_daughter.csv','BOM_daughter.pre_b31.csv'),('totals.json','totals.pre_b31.json')):
    if not os.path.exists(P+b): shutil.copy(P+a,P+b)
NET={'main':'/tmp/b31/genctl.new.xml','meter':'/tmp/b31/genctl_meter.new.xml'}
for k,p in (('main','genctl'),('meter','genctl_meter')):
    subprocess.run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',NET[k],'/workspace/m7/split/'+p+'.kicad_sch'],check=True,capture_output=True)
PR=B.prices()
def ext(r):
    q=int(r['qty']); r['ext_qty1']=f"{float(r['unit_price_qty1'])*q:.2f}"; r['ext_qty10']=f"{float(r['unit_price_qty10'])*q:.2f}"
out={}
for board,src in (('main','BOM_main.pre_b31.csv'),('meter','BOM_daughter.pre_b31.csv')):
    rows=list(csv.DictReader(open(P+src))); F=list(rows[0].keys())
    if board=='main':
        C=B.load('genctl','kicad-cli',NET['main'])
        cap=[r for r in rows if r['section']=='PCB (JLC SMT/THT)' and r['LCSC']=='C14663' and r['value']=='100n']; assert len(cap)==1
        r=cap[0]; r['ref']+=',C320,C321,C322'; r['qty']=str(int(r['qty'])+3); ext(r); r['notes']+=' | Batch 31: +C320/C321/C322 (U91/U92/U93 decoupling).'
        sb=[r for r in rows if r['section']=='PCB (JLC SMT/THT)' and r['LCSC']=='C7836']; assert len(sb)==1
        r=sb[0]; r['ref']+=',U93'; r['qty']=str(int(r['qty'])+1); ext(r); r['notes']+=' | Batch 31: +U93 (NRST Schmitt buffer for the shunt gate; same part, no new loading fee).'
        last=max(i for i,x in enumerate(rows) if x['section']=='PCB (JLC SMT/THT)')
        new=[]
        for refs,key,val,mpn,mfr,fp,note in (
            ('U91,U92','C6053','74LVC08APW','74LVC08APW,118','Nexperia','Package_SO:TSSOP-14_4.4x5mm_P0.65mm','Batch 31: hardware shunt-off gate, AI_SH_Gx = AI_SH_ENx AND SH_ALLOW, SH_ALLOW = WD_OK AND NRST (U92 gate 3); U92 gate 4 spare'),
            ('RN1,RN2','C29718','10k x4','4D03WGJ0103T5E','UNI-ROYAL','Resistor_SMD:R_Array_Convex_4x0603','Batch 31: gate-side pull-downs AI_SH_G1-6 (2 elements spare)')):
            pr=PR[('main',key)]; g={f:'' for f in F}
            g.update(ref=refs,value=val,MPN=mpn,manufacturer=mfr,LCSC=key,JLC_class=pr['class'],stock=pr['stock'],unit_price_qty1=pr['unit_qty1'],unit_price_qty10=pr['unit_qty10'],qty='2',price_source=pr['source'],checked=CHK,notes=note+' | '+C[refs.split(',')[0]]['src'],section='PCB (JLC SMT/THT)',footprint=fp)
            ext(g); new.append(g)
        rows=rows[:last+1]+new+rows[last+1:]
        fee={f:'' for f in F}; fee.update({'ref':'PCBA (Batch 31)','value':'extended-part loading fee x1: 74LVC08APW,118 C6053 (new unique extended part). C29718 and C14663 are Basic; U93 C7836 is already on the order (U85).','manufacturer':'JLCPCB','unit_price_qty1':'3.07','unit_price_qty10':'0.307','qty':'1','price_source':'JLC PCBA fee table (Oct 22, 2026): $3.07 per unique extended part per order','checked':CHK,'notes':'qty10 column = fee spread over 10 boards, as for the Batch 27-29 rows','section':'Off-board controller'})
        ext(fee); k=max(i for i,x in enumerate(rows) if x['ref'].startswith('PCBA')); rows.insert(k+1,fee)
    out[board]=(F,rows)
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
M=out['main'][1]; D=out['meter'][1]; old=json.load(open(P+'totals.pre_b31.json'))
res={'main_pcb_parts':tot(M,'PCB (JLC SMT/THT)'),'main_offboard':tot(M,'Off-board controller'),'harness':tot(M,'Harness J31-J32'),'main_total':tot(M),
     'daughter_pcb_parts':tot(D,'PCB (JLC SMT/THT)'),'daughter_offboard':tot(D,'Off-board daughter'),'daughter_total':tot(D)}
res['controller_total']=(round(res['main_total'][0]+res['daughter_total'][0],2),round(res['main_total'][1]+res['daughter_total'][1],2))
res['rev4c_csv_sum']=old['rev4c_csv_sum']
res['pcb_refs']=[sum(int(r['qty']) for r in M if r['section']=='PCB (JLC SMT/THT)'),sum(int(r['qty']) for r in D if r['section']=='PCB (JLC SMT/THT)')]; res['pcb_refs'].append(sum(res['pcb_refs']))
res['batch31_delta']={k:(round(res[k][0]-old[k][0],2),round(res[k][1]-old[k][1],2)) for k in ('main_pcb_parts','main_offboard','main_total','daughter_pcb_parts','daughter_offboard','daughter_total','controller_total')}
json.dump(res,open(P+'totals.json','w'),indent=1); print(json.dumps(res))
