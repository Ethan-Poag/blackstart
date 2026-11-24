"""Readable one-sheet card schematics: functional blocks, real wires inside a block.

Layout model (all geometry on the 1.27 mm grid, integer units):
- A block is a framed group of "clusters". A cluster is one anchor (an IC unit, transistor or connector)
  plus every 2-pin part reachable from its pins through non-rail nets, drawn as wired trees:
  a pin's net is a straight wire; shunt parts (to GND, rails or other nets) hang perpendicular from it;
  one series part continues the wire; the far side of each part recurses.
- Pins of one side that need trees fan out as a staircase (no wire crossings).
- Labels are used only where a net also appears elsewhere (other cluster, block or the slot connector),
  for rails, and for slot-connector pins. GND is a power symbol.
"""
import math,collections,os,re,json,textwrap
import numpy as np
from mkcard import body,U,q,f,G,PAPER,dump

FS=float(os.environ.get('FS','1.27'))   # text size mm (labels, refs, values)
CW=1.05*FS/1.27/G   # char width in grid units (measured: 20 chars = 23.5 mm at 1.27 mm)
TH=1.3*FS/G
GLOBALS=set()   # nets drawn as global labels (wider: flag outline)
def tw(s): return len(s)*CW+0.6+(2.4 if s in GLOBALS else 0)

DIRS={(1,0):0,(0,-1):90,(-1,0):180,(0,1):270}   # direction -> KiCad angle (label text direction)
def rot(v,th):  # rotate a screen vector CCW (visually) by th degrees
    c=round(math.cos(math.radians(th))); s=round(math.sin(math.radians(th)))
    return (v[0]*c+v[1]*s, -v[0]*s+v[1]*c)
def add(a,b): return (a[0]+b[0],a[1]+b[1])
def mul(a,k): return (a[0]*k,a[1]*k)

class BBox:
    def __init__(s): s.b=None; s.r=[]
    def _pt(s,x,y):
        if s.b is None: s.b=[x,y,x,y]
        else: s.b=[min(s.b[0],x),min(s.b[1],y),max(s.b[2],x),max(s.b[3],y)]
    def pt(s,x,y): s._pt(x,y); s.r.append((x,y,x,y))
    def box(s,x0,y0,x1,y1):
        s._pt(x0,y0); s._pt(x1,y1); s.r.append((min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1)))
    def merge(s,o,dx=0,dy=0):
        if o.b:
            s._pt(o.b[0]+dx,o.b[1]+dy); s._pt(o.b[2]+dx,o.b[3]+dy)
            s.r+= [(a+dx,b+dy,c+dx,d+dy) for a,b,c,d in o.r]
    def proj(s,d):  # interval of the box projected on unit axis d
        if not s.b: return (0,0)
        if d[0]: v=(s.b[0]*d[0],s.b[2]*d[0])
        else: v=(s.b[1]*d[1],s.b[3]*d[1])
        return (min(v),max(v))

class Piece:
    def __init__(s): s.prims=[]; s.bb=BBox()
    def merge(s,o,off):
        for p in o.prims: s.prims.append(shift(p,off))
        s.bb.merge(o.bb,*off)
def shift(p,o):
    k=p[0]
    if k=='wire': return ('wire',add(p[1],o),add(p[2],o))
    if k in('junc','nc'): return (k,add(p[1],o))
    if k=='label': return ('label',p[1],add(p[2],o),p[3])
    if k=='pwr': return ('pwr',p[1],add(p[2],o),p[3])
    if k=='sym': return ('sym',p[1],add(p[2],o),p[3],[(a,add(b,o),c) for a,b,c in p[4]])
    if k=='text': return ('text',add(p[1],o),p[2])
    raise ValueError(k)

def pwr_prim(P,name,pt,d):
    """rail/GND power symbol at pt, graphic pointing d; text after the arrow (GND text hidden)."""
    P.prims.append(('pwr',name,pt,d)); e=add(pt,mul(d,2.6)); P.bb.box(*sorted2(pt,e)); P.bb.box(*sorted2(add(pt,mul((abs(d[1]),abs(d[0])),-1.2)),add(e,mul((abs(d[1]),abs(d[0])),1.2))))
    if name!='GND':
        w=tw(name)
        if d[0]==0: y=e[1]+d[1]*(0.4+TH/2); P.bb.box(pt[0]-w/2,y-TH/2,pt[0]+w/2,y+TH/2)
        else: P.bb.box(*sorted2((e[0],e[1]-TH/2),(e[0]+d[0]*(w+0.4),e[1]+TH/2)))

class Drawer:
    def __init__(s,card,rails,blocks,paper='A3',notes=None,pins_order=None):
        s.c=card; s.rails=set(rails); s.blocks=blocks; s.paper=paper; s.notes=notes or []
        s.parts={(p['ref'],p['unit']):p for p in card.parts}
        # node bookkeeping: node key = (ref,unit,x,y) lib position (stacked pins share a node)
        s.netnodes=collections.defaultdict(set)
        s.pinfo={}
        for k,p in s.parts.items():
            p['grid']=[]
            for pp in p['pins']:
                n=p['pn'][pp['num']]
                nk=(p['ref'],p['unit'],pp['x'],pp['y'])
                if n: s.netnodes[n].add(nk)
        s.two={k for k,p in s.parts.items() if len({(pp['x'],pp['y']) for pp in p['pins']})==2 and not p['lib_id'].startswith('Connector')}
        s.claimed=set(); s.labels_only=set(); s.force_label=set()
    # ---------- helpers ----------
    def pins_of(s,k):
        p=s.parts[k]; seen={}; out=[]
        for pp in p['pins']:
            key=(pp['x'],pp['y'])
            if key in seen: continue
            seen[key]=1; out.append(pp)
        return out
    def is_rail(s,n): return n in s.rails
    def other(s,k,pp):
        pins=s.pins_of(k); o=[x for x in pins if (x['x'],x['y'])!=(pp['x'],pp['y'])][0]; return o
    def node(s,k,pp): return (k[0],k[1],pp['x'],pp['y'])
    def two_on(s,net,allowed):
        out=[]
        for (ref,unit,x,y) in s.netnodes.get(net,()):
            k=(ref,unit)
            if k in s.two and k not in s.claimed and k in allowed:
                pp=[a for a in s.pins_of(k) if (a['x'],a['y'])==(x,y)][0]; out.append((k,pp))
        return sorted(out,key=lambda t:(t[0][0][0],int(re.sub(r'\D','',t[0][0]) or 0)))
    def reach(s,net,allowed,seen=None):
        seen=seen or set(); n=0
        for k,pp in s.two_on(net,allowed):
            if k in seen: continue
            seen.add(k); n+=1; o=s.other(k,pp); on=s.parts[k]['pn'][o['num']]
            if on and not s.is_rail(on): n+=s.reach(on,allowed,seen)
        return n
    def place2(s,k,pa,P,d):
        """2-pin part k with pin pa at point P, other pin in direction d. returns (prim, far point, body bbox)."""
        p=s.parts[k]; pb=s.other(k,pa)
        va=(pa['x']/G,-pa['y']/G); vb=(pb['x']/G,-pb['y']/G); v=(vb[0]-va[0],vb[1]-va[1])
        L=abs(v[0])+abs(v[1])
        for th in (0,90,180,270):
            r=rot(v,th)
            if (round(r[0]/L),round(r[1]/L))==d: break
        else: raise ValueError('rot')
        ra=rot(va,th); O=(P[0]-ra[0],P[1]-ra[1]); far=add(P,mul(d,round(L)))
        bx=body(p['lsym'],p['unit'],p['pins']); corners=[rot((bx[0]/G,bx[1]/G),th),rot((bx[2]/G,bx[3]/G),th)]
        bb=BBox(); [bb.pt(O[0]+c[0],O[1]+c[1]) for c in corners]
        return p,th,O,far,bb
    def fields2(s,p,bb,d,side):
        """ref+value text block next to a 2-pin part body, on unit side `side` (perpendicular to the part axis)."""
        ref=p['ref']; val=p['props'].get('Value',''); w=max(tw(ref),tw(val)); fb=BBox()
        x0,y0,x1,y1=bb.b; cx=(x0+x1)/2; cy=(y0+y1)/2
        if side[0]:      # text left/right of a vertical part
            if side[0]>0: tx=x1+0.8; just='left'
            else: tx=x0-0.8; just='right'
            F=[('Reference',(tx,cy-0.5),just),('Value',(tx,cy+0.5+TH*0.7),just)]
            xa,xb=(tx,tx+w) if side[0]>0 else (tx-w,tx)
            fb.box(xa,cy-0.5-TH,xb,cy+0.5+TH)
        else:            # text above/below a horizontal part
            ty=(y0-0.6) if side[1]<0 else (y1+0.6+TH)
            F=[('Reference',(cx,ty-TH),'center'),('Value',(cx,ty),'center')]
            fb.box(cx-w/2,ty-2*TH,cx+w/2,ty+0.2)
        return F,fb
    # ---------- recursive net tree ----------
    def tree(s,net,d,h,attach,allowed):
        """Wire tree for `net` starting at origin going d; parts hang to +h. attach = node key already at origin."""
        P=Piece(); covered={attach}
        cands=s.two_on(net,allowed)
        for k,_ in cands: s.claimed.add(k)
        ser=None
        if not s.is_rail(net):
            best=-1
            for k,pp in cands:
                on=s.parts[k]['pn'][s.other(k,pp)['num']]
                if on and not s.is_rail(on) and on!=net:
                    r=s.reach(on,allowed)
                    if r>best: best=r; ser=(k,pp)
        taps=[c for c in cands if c!=ser]
        for k,pp in cands: covered.add(s.node(k,pp))
        need_label=bool(s.netnodes[net]-covered) or net in s.force_label
        t=1; pts=[0]
        items=[]
        if need_label and ser: items.append(('lab',None))
        items+= [('tap',c) for c in taps]
        for kind,c in items:
            sub=Piece()
            if kind=='lab':
                sub.prims.append(('wire',(0,0),mul(h,2))); sub.prims.append(('label',net,mul(h,2),h))
                sub.bb.pt(0,0); e=mul(h,2); w=tw(net)
                ln=add(e,mul(h,w)); sub.bb.pt(*ln); sub.bb.pt(*add(e,mul(d,-TH))); sub.bb.pt(*add(ln,mul(d,TH*0.3)))
            else:
                k,pp=c; p,th,O,far,bb=s.place2(k,pp,(0,0),h)
                F,fb=s.fields2(p,bb,h,d)
                sub.prims.append(('sym',p,O,th,F)); sub.bb.merge(bb); sub.bb.merge(fb)
                o=s.other(k,pp); on=p['pn'][o['num']]
                if on is None: sub.prims.append(('nc',far)); sub.bb.pt(*far)
                elif s.is_rail(on): pwr_prim(sub,on,far,h)
                elif on==net or s.node(k,o) in covered:
                    sub.prims.append(('label',on,far,h)); w=tw(on); e=add(far,mul(h,w)); sub.bb.pt(*e); sub.bb.pt(*add(far,mul(d,-TH))); sub.bb.pt(*add(e,mul(d,0.5)))
                else:
                    st=s.tree(on,h,d,s.node(k,o),allowed); sub.merge(st,far)
            a,b=sub.bb.proj(d)
            pos=max(t+1-a, 2) if pts==[0] else t+1-a
            pos=int(math.ceil(pos))
            P.merge(sub,mul(d,pos)); pts.append(pos); t=pos+b
        end=pts[-1]
        if ser:
            k,pp=ser; sp=max(int(math.ceil(t+1)),end+2) if len(pts)>1 else 2
            p,th,O,far,bb=s.place2(k,pp,mul(d,sp),d)
            F,fb=s.fields2(p,bb,d,mul(h,-1))
            P.prims.append(('sym',p,O,th,F)); P.bb.merge(bb); P.bb.merge(fb)
            pts.append(sp)
            o=s.other(k,pp); on=p['pn'][o['num']]
            st=s.tree(on,d,h,s.node(k,o),allowed); P.merge(st,far)
        elif need_label:
            e=max(end,1)+1; e=int(math.ceil(max(e,t+0.5))) if len(pts)>1 else 2
            P.prims.append(('label',net,mul(d,e),d)); pts.append(e)
            w=tw(net); P.bb.pt(*mul(d,e)); P.bb.pt(*add(mul(d,e+w),mul(h,-TH))); P.bb.pt(*add(mul(d,e+w),mul(h,0.4)))
        pts=sorted(set(pts))
        for i in range(len(pts)-1):
            P.prims.append(('wire',mul(d,pts[i]),mul(d,pts[i+1])))
        for x in pts[1:-1]: P.prims.append(('junc',mul(d,x)))
        P.bb.pt(0,0); P.bb.pt(*mul(d,pts[-1]))
        return P
    # ---------- anchors ----------
    def cluster(s,k,allowed):
        p=s.parts[k]; s.claimed.add(k); C=Piece(); lonly=k[0] in s.labels_only
        bx=body(p['lsym'],p['unit'],p['pins']); bb=BBox(); bb.box(bx[0]/G,bx[1]/G,bx[2]/G,bx[3]/G)
        ref=p['ref']; val=p['props'].get('Value','')
        cx=(bb.b[0]+bb.b[2])/2; cy=(bb.b[1]+bb.b[3])/2
        used=set()
        for pp in s.pins_of(k):
            o=(pp['ang']+180)%360; used.add((round(math.cos(math.radians(o))),-round(math.sin(math.radians(o)))))
        w=max(tw(ref),tw(val))
        if (0,1) not in used and (0,-1) in used:     # bottom free: ref + value below
            F=[('Reference',(cx,bb.b[3]+0.8+TH),'center'),('Value',(cx,bb.b[3]+0.8+2*TH),'center')]
            C.bb.box(cx-w/2,bb.b[3],cx+w/2,bb.b[3]+0.8+2*TH+0.3)
        elif (0,-1) not in used:                     # top free: ref + value above
            F=[('Reference',(cx,bb.b[1]-0.8-TH),'center'),('Value',(cx,bb.b[1]-0.8),'center')]
            C.bb.box(cx-w/2,bb.b[1]-0.8-2*TH,cx+w/2,bb.b[1])
        elif (1,0) not in used:
            F=[('Reference',(bb.b[2]+0.8,cy-0.3),'left'),('Value',(bb.b[2]+0.8,cy+TH),'left')]
            C.bb.box(bb.b[2],cy-0.3-TH,bb.b[2]+0.8+w,cy+TH+0.3)
        elif (-1,0) not in used:
            F=[('Reference',(bb.b[0]-0.8,cy-0.3),'right'),('Value',(bb.b[0]-0.8,cy+TH),'right')]
            C.bb.box(bb.b[0]-0.8-w,cy-0.3-TH,bb.b[0],cy+TH+0.3)
        else:
            F=[('Reference',(cx,bb.b[1]-0.8),'center'),('Value',(cx,bb.b[3]+0.8+TH),'center')]
            C.bb.box(cx-w/2,bb.b[1]-0.8-TH,cx+w/2,bb.b[3]+0.8+TH)
        C.prims.append(('sym',p,(0,0),0,F)); C.bb.merge(bb)
        sides=collections.defaultdict(list)
        for pp in s.pins_of(k):
            o=(pp['ang']+180)%360; dv=(round(math.cos(math.radians(o))),-round(math.sin(math.radians(o))))
            end=(round(pp['x']/G),round(-pp['y']/G)); sides[dv].append((pp,end))
        for dv,lst in sides.items():
            a=(0,1) if dv[0] else (1,0)
            lst.sort(key=lambda t:t[1][0]*a[0]+t[1][1]*a[1])
            simple=[]; trees=[]
            for pp,end in lst:
                n=p['pn'][pp['num']]
                if n and not lonly and not s.is_rail(n) and s.two_on(n,allowed): trees.append((pp,end,n))
                else: simple.append((pp,end,n))
            # simple pins: stub + label / GND, consecutive same-net pins joined into one
            base=2; i=0
            while i<len(simple):
                pp,end,n=simple[i]; j=i
                while (j+1<len(simple) and simple[j+1][2]==n and n is not None and
                       abs((simple[j+1][1][0]-simple[j][1][0])+(simple[j+1][1][1]-simple[j][1][1]))<=2): j+=1
                grp=simple[i:j+1]; i=j+1
                if n is None:
                    for pp_,e_,_ in grp: C.prims.append(('nc',e_)); C.bb.pt(*e_)
                    continue
                stubs=[]
                for pp_,e_,_ in grp:
                    se=add(e_,mul(dv,2)); C.prims.append(('wire',e_,se)); stubs.append(se); C.bb.pt(*se)
                if len(stubs)>1:
                    for s0,s1 in zip(stubs,stubs[1:]): C.prims.append(('wire',s0,s1))   # split at every T (kicad-cli needs it)
                    for st in stubs[1:-1]: C.prims.append(('junc',st))
                tip=stubs[len(stubs)//2] if len(stubs)>1 else stubs[0]
                if len(stubs)>1:
                    tip2=add(tip,mul(dv,1)); C.prims.append(('wire',tip,tip2))
                    if len(stubs)%2==1 and len(stubs)>2: C.prims.append(('junc',tip))
                    if len(stubs)==2: pass
                    tip=tip2
                if s.is_rail(n):
                    pwr_prim(C,n,tip,dv); base=max(base,(3 if len(stubs)>1 else 2)+3+(tw(n)+1 if dv[1]==0 and n!='GND' else 0))
                else:
                    C.prims.append(('label',n,tip,dv)); w=tw(n)
                    ext=add(tip,mul(dv,w)); C.bb.pt(*ext); C.bb.pt(*add(ext,mul(a,-TH)))
                    base=max(base,(3 if len(stubs)>1 else 2)+w+1)
            if len(simple)>0 and any(g[2] for g in simple): pass
            # tree pins: staircase (upper pins jog further out, rows stacked along a: no crossings)
            m=len(trees); base=int(math.ceil(base)) if simple else 0
            prev_hi=None
            for idx,(pp,end,n) in enumerate(trees):
                T=s.tree(n,dv,a,s.node(k,pp),allowed)
                lo,hi=T.bb.proj(a)
                u=(base+2*(m-1-idx)+2) if (simple or m>1) else 0
                sA=end[0]*a[0]+end[1]*a[1]
                sp=sA if prev_hi is None else max(sA,int(math.ceil(prev_hi+2-lo)))
                jog=add(end,mul(dv,u)); corner=add(jog,mul(a,sp-sA))
                if u>0: C.prims.append(('wire',end,jog))
                if corner!=jog: C.prims.append(('wire',jog,corner))
                C.merge(T,corner); C.bb.pt(*end); C.bb.pt(*jog)
                prev_hi=sp+hi
        return C

def sorted2(a,b): return (min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1]))

def mask_of(P,pad=1):  # pad on all sides; clusters keep >= 2 units apart
    x0,y0,x1,y1=P.bb.b; w=int(math.ceil(x1-x0))+2*pad+1; h=int(math.ceil(y1-y0))+2*pad+1
    M=np.zeros((h,w),dtype=np.float32)
    rr=list(P.bb.r)+[(min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])) for k,a,b,*_ in [p for p in P.prims if p[0]=='wire']]
    for p in P.prims:   # label text bodies (bb.pt only records their end points, so packing could slide another cluster over the text)
        if p[0]=='label':
            _,n,(x,y),(dx,dy)=p; L=tw(n); ex,ey=x+dx*L,y+dy*L
            rr.append((min(x,ex)-(0.7 if dy else 0),min(y,ey)-(0.7 if dx else 0),max(x,ex)+(0.7 if dy else 0),max(y,ey)+(0.7 if dx else 0)))
    for a,b,c,d in rr:
        M[max(0,int(math.floor(b-y0))):int(math.ceil(d-y0))+2*pad+1, max(0,int(math.floor(a-x0))):int(math.ceil(c-x0))+2*pad+1]=1
    return M
def packm(masks,W,H):
    from scipy.signal import correlate
    occ=np.zeros((int(H),int(W)),dtype=np.float32); out=[]
    for M in masks:
        h,w=M.shape
        if h>occ.shape[0] or w>occ.shape[1]: out.append(None); continue
        C=correlate(occ,M,mode='valid',method='fft')
        fr=np.argwhere(C<0.5)
        if len(fr)==0: out.append(None); continue
        r,c=fr[0]; occ[r:r+h,c:c+w]=np.maximum(occ[r:r+h,c:c+w],M); out.append((c,r))
    return out
def pack(rects,W,H,reserved=(),colmajor=False):
    """rects: list of (w,h) in units -> list of (x,y) top-left, row-major first fit on an occupancy grid."""
    occ=np.zeros((int(H)+1,int(W)+1),dtype=np.int8); out=[]
    for (x0,y0,x1,y1) in reserved: occ[max(0,int(y0)):int(y1)+1,max(0,int(x0)):int(x1)+1]=1
    for w,h in rects:
        n=int(math.ceil(w))+1; m=int(math.ceil(h))+1
        if n>occ.shape[1] or m>occ.shape[0]: out.append(None); continue
        S=np.zeros((occ.shape[0]+1,occ.shape[1]+1),dtype=np.int32); S[1:,1:]=occ.cumsum(0).cumsum(1)
        win=S[m:,n:]-S[:-m,n:]-S[m:,:-n]+S[:-m,:-n]; fr=np.argwhere(win==0)
        if len(fr)==0: out.append(None); continue
        if colmajor: fr=fr[np.lexsort((fr[:,0],fr[:,1]))]
        r,c=fr[0]; occ[r:r+m,c:c+n]=1; out.append((c,r))
    return out

def emit_sym(out,p,O,th,F,proj,root):
    X,Y=O[0]*G,O[1]*G; props=p['props']; lines=[]
    pos={k:(xy,j) for k,xy,j in F}
    for k,v in props.items():
        if k in pos:
            (x,y),j=pos[k]
            if th in (90,180) and j!='center': j={'left':'right','right':'left'}[j]   # KiCad mirrors justify for these rotations
            fa=90 if th in (90,270) else 0                                           # keeps the text horizontal on the page
            jj='' if j=='center' else f' (justify {j})'
            lines.append(f'(property {q(k)} {q(v)} (at {f(x*G)} {f(y*G)} {fa}) (effects (font (size {FS} {FS})){jj}))')
        else:
            lines.append(f'(property {q(k)} {q(v)} (at {f(X)} {f(Y)} 0) (effects (font (size 1.27 1.27)) hide))')
    out.append(f'(symbol (lib_id {q(p["lib_id"])}) (at {f(X)} {f(Y)} {th}) (unit {p["unit"]}) (exclude_from_sim no) (in_bom {"no" if p.get("in_bom") is False else "yes"}) (on_board yes) (dnp {"yes" if p["dnp"] else "no"}) (uuid "{U()}") '
        +' '.join(lines)+' '+' '.join(f'(pin {q(pp["num"])} (uuid "{U()}"))' for pp in p['pins'])
        +f' (instances (project "{proj}" (path "/{root}" (reference {q(p["ref"])}) (unit {p["unit"]})))))')

def run(D,outdir,title):
    c=D.c; W,H=PAPER[D.paper]; Wu=int((W-27)/G); Hu=int((H-27)/G)
    # PWR_FLAGs for rails entering from the slot
    types=collections.defaultdict(set)
    for p in c.parts:
        for pp in p['pins']:
            n=p['pn'][pp['num']]
            if n: types[n].add(pp['typ'])
    flags=sorted(n for n in getattr(D,'flagnets',()) if n in types) if getattr(D,'noflags',False) else sorted(n for n,t in types.items() if ('power_in' in t or (n in D.rails and n!='GND')) and 'power_out' not in t and 'output' not in t)
    D.force_label={n for n in flags if n not in D.rails}|set(getattr(D,'glabels',()))
    blocks=[]
    for bt,keys in D.blocks:
        cl=[]
        for k in keys:
            if k in D.claimed: continue
            cl.append(D.cluster(k,set(D.parts)))
        blocks.append([bt,cl])
    left=[k for k in D.parts if k not in D.claimed]
    for k in list(left):
        t=getattr(D,'extra',{}).get(k[0])
        if t:
            for B in blocks:
                if B[0]==t: B[1].append(D.cluster(k,set(D.parts))); left.remove(k)
    if left:
        cl=[]
        for k in sorted(left):
            if k in D.claimed: continue
            cl.append(D.cluster(k,set(D.parts)))
        blocks.append(['Other',cl])
    D.left=left
    fl=[]
    for n in flags:
        P=Piece(); P.prims.append(('flag',(0,0))); P.prims.append(('wire',(0,0),(0,2)))
        if n in D.rails: pwr_prim(P,n,(0,2),(0,1))
        else: P.prims.append(('label',n,(0,2),(0,1))); P.bb.box(-1,2,1,2+tw(n))
        P.bb.box(-2,-3,2,2)
        fl.append(P)
    blocks.append([getattr(D,'flagtitle','PWR_FLAG (rails enter via the slot)'),fl])
    # lay out clusters inside each block
    laid=[]
    for bt,cl in blocks:
        if not cl: continue
        sizes=[(P.bb.b[2]-P.bb.b[0]+2,P.bb.b[3]-P.bb.b[1]+2) for P in cl]
        masks=[mask_of(P,getattr(D,'pad',1)) for P in cl]
        area=sum(M.sum() for M in masks); best=None; alts=[]
        wmin=math.ceil(max(max(M.shape[1] for M in masks)+1,tw(bt)*1.6+2))
        for bw in sorted(set([wmin]+[int(wmin+k*(Wu-wmin)/10) for k in range(11)])):
            if bw>Wu: continue
            order=sorted(range(len(masks)),key=lambda i:-masks[i].sum())
            pos_=packm([masks[i] for i in order],bw,600)
            if not all(x is not None for x in pos_): continue
            pos=[None]*len(masks)
            for i,pp_ in zip(order,pos_): pos[i]=pp_
            uw=max(x+M.shape[1] for (x,y),M in zip(pos,masks)); uh=max(y+M.shape[0] for (x,y),M in zip(pos,masks))
            score=(uw+3)*(uh+6)*(1+0.1*max(uw/uh,uh/uw))
            alts.append((score,pos,uw,uh))
            if best is None or score<best[0]: best=(score,pos,uw,uh)
        _,pos,used_w,used_h=best
        alts=sorted(alts,key=lambda a:a[0])[:6]
        laid.append(dict(title=bt,cl=cl,pos=pos,w=used_w+3,h=used_h+6,alts=[(a[1],a[2]+3,a[3]+6) for a in alts]))
    notes=[l for t in D.notes for l in textwrap.wrap(t,78)]
    if notes:
        P=Piece(); P.prims.append(('text',(0,0),notes)); P.bb.box(0,0,max(len(l) for l in notes)*CW*1.0,len(notes)*1.75*FS/G)
        laid.append(dict(title='Notes',cl=[P],pos=[(0,0)],w=P.bb.b[2]+5,h=P.bb.b[3]+8))
    res=[(Wu-int(112/G),Hu-int(34/G),Wu,Hu)]
    best=None
    for key in (lambda i:-laid[i]['w']*laid[i]['h'],lambda i:-laid[i]['h'],lambda i:-laid[i]['w'],lambda i:-max(laid[i]['w'],laid[i]['h'])):
        order=sorted(range(len(laid)),key=key)
        for cm in (False,True):
            bp=pack([(laid[i]['w'],laid[i]['h']) for i in order],Wu,Hu,res,cm)
            nover=sum(1 for x in bp if x is None)
            if best is None or nover<best[0]: best=(nover,order,bp)
    import random; rnd=random.Random(1)
    tries=0
    pick=None
    while best[0] and tries<1500:
        tries+=1; order=list(range(len(laid))); rnd.shuffle(order); cm=tries%2==1
        ch=[rnd.randrange(len(B['alts'])) if B.get('alts') and tries>200 else 0 for B in laid]
        dims=[(B['alts'][k][1],B['alts'][k][2]) if B.get('alts') else (B['w'],B['h']) for B,k in zip(laid,ch)]
        bp=pack([dims[i] for i in order],Wu,Hu,res,cm)
        nover=sum(1 for x in bp if x is None)
        if nover<best[0]: best=(nover,order,bp); pick=ch
    if pick:
        for B,k in zip(laid,pick):
            if B.get('alts'): B['pos'],B['w'],B['h']=B['alts'][k]
    _,order,bp=best
    over=[laid[i]['title'] for i,pp_ in zip(order,bp) if pp_ is None]
    if over: print('OVERFLOW blocks:',over)
    print('block area %.0f of %.0f; '%(sum(B['w']*B['h'] for B in laid),Wu*Hu-(112/G)*(34/G))+', '.join('%s %dx%d'%(B['title'][:14],B['w'],B['h']) for B in laid))
    for i,pp_ in zip(order,bp): laid[i]['at']=pp_ if pp_ else (0,Hu+5)
    # emit
    out=[]; root=U(); proj=c.name; x0u=round(13.97/G); y0u=round(15.24/G)
    fileuuid=root
    if getattr(D,'path',None): proj,root=D.proj,D.path   # sub-sheet of a hierarchy: instances under /<root>/<sheet>
    GL=getattr(D,'glabels',set())
    out.append('(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")')
    out.append(f'(uuid "{fileuuid}")'); out.append(f'(paper "{D.paper}")')
    out.append('(title_block (title %s) (date "2026-11-23") (rev "M-mod P2b") (company "Project Blackstart") (comment 1 %s) (comment 2 %s))'%(
        q(title),q('cards/tools (schdraw.py) from tag baseline-2026-11-23-locked; BaselineRef = old ref'),q('One flat page: functional blocks, wired inside, labels between blocks')))
    out.append('(lib_symbols '+' '.join(dump(L) for L in c.libs.values())+' '+dump(c.srclibs['power:GND'])+' '+dump(c.srclibs['power:PWR_FLAG'])+' '+dump(c.srclibs['power:+3V3'])+')')
    cnt=collections.Counter()
    def pwr(lib,x,y,ang,hidev):
        pre='#PWR' if 'GND' in lib else '#FLG'; cnt[pre]+=1; ref='%s%03d'%(pre,cnt[pre]); val='GND' if 'GND' in lib else 'PWR_FLAG'
        out.append(f'(symbol (lib_id "{lib}") (at {f(x)} {f(y)} {ang}) (unit 1) (exclude_from_sim no) (in_bom no) (on_board yes) (dnp no) (uuid "{U()}") '
            f'(property "Reference" "{ref}" (at {f(x)} {f(y+3)} 0) (effects (font (size 1.27 1.27)) hide)) '
            f'(property "Value" {q(val)} (at {f(x)} {f(y-3)} 0) (effects (font (size 1.0 1.0)){" hide" if hidev else ""})) '
            f'(property "Footprint" "" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) hide)) '
            f'(pin "1" (uuid "{U()}")) (instances (project "{proj}" (path "/{root}" (reference "{ref}") (unit 1)))))')
    def rail(n,x,y,d):
        cnt['#PWR']+=1; ref='#PWR%03d'%cnt['#PWR']; th={(0,-1):0,(0,1):180,(-1,0):90,(1,0):270}[d]
        e=add((x,y),mul(d,2.6))
        if d[0]==0: tx,ty=x,e[1]+d[1]*(0.4+TH/2); j=''
        else: tx,ty=e[0]+d[0]*0.4,y; j=' (justify left)' if d[0]>0 else ' (justify right)'
        if th in (90,180) and j: j={' (justify left)':' (justify right)',' (justify right)':' (justify left)'}[j]
        fa=90 if th in (90,270) else 0
        out.append(f'(symbol (lib_id "power:+3V3") (at {f(x*G)} {f(y*G)} {th}) (unit 1) (exclude_from_sim no) (in_bom no) (on_board yes) (dnp no) (uuid "{U()}") '
            f'(property "Reference" "{ref}" (at {f(x*G)} {f(y*G)} 0) (effects (font (size 1.27 1.27)) hide)) '
            f'(property "Value" {q(n)} (at {f(tx*G)} {f(ty*G)} {fa}) (effects (font (size {FS} {FS})){j})) '
            f'(property "Footprint" "" (at {f(x*G)} {f(y*G)} 0) (effects (font (size 1.27 1.27)) hide)) '
            f'(pin "1" (uuid "{U()}")) (instances (project "{proj}" (path "/{root}" (reference "{ref}") (unit 1)))))')
    for B in laid:
        bx,by=B['at']; bx+=x0u; by+=y0u
        out.append(f'(rectangle (start {f(bx*G)} {f(by*G)}) (end {f((bx+B["w"])*G)} {f((by+B["h"])*G)}) (stroke (width 0.3) (type dash) (color 0 0 132 1)) (fill (type none)) (uuid "{U()}"))')
        out.append(f'(text {q(B["title"])} (exclude_from_sim no) (at {f((bx+1)*G)} {f((by+2.6)*G)} 0) (effects (font (size 2 2) (thickness 0.4) bold) (justify left bottom)) (uuid "{U()}"))')
        for P,(px,py) in zip(B['cl'],B['pos']):
            ox=int(math.floor(bx+1+px-P.bb.b[0]+1)); oy=int(math.floor(by+5+py-P.bb.b[1]+1))
            for pr in P.prims:
                pr=shift(pr,(ox,oy)) if pr[0]!='flag' else ('flag',add(pr[1],(ox,oy)))
                k=pr[0]
                if k=='wire':
                    (x1,y1),(x2,y2)=pr[1],pr[2]
                    if (x1,y1)!=(x2,y2): out.append(f'(wire (pts (xy {f(x1*G)} {f(y1*G)}) (xy {f(x2*G)} {f(y2*G)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
                elif k=='junc': out.append(f'(junction (at {f(pr[1][0]*G)} {f(pr[1][1]*G)}) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))')
                elif k=='nc': out.append(f'(no_connect (at {f(pr[1][0]*G)} {f(pr[1][1]*G)}) (uuid "{U()}"))')
                elif k=='label':
                    n,(x,y),d=pr[1],pr[2],pr[3]; ang=DIRS[d]; just='left' if ang in (0,90) else 'right'
                    if n in GL:
                        gj='left' if ang in (0,90) else 'right'
                        out.append(f'(global_label {q(n)} (shape bidirectional) (at {f(x*G)} {f(y*G)} {ang}) (fields_autoplaced yes) (effects (font (size {FS} {FS})) (justify {gj})) (uuid "{U()}") (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {f(x*G)} {f(y*G)} 0) (effects (font (size 1.27 1.27)) hide)))')
                    else:
                        out.append(f'(label {q(n)} (at {f(x*G)} {f(y*G)} {ang}) (fields_autoplaced yes) (effects (font (size {FS} {FS})) (justify {just} bottom)) (uuid "{U()}"))')
                elif k=='pwr':
                    n,(x,y),d=pr[1],pr[2],pr[3]
                    if n=='GND': pwr('power:GND',x*G,y*G,{(0,1):0,(0,-1):180,(1,0):90,(-1,0):270}[d],True)
                    else: rail(n,x,y,d)
                elif k=='flag': pwr('power:PWR_FLAG',pr[1][0]*G,pr[1][1]*G,0,False)
                elif k=='text':
                    out.append(f'(text {q(chr(10).join(pr[2]))} (exclude_from_sim no) (at {f(pr[1][0]*G)} {f(pr[1][1]*G)} 0) (effects (font (size {FS} {FS})) (justify left top)) (uuid "{U()}"))')
                elif k=='sym':
                    p,O,th,F=pr[1],pr[2],pr[3],pr[4]; emit_sym(out,p,O,th,F,proj,root)
    if not getattr(D,'path',None): out.append('(sheet_instances (path "/" (page "1")))')
    out.append('(embedded_fonts no))')
    os.makedirs(outdir,exist_ok=True)
    open(os.path.join(outdir,c.name+'.kicad_sch'),'w').write('\n'.join(out)+'\n')
    return over
