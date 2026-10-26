"""BCR-11: NPTH 9.5 at (12.3,-7.5), move D5 + 4 GND vias, B keep-outs (D14 + 5x10 tongue -y), release H4 PE_BOSS_RING. usage in out"""
import pcbnew,sys,math;T=pcbnew.ToMM;M=pcbnew.VECTOR2I_MM
b=pcbnew.LoadBoard(sys.argv[1]);C=(12.3,-7.5)
from shapely.geometry import Point,box,Polygon
def crt(fp):
    s=fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
    if s.OutlineCount()==0: bb=fp.GetBoundingBox(False);return box(T(bb.GetLeft()),T(bb.GetTop()),T(bb.GetRight()),T(bb.GetBottom()))
    o=s.Outline(0);return Polygon([(T(o.CPoint(i).x),T(o.CPoint(i).y)) for i in range(o.PointCount())])
KO=Point(C).buffer(7.0).union(box(C[0]-2.5,-15.27,C[0]+2.5,C[1]))
for z in b.Zones():
    if z.GetIsRuleArea() and z.GetDoNotAllowFootprints() and z.IsOnLayer(pcbnew.B_Cu):
        print('RA',z.GetZoneName(),[round(T(v),1) for v in (z.GetBoundingBox().GetLeft(),z.GetBoundingBox().GetTop(),z.GetBoundingBox().GetRight(),z.GetBoundingBox().GetBottom())]);o=z.Outline().Outline(0);KO=KO.union(Polygon([(T(o.CPoint(i).x),T(o.CPoint(i).y)) for i in range(o.PointCount())]))
# 1 vias
for t in list(b.GetTracks()):
    if t.GetClass()=='PCB_VIA' and t.GetNetname()=='GND' and math.dist((T(t.GetPosition().x),T(t.GetPosition().y)),C)<6: b.Delete(t)
# 2 D5
d5=b.FindFootprintByReference('D5');from shapely.strtree import STRtree
others=[crt(f) for f in b.GetFootprints() if (f.IsFlipped() or any(p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD for p in f.Pads())) and f.GetReference()!='D5' and f.GetPosition().x<M(70,0).x]
pads=[(Point(T(p.GetPosition().x),T(p.GetPosition().y)),p.GetNetname()) for f in b.GetFootprints() if f.GetReference()!='D5' and f.GetPosition().x<M(70,0).x for p in f.Pads() if p.IsOnLayer(pcbnew.B_Cu)]
best=(0,76.01,78.74,90)  # found by search near D11.2 (+5V), see report
print('D5 ->',best);d5.SetPosition(M(best[1],best[2]));d5.SetOrientationDegrees(best[3])
# 3 NPTH footprint H5 (board only)
fp=pcbnew.FOOTPRINT(b);fp.SetReference('H5');fp.SetValue('PE_BOSS_NPTH_9.5')
fp.SetFPID(pcbnew.LIB_ID('genctl','PE_BOSS_NPTH_9.5'));fp.SetBoardOnly(True);fp.SetExcludedFromBOM(True);fp.SetExcludedFromPosFiles(True)
p=pcbnew.PAD(fp);p.SetAttribute(pcbnew.PAD_ATTRIB_NPTH);p.SetShape(pcbnew.PAD_SHAPE_CIRCLE);p.SetSize(M(9.5,9.5));p.SetDrillSize(M(9.5,9.5))
p.SetLayerSet(pcbnew.LSET.AllCuMask());p.SetNumber('');fp.Add(p);b.Add(fp);fp.SetPosition(M(*C));fp.SetLocked(True)
fp.Reference().SetVisible(False)
# 4 keep-out rule areas on B (no footprints) : circle D14 + tongue box
def ra(name,poly,layers):
    z=pcbnew.ZONE(b);z.SetIsRuleArea(True);z.SetZoneName(name);z.SetLayerSet(layers)
    z.SetDoNotAllowFootprints(True);z.SetDoNotAllowPads(True);z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(False);z.SetDoNotAllowCopperPour(False)
    o=z.Outline();o.NewOutline()
    for x,y in poly: o.Append(M(x,y))
    b.Add(z)
B=pcbnew.LSET();B.AddLayer(pcbnew.B_Cu)
ra('PE_LUG_D14_B',[(C[0]+7*math.cos(2*math.pi*k/48),C[1]+7*math.sin(2*math.pi*k/48)) for k in range(48)],B)
ra('PE_LUG_TONGUE_5x10_B',[(C[0]-2.5,C[1]),(C[0]+2.5,C[1]),(C[0]+2.5,C[1]-10),(C[0]-2.5,C[1]-10)],B)
# 5 release H4 ring
for z in list(b.Zones()):
    if z.GetIsRuleArea() and z.GetZoneName()=='PE_BOSS_RING': b.Delete(z);print('released PE_BOSS_RING')
b.Save(sys.argv[2])
