import symbols
from gen import *

def conn(sh,n,pinnets,value,mpn='',lcsc=None,note=''):
    lid='Connector_Generic:Conn_01x%02d'%n
    return sh.p(lid,value,{str(i+1):v for i,v in enumerate(pinnets)},prefix='J',mpn=mpn,lcsc=lcsc,note=note)
def tvs(sh,val,a,b='GND',uni=False):
    if uni: return sh.p('Device:D_Zener',val,{'K':a,'A':b},prefix='D',mpn=val,note='unidirectional TVS')
    return sh.p('Device:D_TVS',val,{'1':a,'2':b},prefix='D',mpn=val)
def schottky(sh,val,a,k,mpn=None):
    return sh.p('Device:D_Schottky',val,{'A':a,'K':k},prefix='D',mpn=mpn or val)
def fet(sh,lib,val,g,s,d,mpn=None):
    return sh.p(lib,val,{'G':g,'S':s,'D':d},prefix='Q',mpn=mpn or val)
def npn(sh,b,e,c): return sh.p('Transistor_BJT:MMBT3904','MMBT3904',{'B':b,'E':e,'C':c},prefix='Q',mpn='MMBT3904',lcsc='C20526')
def pnp(sh,b,e,c): return sh.p('Transistor_BJT:MMBT3906','MMBT3906',{'B':b,'E':e,'C':c},prefix='Q',mpn='MMBT3906',lcsc='C2143')
def clamp(sh,sig,part='BAV99'):
    # series dual diode: pin1 anode(lower)->GND, pin2 cathode(upper)->+3V3, pin3 common->signal
    lid='Diode:BAV99' if part=='BAV99' else 'Diode:BAT54S'
    return sh.p(lid,part,{'1':'GND','2':'+3V3','3':sig},prefix='D',mpn=part,note='rail clamp: pin1->GND, pin2->+3V3, pin3 signal')
def dec(sh,net,n=1,val='100n',pkg='0603',gnd='GND'):
    for _ in range(n): sh.C(val,net,gnd,pkg=pkg)
def tca(sh,addr,pins,intn='I2C_INT_N'):
    a=[(addr>>i)&1 for i in range(3)]
    c={'VCC':'+3V3','GND':'GND','SCL':'I2C1_SCL','SDA':'I2C1_SDA','~{INT}':intn,
       'A0':'+3V3' if a[0] else 'GND','A1':'+3V3' if a[1] else 'GND','A2':'+3V3' if a[2] else 'GND'}
    c.update(pins)
    u=sh.p('Interface_Expansion:TCA9555PWR','TCA9555PWR @0x%02X'%(0x20+addr),c,mpn='TCA9555PWR',lcsc='C465732',note='LCSC C465732')
    dec(sh,'+3V3'); return u

SHEETS=[]
def S(name,title,notes=''):
    s=Sheet(name,title,name+'.kicad_sch',notes); SHEETS.append(s); return s

# =====================================================================
pw=S('power','Power: input protection, ideal diode, 12V buck-boost, 5V, 3V3',
 'POWER. J0 battery in (BAT_IN; NO on-board fuse: installer fits an external fuse <=10 A fast-acting, >=58 V DC in the battery lead) -> SMDJ36CA -> LM74800 + 2x BSC070N10NS5 back-to-back (VBAT_P).\n'
 'OV 34.0V rise/31.2V fall typ (32.39-35.74 / 29.57-32.70 V), UV 5.56V/5.12V (210k/49.9k/9.76k, 1.231/1.13V thresholds). LM5176 buck-boost -> +12V (FB 140k/10k, RT 27.4k ~300kHz, 8mR sense).\n'
 'TPS56637 -> +5V (FB 75k/10k = 5.1V, 3.3uH). TPS56637 -> +3V3 from +12V (FB 45.3k/10k, 2.2uH, 3x22u), >=3A. MODE open = FCCM.\n'
 'SAFE DOMAIN: LMR36506 buck VBAT_P -> +3V3_BK (always on); TPS2116 priority mux VIN1=+3V3 / VIN2=+3V3_BK -> +3V3_SAFE (MCU, FRAM, WDT, I/O, E-stop logic).')
conn(pw,4,['BAT_IN','BAT_IN','GND','GND'],'PC 5/4-GF-7,62 (battery in)',mpn='1720819 Phoenix',note='J0 battery input')
REFC['F']+=1  # F1 (10A ATO + 2x Keystone 3557-2 clips) deleted in m7-step12: fuse is external; ref reserved so later refs stay stable
pw.p('Device:D_TVS','SMDJ36CA',{'1':'BAT_IN','2':'GND'},prefix='D',mpn='SMDJ36CA',mfr='Littelfuse',lcsc='C224075')
pw.C('100n','VBAT_DD','GND',pkg='0805',note='100V')
pw.C('220n','BAT_IN','GND',pkg='0805',ref='C297',mpn='CC0805KKX7R0BB224',lcsc='C513710',mfr='YAGEO',note='100V X7R; CIN on BAT_IN (LM74800 A/VSNS input) per TI SNOSD95C p23 (0.1 uF min); 220n for DC-bias margin')
pw.p('genctl:LM74800QDRRRQ1','LM74800QDRRRQ1',{'A':'BAT_IN','VS':'VBAT_DD','VSNS':'BAT_IN','SW':'BAT_IN','EN/UVLO':'LM748_EN','OV':'LM748_OV','GND':'GND','RTN':None,
     'DGATE':'LM748_DGATE','C':'VBAT_DD','HGATE':'LM748_HGATE','OUT':'VBAT_P','CAP':'LM748_CAP'},mpn='LM74800QDRRRQ1',lcsc='C3215600',note='EP=RTN left floating per DS')
pw.C('100n','LM748_CAP','VBAT_DD',note='CAP-VS charge-pump cap, 0.1uF per DS typ app')
pw.R('210k','BAT_IN','LM748_EN'); pw.R('49.9k','LM748_EN','LM748_OV'); pw.R('9.76k','LM748_OV','GND',mpn='0603WAF9761T5E',lcsc='C23128',mfr='UNI-ROYAL')
fet(pw,'Transistor_FET:BSC070N10NS5','BSC070N10NS5','LM748_DGATE','BAT_IN','VBAT_DD')
fet(pw,'Transistor_FET:BSC070N10NS5','BSC070N10NS5','LM748_HGATE','VBAT_P','VBAT_DD')
tvs(pw,'SMBJ33CA','VBAT_P')
for _ in range(2): pw.C('100u 50V','VBAT_P','GND',pol=True,mpn='EEHZA1H101P',pkg='Capacitor_SMD:CP_Elec_10x10.5')
for _ in range(4): pw.C('10u','VBAT_P','GND',pkg='1210',note='50V X7R')
# LM5176
pw.p('genctl:LM5176PWPR','LM5176PWPR',{'VIN':'VBAT_P','VISNS':'VBAT_P','EN/UVLO':'BB_EN','MODE':'BB_MODE','DITH':'GND','RT/SYNC':'BB_RT','SLOPE':'BB_SLOPE',
   'SS':'BB_SS','COMP':'BB_COMP','FB':'BB_FB','VOSNS':'+12V','ISNS+':'GND','ISNS-':'GND','AGND':'GND','EP':'GND',
   'HDRV1':'BB_HDRV1','BOOT1':'BB_BOOT1','SW1':'BB_SW1','LDRV1':'BB_LDRV1','HDRV2':'BB_HDRV2','BOOT2':'BB_BOOT2','SW2':'BB_SW2','LDRV2':'BB_LDRV2',
   'CS':'BB_CS','CSG':'GND','PGOOD':'PG_12V','VCC':'BB_VCC','BIAS':'+12V','PGND':'GND'},mpn='LM5176PWPR')  # m7-sch FW-009: BIAS=+12V, ISNS+/- to AGND (=GND net) per lm5176 p17/p30
pw.C('100n','+12V','GND',ref='C303',mpn='CC0603KRX7R9BB104',lcsc='C14663',mfr='YAGEO',note='LM5176 BIAS cap at U2.24 (spec C299)')
pw.R('100k','VBAT_P','BB_EN'); pw.R('33k','BB_EN','GND')
pw.R('93.1k','BB_MODE','GND',note='MODE: 93.1k = CCM, hiccup ENABLED (SNVSAI1D pin table p3; 200k/VCC = disabled)')
pw.R('27.4k','BB_RT','GND',note='fsw ~300kHz per DS RT equation - see DESIGN_NOTES')
pw.C('220p','BB_SLOPE','GND',note='slope comp per DS eq. (see DESIGN_NOTES)')
pw.C('47n','BB_SS','GND'); pw.R('4.7k','BB_COMP','BB_COMP_RC',mpn='0603WAF4701T5E',lcsc='C23162',mfr='UNI-ROYAL',note='Rc (review c65: 22.1k->4.7k)'); pw.C('33n','BB_COMP_RC','GND',note='Cc1'); pw.C('220p','BB_COMP','GND',note='Cc2')
pw.R('140k','+12V','BB_FB'); pw.R('10k','BB_FB','GND')
pw.R('100k','PG_12V','+3V3_SAFE')
pw.C('4.7u','BB_VCC','GND',pkg='1206'); pw.C('1u','+12V','GND',pkg='0805')
pw.C('100n','BB_BOOT1','BB_SW1'); pw.C('100n','BB_BOOT2','BB_SW2')
for bt in ('BB_BOOT1','BB_BOOT2'): schottky(pw,'BAS70','BB_VCC',bt,mpn='BAS70'); pw.parts[-1].lcsc='C77297'; pw.parts[-1].fp='Package_TO_SOT_SMD:SOT-23'; pw.parts[-1].note='external 70V boot diode per LM5176 DS'
for g,s_,d in (('BB_HDRV1','BB_SW1','VBAT_P'),('BB_LDRV1','BB_CS','BB_SW1'),('BB_LDRV2','BB_CS','BB_SW2'),('BB_HDRV2','BB_SW2','+12V')):
    fet(pw,'Transistor_FET:BSC070N10NS5','BSC070N10NS5',g,s_,d)
pw.p('Device:L','4.7u',{'1':'BB_SW1','2':'BB_SW2'},prefix='L',mpn='SPM10065VT-4R7M-D',lcsc='C501976',fp='genctl:L_SPM10065',note='4.7uH 10x10')
pw.R('8m','BB_CS','GND',pkg='2512',mpn='YLR12-2-8F-W',lcsc='C469375',note='buck-boost sense: 8mR -> ~9.4A peak limit (see DESIGN_NOTES)')
REFC['C']+=2  # C17/C18 470u removed (review e50: never connected on board, 160 mm from Q6; ~215 uF ceramics sufficient per reviewer model). Counter bump keeps later C refs stable.
# Review e65 (LM5176 COUT): local ceramics at Q6 drain (QH2), B.Cu. Fixed refs keep annotation stable.
for r in ('C293','C294','C295'): pw.C('22u','+12V','GND',pkg='1206',ref=r,note='LM5176 COUT local to Q6 drain (review e65)')
pw.C('100n','+12V','GND',ref='C296',note='LM5176 COUT HF local to Q6 drain (review e65)')
for _ in range(4): pw.C('22u','+12V','GND',pkg='1206')
# 5V
pw.p('genctl:TPS56637RPAR','TPS56637RPAR',{'VIN':'+12V','EN':'EN_5V','MODE':'MODE_5V','FB':'FB_5V','AGND':'GND','PGND':'GND','BOOT':'BOOT_5V','SW':'SW_5V','PG':'PG_5V','NC':None},mpn='TPS56637RPAR')
pw.R('121k','+12V','EN_5V'); pw.R('16k','EN_5V','GND',note='EN 1.4V at 12V; start ~9V')
pw.R('0R','MODE_5V','GND',dnp=True,note='DNP: MODE open = FCCM; fit 0R for Eco-mode')
pw.C('100n','BOOT_5V','SW_5V')
pw.p('Device:L','3.3u',{'1':'SW_5V','2':'+5V'},prefix='L',mpn='MWSA1004S-3R3MT',lcsc='C408483',fp='genctl:L_MWSA1004S',note='3.3uH per DS Table 4 (5V)')
pw.R('75k','+5V','FB_5V',note='5.1V'); pw.R('10k','FB_5V','GND')
pw.C('100p','+5V','FF_5V',note='C9 feed-forward per DS Table 4'); pw.R('20k','FF_5V','FB_5V',note='R8 per DS Table 4')
pw.R('100k','PG_5V','+3V3_SAFE')
for _ in range(2): pw.C('10u','+12V','GND',pkg='0805')
for _ in range(4): pw.C('22u','+5V','GND',pkg='1206')
tvs(pw,'SMBJ5.0A','+5V',uni=True)
# 3V3 (TPS56637, 6A part used for >=3A rail)
pw.p('genctl:TPS56637RPAR','TPS56637RPAR',{'VIN':'+12V','EN':'EN_3V3','MODE':'MODE_3V3','FB':'FB_3V3','AGND':'GND','PGND':'GND','BOOT':'BOOT_3V3','SW':'SW_3V3','PG':'PG_3V3','NC':None},mpn='TPS56637RPAR',note='+3V3 >=3A (6A capable)')
pw.R('121k','+12V','EN_3V3'); pw.R('16k','EN_3V3','GND',note='EN 1.4V at 12V')
pw.R('0R','MODE_3V3','GND',dnp=True,note='DNP: MODE open = FCCM')
pw.C('100n','BOOT_3V3','SW_3V3')
pw.p('Device:L','2.2u',{'1':'SW_3V3','2':'+3V3'},prefix='L',mpn='MWSA0503S-2R2MT',lcsc='C408408',fp='genctl:L_MWSA0503S',note='2.2uH per DS Table 4 (3.3V)')
pw.R('45.3k','+3V3','FB_3V3',note='DS Table 4: 45.3k/10k -> 3.32V'); pw.R('10k','FB_3V3','GND')
pw.C('100p','+3V3','FF_3V3',note='C9 per DS Table 4'); pw.R('20k','FF_3V3','FB_3V3',note='R8 per DS Table 4 (C9+R8 in series across R6)')
pw.R('100k','PG_3V3','+3V3_SAFE')
for _ in range(2): pw.C('10u','+12V','GND',pkg='0805',note='25V')
for _ in range(3): pw.C('22u','+3V3','GND',pkg='1206')
# ---- always-on backup 3V3 (safety domain) ----
pw.p('genctl:LMR36506RRPER','LMR36506RRPER',{'VIN':'VBAT_P','EN/UVLO':'VBAT_P','RT':'BK_RT','FB':'BK_FB','GND':'GND','SW':'BK_SW','BOOT':'BK_BOOT','VCC':'BK_VCC','PGOOD':None},mpn='LMR36506RRPER',lcsc='C2870127',note='always-on 3.3V from battery, 65V abs max')
pw.C('2.2u','VBAT_P','GND',pkg='1206',mpn='CL31B225KCHSNNE',lcsc='C170101',note='100V'); pw.C('100n','VBAT_P','GND',pkg='0805')
pw.R('40.2k','BK_RT','GND',note='fsw 400kHz (DS eq.1)'); pw.C('100n','BK_BOOT','BK_SW'); pw.C('1u','BK_VCC','GND')
pw.p('Device:L','33u',{'1':'BK_SW','2':'+3V3_BK'},prefix='L',mpn='SWPA6045S330MT',lcsc='C83451',fp='genctl:L_SWPA6045S',note='33uH per DS Table 8-1 (400kHz, 3.3V)')
pw.R('100k','+3V3_BK','BK_FB',note='3.315V'); pw.R('43.2k','BK_FB','GND')
for _ in range(2): pw.C('47u','+3V3_BK','GND',pkg='1206',mpn='CL31A476MQHNNNE',lcsc='C68361')
pw.p('genctl:TPS2116DRLR','TPS2116DRLR',{'VIN1':'+3V3','MODE':'+3V3','PR1':'MUX_PR1','VIN2':'+3V3_BK','GND':'GND','VOUT':'+3V3_SAFE','ST':'PSU_MAIN_OK'},mpn='TPS2116DRLR',lcsc='C3235557',note='priority mux: main +3V3 preferred, battery buck backup')
pw.R('18.7k','+3V3','MUX_PR1',note='switch to backup below ~2.87V'); pw.R('10k','MUX_PR1','GND')
pw.R('100k','PSU_MAIN_OK','+3V3_SAFE'); pw.C('1u','+3V3','GND'); pw.C('1u','+3V3_BK','GND')
for _ in range(2): pw.C('22u','+3V3_SAFE','GND',pkg='1206')
# chassis
for i in range(4): pw.p('Mechanical:MountingHole_Pad','MountingHole_Pad',{'1':'CHASSIS'},prefix='H')
pw.R('1M','CHASSIS','GND',pkg='1206'); pw.C('4.7n','CHASSIS','GND',pkg='1206',note='2kV - chassis/0V RC bond (assumed)')

# =====================================================================
mc=S('mcu','STM32H743 safety MCU',
 'MCU. STM32H743VIT6 LQFP-100. HSE 25MHz, LSE 32.768kHz. SWD header + JP1 (CM5 SWD, optional). CM5 reflash: USART1 PA9/PA10 bootloader, BOOT0 via 1k, NRST via NPN open-collector; PC2_C = CM5 heartbeat.\n'
 'Peripherals: SPI4 slave to CM5, USART2 to CM5, FDCAN1/2, USART3 RS-485, I2C1 (expanders/ADC/FRAM), SPI1 to ADE9000s via isolators.')
MAP={'PA0':'VBAT_SNS','PA1':'VESTOP_SNS','PA2':'DPLUS_SNS','PA3':'FUEL_ISNS','PA4':'ADE_CS1_N','PA5':'ADE_SCK','PA6':'ADE_MISO','PA7':'ADE_MOSI',
 'PA8':'DIAG_EN','PA9':'MCU_UART_TX','PA10':'MCU_UART_RX','PA11':'MUX_A2','PA12':'WDI','PA13':'SWDIO','PA14':'SWCLK','PA15':'MPU_SPEED',
 'PB0':'ADE_IRQ_N','PB1':'CRANK_ISNS','PB2':'OUT_FAULT_N','PB3':'BUZZER_PWM','PB4':'AUX3_MCU','PB5':'AUX4_MCU','PB6':'AUX5_MCU','PB7':'AUX6_MCU',
 'PB8':'I2C1_SCL','PB9':'I2C1_SDA','PB10':'DI8_N','PB11':'DI9_N','PB12':'CAN2_RX','PB13':'CAN2_TX','PB14':'DI10_N','PB15':'DI11_N',
 'PC0':'MUXA_OUT','PC1':'MUXB_OUT','PC2_C':'MCU_CM5_HB','PC3_C':'PSU_MAIN_OK','PC4':'ADE_CS2_N','PC5':'ADE_RST_N','PC6':'ESTOP2_DIG','PC7':'MPU_GATE',
 'PC8':'DPLUS_EXC_EN','PC9':'GCB_CL_MCU','PC10':'GCB_OP_MCU','PC11':'MCB_CL_MCU','PC12':'MCB_OP_MCU','PC13':'EXP_12V_EN','PC14':'LSE_IN','PC15':'LSE_OUT',
 'PD0':'CAN1_RX','PD1':'CAN1_TX','PD2':'FUEL_EN_MCU','PD3':'CRANK_EN_MCU','PD4':'GLOW_EN_MCU','PD5':'MUX_A0','PD6':'MUX_A1','PD7':'MCU_TRIP',
 'PD8':'RS485_TX','PD9':'RS485_RX','PD10':'DI12_N','PD11':'AUX7_MCU','PD12':'RS485_DE','PD13':'AUX8_MCU','PD14':'ESTOP_DIG','PD15':'DPLUS_DIG',
 'PE0':'AUX1_MCU','PE1':'AUX2_MCU','PE2':'MCU_SPI_SCK','PE3':'MCU_IRQ','PE4':'MCU_SPI_NSS','PE5':'MCU_SPI_MISO','PE6':'MCU_SPI_MOSI','PE7':'I2C_INT_N','PE8':'MCU_LED',
 'PH0':'HSE_IN','PH1':'HSE_OUT'}
for i in range(7): MAP['PE%d'%(9+i)]='DI%d_N'%(i+1)
# rev h: DI pins that double as STM32 bootloader pins (SPI4 PE11-14, USART3 PB10/11, USART1-alt PB14/15) get 1k series R
BLPINS=['PE11','PE12','PE13','PE14','PB10','PB11','PB14','PB15']
BLR=[(MAP[p],MAP[p]+'_M') for p in BLPINS]
for p in BLPINS: MAP[p]+='_M'
c=dict(MAP); c.update({'NRST':'NRST','BOOT0':'BOOT0','VREF+':'+3V3','VDD':'+3V3','VSS':'GND','VSSA':'GND','VDDA':'VDDA','48':'VCAP1','73':'VCAP2','VBAT':'VBAT_MCU'})
mc.p('MCU_ST_STM32H7:STM32H743VITx','STM32H743VIT6',c,mpn='STM32H743VIT6')
dec(mc,'+3V3',6); mc.C('4.7u','+3V3','GND',pkg='1206')
mc.p('Device:FerriteBead','600R@100MHz',{'1':'+3V3','2':'VDDA'},prefix='FB',mpn='GZ1608D601TF',lcsc='C1002',fp='Inductor_SMD:L_0603_1608Metric'); mc.C('1u','VDDA','GND'); mc.C('100n','VDDA','GND')
mc.C('2.2u','VCAP1','GND'); mc.C('2.2u','VCAP2','GND')
mc.C('100n','VBAT_MCU','GND')
for a,b in BLR: mc.R('1k',a,b,note='limits contention if bootloader drives this pin (<=3.3mA)')
mc.p('Device:Crystal_GND24','25MHz',{'1':'HSE_IN','3':'HSE_OUT','2':'GND','4':'GND'},prefix='Y',mpn='X322525MOB4SI',lcsc='C9006',fp='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',note='CL=12pF')
mc.C('18p','HSE_IN','GND',pkg='0402'); mc.C('18p','HSE_OUT','GND',pkg='0402')
mc.p('Device:Crystal','32.768kHz',{'1':'LSE_IN','2':'LSE_OUT'},prefix='Y',mpn='SC-32S32.768kHz20PPM7pF',lcsc='C97604',mfr='Seiko',fp='Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm',note='CL=7pF (m7-sch FW-013)')
mc.C('6.8p','LSE_IN','GND',pkg='0603',mpn='0603CG6R8C500NT',lcsc='C1679',mfr='FH'); mc.C('6.8p','LSE_OUT','GND',pkg='0603',mpn='0603CG6R8C500NT',lcsc='C1679',mfr='FH')  # m7-sch FW-013
mc.C('100n','NRST','GND')
mc.p('Switch:SW_Push','RESET',{'1':'NRST','2':'GND'},prefix='SW',mpn='TS-1187A-B-A-B')
mc.R('10k','BOOT0','GND')
mc.p('Switch:SW_Push','BOOT0',{'1':'BOOT0','2':'+3V3'},prefix='SW',mpn='TS-1187A-B-A-B')
mc.p('Connector:Conn_ARM_JTAG_SWD_10','SWD',{'1':'+3V3','2':'SWDIO','3':'GND','4':'SWCLK','5':'GND','6':None,'7':None,'8':None,'9':'GND','10':'NRST'},prefix='J')
mc.p('Connector_Generic:Conn_02x04_Odd_Even','JP1 CM5->MCU SWD (opt)',{'1':'CM5_SWDIO','2':'SWDIO','3':'CM5_SWCLK','4':'SWCLK','5':None,'6':None,'7':None,'8':None},prefix='JP')
mc.R('100k','MCU_CM5_HB','GND',note='heartbeat idle low when CM5 off')
mc.R('10k','OUT_FAULT_N','+3V3'); mc.R('10k','I2C_INT_N','+3V3')
mc.R('2.2k','I2C1_SCL','+3V3'); mc.R('2.2k','I2C1_SDA','+3V3')
mc.R('10k','ADE_IRQ_N','+3V3'); mc.R('10k','MCU_IRQ','GND')
mc.R('1k','MCU_LED','LED_HB_A'); mc.LED('green','LED_HB_A','GND',lcsc='C2297')
mc.p('Memory_NVRAM:FM24C64B','FM24CL64B',{'A0':'GND','A1':'GND','A2':'GND','VSS':'GND','SDA':'I2C1_SDA','SCL':'I2C1_SCL','WP':'GND','VDD':'+3V3'},mpn='FM24CL64B-GTR')
mc.C('100n','+3V3','GND')
mc.p('genctl:CR2032_Holder','CR2032',{'+':'VBAT_CELL','-':'GND'},mpn='CR2032 holder')
mc.p('Diode:BAT54C','BAT54C',{'1':'+3V3','2':'VBAT_CELL','3':'VBAT_MCU'},prefix='D',mpn='BAT54C',note='VBAT OR: +3V3_SAFE / CR2032')
mc.p('Connector_Generic:Conn_02x05_Odd_Even','Header B (MCU spare)',{'1':'+3V3','2':'GND','3':None,'4':None,'5':'I2C1_SCL','6':'I2C1_SDA','7':'GND','8':'+5V','9':None,'10':None},prefix='J')

# =====================================================================
cm=S('cm5','Raspberry Pi CM5',
 'CM5. GPIO map: 0/1 ID_SD/SC -> header A I2C; 2/3 display I2C (DSI83 + touch); 4 TOUCH_INT_N; 5 TOUCH_RST_N; 6 DSI83_EN; 7 DSI83_IRQ;\n'
 '8-11 SPI0 to MCU (33R series); 12 BL_PWM; 13 BTN_BL_PWM (button backlight dimming, PWM0_CHAN1); 14/15 UART0 to MCU; 16 PANEL_VDD_EN (also touch power); 17 CM5_PWR_FAIL (in, hold-up active); 18-21 SPI1 header A;\n'
 '22 CM5_NRST (NPN o/c to MCU NRST); 23 SWCLK; 24 SWDIO; 25 MCU_IRQ; 26 CM5_HB heartbeat -> MCU PC2_C; 27 CM5_BOOT0 (1k -> BOOT0).\n'
 'CM5 5V from +5V_CM5 (TPS2121 mux: +5V / supercap hold-up boost). PMIC_Enable pulled low by MCU (via TCA9555 @0x25 P05 + NPN) = hard power-off.')
cma={'GND':'GND','5V':'+5V_CM5','CM5_3.3V':'CM5_3V3','CM5_1.8V':'CM5_1V8','GPIO_VREF':'CM5_3V3','VBAT':'CM5_VBAT','nRPIBOOT':'CM5_NRPIBOOT',
 'Ethernet_Pair0_P':'ETH0_P','Ethernet_Pair0_N':'ETH0_N','Ethernet_Pair1_P':'ETH1_P','Ethernet_Pair1_N':'ETH1_N','Ethernet_Pair2_P':'ETH2_P','Ethernet_Pair2_N':'ETH2_N','Ethernet_Pair3_P':'ETH3_P','Ethernet_Pair3_N':'ETH3_N',
 'Ethernet_nLED2':'ETH_LED_LINK_N','Ethernet_nLED3':'ETH_LED_ACT_N','Fan_PWM':'FAN_PWM','Fan_Tacho':'FAN_TACH',
 'ID_SD':'HDRA_SDA','ID_SC':'HDRA_SCL','GPIO2':'DISP_SDA','GPIO3':'DISP_SCL','GPIO4':'TOUCH_INT_N','GPIO5':'TOUCH_RST_N','GPIO6':'DSI83_EN','GPIO7':'CM5_SPI_CE0',
 'GPIO8':'CM5_SPI_CE0X','GPIO9':'CM5_SPI_MISO','GPIO10':'CM5_SPI_MOSI','GPIO11':'CM5_SPI_SCK','GPIO12':'BL_PWM','GPIO13':'BTN_BL_PWM','GPIO14':'CM5_UART_TX','GPIO15':'CM5_UART_RX',
 'GPIO16':'PANEL_VDD_EN','GPIO17':'CM5_PWR_FAIL','GPIO18':'HDRA_SPI_CE0','GPIO19':'HDRA_SPI_MISO','GPIO20':'HDRA_SPI_MOSI','GPIO21':'HDRA_SPI_SCK',
 'GPIO22':'CM5_NRST','GPIO23':'CM5_SWCLK','GPIO24':'CM5_SWDIO','GPIO25':'CM5_MCU_IRQ','GPIO26':'CM5_HB','GPIO27':'CM5_BOOT0',
 'LED_nACT':'CM5_LED_ACT_N','LED_nPWR':'CM5_LED_PWR_N','PWR_Button':'CM5_PWR_BTN','PMIC_Enable':'CM5_PMIC_EN','EEPROM_nWP':'CM5_EEPROM_NWP'}
# fix GPIO7 = DSI83_IRQ, GPIO8 = SPI CE0
cma['GPIO7']='DSI83_IRQ'; cma['GPIO8']='CM5_SPI_CE0'
cm.p('genctl:RPi_CM5_A','CM5 (conn A)',cma,mpn='SC1xxx CM5 (variant TBD)')
cmb={'GND':'GND','USB3-0-RX_N':None,'USB3-0-RX_P':None,'USB3-0-DP':'USB30_DP','USB3-0-DM':'USB30_DM','USB3-0-TX_N':None,'USB3-0-TX_P':None,
 'USB3-1-DP':'USB31_DP','USB3-1-DM':'USB31_DM','USB_N':'USB_SVC_N','USB_P':'USB_SVC_P','VBUS_EN':None}
for l in ('D0','D1','D2','D3','C'):
    for pn in 'PN': cmb['MIPI0_%s_%s'%(l,pn)]='DSI_%s_%s'%(l,pn)
cm.p('genctl:RPi_CM5_B','CM5 (conn B)',cmb,mpn='CM5')
for _ in range(2): cm.C('22u','+5V_CM5','GND',pkg='1206')
dec(cm,'+5V_CM5',2); cm.C('100n','CM5_3V3','GND'); cm.C('1u','CM5_3V3','GND'); cm.C('100n','CM5_1V8','GND')
for a,b in (('CM5_SPI_SCK','MCU_SPI_SCK'),('CM5_SPI_MOSI','MCU_SPI_MOSI'),('CM5_SPI_MISO','MCU_SPI_MISO'),('CM5_SPI_CE0','MCU_SPI_NSS'),
            ('CM5_UART_TX','MCU_UART_RX'),('CM5_UART_RX','MCU_UART_TX'),('CM5_MCU_IRQ','MCU_IRQ')):
    _v='10k' if a in ('CM5_UART_RX','CM5_MCU_IRQ') else '1k'  # m7-sch FW-019: R56/R57 1k->10k (fixes_firmware.md s3.4)
    cm.R(_v,a,b,lcsc='C25804' if _v=='10k' else None,note=_v+' domain-boundary R: limits back-power injection when one side is unpowered; SPI <=4MHz')
cm.R('1k','CM5_VBAT','CM5_VBAT_D'); cm.p('Diode:BAT54C','BAT54C',{'1':'VBAT_CELL','2':None,'3':'CM5_VBAT_D'},prefix='D',mpn='BAT54C',note='CR2032 to CM5 RTC; 2nd anode unused')
cm.p('Switch:SW_Push','nRPIBOOT',{'1':'CM5_NRPIBOOT','2':'GND'},prefix='SW',mpn='TS-1187A-B-A-B')
cm.p('Switch:SW_Push','CM5 PWR',{'1':'CM5_PWR_BTN','2':'GND'},prefix='SW',mpn='TS-1187A-B-A-B',note='optional power button')
cm.R('1k','CM5_3V3','CM5_LED_ACT_A'); cm.LED('green','CM5_LED_ACT_A','CM5_LED_ACT_N',lcsc='C2297')
cm.R('1k','CM5_3V3','CM5_LED_PWR_A'); cm.LED('red','CM5_LED_PWR_A','CM5_LED_PWR_N',lcsc='C2295')
conn(cm,4,['GND','+5V','FAN_TACH','FAN_PWM'],'Fan header (SM04B)',mpn='SM04B-SRSS-TB')
cm.p('Connector_Generic:Conn_02x05_Odd_Even','Header A (CM5 I2C/SPI)',{'1':'CM5_3V3','2':'+5V','3':'HDRA_SDA','4':'HDRA_SCL','5':'HDRA_SPI_SCK','6':'HDRA_SPI_MOSI','7':'HDRA_SPI_MISO','8':'HDRA_SPI_CE0','9':'GND','10':'GND'},prefix='J')
cm.R('1k','CM5_HB','MCU_CM5_HB',note='1k domain-boundary R: heartbeat to MCU PC2_C')
cm.R('1k','CM5_BOOT0','BOOT0',note='1k boundary R; MCU 10k pull-down keeps BOOT0 low (0V) when CM5 off/Hi-Z; CM5 high -> 3.0V')
cm.R('10k','CM5_NRST','NRST_QB'); cm.R('100k','NRST_QB','GND',note='CM5 off/Hi-Z -> NPN off'); npn(cm,'NRST_QB','GND','NRST')
cm.R('10k','CM5_OFF','PMIC_QB'); cm.R('100k','PMIC_QB','GND',note='expander Hi-Z/unpowered -> CM5 on'); npn(cm,'PMIC_QB','GND','CM5_PMIC_EN')
cm.R('10k','CM5_PWRBTN_MCU','PBTN_QB'); cm.R('100k','PBTN_QB','GND'); npn(cm,'PBTN_QB','GND','CM5_PWR_BTN')
cm.R('10k','CM5_PWR_FAIL','CM5_3V3',note='PWR_FAIL high = running on hold-up (or CM5_3V3 alone)')
npn(cm,'HU_QB1','GND','CM5_PWR_FAIL'); cm.R('10k','HU_ST','HU_QB1'); cm.R('100k','HU_QB1','GND')
npn(cm,'HU_QB2','GND','PWR_FAIL_MCU'); cm.R('10k','HU_ST','HU_QB2'); cm.R('100k','HU_QB2','GND'); cm.R('10k','PWR_FAIL_MCU','+3V3_SAFE')
# CM5 5V hold-up: 2x20F 3.0V 85C supercap JIERONG JRCD3R0206N120030E (10F, ~4.9V = 2.45V/cell; was 2x HV1030 10F 65C) -> TPS61023 boost 4.85V -> TPS2121 IN2; IN1 = +5V priority
schottky(cm,'SS34','+5V','SC_CHG',mpn='SS34')
for _ in range(3): cm.R('150R','SC_CHG','SC_TOP',pkg='1206',note='3x150R = 50R charge limit (<=92mA, 0.14W each)')
cm.C('20F 3.0V','SC_TOP','SC_MID',pol=True,pkg='Capacitor_THT:CP_Radial_D12.5mm_P5.00mm',mpn='JRCD3R0206N120030E',lcsc='C7471020')
cm.C('20F 3.0V','SC_MID','GND',pol=True,pkg='Capacitor_THT:CP_Radial_D12.5mm_P5.00mm',mpn='JRCD3R0206N120030E',lcsc='C7471020')
cm.R('10k','SC_TOP','SC_MID',note='passive balance'); cm.R('10k','SC_MID','GND',note='passive balance')
cm.C('22u','SC_TOP','GND',pkg='1206')
cm.p('genctl:TPS61023DRLR','TPS61023DRLR',{'VIN':'SC_TOP','EN':'SC_TOP','FB':'HU_FB','GND':'GND','VOUT':'+5V_HU','SW':'HU_SW'},mpn='TPS61023DRLR',lcsc='C919459',note='hold-up boost 4.85V')
cm.p('Device:L','1u',{'1':'SC_TOP','2':'HU_SW'},prefix='L',mpn='FNR5020S1R0MT',lcsc='C167920',fp='genctl:L_FNR5020S',note='1uH 5A')
cm.R('715k','+5V_HU','HU_FB',note='Vout=0.595*(1+715/100)=4.85V'); cm.R('100k','HU_FB','GND')
for _ in range(2): cm.C('22u','+5V_HU','GND',pkg='1206')
cm.p('genctl:TPS2121RUXR','TPS2121RUXR',{'IN1':'+5V','IN2':'+5V_HU','PR1':'HU_PR1','CP2':'GND','OV1':'GND','OV2':'GND','GND':'GND','OUT':'+5V_CM5','ST':'HU_ST','ILM':'HU_ILM','SS':'HU_SS'},mpn='TPS2121RUXR',lcsc='C485916',note='IN1 priority >4.58V')
cm.R('33.2k','+5V','HU_PR1',note='PR1 1.06V -> IN1 valid >4.58V rising / 4.49V falling'); cm.R('10k','HU_PR1','GND')
cm.R('29.4k','HU_ILM','GND',note='ILIM ~3.5A'); cm.C('100n','HU_SS','GND'); cm.C('1u','+5V','GND'); cm.C('1u','+5V_HU','GND')
# m7-sch S-L2: EEPROM write-protect, R558 0R fitted (fixes_firmware.md Rev 2 s12)
cm.R('0','CM5_EEPROM_NWP','GND',ref='R558',mpn='0603WAF0000T5E',lcsc='C21189',mfr='UNI-ROYAL',note='FITTED; lift for bench EEPROM update')
# m7-sch FW-004/FW-028 (fixes_firmware.md s3.3)
cm.R('10k','CM5_OFF','GND',ref='R552',lcsc='C25804',note='CM5_OFF pull-down vs TCA9555 POR'); cm.R('10k','CM5_PWRBTN_MCU','GND',ref='R553',lcsc='C25804',note='CM5_PWRBTN_MCU pull-down vs TCA9555 POR')


# =====================================================================
co=S('comms','Comms: CAN x2, RS-485, Ethernet, USB hub/ports, router 12V',
 'COMMS. CAN1/CAN2 CA-IS3062W (VCC=+5V, 4.5-5.5V). Bus: CMC -> NUP2105L. CAN1: split termination (62R+62R, 4.7nF mid) via solder jumpers JP2/JP3, open by default. CAN2 (expansion bus J7): NO on-board termination (SW6/R92/R93/C92 deleted m7-step12; decision (Ethan): CAN2 is terminated by loose terminator plugs in the daughter-board sockets).\n'
 'RS-485 CA-IS2092W, SEL=GND_485 (3.3V VISO bus; DS: SEL=VISO only valid with VCC=5V), 120R term via solder jumper JP4 (open by default); no on-board bias. Shields -> CHASSIS via 1M||4.7nF.\n'
 'USB: CM5 USB2 OTG -> USB-C service/rpiboot (only external USB). CM5 USB3-0 HS -> internal header (display touch), USB3-1 HS -> internal spare header. No hub, no USB-A. No on-board modem: external router on RJ45, powered from ROUTER_12V.\n'
 'ROUTER_12V: TPS1H200A from +12V, ILIM 1.0k = 2.0A, default ON (100k pull-up), STM32 power-cycles via TCA9555 @0x25 P04.\n'
 'TERMINATION (solder jumpers, all OPEN by default): CAN1 JP2 (H) + JP3 (L); measure J6 powered off: about 60 ohm leave open, about 120 ohm bridge both. RS-485 JP4 (A to R102 120R, other end RS485_B): bridge only at a bus end. No on-board bias. CAN2: loose terminator plugs in the daughter-board sockets.')
for i,(tx,rx,iso) in enumerate((('CAN1_TX','CAN1_RX','GND_CAN1'),('CAN2_TX','CAN2_RX','GND_CAN2')),1):
    n='CAN%d'%i
    co.R('1k',tx,tx+'_T',note='domain-boundary R (SAFE MCU -> +5V transceiver)'); co.R('1k',rx+'_T',rx,note='domain-boundary R')
    co.p('genctl:CA-IS3062W','CA-IS3062W',{'VCC':'+5V','TXD':tx+'_T','RXD':rx+'_T','GND1':'GND','NC':None,'VISO':'VISO_%s'%n,'CANH':n+'_H','CANL':n+'_L','GND2':iso},mpn='CA-IS3062W')
    co.C('100n','+5V','GND'); co.C('10u','+5V','GND',pkg='0805'); co.C('100n','VISO_'+n,iso); co.C('47u','VISO_'+n,iso,pkg='1210',mpn='CL32A476KOJNNNE',lcsc='C2932477',mfr='Samsung',note='VISO 47uF per CA-IS3062W p15 (m7-sch FW-008, fixes_firmware.md s6)')
    co.p('genctl:ACT45B-510-2P','ACT45B-510-2P',{'1':n+'_H','4':n+'_HB','2':n+'_L','3':n+'_LB'},mpn='ACT45B-510-2P-TL003')
    co.p('Power_Protection:NUP2105L','NUP2105L',{'1':n+'_HB','2':n+'_LB','3':iso},prefix='D',mpn='NUP2105LT1G')
    if i==1:
        REFC['SW']+=1  # SW5 DIP deleted (m7-sch): replaced by open solder jumpers JP2 (H) / JP3 (L) per failsafe_latch.md L4
        co.p('Jumper:SolderJumper_2_Open','TERM_CAN1_H',{'1':n+'_HB','2':n+'_TH'},prefix='JP',ref='JP2',fp='genctl:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm',note='CAN1_HB to CAN1_TH (R87). Open by default (failsafe_latch.md L4)')
        co.p('Jumper:SolderJumper_2_Open','TERM_CAN1_L',{'1':n+'_LB','2':n+'_TL'},prefix='JP',ref='JP3',fp='genctl:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm',note='CAN1_LB to CAN1_TL (R88). Open by default (failsafe_latch.md L4)')
        co.R('62R',n+'_TH',n+'_TMID',pkg='1206'); co.R('62R',n+'_TL',n+'_TMID',pkg='1206'); co.C('4.7n',n+'_TMID',iso)
    else:  # CAN2: SW6, R92, R93, C92 deleted in m7-step12 (no on-board termination); refs reserved so later refs stay stable
        REFC['SW']+=1; REFC['R']+=2; REFC['C']+=1
    co.R('1M',n+'_SCR','CHASSIS',pkg='1206'); co.C('4.7n',n+'_SCR','CHASSIS',pkg='1206',note='2kV')
conn(co,4,['CAN1_HB','CAN1_LB','CAN1_SCR','GND_CAN1'],'CAN1 (PC 5/4)',mpn='Phoenix PC 5/4-GF')
co.p('genctl:TPS1H200AQDGNRQ1','TPS1H200AQDGNRQ1',{'VS':'+12V','IN':'EXP_12V_EN','DIAG_EN':'+3V3_SAFE','CL':'EXP12_CL','DELAY':None,'GND':'GND','EP':'GND','OUT':'EXP_12V','FAULT':'OUT_FAULT_N'},mpn='TPS1H200AQDGNRQ1')
co.R('1.33k','EXP12_CL','GND',note='ILIM ~1.5A (0.8*2500/I)'); co.C('100n','+12V','GND'); co.C('10n','EXP_12V','GND')
schottky(co,'SS110','GND','EXP_12V',mpn='SS110')
conn(co,6,['EXP_12V','GND','CAN2_HB','CAN2_LB','GND_CAN2','CAN2_SCR'],'Expansion bus (PC 5/6)',mpn='Phoenix PC 5/6-GF')
co.p('genctl:TPS1H200AQDGNRQ1','TPS1H200AQDGNRQ1',{'VS':'+12V','IN':'ROUTER_12V_EN','DIAG_EN':'+3V3_SAFE','CL':'RTR_CL','DELAY':None,'GND':'GND','EP':'GND','OUT':'ROUTER_12V','FAULT':'OUT_FAULT_N'},mpn='TPS1H200AQDGNRQ1')
co.R('1k','RTR_CL','GND',note='ILIM 2.0A (0.8*2500/I) for ~1.5A router'); co.R('100k','ROUTER_12V_EN','+3V3_SAFE',note='default ON at power-up')
co.C('100n','+12V','GND'); co.C('10n','ROUTER_12V','GND'); schottky(co,'SS110','GND','ROUTER_12V',mpn='SS110')
conn(co,2,['ROUTER_12V','GND'],'Router 12V (3.81/2)',mpn='WJ15EDGRC-3.81-02P')
for n in ('RS485_TX','RS485_RX','RS485_DE'): co.R('1k',n,n+'_T',note='domain-boundary R')
co.p('genctl:CA-IS2092W','CA-IS2092W',{'VCC':'+3V3','DI':'RS485_TX_T','RO':'RS485_RX_T','DE':'RS485_DE_T','~{RE}':'GND','GNDA':'GND','VISO':'VISO_485','SEL':'GND_485','A':'RS485_A','B':'RS485_B','GNDB':'GND_485','NC':None},mpn='CA-IS2092W')
co.C('100n','+3V3','GND'); co.C('10u','+3V3','GND',pkg='0805'); co.C('100n','VISO_485','GND_485'); co.C('10u','VISO_485','GND_485',pkg='0805')
co.R('10k','RS485_DE_T','GND')
co.p('Diode:SM712_SOT23','SM712',{'1':'RS485_A','2':'RS485_B','3':'GND_485'},prefix='D',mpn='SM712')
REFC['SW']+=1  # SW7 DIP deleted (m7-sch): replaced by open solder jumper JP4 in series A -> TA; R102 other end on RS485_B (failsafe_latch.md L4)
co.p('Jumper:SolderJumper_2_Open','TERM_485',{'1':'RS485_A','2':'RS485_TA'},prefix='JP',ref='JP4',fp='genctl:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm',note='RS485_A to RS485_TA (R102 120R; R102 other end on RS485_B). Open by default (failsafe_latch.md L4)')
co.R('120R','RS485_TA','RS485_B',pkg='1206')
REFC['SW']+=1; REFC['R']+=2  # SW8 + R103/R104 fail-safe bias deleted (m7-sch, failsafe_latch.md L4: no on-board bias); refs reserved
conn(co,3,['RS485_A','RS485_B','GND_485'],'RS-485 (PC 5/3)',mpn='Phoenix PC 5/3-GF')
# Ethernet (gigabit)
co.p('genctl:HR963380AE','HR963380AE',{'TRD0+':'ETH0_P','TRD0-':'ETH0_N','TRD1+':'ETH1_P','TRD1-':'ETH1_N','TRD2+':'ETH2_P','TRD2-':'ETH2_N','TRD3+':'ETH3_P','TRD3-':'ETH3_N',
    'CT':'ETH_CT','LED_G_A':'ETH_LEDG_A','LED_G_K':'ETH_LED_LINK_N','LED_O_A':'ETH_LEDY_A','LED_O_K':'ETH_LED_ACT_N','SHIELD':'CHASSIS'},mpn='HR963380AE',
    note='1000BASE-T magjack, vertical top-entry (opening faces the rear shell window); pair order P1/2,P3/4,P7/8,P9/10 = MDI A-D; polarity auto-corrected by PHY')
co.C('100n','ETH_CT','GND',note='voltage-mode PHY: centre taps AC-decoupled only'); co.C('10n','ETH_CT','GND')
co.R('330R','CM5_3V3','ETH_LEDG_A'); co.R('330R','CM5_3V3','ETH_LEDY_A')
co.p('genctl:RClamp0524P','RClamp0524P',{'IO1':'ETH0_P','IO2':'ETH0_N','IO3':'ETH1_P','IO4':'ETH1_N','GND':'GND'},mpn='RCLAMP0524P.TCT')
co.p('genctl:RClamp0524P','RClamp0524P',{'IO1':'ETH2_P','IO2':'ETH2_N','IO3':'ETH3_P','IO4':'ETH3_N','GND':'GND'},mpn='RCLAMP0524P.TCT')
# USB-C service
co.p('Connector:USB_C_Receptacle_USB2.0_16P','USB-C service',{'VBUS':'USBC_VBUS','CC1':'USBC_CC1','CC2':'USBC_CC2','D+':'USB_SVC_P','D-':'USB_SVC_N','GND':'GND','SHIELD':'CHASSIS','SBU1':None,'SBU2':None},prefix='J',mpn='TYPE-C-31-D-06B')
co.R('5.1k','USBC_CC1','GND'); co.R('5.1k','USBC_CC2','GND')
co.p('Power_Protection:USBLC6-2SC6','USBLC6-2SC6',{'1':'USB_SVC_P','6':'USB_SVC_P','3':'USB_SVC_N','4':'USB_SVC_N','5':'USBC_VBUS','2':'GND'},prefix='D',mpn='USBLC6-2SC6')
# Internal USB2 headers direct from CM5 USB3-0/USB3-1 HS pairs (no hub, no USB-A host). SS pairs NC.
for i,(dm,dp,lab) in enumerate((('USB30_DM','USB30_DP','Internal USB0 touch (SM04B)'),('USB31_DM','USB31_DP','Internal USB1 spare (SM04B)'))):
    vb='USB%d_5V'%i; en='USB%d_EN'%i; il='USB%d_ILIM'%i
    # rev h: TPS2553 current-limited switch per header; 40.2k -> ~0.68A nom (>0.5A USB2), FAULT -> OUT_FAULT_N, EN from TCA9555 @0x25 (default ON)
    co.p('genctl:TPS2553DBVR','TPS2553DBVR',{'IN':'+5V','GND':'GND','EN':en,'FAULT':'OUT_FAULT_N','ILIM':il,'OUT':vb},mpn='TPS2553DBVR')
    co.R('40.2k',il,'GND',note='IOS = 25230/R^0.977 ~ 0.68A'); co.R('100k',en,'+3V3_SAFE',note='default ON')
    co.C('1u','+5V','GND',pkg='0603'); co.C('10u',vb,'GND',pkg='0805')
    conn(co,4,[vb,dm,dp,'GND'],lab,mpn='SM04B-SRSS-TB')
    co.p('Power_Protection:USBLC6-2SC6','USBLC6-2SC6',{'1':dp,'6':dp,'3':dm,'4':dm,'5':vb,'2':'GND'},prefix='D',mpn='USBLC6-2SC6')
# m7-sch FW-015 (fixes_firmware.md s2, extra)
co.R('100k','EXP_12V_EN','GND',ref='R551',lcsc='C25803',note='EXP_12V_EN pull-down')


# =====================================================================
di=S('display','Display: DSI->LVDS bridge, panel power, backlight, touch',
 'DISPLAY RVT121HVLNWCA0-B. SN65DSI83 (1.8V TLV75518, ADDR=0 -> 0x2C). Panel VDD and touch power via TPS22918.\n'
 'Backlight TPS61500 (VIN +12V, DS max 18V): EN=BL_PWM (PWM dim), FREQ 180k (~540kHz), OVP 232k/10k = 29.7V, Rsense 2x1.1R (~364mA), L 10uH, SS36.')
di.p('genctl:TLV75518PDBVR','TLV75518PDBVR',{'IN':'+3V3','EN':'+3V3','GND':'GND','OUT':'+1V8_DSI','NC':None},mpn='TLV75518PDBVR')
di.C('1u','+3V3','GND'); di.C('1u','+1V8_DSI','GND')
dsi={'DA0P':'DSI_D0_P','DA0N':'DSI_D0_N','DA1P':'DSI_D1_P','DA1N':'DSI_D1_N','DA2P':'DSI_D2_P','DA2N':'DSI_D2_N','DA3P':'DSI_D3_P','DA3N':'DSI_D3_N','DACP':'DSI_C_P','DACN':'DSI_C_N',
 'SCL':'DISP_SCL_1V8','SDA':'DISP_SDA_1V8','ADDR':'GND','EN':'DSI83_EN_1V8','IRQ':'DSI83_IRQ_1V8','REFCLK':'DSI83_REFCLK','RSVD1':None,'RSVD2':None,
 'A_Y0P':'LVDS0_P','A_Y0N':'LVDS0_N','A_Y1P':'LVDS1_P','A_Y1N':'LVDS1_N','A_Y2P':'LVDS2_P','A_Y2N':'LVDS2_N','A_Y3P':'LVDS3_P','A_Y3N':'LVDS3_N','A_CLKP':'LVDSC_P','A_CLKN':'LVDSC_N',
 'VCC':'+1V8_DSI','VCORE':'DSI83_VCORE','GND':'GND','NC':None}
di.p('genctl:SN65DSI83ZXHR','SN65DSI83ZXHR',dsi,mpn='SN65DSI83ZXHR')
dec(di,'+1V8_DSI',4); di.C('10u','+1V8_DSI','GND',pkg='0805'); di.C('1u','DSI83_VCORE','GND')
di.R('10k','DSI83_REFCLK','GND',note='REFCLK unused (clock from DSI): 10k to GND');
# Optional external REFCLK (DNP). Default build: 10k to GND as above (datasheet: unused REFCLK must be pulled to GND by a resistor), clock from DSI CLK lane.
# Fit Y? + R? (22R series, near source) + C? when the Pi DSI clock is not continuous / its PLL causes panel flicker; then set CSR 0x0A.0 HS_CLK_SRC=0 and REFCLK_MULTIPLIER.
# SN65DSI83 REFCLK: 25-154 MHz, 1.8 V CMOS (abs max 2.175 V), <=50 ps p-p jitter, 40-60 % duty -> oscillator must run from +1V8_DSI. 10k pull-down may stay fitted.
di.p('Oscillator:ASDMB-xxxMHz','25MHz',{'1':'+1V8_DSI','4':'+1V8_DSI','2':'GND','3':'DSI83_REFCLK_OSC'},prefix='Y',ref='Y4',mpn='ASDMB-25.000MHZ-LC-T',fp='Oscillator:Oscillator_SMD_Abracon_ASDMB-4Pin_2.5x2.0mm',dnp=True,note='DNP option: 25 MHz 1.8 V CMOS oscillator for DSI83 REFCLK (Pi DSI PLL flicker risk)')
di.R('22R','DSI83_REFCLK_OSC','DSI83_REFCLK',dnp=True,ref='R531',note='DNP option: REFCLK series R at the oscillator (0R-22R)'); di.C('100n','+1V8_DSI','GND',dnp=True,ref='C286',note='DNP: REFCLK oscillator decoupling')
di.R('100k','DSI83_EN','GND',note='GPIO6 3.3 V side pulldown (R114)'); di.C('10n','DSI83_EN_1V8','GND',note='C116: EN RC delay at U21.B1 (1.8 V side)'); di.R('100k','DSI83_IRQ_1V8','GND',note='R115: IRQ 1.8 V side pulldown (was 10k to CM5_3V3 = 3.3 V on a 1.8 V pin, review C1)')
di.p('genctl:TPS22918DBVR','TPS22918DBVR',{'VIN':'+3V3','ON':'PANEL_VDD_EN','CT':'PNL_CT','GND':'GND','VOUT':'+3V3_PANEL','QOD':'+3V3_PANEL'},mpn='TPS22918DBVR',note='panel VDD switch')
di.C('1n','PNL_CT','GND'); di.R('100k','PANEL_VDD_EN','GND'); di.C('10u','+3V3_PANEL','GND',pkg='0805')
di.p('genctl:TPS22918DBVR','TPS22918DBVR',{'VIN':'+3V3','ON':'PANEL_VDD_EN','CT':'TCH_CT','GND':'GND','VOUT':'+3V3_TOUCH','QOD':'+3V3_TOUCH'},mpn='TPS22918DBVR',note='touch power switch')
di.C('1n','TCH_CT','GND'); di.C('1u','+3V3_TOUCH','GND')
lv=['NC']*40
for p in (2,3,4): lv[p-1]='+3V3_PANEL'
for p in (6,7,10,13,16,19,22,25,28,31,32,33): lv[p-1]='GND'
for p,n in ((8,'LVDS0_N'),(9,'LVDS0_P'),(11,'LVDS1_N'),(12,'LVDS1_P'),(14,'LVDS2_N'),(15,'LVDS2_P'),(17,'LVDSC_N'),(18,'LVDSC_P'),(20,'LVDS3_N'),(21,'LVDS3_P')): lv[p-1]=n
conn(di,40,[None if x=='NC' else x for x in lv],'LVDS FPC 40p 0.5mm',mpn='FPC 40P 0.5mm (BOM)',note='RVT121 LVDS pin map per DS; other pins NC')
conn(di,10,['GND',None,None,None,'GND','+3V3_TOUCH','TOUCH_RST_N','DISP_SCL','TOUCH_INT_N','DISP_SDA'],'Touch FPC 10p 0.5mm',mpn='FPC 10P 0.5mm',note='USB touch pins (2-4) unused - I2C mode')
di.R('10k','TOUCH_RST_N','+3V3_TOUCH'); di.R('10k','TOUCH_INT_N','+3V3_TOUCH')
di.R('2.2k','DISP_SCL_1V8','+1V8_DSI',note='R119: DSI83 SCL pull-up, 1.8 V side of U77 (3.3 V side uses CM5 1.8k on-module pull-ups)'); di.R('2.2k','DISP_SDA_1V8','+1V8_DSI',note='R120')
# ---- Review C1 fix: SN65DSI83 CMOS I/O is 1.8 V (abs max 2.175 V, SLLSEC1I); CM5 GPIO_VREF stays 3.3 V -> translate. Fixed refs keep annotation stable.
# I2C: PCA9306 (SCPS113O Fig 8-1: EN tied to VREF2, 200k to VCC2, 100 pF filter at VREF2). VREF1 = +1V8_DSI (1.2 V..VREF2-0.6 V ok).
di.p('Interface:PCA9306DC','PCA9306DCUR',{'1':'GND','2':'+1V8_DSI','3':'DISP_SCL_1V8','4':'DISP_SDA_1V8','5':'DISP_SDA','6':'DISP_SCL','7':'PCA_VREF2','8':'PCA_VREF2'},ref='U77',mpn='PCA9306DCUR',lcsc='C33196',fp='Package_SO:VSSOP-8_2.3x2mm_P0.5mm',note='DSI83 I2C 1.8V<->3.3V translator (review C1)')
di.R('200k','PCA_VREF2','CM5_3V3',ref='R532',note='PCA9306 VREF2/EN bias (SCPS113O 200k)'); di.C('100p','PCA_VREF2','GND',ref='C287',note='PCA9306 VREF2 filter (SCPS113O 100 pF)'); di.C('100n','+1V8_DSI','GND',ref='C288',note='U77 VREF1 decoupling')
# EN: SN74LVC1T45 (SCES515N) DIR high = A->B, DIR referenced to VCCA. A=GPIO6 3.3 V, B=U21.EN 1.8 V. Either VCC at 0 V -> Hi-Z, R533 holds EN low.
di.p('Logic_LevelTranslator:SN74LVC1T45DBV','SN74LVC1T45DBVR',{'1':'CM5_3V3','2':'GND','3':'DSI83_EN','4':'DSI83_EN_1V8','5':'CM5_3V3','6':'+1V8_DSI'},ref='U78',mpn='SN74LVC1T45DBVR',lcsc='C7843',note='DSI83 EN 3.3V->1.8V (review C1)')
di.R('47k','DSI83_EN_1V8','GND',ref='R533',note='EN held low while translator Hi-Z / +1V8_DSI ramps (U21 internal 200k pull-up)'); di.C('100n','CM5_3V3','GND',ref='C289'); di.C('100n','+1V8_DSI','GND',ref='C290')
# IRQ: SN74LVC1T45 A=U21.IRQ (1.8 V push-pull/Hi-Z, active high), B=GPIO7 3.3 V; DIR tied to VCCA (+1V8_DSI) = A->B.
di.p('Logic_LevelTranslator:SN74LVC1T45DBV','SN74LVC1T45DBVR',{'1':'+1V8_DSI','2':'GND','3':'DSI83_IRQ_1V8','4':'DSI83_IRQ','5':'+1V8_DSI','6':'CM5_3V3'},ref='U79',mpn='SN74LVC1T45DBVR',lcsc='C7843',note='DSI83 IRQ 1.8V->3.3V (review C1)')
di.C('100n','+1V8_DSI','GND',ref='C291'); di.C('100n','CM5_3V3','GND',ref='C292')
# REFCLK: stock Linux sn65dsi83 driver always sets HS_CLK_SRC=1 (DSI clock) -> Y4/R531/C286 stay a DNP footprint option only; R113 10k REFCLK->GND fitted (SLLSEC1I p.5). No buffer.
di.p('genctl:TPS61500PWPR','TPS61500PWPR',{'VIN':'+12V','EN':'BL_PWM','DIMC':'BL_DIMC','SS':'BL_SS','FREQ':'BL_FREQ','COMP':'BL_COMP','AGND':'GND','EP':'GND','SW':'BL_SW','OVP':'BL_OVP','FB':'BL_FB','PGND':'GND'},mpn='TPS61500PWPR')
di.R('100k','BL_PWM','GND'); di.C('1u','BL_DIMC','GND'); di.C('47n','BL_SS','GND'); di.R('180k','BL_FREQ','GND',note='DS FREQ eq. -> ~540kHz'); di.C('470n','BL_COMP','GND',note='DS recommended for PWM dimming')
di.p('Device:L','10u',{'1':'+12V','2':'BL_SW'},prefix='L',mpn='SWPA6045S100MT',lcsc='C79272',fp='genctl:L_SWPA6045S',note='10uH per DS range (4.7-22uH)'); schottky(di,'SS36','BL_SW','VLED',mpn='SS36'); di.parts[-1].lcsc='C16015'; di.parts[-1].fp='Diode_SMD:D_SMA'
for _ in range(2): di.C('10u','+12V','GND',pkg='0805')
for _ in range(2): di.C('4.7u','VLED','GND',pkg='1206',note='50V')
di.R('232k','VLED','BL_OVP'); di.R('10k','BL_OVP','GND')
di.R('1.1R','BL_FB','GND',pkg='0805'); di.R('1.1R','BL_FB','GND',pkg='0805')
conn(di,2,['VLED','BL_FB'],'Backlight (JST SM02B-BHSS)',mpn='SM02B-BHSS-1-TB',lcsc='C485339',note='1 LEDA, 2 LEDK')

# =====================================================================
inp=S('inputs','Inputs: 6 AI, 12 DI, MPU, D+, E-stop sense, VBAT sense',
 'INPUTS. AI: 1mA PNP current source (LM4040 2.5V ref from VBAT_P, LM2904, 2.49k), BSS84 disable; 4-20mA via 100R + DMN6075S shunt switch;\n'
 '100k/18k divider to VMID(1.65V) -> ADS1115 x2 (0x48/0x49). DI: 68k/33k + 100nF -> 74HC14; bank bias via SI2309 (pull-up) / DMN6075S (pull-down).\n'
 'MPU: 10k series, 1M bias to VMID, LM393 w/ hysteresis -> TIM2_CH1. D+: LM317 125mA source (10R) + SS110, sense 100k/10k.')
conn(inp,6,['AI1','AI2','AI3','AI4','AI5','AI6'],'J1A analog in (PC 5/6)',mpn='Phoenix PC 5/6-GF')
conn(inp,6,['COM_A','COM_B','MPU_P','MPU_N','GND',None],'J1B COM/MPU (PC 5/6)',note='MPU screen (pin5) -> 0V assumed')
conn(inp,6,['DI1','DI2','DI3','DI4','DI5','DI6'],'J2A DI1-6'); conn(inp,6,['DI7','DI8','DI9','DI10','DI11','DI12'],'J2B DI7-12')
conn(inp,6,['ESTOP_SENSE','GND','DPLUS','VBAT_SENSE','GND','DI_BIAS_A'],'J3A E-stop/D+/VBAT/bias',note='ESTOP_RTN & VBAT_SENSE- tied to 0V (assumed); BIAS_A = DI bank A bias out')
conn(inp,6,['DI_BIAS_B',None,None,None,None,None],'J3B')
# VMID
inp.R('10k','+3V3','VMID_REF'); inp.R('10k','VMID_REF','GND'); inp.C('100n','VMID_REF','GND')
inp.p('Amplifier_Operational:TLV9062','TLV9062',{'3':'VMID_REF','2':'VMID','1':'VMID','5':'GND','6':'VMID_SP','7':'VMID_SP','8':'+3V3','4':'GND'},prefix='U',mpn='TLV9062IDR',note='unit B spare as follower to GND')
inp.C('1u','VMID','GND'); dec(inp,'+3V3')
# AI ref
inp.p('Reference_Voltage:LM4040DBZ-2.5','LM4040A25',{'K':'VBAT_P','A':'AI_VSET'},prefix='D',mpn='LM4040A25IDBZR')
inp.R('10k','AI_VSET','GND',pkg='1206',note='ref bias ~1-2.8mA')
inp.C('100n','VBAT_P','AI_VSET')
ADC={1:('ADC1','AIN0'),2:('ADC1','AIN1'),3:('ADC1','AIN2'),4:('ADC2','AIN0'),5:('ADC2','AIN1'),6:('ADC2','AIN2')}
oas={}
for ch in range(1,7):
    a='AI%d'%ch
    tvs(inp,'SMAJ36CA',a); inp.C('100n',a,'GND',pkg='1206',note='100V')
    inp.R('2.49k','VBAT_P',a+'_E',pkg='1206',lcsc='C319805',mpn='AR06BTCV2491',note='0.1% 1mA set'); pnp(inp,a+'_B',a+'_E',a+'_C')
    inp.p('Diode:1N4148W','1N4148W',{'A':a+'_C','K':a+'_D'},prefix='D',mpn='1N4148W'); inp.R('1k',a+'_D',a)
    inp.R('10k','AI_VSET',a+'_REF')
    fet(inp,'Transistor_FET:BSS84','BSS84',a+'_PG','VBAT_P',a+'_REF')
    inp.R('100k','VBAT_P',a+'_PG'); inp.R('100k',a+'_PG',a+'_PGC'); npn(inp,a+'_NB','GND',a+'_PGC')
    inp.R('10k','AI_CS_DIS%d'%ch,a+'_NB'); inp.R('100k',a+'_NB','GND')
    inp.R('100R',a,a+'_SH',pkg='1206',note='4-20mA shunt 0.1%'); fet(inp,'Transistor_FET:DMN6075S','DMN6075S','AI_SH_EN%d'%ch,'GND',a+'_SH')
    inp.R('100k','AI_SH_EN%d'%ch,'GND')
    inp.R('100k',a,a+'_ADC',note='0.1%'); inp.R('18k',a+'_ADC','VMID',note='0.1%'); inp.C('100n',a+'_ADC','GND'); clamp(inp,a+'_ADC')
    oas.setdefault((ch-1)//2,[]).append(a)
# op-amps LM2904 (3 packages, 2 ch each): unit A pins 1 out,2 -,3 +; unit B 7 out,6 -,5 +
for k,chs in oas.items():
    c={'8':'VBAT_P','4':'GND'}
    for (o,m,pl),a in zip((('1','2','3'),('7','6','5')),chs):
        c[o]=a+'_B'; c[m]=a+'_E'; c[pl]=a+'_REF'
    inp.p('Amplifier_Operational:LM2904','LM2904',c,prefix='U',mpn='LM2904BIDR'); inp.C('100n','VBAT_P','GND',pkg='0805')
for nm in ('COM_A','COM_B'):
    tvs(inp,'SMAJ36CA',nm); inp.C('100n',nm,'GND',pkg='1206')
    inp.R('100k',nm,nm+'_ADC'); inp.R('18k',nm+'_ADC','VMID'); inp.C('100n',nm+'_ADC','GND'); clamp(inp,nm+'_ADC')
inp.p('Analog_ADC:ADS1115IDGS','ADS1115 @0x48',{'ADDR':'GND','ALERT/RDY':None,'GND':'GND','AIN0':'AI1_ADC','AIN1':'AI2_ADC','AIN2':'AI3_ADC','AIN3':'COM_A_ADC','VDD':'+3V3','SDA':'I2C1_SDA','SCL':'I2C1_SCL'},prefix='U',mpn='ADS1115IDGSR')
inp.p('Analog_ADC:ADS1115IDGS','ADS1115 @0x49',{'ADDR':'+3V3','ALERT/RDY':None,'GND':'GND','AIN0':'AI4_ADC','AIN1':'AI5_ADC','AIN2':'AI6_ADC','AIN3':'COM_B_ADC','VDD':'+3V3','SDA':'I2C1_SDA','SCL':'I2C1_SCL'},prefix='U',mpn='ADS1115IDGSR')
dec(inp,'+3V3',2)
# expander 0x22
ex={}
for ch in range(1,7): ex['P0%d'%(ch-1) if ch<=8 else '']='AI_CS_DIS%d'%ch
ex.update({'P06':'AI_SH_EN1','P07':'AI_SH_EN2','P10':'AI_SH_EN3','P11':'AI_SH_EN4','P12':'AI_SH_EN5','P13':'AI_SH_EN6','P14':'DI_PU_A','P15':'DI_PU_B','P16':'DI_PD_A','P17':'DI_PD_B'})
tca(inp,2,ex)
# DI bank bias
for b in 'AB':
    fet(inp,'Transistor_FET:AO3401A','SI2309CDS','DIB_%s_PG'%b,'VBAT_P','DI_BIAS_'+b,mpn='SI2309CDS-T1-GE3')
    inp.R('100k','VBAT_P','DIB_%s_PG'%b); inp.R('100k','DIB_%s_PG'%b,'DIB_%s_PGC'%b); npn(inp,'DIB_%s_NB'%b,'GND','DIB_%s_PGC'%b)
    inp.R('10k','DI_PU_'+b,'DIB_%s_NB'%b); inp.R('100k','DIB_%s_NB'%b,'GND')
    fet(inp,'Transistor_FET:DMN6075S','DMN6075S','DI_PD_'+b,'GND','DI_BIAS_'+b); inp.R('100k','DI_PD_'+b,'GND')
# Schmitt inputs: list of (input node, output net)
st=[]
for n in range(1,13):
    d='DI%d'%n; tvs(inp,'SMAJ36CA',d); inp.C('100n',d,'GND',pkg='1206')
    inp.R('4.7k','DI_BIAS_'+('A' if n<=6 else 'B'),d,pkg='1206',note='wetting')
    inp.R('68k',d,d+'_D'); inp.R('33k',d+'_D','GND'); inp.C('100n',d+'_D','GND')
    st.append((d+'_D','DI%d_N'%n))
tvs(inp,'SMAJ36CA','ESTOP_SENSE'); inp.C('100n','ESTOP_SENSE','GND',pkg='1206'); inp.R('4.7k','ESTOP_SENSE','GND',pkg='1206',note='wetting/pull-down')
inp.R('68k','ESTOP_SENSE','ESTOP_SENSE_D'); inp.R('33k','ESTOP_SENSE_D','GND'); inp.C('100n','ESTOP_SENSE_D','GND'); st.append(('ESTOP_SENSE_D','ESTOP2_DIG'))
inp.R('68k','DPLUS','DPLUS_D'); inp.R('33k','DPLUS_D','GND'); inp.C('100n','DPLUS_D','GND'); st.append(('DPLUS_D','DPLUS_DIG'))
inp.R('68k','VBAT_ESTOP','VESTOP_D'); inp.R('33k','VESTOP_D','GND'); inp.C('10n','VESTOP_D','GND'); st.append(('VESTOP_D','ESTOP_DIG'))
while len(st)<18: st.append(('GND',None))
gates=[('1','2'),('3','4'),('5','6'),('9','8'),('11','10'),('13','12')]
for k in range(3):
    c={'14':'+3V3','7':'GND'}
    for (i,o),(a,y) in zip(gates,st[k*6:(k+1)*6]): c[i]=a; c[o]=y
    inp.p('74xx:74HC14','74HC14',c,prefix='U',mpn='SN74HC14PWR',note='HC14 inputs see up to ~12V at 36V in (68k/33k) - relies on input clamp; review'); inp.C('100n','+3V3','GND')
# MPU
for s_,n in (('MPU_P','MPU_PC'),('MPU_N','MPU_NC')):
    tvs(inp,'SMBJ58CA',s_); inp.R('10k',s_,n,pkg='1206'); inp.R('1M',n,'VMID'); clamp(inp,n)
inp.C('1n','MPU_PC','MPU_NC')
inp.p('Comparator:LM393','LM393',{'3':'MPU_PH','2':'MPU_NC','1':'MPU_SPEED','5':'MPU_PC','6':'VMID','7':'MPU_GATE','8':'+3V3','4':'GND'},prefix='U',mpn='LM393DR')
inp.R('10k','MPU_PC','MPU_PH'); inp.R('1M','MPU_SPEED','MPU_PH',note='hysteresis')
inp.R('2.2k','MPU_SPEED','+3V3'); inp.R('2.2k','MPU_GATE','+3V3'); inp.C('100n','+3V3','GND')
# D+
tvs(inp,'SMBJ36CA','DPLUS'); inp.C('100n','DPLUS','GND',pkg='1206')
fet(inp,'Transistor_FET:AO3401A','SI2309CDS','DPX_PG','VBAT_P','DPX_VI',mpn='SI2309CDS-T1-GE3')
inp.R('100k','VBAT_P','DPX_PG'); inp.R('100k','DPX_PG','DPX_PGC'); npn(inp,'DPX_NB','GND','DPX_PGC'); inp.R('10k','DPLUS_EXC_EN','DPX_NB'); inp.R('100k','DPX_NB','GND')
inp.p('Regulator_Linear:LM317_TO-252','LM317M',{'VI':'DPX_VI','VO':'DPX_VO','ADJ':'DPX_ADJ'},prefix='U',mpn='LM317MDT-TR',note='125mA current source')
inp.R('10R','DPX_VO','DPX_ADJ',pkg='2512',note='1W'); inp.C('100n','DPX_VI','GND',pkg='0805')
schottky(inp,'SS110','DPX_ADJ','DPLUS',mpn='SS110')
inp.R('100k','DPLUS','DPLUS_SNS'); inp.R('10k','DPLUS_SNS','GND'); inp.C('100n','DPLUS_SNS','GND'); clamp(inp,'DPLUS_SNS','BAT54S')
tvs(inp,'SMAJ36CA','VBAT_SENSE'); inp.R('100k','VBAT_SENSE','VBAT_SNS',note='0.1%'); inp.R('10k','VBAT_SNS','GND',note='0.1%'); inp.C('100n','VBAT_SNS','GND'); clamp(inp,'VBAT_SNS','BAT54S')

# =====================================================================
ou=S('outputs','Outputs: fuel/crank (TPS48100), 15x TPS1HTC30, watchdog gating, readback',
 'OUTPUTS. All MCU enables gated by TPS3431 WDO (LVC1G08 for fuel/crank/glow, LVC541 OE for the rest). Fuel/crank: TPS48100 + 2x BSC070N10NS5 + 1mR shunt +\n'
 'INA281A2 from VBAT_ESTOP. Small outputs TPS1HTC30 from VBAT_P: ILIM 40.2k, SNS 1.1k -> TMUX1208 -> ADC. Readback via NPN to TCA9555 @0x23.')
ou.p('genctl:TPS3431SDRBR','TPS3431SQDRBRQ1',{'VDD':'+3V3','EN':'+3V3','SET1':'+3V3','CWD':'WD_CWD','WDI':'WDI','GND':'GND','EP':'GND','WDO':'WDO_N','ENOUT':None},mpn='TPS3431SQDRBRQ1',lcsc='C2878091')
ou.R('10k','WD_CWD','+3V3',note='CWD via 10k to VDD = factory timing (assumed)'); ou.R('10k','WDO_N','+3V3'); ou.C('100n','+3V3','GND')
npn(ou,'WD_INV_B','GND','WD_OE_N'); ou.R('10k','WD_OK','WD_INV_B'); ou.R('100k','WD_INV_B','GND'); ou.R('10k','WD_OE_N','+3V3')
for n in ('FUEL','CRANK','GLOW'):
    ou.p('74xGxx:74LVC1G08','74LVC1G08',{'1':n+'_EN_MCU','2':'WD_OK','4':n+'_EN','5':'+3V3','3':'GND'},prefix='U',mpn='SN74LVC1G08DBVR'); ou.C('100n','+3V3','GND'); ou.R('100k',n+'_EN','GND')
small=['GCB_CL','GCB_OP','MCB_CL','MCB_OP']+['AUX%d'%i for i in range(1,11)]
for k in range(2):
    grp=small[k*8:(k+1)*8]; c={'~{OE1}':'WD_OE_N','~{OE2}':'WD_OE_N','VCC':'+3V3','GND':'GND'}
    for i in range(8):
        if i<len(grp): c['A%d'%(i+1)]=grp[i]+'_MCU'; c['Y%d'%(i+1)]=grp[i]+'_EN'
        else: c['A%d'%(i+1)]='GND'; c['Y%d'%(i+1)]=None
    ou.p('genctl:SN74LVC541APWR','SN74LVC541APWR',c,mpn='SN74LVC541APWR'); ou.C('100n','+3V3','GND')
for n in small: ou.R('100k',n+'_EN','GND')
# fuel / crank
for n in ('FUEL','CRANK'):
    ou.p('genctl:TPS48100QDGXRQ1','TPS48100QDGXRQ1',{'VS':'VBAT_ESTOP','EN/UVLO':n+'_UVLO','INP1':n+'_EN','INP2':'GND','CS_SEL':'GND','ISCP':n+'_ISCP','TMR':n+'_TMR','SCP_TEST':'GND','GND':'GND','NC':None,
        'CS+':'VBAT_ESTOP','CS-':n+'_DRN','G1PU':n+'_GPU','G1PD':n+'_GPD','G2':None,'BST':n+'_BST','SRC':n+'_OUT','FLT':'OUT_FAULT_N'},mpn='TPS48100QDGXRQ1')
    ou.R('100k','VBAT_ESTOP',n+'_UVLO'); ou.R('27k',n+'_UVLO','GND'); ou.R('35.7k',n+'_ISCP','GND',note='RISCP to GND per DS eq.5: Isc=(35.7k*2uA+19mV)/1mR = 90A'); ou.C('68n',n+'_TMR','GND')
    ou.C('470n',n+'_BST',n+'_OUT'); ou.C('100n','VBAT_ESTOP','GND',pkg='0805')
    ou.R('10R',n+'_GPU',n+'_G'); ou.R('0R',n+'_GPD',n+'_G')
    ou.R('1m','VBAT_ESTOP',n+'_DRN',pkg='2512',mpn='WSLP25121L000FEA',lcsc='C844705',mfr='Vishay',note='shunt')  # R297/R303: manual sch edit 32b12c7/7eaa27d folded into design.py
    for _ in range(2): fet(ou,'Transistor_FET:BSC070N10NS5','BSC070N10NS5',n+'_G',n+'_OUT',n+'_DRN')
    ou.p('Amplifier_Current:INA281A1','INA281A1',{'OUT':n+'_ISNS','GND':'GND','Vin+':'VBAT_ESTOP','Vin-':n+'_DRN','V+':'+3V3'},prefix='U',mpn='INA281A1QDBVRQ1',lcsc='C2862615')  # m7-sch FW-011 gain 20; ou.C('100n','+3V3','GND')
    tvs(ou,'SMBJ33CA',n+'_OUT')
schottky(ou,'SK1010C','GND','FUEL_CLMP',mpn='SK1010C'); tvs(ou,'SMDJ24A','FUEL_CLMP','FUEL_OUT',uni=True)
schottky(ou,'SK1010C','GND','CRANK_OUT',mpn='SK1010C')
# small outputs
outs=['GLOW']+small
mux={}
for i,n in enumerate(outs):
    ou.p('genctl:TPS1HTC30QPWPRQ1','TPS1HTC30QPWPRQ1',{'VS':'VBAT_P','EN':n+'_EN','DIAG_EN':'DIAG_EN','LATCH':'GND','ILIM':n+'_ILIM','GND':'GND','VOUT':n+'_OUT','SNS':n+'_SNS','FAULT':'OUT_FAULT_N','NC':None,'EP':'GND'},mpn='TPS1HTC30QPWPRQ1')
    ou.R('40.2k',n+'_ILIM','GND'); ou.R('1.1k',n+'_SNS','GND'); ou.R('1k',n+'_SNS',n+'_SNSM'); ou.C('100n','VBAT_P','GND',pkg='0805')
    schottky(ou,'SS110','GND',n+'_OUT',mpn='SS110'); tvs(ou,'SMBJ33CA',n+'_OUT')
    mux[n]=n+'_SNSM'
rb=['FUEL','CRANK']+outs
for n in rb:
    ou.R('10k',n+'_OUT',n+'_LED',pkg='1206',note='LED limit 10k (was 1k in BOM - too hot at 24V)'); ou.LED('green',n+'_LED','GND',lcsc='C2297')
    ou.R('100k',n+'_OUT',n+'_RBB'); ou.R('10k',n+'_RBB','GND'); npn(ou,n+'_RBB','GND',n+'_RB_N')
tca(ou,3,{('P0%d'%i if i<8 else 'P1%d'%(i-8)):rb[i]+'_RB_N' for i in range(16)})
mA=[mux[n] for n in outs[:8]]; mB=[mux[n] for n in outs[8:]]+['ESTOP_TRIP_SNSM']
for nm,lst in (('MUXA_OUT',mA),('MUXB_OUT',mB)):
    c={'D':nm,'A0':'MUX_A0','A1':'MUX_A1','A2':'MUX_A2','EN':'+3V3','VDD':'+3V3','GND':'GND','NC':None}
    for i,s_ in enumerate(lst): c['S%d'%(i+1)]=s_
    ou.p('genctl:TMUX1208PWR','TMUX1208PWR',c,mpn='TMUX1208PWR'); ou.C('100n','+3V3','GND'); ou.C('10n',nm,'GND')
# m7-sch FW-007/014/S-L1: BAT54C clamps on TMUX1208 S pins to +3V3_SAFE (fixes_firmware.md s5)
for _i,(_a,_b) in enumerate(zip((mA+mB)[0::2],(mA+mB)[1::2])):
    ou.p('Diode:BAT54C','BAT54C',{'1':_a,'2':_b,'3':'+3V3_SAFE'},ref='D%d'%(128+_i),mpn='BAT54C,215',lcsc='C37704',mfr='Nexperia',fp='Package_TO_SOT_SMD:SOT-23',note='TMUX1208 S-pin clamp')
conn(ou,4,['VBAT_ESTOP','VBAT_ESTOP','FUEL_OUT','CRANK_OUT'],'J4 E-stop/fuel/crank (PC 5/4-7.62)',mpn='Phoenix PC 5/4-GF-7,62')
conn(ou,6,['GLOW_OUT','GCB_CL_OUT','GCB_OP_OUT','MCB_CL_OUT','MCB_OP_OUT','ESTOP_TRIP_OUT'],'J5A outputs')
conn(ou,6,['GND','GND','GND','GND','GND','GND'],'J5B returns')
conn(ou,6,['AUX1_OUT','AUX2_OUT','AUX3_OUT','AUX4_OUT','AUX5_OUT','AUX6_OUT'],'J6A AUX1-6')
conn(ou,6,['AUX7_OUT','AUX8_OUT','AUX9_OUT','AUX10_OUT','GND','GND'],'J6B AUX7-10 + returns')
# m7-sch FW-001/FW-027 watchdog trip latch (fixes_firmware.md Rev 2 s1: POR RC re-arm 220k/4.7u/BAT54WS, ENOUT NC). WDO_N now only U37.7/R271/U84.6; gates + R272 + U76 P15 on WD_OK
ou.p('74xGxx:74AUP1G74','74LVC1G74DP-Q100H',{'1':'WD_REARM','2':'+3V3_SAFE','3':None,'4':'GND','5':'WD_OK','6':'WDO_N','7':'+3V3_SAFE','8':'+3V3_SAFE'},ref='U84',mpn='74LVC1G74DP-Q100H',lcsc='C548409',mfr='Nexperia',fp='Package_SO:TSSOP-8_3x3mm_P0.65mm',note='Watchdog trip latch; stock 74AUP1G74 symbol, same pinout')
ou.p('74xGxx:74LVC1G17','SN74LVC1G17DBVR',{'1':None,'2':'WD_RC','3':'GND','4':'WD_REARM','5':'+3V3_SAFE'},ref='U85',mpn='SN74LVC1G17DBVR',lcsc='C7836',mfr='TI',fp='Package_TO_SOT_SMD:SOT-23-5',note='Schmitt buffer ENOUT RC -> U84 CP')
ou.R('220k','+3V3_SAFE','WD_RC',ref='R554',lcsc='C22961',note='POR re-arm RC (Rev 2), tau 1.03 s'); ou.C('4.7u','WD_RC','GND',ref='C298',pkg='1206',mpn='CL31B475KAHNNNE',lcsc='C1872',mfr='Samsung',note='POR re-arm RC cap 25V X7R (spec C293, Rev 3)')
ou.p('Device:D_Schottky','BAT54WS-7-F',{'1':'+3V3_SAFE','2':'WD_RC'},ref='D136',mpn='BAT54WS-7-F',lcsc='C124205',mfr='Diodes',fp='Diode_SMD:D_SOD-323',note='WD_RC discharge diode')
ou.C('100n','+3V3_SAFE','GND',ref='C299',lcsc='C14663',note='U84 decoupling'); ou.C('100n','+3V3_SAFE','GND',ref='C300',lcsc='C14663',note='U85 decoupling')
# m7-sch FW-002/003/004 enable pull-downs (fixes_firmware.md s2, s3.1, s3.2)
for _r,_n,_v in [('R534', 'FUEL_EN_MCU', '100k'), ('R535', 'CRANK_EN_MCU', '100k'), ('R536', 'AUX3_MCU', '4.7k'), ('R537', 'GLOW_EN_MCU', '100k'), ('R538', 'GCB_CL_MCU', '100k'), ('R539', 'GCB_OP_MCU', '100k'), ('R540', 'MCB_CL_MCU', '100k'), ('R541', 'MCB_OP_MCU', '100k'), ('R542', 'AUX1_MCU', '100k'), ('R543', 'AUX2_MCU', '100k'), ('R544', 'AUX4_MCU', '100k'), ('R545', 'AUX5_MCU', '100k'), ('R546', 'AUX6_MCU', '100k'), ('R547', 'AUX7_MCU', '100k'), ('R548', 'AUX8_MCU', '100k'), ('R549', 'AUX9_MCU', '10k'), ('R550', 'AUX10_MCU', '10k')]:
    ou.R(_v,_n,'GND',ref=_r,lcsc={'100k': 'C25803', '10k': 'C25804', '4.7k': 'C23162'}[_v],note='enable pull-down (fixes_firmware.md s2)')


# =====================================================================
es=S('estop','E-stop trip and sense',
 'E-STOP (estop_notes v5). VBAT_ESTOP open -> Q 47k/10k releases 555 RESET; TRIG RC (100k/100n) fires one-shot 1.1*200k*2.2u = 0.48s.\n'
 '555 powered from +5V_TRIP (TPS7B6950 from VBAT_P via SS110 + hold-up). BAT54C OR of 555 Q and (MCU_TRIP AND WDO) -> TPS1HTC30 ESTOP_TRIP.\n'
 'ADDED: 4th LVC1G08 gates MCU_TRIP with WDO. Hold-up cap changed to 50V (BOM 25V part < 30V OV threshold).')
schottky(es,'SS110','VBAT_P','TRIP_LDO_IN',mpn='SS110')
es.C('10u','TRIP_LDO_IN','GND',pkg='1210',note='50V (BOM 25V too low)')
es.p('genctl:TPS7B6950QDBVRQ1','TPS7B6950QDBVRQ1',{'IN':'TRIP_LDO_IN','GND':'GND','OUT':'+5V_TRIP','NC':None},mpn='TPS7B6950QDBVRQ1',lcsc='C132202')
es.C('2.2u','+5V_TRIP','GND',pkg='0805'); es.C('100n','+5V_TRIP','GND')
es.R('47k','VBAT_ESTOP','TRIP_QB'); es.R('10k','TRIP_QB','GND'); npn(es,'TRIP_QB','GND','TRIP_RST')
es.R('10k','+5V_TRIP','TRIP_RST'); es.R('100k','TRIP_RST','TRIP_TRIG'); es.C('100n','TRIP_TRIG','GND')
es.p('Timer:TLC555xD','TLC555CDR',{'VCC':'+5V_TRIP','GND':'GND','TR':'TRIP_TRIG','CV':'TRIP_CV','R':'TRIP_RST','Q':'TRIP_555_Q','DIS':'TRIP_TIM','THR':'TRIP_TIM'},prefix='U',mpn='TLC555CDR')
es.R('200k','+5V_TRIP','TRIP_TIM'); es.C('2.2u','TRIP_TIM','GND',pkg='0805',note='tw 1.1*200k*2.2u = 0.48s (0.44-0.53s tol); measure cold/hot'); es.C('100n','TRIP_CV','GND'); es.C('100n','+5V_TRIP','GND')
es.p('74xGxx:74LVC1G08','74LVC1G08',{'1':'MCU_TRIP','2':'WD_OK','4':'MCU_TRIP_G','5':'+3V3_SAFE','3':'GND'},prefix='U',mpn='SN74LVC1G08DBVR',note='ADDED 4th gate'); es.C('100n','+3V3_SAFE','GND')  # +3V3_SAFE explicit (POST-PASS 1 maps estop +3V3 -> +3V3_SAFE anyway; matches board U67.5)
es.R('100k','MCU_TRIP','GND')
es.p('Diode:BAT54C','BAT54C',{'1':'TRIP_555_Q','2':'MCU_TRIP_G','3':'ESTOP_TRIP_EN'},prefix='D',mpn='BAT54C'); es.R('100k','ESTOP_TRIP_EN','GND')
es.p('genctl:TPS1HTC30QPWPRQ1','TPS1HTC30QPWPRQ1',{'VS':'VBAT_P','EN':'ESTOP_TRIP_EN','DIAG_EN':'DIAG_EN','LATCH':'GND','ILIM':'ESTOP_TRIP_ILIM','GND':'GND','VOUT':'ESTOP_TRIP_OUT','SNS':'ESTOP_TRIP_SNS','FAULT':'OUT_FAULT_N','NC':None,'EP':'GND'},mpn='TPS1HTC30QPWPRQ1')
es.R('47k','ESTOP_TRIP_ILIM','GND',note='ILIM 100A*kOhm/47k = 2.13A typ (1.70-2.55A); relay drive'); es.R('1.1k','ESTOP_TRIP_SNS','GND'); es.R('1k','ESTOP_TRIP_SNS','ESTOP_TRIP_SNSM'); es.C('100n','VBAT_P','GND',pkg='0805')
schottky(es,'SS110','GND','ESTOP_TRIP_OUT',mpn='SS110'); tvs(es,'SMBJ33CA','ESTOP_TRIP_OUT')
es.R('10k','ESTOP_TRIP_OUT','ESTOP_TRIP_LED',pkg='1206'); es.LED('red','ESTOP_TRIP_LED','GND',lcsc='C2295')
es.R('100k','VBAT_ESTOP','VESTOP_SNS',note='0.1%'); es.R('10k','VESTOP_SNS','GND',note='0.1%'); es.C('100n','VESTOP_SNS','GND'); clamp(es,'VESTOP_SNS','BAT54S')
tvs(es,'SMBJ33CA','VBAT_ESTOP')

# =====================================================================
ac=S('ac_metering','AC metering: 2x ADE9000 (gen + bus), isolated',
 'AC METERING. Hot side GND_AC isolated by ISOW7841 (data+power) + ISO7741, both 5kVrms reinforced, SOIC-16W 8mm. Barrier keep-out >=8mm + slot.\n'
 'Voltage: fully differential. Each line 4x1M -> tap (1k to GND_AC); each neutral (GEN_N, BUS_N separately) 4x1M -> N_TAP (1k to GND_AC); VxN <- 1k <- N_TAP.\n'
 'No 0R neutral link: GND_AC floats at the divider mid-point, common-mode attenuated 4001:1. Current: AC1005 CTs, burden 2x24.9R.')
for n in ('ADE_SCK','ADE_MOSI','ADE_CS1_N','ADE_MISO','ADE_CS2_N','ADE_RST_N','ADE_IRQ_N'): ac.R('1k',n,n+'_I',note='domain-boundary R (SAFE MCU <-> +3V3 isolator)')
ac.p('genctl:ISOW7841DWE','ISOW7841DWER',{'VCC':'+3V3','GND1':'GND','INA':'ADE_SCK_I','INB':'ADE_MOSI_I','INC':'ADE_CS1_N_I','OUTD':'ADE_MISO_I','NC':None,
   'VISO':'+3V3_AC','GND2':'GND_AC','OUTA':'AC_SCK','OUTB':'AC_MOSI','OUTC':'AC_CS1_N','IND':'AC_MISO','SEL':'GND_AC'},mpn='ISOW7841DWER',fp='genctl:SOIC-16W_7.5x10.3mm_P1.27mm_HV_Slot',note='5kVrms reinforced; SEL=GND2 -> VISO 3.3V')
ac.C('10u','+3V3','GND',pkg='0805'); ac.C('100n','+3V3','GND'); ac.C('10u','+3V3_AC','GND_AC',pkg='0805'); ac.C('100n','+3V3_AC','GND_AC')
ac.p('genctl:ISO7741DW','ISO7741DWR',{'VCC1':'+3V3','GND1':'GND','INA':'ADE_CS2_N_I','INB':'ADE_RST_N_I','INC':'GND','OUTD':'ADE_IRQ_N_I','EN1':'+3V3',
   'VCC2':'+3V3_AC','GND2':'GND_AC','OUTA':'AC_CS2_N','OUTB':'AC_RST_N','OUTC':None,'IND':'AC_IRQ_N','EN2':'+3V3_AC'},mpn='ISO7741DWR',fp='genctl:SOIC-16W_7.5x10.3mm_P1.27mm_HV_Slot',note='5kVrms reinforced')
ac.C('100n','+3V3','GND'); ac.C('100n','+3V3_AC','GND_AC')
ac.R('10k','AC_IRQ_N','+3V3_AC'); ac.R('10k','AC_RST_N','+3V3_AC')
for k,(tag,clkin,clkout) in enumerate((('GEN','ADE_XI','ADE_XO'),('BUS','ADE_XO2',None)),1):
    c={'VDD':'+3V3_AC','PULL_HIGH':'+3V3_AC','AVDDOUT':'AVDD_%s'%tag,'DVDDOUT':'DVDD_%s'%tag,'REF':'REF_%s'%tag,'SCLK':'AC_SCK','MOSI':'AC_MOSI','MISO':'AC_MISO',
       '~{SS}':'AC_CS%d_N'%k,'~{RESET}':'AC_RST_N','~{IRQ0}':'AC_IRQ_N' if k==1 else None,'~{IRQ1}':None,'CF1':None,'CF2':None,'CF3/ZX':None,'CF4/EVENT':None,'PM0':'GND_AC','PM1':'GND_AC',
       'DGND':'GND_AC','REFGND':'GND_AC','NC1':'GND_AC','NC2':'GND_AC','AGND':'GND_AC','GND':'GND_AC','EP':'GND_AC','CLKIN':clkin if k==1 else 'ADE_CLK_BUF','CLKOUT':clkout}
    for ph in 'ABC': c['V%sP'%ph]='%s_V%s_P'%(tag,ph); c['V%sN'%ph]='%s_V%s_N'%(tag,ph)
    if k==1:
        for i,ph in enumerate('ABCN'): c['I%sP'%ph]='GEN_I%s_P'%ph; c['I%sN'%ph]='GEN_I%s_N'%ph
    else:
        for ph in 'ABCN': c['I%sP'%ph]='GND_AC'; c['I%sN'%ph]='GND_AC'
    ac.p('genctl:ADE9000ACPZ','ADE9000ACPZ (%s)'%tag,c,mpn='ADE9000ACPZ')
    ac.C('4.7u','AVDD_'+tag,'GND_AC',pkg='0805'); ac.C('100n','AVDD_'+tag,'GND_AC'); ac.C('4.7u','DVDD_'+tag,'GND_AC',pkg='0805'); ac.C('100n','DVDD_'+tag,'GND_AC')
    ac.C('4.7u','REF_'+tag,'GND_AC',pkg='0805'); ac.C('100n','REF_'+tag,'GND_AC'); ac.C('10u','+3V3_AC','GND_AC',pkg='0805'); ac.C('100n','+3V3_AC','GND_AC')
ac.p('Device:Crystal_GND24','24.576MHz',{'1':'ADE_XI','3':'ADE_XO','2':'GND_AC','4':'GND_AC'},prefix='Y',mpn='X322524576MOB4SI',lcsc='C70568',fp='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm'); ac.C('22p','ADE_XI','GND_AC',pkg='0402'); ac.C('22p','ADE_XO','GND_AC',pkg='0402')
# m7-sch S-M1: U87 GU04 self-biased buffer U71 CLKOUT -> U72 CLKIN (fixes_firmware.md s11); spec C297/C298 renumbered C301/C302
ac.p('74xGxx:74LVC1GU04','SN74LVC1GU04DBVR',{'2':'ADE_XO_AC','3':'GND_AC','4':'ADE_CLK_Y','5':'+3V3_AC'},ref='U87',mpn='SN74LVC1GU04DBVR',lcsc='C81934',mfr='TI',fp='Package_TO_SOT_SMD:SOT-23-5')
ac.C('100p','ADE_XO','ADE_XO_AC',ref='C301',mpn='CL10C101JB8NNNC',lcsc='C14858',mfr='Samsung'); ac.R('1M','ADE_CLK_Y','ADE_XO_AC',ref='R556',lcsc='C22935')
ac.R('33','ADE_CLK_Y','ADE_CLK_BUF',ref='R557',mpn='0603WAF330JT5E',lcsc='C23140',mfr='UNI-ROYAL'); ac.C('100n','+3V3_AC','GND_AC',ref='C302',lcsc='C14663')
for tag,J in (('GEN','J7'),('BUS','J8')):
    conn(ac,4,[tag+'_L1',tag+'_L2',tag+'_L3',tag+'_N'],'%s %s voltage (L1 L2 L3 N)'%(J,tag),note='external DIN fuses assumed (spec); >=600VAC rated terminal')
    for ph,L in zip('ABC',('L1','L2','L3')):
        ac.p('Device:Varistor','TMOV20RP460E',{'1':tag+'_'+L,'2':tag+'_N'},prefix='RV',mpn='TMOV20RP460EL2T7',lcsc='C3260792',mfr='Littelfuse',fp='genctl:TMOV20RP_P7.5mm_inline')  # RV1-RV6: manual sch edit 32b12c7/7eaa27d folded into design.py
        a=tag+'_'+L
        for j in range(4):
            b=('%s_%s_HV%d'%(tag,L,j+1)) if j<3 else '%s_V%s_TAP'%(tag,ph)
            ac.R('1M',a,b,pkg='1206',note='HV 1206 (>=200V each)'); a=b
        ac.R('1k','%s_V%s_TAP'%(tag,ph),'GND_AC'); ac.R('1k','%s_V%s_TAP'%(tag,ph),'%s_V%s_P'%(tag,ph)); ac.C('33n','%s_V%s_P'%(tag,ph),'GND_AC')
        ac.R('1k',tag+'_VN_TAP','%s_V%s_N'%(tag,ph)); ac.C('33n','%s_V%s_N'%(tag,ph),'GND_AC')
    a=tag+'_N'
    for j in range(4):
        b=('%s_N_HV%d'%(tag,j+1)) if j<3 else tag+'_VN_TAP'
        ac.R('1M',a,b,pkg='1206',note='HV 1206 neutral divider (own reference per system)'); a=b
    ac.R('1k',tag+'_VN_TAP','GND_AC',note='neutral divider tap - no direct N-GND_AC link')
cts=[]
for i,ph in enumerate('ABCN',1):
    ac.p('genctl:AC1005','AC1005',{'P1':'CT%d_S1'%i,'P2':'CT%d_S2'%i,'S1':'GEN_CT%s_1'%ph,'S2':'GEN_CT%s_2'%ph,'NC':None},mpn='AC1005',lcsc='C6117861')
    ac.R('24.9R','GEN_CT%s_1'%ph,'GND_AC',note='0.1% burden'); ac.R('24.9R','GEN_CT%s_2'%ph,'GND_AC',note='0.1% burden')
    ac.R('1k','GEN_CT%s_1'%ph,'GEN_I%s_P'%ph); ac.C('33n','GEN_I%s_P'%ph,'GND_AC'); ac.R('1k','GEN_CT%s_2'%ph,'GEN_I%s_N'%ph); ac.C('33n','GEN_I%s_N'%ph,'GND_AC')
    cts+=['CT%d_S1'%i,'CT%d_S2'%i]
conn(ac,8,cts,'J9 CT secondaries (5A)',note='external 5A CT loops pass through AC1005 cores')

# =====================================================================
fp_=S('frontpanel','Front panel: backlit buttons, buzzer',
 'FRONT PANEL. 12x CTS 228EMVARGBFR IP67 RGB-backlit tactile switches. Switch -> TCA9555 @0x20 (internal pull-ups).\n'
 'Backlight: common anodes on BTN_LED_V (+5V via AO3401A high-side, gated by CM5 GPIO13 BTN_BL_PWM = global dimming, default off).\n'
 'Cathodes R/G/B per button via 470R/470R/330R (~6mA, <=18mA/pin, ~96mA/expander worst case) to TCA9555 @0x21/@0x24/@0x25, active low. OFF = Hi-Z.\n'
 'TCA9555s on +3V3_SAFE; buzzer on main +3V3.')
b={}
for i in range(12): b[('P0%d'%i) if i<8 else 'P1%d'%(i-8)]='BTN%d'%(i+1)
for i in range(12,16): b['P1%d'%(i-8)]=None
tca(fp_,0,b)
ch=[]
for i in range(12):
    n=i+1
    fp_.p('genctl:228EMVARGBFR','BTN%d'%n,{'A':'BTN%d'%n,'B':'GND','L1':'BTN_LED_V','L2':'BTN%d_GK'%n,'L3':'BTN%d_RK'%n,'L4':'BTN%d_BK'%n},prefix='SW',mpn='228EMVARGBFR')
    for col,r in (('R','470R'),('G','470R'),('B','330R')):
        fp_.R(r,'BTN%d_%sK'%(n,col),'BL%d_%s'%(n,col),note='LED %s ~5-6mA from 5V'%col); ch.append('BL%d_%s'%(n,col))
pins=[('P0%d'%k) for k in range(8)]+[('P1%d'%k) for k in range(8)]
for addr,chunk in ((1,ch[0:16]),(4,ch[16:32]),(5,ch[32:36])):
    m={pn:None for pn in pins}
    for pn,net in zip(pins,chunk): m[pn]=net
    if addr==5: m.update({'P04':'ROUTER_12V_EN','P05':'CM5_OFF','P06':'CM5_PWRBTN_MCU','P07':'PWR_FAIL_MCU','P10':'AUX9_MCU','P11':'AUX10_MCU','P12':'AUX10_RB_N','P13':'USB0_EN','P14':'USB1_EN','P15':'WD_OK'})  # P15 = WD_OK readback (fixes_firmware.md s1)
    tca(fp_,addr,m)
fp_.R('1k','BTN_BL_PWM','BL_Q_B'); fp_.R('100k','BL_Q_B','GND',note='default off'); npn(fp_,'BL_Q_B','GND','BL_PG')
fp_.R('10k','+5V','BL_PG',note='PFET gate pull-up'); fet(fp_,'Transistor_FET:AO3401A','AO3401A','BL_PG','+5V','BTN_LED_V')
fp_.C('1u','BTN_LED_V','GND',pkg='0603'); fp_.C('10u','+5V','GND',pkg='0805')
fp_.R('1k','BUZZER_PWM','BUZ_B'); fp_.R('100k','BUZ_B','GND'); npn(fp_,'BUZ_B','GND','BUZ_K')
fp_.p('Device:Buzzer','MLT-8530',{'+':'+3V3','-':'BUZ_K'},prefix='BZ',mpn='MLT-8530',lcsc='C94599',fp='genctl:MLT-8530_buzzer',note='FIXED polarity: pad1 = +')
fp_.p('Diode:1N4148W','1N4148W',{'A':'BUZ_K','K':'+3V3'},prefix='D',mpn='1N4148W')
fp_.C('10u','+3V3','GND',pkg='0805')

# =====================================================================
# POST-PASS 1: safety domain. Everything on the MCU, inputs, outputs and E-stop sheets, plus the
# front-panel TCA9555 expanders, runs from +3V3_SAFE (TPS2116 mux of +3V3 / always-on +3V3_BK).
SAFE_SHEETS=('mcu','inputs','outputs','estop')
for sh in SHEETS:
    for pt in sh.parts:
        keep = sh.name=='frontpanel' and (pt.value in ('MLT-8530','1N4148W') or pt is sh.parts[-1])
        if sh.name in SAFE_SHEETS or (sh.name=='frontpanel' and not keep):
            for k,v in pt.net.items():
                if v=='+3V3': pt.net[k]='+3V3_SAFE'

# POST-PASS 2: footprint / LCSC fill for generic parts (explicit values above win)
FPMAP={  # libid -> (fp, lcsc, mpn)
 'Transistor_FET:BSC070N10NS5':('Package_TO_SOT_SMD:TDSON-8-1','C152539','BSC070N10NS5ATMA1'),
 'Transistor_FET:BSS84':('Package_TO_SOT_SMD:SOT-23',None,None),'Transistor_FET:DMN6075S':('Package_TO_SOT_SMD:SOT-23',None,None),
 'Transistor_FET:AO3401A':('Package_TO_SOT_SMD:SOT-23',None,None),'Transistor_BJT:MMBT3904':('Package_TO_SOT_SMD:SOT-23',None,None),
 'Transistor_BJT:MMBT3906':('Package_TO_SOT_SMD:SOT-23',None,None),'Diode:BAV99':('Package_TO_SOT_SMD:SOT-23',None,None),
 'Diode:BAT54S':('Package_TO_SOT_SMD:SOT-23',None,None),'Diode:BAT54C':('Package_TO_SOT_SMD:SOT-23',None,None),
 'Diode:1N4148W':('Diode_SMD:D_SOD-123',None,None),'Diode:SM712_SOT23':('Package_TO_SOT_SMD:SOT-23',None,None),
 'Power_Protection:NUP2105L':('Package_TO_SOT_SMD:SOT-23',None,None),'Power_Protection:USBLC6-2SC6':('Package_TO_SOT_SMD:SOT-23-6',None,None),
 'Power_Protection:SRV05-4':('Package_TO_SOT_SMD:SOT-23-6',None,None),
 'Interface_Expansion:TCA9555PWR':('Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm',None,None),
 'MCU_ST_STM32H7:STM32H743VITx':('Package_QFP:LQFP-100_14x14mm_P0.5mm','C114409',None),
 'Memory_NVRAM:FM24C64B':('Package_SO:SOIC-8_3.9x4.9mm_P1.27mm','C9829',None),
 'Switch:SW_Push':('Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A','C318884',None),
 'Connector:Conn_ARM_JTAG_SWD_10':('genctl:FTSH-105-01_SWD','C5199898','FTSH-105-01-L-DV'),
 'Connector_Generic:Conn_02x04_Odd_Even':('Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical','C225519','A2541WV-2x4P'),
 'Connector_Generic:Conn_02x05_Odd_Even':('genctl:PZ254-2-05-S_2x05_SMD','C3294463','PZ254-2-05-S'),
 'Connector:USB_C_Receptacle_USB2.0_16P':('genctl:USB_C_Receptacle_HRO_TYPE-C-31-D-06B_Vertical','C47817619','TYPE-C-31-D-06B'),
 'Power_Management:TPS2051CDBV':('Package_TO_SOT_SMD:SOT-23-5',None,None),
 'Interface_USB:USB2514B_Bi':('Package_DFN_QFN:QFN-36-1EP_6x6mm_P0.5mm_EP3.7x3.7mm',None,None),
 'Amplifier_Operational:TLV9062':('Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',None,None),'Amplifier_Operational:LM2904':('Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',None,None),
 'Comparator:LM393':('Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',None,None),'Analog_ADC:ADS1115IDGS':('Package_SO:MSOP-10_3x3mm_P0.5mm',None,None),
 'Reference_Voltage:LM4040DBZ-2.5':('Package_TO_SOT_SMD:SOT-23','C9421','LM4040A25IDBZR'),
 '74xx:74HC14':('Package_SO:SOIC-14_3.9x8.7mm_P1.27mm','C5605','74HC14D,653'),'Regulator_Linear:LM317_TO-252':('Package_TO_SOT_SMD:TO-252-2',None,None),
 '74xGxx:74LVC1G08':('Package_TO_SOT_SMD:SOT-23-5',None,None),'Amplifier_Current:INA281A2':('Package_TO_SOT_SMD:SOT-23-5',None,None),'Amplifier_Current:INA281A1':('Package_TO_SOT_SMD:SOT-23-5',None,None),
 'Timer:TLC555xD':('Package_SO:SOIC-8_3.9x4.9mm_P1.27mm','C130208','TLC555QDRQ1'),
 'Switch:SW_DIP_x02':('genctl:DSHP02TSGER_DIP2','C367376','DSHP02TSGER'),
 'Mechanical:MountingHole_Pad':('MountingHole:MountingHole_3.2mm_M3_Pad','',None),
}
MPNLCSC={'BSS84':'C8492','DMN6075S':'C155242','SI2309CDS-T1-GE3':'C10493','AO3401A':'C347476','BAV99':'C2500','BAT54S':'C8592','BAT54C':'C2135',
 '1N4148W':'C81598','SM712':'C12067','NUP2105LT1G':'C14486','USBLC6-2SC6':'C7519','SRV05-4':'C85364','TPS2051CDBVR':'C129581',
 'USB2514B-AEZC-TR':'C51062','TLV9062IDR':'C398355','LM2904BIDR':'C1849422','LM393DR':'C7955','ADS1115IDGSR':'C37593','LM317MDT-TR':'C3015165',
 'SN74LVC1G08DBVR':'C7666','INA281A2QDBVRQ1':'C2908677','INA281A1QDBVRQ1':'C2862615','STM32H743VIT6':'C114409','FM24CL64B-GTR':'C9829',
 'SMDJ36CA':'C224075','SMBJ33CA':'C78420','SMBJ5.0A':'C78423','SMAJ36CA':'C10757','SMBJ58CA':'C114007','SMBJ36CA':'C78421','SMDJ24A':'C362107',
 'SS110':'C2482','SS34':'C8678','SK1010C':'C3018527','EEHZA1H101P':'C109086','EEHZK1E471P':'C242138','TS-1187A-B-A-B':'C318884',
 'SM04B-SRSS-TB':'C51940130','TYPE-C-31-M-12':'C165948','TYPE-C-31-D-06B':'C47817619','MMBT3904':'C20526','MMBT3906':'C2143'}
DIODEFP={'SMDJ':'Diode_SMD:D_SMC','SMBJ':'Diode_SMD:D_SMB','SMAJ':'Diode_SMD:D_SMA','SS110':'Diode_SMD:D_SMA','SS34':'Diode_SMD:D_SMA','SK1010C':'Diode_SMD:D_SMC'}
_r6='Resistor_SMD:R_0603_1608Metric'; _r12='Resistor_SMD:R_1206_3216Metric'; _c6='Capacitor_SMD:C_0603_1608Metric'
RCX={  # (value, fp) -> lcsc for passives not in gen.RLCSC/CLCSC (all checked on JLC parts search 2026-10-24)
 ('121k',_r6):'C25809',('16k',_r6):'C4210',('180k',_r6):'C22827',('18.7k',_r6):'C22893',('20k',_r6):'C4184',('232k',_r6):'C22913',
 ('27.4k',_r6):'C22964',('330R',_r6):'C23138',('35.7k',_r6):'C23027',('40.2k',_r6):'C12447',('43.2k',_r6):'C23053',('470R',_r6):'C23179',
 ('53.6k',_r6):'C23074',('680R',_r6):'C23228',('93.1k',_r6):'C23266',('1.1k',_r6):'C22764',('1.33k',_r6):'C22838',('13.3k',_r6):'C25952',
 ('10R',_r6):'C22859',('1M',_r12):'C17927',('120R',_r12):'C17909',('62R',_r12):'C17971',('10k',_r12):'C17902',('4.7k',_r12):'C17936',
 ('100R',_r12):'C319961',('715k',_r6):'C23237',('33.2k',_r6):'C23003',('29.4k',_r6):'C22974',('150R',_r12):'C17917',('1.1R','Resistor_SMD:R_0805_2012Metric'):'C2933354',('10R','Resistor_SMD:R_2512_6332Metric'):'C47019',
 ('100n','Capacitor_SMD:C_0805_2012Metric'):'C28233',('220n','Capacitor_SMD:C_0805_2012Metric'):'C513710',('100n','Capacitor_SMD:C_1206_3216Metric'):'C1945',('100p',_c6):'C14858',
 ('10n',_c6):'C57112',('18p','Capacitor_SMD:C_0402_1005Metric'):'C1549',('2.2u','Capacitor_SMD:C_0805_2012Metric'):'C5137595',
 ('220p',_c6):'C1603',('270p',_c6):'C1608',('4.7n','Capacitor_SMD:C_1206_3216Metric'):'C41017',('4.7u','Capacitor_SMD:C_0805_2012Metric'):'C1779',
 ('470n',_c6):'C1623',('47n',_c6):'C1622',('68n',_c6):'C5137586',
}
PREC={('100k',_r6):'C122538',('18k',_r6):'C309650'}  # 0.1% thin film where the note asks for 0.1%
CONNFP={  # value prefix -> (fp, lcsc, mpn)
 'PC 5/4-GF-7,62':('genctl:PhoenixContact_PC5_4-GF-7.62_1720819','C3579760','1720819'),
 'J4 E-stop':('genctl:PhoenixContact_PC5_4-GF-7.62_1720819','C3579760','1720819'),
 'Fan header':('Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal','C160390','SM04B-SRSS-TB'),
 'Internal USB':('Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal','C160390','SM04B-SRSS-TB'),
 'Spare USB':('Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical','C2337','1x6 2.54 header'),
 'LVDS FPC':('genctl:FPC_40P_0.5_05A20L40P','C5362161','05A20L40P'),'Touch FPC':('genctl:FPC_10P_0.5_05B20L10P','C5362168','05B20L10P'),
 'Backlight':('genctl:SM02B-BHSS-1-TB','C485339','SM02B-BHSS-1-TB'),
 'CAN1':('genctl:WJ15EDGRC-3.81-4P','C7245','WJ15EDGRC-3.81-04P'),'Expansion':('genctl:WJ15EDGRC-3.81-6P','C7246','WJ15EDGRC-3.81-06P'),
 'RS-485':('genctl:WJ15EDGRC-3.81-3P','C8406','WJ15EDGRC-3.81-03P'),'Router':('genctl:WJ15EDGRC-3.81-2P','C8387','WJ15EDGRC-3.81-02P'),
 'J9 CT':('genctl:KF2EDGRM-5.08-8P','C441294','KF2EDGRM-5.08-8P'),
}
def _fill(pt):
    lid=pt.libid
    if lid in ('74xx:74HC14','Timer:TLC555xD'): pt.fp=None; pt.lcsc=None; pt.mpn=None  # align with CSV BOM part
    if pt.mpn=='MMBT3906': pt.lcsc='C2143'
    if lid in FPMAP:
        f,l,m=FPMAP[lid]
        if not pt.fp: pt.fp=f
        if not pt.lcsc and l: pt.lcsc=l
        if not pt.mpn and m: pt.mpn=m
    if not pt.lcsc and pt.mpn in MPNLCSC: pt.lcsc=MPNLCSC[pt.mpn]
    if lid in ('Device:D_TVS','Device:D_Zener','Device:D_Schottky') and not pt.fp:
        for k,f in DIODEFP.items():
            if pt.value.startswith(k): pt.fp=f
    if lid.startswith('Connector_Generic:Conn_01x') and not pt.fp:
        for k,(f,l,m) in CONNFP.items():
            if pt.value.startswith(k): pt.fp=f; pt.lcsc=pt.lcsc or l; pt.mpn=m
        if not pt.fp:
            n=int(lid[-2:])
            if n==6 and ('7.62' not in pt.value):
                pt.fp='genctl:KF2EDGRM-5.08-6P'; pt.lcsc='C441292'; pt.mpn='KF2EDGRM-5.08-6P'  # FIX rev f: field I/O are 5.08 mm Kefa per BOM (was 3.81 WJ15)
            if n==4 and 'voltage' in pt.value:
                pt.fp='genctl:PhoenixContact_PC5_4-GF-7.62_1720819'; pt.lcsc='C3579760'; pt.mpn='1720819'  # FIX rev f: BOM part is Phoenix PC 5/4-GF-7,62 (was KF2 5.08 6P, 2.6 mm L-L gap)
    if lid=='Device:LED' and pt.lcsc in ('C2297','C2295'): pt.fp='LED_SMD:LED_0805_2012Metric'
    if lid=='Device:R' and '0.1%' in (pt.note or '') and (pt.value,pt.fp) in PREC: pt.lcsc=PREC[(pt.value,pt.fp)]
    if lid in ('Device:R','Device:C','Device:C_Polarized') and not pt.lcsc:
        pt.lcsc=RCX.get((pt.value,pt.fp),'')
    if not pt.lcsc and not pt.power:
        sl={p[1]:p[2] for p in find(pt.sym,'property')}.get('LCSC','')
        if sl: pt.lcsc=sl
for pt in ALLPARTS: _fill(pt)

# project footprint library
open(os.path.join(OUT,'fp-lib-table'),'w').write('(fp_lib_table\n  (version 7)\n  (lib (name "genctl")(type "KiCad")(uri "${KIPRJMOD}/genctl.pretty")(options "")(descr "genctl project footprints (EasyEDA-derived land patterns + hand-drawn 228E/AC1005 pads: VERIFY before layout)"))\n)\n')
