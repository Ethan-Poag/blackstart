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
L=[(11,'~{CS}','input'),(12,'SCK','input'),(13,'SI','input'),(14,'SO','output'),(18,'~{RESET}','input'),(20,'INTA','output'),(19,'INTB','output'),(15,'A0','input'),(16,'A1','input'),(17,'A2','input')]
p=[pin(n,nm,-12.7,round(17.78-i*2.54,2),0,t) for i,(n,nm,t) in enumerate(L)]
R=[(21+i,f'GPA{i}') for i in range(8)]+[(1+i,f'GPB{i}') for i in range(8)]
p+=[pin(n,nm,12.7,round(19.05-i*2.54-(1.27 if i>=8 else 0),2),180,'bidirectional') for i,(n,nm) in enumerate(R)]
p+=[pin(9,'VDD',0,25.4,270,'power_in'),pin(10,'VSS',0,-25.4,90,'power_in')]
syms.append('(symbol "MCP23S17-SS" (pin_names (offset 0.5)) (exclude_from_sim no) (in_bom yes) (on_board yes) '
  +prop('Reference','U',0,27.94)+prop('Value','MCP23S17T-E/SS',0,-27.94)+prop('Footprint','Package_SO:SSOP-28_5.3x10.2mm_P0.65mm',0,0,True)+prop('Datasheet','',0,0,True)
  +prop('Description','16-bit SPI I/O expander, SSOP-28 (pinout per Microchip DS / LCSC C128577)',0,0,True)
  +'(symbol "MCP23S17-SS_1_1" (rectangle (start -10.16 22.86) (end 10.16 -22.86) (stroke (width 0.254) (type default)) (fill (type background))) '+' '.join(p)+'))')

def box(name,value,fpn,desc,left,right,top=(),bottom=(),w=7.62):
    """generic box symbol: left/right = [(num,name,type)], top/bottom = power pins"""
    n=max(len(left),len(right)); h=round((n+1)*2.54/2/1.27)*1.27; h=max(h,5.08)
    p=[pin(num,nm,-(w+2.54),round(h-2.54-i*2.54,2),0,t) for i,(num,nm,t) in enumerate(left)]
    p+=[pin(num,nm,w+2.54,round(h-2.54-i*2.54,2),180,t) for i,(num,nm,t) in enumerate(right)]
    p+=[pin(num,nm,round((i-(len(top)-1)/2)*2.54,2),h+2.54,270,t) for i,(num,nm,t) in enumerate(top)]
    p+=[pin(num,nm,round((i-(len(bottom)-1)/2)*2.54,2),-(h+2.54),90,t) for i,(num,nm,t) in enumerate(bottom)]
    syms.append(f'(symbol "{name}" (pin_names (offset 0.5)) (exclude_from_sim no) (in_bom yes) (on_board yes) '
      +prop('Reference','U',0,h+3.81)+prop('Value',value,0,-(h+3.81))+prop('Footprint',fpn,0,0,True)+prop('Datasheet','',0,0,True)
      +prop('Description',desc,0,0,True)
      +f'(symbol "{name}_1_1" (rectangle (start {-w} {h}) (end {w} {-h}) (stroke (width 0.254) (type default)) (fill (type background))) '+' '.join(p)+'))')
I,O,B,P,OD='input','output','bidirectional','power_in','open_collector'
box('TCA9548APWR','TCA9548APWR','Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm','8-channel I2C switch with reset (TI SCPS207, pinout Table 4-1 PW)',
    [(22,'SCL',B),(23,'SDA',B),(3,'~{RESET}',I),(1,'A0',I),(2,'A1',I),(21,'A2',I)],
    [(5,'SC0',B),(4,'SD0',B),(7,'SC1',B),(6,'SD1',B),(9,'SC2',B),(8,'SD2',B),(11,'SC3',B),(10,'SD3',B),(14,'SC4',B),(13,'SD4',B),(16,'SC5',B),(15,'SD5',B),(18,'SC6',B),(17,'SD6',B),(20,'SC7',B),(19,'SD7',B)],
    [(24,'VCC',P)],[(12,'GND',P)])
box('LM74700QDBVRQ1','LM74700QDBVRQ1','Package_TO_SOT_SMD:SOT-23-6','Automotive ideal-diode controller, N-FET, -65 V reverse (TI SNOSD17, DBV: 1 VCAP 2 GND 3 EN 4 CATHODE 5 GATE 6 ANODE)',
    [(6,'ANODE',P),(3,'EN',I),(1,'VCAP','passive')],[(4,'CATHODE',I),(5,'GATE',O)],(),[(2,'GND',P)])
box('SN74LVC138APWR','SN74LVC138APWR','Package_SO:TSSOP-16_4.4x5mm_P0.65mm','3-to-8 decoder, active-low outputs (TI SCAS291, PW pinout)',
    [(1,'A',I),(2,'B',I),(3,'C',I),(6,'G1',I),(4,'~{G2A}',I),(5,'~{G2B}',I)],[(15,'~{Y0}',O),(14,'~{Y1}',O),(13,'~{Y2}',O),(12,'~{Y3}',O),(11,'~{Y4}',O),(10,'~{Y5}',O),(9,'~{Y6}',O),(7,'~{Y7}',O)],
    [(16,'VCC',P)],[(8,'GND',P)])
box('74LVC1G02','74LVC1G02','Package_TO_SOT_SMD:SOT-23-5','Single 2-input NOR (DBV: 1 A 2 B 3 GND 4 Y 5 VCC, TI SCES213)',[(1,'A',I),(2,'B',I)],[(4,'Y',O)],[(5,'VCC',P)],[(3,'GND',P)],w=5.08)
box('74LVC1G00','74LVC1G00','Package_TO_SOT_SMD:SOT-23-5','Single 2-input NAND (DBV: 1 A 2 B 3 GND 4 Y 5 VCC, TI SCES212)',[(1,'A',I),(2,'B',I)],[(4,'Y',O)],[(5,'VCC',P)],[(3,'GND',P)],w=5.08)
box('74LVC125APW','74LVC125APW,118','Package_SO:TSSOP-14_4.4x5mm_P0.65mm','Quad buffer, 3-state, IOFF partial power-down (Nexperia 74LVC125A rev 11: IOFF +/-10 uA at VCC 0 V, VI/VO 5.5 V). PW: 1 1OE 2 1A 3 1Y 4 2OE 5 2A 6 2Y 7 GND 8 3Y 9 3A 10 3OE 11 4Y 12 4A 13 4OE 14 VCC',
    [(2,'1A',I),(5,'2A',I),(9,'3A',I),(12,'4A',I),(1,'~{1OE}',I),(4,'~{2OE}',I),(10,'~{3OE}',I),(13,'~{4OE}',I)],[(3,'1Y','tri_state'),(6,'2Y','tri_state'),(8,'3Y','tri_state'),(11,'4Y','tri_state')],[(14,'VCC',P)],[(7,'GND',P)])
box('74LVC1G125','SN74LVC1G125DBVR','Package_TO_SOT_SMD:SOT-23-5','Single buffer, 3-state, Ioff (TI SCES223U, DBV: 1 OE# 2 A 3 GND 4 Y 5 VCC)',[(2,'A',I),(1,'~{OE}',I)],[(4,'Y','tri_state')],[(5,'VCC',P)],[(3,'GND',P)],w=5.08)
box('74LVC1G07','SN74LVC1G07DBVR','Package_TO_SOT_SMD:SOT-23-5','Single buffer, open-drain output, Ioff (TI SCES296AG, DBV: 1 NC 2 A 3 GND 4 Y 5 VCC)',[(2,'A',I),(1,'NC','no_connect')],[(4,'Y',OD)],[(5,'VCC',P)],[(3,'GND',P)],w=5.08)
box('74LVC1G04','SN74LVC1G04DBVR','Package_TO_SOT_SMD:SOT-23-5','Single inverter, Ioff (TI SCES214AF, DBV: 1 NC 2 A 3 GND 4 Y 5 VCC)',[(2,'A',I),(1,'NC','no_connect')],[(4,'Y',O)],[(5,'VCC',P)],[(3,'GND',P)],w=5.08)
box('74LVC1G10','SN74LVC1G10DBVR','Package_TO_SOT_SMD:SOT-23-6','Single 3-input NAND, Ioff (TI SCES486F, DBV-6: 1 A 2 GND 3 B 4 Y 5 VCC 6 C)',[(1,'A',I),(3,'B',I),(6,'C',I)],[(4,'Y',O)],[(5,'VCC',P)],[(2,'GND',P)],w=5.08)
box('74LVC1G11','SN74LVC1G11DBVR','Package_TO_SOT_SMD:SOT-23-6','Single 3-input AND, Ioff (TI SCES487J, DBV-6: 1 A 2 GND 3 B 4 Y 5 VCC 6 C)',[(1,'A',I),(3,'B',I),(6,'C',I)],[(4,'Y',O)],[(5,'VCC',P)],[(2,'GND',P)],w=5.08)
box('TLV3012B','TLV3012BIDBVR','Package_TO_SOT_SMD:SOT-23-6','Comparator, push-pull, 1.242 V reference, POR (output low while V+ ramps) (TI SBOS300C, DBV-6: 1 OUT 2 V- 3 IN+ 4 IN- 5 REF 6 V+)',
    [(3,'IN+',I),(4,'IN-',I)],[(1,'OUT',O),(5,'REF',O)],[(6,'V+',P)],[(2,'V-',P)],w=5.08)
box('TPS16630PWPR','TPS16630PWPR','Package_SO:HTSSOP-20-1EP_4.4x6.5mm_P0.65mm_EP3.4x6.5mm_Mask2.96x2.96mm_ThermalVias',
    'eFuse 4.5-60 V, 6 A, 31 mOhm, adjustable UVLO/OVP cut-off, I_OL = 18/R_ILIM(k), fast-trip 2x I_OL, SCP 45 A / 1 us, MODE open = latch (TI SLVSET9G, PWP: 1-3 IN 4-5 NC 6 P_IN 7 UVLO 8 OVP 9 GND 10 dVdT 11 ILIM 12 MODE 13 SHDN# 14 IMON 15 FLT# 16 PGOOD 17 NC 18-20 OUT, EP = GND) (Pass 5)',
    [(1,'IN','passive'),(2,'IN','passive'),(3,'IN','passive'),(6,'P_IN','passive'),(7,'UVLO',I),(8,'OVP',I),(13,'~{SHDN}',I),(12,'MODE',I),(4,'NC','no_connect'),(5,'NC','no_connect')],
    [(18,'OUT','passive'),(19,'OUT','passive'),(20,'OUT','passive'),(15,'~{FLT}',OD),(16,'PGOOD',OD),(14,'IMON','passive'),(11,'ILIM','passive'),(10,'dVdT','passive'),(17,'NC','no_connect')],
    (),[(9,'GND',P),(21,'EP',P)],w=7.62)
box('TS5A3166','TS5A3166DBVR','Package_TO_SOT_SMD:SOT-23-5','SPST analog switch, NO, 0.9 ohm (TI SCDS186E, DBV: 1 NO 2 COM 3 GND 4 IN 5 V+; INO(OFF) +/-100 nA max -40..85 C at V+ 4.5-5.5 V)',
    [(1,'NO','passive'),(4,'IN',I)],[(2,'COM','passive')],[(5,'V+',P)],[(3,'GND',P)],w=5.08)
# Pass 3 N13: KiCad stock symbols renamed to the parts actually fitted (pinout identical, flattened from the stock 'extends' parent)
import sys as _s; _s.path.insert(0,os.path.join(os.path.dirname(D),'..','tools'))
from sexp import parse as _parse,dump as _dump,find as _find,Sym as _Sym
STOCK=os.environ.get('KICAD9_SYMBOL_DIR','/workspace/kicad-libs/kicad-symbols-9.0.2')
def flat(lib,name,new,props):
    L=_parse(open(os.path.join(STOCK,lib+'.kicad_sym')).read())[0]
    S={e[1]:e for e in _find(L,'symbol')}
    ch=S[name]; ext=[e for e in ch if isinstance(e,list) and e[0]=='extends']
    par=S[ext[0][1]] if ext else ch
    out=[_Sym('symbol'),new]
    for e in par[2:]:
        if isinstance(e,list) and e[0]=='property':
            e=list(e); k=e[1]
            src=[x for x in ch if isinstance(x,list) and x[0]=='property' and x[1]==k]
            if src: e=list(src[0])
            if k in props: e[2]=props[k]
            out.append(e)
        elif isinstance(e,list) and e[0]=='symbol':
            sub=list(e); sub[1]=sub[1].replace(par[1],new,1); out.append(sub)
        elif isinstance(e,list) and e[0]=='extends': continue
        else: out.append(e)
    syms.append(_dump(out))
flat('Transistor_FET','DMN6075S','AO3400A',{'Value':'AO3400A','Footprint':'Package_TO_SOT_SMD:SOT-23','Datasheet':'http://www.aosmd.com/pdfs/datasheet/AO3400A.pdf',
     'Description':'30 V N-FET, VGS(th) 0.65-1.45 V, SOT-23 (G 1, S 2, D 3)'})
flat('Transistor_FET','DMN6075S','IRLML0100',{'Value':'IRLML0100','Footprint':'Package_TO_SOT_SMD:SOT-23','Datasheet':'https://www.infineon.com/dgdl/irlml0100pbf.pdf',
     'Description':'100 V N-FET, VGS(th) 1.0-2.5 V, 235 mOhm at 4.5 V, SOT-23 (G 1, S 2, D 3)'})
flat('74xGxx','74AUP1G74','74LVC1G74',{'Value':'74LVC1G74','Footprint':'Package_SO:TSSOP-8_3x3mm_P0.65mm','Datasheet':'https://assets.nexperia.com/documents/data-sheet/74LVC1G74_Q100.pdf',
     'Description':'Single D flip-flop, set/reset, 5.5 V tolerant, Ioff (Nexperia 74LVC1G74-Q100, DP: 1 CP 2 D 3 Q# 4 GND 5 Q 6 RD# 7 SD# 8 VCC)'})
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
