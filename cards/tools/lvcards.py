"""Universal LV cards: DI-8, AI-4, HSO-5, BRK-4. Each card is self-contained (own bias / references / ADC / expander /
clamps), conforms to docs/modular/slot_pinout_LV.csv and carries an AT24CS32 ID EEPROM. Baseline circuitry is MOVED
(same parts); extra copies of baseline blocks carry BaselineRef 'copy:<ref>'. Every intentional net change is listed in
cards/<name>/net_changes.csv."""
import os,sys,re,csv,collections,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from mkcard import Card,ROOT,short
from partition import ASSIGN
import lvcommon as L, schdraw
from verify_card import verify

TYPES={'di8':0x0010,'ai4':0x0011,'hso5':0x0012,'brk4':0x0013}
COMMON_RENAME={'VBAT_P':'VBAT_FIELD','+3V3_SAFE':'+3V3_SLOT','OUT_FAULT_N':'CARD_FAULT_N'}
RAILS={'GND','+3V3_SLOT','+3V3_ID','VBAT_FIELD'}

def setup(name,title,rename):
    c=Card(name,title)
    R=dict(COMMON_RENAME); R.update(rename)
    for n in c.nets:
        sn=short(n['name'])
        if sn in R: c.netmap[n['name']]=R[sn]
    c.rename=R; c.changes=[]; c.vchanges=[]
    return c
def retarget(c,bref,pin,new,why):
    for p in c.parts:
        if p['props'].get('BaselineRef')==bref and pin in p['pn']:
            old=p['pn'][pin]; p['pn'][pin]=new; c.changes.append((bref,pin,old,new,why)); return
    raise KeyError((bref,pin))
def nf(c,extra=None,default_keep=True):
    """netfn for copies: rename map, then extra (short->new), auto nets prefixed by copy."""
    def f(full,pin):
        if full.startswith('unconnected-'): return None
        sn=short(full)
        if extra and sn in extra: return extra[sn]
        if sn in c.rename: return c.rename[sn]
        return c.netname(full)
    return f
def header(c,nets,desc):
    J18=c.inst['J18'][0]['props']; h=dict(J18); [h.pop(k,None) for k in ('Reference','Value','Note')]
    J=c.newref('J'); c.add('Connector_Generic:Conn_01x06',J,desc,{str(i+1):n for i,n in enumerate(nets)},h); return J
def pullup(c,net,rail='+3V3_SLOT'):
    res=L.r10k(f'{net} pull-up to {rail}'); R=c.newref('R'); c.add('Device:R',R,res['Value'],{'1':rail,'2':net},res); return R
R0603='Resistor_SMD:R_0603_1608Metric'
VAL={'33.2k':dict(Value='33.2k',Footprint=R0603,MPN='0603WAF3322T5E',Manufacturer='UNI-ROYAL',LCSC='C23003'),
     '910':dict(Value='910',Footprint=R0603,MPN='0603WAF9100T5E',Manufacturer='UNI-ROYAL',LCSC='C23264'),
     '4.7k':dict(Value='4.7k',Footprint=R0603,MPN='0603WAF4701T5E',Manufacturer='UNI-ROYAL',LCSC='C23162'),
     'C100N100V':dict(Value='100n',Footprint='Capacitor_SMD:C_0805_2012Metric',MPN='CL21B104KCFNNNE',Manufacturer='Samsung Electro-Mechanics',LCSC='C28233'),
     'C2U2100V':dict(Value='2.2u',Footprint='Capacitor_SMD:C_1206_3216Metric',MPN='CL31B225KCHSNNE',Manufacturer='Samsung Electro-Mechanics',LCSC='C170101')}
def revalue(c,ref,key,why):
    """change Value/MPN/LCSC of a MOVED baseline part (connectivity unchanged); recorded in value_changes.csv"""
    for p in c.parts:
        if p['ref']==ref:
            old=p['props'].get('Value'); p['props'].update(VAL[key]); c.vchanges.append((p['props'].get('BaselineRef'),ref,old,VAL[key]['Value'],why)); return
    raise KeyError(ref)
def newpart(c,key,a,b,desc):
    d=dict(VAL[key]); d['Description']=desc; pre='C' if key.startswith('C') else 'R'; r=c.newref(pre)
    c.add('Device:'+pre,r,d['Value'],{'1':a,'2':b},d); return r
def pulls(c,nets,rail,desc):
    return [L.res(c,'C25819',n,rail,desc) for n in nets]
def bufcopy(c,inputs,outputs):
    """SN74LVC541A (copy of baseline U42): both OE pins on OUT_EN_N (slot, active low, card pull-up) -> outputs Hi-Z unless enabled."""
    pinmap={'1':'OUT_EN_N','19':'OUT_EN_N','10':'GND','20':'+3V3_SLOT'}
    for i in range(8):
        pinmap[str(2+i)]=inputs[i] if i<len(inputs) else 'GND'; pinmap[str(18-i)]=outputs[i] if i<len(outputs) else None
    return L.copy_parts(c,['U42'],lambda full,pin:pinmap[pin])['U42']
def finish(c,blocks,slot_ref,fields,paper,notes,replaced,labels_only=(),extra=None,rails=(),pad=1):
    c.notes=notes
    cnt=collections.Counter(v for p in c.parts if p['ref']!=slot_ref for v in p['pn'].values() if v)
    for p in c.parts:
        if p['ref']==slot_ref:
            for k,v in p['pn'].items():
                if v and v not in RAILS and cnt[v]==0: p['pn'][k]=None; c.P[k]=None   # slot signal unused on this card: NC
    c.write(os.path.join(ROOT,'cards',c.name))      # project files + refmap (sheet re-drawn below)
    D=schdraw.Drawer(c,RAILS|set(rails),blocks,paper,notes); D.labels_only=set(labels_only)|{slot_ref}; D.pad=pad; D.extra=dict(extra or {})
    for p in c.parts:
        if p['lib_id']=='Device:C' and p['ref'] not in D.extra and p['props'].get('BaselineRef') is None: D.extra[p['ref']]=blocks[-1][0]
    over=schdraw.run(D,os.path.join(ROOT,'cards',c.name),c.title)
    slot=collections.defaultdict(list)
    for k,v in c.P.items():
        if v: slot[v].append(k)
    field={}
    for p in c.parts:
        if p['ref'] in fields:
            for k,v in p['pn'].items():
                if v: field.setdefault(v,f"{p['ref']}.{k}")
    ov={(b,p):n for b,p,o,n,w in c.changes}
    errs,unacc=verify(c.name,slot,field,ov,c.netmap,replaced)
    with open(os.path.join(ROOT,'cards',c.name,'net_changes.csv'),'w',newline='') as f:
        w=csv.writer(f); w.writerow(['baseline_ref','pin','baseline_net','card_net','why'])
        for r in c.changes: w.writerow(r)
        for r in c.vchanges: w.writerow([r[0],'(value)',r[2],r[3],r[4]])
        for k,v in sorted(c.rename.items()): w.writerow(['(rename)','',k,v,'card-local name'])
    print(c.name,'parts',len({p['ref'] for p in c.parts}),'overflow',over,'left',D.left)
    return errs,unacc,over

def B(c,*refs):
    return [k for r in refs for k in sorted((p['ref'],p['unit']) for p in c.parts if p['props'].get('BaselineRef') in (r,'copy:'+r) or p['ref']==r)]

# ---------------------------------------------------------------- DI-8
def di8(paper=None):
    paper=os.environ.get('PAPER','A3')
    rn={f'DI{5+i}':f'IN{1+i}' for i in range(8)}
    rn.update({f'DI{5+i}_D':f'IN{1+i}_D' for i in range(8)}); rn.update({f'DI{5+i}_N':f'IN{1+i}_N' for i in range(8)})
    rn.update({'DI_BIAS_B':'BIAS','DI_PU_B':'BIAS_ON','DI_PD_B':'BIAS_DISCH','DI_BIAS_FLT_N':'CARD_FAULT_N'})
    c=setup('di8','DI-8 card (type 0x0010): 8 digital inputs',rn)
    bias=['U90','Q39','Q40','Q41','F102','C311','C312','C313','D148','R205','R206','R207','R208','R633','R634','R209']
    moved=sorted(r for r,v in ASSIGN.items() if v=='DI8')+['U33','J20','J22']+bias
    c.move(moved)
    for r in ('R222','R225'): retarget(c,r,'1','BIAS','IN1/IN2 (baseline DI5/DI6) pull-ups move from bank-A bias to the card bias')
    retarget(c,'J22','2','IN1','J22 becomes IN1/IN2/BIAS header (was DI_BIAS_B only)')
    retarget(c,'J22','3','IN2','J22 becomes IN1/IN2/BIAS header')
    retarget(c,'J22','4','GND','J22 return terminal')
    # own Schmitt triggers for IN1/IN2 (copy of U32, unused gates: input GND, output NC)
    sm={'DI5_D':'IN1_D','DI6_D':'IN2_D','DI5_N':'IN1_N','DI6_N':'IN2_N','DI1_D':'GND','DI2_D':'GND','DI3_D':'GND','DI4_D':'GND','DI1_N':None,'DI2_N':None,'DI3_N':None,'DI4_N':None}
    L.copy_parts(c,['U32'],nf(c,sm))
    JS,c.P=L.slot(c); ee=L.eeprom(c)
    buf=L.slotbuf(c)
    mc=L.mcp(c,[f'IN{i}_N' for i in range(1,9)],['BIAS_ON','BIAS_DISCH',None,None,'SLOT_ID0','SLOT_ID1','SLOT_ID2','SLOT_IDP'])
    blocks=[('Slot connector (universal LV slot) - DIN 41612 C96',B(c,JS)),
      ('Card bias supply: switch + eFuse + PTC + TVS + discharge',B(c,'Q39','Q40','U90','Q41')),
      ('Inputs IN1-IN8 (field headers J20: IN3-IN8, J22: IN1, IN2)',B(c,'J20','J22')),
      ('Schmitt triggers',B(c,'U33','U32')),
      ('IOFF slot buffers + SPI I/O expander + card ID EEPROM',B(c,*buf,mc[0],ee[0]))]
    notes=['DI-8 CARD, card type 0x0010. Fits any universal LV slot (LV coding notch).',
      'Self-contained: own bias supply (copy of baseline bank-B switch/eFuse, fed from VBAT_FIELD), own 74HC14 Schmitt triggers, own MCP23S17 on the slot SPI bus.',
      'MCP23S17: GPA0-7 = IN1_N..IN8_N; GPB0 BIAS_ON, GPB1 BIAS_DISCH, GPB2/GPB3 unused (NC, GPPU on), GPB4-7 slot ID straps (GPPU on). CARD_FAULT_N (TPS26621 FLT, open drain, 62 V abs max to RTN) goes to the slot only; pulled up on the backplane, read by U-exp 0x22.',
      'Slot logic behind IOFF buffers (74LVC125A in, 1G125 MISO + 33R, 1G07 INT_N, INTA_B 100k pull-up): an unpowered card never loads the slot bus.',
      'Baseline names: IN1..IN8 = DI5..DI12, BIAS = DI_BIAS_B. Net changes: net_changes.csv.']
    replaced={f'IN{i}_N':'was a 74HC14 output to an STM32 pin (series R on mainboard); now read by the card MCP23S17' for i in range(1,9)}
    replaced.update({'BIAS_ON':'was driven by mainboard TCA9555 U31 P16; now card MCP23S17 GPB0','BIAS_DISCH':'was mainboard TCA9555 U31 P17; now MCP23S17 GPB1',
      'CARD_FAULT_N':'was DI_BIAS_FLT_N to mainboard TCA9555 U76 (shared with bank A); now card fault to the slot only (pull-up + 0x22 expander on the backplane)',
      'IN1':'field terminal moved from mainboard J19.5 to card J22.2','IN2':'field terminal moved from mainboard J19.6 to card J22.3',
      'IN1_D':'mainboard U32 gate replaced by the card 74HC14 copy','IN2_D':'mainboard U32 gate replaced by the card 74HC14 copy'})
    return finish(c,blocks,JS,[c.refmap['J20'],c.refmap['J22']],paper,notes,replaced,rails={'BIAS'})


# ---------------------------------------------------------------- AI-4
def ai4(paper=None):
    paper=os.environ.get('PAPER','A2')   # pass 1 additions (IOFF buffers, boot pulls) no longer pack on A3
    rn={}
    for i,b in enumerate((3,4,5,6)):
        k=i+1; rn.update({f'AI{b}':f'IN{k}',f'AI{b}_ADC':f'IN{k}_ADC',f'AI_CS_DIS{b}':f'CS_DIS{k}',f'AI_SH_EN{b}':f'SH_EN{k}',f'AI_SH_G{b}':f'SH_G{k}'})
    import srcdb
    for nn in srcdb.load()[1]:
        sn=short(nn['name'])
        for i,b in enumerate((3,4,5,6)):
            if sn.startswith(f'AI{b}_') and sn not in rn: rn[sn]=f'IN{i+1}_'+sn[len(f'AI{b}_'):]
    c=setup('ai4','AI-4 card (type 0x0011): 4 analog inputs',rn)
    moved=sorted(r for r,v in ASSIGN.items() if v=='AI4')+['C137','D32','R162','C139','D35','R173','C141','D38','R184','C143','D41','R195']
    c.move(moved)
    # own ADS1115 (copy of U30): AIN0-3 = IN1-4, ADDR=GND -> 0x48 on the slot I2C bus
    um={'1':'GND','2':None,'3':'GND','4':'IN1_ADC','5':'IN2_ADC','6':'IN3_ADC','7':'IN4_ADC','8':'+3V3_SLOT','9':'I2C_SDA','10':'I2C_SCL'}
    adc=L.copy_parts(c,['U30'],lambda n,p:um[p])['U30']
    for p in c.parts:
        if p['ref']==adc: p['props']['Value']='ADS1115 @0x48'   # ADDR = GND -> 0x48 (pass 1 N1)
    L.copy_parts(c,['C130'],nf(c))                                   # ADC decoupling
    L.copy_parts(c,['U25','R127','R128','C128'],nf(c))               # own VMID buffer
    L.copy_parts(c,['Q72','R628','D146','C144','C145','C146','D23','C131','R129'],nf(c))  # own VBAT_AI + AI_VSET current-source reference
    rm={'AI_SH_G1':'SH_G1','AI_SH_G2':'SH_G2','AI_SH_G3':'SH_G3','AI_SH_G4':'SH_G4'}
    L.copy_parts(c,['RN1'],nf(c,rm))                                 # shunt-gate pull-downs (off when '541 is Hi-Z)
    buf=bufcopy(c,[f'SH_EN{i}' for i in range(1,5)],[f'SH_G{i}' for i in range(1,5)])
    pu=pullup(c,'OUT_EN_N','+3V3_ID')
    pd=pulls(c,[f'SH_EN{i}' for i in range(1,5)],'GND','boot-safe: shunt request low while MCP23S17 is reset/Hi-Z')
    pu2=pulls(c,[f'CS_DIS{i}' for i in range(1,5)],'+3V3_SLOT','boot-safe: CS_DIS high = current source OFF (baseline TCA9555 POR high) while MCP23S17 is reset/Hi-Z')
    JS,c.P=L.slot(c); ee=L.eeprom(c); buf2=L.slotbuf(c)
    # Pass 2 m9: TPS2553 has no output discharge (only TPS25530-1 has QOD). 4 live loops back-feed ~0.94 mA via R9..R12 100k + BAV99 into an
    # unpowered +3V3_SLOT; 1k holds it at <= 0.94 V (below the 1.65 V LVC / 1.8 V MCP23S17 minimum VCC). 3.3 mA / 11 mW when powered.
    bl=L.res(c,'C21190','+3V3_SLOT','GND','Pass 2 m9: +3V3_SLOT bleeder, back-feed from live inputs held <= 0.94 V')
    mc=L.mcp(c,[f'CS_DIS{i}' for i in range(1,5)]+[f'SH_EN{i}' for i in range(1,5)],['SLOT_ID0','SLOT_ID1','SLOT_ID2','SLOT_IDP',None,None,None,None])
    J=header(c,['IN1','IN2','IN3','IN4','GND','GND'],'AI_FIELD')
    blocks=[('Slot connector (universal LV slot) - DIN 41612 C96',B(c,JS)),
      ('Field inputs IN1-IN4: current source, shunt, filter, clamp',B(c,J,*[r for r in moved])),
      ('ADC + mid-rail reference',B(c,adc,'U25','R127','R128','C128','C130')),
      ('Current-source supply VBAT_AI + 2.5 V reference',B(c,'Q72','R628','D146','C144','C145','C146','D23','C131','R129')),
      ("Shunt gate drive ('541 gated by OUT_EN_N) + boot-safe defaults",B(c,buf,'RN1',pu,*pd)),
      ('IOFF slot buffers + SPI I/O expander + card ID EEPROM',B(c,*buf2,mc[0],ee[0],*pu2,bl))]
    notes=['AI-4 CARD, card type 0x0011. 4 configurable analog inputs (0-5/0-10 V, 4-20 mA shunt, resistive sender via current source).',
      'Self-contained: own ADS1115 (0x48 on the slot I2C bus), own VMID buffer, own VBAT_AI pre-regulator and LM4040 current-source reference, own MCP23S17.',
      'MCP23S17: GPA0-3 CS_DIS1-4 (47k pull-up: source OFF at reset), GPA4-7 SH_EN1-4 (47k pull-down: shunt open at reset); GPB0-3 slot ID straps, GPB4-7 unused (NC, GPPU on). Shunts only close while OUT_EN_N is low (backplane: PWR_EN AND WD_OK AND NRST AND SLOT_RST_N AND slot ARM).',
      'Slot logic behind IOFF buffers (74LVC125A in, 1G125 MISO + 33R, 1G07 INT_N, INTA_B 100k pull-up); OUT_EN_N pull-up on +3V3_ID (always on). 1k +3V3_SLOT bleeder: live loops cannot back-power the card (<= 0.94 V).',
      'Baseline names: IN1..IN4 = AI3..AI6. Net changes: net_changes.csv.']
    replaced={}
    for i,b in enumerate((3,4,5,6)):
        k=i+1
        replaced[f'IN{k}']=f'field terminal moved from mainboard J17.{b} to the card header'
        replaced[f'IN{k}_ADC']='mainboard ADS1115 input replaced by the card ADS1115 copy'
        replaced[f'CS_DIS{k}']='was mainboard TCA9555 U31; now card MCP23S17 GPA'
        replaced[f'SH_G{k}']="was 74LVC08 (SH_EN AND SH_ALLOW) on mainboard; now card '541 gated by OUT_EN_N"
    for n in ('VBAT_AI','VMID','AI_VSET','+3V3_SLOT','VBAT_FIELD'): replaced[n]='card-local copy of the baseline rail/reference (engine card keeps its own)'
    return finish(c,blocks,JS,[J],paper,notes,replaced,rails={'VBAT_AI','AI_VSET'})

def grow(c,seed,allowed,rails):
    """baseline refs reachable from seed through non-rail nets, visiting only allowed refs."""
    byref=collections.defaultdict(list); nodes=collections.defaultdict(list)
    for n in c.nets:
        for r,p in n['nodes']: nodes[n['name']].append(r); byref[r].append(n['name'])
    seen={seed}; todo=[seed]
    while todo:
        r=todo.pop()
        for n in byref[r]:
            if short(n) in rails or n.startswith('unconnected-'): continue
            for x in nodes[n]:
                if x in allowed and x not in seen: seen.add(x); todo.append(x)
    return seen

# ---------------------------------------------------------------- HSO-5 / BRK-4 (high-side output cards)
def hso_card(name,title,typ,part,outs,extra_moves,clamp,straps,notes,nc_pins=(),paper='A2',pad=1):
    """outs: baseline output prefixes in card order (OUT1..). Each card: its outputs' high-side switches (moved), own '541
    (OUT_EN_N gated), own TMUX1208 current-sense mux to ANA_OUT, own MCP23S17, own clamps, CARD_FAULT_N pull-up."""
    rn={'DIAG_EN':'DIAG_EN'}
    for k,b in enumerate(outs,1):
        rn.update({f'{b}_EN':f'OUT{k}_EN',f'{b}_OUT':f'OUT{k}',f'{b}_RB_N':f'OUT{k}_RB_N',f'{b}_SNSM':f'OUT{k}_SNSM'})
    import srcdb
    for nn in srcdb.load()[1]:
        sn=short(nn['name'])
        for k,b in enumerate(outs,1):
            if sn.startswith(b+'_') and sn not in rn: rn[sn]=f'OUT{k}_'+sn[len(b)+1:]
    c=setup(name,title,rn)
    moved=sorted(r for r,v in ASSIGN.items() if v==part)+extra_moves
    c.move(moved)
    for r,pin,why in nc_pins: retarget(c,r,pin,None,why)
    if clamp: L.copy_parts(c,[clamp[0]],lambda n,p:clamp[1][p])
    n=len(outs)
    buf=bufcopy(c,[f'OUT{k}_REQ' for k in range(1,n+1)],[f'OUT{k}_EN' for k in range(1,n+1)])
    S=['4','5','6','7','12','11','10','9']
    tm={'1':'MUX_A0','16':'MUX_A1','15':'MUX_A2','2':'+3V3_SLOT','3':None,'13':'+3V3_SLOT','14':'GND','8':'ANA_OUT'}
    for i,pn in enumerate(S): tm[pn]=f'OUT{i+1}_SNSM' if i<n else 'GND'
    mux=L.copy_parts(c,['U63'],lambda nn,p:tm[p])['U63']
    L.copy_parts(c,['C182'],nf(c))
    pu=pullup(c,'OUT_EN_N','+3V3_ID')
    pd=pulls(c,[f'OUT{k}_REQ' for k in range(1,n+1)]+['DIAG_EN','MUX_A0','MUX_A1','MUX_A2'],'GND','boot-safe: low while MCP23S17 is reset/Hi-Z')
    JS,c.P=L.slot(c); ee=L.eeprom(c); sbuf=L.slotbuf(c)
    # M1 + M2 + N17 (pass 1): per-driver VS decoupling, card bulk, ILIM 33.2k, SNS 910 / 4.7k series into the clamp
    vs={}; bulk=newpart(c,'C2U2100V','VBAT_FIELD','GND','card bulk on VBAT_FIELD, 100 V X7R (slot SCP blanking ~70 us >> 2.7 uF charge time)')
    for u in sorted([r for r in moved if r.startswith('U')],key=lambda r:int(r[1:])):
        cu=c.refmap[u]; vs[cu]=newpart(c,'C100N100V','VBAT_FIELD','GND',f'{cu} VS decoupling (TPS1HTC30-Q1 C_IC >= 100 nF)')
        pp=[p for p in c.parts if p['ref']==cu][0]; ilim=pp['pn']['7']; sns=pp['pn']['6']
        for q in c.parts:
            if q['lib_id']!='Device:R': continue
            nets=set(q['pn'].values())
            if ilim in nets: revalue(c,q['ref'],'33.2k','ILIM 33.2k: I_CL = 80..120 A*kOhm / 33.2k = 2.41/3.01/3.61 A')
            elif sns in nets and 'GND' in nets: revalue(c,q['ref'],'910','R_SNS 910: 3.61 A / 1300 x 910 = 2.53 V < V_SNSFH min 3.0 V')
            elif sns in nets: revalue(c,q['ref'],'4.7k','SNS series 4.7k: clamp current <= 0.13 mA, S pin <= VDD + 0.25 V (BAT54C VF max 240 mV @ 0.1 mA)')
    gpa=[f'OUT{k}_REQ' for k in range(1,n+1)]+['DIAG_EN']; gpb=[f'OUT{k}_RB_N' for k in range(1,n+1)]+['MUX_A0','MUX_A1','MUX_A2']
    free=[None]*(16-len(gpa)-len(gpb)); st=list(straps)
    gpa+= [st.pop(0) if st else None for _ in range(8-len(gpa))]; gpb+=[st.pop(0) if st else None for _ in range(8-len(gpb))]
    mc=L.mcp(c,gpa,gpb)
    J=header(c,[f'OUT{k}' for k in range(1,n+1)]+['GND']*(6-n),'OUT_FIELD')
    sw=sorted([r for r in moved if r.startswith('U')],key=lambda r:int(r[1:]))
    clamps=[r for r in moved if c.comps[r]['value'].startswith('BAT54C')]; clamp_new=[p['ref'] for p in c.parts if p['props'].get('BaselineRef','').startswith('copy:D')]
    grp=[]; taken=set(clamps)
    for u in sw:
        g=[r for r in sorted(grow(c,u,set(moved)-set(sw)-set(clamps)|{u},{'GND','+3V3_SAFE','VBAT_P','DIAG_EN','OUT_FAULT_N'})) if r not in taken]
        taken|=set(g); grp.append(g)
    rest=[r for r in moved if r not in taken]
    blocks=[('Slot connector (universal LV slot) - DIN 41612 C96',B(c,JS))]
    chunks=[(k,k+1) for k in range(n)] if os.environ.get('SPLIT1') else ([(0,2),(2,4),(4,n)] if n==5 else [(0,2),(2,4)])
    for a,b2 in chunks:
        refs=[r for g in grp[a:b2] for r in g]+(rest+[J] if b2==n else [])
        lab=f'OUT{a+1}' if b2-a==1 else f'OUT{a+1}-OUT{b2}'
        blocks.append((f'High-side switch {lab}: driver, sense resistor, readback, clamps'+(' + field header' if b2==n else ''),B(c,*refs)))
    blocks.append(("Enable buffer ('541, OUT_EN_N) + boot-safe pull-downs",B(c,buf,pu,*pd)))
    blocks.append(('Sense mux to ANA_OUT + clamps',B(c,mux,'C182',*clamps,*clamp_new)))
    blocks.append(('IOFF slot buffers (no back-power into an unpowered card)',B(c,*sbuf)))
    blocks.append(('SPI I/O expander + card ID EEPROM',B(c,mc[0],ee[0])))
    xb={}
    for t,keys in blocks:
        for cu,cr in vs.items():
            if any(k[0]==cu for k in keys): xb[cr]=t
    xb[bulk]=blocks[1][0]
    replaced={'DIAG_EN':'was one mainboard net shared by all 15 high-side switches; now driven by the card MCP23S17',
              'CARD_FAULT_N':'was the board-wide OUT_FAULT_N wired-OR (R44 pull-up); now a per-card fault line to the slot, pulled up on the backplane only (TPS1HTC30 FAULT abs max 7 V to GND, no VS clamp)',
              'MUX_A0':'card-local mux select from the MCP23S17','MUX_A1':'card-local mux select','MUX_A2':'card-local mux select'}
    for k,b in enumerate(outs,1):
        replaced[f'OUT{k}']=f'field terminal moved from the mainboard output header to the card header'
        replaced[f'OUT{k}_EN']="was mainboard '541 U41/U42 output; now the card '541"
        replaced[f'OUT{k}_RB_N']='was mainboard TCA9555 U62 input; now card MCP23S17'
        replaced[f'OUT{k}_SNSM']='was a mainboard TMUX1208 U63/U64 channel; now the card TMUX1208'
    return finish(c,blocks,JS,[J],os.environ.get('PAPER',paper),notes,replaced,pad=pad,extra=xb)


def hso5():
    notes=['HSO-5 CARD, card type 0x0012. 5 protected high-side outputs (TPS1HTC30-class, baseline AUX1-AUX5 circuit); a 2nd instance replaces AUX6-AUX10.',
      "Self-contained: own SN74LVC541A enable buffer (outputs only enabled while OUT_EN_N is low), own TMUX1208 current-sense mux to ANA_OUT, own BAT54C clamps, own MCP23S17 behind IOFF slot buffers.",
      'Pass 1: REQ/DIAG_EN/MUX_A 47k pull-downs (boot-safe), OUT_EN_N pull-up on +3V3_ID, 100 nF/100 V at every VS + 2.2 uF bulk, ILIM 33.2k (2.41/3.01/3.61 A), R_SNS 910 + 4.7k into the clamp. CARD_FAULT_N pulled up on the backplane only. Pass 2: slot MISO 33R, INTA_B pull-up, 0603 pull-ups.',
      'MCP23S17: GPA0-4 OUT1-5_REQ, GPA5 DIAG_EN, GPA6-7 SLOT_ID0/1; GPB0-4 OUT1-5_RB_N, GPB5-7 MUX_A0-2. SLOT_ID2/IDP not read (no spare GPIO): slot identity also comes from the I2C mux channel.',
      'Baseline names: OUTk = AUXk. Net changes: net_changes.csv.']
    return hso_card('hso5','HSO-5 card (type 0x0012): 5 high-side outputs',0x12,'HSO_A',['AUX1','AUX2','AUX3','AUX4','AUX5'],[],
        ('D130',{'1':None,'2':'OUT1_SNSM','3':'+3V3_SLOT'}),['SLOT_ID0','SLOT_ID1'],notes)

def brk4():
    notes=['BRK-4 CARD, card type 0x0013. 4 breaker coil outputs: OUT1 GCB close, OUT2 GCB open, OUT3 MCB close, OUT4 MCB open.',
      "Self-contained: own SN74LVC541A enable buffer (OUT_EN_N gated), own TMUX1208 current-sense mux to ANA_OUT, own MCP23S17 behind IOFF slot buffers. Shared clamps D128/D130 split: their GLOW/AUX1 halves are left NC here.",
      'Pass 1: REQ/DIAG_EN/MUX_A 47k pull-downs (boot-safe), OUT_EN_N pull-up on +3V3_ID, 100 nF/100 V at every VS + 2.2 uF bulk, ILIM 33.2k: 2.41/3.01/3.61 A. Pass 2 MAJ-6: every GCB/MCB trip/close/motor-operator coil is switched through an external interposing relay (relay coil <= 2.4 A incl. pull-in); never drive a breaker coil directly. R_SNS 910 + 4.7k into the clamp. Slot MISO 33R, INTA_B pull-up.',
      'MCP23S17: GPA0-3 OUT1-4_REQ, GPA4 DIAG_EN, GPA5-7 SLOT_ID0-2; GPB0-3 OUT1-4_RB_N, GPB4-6 MUX_A0-2, GPB7 SLOT_IDP.',
      'Baseline names: OUT1 GCB_CL, OUT2 GCB_OP, OUT3 MCB_CL, OUT4 MCB_OP. Net changes: net_changes.csv.']
    return hso_card('brk4','BRK-4 card (type 0x0013): 4 breaker coil outputs',0x13,'BRK4',['GCB_CL','GCB_OP','MCB_CL','MCB_OP'],[],None,
        ['SLOT_ID0','SLOT_ID1','SLOT_ID2','SLOT_IDP'],notes,
        pad=2,nc_pins=[('D128','1','clamp half for GLOW_SNSM stays on the mainboard (new BAT54C there)'),('D130','2','clamp half for AUX1_SNSM moves to the HSO-5 card')])

if __name__=='__main__':
    which=sys.argv[1:] or ['di8','ai4','hso5','brk4']
    for w in which: globals()[w]()
