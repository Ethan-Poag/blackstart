import pcbnew,math,sys;T=pcbnew.ToMM;b=pcbnew.LoadBoard(sys.argv[1])
cor=[(13.5,y+s) for y in (28.2,35.81,43.44,78.01,85.63,93.25) for s in (-1,1)]
bad=[]
for t in b.GetTracks():
  if not t.GetNetClassName().startswith('HV'): continue
  for L in (pcbnew.F_Cu,pcbnew.B_Cu):
    if not t.IsOnLayer(L): continue
    s,e=t.GetStart(),t.GetEnd();ax,ay,bx,by=T(s.x),T(s.y),T(e.x),T(e.y);l=(bx-ax)**2+(by-ay)**2 or 1e-9
    w=T(t.GetWidth())/2
    for cx,cy in cor:
      u=max(0,min(1,((cx-ax)*(bx-ax)+(cy-ay)*(by-ay))/l));d=math.hypot(ax+u*(bx-ax)-cx,ay+u*(by-ay)-cy)-w
      if d<7.1: bad.append((round(d,2),t.GetNetname().split('/')[-1],b.GetLayerName(L),t.GetClass()[4:],cx,cy,t.IsLocked()))
bad=sorted(set(bad));print('slot-corner<7.1:',len(bad))
for x in bad[:40]: print(' ',x)
