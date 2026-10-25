#!/usr/bin/env python3
"""Project Blackstart v4 routing pipeline (KiCad 9 pcbnew python, no plugins).

  python3 route_v4.py setup  in.kicad_pcb out.kicad_pcb   # netclasses, planes, plane fan-out (critical step 1)
  python3 route_v4.py dsn    in.kicad_pcb out.dsn
  python3 route_v4.py ses    in.kicad_pcb in.ses out.kicad_pcb  # import Freerouting result + refill zones

Stackup JLC06161H-3313: F.Cu sig | GND1 (In1) | SIG_In2 | PWR (In3) | GND2 (In4) | B.Cu sig
Planes: LV area  GND on GND1+GND2, +3V3_SAFE on PWR
        HV box   GND_AC on GND1+GND2, +3V3_AC on PWR   (inside HV box only; barrier rule areas untouched)
Impedance widths are ESTIMATES for this stackup -- confirm in JLC's impedance calculator before fab.
"""
import sys, re, math, pcbnew
sys.path.insert(0, "/workspace/genctl/layout_prep")
MM = pcbnew.FromMM; TM = pcbnew.ToMM
HV = (-3.745, 11.0, 60.0, 162.0)

CLASSES = {  # name: (track, clearance, via_d, via_drill, dp_width, dp_gap, patterns)
    "PWR":     (0.50, 0.15, 0.6, 0.3, None, None, [r"^VBAT_(P|F|ESTOP)$", r"^\+12V$", r"^\+5V", r"^\+3V3", r"^\+1V8", r"CM5_3V3", r"USB\d_5V", r"BAT_IN", r"/BB_SW", r"OUT\d+$", r"CRANK_OUT", r"FUEL_OUT"]),
    "HV_LINE": (0.50, 1.50, 0.8, 0.4, None, None, [r"(GEN|BUS)_L\d$", r"(GEN|BUS)_N$", r"(GEN|BUS)_L\d_F", r"Net-\(F\d+-"]),
    "DIFF100": (0.11, 0.15, 0.4, 0.2, 0.11, 0.15, [r"ETH\d_[PN]$", r"LVDS\w*_[PN]$", r"DSI\w*_[PN]$"]),
    "DIFF90":  (0.15, 0.15, 0.4, 0.2, 0.15, 0.18, [r"USB\w*_D[PMN]$", r"USB\w*_D[+-]$"]),
}
PLANES = [("GND", "GND1", "LV"), ("GND", "GND2", "LV"), ("+3V3_SAFE", "PWR", "LV"),
          ("GND_AC", "GND1", "HV"), ("GND_AC", "GND2", "HV"), ("+3V3_AC", "PWR", "HV")]

def short(n): return n.split("/")[-1]

def setup_classes(b):
    ds = b.GetDesignSettings(); ns = ds.m_NetSettings
    d = ns.GetDefaultNetclass(); d.SetTrackWidth(MM(0.15)); d.SetClearance(MM(0.10)); d.SetViaDiameter(MM(0.40)); d.SetViaDrill(MM(0.20))
    ds.m_TrackMinWidth = MM(0.10); ds.m_MinClearance = MM(0.10); ds.m_ViasMinSize = MM(0.40); ds.m_MinThroughDrill = MM(0.20)
    ds.m_HoleClearance = MM(0.20); ds.m_CopperEdgeClearance = MM(0.30)
    ns.ClearNetclassPatternAssignments()
    for name, (tw, cl, vd, vdr, dw, dg, pats) in CLASSES.items():
        nc = pcbnew.NETCLASS(name); nc.SetTrackWidth(MM(tw)); nc.SetClearance(MM(cl)); nc.SetViaDiameter(MM(vd)); nc.SetViaDrill(MM(vdr))
        if dw: nc.SetDiffPairWidth(MM(dw)); nc.SetDiffPairGap(MM(dg))
        nc.SetPriority(list(CLASSES).index(name))
        ns.SetNetclass(name, nc)
    count = {}
    for n in b.GetNetsByName().keys():
        n = str(n)
        for name, c in CLASSES.items():
            if any(re.search(p, short(n)) or re.search(p, n) for p in c[6]):
                ns.SetNetclassPatternAssignment(n.replace("(", r"\(").replace(")", r"\)").replace("+", r"\+").replace("{", r"\{").replace("}", r"\}"), name)
                count[name] = count.get(name, 0) + 1; break
    ns.RecomputeEffectiveNetclasses() if hasattr(ns, "RecomputeEffectiveNetclasses") else None
    b.SynchronizeNetsAndNetClasses(True)
    print("netclasses:", count)

def poly(pts):
    sh = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in pts: sh.Append(MM(x), MM(y))
    sh.SetClosed(True); return sh

def add_zone(b, net, layer, pts, name, prio):
    z = pcbnew.ZONE(b); z.SetLayer(b.GetLayerID(layer)); z.SetNetCode(b.GetNetcodeFromNetname(net))
    z.Outline().AddOutline(poly(pts)); z.SetZoneName(name); z.SetAssignedPriority(prio)
    z.SetLocalClearance(MM(0.2)); z.SetMinThickness(MM(0.15)); z.SetThermalReliefGap(MM(0.25)); z.SetThermalReliefSpokeWidth(MM(0.3))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    b.Add(z); return z

def setup_planes(b):
    bb = b.GetBoardEdgesBoundingBox(); X0, Y0, X1, Y1 = TM(bb.GetLeft()), TM(bb.GetTop()), TM(bb.GetRight()), TM(bb.GetBottom())
    lv = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1), (X0, HV[3] + 13.0), (HV[2] + 13.0, HV[3] + 13.0), (HV[2] + 13.0, HV[1] - 6.0), (X0, HV[1] - 6.0)]
    hv = [(HV[0] + 0.5, HV[1] + 0.5), (HV[2] - 0.5, HV[1] + 0.5), (HV[2] - 0.5, HV[3] - 0.5), (HV[0] + 0.5, HV[3] - 0.5)]
    for z in list(b.Zones()):
        if not z.GetIsRuleArea(): b.Remove(z)
    for i, (net, layer, reg) in enumerate(PLANES):
        add_zone(b, net, layer, lv if reg == "LV" else hv, f"{reg}_{net}_{layer}", 0)

def plane_layer(net):
    for n, l, _ in PLANES:
        if n == net: return l
    return None

def fanout(b):
    """critical step 1: every SMD pad on a plane net gets a short stub + via straight into its plane (decap/IC GND & supply pins)."""
    pads = [p for f in b.GetFootprints() for p in f.Pads()]
    rects = []
    for p in pads:
        bb = p.GetBoundingBox(); rects.append((TM(bb.GetLeft()), TM(bb.GetTop()), TM(bb.GetRight()), TM(bb.GetBottom()), p.GetNetname(), p.IsOnLayer(pcbnew.F_Cu), p.IsOnLayer(pcbnew.B_Cu)))
    vias = []; added = 0; failed = []
    VD, CL = 0.40, 0.16
    def pcl(n):
        for name, c in CLASSES.items():
            if any(re.search(p, short(n)) for p in c[6]): return c[1]
        return 0.10
    rects = [(l, t, rr, bt, n, onf, onb, max(CL, pcl(n))) for (l, t, rr, bt, n, onf, onb) in rects]
    stubs = []   # (x0,y0,x1,y1,net,layer)
    def free(x, y, net, cu, sx=None, sy=None):
        # via disc + stub segment against foreign pads (all layers for via, same layer for stub), vias and stubs
        r = VD / 2
        pts = [(x, y, r, True)]
        if sx is not None:
            for k in range(1, 6):
                pts.append((sx + (x - sx) * k / 6, sy + (y - sy) * k / 6, 0.125, False))
        for (l, t, rr, bt, n, onf, onb, c) in rects:
            if n == net: continue
            for (qx, qy, qr, isvia) in pts:
                if not isvia and not ((cu == pcbnew.F_Cu and onf) or (cu == pcbnew.B_Cu and onb)): continue
                if qx + qr + c > l and qx - qr - c < rr and qy + qr + c > t and qy - qr - c < bt: return False
        for (vx, vy, vn) in vias:
            if vn != net and math.hypot(vx - x, vy - y) < VD + 0.2: return False
            if vn == net and math.hypot(vx - x, vy - y) < VD + 0.1: return False
        return True
    keep = [z for z in b.Zones() if z.GetIsRuleArea()]
    def in_keep(x, y, net=""):
        # hard isolation rule: no via in/near the 13 mm barrier band; HV nets only inside the HV box, LV nets only outside
        if HV[2] - 0.6 <= x <= HV[2] + 13.6 and HV[1] - 13.6 <= y <= HV[3] + 13.6: return True
        inhv = HV[0] <= x <= HV[2] - 0.6 and HV[1] + 0.6 <= y <= HV[3] - 0.6
        if net.endswith("_AC") != inhv: return True
        v = pcbnew.VECTOR2I(MM(x), MM(y))
        return any(z.Outline().Contains(v) and (z.GetDoNotAllowVias() or z.GetDoNotAllowTracks()) for z in keep)
    for f in b.GetFootprints():
        fx, fy = TM(f.GetPosition().x), TM(f.GetPosition().y)
        for p in f.Pads():
            net = p.GetNetname()
            if not plane_layer(net) or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
            cu = pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu
            px, py = TM(p.GetPosition().x), TM(p.GetPosition().y)
            bb = p.GetBoundingBox(); hw, hh = TM(bb.GetWidth()) / 2, TM(bb.GetHeight()) / 2
            dx, dy = px - fx, py - fy
            if hw > 1.0 and hh > 1.0:   # exposed/thermal pad: via-in-pad grid (JLC tented/plugged)
                n = 0
                for ix in (-0.6, 0.6):
                    for iy in (-0.6, 0.6):
                        vx, vy = px + ix * min(hw - 0.4, 1.0), py + iy * min(hh - 0.4, 1.0)
                        if in_keep(vx, vy, net): continue
                        vias.append((vx, vy, net))
                        v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(MM(vx), MM(vy))); v.Padstack().SetSize(pcbnew.VECTOR2I(MM(VD), MM(VD)), pcbnew.F_Cu); v.SetDrill(MM(0.20)); v.SetNetCode(p.GetNetCode()); b.Add(v); n += 1
                added += n; continue
            dirs = [(math.copysign(1, dx), 0), (0, math.copysign(1, dy))] if abs(dx) >= abs(dy) else [(0, math.copysign(1, dy)), (math.copysign(1, dx), 0)]
            dirs += [(-dirs[0][0], -dirs[0][1]), (-dirs[1][0], -dirs[1][1])]
            ok = False
            for ux, uy in dirs:
                for ext in (0.45, 0.65, 0.9, 1.2):
                    vx = px + ux * (hw + ext - 0.2 * (ux == 0)); vy = py + uy * (hh + ext - 0.2 * (uy == 0))
                    if ux == 0: vx = px
                    if uy == 0: vy = py
                    if in_keep(vx, vy, net) or not free(vx, vy, net, cu, px, py): continue
                    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(MM(vx), MM(vy))); v.Padstack().SetSize(pcbnew.VECTOR2I(MM(VD), MM(VD)), pcbnew.F_Cu); v.SetDrill(MM(0.20))
                    v.SetNetCode(p.GetNetCode()); b.Add(v)
                    t = pcbnew.PCB_TRACK(b); t.SetStart(p.GetPosition()); t.SetEnd(v.GetPosition()); t.SetWidth(MM(0.25)); t.SetLayer(cu); t.SetNetCode(p.GetNetCode()); b.Add(t)
                    vias.append((vx, vy, net)); added += 1; ok = True; break
                if ok: break
            if not ok: failed.append(f"{f.GetReference()}.{p.GetNumber()}")
    print(f"fanout vias: {added}, no room: {len(failed)}", failed[:30])

def fill(b):
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())

if __name__ == "__main__":
    cmd = sys.argv[1]
    b = pcbnew.LoadBoard(sys.argv[2])
    if cmd == "setup":
        setup_classes(b); setup_planes(b); fanout(b); fill(b); b.Save(sys.argv[3])
    elif cmd == "dsn":
        print("dsn", pcbnew.ExportSpecctraDSN(b, sys.argv[3]))
    elif cmd == "ses":
        print("ses", pcbnew.ImportSpecctraSES(b, sys.argv[3])); fill(b); b.Save(sys.argv[4])
