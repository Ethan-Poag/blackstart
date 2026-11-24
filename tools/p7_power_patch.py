#!/usr/bin/env python3
"""Split P7 (Ethan 2026-11-24 10:20 AM HST, "make fixes to both"): port the modular Pass 5/6 Q2 front-end fix to the two-board design.
Edits power.kicad_sch only (idempotent):
  1. U1 HGATE dV/dt network: R1001 1k + C601 22 nF / 100 V to GND (Q2 inrush ~0.6 A into ~230 uF instead of 36-53 A).
  2. C602 1 uF / 50 V on U2 EN/UVLO (BB_UVLO), R4 100k / R5 33k Thevenin 24.8k: tau ~25 ms.
  3. U5 LMR36506 EN/UVLO no longer strapped to VIN: R1125 100k / R1126 47k from VBAT_P (on above 4.25 V; EN <= 18.4 V at 57.6 V).
  4. Q2 hold-off: BAT_IN -> D401 1N4148W -> Q121 MMBT5401 (R1121 22k E-B, R1122 68k B -> VBAT_P; Vth 2.5-3.8 V) -> R1123 22k ->
     HO_F (C1121 100 nF || R1124 100k) -> Q122 MMBT3904 -> D402 BAT54C pulls BB_UVLO and U5_EN to <= 0.45 V while Q2 still ramps.
Same refs and values as m7-modular (MOD sections 19/20, Pass 8 resistor fix). Math: docs/split_evidence/p7/p7_calc.txt."""
import os,re,uuid
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fn=os.path.join(ROOT,'power.kicad_sch'); s=open(fn).read()
# P7 review: notes that still said U5 is "always on" (idempotent text fixes)
for old,new in (('+3V3_BK (always on); TPS2116','+3V3_BK (EN = R1125/R1126 divider from VBAT_P: on above 3.6-4.25 V; held off with U2 by the Q2 hold-off, Batch 34); TPS2116'),
                ('always-on 3.3V from battery, 65V abs max','3.3V backup from battery (EN divider R1125/R1126 + Q2 hold-off, Batch 34), 65V abs max')):
    if old in s: s=s.replace(old,new); open(fn,'w').write(s); print('power.kicad_sch: note updated:',old[:30])
if '(property "Reference" "D402"' in s: print('power.kicad_sch: P7 front end already present'); raise SystemExit
PATH='/2f7a4bb8-89ed-4e3c-b40c-67c49fede2c6/d8c05520-8978-4d93-9881-80f603685ecb'
U=lambda: str(uuid.uuid4())
F=lambda v: f'{v:.2f}'
pw=[9001]
def block(t,start):
    i=start; d=0
    while True:
        c=t[i]
        if c=='(': d+=1
        elif c==')':
            d-=1
            if d==0: return t[start:i+1]
        i+=1
def libsym(sheet,name):
    t=open(os.path.join(ROOT,sheet)).read(); i=t.index('(lib_symbols'); return block(t,t.index(f'(symbol "{name}"',i))
def sym(lib,ref,val,x,y,fp,lcsc,mpn,man,desc,pins):
    rx,ry,vy,j=(x,y-5.08,y+3.81,'') if lib.startswith('Diode:') else (x+2.54,y-1.27,y+1.27,' (justify left)')
    return (f'(symbol (lib_id "{lib}") (at {F(x)} {F(y)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}")\n'
      f'(property "Reference" "{ref}" (at {F(rx)} {F(ry)} 0) (effects (font (size 1.27 1.27)){j}))\n'
      f'(property "Value" "{val}" (at {F(rx)} {F(vy if lib.startswith('Diode:') else ry+2.54)} 0) (effects (font (size 1.27 1.27)){j}))\n'
      f'(property "Footprint" "{fp}" (at {F(x)} {F(y)} 0) (effects (font (size 1.27 1.27)) hide))\n'
      f'(property "Datasheet" "~" (at {F(x)} {F(y)} 0) (effects (font (size 1.27 1.27)) hide))\n'
      f'(property "Description" "{desc}" (at {F(x)} {F(y)} 0) (effects (font (size 1.27 1.27)) hide))\n'
      f'(property "LCSC" "{lcsc}" (at {F(x)} {F(y)} 0) (effects (font (size 1.27 1.27)) hide))\n'
      f'(property "MPN" "{mpn}" (at {F(x)} {F(y)} 0) (effects (font (size 1.27 1.27)) hide))\n'
      f'(property "Manufacturer" "{man}" (at {F(x)} {F(y)} 0) (effects (font (size 1.27 1.27)) hide))\n'
      +''.join(f'(pin "{p}" (uuid "{U()}"))\n' for p in pins)
      +f'(instances (project "genctl" (path "{PATH}" (reference "{ref}") (unit 1))))\n)\n')
def gnd(x,y):
    n=pw[0]; pw[0]+=1
    return (f'(symbol (lib_id "power:GND") (at {F(x)} {F(y)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}")\n'
     f'(property "Reference" "#PWR{n:04d}" (at {F(x)} {F(y+6.35)} 0) (effects (font (size 1.27 1.27)) hide))\n(property "Value" "GND" (at {F(x)} {F(y+3.81)} 0) (effects (font (size 1.27 1.27))))\n'
     f'(property "Footprint" "" (at {F(x)} {F(y)} 0) (effects (font (size 1.27 1.27)) hide))\n(property "Datasheet" "" (at {F(x)} {F(y)} 0) (effects (font (size 1.27 1.27)) hide))\n'
     f'(pin "1" (uuid "{U()}"))\n(instances (project "genctl" (path "{PATH}" (reference "#PWR{n:04d}") (unit 1))))\n)\n')
def wire(x1,y1,x2,y2): return f'(wire (pts (xy {F(x1)} {F(y1)}) (xy {F(x2)} {F(y2)})) (stroke (width 0) (type default)) (uuid "{U()}"))\n'
def label(n,x,y,a=0,j='left bottom'): return f'(label "{n}" (at {F(x)} {F(y)} {a}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {j})) (uuid "{U()}"))\n'
def glabel(n,x,y,a=0,j='left'):
    return (f'(global_label "{n}" (shape input) (at {F(x)} {F(y)} {a}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {j})) (uuid "{U()}") '
            f'(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {F(x)} {F(y)} 0) (effects (font (size 1.27 1.27)) hide)))\n')
def net(n,x,y,up):
    """connect a pin end at (x,y) to net n with a 2.54 mm stub (up = stub goes up)"""
    y2=y-2.54 if up else y+2.54
    if n=='GND': return wire(x,y,x,y+2.54)+gnd(x,y+2.54)
    if n=='VBAT_P': return wire(x,y,x,y2)+glabel('VBAT_P',x,y2,90 if up else 270,'left' if up else 'right')
    return wire(x,y,x,y2)+label(n,x,y2,90 if up else 270,'left bottom' if up else 'right bottom')
R0603='Resistor_SMD:R_0603_1608Metric'; UR='UNI-ROYAL'
# ---- 1+2: Pass 5 network (R1001/C601 at the U1 HGATE, C602 on BB_UVLO) as on m7-modular, C602 already 1 uF
X=190.5
add=(sym('Device:R','R1001','1k',X,135.89,R0603,'C21190','0603WAF1001T5E',UR,'P7: R1 1k in series with CdVdT (TI SNOSDB4 Fig 9-3)',['1','2'])
    +sym('Device:C','C601','22n 100V',X,147.32,'Capacitor_SMD:C_0603_1608Metric','C313105','CC0603KRX7R0BB223','YAGEO',
         'P7: CdVdT 22 nF / 100 V X7R HGATE -> GND: Q2 inrush 0.6 A typ (0.78 A max) into ~230 uF',['1','2'])
    +gnd(X,151.13)+wire(X,129.54,X,132.08)+wire(X,129.54,195.58,129.54)+label("LM748_HGATE",195.58,129.54)+wire(X,139.7,X,143.51)+label('LM748_DVDT',X,141.605))
XU=435.61
add+=(sym('Device:C','C602','1u 50V',XU,80.01,'Capacitor_SMD:C_0805_2012Metric','C28323','CL21B105KBFNNNE','Samsung',
         'P7: LM5176 EN/UVLO 1 uF X7R (tau ~25 ms with R4/R5): the Q2 hold-off (D402) pulls it below 1.17 V in <= 0.25 ms',['1','2'])
    +gnd(XU,83.82)+wire(XU,76.2,XU,73.66)+label('BB_UVLO',XU,73.66,90)
    +label('BB_UVLO',462.28,105.41,180,'right bottom'))
s=s.replace('(rectangle (start 20.32 46.99) (end 289.56 125.73)','(rectangle (start 20.32 46.99) (end 289.56 158.75)',1)
# ---- 3: U5 EN strap removal
for frag in ('(wire (pts (xy 477.52 219.71) (xy 477.52 222.25)) (stroke (width 0) (type default)) (uuid "0ef8a79f-d707-4e75-a8a5-b2087c0da3b5"))\n',
             '(junction (at 477.52 219.71) (diameter 0) (color 0 0 0 0) (uuid "8defdf2b-cc69-440d-a401-e2f98a7937f5"))\n'):
    assert s.count(frag)==1,frag[:60]; s=s.replace(frag,'')
add+=label('U5_EN',477.52,222.25,180,'right bottom')
# ---- 4: hold-off block in the free area (x 405-650, y 270-320)
Y=292.1; xs=dict(D401=419.1,Q121=458.47,R1121=472.44,R1122=487.68,R1123=502.92,R1124=518.16,C1121=533.4,Q122=561.34,D402=594.36,R1125=622.3,R1126=637.54)
x=xs['D401']; add+=sym('Diode:1N4148W','D401','1N4148W',x,Y,'Diode_SMD:D_SOD-123','C81598','1N4148W','ST(Semtech)','P7 hold-off: blocks reverse battery and the crank case from the PNP E-B junction',['1','2'])
add+=wire(x-3.81,Y,x-6.35,Y)+label('HO_E',x-6.35,Y,180,'right bottom')+wire(x+3.81,Y,x+8.89,Y)+label('BAT_IN',x+8.89,Y)
x=xs['Q121']; add+=sym('Transistor_BJT:MMBT3906','Q121','MMBT5401',x,Y,'Package_TO_SOT_SMD:SOT-23','C8326','MMBT5401(RANGE:200-300)','CJ','P7 hold-off sense PNP MMBT5401 (150 V, MMBT3906 B-E-C pinout): on when BAT_IN - VBAT_P > 2.5-3.8 V',['1','2','3'])
add+=wire(x-5.08,Y,x-7.62,Y)+label('HO_B',x-7.62,Y,180,'right bottom')+net('HO_C',x+2.54,Y-5.08,True)+net('HO_E',x+2.54,Y+5.08,False)
for ref,val,lc,mpn,a,b,desc in (('R1121','22k','C31850','0603WAF2202T5E','HO_E','HO_B','P7 hold-off E-B 22k (threshold divider)'),
                                 ('R1122','68k','C23231','0603WAF6802T5E','HO_B','VBAT_P','P7 hold-off base 68k to VBAT_P: Vth = Vf + Veb x 90/22 = 2.5-3.8 V'),
                                 ('R1123','22k','C31850','0603WAF2202T5E','HO_C','HO_F','P7 hold-off collector 22k into the filter node'),
                                 ('R1124','100k','C25803','0603WAF1003T5E','HO_F','GND','P7 hold-off filter bleed 100k'),
                                 ('R1125','100k','C25803','0603WAF1003T5E','VBAT_P','U5_EN','P7: U5 EN/UVLO pull-up 100k (was strapped to VIN)'),
                                 ('R1126','47k','C25819','0603WAF4702T5E','U5_EN','GND','P7: U5 EN/UVLO 47k: on above VBAT_P 4.25 V, off below 2.4-3.3 V; EN <= 18.4 V at 57.6 V')):
    x=xs[ref]; add+=sym('Device:R',ref,val,x,Y,R0603,lc,mpn,UR,desc,['1','2'])+net(a,x,Y-3.81,True)+net(b,x,Y+3.81,False)
x=xs['C1121']; add+=sym('Device:C','C1121','100n',x,Y,'Capacitor_SMD:C_0603_1608Metric','C14663','CC0603KRX7R9BB104','YAGEO','P7 hold-off filter 100 nF: 46 us (32 V) to 270 us (8 V, cold) before U2/U5 are pulled off',['1','2'])
add+=net('HO_F',x,Y-3.81,True)+net('GND',x,Y+3.81,False)
x=xs['Q122']; add+=sym('Transistor_BJT:MMBT3904','Q122','MMBT3904',x,Y,'Package_TO_SOT_SMD:SOT-23','C20526','MMBT3904','JSCJ','P7 hold-off pull-down NPN',['1','2','3'])
add+=wire(x-5.08,Y,x-7.62,Y)+label('HO_F',x-7.62,Y,180,'right bottom')+net('HO_K',x+2.54,Y-5.08,True)+net('GND',x+2.54,Y+5.08,False)
x=xs['D402']; add+=sym('Diode:BAT54C','D402','BAT54C',x,Y,'Package_TO_SOT_SMD:SOT-23','C37704','BAT54C,215','Nexperia','P7 hold-off: pulls U2 EN/UVLO (BB_UVLO, discharges C602) and U5 EN to <= 0.45 V',['1','2','3'])
add+=wire(x-7.62,Y,x-10.16,Y)+label('BB_UVLO',x-10.16,Y,180,'right bottom')+wire(x+7.62,Y,x+10.16,Y)+label('U5_EN',x+10.16,Y)+net('HO_K',x,Y+5.08,False)
add+=(f'(rectangle (start 406.4 270.51) (end 650.24 317.5) (stroke (width 0) (type dash)) (fill (type none)) (uuid "{U()}"))\n'
      f'(text "P7 Q2 hold-off (port of m7-modular Pass 6 B1): BAT_IN - VBAT_P > 2.5-3.8 V for >= 46-270 us holds U2 (BB_UVLO) and U5 (U5_EN) off until Q2 has nearly finished its ramp.\\nWorst Q2 SOA ratio 0.91 at 12-32 V (all corners). Math: docs/split_evidence/p7/p7_calc.txt" (at 407.67 274.32 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{U()}"))\n')
# lib symbols the power sheet did not carry
ls=''
for sheet,nm in (('inputs.kicad_sch','Transistor_BJT:MMBT3906'),('estop.kicad_sch','Transistor_BJT:MMBT3904'),('frontpanel.kicad_sch','Diode:1N4148W'),('estop.kicad_sch','Diode:BAT54C')):
    if f'(symbol "{nm}"' not in s: ls+=libsym(sheet,nm)+'\n'
i=s.index('(lib_symbols')+len('(lib_symbols'); s=s[:i]+'\n'+ls+s[i:]
k=s.rindex('(sheet_instances') if '(sheet_instances' in s else s.rindex(')')
s=s[:k]+add+s[k:]
open(fn,'w').write(s); print('power.kicad_sch: P7 front end added (R1001/C601, C602 1 uF, U5 EN divider, 11-part hold-off)')
