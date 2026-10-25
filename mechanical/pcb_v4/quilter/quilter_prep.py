"""Build a Quilter input package from genctl_v4_handrouted.

  cd mechanical/pcb_v4
  kicad-cli pcb drc --severity-all --format json -o w6/drc_all.json genctl_v4_handrouted.kicad_pcb   # dangling list
  python3 quilter/quilter_prep.py genctl_v4_handrouted.kicad_pcb w6/drc_all.json /workspace/genctl/layout_prep/quilter_v4

Output (flat, no zip): genctl.kicad_pcb / genctl.kicad_pro / genctl.kicad_dru + every root *.kicad_sch.
Changes vs. the source board, Quilter copy only:
  1. Net names reconciled with the schematic.  The board had DSI83_REFCLK split into a short-name and a full-path net,
     and DSI83_REFCLK_OSC was short-named.
  2. Dangling track/via segments listed by DRC (track_dangling / via_dangling) are deleted.  Quilter will not remove orphans itself.
  3. Copper layers are renamed so Quilter detects plane use: GND1->gnd, GND2->ground, PWR->pwr, SIG_In2->sig.
  4. Internal Edge.Cuts slots (6 HV slots at x 2.7-11 mm, plus the U69/U70 isolator slots) are moved to Dwgs.User.
     Quilter accepts only one closed outline.  Each slot gets a full keep-out rule area (QUILTER_SLOT_n) in its place.
  5. A 600 V keep-out rule area (QUILTER_HV_KEEPOUT_600V: tracks+vias, all copper, x -3.745..60, y 11..162) is added.
     Quilter does not support high voltage; the barrier rule areas already block x 60..73.
  6. All footprints, tracks and vias are locked; Quilter treats in-outline items as fixed anyway.
"""
import sys, os, json, shutil, glob, pcbnew
FM = pcbnew.FromMM
src, drcf, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
b = pcbnew.LoadBoard(src)
log = {}
P = lambda *a: print(*a, flush=True)
# 1 net reconcile
nets = b.GetNetsByName()
full = {str(n).split("/")[-1]: nets[n] for n in nets.keys() if str(n).startswith("/Display")}
moved = 0
for short in ("DSI83_REFCLK", "DSI83_REFCLK_OSC"):
    if short not in [str(k) for k in nets.keys()]: continue
    sn = b.FindNet(short)
    if short in full:
        tgt = full[short]
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetNetCode() == sn.GetNetCode(): p.SetNet(tgt); moved += 1
        for t in b.GetTracks():
            if t.GetNetCode() == sn.GetNetCode(): t.SetNet(tgt); moved += 1
    else:
        sn.SetNetname("/Display: DSI->LVDS bridge, panel power, backlight, touch/" + short); moved += 1
log["net_reconcile_items"] = moved
P("# 2 dangling")
# 2 dangling
d = json.load(open(drcf)); dead = 0
uu = {i["uuid"] for v in d["violations"] if v["type"] in ("track_dangling", "via_dangling") for i in v["items"]}
byid = {t.m_Uuid.AsString(): t for t in b.GetTracks()}
for u in sorted(uu):
    if u in byid: b.Delete(byid[u]); dead += 1
log["dangling_deleted"] = dead
P("# 3 layer")
# 3 layer names
ren = {"GND1": "gnd", "GND2": "ground", "PWR": "pwr", "SIG_In2": "sig"}
for l in b.GetEnabledLayers().CuStack():
    n = b.GetLayerName(l)
    if n in ren: b.SetLayerName(l, ren[n])
log["layers"] = [b.GetLayerName(l) for l in b.GetEnabledLayers().CuStack()]
P("# 4 internal")
# 4 internal slots -> Dwgs.User + keepouts
def keepout(name, x0, y0, x1, y1, everything=True):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetZoneName(name)
    ls = pcbnew.LSET()
    for l in b.GetEnabledLayers().CuStack(): ls.AddLayer(l)
    z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    if hasattr(z, "SetDoNotAllowCopperPour"): z.SetDoNotAllowCopperPour(everything)
    else: z.SetDoNotAllowZoneFills(everything)
    o = z.Outline(); o.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)): o.Append(FM(x), FM(y))
    b.Add(z)
eb = b.GetBoardEdgesBoundingBox()
EX0, EY0, EX1, EY1 = eb.GetX(), eb.GetY(), eb.GetRight(), eb.GetBottom()
box = lambda it: (lambda bb: [bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom()])(it.GetBoundingBox())
groups = []
for dr in list(b.GetDrawings()):
    if dr.GetLayer() != pcbnew.Edge_Cuts: continue
    r = box(dr)
    if r[0] <= EX0 + FM(0.5) or r[2] >= EX1 - FM(0.5) or r[1] <= EY0 + FM(0.5) or r[3] >= EY1 - FM(0.5):
        continue                      # outer outline
    dr.SetLayer(pcbnew.Dwgs_User); groups.append(r)
for f in b.GetFootprints():
    for g in f.GraphicalItems():
        if g.GetLayer() == pcbnew.Edge_Cuts:
            groups.append(box(g)); g.SetLayer(pcbnew.Dwgs_User); log.setdefault("fp_slot_items", []).append(f.GetReference())
rects = []
for r in groups:
    for q in rects:
        if not (r[2] < q[0] or q[2] < r[0] or r[3] < q[1] or q[3] < r[1]):
            q[:] = [min(q[0], r[0]), min(q[1], r[1]), max(q[2], r[2]), max(q[3], r[3])]; break
    else: rects.append(list(r))
for i, r in enumerate(rects):
    keepout(f"QUILTER_SLOT_{i}", r[0]/1e6, r[1]/1e6, r[2]/1e6, r[3]/1e6)
log["slots"] = [[round(v/1e6, 2) for v in r] for r in rects]
P("# 5 HV")
# 5 HV keepout (tracks+vias only, pours left so HV_GND_AC / HV_+3V3_AC planes can be preserved)
keepout("QUILTER_HV_KEEPOUT_600V", EX0/1e6, 11.0, 60.0, 162.0, everything=False)
P("# 6 lock")
# 6 lock
for f in b.GetFootprints(): f.SetLocked(True)
for t in b.GetTracks(): t.SetLocked(True)
pcb = os.path.join(out, "genctl.kicad_pcb")
b.Save(pcb)
# fresh reload + refill
import subprocess   # refill in a fresh process (reloading in-process crashes pcbnew's SWIG layer)
r = subprocess.run([sys.executable, "-c", "import pcbnew,sys;b=pcbnew.LoadBoard(sys.argv[1]);pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.Save(sys.argv[1]);b.BuildConnectivity();print('UNC',b.GetConnectivity().GetUnconnectedCount(True))", pcb], capture_output=True, text=True)
log["unconnected"] = [l for l in r.stdout.splitlines() if l.startswith("UNC")]
# project / rules / schematic (flat)
repo = os.path.abspath(os.path.join(os.path.dirname(src) or ".", "..", ".."))
pr = json.load(open(os.path.join(repo, "genctl.kicad_pro"))); pb = json.load(open(src.replace(".kicad_pcb", ".kicad_pro")))
for k in ("board", "net_settings"): pr[k] = pb[k]
pr.setdefault("meta", {})["filename"] = "genctl.kicad_pro"
json.dump(pr, open(os.path.join(out, "genctl.kicad_pro"), "w"), indent=2)
shutil.copy(src.replace(".kicad_pcb", ".kicad_dru"), os.path.join(out, "genctl.kicad_dru"))
sch = sorted(glob.glob(os.path.join(repo, "*.kicad_sch")))
for s in sch: shutil.copy(s, out)
log["schematics"] = [os.path.basename(s) for s in sch]
print(json.dumps(log, indent=1))
