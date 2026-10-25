"""Merge a Quilter candidate back onto the master board: NEW copper on plain low-voltage nets only.

  python3 quilter/merge_back.py genctl_v4_handrouted.kicad_pcb <quilter_candidate>.kicad_pcb w6/merged.kicad_pcb
  kicad-cli pcb drc --severity-error -o w6/merged_drc.rpt w6/merged.kicad_pcb

Copies a track/via from the candidate only when ALL of these hold:
  - it is not already on the master (same net, layer, geometry within 1 um);
  - its net is in netclass Default on the MASTER (so not HV_LINE/HV_LINE_DIV/DIFF100/DIFF90/PWR) and not in CRITICAL;
  - it does not touch the 600 V box (x < 60 mm, 11 < y < 162) or the barrier strip (x < 73 mm);
  - its net exists on the master (names are matched by full name, then by last path component).
Quilter's pours are ignored; master zones are refilled.  Footprints are never moved (Quilter keeps pre-placed parts fixed).
"""
import sys, subprocess, pcbnew
CRITICAL = {"AC_SCK", "AC_MISO", "AC_MOSI", "AC_IRQ_N", "AC_RST_N", "AC_CS1_N", "AC_CS2_N", "ADE_XI", "ADE_XO",
            "ADE_SCK", "ADE_MISO", "ADE_MOSI", "ADE_IRQ_N", "ADE_RST_N", "ADE_CS1_N", "ADE_CS2_N",
            "DSI83_REFCLK", "DSI83_REFCLK_OSC"}
master_f, cand_f, out_f = sys.argv[1:4]
M = pcbnew.LoadBoard(master_f); C = pcbnew.LoadBoard(cand_f)
mn = {str(k): v for k, v in M.GetNetsByName().items()}
short = {}
for k, v in mn.items(): short.setdefault(k.split("/")[-1], v)
def mnet(name):
    return mn.get(name) or short.get(name.split("/")[-1])
def key(t):
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition(); return ("v", t.GetNetname().split("/")[-1], p.x // 1000, p.y // 1000)
    s, e = t.GetStart(), t.GetEnd(); a, b = sorted([(s.x // 1000, s.y // 1000), (e.x // 1000, e.y // 1000)])
    return ("t", t.GetNetname().split("/")[-1], t.GetLayer(), a, b)
have = {key(t) for t in M.GetTracks()}
def hvzone(t):
    pts = [t.GetPosition()] if t.GetClass() == "PCB_VIA" else [t.GetStart(), t.GetEnd()]
    return any(p.x / 1e6 < 73 and (p.y / 1e6 > -1.3 and p.y / 1e6 < 175.1) for p in pts)
stats = dict(candidate=0, existing=0, critical_or_class=0, hv=0, nonet=0, added=0)
for t in C.GetTracks():
    stats["candidate"] += 1
    if key(t) in have: stats["existing"] += 1; continue
    n = mnet(t.GetNetname())
    if n is None: stats["nonet"] += 1; continue
    if n.GetNetClassName() != "Default" or n.GetNetname().split("/")[-1] in CRITICAL: stats["critical_or_class"] += 1; continue
    if hvzone(t): stats["hv"] += 1; continue
    if t.GetClass() == "PCB_VIA":
        v = pcbnew.PCB_VIA(M); v.SetPosition(t.GetPosition()); v.SetWidth(t.GetWidth()); v.SetDrill(t.GetDrill())
        v.SetViaType(t.GetViaType()); v.SetLayerPair(t.TopLayer(), t.BottomLayer()); v.SetNet(n); M.Add(v)
    else:
        x = pcbnew.PCB_TRACK(M); x.SetStart(t.GetStart()); x.SetEnd(t.GetEnd()); x.SetWidth(t.GetWidth())
        x.SetLayer(t.GetLayer()); x.SetNet(n); M.Add(x)
    stats["added"] += 1
M.Save(out_f)
print(stats, flush=True)
r = subprocess.run([sys.executable, "-c", "import pcbnew,sys;b=pcbnew.LoadBoard(sys.argv[1]);pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.Save(sys.argv[1]);b.BuildConnectivity();print('unconnected',b.GetConnectivity().GetUnconnectedCount(True))", out_f], capture_output=True, text=True)
print([l for l in r.stdout.splitlines() if l.startswith("unconnected")])
