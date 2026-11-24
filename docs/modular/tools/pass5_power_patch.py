"""Pass 5: add the LM74800 (U1) HGATE dV/dt network and the LM5176 (U2) start delay to the kept power sheet (idempotent).
C602 10 uF / 25 V on U2 EN/UVLO (R4 100k / R5 33k, Thevenin 24.8k): U2 starts only after VBAT_P has finished its slow Q2 ramp, so Q2
ramps the bulk caps without the converter load (Q2 SOA, kick_calc.txt hot-plug table).
CdVdT 22 nF / 100 V X7R from HGATE to GND through R1 1k (TI SNOSDB4 Fig 9-3: R1 in series improves turn-off).
I_INRUSH = I_HGATE x C_OUT / CdVdT = 55 uA x ~230 uF / 22 nF ~ 0.6 A (0.78 A at 75 uA). Math: docs/modular/pass5_calc.txt."""
import os,re,uuid
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','..'))
fn=os.path.join(ROOT,'power.kicad_sch'); s=open(fn).read()
if '(property "Reference" "R1001"' in s: print('power.kicad_sch: Pass 5 HGATE network already present'); raise SystemExit
PATH='/2f7a4bb8-89ed-4e3c-b40c-67c49fede2c6/d8c05520-8978-4d93-9881-80f603685ecb'
U=lambda: str(uuid.uuid4())
import glob
pw=9001   # fixed, above every generated #PWR number
X=190.5
def sym(lib,ref,val,x,y,fp,lcsc,mpn,man,desc,pins):
    return (f'(symbol (lib_id "{lib}") (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}")\n'
      f'(property "Reference" "{ref}" (at {x+2.54:.2f} {y-1.27:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))\n'
      f'(property "Value" "{val}" (at {x+2.54:.2f} {y+1.27:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))\n'
      f'(property "Footprint" "{fp}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
      f'(property "Datasheet" "~" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
      f'(property "Description" "{desc}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
      +(f'(property "LCSC" "{lcsc}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n(property "MPN" "{mpn}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n(property "Manufacturer" "{man}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n' if lcsc else '')
      +''.join(f'(pin "{p}" (uuid "{U()}"))\n' for p in pins)
      +f'(instances (project "genctl" (path "{PATH}" (reference "{ref}") (unit 1))))\n)\n')
def wire(x1,y1,x2,y2): return f'(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid "{U()}"))\n'
def label(n,x,y,a): return f'(label "{n}" (at {x} {y} {a}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{U()}"))\n'
add=(sym('Device:R','R1001','1k',X,135.89,'Resistor_SMD:R_0603_1608Metric','C21190','0603WAF1001T5E','UNI-ROYAL',
         'Pass 5: R1 1k in series with CdVdT (TI SNOSDB4 Fig 9-3), resets CdVdT in ~22 us after an OV/fault turn-off',['1','2'])
    +sym('Device:C','C601','22n 100V',X,147.32,'Capacitor_SMD:C_0603_1608Metric','C313105','CC0603KRX7R0BB223','YAGEO',
         'Pass 5: CdVdT 22 nF / 100 V X7R HGATE -> GND: Q2 inrush 0.6 A typ (0.78 A max) into ~230 uF, hot-plug dV/dt',['1','2'])
    +f'(symbol (lib_id "power:GND") (at {X} 151.13 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}")\n'
     f'(property "Reference" "#PWR{pw:04d}" (at {X} 157.48 0) (effects (font (size 1.27 1.27)) hide))\n(property "Value" "GND" (at {X} 154.94 0) (effects (font (size 1.27 1.27))))\n'
     f'(property "Footprint" "" (at {X} 151.13 0) (effects (font (size 1.27 1.27)) hide))\n(property "Datasheet" "" (at {X} 151.13 0) (effects (font (size 1.27 1.27)) hide))\n'
     f'(pin "1" (uuid "{U()}"))\n(instances (project "genctl" (path "{PATH}" (reference "#PWR{pw:04d}") (unit 1))))\n)\n'
    +wire(X,129.54,X,132.08)+wire(X,129.54,195.58,129.54)+label("LM748_HGATE",195.58,129.54,0)+wire(X,139.7,X,143.51)+label('LM748_DVDT',X,141.605,0))
XU=435.61
add+=(sym('Device:C','C602','10u 25V',XU,80.01,'Capacitor_SMD:C_0805_2012Metric','C15850','CL21A106KAYNNNE','Samsung',
         'Pass 5: LM5176 EN/UVLO delay 10 uF X5R (tau 124-273 ms with R4/R5): U2 starts 31 ms after VBAT_P at 32 V, after the Q2 ramp; 0.2 s at 9 V',['1','2'])
    +f'(symbol (lib_id "power:GND") (at {XU} 83.82 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}")\n'
     f'(property "Reference" "#PWR{pw+1:04d}" (at {XU} 90.17 0) (effects (font (size 1.27 1.27)) hide))\n(property "Value" "GND" (at {XU} 87.63 0) (effects (font (size 1.27 1.27))))\n'
     f'(property "Footprint" "" (at {XU} 83.82 0) (effects (font (size 1.27 1.27)) hide))\n(property "Datasheet" "" (at {XU} 83.82 0) (effects (font (size 1.27 1.27)) hide))\n'
     f'(pin "1" (uuid "{U()}"))\n(instances (project "genctl" (path "{PATH}" (reference "#PWR{pw+1:04d}") (unit 1))))\n)\n'
    +wire(XU,76.2,XU,73.66)+label('BB_UVLO',XU,73.66,90)
    +f'(label "BB_UVLO" (at 462.28 105.41 180) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify right bottom)) (uuid "{U()}"))\n')
# grow the input-protection block frame (20.32,46.99)-(289.56,125.73) down to 158.75 to hold the network
s=s.replace('(rectangle (start 20.32 46.99) (end 289.56 125.73)','(rectangle (start 20.32 46.99) (end 289.56 158.75)',1)
k=s.rindex('(sheet_instances') if '(sheet_instances' in s else s.rindex(')')
s=s[:k]+add+s[k:]
open(fn,'w').write(s); print('power.kicad_sch: added R1001 1k + C601 22 nF (HGATE dV/dt), C602 10 uF (U2 EN/UVLO delay)')
