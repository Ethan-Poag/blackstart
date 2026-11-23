"""True net cost delta, modular build vs the locked one-board baseline (example build: ENGINE + HSO-5 x2 + BRK-4 + DI-8 + AI-4 + HV).
Card side: every card ref that is not a moved baseline part (refmap.json) is NEW and priced; moved parts cost nothing extra.
HSO-5 x2: the 2nd instance re-uses the baseline AUX6-10 circuit (HSO_B partition), so only its new parts are added again.
Mainboard side: parts that leave the mainboard without moving onto a card are subtracted (REMOVED below, reasons given).
Prices: bom/lcsc_prices.csv (LCSC/JLC API, dates in file), else bom/genctl_main_bom.csv, else LCSC detail API this phase (PX). [E] = estimate."""
import csv,json,os,collections
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P={}
for r in csv.DictReader(open(os.path.join(R,'bom/lcsc_prices.csv'))): P.setdefault(r['key'],(float(r['unit_qty1']),float(r['unit_qty10'])))
MB={r['Refs']:r for r in csv.DictReader(open(os.path.join(R,'bom/genctl_main_bom.csv')))}
import re
REF={}
def expand(k):
    out=[]
    for part in k.split(','):
        part=part.strip(); m=re.fullmatch(r'([A-Z#]+)(\d+)-([A-Z#]+)(\d+)',part)
        if m: out+=[m.group(1)+str(i) for i in range(int(m.group(2)),int(m.group(4))+1)]
        else: out.append(part)
    return out
for k,r in MB.items():
    for x in expand(k): REF[x]=r
for r in MB.values():
    if r['LCSC'] and r['Unit USD qty1']: P.setdefault(r['LCSC'],(float(r['Unit USD qty1']),float(r['Unit USD qty10'])))
PX={'C5173361':(1.2659,1.061),'C5173363':(1.3035,1.0953),'C147891':(1.4297,1.1721),'C128577':(1.7271,1.4661),'C160590':(0.0593,0.0593),'C534364':(0.5569,0.4693),'C137808':(0.004,0.004)}
for k,v in PX.items(): P.setdefault(k,v)
rows=[]; unpriced=[]
def add(g,item,q,p1,p10,src): rows.append((g,item,q,p1,p10,src))
def price(lcsc):
    if lcsc in P: return P[lcsc]
    unpriced.append(lcsc); return (0,0)
inst={'engine':1,'hso5':2,'brk4':1,'di8':1,'ai4':1}
for card,n in inst.items():
    d=os.path.join(R,'cards',card); moved=set(json.load(open(os.path.join(d,'refmap.json'))).values())
    for r in csv.DictReader(open(os.path.join(d,f'{card}_bom.csv'))):
        refs=[x.strip() for x in r['Refs'].split(',')]; new=[x for x in refs if x not in moved]
        if not new: continue
        p1,p10=price(r['LCSC'])
        add(f'card {card} x{n}',f"{r['Value']} {r['MPN']} ({r['LCSC']}) new: {' '.join(new)}",len(new)*n,p1,p10,'M')
# backplane / mainboard additions (not on a card BOM)
S=8
add('backplane','DIN 41612 C96 female vertical 9001-12961C00A, 8 LV + engine (C5173363)',S+1,*PX['C5173363'],'M-LCSC')
add('backplane','TPS48100QDGXRQ1 slot VBAT_FIELD switch (C43131316)',S,*price('C43131316'),'M')
add('backplane','BSC070N10NS5 slot FETs, 2 in parallel (C534364)',2*S,*PX['C534364'],'M-LCSC')
add('backplane','10 mOhm 2512 slot shunt (priced as the 20 mOhm C105360) [E part]',S,0.0655,0.0655,'E')
add('backplane','TPS2553DBVR +5V_SLOT/+3V3_SLOT switches (C55266)',2*S,*price('C55266'),'M')
add('backplane','74LVC1G08 slot OUT_EN gate (C176929)',S,*price('C176929'),'M')
add('backplane','Slot passives ~10 per slot [E]',S,0.10,0.10,'E')
add('backplane','TCA9548APWR x2 ID mux 0x70/0x71 on I2C2 (C130026)',2,0.8659,0.732,'M-LCSC')
add('backplane','TCA9555PWR x2 slot PRESENT/INT/FAULT/EN (C465732)',2,*price('C465732'),'M')
add('backplane','TMUX1208PWR slot ANA_OUT mux (C494728)',1,*price('C494728'),'M')
add('backplane','I2C pull-ups 4.7k x20 + CS decoder [E]',1,0.35,0.30,'E')
add('backplane','BAT54C clamp GLOW_SNSM + ESTOP_TRIP_SNSM (replaces D133-D135)',1,*price(REF['D133']['LCSC']),'M')
add('rail cut','TPS48100QDGXRQ1 watchdog rail cut (C43131316)',1,*price('C43131316'),'M')
add('rail cut','BSC070N10NS5 x2 parallel (C534364)',2,*PX['C534364'],'M-LCSC')
add('rail cut','RLP25FEER002 2 mOhm 2 W 2512 shunt (C160590)',1,*PX['C160590'],'M-LCSC')
add('rail cut','74LVC1G08 WD_OK AND ESTOP_OK (C176929)',1,*price('C176929'),'M')
add('rail cut','10.5k ISCP RC0603FR-0710K5L (C137808) + 100k/27k UVLO, 4.7n TMR, 470n BST, 10R, 0R, 100k pull-down [E for the rest]',1,0.004+0.06,0.004+0.05,'M/E')
add('hv meter','U94 AT24CS32 + R650 + C323 (meter BOM regenerated)',1,1.43,1.18,'M')
# removed from the mainboard, not moved onto a card
REMOVED={'U41':"'541 for GCB/MCB/AUX1-4 enables (card '541s replace it)",'U42':"'541 for AUX5-10 enables",'U64':'TMUX1208 AUX4-10 + ESTOP_TRIP (ESTOP_TRIP moves to U63)',
 'D133':'BAT54C AUX6/7 clamp','D134':'BAT54C AUX8/9 clamp','D135':'BAT54C AUX10/ESTOP_TRIP clamp','RN2':'SH_G5/6 pull-downs (AI-4 card RN copy)',
 'J17':'AI1-6 terminal (AI1-2 on engine card, AI3-6 on AI-4)','J26':'AUX1-6 terminal (HSO-5 headers)','J19':'DI1-6 terminal (engine card + DI-8)'}
for ref,why in REMOVED.items():
    lc=REF[ref]['LCSC']; p1,p10=price(lc)
    add('removed',f'{ref} {why} ({lc})',-1,p1,p10,'M')
# boards / mechanical (estimates)
add('boards','Card PCBs: 4 LV designs + engine, 4-layer, 5 pcs per design at qty 1 [E]',5,8.0,1.2,'E')
add('boards','PCBA fixed fees per extra card order (JLC fee table) ',5,13.74,1.374,'DS')
add('boards','Extended-part loading ~6 per card order at 3.07 [E count]',5,18.42,1.842,'E')
add('mechanical','Card bays: guides, faceplates, captive screws, coding ribs [E]',1,29.0,17.5,'E')
t1=sum(q*p1 for g,i,q,p1,p10,s in rows); t10=sum(q*p10 for g,i,q,p1,p10,s in rows)
out=os.path.join(R,'docs/modular/true_cost_delta.csv')
with open(out,'w',newline='') as f:
    w=csv.writer(f); w.writerow(['group','item','qty','unit_qty1','unit_qty10','ext_qty1','ext_qty10','source'])
    for g,i,q,p1,p10,s in rows: w.writerow([g,i,q,p1,p10,round(q*p1,2),round(q*p10,2),s])
    w.writerow(['TOTAL','true net delta per controller vs baseline','','','',round(t1,2),round(t10,2),'mix'])
G=collections.OrderedDict()
for g,i,q,p1,p10,s in rows:
    k=g.split(' x')[0]; a=G.setdefault(k,[0,0]); a[0]+=q*p1; a[1]+=q*p10
for k,(a,b) in G.items(): print('%-14s %8.2f %8.2f'%(k,a,b))
print('TOTAL %.2f %.2f'%(t1,t10)); print('unpriced',sorted(set(unpriced)))
# ---- combined BOM for the example build (by LCSC code): mainboard after the split + cards x instances + backplane/rail-cut adds + meter
moved_all=set()
for card in inst:
    moved_all|=set(json.load(open(os.path.join(R,'cards',card,'refmap.json'))).keys())
# 2nd HSO-5 instance replaces the baseline AUX6-10 (HSO_B) circuit: those baseline refs also leave the mainboard
import sys; sys.path.insert(0,os.path.join(R,'cards','tools'))
from partition import ASSIGN
hsob=set(r for r,v in ASSIGN.items() if v=='HSO_B')
C=collections.OrderedDict()
def put(lc,val,q,src):
    a=C.setdefault(lc or val,dict(lcsc=lc,value=val,qty=0,src=set())); a['qty']+=q; a['src'].add(src)
for k,r in MB.items():
    if r['DNP']: continue
    for x in expand(k):
        if x in moved_all or x in hsob or x in REMOVED: continue
        put(r['LCSC'],r['Value'],1,'mainboard')
for card,n in inst.items():
    for r in csv.DictReader(open(os.path.join(R,'cards',card,f'{card}_bom.csv'))): put(r['LCSC'],r['Value'],int(r['Qty'])*n,card)
for g,i,q,p1,p10,s in rows:
    if g in ('backplane','rail cut'):
        import re as _re; m=_re.search(r'\((C\d+)\)',i); put(m.group(1) if m else '',i[:40],q,g)
with open(os.path.join(R,'docs/modular/combined_bom.csv'),'w',newline='') as f:
    w=csv.writer(f); w.writerow(['LCSC','Value','Qty','From'])
    for a in C.values(): w.writerow([a['lcsc'],a['value'],a['qty'],'+'.join(sorted(a['src']))])
print('combined BOM lines',len(C),'parts',sum(a['qty'] for a in C.values()),'(HV meter board: bom/genctl_meter_bom.csv, 221 refs)')
