"""Batch 29 schematic edits (m7-split): pass-3 review fixes. Run once on the ade499e tree."""
import re,sys,uuid
sys.path.insert(0,'/workspace/review/fix29'); sys.path.insert(0,'/workspace/review/split/exec')
from ed import *
from geo import blocks,libsyms,at_point
from sx import block_at
W='/workspace/m7/split/'
pwr=[f'#PWR{n:04d}' for n in range(3200,3300)]
def delat(sh,pt,kinds):
    n=0
    for k in kinds:
        while True:
            h=[x for x in at_point(sh.s,pt) if x[0]==k]
            if not h: break
            sh._rep(h[0][1],h[0][2],''); n+=1
    return n
def drop_libsym(sh,name):
    L,(li,le)=libsyms(sh.s)
    if name in L and not re.search(r'\(lib_id "%s"\)'%re.escape(name),sh.s):
        i=sh.s.find(L[name],li); sh._rep(i,i+len(L[name]),'')
def settext(sh,old,new):
    assert sh.s.count(old)==1,(old,sh.s.count(old)); sh.s=sh.s.replace(old,new)
# ======================= METER: B1 CT architecture =======================
ac=Sheet(W+'ac_metering.kicad_sch')
ZSYM='''(symbol "genctl:ZMCT103C"
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(property "Reference" "T" (at -5.08 6.35 0) (effects (font (size 1.27 1.27))))
		(property "Value" "ZMCT103C" (at -5.08 -6.35 0) (effects (font (size 1.27 1.27))))
		(property "Footprint" "genctl:Transformer_Zeming_ZMCT103C" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
		(property "Datasheet" "https://datasheet.lcsc.com/datasheet/pdf/fadce25fa7c9b6a55b2a8de064d6384d.pdf?productCode=C94571" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
		(property "Description" "Window current transformer 5 A : 5 mA (1000:1), rated burden 50 R, linear 0-15 A, 4500 V isolation withstand, -40..+85 C. Primary = insulated wire through the 5 mm window (no primary pins). S1 = pin 1* (dot), S2 = pin 2" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
		(symbol "ZMCT103C_0_1"
			(rectangle (start -5.08 5.08) (end 5.08 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))
			(circle (center -1.27 0) (radius 1.905) (stroke (width 0.254) (type default)) (fill (type none)))
			(polyline (pts (xy -1.27 4.445) (xy -1.27 -4.445)) (stroke (width 0.254) (type dash)) (fill (type none))))
		(symbol "ZMCT103C_1_1"
			(pin passive line (at 7.62 2.54 180) (length 2.54) (name "S1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
			(pin passive line (at 7.62 0 180) (length 2.54) (name "S2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))))'''
L,(li,le)=libsyms(ac.s)
ac.s=ac.s[:le-1]+ZSYM+'\n'+ac.s[le-1:]
ZP=[('Value','ZMCT103C'),('Footprint','genctl:Transformer_Zeming_ZMCT103C'),('LCSC','C94571'),('MPN','ZMCT103C'),('Manufacturer','Qingxian Zeming Langxi Electronic'),
    ('Datasheet','https://datasheet.lcsc.com/datasheet/pdf/fadce25fa7c9b6a55b2a8de064d6384d.pdf?productCode=C94571'),
    ('Description','Window CT 5 A:5 mA 1000:1, rated 50 R burden, +/-0.2 % ratio, <=15 min phase (class A), linear 0-15 A, 4.5 kV isolation, -40..+85 C'),
    ('Note','Batch 29 (pass-3 B1): replaces AC1005 C6117861. The field CT loop is a 600 V insulated wire (UL1015 14 AWG max, OD <=3.5 mm) through the 5 mm window; no CT-loop copper on this board. Wire from the external CT S1 enters the P1* face. Burden R474..R489 2 x 24.9R = 49.8R (rated 50R).')]
for t in ('T1','T2','T3','T4'):
    for k,v in ZP: ac.set_prop(t,k,v)
    for i,e,b in reversed(ac.sym(t)):
        nb=b.replace('(lib_id "genctl:AC1005")','(lib_id "genctl:ZMCT103C")',1)
        nb=re.sub(r'\(pin "[345]" \(uuid "[^"]+"\)\)\s*','',nb)
        ac._rep(i,e,nb)
# delete CT-loop stubs at old pins 4/5 and NC at pin 3
CTX={'T1':408.94,'T2':495.3,'T3':581.66,'T4':666.75}
for t,x in CTX.items():
    assert delat(ac,(round(x+7.62,2),218.44),['(no_connect'])==1
    for y in (215.9,218.44):
        assert delat(ac,(round(x-7.62-2.54,2),y),['(label','(wire (pts'])==2,(t,y)
# delete J30 and its 8 stubs
for p in range(8):
    assert delat(ac,(742.95,round(198.12+2.54*p,2)),['(label','(wire (pts'])==2
i,e,b=ac.sym('J30')[0]; ac._rep(i,e,'')
drop_libsym(ac,'genctl:AC1005'); drop_libsym(ac,'Connector_Generic:Conn_01x08')
for n in (1,2,3,4): settext(ac,f'(text "T{n} AC1005"',f'(text "T{n} ZMCT103C"')
settext(ac,'(text "J30 J9 CT secondaries (5A)"','(text "J30: OFF-BOARD (Batch 29)"')
settext(ac,'(text "U69 ISOW7841DWER"','(text "U69 ISOW7841AQDWERQ1"')
old=re.search(r'\(text "AC METERING\. [^"]*"',ac.s).group(0)
new=('(text "AC METERING. Hot side GND_AC isolated by ISOW7841 (data+power) + ISO7741, both 5kVrms reinforced, SOIC-16W 8mm. Barrier keep-out >=13mm + slot (docs/ISOLATION_CHECK.md).\\n'
     'Voltage: fully differential. Each line 12x330k (1206) -> tap (1k to GND_AC); each neutral (GEN_N, BUS_N separately) 12x330k -> N_TAP (1k to GND_AC); VxN <- 1k <- N_TAP. Ratio 1:3961.\\n'
     'No 0R neutral link: GND_AC floats at the divider mid-point, common-mode attenuated 3961:1. Current: ZMCT103C window CTs (Batch 29), burden 2x24.9R 1%, field CT loop = 600 V wire through the window."')
ac.s=ac.s.replace(old,new)
ac.text('Batch 29 (pass-3 B1), CT architecture: J30 is no longer on this board. T1-T4 are ZMCT103C window CTs (C94571). Each external 5 A CT circuit is a factory-fitted pigtail of 600 V UL1015 wire (14 AWG max, Ø5 mm window) threaded once through its CT window, P1* face toward the external CT S1, and both ends leave the enclosure to J30 = the off-board CT shorting/test terminal block in the genset panel (site wiring; CT S2 earthed there). No CT-loop copper anywhere on this PCB. The barrier between the earthed CT loop and GND_AC is the wire insulation (600 V) plus the CT body (4.5 kV withstand). Layout rules: docs/ISOLATION_CHECK.md §5c.',383.54,262.0)
ac.s=ac.s.replace(')\n(text "J30: OFF-BOARD (Batch 29)"',')\n(text "NEVER OPEN A CT LOOP OR DISCONNECT J30 WITH THE GENERATOR LIVE\\n(short the CTs at the J30 shorting block first: an open 5 A CT secondary develops lethal voltage)" (exclude_from_sim no) (at 383.54 250.0 0) (effects (font (size 1.5 1.5) (thickness 0.3) bold (color 200 0 0 1)) (justify left bottom)) (uuid "%s"))\n(text "J30: OFF-BOARD (Batch 29)"'%U(),1)
assert 'NEVER OPEN A CT LOOP' in ac.s
BURDEN=[r for r in (f'R{k}' for k in range(474,490)) if re.search(r'\(property "Note" "0\.1% burden"',ac.sym(r)[0][2])]
assert len(BURDEN)==8,BURDEN; print('burden',BURDEN)
for r in BURDEN:
    ac.set_prop(r,'Note','CT burden half: 24.9R 1 % 100 ppm/K (C22916). 2 x 24.9R = 49.8R = ZMCT103C rated 50R. Absolute gain set by per-channel calibration (xIGAIN); was mislabelled 0.1 % (pass-1 N4 / pass-3 m5)')
ac.set_prop('U69','Sourcing','CONSIGN (Batch 29): buy ISOW7841AQDWERQ1 from the TI store (live 2,026 on 2026-11-22) or Digi-Key 296-ISOW7841AQDWERQ1CT-ND and ship to JLC; LCSC/JLC stock 1. Fallback ISOW7841DWER (same pinout, commercial temp)')
ac.save()
# ======================= MAIN: power (m1, m2) =======================
pw=Sheet(W+'power.kicad_sch')
for k,v in [('Value','2.7k'),('LCSC','C13167'),('MPN','0603WAF2701T5E'),('Manufacturer','UNI-ROYAL'),('Description','Resistor 2.7k 1% 0603'),
            ('Note','Rc1. Batch 29 (pass-3 m1): 4.7k -> 2.7k. LM5176 DS eq.44: fbw = Rc1*gm*(1-D)/(2pi*15*5*8m*Cout). Cout(eff) ~70 uF: boost Vin 6 V fbw 6.7 kHz < fRHP/3 8.5 kHz (4 A); Vin 9 V 10.1 kHz < fsw/20 15 kHz; buck 13.4 kHz < 15 kHz. Bench load-step: docs/BENCH_12V_TEST.md §B29')]:
    pw.set_prop('R8',k,v)
for k,v in [('Value','1n'),('LCSC','C1588'),('MPN','CL10B102KB8NNNC'),('Manufacturer','Samsung Electro-Mechanics'),('Description','Capacitor 1 nF 50 V X7R 0603'),
            ('Note','Cc2. Batch 29: 220p -> 1n so fpc2 = 1/(2pi*2.7k*1n) = 59 kHz = 5.8-8.8 x fbw (DS: 7-10 x); 1n is a Basic part already on the BOM (C117/C119/C185)')]:
    pw.set_prop('C12',k,v)
for c,rail in (('C29','+5V'),('C30','+5V'),('C36','+3V3'),('C37','+3V3')):
    pw.set_dnp(c,True)
    pw.set_prop(c,'Note',f'Batch 29 (pass-3 m2): DNP. TPS56637 DS Table 4 allows 20-100 uF EFFECTIVE Cout. {rail} with this cap fitted plus downstream decoupling is ~100-120 uF effective (estimate); without it ~60 ({"+5V, plus CM5 module input caps" if rail=="+5V" else "+3V3 incl. +3V3_SAFE and the meter board"}: ~90) uF. Pads kept: fit only if the bench load-step (docs/BENCH_12V_TEST.md §B29) shows too much droop.')
pw.save()
# ======================= MAIN: inputs (m4, COM dividers) =======================
ins=Sheet(W+'inputs.kicad_sch')
for r in ('R137','R148','R159','R170','R181','R192'):
    for k,v in [('Footprint','Resistor_SMD:R_2010_5025Metric'),('LCSC','C876535'),('MPN','RT2010BKD07100RL'),('Manufacturer','YAGEO'),
                ('Description','Resistor 100R 0.1% 25 ppm/K 0.5 W thin film 2010'),
                ('Note','4-20mA shunt 0.1%. Batch 29 (pass-3 m4): 1206 0.25 W AR06BTCV1000 -> 2010 0.5 W RT2010BKD07100RL (same 0.1 %/25 ppm, ~2.5x thermal mass) + firmware over-range trip (docs/FW_REQ_BATCH29.md FW-AI-2: >25 mA -> shunt off within 50 ms, latch). A series PTC was rejected: AI1..AI6 are measured at the terminal node, so a PTC in the shunt leg adds its drifting resistance to every 4-20 mA reading, and one in the input line adds it to every resistive-sender reading.')]:
        ins.set_prop(r,k,v)
for r,val,lc,mpn in (('R196','100k','C122538','RT0603BRD07100KL'),('R198','100k','C122538','RT0603BRD07100KL'),('R197','18k','C309650','RT0603BRD0718KL'),('R199','18k','C309650','RT0603BRD0718KL')):
    for k,v in [('LCSC',lc),('MPN',mpn),('Manufacturer','YAGEO'),('Description',f'Resistor {val} 0.1% 25 ppm/K 0603 thin film'),
                ('Note','Batch 29 (pass-3 NOTE 6): 1 % -> 0.1 %, same parts as the AI channel dividers, so COM_A/COM_B scale matches AINx and the VMID term cancels in AINx-AIN3')]:
        ins.set_prop(r,k,v)
ins.save()
# ======================= MAIN: mcu (coin cell series R) =======================
mc=Sheet(W+'mcu.kicad_sch')
h=[x for x in at_point(mc.s,(104.14,347.98)) if x[0]=='(global_label']; assert len(h)==1
mc._rep(h[0][1],h[0][2],''); mc.label('VBAT_CELL_R',(104.14,347.98),180)
fpR=re.search(r'\(property "Footprint" "([^"]*)"',mc.sym('R46')[0][2]).group(1) if True else ''
x,y=free(mc,40,25)
mc.text('Batch 29 (pass-3 NOTE 10): R649 1k in series with BT1 (CR2032). With D7/D8 (BAT54C) this gives two independent protections against charging the primary lithium cell (UL 1642 / IEC 62368-1 Annex M style): if a diode shorts, reverse current is <= (3.3 V - 2.0 V)/1k = 1.3 mA. VBAT load is a few uA, so the drop is < 10 mV.',x,y)
mc.place('Device:R','R649','1k',x+10.16,y+15.24,'Resistor_SMD:R_0603_1608Metric',[('LCSC','C21190'),('MPN','0603WAF1001T5E'),('Manufacturer','UNI-ROYAL'),('Description','Resistor 1k 1% 0603'),('Note','Batch 29: coin-cell reverse-charge limit, place next to BT1')],
         conn={'1':('label','VBAT_CELL_R'),'2':('global','VBAT_CELL')},rot=90)
mc.save()
# ======================= MAIN: outputs / estop (stock plan metadata) =======================
ou=Sheet(W+'outputs.kicad_sch')
for k,v in [('Value','TPS3431SDRBR'),('MPN','TPS3431SDRBR'),('LCSC','C702145'),('Manufacturer','Texas Instruments'),('Datasheet','https://www.ti.com/lit/ds/symlink/tps3431.pdf'),
            ('Description','Programmable-timeout watchdog, DRB (VSON-8 3x3), -40..+125 C (commercial version of TPS3431-Q1: same die, pinout and timing)'),
            ('Sourcing','CONSIGN (Batch 29): TI store TPS3431SDRBR (live 700 on 2026-11-22) or Mouser 595-TPS3431SDRBR; LCSC/JLC 0. Was TPS3431SQDRBRQ1 C2878091 (0 everywhere live)')]:
    ou.set_prop('U37',k,v)
SRC_HTC='CONSIGN (Batch 29): buy TPS1HTC30AQPWPRQ1 from the TI store (live 3,000 on 2026-11-22) or Digi-Key 296-TPS1HTC30AQPWPRQ1CT-ND and ship 16/board to JLC; JLC/LCSC stock 12'
for n in list(range(47,62)):
    ou.set_prop(f'U{n}','Sourcing',SRC_HTC)
for q in ('Q70','Q71'):
    ou.set_prop(q,'Sourcing','CONSIGN (Batch 29): Vishay SQD40P10-40L_GE3 from Mouser 781-SQD40P10-40L_GE3 (AEC-Q101); LCSC/JLC 0. Clone DOINGTER C49237801 not used in the E-stop path')
ou.save()
es=Sheet(W+'estop.kicad_sch'); es.set_prop('U68','Sourcing',SRC_HTC); es.save()
print('batch29 ok, next PWR',pwr[0])
