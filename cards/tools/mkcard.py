"""Generate ONE flat, label-based KiCad 9 schematic page for a card from baseline circuitry.
Every moved part keeps lib symbol, Value, Footprint, MPN, LCSC, Manufacturer; it is renumbered per card and
carries field 'BaselineRef'. Every pin gets a 2.54 mm stub + local net label (GND uses power:GND symbols)."""
import numpy as np,textwrap,os,sys,uuid,math,re,json,collections,copy
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from srcdb import load,short,ROOT,find,find1,Sym
from sexp import dump,parse
G=1.27
def U(): return str(uuid.uuid4())
def snap(v): return round(v/G)*G
def q(s): return '"'+str(s).replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')+'"'
def f(v): return ('%.4f'%v).rstrip('0').rstrip('.')
PAPER={'A3':(420,297),'A2':(594,420),'A4':(297,210),'A1':(841,594),'A0':(1189,841)}
CARDLIB=parse(open(os.path.join(ROOT,'cards','lib','cards.kicad_sym')).read())[0]
CARDSYMS={e[1]:e for e in find(CARDLIB,'symbol')}

def lib_pins(lsym,unit):
    out=[]
    for sub in find(lsym,'symbol'):
        m=re.match(r'.*_(\d+)_(\d+)$',sub[1]); u=int(m.group(1)); st=int(m.group(2))
        if u not in (0,unit) or st not in (0,1): continue
        for p in find(sub,'pin'):
            at=find1(p,'at'); out.append(dict(num=find1(p,'number')[1],name=find1(p,'name')[1],
                x=float(at[1]),y=float(at[2]),ang=float(at[3]),len=float(find1(p,'length')[1]),typ=str(p[1]),
                hide=any(isinstance(e,list) and e[0]=='hide' for e in p) or 'hide' in [str(e) for e in p]))
    return out
def body(lsym,unit,pins):
    xs=[p['x'] for p in pins]; ys=[-p['y'] for p in pins]
    for sub in find(lsym,'symbol'):
        m=re.match(r'.*_(\d+)_(\d+)$',sub[1]); u=int(m.group(1))
        if u not in (0,unit): continue
        for r in find(sub,'rectangle'):
            for k in ('start','end'):
                e=find1(r,k); xs.append(float(e[1])); ys.append(-float(e[2]))
        for pl in find(sub,'polyline'):
            for xy in find(find1(pl,'pts'),'xy'): xs.append(float(xy[1])); ys.append(-float(xy[2]))
        for c in find(sub,'circle'):
            ce=find1(c,'center'); ra=float(find1(c,'radius')[1]); xs+=[float(ce[1])-ra,float(ce[1])+ra]; ys+=[-float(ce[2])-ra,-float(ce[2])+ra]
    if not xs: xs=[0]; ys=[0]
    return min(xs),min(ys),max(xs),max(ys)

class Card:
    def __init__(s,name,title,paper='A3'):
        s.name=name; s.title=title; s.paper=paper; s.parts=[]; s.libs={}; s.notes=[]; s.netmap={}
        s.comps,s.nets,s.pinnet,s.inst,s.srclibs=load()
        s.count=collections.Counter(); s.refmap={}
    def netname(s,full):
        n=short(full)
        if full.startswith('unconnected-'): return None
        if full in s.netmap: return s.netmap[full]
        if n.startswith('Net-('):
            n=re.sub(r'[^A-Za-z0-9_+]+','_',n[5:-1].replace('{slash}','_')).strip('_')
        return n
    def newref(s,prefix):
        s.count[prefix]+=1; return f'{prefix}{s.count[prefix]}'
    def symfix(s,lib_id,props):
        """Pass 3 N13: baseline parts drawn with stand-in stock symbols get the cards: symbol of the fitted part (identical pinout)."""
        v=props.get('Value','')
        new={'Transistor_FET:DMN6075S':{'IRLML0100':'cards:IRLML0100','AO3400A':'cards:AO3400A'}.get(v),'74xGxx:74AUP1G74':'cards:74LVC1G74'}.get(lib_id)
        if not new: return lib_id,None
        if 'Note' in props: props['Note']=props['Note'].replace('Stock symbol 74AUP1G74 used (no 74LVC1G74 in KiCad 9 libs)','Symbol cards:74LVC1G74 (Pass 3 N13)')
        L=copy.deepcopy(CARDSYMS[new.split(':')[1]]); L[1]=new; return new,L
    def move(s,refs,rename=None):
        for r in refs:
            insts=s.inst[r]; assert insts,r
            prefix=re.match(r'[A-Z]+',r).group(0)
            nr=(rename or {}).get(r) or s.newref(prefix); s.refmap[r]=nr
            for i in sorted(insts,key=lambda x:x['unit']):
                props=dict(i['props']); props['Reference']=nr; props['BaselineRef']=r
                lib,lsym=s.symfix(i['lib_id'],props)
                if lsym is None: lsym=s.srclibs[lib]
                else: assert sorted(x['num'] for x in lib_pins(lsym,i['unit']))==sorted(x['num'] for x in lib_pins(s.srclibs[i['lib_id']],i['unit'])),lib
                s.libs[lib]=lsym
                pins=lib_pins(lsym,i['unit'])
                pn={p['num']:s.netname(s.pinnet.get((r,p['num']),'unconnected-')) for p in pins}
                s.parts.append(dict(ref=nr,lib_id=lib,unit=i['unit'],props=props,pins=pins,pn=pn,dnp=i['dnp'],lsym=lsym))
    def add(s,lib_id,ref,value,pn,props=None,unit=1,lsym=None):
        lsym=lsym or s.srclibs.get(lib_id) or CARDSYMS[lib_id.split(':')[1]]
        if lsym[1]!=lib_id:  # card lib symbols are stored with bare names; embed under full id
            lsym=copy.deepcopy(lsym); lsym[1]=lib_id
        s.libs[lib_id]=lsym; pins=lib_pins(lsym,unit)
        P={'Reference':ref,'Value':value,'Footprint':'','Datasheet':'','Description':''}; P.update(props or {})
        s.parts.append(dict(ref=ref,lib_id=lib_id,unit=unit,props=P,pins=pins,pn={p['num']:pn.get(p['num']) for p in pins},dnp=False,lsym=lsym))
    # ---------------- layout + write ----------------
    notew=118; notewrap=88; pack='height'
    def write(s,outdir,order_key=None):
        W,H=PAPER[s.paper]; x0,y0=13.97,15.24; xmax=W-13; ymax=H-13; tb=(W-120,H-45)
        items=[]
        for p in s.parts:
            bx=body(p['lsym'],p['unit'],p['pins'])
            lab=max([len(p['pn'][q_['num']] or '') for q_ in p['pins']]+[0])*0.68+2
            items.append((p,bx,lab))
        if order_key: items.sort(key=lambda t:order_key(t[0]))
        if s.pack=='height': items.sort(key=lambda t:-(t[1][3]-t[1][1]+2*t[2]*(not any(pp['ang']%360 in (0,180) for pp in t[0]['pins']))))
        # skyline packing; bottom-right block reserved for title block + notes + PWR_FLAGs
        nnote=sum(len(textwrap.wrap(t,s.notewrap)) for t in s.notes)+1
        s.res_x=W-12-s.notew; s.res_y=snap(H-45-nnote*2.2-14)
        R=1.27; ncol=int((xmax-x0)/R); nrow=int((ymax-y0)/R); occ=np.zeros((nrow,ncol),dtype=np.int8)
        rc=int((s.res_x-x0)/R); rr=int((s.res_y-y0)/R); occ[rr:,rc:]=1; placed=[]; s.overflow=False; s.over=[]
        for p,(bx0,by0,bx1,by1),lab in items:
            angs={p_['ang']%360 for p_ in p['pins']}
            hasL,hasR,hasU,hasD=(0 in angs),(180 in angs),(270 in angs),(90 in angs)
            p['side']=angs<= {90,270}
            tl=(max(len(p['props']['Reference']),len(p['props'].get('Value','')))*0.8+1.5) if p['side'] else 0
            w=(bx1-bx0)+(lab+2.54 if hasL else 1.5)+(lab+2.54 if hasR else 1.5)+tl
            if not p['side']: w=max(w,max(len(p['props'].get('Value','')),len(p['props']['Reference']))*0.85+2)
            h=(by1-by0)+(lab+2.54 if hasU else (1.5 if p['side'] else 3.2))+(lab+2.54 if hasD else (1.5 if p['side'] else 3.2))
            n=int(math.ceil(w/R))+1; m=int(math.ceil(h/R))+1
            S=np.zeros((occ.shape[0]+1,occ.shape[1]+1),dtype=np.int32); S[1:,1:]=occ.cumsum(0).cumsum(1)
            win=S[m:,n:]-S[:-m,n:]-S[m:,:-n]+S[:-m,:-n]
            free=np.argwhere(win==0)
            if len(free)==0:
                s.overflow=True; s.over.append(p['ref']); r0,c0=occ.shape[0]-m,0
            else:
                r0,c0=free[0]
            occ[r0:r0+m,c0:c0+n]=1; s.area=getattr(s,'area',0)+m*n*R*R
            top=y0+r0*R; cx=x0+c0*R
            X=snap(cx+(lab+2.54 if hasL else 1.5)-bx0); Y=snap(top+(lab+2.54 if hasU else (1.5 if p['side'] else 3.2))-by0)
            p['X'],p['Y']=X,Y; p['bx']=(bx0,by0,bx1,by1); placed.append(p)
        out=[]
        out.append('(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")')
        root=U(); out.append(f'(uuid "{root}")'); out.append(f'(paper "{s.paper}")')
        out.append('(title_block (title %s) (date "2026-11-23") (rev "M-mod P2") (company "Project Blackstart") (comment 1 %s) (comment 2 %s))'%(
            q(s.title),q('cards/tools/mkcard.py from tag baseline-2026-11-23-locked; BaselineRef = old ref'),q('One flat page; nets by local label; GND by power symbol.')))
        out.append('(lib_symbols '+' '.join(dump(L) for L in s.libs.values())+' '+dump(s.srclibs['power:GND'])+' '+dump(s.srclibs['power:PWR_FLAG'])+')')
        flags=set(); proj=s.name
        def pwr(lib,x,y,ang,val):
            ref='#PWR%03d'%(s.count['#PWR']+1) if 'GND' in lib else '#FLG%03d'%(s.count['#FLG']+1)
            s.count['#PWR' if 'GND' in lib else '#FLG']+=1
            out.append(f'(symbol (lib_id "{lib}") (at {f(x)} {f(y)} {ang}) (unit 1) (exclude_from_sim no) (in_bom no) (on_board yes) (dnp no) (uuid "{U()}") '
                f'(property "Reference" "{ref}" (at {f(x)} {f(y+3)} 0) (effects (font (size 1.27 1.27)) hide)) '
                f'(property "Value" {q(val)} (at {f(x)} {f(y+3.5)} 0) (effects (font (size 1.0 1.0)){" hide" if ang in (90,270) else ""})) '
                f'(property "Footprint" "" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) hide)) '
                f'(pin "1" (uuid "{U()}")) (instances (project "{proj}" (path "/{root}" (reference "{ref}") (unit 1)))))')
        nets_used=collections.Counter()
        for p in placed:
            X,Y=p['X'],p['Y']; pr=p['props']
            proplines=[]
            for i,(k,v) in enumerate(pr.items()):
                vis=k in('Reference','Value')
                bx=body(p['lsym'],p['unit'],p['pins'])
                if p['side']:
                    px_=X+bx[2]+0.8; py=Y-0.6 if k=='Reference' else Y+1.9
                    proplines.append(f'(property {q(k)} {q(v)} (at {f(px_)} {f(py)} 0) (effects (font (size 1.27 1.27)) (justify left){"" if vis else " hide"}))')
                else:
                    py=Y+bx[1]-1.4 if k=='Reference' else Y+bx[3]+1.6
                    proplines.append(f'(property {q(k)} {q(v)} (at {f(X)} {f(py)} 0) (effects (font (size 1.27 1.27)){"" if vis else " hide"}))')
            out.append(f'(symbol (lib_id {q(p["lib_id"])}) (at {f(X)} {f(Y)} 0) (unit {p["unit"]}) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp {"yes" if p["dnp"] else "no"}) (uuid "{U()}") '
                +' '.join(proplines)+' '+' '.join(f'(pin {q(pp["num"])} (uuid "{U()}"))' for pp in p['pins'])
                +f' (instances (project "{proj}" (path "/{root}" (reference {q(p["ref"])}) (unit {p["unit"]})))))')
            seen=set()
            for pp in p['pins']:
                if (pp['x'],pp['y']) in seen: continue   # stacked pins share one point
                seen.add((pp['x'],pp['y']))
                px,py=X+pp['x'],Y-pp['y']; o=(pp['ang']+180)%360
                dx,dy=round(math.cos(math.radians(o))),-round(math.sin(math.radians(o)))
                net=p['pn'][pp['num']]
                if net is None:
                    out.append(f'(no_connect (at {f(px)} {f(py)}) (uuid "{U()}"))'); continue
                ex,ey=px+dx*2.54,py+dy*2.54
                out.append(f'(wire (pts (xy {f(px)} {f(py)}) (xy {f(ex)} {f(ey)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
                nets_used[net]+=1
                if net=='GND':
                    pwr('power:GND',ex,ey,{(0,1):0,(0,-1):180,(1,0):90,(-1,0):270}[(dx,dy)],'GND'); continue
                ang={(1,0):0,(-1,0):180,(0,-1):90,(0,1):270}[(dx,dy)]
                just='left' if ang in (0,90) else 'right'
                out.append(f'(label {q(net)} (at {f(ex)} {f(ey)} {ang}) (fields_autoplaced yes) (effects (font (size 1.0 1.0)) (justify {just} bottom)) (uuid "{U()}"))')
        # PWR_FLAGs: every net with a power_in pin and no power_out pin (rails enter through the slot connector)
        ptypes=collections.defaultdict(set)
        for p in placed:
            for pp in p['pins']:
                n_=p['pn'][pp['num']]
                if n_: ptypes[n_].add(pp['typ'])
        s.power_nets=sorted(n_ for n_,t in ptypes.items() if 'power_in' in t and 'power_out' not in t)
        fx=snap(s.res_x+2); fy=snap(H-45-6)
        for i,net in enumerate(sorted(s.power_nets)):
            x=snap(fx+(i%6)*17.78); y=snap(fy-(i//6)*10.16)
            pwr('power:PWR_FLAG',x,y,0,'PWR_FLAG')
            if net=='GND':
                pwr('power:GND',x,y,90,'GND')   # value hidden (shares point with the flag)
            else:
                out.append(f'(label {q(net)} (at {f(x)} {f(y)} 0) (fields_autoplaced yes) (effects (font (size 1.0 1.0)) (justify left bottom)) (uuid "{U()}"))')
        ny=H-110 if s.paper!='A4' else H-80
        for i,t in enumerate(s.notes):
            pass
        if s.notes:
            txt=chr(10).join(l for t in s.notes for l in textwrap.wrap(t,s.notewrap))
            out.append(f'(text {q(txt)} (exclude_from_sim no) (at {f(s.res_x+2)} {f(s.res_y+2)} 0) (effects (font (size 1.4 1.4)) (justify left top)) (uuid "{U()}"))')
        out.append('(sheet_instances (path "/" (page "1")))'); out.append('(embedded_fonts no))')
        os.makedirs(outdir,exist_ok=True)
        open(os.path.join(outdir,s.name+'.kicad_sch'),'w').write('\n'.join(out)+'\n')
        pro={"meta":{"filename":s.name+".kicad_pro","version":3},"schematic":{"legacy_lib_dir":"","legacy_lib_list":[]},"sheets":[[root,"Root"]],"boards":[],
             "libraries":{"pinned_footprint_libs":[],"pinned_symbol_libs":[]},"erc":{"rule_severities":{}},"text_variables":{}}
        open(os.path.join(outdir,s.name+'.kicad_pro'),'w').write(json.dumps(pro,indent=2))
        open(os.path.join(outdir,'sym-lib-table'),'w').write('(sym_lib_table\n  (version 7)\n  (lib (name "genctl")(type "KiCad")(uri "${KIPRJMOD}/../../genctl.kicad_sym")(options "")(descr ""))\n  (lib (name "cards")(type "KiCad")(uri "${KIPRJMOD}/../lib/cards.kicad_sym")(options "")(descr "card/slot symbols"))\n)\n')
        open(os.path.join(outdir,'fp-lib-table'),'w').write('(fp_lib_table\n  (version 7)\n  (lib (name "genctl")(type "KiCad")(uri "${KIPRJMOD}/../../genctl.pretty")(options "")(descr ""))\n  (lib (name "cards")(type "KiCad")(uri "${KIPRJMOD}/../lib/cards.pretty")(options "")(descr "card/slot footprints (VERIFY)"))\n)\n')
        json.dump(s.refmap,open(os.path.join(outdir,'refmap.json'),'w'),indent=1)
        return nets_used
