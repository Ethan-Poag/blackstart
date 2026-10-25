import pcbnew,json,sys,collections
b=pcbnew.LoadBoard(sys.argv[1]); d=json.load(open(sys.argv[2]))
TYPES={'clearance','hole_clearance','shorting_items','tracks_crossing','copper_edge_clearance','via_dangling','track_dangling','solder_mask_bridge','hole_to_hole','annular_width','drill_out_of_range','courtyards_overlap'}
items={t.m_Uuid.AsString():t for t in b.GetTracks()}
rm={};unfixed=[]
for v in d['violations']:
    if v['severity']!='error': continue
    cand=[items[i['uuid']] for i in v['items'] if i['uuid'] in items and not items[i['uuid']].IsLocked()]
    if not cand: unfixed.append((v['type'],v['description'][:80],[i['description'][:60] for i in v['items']])); continue
    # prefer tracks over vias, shortest first
    cand.sort(key=lambda t:(t.GetClass()=="PCB_VIA", t.GetLength() if t.GetClass()!="PCB_VIA" else 0))
    t=cand[0]; rm[t.m_Uuid.AsString()]=t
for t in rm.values(): b.Remove(t)
print('removed',len(rm),'unfixable(locked)',len(unfixed))
for u in unfixed: print(' ',u)
b.Save(sys.argv[3])
