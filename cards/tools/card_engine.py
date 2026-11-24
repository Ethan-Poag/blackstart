"""ENGINE I/O card (dedicated keyed slot): fuel/crank/glow drivers, MPU, D+, COM_A/B, DI1-4, AI1-2 + protection."""
import json,re,sys,os,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from mkcard import Card,ROOT
from partition import ASSIGN
c=Card('engine','ENGINE I/O card: fuel, crank, glow, speed, D+, DI1-4, AI1-2','A3')
refs=sorted([r for r,v in ASSIGN.items() if v=='ENGINE'])
c.netmap={'/Inputs: 6 AI, 12 DI, MPU, D+, E-stop sense, VBAT sense/Net-(U31-P00)':'U31_P00','Net-(U31-P00)':'U31_P00'}
c.move(refs)
# Enginerd decision 2026-11-23 10:24 HST: glow driver supply on the E-stop rail (was VBAT_P)
for p in c.parts:
    if p['props'].get('BaselineRef')=='U47':
        for k in ('12','13','14'): assert p['pn'][k]=='VBAT_P'; p['pn'][k]='VBAT_ESTOP'
# field headers (KF2EDGRM-5.08-6P, same part as baseline J17-J22)
J18=[p for p in c.parts if p['props'].get('BaselineRef')=='J18'][0]
hdr=dict(J18['props']); [hdr.pop(k,None) for k in ('Reference','BaselineRef','Value')]
SIG=['AI1_ADC','AI2_ADC','COM_A_ADC','COM_B_ADC','AI_CS_DIS2','AI_SH_G1','AI_SH_G2','AI_VSET','VMID','VBAT_AI',
     'DI1_D','DI2_D','DI3_D','DI4_D','DI_BIAS_A','DPLUS_D','DPLUS_SNS','DPLUS_EXC_EN','MPU_GATE','MPU_SPEED','U31_P00',
     'FUEL_EN','CRANK_EN','GLOW_EN','FUEL_RB_N','CRANK_RB_N','GLOW_RB_N','GLOW_SNSM','FUEL_ISNS','CRANK_ISNS',
     'DIAG_EN','OUT_FAULT_N','ID_SDA','ID_SCL','ID_WP','ENG_PRESENT_N']
PIN={}
def row(pos,a,b,c_): PIN[f'a{pos}']=a; PIN[f'b{pos}']=b; PIN[f'c{pos}']=c_
for pos in (1,2,3,4): row(pos,'VBAT_ESTOP','VBAT_ESTOP','VBAT_ESTOP')          # 12 contacts
for pos in (5,6): row(pos,'FUEL_OUT','FUEL_OUT','FUEL_OUT')
row(7,'FUEL_OUT','GND','FUEL_OUT')                                                # FUEL_OUT 8 contacts
for pos in (8,9): row(pos,'CRANK_OUT','CRANK_OUT','CRANK_OUT')
row(10,'CRANK_OUT','GND','CRANK_OUT')                                             # CRANK_OUT 8 contacts
row(11,'GND','GND','GND'); row(12,'VBAT_P','GND','VBAT_P'); row(13,'+3V3_SAFE','GND','+3V3_SAFE')
for i in range(0,len(SIG),2): row(14+i//2,SIG[i],'GND',SIG[i+1])
for pos in range(14+len(SIG)//2,33): row(pos,'GND','GND','GND')
PIN={k:('GND' if v=='ENG_PRESENT_N' else v) for k,v in PIN.items()} | {'_present':'ENG_PRESENT_N'}
present_pin=[k for k,v in zip([f'{r}{14+i//2}' for i in range(len(SIG)) for r in ('a' if i%2==0 else 'c')],SIG) if v=='ENG_PRESENT_N'][0]
PIN.pop('_present'); PIN[present_pin]='GND'   # card ties PRESENT_N to GND: net on the card is GND
din={'Footprint':'cards:DIN41612_C96_Male_RA_WingTAT_9001-11961','MPN':'9001-11961C00A','Manufacturer':'WingTAT','LCSC':'C5173361',
     'Description':'ENGINE slot plug, DIN 41612 C96 RA male. Keyed: engine-only coding notch (see notes). Pinout: cards/engine/engine_slot_pinout.csv'}
JS=c.newref('J')
for u,r in enumerate('abc',1): c.add('cards:DIN41612_C96',JS,'DIN41612_C96',{k:v for k,v in PIN.items() if k[0]==r},din,unit=u)
JF1=c.newref('J'); c.add('Connector_Generic:Conn_01x06',JF1,'DI1-4/AI1-2',{'1':'DI1','2':'DI2','3':'DI3','4':'DI4','5':'AI1','6':'AI2'},hdr)
JF2=c.newref('J'); c.add('Connector_Generic:Conn_01x06',JF2,'D+/GLOW/BIAS',{'1':'DPLUS','2':'GLOW_OUT','3':'DI_BIAS_A','4':'GND','5':None,'6':None},hdr)
for p in c.parts:
    if p['props'].get('BaselineRef')=='J18': p['props']['Value']='COM/MPU'
# ID EEPROM
cap=dict(c.inst['C199'][0]['props']); cap.pop('Reference')
import lvcommon as L
res=L.r10k('ID_WP pull-up: write-protected unless the backplane pulls ID_WP low')   # Pass 2 m16: 0603
c.add('cards:AT24CS32-STUM',c.newref('U'),'AT24CS32-STUM-T',{'1':'ID_SCL','2':'GND','3':'ID_SDA','4':'+3V3_SAFE','5':'ID_WP'},
      {'Footprint':'Package_TO_SOT_SMD:SOT-23-5','MPN':'AT24CS32-STUM-T','Manufacturer':'Microchip','LCSC':'C147891','Description':'Card ID + calibration EEPROM (0x50 / serial 0x58)'})
CID=c.newref('C'); c.add('Device:C',CID,cap['Value'],{'1':'+3V3_SAFE','2':'GND'},cap)
c.add('Device:R',c.newref('R'),res['Value'],{'1':'+3V3_SAFE','2':'ID_WP'},res)
# Pass 1 M1: VS decoupling for the glow TPS1HTC30-Q1 (C_IC >= 100 nF) + VBAT_ESTOP bulk (100 V X7R)
C100N100V=dict(Value='100n',Footprint='Capacitor_SMD:C_0805_2012Metric',MPN='CL21B104KCFNNNE',Manufacturer='Samsung Electro-Mechanics',LCSC='C28233',Description='glow driver VS decoupling (TPS1HTC30-Q1 C_IC >= 100 nF)')
C2U2100V=dict(Value='2.2u',Footprint='Capacitor_SMD:C_1206_3216Metric',MPN='CL31B225KCHSNNE',Manufacturer='Samsung Electro-Mechanics',LCSC='C170101',Description='VBAT_ESTOP bulk, 100 V X7R')
CVS=c.newref('C'); c.add('Device:C',CVS,'100n',{'1':'VBAT_ESTOP','2':'GND'},C100N100V)
CBK=c.newref('C'); c.add('Device:C',CBK,'2.2u',{'1':'VBAT_ESTOP','2':'GND'},C2U2100V)
# Pass 3 MAJ-D: TPS48100-Q1 recommends >= 22 nF on SRC; U4 (fuel) / U6 (crank) SRC = FUEL_OUT / CRANK_OUT had none (63 nF worst at 32 V)
CSF=c.newref('C'); c.add('Device:C',CSF,'100n',{'1':'FUEL_OUT','2':'GND'},dict(C100N100V,Description='fuel TPS48100 SRC cap 100 nF / 100 V (Pass 3 MAJ-D)'))
CSC=c.newref('C'); c.add('Device:C',CSC,'100n',{'1':'CRANK_OUT','2':'GND'},dict(C100N100V,Description='crank TPS48100 SRC cap 100 nF / 100 V (Pass 3 MAJ-D)'))
c.notes=['ENGINE I/O CARD (dedicated keyed slot, card type 0x0001)',
 'Key: engine-only coding notch in the card edge + matching rib in the engine slot guide; LV cards have the LV notch. ID EEPROM type check too.',
 'Fuel/crank/glow drivers are fed ONLY from VBAT_ESTOP (E-stop cut is external, upstream of J23 on the mainboard).',
 'FUEL_EN/CRANK_EN/GLOW_EN arrive already gated by WD_OK on the mainboard (U38-U40). Missing card = no drive = engine stops.',
 'Contacts (2 A each, 50 % derate): VBAT_ESTOP 12 (12 A >= 10 A F2 fuse); FUEL_OUT 8 and CRANK_OUT 8 (8 A >= 6.14 A max short-circuit trip).',
 'Glow driver (baseline U47) VS moved VBAT_P -> VBAT_ESTOP (Nov 23 decision): E-stop now also cuts glow.',
 'Slot pinout table: cards/engine/engine_slot_pinout.csv. b-row signals are GND guards. ENG_PRESENT_N (c31) tied to GND on the card, read on the mainboard 0x22 P10.',
 'Pass 1 M1: 100 nF / 100 V at the glow driver VS + 2.2 uF / 100 V bulk on VBAT_ESTOP (mainboard C205-C219 removed). Pass 3 MAJ-D: 100 nF / 100 V on the fuel / crank TPS48100 SRC (FUEL_OUT, CRANK_OUT).']
def key(p):
    br=p['props'].get('BaselineRef','')
    nets=' '.join(n or '' for n in p['pn'].values())
    for i,rx in enumerate([r'^J',r'ID_',r'FUEL',r'CRANK',r'GLOW',r'MPU',r'DPLUS',r'COM_',r'DI[1-4]',r'AI[12]',r'AI_']):
        if re.search(rx,p['ref'] if i<1 else nets): return (i,br)
    return (99,br)
used=c.write(os.path.join(ROOT,'cards','engine'),key)
import schdraw
B=lambda *refs:[k for r in refs for k in sorted((p['ref'],p['unit']) for p in c.parts if p['props'].get('BaselineRef')==r or (r.startswith('=') and p['ref']==r[1:]))]
BLOCKS=[('Slot connector (ENGINE slot, keyed) - DIN 41612 C96',B('='+JS)),
 ('Fuel driver + current sense + readback',B('U43','Q45','Q46','U44','Q49')),
 ('Crank driver + current sense + readback',B('U45','Q47','Q48','U46','Q50')),
 ('Glow driver (VS on VBAT_ESTOP)',B('U47','Q51')),
 ('MPU speed comparator + COM_A/B (J1)',B('U35','D60','D62','J18')),
 ('D+ excite / sense + field header J4',B('U36','Q42','Q43','='+JF2)),
 ('AI1 channel',[k for k in B('U26') if k[1]==1]+B('Q12','Q13','Q14','Q15')),
 ('AI2 channel',[k for k in B('U26') if k[1]!=1]+B('Q16','Q17','Q18','Q19')),
 ('DI1-4 inputs + AI1/AI2 field header J3',B('='+JF1)),
 ('Card ID EEPROM',[k for k in ((p['ref'],p['unit']) for p in c.parts) if c.parts and k[0].startswith('U') and k[0] not in c.refmap.values()])]
RAILS={'GND','+3V3_SAFE','VBAT_ESTOP','VBAT_P','VBAT_AI','VMID','AI_VSET','DI_BIAS_A'}
D=schdraw.Drawer(c,RAILS,BLOCKS,os.environ.get('PAPER','A2'),c.notes); D.labels_only={JS}; D.extra={CID:'Card ID EEPROM',CVS:'Glow driver (VS on VBAT_ESTOP)',CBK:'Glow driver (VS on VBAT_ESTOP)',CSF:'Fuel driver + current sense + readback',CSC:'Crank driver + current sense + readback'}
over=schdraw.run(D,os.path.join(ROOT,'cards','engine'),c.title)
print('leftover clusters',len(D.left),D.left[:20])
import csv
with open(os.path.join(ROOT,'cards','engine','engine_slot_pinout.csv'),'w',newline='') as f:
    w=csv.writer(f); w.writerow(['position','row_a','row_b','row_c'])
    for pos in range(1,33): w.writerow([pos]+[('ENG_PRESENT_N' if f'{r}{pos}'==present_pin else PIN[f'{r}{pos}']) for r in 'abc'])   # mainboard-side net; the card grounds it
print('parts',len({p['ref'] for p in c.parts}),'overflow',c.over)
if __name__=='__main__':
    from verify_card import verify
    slot=collections.defaultdict(list)
    for k,v in PIN.items(): slot[v].append(k)
    slot['ENG_PRESENT_N']=[present_pin]
    field={}
    for p in c.parts:
        if p['ref'] in (c.refmap['J18'],JF1,JF2):
            for k,v in p['pn'].items():
                if v: field.setdefault(v,f"{p['ref']}.{k}")
    ov={('U47',k):'VBAT_ESTOP' for k in ('12','13','14')}
    verify('engine',slot,field,ov,{'Net-(U31-P00)':'U31_P00'})
