import pcbnew,sys,math;T=pcbnew.ToMM;M=pcbnew.VECTOR2I_MM
b=pcbnew.LoadBoard(sys.argv[1]);ref=pcbnew.LoadBoard('a9.kicad_pcb')
h=b.FindFootprintByReference('H5')
if h: b.Delete(h)
for z in list(b.Zones()):
    if z.GetIsRuleArea() and z.GetZoneName().startswith('PE_LUG'): b.Delete(z)
if not any(z.GetIsRuleArea() and z.GetZoneName()=='PE_BOSS_RING' for z in b.Zones()):
    for z in ref.Zones():
        if z.GetIsRuleArea() and z.GetZoneName()=='PE_BOSS_RING': n=z.Duplicate();b.Add(n)
r5=ref.FindFootprintByReference('D5');d5=b.FindFootprintByReference('D5')
d5.SetPosition(r5.GetPosition());d5.SetOrientationDegrees(r5.GetOrientationDegrees())
C=(12.3,-7.5);g=b.FindNet('GND');k=0
for t in ref.GetTracks():
    if t.GetClass()=='PCB_VIA' and t.GetNetname()=='GND' and math.dist((T(t.GetPosition().x),T(t.GetPosition().y)),C)<6:
        v=t.Duplicate();b.Add(v);v.SetNet(g);k+=1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
print('reverted; vias restored',k,'D5',T(d5.GetPosition().x),T(d5.GetPosition().y));b.Save(sys.argv[2])
