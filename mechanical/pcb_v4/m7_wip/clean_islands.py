import pcbnew,sys;b=pcbnew.LoadBoard(sys.argv[1]);b.BuildConnectivity();cn=b.GetConnectivity()
only=sys.argv[3] if len(sys.argv)>3 else 'HV'
seen=set();dl=[];lk=0
for t in b.GetTracks():
    if t.m_Uuid.AsString() in seen: continue
    if only=='HV' and not t.GetNetClassName().startswith('HV'): continue
    cl=[t]+[x for x in cn.GetConnectedItems(t,[pcbnew.PCB_TRACE_T,pcbnew.PCB_VIA_T,pcbnew.PCB_ARC_T,pcbnew.PCB_PAD_T,pcbnew.PCB_ZONE_T]) ]
    for x in cl: seen.add(x.m_Uuid.AsString())
    if any(x.GetClass()=='PAD' for x in cl) or any(x.GetClass()=='ZONE' for x in cl): continue
    tr=[x for x in cl if x.GetClass() in('PCB_TRACK','PCB_VIA','PCB_ARC')]
    if any(x.IsLocked() for x in tr): lk+=1;continue
    dl+=tr
u={x.m_Uuid.AsString():x for x in dl}
for x in u.values(): b.Delete(x)
print('deleted',len(u),'padless items; skipped locked islands',lk);b.Save(sys.argv[2])
