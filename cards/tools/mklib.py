"""Write cards/lib/cards.kicad_sym (DIN 41612 C96 3-unit connector, AT24CS32 SOT-23-5) and cards/lib/cards.pretty footprints.
Footprint geometry from the WingTAT 9001 drawings (LCSC C5173361/C5173363): 3 rows x 32, 2.54 mm pitch, rows 2.54 apart,
mounting holes 88.9 mm (male RA) / 90.0 mm (female vertical) apart, dia 2.8; checked against the WingTAT drawings (see fp())."""
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
L=[(11,'~{CS}','input'),(12,'SCK','input'),(13,'SI','input'),(14,'SO','output'),(18,'~{RESET}','input'),(20,'INTA','open_collector'),(19,'INTB','open_collector'),(15,'A0','input'),(16,'A1','input'),(17,'A2','input')]
p=[pin(n,nm,-12.7,round(17.78-i*2.54,2),0,t) for i,(n,nm,t) in enumerate(L)]
R=[(21+i,f'GPA{i}') for i in range(8)]+[(1+i,f'GPB{i}') for i in range(8)]
p+=[pin(n,nm,12.7,round(19.05-i*2.54-(1.27 if i>=8 else 0),2),180,'bidirectional') for i,(n,nm) in enumerate(R)]
p+=[pin(9,'VDD',0,25.4,270,'power_in'),pin(10,'VSS',0,-25.4,90,'power_in')]
syms.append('(symbol "MCP23S17-SS" (pin_names (offset 0.5)) (exclude_from_sim no) (in_bom yes) (on_board yes) '
  +prop('Reference','U',0,27.94)+prop('Value','MCP23S17T-E/SS',0,-27.94)+prop('Footprint','Package_SO:SSOP-28_5.3x10.2mm_P0.65mm',0,0,True)+prop('Datasheet','',0,0,True)
  +prop('Description','16-bit SPI I/O expander, SSOP-28 (pinout per Microchip DS / LCSC C128577)',0,0,True)
  +'(symbol "MCP23S17-SS_1_1" (rectangle (start -10.16 22.86) (end 10.16 -22.86) (stroke (width 0.254) (type default)) (fill (type background))) '+' '.join(p)+'))')
open(os.path.join(D,'cards.kicad_sym'),'w').write('(kicad_symbol_lib (version 20241209) (generator "mklib") (generator_version "9.0")\n'+'\n'.join(syms)+'\n)\n')
def fp(name,desc,holes,hole_y,pin1_right,edge_y=None):
    """Pads per the WingTAT 'P.C. Board Layout' (component-side view): rows c (top, y=0), b (2.54), a (5.08); 2.54 pitch,
    dia 1.0 drills; mounting holes dia 2.8 at +/-holes/2, hole_y. pin1_right: contact 1 at the right end (male RA drawing)."""
    pads=[]
    for row,y in (('c',0.0),('b',2.54),('a',5.08)):
        for i in range(1,33):
            x=round((39.37-(i-1)*2.54) if pin1_right else ((i-1)*2.54-39.37),3)
            pads.append(f'(pad "{row}{i}" thru_hole {"rect" if (row,i)==("a",1) else "circle"} (at {x} {y}) (size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask"))')
    for hx in (-holes/2,holes/2):
        pads.append(f'(pad "" np_thru_hole circle (at {hx} {hole_y}) (size 2.8 2.8) (drill 2.8) (layers "*.Cu" "*.Mask"))')
    w=holes/2+3; yb=max(hole_y+3,8.08)
    edge=f'(fp_line (start {-w} {edge_y}) (end {w} {edge_y}) (stroke (width 0.1) (type dash)) (layer "F.Fab")) (fp_text user "card edge" (at 0 {edge_y+1}) (layer "F.Fab") (effects (font (size 1 1)))) ' if edge_y else ''
    s=(f'(footprint "{name}" (version 20241229) (generator "mklib") (layer "F.Cu") (descr "{desc}") '
       f'(property "Reference" "REF**" (at 0 -4 0) (layer "F.SilkS") (effects (font (size 1 1)))) (property "Value" "{name}" (at 0 {yb+1} 0) (layer "F.Fab") (effects (font (size 1 1)))) '
       f'(fp_rect (start {-w} -3) (end {w} {yb}) (stroke (width 0.05) (type default)) (fill no) (layer "F.CrtYd")) '+edge+' '.join(pads)+')')
    open(os.path.join(D,'cards.pretty',name+'.kicad_mod'),'w').write(s+'\n')
# Checked 2026-11-23 against WingTAT drawings 9001D11001 R7 (C5173361) and 9001D12003 R7 (C5173363), LCSC PDFs in modular_work/fetch:
#  both: 2.54 x 31 = 78.74 contact span, rows 2.54 apart (5.08 a-c), contact holes dia 1.0 +/-0.05, mounting holes dia 2.8
#  male RA 9001-11961: holes 88.9 apart, 2.54 beyond the outer row on the card-edge side, card edge 5.30 from that row, contact 1 at the right end
#  female vertical 9001-12961: holes 90.0 apart, 2.24 from row a towards row b, contact 1 at the left end, rows c/b/a top to bottom
fp('DIN41612_C96_Male_RA_WingTAT_9001-11961','Card side, LCSC C5173361, per drawing 9001D11001 R7. Row letters on the male drawing are not printed: edge row taken as a - VERIFY on a sample',88.9,5.08+2.54,True,5.08+5.30)
fp('DIN41612_C96_Female_Vertical_WingTAT_9001-12961','Mainboard side, LCSC C5173363, per drawing 9001D12003 R7 (rows c/b/a, holes 90.0 at 2.24 from row a). Slot keying NPTH per slot in Phase 3',90.0,5.08-2.24,False)
print('ok')
