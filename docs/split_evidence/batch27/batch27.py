import re,sys
sys.path.insert(0,'/workspace/review/fix27')
from ed import *
W='/workspace/m7/split/'
def tprops(sh,ref,keys=('LCSC','MPN','Manufacturer','Description')):
    b=sh.sym(ref)[0][2]; out=[]
    for k in keys:
        m=re.search(r'\(property "%s" "((?:[^"\\]|\\.)*)"'%k,b)
        if m: out.append((k,m.group(1)))
    fp=re.search(r'\(property "Footprint" "([^"]*)"',b).group(1)
    return fp,out
pwr=[f'#PWR{n:04d}' for n in range(3000,3100)]
# ---------------- CM5 sheet ----------------
cm=Sheet(W+'cm5.kicad_sch')
fpR,p10k=tprops(cm,'R69'); fpR2,p100k=tprops(cm,'R71'); fpQ,pQ=tprops(cm,'Q10')
assert '10k' in cm.sym('R69')[0][2] and '100k' in cm.sym('R71')[0][2]
# 1. U12 ST pull-up: label the ST net at U12 pin 9, R637 10k to +5V_CM5
cm.label('HU_ST',(316.23,280.67),0)
x,y=345.44,317.5
cm.text('Batch 27: R637 = TPS2121 ST pull-up (open-drain, DS SLVSEA3F 8.3 RST 6-20k) to +5V_CM5 (U12 OUT, present whenever U12 drives the CM5; CM5_3V3 would read PWR_FAIL while the CM5 is off).',x,y)
cm.place('Device:R','R637','10k',x+5.08,y+12.7,fpR,p10k+[('Note','TPS2121 ST pull-up (Batch 27)')],conn={'1':('pwr',('power:VCC','+5V_CM5')),'2':('label','HU_ST')},pwrref=pwr)
# 7. EEPROM_nWP: R558 DNP; Q74 pulls nWP low only when U73 P15 (CM5_EEPROM_LOCK_N) is driven low
cm.set_dnp('R558'); cm.set_prop('R558','Note','DNP (Batch 27): fit only for a permanently write-protected build. Default: nWP floats (CM5 internal 100k to CM5_3V3) = EEPROM writable; MCU can lock via U73 P15 -> Q73/Q74')
x,y2=101.6,360.68
cm.text('Batch 27: CM5 boot EEPROM write-protect. U73 P15 CM5_EEPROM_LOCK_N: input/high (TCA9555 default, 100k pull-up) -> Q73 on -> Q74 off -> nWP floats = writable. Output low -> Q74 on -> nWP low = locked (set before PMIC_EN rises, CM5 DS 3.1).',x,y2)
cm.place('Device:R','R641','10k',x+5.08,y2+27.94,fpR,p10k,conn={'1':('global','CM5_EEPROM_LOCK_N'),'2':('label','WP_QB1')})
cm.place('Device:R','R642','100k',x+22.86,y2+27.94,fpR2,p100k,conn={'1':('label','WP_QB1'),'2':('pwr',('power:GND','GND'))},pwrref=pwr)
cm.place('Transistor_BJT:MMBT3904','Q73','MMBT3904',x+38.1,y2+27.94,fpQ,pQ,conn={'1':('label','WP_QB1'),'2':('pwr',('power:GND','GND')),'3':('label','WP_QB2')},pwrref=pwr)
cm.place('Device:R','R643','100k',x+60.96,y2+27.94,fpR2,p100k,conn={'1':('global','+3V3_SAFE'),'2':('label','WP_QB2')})
cm.place('Transistor_BJT:MMBT3904','Q74','MMBT3904',x+81.28,y2+27.94,fpQ,pQ,conn={'1':('label','WP_QB2'),'2':('pwr',('power:GND','GND')),'3':('label','CM5_EEPROM_NWP')},pwrref=pwr)
cm.save()
# ---------------- frontpanel: U73 P15 ----------------
fp=Sheet(W+'frontpanel.kicad_sch')
fp.remove_nc((77.47,158.75)); fp.label('CM5_EEPROM_LOCK_N',(77.47,158.75),0,glob=True)
fp.save()
# ---------------- inputs ----------------
ins=Sheet(W+'inputs.kicad_sch')
# 2. U35 -> TLV1812DR
for k,v in [('Value','TLV1812'),('MPN','TLV1812DR'),('LCSC','C6333176'),('Manufacturer','Texas Instruments'),('Datasheet','https://www.ti.com/lit/ds/symlink/tlv1812.pdf'),
            ('Description','Dual 40 V rail-to-rail-input push-pull comparator, SOIC-8, LM393 pinout'),('Note','Batch 27: was LM393 (VICR VCC-1.5/-2.0 V < 1.65 V VMID bias at 3.3 V; 0-70 C part). TLV1812 VCM (V-)-0.2..(V+)+0.2 V, -40..125 C')]:
    ins.set_prop('U35',k,v)
for r in ('R259','R260'):
    ins.set_dnp(r); ins.set_prop(r,'Note','DNP (Batch 27): U35 TLV1812 is push-pull; footprint kept for an open-drain TLV1822 alternate')
# 3. VMID: R638 100R in series with C129 only (resistive loads stay on the feedback node)
ins.relabel((387.35,350.52),'VMID','VMID_C')
fpr,p100=tprops(ins,'R140')
x,y=373.38,604.52
ins.text('Batch 27: R638 100R isolates C129 (1u) from U25A output (TLV906x cap-load drive 100 pF, SBOS839N p1); DC loads stay on VMID = feedback node, no offset.',x,y)
ins.place('Device:R','R638','100R',x+5.08,y+12.7,'Resistor_SMD:R_0603_1608Metric',[('LCSC','C22775'),('MPN','0603WAF1000T5E'),('Manufacturer','UNI-ROYAL'),('Description','Resistor')],conn={'1':('label','VMID'),'2':('label','VMID_C')})
# 5. D+ excitation pre-drop: R639||R640 100R 2512 between Q42 drain (DPX_VI) and U36 VI (DPX_LDO_IN)
ins.relabel((60.96,547.37),'DPX_VI','DPX_LDO_IN'); ins.relabel((111.76,554.99),'DPX_VI','DPX_LDO_IN')
x3,y3=55.88,604.52
ins.text('Batch 27: R639||R640 (2x 100R 1W 2512 = 50R) take 0.78 W of the D+ source loss (125 mA) off U36; full 125 mA down to ~10.8 V battery. Firmware: drop excitation if D+ not up within 30 s (charge-fail alarm).',x3,y3)
P2512=[('LCSC','C35218'),('MPN','25121WF1000T4E'),('Manufacturer','UNI-ROYAL'),('Description','Resistor 1 W 2512')]
ins.place('Device:R','R639','100R',x3+5.08,y3+12.7,'Resistor_SMD:R_2512_6332Metric',P2512,conn={'1':('label','DPX_VI'),'2':('label','DPX_LDO_IN')})
ins.place('Device:R','R640','100R',x3+20.32,y3+12.7,'Resistor_SMD:R_2512_6332Metric',P2512,conn={'1':('label','DPX_VI'),'2':('label','DPX_LDO_IN')})
ins.s=ins.s.replace('LM393 w/ hysteresis -> TIM2_CH1. D+: LM317 125mA source (10R) + SS110','TLV1812 (RRI, push-pull; Batch 27) w/ hysteresis -> TIM2_CH1. D+: 50R 2512 pre-drop + LM317 125mA source (10R) + SS110',1)
ins.save()
# ---------------- comms: C101 ----------------
co=Sheet(W+'comms.kicad_sch')
for k,v in [('Value','47u'),('Footprint','Capacitor_SMD:C_1210_3225Metric'),('MPN','CL32A476KOJNNNE'),('LCSC','C2932477'),('Manufacturer','Samsung Electro-Mechanics'),('Note','Batch 27: 10u -> 47u (CA-IS2092W VISO recommendation, same part as C85/C91)')]:
    co.set_prop('C101',k,v)
co.save()
# ---------------- power: D5 ----------------
pw=Sheet(W+'power.kicad_sch')
for k,v in [('Value','SMBJ6.0A'),('MPN','SMBJ6.0A'),('LCSC','C113976'),('Manufacturer','MDD(Microdiode Semiconductor)'),('Note','unidirectional TVS; Batch 27: was SMBJ5.0A (VRWM 5.0 V < 5.10-5.18 V rail). VRWM 6.0, VBR 6.67 min, VC 10.3 V @58 A')]:
    pw.set_prop('D5',k,v)
pw.save()
print('ok', pwr[0])
# --- follow-up: PWR_FLAG #FLG0018 moves with U36 VI (DPX_VI -> DPX_LDO_IN)
ins2=Sheet(W+'inputs.kicad_sch'); ins2.relabel((260.35,548.64),'DPX_VI','DPX_LDO_IN'); ins2.save()
