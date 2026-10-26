"""READ-ONLY pcbnew export of hazardous-live outer-layer copper (AC-metering domain) for finger_check.py.
Live set (ASSUMED conservative): every net under '/AC metering', GND_AC, +3V3_AC, Net-(U22-CT), Net-(U23-CT).
Outer layers only (F.Cu, B.Cu); inner copper is buried in FR4 and not touchable. Output: hv_copper.json (MEASURED from board file)."""
import pcbnew, json, os, math
H = os.path.dirname(os.path.abspath(__file__))
b = pcbnew.LoadBoard(os.path.join(H, "../../../pcb_v4/genctl_v4_handrouted.kicad_pcb"))
def live(n): return "/AC metering" in n or n in ("GND_AC", "+3V3_AC", "Net-(U22-CT)", "Net-(U23-CT)")
mm = pcbnew.ToMM; pts = []
for p in b.GetPads():
    n = p.GetNetname()
    if not live(n): continue
    c = p.GetPosition(); s = p.GetSize(); r = 0.5 * math.hypot(mm(s.x), mm(s.y))
    layers = [l for l in (pcbnew.F_Cu, pcbnew.B_Cu) if p.IsOnLayer(l)]
    for l in layers: pts.append([round(mm(c.x), 3), round(mm(c.y), 3), "F" if l == pcbnew.F_Cu else "B", round(r, 3), p.GetParentAsString() if hasattr(p, "GetParentAsString") else p.GetParent().GetReference(), n.split("/")[-1]])
for t in b.GetTracks():
    n = t.GetNetname()
    if not live(n): continue
    if t.GetClass() == "PCB_VIA":
        c = t.GetPosition(); w = mm(t.GetWidth(pcbnew.F_Cu))
        for side in "FB": pts.append([round(mm(c.x), 3), round(mm(c.y), 3), side, round(w / 2, 3), "via", n.split("/")[-1]])
        continue
    l = t.GetLayer()
    if l not in (pcbnew.F_Cu, pcbnew.B_Cu): continue
    a, e = t.GetStart(), t.GetEnd(); L = mm(math.hypot(e.x - a.x, e.y - a.y)); k = max(1, int(L / 0.5))
    for i in range(k + 1):
        x = mm(a.x + (e.x - a.x) * i / k); y = mm(a.y + (e.y - a.y) * i / k)
        pts.append([round(x, 3), round(y, 3), "F" if l == pcbnew.F_Cu else "B", round(mm(t.GetWidth()) / 2, 3), "track", n.split("/")[-1]])
json.dump({"source": "genctl_v4_handrouted.kicad_pcb (read-only)", "points": pts}, open(os.path.join(H, "hv_copper.json"), "w"))
print(len(pts))
