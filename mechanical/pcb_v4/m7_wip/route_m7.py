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

# ---- M7-A: sheet-aware HV clearances (HVSHEET=1): foreign-chain HV copper 6.7 mm outer / 1.5 inner; same chain 1.5
if os.environ.get('HVSHEET')=='1':
    CHN={'GEN_L1':422,'GEN_L2':429,'GEN_L3':436,'GEN_N':443,'BUS_L1':448,'BUS_L2':455,'BUS_L3':462,'BUS_N':469}
    chain={}
    for ch,r0 in CHN.items():
        for nm,ni in b.GetNetsByName().items():
            if str(nm).endswith('/'+ch): chain[ni.GetNetCode()]=ch
        for i in range(4):
            for p in b.FindFootprintByReference('R%d'%(r0+i)).Pads():
                if p.GetNetCode()>0 and H.cls_of(p.GetNetCode()).startswith('HV'): chain.setdefault(p.GetNetCode(),ch)
    HVO=float(os.environ.get('HVO','6.7'));EDGE_HV=float(os.environ.get('EDGE_HV','8.0'))
    _hv=open('/workspace/m7/hvrules.py').read();_g={'b':b,'pcbnew':pcbnew}
    import cmath as _cm,math as _m;_g.update(cmath=_cm,math=_m)
    exec(_hv[_hv.index('CH={'):_hv.index('def geoms')].replace("F={f.GetReference():f for f in b.GetFootprints()}","F={f.GetReference():f for f in b.GetFootprints()}"),_g)
    RQ={}
    for a in _g['node']:
        d={}
        for c2 in _g['node']:
            if c2==a: continue
            r=_g['req'](a,c2,True)[0]+0.1   # +0.1 mm margin
            if r<=1.6: continue
            d.setdefault(round(r,1),[]).append(c2)
        RQ[a]=d
    # M7: reviewer hvsheet model - HV-domain ~0 V nets (GND_AC, CT, taps, ADE) need creep(|V(node)|) from each divider node
    import sys as _s;_s.path.insert(0,'/tmp/rv');from common import domains as _dom
    _hvd,_ctd,_,_=_dom(b);_nm2c={str(k):v.GetNetCode() for k,v in b.GetNetsByName().items()}
    _lv=[_nm2c[n] for n in _hvd if n in _nm2c and _nm2c[n] not in _g['node'] and n not in _ctd]
    _lv=[_nm2c[n] for n in _hvd if n in _nm2c and _nm2c[n] not in _g['node']]
    def _creep(v):
        T=[(0,0.0),(250,2.5),(320,3.2),(400,4.0),(500,5.0),(630,6.3),(800,8.0),(1000,10.0)]
        for (a0,x),(c0,y) in zip(T,T[1:]):
            if v<=c0: return x+(y-x)*(v-a0)/(c0-a0)
        return 10.0
    for a in _g['node']:
        ch,k=_g['node'][a] if isinstance(_g['node'][a],tuple) else (None,None)
        try: va=abs(_g['V'](a))
        except Exception: continue
        if va<1: continue
        r=round(_creep(va)+0.15,1)
        if r>1.6: RQ.setdefault(a,{}).setdefault(r,[]).extend(_lv)
        for c2 in _lv: RQ.setdefault(c2,{}).setdefault(r,[]).append(a)
    def free_map(code,w,win,extra_clear=0.0,allow_layers=(0,1,2)):
        y0,y1,x0,x1=win;lab_w=H.LAB[:,y0:y1,x0:x1];me=code+1;cl=H.cls_of(code)
        other=(lab_w!=0)&(lab_w!=me)
        allhv=np.isin(lab_w,list((H.HVN|H.DIVN)-{me}))&other
        mych=chain.get(code)
        same=allhv
        nrm=other&~allhv
        own_c=H.CLS.get(cl,H.CLS["Default"])[1]
        dn,ds=H.disk_dist(nrm),H.disk_dist(same)
        # node-aware: df = min over buckets of (dist - required) + HVO  (so test df>HVO+... == dist>req+...)
        df=np.full(lab_w.shape,1e3,np.float32)
        if code in RQ:
            for rq,cs in RQ[code].items():
                m=np.isin(lab_w,[c+1 for c in cs])&other
                if m.any(): df=np.minimum(df,H.disk_dist(m)-rq+HVO)
        else:
            df=H.disk_dist(allhv)
        free=np.zeros(lab_w.shape,bool);ishv=cl.startswith('HV')
        for l in range(3):
            outer=H.OUTER[l];hw=w/2
            c_n=((3.0 if outer else 1.5) if cl=='HV_LINE' else 1.5) if ishv else max(own_c,0.12)+extra_clear
            c_f=(HVO if outer else -1e9) if ishv else (3.0 if outer else 1.5)
            c_s=1.5
            mn=H.HV_MARGIN if ishv else H.MARGIN
            free[l]=(dn[l]>c_n+hw+mn)&(ds[l]>c_s+hw+H.HV_MARGIN)&(df[l]>c_f+hw+H.HV_MARGIN)
            if l not in allow_layers: free[l]=False
        if ishv:
            yy=H.Y0+np.arange(y0,y1)*H.R;xx=H.X0+np.arange(x0,x1)*H.R
            de=np.minimum.outer(np.minimum(yy-(-15.27),194.73-yy),np.minimum(xx-(-3.72),280.28-xx))
            eok=de>EDGE_HV+w/2+0.1
            free&=eok[None]
            # J28/J29 slot zone: HV line exits only on inner layers (slot-end creepage, compliance ruling 2)
            # M7: slot-corner rule (lead): other-phase HV outer copper/vias >=7.1 mm from J28/J29 slot-end corners;
            # own-phase (adjacent pin's phase): >=3.62 mm (3.62 + 3.48 corner->other pad = 7.1 creepage)
            import json as _j
            _PH=_j.load(open('/workspace/m7/phase.json'));_myph=_PH.get(H.NAME_OF[code] if hasattr(H,'NAME_OF') else NAMES.get(code,''),None)
            SLOTS=((27.195,'GEN_N','GEN_L3'),(34.815,'GEN_L3','GEN_L2'),(42.435,'GEN_L2','GEN_L1'),(77.013,'BUS_N','BUS_L3'),(84.6325,'BUS_L3','BUS_L2'),(92.252,'BUS_L2','BUS_L1'))
            def _szm(rad):
                m=np.zeros((len(yy),len(xx)),bool)
                for _cy,_a,_b in SLOTS:
                    r=(3.62 if _myph in (_a,_b) else 7.1)+rad+0.15
                    for _s in (-1,1): m|=np.hypot.outer(yy-(_cy+_s),xx-13.5)<r
                return m|np.outer(((yy>20)&(yy<49))|((yy>70)&(yy<99)),xx<13.6)
            sz=_szm(w/2)
            for l in range(3):
                if H.OUTER[l] and not os.environ.get("SLOTOFF"): free[l]&=~sz
        free&=~H.BLK[:,y0:y1,x0:x1];free|=(lab_w==me)
        vd=H.HV_VIA_D if ishv else H.VIA_D;c_v=1.5 if ishv else max(own_c,0.12)
        vfree=np.ones(lab_w.shape[1:],bool);vfree_nopad=np.ones(lab_w.shape[1:],bool)
        for l in range(3):
            cf=(HVO if ishv else 3.0) if H.OUTER[l] else (-1e9 if ishv else 1.5)
            vfree&=(dn[l]>c_v+vd/2+0.1)&(ds[l]>1.5+vd/2+H.HV_MARGIN)&(df[l]>cf+vd/2+H.HV_MARGIN)
            vfree_nopad&=(dn[l]>c_v+H.BGA_VIA_D/2+H.MARGIN)&(ds[l]>1.5+H.BGA_VIA_D/2)&(df[l]>cf+H.BGA_VIA_D/2)
        vfree&=~H.VBLK[y0:y1,x0:x1]
        if ishv:
            szv=_szm(vd/2)
            vfree&=(de>EDGE_HV+vd/2+0.1)&~szv
        return free,vfree,(dn,ds,df,vfree_nopad)
    H.free_map=free_map

# ---- M7 step1: stub-bug fix. Source = tree pads + only the own-net copper CONNECTED to them (3D label, vias join layers).
import inspect as _insp, scipy.ndimage as _ndi
_src=_insp.getsource(H.route_net)
_src=_src.replace("srcm = (src | own_new_copper(code, win)) & ~tgt","srcm = _conn_src(code, win, src) & ~tgt")
def _conn_src(code,win,src):
    y0,y1,x0,x1=win
    own=(H.LAB[:,y0:y1,x0:x1]==code+1)|src
    lab,n=_ndi.label(own,structure=_ndi.generate_binary_structure(3,1))
    ids=np.unique(lab[src&own]);ids=ids[ids>0]
    return np.isin(lab,ids)
H._conn_src=_conn_src
exec(compile(_src,'route_net_m7','exec'),H.__dict__)
NAMES={c:n.GetNetname() for c,n in b.GetNetsByNetcode().items()}
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
        if it[0]=="pad" and it[1]==c:isl.setdefault(fd(i),[]).append((it[2],it[3]))
    rep=[]
    for g in isl.values():
        (ref,num),q=g[0][0].rsplit(".",1),g[0][1]
        cand=[p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber()==num]
        rep+=sorted(cand,key=lambda p:(TM(p.GetPosition().x)-q[0])**2+(TM(p.GetPosition().y)-q[1])**2)[:1]
    _ex=[e for e in os.environ.get('EXCL','').split(',') if e]
    rep=[p for p in rep if p.GetParentFootprint().GetReference() not in _ex]
    if len(rep)<2:continue
    xs=[TM(p.GetPosition().x) for p in rep];ys=[TM(p.GetPosition().y) for p in rep]
    jobs.append((max(xs)-min(xs)+max(ys)-min(ys),name,c,rep))
jobs.sort(key=lambda j:j[0])
# AVOID="net1,net2:1.2" -> keep the routed nets this many mm (extra) from those nets' copper (crosstalk separation)
if os.environ.get('AVOID'):
    import scipy.ndimage as _nd
    _an,_ad=os.environ['AVOID'].split(':');_r=int(round(float(_ad)/H.R))
    _st=_nd.iterate_structure(_nd.generate_binary_structure(2,1),_r)
    for _a in _an.split(','):
        _cs=[c for c,n in NAMES.items() if n==_a or n.endswith('/'+_a)]
        for _c in _cs:
            for _l in range(3): H.BLK[_l]|=_nd.binary_dilation(H.LAB[_l]==_c+1,structure=_st)
    print('AVOID applied',_an,_ad,flush=True)
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
per2,_,_=uf.analyze(b)
ver={name:per2.get(name,0) for name in res}
tok=sum(1 for n in res if ver[n]==0)
print("VERIFIED (uf copper islands): truly complete",tok,"of",len(res),"; router-claimed ok",ok,"; claimed-ok but still open",sum(1 for n in res if res[n]=='ok' and ver[n]>0),flush=True)
json.dump(dict(res=res,verified_open=ver,fail=fail,stitch=nst,stitch_fail=nsf),open(dst+".route.json","w"))
