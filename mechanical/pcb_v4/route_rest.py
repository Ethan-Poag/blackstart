#!/usr/bin/env python3
"""M6 general LV router: numba grid A* from handroute_v4 on F/In2/B, every non-critical LV net with open
connections (union-find islands -> one pad each), shortest HPWL first. usage: route_rest.py in out [budget_s]"""
import sys,time,math,json
src,dst=sys.argv[1],sys.argv[2];budget=float(sys.argv[3]) if len(sys.argv)>3 else 3000
sys.argv=[sys.argv[0],src,dst]
import handroute_v4 as H, uf, pcbnew
b=H.b;TM=pcbnew.ToMM
per,items,fd=uf.analyze(b)
codes={n.GetNetname():c for c,n in b.GetNetsByNetcode().items()}
jobs=[]
for name,k in per.items():
    c=codes[name];cl=H.cls_of(c)
    if cl.startswith(("HV","DIFF")) or name in("GND","+3V3_SAFE","GND_AC","+3V3_AC"):continue
    pads=H.pads_of(c)
    # one pad per island
    isl={}
    for i,it in enumerate(items):
        if it[0]=="pad" and it[1]==c:isl.setdefault(fd(i),[]).append(it[2])
    rep=[]
    for g in isl.values():
        ref,num=g[0].rsplit(".",1)
        if all(TM(q.GetPosition().x)<60 for q in [pp for r_,n_ in (x.rsplit('.',1) for x in g) for pp in b.FindFootprintByReference(r_).Pads() if pp.GetNumber()==n_]):continue
        rep+=[p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber()==num][:1]
    if len(rep)<2:continue
    xs=[TM(p.GetPosition().x) for p in rep];ys=[TM(p.GetPosition().y) for p in rep]
    jobs.append((max(xs)-min(xs)+max(ys)-min(ys),name,c,rep))
jobs.sort(key=lambda j:j[0])
print("jobs",len(jobs),flush=True)
t0=time.time();ok=0;fail=[]
for i,(hp,name,c,rep) in enumerate(jobs):
    if time.time()-t0>budget:fail.append(name+" (budget)");continue
    try:
        r=H.route_net(c,order=list(rep),margin=float(__import__('os').environ.get('MG','6'))+min(hp*0.1,10),viac=float(__import__('os').environ.get('VC','120')))
    except Exception as e:
        r=dict(ok=False,failed=[str(e)[:60]])
    if r and r["ok"]:ok+=1
    else:
        H.ripup([c]);fail.append(name)
    if i%25==0:print(i,round(time.time()-t0),ok,len(fail),flush=True)
for t in H.made:t.SetLocked(False)
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.Save(dst)
b.BuildConnectivity();print("done ok",ok,"fail",len(fail),"unconnected",b.GetConnectivity().GetUnconnectedCount(True),flush=True)
json.dump(fail,open(dst+".fail.json","w"))
