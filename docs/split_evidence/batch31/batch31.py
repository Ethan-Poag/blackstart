"""Batch 31 schematic edits (run once from repo root on 956a998).
Hardware shunt-off gating: AI_SH_Gx = AI_SH_ENx AND SH_ALLOW, SH_ALLOW = WD_OK AND NRST.
U91/U92 74LVC08APW (C6053), C320/C321/C322 100n (C14663), RN1/RN2 10k x4 (C29718),
U93 SN74LVC1G17DBVR Schmitt buffer (C7836, same part as U85) on NRST -> NRST_S (NRST rises slowly through C65 100n,
so it must not drive an LVC input directly: LVC dt/dV limit 10 ns/V).
Also: R531 MPN/Manufacturer; J2/U71/U72 footprint attr smd."""
import sys,re,math
sys.path.insert(0,'/workspace/review/fix29'); sys.path.insert(0,'/workspace/review/split/exec')
from ed import Sheet,U,HIDE,free
from geo import libsyms,libpins,instances
from sx import block_at
KS='/workspace/kicad-libs/kicad-symbols-9.0.2/'

def embed(sh,libfile,name,libid):
    L,(i,e)=libsyms(sh.s)
    if libid in L: return
    t=open(KS+libfile).read(); k=t.find(f'(symbol "{name}"'); b=t[k:block_at(t,k)]
    b=b.replace(f'(symbol "{name}"',f'(symbol "{libid}"',1)
    sh.s=sh.s[:e-1]+b+'\n'+sh.s[e-1:]

def placeu(sh,lib,ref,val,unit,x,y,fp,props,conn,pwrref):
    L,_=libsyms(sh.s); lb=L[lib]
    pl={}
    for n,v in libpins(lb).items():
        for px,py,u in v:
            if u in (0,unit): pl[n]=(px,py); break
    dirs={}
    for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)',lb):
        pb=lb[m.start():block_at(lb,m.start())]; num=re.search(r'\(number "([^"]+)"',pb).group(1)
        a=math.radians(float(m.group(3))); dirs.setdefault(num,(-math.cos(a),math.sin(a)))
    body=[f'(symbol (lib_id "{lib}") (at {x:.2f} {y:.2f} 0) (unit {unit}) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}")',
          f'(property "Reference" "{ref}" (at {x:.2f} {y-6.35:.2f} 0) (effects (font (size 1.27 1.27))))',
          f'(property "Value" "{val}" (at {x:.2f} {y+6.35:.2f} 0) (effects (font (size 1.27 1.27))))',
          f'(property "Footprint" "{fp}" (at {x:.2f} {y:.2f} 0) {HIDE})',f'(property "Datasheet" "~" (at {x:.2f} {y:.2f} 0) {HIDE})']
    for k,v in props: body.append(f'(property "{k}" "{v}" (at {x:.2f} {y:.2f} 0) {HIDE})')
    for n in pl: body.append(f'(pin "{n}" (uuid "{U()}"))')
    body.append(f'(instances (project "{sh.project}" (path "{sh.ipath}" (reference "{ref}") (unit {unit}))))')
    body.append(')'); sh.new.append(''.join(body))
    for n,(kind,name) in conn.items():
        px,py=pl[n]; p=(round(x+px,2),round(y-py,2)); d=dirs[n]
        if kind=='nc': sh.new.append(f'(no_connect (at {p[0]:.2f} {p[1]:.2f}) (uuid "{U()}"))'); continue
        end=(round(p[0]+2.54*d[0],2),round(p[1]+2.54*d[1],2)); sh.wire(p,end)
        ang={(1,0):0,(-1,0):180,(0,-1):90,(0,1):270}[(round(d[0]),round(d[1]))]
        if kind=='label': sh.label(name,end,ang)
        elif kind=='global': sh.label(name,end,ang,glob=True)
        elif kind=='gnd':
            prot={(0,1):0,(0,-1):180,(1,0):90,(-1,0):270}[(round(d[0]),round(d[1]))]
            sh.place('power:GND',pwrref.pop(0),'GND',end[0],end[1],rot=prot)

sh=Sheet('inputs.kicad_sch')
# 1. relabel FET-gate side of each shunt enable
QG={1:(426.72,457.2),2:(477.52,459.74),3:(508,490.22),4:(528.32,447.04),5:(548.64,495.3),6:(426.72,497.84)}
QREF={1:'Q15',2:'Q19',3:'Q23',4:'Q27',5:'Q31',6:'Q35'}
inst={d['ref']:d for d in instances(sh.s)}
for k,pt in QG.items():
    gp=inst[QREF[k]]['pins']['1']; assert abs(gp[0]-2.54-pt[0])<0.01 and abs(gp[1]-pt[1])<0.01,(k,gp,pt)
    sh.relabel(pt,f'AI_SH_EN{k}',f'AI_SH_G{k}')
embed(sh,'74xx.kicad_sym','74LS08','74xx:74LS08')
embed(sh,'Device.kicad_sym','R_Pack04','Device:R_Pack04')
so=open('outputs.kicad_sch').read(); Lo,_=libsyms(so); L,(li,le)=libsyms(sh.s)
if '74xGxx:74LVC1G17' not in L: sh.s=sh.s[:le-1]+Lo['74xGxx:74LVC1G17']+'\n'+sh.s[le-1:]
x0,y0=free(sh,150,90); print('block at',x0,y0)
pw=[f'#PWR{n}' for n in range(3108,3140)]
LV=[('LCSC','C6053'),('MPN','74LVC08APW,118'),('Manufacturer','Nexperia'),('Description','Quad 2-input AND, LVC, 5 V tolerant inputs'),
    ('Note','Batch 31: hardware shunt-off gate. AI_SH_Gx = AI_SH_ENx AND SH_ALLOW; SH_ALLOW = WD_OK AND NRST. All six 4-20 mA shunt FETs off while MCU in reset or watchdog tripped.')]
FPU='Package_SO:TSSOP-14_4.4x5mm_P0.65mm'
GATE={1:('1','2','3'),2:('4','5','6'),3:('9','10','8'),4:('12','13','11')}
for k in range(1,5):
    a,b,y=GATE[k]
    placeu(sh,'74xx:74LS08','U91','74LVC08APW',k,x0+15.24,y0+k*17.78,FPU,LV,{a:('label',f'AI_SH_EN{k}'),b:('label','SH_ALLOW'),y:('label',f'AI_SH_G{k}')},pw)
for k in (1,2):
    a,b,y=GATE[k]
    placeu(sh,'74xx:74LS08','U92','74LVC08APW',k,x0+55.88,y0+k*17.78,FPU,LV,{a:('label',f'AI_SH_EN{k+4}'),b:('label','SH_ALLOW'),y:('label',f'AI_SH_G{k+4}')},pw)
a,b,y=GATE[3]
placeu(sh,'74xx:74LS08','U92','74LVC08APW',3,x0+55.88,y0+3*17.78,FPU,LV,{a:('global','WD_OK'),b:('label','NRST_S'),y:('label','SH_ALLOW')},pw)
a,b,y=GATE[4]
placeu(sh,'74xx:74LS08','U92','74LVC08APW',4,x0+55.88,y0+4*17.78,FPU,LV,{a:('gnd',''),b:('gnd',''),y:('nc','')},pw)
for ref,xx in (('U91',x0+88.9),('U92',x0+101.6)):
    placeu(sh,'74xx:74LS08',ref,'74LVC08APW',5,xx,y0+30.48,FPU,LV,{'14':('global','+3V3_SAFE'),'7':('gnd','')},pw)
placeu(sh,'74xGxx:74LVC1G17','U93','SN74LVC1G17DBVR',1,x0+15.24,y0+104.14,'Package_TO_SOT_SMD:SOT-23-5',
    [('LCSC','C7836'),('MPN','SN74LVC1G17DBVR'),('Manufacturer','Texas Instruments'),('Description','Single Schmitt buffer'),('Note','Batch 31: Schmitt buffer NRST -> NRST_S for U92 gate 3. NRST rises slowly (C65 100n + MCU pull-up); LVC08 inputs need fast edges.')],
    {'1':('nc',''),'2':('global','NRST'),'4':('label','NRST_S'),'5':('global','+3V3_SAFE'),'3':('gnd','')},pw)
CP=[('LCSC','C14663'),('MPN','CC0603KRX7R9BB104'),('Manufacturer','YAGEO'),('Description','Unpolarized capacitor')]
for ref,xx,yy,u in (('C320',x0+88.9,y0+78.74,'U91'),('C321',x0+101.6,y0+78.74,'U92'),('C322',x0+40.64,y0+104.14,'U93')):
    placeu(sh,'Device:C',ref,'100n',1,xx,yy,'Capacitor_SMD:C_0603_1608Metric',CP+[('Note',f'Batch 31: {u} VCC decoupling, place at its VCC pin')],{'1':('global','+3V3_SAFE'),'2':('gnd','')},pw)
RP=[('LCSC','C29718'),('MPN','4D03WGJ0103T5E'),('Manufacturer','UNI-ROYAL'),('Description','4 resistor network, isolated, 0603x4 convex')]
placeu(sh,'Device:R_Pack04','RN1','10k x4',1,x0+124.46,y0+30.48,'Resistor_SMD:R_Array_Convex_4x0603',RP+[('Note','Batch 31: gate-side pull-downs AI_SH_G1-4 (shunt FET off if U91 unpowered / output floating)')],
       {'8':('label','AI_SH_G1'),'7':('label','AI_SH_G2'),'6':('label','AI_SH_G3'),'5':('label','AI_SH_G4'),'1':('gnd',''),'2':('gnd',''),'3':('gnd',''),'4':('gnd','')},pw)
placeu(sh,'Device:R_Pack04','RN2','10k x4',1,x0+124.46,y0+78.74,'Resistor_SMD:R_Array_Convex_4x0603',RP+[('Note','Batch 31: gate-side pull-downs AI_SH_G5-6; elements 3/4 spare, both ends GND')],
       {'8':('label','AI_SH_G5'),'7':('label','AI_SH_G6'),'6':('gnd',''),'5':('gnd',''),'1':('gnd',''),'2':('gnd',''),'3':('gnd',''),'4':('gnd','')},pw)
sh.text('Batch 31 hardware shunt-off gating (Ethan approved Nov 22, 2026 HST). Each 4-20 mA shunt FET gate AI_SH_Gx = AI_SH_ENx (U31 TCA9555) AND SH_ALLOW. SH_ALLOW = WD_OK (U84, latched low on TPS3431 timeout until power cycle) AND NRST (MCU reset, through U93 Schmitt buffer as NRST_S). Shunts are therefore off while the MCU is in reset, after a watchdog trip, and for the first 0.70-1.06 s after power-on. R138/R149/R160/R171/R182/R193 keep the U31-side enables low while U31 pins are inputs; RN1/RN2 hold the FET gates low if U91/U92 are unpowered. Firmware: treat AI 4-20 mA channels as invalid while SH_ALLOW (WD_OK) is low. See docs/FW_REQ_BATCH30.md.',x0,y0)
sh.save()
# R531 MPN
sd=Sheet('display.kicad_sch'); sd.set_prop('R531','MPN','0603WAF220JT5E'); sd.set_prop('R531','Manufacturer','UNI-ROYAL'); sd.save()
# footprint attrs
for f in ('genctl.pretty/FTSH-105-01_SWD.kicad_mod','genctl.pretty/ADE9000_LFCSP-40_6x6.kicad_mod'):
    t=open(f).read(); assert t.count('(attr through_hole)')+t.count('(attr smd)')==1; open(f,'w').write(t.replace('(attr through_hole)','(attr smd)'))
print('ok')
