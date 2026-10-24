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
def pnp(sh,b,e,c): return sh.p('Transistor_BJT:MMBT3906','MMBT3906',{'B':b,'E':e,'C':c},prefix='Q',mpn='MMBT3906',lcsc='C2940')
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
 'POWER. J0 battery in -> 10A ATO -> SMDJ58CA -> LM74800 + 2x BSC070N10NS5 back-to-back (VBAT_P).\n'
 'OV 30.3V / UV 5.5V (191k/45.3k/10k, 1.231V thresholds). LM5176 buck-boost -> +12V (FB 140k/10k, RT 27k ~290kHz).\n'
 'TPS56637 -> +5V (FB 75k/10k = 5.1V). TPS56637 -> +3V3 from +12V (FB 45.3k/10k, 2.2uH, 3x22u), >=3A.')
conn(pw,4,['BAT_IN','BAT_IN','GND','GND'],'PC 5/4-GF-7,62 (battery in)',mpn='1720819 Phoenix',note='J0 battery input')
pw.p('Device:Fuse','10A ATO (3557-2 clips)',{'1':'BAT_IN','2':'VBAT_F'},prefix='F',mpn='3557-2')
tvs(pw,'SMDJ58CA','VBAT_F')
pw.C('100n','VBAT_F','GND',pkg='0805',note='100V')
pw.p('genctl:LM74800QDRRRQ1','LM74800QDRRRQ1',{'A':'VBAT_F','VS':'VBAT_F','VSNS':'VBAT_F','SW':'OVUV_TOP','EN/UVLO':'LM748_EN','OV':'LM748_OV','GND':'GND',
     'DGATE':'LM748_DGATE','C':'VBAT_DD','HGATE':'LM748_HGATE','OUT':'VBAT_P','CAP':'LM748_CAP'},mpn='LM74800QDRRRQ1')
pw.C('100n','LM748_CAP','VBAT_F',note='CAP-VS charge-pump cap, 0.1uF per DS typ app')
pw.R('191k','OVUV_TOP','LM748_EN'); pw.R('45.3k','LM748_EN','LM748_OV'); pw.R('10k','LM748_OV','GND')
fet(pw,'Transistor_FET:BSC070N10NS5','BSC070N10NS5','LM748_DGATE','VBAT_F','VBAT_DD')
fet(pw,'Transistor_FET:BSC070N10NS5','BSC070N10NS5','LM748_HGATE','VBAT_P','VBAT_DD')
tvs(pw,'SMBJ28CA','VBAT_P')
for _ in range(2): pw.C('100u 50V','VBAT_P','GND',pol=True,mpn='EEHZA1H101P',pkg='Capacitor_SMD:CP_Elec_10x10.5')
for _ in range(4): pw.C('10u','VBAT_P','GND',pkg='1210',note='50V X7R')
# LM5176
pw.p('genctl:LM5176PWPR','LM5176PWPR',{'VIN':'VBAT_P','VISNS':'VBAT_P','EN/UVLO':'BB_EN','MODE':'BB_MODE','DITH':'GND','RT/SYNC':'BB_RT','SLOPE':'BB_SLOPE',
   'SS':'BB_SS','COMP':'BB_COMP','FB':'BB_FB','VOSNS':'+12V','ISNS+':'+12V','ISNS-':'+12V','AGND':'GND','EP':'GND',
   'HDRV1':'BB_HDRV1','BOOT1':'BB_BOOT1','SW1':'BB_SW1','LDRV1':'BB_LDRV1','HDRV2':'BB_HDRV2','BOOT2':'BB_BOOT2','SW2':'BB_SW2','LDRV2':'BB_LDRV2',
   'CS':'BB_CS','CSG':'GND','PGOOD':'PG_12V','VCC':'BB_VCC','BIAS':'+12V','PGND':'GND'},mpn='LM5176PWPR')
pw.R('100k','VBAT_P','BB_EN'); pw.R('33k','BB_EN','GND')
pw.R('93.1k','BB_MODE','GND',note='MODE strap value TBD from DS table (assumed CCM/hiccup off)')
pw.R('27k','BB_RT','GND',note='~290kHz assumed (40k=200k, 20k=390k)')
pw.C('100p','BB_SLOPE','GND',note='slope comp - verify with DS eq.')
pw.C('47n','BB_SS','GND'); pw.R('10k','BB_COMP','BB_COMP_RC'); pw.C('22n','BB_COMP_RC','GND'); pw.C('220p','BB_COMP','GND')
pw.R('140k','+12V','BB_FB'); pw.R('10k','BB_FB','GND')
pw.R('100k','PG_12V','+3V3')
pw.C('4.7u','BB_VCC','GND',pkg='1206'); pw.C('1u','+12V','GND',pkg='0805')
pw.C('100n','BB_BOOT1','BB_SW1'); pw.C('100n','BB_BOOT2','BB_SW2')
for g,s_,d in (('BB_HDRV1','BB_SW1','VBAT_P'),('BB_LDRV1','BB_CS','BB_SW1'),('BB_LDRV2','BB_CS','BB_SW2'),('BB_HDRV2','BB_SW2','+12V')):
    fet(pw,'Transistor_FET:BSC070N10NS5','BSC070N10NS5',g,s_,d)
pw.p('Device:L','4.7u',{'1':'BB_SW1','2':'BB_SW2'},prefix='L',note='4.7uH >=15A sat (BOM)')
pw.R('2m','BB_CS','GND',pkg='2512',mpn='WSL25122L000FEA',note='buck-boost current sense')
pw.R('2m','BB_CS','GND',pkg='2512',mpn='WSL25122L000FEA',dnp=True,note='DNP - 2nd sense R option (BOM qty 2)')
for _ in range(2): pw.C('470u 25V','+12V','GND',pol=True,mpn='EEHZK1E471P',pkg='Capacitor_SMD:CP_Elec_10x10.5')
for _ in range(4): pw.C('22u','+12V','GND',pkg='1206')
# 5V
pw.p('genctl:TPS56637RPAR','TPS56637RPAR',{'VIN':'+12V','EN':'EN_5V','MODE':'MODE_5V','FB':'FB_5V','AGND':'GND','PGND':'GND','BOOT':'BOOT_5V','SW':'SW_5V','PG':'PG_5V','NC':None},mpn='TPS56637RPAR')
pw.R('100k','+12V','EN_5V'); pw.R('27k','EN_5V','GND')
pw.R('100k','MODE_5V','GND',note='MODE resistor TBD per DS table')
pw.C('100n','BOOT_5V','SW_5V')
pw.p('Device:L','4.7u',{'1':'SW_5V','2':'+5V'},prefix='L')
pw.R('75k','+5V','FB_5V'); pw.R('10k','FB_5V','GND')
pw.R('100k','PG_5V','+3V3')
for _ in range(2): pw.C('10u','+12V','GND',pkg='0805')
for _ in range(4): pw.C('22u','+5V','GND',pkg='1206')
tvs(pw,'SMBJ5.0A','+5V',uni=True)
# 3V3 (TPS56637, 6A part used for >=3A rail)
pw.p('genctl:TPS56637RPAR','TPS56637RPAR',{'VIN':'+12V','EN':'EN_3V3','MODE':'MODE_3V3','FB':'FB_3V3','AGND':'GND','PGND':'GND','BOOT':'BOOT_3V3','SW':'SW_3V3','PG':'PG_3V3','NC':None},mpn='TPS56637RPAR',note='+3V3 >=3A (6A capable)')
pw.R('100k','+12V','EN_3V3'); pw.R('27k','EN_3V3','GND')
pw.R('100k','MODE_3V3','GND',note='MODE resistor TBD per DS table (same as 5V rail)')
pw.C('100n','BOOT_3V3','SW_3V3')
pw.p('Device:L','2.2u',{'1':'SW_3V3','2':'+3V3'},prefix='L',note='2.2uH per DS Table 4 (3.3V), Isat >=5A')
pw.R('45.3k','+3V3','FB_3V3',note='DS Table 4: 45.3k/10k -> 3.32V'); pw.R('10k','FB_3V3','GND')
pw.C('150p','+3V3','FF_3V3',note='feed-forward per DS Table 4 (100-220p)'); pw.R('20k','FF_3V3','FB_3V3',note='feed-forward R per DS Table 4 - verify topology')
pw.R('100k','PG_3V3','+3V3')
for _ in range(2): pw.C('10u','+12V','GND',pkg='0805',note='25V')
for _ in range(3): pw.C('22u','+3V3','GND',pkg='1206')
# chassis
for i in range(4): pw.p('Mechanical:MountingHole_Pad','MountingHole_Pad',{'1':'CHASSIS'},prefix='H')
pw.R('1M','CHASSIS','GND',pkg='1206'); pw.C('4.7n','CHASSIS','GND',pkg='1206',note='2kV - chassis/0V RC bond (assumed)')

# =====================================================================
mc=S('mcu','STM32H743 safety MCU',
 'MCU. STM32H743VIT6 LQFP-100. HSE 25MHz, LSE 32.768kHz. SWD header + JP1 (CM5 can reflash MCU over SWD).\n'
 'Peripherals: SPI4 slave to CM5, USART2 to CM5, FDCAN1/2, USART3 RS-485, I2C1 (expanders/ADC/FRAM), SPI1 to ADE9000s via isolators.')
MAP={'PA0':'VBAT_SNS','PA1':'VESTOP_SNS','PA2':'DPLUS_SNS','PA3':'FUEL_ISNS','PA4':'ADE_CS1_N','PA5':'ADE_SCK','PA6':'ADE_MISO','PA7':'ADE_MOSI',
 'PA8':'DIAG_EN','PA9':'MUX_A0','PA10':'MUX_A1','PA11':'MUX_A2','PA12':'WDI','PA13':'SWDIO','PA14':'SWCLK','PA15':'MPU_SPEED',
 'PB0':'ADE_IRQ_N','PB1':'CRANK_ISNS','PB2':'OUT_FAULT_N','PB3':'BUZZER_PWM','PB4':'AUX3_MCU','PB5':'AUX4_MCU','PB6':'AUX5_MCU','PB7':'AUX6_MCU',
 'PB8':'I2C1_SCL','PB9':'I2C1_SDA','PB10':'DI8_N','PB11':'DI9_N','PB12':'CAN2_RX','PB13':'CAN2_TX','PB14':'DI10_N','PB15':'DI11_N',
 'PC0':'MUXA_OUT','PC1':'MUXB_OUT','PC2_C':'MCU_SPARE1','PC3_C':'MCU_SPARE2','PC4':'ADE_CS2_N','PC5':'ADE_RST_N','PC6':'ESTOP2_DIG','PC7':'MPU_GATE',
 'PC8':'DPLUS_EXC_EN','PC9':'GCB_CL_MCU','PC10':'GCB_OP_MCU','PC11':'MCB_CL_MCU','PC12':'MCB_OP_MCU','PC13':'EXP_12V_EN','PC14':'LSE_IN','PC15':'LSE_OUT',
 'PD0':'CAN1_RX','PD1':'CAN1_TX','PD2':'FUEL_EN_MCU','PD3':'CRANK_EN_MCU','PD4':'GLOW_EN_MCU','PD5':'MCU_UART_TX','PD6':'MCU_UART_RX','PD7':'MCU_TRIP',
 'PD8':'RS485_TX','PD9':'RS485_RX','PD10':'DI12_N','PD11':'AUX7_MCU','PD12':'RS485_DE','PD13':'AUX8_MCU','PD14':'ESTOP_DIG','PD15':'DPLUS_DIG',
 'PE0':'AUX1_MCU','PE1':'AUX2_MCU','PE2':'MCU_SPI_SCK','PE3':'MCU_IRQ','PE4':'MCU_SPI_NSS','PE5':'MCU_SPI_MISO','PE6':'MCU_SPI_MOSI','PE7':'I2C_INT_N','PE8':'MCU_LED',
 'PH0':'HSE_IN','PH1':'HSE_OUT'}
for i in range(7): MAP['PE%d'%(9+i)]='DI%d_N'%(i+1)
c=dict(MAP); c.update({'NRST':'NRST','BOOT0':'BOOT0','VREF+':'+3V3','VDD':'+3V3','VSS':'GND','VSSA':'GND','VDDA':'VDDA','48':'VCAP1','73':'VCAP2','VBAT':'VBAT_MCU'})
mc.p('MCU_ST_STM32H7:STM32H743VITx','STM32H743VIT6',c,mpn='STM32H743VIT6')
dec(mc,'+3V3',6); mc.C('4.7u','+3V3','GND',pkg='1206')
mc.p('Device:FerriteBead','600R@100MHz',{'1':'+3V3','2':'VDDA'},prefix='FB'); mc.C('1u','VDDA','GND'); mc.C('100n','VDDA','GND')
mc.C('2.2u','VCAP1','GND'); mc.C('2.2u','VCAP2','GND')
mc.C('100n','VBAT_MCU','GND')
mc.p('Device:Crystal_GND24','25MHz',{'1':'HSE_IN','3':'HSE_OUT','2':'GND','4':'GND'},prefix='Y',mpn='X322525MOB4SI',note='load caps assume CL=12pF')
mc.C('18p','HSE_IN','GND',pkg='0402'); mc.C('18p','HSE_OUT','GND',pkg='0402')
mc.p('Device:Crystal','32.768kHz',{'1':'LSE_IN','2':'LSE_OUT'},prefix='Y',mpn='X321532768KGD2SI',note='load caps assume CL=12.5pF')
mc.C('18p','LSE_IN','GND',pkg='0402'); mc.C('18p','LSE_OUT','GND',pkg='0402')
mc.C('100n','NRST','GND')
mc.p('Switch:SW_Push','RESET',{'1':'NRST','2':'GND'},prefix='SW',mpn='TS-1187A-B-A-B')
mc.R('10k','BOOT0','GND')
mc.p('Switch:SW_Push','BOOT0',{'1':'BOOT0','2':'+3V3'},prefix='SW',mpn='TS-1187A-B-A-B')
mc.p('Connector:Conn_ARM_JTAG_SWD_10','SWD',{'1':'+3V3','2':'SWDIO','3':'GND','4':'SWCLK','5':'GND','6':None,'7':None,'8':None,'9':'GND','10':'NRST'},prefix='J')
mc.p('Connector_Generic:Conn_02x04_Odd_Even','JP1 CM5->MCU SWD/boot',{'1':'CM5_SWDIO','2':'SWDIO','3':'CM5_SWCLK','4':'SWCLK','5':'CM5_NRST','6':'NRST','7':'CM5_BOOT0','8':'BOOT0'},prefix='JP')
mc.R('10k','OUT_FAULT_N','+3V3'); mc.R('10k','I2C_INT_N','+3V3')
mc.R('2.2k','I2C1_SCL','+3V3'); mc.R('2.2k','I2C1_SDA','+3V3')
mc.R('10k','ADE_IRQ_N','+3V3'); mc.R('10k','MCU_IRQ','GND')
mc.R('1k','MCU_LED','LED_HB_A'); mc.LED('green','LED_HB_A','GND')
mc.p('Memory_NVRAM:FM24C64B','FM24CL64B',{'A0':'GND','A1':'GND','A2':'GND','VSS':'GND','SDA':'I2C1_SDA','SCL':'I2C1_SCL','WP':'GND','VDD':'+3V3'},mpn='FM24CL64B-GTR')
mc.C('100n','+3V3','GND')
mc.p('genctl:CR2032_Holder','CR2032',{'+':'VBAT_CELL','-':'GND'},mpn='CR2032 holder')
mc.p('Diode:BAT54C','BAT54C',{'1':'+3V3','2':'VBAT_CELL','3':'VBAT_MCU'},prefix='D',mpn='BAT54C',note='VBAT OR: +3V3 / CR2032')
mc.p('Connector_Generic:Conn_02x05_Odd_Even','Header B (MCU spare)',{'1':'+3V3','2':'GND','3':'MCU_SPARE1','4':'MCU_SPARE2','5':'I2C1_SCL','6':'I2C1_SDA','7':'GND','8':'+5V','9':None,'10':None},prefix='J')

# =====================================================================
cm=S('cm5','Raspberry Pi CM5',
 'CM5. GPIO map: 0/1 ID_SD/SC -> header A I2C; 2/3 display I2C (DSI83 + touch); 4 TOUCH_INT_N; 5 TOUCH_RST_N; 6 DSI83_EN; 7 DSI83_IRQ;\n'
 '8-11 SPI0 to MCU (33R series); 12 BL_PWM; 13 BTN_BL_PWM (button backlight dimming, PWM0_CHAN1); 14/15 UART0 to MCU; 16 PANEL_VDD_EN; 17 TOUCH_PWR_EN; 18-21 SPI1 header A;\n'
 '22 CM5_NRST; 23 SWCLK; 24 SWDIO; 25 MCU_IRQ; 26 MODEM_PWR_EN; 27 CM5_BOOT0.')
cma={'GND':'GND','5V':'+5V','CM5_3.3V':'CM5_3V3','CM5_1.8V':'CM5_1V8','GPIO_VREF':'CM5_3V3','VBAT':'CM5_VBAT','nRPIBOOT':'CM5_NRPIBOOT',
 'Ethernet_Pair0_P':'ETH0_P','Ethernet_Pair0_N':'ETH0_N','Ethernet_Pair1_P':'ETH1_P','Ethernet_Pair1_N':'ETH1_N','Ethernet_Pair2_P':'ETH2_P','Ethernet_Pair2_N':'ETH2_N','Ethernet_Pair3_P':'ETH3_P','Ethernet_Pair3_N':'ETH3_N',
 'Ethernet_nLED2':'ETH_LED_LINK_N','Ethernet_nLED3':'ETH_LED_ACT_N','Fan_PWM':'FAN_PWM','Fan_Tacho':'FAN_TACH',
 'ID_SD':'HDRA_SDA','ID_SC':'HDRA_SCL','GPIO2':'DISP_SDA','GPIO3':'DISP_SCL','GPIO4':'TOUCH_INT_N','GPIO5':'TOUCH_RST_N','GPIO6':'DSI83_EN','GPIO7':'CM5_SPI_CE0',
 'GPIO8':'CM5_SPI_CE0X','GPIO9':'CM5_SPI_MISO','GPIO10':'CM5_SPI_MOSI','GPIO11':'CM5_SPI_SCK','GPIO12':'BL_PWM','GPIO13':'BTN_BL_PWM','GPIO14':'CM5_UART_TX','GPIO15':'CM5_UART_RX',
 'GPIO16':'PANEL_VDD_EN','GPIO17':'TOUCH_PWR_EN','GPIO18':'HDRA_SPI_CE0','GPIO19':'HDRA_SPI_MISO','GPIO20':'HDRA_SPI_MOSI','GPIO21':'HDRA_SPI_SCK',
 'GPIO22':'CM5_NRST','GPIO23':'CM5_SWCLK','GPIO24':'CM5_SWDIO','GPIO25':'CM5_MCU_IRQ','GPIO26':'MODEM_PWR_EN','GPIO27':'CM5_BOOT0',
 'LED_nACT':'CM5_LED_ACT_N','LED_nPWR':'CM5_LED_PWR_N','PWR_Button':'CM5_PWR_BTN','EEPROM_nWP':None}
# fix GPIO7 = DSI83_IRQ, GPIO8 = SPI CE0
cma['GPIO7']='DSI83_IRQ'; cma['GPIO8']='CM5_SPI_CE0'
cm.p('genctl:RPi_CM5_A','CM5 (conn A)',cma,mpn='SC1xxx CM5 (variant TBD)')
cmb={'GND':'GND','USB3-0-RX_N':'USB30_RX_N','USB3-0-RX_P':'USB30_RX_P','USB3-0-DP':'USB30_DP','USB3-0-DM':'USB30_DM','USB3-0-TX_N':'USB30_TX_N','USB3-0-TX_P':'USB30_TX_P',
 'USB3-1-DP':'USB31_DP','USB3-1-DM':'USB31_DM','USB_N':'USB_SVC_N','USB_P':'USB_SVC_P','VBUS_EN':'USBA_VBUS_EN'}
for l in ('D0','D1','D2','D3','C'):
    for pn in 'PN': cmb['MIPI0_%s_%s'%(l,pn)]='DSI_%s_%s'%(l,pn)
cm.p('genctl:RPi_CM5_B','CM5 (conn B)',cmb,mpn='CM5')
for _ in range(2): cm.C('22u','+5V','GND',pkg='1206')
dec(cm,'+5V',2); cm.C('100n','CM5_3V3','GND'); cm.C('1u','CM5_3V3','GND'); cm.C('100n','CM5_1V8','GND')
for a,b in (('CM5_SPI_SCK','MCU_SPI_SCK'),('CM5_SPI_MOSI','MCU_SPI_MOSI'),('CM5_SPI_MISO','MCU_SPI_MISO'),('CM5_SPI_CE0','MCU_SPI_NSS'),
            ('CM5_UART_TX','MCU_UART_RX'),('CM5_UART_RX','MCU_UART_TX'),('CM5_MCU_IRQ','MCU_IRQ')):
    cm.R('33R',a,b,note='series/link resistor CM5<->MCU')
cm.R('1k','CM5_VBAT','CM5_VBAT_D'); cm.p('Diode:BAT54C','BAT54C',{'1':'VBAT_CELL','2':None,'3':'CM5_VBAT_D'},prefix='D',mpn='BAT54C',note='CR2032 to CM5 RTC; 2nd anode unused')
cm.p('Switch:SW_Push','nRPIBOOT',{'1':'CM5_NRPIBOOT','2':'GND'},prefix='SW',mpn='TS-1187A-B-A-B')
cm.p('Switch:SW_Push','CM5 PWR',{'1':'CM5_PWR_BTN','2':'GND'},prefix='SW',mpn='TS-1187A-B-A-B',note='optional power button')
cm.R('1k','CM5_3V3','CM5_LED_ACT_A'); cm.LED('green','CM5_LED_ACT_A','CM5_LED_ACT_N')
cm.R('1k','CM5_3V3','CM5_LED_PWR_A'); cm.LED('red','CM5_LED_PWR_A','CM5_LED_PWR_N')
conn(cm,4,['GND','+5V','FAN_TACH','FAN_PWM'],'Fan header (SM04B)',mpn='SM04B-SRSS-TB')
cm.p('Connector_Generic:Conn_02x05_Odd_Even','Header A (CM5 I2C/SPI)',{'1':'CM5_3V3','2':'+5V','3':'HDRA_SDA','4':'HDRA_SCL','5':'HDRA_SPI_SCK','6':'HDRA_SPI_MOSI','7':'HDRA_SPI_MISO','8':'HDRA_SPI_CE0','9':'GND','10':'GND'},prefix='J')
cm.R('10k','CM5_NRST','CM5_3V3',dnp=True,note='DNP - JP1 open by default')

# =====================================================================
co=S('comms','Comms: CAN x2, RS-485, Ethernet, USB hub/ports, LTE modem',
 'COMMS. CAN1/CAN2 CA-IS3062W (VCC=+5V, 4.5-5.5V). Bus: CMC -> NUP2105L -> split termination via DIP (62R+62R, 4.7nF mid).\n'
 'RS-485 CA-IS2092W, SEL=VISO (5V bus), DIP for 120R term + 680R bias. Shields -> CHASSIS via 1M||4.7nF.\n'
 'USB: CM5 USB2 -> USB-C service; USB3-0 -> USB-A (TPS2051C); USB3-1 HS -> USB2514B hub (DN1 M.2 modem, DN2 internal header, DN3/4 spare).')
for i,(tx,rx,iso) in enumerate((('CAN1_TX','CAN1_RX','GND_CAN1'),('CAN2_TX','CAN2_RX','GND_CAN2')),1):
    n='CAN%d'%i
    co.p('genctl:CA-IS3062W','CA-IS3062W',{'VCC':'+5V','TXD':tx,'RXD':rx,'GND1':'GND','NC':None,'VISO':'VISO_%s'%n,'CANH':n+'_H','CANL':n+'_L','GND2':iso},mpn='CA-IS3062W')
    co.C('100n','+5V','GND'); co.C('10u','+5V','GND',pkg='0805'); co.C('100n','VISO_'+n,iso); co.C('10u','VISO_'+n,iso,pkg='0805')
    co.p('genctl:ACT45B-510-2P','ACT45B-510-2P',{'1':n+'_H','4':n+'_HB','2':n+'_L','3':n+'_LB'},mpn='ACT45B-510-2P-TL003')
    co.p('Power_Protection:NUP2105L','NUP2105L',{'1':n+'_HB','2':n+'_LB','3':iso},prefix='D',mpn='NUP2105LT1G')
    co.p('Switch:SW_DIP_x02','TERM',{'1':n+'_HB','4':n+'_TH','2':n+'_LB','3':n+'_TL'},prefix='SW',mpn='DIP switch 2P (BOM)')
    co.R('62R',n+'_TH',n+'_TMID',pkg='1206'); co.R('62R',n+'_TL',n+'_TMID',pkg='1206'); co.C('4.7n',n+'_TMID',iso)
    co.R('1M',n+'_SCR','CHASSIS',pkg='1206'); co.C('4.7n',n+'_SCR','CHASSIS',pkg='1206',note='2kV')
conn(co,4,['CAN1_HB','CAN1_LB','CAN1_SCR','GND_CAN1'],'CAN1 (PC 5/4)',mpn='Phoenix PC 5/4-GF')
co.p('genctl:TPS1H200AQDGNRQ1','TPS1H200AQDGNRQ1',{'VS':'+12V','IN':'EXP_12V_EN','DIAG_EN':'+3V3','CL':'EXP12_CL','DELAY':None,'GND':'GND','EP':'GND','OUT':'EXP_12V','FAULT':'OUT_FAULT_N'},mpn='TPS1H200AQDGNRQ1')
co.R('1.33k','EXP12_CL','GND',note='ILIM ~1.5A (0.8*2500/I)'); co.C('100n','+12V','GND'); co.C('10n','EXP_12V','GND')
schottky(co,'SS110','GND','EXP_12V',mpn='SS110')
conn(co,6,['EXP_12V','GND','CAN2_HB','CAN2_LB','GND_CAN2','CAN2_SCR'],'Expansion bus (PC 5/6)',mpn='Phoenix PC 5/6-GF')
co.p('genctl:CA-IS2092W','CA-IS2092W',{'VCC':'+3V3','DI':'RS485_TX','RO':'RS485_RX','DE':'RS485_DE','~{RE}':'GND','GNDA':'GND','VISO':'VISO_485','SEL':'VISO_485','A':'RS485_A','B':'RS485_B','GNDB':'GND_485','NC':None},mpn='CA-IS2092W')
co.C('100n','+3V3','GND'); co.C('10u','+3V3','GND',pkg='0805'); co.C('100n','VISO_485','GND_485'); co.C('10u','VISO_485','GND_485',pkg='0805')
co.R('10k','RS485_DE','GND')
co.p('Diode:SM712_SOT23','SM712',{'1':'RS485_A','2':'RS485_B','3':'GND_485'},prefix='D',mpn='SM712')
co.p('Switch:SW_DIP_x02','TERM/BIAS',{'1':'RS485_A','4':'RS485_TA','2':'RS485_B','3':'RS485_TB'},prefix='SW',note='ADDED: SW1 term, SW2 term other end - see notes')
co.R('120R','RS485_TA','RS485_TB',pkg='1206')
co.p('Switch:SW_DIP_x02','BIAS',{'1':'VISO_485','4':'RS485_BIASP','2':'GND_485','3':'RS485_BIASN'},prefix='SW',note='ADDED: fail-safe bias enable')
co.R('680R','RS485_BIASP','RS485_A'); co.R('680R','RS485_BIASN','RS485_B')
conn(co,3,['RS485_A','RS485_B','GND_485'],'RS-485 (PC 5/3)',mpn='Phoenix PC 5/3-GF')
# Ethernet (gigabit)
co.p('genctl:HR911131A','HR911131A',{'TRD0+':'ETH0_P','TRD0-':'ETH0_N','TRD1+':'ETH1_P','TRD1-':'ETH1_N','TRD2+':'ETH2_P','TRD2-':'ETH2_N','TRD3+':'ETH3_P','TRD3-':'ETH3_N',
    'CT':'ETH_CT','LED_G_A':'ETH_LEDG_A','LED_G_K':'ETH_LED_LINK_N','LED_Y_A':'ETH_LEDY_A','LED_Y_K':'ETH_LED_ACT_N','SHIELD':'CHASSIS'},mpn='HR911131A',
    note='1000BASE-T magjack; pair order P1/2,P3/4,P7/8,P9/10 = MDI A-D; polarity auto-corrected by PHY')
co.C('100n','ETH_CT','GND',note='voltage-mode PHY: centre taps AC-decoupled only'); co.C('10n','ETH_CT','GND')
co.R('330R','CM5_3V3','ETH_LEDG_A'); co.R('330R','CM5_3V3','ETH_LEDY_A')
co.p('genctl:RClamp0524P','RClamp0524P',{'IO1':'ETH0_P','IO2':'ETH0_N','IO3':'ETH1_P','IO4':'ETH1_N','GND':'GND'},mpn='RCLAMP0524P.TCT')
co.p('genctl:RClamp0524P','RClamp0524P',{'IO1':'ETH2_P','IO2':'ETH2_N','IO3':'ETH3_P','IO4':'ETH3_N','GND':'GND'},mpn='RCLAMP0524P.TCT')
# USB-C service
co.p('Connector:USB_C_Receptacle_USB2.0_16P','USB-C service',{'VBUS':'USBC_VBUS','CC1':'USBC_CC1','CC2':'USBC_CC2','D+':'USB_SVC_P','D-':'USB_SVC_N','GND':'GND','SHIELD':'CHASSIS','SBU1':None,'SBU2':None},prefix='J',mpn='TYPE-C-31-M-12')
co.R('5.1k','USBC_CC1','GND'); co.R('5.1k','USBC_CC2','GND')
co.p('Power_Protection:USBLC6-2SC6','USBLC6-2SC6',{'1':'USB_SVC_P','6':'USB_SVC_P','3':'USB_SVC_N','4':'USB_SVC_N','5':'USBC_VBUS','2':'GND'},prefix='D',mpn='USBLC6-2SC6')
# USB-A
co.p('Power_Management:TPS2051CDBV','TPS2051C',{'IN':'+5V','EN':'USBA_VBUS_EN','GND':'GND','OUT':'USBA_VBUS','~{FLT}':'USBA_FLT_N'},prefix='U',mpn='TPS2051CDBVR')
co.R('10k','USBA_FLT_N','+3V3'); co.C('100n','+5V','GND'); co.C('100u 10V','USBA_VBUS','GND',pol=True,pkg='Capacitor_SMD:CP_Elec_6.3x5.4')
co.p('genctl:USB3_A_Receptacle','USB3 Type-A',{'VBUS':'USBA_VBUS','D-':'USB30_DM','D+':'USB30_DP','GND':'GND','SSRX-':'USB30_RX_N','SSRX+':'USB30_RX_P','GND_DRAIN':'GND','SSTX-':'USBA_SSTX_N','SSTX+':'USBA_SSTX_P','SHIELD':'CHASSIS'})
co.C('100n','USB30_TX_P','USBA_SSTX_P',pkg='0402',note='USB3 TX AC-coupling (check if already on CM5)')
co.C('100n','USB30_TX_N','USBA_SSTX_N',pkg='0402')
co.p('Power_Protection:USBLC6-2SC6','USBLC6-2SC6',{'1':'USB30_DP','6':'USB30_DP','3':'USB30_DM','4':'USB30_DM','5':'USBA_VBUS','2':'GND'},prefix='D',mpn='USBLC6-2SC6')
# Hub
co.p('Interface_USB:USB2514B_Bi','USB2514B',{'VBUS_DET':'HUB_VBUSDET','USBDM_UP':'USB31_DM','USBDP_UP':'USB31_DP','RESET_N':'HUB_RST_N','TEST':'GND','RBIAS':'HUB_RBIAS',
   'XTALIN/CLKIN':'HUB_XI','XTALOUT':'HUB_XO','PLLFILT':'HUB_PLLF','CRFILT':'HUB_CRF','VDDA33':'+3V3','VDD33':'+3V3','VSS':'GND',
   'USBDM_DN1/PRT_DIS_M1':'USB_M2_N','USBDP_DN1/PRT_DIS_P1':'USB_M2_P','USBDM_DN2/PRT_DIS_M2':'USB_INT_N','USBDP_DN2/PRT_DIS_P2':'USB_INT_P','USBDM_DN3/PRT_DIS_M3':'USB_SP3_N','USBDP_DN3/PRT_DIS_P3':'USB_SP3_P','USBDM_DN4/PRT_DIS_M4':'USB_SP4_N','USBDP_DN4/PRT_DIS_P4':'USB_SP4_P',
   '12':None,'16':None,'18':None,'20':None,'13':'HUB_OCS_N','17':'HUB_OCS_N','19':'HUB_OCS_N','21':'HUB_OCS_N',
   '24':'HUB_CFG0','25':'HUB_CFG1','22':'HUB_NONREM1','28':'HUB_NONREM0'},prefix='U',mpn='USB2514B-AEZC-TR')
dec(co,'+3V3',6); co.C('4.7u','+3V3','GND',pkg='1206')
co.C('1u','HUB_PLLF','GND'); co.C('1u','HUB_CRF','GND'); co.R('12k','HUB_RBIAS','GND',note='1%')
co.p('Device:Crystal','24MHz',{'1':'HUB_XI','2':'HUB_XO'},prefix='Y',mpn='24MHz 3225 (TBD)',note='CL assumed 12pF')
co.C('18p','HUB_XI','GND',pkg='0402'); co.C('18p','HUB_XO','GND',pkg='0402'); co.R('1M','HUB_XI','HUB_XO')
co.R('10k','HUB_RST_N','+3V3'); co.C('100n','HUB_RST_N','GND'); co.R('10k','HUB_VBUSDET','+3V3')
for n in ('HUB_CFG0','HUB_CFG1','HUB_NONREM1','HUB_NONREM0'): co.R('10k',n,'GND',note='strap: default config')
co.R('10k','HUB_OCS_N','+3V3')
conn(co,4,['+5V','USB_INT_N','USB_INT_P','GND'],'Internal USB (SM04B)',mpn='SM04B-SRSS-TB')
co.p('Power_Protection:USBLC6-2SC6','USBLC6-2SC6',{'1':'USB_INT_P','6':'USB_INT_P','3':'USB_INT_N','4':'USB_INT_N','5':'+5V','2':'GND'},prefix='D',mpn='USBLC6-2SC6')
conn(co,6,['+5V','USB_SP3_N','USB_SP3_P','USB_SP4_N','USB_SP4_P','GND'],'Spare USB header')
# Modem
co.p('genctl:TPS56637RPAR','TPS56637RPAR',{'VIN':'+12V','EN':'MODEM_PWR_EN_12','MODE':'MDM_MODE','FB':'MDM_FB','AGND':'GND','PGND':'GND','BOOT':'MDM_BOOT','SW':'MDM_SW','PG':None,'NC':None},mpn='TPS56637RPAR',note='3.8V modem rail')
npn(co,'MDM_EN_B','GND','MDM_EN_INV'); co.R('10k','MODEM_PWR_EN','MDM_EN_B'); co.R('100k','MDM_EN_B','GND')
co.R('100k','+12V','MDM_EN_INV'); npn(co,'MDM_EN_INV','GND','MODEM_PWR_EN_12'); co.R('100k','+12V','MODEM_PWR_EN_12',note='EN pull-up; 2 NPN = non-inverting 3V3->12V level shift')
co.R('100k','MDM_MODE','GND',note='TBD'); co.C('100n','MDM_BOOT','MDM_SW'); co.p('Device:L','2.2u',{'1':'MDM_SW','2':'+3V8_MDM'},prefix='L')
co.R('53.6k','+3V8_MDM','MDM_FB'); co.R('10k','MDM_FB','GND'); co.C('10u','+12V','GND',pkg='0805')
co.C('1000u 6.3V','+3V8_MDM','GND',pol=True,pkg='Capacitor_SMD:CP_Elec_10x10.5',note='LTE burst hold-up')
for _ in range(2): co.C('22u','+3V8_MDM','GND',pkg='1206')
co.p('genctl:M.2_KeyB_Modem','M.2 Key B (LTE)',{'3.3V':'+3V8_MDM','GND':'GND','FULL_CARD_PWR_OFF#':'+3V8_MDM','W_DISABLE1#':None,'RESET#':None,'LED1#':'MDM_LED_K',
   'USB_D+':'USB_M2_P','USB_D-':'USB_M2_N','UIM_RESET':'SIM_RST','UIM_CLK':'SIM_CLK','UIM_DATA':'SIM_IO','UIM_PWR':'SIM_VCC','SIM_DETECT':None},mpn='M.2 Key-B socket',note='"3.3V" pins fed 3.8V per BOM/notes (modem dependent!)')
co.R('1k','+3V8_MDM','MDM_LED_A'); co.LED('green','MDM_LED_A','MDM_LED_K')
co.p('Connector:SIM_Card','nano-SIM',{'VCC':'SIM_VCC','RST':'SIM_RST','CLK':'SIM_CLK','GND':'GND','VPP':None,'I/O':'SIM_IO'},prefix='J')
co.p('Power_Protection:SRV05-4','SRV05-4',{'1':'SIM_RST','3':'SIM_CLK','4':'SIM_IO','6':None,'5':'SIM_VCC','2':'GND'},prefix='D',mpn='SRV05-4')
co.C('100n','SIM_VCC','GND')

# =====================================================================
di=S('display','Display: DSI->LVDS bridge, panel power, backlight, touch',
 'DISPLAY RVT121HVLNWCA0-B. SN65DSI83 (1.8V TLV75518, ADDR=0 -> 0x2C). Panel VDD and touch power via TPS22918.\n'
 'Backlight TPS61500: EN=BL_PWM (PWM dim), FREQ 160k (~600kHz assumed), OVP 232k/10k = 29.7V, Rsense 2x1.1R (~360mA). COMP/SS assumed.')
di.p('genctl:TLV75518PDBVR','TLV75518PDBVR',{'IN':'+3V3','EN':'+3V3','GND':'GND','OUT':'+1V8_DSI','NC':None},mpn='TLV75518PDBVR')
di.C('1u','+3V3','GND'); di.C('1u','+1V8_DSI','GND')
dsi={'DA0P':'DSI_D0_P','DA0N':'DSI_D0_N','DA1P':'DSI_D1_P','DA1N':'DSI_D1_N','DA2P':'DSI_D2_P','DA2N':'DSI_D2_N','DA3P':'DSI_D3_P','DA3N':'DSI_D3_N','DACP':'DSI_C_P','DACN':'DSI_C_N',
 'SCL':'DISP_SCL','SDA':'DISP_SDA','ADDR':'GND','EN':'DSI83_EN','IRQ':'DSI83_IRQ','REFCLK':'GND','RSVD1':None,'RSVD2':'GND',
 'A_Y0P':'LVDS0_P','A_Y0N':'LVDS0_N','A_Y1P':'LVDS1_P','A_Y1N':'LVDS1_N','A_Y2P':'LVDS2_P','A_Y2N':'LVDS2_N','A_Y3P':'LVDS3_P','A_Y3N':'LVDS3_N','A_CLKP':'LVDSC_P','A_CLKN':'LVDSC_N',
 'VCC':'+1V8_DSI','VCORE':'DSI83_VCORE','GND':'GND','NC':None}
di.p('genctl:SN65DSI83ZXHR','SN65DSI83ZXHR',dsi,mpn='SN65DSI83ZXHR')
dec(di,'+1V8_DSI',4); di.C('10u','+1V8_DSI','GND',pkg='0805'); di.C('1u','DSI83_VCORE','GND')
di.R('100k','DSI83_EN','GND'); di.C('10n','DSI83_EN','GND'); di.R('10k','DSI83_IRQ','CM5_3V3')
di.p('genctl:TPS22918DBVR','TPS22918DBVR',{'VIN':'+3V3','ON':'PANEL_VDD_EN','CT':'PNL_CT','GND':'GND','VOUT':'+3V3_PANEL','QOD':'+3V3_PANEL'},mpn='TPS22918DBVR',note='panel VDD switch')
di.C('1n','PNL_CT','GND'); di.R('100k','PANEL_VDD_EN','GND'); di.C('10u','+3V3_PANEL','GND',pkg='0805')
di.p('genctl:TPS22918DBVR','TPS22918DBVR',{'VIN':'+3V3','ON':'TOUCH_PWR_EN','CT':'TCH_CT','GND':'GND','VOUT':'+3V3_TOUCH','QOD':'+3V3_TOUCH'},mpn='TPS22918DBVR',note='touch power switch')
di.C('1n','TCH_CT','GND'); di.R('100k','TOUCH_PWR_EN','GND'); di.C('1u','+3V3_TOUCH','GND')
lv=['NC']*40
for p in (2,3,4): lv[p-1]='+3V3_PANEL'
for p in (6,7,10,13,16,19,22,25,28,31,32,33): lv[p-1]='GND'
for p,n in ((8,'LVDS0_N'),(9,'LVDS0_P'),(11,'LVDS1_N'),(12,'LVDS1_P'),(14,'LVDS2_N'),(15,'LVDS2_P'),(17,'LVDSC_N'),(18,'LVDSC_P'),(20,'LVDS3_N'),(21,'LVDS3_P')): lv[p-1]=n
conn(di,40,[None if x=='NC' else x for x in lv],'LVDS FPC 40p 0.5mm',mpn='FPC 40P 0.5mm (BOM)',note='RVT121 LVDS pin map per DS; other pins NC')
conn(di,10,['GND',None,None,None,'GND','+3V3_TOUCH','TOUCH_RST_N','DISP_SCL','TOUCH_INT_N','DISP_SDA'],'Touch FPC 10p 0.5mm',mpn='FPC 10P 0.5mm',note='USB touch pins (2-4) unused - I2C mode')
di.R('10k','TOUCH_RST_N','+3V3_TOUCH'); di.R('10k','TOUCH_INT_N','+3V3_TOUCH')
di.R('2.2k','DISP_SCL','CM5_3V3',dnp=True,note='DNP: CM5 GPIO2/3 have 1.8k on-module pull-ups'); di.R('2.2k','DISP_SDA','CM5_3V3',dnp=True)
di.p('genctl:TPS61500PWPR','TPS61500PWPR',{'VIN':'+12V','EN':'BL_PWM','DIMC':'BL_DIMC','SS':'BL_SS','FREQ':'BL_FREQ','COMP':'BL_COMP','AGND':'GND','EP':'GND','SW':'BL_SW','OVP':'BL_OVP','FB':'BL_FB','PGND':'GND'},mpn='TPS61500PWPR')
di.R('100k','BL_PWM','GND'); di.C('1u','BL_DIMC','GND'); di.C('100n','BL_SS','GND'); di.R('160k','BL_FREQ','GND'); di.C('470n','BL_COMP','GND')
di.p('Device:L','6.8u',{'1':'+12V','2':'BL_SW'},prefix='L'); schottky(di,'SS34','BL_SW','VLED',mpn='SS34')
for _ in range(2): di.C('10u','+12V','GND',pkg='0805')
for _ in range(2): di.C('4.7u','VLED','GND',pkg='1206',note='50V')
di.R('232k','VLED','BL_OVP'); di.R('10k','BL_OVP','GND')
di.R('1.1R','BL_FB','GND',pkg='0805'); di.R('1.1R','BL_FB','GND',pkg='0805')
conn(di,2,['VLED','BL_FB'],'Backlight (JST)',note='1 LEDA, 2 LEDK')

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
inp.p('Reference_Voltage:LM4040DBZ-2.5','LM4040A25',{'K':'VBAT_P','A':'AI_VSET'},prefix='D',mpn='LM4040AIM3-2.5')
inp.R('10k','AI_VSET','GND',pkg='1206',note='ref bias ~1-2.8mA')
inp.C('100n','VBAT_P','AI_VSET')
ADC={1:('ADC1','AIN0'),2:('ADC1','AIN1'),3:('ADC1','AIN2'),4:('ADC2','AIN0'),5:('ADC2','AIN1'),6:('ADC2','AIN2')}
oas={}
for ch in range(1,7):
    a='AI%d'%ch
    tvs(inp,'SMAJ36CA',a); inp.C('100n',a,'GND',pkg='1206',note='100V')
    inp.R('2.49k','VBAT_P',a+'_E',note='0.1% 1mA set'); pnp(inp,a+'_B',a+'_E',a+'_C')
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
    inp.p('Amplifier_Operational:LM2904','LM2904',c,prefix='U',mpn='LM2904DR'); inp.C('100n','VBAT_P','GND',pkg='0805')
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
ou=S('outputs','Outputs: fuel/crank (TPS48100), 13x TPS1HTC30, watchdog gating, readback',
 'OUTPUTS. All MCU enables gated by TPS3431 WDO (LVC1G08 for fuel/crank/glow, LVC541 OE for the rest). Fuel/crank: TPS48100 + 2x BSC070N10NS5 + 1mR shunt +\n'
 'INA281A2 from VBAT_ESTOP. Small outputs TPS1HTC30 from VBAT_P: ILIM 40.2k, SNS 1.1k -> TMUX1208 -> ADC. Readback via NPN to TCA9555 @0x23.')
ou.p('genctl:TPS3431SDRBR','TPS3431SDRBR',{'VDD':'+3V3','EN':'+3V3','SET1':'+3V3','CWD':'WD_CWD','WDI':'WDI','GND':'GND','WDO':'WDO_N','ENOUT':None},mpn='TPS3431SDRBR')
ou.R('10k','WD_CWD','+3V3',note='CWD via 10k to VDD = factory timing (assumed)'); ou.R('10k','WDO_N','+3V3'); ou.C('100n','+3V3','GND')
npn(ou,'WD_INV_B','GND','WD_OE_N'); ou.R('10k','WDO_N','WD_INV_B'); ou.R('100k','WD_INV_B','GND'); ou.R('10k','WD_OE_N','+3V3')
for n in ('FUEL','CRANK','GLOW'):
    ou.p('74xGxx:74LVC1G08','74LVC1G08',{'1':n+'_EN_MCU','2':'WDO_N','4':n+'_EN','5':'+3V3','3':'GND'},prefix='U',mpn='SN74LVC1G08DBVR'); ou.C('100n','+3V3','GND'); ou.R('100k',n+'_EN','GND')
small=['GCB_CL','GCB_OP','MCB_CL','MCB_OP']+['AUX%d'%i for i in range(1,9)]
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
    ou.R('100k','VBAT_ESTOP',n+'_UVLO'); ou.R('27k',n+'_UVLO','GND'); ou.R('35.7k',n+'_ISCP',n+'_DRN',note='ISCP R - reference node assumed CS-; verify'); ou.C('68n',n+'_TMR','GND')
    ou.C('470n',n+'_BST',n+'_OUT'); ou.C('100n','VBAT_ESTOP','GND',pkg='0805')
    ou.R('10R',n+'_GPU',n+'_G'); ou.R('0R',n+'_GPD',n+'_G')
    ou.R('1m','VBAT_ESTOP',n+'_DRN',pkg='2512',mpn='WSLP2512 1mR',note='shunt')
    for _ in range(2): fet(ou,'Transistor_FET:BSC070N10NS5','BSC070N10NS5',n+'_G',n+'_OUT',n+'_DRN')
    ou.p('Amplifier_Current:INA281A2','INA281A2',{'OUT':n+'_ISNS','GND':'GND','Vin+':'VBAT_ESTOP','Vin-':n+'_DRN','V+':'+3V3'},prefix='U',mpn='INA281A2QDBVRQ1'); ou.C('100n','+3V3','GND')
    tvs(ou,'SMBJ28CA',n+'_OUT')
schottky(ou,'SK1010C','GND','FUEL_CLMP',mpn='SK1010C'); tvs(ou,'SMDJ24A','FUEL_CLMP','FUEL_OUT',uni=True)
schottky(ou,'SK1010C','GND','CRANK_OUT',mpn='SK1010C')
# small outputs
outs=['GLOW']+small
mux={}
for i,n in enumerate(outs):
    ou.p('genctl:TPS1HTC30QPWPRQ1','TPS1HTC30QPWPRQ1',{'VS':'VBAT_P','EN':n+'_EN','DIAG_EN':'DIAG_EN','LATCH':'GND','ILIM':n+'_ILIM','GND':'GND','VOUT':n+'_OUT','SNS':n+'_SNS','FAULT':'OUT_FAULT_N','NC':None},mpn='TPS1HTC30QPWPRQ1')
    ou.R('40.2k',n+'_ILIM','GND'); ou.R('1.1k',n+'_SNS','GND'); ou.R('1k',n+'_SNS',n+'_SNSM'); ou.C('100n','VBAT_P','GND',pkg='0805')
    schottky(ou,'SS110','GND',n+'_OUT',mpn='SS110'); tvs(ou,'SMBJ28CA',n+'_OUT')
    mux[n]=n+'_SNSM'
rb=['FUEL','CRANK']+outs
for n in rb:
    ou.R('10k',n+'_OUT',n+'_LED',pkg='1206',note='LED limit 10k (was 1k in BOM - too hot at 24V)'); ou.LED('green',n+'_LED','GND')
    ou.R('100k',n+'_OUT',n+'_RBB'); ou.R('10k',n+'_RBB','GND'); npn(ou,n+'_RBB','GND',n+'_RB_N')
tca(ou,3,{('P0%d'%i if i<8 else 'P1%d'%(i-8)):rb[i]+'_RB_N' for i in range(15)} | {'P17':None})
mA=[mux[n] for n in outs[:8]]; mB=[mux[n] for n in outs[8:]]+['ESTOP_TRIP_SNSM','GND','GND']
for nm,lst in (('MUXA_OUT',mA),('MUXB_OUT',mB)):
    c={'D':nm,'A0':'MUX_A0','A1':'MUX_A1','A2':'MUX_A2','EN':'+3V3','VDD':'+3V3','GND':'GND','GND/NC?':'GND'}
    for i,s_ in enumerate(lst): c['S%d'%(i+1)]=s_
    ou.p('genctl:TMUX1208PWR','TMUX1208PWR',c,mpn='TMUX1208PWR'); ou.C('100n','+3V3','GND'); ou.C('10n',nm,'GND')
conn(ou,4,['VBAT_ESTOP','VBAT_ESTOP','FUEL_OUT','CRANK_OUT'],'J4 E-stop/fuel/crank (PC 5/4-7.62)',mpn='Phoenix PC 5/4-GF-7,62')
conn(ou,6,['GLOW_OUT','GCB_CL_OUT','GCB_OP_OUT','MCB_CL_OUT','MCB_OP_OUT','ESTOP_TRIP_OUT'],'J5A outputs')
conn(ou,6,['GND','GND','GND','GND',None,None],'J5B returns')
conn(ou,6,['AUX1_OUT','AUX2_OUT','AUX3_OUT','AUX4_OUT','AUX5_OUT','AUX6_OUT'],'J6A AUX1-6')
conn(ou,6,['AUX7_OUT','AUX8_OUT','GND','GND','GND','GND'],'J6B AUX7-8 + returns')

# =====================================================================
es=S('estop','E-stop trip and sense',
 'E-STOP (estop_notes v5). VBAT_ESTOP open -> Q 47k/10k releases 555 RESET; TRIG RC (100k/100n) fires one-shot 1.1*200k*10u = 2.2s.\n'
 '555 powered from +5V_TRIP (TPS7B6950 from VBAT_P via SS110 + hold-up). BAT54C OR of 555 Q and (MCU_TRIP AND WDO) -> TPS1HTC30 ESTOP_TRIP.\n'
 'ADDED: 4th LVC1G08 gates MCU_TRIP with WDO. Hold-up cap changed to 50V (BOM 25V part < 30V OV threshold).')
schottky(es,'SS110','VBAT_P','TRIP_LDO_IN',mpn='SS110')
es.C('10u','TRIP_LDO_IN','GND',pkg='1210',note='50V (BOM 25V too low)')
es.p('genctl:TPS7B6950QDBVRQ1','TPS7B6950QDBVRQ1',{'IN':'TRIP_LDO_IN','GND':'GND','OUT':'+5V_TRIP','NC':None},mpn='TPS7B6950QDBVRQ1')
es.C('2.2u','+5V_TRIP','GND',pkg='0805'); es.C('100n','+5V_TRIP','GND')
es.R('47k','VBAT_ESTOP','TRIP_QB'); es.R('10k','TRIP_QB','GND'); npn(es,'TRIP_QB','GND','TRIP_RST')
es.R('10k','+5V_TRIP','TRIP_RST'); es.R('100k','TRIP_RST','TRIP_TRIG'); es.C('100n','TRIP_TRIG','GND')
es.p('Timer:TLC555xD','TLC555CDR',{'VCC':'+5V_TRIP','GND':'GND','TR':'TRIP_TRIG','CV':'TRIP_CV','R':'TRIP_RST','Q':'TRIP_555_Q','DIS':'TRIP_TIM','THR':'TRIP_TIM'},prefix='U',mpn='TLC555CDR')
es.R('200k','+5V_TRIP','TRIP_TIM'); es.C('10u','TRIP_TIM','GND',pkg='0805'); es.C('100n','TRIP_CV','GND'); es.C('100n','+5V_TRIP','GND')
es.p('74xGxx:74LVC1G08','74LVC1G08',{'1':'MCU_TRIP','2':'WDO_N','4':'MCU_TRIP_G','5':'+3V3','3':'GND'},prefix='U',mpn='SN74LVC1G08DBVR',note='ADDED 4th gate'); es.C('100n','+3V3','GND')
es.R('100k','MCU_TRIP','GND')
es.p('Diode:BAT54C','BAT54C',{'1':'TRIP_555_Q','2':'MCU_TRIP_G','3':'ESTOP_TRIP_EN'},prefix='D',mpn='BAT54C'); es.R('100k','ESTOP_TRIP_EN','GND')
es.p('genctl:TPS1HTC30QPWPRQ1','TPS1HTC30QPWPRQ1',{'VS':'VBAT_P','EN':'ESTOP_TRIP_EN','DIAG_EN':'DIAG_EN','LATCH':'GND','ILIM':'ESTOP_TRIP_ILIM','GND':'GND','VOUT':'ESTOP_TRIP_OUT','SNS':'ESTOP_TRIP_SNS','FAULT':'OUT_FAULT_N','NC':None},mpn='TPS1HTC30QPWPRQ1')
es.R('13.3k','ESTOP_TRIP_ILIM','GND',note='~ILIM per BOM'); es.R('1.1k','ESTOP_TRIP_SNS','GND'); es.R('1k','ESTOP_TRIP_SNS','ESTOP_TRIP_SNSM'); es.C('100n','VBAT_P','GND',pkg='0805')
schottky(es,'SS110','GND','ESTOP_TRIP_OUT',mpn='SS110'); tvs(es,'SMBJ28CA','ESTOP_TRIP_OUT')
es.R('10k','ESTOP_TRIP_OUT','ESTOP_TRIP_LED',pkg='1206'); es.LED('red','ESTOP_TRIP_LED','GND')
es.R('100k','VBAT_ESTOP','VESTOP_SNS',note='0.1%'); es.R('10k','VESTOP_SNS','GND',note='0.1%'); es.C('100n','VESTOP_SNS','GND'); clamp(es,'VESTOP_SNS','BAT54S')
tvs(es,'SMBJ28CA','VBAT_ESTOP')

# =====================================================================
ac=S('ac_metering','AC metering: 2x ADE9000 (gen + bus), isolated',
 'AC METERING. Hot side GND_AC isolated by ISOW7841 (data+power) + ISO7741, both 5kVrms reinforced, SOIC-16W 8mm. Barrier keep-out >=8mm + slot.\n'
 'Voltage: fully differential. Each line 4x1M -> tap (1k to GND_AC); each neutral (GEN_N, BUS_N separately) 4x1M -> N_TAP (1k to GND_AC); VxN <- 1k <- N_TAP.\n'
 'No 0R neutral link: GND_AC floats at the divider mid-point, common-mode attenuated 4001:1. Current: AC1005 CTs, burden 2x24.9R.')
ac.p('genctl:ISOW7841DWE','ISOW7841DWER',{'VCC':'+3V3','GND1':'GND','INA':'ADE_SCK','INB':'ADE_MOSI','INC':'ADE_CS1_N','OUTD':'ADE_MISO','NC':None,
   'VISO':'+3V3_AC','GND2':'GND_AC','OUTA':'AC_SCK','OUTB':'AC_MOSI','OUTC':'AC_CS1_N','IND':'AC_MISO','SEL':'GND_AC'},mpn='ISOW7841DWER',note='5kVrms reinforced; SEL=GND2 -> VISO 3.3V')
ac.C('10u','+3V3','GND',pkg='0805'); ac.C('100n','+3V3','GND'); ac.C('10u','+3V3_AC','GND_AC',pkg='0805'); ac.C('100n','+3V3_AC','GND_AC')
ac.p('genctl:ISO7741DW','ISO7741DWR',{'VCC1':'+3V3','GND1':'GND','INA':'ADE_CS2_N','INB':'ADE_RST_N','INC':'GND','OUTD':'ADE_IRQ_N','EN1':'+3V3',
   'VCC2':'+3V3_AC','GND2':'GND_AC','OUTA':'AC_CS2_N','OUTB':'AC_RST_N','OUTC':None,'IND':'AC_IRQ_N','EN2':'+3V3_AC'},mpn='ISO7741DWR',note='5kVrms reinforced')
ac.C('100n','+3V3','GND'); ac.C('100n','+3V3_AC','GND_AC')
ac.R('10k','AC_IRQ_N','+3V3_AC'); ac.R('10k','AC_RST_N','+3V3_AC')
for k,(tag,clkin,clkout) in enumerate((('GEN','ADE_XI','ADE_XO'),('BUS','ADE_XO2',None)),1):
    c={'VDD':'+3V3_AC','PULL_HIGH':'+3V3_AC','AVDDOUT':'AVDD_%s'%tag,'DVDDOUT':'DVDD_%s'%tag,'REF':'REF_%s'%tag,'SCLK':'AC_SCK','MOSI':'AC_MOSI','MISO':'AC_MISO',
       '~{SS}':'AC_CS%d_N'%k,'~{RESET}':'AC_RST_N','~{IRQ0}':'AC_IRQ_N' if k==1 else None,'~{IRQ1}':None,'CF1':None,'CF2':None,'CF3/ZX':None,'CF4/EVENT':None,'PM0':'GND_AC','PM1':'GND_AC',
       'DGND':'GND_AC','REFGND':'GND_AC','NC1':'GND_AC','NC2':'GND_AC','AGND':'GND_AC','GND':'GND_AC','EP':'GND_AC','CLKIN':clkin if k==1 else 'ADE_XO','CLKOUT':clkout}
    for ph in 'ABC': c['V%sP'%ph]='%s_V%s_P'%(tag,ph); c['V%sN'%ph]='%s_V%s_N'%(tag,ph)
    if k==1:
        for i,ph in enumerate('ABCN'): c['I%sP'%ph]='GEN_I%s_P'%ph; c['I%sN'%ph]='GEN_I%s_N'%ph
    else:
        for ph in 'ABCN': c['I%sP'%ph]='GND_AC'; c['I%sN'%ph]='GND_AC'
    ac.p('genctl:ADE9000ACPZ','ADE9000ACPZ (%s)'%tag,c,mpn='ADE9000ACPZ')
    ac.C('4.7u','AVDD_'+tag,'GND_AC',pkg='0805'); ac.C('100n','AVDD_'+tag,'GND_AC'); ac.C('4.7u','DVDD_'+tag,'GND_AC',pkg='0805'); ac.C('100n','DVDD_'+tag,'GND_AC')
    ac.C('4.7u','REF_'+tag,'GND_AC',pkg='0805'); ac.C('100n','REF_'+tag,'GND_AC'); ac.C('10u','+3V3_AC','GND_AC',pkg='0805'); ac.C('100n','+3V3_AC','GND_AC')
ac.p('Device:Crystal','24.576MHz',{'1':'ADE_XI','2':'ADE_XO'},prefix='Y',mpn='24.576MHz 3225 (TBD)'); ac.C('22p','ADE_XI','GND_AC',pkg='0402'); ac.C('22p','ADE_XO','GND_AC',pkg='0402')
for tag,J in (('GEN','J7'),('BUS','J8')):
    conn(ac,4,[tag+'_L1',tag+'_L2',tag+'_L3',tag+'_N'],'%s %s voltage (L1 L2 L3 N)'%(J,tag),note='external DIN fuses assumed (spec); >=600VAC rated terminal')
    for ph,L in zip('ABC',('L1','L2','L3')):
        ac.p('Device:Varistor','V20E385P',{'1':tag+'_'+L,'2':tag+'_N'},prefix='RV',mpn='V20E385P')
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
    ac.p('genctl:AC1005','AC1005',{'P1':'CT%d_S1'%i,'P2':'CT%d_S2'%i,'S1':'GEN_CT%s_1'%ph,'S2':'GEN_CT%s_2'%ph},mpn='AC1005')
    ac.R('24.9R','GEN_CT%s_1'%ph,'GND_AC',note='0.1% burden'); ac.R('24.9R','GEN_CT%s_2'%ph,'GND_AC',note='0.1% burden')
    ac.R('1k','GEN_CT%s_1'%ph,'GEN_I%s_P'%ph); ac.C('33n','GEN_I%s_P'%ph,'GND_AC'); ac.R('1k','GEN_CT%s_2'%ph,'GEN_I%s_N'%ph); ac.C('33n','GEN_I%s_N'%ph,'GND_AC')
    cts+=['CT%d_S1'%i,'CT%d_S2'%i]
conn(ac,8,cts,'J9 CT secondaries (5A)',note='external 5A CT loops pass through AC1005 cores')

# =====================================================================
fp_=S('frontpanel','Front panel: backlit buttons, buzzer',
 'FRONT PANEL. 12x CTS 228EMVARGBFR IP67 RGB-backlit tactile switches. Switch -> TCA9555 @0x20 (internal pull-ups).\n'
 'Backlight: common anodes on BTN_LED_V (+5V via AO3401A high-side, gated by CM5 GPIO13 BTN_BL_PWM = global dimming, default off).\n'
 'Cathodes R/G/B per button via 330R/330R/200R (~8-9mA) to TCA9555 @0x21/@0x24/@0x25, active low. OFF = pin set as input (Hi-Z).')
b={}
for i in range(12): b[('P0%d'%i) if i<8 else 'P1%d'%(i-8)]='BTN%d'%(i+1)
for i in range(12,16): b['P1%d'%(i-8)]=None
tca(fp_,0,b)
ch=[]
for i in range(12):
    n=i+1
    fp_.p('genctl:228EMVARGBFR','BTN%d'%n,{'A':'BTN%d'%n,'B':'GND','L1':'BTN_LED_V','L2':'BTN%d_GK'%n,'L3':'BTN%d_RK'%n,'L4':'BTN%d_BK'%n},prefix='SW',mpn='228EMVARGBFR')
    for col,r in (('R','330R'),('G','330R'),('B','200R')):
        fp_.R(r,'BTN%d_%sK'%(n,col),'BL%d_%s'%(n,col),note='LED %s ~8-9mA from 5V'%col); ch.append('BL%d_%s'%(n,col))
pins=[('P0%d'%k) for k in range(8)]+[('P1%d'%k) for k in range(8)]
for addr,chunk in ((1,ch[0:16]),(4,ch[16:32]),(5,ch[32:36])):
    m={pn:None for pn in pins}
    for pn,net in zip(pins,chunk): m[pn]=net
    tca(fp_,addr,m)
fp_.R('1k','BTN_BL_PWM','BL_Q_B'); fp_.R('100k','BL_Q_B','GND',note='default off'); npn(fp_,'BL_Q_B','GND','BL_PG')
fp_.R('10k','+5V','BL_PG',note='PFET gate pull-up'); fet(fp_,'Transistor_FET:AO3401A','AO3401A','BL_PG','+5V','BTN_LED_V')
fp_.C('1u','BTN_LED_V','GND',pkg='0603'); fp_.C('10u','+5V','GND',pkg='0805')
fp_.R('1k','BUZZER_PWM','BUZ_B'); fp_.R('100k','BUZ_B','GND'); npn(fp_,'BUZ_B','GND','BUZ_K')
fp_.p('Device:Buzzer','MLT-8530',{'1':'BUZ_K','2':'+3V3'},prefix='BZ',mpn='MLT-8530')
fp_.p('Diode:1N4148W','1N4148W',{'A':'BUZ_K','K':'+3V3'},prefix='D',mpn='1N4148W')
fp_.C('10u','+3V3','GND',pkg='0805')
