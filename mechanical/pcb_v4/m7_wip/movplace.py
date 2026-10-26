"""M7-A: re-place the 32 HV divider resistors so every pad meets hv_layout_rules_600V.md vs other HV pads (outer, node-voltage aware),
>=8 mm from board edge, >=12.6 mm from H1-H4. Rips HV-class copper on B.Cu/In2 + vias (F.Cu kept). usage: hvplace.py in out"""
import sys,math,cmath,json,pcbnew
sys.argv_saved=list(sys.argv)
src,dst=sys.argv[1],sys.argv[2]
sys.argv=['mover.py',src,dst,'/dev/null']
exec(open('/workspace/m7/mover.py').read().split('log=[]')[0])
from shapely.geometry import Point
CH={'GEN_L1':(422,0),'GEN_L2':(429,-120),'GEN_L3':(436,120),'GEN_N':(443,None),'BUS_L1':(448,0),'BUS_L2':(455,-120),'BUS_L3':(462,120),'BUS_N':(469,None)}
hv=open('/workspace/m7/hvrules.py').read()
exec(hv[hv.index('def V(nc)'):hv.index('def geoms')])
node={}
for ch,(r0,ang) in CH.items():
    rs=[fps['R%d'%(r0+i)] for i in range(4)]
    nets=[set(p.GetNetCode() for p in r.Pads()) for r in rs]
    line=[ni.GetNetCode() for n,ni in b.GetNetsByName().items() if str(n).endswith('/'+ch)][0]
    node[line]=(ch,0);cur=line
    for k in range(4):
        nxt=(nets[k]-{cur}).pop();node[nxt]=(ch,k+1);cur=nxt
MOV=['RV%d'%i for i in range(1,7)]
# rip HV copper (not F.Cu)
rip=[t for t in b.GetTracks() if nc.get(t.GetNetCode(),'').startswith('HV') and (t.GetClass()=='PCB_VIA' or t.GetLayer()!=pcbnew.F_Cu)]
print('ripping',len(rip),'HV items (locked %d)'%sum(t.IsLocked() for t in rip))
rip=[]
edge=Polygon([P(o.CPoint(i)) for i in range(o.PointCount())]).exterior
holes=[Point(P(fps[h].GetPosition())) for h in ('H1','H2','H3','H4') if h in fps]
def hvpads(skip):
    out=[]
    for f in fps.values():
        if f.GetReference()==skip: continue
        for p in f.Pads():
            if p.GetNetCode() in node and p.IsOnLayer(pcbnew.B_Cu): out.append((padg(p,pcbnew.B_Cu),p.GetNetCode(),f.GetReference()+'.'+p.GetNumber()))
    return out
def hvok(f,HP):
    bad=[]
    for p in f.Pads():
        g=padg(p,pcbnew.B_Cu);n=p.GetNetCode()
        if g.distance(edge)<8.0: bad.append(('edge',round(g.distance(edge),2)))
        for h in holes:
            if g.distance(h)<12.6+1.6: bad.append(('hole',))
        for g2,n2,lab in HP:
            if n2==n: continue
            r,_=req(n,n2,True)
            d=g.distance(g2)
            if d<r+0.25: bad.append((lab,round(d,2),round(r,2)))
    return bad
def wl(f):
    s=0
    for p in f.Pads():
        q=[x for x in b.GetPads() if x.GetNetCode()==p.GetNetCode() and x.GetParentFootprint().GetReference()!=f.GetReference()]
        if q: s+=min(math.hypot(*(TM(v) for v in (x.GetPosition()-p.GetPosition()))) for x in q)
    return s
log=[]
for it in range(3):
    moved=0
    for ref in MOV:
        f=fps[ref];HP=hvpads(ref);bad=hvok(f,HP)
        if not bad: continue
        C,CU,TH=obstacles(ref)
        ox,oy=P(f.GetPosition());oa=f.GetOrientationDegrees();best=None
        # target = centroid of connected pads
        tg=[P(x.GetPosition()) for p in f.Pads() for x in b.GetPads() if x.GetNetCode()==p.GetNetCode() and x.GetParentFootprint().GetReference()!=ref]
        tx=sum(a for a,_ in tg)/len(tg);ty=sum(c for _,c in tg)/len(tg)
        for cx,cy in ((ox,oy),(tx,ty)):
          for r in [x*0.5 for x in range(0,41)]:
            n=max(1,int(2*math.pi*r/0.5));found=[]
            for k in range(n):
                x=cx+r*math.cos(2*math.pi*k/n);y=cy+r*math.sin(2*math.pi*k/n)
                for ang in (0,90,180,270):
                    f.SetPosition(pcbnew.VECTOR2I_MM(x,y));f.SetOrientationDegrees(ang);CRT.pop(ref,None)
                    if legal(f,True,C,CU,TH) and not hvok(f,HP): found.append((wl(f),x,y,ang))
            if found: best=min(found) if best is None or min(found)[0]<best[0] else best;break
        if best:
            f.SetPosition(pcbnew.VECTOR2I_MM(best[1],best[2]));f.SetOrientationDegrees(best[3]);CRT.pop(ref,None)
            log.append((it,ref,(round(ox,2),round(oy,2)),(round(best[1],2),round(best[2],2)),best[3]));moved+=1
            print(it,ref,'moved',(round(ox,1),round(oy,1)),'->',(round(best[1],1),round(best[2],1)),flush=True)
        else:
            f.SetPosition(pcbnew.VECTOR2I_MM(ox,oy));f.SetOrientationDegrees(oa);CRT.pop(ref,None)
            print(it,ref,'NO SPOT',bad[:3],flush=True);log.append((it,ref,'nospot',str(bad[:3])))
    if not moved: break
rem={r:hvok(fps[r],hvpads(r)) for r in MOV};rem={k:v for k,v in rem.items() if v}
print('remaining pad violators',len(rem));[print(' ',k,v[:3]) for k,v in rem.items()]
b.Save(dst);json.dump(dict(log=log,rem={k:str(v) for k,v in rem.items()}),open(dst+'.hvplace.json','w'))
