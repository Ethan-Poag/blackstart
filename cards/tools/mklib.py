"""Write cards/lib/cards.kicad_sym (DIN 41612 C96 3-unit connector, AT24CS32 SOT-23-5) and cards/lib/cards.pretty footprints.
Footprint geometry from the WingTAT 9001 drawings (LCSC C5173361/C5173363): 3 rows x 32, 2.54 mm pitch, rows 2.54 apart,
mounting holes 88.9 mm (male RA) / 90.0 mm (female vertical) apart, dia 2.8. VERIFY against the parts before layout."""
import os
D=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'lib')
os.makedirs(os.path.join(D,'cards.pretty'),exist_ok=True)
def pin(num,name,x,y,ang,typ='passive',ln=2.54):
    return f'(pin {typ} line (at {x} {y} {ang}) (length {ln}) (name "{name}" (effects (font (size 1.0 1.0)))) (number "{num}" (effects (font (size 1.0 1.0)))))'
def prop(k,v,x,y,hide=False):
    return f'(property "{k}" "{v}" (at {x} {y} 0) (effects (font (size 1.27 1.27)){" hide" if hide else ""}))'
syms=[]
# DIN 41612 C96: unit 1 = row a, 2 = row b, 3 = row c
units=[]
for u,row in enumerate('abc',1):
    pins=[pin(f'{row}{i}',f'{row}{i}',-5.08,round(39.37-(i-1)*2.54,2),0) for i in range(1,33)]
    units.append(f'(symbol "DIN41612_C96_{u}_1" (rectangle (start -2.54 41.91) (end 2.54 -41.91) (stroke (width 0.254) (type default)) (fill (type background))) {" ".join(pins)})')
syms.append('(symbol "DIN41612_C96" (pin_names (offset 0.5)) (exclude_from_sim no) (in_bom yes) (on_board yes) '
  +prop('Reference','J',0,44.45)+prop('Value','DIN41612_C96',0,-44.45)+prop('Footprint','',0,0,True)+prop('Datasheet','',0,0,True)
  +prop('Description','DIN 41612 type C, 3 rows x 32 (a/b/c), 2.54 mm; units 1/2/3 = rows a/b/c',0,0,True)+' '.join(units)+')')
p=[pin(1,'SCL',-7.62,2.54,0,'input'),pin(2,'GND',0,-7.62,90,'power_in'),pin(3,'SDA',-7.62,-2.54,0,'bidirectional'),
   pin(4,'VCC',0,7.62,270,'power_in'),pin(5,'WP',7.62,0,180,'input')]
syms.append('(symbol "AT24CS32-STUM" (pin_names (offset 0.5)) (exclude_from_sim no) (in_bom yes) (on_board yes) '
  +prop('Reference','U',3.81,6.35)+prop('Value','AT24CS32-STUM-T',3.81,-6.35)+prop('Footprint','Package_TO_SOT_SMD:SOT-23-5',0,0,True)+prop('Datasheet','',0,0,True)
  +prop('Description','32 Kbit I2C EEPROM + 128-bit factory serial (0x50 EEPROM / 0x58 serial, SOT-23 A2..A0 = 0)',0,0,True)
  +'(symbol "AT24CS32-STUM_1_1" (rectangle (start -5.08 5.08) (end 5.08 -5.08) (stroke (width 0.254) (type default)) (fill (type background))) '+' '.join(p)+'))')
open(os.path.join(D,'cards.kicad_sym'),'w').write('(kicad_symbol_lib (version 20241209) (generator "mklib") (generator_version "9.0")\n'+'\n'.join(syms)+'\n)\n')
def fp(name,desc,holes,dx_row):
    pads=[]
    for r,row in enumerate('abc'):
        for i in range(1,33):
            x=round((i-1)*2.54-78.74/2,3); y=round(r*dx_row,3)
            pads.append(f'(pad "{row}{i}" thru_hole {"rect" if (row,i)==("a",1) else "circle"} (at {x} {y}) (size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask"))')
    for hx in (-holes/2,holes/2):
        pads.append(f'(pad "" np_thru_hole circle (at {hx} {dx_row}) (size 2.8 2.8) (drill 2.8) (layers "*.Cu" "*.Mask"))')
    w=holes/2+3
    s=(f'(footprint "{name}" (version 20241229) (generator "mklib") (layer "F.Cu") (descr "{desc}") '
       f'(property "Reference" "REF**" (at 0 -4 0) (layer "F.SilkS") (effects (font (size 1 1)))) (property "Value" "{name}" (at 0 9 0) (layer "F.Fab") (effects (font (size 1 1)))) '
       f'(fp_rect (start {-w} -3) (end {w} {2*dx_row+3}) (stroke (width 0.05) (type default)) (fill no) (layer "F.CrtYd")) '+' '.join(pads)+')')
    open(os.path.join(D,'cards.pretty',name+'.kicad_mod'),'w').write(s+'\n')
fp('DIN41612_C96_Male_RA_WingTAT_9001-11961','Card side, LCSC C5173361. VERIFY pad/row offsets vs drawing 9001D11001 before layout',88.9,2.54)
fp('DIN41612_C96_Female_Vertical_WingTAT_9001-12961','Mainboard side, LCSC C5173363. Slot keying: coding NPTH added per slot in the slot footprint (Phase 3). VERIFY',90.0,2.54)
print('ok')
