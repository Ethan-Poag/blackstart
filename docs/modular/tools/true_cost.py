"""True net cost delta, modular build vs the locked one-board baseline, from ACTUAL BOM extraction.
Example build: mainboard (reworked, bom/genctl_main_bom.csv) + ENGINE + DI-8 + AI-4 + HSO-5 x2 + BRK-4 + HV meter (with ID EEPROM).
Baseline: tag baseline-2026-11-23-locked bom/genctl_main_bom.csv + bom/genctl_meter_bom.csv.
Part prices: the regenerated BOMs (bom_from_sch.py over bom/lcsc_prices.csv); card BOM lines priced from the same table.
Boards and mechanics for the 5 extra card designs are estimates [E] or JLC fee table [DS]. Same harness in both builds (cancels)."""
import csv,os,io,subprocess,collections
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
def total(text):
    for r in csv.DictReader(io.StringIO(text)):
        if r['Refs'].startswith('TOTAL'): return float(r['Ext USD qty1']),float(r['Ext USD qty10'])
def tag(p): return subprocess.run(['git','-C',R,'show',f'baseline-2026-11-23-locked:{p}'],capture_output=True,text=True,check=True).stdout
P={}
for r in csv.DictReader(open(os.path.join(R,'bom/lcsc_prices.csv'))): P.setdefault(r['key'],(float(r['unit_qty1']),float(r['unit_qty10'])))
for t in (open(os.path.join(R,'bom/genctl_main_bom.csv')).read(),tag('bom/genctl_main_bom.csv')):
    for r in csv.DictReader(io.StringIO(t)):
        if r['LCSC'] and r['Unit USD qty1']: P.setdefault(r['LCSC'],(float(r['Unit USD qty1']),float(r['Unit USD qty10'])))
PX={'C5173361':(1.2659,1.061),'C147891':(1.4297,1.1721),'C128577':(1.7271,1.4661)}   # LCSC detail API this phase (card-only parts)
for k,v in PX.items(): P.setdefault(k,v)
rows=[]; unpriced=[]
def add(g,item,q,p1,p10,src): rows.append((g,item,q,p1,p10,src))
b1,b10=total(tag('bom/genctl_main_bom.csv')); m1,m10=total(tag('bom/genctl_meter_bom.csv'))
n1,n10=total(open(os.path.join(R,'bom/genctl_main_bom.csv')).read()); nm1,nm10=total(open(os.path.join(R,'bom/genctl_meter_bom.csv')).read())
add('baseline','Locked one-board mainboard BOM (tag)',-1,b1,b10,'BOM')
add('baseline','Locked HV meter BOM (tag)',-1,m1,m10,'BOM')
add('mainboard','Reworked mainboard BOM (bom/genctl_main_bom.csv: backplane, slot power, ideal diode, rail cut)',1,n1,n10,'BOM')
add('hv meter','HV meter BOM with ID EEPROM (bom/genctl_meter_bom.csv)',1,nm1,nm10,'BOM')
inst={'engine':1,'di8':1,'ai4':1,'hso5':2,'brk4':1}
card_tot={}; card_parts={}
for c,n in inst.items():
    t1=t10=0; q=0
    for r in csv.DictReader(open(os.path.join(R,'cards',c,f'{c}_bom.csv'))):
        k=int(r['Qty']); q+=k
        if r['LCSC'] in P: p1,p10=P[r['LCSC']]
        else: unpriced.append((c,r['LCSC'],r['Value'])); p1=p10=0
        t1+=k*p1; t10+=k*p10
    card_tot[c]=(t1,t10); card_parts[c]=q
    add('cards',f'{c} card parts ({q} parts, cards/{c}/{c}_bom.csv) x{n}',n,round(t1,4),round(t10,4),'BOM')
add('boards','Card PCBs: 4 LV designs + engine, 4-layer, 5 pcs per design at qty 1 [E]',5,8.0,1.2,'E')
add('boards','PCBA fixed fees per extra card order (JLC fee table)',5,13.74,1.374,'DS')
add('boards','Extended-part loading ~6 per card order at 3.07 [E count]',5,18.42,1.842,'E')
add('mechanical','Card bays: guides, faceplates, captive screws, coding ribs [E]',1,29.0,17.5,'E')
t1=sum(q*p1 for g,i,q,p1,p10,s in rows); t10=sum(q*p10 for g,i,q,p1,p10,s in rows)
with open(os.path.join(R,'docs/modular/true_cost_delta.csv'),'w',newline='') as f:
    w=csv.writer(f); w.writerow(['group','item','qty','unit_qty1','unit_qty10','ext_qty1','ext_qty10','source'])
    for g,i,q,p1,p10,s in rows: w.writerow([g,i,q,p1,p10,round(q*p1,2),round(q*p10,2),s])
    w.writerow(['TOTAL','true net delta per controller vs baseline (actual BOMs)','','','',round(t1,2),round(t10,2),'mix'])
G=collections.OrderedDict()
for g,i,q,p1,p10,s in rows:
    a=G.setdefault(g,[0,0]); a[0]+=q*p1; a[1]+=q*p10
for k,(a,b) in G.items(): print('%-12s %9.2f %9.2f'%(k,a,b))
print('TOTAL %.2f %.2f'%(t1,t10)); print('unpriced',unpriced)
# combined BOM of the example build by LCSC (mainboard + cards x instances + meter)
C=collections.OrderedDict()
def put(lc,val,q,src):
    a=C.setdefault(lc or val,dict(lcsc=lc,value=val,qty=0,src=set())); a['qty']+=q; a['src'].add(src)
def bomrows(path,src,mult=1):
    for r in csv.DictReader(open(path)):
        if r['Refs'].startswith('TOTAL') or r.get('DNP'): continue
        put(r['LCSC'],r['Value'],int(r['Qty'])*mult,src)
bomrows(os.path.join(R,'bom/genctl_main_bom.csv'),'mainboard')
for c,n in inst.items():
    for r in csv.DictReader(open(os.path.join(R,'cards',c,f'{c}_bom.csv'))): put(r['LCSC'],r['Value'],int(r['Qty'])*n,c)
bomrows(os.path.join(R,'bom/genctl_meter_bom.csv'),'hv meter')
with open(os.path.join(R,'docs/modular/combined_bom.csv'),'w',newline='') as f:
    w=csv.writer(f); w.writerow(['LCSC','Value','Qty','From'])
    for a in C.values(): w.writerow([a['lcsc'],a['value'],a['qty'],'+'.join(sorted(a['src']))])
mb=sum(int(r['Qty']) for r in csv.DictReader(open(os.path.join(R,'bom/genctl_main_bom.csv'))) if not r['Refs'].startswith('TOTAL') and not r['DNP'])
print('mainboard fitted parts',mb,'cards',card_parts,'combined BOM lines',len(C),'parts',sum(a['qty'] for a in C.values()))
