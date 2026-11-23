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
    cap=dict(c.inst['C199'][0]['props']); cap.pop('Reference'); res=dict(c.inst['R349'][0]['props']); res.pop('Reference')
    U=c.newref('U'); c.add('cards:AT24CS32-STUM',U,'AT24CS32-STUM-T',{'1':'I2C_SCL','2':'GND','3':'I2C_SDA','4':'+3V3_ID','5':'ID_WP'},
      {'Footprint':'Package_TO_SOT_SMD:SOT-23-5','MPN':'AT24CS32-STUM-T','Manufacturer':'Microchip','LCSC':'C147891','Description':'Card ID + calibration EEPROM (0x50 / serial 0x58)'})
    C=c.newref('C'); c.add('Device:C',C,cap['Value'],{'1':'+3V3_ID','2':'GND'},cap)
    R=c.newref('R'); c.add('Device:R',R,res['Value'],{'1':'+3V3_ID','2':'ID_WP'},res)
    return [U,C,R]
def mcp(c,gpa,gpb):
    """MCP23S17 on the slot SPI bus. RESET has a 10k pull-down: an unpowered/undriven reset holds every GPIO as input (Hi-Z)."""
    cap=dict(c.inst['C199'][0]['props']); cap.pop('Reference'); res=dict(c.inst['R349'][0]['props']); res.pop('Reference')
    U=c.newref('U'); pn={'9':'+3V3_SLOT','10':'GND','11':'SPI_CS_N','12':'SPI_SCK','13':'SPI_MOSI','14':'SPI_MISO','15':'GND','16':'GND','17':'GND',
                       '18':'RST_N','19':None,'20':'INT_N'}
    for i in range(8): pn[str(21+i)]=gpa[i]; pn[str(1+i)]=gpb[i]
    c.add('cards:MCP23S17-SS',U,'MCP23S17T-E/SS',pn,{'Footprint':'Package_SO:SSOP-28_5.3x10.2mm_P0.65mm','MPN':'MCP23S17T-E/SS','Manufacturer':'Microchip','LCSC':'C128577',
          'Description':'16-bit SPI I/O expander (card I/O). INTA open-drain (IOCON.ODR)'})
    C=c.newref('C'); c.add('Device:C',C,cap['Value'],{'1':'+3V3_SLOT','2':'GND'},cap)
    R=c.newref('R'); c.add('Device:R',R,res['Value'],{'1':'RST_N','2':'GND'},res)
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
            c.parts.append(dict(ref=nr,lib_id=i['lib_id'],unit=i['unit'],props=props,pins=pins,pn=pn,dnp=i['dnp'],lsym=lsym))
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
