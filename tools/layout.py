"""Clustered placement + orthogonal maze routing for generated sheets.
Same-sheet nets become real wires on the 1.27 mm grid (with junctions); labels remain only for
off-sheet nets (global labels), power/ground/isolated rails (power symbols) and wide buses (local labels)."""
import math, re, heapq, collections
import gen, kilib
from gen import G, U, q, f, snap, POWER_SYMS, REFC, find, find1

BUS_RE=re.compile(r'(SPI|SCK|SCLK|MOSI|MISO|_CS\b|SDA|SCL|I2C|DSI|LVDS|MDI|^EXP|_P[01][0-7]$|^DPLUS|^DMINUS|_D[PN]\d?$|USB_D)')
RAIL_RE=re.compile(r'^(GND|\+)|^V(MID|LED|DDA|BAT|DD|CC|IN|ISO|_)|VCC$|VDD|BTN_LED_V|^VBUS|_VCC$')
STATS={}
LMAX=36  # max wire cells (1.27 mm) per connection before falling back to labels

def gi(v): return int(round(v/G))

def body_box(pt,ps):
    xs=[];ys=[]
    for p in ps: xs.append(p['x']); ys.append(-p['y'])
    for sub in find(pt.sym,'symbol'):
        for r in find(sub,'rectangle'):
            st=find1(r,'start'); en=find1(r,'end'); xs+=[float(st[1]),float(en[1])]; ys+=[-float(st[2]),-float(en[2])]
        for c in find(sub,'circle'):
            ce=find1(c,'center'); ra=float(find1(c,'radius')[1]); xs+=[float(ce[1])-ra,float(ce[1])+ra]; ys+=[-float(ce[2])-ra,-float(ce[2])+ra]
        for pl in find(sub,'polyline'):
            for xy in find(find1(pl,'pts'),'xy'): xs.append(float(xy[1])); ys.append(-float(xy[2]))
    if not xs: xs=[0];ys=[0]
    x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys)
    if x1-x0<2.54: x0-=1.27; x1+=1.27
    if y1-y0<2.54: y0-=1.27; y1+=1.27
    return [x0,y0,x1,y1]

def outdir(p):
    o=(p['ang']+180)%360
    return o, round(math.cos(math.radians(o))), -round(math.sin(math.radians(o)))

class Item:
    def __init__(s,pt,u,ps,bb):
        s.pt=pt; s.u=u; s.ps=ps; s.full=bb; s.body=body_box(pt,ps); s.X=s.Y=0; s.anchor=None; s.sats=[]
        s.npins=len([p for p in ps])
    def pinpos(s,p): return (s.X+p['x'], s.Y-p['y'])

def classify(n,driven,netsheets,npins):
    if n is None: return 'nc'
    if n in POWER_SYMS: return 'power'
    if len(netsheets[n])>1: return 'global'
    if npins.get(n,0)>=6 and RAIL_RE.search(n) and n in driven: return 'rail'
    if BUS_RE.search(n): return 'bus'
    if npins.get(n,0)<2: return 'single'
    return 'local'

def overlap(a,b,m=0):
    return not (a[2]+m<=b[0] or b[2]+m<=a[0] or a[3]+m<=b[1] or b[3]+m<=a[1])

def place(sh,items,kind):
    anchors=[it for it in items if it.npins>=5 and not it.pt.power]
    if not anchors: anchors=items[:1]
    sats=[it for it in items if it not in anchors]
    def nets(it,kinds=('local',)): return {it.pt.net[p['num']] for p in it.ps if kind(it.pt.net[p['num']]) in kinds}
    owner={}
    # pass 1: local-net sharing with anchors
    for s_ in sats:
        ns=nets(s_); best=None;bc=0
        for a in anchors:
            c=len(ns & nets(a))
            if c>bc: best,bc=a,c
        if best: owner[id(s_)]=best
    # pass 2: chains through other satellites
    for _ in range(4):
        for s_ in sats:
            if id(s_) in owner: continue
            ns=nets(s_)
            for o in sats:
                if id(o) in owner and ns & nets(o): owner[id(s_)]=owner[id(o)]; break
    # pass 3: decoupling caps (only power/rail nets) -> preceding anchor with that rail
    order={id(it):i for i,it in enumerate(items)}
    for s_ in sats:
        if id(s_) in owner: continue
        rails=[n for n in nets(s_,('power','rail','global')) if not n.startswith('GND')]
        cand=[a for a in anchors if rails and set(rails)&nets(a,('power','rail','global')) and order[id(a)]<order[id(s_)]]
        if not cand: cand=[a for a in anchors if rails and set(rails)&nets(a,('power','rail','global'))]
        if cand:
            owner[id(s_)]=max(cand,key=lambda a:order[id(a)]) if order[id(cand[0])]<order[id(s_)] else cand[0]
            s_.decap=True
    loose=[s_ for s_ in sats if id(s_) not in owner]
    for s_ in sats:
        if id(s_) in owner: owner[id(s_)].sats.append(s_); s_.anchor=owner[id(s_)]
    clusters=[]
    for a in anchors: clusters.append(layout_cluster(a,kind))
    # loose: group consecutive
    for i in range(0,len(loose),6):
        grp=loose[i:i+6]; x=0; rects=[]
        for it in grp:
            it.X=x-it.full[0]; it.Y=-it.full[1]; x+=it.full[2]-it.full[0]+5.08
        clusters.append(grp)
    return clusters

def side_of(p):
    o,dx,dy=outdir(p); return {(-1,0):'L',(1,0):'R',(0,-1):'T',(0,1):'B'}[(dx,dy)]

def layout_cluster(a,kind):
    a.X=0;a.Y=0
    placed=[[a.full[0],a.full[1],a.full[2],a.full[3]]]
    ab=a.full
    for s_ in a.sats:
        # target anchor pin
        tp=None
        sn={s_.pt.net[p['num']] for p in s_.ps}
        for p in a.ps:
            n=a.pt.net[p['num']]
            if n in sn and kind(n)=='local': tp=p;break
        if tp is None:
            for p in a.ps:
                n=a.pt.net[p['num']]
                if n in sn and n and not n.startswith('GND'): tp=p;break
        if tp is None: tp=a.ps[0]
        sd=side_of(tp); px,py=tp['x'],-tp['y']
        fb=s_.full; w=fb[2]-fb[0]; h=fb[3]-fb[1]
        done=False
        for k in range(0,400):
            for j in [0,1,-1,2,-2,3,-3,4,-4,5,-5,6,-6,8,-8,10,-10]:
                if sd=='L': x1=ab[0]-2.54-k*5.08; x0=x1-w; y0=py-h/2+j*2.54
                elif sd=='R': x0=ab[2]+2.54+k*5.08; y0=py-h/2+j*2.54
                elif sd=='T': y1=ab[1]-2.54-k*5.08; y0=y1-h; x0=px-w/2+j*2.54
                else: y0=ab[3]+2.54+k*5.08; x0=px-w/2+j*2.54
                r=[x0,y0,x0+w,y0+h]
                if not any(overlap(r,o,2.54) for o in placed):
                    placed.append(r); s_.X=snap(x0-fb[0]); s_.Y=snap(y0-fb[1]); done=True; break
            if done: break
        assert done, s_.pt.ref
    return [a]+a.sats

def item_rect(it,full=True):
    b=it.full if full else it.body
    return [it.X+b[0],it.Y+b[1],it.X+b[2],it.Y+b[3]]

# ---------------- router ----------------
DIRS=[(1,0),(0,1),(-1,0),(0,-1)]
class Router:
    def __init__(s,W,H):
        s.W=W;s.H=H; s.block=set(); s.tip={}; s.occ={}; s.edges=collections.defaultdict(set); s.reserve={}; s.cross=set()
    def ok(s,n):
        return 0<=n[0]<s.W and 0<=n[1]<s.H
    def route(s,net,start,sdir,targets,tipdir,limit_box=None,maxexp=150000):
        """A* from start (pin tip, must leave along sdir) to any node in targets (tip nodes need entering along tipdir[node])."""
        tx=[t for t in targets]
        if not tx: return None
        def h(n): return min(abs(n[0]-t[0])+abs(n[1]-t[1]) for t in tx[:40])
        st=(start,sdir); pq=[(h(start),0,start,sdir)]; prev={st:None}; cost={st:0}; exp=0
        while pq:
            _,c,n,d=heapq.heappop(pq)
            if cost.get((n,d),1e9)<c: continue
            exp+=1
            if exp>maxexp: return None
            o=s.occ.get(n)
            crossing = o is not None and o[0]!=net
            for di,(dx,dy) in enumerate(DIRS):
                if n==start and di!=sdir: continue
                if crossing and di!=d: continue
                if (di+2)%4==d and n!=start: continue
                m=(n[0]+dx,n[1]+dy)
                if not s.ok(m): continue
                if limit_box and not (limit_box[0]<=m[0]<=limit_box[2] and limit_box[1]<=m[1]<=limit_box[3]): continue
                nc=c+1+(3 if (di!=d and n!=start) else 0)
                if m in targets and m not in s.cross:
                    if m in tipdir and tipdir[m]!=di: continue
                    key=(m,di); prev[key]=(n,d); return s._path(prev,key)
                if m in s.block: continue
                if m in s.tip: continue
                r=s.reserve.get(m)
                if r is not None and r!=net and r!=net.rsplit('#',1)[0]: continue
                om=s.occ.get(m)
                if om is not None:
                    if om[0]==net: continue
                    if om[1]=='X': continue
                    if om[1]==('H' if dx else 'V'): continue
                    nc+=12
                if (m,di) not in cost or nc<cost[(m,di)]:
                    cost[(m,di)]=nc; prev[(m,di)]=(n,d); heapq.heappush(pq,(nc+h(m),nc,m,di))
        return None
    def _path(s,prev,key):
        out=[]
        while key: out.append(key[0]); key=prev[key]
        return out[::-1]
    def commit(s,net,path):
        for a,b in zip(path,path[1:]):
            s.edges[net].add((min(a,b),max(a,b)))
        for i,n in enumerate(path):
            if i in (0,len(path)-1): kind='X'
            else:
                a,b=path[i-1],path[i+1]
                kind='H' if a[1]==b[1]==n[1] else ('V' if a[0]==b[0]==n[0] else 'X')
            o=s.occ.get(n)
            if o and o[0]==net: kind='X'
            if o and o[0]!=net: s.cross.add(n); continue
            s.occ[n]=(net,kind)
    def uncommit(s,net):
        s.edges.pop(net,None)
        for n in [k for k,v in s.occ.items() if v[0]==net]: del s.occ[n]

def segments(edges):
    adj=collections.defaultdict(set)
    for a,b in edges: adj[a].add(b); adj[b].add(a)
    segs=[]; seen=set()
    for a,b in edges:
        if (a,b) in seen: continue
        # extend straight both ways through degree-2 straight nodes
        horiz=a[1]==b[1]
        def ext(n,p):
            while True:
                nx=[m for m in adj[n] if m!=p]
                if len(adj[n])==2 and len(nx)==1 and ((nx[0][1]==n[1])==horiz) and ((p[1]==n[1])==horiz):
                    seen.add((min(n,nx[0]),max(n,nx[0]))); p,n=n,nx[0]
                else: return n
        seen.add((a,b))
        e1=ext(a,b); e2=ext(b,a); segs.append((e1,e2))
    junc=[n for n,v in adj.items() if len(v)>=3]
    return segs,junc

def write_sheet(sh, root_uuid, netsheets):
    npins=collections.Counter(); driven=set()
    items=[]
    for pt in sh.parts:
        for u in kilib.units(pt.sym):
            ps,bb=gen.unit_geom(pt,u); items.append(Item(pt,u,ps,bb))
            for p in ps:
                if pt.net[p['num']]:
                    npins[pt.net[p['num']]]+=1
                    if p['type']=='power_out' or pt.libid=='power:PWR_FLAG': driven.add(pt.net[p['num']])
    kind=lambda n: classify(n,driven,netsheets,npins)
    clusters=place(sh,items,kind)
    # cluster bboxes and shelf placement
    cb=[]
    for cl in clusters:
        rs=[item_rect(it) for it in cl]
        cb.append((min(r[0] for r in rs)-10.16,min(r[1] for r in rs)-12.7,max(r[2] for r in rs)+10.16,max(r[3] for r in rs)+7.62))
    for pname,PW,PH in gen.PAPERS+[('User',1500,1100)]:
        W=PW-30; x=y=rowh=0; offs=[]
        for b in cb:
            w=b[2]-b[0];h=b[3]-b[1]
            if x+w>W and x>0: y+=rowh; x=0; rowh=0
            offs.append((x-b[0],y-b[1])); x+=w; rowh=max(rowh,h)
        if y+rowh<=PH-50: break
    if pname=='User': PW,PH=max(PW,int(x)+60),int(y+rowh)+80
    for cl,(ox,oy) in zip(clusters,offs):
        for it in cl: it.X=snap(it.X+ox+15); it.Y=snap(it.Y+oy+40)
    CL={}
    for ci,cl in enumerate(clusters):
        for it in cl: CL[id(it)]=ci
    prev_failed=[]
    for attempt in range(2):
        R=Router(gi(PW),gi(PH))
        libs={}; body=[]; path='/%s/%s'%(root_uuid,sh.uuid)
        # obstacles: bodies (open interior + boundary except tips)
        pins=[]  # (it,p,node,outdir_index,net)
        for it in items:
            libs[it.pt.libid]=it.pt.sym
            b=item_rect(it,False)
            for gx in range(gi(b[0]),gi(b[2])+1):
                for gy in range(gi(b[1]),gi(b[3])+1): R.block.add((gx,gy))
            for p in it.ps:
                x,y=it.pinpos(p); nd=(gi(x),gi(y)); o,dx,dy=outdir(p)
                di=DIRS.index((dx,dy)); pins.append((it,p,nd,di,it.pt.net[p['num']]))
        for it,p,nd,di,n in pins:
            R.block.discard(nd); R.tip[nd]=n
            # reserve 2-cell stub
            dx,dy=DIRS[di]
            for k in (1,2):
                m=(nd[0]+dx*k,nd[1]+dy*k)
                if m not in R.reserve: R.reserve[m]=n
                else: R.reserve[m]='#conflict'
        # which pins get wires
        bynet=collections.defaultdict(list)
        for t in pins:
            if t[4] is not None: bynet[t[4]].append(t)
        wired=collections.defaultdict(list)  # net -> list of pin tuples to connect
        for n,lst in bynet.items():
            k=kind(n)
            if k=='local':
                if len({CL[id(t[0])] for t in lst})==1: wired[n]=lst   # beautify: wire only inside one functional group
            elif k in ('power','rail','global'):
                # decap groups: anchor pins + decap pins of same net
                grp=collections.defaultdict(list)
                for t in lst:
                    it=t[0]; a=it if it.sats else it.anchor
                    if a is not None and (it.sats or getattr(it,'decap',False)) and not n.startswith('GND'): grp[id(a)].append(t)
                for g in grp.values():
                    g.sort(key=lambda t:0 if t[0].sats else 1)
                    if len(g)>=2 and any(getattr(t[0],'decap',False) for t in g): wired[(n,len(wired))]=g
        for key_,_ in prev_failed: wired.pop(key_,None)
        labelled=set()
        wp=set()
        for key,lst in wired.items():
            for t in lst: wp.add((id(t[0]),t[1]['num'],t[1]['unit']))
        for it,p,nd,di,n in pins:
            if n is None or (id(it),p['num'],p['unit']) in wp: continue
            dx,dy=DIRS[di]; k=kind(n)
            L=4 if k in ('power','rail') else int(gen.lab_len(n,k=='global')/G)+2
            for a in range(3,3+L):
                for b in (-1,0,1):
                    m=(nd[0]+dx*a+(b if dy else 0), nd[1]+dy*a+(b if dx else 0))
                    if m not in R.tip: R.block.add(m)
        order=sorted(wired.items(),key=lambda kv:(len(kv[1]),max(abs(a[2][0]-b[2][0])+abs(a[2][1]-b[2][1]) for a in kv[1] for b in kv[1])))
        failed=[]
        for key,lst in order:
            net=key if isinstance(key,str) else key[0]
            tag=key if isinstance(key,str) else '%s#%d'%key
            ok=True
            conn=[lst[0]]; tree=set(); tipdir={}
            rest=lst[1:]
            # first: from lst[0] to nearest other tip
            tree_nodes={lst[0][2]}
            R.reserve.update({})
            for t in sorted(rest,key=lambda t:abs(t[2][0]-lst[0][2][0])+abs(t[2][1]-lst[0][2][1])):
                targets=set(tree_nodes)
                tdir={}
                if len(tree_nodes)==1:
                    s0=lst[0]; tdir[s0[2]]=(s0[3]+2)%4
                xs=[n[0] for n in targets]+[t[2][0]]; ys=[n[1] for n in targets]+[t[2][1]]
                box=(min(xs)-25,min(ys)-25,max(xs)+25,max(ys)+25)
                pth=R.route(tag,t[2],t[3],targets,tdir,box)
                if not pth: ok=False; break
                R.commit(tag,pth); tree_nodes|=set(pth)
            if ok and len(R.edges.get(tag,()))>LMAX*max(1,len(lst)-1): ok=False   # beautify: long detours -> labels
            if not ok:
                R.uncommit(tag); failed.append((key,lst))
        if not failed or attempt==1: break
        prev_failed=prev_failed+failed   # beautify pass 2: re-route with label areas of fallback nets blocked
    failed_total=prev_failed+failed
    rs=[item_rect(it,False) for it in items]
    ov=sum(1 for i in range(len(rs)) for j in range(i) if overlap(rs[i],rs[j]))
    STATS[sh.name]=dict(routed=len(wired)-len(failed),label_fallback=len(failed)+len(prev_failed),body_overlaps=ov,paper=pname)
    failed_pins=set()
    for key,lst in failed:
        for t in lst: failed_pins.add((id(t[0]),t[1]['num'],t[1]['unit']))
    wired_pins=set()
    for key,lst in wired.items():
        if (key,lst) in failed: continue
        for t in lst: wired_pins.add((id(t[0]),t[1]['num'],t[1]['unit']))
    # emit symbols
    for it in items: body.append(gen.sym_inst(it.pt,it.u,it.X,it.Y,path))
    # power symbol per wired power group: keep on first anchor pin only
    grp_rep=set()
    for key,lst in wired.items():
        if isinstance(key,tuple) and (key,lst) not in failed:
            for t in lst[1:]: grp_rep.add((id(t[0]),t[1]['num'],t[1]['unit']))
    nlab=0; nwire=0
    for it,p,nd,di,n in pins:
        pid=(id(it),p['num'],p['unit'])
        x,y=nd[0]*G,nd[1]*G
        if n is None:
            body.append('(no_connect (at %s %s) (uuid "%s"))'%(f(x),f(y),U())); continue
        k=kind(n)
        if pid in wired_pins and (k=='local' or pid in grp_rep): continue
        o,dx,dy=outdir(p)
        ex,ey=round(x+dx*2.54,2),round(y+dy*2.54,2)
        body.append('(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))'%(f(x),f(y),f(ex),f(ey),U())); nwire+=1
        if k in ('power','rail'):
            if k=='power': lid=POWER_SYMS[n]
            else: lid='power:GND' if n.startswith('GND') else 'power:VCC'
            psym=kilib.get_symbol(lid); libs[lid]=psym
            gnd=lid=='power:GND'
            if dx: rot=(o-kilib.pins(psym)[0]['ang'])%360   # side pin: point outward so names do not stack
            else: rot=(180 if dy<0 else 0) if gnd else (180 if dy>0 else 0)   # top/bottom: rails up, ground down
            REFC['#PWR']+=1; ref='#PWR%04d'%REFC['#PWR']
            s_=gen.power_inst(lid,n,ref,ex,ey,rot,path)
            if k=='rail': s_=s_.replace('(property "Value" %s'%q(lid.split(':')[1]),'(property "Value" %s'%q(n))
            body.append(s_)
        elif k=='global':
            just='left' if o in (0,90) else 'right'
            body.append('(global_label %s (shape passive) (at %s %s %d) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify %s)) (uuid "%s") (property "Intersheetrefs" "${INTERSHEET_REFS}" (at %s %s 0) (effects (font (size 1.27 1.27)) (hide yes))))'%(q(n),f(ex),f(ey),o,just,U(),f(ex),f(ey))); nlab+=1
        else:
            just='left' if o in (0,90) else 'right'
            body.append('(label %s (at %s %s %d) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid "%s"))'%(q(n),f(ex),f(ey),o,just,U())); nlab+=1
    for net,edges in R.edges.items():
        segs,junc=segments(edges)
        for a,b in segs:
            body.append('(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))'%(f(a[0]*G),f(a[1]*G),f(b[0]*G),f(b[1]*G),U())); nwire+=1
        for j in junc:
            body.append('(junction (at %s %s) (diameter 0) (color 0 0 0 0) (uuid "%s"))'%(f(j[0]*G),f(j[1]*G),U()))
    for ci,cl in enumerate(clusters):
        rs=[item_rect(it) for it in cl]
        x0=snap(min(r[0] for r in rs)-5.08); y0=snap(min(r[1] for r in rs)-5.08); x1=snap(max(r[2] for r in rs)+5.08); y1=snap(max(r[3] for r in rs)+5.08)
        body.append('(rectangle (start %s %s) (end %s %s) (stroke (width 0.25) (type dash) (color 72 72 160 1)) (fill (type none)) (uuid "%s"))'%(f(x0),f(y0),f(x1),f(y1),U()))
        a0=cl[0]
        ttl=(a0.pt.ref+' '+a0.pt.value) if (len(cl)>1 or a0.npins>=5) else 'misc'
        if len(cl)>1 and a0.npins<5: ttl='misc / support'
        body.append('(text %s (exclude_from_sim no) (at %s %s 0) (effects (font (size 2 2) (thickness 0.3) bold (color 72 72 160 1)) (justify left bottom)) (uuid "%s"))'%(q(ttl),f(x0+1.27),f(y0-0.635),U()))
    if sh.notes:
        body.append('(text %s (exclude_from_sim no) (at 15 12 0) (effects (font (size 1.6 1.6)) (justify left top)) (uuid "%s"))'%(q(sh.notes),U()))
    txt=['(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")',
         '(uuid "%s")'%sh.uuid, '(paper "%s"%s)'%(pname,'' if pname!='User' else ' %d %d'%(PW,PH)),
         '(title_block (title %s) (company "genctl") (rev "A-draft") (comment 1 "Generated by tools/gen.py + tools/layout.py (clustered, wired) - see DESIGN_NOTES.md"))'%q(sh.title),
         '(lib_symbols']
    for lid,s in libs.items():
        s2=list(s); s2[1]=lid; txt.append(gen.dump(s2,1))
    txt.append(')'); txt+=body; txt.append(')')
    import os
    open(os.path.join(gen.OUT,sh.file),'w').write(('\n'.join(txt)+'\n').replace('(hide yes)','hide'))
