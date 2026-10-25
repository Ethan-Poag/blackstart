from gen import ic as _ic
# Electrical pin types per symbol (codes: W power_in, w power_out, I input, O output, B bidir, C open-drain, T tri-state, N no-connect; default passive)
TYPES={
 'LM74800QDRRRQ1':dict(RTN='N',A='W',VS='W',VSNS='I',OV='I',GND='W',DGATE='O',HGATE='O',**{'EN/UVLO':'I'}),
 'LM5176PWPR':dict(VIN='W',VISNS='I',MODE='I',FB='I',VOSNS='I',AGND='W',HDRV1='O',HDRV2='O',LDRV1='O',LDRV2='O',CS='I',CSG='I',PGOOD='C',VCC='w',BIAS='W',PGND='W',**{'EN/UVLO':'I','RT/SYNC':'I','ISNS+':'I','ISNS-':'I'}),
 'TPS56637RPAR':dict(VIN='W',EN='I',MODE='I',FB='I',AGND='W',PGND='W',PG='C',NC='N'),
 'TPS3431SDRBR':dict(EP='W',VDD='W',EN='I',SET1='I',WDI='I',GND='W',WDO='C',ENOUT='O'),
 'TPS61500PWPR':dict(VIN='W',EN='I',DIMC='I',AGND='W',OVP='I',FB='I',PGND='W'),
 'TPS2553DBVR':dict(IN='W',GND='W',EN='I',FAULT='C',ILIM='P',OUT='w'),
 'TPS22918DBVR':dict(VIN='W',ON='I',GND='W',VOUT='w'),
 'TLV75518PDBVR':dict(IN='W',EN='I',GND='W',OUT='w',NC='N'),
 'TPS7B6950QDBVRQ1':dict(IN='W',GND='W',OUT='w',NC='N'),
 'TPS1H200AQDGNRQ1':dict(VS='W',IN='I',DIAG_EN='I',GND='W',FAULT='C'),
 'TPS1HTC30QPWPRQ1':dict(EP='W',VS='W',EN='I',DIAG_EN='I',LATCH='I',GND='W',FAULT='C',NC='N'),
 'TPS48100QDGXRQ1':dict(VS='W',INP1='I',INP2='I',CS_SEL='I',SCP_TEST='I',ISCP='I',TMR='I',GND='W',NC='N',G1PU='O',G1PD='O',G2='O',FLT='C',**{'EN/UVLO':'I','CS+':'I','CS-':'I'}),
 'TMUX1208PWR':dict(A0='I',A1='I',A2='I',EN='I',VDD='W',GND='W',NC='N'),
 'SN74LVC541APWR':dict(VCC='W',GND='W',**{'~{OE1}':'I','~{OE2}':'I'},**{'A%d'%i:'I' for i in range(1,9)},**{'Y%d'%i:'T' for i in range(1,9)}),
 'SN65DSI83ZXHR':dict(SCL='I',SDA='B',ADDR='I',EN='I',IRQ='O',REFCLK='I',VCC='W',VCORE='W',GND='W',NC='N',**{k:'I' for k in 'DA0P DA0N DA1P DA1N DA2P DA2N DA3P DA3N DACP DACN'.split()},**{k:'O' for k in 'A_Y0P A_Y0N A_Y1P A_Y1N A_Y2P A_Y2N A_Y3P A_Y3N A_CLKP A_CLKN'.split()}),
 'CA-IS3062W':dict(**{'11':'W','16':'w'},VCC='W',TXD='I',RXD='O',GND1='W',NC='N',VISO='w',CANH='B',CANL='B',GND2='W'),
 'CA-IS2092W':dict(VCC='W',DI='I',RO='T',DE='I',GNDA='W',VISO='w',SEL='I',A='B',B='B',GNDB='W',NC='N',**{'~{RE}':'I'}),
 'ADE9000ACPZ':dict(CLKIN='I',CLKOUT='O',VDD='W',PULL_HIGH='I',AVDDOUT='w',DVDDOUT='w',SCLK='I',MOSI='I',MISO='T',PM0='I',PM1='I',DGND='W',REFGND='W',AGND='W',GND='W',
     **{'~{SS}':'I','~{RESET}':'I','~{IRQ0}':'C','~{IRQ1}':'C','CF1':'O','CF2':'O','CF3/ZX':'O','CF4/EVENT':'O'},**{k:'I' for k in 'IAP IAN IBP IBN ICP ICN INP INN VAP VAN VBP VBN VCP VCN'.split()}),
 'ISOW7841DWE':dict(VCC='W',INA='I',INB='I',INC='I',OUTD='O',NC='N',GND1='W',VISO='w',OUTA='O',OUTB='O',OUTC='O',IND='I',SEL='I',GND2='W'),
 'ISO7741DW':dict(VCC1='W',INA='I',INB='I',INC='I',OUTD='O',EN1='I',GND1='W',VCC2='W',OUTA='O',OUTB='O',OUTC='O',IND='I',EN2='I',GND2='W'),
 'M.2_KeyB_Modem':{'3.3V':'W'},
 'CR2032_Holder':{'+':'w'},
 'LMR36506RRPER':dict(PGOOD='C',VIN='W',FB='I',GND='W',RT='I',VCC='w',**{'EN/UVLO':'I'}),
 'USB3_A_Receptacle':{},
 'AC1005':{'3':'N'},
 'TPS2121RUXR':dict(**{'8':'P'},IN1='W',IN2='W',OUT='w',GND='W',PR1='I',CP2='I',OV1='I',OV2='I'),
 'TPS61023DRLR':dict(VIN='W',EN='I',FB='I',GND='W',VOUT='w'),
 'TPS2116DRLR':dict(**{'7':'P'},GND='W',VOUT='w',VIN1='W',VIN2='W',PR1='I',MODE='I',ST='C'),
}
def ic(name,*a,**k): return _ic(name,*a,types=TYPES.get(name),**k)
def P(*a): return [(str(x[0]),x[1]) if x else None for x in a]
def mk(nums_names): return [(str(n),nm) for n,nm in nums_names]

ic('LM74800QDRRRQ1', P((2,'A'),(10,'VS'),(3,'VSNS'),(4,'SW'),(6,'EN/UVLO'),(5,'OV'),(7,'GND')),
   P((1,'DGATE'),(12,'C'),(8,'HGATE'),(9,'OUT'),(11,'CAP'),(13,'RTN')), desc='Ideal diode controller w/ load-dump protection, WSON-12. EP (13) = RTN: leave floating per DS Table 6-1', mfr='TI', mpn='LM74800QDRRRQ1',
   fp='genctl:LM74800_WSON-12_3x3', lcsc='C3215600')
ic('LM5176PWPR', P((2,'VIN'),(3,'VISNS'),(1,'EN/UVLO'),(4,'MODE'),(5,'DITH'),(6,'RT/SYNC'),(7,'SLOPE'),(8,'SS'),(9,'COMP'),(11,'FB'),(12,'VOSNS'),(14,'ISNS+'),(13,'ISNS-'),(10,'AGND'),(29,'EP')),
   P((27,'HDRV1'),(26,'BOOT1'),(28,'SW1'),(25,'LDRV1'),(19,'HDRV2'),(20,'BOOT2'),(18,'SW2'),(21,'LDRV2'),(16,'CS'),(15,'CSG'),(17,'PGOOD'),(23,'VCC'),(24,'BIAS'),(22,'PGND')),
   desc='4-switch buck-boost controller, HTSSOP-28', mfr='TI', mpn='LM5176PWPR', lcsc='C442493', fp='Package_SO:HTSSOP-28-1EP_4.4x9.7mm_P0.65mm_EP2.85x5.4mm')
ic('TPS56637RPAR', P((8,'VIN'),(1,'EN'),(10,'MODE'),(2,'FB'),(3,'AGND'),(9,'PGND')), P((7,'BOOT'),(6,'SW'),(4,'PG'),(5,'NC')),
   desc='4.5-28V 6A sync buck, VQFN-HR-10', mfr='TI', mpn='TPS56637RPAR', fp='genctl:TPS56637_VQFN-HR-10_RPA', lcsc='C841386')
ic('TPS3431SDRBR', P((1,'VDD'),(3,'EN'),(5,'SET1'),(2,'CWD'),(6,'WDI'),(4,'GND'),(9,'EP')), P((7,'WDO'),(8,'ENOUT')),
   desc='Standard programmable window watchdog, VSON-8 DRB; EP (9) to GND', mfr='TI', mpn='TPS3431SQDRBRQ1', fp='genctl:TPS3431_VSON-8_DRB', lcsc='C2878091')
ic('TPS61500PWPR', P((3,'VIN'),(4,'EN'),(6,'DIMC'),(5,'SS'),(10,'FREQ'),(8,'COMP'),(7,'AGND'),(15,'EP')), P((1,'SW'),(2,'SW'),(11,'OVP'),(9,'FB'),(12,'PGND'),(13,'PGND'),(14,'PGND')),
   desc='3A boost WLED driver, HTSSOP-14 PowerPAD', mfr='TI', mpn='TPS61500PWPR', fp='genctl:TPS61500_HTSSOP-14_PWP', lcsc='C71160')
ic('TPS22918DBVR', P((1,'VIN'),(3,'ON'),(4,'CT'),(2,'GND')), P((6,'VOUT'),(5,'QOD')), desc='5.5V 2A load switch, SOT-23-6', mfr='TI', mpn='TPS22918DBVR',
   fp='Package_TO_SOT_SMD:SOT-23-6', lcsc='C131941')
ic('TPS2553DBVR', P((1,'IN'),(3,'EN'),(5,'ILIM'),(2,'GND')), P((6,'OUT'),(4,'FAULT')), desc='USB power switch, adjustable ILIM 75-1700 mA, active-high EN, SOT-23-6', mfr='TI', mpn='TPS2553DBVR',
   fp='Package_TO_SOT_SMD:SOT-23-6', lcsc='C55266')
ic('TLV75518PDBVR', P((1,'IN'),(3,'EN'),(2,'GND')), P((5,'OUT'),(4,'NC')), desc='1.8V 500mA LDO, SOT-23-5', mfr='TI', mpn='TLV75518PDBVR', fp='Package_TO_SOT_SMD:SOT-23-5', lcsc='C2877863')
ic('TPS7B6950QDBVRQ1', P((1,'IN'),(3,'GND')), P((5,'OUT'),(2,'NC'),(4,'GND')), desc='40V 150mA 5V LDO, SOT-23-5 DBV: pins 3 and 4 both GND per DS pin table', mfr='TI', mpn='TPS7B6950QDBVRQ1', fp='Package_TO_SOT_SMD:SOT-23-5', lcsc='C132202')
ic('TPS1H200AQDGNRQ1', P((8,'VS'),(1,'IN'),(2,'DIAG_EN'),(4,'CL'),(5,'DELAY'),(6,'GND'),(9,'EP')), P((7,'OUT'),(3,'FAULT')), desc='40V 200mOhm high-side switch, MSOP-8-PowerPAD', mfr='TI', mpn='TPS1H200AQDGNRQ1', fp='genctl:TPS1H200_MSOP-8-EP_DGN', lcsc='C2653785')
ic('TPS1HTC30QPWPRQ1', P((12,'VS'),(13,'VS'),(14,'VS'),(2,'EN'),(3,'DIAG_EN'),(5,'LATCH'),(7,'ILIM'),(1,'GND')), P((8,'VOUT'),(9,'VOUT'),(10,'VOUT'),(6,'SNS'),(4,'FAULT'),(11,'NC'),(15,'EP')),
   desc='40V 30mOhm high-side switch, HTSSOP-14 PWP; EP (15) to GND per DS', mfr='TI', mpn='TPS1HTC30AQPWPRQ1', fp='genctl:TPS1HTC30_HTSSOP-14_PWP', lcsc='C22414694')
ic('TPS48100QDGXRQ1', P((20,'VS'),(1,'EN/UVLO'),(3,'INP1'),(2,'INP2'),(7,'CS_SEL'),(8,'ISCP'),(9,'TMR'),(10,'SCP_TEST'),(6,'GND'),(4,'NC'),(19,'NC')),
   P((18,'CS+'),(17,'CS-'),(15,'G1PU'),(14,'G1PD'),(11,'G2'),(12,'BST'),(13,'SRC'),(5,'FLT')), desc='Smart high-side driver with protection, VSSOP-19 DGX (pin 16 absent). ISCP: R to GND; CS_SEL GND = high-side sense', mfr='TI', mpn='TPS48100QDGXRQ1', fp='genctl:TPS48100_VSSOP-19_DGX', lcsc='C43131316')
ic('TMUX1208PWR', P((8,'D'),(1,'A0'),(16,'A1'),(15,'A2'),(2,'EN'),(13,'VDD'),(14,'GND'),(3,'NC')), P((4,'S1'),(5,'S2'),(6,'S3'),(7,'S4'),(12,'S5'),(11,'S6'),(10,'S7'),(9,'S8')),
   desc='8:1 analog mux, TSSOP-16 (pin 3 = NC per DS)', mfr='TI', mpn='TMUX1208PWR', fp='Package_SO:TSSOP-16_4.4x5mm_P0.65mm', lcsc='C494728')
ic('SN74LVC541APWR', P((2,'A1'),(3,'A2'),(4,'A3'),(5,'A4'),(6,'A5'),(7,'A6'),(8,'A7'),(9,'A8'),(1,'~{OE1}'),(19,'~{OE2}'),(20,'VCC'),(10,'GND')),
   P((18,'Y1'),(17,'Y2'),(16,'Y3'),(15,'Y4'),(14,'Y5'),(13,'Y6'),(12,'Y7'),(11,'Y8')), desc='Octal buffer 3-state, TSSOP-20', mfr='TI', mpn='SN74LVC541APWR', fp='Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm', lcsc='C113281')
ic('SN65DSI83ZXHR', P(('H3','DA0P'),('J3','DA0N'),('H4','DA1P'),('J4','DA1N'),('H6','DA2P'),('J6','DA2N'),('H7','DA3P'),('J7','DA3N'),('H5','DACP'),('J5','DACN'),None,('H1','SCL'),('J1','SDA'),('A1','ADDR'),('B1','EN'),('J9','IRQ'),('H2','REFCLK'),('H8','RSVD1'),('B2','RSVD2')),
   P(('C8','A_Y0P'),('C9','A_Y0N'),('D8','A_Y1P'),('D9','A_Y1N'),('E8','A_Y2P'),('E9','A_Y2N'),('G8','A_Y3P'),('G9','A_Y3N'),('F8','A_CLKP'),('F9','A_CLKN'),None,
     ('A9','VCC'),('B8','VCC'),('D6','VCC'),('E5','VCC'),('E6','VCC'),('F6','VCC'),('J2','VCC'),('J8','VCORE'),
     ('A2','GND'),('A8','GND'),('B9','GND'),('D5','GND'),('E4','GND'),('F4','GND'),('F5','GND'),('H9','GND')),
   bottom=P(('B3','NC'),('A3','NC'),('B4','NC'),('A4','NC'),('B5','NC'),('A5','NC'),('B6','NC'),('A6','NC'),('B7','NC'),('A7','NC'),('C2','NC'),('C1','NC'),('D2','NC'),('D1','NC'),('F2','NC'),('F1','NC'),('G2','NC'),('G1','NC'),('E2','NC'),('E1','NC')),
   desc='MIPI DSI to single-link LVDS bridge, nFBGA-64', mfr='TI', mpn='SN65DSI83ZXHR', fp='genctl:SN65DSI83_nFBGA-64_ZXH', lcsc='C2871688')
ic('CA-IS3062W', P((1,'VCC'),(3,'TXD'),(5,'RXD'),(2,'GND1'),(8,'GND1'),(4,'NC'),(6,'NC'),(7,'NC')), P((11,'VISO'),(16,'VISO'),(13,'CANH'),(12,'CANL'),(9,'GND2'),(10,'GND2'),(15,'GND2'),(14,'NC')),
   desc='Isolated CAN FD transceiver w/ integrated DC-DC, SOIC-16W, VCC 4.5-5.5V', mfr='Chipanalog', mpn='CA-IS3062W', fp='Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm', lcsc='C2890050')
ic('CA-IS2092W', P((1,'VCC'),(6,'DI'),(3,'RO'),(5,'DE'),(4,'~{RE}'),(2,'GNDA'),(7,'GNDA'),(8,'GNDA')), P((16,'VISO'),(10,'SEL'),(12,'A'),(13,'B'),(9,'GNDB'),(15,'GNDB'),(11,'NC'),(14,'NC')),
   desc='Isolated RS-485 transceiver w/ integrated DC-DC, SOIC-16W', mfr='Chipanalog', mpn='CA-IS2092W', fp='Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm', lcsc='C5121950')
ic('ADE9000ACPZ', P((7,'IAP'),(8,'IAN'),(9,'IBP'),(10,'IBN'),(11,'ICP'),(12,'ICN'),(13,'INP'),(14,'INN'),(20,'VAP'),(19,'VAN'),(22,'VBP'),(21,'VBN'),(24,'VCP'),(23,'VCN'),(29,'CLKIN'),(30,'CLKOUT')),
   P((27,'VDD'),(1,'PULL_HIGH'),(25,'AVDDOUT'),(3,'DVDDOUT'),(16,'REF'),(37,'SCLK'),(39,'MOSI'),(38,'MISO'),(40,'~{SS}'),(6,'~{RESET}'),(31,'~{IRQ0}'),(32,'~{IRQ1}'),(33,'CF1'),(34,'CF2'),(35,'CF3/ZX'),(36,'CF4/EVENT'),(4,'PM0'),(5,'PM1')),
   bottom=P((2,'DGND'),(15,'REFGND'),(17,'NC1'),(18,'NC2'),(26,'AGND'),(28,'GND'),(41,'EP')),
   desc='High-performance polyphase energy metering IC, LFCSP-40', mfr='Analog Devices', mpn='ADE9000ACPZ-RL', fp='genctl:ADE9000_LFCSP-40_6x6', lcsc='C654559')
ic('AC1005', P((4,'P1'),(5,'P2')), P((1,'S1'),(2,'S2'),(3,'NC')), ref='T', desc='Current transformer 5A:5mA 1000:1, pass-through primary. S1/S2 = CT pins 1/2, pin 3 mechanical. P1/P2 = footprint wire-loop pads 4/5 (primary wire passes through the core window)', mfr='Talema', mpn='AC1005', fp='genctl:AC1005_CT', lcsc='C6117861')
ic('HR911131A', P((1,'TRD0+'),(2,'TRD0-'),(3,'TRD1+'),(4,'TRD1-'),(7,'TRD2+'),(8,'TRD2-'),(9,'TRD3+'),(10,'TRD3-'),(5,'CT'),(6,'CT')), P((11,'LED_G_A'),(12,'LED_G_K'),(14,'LED_Y_A'),(13,'LED_Y_K'),(15,'SHIELD'),(16,'SHIELD')),
   ref='J', desc='RJ45 magjack 10/100/1000BASE-T (IEEE802.3ab), 4x 1CT:1CT, centre taps common on P5/P6, green LED 11(A)-12(K), yellow 14(A)-13(K) per HanRun DS schematic. Shield pads 15/16 per footprint', mfr='HanRun', mpn='HR911131A', fp='genctl:HR911131A_RJ45', lcsc='C5184934')
ic('ISOW7841DWE', P((1,'VCC'),(3,'INA'),(4,'INB'),(5,'INC'),(6,'OUTD'),(7,'NC'),(2,'GND1'),(8,'GND1')), P((16,'VISO'),(14,'OUTA'),(13,'OUTB'),(12,'OUTC'),(11,'IND'),(10,'SEL'),(9,'GND2'),(15,'GND2')),
   desc='5kVrms reinforced quad isolator 3/1 + integrated DC-DC, SOIC-16 DWE (8mm creepage). Pinout per TI SLLSEY2G', mfr='TI', mpn='ISOW7841DWER', fp='Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm', lcsc='C179690')
ic('ISO7741DW', P((1,'VCC1'),(3,'INA'),(4,'INB'),(5,'INC'),(6,'OUTD'),(7,'EN1'),(2,'GND1'),(8,'GND1')), P((16,'VCC2'),(14,'OUTA'),(13,'OUTB'),(12,'OUTC'),(11,'IND'),(10,'EN2'),(9,'GND2'),(15,'GND2')),
   desc='5kVrms reinforced quad isolator 3/1, SOIC-16 DW (8mm creepage). Pinout per TI datasheet', mfr='TI', mpn='ISO7741DWR', fp='Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm', lcsc='C571196')
ic('228EMVARGBFR', P((1,'B'),(2,'B'),(3,'A')), P((4,'L1'),(5,'L2'),(6,'L3'),(7,'L4')),
   ref='SW', desc='Sealed IP67 SMD tactile switch, RGB backlit. Switch A-B (B pins common). LED: L1 common anode, L2 green K, L3 red K, L4 blue K (CTS 228E Rev H fig.1). Pads 1-7 = symbol pins; footprint hand-drawn from CTS drawing', mfr='CTS', mpn='228EMVARGBFR', fp='genctl:CTS_228E_RGB', lcsc='C6077135')
ic('RClamp0524P', P((1,'IO1'),(2,'IO2'),(4,'IO3'),(5,'IO4'),(3,'GND')), P((10,'IO1'),(9,'IO2'),(7,'IO3'),(6,'IO4'),(8,'GND')), ref='D', desc='4-line ESD array, flow-through SLP2510P8 (pins 6/7/9/10 are internally the same lines as 5/4/2/1 - route through)', mfr='Semtech', mpn='RCLAMP0524P.TCT', fp='genctl:RClamp0524P_SLP2510P8', lcsc='C40960')
ic('ACT45B-510-2P', P((1,'1'),(2,'2')), P((4,'4'),(3,'3')), ref='L', desc='CAN common-mode choke 51uH; windings 1-4 and 2-3 per TDK ACT45B drawing', mfr='TDK', mpn='ACT45B-510-2P-TL003', fp='genctl:ACT45B_CMC', lcsc='C76584')
ic('M.2_KeyB_Modem', [('2','3.3V'),('4','3.3V'),('70','3.3V'),('72','3.3V'),('74','3.3V'),('6','FULL_CARD_PWR_OFF#'),('8','W_DISABLE1#'),('67','RESET#'),('10','LED1#'),('7','USB_D+'),('9','USB_D-'),('30','UIM_RESET'),('32','UIM_CLK'),('34','UIM_DATA'),('36','UIM_PWR'),('66','SIM_DETECT'),('1','CONFIG_3'),('21','CONFIG_0'),('69','CONFIG_1'),('75','CONFIG_2')],
   [(str(n),'GND') for n in (3,5,11,27,33,39,45,51,57,71,73)]+[(str(n),'P%d'%n) for n in [20,22,23,24,25,26,28,29,31,35,37,38,40,41,42,43,44,46,47,48,49,50,52,53,54,55,56,58,59,60,61,62,63,64,65,68]],
   ref='J', desc='M.2 Key B socket (WWAN/LTE). Pin functions per PCI-SIG M.2 WWAN Key B assignment (verify vs modem); Pnn = unused/NC', mfr='Molex/MDT', mpn='MDT420B01001', fp='genctl:M.2_KeyB_MDT420B03001', lcsc='C4594496')
CM5={}
for line in open('/workspace/genctl/kicad/genctl/tools/cm5pins.txt'):
    n,nm=line.split(None,1); CM5[int(n)]=nm.strip()
for nm,rng in (('RPi_CM5_A',range(1,101)),('RPi_CM5_B',range(101,201))):
    ic(nm,[(str(n),CM5[n]) for n in rng if n%2==1],[(str(n),CM5[n]) for n in rng if n%2==0],ref='U',
       desc='Raspberry Pi Compute Module 5, connector %s (pins %d-%d), pin names from CM5 datasheet'%(nm[-1],rng[0],rng[-1]),
       mfr='Hirose', mpn='DF40C-100DS-0.4V(51)', fp='genctl:DF40C-100DS-0.4V'+('_B' if nm.endswith('B') else ''), lcsc='C597931')
ic('USB3_A_Receptacle', P((1,'VBUS'),(2,'D-'),(3,'D+'),(4,'GND'),(5,'SSRX-'),(6,'SSRX+'),(7,'GND_DRAIN'),(8,'SSTX-'),(9,'SSTX+')), P((10,'SHIELD'),), ref='J', desc='USB 3.0 Type-A receptacle, THT right-angle, Hong Cheng HC-USB3.0-L168-WP (DS pins 1-9 std USB3 StdA, 2 shell pads = 10)', mfr='Hong Cheng', mpn='HC-USB3.0-L168-WP', lcsc='C7501850', fp='genctl:USB3_A_HC-USB3.0-L168-WP')
ic('CR2032_Holder', P((1,'+')), P((2,'-')), ref='BT', desc='CR2032 SMD holder', mfr='MYOUNG', mpn='BS-CR2032-8', fp='genctl:BS-CR2032-8', lcsc='C7498149')
ic('LMR36506RRPER', P((4,'VIN'),(3,'EN/UVLO'),(1,'RT'),(8,'FB'),(9,'GND')), P((5,'SW'),(6,'BOOT'),(7,'VCC'),(2,'PGOOD')), desc='3-65V 0.6A sync buck, VQFN-HR-9 2x2 (RPE)', mfr='TI', mpn='LMR36506RRPER', fp='genctl:LMR36506_VQFN-HR-9_RPE', lcsc='C2870127')
ic('TPS2121RUXR', P((7,'IN1'),(2,'IN2'),(6,'PR1'),(3,'CP2'),(5,'OV1'),(4,'OV2'),(12,'GND')), P((1,'OUT'),(8,'OUT'),(9,'ST'),(10,'ILM'),(11,'SS')), desc='2.8-22V 4.5A priority power mux, VQFN-HR-12 (RUX)', mfr='TI', mpn='TPS2121RUXR', fp='genctl:TPS2121_VQFN-HR-12_RUX', lcsc='C485916')
ic('TPS61023DRLR', P((3,'VIN'),(2,'EN'),(1,'FB'),(4,'GND')), P((6,'VOUT'),(5,'SW')), desc='0.5-5.5V in 3.7A boost, SOT-563', mfr='TI', mpn='TPS61023DRLR', fp='Package_TO_SOT_SMD:SOT-563', lcsc='C919459')
ic('TPS2116DRLR', P((3,'VIN1'),(6,'VIN2'),(4,'PR1'),(5,'MODE'),(1,'GND')), P((2,'VOUT'),(7,'VOUT'),(8,'ST')), desc='1.6-5.5V 2.5A power mux, SOT-583-8', mfr='TI', mpn='TPS2116DRLR', fp='Package_TO_SOT_SMD:SOT-583-8', lcsc='C3235557')
