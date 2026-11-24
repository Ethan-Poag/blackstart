"""Pass 6 (Ethan's B1 pick, Nov 24 2026): U5 EN/UVLO is split from VIN and both converter enables become global nets, so the
Q2 hold-off on the estop sheet (cards/tools/mainboard.py) can hold U2 (BB_UVLO) and U5 (U5_EN) off while Q2 is still ramping
(BAT_IN - VBAT_P > ~3 V). Idempotent. Math: docs/modular/pass6_fix_calc.txt."""
import os,uuid
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','..'))
fn=os.path.join(ROOT,'power.kicad_sch'); s=open(fn).read()
# 0. C602 10 uF -> 1 uF (same 0805 pad): the hold-off must pull U2 EN/UVLO below 1.17 V within ~0.2 ms; 10 uF took 1.2-1.7 ms and Q2 still
#    exceeded its SOA (ratio up to 1.67) when U2 kept running at full load through a short dip. 1 uF: tau 25 ms, the cold-start U2 delay is
#    now the hold-off itself (U2 held until BAT_IN - VBAT_P < Vth).
c6_old=('(property "Value" "10u 25V" (at 438.15 81.28 0)','"Pass 5: LM5176 EN/UVLO delay 10 uF X5R (tau 124-273 ms with R4/R5): U2 starts 31 ms after VBAT_P at 32 V, after the Q2 ramp; 0.2 s at 9 V"',
        '(property "LCSC" "C15850" (at 435.61 80.01 0)','(property "MPN" "CL21A106KAYNNNE" (at 435.61 80.01 0)')
c6_new=('(property "Value" "1u 50V" (at 438.15 81.28 0)','"Pass 6 B1: LM5176 EN/UVLO 1 uF X7R (tau ~25 ms with R4/R5; was 10 uF): the Q2 hold-off (D402) pulls it below 1.17 V in <= 0.25 ms; U2 restarts 1-3 ms after the hold-off releases"',
        '(property "LCSC" "C28323" (at 435.61 80.01 0)','(property "MPN" "CL21B105KBFNNNE" (at 435.61 80.01 0)')
if c6_old[0] in s:
    for a,b in zip(c6_old,c6_new): assert s.count(a)==1,a[:50]; s=s.replace(a,b)
    print('power.kicad_sch: C602 10 uF -> 1 uF (Pass 6 B1)')
if '(global_label "U5_EN"' in s: open(fn,'w').write(s); print('power.kicad_sch: Pass 6 enables already global'); raise SystemExit
U=lambda: str(uuid.uuid4())
# 1. U5 pin 3 (EN/UVLO) was strapped to pin 4 (VIN = VBAT_P) by a wire at x 477.52: remove the strap and its junction
for frag in ('(wire (pts (xy 477.52 219.71) (xy 477.52 222.25)) (stroke (width 0) (type default)) (uuid "0ef8a79f-d707-4e75-a8a5-b2087c0da3b5"))\n',
             '(junction (at 477.52 219.71) (diameter 0) (color 0 0 0 0) (uuid "8defdf2b-cc69-440d-a401-e2f98a7937f5"))\n'):
    assert s.count(frag)==1,frag[:60]; s=s.replace(frag,'')
def gl(n,x,y,a,j):
    return (f'(global_label "{n}" (shape input) (at {x} {y} {a}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {j})) (uuid "{U()}") '
            f'(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide)))\n')
add=gl('U5_EN',477.52,222.25,180,'right')
# 2. BB_UVLO (U2 EN/UVLO + C602) becomes a global net: the two Pass 5 local labels turn into global labels at the same points
for old,(x,y,a,j) in (('(label "BB_UVLO" (at 435.61 73.66 90) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "85e4a932-67c8-493d-be7b-74aa87ebf177"))\n',(435.61,73.66,90,'left')),
                      ('(label "BB_UVLO" (at 462.28 105.41 180) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify right bottom)) (uuid "4b454389-651e-49de-b95e-d615e88cd5e7"))\n',(462.28,105.41,180,'right'))):
    assert s.count(old)==1,old[:50]; s=s.replace(old,gl('BB_UVLO',x,y,a,j))
k=s.rindex('(sheet_instances') if '(sheet_instances' in s else s.rindex(')')
s=s[:k]+add+s[k:]
open(fn,'w').write(s); print('power.kicad_sch: U5 EN split from VIN (global U5_EN), BB_UVLO global (Pass 6 hold-off)')
