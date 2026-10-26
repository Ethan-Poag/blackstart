import pcbnew,math,sys,json;T=pcbnew.ToMM;b=pcbnew.LoadBoard(sys.argv[1])
PH=json.load(open('/workspace/m7/phase.json'))
SL=((27.195,'GEN_N','GEN_L3'),(34.815,'GEN_L3','GEN_L2'),(42.435,'GEN_L2','GEN_L1'),(77.013,'BUS_N','BUS_L3'),(84.6325,'BUS_L3','BUS_L2'),(92.252,'BUS_L2','BUS_L1'))
OUT=(pcbnew.F_Cu,pcbnew.B_Cu);bad=[]
def chk(name,poly_d,tag,lk):
  ph=PH.get(name)
  if ph is None: return
  for cy,a,c in SL:
    for s in (-1,1):
      req=3.62 if ph in (a,c) else 7.1
      d=poly_d(13.5,cy+s)
      if d<req-1e-3: bad.append((round(d,3),req,name.split('/')[-1],tag,(13.5,round(cy+s,3)),lk))
for t in b.GetTracks():
  n=t.GetNetname()
  if n not in PH: continue
  for L in OUT:
    if not t.IsOnLayer(L): continue
    sh=t.GetEffectiveShape(L)
    chk(n,lambda x,y:T(sh.GetClearance(pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y)),0))) if False else T(int(math.sqrt(max(0,sh.SquaredDistance(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))))))),t.GetClass()[4:]+'@'+b.GetLayerName(L),t.IsLocked())
for f in b.GetFootprints():
  if f.GetReference() in ('J28','J29'): continue
  for p in f.Pads():
    n=p.GetNetname()
    if n not in PH: continue
    for L in OUT:
      if not p.IsOnLayer(L): continue
      sh=p.GetEffectiveShape(L)
      chk(n,lambda x,y:T(int(math.sqrt(max(0,sh.SquaredDistance(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))))))),f.GetReference()+'.'+p.GetNumber()+'@'+b.GetLayerName(L),f.IsLocked())
bad=sorted(set(bad));print('slot-corner violations:',len(bad),'unlocked',sum(1 for x in bad if not x[5]))
for x in bad: print(' ',x)
