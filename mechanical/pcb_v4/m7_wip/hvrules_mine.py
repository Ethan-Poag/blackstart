"""Own checker for /workspace/compliance/hv_layout_rules_600V.md (sec 2/3). usage: hvrules.py board.kicad_pcb [out.json]
Model (sheet sec.3, [I]): 4x1M chains; node k at Vph*(4-k)/4 (Vph=382 Vrms, +10%); N chains ~0 V; GEN vs BUS worst case |a|+|b|.
Outer layers: full line-line 6.6, line-N 5.5, other node pairs creepage(table F.4 interp, PD2 IIIa); same chain adjacent >=1.5; tap nodes exempt (>=0.2).
Inner: 1.5 between different hot nets. HOT<->SELV >=12.6 all layers. HOT<->edge >=8.0.  Slots: copper on the far side of an Edge.Cuts slot is measured
straight-line (conservative: creepage around slot not credited)."""
import pcbnew,sys,math,cmath,json,collections
from shapely.geometry import Point,LineString,Polygon
from shapely.strtree import STRtree
TM=pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1])
CH={'GEN_L1':(422,0),'GEN_L2':(429,-120),'GEN_L3':(436,120),'GEN_N':(443,None),'BUS_L1':(448,0),'BUS_L2':(455,-120),'BUS_L3':(462,120),'BUS_N':(469,None)}
F={f.GetReference():f for f in b.GetFootprints()}
node={}  # netcode -> (chain,k)
for ch,(r0,ang) in CH.items():
    rs=[F['R%d'%(r0+i)] for i in range(4)]
    nets=[set(p.GetNetCode() for p in r.Pads()) for r in rs]
    line=[ni.GetNetCode() for n,ni in b.GetNetsByName().items() if str(n).endswith('/'+ch)][0]
    node[line]=(ch,0); cur=line
    for k in range(4):
        nxt=(nets[k]-{cur}).pop(); node[nxt]=(ch,k+1); cur=nxt
def V(nc):
    ch,k=node[nc];ang=CH[ch][1]
    if ang is None: return 0j
    return 382*(4-k)/4*cmath.exp(1j*math.radians(ang))
def creep(v):
    T=[(0,0.2),(250,2.5),(320,3.2),(400,4.0),(500,5.0),(630,6.3),(800,8.0),(1000,10.0)]
    for (a,x),(c,y) in zip(T,T[1:]):
        if v<=c: return x+(y-x)*(v-a)/(c-a)
    return 10
def req(a,c,outer):
    (ca,ka),(cc,kc)=node[a],node[c]
    if ca==cc and abs(ka-kc)==1: return 1.5,'same-chain adjacent'
    if ka==4 or kc==4: return 0.2,'tap node exempt'
    if not outer: return 1.5,'inner'
    va,vc=V(a),V(c)
    dv=abs(va)+abs(vc) if ca[:3]!=cc[:3] else abs(va-vc)
    r=creep(dv)
    if ka==0 and kc==0:
        nn=(CH[ca][1] is None)+(CH[cc][1] is None)
        r=max(r,6.6 if nn==0 else 5.5)
    return r,'%.0f Vrms'%dv
def geoms(layer):
    out=[]
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.IsOnLayer(layer) and p.GetNetCode()>0:
                s=p.GetEffectivePolygon(layer);o=s.Outline(0)
                out.append((Polygon([(TM(o.CPoint(i).x),TM(o.CPoint(i).y)) for i in range(o.PointCount())]).buffer(0),p.GetNetCode(),f.GetReference()+'.'+p.GetNumber()))
    for t in b.GetTracks():
        if t.GetNetCode()<=0: continue
        if t.GetClass()=='PCB_VIA':
            out.append((Point(TM(t.GetPosition().x),TM(t.GetPosition().y)).buffer(TM(t.GetWidth(pcbnew.F_Cu))/2),t.GetNetCode(),'via'))
        elif t.GetLayer()==layer:
            out.append((LineString([(TM(t.GetStart().x),TM(t.GetStart().y)),(TM(t.GetEnd().x),TM(t.GetEnd().y))]).buffer(TM(t.GetWidth())/2),t.GetNetCode(),'track'))
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetCode()<=0 or not z.IsOnLayer(layer): continue
        ps=z.GetFilledPolysList(layer)
        for k in range(ps.OutlineCount()):
            o=ps.Outline(k);pts=[(TM(o.CPoint(j).x),TM(o.CPoint(j).y)) for j in range(o.PointCount())]
            if len(pts)>2: out.append((Polygon(pts).buffer(0),z.GetNetCode(),'zone'))
    return out
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
# SELV = nets with no pad in the hot zone (x<59.5)
hotzone=set()
for f in b.GetFootprints():
    for p in f.Pads():
        if TM(p.GetPosition().x)<59.5 and TM(p.GetPosition().y)>11 and TM(p.GetPosition().y)<163: hotzone.add(p.GetNetCode())
for z in b.Zones():
    if not z.GetIsRuleArea() and z.GetZoneName().startswith('HV'): hotzone.add(z.GetNetCode())
# M7 ruling 3: isolator side-2 pins (U69/U70 pins 9-16) are HOT domain
for r in ('U69','U70'):
    for p in F[r].Pads():
        if p.GetNumber().isdigit() and 9<=int(p.GetNumber())<=16: hotzone.add(p.GetNetCode())
ol=pcbnew.SHAPE_POLY_SET();b.GetBoardPolygonOutlines(ol);o=ol.Outline(0)
edge=Polygon([(TM(o.CPoint(i).x),TM(o.CPoint(i).y)) for i in range(o.PointCount())]).exterior
_b0=pcbnew.LoadBoard('/workspace/m7/base.kicad_pcb');_o=pcbnew.SHAPE_POLY_SET();_b0.GetBoardPolygonOutlines(_o);_oo=_o.Outline(0)
edge=Polygon([(TM(_oo.CPoint(i).x),TM(_oo.CPoint(i).y)) for i in range(_oo.PointCount())]).exterior  # true outer edge (slots excluded)
hot={n for n,(c,k) in node.items() if k<4}
from shapely.ops import nearest_points
slots=[]
for k in range(ol.OutlineCount()):
    for h in range(ol.HoleCount(k)):
        hh=ol.Hole(k,h);slots.append(Polygon([(TM(hh.CPoint(j).x),TM(hh.CPoint(j).y)) for j in range(hh.PointCount())]))
def creepd(g,g2):
    a,c=nearest_points(g,g2);d=a.distance(c);seg=LineString([a,c])
    for s in slots:
        if seg.crosses(s) or seg.within(s) or seg.intersects(s.buffer(-0.01)):
            cs=list(s.exterior.coords)[:-1];best=1e9
            for p in cs:
                for q in cs:
                    l1,l2,l3=LineString([a.coords[0],p]),LineString([p,q]),LineString([q,c.coords[0]])
                    if any(x.intersects(s.buffer(-0.01)) for x in (l1,l2,l3)):continue
                    best=min(best,g.distance(Point(p))+Point(p).distance(Point(q))+g2.distance(Point(q)))
            return max(d,best),d
    return d,d
viol=collections.defaultdict(list)
for layer in b.GetEnabledLayers().CuStack():
    outer=layer in (pcbnew.F_Cu,pcbnew.B_Cu);ln=b.GetLayerName(layer)
    G=geoms(layer);tree=STRtree([g for g,_,_ in G])
    for i,(g,n,lab) in enumerate(G):
        if n not in hot: continue
        d=g.distance(edge)
        if d<8.0: viol['hot-edge<8.0'].append((ln,b.GetNetsByNetcode()[n].GetNetname().split('/')[-1],lab,round(d,3)))
        for j in tree.query(g.buffer(12.6)):
            g2,n2,lab2=G[j]
            if n2==n: continue
            d=g.distance(g2)
            if n2 in node and d<12.6:
                cr,cl_=creepd(g,g2)
                if cr>d+1e-3:
                    r,why=req(n,n2,outer)
                    if cr>=r-1e-3 and cl_>=(5.5 if node[n][1]==0 and node[n2][1]==0 else 0): continue
                    d=cr
            if n2 in node:
                if j<i and n2 in hot: continue
                r,why=req(n,n2,outer)
                if d<r-1e-3: viol['hv-hv'].append((ln,b.GetNetsByNetcode()[n].GetNetname().split('/')[-1],b.GetNetsByNetcode()[n2].GetNetname().split('/')[-1],lab,lab2,round(d,3),round(r,2),why,[round(x,2) for x in g.centroid.coords[0]]))
            elif n2 not in hotzone:
                if d<12.6: viol['hot-selv<12.6'].append((ln,b.GetNetsByNetcode()[n].GetNetname().split('/')[-1],b.GetNetsByNetcode()[n2].GetNetname().split('/')[-1],lab,lab2,round(d,3)))
# dedupe hv-hv by (layer,netA,netB) keeping worst, but also count raw
summ={}
for k,v in viol.items():
    if k=='hv-hv':
        w={}
        for x in v:
            key=(x[0],)+tuple(sorted((x[1],x[2])))
            if key not in w or x[5]<w[key][5]: w[key]=x
        summ[k]=dict(raw=len(v),net_pairs=len(w),worst=sorted(w.values(),key=lambda x:x[5]-x[6])[:40])
    else:
        w={}
        for x in v:
            key=x[:3] if k!='hot-edge<8.0' else x[:2]
            if key not in w or x[-1]<w[key][-1]: w[key]=x
        summ[k]=dict(raw=len(v),groups=len(w),worst=sorted(w.values(),key=lambda x:x[-1])[:20])
print(json.dumps({k:{kk:vv for kk,vv in v.items() if kk!='worst'} for k,v in summ.items()}))
for k,v in summ.items():
    print('==',k)
    for x in v['worst'][:30]: print('  ',x)
if len(sys.argv)>2: json.dump(summ,open(sys.argv[2],'w'),indent=1)
