#!/usr/bin/env python3
"""M7 router driver (grid A* from handroute_v4). usage: route_m7.py in out [budget_s]
 env NETS=comma list of net-name suffixes (else all open non-HV, non-DIFF signal/power nets)
 CR1: nets in CTKEEP get a hard keep-out of CTCLR_OUT (outer) / CTCLR_IN (In2) mm around every CT-secondary pad
 Plane nets (GND, GND_AC, +3V3_SAFE, +3V3_AC): unconnected SMD pads get a short stub + via to the inner plane."""
import sys,os,time,math,json
src,dst=sys.argv[1],sys.argv[2];budget=float(sys.argv[3]) if len(sys.argv)>3 else 3000
sys.argv=[sys.argv[0],src,dst]
sys.path.insert(0,'/workspace/genctl/kicad/genctl/mechanical/pcb_v4')
import handroute_v4 as H, uf, pcbnew, numpy as np
b=H.b;TM=pcbnew.ToMM
CTKEEP=[s for s in os.environ.get('CTKEEP','').split(',') if s]
CO=float(os.environ.get('CTCLR_OUT','3.0'));CI=float(os.environ.get('CTCLR_IN','1.5'))
ctpads=[p for f in b.GetFootprints() if f.GetReference() in('T1','T2','T3','T4','J30') for p in f.Pads() if p.GetNetCode()>0]
def ct_block(on):
    yy,xx=np.ogrid[:H.H,:H.W]
    if not hasattr(ct_block,'m'):
        m=np.zeros(H.BLK.shape,bool);vm=np.zeros(H.VBLK.shape,bool)
        for p in ctpads:
            c=p.GetPosition();cx,cy=H.gx(TM(c.x)),H.gy(TM(c.y));r0=TM(max(p.GetSize().x,p.GetSize().y))/2
            for l,cl in ((0,CO),(1,CI),(2,CO)):
                rr=(r0+cl+0.2)/H.R;m[l]|=((yy-cy)**2+(xx-cx)**2)<=rr*rr
            rr=(r0+CO+0.6)/H.R;vm|=((yy-cy)**2+(xx-cx)**2)<=rr*rr
        ct_block.m=(m,vm);ct_block.save=None
    m,vm=ct_block.m
    if on: ct_block.save=(H.BLK.copy(),H.VBLK.copy());H.BLK|=m;H.VBLK|=vm
    else: H.BLK[:],H.VBLK[:]=ct_block.save
PLANE=('GND','GND_AC','+3V3_SAFE','+3V3_AC')
per,items,fd=uf.analyze(b)
codes={n.GetNetname():c for c,n in b.GetNetsByNetcode().items()}
want=[s for s in os.environ.get('NETS','').split(',') if s]
jobs=[]
for name,k in per.items():
    c=codes[name];cl=H.cls_of(c)
    if want and not any(name==w or name.endswith('/'+w) for w in want):continue
    if cl.startswith(("HV","DIFF")) and not want:continue
    if name in PLANE:continue
    isl={}
    for i,it in enumerate(items):
        if it[0]=="pad" and it[1]==c:isl.setdefault(fd(i),[]).append(it[2])
    rep=[]
    for g in isl.values():
        ref,num=g[0].rsplit(".",1)
        rep+=[p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber()==num][:1]
    if len(rep)<2:continue
    xs=[TM(p.GetPosition().x) for p in rep];ys=[TM(p.GetPosition().y) for p in rep]
    jobs.append((max(xs)-min(xs)+max(ys)-min(ys),name,c,rep))
jobs.sort(key=lambda j:j[0])
print("jobs",len(jobs),flush=True)
t0=time.time();ok=0;fail=[];res={}
for i,(hp,name,c,rep) in enumerate(jobs):
    if time.time()-t0>budget:fail.append(name+" (budget)");continue
    ck=any(name.endswith('/'+s) or name==s for s in CTKEEP)
    if ck: ct_block(True)
    try:
        r=H.route_net(c,order=list(rep),margin=float(os.environ.get('MG','8'))+min(hp*0.1,12),viac=float(os.environ.get('VC','60')))
    except Exception as e:
        r=dict(ok=False,failed=[str(e)[:60]])
    if ck: ct_block(False)
    if r and r["ok"]:ok+=1;res[name]='ok'
    else:
        H.ripup([c]);fail.append(name);res[name]='fail'
    if i%25==0:print(i,round(time.time()-t0),ok,len(fail),flush=True)
for t in H.made:t.SetLocked(False)
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.Save(dst)
# plane stitching
nst=0;nsf=0
if os.environ.get('STITCH','1')=='1':
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    per,items,fd=uf.analyze(b)
    for pn in PLANE:
        if pn not in codes: continue
        c=codes[pn]
        comp={}
        for i,it in enumerate(items):
            if it[1]==c: comp.setdefault(fd(i),[]).append(it)
        big=max(comp.values(),key=lambda l:sum(1 for x in l if x[0]=="zone"))
        bigroot=fd(items.index(big[0]))
        for root,l in comp.items():
            if root==bigroot: continue
            for it in l:
                if it[0]!="pad":continue
                ref,num=it[2].rsplit(".",1);f=b.FindFootprintByReference(ref)
                p=[q for q in f.Pads() if q.GetNumber()==num][0]
                if p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD:continue
                li=0 if p.IsOnLayer(pcbnew.F_Cu) else 2
                px,py=TM(p.GetPosition().x),TM(p.GetPosition().y)
                win=H.window([p],4.0)
                free,vfree,_=H.free_map(c,0.3,win)
                y0,y1,x0,x1=win;best=None
                for rr in np.arange(0.7,3.0,0.1):
                    for a in np.arange(0,2*math.pi,math.pi/16):
                        vx,vy=px+rr*math.cos(a),py+rr*math.sin(a)
                        gi,gj=int(round(H.gy(vy)))-y0,int(round(H.gx(vx)))-x0
                        if not(0<=gi<y1-y0 and 0<=gj<x1-x0) or not vfree[gi,gj]:continue
                        okl=True
                        for t in np.linspace(0,1,int(rr/0.05)+2):
                            qi,qj=int(round(H.gy(py+t*(vy-py))))-y0,int(round(H.gx(px+t*(vx-px))))-x0
                            if not free[li,qi,qj]:okl=False;break
                        if okl:best=(float(vx),float(vy));break
                    if best:break
                if best:
                    H.add_track(c,li,(float(px),float(py)),best,0.3);H.add_via(c,best,H.VIA_D,H.VIA_DR);nst+=1
                else:nsf+=1
                break
print("stitch vias",nst,"stitch fail",nsf)
for t in H.made:t.SetLocked(False)
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.Save(dst)
b.BuildConnectivity();print("done ok",ok,"fail",len(fail),"unconnected",b.GetConnectivity().GetUnconnectedCount(True),flush=True)
json.dump(dict(res=res,fail=fail,stitch=nst,stitch_fail=nsf),open(dst+".route.json","w"))
