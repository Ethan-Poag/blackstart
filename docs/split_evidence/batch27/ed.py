import re,uuid,math,sys
sys.path.insert(0,'/workspace/review/fix27'); sys.path.insert(0,'/workspace/review/split/exec')
from sx import block_at
from geo import blocks,libsyms,libpins,instances,at_point
U=lambda: str(uuid.uuid4())
PAPER={'A0':(1189,841),'A1':(841,594),'A2':(594,420),'A3':(420,297),'A4':(297,210)}
HIDE='(effects (font (size 1.27 1.27)) hide)'
class Sheet:
    def __init__(s,path):
        s.path=path; s.s=open(path).read(); s.new=[]
        m=re.search(r'\(instances \(project "([^"]+)" \(path "([^"]+)"',s.s); s.project,s.ipath=m.group(1),m.group(2)
        s.paper=PAPER[re.search(r'\(paper "([^"]+)"',s.s).group(1)]
    def save(s):
        txt=s.s
        if s.new:
            k=txt.rfind('(sheet_instances')
            if k<0: k=txt.rstrip().rfind(')')
            txt=txt[:k]+'\n'.join(s.new)+'\n'+txt[k:]
        open(s.path,'w').write(txt)
    def sym(s,ref,unit=None):
        out=[]
        for i,e,b in blocks(s.s,'(symbol (lib_id'):
            if re.search(r'\(property "Reference" "%s"'%re.escape(ref),b):
                if unit is None or re.search(r'\(unit %d\)'%unit,b[:300]): out.append((i,e,b))
        assert out,ref; return out
    def _rep(s,i,e,nb): s.s=s.s[:i]+nb+s.s[e:]
    def set_prop(s,ref,key,val):
        for i,e,b in reversed(s.sym(ref)):
            m=re.search(r'\(property "%s" "((?:[^"\\]|\\.)*)"'%re.escape(key),b)
            if m: nb=b[:m.start(1)]+val.replace('"','\\"')+b[m.end(1):]
            else:
                at=re.search(r'\(at ([-\d.]+) ([-\d.]+)',b).groups()
                k=b.find('(pin ') if '(pin ' in b else b.find('(instances')
                nb=b[:k]+f'(property "{key}" "{val}" (at {at[0]} {at[1]} 0) {HIDE})'+b[k:]
            s._rep(i,e,nb)
    def set_dnp(s,ref,dnp=True):
        for i,e,b in reversed(s.sym(ref)):
            nb=re.sub(r'\(dnp (yes|no)\)',f'(dnp {"yes" if dnp else "no"})',b,1); s._rep(i,e,nb)
    def label_at(s,pt):
        return [h for h in at_point(s.s,pt) if h[0] in('(label','(global_label')]
    def relabel(s,pt,old,new):
        h=[x for x in s.label_at(pt) if f'"{old}"' in x[3]]; assert len(h)==1,(pt,old,h)
        i,e=h[0][1],h[0][2]; b=s.s[i:e]; s._rep(i,e,b.replace(f'"{old}"',f'"{new}"',1))
    def remove_nc(s,pt):
        h=[x for x in at_point(s.s,pt) if x[0]=='(no_connect']; assert len(h)==1
        s._rep(h[0][1],h[0][2],'')
    def label(s,name,pt,ang=0,glob=False):
        just={0:'left bottom',90:'left bottom',180:'right bottom',270:'right bottom'}[ang] if not glob else {0:'left',90:'left',180:'right',270:'right'}[ang]
        if glob: s.new.append(f'(global_label "{name}" (shape passive) (at {pt[0]:.2f} {pt[1]:.2f} {ang}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {just})) (uuid "{U()}") (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {pt[0]:.2f} {pt[1]:.2f} 0) {HIDE}))')
        else: s.new.append(f'(label "{name}" (at {pt[0]:.2f} {pt[1]:.2f} {ang}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {just})) (uuid "{U()}"))')
    def wire(s,a,b): s.new.append(f'(wire (pts (xy {a[0]:.2f} {a[1]:.2f}) (xy {b[0]:.2f} {b[1]:.2f})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    def text(s,t,x,y):
        import textwrap; t='\\n'.join(textwrap.wrap(t,80))
        s.new.append(f'(text "{t}" (exclude_from_sim no) (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{U()}"))')
    def place(s,lib,ref,val,x,y,fp='',props=(),conn=None,dnp=False,rot=0,inbom=True,pwrref=None):
        L,_=libsyms(s.s); assert lib in L,lib
        pl={n:v[0] for n,v in libpins(L[lib]).items()}
        hide=ref.startswith('#')
        body=[f'(symbol (lib_id "{lib}") (at {x:.2f} {y:.2f} {rot}) (unit 1) (exclude_from_sim no) (in_bom {"yes" if inbom else "no"}) (on_board yes) (dnp {"yes" if dnp else "no"}) (uuid "{U()}")',
              f'(property "Reference" "{ref}" (at {x+2.54:.2f} {y-1.27:.2f} 0) {HIDE if hide else "(effects (font (size 1.27 1.27)))"})',
              f'(property "Value" "{val}" (at {x+2.54:.2f} {y+1.27:.2f} 0) (effects (font (size 1.27 1.27))))',
              f'(property "Footprint" "{fp}" (at {x:.2f} {y:.2f} 0) {HIDE})',f'(property "Datasheet" "~" (at {x:.2f} {y:.2f} 0) {HIDE})']
        for k,v in props: body.append(f'(property "{k}" "{v}" (at {x:.2f} {y:.2f} 0) {HIDE})')
        for n in pl: body.append(f'(pin "{n}" (uuid "{U()}"))')
        body.append(f'(instances (project "{s.project}" (path "{s.ipath}" (reference "{ref}") (unit 1))))')
        body.append(')'); s.new.append(''.join(body))
        a=math.radians(rot); pts={}
        for n,(px,py,u) in pl.items():
            rx=px*math.cos(a)-py*math.sin(a); ry=px*math.sin(a)+py*math.cos(a)
            pts[n]=(round(x+rx,2),round(y-ry,2))
        # pin directions from lib
        dirs={}
        for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)',L[lib]):
            pb=L[lib][m.start():block_at(L[lib],m.start())]; num=re.search(r'\(number "([^"]+)"',pb).group(1)
            ang=math.radians(float(m.group(3))+rot); dirs[num]=(-math.cos(ang),math.sin(ang))  # outward in sheet coords (y down)
        if conn:
            for n,c in conn.items():
                p=pts[n]; d=dirs[n]; end=(round(p[0]+2.54*d[0],2),round(p[1]+2.54*d[1],2))
                kind,name=c
                if kind=='nc': s.new.append(f'(no_connect (at {p[0]:.2f} {p[1]:.2f}) (uuid "{U()}"))'); continue
                s.wire(p,end)
                ang={(1,0):0,(-1,0):180,(0,-1):90,(0,1):270}[(round(d[0]),round(d[1]))]
                if kind=='label': s.label(name,end,ang)
                elif kind=='global': s.label(name,end,ang,glob=True)
                elif kind=='pwr':
                    plib,pval=name
                    prot={'power:GND':{(0,1):0,(0,-1):180,(1,0):90,(-1,0):270}}.get(plib,{(0,-1):0,(0,1):180,(1,0):270,(-1,0):90})[(round(d[0]),round(d[1]))]
                    s.place(plib,pwrref.pop(0),pval,end[0],end[1],rot=prot,inbom=True)
        return pts
def free(sh,w,h,step=5.08,start=None):
    pts=[(float(a),float(b)) for a,b in re.findall(r'\(at ([-\d.]+) ([-\d.]+)',sh.s)]+[(float(a),float(b)) for a,b in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)',sh.s)]
    W,H=sh.paper
    y=25.4
    while y+h<H-15:
        x=25.4
        while x+w<W-15:
            if not any(x-10<=px<=x+w+10 and y-10<=py<=y+h+10 for px,py in pts): return (round(x/1.27)*1.27,round(y/1.27)*1.27)
            x+=step
        y+=step
    raise Exception('no space')
