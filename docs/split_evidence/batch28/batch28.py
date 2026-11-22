import re,sys
sys.path.insert(0,'/workspace/review/fix28')
from ed import *
from geo import blocks,libsyms
W='/workspace/m7/split/'
def tprops(sh,ref,keys=('LCSC','MPN','Manufacturer','Description')):
    b=sh.sym(ref)[0][2]; out=[]
    for k in keys:
        m=re.search(r'\(property "%s" "((?:[^"\\]|\\.)*)"'%k,b)
        if m: out.append((k,m.group(1)))
    fp=re.search(r'\(property "Footprint" "([^"]*)"',b).group(1)
    return fp,out
pwr=[f'#PWR{n:04d}' for n in range(3100,3200)]
def to_local(sh,pt,old,new):
    h=[x for x in at_point(sh.s,pt) if x[0]=='(global_label' and f'"{old}"' in x[3]]; assert len(h)==1,(pt,old,h)
    sh._rep(h[0][1],h[0][2],''); ang=0 if pt[0]>100 else 180
    sh.label(new,pt,ang)
# ---------------- inputs ----------------
ins=Sheet(W+'inputs.kicad_sch')
R10K=[('Value','10k'),('LCSC','C25804'),('MPN','0603WAF1002T5E'),('Manufacturer','UNI-ROYAL')]
for r in ('R204','R209'):
    for k,v in R10K+[('Note','Batch 28: 100k -> 10k. TCA9555 (U31) powers up as input with ~100k internal pull-up; 100k:100k left ~1.65 V on the DI pull-down FET gate while DI_PU defaults on. 10k gives ~0.30 V (< IRLML0100 VGS(th) 1.0 V min)')]:
        ins.set_prop(r,k,v)
for r in ('R138','R149','R160','R171','R182','R193'):
    for k,v in R10K+[('Note','Batch 28: 100k -> 10k so the AI shunt FET stays off (~0.30 V gate) while U31 is still an input with its ~100k pull-up')]:
        ins.set_prop(r,k,v)
for q in ('Q15','Q19','Q23','Q27','Q31','Q35','Q38','Q41'):
    for k,v in [('Value','IRLML0100'),('MPN','IRLML0100TRPBF'),('LCSC','C53658'),('Manufacturer','Infineon Technologies'),
                ('Datasheet','https://www.infineon.com/dgdl/irlml0100pbf.pdf?fileId=5546d462533600a401535664773825df'),
                ('Description','N-MOSFET 100 V 1.6 A SOT-23, VGS(th) 1.0-2.5 V, RDS(on) 235 mR max @4.5 V'),
                ('Note','Batch 28: was DMN6075S (60 V < SMAJ40CA 64.5 V clamp; VGS(th) up to 3.0 V at 3.3 V drive). Same SOT-23 G-S-D pinout; symbol kept')]:
        ins.set_prop(q,k,v)
fpD,_=tprops(ins,'D46')
x,y=free(ins,60,40)
ins.text('Batch 28: SMAJ40A at the DI_BIAS_A/B field pins (J21.6, J22.1). DI_BIAS = VBAT_P via Q36/Q39 + TPS26621 eFuse: max 40.1 V (LM74800 OV cut-off max) < VRWM 40 V + VBR 44.4 V min; clamp 64.5 V < IRLML0100 100 V. Unidirectional: the bias never goes negative. Place at the connector.',x,y)
PT=[('LCSC','C113969'),('MPN','SMAJ40A'),('Manufacturer','MDD(Microdiode Semiconductor)'),('Description','TVS unidirectional 400 W, VRWM 40 V, VBR 44.4 V min, VC 64.5 V'),('Note','Batch 28: DI_BIAS field-pin surge clamp')]
ins.place('Device:D_Zener','D150','SMAJ40A',x+5.08,y+12.7,fpD,PT+[('Note','Batch 28: DI_BIAS_A (J21.6) surge clamp, place at J21')],conn={'1':('label','DI_BIAS_A'),'2':('pwr',('power:GND','GND'))},rot=90,pwrref=pwr)
ins.place('Device:D_Zener','D151','SMAJ40A',x+30.48,y+12.7,fpD,PT+[('Note','Batch 28: DI_BIAS_B (J22.1) surge clamp, place at J22')],conn={'1':('label','DI_BIAS_B'),'2':('pwr',('power:GND','GND'))},rot=90,pwrref=pwr)
ins.save()
# ---------------- mcu: VREF+ ----------------
mc=Sheet(W+'mcu.kicad_sch')
def delwire(sh,a,b):
    for i,e,blk in blocks(sh.s,'(wire (pts'):
        pts=[tuple(map(float,m)) for m in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)',blk)]
        if set(pts)=={a,b}: sh._rep(i,e,''); return
    raise Exception(('nowire',a,b))
delwire(mc,(217.17,163.83),(218.44,163.83)); delwire(mc,(218.44,163.83),(215.9,163.83))
mc.wire((215.9,163.83),(217.17,163.83)); mc.wire((218.44,163.83),(218.44,166.37)); mc.label('VDDA_F',(218.44,166.37),180)
mc.label('VDDA_F',(248.92,119.38),90)
fpC1,p1u=tprops(mc,'C56'); fpC,p100n=tprops(mc,'C57')
x,y=free(mc,45,35)
mc.text('Batch 28: VREF+ (U7 pin 20) moved from +3V3_SAFE to VDDA_F (after FB1, same node as VDDA, so VREF+ <= VDDA always). C318 1u X7R + C319 100n at pin 20 (DS12110 6.1.6 / AN5036).',x,y)
mc.place('Device:C','C318','1u',x+5.08,y+12.7,'Capacitor_SMD:C_0805_2012Metric',[('LCSC','C28323'),('MPN','CL21B105KBFNNNE'),('Manufacturer','Samsung Electro-Mechanics'),('Note','Batch 28: VREF+ decoupling, place at U7 pin 20')],conn={'1':('label','VDDA_F'),'2':('pwr',('power:GND','GND'))},pwrref=pwr)
mc.place('Device:C','C319','100n',x+20.32,y+12.7,fpC,p100n+[('Note','Batch 28: VREF+ decoupling, place at U7 pin 20')],conn={'1':('label','VDDA_F'),'2':('pwr',('power:GND','GND'))},pwrref=pwr)
mc.save()
# ---------------- mtr_if: 33R + ESD ----------------
mt=Sheet(W+'mtr_if.kicad_sch')
cs=open(W+'comms.kicad_sch').read(); LC,_=libsyms(cs)
L,(li,le)=libsyms(mt.s)
if 'genctl:RClamp0524P' not in L:
    mt.s=mt.s[:le-1]+LC['genctl:RClamp0524P']+'\n'+mt.s[le-1:]
co=Sheet(W+'comms.kicad_sch'); fpE,pE=tprops(co,'D17')
SER=[('ADE_SCK',(88.90,88.90)),('ADE_MOSI',(88.90,93.98)),('ADE_CS1_N',(116.84,83.82)),('ADE_CS2_N',(116.84,86.36)),('ADE_RST_N',(116.84,91.44))]
for n,pt in SER: to_local(mt,pt,n,n+'_J')
W_=mt.paper
x,y=25.4,129.54
mt.text('Batch 28: R644-R648 33R source series resistors on the MCU-driven inter-board lines (place within 10 mm of U7 PA5/PA7/PA4/PC4/PC5): damp ringing on the ~80 mm harness and limit ESD current into the MCU. D152/D153 RClamp0524PA (same part as D17/D18, 0.3 pF, 5 V) fitted at J31 on all 8 signal lines: the harness is unplugged in service (FW-MTR-8) and MISO/IRQ/MTR_DET_N otherwise reach MCU/TCA pins unprotected.',x,y)
R33=[('LCSC','C23140'),('MPN','0603WAF330JT5E'),('Manufacturer','UNI-ROYAL'),('Description','Resistor 33R 1% 0603'),('Note','Batch 28: SPI source series R, place at U7')]
for i,(n,pt) in enumerate(SER):
    mt.place('Device:R',f'R{644+i}','33R',x+35.56,139.7+i*7.62,'Resistor_SMD:R_0603_1608Metric',R33,conn={'1':('global',n),'2':('label',n+'_J')},rot=90)
ESD=[('D152',{'1':'ADE_SCK_J','2':'ADE_MOSI_J','4':'ADE_MISO','5':'ADE_CS1_N_J'}),('D153',{'1':'ADE_CS2_N_J','2':'ADE_RST_N_J','4':'ADE_IRQ_N','5':'MTR_DET_N'})]
pair={'1':'10','2':'9','4':'7','5':'6'}
for j,(ref,m) in enumerate(ESD):
    conn={}
    for p,n in m.items():
        k='global' if not n.endswith('_J') else 'label'
        conn[p]=(k,n); conn[pair[p]]=(k,n)
    conn['3']=('pwr',('power:GND','GND')); conn['8']=('pwr',('power:GND','GND'))
    mt.place('genctl:RClamp0524P',ref,'RClamp0524PA',170.18+j*60.96,124.46,fpE,pE+[('Note','Batch 28: J31 ESD array, place at J31 (flow-through)')],conn=conn,pwrref=pwr)
mt.save()
# ---------------- meter: crystal caps ----------------
ac=Sheet(W+'ac_metering.kicad_sch')
for c in ('C257','C258'):
    for k,v in [('Value','15p'),('LCSC','C1548'),('MPN','0402CG150J500NT'),('Manufacturer','FH (Guangdong Fenghua Advanced Tech)'),
                ('Note','Batch 28: 22p -> 15p C0G. Y3 X322524576MOB4SI CL = 12 pF; Cext = 2 x (CL - Cstray), Cstray ~4.5 pF (ADE9000 4 pF per pin in series = 2 pF + ~2.5 pF board) -> 15 pF')]:
        ac.set_prop(c,k,v)
ac.save()
print('ok',pwr[0])
# ---------------- outputs: stale R294/R300 notes ----------------
ou=Sheet(W+'outputs.kicad_sch')
for r in ('R294','R300'):
    ou.set_prop(r,'Note','RISCP, ISCP to GND (TPS48100-Q1 DS SLUSEW1C pin table). V(SCP) = 2 uA x 40.2k + 19 mV = 99.4 mV typ (DS table: 75 mV @28k, 300 mV @140.5k); Isc = 99.4 mV / 20 mR (R297/R303) = 4.97 A typ (B3-8; Batch 28 note fix, was 35.7k / 1 mR / 90 A)')
ou.save()
print('notes ok')
