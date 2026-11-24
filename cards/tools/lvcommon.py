"""Shared pieces for the universal LV cards: slot connector (LV pinout), ID EEPROM, SPI expander, copies of baseline blocks."""
import os,sys,csv,collections,re,copy
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from mkcard import ROOT,lib_pins
from srcdb import short
LV_CSV=os.path.join(ROOT,'docs','modular','slot_pinout_LV.csv')
def lv_pinout():
    """slot pin -> card net. FIELD_GND contacts join GND on the card (high-current return group);
    PRESENT_N is tied to GND on every card; RSVD 18a = ID_WP (EEPROM write enable, Phase 2)."""
    P={}
    for r in csv.DictReader(open(LV_CSV)):
        pos=int(r['position'])
        for row in 'abc':
            n=r['row_'+row]
            if n in('FIELD_GND','PRESENT_N'): n='GND'
            if n=='RSVD': n=None
            P[f'{row}{pos}']=n
    return P
def slot(c,mpn_note=''):
    P=lv_pinout(); JS=c.newref('J')
    din={'Footprint':'cards:DIN41612_C96_Male_RA_WingTAT_9001-11961','MPN':'9001-11961C00A','Manufacturer':'WingTAT','LCSC':'C5173361',
         'Description':'Universal LV slot plug, DIN 41612 C96 RA male, LV coding notch. Pinout docs/modular/slot_pinout_LV.csv'}
    for u,r in enumerate('abc',1): c.add('cards:DIN41612_C96',JS,'DIN41612_C96',{k:v for k,v in P.items() if k[0]==r},din,unit=u)
    return JS,P
def eeprom(c):
    cap=dict(c.inst['C199'][0]['props']); cap.pop('Reference'); cap.pop('Note',None); res=r10k('ID_WP pull-up: write-protected unless the backplane pulls ID_WP low')
    U=c.newref('U'); c.add('cards:AT24CS32-STUM',U,'AT24CS32-STUM-T',{'1':'I2C_SCL','2':'GND','3':'I2C_SDA','4':'+3V3_ID','5':'ID_WP'},
      {'Footprint':'Package_TO_SOT_SMD:SOT-23-5','MPN':'AT24CS32-STUM-T','Manufacturer':'Microchip','LCSC':'C147891','Description':'Card ID + calibration EEPROM (0x50 / serial 0x58)'})
    C=c.newref('C'); c.add('Device:C',C,cap['Value'],{'1':'+3V3_ID','2':'GND'},cap)
    R=c.newref('R'); c.add('Device:R',R,res['Value'],{'1':'+3V3_ID','2':'ID_WP'},res)
    return [U,C,R]
NEWP={'C6059':{'Footprint':'Package_SO:TSSOP-14_4.4x5mm_P0.65mm','MPN':'74LVC125APW,118','Manufacturer':'Nexperia','LCSC':'C6059',
           'Description':'Slot SPI/reset input buffer, IOFF (+/-10 uA at VCC 0 V): no back-power from the live slot bus into an unpowered card'},
      'C23654':{'Footprint':'Package_TO_SOT_SMD:SOT-23-5','MPN':'SN74LVC1G125DBVR','Manufacturer':'Texas Instruments','LCSC':'C23654',
           'Description':'Slot MISO driver, 3-state (OE# = buffered CS_N), Ioff'},
      'C7829':{'Footprint':'Package_TO_SOT_SMD:SOT-23-5','MPN':'SN74LVC1G07DBVR','Manufacturer':'Texas Instruments','LCSC':'C7829',
           'Description':'Slot INT_N open-drain driver, Ioff (MCP23S17 INTA push-pull active-low into A)'},
      'C25819':{'Value':'47k','Footprint':'Resistor_SMD:R_0603_1608Metric','MPN':'0603WAF4702T5E','Manufacturer':'UNI-ROYAL','LCSC':'C25819','Description':'boot-safe default'},
      'C25804':{'Value':'10k','Footprint':'Resistor_SMD:R_0603_1608Metric','MPN':'0603WAF1002T5E','Manufacturer':'UNI-ROYAL','LCSC':'C25804','Description':''},
      'C23140':{'Value':'33R','Footprint':'Resistor_SMD:R_0603_1608Metric','MPN':'0603WAF330JT5E','Manufacturer':'UNI-ROYAL','LCSC':'C23140','Description':''},
      'C21190':{'Value':'1k','Footprint':'Resistor_SMD:R_0603_1608Metric','MPN':'0603WAF1001T5E','Manufacturer':'UNI-ROYAL','LCSC':'C21190','Description':''},
      'C25803':{'Value':'100k','Footprint':'Resistor_SMD:R_0603_1608Metric','MPN':'0603WAF1003T5E','Manufacturer':'UNI-ROYAL','LCSC':'C25803','Description':''}}
def r10k(desc=''):
    """Pass 2 m16: new 10k card pull-ups are 0603 (C25804), not the baseline R349 1206 part."""
    d=dict(NEWP['C25804']); d['Description']=desc; return d
def capp(c): cap=dict(c.inst['C199'][0]['props']); cap.pop('Reference'); cap.pop('Note',None); return cap   # Pass 4 m3
def res(c,lcsc,a,b,desc=''):
    d=dict(NEWP[lcsc]); d['Description']=desc or d['Description']; R=c.newref('R'); c.add('Device:R',R,d['Value'],{'1':a,'2':b},d); return R
def slotbuf(c):
    """B1 fix (pass 1): every slot logic line crosses an IOFF buffer powered from +3V3_SLOT, so an unpowered card
    (or a card whose 3V3 is shorted) never back-powers the MCP23S17 and never clamps the shared slot bus.
    In: SPI_CS_N/SCK/MOSI/RST_N -> 74LVC125A (OE# = GND) -> CS_N_B/SCK_B/MOSI_B/RST_N_B.
    Out: MISO_B -> 1G125 (OE# = CS_N_B) -> 33R -> SPI_MISO; INTA_B (100k pull-up) -> 1G07 (open drain) -> INT_N."""
    cap=capp(c); out=[]
    U=c.newref('U'); c.add('cards:74LVC125APW',U,'74LVC125APW,118',{'2':'SPI_CS_N','3':'CS_N_B','5':'SPI_SCK','6':'SCK_B','9':'SPI_MOSI','8':'MOSI_B',
        '12':'RST_N','11':'RST_N_B','1':'GND','4':'GND','10':'GND','13':'GND','14':'+3V3_SLOT','7':'GND'},NEWP['C6059']); out.append(U)
    C=c.newref('C'); c.add('Device:C',C,cap['Value'],{'1':'+3V3_SLOT','2':'GND'},cap)
    U2=c.newref('U'); c.add('cards:74LVC1G125',U2,'SN74LVC1G125DBVR',{'1':'CS_N_B','2':'MISO_B','3':'GND','4':'MISO_S','5':'+3V3_SLOT'},NEWP['C23654']); out.append(U2)
    res(c,'C23140','MISO_S','SPI_MISO','Pass 2 m4: 33R source series at the 1G125 output (shared MISO, 8 slots + engine)')
    C=c.newref('C'); c.add('Device:C',C,cap['Value'],{'1':'+3V3_SLOT','2':'GND'},cap)
    res(c,'C25803','MISO_B','GND','MISO_B pull-down: 1G125 input defined while MCP23S17 SO is 3-state')
    res(c,'C25803','INTA_B','+3V3_SLOT','Pass 2 m3: INTA_B pull-up, 1G07 input defined while the MCP23S17 is in reset')
    U3=c.newref('U'); c.add('cards:74LVC1G07',U3,'SN74LVC1G07DBVR',{'1':None,'2':'INTA_B','3':'GND','4':'INT_N','5':'+3V3_SLOT'},NEWP['C7829']); out.append(U3)
    C=c.newref('C'); c.add('Device:C',C,cap['Value'],{'1':'+3V3_SLOT','2':'GND'},cap)
    return out
def mcp(c,gpa,gpb):
    """MCP23S17 behind the slot buffers (slotbuf). RESET has a 10k pull-down: an unpowered/undriven reset holds every GPIO as input (Hi-Z).
    INTA push-pull (IOCON.ODR = 0, INTPOL = 0: active low) into the 1G07 open-drain slot driver."""
    cap=capp(c); res_=r10k('MCP23S17 RESET pull-down: GPIO Hi-Z until the buffered RST_N releases')
    U=c.newref('U'); pn={'9':'+3V3_SLOT','10':'GND','11':'CS_N_B','12':'SCK_B','13':'MOSI_B','14':'MISO_B','15':'GND','16':'GND','17':'GND',
                       '18':'RST_N_B','19':None,'20':'INTA_B'}
    for i in range(8): pn[str(21+i)]=gpa[i]; pn[str(1+i)]=gpb[i]   # unused GPIO: NC, firmware sets GPPU=1 (defined, never driven)
    c.add('cards:MCP23S17-SS',U,'MCP23S17T-E/SS',pn,{'Footprint':'Package_SO:SSOP-28_5.3x10.2mm_P0.65mm','MPN':'MCP23S17T-E/SS','Manufacturer':'Microchip','LCSC':'C128577',
          'Description':'16-bit SPI I/O expander (card I/O), behind IOFF slot buffers. INTA push-pull active low (IOCON.ODR=0) into 1G07. Unused GPIO NC with GPPU on'})
    C=c.newref('C'); c.add('Device:C',C,cap['Value'],{'1':'+3V3_SLOT','2':'GND'},cap)
    R=c.newref('R'); c.add('Device:R',R,res_['Value'],{'1':'RST_N_B','2':'GND'},res_)
    return [U,C,R]
def copy_parts(c,refs,netfn,tag='copy'):
    """Copy baseline parts (same symbol, value, footprint, LCSC) onto the card with new refs; nets via netfn(full_net)->name|None."""
    out={}
    for r in refs:
        insts=c.inst[r]; prefix=re.match(r'[A-Z]+',r).group(0); nr=c.newref(prefix); out[r]=nr
        for i in sorted(insts,key=lambda x:x['unit']):
            lsym=c.srclibs[i['lib_id']]; c.libs[i['lib_id']]=lsym; pins=lib_pins(lsym,i['unit'])
            pn={p['num']:netfn(c.pinnet.get((r,p['num']),'unconnected-'),p['num']) for p in pins}
            props=dict(i['props']); props['Reference']=nr; props['BaselineRef']=f'{tag}:{r}'
            c.parts.append(dict(ref=nr,lib_id=i['lib_id'],unit=i['unit'],props=props,pins=pins,pn=pn,dnp=i['dnp'],lsym=lsym,carried='copy:'+r))
    c.copymap=dict(getattr(c,'copymap',{})); c.copymap.update(out)
    return out
def bfs(c,seeds,stop_refs,rails):
    """baseline parts reachable from seeds through non-rail nets, not crossing nets that touch stop_refs."""
    byref=collections.defaultdict(list)
    for (r,p),n in c.pinnet.items(): byref[r].append(n)
    nodes=collections.defaultdict(list)
    for n in c.nets:
        for r,p in n['nodes']: nodes[n['name']].append(r)
    seen=set(seeds); todo=list(seeds)
    while todo:
        r=todo.pop()
        for n in byref[r]:
            if short(n) in rails or n.startswith('unconnected-'): continue
            if any(x in stop_refs for x in nodes[n]): continue
            for x in nodes[n]:
                if x not in seen: seen.add(x); todo.append(x)
    return seen
