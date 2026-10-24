"""genctl KiCad schematic generator framework."""
import uuid, math, os, re, csv, glob, collections
from sexp import parse, dump, find, find1, Sym, q
import kilib

PROJ='genctl'
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G=1.27
WIRED=True  # clustered placement + real wires (tools/layout.py); False = legacy label-only shelf layout
def snap(v): return round(v/G)*G
def U(): return str(uuid.uuid4())

# ---------------- LCSC lookup from the BOMs ----------------
LCSC={}
for f in ['power_bom','outputs_bom','inputs_bom','comms_bom','other_bom','ac_metering_bom_jlc']:
    p='/workspace/genctl/%s.csv'%f
    for r in csv.DictReader(open(p,encoding='utf-8',errors='replace')):
        pn=(r.get('part number') or '').strip(); l=(r.get('LCSC part') or '').strip()
        if pn and re.match(r'^C\d+$',l): LCSC.setdefault(pn.upper(),l)
def lcsc_for(mpn):
    if not mpn: return ''
    k=mpn.upper()
    if k in LCSC: return LCSC[k]
    for kk,v in LCSC.items():
        if k in kk or kk in k: return v
    return ''

# ---------------- custom symbol library ----------------
CUSTOM={}
def mkpin(num,name,x,y,ang,ln=2.54,typ='passive',hide=False):
    p=[Sym('pin'),Sym(typ),Sym('line'),[Sym('at'),x,y,ang],[Sym('length'),ln]]
    if hide: p.append([Sym('hide'),Sym('yes')])
    p+= [[Sym('name'),name,[Sym('effects'),[Sym('font'),[Sym('size'),1.27,1.27]]]],
         [Sym('number'),str(num),[Sym('effects'),[Sym('font'),[Sym('size'),1.27,1.27]]]]]
    return p
def prop(k,v,x=0,y=0,hide=False,ang=0):
    e=[Sym('effects'),[Sym('font'),[Sym('size'),1.27,1.27]]]
    if hide: e.append([Sym('hide'),Sym('yes')])
    return [Sym('property'),k,v,[Sym('at'),x,y,ang],e]
TYPEMAP={'W':'power_in','w':'power_out','I':'input','O':'output','B':'bidirectional','C':'open_collector','N':'no_connect','P':'passive','T':'tri_state','E':'open_emitter','U':'unspecified'}
def ic(name, left, right, top=(), bottom=(), ref='U', desc='', fp='', ds='', lcsc='', mpn='', mfr='', types=None):
    """left/right: list of (num,name) or None (spacer). types: {pin name or number: code} (W power_in, w power_out, I in, O out,
    B bidir, C open collector/drain, N no_connect, P passive). Unlisted pins default to passive."""
    types=types or {}
    def ty(num,nm):
        c=types.get(str(num), types.get(nm, 'P'))
        return TYPEMAP.get(c,c)
    cw=0.85
    lw=max([len(e[1]) for e in left if e] or [0]); rw=max([len(e[1]) for e in right if e] or [0])
    tw=max(len(top),len(bottom))*2.54+5.08
    w=max((lw+rw)*G*cw+5.08, tw, 10.16)
    hw=math.ceil(w/2/2.54)*2.54
    n=max(len(left),len(right))
    ht=n*2.54; hh=math.ceil((ht/2)/2.54)*2.54+ (2.54 if (top or bottom) else 0)
    ytop=hh; 
    pins=[]
    def col(lst,x,ang):
        y=snap((len(lst)-1)*2.54/2); y=math.floor(y/2.54)*2.54
        for e in lst:
            if e: pins.append(mkpin(e[0],e[1],x,round(y,2),ang,typ=ty(e[0],e[1])))
            y-=2.54
    col(left,-hw-2.54,0); col(right,hw+2.54,180)
    yb=-(math.ceil(((len(left) if len(left)>len(right) else len(right))-1)*2.54/2/2.54)*2.54) - 2.54
    yt=math.floor((max(len(left),len(right))-1)*2.54/2/2.54)*2.54 + 2.54
    if top:
        yt+=2.54
        x=-(len(top)-1)*2.54/2; x=math.floor(x/2.54)*2.54
        for e in top:
            if e: pins.append(mkpin(e[0],e[1],round(x,2),yt+2.54,270,typ=ty(e[0],e[1])))
            x+=2.54
    if bottom:
        yb-=2.54
        x=-(len(bottom)-1)*2.54/2; x=math.floor(x/2.54)*2.54
        for e in bottom:
            if e: pins.append(mkpin(e[0],e[1],round(x,2),yb-2.54,90,typ=ty(e[0],e[1])))
            x+=2.54
    body=[Sym('symbol'),name+'_0_1',[Sym('rectangle'),[Sym('start'),-hw,yt],[Sym('end'),hw,yb],
          [Sym('stroke'),[Sym('width'),0.254],[Sym('type'),Sym('default')]],[Sym('fill'),[Sym('type'),Sym('background')]]]]
    s=[Sym('symbol'),name,[Sym('exclude_from_sim'),Sym('no')],[Sym('in_bom'),Sym('yes')],[Sym('on_board'),Sym('yes')],
       prop('Reference',ref,-hw,yt+1.27+(2.54 if top else 0)),prop('Value',name,-hw,yb-1.27-(2.54 if bottom else 0)),
       prop('Footprint',fp,0,0,True),prop('Datasheet',ds,0,0,True),prop('Description',desc,0,0,True),
       prop('LCSC',lcsc,0,0,True),prop('MPN',mpn or name,0,0,True),prop('Manufacturer',mfr,0,0,True),
       body,[Sym('symbol'),name+'_1_1']+pins]
    CUSTOM[name]=s
    return name

def write_custom_lib():
    lib=[Sym('kicad_symbol_lib'),[Sym('version'),20231120],[Sym('generator'),'genctl_gen'],[Sym('generator_version'),'1.0']]
    lib+=list(CUSTOM.values())
    open(os.path.join(OUT,'genctl.kicad_sym'),'w').write((dump(lib)+'\n').replace('(hide yes)','hide'))

# ---------------- netlist model ----------------
POWER_SYMS={'GND':'power:GND','+3V3':'power:+3V3','+5V':'power:+5V','+12V':'power:+12V'}
REFC=collections.Counter()
ALLPARTS=[]
NCLOG=[]
class Part:
    def __init__(s,sheet,libid,value,conns,prefix=None,lcsc=None,mpn='',fp='',mfr='',dnp=False,note='',ds=''):
        s.sheet=sheet; s.libid=libid; s.value=value; s.dnp=dnp; s.note=note
        s.sym=kilib.get_symbol(libid,CUSTOM)
        s.pins=kilib.pins(s.sym)
        props={p[1]:p for p in find(s.sym,'property')}
        if prefix is None: prefix=props['Reference'][2].rstrip('?')
        s.power = libid.startswith('power:')
        if s.power:
            REFC['#PWR' if prefix!='#FLG' else '#FLG']+=1
            s.ref='%s%04d'%(prefix, REFC['#PWR' if prefix!='#FLG' else '#FLG'])
        else:
            REFC[prefix]+=1; s.ref='%s%d'%(prefix,REFC[prefix])
        s.fp=fp or (props['Footprint'][2] if 'Footprint' in props else '')
        s.ds=ds or (props['Datasheet'][2] if 'Datasheet' in props else '')
        s.mpn=mpn
        if lcsc is None: lcsc=lcsc_for(mpn) if mpn else (props['LCSC'][2] if 'LCSC' in props else '')
        s.lcsc=lcsc; s.mfr=mfr
        s.net={}  # pin num -> net (None = NC)
        names=collections.defaultdict(list)
        for p in s.pins: names[p['name']].append(p['num'])
        nums={p['num'] for p in s.pins}
        for k,v in conns.items():
            k=str(k)
            if k in nums: s.net[k]=v
            elif k in names:
                for n in names[k]: s.net[n]=v
            else: raise KeyError('%s %s: no pin %s (have %s)'%(libid,s.ref,k,sorted(names)))
        for p in s.pins:
            if p['num'] not in s.net:
                s.net[p['num']]=None
                if not s.power: NCLOG.append('%s/%s %s pin %s (%s)'%(sheet.name,s.ref,s.value,p['num'],p['name']))
        sheet.parts.append(s); ALLPARTS.append(s)

class Sheet:
    def __init__(s,name,title,file,notes=''):
        s.name=name; s.title=title; s.file=file; s.parts=[]; s.notes=notes; s.uuid=U()
    def p(s,libid,value,conns,**kw): return Part(s,libid,value,conns,**kw)
    def R(s,val,a,b,mpn='',lcsc=None,pkg='0603',**kw):
        fp={'0402':'Resistor_SMD:R_0402_1005Metric','0603':'Resistor_SMD:R_0603_1608Metric','0805':'Resistor_SMD:R_0805_2012Metric',
            '1206':'Resistor_SMD:R_1206_3216Metric','2512':'Resistor_SMD:R_2512_6332Metric','2010':'Resistor_SMD:R_2010_5025Metric'}.get(pkg,pkg)
        if lcsc is None: lcsc=RLCSC.get((val,pkg),'')
        return Part(s,'Device:R',val,{'1':a,'2':b},mpn=mpn,lcsc=lcsc,fp=fp,**kw)
    def C(s,val,a,b,mpn='',lcsc=None,pkg='0603',pol=False,**kw):
        fp={'0402':'Capacitor_SMD:C_0402_1005Metric','0603':'Capacitor_SMD:C_0603_1608Metric','0805':'Capacitor_SMD:C_0805_2012Metric',
            '1206':'Capacitor_SMD:C_1206_3216Metric','1210':'Capacitor_SMD:C_1210_3225Metric'}.get(pkg,pkg)
        if lcsc is None: lcsc=CLCSC.get((val,pkg),'')
        return Part(s,'Device:C_Polarized' if pol else 'Device:C',val,{'1':a,'2':b},mpn=mpn,lcsc=lcsc,fp=fp,**kw)
    def LED(s,col,a,k,lcsc=''):
        return Part(s,'Device:LED',col,{'A':a,'K':k},lcsc=lcsc,fp='LED_SMD:LED_0603_1608Metric')

RLCSC={('10k','0603'):'C25804',('100k','0603'):'C25803',('1k','0603'):'C21190',('2.2k','0603'):'C4190',('47k','0603'):'C25819',
 ('33k','0603'):'C4216',('68k','0603'):'C23231',('1M','0603'):'C22935',('200k','0603'):'C25811',('5.1k','0603'):'C23186',('0R','0603'):'C21189',
 ('12k','0603'):'C22790',('22R','0603'):'C23345',('33R','0603'):'C23140',('4.7k','0603'):'C23162',('120R','0603'):'C22787',('27k','0603'):'C22967',
 ('22.1k','0603'):'C23059',('75k','0603'):'C23242',('140k','0603'):'C22806',('191k','0603'):'C22932',('45.3k','0603'):'C23058',('210k','0603'):'C22952',('49.9k','0603'):'C23184',('18k','0603'):'C25810',('24.9R','0603'):'C23111'}
CLCSC={('100n','0603'):'C14663',('100n','0805'):'C28233',('100n','0402'):'C1525',('1u','0805'):'C28323',('10u','0805'):'C15850',('22u','1206'):'C12891',
 ('10u','1210'):'C138687',('4.7u','1206'):'C29823',('1n','0603'):'C1588',('4.7n','0603'):'C1621',('22p','0402'):'C1555',('1u','0603'):'C15849',('2.2u','0603'):'C23630',('33n','0603'):'C21117'}

# ---------------- writer ----------------
def lab_len(t, glob):
    return len(t)*G*0.72 + (3.2 if glob else 0.8)

def build(sheets, root_title='genctl generator controller'):
    root_uuid=U()
    # net -> sheets
    netsheets=collections.defaultdict(set); nettypes=collections.defaultdict(list)
    for sh in sheets:
        for pt in sh.parts:
            for p in pt.pins:
                n=pt.net[p['num']]
                if n: netsheets[n].add(sh.name); nettypes[n].append(p['type'] if (not pt.power and n not in POWER_SYMS) else 'power_in')
    # auto PWR_FLAG
    flagged=[]
    for n,types in list(nettypes.items()):
        if 'power_in' in types and 'power_out' not in types:
            sh=[s for s in sheets if s.name in netsheets[n]][0]
            Part(sh,'power:PWR_FLAG','PWR_FLAG',{'1':n},prefix='#FLG'); flagged.append(n)
    netsheets=collections.defaultdict(set)
    for sh in sheets:
        for pt in sh.parts:
            for p in pt.pins:
                n=pt.net[p['num']]
                if n: netsheets[n].add(sh.name)
    import layout
    for sh in sheets: (layout.write_sheet if WIRED else write_sheet)(sh, root_uuid, netsheets)
    if WIRED: print('route stats',layout.STATS)
    write_root(sheets, root_uuid, root_title)
    write_custom_lib()
    return flagged, netsheets

PAPERS=[('A3',420,297),('A2',594,420),('A1',841,594),('A0',1189,841)]

def unit_geom(pt,unit):
    """pins of this unit (incl unit 0 common), with outward vector, and bbox incl labels."""
    ps=[]
    vis=[(p['x'],p['y']) for p in pt.pins if not p['hidden'] and p['unit'] in (0,unit)]
    for p in pt.pins:
        if p['unit'] not in (0,unit): continue
        if p['hidden'] and (p['x'],p['y']) in vis: continue
        ps.append(p)
    xs=[0];ys=[0]
    for p in ps:
        o=math.radians((p['ang']+180)%360)
        dx,dy=round(math.cos(o)),-round(math.sin(o))
        x,y=p['x'],-p['y']
        n=pt.net[p['num']]
        L=0 if n is None else 2.54+ (6 if n in POWER_SYMS else lab_len(n,True))
        # also body: pin length inward
        xs+= [x, x+dx*L, x-dx*p['len']*1.0]; ys+=[y, y+dy*L, y-dy*p['len']]
    # include symbol body graphics roughly via rectangles
    for sub in find(pt.sym,'symbol'):
        for r in find(sub,'rectangle'):
            st=find1(r,'start'); en=find1(r,'end'); xs+=[float(st[1]),float(en[1])]; ys+=[-float(st[2]),-float(en[2])]
    return ps,(min(xs)-2.54,min(ys)-3.81,max(xs)+2.54,max(ys)+3.81)

def write_sheet(sh, root_uuid, netsheets):
    items=[]  # (pt,unit,ps,bbox)
    for pt in sh.parts:
        us=kilib.units(pt.sym)
        for u in us:
            ps,bb=unit_geom(pt,u)
            items.append((pt,u,ps,bb))
    # choose paper
    for pname,PW,PH in PAPERS:
        placed=shelf(items,PW-30,PH-45)
        if placed: break
    else:
        pname,PW,PH='User',1500,1100
        placed=shelf(items,PW-30,PH-45,force=True)
    libs={}; body=[]; pwrn=0
    path='/%s/%s'%(root_uuid,sh.uuid)
    for (pt,u,ps,bb),(ox,oy) in zip(items,placed):
        X=snap(15+ox-bb[0]); Y=snap(40+oy-bb[1])
        libs[pt.libid]=pt.sym
        body.append(sym_inst(pt,u,X,Y,path))
        for p in ps:
            n=pt.net[p['num']]
            px,py=round(X+p['x'],2),round(Y-p['y'],2)
            if n is None:
                body.append('(no_connect (at %s %s) (uuid "%s"))'%(f(px),f(py),U())); continue
            o=(p['ang']+180)%360
            dx,dy=round(math.cos(math.radians(o))),-round(math.sin(math.radians(o)))
            ex,ey=round(px+dx*2.54,2),round(py+dy*2.54,2)
            body.append('(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))'%(f(px),f(py),f(ex),f(ey),U()))
            if n in POWER_SYMS:
                ps_=Part.__new__(Part)
                lid=POWER_SYMS[n]; psym=kilib.get_symbol(lid); libs[lid]=psym
                pp=kilib.pins(psym)[0]
                rot=(o-pp['ang'])%360
                REFC['#PWR']+=1; ref='#PWR%04d'%REFC['#PWR']
                body.append(power_inst(lid,n,ref,ex,ey,rot,path))
            else:
                glob=len(netsheets[n])>1
                just='left' if o in (0,90) else 'right'
                if glob:
                    body.append('(global_label %s (shape passive) (at %s %s %d) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify %s)) (uuid "%s") (property "Intersheetrefs" "${INTERSHEET_REFS}" (at %s %s 0) (effects (font (size 1.27 1.27)) (hide yes))))'%(q(n),f(ex),f(ey),o,just,U(),f(ex),f(ey)))
                else:
                    body.append('(label %s (at %s %s %d) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid "%s"))'%(q(n),f(ex),f(ey),o,just,U()))
    if sh.notes:
        body.append('(text %s (exclude_from_sim no) (at 15 12 0) (effects (font (size 1.6 1.6)) (justify left top)) (uuid "%s"))'%(q(sh.notes),U()))
    txt=['(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")',
         '(uuid "%s")'%sh.uuid, '(paper "%s"%s)'%(pname,'' if pname!='User' else ' %d %d'%(PW,PH)),
         '(title_block (title %s) (company "genctl") (rev "A-draft") (comment 1 "Generated by tools/gen.py - see DESIGN_NOTES.md"))'%q(sh.title),
         '(lib_symbols']
    for lid,s in libs.items():
        s2=list(s); s2[1]=lid
        txt.append(dump(s2,1))
    txt.append(')')
    txt+=body
    txt.append(')')
    open(os.path.join(OUT,sh.file),'w').write(('\n'.join(txt)+'\n').replace('(hide yes)','hide'))

def f(v): return dump(float(v))

def shelf(items,W,H,force=False):
    x=y=0; rowh=0; out=[]
    for pt,u,ps,bb in items:
        w=bb[2]-bb[0]; h=bb[3]-bb[1]
        if x+w>W and x>0:
            y+=rowh+2.54; x=0; rowh=0
        out.append((x,y)); x+=w+2.54; rowh=max(rowh,h)
    if y+rowh>H and not force: return None
    return out

def fields_xml(pt,X,Y,u):
    props={p[1]:p for p in find(pt.sym,'property')}
    def at(k):
        if k in props:
            a=find1(props[k],'at'); return X+float(a[1]),Y-float(a[2]),(int(float(a[3])) if len(a)>3 else 0)
        return X,Y,0
    out=[]
    vals=[('Reference',pt.ref,False),('Value',pt.value,False),('Footprint',pt.fp,True),('Datasheet',pt.ds,True),
          ('Description',(props['Description'][2] if 'Description' in props else ''),True)]
    if not pt.power:
        vals+=[('LCSC',pt.lcsc,True),('MPN',pt.mpn,True),('Manufacturer',pt.mfr,True)]
        if pt.note: vals.append(('Note',pt.note,True))
    for k,v,h in vals:
        x,y,a=at(k)
        out.append('(property %s %s (at %s %s %d) (effects (font (size 1.27 1.27))%s))'%(q(k),q(v),f(snap(x) if k not in('Reference','Value') else x),f(y),a,' (hide yes)' if h else ''))
    return out

def sym_inst(pt,u,X,Y,path):
    s=['(symbol (lib_id %s) (at %s %s 0) (unit %d) (exclude_from_sim no) (in_bom %s) (on_board yes) (dnp %s) (uuid "%s")'%(
        q(pt.libid),f(X),f(Y),u,'no' if pt.power else 'yes','yes' if pt.dnp else 'no',U())]
    s+=fields_xml(pt,X,Y,u)
    for p in pt.pins:
        if p['unit'] in (0,u): s.append('(pin %s (uuid "%s"))'%(q(p['num']),U()))
    s.append('(instances (project %s (path %s (reference %s) (unit %d))))'%(q(PROJ),q(path),q(pt.ref),u))
    s.append(')')
    return '\n'.join(s)

def power_inst(lid,net,ref,x,y,rot,path):
    psym=kilib.get_symbol(lid)
    props={p[1]:p for p in find(psym,'property')}
    va=find1(props['Value'],'at')
    # value text position: rotate offset
    vx,vy=float(va[1]),-float(va[2]); r=math.radians(rot)
    tx=x+vx*math.cos(r)+vy*math.sin(r); ty=y-vx*math.sin(r)+vy*math.cos(r)
    return ('(symbol (lib_id %s) (at %s %s %d) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "%s")'
            '(property "Reference" %s (at %s %s 0) (effects (font (size 1.27 1.27)) (hide yes)))'
            '(property "Value" %s (at %s %s 0) (effects (font (size 1.27 1.27))))'
            '(property "Footprint" "" (at %s %s 0) (effects (font (size 1.27 1.27)) (hide yes)))'
            '(property "Datasheet" "" (at %s %s 0) (effects (font (size 1.27 1.27)) (hide yes)))'
            '(pin "1" (uuid "%s"))'
            '(instances (project %s (path %s (reference %s) (unit 1)))))')%(q(lid),f(x),f(y),rot,U(),q(ref),f(x),f(y),q(net),f(tx),f(ty),f(x),f(y),f(x),f(y),U(),q(PROJ),q(path),q(ref))

def write_root(sheets,root_uuid,title):
    body=[]; x=20; y=40; n=2
    for i,sh in enumerate(sheets):
        w,h=60,25
        body.append('(sheet (at %s %s) (size %d %d) (fields_autoplaced yes) (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0000)) (uuid "%s")'
            '(property "Sheetname" %s (at %s %s 0) (effects (font (size 1.27 1.27)) (justify left bottom)))'
            '(property "Sheetfile" %s (at %s %s 0) (effects (font (size 1.27 1.27)) (justify left top)))'
            '(instances (project %s (path "/%s" (page "%d")))))'%(f(x),f(y),w,h,sh.uuid,q(sh.title),f(x),f(y-0.7),q(sh.file),f(x),f(y+h+0.6),q(PROJ),root_uuid,n))
        n+=1; x+=80
        if x>300: x=20; y+=45
    txt=['(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")','(uuid "%s")'%root_uuid,'(paper "A3")',
         '(title_block (title %s) (company "genctl") (rev "A-draft") (comment 1 "Hierarchical root - inter-sheet connectivity via global labels"))'%q(title),
         '(lib_symbols)']+body+['(text %s (exclude_from_sim no) (at 20 150 0) (effects (font (size 2 2)) (justify left top)) (uuid "%s"))'%(q('All inter-sheet nets are global labels (names identical across sheets).\nRails +3V3/+5V/+12V/GND use power symbols. See DESIGN_NOTES.md for assumptions/open questions.'),U()),
         '(sheet_instances (path "/" (page "1")))',')']
    open(os.path.join(OUT,PROJ+'.kicad_sch'),'w').write('\n'.join(txt)+'\n')

def write_project():
    open(os.path.join(OUT,'sym-lib-table'),'w').write('(sym_lib_table\n  (version 7)\n  (lib (name "genctl")(type "KiCad")(uri "${KIPRJMOD}/genctl.kicad_sym")(options "")(descr "genctl project symbols"))\n)\n')
    import json
    pro={"meta":{"filename":"genctl.kicad_pro","version":1},"schematic":{"legacy_lib_dir":"","legacy_lib_list":[]},
         "sheets":[],"boards":[],"libraries":{"pinned_footprint_libs":[],"pinned_symbol_libs":[]},
         "erc":{"rule_severities":{}},"text_variables":{}}
    open(os.path.join(OUT,'genctl.kicad_pro'),'w').write(json.dumps(pro,indent=2))
