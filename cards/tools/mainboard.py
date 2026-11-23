"""Phase 2 mainboard rework (genctl root project).
Regenerates the sheets that change (mcu, estop, mtr_if, io_core = what stays of inputs+outputs) from the locked baseline
netlist with the documented net edits, and adds the new sheets (backplane = 9 slot connectors + ID muxes + slot bus,
slot_power = per-slot switches). Untouched sheets: power, cm5, comms, display, frontpanel (2 global-label renames).
All inter-sheet nets are global labels; rails use power symbols. Refs of kept parts are unchanged; new refs start at
R700 / C400 / U100 / Q100 / J40 / D200 / TP10."""
import os,sys,re,json,csv,collections,uuid,glob
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from mkcard import Card,short,ROOT,lib_pins
import schdraw
from lvcommon import lv_pinout
ROOTUUID='2f7a4bb8-89ed-4e3c-b40c-67c49fede2c6'
SHEETS=collections.OrderedDict([   # file -> (sheet uuid, title, paper)
 ('mcu',('c2700331-201a-4cfa-a277-c8f7379e4af6','STM32H743 safety MCU (slot SPI3, slot CS decoder lines, I2C2 ID bus)','A2')),
 ('estop',('bf2b4d33-db1c-4f32-83fb-5781585769ff','E-stop feed: J23, LM74700-Q1 ideal diode, watchdog rail cut, trip and sense','A2')),
 ('io_core',('6b1f0c2e-3a7d-4c55-9e2b-0f6a1d7c9b01','Core I/O kept on the mainboard: AI1/AI2 + COM ADC, DI1-4, D+, MPU, expanders, fuel/crank/glow gating, sense mux','A1')),
 ('backplane',('9c4e2a10-5b8f-4d3e-a1c7-2e9f0b6d4a02','Backplane: ENGINE slot + 8 universal LV slots, ID muxes, slot bus','A1')),
 ('slot_power',('3d7a9e51-0c2b-4f8a-b6d1-7e4c2a9f1b03','Per-slot power: TPS48100 VBAT_FIELD, TPS2553 +5V/+3V3, OUT_EN_N / PWR_EN logic','A1')),
 ('mtr_if',('5d1b3a52-6c1e-4f0a-9a31-3b0c2a6e7f10','Metering interface J31 (HV meter ID I2C on J31.12/16)','A3')),
])
KEEP_SHEETS={'power':'d8c05520-8978-4d93-9881-80f603685ecb','cm5':'d811a5f3-3ea5-4969-ac51-150b5151ab82','comms':'7172d8aa-4982-46d4-80f3-9c3b7e936f89',
             'display':'fcebac73-5e7d-409a-9893-556fac7ba7b9','frontpanel':'bd3092dd-3b47-4d13-9646-0a27ee0e3b04'}
RAILS={'GND','+3V3_SAFE','+3V3','+5V','+12V','VBAT_P','VBAT_ESTOP','VBAT_ESTOP_PRE'}
REMOVED_P1={'U41':"'541 GCB/MCB/AUX1-4 enables (card '541s)",'U42':"'541 AUX5-10 enables",'U64':'TMUX1208 AUX4-10 + ESTOP_TRIP (ESTOP_TRIP moves to U63)',
 'D133':'BAT54C AUX6/7 clamp','D134':'BAT54C AUX8/9 clamp','D135':'BAT54C AUX10/ESTOP_TRIP clamp','RN2':'SH_G5/6 pull-downs (AI-4 card copy)',
 'J17':'AI1-6 terminal (engine card / AI-4)','J26':'AUX1-6 terminal (HSO-5 headers)','J19':'DI1-6 terminal (engine card / DI-8)'}
REMOVED_P2={'Q70':'SQD40P10-40L reverse-polarity P-FET -> LM74700-Q1 + BSC070N10NS5','Q71':'SQD40P10-40L (parallel) -> ideal diode',
 'D137':'BZT52C15 P-FET gate clamp (no P-FET)','R627':'10k P-FET gate pull-down (no P-FET)',
 'D151':'SMAJ40A on DI_BIAS_B (bank B moved to DI-8 with its own TVS)','J27':'AUX7-10 terminal (HSO-5 headers)',
 'Q44':"WD_OE_N inverter for U41/U42 OE (removed '541s)",'R272':'Q44 base resistor','R273':'Q44 base pull-down','R274':'WD_OE_N pull-up',
 'R536':'PB4 4.7k pull-down (PB4 is now SLOT_EXP_INT_N, pulled up)','R36':'DI5 series R (DI5/DI6 moved to DI-8)','R37':'DI6 series R',
 'R38':'DI8 series R (PB10 = I2C2_SCL direct)','R39':'DI9 series R (PB11 = I2C2_SDA direct)','R40':'DI10 series R','R41':'DI11 series R'}
gone=set()
for cd in ['engine','di8','ai4','hso5','brk4']: gone|=set(json.load(open(os.path.join(ROOT,'cards',cd,'refmap.json'))))
from partition import ASSIGN
gone|={r for r,v in ASSIGN.items() if v=='HSO_B'}
REM=set(REMOVED_P1)|set(REMOVED_P2)
def sheet_refs(f):
    import subprocess
    t=subprocess.run(['git','-C',ROOT,'show',f'baseline-2026-11-23-locked:{f}.kicad_sch'],capture_output=True,text=True,check=True).stdout
    return set(re.findall(r'\(property "Reference" "([A-Z]+[0-9]+)"',t))
base_sheet={r:f for f in ['inputs','outputs','estop','mcu','mtr_if','power','cm5','comms','display','frontpanel'] for r in sheet_refs(f)}
# ---------------- net edits on kept baseline parts: (ref,pin) -> new net (None = NC) ----------------
OV={}
for p in ('6',): OV[('U29',p)]=None
for p in ('4','5','6'): OV[('U30',p)]=None                       # AI3-6 ADS1115 inputs: AI-4 has its own ADS1115
for p in ('6','7','8','9','18','20'): OV[('U31',p)]=None          # AI_CS_DIS3-6, DI_PU_B, DI_PD_B outputs (now on cards)
for p in ('3','6'): OV[('U92',p)]=None                            # AI_SH_G5/G6 outputs (AI-4 card)
for p in ('11','13'): OV[('U32',p)]='GND'                          # DI5/DI6 Schmitt gates unused: input to GND
for p in ('10','12'): OV[('U32',p)]=None
for i,p in enumerate(('7','8','9','10','11','13','14','15')): OV[('U62',p)]=f'SL{i+1}_PRESENT_N'   # freed readback inputs -> slot presence
for p in ('16','17','18','19','20'): OV[('U62',p)]=None         # spare: firmware sets them as outputs (low)
OV[('U63','5')]='ESTOP_TRIP_SNSM'                                  # ESTOP_TRIP sense moves from U64 to U63 S2
for p in ('6','7','9','10','11','12'): OV[('U63',p)]='GND'
OV[('J21','3')]=None                                               # D+ terminal now on the engine card
for p in ('1','2','3','4','5'): OV[('J24',p)]=None                 # GLOW/GCB/MCB terminals now on the engine card / BRK-4; J24.6 ESTOP_TRIP_OUT stays
OV[('C224','1')]='SLOT_ANA'; OV[('U7','16')]='SLOT_ANA'             # PA? ADC: was MUXB_OUT (U64), now the slot ANA_OUT mux
REN={'GCB_CL_MCU':'SLOT_RST_N','GCB_OP_MCU':'SLOT_SPI_SCK','MCB_CL_MCU':'SLOT_SPI_MISO','MCB_OP_MCU':'SLOT_SPI_MOSI',
     'AUX1_MCU':'SLOT_CS_A0','AUX2_MCU':'SLOT_CS_A1','AUX7_MCU':'SLOT_CS_A2','AUX8_MCU':'SLOT_CS_EN',
     'AUX4_MCU':'SPARE_PB5','AUX5_MCU':'SPARE_PB6','AUX6_MCU':'SPARE_PB7','AUX3_MCU':'SLOT_EXP_INT_N',
     'AUX9_MCU':'EXP25_P07_SPARE','AUX10_MCU':'EXP25_P10_SPARE'}
for p in ('43','44','45','53','54','57'): OV[('U7',p)]=None        # DI5/6/7/10/11/12 MCU pins: inputs moved to DI-8 (SPI expander)
OV[('U7','46')]='I2C2_SCL'; OV[('U7','47')]='I2C2_SDA'              # PB10/PB11 AF4 = I2C2 (DS12110 rev 10)
# E-stop feed split: ideal diode J23 -> VBAT_ESTOP_PRE (sense, pre-cut) -> rail cut -> VBAT_ESTOP (engine slot, ADC readback)
for rp in (('C199','1'),('R251','1'),('R400','1')): OV[rp]='VBAT_ESTOP_PRE'
OV[('D126','1')]='VBAT_ESTOP_IN'                                   # bidirectional TVS ahead of the ideal diode
OV[('U34','9')]='ESTOP_DIG'; OV[('U34','8')]='ESTOP_OK'             # spare 74HC14 gate: ESTOP_OK = NOT ESTOP_DIG
OV[('J31','12')]='MTR_ID_SCL'; OV[('J31','16')]='MTR_ID_SDA'         # HV meter ID EEPROM (matches J32.12/J32.16)
ASSIGN_SHEET={}
for r,f in base_sheet.items():
    if r in gone or r in REM: continue
    if f in ('inputs','outputs'): ASSIGN_SHEET[r]='io_core'
    elif f in ('estop','mcu','mtr_if'): ASSIGN_SHEET[r]=f
for r in ('J23','C199','C203','D126'): ASSIGN_SHEET[r]='estop'
cards={}
def card(f):
    if f not in cards:
        c=Card(f,SHEETS[f][1],SHEETS[f][2]); c.count.update({'R':699,'C':399,'U':99,'Q':99,'J':39,'D':199,'TP':9}); cards[f]=c
    return cards[f]
for r in sorted(ASSIGN_SHEET):
    c=card(ASSIGN_SHEET[r]); c.move([r],rename={r:r})
for c in cards.values():
    for p in c.parts:
        for k in list(p['pn']):
            if (p['ref'],k) in OV: p['pn'][k]=OV[(p['ref'],k)]
            elif p['pn'][k] in REN: p['pn'][k]=REN[p['pn'][k]]
        p['props'].pop('BaselineRef',None)
# ---------------- new parts ----------------
SRC=card('io_core')
def props_lcsc(lcsc):
    for r,ii in SRC.inst.items():
        if ii and ii[0]['props'].get('LCSC')==lcsc:
            P=dict(ii[0]['props']); P.pop('Reference',None); return P
    raise KeyError(lcsc)
def P(value,fp,mpn,man,lcsc,desc=''): return {'Value':value,'Footprint':fp,'MPN':mpn,'Manufacturer':man,'LCSC':lcsc,'Description':desc}
R0603='Resistor_SMD:R_0603_1608Metric'
NEWP={'C2941042':P('LM74700QDBVRQ1','Package_TO_SOT_SMD:SOT-23-6','LM74700QDBVRQ1','Texas Instruments','C2941042','Ideal-diode controller, reverse battery to -65 V'),
 'C130026':P('TCA9548APWR','Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm','TCA9548APWR','Texas Instruments','C130026','8-ch I2C switch'),
 'C485077':P('SN74LVC138APWR','Package_SO:TSSOP-16_4.4x5mm_P0.65mm','SN74LVC138APWR','Texas Instruments','C485077','slot CS decoder'),
 'C7394016':P('74LVC1G02','Package_TO_SOT_SMD:SOT-23-5','SN74LVC1G02DBVR(UMW)','UMW','C7394016','NOR: PWR_EN = SLOT_EN AND PRESENT'),
 'C7826':P('74LVC1G00','Package_TO_SOT_SMD:SOT-23-5','SN74LVC1G00DBVR','Texas Instruments','C7826','NAND: OUT_EN_N = NOT(PWR_EN AND WD_OK)'),
 'C2903468':P('10m','Resistor_SMD:R_2512_6332Metric','HoJLR2512-3W-10mR-1%','Milliohm','C2903468','slot shunt 10 mOhm 3 W'),
 'C160590':P('2m','Resistor_SMD:R_2512_6332Metric','RLP25FEER002','TA-I Tech','C160590','rail-cut shunt 2 mOhm 2 W'),
 'C137808':P('10.5k',R0603,'RC0603FR-0710K5L','YAGEO','C137808','rail-cut ISCP: 15.8/20/24.8 A'),
 'C23000':P('30.1k',R0603,'0603WAF3012T5E','UNI-ROYAL','C23000','slot ISCP: 7.9 A typ with 10 mOhm'),
 'C23249':P('80.6k',R0603,'0603WAF8062T5E','UNI-ROYAL','C23249','TPS2553 ILIM: 291-370 mA'),
 'C5173363':{'Value':'DIN41612_C96','Footprint':'cards:DIN41612_C96_Female_Vertical_WingTAT_9001-12961','MPN':'9001-12961C00A','Manufacturer':'WingTAT','LCSC':'C5173363','Description':'slot socket'}}
def pr(lcsc,**kw):
    d=dict(NEWP[lcsc]) if lcsc in NEWP else props_lcsc(lcsc); d.update(kw); return d
def add(sheet,lib,prefix,lcsc,pn,unit=1,**kw):
    c=card(sheet); ref=c.newref(prefix) if unit==1 else kw.pop('ref'); d=pr(lcsc,**{k:v for k,v in kw.items() if k!='ref'})
    c.add(lib,ref,d['Value'],pn,d,unit=unit); return ref
for c in cards.values(): pass
def R(sheet,lcsc,a,b,**kw): return add(sheet,'Device:R','R',lcsc,{'1':a,'2':b},**kw)
def C(sheet,lcsc,a,b='GND',**kw): return add(sheet,'Device:C','C',lcsc,{'1':a,'2':b},**kw)
# all sheets share one ref counter
class Shared(collections.Counter): pass
shared=collections.Counter({'R':699,'C':399,'U':99,'Q':99,'J':39,'D':199,'JP':9})
for f in SHEETS: card(f).count=shared
FET='C534364'; R10K='C25804'; R100K='C25803'; R47K='C23162'; R22K='C4190'; C100N='C14663'; R100='C22775'
# ---- E-stop feed: ideal diode + rail cut ----
S='estop'
Uid=add(S,'cards:LM74700QDBVRQ1','U','C2941042',{'6':'VBAT_ESTOP_IN','3':'VBAT_ESTOP_IN','1':'ESTOP_ID_VCAP','4':'VBAT_ESTOP_PRE','5':'ESTOP_ID_G','2':'GND'})
Qid=add(S,'Transistor_FET:BSC070N10NS5','Q',FET,{'1':'VBAT_ESTOP_IN','2':'VBAT_ESTOP_IN','3':'VBAT_ESTOP_IN','4':'ESTOP_ID_G','5':'VBAT_ESTOP_PRE'},
        Description='Ideal-diode FET: source = J23 side, drain = PRE; body diode blocks reverse battery')
C(S,C100N,'ESTOP_ID_VCAP','VBAT_ESTOP_IN',Description='LM74700 VCAP to ANODE >= 0.1 uF')
C(S,C100N,'VBAT_ESTOP_IN',Description='LM74700 ANODE >= 22 nF')
Urc=add(S,'genctl:TPS48100QDGXRQ1','U','C43131316',{'1':'RC_UVLO','2':'GND','3':'RC_EN','5':'OUT_FAULT_N','6':'GND','7':'GND','8':'RC_ISCP','9':'RC_TMR','10':'GND',
        '12':'RC_BST','13':'VBAT_ESTOP','14':'RC_GPD','15':'RC_GPU','17':'RC_DRN','18':'VBAT_ESTOP_PRE','20':'VBAT_ESTOP_PRE','4':None,'11':None,'19':None})
R(S,'C160590','VBAT_ESTOP_PRE','RC_DRN')
for i in range(2): add(S,'Transistor_FET:BSC070N10NS5','Q',FET,{'5':'RC_DRN','1':'VBAT_ESTOP','2':'VBAT_ESTOP','3':'VBAT_ESTOP','4':'RC_G'})
R(S,'C22859','RC_GPU','RC_G'); R(S,'C21189','RC_GPD','RC_G')
R(S,'C137808','RC_ISCP','GND'); C(S,'C106218','RC_TMR'); C(S,'C1623','RC_BST','VBAT_ESTOP')
R(S,R100K,'VBAT_ESTOP_PRE','RC_UVLO'); R(S,'C22967','RC_UVLO','GND')
add(S,'74xGxx:74LVC1G08','U','C176929',{'1':'WD_OK','2':'ESTOP_OK','3':'GND','4':'RC_EN','5':'+3V3_SAFE'},Description='rail cut enable = WD_OK AND ESTOP_OK')
C(S,C100N,'+3V3_SAFE'); R(S,R100K,'RC_EN','GND')
# ---- backplane ----
S='backplane'; LV={}
for r in csv.DictReader(open(os.path.join(ROOT,'docs/modular/slot_pinout_LV.csv'))):
    for row in 'abc': LV[f"{row}{r['position']}"]=r['row_'+row]
def din(sheet,pmap,desc):
    c=card(sheet); ref=c.newref('J'); d=pr('C5173363',Description=desc)
    for u,row in enumerate('abc',1): c.add('cards:DIN41612_C96',ref,'DIN41612_C96',{k:v for k,v in pmap.items() if k[0]==row},d,unit=u)
    return ref
ID=lambda n:[(n>>0)&1,(n>>1)&1,(n>>2)&1]
slots=[]
for s in range(1,9):
    b=ID(s-1); par=1-(sum(b)%2)   # odd parity over ID0..2+IDP: all-GND and all-open never decode as valid
    m={'VBAT_FIELD':f'SL{s}_VBAT','FIELD_GND':'GND','GND':'GND','+5V_SLOT':f'SL{s}_5V','+3V3_SLOT':f'SL{s}_3V3','+3V3_ID':f'SL{s}_3V3_ID',
       'PRESENT_N':f'SL{s}_PRESENT_N','SPI_SCK':'SLOT_SPI_SCK','SPI_MOSI':'SLOT_SPI_MOSI','SPI_MISO':'SLOT_SPI_MISO','SPI_CS_N':f'SL{s}_CS_N',
       'I2C_SDA':f'SL{s}_ID_SDA','I2C_SCL':f'SL{s}_ID_SCL','INT_N':f'SL{s}_INT_N','RST_N':'SLOT_RST_N','OUT_EN_N':f'SL{s}_OUT_EN_N',
       'CARD_FAULT_N':f'SL{s}_FAULT_N','SLOT_ID0':'GND' if not b[0] else None,'SLOT_ID1':'GND' if not b[1] else None,'SLOT_ID2':'GND' if not b[2] else None,
       'SLOT_IDP':'GND' if not par else None,'ANA_OUT':f'SL{s}_ANA','ID_WP':'ID_WP','RSVD':None}
    pmap={k:m[v] for k,v in LV.items()}
    slots.append(din(S,pmap,f'LV slot {s} socket (slot ID {s-1}: ID2..0 = {b[2]}{b[1]}{b[0]}, IDP = {par}; 1 = open, 0 = GND)'))
E={}
for r in csv.DictReader(open(os.path.join(ROOT,'cards/engine/engine_slot_pinout.csv'))):
    for row in 'abc':
        n=r['row_'+row]; E[f"{row}{r['position']}"]={'ID_SDA':'ENG_ID_SDA','ID_SCL':'ENG_ID_SCL'}.get(n,n)
JE=din(S,E,'ENGINE slot socket (keyed). Pinout cards/engine/engine_slot_pinout.csv')
# ID muxes on I2C2 (0x70 = slots 1-8, 0x71 = engine + HV meter)
mx=[]
for a in (0,1):
    pn={'22':'I2C2_SCL','23':'I2C2_SDA','3':'ID_MUX_RST_N','1':'+3V3_SAFE' if a else 'GND','2':'GND','21':'GND','24':'+3V3_SAFE','12':'GND'}
    ch=[f'SL{i+1}' for i in range(8)] if a==0 else ['ENG','MTR']+[None]*6
    for i,n in enumerate(ch):
        sc,sd={0:('5','4'),1:('7','6'),2:('9','8'),3:('11','10'),4:('14','13'),5:('16','15'),6:('18','17'),7:('20','19')}[i]
        pn[sc]=f'{n}_ID_SCL' if n else None; pn[sd]=f'{n}_ID_SDA' if n else None
    mx.append(add(S,'cards:TCA9548APWR','U','C130026',pn,Value=f'TCA9548APWR @0x7{a}')); C(S,C100N,'+3V3_SAFE')
R(S,R10K,'ID_MUX_RST_N','+3V3_SAFE'); R(S,R22K,'I2C2_SCL','+3V3_SAFE'); R(S,R22K,'I2C2_SDA','+3V3_SAFE')
for n in [f'SL{i}' for i in range(1,9)]+['ENG','MTR']:
    R(S,R47K,f'{n}_ID_SCL','+3V3_SAFE'); R(S,R47K,f'{n}_ID_SDA','+3V3_SAFE')
R(S,R10K,'ID_WP','+3V3_SAFE',Description='ID_WP idle high = all ID EEPROMs write-protected')
jp=dict(SRC.inst['JP2'][0]['props']); jp.pop('Reference'); jp.update(Value='ID_WP_LOW',Note='Close only for factory/calibration ID EEPROM writes (all slots + HV meter)')
card(S).add('Jumper:SolderJumper_2_Open',card(S).newref('JP'),'ID_WP_LOW',{'1':'ID_WP','2':'GND'},jp); card(S).parts[-1]['in_bom']=False   # PCB feature, like JP2-JP4
# slot SPI chip selects
add(S,'cards:SN74LVC138APWR','U','C485077',{'1':'SLOT_CS_A0','2':'SLOT_CS_A1','3':'SLOT_CS_A2','6':'SLOT_CS_EN','4':'GND','5':'GND','16':'+3V3_SAFE','8':'GND',
    '15':'SL1_CS_N','14':'SL2_CS_N','13':'SL3_CS_N','12':'SL4_CS_N','11':'SL5_CS_N','10':'SL6_CS_N','9':'SL7_CS_N','7':'SL8_CS_N'}); C(S,C100N,'+3V3_SAFE')
# slot expanders on I2C2 root (0x20 EN_N/FAULT_N, 0x21 INT_N)
for a,lo,hi in ((0,'EN_N','FAULT_N'),(1,'INT_N',None)):
    pn={'1':'SLOT_EXP_INT_N','2':'GND','3':'GND','21':'+3V3_SAFE' if a else 'GND','22':'I2C2_SCL','23':'I2C2_SDA','24':'+3V3_SAFE','12':'GND'}
    for i in range(8):
        pn[str(4+i)]=f'SL{i+1}_{lo}'; pn[str(13+i)]=f'SL{i+1}_{hi}' if hi else None   # 0x21 port 1 spare: firmware drives low
    add(S,'Interface_Expansion:TCA9555PWR','U','C465732',pn,Value=f'TCA9555PWR @0x2{a}'); C(S,C100N,'+3V3_SAFE')
R(S,R10K,'SLOT_EXP_INT_N','+3V3_SAFE')
# slot ANA_OUT mux -> SLOT_ANA (MCU ADC, was MUXB_OUT)
add(S,'genctl:TMUX1208PWR','U','C494728',{'1':'MUX_A0','16':'MUX_A1','15':'MUX_A2','2':'+3V3_SAFE','13':'+3V3_SAFE','14':'GND','8':'SLOT_ANA','3':None,
    '4':'SL1_ANA','5':'SL2_ANA','6':'SL3_ANA','7':'SL4_ANA','12':'SL5_ANA','11':'SL6_ANA','10':'SL7_ANA','9':'SL8_ANA'}); C(S,C100N,'+3V3_SAFE')
# ---- per-slot power ----
S='slot_power'; blocks_sp=[]
for s in range(1,9):
    k=f'SL{s}'; refs=[]
    u=add(S,'genctl:TPS48100QDGXRQ1','U','C43131316',{'1':f'{k}_UVLO','2':'GND','3':f'{k}_PWR_EN','5':f'{k}_FAULT_N','6':'GND','7':'GND','8':f'{k}_ISCP','9':f'{k}_TMR','10':'GND',
        '12':f'{k}_BST','13':f'{k}_VBAT','14':f'{k}_GPD','15':f'{k}_GPU','17':f'{k}_DRN','18':'VBAT_P','20':'VBAT_P','4':None,'11':None,'19':None}); refs.append(u)
    refs.append(R(S,'C2903468','VBAT_P',f'{k}_DRN'))
    for i in range(2): refs.append(add(S,'Transistor_FET:BSC070N10NS5','Q',FET,{'5':f'{k}_DRN','1':f'{k}_VBAT','2':f'{k}_VBAT','3':f'{k}_VBAT','4':f'{k}_G'}))
    refs+=[R(S,'C22859',f'{k}_GPU',f'{k}_G'),R(S,'C21189',f'{k}_GPD',f'{k}_G'),R(S,'C23000',f'{k}_ISCP','GND'),C(S,'C106218',f'{k}_TMR'),
           C(S,'C1623',f'{k}_BST',f'{k}_VBAT'),R(S,R100K,'VBAT_P',f'{k}_UVLO'),R(S,'C22967',f'{k}_UVLO','GND')]
    u5=add(S,'genctl:TPS2553DBVR','U','C55266',{'1':'+5V','2':'GND','3':f'{k}_PWR_EN','4':f'{k}_FAULT_N','5':f'{k}_ILIM5','6':f'{k}_5V'})
    u3=add(S,'genctl:TPS2553DBVR','U','C55266',{'1':'+3V3_SAFE','2':'GND','3':f'{k}_PWR_EN','4':f'{k}_FAULT_N','5':f'{k}_ILIM3','6':f'{k}_3V3'})
    refs+=[u5,u3,R(S,'C23058',f'{k}_ILIM5','GND',Description='TPS2553 ILIM 45.3k: 523-638 mA'),R(S,'C23249',f'{k}_ILIM3','GND'),C(S,C100N,f'{k}_5V'),C(S,C100N,f'{k}_3V3')]
    g1=add(S,'cards:74LVC1G02','U','C7394016',{'1':f'{k}_EN_N','2':f'{k}_PRESENT_N','3':'GND','4':f'{k}_PWR_EN','5':'+3V3_SAFE'})
    g2=add(S,'cards:74LVC1G00','U','C7826',{'1':f'{k}_PWR_EN','2':'WD_OK','3':'GND','4':f'{k}_OUT_EN_N','5':'+3V3_SAFE'})
    refs+=[g1,g2,C(S,C100N,'+3V3_SAFE'),C(S,C100N,'+3V3_SAFE'),
           R(S,R10K,f'{k}_EN_N','+3V3_SAFE'),R(S,R10K,f'{k}_PRESENT_N','+3V3_SAFE'),R(S,R10K,f'{k}_FAULT_N','+3V3_SAFE'),R(S,R10K,f'{k}_INT_N','+3V3_SAFE'),
           R(S,R100,'+3V3_SAFE',f'{k}_3V3_ID',Description='+3V3_ID always on via 100R (EEPROM only)')]
    blocks_sp.append((f'Slot {s}: VBAT_FIELD switch (TPS48100, 10 mOhm, 7.9 A), +5V/+3V3 switches, PWR_EN / OUT_EN_N',refs))
add('io_core','Diode:BAT54C','D','C37704',{'1':'GLOW_SNSM','2':'ESTOP_TRIP_SNSM','3':'+3V3_SAFE'},Description='Relocated clamp: GLOW_SNSM + ESTOP_TRIP_SNSM (replaces D128 glow half / D135)')
R('io_core',R10K,'EXP25_P12_SPARE','+3V3_SAFE',Description='U76 P12 (was AUX10_RB_N) spare input pull-up')
# ---------------- global vs local labels ----------------
where=collections.defaultdict(set)
for f,c in cards.items():
    for p in c.parts:
        for n in p['pn'].values():
            if n: where[n].add(f)
for f in KEEP_SHEETS:
    s=open(os.path.join(ROOT,f+'.kicad_sch')).read()
    for n in re.findall(r'\(global_label "([^"]+)"',s): where[REN.get(n,n)].add(f)
where['EXP25_P12_SPARE'].add('frontpanel')
GL={n for n,w in where.items() if len(w)>1 and n not in RAILS}
# local nets that only lived in one baseline sheet but now meet across sheets are global too (above); report singles
single=collections.Counter()
for c in cards.values():
    for p in c.parts:
        for n in p['pn'].values():
            if n: single[n]+=1
def blocks_for(f,c):
    keys=[(p['ref'],p['unit']) for p in c.parts]
    if f=='slot_power':
        return [(t,[(r,1) for r in refs]) for t,refs in blocks_sp]
    if f=='backplane':
        conn=[(p['ref'],p['unit']) for p in c.parts if p['lib_id']=='cards:DIN41612_C96']
        rest=[k for k in keys if k not in conn]
        return [('ENGINE slot (keyed) + LV slots 1-8 sockets, DIN 41612 C96 female',conn),('ID muxes (I2C2: 0x70 slots 1-8, 0x71 engine + HV meter), slot CS decoder, slot expanders (0x20 EN_N/FAULT_N, 0x21 INT_N), slot ANA_OUT mux',rest)]
    # one block per IC/connector: the IC + 2-pin parts reachable through small non-rail nets without crossing another IC
    two={p['ref'] for p in c.parts if len({pp['num'] for pp in p['pins']})<=2}
    nets_of=collections.defaultdict(set); refs_on=collections.defaultdict(set)
    for p in c.parts:
        for n in p['pn'].values():
            if n and n not in RAILS: nets_of[p['ref']].add(n); refs_on[n].add(p['ref'])
    val={p['ref']:p['props'].get('Value','') for p in c.parts}
    heads=sorted({p['ref'] for p in c.parts}-two,key=lambda r:(-len(nets_of[r]),r))
    owner={}
    for h in heads:
        todo=[h]; seen={h}
        while todo:
            x=todo.pop()
            for n in nets_of[x]:
                if len(refs_on[n])>=9: continue
                for y in refs_on[n]:
                    if y in two and y not in owner and y not in seen: seen.add(y); owner[y]=h; todo.append(y)
    out=[]
    for h in heads:
        mem={h}|{y for y,o in owner.items() if o==h}
        out.append((f'{h} {val[h][:40]}',[k for k in keys if k[0] in mem]))
    rest=[k for k in keys if k[0] in two and k[0] not in owner]
    if rest: out.append(('Decoupling, bulk caps and rail-to-rail passives',rest))
    return out
NOTES={'mcu':['Regenerated from the baseline netlist (tag baseline-2026-11-23-locked) with the Phase 2 pin re-use: PC10/PC11/PC12 = SPI3 SCK/MISO/MOSI (AF6) slot bus; PE0/PE1/PD11 = slot CS decoder A0-A2, PD13 = decoder enable (100k pull-down = no slot selected); PC9 = SLOT_RST_N (100k pull-down = slots held in reset); PB4 = SLOT_EXP_INT_N; PB10/PB11 = I2C2 SCL/SDA (AF4, DS12110 rev 10) for the slot ID bus; PA? MUXB_OUT ADC pin = SLOT_ANA. DI5-DI12 MCU pins are free (DI-8 card serialises them). Baseline sheet notes: docs/modular/mainboard_sheet_notes.md.'],
 'estop':['J23 E-stop feed -> LM74700-Q1 ideal diode + BSC070N10NS5 (reverse battery to -65 V) -> VBAT_ESTOP_PRE: E-stop status sense (R251 -> U34), trip driver bias (R400). Rail cut TPS48100 + 2x BSC070N10NS5 + 2 mOhm (trip 15.8/20/24.8 A) enabled by WD_OK AND ESTOP_OK -> VBAT_ESTOP: engine slot (fuel/crank/glow) and ADC readback R411. Replaces Q70/Q71 SQD40P10-40L, D137, R627.'],
 'io_core':['What stays of the baseline inputs + outputs sheets after the card split. Free U62 inputs read SL1-8_PRESENT_N; U63 S1 GLOW_SNSM, S2 ESTOP_TRIP_SNSM (new BAT54C clamp next to U63), S3-S8 GND. U30 AIN1-3 / U29 AIN2 unused (AI-4 card). Baseline sheet notes: docs/modular/mainboard_sheet_notes.md.'],
 'backplane':['Universal LV pinout docs/modular/slot_pinout_LV.csv; engine pinout cards/engine/engine_slot_pinout.csv. Slot ID straps: slot n = ID n-1, 0 = GND, 1 = open (card pull-up); IDP makes ID0..2+IDP odd. ID_WP is high (protected) unless pulled low at the test pad for factory writes.'],
 'slot_power':['Each slot: TPS48100 + 2x BSC070N10NS5 + 10 mOhm (ISCP 30.1k, 7.9 A typ) from VBAT_P; TPS2553 45.3k (+5V, 523-638 mA) and 80.6k (+3V3, 291-370 mA). PWR_EN = NOT EN_N AND NOT PRESENT_N (74LVC1G02); OUT_EN_N = NOT(PWR_EN AND WD_OK) (74LVC1G00). All three switch faults and the card CARD_FAULT_N share SLn_FAULT_N.'],
 'mtr_if':['J31.12 / J31.16 now carry MTR_ID_SCL / MTR_ID_SDA from ID mux 0x71 channel 1 (HV meter AT24CS32), matching J32.12 / J32.16 on genctl_meter.']}
def write_root():
    fn=os.path.join(ROOT,'genctl.kicad_sch'); t=open(fn).read()
    t=re.sub(r'\(sheet \(at [^\n]*\n','',t)
    ent=[]; pages=['power','mcu','cm5','comms','display','io_core','backplane','slot_power','estop','mtr_if','frontpanel']
    names={'power':'Power: input protection, ideal diode, 12V buck-boost, 5V, 3V3','cm5':'Raspberry Pi CM5','comms':'Comms: CAN x2, RS-485, Ethernet, USB hub/ports, router 12V',
           'display':'Display: DSI->LVDS bridge, panel power, backlight, touch','frontpanel':'Front panel: backlit buttons, buzzer'}
    for i,f in enumerate(pages):
        uid=KEEP_SHEETS.get(f) or SHEETS[f][0]; nm=names.get(f) or SHEETS[f][1]
        x=20+80*(i%4); y=40+45*(i//4)
        ent.append(f'(sheet (at {x} {y}) (size 60 25) (fields_autoplaced yes) (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0000)) (uuid "{uid}")'
          f'(property "Sheetname" "{nm}" (at {x} {y-0.7} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))'
          f'(property "Sheetfile" "{f}.kicad_sch" (at {x} {y+25.6} 0) (effects (font (size 1.27 1.27)) (justify left top)))'
          f'(instances (project "genctl" (path "/{ROOTUUID}" (page "{i+2}")))))')
    t=re.sub(r'\(text "All inter-sheet[^\n]*\n','',t)
    k=t.index('(sheet_instances')
    t=t[:k]+'\n'.join(ent)+'\n(text "All inter-sheet nets are global labels (names identical across sheets). Rails use power symbols.\\nPhase 2 (modular): io_core/backplane/slot_power/estop/mcu/mtr_if regenerated by cards/tools/mainboard.py from tag baseline-2026-11-23-locked; inputs/outputs retired." (exclude_from_sim no) (at 20 190 0) (effects (font (size 2 2)) (justify left top)) (uuid "20faa0b2-3e04-4a28-b429-178a5abb4d04"))\n'+t[k:]
    open(fn,'w').write(t)
    fp=os.path.join(ROOT,'frontpanel.kicad_sch'); t=open(fp).read()
    for a,b in (('AUX9_MCU','EXP25_P07_SPARE'),('AUX10_MCU','EXP25_P10_SPARE'),('AUX10_RB_N','EXP25_P12_SPARE')):
        t=t.replace(f'(global_label "{a}"',f'(global_label "{b}"')
    open(fp,'w').write(t)
if __name__=='__main__':
    FLAGS={'U7_VBAT','VDDA_F','VBAT_ESTOP_PRE','VBAT_ESTOP_IN','VBAT_ESTOP','D120_K'}; flagged=set()
    for f,c in cards.items():
        uid,title,paper=SHEETS[f]
        here={n for p in c.parts for n in p['pn'].values() if n}; fl=(FLAGS-flagged)&here; flagged|=fl
        for paper in ('A3','A2','A1','A0'):   # smallest sheet that packs without overflow
            c.paper=paper; D=schdraw.Drawer(c,RAILS,blocks_for(f,c),paper,NOTES.get(f,[]))
            D.labels_only={p['ref'] for p in c.parts if p['lib_id'].startswith(('cards:DIN','Connector'))}; D.pad=1
            D.path=f'{ROOTUUID}/{uid}'; D.proj='genctl'; D.glabels=GL; schdraw.GLOBALS=GL; D.noflags=True; D.flagnets=fl; D.flagtitle='PWR_FLAG'
            over=schdraw.run(D,ROOT,title)
            if not over: break
        SHEETS[f]=(uid,title,paper)
        print(f,'parts',len({p['ref'] for p in c.parts}),'overflow',over,'left',len(D.left))
    write_root()
    json.dump(dict(removed_p1=REMOVED_P1,removed_p2=REMOVED_P2,ov={f'{a}.{b}':v for (a,b),v in OV.items()},ren=REN,sheet={r:f for r,f in ASSIGN_SHEET.items()}),
              open(os.path.join(ROOT,'docs/modular/mainboard_rework.json'),'w'),indent=1)
