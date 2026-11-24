"""Phase 2 mainboard rework (genctl root project).
Regenerates the sheets that change (mcu, estop, mtr_if, io_core = what stays of inputs+outputs) from the locked baseline
netlist with the documented net edits, and adds the new sheets (backplane = 9 slot connectors + ID muxes + slot bus,
slot_power = per-slot switches). Untouched sheets: power, cm5, comms, display, frontpanel (2 global-label renames).
All inter-sheet nets are global labels; rails use power symbols. Refs of kept parts are unchanged; new refs start at
R700 / C400 / U100 / Q100 / J40 / D200 / TP10."""
import os,sys,re,json,csv,collections,uuid,glob
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from mkcard import Card,short,ROOT,lib_pins
import schdraw
from lvcommon import lv_pinout
ROOTUUID='2f7a4bb8-89ed-4e3c-b40c-67c49fede2c6'
SHEETS=collections.OrderedDict([   # file -> (sheet uuid, title, paper)
 ('mcu',('c2700331-201a-4cfa-a277-c8f7379e4af6','STM32H743 safety MCU: slot SPI3, CS decoder, I2C2 ID bus','A2')),
 ('estop',('bf2b4d33-db1c-4f32-83fb-5781585769ff','E-stop feed: ideal diode, rail cut, bleeder, trip + sense','A2')),
 ('io_core',('6b1f0c2e-3a7d-4c55-9e2b-0f6a1d7c9b01','Core IO: AI1-2, DI1-4, D+, MPU, expanders, engine gating','A1')),
 ('backplane',('9c4e2a10-5b8f-4d3e-a1c7-2e9f0b6d4a02','Backplane: ENGINE + 8 LV slots, ID muxes, slot bus','A1')),
 ('slot_power',('3d7a9e51-0c2b-4f8a-b6d1-7e4c2a9f1b03','Slot power: bank limiter, overload cutoff, 8 slots','A1')),
 ('mtr_if',('5d1b3a52-6c1e-4f0a-9a31-3b0c2a6e7f10','Metering interface J31 (HV meter ID I2C on J31.12/16)','A3')),
])
KEEP_SHEETS={'power':'d8c05520-8978-4d93-9881-80f603685ecb','cm5':'d811a5f3-3ea5-4969-ac51-150b5151ab82','comms':'7172d8aa-4982-46d4-80f3-9c3b7e936f89',
             'display':'fcebac73-5e7d-409a-9893-556fac7ba7b9','frontpanel':'bd3092dd-3b47-4d13-9646-0a27ee0e3b04'}
RAILS={'GND','+3V3_SAFE','+3V3','+5V','+12V','VBAT_P','VBAT_ESTOP','VBAT_ESTOP_PRE','VBAT_SLOTS','BAT_IN'}   # Pass 6: BAT_IN (power sheet power symbol) for the Q2 hold-off
REMOVED_P1={'U41':"'541 GCB/MCB/AUX1-4 enables (card '541s)",'U42':"'541 AUX5-10 enables",'U64':'TMUX1208 AUX4-10 + ESTOP_TRIP (ESTOP_TRIP moves to U63)',
 'D133':'BAT54C AUX6/7 clamp','D134':'BAT54C AUX8/9 clamp','D135':'BAT54C AUX10/ESTOP_TRIP clamp','RN2':'SH_G5/6 pull-downs (AI-4 card copy)',
 'J17':'AI1-6 terminal (engine card / AI-4)','J26':'AUX1-6 terminal (HSO-5 headers)','J19':'DI1-6 terminal (engine card / DI-8)'}
REMOVED_P2={'Q70':'SQD40P10-40L reverse-polarity P-FET -> LM74700-Q1 + BSC070N10NS5','Q71':'SQD40P10-40L (parallel) -> ideal diode',
 'D137':'BZT52C15 P-FET gate clamp (no P-FET)','R627':'10k P-FET gate pull-down (no P-FET)',
 'D151':'SMAJ40A on DI_BIAS_B (bank B moved to DI-8 with its own TVS)','J27':'AUX7-10 terminal (HSO-5 headers)',
 'Q44':"WD_OE_N inverter for U41/U42 OE (removed '541s)",'R272':'Q44 base resistor','R273':'Q44 base pull-down','R274':'WD_OE_N pull-up',
 'R536':'PB4 4.7k pull-down (PB4 is now SLOT_EXP_INT_N, pulled up)','R36':'DI5 series R (DI5/DI6 moved to DI-8)','R37':'DI6 series R',
 'R38':'DI8 series R (PB10 = I2C2_SCL direct)','R39':'DI9 series R (PB11 = I2C2_SDA direct)','R40':'DI10 series R','R41':'DI11 series R'}
REMOVED_P3={'R160':'AI_SH_EN3 pull-down (U31 P10 unused, N2)','R171':'AI_SH_EN4 pull-down (N2)','R182':'AI_SH_EN5 pull-down (N2)','R193':'AI_SH_EN6 pull-down (N2)',
 'R544':'PB5 100k pull-down (PB5 now drives ID_MUX_RST_N, R707 10k pull-up keeps the muxes running at MCU reset; M4)'}
REMOVED_P3.update({f'C{n}':'TPS1HTC30 VS decoupling for drivers now on HSO-5/BRK-4/engine cards (decoupling moved onto the cards, M1)' for n in range(205,220)})
gone=set()
for cd in ['engine','di8','ai4','hso5','brk4']: gone|=set(json.load(open(os.path.join(ROOT,'cards',cd,'refmap.json'))))
from partition import ASSIGN
gone|={r for r,v in ASSIGN.items() if v=='HSO_B'}
REM=set(REMOVED_P1)|set(REMOVED_P2)|set(REMOVED_P3)
def sheet_refs(f):
    import subprocess
    t=subprocess.run(['git','-C',ROOT,'show',f'baseline-2026-11-23-locked:{f}.kicad_sch'],capture_output=True,text=True,check=True).stdout
    return set(re.findall(r'\(property "Reference" "([A-Z]+[0-9]+)"',t))
base_sheet={r:f for f in ['inputs','outputs','estop','mcu','mtr_if','power','cm5','comms','display','frontpanel'] for r in sheet_refs(f)}
# ---------------- net edits on kept baseline parts: (ref,pin) -> new net (None = NC) ----------------
OV={}
for p in ('6',): OV[('U29',p)]=None
for p in ('4','5','6'): OV[('U30',p)]=None                       # AI3-6 ADS1115 inputs: AI-4 has its own ADS1115
for p in ('6','7','8','9','18','20'): OV[('U31',p)]=None          # AI_CS_DIS3-6, DI_PU_B, DI_PD_B outputs (now on cards)
for p in ('3','6'): OV[('U92',p)]=None                            # AI_SH_G5/G6 outputs (AI-4 card)
for p in ('1','2','4','5'): OV[('U92',p)]='GND'                     # N2: U92 gates 1-2 unused (AI_SH_EN5/6 gone): inputs to GND
OV[('U92','12')]='SH_ALLOW'; OV[('U92','13')]='SLOT_RST_N'; OV[('U92','11')]='GLOBAL_OUT_ALLOW'   # B2: spare gate 4 = WD_OK AND NRST_S AND SLOT_RST_N
for p in ('9','10','12','13'): OV[('U91',p)]='GND'                  # N2: U91 gates 3-4 unused (SH_G3/G4 on the AI-4 card): inputs to GND
for p in ('8','11'): OV[('U91',p)]=None
for p in ('5','6'): OV[('RN1',p)]=None                              # N2: RN1 R3/R4 (SH_G3/G4 pull-downs) unused
for p in ('13','14','15','16'): OV[('U31',p)]=None                  # N2: U31 P10-P13 (AI_SH_EN3-6) unused
for p in ('11','13'): OV[('U32',p)]='GND'                          # DI5/DI6 Schmitt gates unused: input to GND
for p in ('10','12'): OV[('U32',p)]=None
for i,p in enumerate(('7','8','9','10','11','13','14','15')): OV[('U62',p)]=f'SL{i+1}_PRESENT_N'   # freed readback inputs -> slot presence
for p in ('16','17','18','19','20'): OV[('U62',p)]=None         # spare: firmware sets them as outputs (low)
OV[('U63','5')]='ESTOP_TRIP_SNSM'                                  # ESTOP_TRIP sense moves from U64 to U63 S2
for p in ('6','7','9','10','11','12'): OV[('U63',p)]='GND'
OV[('J21','3')]=None                                               # D+ terminal now on the engine card
for p in ('1','2','3','4','5'): OV[('J24',p)]=None                 # GLOW/GCB/MCB terminals now on the engine card / BRK-4; J24.6 ESTOP_TRIP_OUT stays
OV[('C224','1')]='SLOT_ANA'; OV[('U7','16')]='SLOT_ANA'             # PC1 (pin 16) ADC: was MUXB_OUT (U64), now the slot ANA_OUT mux
REN={'GCB_CL_MCU':'SLOT_RST_N_M','GCB_OP_MCU':'SLOT_SPI_SCK_M','MCB_CL_MCU':'SLOT_SPI_MISO','MCB_OP_MCU':'SLOT_SPI_MOSI_M',
     'AUX1_MCU':'SLOT_CS_A0','AUX2_MCU':'SLOT_CS_A1','AUX7_MCU':'SLOT_CS_A2','AUX8_MCU':'SLOT_CS_EN',
     'AUX4_MCU':'ID_MUX_RST_N','AUX5_MCU':'ID_WP_UNLOCK','AUX6_MCU':'RC_ALLOW','AUX3_MCU':'SLOT_EXP_INT_N',
     'AUX9_MCU':'EXP25_P07_SPARE','AUX10_MCU':'EXP25_P10_SPARE'}
for p in ('44','45','53','54','57'): OV[('U7',p)]=None        # DI6/7/10/11/12 MCU pins: inputs moved to DI-8 (SPI expander)
OV[('U7','43')]='SLOT_ANA_EN'                                      # Pass 2 m1: PE13 (was DI5, freed) drives the U109 slot ANA mux EN (100k pull-down)
OV[('U7','46')]='I2C2_SCL'; OV[('U7','47')]='I2C2_SDA'              # PB10/PB11 AF4 = I2C2 (DS12110 rev 10)
# E-stop feed split: ideal diode J23 -> VBAT_ESTOP_PRE (sense, pre-cut) -> rail cut -> VBAT_ESTOP (engine slot, ADC readback)
for rp in (('C199','1'),('R251','1'),('R400','1')): OV[rp]='VBAT_ESTOP_PRE'
OV[('D126','1')]='VBAT_ESTOP_IN'                                   # bidirectional TVS ahead of the ideal diode
OV[('U34','9')]='ESTOP_DIG'; OV[('U34','8')]='ESTOP_OK'             # spare 74HC14 gate: ESTOP_OK = NOT ESTOP_DIG
OV[('C225','1')]='U65_IN'; OV[('U65','1')]='U65_IN'                # Pass 5: 47R R1002 between D120 K (D120_K) and C225/U65 IN
OV[('U5','3')]='U5_EN'                                            # Pass 6 B1: U5 EN/UVLO split from VIN (power sheet, pass6_power_patch.py): 100k/47k from VBAT_P + Q2 hold-off
for n,p in (('DPLUS_SNS','24'),('FUEL_ISNS','25'),('CRANK_ISNS','35'),('MPU_GATE','64'),('DPLUS_EXC_EN','65'),('DIAG_EN','67'),('MPU_SPEED','77')):
    OV[('U7',p)]=n+'_M'                                           # Pass 6 M3: engine-slot lines reach U7 only through a series R (+ BAT54S clamp)
OV[('J31','12')]='MTR_ID_SCL'; OV[('J31','16')]='MTR_ID_SDA'         # HV meter ID EEPROM (matches J32.12/J32.16)
ASSIGN_SHEET={}
for r,f in base_sheet.items():
    if r in gone or r in REM: continue
    if f in ('inputs','outputs'): ASSIGN_SHEET[r]='io_core'
    elif f in ('estop','mcu','mtr_if'): ASSIGN_SHEET[r]=f
for r in ('J23','C199','C203','D126'): ASSIGN_SHEET[r]='estop'
cards={}
def card(f):
    if f not in cards:
        c=Card(f,SHEETS[f][1],SHEETS[f][2]); c.count.update({'R':699,'C':399,'U':99,'Q':99,'J':39,'D':199,'TP':9}); cards[f]=c
    return cards[f]
for r in sorted(ASSIGN_SHEET):
    c=card(ASSIGN_SHEET[r]); c.move([r],rename={r:r})
for c in cards.values():
    for p in c.parts:
        for k in list(p['pn']):
            if (p['ref'],k) in OV: p['pn'][k]=OV[(p['ref'],k)]
            elif p['pn'][k] in REN: p['pn'][k]=REN[p['pn'][k]]
        p['props'].pop('BaselineRef',None)
        if p['ref']=='D126':   # M6: SMDJ36CA (Littelfuse: VR 36 V, VBR 40.0-44.2 V, VC 58.1 V @ 51.6 A 10/1000 us) keeps VC under LM74700 ANODE 65 V
            p['props'].update(Value='SMDJ36CA',MPN='SMDJ36CA',Manufacturer='Littelfuse',LCSC='C224075')
# ---------------- new parts ----------------
SRC=card('io_core')
def props_lcsc(lcsc):
    for r,ii in SRC.inst.items():
        if ii and ii[0]['props'].get('LCSC')==lcsc:
            P=dict(ii[0]['props']); P.pop('Reference',None); P.pop('Note',None); return P   # Pass 4 m3: never inherit another part's Note
    raise KeyError(lcsc)
def P(value,fp,mpn,man,lcsc,desc=''): return {'Value':value,'Footprint':fp,'MPN':mpn,'Manufacturer':man,'LCSC':lcsc,'Description':desc}
R0603='Resistor_SMD:R_0603_1608Metric'
NEWP={'C2941042':P('LM74700QDBVRQ1','Package_TO_SOT_SMD:SOT-23-6','LM74700QDBVRQ1','Texas Instruments','C2941042','Ideal-diode controller, reverse battery to -65 V'),
 'C130026':P('TCA9548APWR','Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm','TCA9548APWR','Texas Instruments','C130026','8-ch I2C switch'),
 'C485077':P('SN74LVC138APWR','Package_SO:TSSOP-16_4.4x5mm_P0.65mm','SN74LVC138APWR','Texas Instruments','C485077','slot CS decoder'),
 'C7394016':P('74LVC1G02','Package_TO_SOT_SMD:SOT-23-5','SN74LVC1G02DBVR(UMW)','UMW','C7394016','NOR: PWR_EN = SLOT_EN AND PRESENT'),
 'C7826':P('74LVC1G00','Package_TO_SOT_SMD:SOT-23-5','SN74LVC1G00DBVR','Texas Instruments','C7826','NAND: OUT_EN_N = NOT(PWR_EN AND WD_OK)'),
 'C2903468':P('10m','Resistor_SMD:R_2512_6332Metric','HoJLR2512-3W-10mR-1%','Milliohm','C2903468','slot shunt 10 mOhm 3 W'),
 'C160590':P('2m','Resistor_SMD:R_2512_6332Metric','RLP25FEER002','TA-I Tech','C160590','rail-cut shunt 2 mOhm 2 W'),
 'C137808':P('10.5k',R0603,'RC0603FR-0710K5L','YAGEO','C137808','rail-cut ISCP: 15.8/20/24.8 A'),
 'C23000':P('30.1k',R0603,'0603WAF3012T5E','UNI-ROYAL','C23000','slot ISCP: 7.9 A typ with 10 mOhm'),
 'C23249':P('80.6k',R0603,'0603WAF8062T5E','UNI-ROYAL','C23249','TPS2553 ILIM: 291-370 mA'),
 'C22046':P('SN74LVC1G11DBVR','Package_TO_SOT_SMD:SOT-23-6','SN74LVC1G11DBVR','Texas Instruments','C22046','3-input AND, Ioff (SCES487J)'),
 'C403721':P('SN74LVC1G10DBVR','Package_TO_SOT_SMD:SOT-23-6','SN74LVC1G10DBVR','Texas Instruments','C403721','3-input NAND, Ioff (SCES486F)'),
 'C7827':P('SN74LVC1G04DBVR','Package_TO_SOT_SMD:SOT-23-5','SN74LVC1G04DBVR','Texas Instruments','C7827','inverter, Ioff (SCES214AF)'),
 'C20917':P('AO3400A','Package_TO_SOT_SMD:SOT-23','AO3400A','Alpha & Omega','C20917','N-FET 30 V, VGS(th) 1.45 V max, 48 mOhm @ 2.5 V'),
 'C2903482':P('5m','Resistor_SMD:R_2512_6332Metric','HoJLR2512-3W-5mR-1%','Milliohm','C2903482','shunt 5 mOhm 3 W'),
 'C23348':P('24.3k',R0603,'0603WAF2432T5E','UNI-ROYAL','C23348','slot ISCP 24.3k: 10.7/13.6/16.6 A with 5 mOhm'),
 'C22898':P('19.6k',R0603,'0603WAF1962T5E','UNI-ROYAL','C22898','bank ISCP 19.6k: 9.2/11.6/14.4 A with 5 mOhm'),
 'C22952':P('210k',R0603,'0603WAF2103T5E','UNI-ROYAL','C22952','TPS2553 ILIM 210k: 110/130/150 mA'),
 'C17471':P('150R','Resistor_SMD:R_0805_2012Metric','0805W8F1500T5E','UNI-ROYAL','C17471','+3V3_ID feed 150R 0805 (72.6 mW into a short)'),
 'C23140':P('33R',R0603,'0603WAF330JT5E','UNI-ROYAL','C23140','slot bus source series 33R'),
 'C13967':P('470n','Capacitor_SMD:C_0805_2012Metric','CL21B474KBFNNNE','Samsung','C13967','0.47 uF 50 V X7R 0805'),
 'C23091':P('61.9k',R0603,'0603WAF6192T5E','UNI-ROYAL','C23091','bank ISCP 61.9k: 22.4/28.6/35.0 A with 5 mOhm (Pass 2 MAJ-1)'),
 'C31658':P('68n','Capacitor_SMD:C_0603_1608Metric','CL10B683KB8NNNC','Samsung','C31658','bank C_TMR 68 nF X7R 50 V: 517/919/1490 us with 100k latch (Pass 2 MAJ-1)'),
 'C1517405':P('INA281A2IDBVR','Package_TO_SOT_SMD:SOT-23-5','INA281A2IDBVR','Texas Instruments','C1517405','bank current monitor 50 V/V on the 5 mOhm bank shunt (CM -4..110 V, VS +5V_TRIP)'),
 'C20345924':P('TLV3012BIDBVR','Package_TO_SOT_SMD:SOT-23-6','TLV3012BIDBVR','Texas Instruments','C20345924','bank overload comparator + 1.242 V ref; POR holds OUT low = trip (fail-safe)'),
 'C23056':P('44.2k',R0603,'0603WAF4422T5E','UNI-ROYAL','C23056','REF divider 44.2k/100k: V_TH 0.861 V'),
 'C113804':P('2.2n','Capacitor_SMD:C_0603_1608Metric','CC0603KRX7R0BB222','YAGEO','C113804','gate dV/dt cap C1 2.2 nF X7R 100 V, diode-steered (charge only) via 1N4148W + 10R (Pass 3 B1)'),
 'C22880':P('15.8k',R0603,'0603WAF1582T5E','UNI-ROYAL','C22880','bank overload filter R 15.8k: tau 316 ms with 2x 10 uF (Pass 3 MAJ-A)'),
 'C22920':P('25.5k',R0603,'0603WAF2552T5E','UNI-ROYAL','C22920','bank overload ROOM divider 25.5k (k 0.617, tau 195 ms) (Pass 3 MAJ-A)'),
 'C14860':P('10u','Capacitor_SMD:C_1206_3216Metric','CL31B106KAHNNNE','Samsung','C14860','bank overload filter C 10 uF X7R 25 V 1206 (2 in parallel; -1.3 % at 1.5 V) (Pass 3 MAJ-A)'),
 'C353035':P('TS5A3166DBVR','Package_TO_SOT_SMD:SOT-23-5','TS5A3166DBVR','Texas Instruments','C353035','ROOM-select analog switch: off-leakage +/-100 nA max -40..185 F (replaces AO3400A Q108, Pass 3 MAJ-A)'),
 'C421608':P('2.2k 1W','Resistor_SMD:R_2512_6332Metric','25121WF2201T4E','UNI-ROYAL','C421608','VBAT_ESTOP bleeder 2.2k 2512 1 W (2 in parallel = 1.1k, Pass 2 MAJ-3)'),
 'C17976':P('68R','Resistor_SMD:R_1206_3216Metric','1206W4F680JT5E','UNI-ROYAL','C17976','+3V3_ID feed 68R 1206 0.25 W: 160 mW into a short, >= 3.0 V at 3.7 mA (Pass 2 m14)'),
 'C50254':P('2.2u','Capacitor_SMD:C_1206_3216Metric','CL31B225KBHNNNE','Samsung','C50254','C_BST 2.2 uF / 50 V X7R 1206 (Pass 4 m4)'),
 'C13832':P('1u 100V','Capacitor_SMD:C_1206_3216Metric','CL31B105KCHNNNE','Samsung','C13832','C_VS hold-up 1 uF / 100 V X7R 1206 (Pass 4 P4-MAJ-1)'),
 'C106246':P('1n C0G','Capacitor_SMD:C_0603_1608Metric','CC0603JRNPO9BN102','YAGEO','C106246','slot C_TMR 1 nF C0G 50 V 5 %: t_SC 8.0/13.5/20.9 us with 100k latch (Pass 4 P4-MAJ-1)'),
 'C1849461':P('TPS16630PWPR','Package_SO:HTSSOP-20-1EP_4.4x6.5mm_P0.65mm_EP3.4x6.5mm_Mask2.96x2.96mm_ThermalVias','TPS16630PWPR','Texas Instruments','C1849461','eFuse 4.5-60 V (67 V abs max), I_OL = 18/R_ILIM(k): slots 3.09k 5.36-6.30 A latch (MODE open, Pass 6 M2); engine VBAT_P U161 30k 0.54-0.66 A auto-retry (Pass 6 M3); fast-trip 2x I_OL, SCP 45 A / 1 us'),
 'C23040':P('4.02k','Resistor_SMD:R_0603_1608Metric','0603WAF4021T5E','UNI-ROYAL','C23040','eFuse R_ILIM 4.02k 1 %: I_OL = 18/4.02 = 4.48 A typ (4.19-4.82 A) (Pass 5)'),
 'C22992':P('3.09k','Resistor_SMD:R_0603_1608Metric','0603WAF3091T5E','UNI-ROYAL','C22992','eFuse R_ILIM 3.09k 1 %: I_OL = 18/3.09 = 5.83 A typ (5.36-6.30 A incl. 1 % R); smallest E96 value whose -1 % stays >= 3 kOhm (SLVSET9G, UL 2367) (Pass 6 M2)'),
 'C8326':P('MMBT5401','Package_TO_SOT_SMD:SOT-23','MMBT5401(RANGE:200-300)','CJ','C8326','PNP 150 V VCEO, hFE 200-300, SOT-23 (pin 1 B, 2 E, 3 C = MMBT3906 symbol) (Pass 6 B1 hold-off)'),
 'C23231':P('68k',R0603,'0603WAF6802T5E','UNI-ROYAL','C23231','68k 1 % 0603'),
 'C17414':P('10k','Resistor_SMD:R_0805_2012Metric','0805W8F1002T5E','UNI-ROYAL','C17414','10k 1 % 0805 125 mW 150 V'),
 'C31850':P('22k','Resistor_SMD:R_0603_1608Metric','0603WAF2202T5E','UNI-ROYAL','C31850','22k 1 % 0603 100 mW (Pass 8: hold-off divider; R22K/C4190 is 2.2k)'),
 'C25819':P('47k','Resistor_SMD:R_0603_1608Metric','0603WAF4702T5E','UNI-ROYAL','C25819','47k 1 % 0603 100 mW (Pass 8: U5 EN divider; R47K/C23162 is 4.7k)'),
 'C22984':P('30k','Resistor_SMD:R_0603_1608Metric','0603WAF3002T5E','UNI-ROYAL','C22984','30k 1 % 0603 100 mW'),
 'C25818':P('453k','Resistor_SMD:R_0603_1608Metric','0603WAF4533T5E','UNI-ROYAL','C25818','eFuse OVP divider top 453k 1 % (Pass 5)'),
 'C22809':P('15k','Resistor_SMD:R_0603_1608Metric','0603WAF1502T5E','UNI-ROYAL','C22809','eFuse IMON 15k: 0.42 V/A (27.9 uA/A), 2.0 V at 4.8 A (Pass 5)'),
 'C14281':P('SS310B','Diode_SMD:D_SMB','SS310B','MDD','C14281','Schottky 100 V 3 A SMB, eFuse OUT -> GND freewheel (TI SLVSET9G 10.2.1) (Pass 5)'),
 'C170101':P('2.2u 100V','Capacitor_SMD:C_1206_3216Metric','CL31B225KCHSNNE','Samsung','C170101','eFuse IN cap 2.2 uF / 100 V X7R 1206: absorbs the trip kick, VBAT_SLOTS <= 57 V vs 67 V (Pass 5)'),
 'C17969':P('47R','Resistor_SMD:R_1206_3216Metric','1206W4F470JT5E','UNI-ROYAL','C17969','U65 feed 47R 1206: RC with C225 limits U65 IN kick (Pass 5)'),
 'C5173363':{'Value':'DIN41612_C96','Footprint':'cards:DIN41612_C96_Female_Vertical_WingTAT_9001-12961','MPN':'9001-12961C00A','Manufacturer':'WingTAT','LCSC':'C5173363','Description':'slot socket'}}
def pr(lcsc,**kw):
    d=dict(NEWP[lcsc]) if lcsc in NEWP else props_lcsc(lcsc); d.update(kw); return d
def add(sheet,lib,prefix,lcsc,pn,unit=1,**kw):
    c=card(sheet); ref=kw.pop('ref') if 'ref' in kw else c.newref(prefix); d=pr(lcsc,**{k:v for k,v in kw.items() if k!='ref'})
    c.add(lib,ref,d['Value'],pn,d,unit=unit); return ref
for c in cards.values(): pass
def R(sheet,lcsc,a,b,**kw): return add(sheet,'Device:R','R',lcsc,{'1':a,'2':b},**kw)
def C(sheet,lcsc,a,b='GND',**kw): return add(sheet,'Device:C','C',lcsc,{'1':a,'2':b},**kw)
# all sheets share one ref counter
class Shared(collections.Counter): pass
shared=collections.Counter({'R':699,'C':399,'U':99,'Q':99,'J':39,'D':199,'JP':9})
for f in SHEETS: card(f).count=shared
def gate_net(S,k,src):
    """Pass 3 B1/MAJ-C (all 9 slot-power channels): R1 470R G1PU; C1 2.2 nF diode-steered (gate -> 1N4148W -> 10R -> C1 -> GND, 1M C1 -> SRC):
    C1 only sinks gate current (dV/dt control) and can never hold the gate up when SRC collapses; 1N4148W gate -> BST clamps Vgs to BST-SRC + Vf;
    BZT52C15 G-S secondary clamp (K = gate); C_BST 2.2 uF / 50 V 1206 X7R (Pass 4 m4). Math: docs/modular/pass3_calc.txt, pass4_calc.txt."""
    return [R(S,'C23179',f'{k}_GPU',f'{k}_G',Description='G1PU gate resistor R1 470R (Pass 3 B1)'),R(S,'C21189',f'{k}_GPD',f'{k}_G',Description='G1PD link 0R, FIT: fast SCP / normal turn-off straight onto the gate'),
            add(S,'Diode:1N4148W','D','C81598',{'2':f'{k}_G','1':f'{k}_GD'},Description='C1 steering diode: gate charges C1, C1 cannot drive the gate (Pass 3 B1)'),
            R(S,'C22859',f'{k}_GD',f'{k}_GC',Description='10R in series with the steered gate dV/dt cap C1'),C(S,'C113804',f'{k}_GC','GND'),
            R(S,'C22935',f'{k}_GC',src,Description='C1 bleed to SRC (tau 2.2 ms): C1 reset between turn-ons (re-enable >= 20 ms)'),
            add(S,'Diode:1N4148W','D','C81598',{'2':f'{k}_G','1':f'{k}_BST'},Description='gate -> BST clamp: Vgs <= BST-SRC + Vf (14.8 V worst, abs max 19 V) (Pass 3 B1)'),
            add(S,'Device:D_Zener','D','C2104',{'1':f'{k}_G','2':src},Description='G-S clamp BZT52C15 13.8-15.6 V, K = gate, A = source (Pass 3 B1, secondary)'),
            C(S,'C50254',f'{k}_BST',src,Description='C_BST 2.2 uF / 50 V X7R 1206: BST-SRC >= 9.12 V at turn-on, TDRV_EN <= 126 ms (Pass 4 m4)')]
VSREF={'D':240,'R':920,'C':520}
def vs_holdup(S,k,feed):
    """Pass 4 P4-MAJ-1: per-controller VS hold-up (SLUSEW1C 8.3 RVS-CVS + series diode): feed -> 1N4148W -> 100R -> VS, 1 uF / 100 V to GND.
    Holds VS >= 4 V for >= 8 ms after the feed collapses in a dead short (slot latch <= 25.2 us). Math: docs/modular/pass4_calc.txt."""
    # own ref range (D241+, R921+, C521+) so every Pass 3 reference designator keeps its number
    VSREF.update({x:VSREF[x]+1 for x in VSREF})
    return [add(S,'Diode:1N4148W','D','C81598',{'2':feed,'1':f'{k}_VSD'},ref=f"D{VSREF['D']}",Description=f'VS hold-up diode from {feed}: blocks when {feed} collapses (Pass 4 P4-MAJ-1)'),
            R(S,'C22775',f'{k}_VSD',f'{k}_VS',ref=f"R{VSREF['R']}",Description='RVS 100R (SLUSEW1C 8.3) (Pass 4 P4-MAJ-1)'),
            C(S,'C13832',f'{k}_VS','GND',ref=f"C{VSREF['C']}",Description='C_VS 1 uF / 100 V hold-up: VS >= 4 V for >= 8.3 ms (Pass 4 P4-MAJ-1)')]
C10N='C57112'; FET='C534364'; R10K='C25804'; R100K='C25803'; R4K7='C23162'; R2K2='C4190';   # Pass 8: were named R47K/R22K although they are the 4.7k/2.2k parts (caused the hold-off value bug)
C100N='C14663'; R100='C22775'
# ---- E-stop feed: ideal diode + rail cut ----
S='estop'
Uid=add(S,'cards:LM74700QDBVRQ1','U','C2941042',{'6':'VBAT_ESTOP_IN','3':'VBAT_ESTOP_IN','1':'ESTOP_ID_VCAP','4':'VBAT_ESTOP_PRE','5':'ESTOP_ID_G','2':'GND'})
Qid=add(S,'Transistor_FET:BSC070N10NS5','Q',FET,{'1':'VBAT_ESTOP_IN','2':'VBAT_ESTOP_IN','3':'VBAT_ESTOP_IN','4':'ESTOP_ID_G','5':'VBAT_ESTOP_PRE'},
        Description='Ideal-diode FET: source = J23 side, drain = PRE; body diode blocks reverse battery')
C(S,'C13967','ESTOP_ID_VCAP','VBAT_ESTOP_IN',Description='LM74700 VCAP to ANODE 0.47 uF / 50 V X7R (N7)')
C(S,C100N,'VBAT_ESTOP_IN',Description='LM74700 ANODE >= 22 nF')
Urc=add(S,'genctl:TPS48100QDGXRQ1','U','C43131316',{'1':'RC_UVLO','2':'GND','3':'RC_EN','5':'OUT_FAULT_N','6':'GND','7':'GND','8':'RC_ISCP','9':'RC_TMR','10':'GND',
        '12':'RC_BST','13':'VBAT_ESTOP','14':'RC_GPD','15':'RC_GPU','17':'RC_DRN','18':'VBAT_ESTOP_PRE','20':'VBAT_ESTOP_PRE','4':None,'11':None,'19':None})
R(S,'C160590','VBAT_ESTOP_PRE','RC_DRN')
for i in range(2): add(S,'Transistor_FET:BSC070N10NS5','Q',FET,{'5':'RC_DRN','1':'VBAT_ESTOP','2':'VBAT_ESTOP','3':'VBAT_ESTOP','4':'RC_G'})
R(S,'C22859','RC_GPU','RC_G'); R(S,'C21189','RC_GPD','RC_G')
R(S,'C137808','RC_ISCP','GND'); C(S,'C106218','RC_TMR'); R(S,R100K,'RC_TMR','GND',Description='100k across C_TMR = latch-off after a short (TPS48100 Eq 9); reset by toggling RC_ALLOW'); C(S,'C1623','RC_BST','VBAT_ESTOP')
R(S,R100K,'VBAT_ESTOP_PRE','RC_UVLO'); R(S,'C22967','RC_UVLO','GND')
add(S,'cards:74LVC1G11','U','C22046',{'1':'WD_OK','3':'ESTOP_OK','6':'RC_ALLOW','2':'GND','4':'RC_EN','5':'+3V3_SAFE'},Description='rail cut enable = WD_OK AND ESTOP_OK AND RC_ALLOW (PB7, 100k pull-down R546)')
C(S,C100N,'+3V3_SAFE'); R(S,R100K,'RC_EN','GND')
# Pass 2 MAJ-3: switched active bleeder on VBAT_ESTOP, ON whenever RC_EN is low (E-stop, watchdog, RC_ALLOW low): 1.1k, tau ~2 ms, 32 V -> 2 V in <= 6.6 ms
add(S,'cards:AO3400A','Q','C20917',{'1':'RC_EN','2':'GND','3':'RC_BLEED_G'},Description='bleeder gate inverter: RC_EN high -> on -> bleeder gate low (off)')
R(S,R100K,'+5V_TRIP','RC_BLEED_G',Description='bleeder gate pull-up to +5V_TRIP (from VBAT_P): bleeder ON when RC_EN is low')
add(S,'cards:IRLML0100','Q','C53658',{'1':'RC_BLEED_G','2':'GND','3':'RC_BLEED_D'},Description='bleeder switch IRLML0100 100 V: VGS 5 V vs VGS(th) 2.5 V max, 235 mOhm at 4.5 V')
for i in range(2): R(S,'C421608','VBAT_ESTOP','RC_BLEED_D',Description='bleeder 2.2k 2512 1 W (x2 = 1.1k): stuck-on Q101/Q102 at 32 V = 0.47 W each')
for a,b in (('SLOT_SPI_SCK_M','SLOT_SPI_SCK'),('SLOT_SPI_MOSI_M','SLOT_SPI_MOSI'),('SLOT_RST_N_M','SLOT_RST_N')):
    R('mcu','C23140',a,b,Description='33R source series at the MCU pin (N12)')
for n in ('MUX_A0','MUX_A1','MUX_A2'): R('mcu',R100K,n,'GND',Description='Pass 2 m1: MUX_A pull-down, defined mux address at MCU reset')
# ---- backplane ----
S='backplane'; LV={}
for r in csv.DictReader(open(os.path.join(ROOT,'docs/modular/slot_pinout_LV.csv'))):
    for row in 'abc': LV[f"{row}{r['position']}"]=r['row_'+row]
def din(sheet,pmap,desc):
    c=card(sheet); ref=c.newref('J'); d=pr('C5173363',Description=desc)
    for u,row in enumerate('abc',1): c.add('cards:DIN41612_C96',ref,'DIN41612_C96',{k:v for k,v in pmap.items() if k[0]==row},d,unit=u)
    return ref
ID=lambda n:[(n>>0)&1,(n>>1)&1,(n>>2)&1]
slots=[]
for s in range(1,9):
    b=ID(s-1); par=1-(sum(b)%2)   # odd parity over ID0..2+IDP: all-GND and all-open never decode as valid
    m={'VBAT_FIELD':f'SL{s}_VBAT','FIELD_GND':'GND','GND':'GND','+3V3_SLOT':f'SL{s}_3V3','+3V3_ID':f'SL{s}_3V3_ID',
       'PRESENT_N':f'SL{s}_PRESENT_N','SPI_SCK':'SLOT_SPI_SCK','SPI_MOSI':'SLOT_SPI_MOSI','SPI_MISO':'SLOT_SPI_MISO','SPI_CS_N':f'SL{s}_CS_N',
       'I2C_SDA':f'SL{s}_ID_SDA','I2C_SCL':f'SL{s}_ID_SCL','INT_N':f'SL{s}_INT_N','RST_N':'SLOT_RST_N','OUT_EN_N':f'SL{s}_OUT_EN_N',
       'CARD_FAULT_N':f'SL{s}_CARD_FAULT_N','SLOT_ID0':'GND' if not b[0] else None,'SLOT_ID1':'GND' if not b[1] else None,'SLOT_ID2':'GND' if not b[2] else None,
       'SLOT_IDP':'GND' if not par else None,'ANA_OUT':f'SL{s}_ANA','ID_WP':'ID_WP','RSVD':None}
    pmap={k:m[v] for k,v in LV.items()}
    slots.append(din(S,pmap,f'LV slot {s} socket (slot ID {s-1}: ID2..0 = {b[2]}{b[1]}{b[0]}, IDP = {par}; 1 = open, 0 = GND)'))
E={}
for r in csv.DictReader(open(os.path.join(ROOT,'cards/engine/engine_slot_pinout.csv'))):
    for row in 'abc':
        n=r['row_'+row]; E[f"{row}{r['position']}"]={'ID_SDA':'ENG_ID_SDA','ID_SCL':'ENG_ID_SCL','+3V3_SAFE':'ENG_3V3_SAFE','VBAT_P':'ENG_VBAT_P'}.get(n,n)   # Pass 6 M3: protected engine feeds   # ENG_PRESENT_N (c31): card grounds it, read on 0x22 P10
JE=din(S,E,'ENGINE slot socket (keyed). Pinout cards/engine/engine_slot_pinout.csv')
# ID muxes on I2C2 (0x70 = slots 1-8, 0x71 = engine + HV meter)
mx=[]
for a in (0,1):
    pn={'22':'I2C2_SCL','23':'I2C2_SDA','3':'ID_MUX_RST_N','1':'+3V3_SAFE' if a else 'GND','2':'GND','21':'GND','24':'+3V3_SAFE','12':'GND'}
    ch=[f'SL{i+1}' for i in range(8)] if a==0 else ['ENG','MTR']+[None]*6
    for i,n in enumerate(ch):
        sc,sd={0:('5','4'),1:('7','6'),2:('9','8'),3:('11','10'),4:('14','13'),5:('16','15'),6:('18','17'),7:('20','19')}[i]
        pn[sc]=f'{n}_ID_SCL' if n else None; pn[sd]=f'{n}_ID_SDA' if n else None
    mx.append(add(S,'cards:TCA9548APWR','U','C130026',pn,Value=f'TCA9548APWR @0x7{a}')); C(S,C100N,'+3V3_SAFE')
R(S,R10K,'ID_MUX_RST_N','+3V3_SAFE'); R(S,R2K2,'I2C2_SCL','+3V3_SAFE'); R(S,R2K2,'I2C2_SDA','+3V3_SAFE')
for n in [f'SL{i}' for i in range(1,9)]+['ENG','MTR']:
    R(S,R4K7,f'{n}_ID_SCL','+3V3_SAFE'); R(S,R4K7,f'{n}_ID_SDA','+3V3_SAFE')
R(S,R10K,'ID_WP','+3V3_SAFE',Description='ID_WP idle high = all ID EEPROMs write-protected')
add(S,'cards:AO3400A','Q','C20917',{'1':'ID_WP_UNLOCK','2':'GND','3':'ID_WP'},Description='M7: PB6 high (ID_WP_UNLOCK, 100k pull-down R545) pulls ID_WP low = slot + engine ID EEPROMs writable')
# slot SPI chip selects
add(S,'cards:SN74LVC138APWR','U','C485077',{'1':'SLOT_CS_A0','2':'SLOT_CS_A1','3':'SLOT_CS_A2','6':'SLOT_CS_EN','4':'GND','5':'GND','16':'+3V3_SAFE','8':'GND',
    '15':'SL1_CS_N','14':'SL2_CS_N','13':'SL3_CS_N','12':'SL4_CS_N','11':'SL5_CS_N','10':'SL6_CS_N','9':'SL7_CS_N','7':'SL8_CS_N'}); C(S,C100N,'+3V3_SAFE')
# slot expanders on I2C2 root (0x20 EN_N / PWR_FAULT_N, 0x21 INT_N / ARM_N, 0x22 CARD_FAULT_N / ENG_PRESENT_N / bank limiter)
for a,lo,hi in ((0,'EN_N','PWR_FAULT_N'),(1,'INT_N','ARM_N'),(2,'CARD_FAULT_N',None)):
    pn={'1':'SLOT_EXP_INT_N','2':'+3V3_SAFE' if a==2 else 'GND','3':'GND','21':'+3V3_SAFE' if a==1 else 'GND','22':'I2C2_SCL','23':'I2C2_SDA','24':'+3V3_SAFE','12':'GND'}
    for i in range(8):
        pn[str(4+i)]=f'SL{i+1}_{lo}'; pn[str(13+i)]=f'SL{i+1}_{hi}' if hi else None
    if a==2: pn.update({'13':'ENG_PRESENT_N','14':'BANK_EN','15':'BANK_FAULT_N','16':'BANK_OVL_ROOM','17':'BANK_OVL_N','18':'ENG_PWR_FAULT_N'})   # P13 out ROOM select, P14 in overload latch; P15 ENG_PWR_FAULT_N (Pass 6 M3); P16-P17 spare
    add(S,'Interface_Expansion:TCA9555PWR','U','C465732',pn,Value=f'TCA9555PWR @0x2{a}'); C(S,C100N,'+3V3_SAFE')
for i in range(1,9): R(S,R10K,f'SL{i}_CARD_FAULT_N','+3V3_SAFE')
R(S,R10K,'ENG_PRESENT_N','+3V3_SAFE',Description='engine card grounds c31: low = engine card present')
R(S,R10K,'SLOT_EXP_INT_N','+3V3_SAFE')
# slot ANA_OUT mux -> SLOT_ANA (MCU ADC, was MUXB_OUT)
add(S,'genctl:TMUX1208PWR','U','C494728',{'1':'MUX_A0','16':'MUX_A1','15':'MUX_A2','2':'SLOT_ANA_EN','13':'+3V3_SAFE','14':'GND','8':'SLOT_ANA','3':None,
    '4':'SL1_ANA_R','5':'SL2_ANA_R','6':'SL3_ANA_R','7':'SL4_ANA_R','12':'SL5_ANA_R','11':'SL6_ANA_R','10':'SL7_ANA_R','9':'SL8_ANA_R'}); C(S,C100N,'+3V3_SAFE')
R(S,R100K,'SLOT_ANA_EN','GND',Description='Pass 2 m1: U109 EN pull-down = all slot ANA switches open at MCU reset (PE13)')
for i in range(1,9): R(S,'C21190',f'SL{i}_ANA',f'SL{i}_ANA_R',Description='Pass 2 m1: 1k series, limits an unpowered or faulty slot into U109 to <= 3.3 mA')
# ---- per-slot power ----
S='slot_power'; blocks_sp=[]
# slot-bank limiter (M2/N13): one TPS48100 ahead of all 8 slot switches, VBAT_P -> VBAT_SLOTS. Trip 9.2/11.6/14.4 A (5 mOhm, 19.6k),
# C_TMR 10 nF + 100k = latch-off, tSC ~148 us (slots trip first at ~70 us = selectivity). INP1 = BANK_EN (0x22 P11, pull-down = off at reset)
refs=[]
refs.append(add(S,'genctl:TPS48100QDGXRQ1','U','C43131316',{'1':'BANK_UVLO','2':'GND','3':'BANK_EN','5':'BANK_FAULT_N','6':'GND','7':'GND','8':'BANK_ISCP','9':'BANK_TMR','10':'GND',
    '12':'BANK_BST','13':'VBAT_SLOTS','14':'BANK_GPD','15':'BANK_GPU','17':'BANK_DRN','18':'VBAT_P','20':'BANK_VS','4':None,'11':None,'19':None}))
refs.append(R(S,'C2903482','VBAT_P','BANK_DRN'))
for i in range(2): refs.append(add(S,'Transistor_FET:BSC070N10NS5','Q',FET,{'5':'BANK_DRN','1':'VBAT_SLOTS','2':'VBAT_SLOTS','3':'VBAT_SLOTS','4':'BANK_G'}))
refs+=gate_net(S,'BANK','VBAT_SLOTS')
refs+=vs_holdup(S,'BANK','VBAT_P')
refs+=[R(S,'C23091','BANK_ISCP','GND'),C(S,'C31658','BANK_TMR'),
       R(S,R100K,'BANK_TMR','GND',Description='latch-off (TPS48100 Eq 9); reset by toggling BANK_EN'),
       R(S,R100K,'VBAT_P','BANK_UVLO'),R(S,'C22967','BANK_UVLO','GND'),
       C(S,'C1621','BANK_UVLO','GND',Description='UVLO filter 4.7 nF: tau 100 us, dips <= 120 us cannot beat the SCP latch (Pass 3 MAJ-B)'),
       C(S,'C28233','VBAT_SLOTS',Description='U110 SRC cap 100 nF / 100 V (>= 22 nF: 63 nF worst at 32 V) (Pass 3 MAJ-D)'),
       R(S,R10K,'BANK_EN','GND',Description='slot bank off while the expander is in reset / inputs'),R(S,R10K,'BANK_FAULT_N','+3V3_SAFE')]
blocks_sp.append(('Bank limiter VBAT_P -> VBAT_SLOTS (SCP 21.2 A min, 466 us min), VS hold-up',refs))
# Pass 2 MAJ-2 / Pass 3 MAJ-A: hardware bank overload cutoff. INA281A2 on the bank shunt -> RC (tau 316 ms HOT / 195 ms ROOM) -> TLV3012B (V_TH 0.861 V)
# -> 74LVC1G74 ~SD (level set, POR-low = set) -> Q -> AO3400A pulls BANK_UVLO low (U110 off). Reset: BANK_EN low (~RD). Trip 3.15-3.76 A HOT, 5.11-6.08 A ROOM.
refs=[]
refs.append(add(S,'Amplifier_Current:INA281A2','U','C1517405',{'5':'+5V_TRIP','3':'VBAT_P','4':'BANK_DRN','2':'GND','1':'BANK_IMON'}))
refs+=[C(S,C100N,'+5V_TRIP'),R(S,'C22880','BANK_IMON','BANK_OVL_F'),C(S,'C14860','BANK_OVL_F'),C(S,'C14860','BANK_OVL_F'),R(S,'C22920','BANK_OVL_F','BANK_OVL_RX')]
refs.append(add(S,'cards:TS5A3166','U','C353035',{'1':'BANK_OVL_RX','2':'GND','3':'GND','4':'BANK_OVL_ROOM','5':'+5V_TRIP'},
    Description='ROOM select (0x22 P13 high): 25.5k in, trip 5.11-6.08 A; off (default, or unpowered) = HOT 3.15-3.76 A. NO leakage +/-100 nA. Rated 185 F (85 C): LAYOUT keep >= 15 mm from R760/Q106/Q107/U110 (Pass 4 m7)'))
refs.append(C(S,C100N,'+5V_TRIP'))
refs.append(R(S,R10K,'BANK_OVL_ROOM','GND',Description='10k: HOT by default against the TCA9555 internal pull-up, <= 0.55 V at reset (Pass 4 m2)'))
refs.append(add(S,'cards:TLV3012B','U','C20345924',{'6':'+5V_TRIP','2':'GND','3':'BANK_OVL_TH','4':'BANK_OVL_F','5':'BANK_OVL_REF','1':'BANK_OVL_TRIP_N'}))
refs+=[C(S,C100N,'+5V_TRIP'),R(S,'C23056','BANK_OVL_REF','BANK_OVL_TH'),R(S,R100K,'BANK_OVL_TH','GND')]
refs.append(add(S,'cards:74LVC1G74','U','C548409',{'1':'GND','2':'GND','7':'BANK_OVL_TRIP_N','6':'BANK_EN','5':'BANK_OVL','3':'BANK_OVL_N','8':'+3V3_SAFE','4':'GND'},
    Value='74LVC1G74DP-Q100H',Note='Pass 2 MAJ-2 bank overload latch. Symbol cards:74LVC1G74 (Pass 3 N13): DP pinout 1 CP, 2 D, 3 Q#, 4 GND, 5 Q, 6 RD#, 7 SD#, 8 VCC',Description='overload latch: ~SD = trip (level), ~RD = BANK_EN (firmware clears by toggling BANK_EN); ~Q -> 0x22 P14'))
refs+=[C(S,C100N,'+3V3_SAFE'),R(S,R100K,'BANK_OVL','GND',Description='keeps the UVLO FET off while +3V3_SAFE is down (Ioff output)')]
refs.append(add(S,'cards:AO3400A','Q','C20917',{'1':'BANK_OVL','2':'GND','3':'BANK_UVLO'},Description='overload latched: pulls U110 EN/UVLO < 0.3 V = bank off'))
blocks_sp.append(('Bank overload cutoff: INA281A2, RC, TLV3012B, 1G74 latch',refs))
def skip(prefix,n=1):   # Pass 5: removed TPS48100 slot parts still consume their designators so every kept ref is unchanged
    for _ in range(n): shared[prefix]+=1
for s in range(1,9):
    k=f'SL{s}'; refs=[]
    # Pass 5: TPS16630 eFuse replaces TPS48100 + 2x BSC070N10NS5 + 5 mOhm + gate network + VS hold-up (refs of removed parts retired)
    u=add(S,'cards:TPS16630PWPR','U','C1849461',{'1':'VBAT_SLOTS','2':'VBAT_SLOTS','3':'VBAT_SLOTS','6':'VBAT_SLOTS','7':f'{k}_UVLO','8':f'{k}_OVP','9':'GND','21':'GND',
        '10':f'{k}_DVDT','11':f'{k}_ILIM','12':None,'13':f'{k}_PWR_EN','14':f'{k}_IMON','15':f'{k}_PWR_FAULT_N','16':f'{k}_PWR_FAULT_N','18':f'{k}_VBAT','19':f'{k}_VBAT','20':f'{k}_VBAT',
        '4':None,'5':None,'17':None},
        Description='Slot eFuse: I_OL 5.42-6.23 A (3.09k; 5.36-6.30 A incl. 1 % R, Pass 6 M2), fast-trip 2x I_OL, SCP 45 A / 1 us, latch (MODE open), UVLO 5.64 V, OVP 55.6 V; FLT# and PGOOD wired-OR onto SLn_PWR_FAULT_N (Pass 5)'); refs.append(u)
    skip('R'); skip('Q',2); skip('R',2); skip('D'); skip('R'); skip('C'); skip('R'); skip('D',2); skip('C')   # shunt, FETs, gate_net
    refs+=[R(S,'C22992',f'{k}_ILIM','GND',Description='R_ILIM 3.09k 1 %: I_OL 5.36-6.30 A: a shorted 3.61 A channel leaves 1.75 A for the rest of the card (Pass 6 M2; was 4.02k)'),
           C(S,C10N,f'{k}_DVDT','GND',Description='C_dVdT 10 nF: 5 V/ms (2 uA x 25 / C), 32 V in 6.4 ms typ, ~14 mA into the 2.76 uF card load (Pass 5)')]
    skip('R')   # old TMR 100k
    refs+=[R(S,R100K,'VBAT_SLOTS',f'{k}_UVLO'),R(S,'C22967',f'{k}_UVLO','GND'),
           C(S,'C1621',f'{k}_UVLO','GND',Description='UVLO 100k/27k + 4.7 nF: on 5.64 V, off 5.28 V (TPS16630 1.20/1.12 V) (Pass 5)'),
           C(S,'C28233','VBAT_SLOTS',Description='VBAT_SLOTS local decoupling 100 nF / 100 V at this slot'),
           C(S,'C28233',f'{k}_VBAT',Description='SLn_VBAT 100 nF / 100 V at the eFuse OUT')]
    b=1000+10*s
    refs+=[R(S,'C25818','VBAT_SLOTS',f'{k}_OVP',ref=f'R{b+1}'),
           R(S,R10K,f'{k}_OVP','GND',ref=f'R{b+2}',Description='OVP 453k/10k: off at 53.4/55.6/57.8 V rising (1.176-1.224 V, 1 % R), on below 49.5-53.9 V, FLT# + PGOOD; far above 36 V, below the 60-62 V card parts (Pass 5)'),
           R(S,R10K,f'{k}_PWR_EN','GND',ref=f'R{b+4}',Description='PWR_EN pull-down 10k: SHDN# has an internal pull-up (2.48-3.3 V open, 10 uA): keeps the eFuse OFF if the 1G02 is unpowered/open (<= 0.1 V) (Pass 5)'),
           R(S,'C22809',f'{k}_IMON','GND',ref=f'R{b+3}',Description='IMON 15k: 0.42 V/A, test point only (no ADC channel; layout frozen) (Pass 5)'),
           C(S,'C170101','VBAT_SLOTS','GND',ref=f'C{600+10*s+1}',Description='eFuse IN 2.2 uF / 100 V X7R 1206 at pins 1-3: trip kick, VBAT_SLOTS <= 57 V pessimistic vs 67 V (Pass 5 kick_calc)'),
           add(S,'Device:D_Schottky','D','C14281',{'1':f'{k}_VBAT','2':'GND'},ref=f'D{300+s}',Description='SS310B OUT -> GND: holds OUT >= -0.85 V at turn-off of the card harness inductance (OUT abs min -0.3 V DC; TI 10.2.1) (Pass 5)')]
    u3=add(S,'genctl:TPS2553DBVR','U','C55266',{'1':'+3V3','2':'GND','3':f'{k}_PWR_EN','4':f'{k}_PWR_FAULT_N','5':f'{k}_ILIM3','6':f'{k}_3V3'})
    refs+=[u3,R(S,'C22952',f'{k}_ILIM3','GND'),C(S,C100N,f'{k}_3V3')]
    g1=add(S,'cards:74LVC1G02','U','C7394016',{'1':f'{k}_EN_N','2':f'{k}_PRESENT_N','3':'GND','4':f'{k}_PWR_EN','5':'+3V3_SAFE'})
    g2=add(S,'cards:74LVC1G04','U','C7827',{'2':f'{k}_ARM_N','1':None,'3':'GND','4':f'{k}_ARM','5':'+3V3_SAFE'})
    g3=add(S,'cards:74LVC1G10','U','C403721',{'1':f'{k}_PWR_EN','3':'GLOBAL_OUT_ALLOW','6':f'{k}_ARM','2':'GND','4':f'{k}_OUT_EN_N','5':'+3V3_SAFE'})
    refs+=[g1,g2,g3,C(S,C100N,'+3V3_SAFE'),C(S,C100N,'+3V3_SAFE'),C(S,C100N,'+3V3_SAFE'),
           R(S,R10K,f'{k}_EN_N','+3V3_SAFE'),R(S,R10K,f'{k}_PRESENT_N','+3V3_SAFE'),R(S,R10K,f'{k}_PWR_FAULT_N','+3V3_SAFE'),R(S,R10K,f'{k}_INT_N','+3V3_SAFE'),
           R(S,R10K,f'{k}_ARM_N','+3V3_SAFE',Description='ARM_N high (expander input at reset) = outputs disarmed'),
           R(S,'C17976','+3V3_SAFE',f'{k}_3V3_ID',Description='+3V3_ID always on via 68R 1206 (EEPROM + OUT_EN_N / ID_WP pull-ups only)')]
    blocks_sp.append((f'Slot {s}: TPS16630 eFuse 5.36-6.30 A limit, 1 us SCP, latch, OVP 55.6 V, +3V3, PWR_EN / ARM / OUT_EN_N',refs))
R('estop','C17969','D120_K','U65_IN',ref='R1002',Description='Pass 5: 47R 1206 ahead of C225/U65 (TPS7B6950 45 V abs max): with C225 limits the VBAT kick at U65 IN to <= 31.8 V')
# ---- Pass 6 B1 (Ethan): Q2 hold-off. BAT_IN - VBAT_P > ~3 V (Q2 still in its linear ramp) holds U2 (BB_UVLO) and U5 (U5_EN) off.
# BAT_IN -> 1N4148W (reverse battery) -> MMBT5401 E; 22k E-B / 68k B -> VBAT_P sets Vth = Vf + Veb x 90/22 (2.5-3.8 V);
# collector -> 22k -> filter node (100 nF || 100k, 46-270 us: ignores us kicks and bank inrush) = MMBT3904 base; its collector pulls
# BB_UVLO and U5_EN low through a BAT54C (<= 0.45 V). Releasing re-arms C602 (now 1 uF) from ~0.45 V: U2 back 1.3-17 ms later. Math: docs/modular/pass6_fix_calc.txt.
S='estop'
add(S,'Diode:1N4148W','D','C81598',{'2':'BAT_IN','1':'HO_E'},ref='D401',Description='Pass 6 hold-off: blocks reverse battery and the VBAT_P > BAT_IN case (crank) from the PNP E-B junction')
add(S,'Transistor_BJT:MMBT3906','Q','C8326',{'1':'HO_B','2':'HO_E','3':'HO_C'},ref='Q121',Description='Pass 6 hold-off sense PNP MMBT5401 (150 V): on when BAT_IN - VBAT_P > ~3 V')
R(S,'C31850','HO_E','HO_B',ref='R1121',Description='Pass 6 hold-off E-B 22k (threshold divider)')
R(S,'C23231','HO_B','VBAT_P',ref='R1122',Description='Pass 6 hold-off base 68k to VBAT_P: Vth = Vf + Veb x (68k+22k)/22k = 2.5-3.8 V')
R(S,'C31850','HO_C','HO_F',ref='R1123',Description='Pass 6 hold-off collector 22k into the filter node')
R(S,R100K,'HO_F','GND',ref='R1124',Description='Pass 6 hold-off filter bleed 100k')
C(S,C100N,'HO_F','GND',ref='C1121',Description='Pass 6 hold-off filter 100 nF: 46 us (32 V) to 270 us (8 V, cold) before U2/U5 are pulled off')
add(S,'Transistor_BJT:MMBT3904','Q','C20526',{'1':'HO_F','2':'GND','3':'HO_K'},ref='Q122',Description='Pass 6 hold-off pull-down NPN')
add(S,'Diode:BAT54C','D','C37704',{'1':'BB_UVLO','2':'U5_EN','3':'HO_K'},ref='D402',Description='Pass 6 hold-off: pulls U2 EN/UVLO (BB_UVLO, discharges C602) and U5 EN to <= 0.45 V')
R(S,R100K,'VBAT_P','U5_EN',ref='R1125',Description='Pass 6: U5 EN/UVLO pull-up 100k (was strapped to VIN)')
R(S,'C25819','U5_EN','GND',ref='R1126',Description='Pass 6: U5 EN/UVLO 47k: U5 on above VBAT_P 4.25 V (1.36 V max x 147/47), off below 2.5 V; EN <= 18 V at a 57 V kick')
# ---- Pass 6 M3 (Ethan): engine slot feeds. J48 a13/c13 = ENG_3V3_SAFE via TPS2553 (110-150 mA, auto-retry, FAULT -> 0x22 P15),
# J48 a12/c12 = ENG_VBAT_P via a TPS16630 eFuse (engine card VBAT_P load <= 0.13 A: D+ excitation LM317 current source).
S='backplane'
add(S,'genctl:TPS2553DBVR','U','C55266',{'1':'+3V3_SAFE','2':'GND','3':'+3V3_SAFE','4':'ENG_PWR_FAULT_N','5':'ENG_ILIM3','6':'ENG_3V3_SAFE'},ref='U160',
    Description='Pass 6 M3: engine card +3V3_SAFE limiter, 110-150 mA (210k), auto-retry; engine card load <= 15 mA')
R(S,'C22952','ENG_ILIM3','GND',ref='R1101',Description='Pass 6 M3: TPS2553 ILIM 210k = 110/130/150 mA (SLVS841 table)')
C(S,C100N,'+3V3_SAFE','GND',ref='C1101',Description='Pass 6 M3: U160 IN 100 nF')
C(S,C100N,'ENG_3V3_SAFE','GND',ref='C1102',Description='Pass 6 M3: U160 OUT 100 nF')
R(S,R10K,'ENG_PWR_FAULT_N','+3V3_SAFE',ref='R1102',Description='Pass 6 M3: ENG_PWR_FAULT_N pull-up (U160 FAULT, 0x22 P15)')
# Pass 6 M3 engine VBAT_P: TPS16630 eFuse (same part as the slots) instead of a PTC: a PTC sees ~100 A prospective (> its 40 A I_max) and
# its <= 1 ms trip can drop BAT_IN - VBAT_P past the B1 hold-off threshold; the eFuse cuts in 1 us (SCP 45 A) and limits at 0.54-0.66 A.
add(S,'cards:TPS16630PWPR','U','C1849461',{'1':'VBAT_P','2':'VBAT_P','3':'VBAT_P','6':'VBAT_P','7':'ENG_UVLO','8':'ENG_OVP','9':'GND','21':'GND',
    '10':'ENG_DVDT','11':'ENG_ILIM','12':'GND','13':None,'14':None,'15':'ENG_PWR_FAULT_N','16':'ENG_PWR_FAULT_N','18':'ENG_VBAT_P','19':'ENG_VBAT_P','20':'ENG_VBAT_P',
    '4':None,'5':None,'17':None},ref='U161',
    Description='Pass 6 M3: engine card VBAT_P eFuse, I_OL 0.54-0.66 A (30k) vs <= 0.13 A load, fast-trip 2x I_OL, SCP 45 A / 1 us, MODE = GND auto-retry (648 ms), SHDN# open (internal pull-up = on), FLT#/PGOOD -> ENG_PWR_FAULT_N')
R(S,'C22984','ENG_ILIM','GND',ref='R1103',Description='Pass 6 M3: U161 R_ILIM 30k = I_OL 0.54/0.60/0.66 A (SLVSET9G table row)')
R(S,R100K,'VBAT_P','ENG_UVLO',ref='R1104'); R(S,'C22967','ENG_UVLO','GND',ref='R1105',Description='Pass 6 M3: U161 UVLO 100k/27k: on 5.64 V, off 5.28 V (as the slots)')
C(S,'C1621','ENG_UVLO','GND',ref='C1103',Description='Pass 6 M3: U161 UVLO 4.7 nF')
R(S,'C25818','VBAT_P','ENG_OVP',ref='R1106'); R(S,R10K,'ENG_OVP','GND',ref='R1107',Description='Pass 6 M3: U161 OVP 453k/10k: off 53.4-57.8 V (as the slots)')
C(S,C10N,'ENG_DVDT','GND',ref='C1104',Description='Pass 6 M3: U161 dVdT 10 nF: 5 V/ms output ramp')
C(S,'C170101','VBAT_P','GND',ref='C1105',Description='Pass 6 M3: U161 IN 2.2 uF / 100 V at pins 1-3')
C(S,'C28233','ENG_VBAT_P','GND',ref='C1106',Description='Pass 6 M3: U161 OUT 100 nF / 100 V')
add(S,'Device:D_Schottky','D','C14281',{'1':'ENG_VBAT_P','2':'GND'},ref='D403',Description='Pass 6 M3: SS310B OUT -> GND: holds U161 OUT >= -0.85 V at turn-off')
# ---- Pass 6 M3: engine lines that went straight to U7: series R at the MCU (+ BAT54S clamp to +3V3_SAFE/GND on the MCU side)
S='mcu'
R(S,'C21190','DPLUS_SNS','DPLUS_SNS_M',ref='R1111',Description='Pass 6 M3: 1k after the existing D65 clamp (card side already 100k)')
for i,n in enumerate(('FUEL_ISNS','CRANK_ISNS','MPU_GATE','MPU_SPEED','DPLUS_EXC_EN','DIAG_EN')):
    R(S,'C17414',n,n+'_M',ref=f'R{1112+i}',Description='Pass 6 M3: 10k 0805 series: a card fault at 36 V injects <= 3.3 mA (0.11 W) into the clamp, not the pin')
    add(S,'Diode:BAT54S','D','C8592',{'1':'GND','2':'+3V3_SAFE','3':n+'_M'},ref=f'D{411+i}',Description='Pass 6 M3: MCU-side clamp, Schottky to +3V3_SAFE / GND')
for i,n in enumerate(('FUEL_ISNS','CRANK_ISNS')):
    C(S,'C1588',n+'_M','GND',ref=f'C{1111+i}',Description='Pass 6 M3: 1 nF ADC hold-up cap behind the 10k (tau 10 us)')
add('io_core','Diode:BAT54C','D','C37704',{'1':'GLOW_SNSM','2':'ESTOP_TRIP_SNSM','3':'+3V3_SAFE'},Description='Relocated clamp: GLOW_SNSM + ESTOP_TRIP_SNSM (replaces D128 glow half / D135)')
R('io_core',R10K,'EXP25_P12_SPARE','+3V3_SAFE',Description='U76 P12 (was AUX10_RB_N) spare input pull-up')
# ---------------- global vs local labels ----------------
where=collections.defaultdict(set)
for f,c in cards.items():
    for p in c.parts:
        for n in p['pn'].values():
            if n: where[n].add(f)
for f in KEEP_SHEETS:
    s=open(os.path.join(ROOT,f+'.kicad_sch')).read()
    for n in re.findall(r'\(global_label "([^"]+)"',s): where[REN.get(n,n)].add(f)
where['EXP25_P12_SPARE'].add('frontpanel')
GL={n for n,w in where.items() if len(w)>1 and n not in RAILS}
# J31 pins are 2.54 mm apart: local-label text sits above its wire and touches the next flag, so draw every J31 net as a (centred) global label
GL|={n for p in card('mtr_if').parts if p['ref']=='J31' for n in p['pn'].values() if n and n not in RAILS}
# local nets that only lived in one baseline sheet but now meet across sheets are global too (above); report singles
single=collections.Counter()
for c in cards.values():
    for p in c.parts:
        for n in p['pn'].values():
            if n: single[n]+=1
def blocks_for(f,c):
    keys=[(p['ref'],p['unit']) for p in c.parts]
    if f=='slot_power':
        return [(t,[(r,1) for r in refs]) for t,refs in blocks_sp]
    if f=='backplane':
        conn=[(p['ref'],p['unit']) for p in c.parts if p['lib_id']=='cards:DIN41612_C96']
        rest=[k for k in keys if k not in conn]
        return [('ENGINE slot (keyed) + LV slots 1-8 sockets, DIN 41612 C96 female',conn),('ID muxes 0x70/0x71, slot CS decoder, expanders 0x20-0x22, ID_WP FET, ANA_OUT mux',rest)]
    # one block per IC/connector: the IC + 2-pin parts reachable through small non-rail nets without crossing another IC
    two={p['ref'] for p in c.parts if len({pp['num'] for pp in p['pins']})<=2}
    nets_of=collections.defaultdict(set); refs_on=collections.defaultdict(set)
    for p in c.parts:
        for n in p['pn'].values():
            if n and n not in RAILS: nets_of[p['ref']].add(n); refs_on[n].add(p['ref'])
    val={p['ref']:p['props'].get('Value','') for p in c.parts}
    heads=sorted({p['ref'] for p in c.parts}-two,key=lambda r:(-len(nets_of[r]),r))
    owner={}
    for h in heads:
        todo=[h]; seen={h}
        while todo:
            x=todo.pop()
            for n in nets_of[x]:
                if len(refs_on[n])>=9: continue
                for y in refs_on[n]:
                    if y in two and y not in owner and y not in seen: seen.add(y); owner[y]=h; todo.append(y)
    out=[]
    for h in heads:
        mem={h}|{y for y,o in owner.items() if o==h}
        out.append((f'{h} {val[h][:40]}',[k for k in keys if k[0] in mem]))
    rest=[k for k in keys if k[0] in two and k[0] not in owner]
    if rest: out.append(('Decoupling, bulk caps and rail-to-rail passives',rest))
    return out
NOTES={'mcu':['Regenerated from the baseline netlist (tag baseline-2026-11-23-locked) with the Phase 2 pin re-use: PC10/PC11/PC12 = SPI3 SCK/MISO/MOSI (AF6) slot bus, SCK/MOSI through 33R source resistors; PE0/PE1/PD11 = slot CS decoder A0-A2, PD13 = decoder enable (100k pull-down = no slot selected); PC9 = SLOT_RST_N via 33R (100k pull-down = slots held in reset, also forces GLOBAL_OUT_ALLOW low); PB4 = SLOT_EXP_INT_N; PB5 = ID_MUX_RST_N (10k pull-up on the backplane: muxes run at MCU reset, pulse low to recover a stuck ID bus); PB6 = ID_WP_UNLOCK (100k pull-down, drives the ID_WP FET); PB7 = RC_ALLOW (100k pull-down: rail cut off until firmware allows it); PB10/PB11 = I2C2 SCL/SDA (AF4, DS12110 rev 10) for the slot ID bus; PC1 (pin 16, ADC123_INP11; was MUXB_OUT) = SLOT_ANA; PE13 = SLOT_ANA_EN (U109 EN, 100k pull-down); MUX_A0-2 100k pull-downs. Baseline sheet notes: docs/modular/mainboard_sheet_notes.md.','Pass 6 M3: the engine-slot lines that reached U7 directly now pass a series resistor at the MCU: DPLUS_SNS 1k (after the D65 clamp), FUEL_ISNS / CRANK_ISNS / MPU_GATE / MPU_SPEED / DPLUS_EXC_EN / DIAG_EN 10k 0805 with a BAT54S clamp to +3V3_SAFE/GND on the MCU side (36 V card fault -> <= 3.3 mA); ISNS lines add 1 nF (tau 10 us, ADC sample time >= 64.5 cycles, FW_REQ C8). Math: docs/modular/pass6_fix_calc.txt.'],
 'estop':['J23 E-stop feed -> SMDJ36CA TVS -> LM74700-Q1 ideal diode + BSC070N10NS5 (reverse battery to -65 V) -> VBAT_ESTOP_PRE: E-stop status sense (R251 -> U34), trip driver bias (R400). Rail cut TPS48100 + 2x BSC070N10NS5 + 2 mOhm (trip 15.8/20/24.8 A), latch-off (100k across C_TMR), enabled by WD_OK AND ESTOP_OK AND RC_ALLOW (74LVC1G11) -> VBAT_ESTOP: engine slot (fuel/crank/glow) and ADC readback R411. Re-arm after a trip: firmware toggles RC_ALLOW (PB7). Switched bleeder: RC_EN low -> AO3400A off -> IRLML0100 gate to +5V_TRIP -> 1.1k (2x 2.2k 2512 1 W) on VBAT_ESTOP: tau ~2 ms, 32 V -> 2 V in <= 6.6 ms; stuck-on rail-cut FETs at 32 V = 0.47 W per resistor. Replaces Q70/Q71 SQD40P10-40L, D137, R627.','Pass 6 B1 Q2 hold-off: BAT_IN -> 1N4148W -> MMBT5401 (22k E-B, 68k to VBAT_P: on when BAT_IN - VBAT_P > 2.5-3.8 V) -> 22k -> 100 nF || 100k (46-270 us) -> MMBT3904 -> BAT54C pulls BB_UVLO (U2 EN/UVLO, discharges C602 1 uF in <= 0.25 ms; C602 was 10 uF) and U5_EN (U5 EN/UVLO, 100k/47k from VBAT_P) to <= 0.45 V while Q2 is still ramping. Math: docs/modular/pass6_fix_calc.txt.'],
 'io_core':['What stays of the baseline inputs + outputs sheets after the card split. Free U62 inputs read SL1-8_PRESENT_N; U63 S1 GLOW_SNSM, S2 ESTOP_TRIP_SNSM (new BAT54C clamp next to U63), S3-S8 GND. U30 AIN1-3 / U29 AIN2 unused (AI-4 card). U91 gates 3-4 and U92 gates 1-2 unused (inputs GND); U92 gate 4 = GLOBAL_OUT_ALLOW = SH_ALLOW (WD_OK AND NRST_S) AND SLOT_RST_N. Baseline sheet notes: docs/modular/mainboard_sheet_notes.md.'],
 'backplane':['Universal LV pinout docs/modular/slot_pinout_LV.csv; engine pinout cards/engine/engine_slot_pinout.csv. Slot ID straps: slot n = ID n-1, 0 = GND, 1 = open (card pull-up); IDP makes ID0..2+IDP odd. ID_WP is high (protected); PB6 -> AO3400A pulls it low for factory/calibration writes (all LV slots + engine). Expanders on I2C2: 0x20 P0 EN_N / P1 PWR_FAULT_N (eFuse FLT#/PGOOD + TPS2553 FAULT), 0x21 P0 INT_N / P1 ARM_N, 0x22 P0 CARD_FAULT_N, P10 ENG_PRESENT_N, P11 BANK_EN, P12 BANK_FAULT_N, P13 BANK_OVL_ROOM (out), P14 BANK_OVL_N (in). Slot ANA_OUT -> 1k -> U109 (EN = PE13 SLOT_ANA_EN, 100k pull-down).','Pass 6 M3: J48 a13/c13 = ENG_3V3_SAFE through U160 TPS2553 (210k: 110-150 mA, auto-retry, FAULT -> ENG_PWR_FAULT_N on 0x22 P15); J48 a12/c12 = ENG_VBAT_P through U161 TPS16630 eFuse (30k: 0.54-0.66 A vs <= 0.13 A load, 1 us short cut, auto-retry, FLT#/PGOOD -> ENG_PWR_FAULT_N). A cracked cap or bent pin on the engine card no longer collapses +3V3_SAFE or blows F1.'],
 'slot_power':['Bank TPS48100 VBAT_P -> VBAT_SLOTS: 5 mOhm + 61.9k = SCP 21.2/28.6/36.3 A, 68 nF + 100k latch-off 466-1490 us (>100x the 1-4.5 us slot eFuse trip). Hardware overload cutoff: INA281A2 -> 15.8k / 2x 10 uF -> TLV3012B -> 74LVC1G74 latch -> AO3400A pulls U110 UVLO low; trip 3.15-3.76 A HOT (default; R773 10k holds P13 low at reset) or 5.11-6.08 A ROOM (TS5A3166 adds 25.5k, 0x22 P13); clear by toggling BANK_EN. U112 TS5A3166 is an 185 F (85 C) part: keep it >= 15 mm from R760/Q106/Q107/U110.',
  'Each slot (Pass 5): TPS16630 eFuse, no per-slot blade fuse. ILIM 3.09k = I_OL 5.36-6.30 A (Pass 6 M2; was 4.02k), fast trip 2x I_OL, hard short 45 A / 1 us, MODE open = latch (reset by SHDN#). OVP 453k/10k: off 53.4-57.8 V. UVLO 100k/27k/4.7 nF. dVdT 10 nF (32 V in 5-8.4 ms). IMON 15k test point. 10k pull-down on SHDN# (PWR_EN). 2.2 uF / 100 V at IN, SS310B OUT -> GND at the pins. Bank VS hold-up (Pass 4): VBAT_P -> 1N4148W -> 100R -> VS, 1 uF / 100 V.',
  'Bank gate network: 470R G1PU; 0R G1PD (fitted); 2.2 nF C1 diode-steered (1N4148W + 10R, 1M bleed to SRC); 1N4148W gate -> BST clamp; BZT52C15 K = gate, A = source; C_BST 2.2 uF / 50 V. UVLO nodes 4.7 nF; 100 nF / 100 V on VBAT_SLOTS and every SLn_VBAT. TPS2553 210k; its FAULT, eFuse FLT# and eFuse PGOOD are wired-OR onto SLn_PWR_FAULT_N.',
  'PWR_EN = NOT EN_N AND NOT PRESENT_N (1G02); OUT_EN_N = NAND(PWR_EN, GLOBAL_OUT_ALLOW, NOT ARM_N) (1G04 + 1G10). +3V3_ID via 68R 1206. Math: MODULAR_ARCHITECTURE sections 15-17, docs/modular/pass3_calc.txt, pass4_calc.txt, pass5_calc.txt, kick_calc.txt.'],
 'mtr_if':['J31.12 / J31.16 now carry MTR_ID_SCL / MTR_ID_SDA from ID mux 0x71 channel 1 (HV meter AT24CS32), matching J32.12 / J32.16 on genctl_meter. No spare harness pin for the meter WP: it stays on the meter TP3 bench pad.']}
def write_root():
    fn=os.path.join(ROOT,'genctl.kicad_sch'); t=open(fn).read()
    t=re.sub(r'\(sheet \(at [^\n]*\n','',t)
    ent=[]; pages=['power','mcu','cm5','comms','display','io_core','backplane','slot_power','estop','mtr_if','frontpanel']
    names={'power':'Power: input protection, ideal diode, 12V buck-boost, 5V, 3V3','cm5':'Raspberry Pi CM5','comms':'Comms: CAN x2, RS-485, Ethernet, USB hub/ports, router 12V',
           'display':'Display: DSI->LVDS bridge, panel power, backlight, touch','frontpanel':'Front panel: backlit buttons, buzzer'}
    for i,f in enumerate(pages):
        uid=KEEP_SHEETS.get(f) or SHEETS[f][0]; nm=names.get(f) or SHEETS[f][1]
        x=20+80*(i%4); y=40+45*(i//4)
        ent.append(f'(sheet (at {x} {y}) (size 60 25) (fields_autoplaced yes) (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0000)) (uuid "{uid}")'
          f'(property "Sheetname" "{nm}" (at {x} {y-0.7} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))'
          f'(property "Sheetfile" "{f}.kicad_sch" (at {x} {y+25.6} 0) (effects (font (size 1.27 1.27)) (justify left top)))'
          f'(instances (project "genctl" (path "/{ROOTUUID}" (page "{i+2}")))))')
    t=re.sub(r'\(text "All inter-sheet[^\n]*\n','',t)
    t=re.sub(r'\(rev "[^"]*"\)','(rev "M-mod P6")',t,count=1)   # Pass 6: root sheet Rev
    k=t.index('(sheet_instances')
    t=t[:k]+'\n'.join(ent)+'\n(text "All inter-sheet nets are global labels (names identical across sheets). Rails use power symbols.\\nPhase 2 (modular): io_core/backplane/slot_power/estop/mcu/mtr_if regenerated by cards/tools/mainboard.py from tag baseline-2026-11-23-locked; inputs/outputs retired." (exclude_from_sim no) (at 20 190 0) (effects (font (size 2 2)) (justify left top)) (uuid "20faa0b2-3e04-4a28-b429-178a5abb4d04"))\n'+t[k:]
    open(fn,'w').write(t)
    fp=os.path.join(ROOT,'frontpanel.kicad_sch'); t=open(fp).read()
    for a,b in (('AUX9_MCU','EXP25_P07_SPARE'),('AUX10_MCU','EXP25_P10_SPARE'),('AUX10_RB_N','EXP25_P12_SPARE')):
        t=t.replace(f'(global_label "{a}"',f'(global_label "{b}"')
    open(fp,'w').write(t)
if __name__=='__main__':
    PROJ={p['ref'] for c in cards.values() for p in c.parts}
    for f in KEEP_SHEETS:
        PROJ|=set(re.findall(r'\(property "Reference" "([^#"][^"]*)"',open(os.path.join(ROOT,f+'.kicad_sch')).read()))
    for c in cards.values(): c.project_refs=PROJ
    FLAGS={'U7_VBAT','VDDA_F','VBAT_ESTOP_PRE','VBAT_ESTOP_IN','VBAT_ESTOP','D120_K','U65_IN','VBAT_SLOTS','BANK_VS'}|{f'SL{i}_VS' for i in range(1,9)}; flagged=set()   # Pass 4: VS hold-up nodes are fed through 1N4148W+100R (passive)
    for f,c in cards.items():
        uid,title,paper=SHEETS[f]
        here={n for p in c.parts for n in p['pn'].values() if n}; fl=(FLAGS-flagged)&here; flagged|=fl
        for paper in ('A3','A2','A1','A0'):   # smallest sheet that packs without overflow
            c.paper=paper; D=schdraw.Drawer(c,RAILS,blocks_for(f,c),paper,NOTES.get(f,[]))
            D.labels_only={p['ref'] for p in c.parts if p['lib_id'].startswith(('cards:DIN','Connector'))}; D.pad=1
            D.path=f'{ROOTUUID}/{uid}'; D.proj='genctl'; D.glabels=GL; schdraw.GLOBALS=GL; D.noflags=True; D.flagnets=fl; D.flagtitle='PWR_FLAG'
            over=schdraw.run(D,ROOT,title)
            if not over: break
        SHEETS[f]=(uid,title,paper)
        print(f,'parts',len({p['ref'] for p in c.parts}),'overflow',over,'left',len(D.left))
    write_root()
    json.dump(dict(removed_p1=REMOVED_P1,removed_p2=REMOVED_P2,removed_p3=REMOVED_P3,ov={f'{a}.{b}':v for (a,b),v in OV.items()},ren=REN,sheet={r:f for r,f in ASSIGN_SHEET.items()}),
              open(os.path.join(ROOT,'docs/modular/mainboard_rework.json'),'w'),indent=1)
