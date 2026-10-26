# DRC rule-order proof: add GEN_L1 and GEN_L2 0.5 mm F.Cu tracks 6.0 mm apart (between 5.5 and 6.6) on a COPY of the board.
# usage: drutest.py board.kicad_pcb out.kicad_pcb ; then run kicad-cli DRC on out with the repo .kicad_pro/.kicad_dru.
import pcbnew,sys;F=pcbnew.FromMM
b=pcbnew.LoadBoard(sys.argv[1]);N=b.GetNetsByName()
net=lambda s:[v for k,v in N.items() if str(k).endswith('/'+s)][0]
for nm,y in (('GEN_L1',60.0),('GEN_L2',66.5)):
  t=pcbnew.PCB_TRACK(b);t.SetStart(pcbnew.VECTOR2I(F(120),F(y)));t.SetEnd(pcbnew.VECTOR2I(F(125),F(y)));t.SetWidth(F(0.5));t.SetLayer(pcbnew.F_Cu);t.SetNet(net(nm));b.Add(t)
b.Save(sys.argv[2])
