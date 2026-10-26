# Fix hole_to_hole: a same-net via too close to a PTH pad is removed and its tracks are re-ended on the PTH pad centre
# (the PTH pad is on every copper layer). usage: h2h.py in.kicad_pcb drc.json out.kicad_pcb
import pcbnew,sys,json;T=pcbnew.ToMM;F=pcbnew.FromMM
b=pcbnew.LoadBoard(sys.argv[1]);d=json.load(open(sys.argv[2]))
U={}
for t in b.GetTracks(): U[t.m_Uuid.AsString()]=t
P={}
for f in b.GetFootprints():
  for p in f.Pads(): P[p.m_Uuid.AsString()]=p
done=set();log=[]
for x in d['violations']:
  if x['type']!='hole_to_hole': continue
  ids=[i['uuid'] for i in x['items']]
  if any(i in done for i in ids): continue
  vias=[U[i] for i in ids if i in U and U[i].GetClass()=='PCB_VIA'];pads=[P[i] for i in ids if i in P]
  if len(vias)==2 and vias[0].GetNetCode()==vias[1].GetNetCode():   # duplicate/overlapping via
    v,keep=vias[1],vias[0]
    if v.m_Uuid.AsString() in done or keep.m_Uuid.AsString() in done: continue
    tgt=keep.GetPosition();pad=None
  elif len(vias)==1 and len(pads)==1 and vias[0].GetNetCode()==pads[0].GetNetCode():
    v,pad=vias[0],pads[0];tgt=pad.GetPosition()
    if v.m_Uuid.AsString() in done: continue
  else:
    log.append(('SKIP',x['description'][-30:]));continue
  vp=v.GetPosition();n=0
  if pad is not None:
    inner=[t for t in b.GetTracks() if t.Type()==pcbnew.PCB_TRACE_T and t.GetNetCode()==v.GetNetCode() and not pad.IsOnLayer(t.GetLayer()) and ((t.GetStart()-vp).EuclideanNorm()<F(0.01) or (t.GetEnd()-vp).EuclideanNorm()<F(0.01))]
    if inner:   # pad absent on that layer: shift the via away from the pad instead of removing it
      act=float(x['description'].split('actual ')[1].split(' mm')[0]);need=F(0.25+0.06-act)
      dv=vp-pad.GetPosition();L=dv.EuclideanNorm();np_=pcbnew.VECTOR2I(int(vp.x+dv.x*need/L),int(vp.y+dv.y*need/L))
      for t in b.GetTracks():
        if t.GetNetCode()!=v.GetNetCode() or t.Type()!=pcbnew.PCB_TRACE_T: continue
        if (t.GetStart()-vp).EuclideanNorm()<F(0.01): t.SetStart(np_)
        if (t.GetEnd()-vp).EuclideanNorm()<F(0.01): t.SetEnd(np_)
      v.SetPosition(np_);done.add(v.m_Uuid.AsString());log.append(('shifted',v.GetNetname()[-14:],round(T(need),3)));continue
  for t in b.GetTracks():
    if t.Type()!=pcbnew.PCB_TRACE_T: continue
    if t.GetNetCode()!=v.GetNetCode(): continue
    for s in ('S','E'):
      e=t.GetStart() if s=='S' else t.GetEnd()
      if (e-vp).EuclideanNorm()<F(0.01):
        if pad is not None and not pad.IsOnLayer(t.GetLayer()): log.append(('PADLAYER',T(vp)));continue
        (t.SetStart if s=='S' else t.SetEnd)(tgt);n+=1
  nm=v.GetNetname()[-14:];done.add(v.m_Uuid.AsString());b.Delete(v);log.append(('fixed',nm,[round(a,2) for a in T(vp)],n))
for l in log: print(l)
print('handled vias',len(done));pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.Save(sys.argv[3])
