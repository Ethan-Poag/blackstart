from gen import ic
def P(*a): return [(str(x[0]),x[1]) if x else None for x in a]
def mk(nums_names): return [(str(n),nm) for n,nm in nums_names]

ic('LM74800QDRRRQ1', P((2,'A'),(10,'VS'),(3,'VSNS'),(4,'SW'),(6,'EN/UVLO'),(5,'OV'),(7,'GND')),
   P((1,'DGATE'),(12,'C'),(8,'HGATE'),(9,'OUT'),(11,'CAP')), desc='Ideal diode controller w/ load-dump protection, WSON-12', mfr='TI', mpn='LM74800QDRRRQ1',
   fp='')
ic('LM5176PWPR', P((2,'VIN'),(3,'VISNS'),(1,'EN/UVLO'),(4,'MODE'),(5,'DITH'),(6,'RT/SYNC'),(7,'SLOPE'),(8,'SS'),(9,'COMP'),(11,'FB'),(12,'VOSNS'),(14,'ISNS+'),(13,'ISNS-'),(10,'AGND'),(29,'EP')),
   P((27,'HDRV1'),(26,'BOOT1'),(28,'SW1'),(25,'LDRV1'),(19,'HDRV2'),(20,'BOOT2'),(18,'SW2'),(21,'LDRV2'),(16,'CS'),(15,'CSG'),(17,'PGOOD'),(23,'VCC'),(24,'BIAS'),(22,'PGND')),
   desc='4-switch buck-boost controller, HTSSOP-28', mfr='TI', mpn='LM5176PWPR', fp='Package_SO:HTSSOP-28-1EP_4.4x9.7mm_P0.65mm_EP2.85x5.4mm')
ic('TPS56637RPAR', P((8,'VIN'),(1,'EN'),(10,'MODE'),(2,'FB'),(3,'AGND'),(9,'PGND')), P((7,'BOOT'),(6,'SW'),(4,'PG'),(5,'NC')),
   desc='4.5-28V 6A sync buck, VQFN-HR-10', mfr='TI', mpn='TPS56637RPAR')
ic('TPS629210DRL', P((6,'VIN'),(7,'EN'),(8,'MODE/S-CONF'),(5,'GND')), P((4,'SW'),(3,'VOS'),(1,'FB/VSET'),(2,'PG')),
   desc='3-17V 1A sync buck, SOT-583', mfr='TI', mpn='TPS629210QDRLRQ1')
ic('TPS3431SDRBR', P((1,'VDD'),(3,'EN'),(5,'SET1'),(2,'CWD'),(6,'WDI'),(4,'GND')), P((7,'WDO'),(8,'ENOUT')),
   desc='Standard programmable window watchdog, SON-8', mfr='TI', mpn='TPS3431SDRBR')
ic('TPS61500PWPR', P((3,'VIN'),(4,'EN'),(6,'DIMC'),(5,'SS'),(10,'FREQ'),(8,'COMP'),(7,'AGND'),(15,'EP')), P((1,'SW'),(2,'SW'),(11,'OVP'),(9,'FB'),(12,'PGND'),(13,'PGND'),(14,'PGND')),
   desc='3A boost WLED driver, HTSSOP-14', mfr='TI', mpn='TPS61500PWPR')
ic('TPS22918DBVR', P((1,'VIN'),(3,'ON'),(4,'CT'),(2,'GND')), P((6,'VOUT'),(5,'QOD')), desc='5.5V 2A load switch, SOT-23-6', mfr='TI', mpn='TPS22918DBVR',
   fp='Package_TO_SOT_SMD:SOT-23-6')
ic('TLV75518PDBVR', P((1,'IN'),(3,'EN'),(2,'GND')), P((5,'OUT'),(4,'NC')), desc='1.8V 500mA LDO, SOT-23-5', mfr='TI', mpn='TLV75518PDBVR', fp='Package_TO_SOT_SMD:SOT-23-5')
ic('TPS7B6950QDBVRQ1', P((1,'IN'),(3,'GND')), P((5,'OUT'),(2,'NC'),(4,'NC')), desc='40V 150mA 5V LDO, SOT-23-5 (pin4 assumed NC)', mfr='TI', mpn='TPS7B6950QDBVRQ1', fp='Package_TO_SOT_SMD:SOT-23-5')
ic('TPS1H200AQDGNRQ1', P((8,'VS'),(1,'IN'),(2,'DIAG_EN'),(4,'CL'),(5,'DELAY'),(6,'GND'),(9,'EP')), P((7,'OUT'),(3,'FAULT')), desc='40V 200mOhm high-side switch, MSOP-8-PowerPAD', mfr='TI', mpn='TPS1H200AQDGNRQ1')
ic('TPS1HTC30QPWPRQ1', P((12,'VS'),(13,'VS'),(14,'VS'),(2,'EN'),(3,'DIAG_EN'),(5,'LATCH'),(7,'ILIM'),(1,'GND')), P((8,'VOUT'),(9,'VOUT'),(10,'VOUT'),(6,'SNS'),(4,'FAULT'),(11,'NC')),
   desc='40V 30mOhm high-side switch, HTSSOP-14 (EP not modelled - check DS)', mfr='TI', mpn='TPS1HTC30QPWPRQ1')
ic('TPS48100QDGXRQ1', P((20,'VS'),(1,'EN/UVLO'),(3,'INP1'),(2,'INP2'),(7,'CS_SEL'),(8,'ISCP'),(9,'TMR'),(10,'SCP_TEST'),(6,'GND'),(4,'NC'),(19,'NC')),
   P((18,'CS+'),(17,'CS-'),(15,'G1PU'),(14,'G1PD'),(11,'G2'),(12,'BST'),(13,'SRC'),(5,'FLT')), desc='Smart high-side driver with protection, VSSOP-19', mfr='TI', mpn='TPS48100QDGXRQ1')
ic('TMUX1208PWR', P((8,'D'),(1,'A0'),(16,'A1'),(15,'A2'),(2,'EN'),(13,'VDD'),(14,'GND'),(3,'GND/NC?')), P((4,'S1'),(5,'S2'),(6,'S3'),(7,'S4'),(12,'S5'),(11,'S6'),(10,'S7'),(9,'S8')),
   desc='8:1 analog mux, TSSOP-16 (pin3 per DS table UNVERIFIED)', mfr='TI', mpn='TMUX1208PWR', fp='Package_SO:TSSOP-16_4.4x5mm_P0.65mm')
ic('SN74LVC541APWR', P((2,'A1'),(3,'A2'),(4,'A3'),(5,'A4'),(6,'A5'),(7,'A6'),(8,'A7'),(9,'A8'),(1,'~{OE1}'),(19,'~{OE2}'),(20,'VCC'),(10,'GND')),
   P((18,'Y1'),(17,'Y2'),(16,'Y3'),(15,'Y4'),(14,'Y5'),(13,'Y6'),(12,'Y7'),(11,'Y8')), desc='Octal buffer 3-state, TSSOP-20', mfr='TI', mpn='SN74LVC541APWR', fp='Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm')
ic('SN65DSI83ZXHR', P(('H3','DA0P'),('J3','DA0N'),('H4','DA1P'),('J4','DA1N'),('H6','DA2P'),('J6','DA2N'),('H7','DA3P'),('J7','DA3N'),('H5','DACP'),('J5','DACN'),None,('H1','SCL'),('J1','SDA'),('A1','ADDR'),('B1','EN'),('J9','IRQ'),('H2','REFCLK'),('H8','RSVD1'),('B2','RSVD2')),
   P(('C8','A_Y0P'),('C9','A_Y0N'),('D8','A_Y1P'),('D9','A_Y1N'),('E8','A_Y2P'),('E9','A_Y2N'),('G8','A_Y3P'),('G9','A_Y3N'),('F8','A_CLKP'),('F9','A_CLKN'),None,
     ('A9','VCC'),('B8','VCC'),('D6','VCC'),('E5','VCC'),('E6','VCC'),('F6','VCC'),('J2','VCC'),('J8','VCORE'),
     ('A2','GND'),('A8','GND'),('B9','GND'),('D5','GND'),('E4','GND'),('F4','GND'),('F5','GND'),('H9','GND')),
   bottom=P(('B3','NC'),('A3','NC'),('B4','NC'),('A4','NC'),('B5','NC'),('A5','NC'),('B6','NC'),('A6','NC'),('B7','NC'),('A7','NC'),('C2','NC'),('C1','NC'),('D2','NC'),('D1','NC'),('F2','NC'),('F1','NC'),('G2','NC'),('G1','NC'),('E2','NC'),('E1','NC')),
   desc='MIPI DSI to single-link LVDS bridge, nFBGA-64', mfr='TI', mpn='SN65DSI83ZXHR')
ic('CA-IS3062W', P((1,'VCC'),(3,'TXD'),(5,'RXD'),(2,'GND1'),(8,'GND1'),(4,'NC'),(6,'NC'),(7,'NC')), P((11,'VISO'),(16,'VISO'),(13,'CANH'),(12,'CANL'),(9,'GND2'),(10,'GND2'),(15,'GND2'),(14,'NC')),
   desc='Isolated CAN FD transceiver w/ integrated DC-DC, SOIC-16W, VCC 4.5-5.5V', mfr='Chipanalog', mpn='CA-IS3062W', fp='Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm')
ic('CA-IS2092W', P((1,'VCC'),(6,'DI'),(3,'RO'),(5,'DE'),(4,'~{RE}'),(2,'GNDA'),(7,'GNDA'),(8,'GNDA')), P((16,'VISO'),(10,'SEL'),(12,'A'),(13,'B'),(9,'GNDB'),(15,'GNDB'),(11,'NC'),(14,'NC')),
   desc='Isolated RS-485 transceiver w/ integrated DC-DC, SOIC-16W', mfr='Chipanalog', mpn='CA-IS2092W', fp='Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm')
ic('ADE9000ACPZ', P((7,'IAP'),(8,'IAN'),(9,'IBP'),(10,'IBN'),(11,'ICP'),(12,'ICN'),(13,'INP'),(14,'INN'),(20,'VAP'),(19,'VAN'),(22,'VBP'),(21,'VBN'),(24,'VCP'),(23,'VCN'),(29,'CLKIN'),(30,'CLKOUT')),
   P((27,'VDD'),(1,'PULL_HIGH'),(25,'AVDDOUT'),(3,'DVDDOUT'),(16,'REF'),(37,'SCLK'),(39,'MOSI'),(38,'MISO'),(40,'~{SS}'),(6,'~{RESET}'),(31,'~{IRQ0}'),(32,'~{IRQ1}'),(33,'CF1'),(34,'CF2'),(35,'CF3/ZX'),(36,'CF4/EVENT'),(4,'PM0'),(5,'PM1')),
   bottom=P((2,'DGND'),(15,'REFGND'),(17,'NC1'),(18,'NC2'),(26,'AGND'),(28,'GND'),(41,'EP')),
   desc='High-performance polyphase energy metering IC, LFCSP-40', mfr='Analog Devices', mpn='ADE9000ACPZ')
ic('ADuM5020-5BRWZ', P((5,'VDDP'),(3,'PDIS'),(2,'GND1'),(4,'GND1'),(6,'GND1'),(8,'GND1'),(1,'NIC'),(7,'NIC')), P((12,'VISO'),(14,'VSEL'),(9,'GNDISO'),(11,'GNDISO'),(13,'GNDISO'),(15,'GNDISO'),(10,'NIC'),(16,'NIC')),
   desc='Isolated DC-DC 500mW, SOIC-16W (3 kVrms - NOT reinforced 5kV)', mfr='Analog Devices', mpn='ADuM5020-5BRWZ', fp='Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm')
ic('ADuM141E1BRWZ', P((1,'VDD1'),(3,'VIA'),(4,'VIB'),(5,'VIC'),(6,'VOD'),(7,'VE1'),(2,'GND1'),(8,'GND1')), P((16,'VDD2'),(14,'VOA'),(13,'VOB'),(12,'VOC'),(11,'VID'),(10,'VE2'),(9,'GND2'),(15,'GND2')),
   desc='Quad digital isolator 3/1, SOIC-16W (pinout from memory - UNVERIFIED)', mfr='Analog Devices', mpn='ADuM141E1BRWZ', fp='Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm')
ic('ADP150AUJZ-3.3', P((1,'VIN'),(3,'EN'),(2,'GND')), P((5,'VOUT'),(4,'NC')), desc='150mA 3.3V LDO TSOT-5', mfr='Analog Devices', mpn='ADP150AUJZ-3.3-R7', fp='Package_TO_SOT_SMD:TSOT-23-5')
ic('AC1005', P((1,'P1'),(2,'P2')), P((3,'S1'),(4,'S2')), ref='T', desc='Current transformer 5A:5mA 1000:1, pass-through primary. P1/P2 = primary wire loop through core (wire bridge / busbar link - not a pin on the CT)', mfr='Talema', mpn='AC1005')
ic('HR911130C', P((1,'TD+'),(2,'TD-'),(3,'RD+'),(6,'RD-'),(4,'CT1'),(5,'CT2'),(7,'NC'),(8,'GND_CHS')), P((9,'LED_L_A'),(10,'LED_L_K'),(11,'LED_R_A'),(12,'LED_R_K'),(13,'SHIELD'),(14,'SHIELD')),
   ref='J', desc='RJ45 magjack 10/100 w/ LEDs (pin map UNVERIFIED - DS is graphical). CM5 needs 1000BASE-T 4-pair jack for gigabit', mfr='HanRun', mpn='HR911130C')
ic('RClamp0524P', P((1,'IO1'),(2,'IO2'),(4,'IO3'),(5,'IO4'),(3,'GND')), P((10,'IO1'),(9,'IO2'),(7,'IO3'),(6,'IO4'),(8,'GND')), ref='D', desc='4-line ESD array, flow-through SLP2510P8', mfr='Semtech', mpn='RCLAMP0524P.TCT')
ic('ACT45B-510-2P', P((1,'1'),(2,'2')), P((4,'4'),(3,'3')), ref='L', desc='CAN common-mode choke 51uH (winding 1:1-4, 2:2-3 UNVERIFIED)', mfr='TDK', mpn='ACT45B-510-2P-TL003')
ic('M.2_KeyB_Modem', [('2','3.3V'),('4','3.3V'),('70','3.3V'),('72','3.3V'),('74','3.3V'),('6','FULL_CARD_PWR_OFF#'),('8','W_DISABLE1#'),('67','RESET#'),('10','LED1#'),('7','USB_D+'),('9','USB_D-'),('30','UIM_RESET'),('32','UIM_CLK'),('34','UIM_DATA'),('36','UIM_PWR'),('66','SIM_DETECT'),('1','CONFIG_3'),('21','CONFIG_0'),('69','CONFIG_1'),('75','CONFIG_2')],
   [(str(n),'GND') for n in (3,5,11,27,33,39,45,51,57,71,73)]+[(str(n),'P%d'%n) for n in [20,22,23,24,25,26,28,29,31,35,37,38,40,41,42,43,44,46,47,48,49,50,52,53,54,55,56,58,59,60,61,62,63,64,65,68]],
   ref='J', desc='M.2 Key B socket (WWAN/LTE). Pin functions from M.2 spec from memory - UNVERIFIED; Pnn = unused/NC', mfr='', mpn='M.2 Key-B socket 0.5mm (TBD)')
CM5={}
for line in open('/workspace/genctl/kicad/genctl/tools/cm5pins.txt'):
    n,nm=line.split(None,1); CM5[int(n)]=nm.strip()
for nm,rng in (('RPi_CM5_A',range(1,101)),('RPi_CM5_B',range(101,201))):
    ic(nm,[(str(n),CM5[n]) for n in rng if n%2==1],[(str(n),CM5[n]) for n in rng if n%2==0],ref='U',
       desc='Raspberry Pi Compute Module 5, connector %s (pins %d-%d), pin names from CM5 datasheet'%(nm[-1],rng[0],rng[-1]),
       mfr='Raspberry Pi', mpn='Hirose DF40C-100DS-0.4V mating connector (CM5 socket)', fp='')
ic('USB3_A_Receptacle', P((1,'VBUS'),(2,'D-'),(3,'D+'),(4,'GND'),(5,'SSRX-'),(6,'SSRX+'),(7,'GND_DRAIN'),(8,'SSTX-'),(9,'SSTX+')), P((10,'SHIELD'),(11,'SHIELD')), ref='J', desc='USB 3.0 Type-A receptacle (part TBD)', mpn='USB3.0 A female TBD')
ic('CR2032_Holder', P((1,'+')), P((2,'-')), ref='BT', desc='CR2032 holder', mfr='', mpn='CR2032 holder (BOM other_bom)')
