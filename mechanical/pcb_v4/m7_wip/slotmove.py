import pcbnew,json,math,sys;T=pcbnew.ToMM;F=pcbnew.FromMM
b=pcbnew.LoadBoard(sys.argv[1]);PH=json.load(open('phase.json'))
SL=((28.2,'GEN_N','GEN_L3'),(35.81,'GEN_L3','GEN_L2'),(43.44,'GEN_L2','GEN_L1'),(78.01,'BUS_N','BUS_L3'),(85.63,'BUS_L3','BUS_L2'),(93.25,'BUS_L2','BUS_L1'))
def bad(f,m=0.4):
  for p in f.Pads():
    ph=PH.get(p.GetNetname())
    if not ph: continue
    bb=p.GetBoundingBox()
    if T(bb.GetLeft())<13.6+m: pass
    for cy,a,c in SL:
      for s in(-1,1):
        dx=max(T(bb.GetLeft())-13.5,0,13.5-T(bb.GetRight()));dy=max(T(bb.GetTop())-cy-s,0,cy+s-T(bb.GetBottom()))
        if math.hypot(dx,dy)<(3.62 if ph in(a,c) else 7.1)+m: return True
  return False
def cy(f):
  return f.GetCourtyard(pcbnew.F_CrtYd if not f.IsFlipped() else pcbnew.B_CrtYd)
def overlap(f):
  me=cy(f)
  for g in b.GetFootprints():
    if g.GetReference()==f.GetReference() or g.IsFlipped()!=f.IsFlipped(): continue
    o=cy(g)
    if me.OutlineCount() and o.OutlineCount() and me.Collide(o): return g.GetReference()
  # also HV other-phase pad distance >=6.6
  for g in b.GetFootprints():
    if g is f: continue
    for q in g.Pads():
      for p in f.Pads():
        a,c=PH.get(p.GetNetname()),PH.get(q.GetNetname())
        if a and c and a!=c and p.GetBoundingBox().Distance(q.GetPosition()) if False else False: pass
  return None
def hvnear(f,req=4.8):
  me=f.GetReference()
  for p in f.Pads():
    a=PH.get(p.GetNetname())
    if not a: continue
    for g,q in HVP:
      if g.GetReference()==me: continue
      if 1:
        if PH.get(q.GetNetname()) not in (None,a) and (g.IsFlipped()==f.IsFlipped() or q.GetAttribute()==pcbnew.PAD_ATTRIB_PTH):
          d=T((p.GetPosition()-q.GetPosition()).EuclideanNorm())-(T(max(p.GetSize().x,p.GetSize().y))+T(max(q.GetSize().x,q.GetSize().y)))/2
          if d<req: return True
  return False
HVP=[(g,q) for g in b.GetFootprints() for q in g.Pads() if PH.get(q.GetNetname())]
out={}
for g in b.GetFootprints(): g.BuildCourtyardCaches()
for ref in sys.argv[3].split(','):
  f=b.FindFootprintByReference(ref);p0=f.GetPosition();best=None
  for r in [i*0.25 for i in range(1,41)]:
    for ang in range(0,360,15):
      d=F(r);f.SetPosition(pcbnew.VECTOR2I(p0.x+int(d*math.cos(math.radians(ang))),p0.y+int(d*math.sin(math.radians(ang)))))
      f.BuildCourtyardCaches() if hasattr(f,'BuildCourtyardCaches') else None
      if not bad(f) and not overlap(f) and not hvnear(f): best=f.GetPosition();break
    if best: break
  if best: f.SetPosition(best);out[ref]=(round(T(p0.x),3),round(T(p0.y),3),round(T(best.x),3),round(T(best.y),3))
  else: f.SetPosition(p0);out[ref]='NO SPOT'
  print(ref,out[ref])
b.Save(sys.argv[2]);json.dump(out,open(sys.argv[2]+'.move.json','w'))
