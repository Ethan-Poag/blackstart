#!/usr/bin/env python3
"""Option B ride-through U5 input hold-up (power sheet, idempotent):
VBAT_P -> D417 (SS110 C2482) -> U5_VIN (feeds U5 pin 4 VIN, C38, C39, and global label U5_VIN -> R1125 on estop).
U5_VIN -> R1130 (2.2k C4190) || D418 (SS110 C2482, A=U5_HU, K=U5_VIN) -> U5_HU -> C1122, C1123 (2x EEETG1J101UP 100u 63V C178628).
Together with Q123/Q124/R1127-R1129 on estop (mainboard.py), gives 10 ms ride-through at 24 V and 20 ms at 32 V (O and G breaks)."""
import os, uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
fn = os.path.join(ROOT, 'power.kicad_sch')
s = open(fn).read()

if '(property "Reference" "D417"' in s:
    print('power.kicad_sch: Option B hold-up already present')
    raise SystemExit

U = lambda: str(uuid.uuid4())
PATH = '/2f7a4bb8-89ed-4e3c-b40c-67c49fede2c6/d8c05520-8978-4d93-9881-80f603685ecb'

# 1. Change U5 VIN global_label VBAT_P -> U5_VIN (keeps #FLG0003 PWR_FLAG on U5_VIN, C38/C39/U5.4 on U5_VIN)
old_lbl = '(global_label "VBAT_P" (shape passive) (at 476.25 219.71 180) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify right)) (uuid "1a4ac051-f3bc-4d5b-8754-d392f12f41ec")'
new_lbl = '(global_label "U5_VIN" (shape passive) (at 476.25 219.71 180) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify right)) (uuid "1a4ac051-f3bc-4d5b-8754-d392f12f41ec")'
assert s.count(old_lbl) == 1, 'U5 VBAT_P global_label not found'
s = s.replace(old_lbl, new_lbl, 1)

# 2. Update power sheet text / U5 Note
s = s.replace(
    'SAFE DOMAIN: LMR36506 buck VBAT_P -> +3V3_BK (EN = R1125/R1126 divider from VBAT_P: on above 3.6-4.25 V; held off with U2 by the Q2 hold-off, Pass 6)',
    'SAFE DOMAIN: LMR36506 buck U5_VIN (VBAT_P via D417 SS110 + R1130 2.2k/D418 SS110 + C1122/C1123 2x 100u 63V hold-up) -> +3V3_BK (EN = R1125/R1126 from U5_VIN; Q123/Q124 lockout while +3V3_BK is up, Option B)',
    1,
)
s = s.replace(
    '3.3V backup from battery (EN divider R1125/R1126 + Q2 hold-off, Pass 6), 65V abs max',
    '3.3V backup from U5_VIN (D417 + 2x 100u hold-up, EN divider R1125/R1126 + Q123/Q124 lockout, Option B), 65V abs max',
    1,
)

def sym(lib, ref, val, x, y, ang, fp, lcsc, mpn, man, desc, pins, ref_off=(0, -5.08), val_off=(0, 5.08)):
    return (
        f'(symbol (lib_id "{lib}") (at {x} {y} {ang}) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}")\n'
        f'(property "Reference" "{ref}" (at {x+ref_off[0]:.2f} {y+ref_off[1]:.2f} 0) (effects (font (size 1.27 1.27))))\n'
        f'(property "Value" "{val}" (at {x+val_off[0]:.2f} {y+val_off[1]:.2f} 0) (effects (font (size 1.27 1.27))))\n'
        f'(property "Footprint" "{fp}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'(property "Datasheet" "~" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'(property "Description" "{desc}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'(property "LCSC" "{lcsc}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'(property "MPN" "{mpn}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'(property "Manufacturer" "{man}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        + ''.join(f'(pin "{p}" (uuid "{U()}"))\n' for p in pins)
        + f'(instances (project "genctl" (path "{PATH}" (reference "{ref}") (unit 1))))\n)\n'
    )

def wire(x1, y1, x2, y2):
    return f'(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid "{U()}"))\n'

def junc(x, y):
    return f'(junction (at {x} {y}) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))\n'

def gl(n, x, y, a, j):
    return (
        f'(global_label "{n}" (shape passive) (at {x} {y} {a}) (fields_autoplaced yes) '
        f'(effects (font (size 1.27 1.27)) (justify {j})) (uuid "{U()}") '
        f'(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide)))\n'
    )

def gnd(pw, x, y):
    return (
        f'(symbol (lib_id "power:GND") (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}")\n'
        f'(property "Reference" "#PWR{pw:04d}" (at {x} {y+6.35:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'(property "Value" "GND" (at {x} {y+3.81:.2f} 0) (effects (font (size 1.27 1.27))))\n'
        f'(property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'(property "Datasheet" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'(pin "1" (uuid "{U()}"))\n'
        f'(instances (project "genctl" (path "{PATH}" (reference "#PWR{pw:04d}") (unit 1))))\n)\n'
    )

# Hold-up block below U5: x = 408.94..502.92, y = 256.54..290.83
add = ''
def flg(pw, x, y):
    return (
        f'(symbol (lib_id "power:PWR_FLAG") (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board yes) (dnp no) (uuid "{U()}")\n'
        f'(property "Reference" "#FLG{pw:04d}" (at {x} {y-1.905:.3f} 0) (effects (font (size 1.27 1.27))))\n'
        f'(property "Value" "PWR_FLAG" (at {x} {y-3.81:.2f} 0) (effects (font (size 1.27 1.27))))\n'
        f'(property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'(property "Datasheet" "~" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))\n'
        f'(pin "1" (uuid "{U()}"))\n'
        f'(instances (project "genctl" (path "{PATH}" (reference "#FLG{pw:04d}") (unit 1))))\n)\n'
    )
add += gl('VBAT_P', 419.10, 266.70, 180, 'right')
add += wire(419.10, 266.70, 420.37, 266.70) + wire(420.37, 266.70, 422.91, 266.70) + junc(420.37, 266.70)
add += wire(420.37, 266.70, 420.37, 262.89) + flg(9001, 420.37, 262.89)
# D417 SS110 at (426.72, 266.70) rot 180 -> pin 2 (A) at 422.91, pin 1 (K) at 430.53
add += sym('Device:D_Schottky', 'D417', 'SS110', 426.72, 266.70, 180, 'Diode_SMD:D_SMA', 'C2482', 'SS110', 'MDD(Microdiode Semiconductor)',
           'Option B ride-through: isolates U5_VIN from VBAT_P dips/ground shorts', ['1', '2'], ref_off=(0, -3.18), val_off=(0, 3.18))
add += wire(430.53, 266.70, 435.61, 266.70) + wire(435.61, 266.70, 443.23, 266.70)
add += junc(435.61, 266.70)
add += wire(435.61, 266.70, 435.61, 261.62)
add += gl('U5_VIN', 435.61, 261.62, 90, 'left')
# D418 SS110 at (447.04, 266.70) rot 0 -> pin 1 (K) at 443.23 (U5_VIN), pin 2 (A) at 450.85 (U5_HU)
add += sym('Device:D_Schottky', 'D418', 'SS110', 447.04, 266.70, 0, 'Diode_SMD:D_SMA', 'C2482', 'SS110', 'MDD(Microdiode Semiconductor)',
           'Option B ride-through: feeds U5_VIN from hold-up caps C1122/C1123 on loss of VBAT_P', ['1', '2'], ref_off=(0, -3.18), val_off=(0, 3.18))
# R1130 2.2k at (447.04, 276.86) rot 90 -> pins at 443.23 and 450.85
add += sym('Device:R', 'R1130', '2.2k', 447.04, 276.86, 90, 'Resistor_SMD:R_0603_1608Metric', 'C4190', '0603WAF2201T5E', 'UNI-ROYAL',
           'Option B ride-through: limits C1122/C1123 charging current off Q2 cold-start ramp', ['1', '2'], ref_off=(0, -2.54), val_off=(0, 2.54))
add += wire(435.61, 266.70, 435.61, 276.86) + wire(435.61, 276.86, 443.23, 276.86)
add += wire(450.85, 276.86, 458.47, 276.86) + wire(458.47, 276.86, 458.47, 266.70)
add += wire(450.85, 266.70, 458.47, 266.70) + wire(458.47, 266.70, 472.44, 266.70) + wire(472.44, 266.70, 487.68, 266.70)
add += junc(458.47, 266.70)
add += f'(label "U5_HU" (at 464.82 266.70 0) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{U()}"))\n'
# C1122, C1123 100u 63V at (472.44, 274.32) and (487.68, 274.32)
add += junc(472.44, 266.70) + wire(472.44, 266.70, 472.44, 270.51)
add += sym('Device:C_Polarized', 'C1122', '100u 63V', 472.44, 274.32, 0, 'Capacitor_SMD:CP_Elec_10x10.5', 'C178628', 'EEETG1J101UP', 'Panasonic',
           'Option B ride-through: U5 input hold-up 100 uF 63 V (1 of 2; 10 ms @ 24 V, 20 ms @ 32 V)', ['1', '2'], ref_off=(2.54, -1.27), val_off=(2.54, 1.27))
add += wire(472.44, 278.13, 472.44, 281.94) + gnd(9003, 472.44, 281.94)
add += wire(487.68, 266.70, 487.68, 270.51)
add += sym('Device:C_Polarized', 'C1123', '100u 63V', 487.68, 274.32, 0, 'Capacitor_SMD:CP_Elec_10x10.5', 'C178628', 'EEETG1J101UP', 'Panasonic',
           'Option B ride-through: U5 input hold-up 100 uF 63 V (2 of 2; 10 ms @ 24 V, 20 ms @ 32 V)', ['1', '2'], ref_off=(2.54, -1.27), val_off=(2.54, 1.27))
add += wire(487.68, 278.13, 487.68, 281.94) + gnd(9004, 487.68, 281.94)
add += f'(rectangle (start 408.94 256.54) (end 502.92 290.83) (stroke (width 0) (type default)) (fill (type none)) (uuid "{U()}"))\n'
add += f'(text "Option B U5 ride-through hold-up (10 ms @ 24 V, 20 ms @ 32 V)" (exclude_from_sim no) (at 410.21 258.0 0) (effects (font (size 1.27 1.27)) (justify left top)) (uuid "{U()}"))\n'

k = s.rindex('(sheet_instances') if '(sheet_instances' in s else s.rindex(')')
s = s[:k] + add + s[k:]
open(fn, 'w').write(s)
print('power.kicad_sch: added Option B U5_VIN isolation & hold-up (D417, D418, R1130, C1122, C1123)')
