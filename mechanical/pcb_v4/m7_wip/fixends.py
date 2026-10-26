# join track ends that stop just short of an own-net pad: add a segment to the pad centre (same layer, pad must be on it)
import pcbnew,sys;T=pcbnew.ToMM;F=pcbnew.FromMM
b=pcbnew.LoadBoard(sys.argv[1]);n=0;skip=0
pads={}
for f in b.GetFootprints():
  for p in f.Pads():
    if p.GetNetCode()>0: pads.setdefault(p.GetNetCode(),[]).append(p)
ends=[];ADDED=[];blocked=0
# clearance guard (2026-10-25): never add a join closer than CLR (default 0.2 mm, > every LV netclass clearance) to other-net copper.
import os;CLR=F(float(os.environ.get('FE_CLR','0.2')))
OTH=[p for f in b.GetFootprints() for p in f.Pads()]+[t for t in b.GetTracks()]
def clash(s,L,c):
  bb=s.GetBoundingBox();bb.Inflate(CLR+F(3))
  sh=s.GetEffectiveShape(L)
  for o in OTH:
    if o.GetNetCode()==c or not o.IsOnLayer(L): continue
    if not bb.Intersects(o.GetBoundingBox()): continue
    if sh.Collide(o.GetEffectiveShape(L),CLR): return True
  return False
for t in b.GetTracks():
  if t.Type()!=pcbnew.PCB_TRACE_T or t.IsLocked(): continue
  for e in (t.GetStart(),t.GetEnd()): ends.append((t,e))
EP={}
for t,e in ends: EP.setdefault((e.x,e.y,t.GetLayer()),[]).append(t)
for t,e in ends:
  L=t.GetLayer();c=t.GetNetCode()
  for p in pads.get(c,[]):
    if not p.IsOnLayer(L): continue
    sh=p.GetEffectivePolygon(L) if hasattr(p,'GetEffectivePolygon') else None
    if p.HitTest(e,0): break   # already inside
    if any(p.HitTest(o.GetEnd() if o.GetStart()==e else o.GetStart(),0) for o in EP.get((e.x,e.y,L),[])): break
    if p.HitTest(e,F(0.35)):
      pc=p.GetPosition()
      if T((pc-e).EuclideanNorm())>1.5: skip+=1;continue
      s=pcbnew.PCB_TRACK(b);s.SetStart(e);s.SetEnd(pc);s.SetWidth(t.GetWidth());s.SetLayer(L);s.SetNetCode(c)
      if clash(s,L,c): blocked+=1;break
      b.Add(s);ADDED.append(s);n+=1;break
print('joined ends',n,'skipped far',skip,'blocked by clearance guard',blocked)
b.Save(sys.argv[2])
import json;json.dump([x.m_Uuid.AsString() for x in ADDED],open(sys.argv[2]+'.added.json','w'))
