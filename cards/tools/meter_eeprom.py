# One-shot edit applied to genctl_meter.kicad_sch (M-mod P2): HV-METER AT24CS32 ID/cal EEPROM on J32.12/J32.16. Kept for provenance; do not re-run on the edited file.
import re,uuid
U=lambda:str(uuid.uuid4())
def block(s,key):
    i=s.index(key); d=0
    for j in range(i,len(s)):
        if s[j]=='(': d+=1
        elif s[j]==')':
            d-=1
            if d==0: return s[i:j+1]
p='genctl_meter.kicad_sch'; s=open(p).read()
root=re.search(r'\(path "(/[0-9a-f-]+)" \(reference "J32"',s).group(1)
# 1) J32.12: GND symbol -> MTR_ID_SCL label (J32.15 stays MTR_DET_N GND strap) ; J32.16: NC -> MTR_ID_SDA
g=block(s,'(symbol (lib_id "power:GND") (at 116.84 88.90 0)'); s=s.replace(g+'\n','',1) if g+'\n' in s else s.replace(g,'',1)
s=s.replace('(no_connect (at 109.22 99.06) (uuid "a6c1f913-3635-47c7-bca4-8c30e6dba803"))\n','')
def glabel(name,x,y,ang,just):
    return f'(global_label "{name}" (shape bidirectional) (at {x:.2f} {y:.2f} {ang}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {just})) (uuid "{U()}") (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide)))'
def wire(a,b): return f'(wire (pts (xy {a[0]:.2f} {a[1]:.2f}) (xy {b[0]:.2f} {b[1]:.2f})) (stroke (width 0) (type default)) (uuid "{U()}"))'
pwrn=[0]
def pwr(kind,x,y):
    pwrn[0]+=1; ref='#PWR%d'%(2900+pwrn[0])
    vy=y-3.81 if kind=='+3V3' else y+3.81
    return (f'(symbol (lib_id "power:{kind}") (at {x:.2f} {y:.2f} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}")\n'
      f'(property "Reference" "{ref}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n(property "Value" "{kind}" (at {x:.2f} {vy:.2f} 0) (effects (font (size 1.27 1.27))))\n'
      f'(property "Footprint" "" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n(property "Datasheet" "~" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
      f'(pin "1" (uuid "{U()}"))\n(instances (project "genctl_meter" (path "{root}" (reference "{ref}") (unit 1))))\n)')
def part(lib,ref,val,x,y,pins,props,rx=2.54,rpos=None):
    o=f'(symbol (lib_id "{lib}") (at {x:.2f} {y:.2f} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}")\n'
    (rxp,ryp),(vxp,vyp)=rpos if rpos else ((x+rx,y-1.27),(x+rx,y+1.27))
    o+=f'(property "Reference" "{ref}" (at {rxp:.2f} {ryp:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))\n(property "Value" "{val}" (at {vxp:.2f} {vyp:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))\n'
    for k,v in props.items(): o+=f'(property "{k}" "{v}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
    for pn in pins: o+=f'(pin "{pn}" (uuid "{U()}"))\n'
    return o+f'(instances (project "genctl_meter" (path "{root}" (reference "{ref}") (unit 1))))\n)'
add=[]
add+= [wire((109.22,99.06),(116.84,99.06)), glabel('MTR_ID_SCL',116.84,88.90,0,'left'), glabel('MTR_ID_SDA',116.84,99.06,0,'left')]
X,Y=200.66,91.44
add+= [glabel('MTR_ID_SCL',185.42,88.90,180,'right'), wire((185.42,88.90),(193.04,88.90)),
       glabel('MTR_ID_SDA',185.42,93.98,180,'right'), wire((185.42,93.98),(193.04,93.98)),
       pwr('+3V3',X,83.82), pwr('GND',X,99.06)]
add.append(part('genctl:AT24CS32-STUM','U94','AT24CS32-STUM-T',X,Y,['1','2','3','4','5'],
  {'Footprint':'Package_TO_SOT_SMD:SOT-23-5','Datasheet':'https://ww1.microchip.com/downloads/en/DeviceDoc/AT24CS32-I2C-Compatible-Two-Wire-Serial-EEPROM-32-Kbit-Serial-Number-DS20005792.pdf',
   'LCSC':'C147891','MPN':'AT24CS32-STUM-T','Manufacturer':'Microchip','Description':'HV-METER card ID + calibration EEPROM, type 0x0020; 0x50 array, 0x58 serial; WP high = protected'},rpos=((203.20,85.09),(203.20,101.60))))
# WP pull-up + cal-write pad
add+= [wire((208.28,91.44),(220.98,91.44)), wire((220.98,91.44),(228.60,91.44)), f'(junction (at 220.98 91.44) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))', pwr('+3V3',220.98,83.82)]
add.append(part('Device:R','R650','10k',220.98,87.63,['1','2'],{'Footprint':'Resistor_SMD:R_0603_1608Metric','Datasheet':'~','LCSC':'C98220','MPN':'RC0603FR-0710KL','Manufacturer':'YAGEO','Description':'WP pull-up: EEPROM write-protected unless TP3 is shorted to GND'}))
add.append(part('Connector:TestPoint','TP3','EE_WP',228.60,91.44,['1'],{'Footprint':'TestPoint:TestPoint_Pad_D1.5mm','Datasheet':'~','Description':'short to GND only for factory/calibration write of U94'}).replace('(in_bom yes)','(in_bom no)',1))
add+= [pwr('+3V3',238.76,83.82), pwr('GND',238.76,91.44)]
add.append(part('Device:C','C323','100n',238.76,87.63,['1','2'],{'Footprint':'Capacitor_SMD:C_0603_1608Metric','Datasheet':'~','LCSC':'C14663','MPN':'CC0603KRX7R9BB104','Manufacturer':'YAGEO','Description':'U94 decoupling'}))
add.append(f'(text "HV-METER ID / calibration EEPROM (type 0x0020, Phase 2).\\nJ32.12 MTR_ID_SCL, J32.16 MTR_ID_SDA (were GND / NC),\\nharness pin n to pin n to mainboard J31.12/16, TCA9548A\\nslot-ID channel (pull-ups on mainboard). SELV side, not GND_AC." (exclude_from_sim no) (at 185.42 113.03 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{U()}"))')
# lib symbols
cs=open('cards/lib/cards.kicad_sym').read(); ee=block(cs,'(symbol "AT24CS32-STUM"').replace('(symbol "AT24CS32-STUM"','(symbol "genctl:AT24CS32-STUM"',1)
rs=block(open('ac_metering.kicad_sch').read(),'(symbol "Device:R"')
s=s.replace('(lib_symbols\n','(lib_symbols\n'+ee+'\n'+rs+'\n',1)
# wires: 3-segment at J32.15 already exists (109.22->116.84 at 96.52)
i=s.rindex('(sheet_instances') if '(sheet_instances' in s else s.rindex(')')
s=s[:i]+'\n'.join(add)+'\n'+s[i:]
s=s.replace('J32.15 MTR_DET_N strapped to GND here (board detect). J32.16 spare (NC).','J32.15 MTR_DET_N strapped to GND here (board detect). J32.12 / J32.16 = ID EEPROM I2C (Phase 2).')
open(p,'w').write(s)
# project symbol library
gs=open('genctl.kicad_sym').read()
if 'AT24CS32-STUM' not in gs:
    j=gs.rindex(')'); open('genctl.kicad_sym','w').write(gs[:j]+block(cs,'(symbol "AT24CS32-STUM"')+'\n'+gs[j:])
print('ok',root)
