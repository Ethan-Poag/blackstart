import pcbnew,sys;T=pcbnew.ToMM
b=pcbnew.LoadBoard(sys.argv[1]);lib='/workspace/genctl/kicad/genctl/genctl.pretty'
info=[]
for i in range(1,7):
  o=b.FindFootprintByReference('RV%d'%i);pads={p.GetNumber():p for p in o.Pads()}
  info.append(dict(r='RV%d'%i,mid=(pads['1'].GetPosition()+pads['2'].GetPosition())/2,nets={k:p.GetNetCode() for k,p in pads.items()},
    fields={f.GetName():f.GetText() for f in o.GetFields()},flip=o.IsFlipped(),ang=o.GetOrientationDegrees(),path=pcbnew.KIID_PATH(o.GetPath().AsString()),lock=o.IsLocked()))
for i in range(1,7): b.Delete(b.FindFootprintByReference('RV%d'%i))
for d in info:
  n=pcbnew.FootprintLoad(lib,'TMOV20RP_P7.5mm_inline');b.Add(n)
  n.SetReference(d['r']);n.SetValue('TMOV20RP460E')
  for k,v in d['fields'].items():
    if k not in('Reference','Value','Footprint'): n.SetField(k,v)
  n.SetField('LCSC','C3260792');n.SetField('MPN','TMOV20RP460EL2T7');n.SetField('Manufacturer','Littelfuse')
  n.SetFPID(pcbnew.LIB_ID('genctl','TMOV20RP_P7.5mm_inline'))
  if d['flip']: n.Flip(n.GetPosition(),False)
  n.SetOrientationDegrees(d['ang']);n.SetPath(d['path']);n.SetLocked(d['lock'])
  for p in n.Pads(): p.SetNet(b.FindNet(d['nets'][p.GetNumber()]))
  np={p.GetNumber():p for p in n.Pads()};n.Move(d['mid']-(np['1'].GetPosition()+np['2'].GetPosition())/2)
  print(d['r'],[(round(T(p.GetPosition().x),2),round(T(p.GetPosition().y),2),p.GetNetname().split('/')[-1]) for p in n.Pads()])
b.Save(sys.argv[2])
