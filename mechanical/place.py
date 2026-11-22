#!/usr/bin/env python3
"""Blackstart / genctl scripted placement, v3 (enclosure rev C). KiCad 9 pcbnew API.

RETIRED / HISTORIC (Batch 30, 2026-11-22 HST): this is the pre-split single-board placer. Since the split (09b60d3)
the HV metering (J28/J29, T1-T4 ZMCT103C, 19.2 mm tall) lives on genctl_meter, and J30 is OFF-BOARD (shorting-type CT
block in the genset panel). J30 was removed from LEFT below; the CT_AT_BARRIER zone and the left-edge HV rows are
historic. Do not use for the next layout without rewriting it for two boards (mechanical/LAYOUT_PLAN.md 4a).

Builds a .kicad_pcb from a KiCad netlist (kicad-cli sch export netlist), then
  * outline 284 x 210 (geometry.py), 6 layers + JLC rules
  * FIXED parts: 12 x CTS 228E keys (F), H1-H3 M4 (D4.3, 9 mm pad), H4 D9.5 PE-boss clearance (NPTH),
    display connectors (F), CM5 DF40 connectors (B), ISOW7841/ISO7741 straddling the 600 V barrier
  * edge terminals: KF2EDGRM 5.08 headers one per key gap (top/bottom), 600 V Phoenix on the left edge,
    comms / battery / fuel-crank on the right edge; wire-entry side of each body points at the board edge
  * every other part shelf-packed into its block zone (B side), avoiding keys, posts, CM5 body, strap corridor
  * barrier keep-outs (13 mm, all layers), isolator windows, 1.5 mm inter-phase slots under J28/J29,
    shell-post / switch / strap / PE-ring keep-outs, Quilter placement regions, silkscreen title.
Usage:
  kicad-cli sch export netlist -o genctl.net snap/genctl.kicad_sch
  python3 place.py --netlist genctl.net --out out/genctl_placed_v3.kicad_pcb [--quilter]
Coordinates: geometry.py (mm, origin = glass top-left, FRONT view, y down; F side faces the display).
"""
import argparse, os, re, sys, math
import pcbnew
import geometry as g

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ_LIB = os.path.join(HERE, "snap", "genctl.pretty")   # refreshed copy of the repo lib (all genctl:* footprints)
STOCK = "/usr/share/kicad/footprints"
MM = pcbnew.FromMM
X0, Y0, X1, Y1 = g.BOARD
KEY_TOP_Y1 = g.BTN_Y_TOP + g.SW_KO_H / 2          # -1.25: bottom of the top key band keep-out
KEY_BOT_Y0 = g.BTN_Y_BOT - g.SW_KO_H / 2          # 180.71

# ---------------- 600 V metering block and barrier (docs/ISOLATION_CHECK.md: >=13 mm copper-free on FR-4)
BARRIER = 13.0
HV = (X0, 11.0, 60.0, 162.0)                      # hot copper only inside this box (top-left)
BAR_X = (HV[2], HV[2] + BARRIER)                  # vertical barrier band x 60..73
LV_X0 = BAR_X[1] + 1.0                            # 74: first LV column
ISO_Y = {"U69": 62.0, "U70": 98.0}                # ISOW7841 / ISO7741 straddle the barrier (slot in footprint)
ISO_WIN = 11.0                                    # half-height of the barrier gap at each isolator (= its 21 mm slot + margin)

# ---------------- CM5 + heat strap to M4 boss H2 (top-right)
CM5 = (203.0, 1.0, 258.0, 41.0)                   # module outline (55 x 40, B side, 1.5 mm stack: nothing under it)
CM5_CONN_DY = 34.0                                # DF40 centres 34 mm apart, 3 mm in from the 55 mm edges (CM4/CM5 datasheet)
STRAP_KO = (247.0, -14.8, 279.8, 3.8)             # strap corridor heatsink top-right -> H2 lug: B side, no parts
H2 = next((x, y) for r, x, y in g.MOUNT_HOLES if r == "H2")

FIXED = {ref: (x, y, 0, "F") for ref, x, y in g.buttons()}
FIXED.update({ref: (x, y, 0, "F") for ref, x, y in g.MOUNT_HOLES})
cm5x = (CM5[0] + CM5[2]) / 2
FIXED.update({
    "J14": (g.LVDS_ZIF_PIN1[0] + 10, g.SRC_PCB_BAND[1] - 8, 0, "F"),  # LVDS 40p FFC, just above the TFT source-PCB band
    "J15": (sum(g.TOUCH_TAIL_X) / 2, g.GLASS_H - 6, 0, "F"),          # touch 10p (VERIFY tail length vs STEP)
    "J16": (12.0 + 70, 18.0, 0, "F"),                                   # backlight: moved out of the HV block (200 mm cable)
    "J12": (sum(g.TOUCH_TAIL_X) / 2 - 20, g.GLASS_H - 6, 0, "F"),     # touch USB alt (SM04B)
    # TODO verify: +-2.5 mm x offset of the DF40 pair and which one is A, against the CM5 IO board KiCad files
    "U9":  (cm5x, CM5[1] + 3.0, 0, "B"),
    "U10": (cm5x, CM5[1] + 3.0 + CM5_CONN_DY, 0, "B"),
})

# top/bottom key gaps (5 each, 30.52 mm between 13 mm switch keep-outs). KF2EDGRM-6P pin row 27.9 mm fits;
# the flanged body (40.9) overhangs 5.2 mm per side on the B side behind the switches (switches are SMD on F).
TOP_GAPS = ["J24", "J25", "J26", "J27", "J21"]    # outputs + E-stop/D+ (outputs block is the top band)
BOT_GAPS = ["J17", "J18", "J19", "J20", "J22"]    # analog / MPU / DI (inputs block is the bottom band)
END_SLOTS = {"J9": ("B", (X0 + 9.5 + 1.0 + (g.BTN_X[0] - g.SW_KO_W / 2)) / 2),     # RS-485, bottom-left end slot
             "J8": ("B", (g.BTN_X[-1] + g.SW_KO_W / 2 + 266.0) / 2)}              # router 12 V, bottom-right end slot
LEFT = (["J28", "J29"], HV[1], HV[3])     # 600 V GEN V, BUS V (J30 CT header removed Batch 29/30: off-board CT shorting block)
RIGHT = (["J10", "J11", "J6", "J7", "J23", "J1"], STRAP_KO[3] + 0.4, 179.5 - 0.3)

ZONES = [  # name, bbox, side, explicit ref regexes (first match wins)
    ("CT_AT_BARRIER", (26.5, 112.0, HV[2], HV[3]), "B", [r"^T[1-4]$"]),
    ("ISO_LV", (LV_X0, 52.0, LV_X0 + 12.0, 95.0), "B", []),   # SELV-side decoupling of the isolators
    ("HV_METER", (13.4, HV[1], HV[2], HV[3]), "B", []),
    ("OUTPUTS", (LV_X0, KEY_TOP_Y1 + 0.3, 200.0, 52.0), "B", []),
    ("CM5", (200.0, 41.5, 262.0, 62.0), "B", []),
    ("FRONT", (LV_X0 + 12.5, 52.0, 135.0, 95.0), "B", []),
    ("MCU", (135.0, 52.0, 200.0, 100.0), "B", []),
    ("COMMS", (200.0, 62.0, 262.0, 135.0), "B", []),
    ("DISPLAY", (135.0, 100.0, 200.0, 135.0), "B", []),
    ("SPILL", (LV_X0, 95.0, 135.0, 135.0), "B", []),
    ("INPUTS", (LV_X0, 135.0, 190.0, KEY_BOT_Y0 - 0.3), "B", []),
    ("POWER", (190.0, 135.0, 262.0, KEY_BOT_Y0 - 0.3), "B", [r"^U2$"]),
    ("MISC", (LV_X0, 46.0, 262.0, 140.0), "B", [r".*"]),
]
SPILL_ORDER = {"OUTPUTS": ["FRONT", "SPILL", "MISC"], "INPUTS": ["SPILL", "MISC"], "POWER": ["COMMS", "SPILL", "MISC"],
               "FRONT": ["SPILL", "MISC"], "MCU": ["SPILL", "MISC"], "COMMS": ["MISC"], "CM5": ["COMMS", "MCU", "MISC"],
               "DISPLAY": ["SPILL", "MISC"], "SPILL": ["MISC"], "HV_METER": [], "CT_AT_BARRIER": ["HV_METER"], "ISO_LV": ["FRONT"]}

SHEET_ZONE = [("AC metering", "HV_METER"), ("Power:", "POWER"), ("Raspberry Pi CM5", "CM5"),
              ("Display:", "DISPLAY"), ("Comms:", "COMMS"), ("STM32", "MCU"), ("Front panel", "FRONT"),
              ("Inputs:", "INPUTS"), ("Outputs:", "OUTPUTS"), ("E-stop", "OUTPUTS")]
ALL_CU = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]

def barrier_areas():
    """13 mm copper-free U-shaped barrier round the HV box, with windows for the two isolators."""
    out = [("BARRIER_top", (X0, KEY_TOP_Y1, BAR_X[1], HV[1])), ("BARRIER_bottom", (X0, HV[3], BAR_X[1], HV[3] + BARRIER))]
    ys = [HV[1]] + [v for y in sorted(ISO_Y.values()) for v in (y - ISO_WIN, y + ISO_WIN)] + [HV[3]]
    for i in range(0, len(ys), 2):
        out.append((f"BARRIER_v{i//2}", (BAR_X[0], ys[i], BAR_X[1], ys[i + 1])))
    return out

KEEPOUTS = [  # (name, bbox, layers, no_tracks, no_vias, no_pads, no_fp, no_pour)
    *[(n, bb, ALL_CU, True, True, True, True, True) for n, bb in barrier_areas()],
    ("STRAP_CORRIDOR", STRAP_KO, ["B.Cu"], False, False, False, True, False),
    ("CM5_BODY", CM5, ["B.Cu"], False, False, False, False, False),     # placement only (connectors live here)
]

# ---------------------------------------------------------------- netlist
def sexpr(text):
    tok = re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', text)
    st = [[]]
    for t in tok:
        if t == "(":
            st.append([])
        elif t == ")":
            x = st.pop(); st[-1].append(x)
        else:
            st[-1].append(t[1:-1].replace('\\"', '"') if t.startswith('"') else t)
    return st[0][0]

def find(node, key):
    return [n for n in node if isinstance(n, list) and n and n[0] == key]

def read_netlist(path):
    root = sexpr(open(path).read())
    comps = {}
    for c in find(find(root, "components")[0], "comp"):
        ref = find(c, "ref")[0][1]
        fp = (find(c, "footprint") or [[None, ""]])[0][1]
        val = (find(c, "value") or [[None, ""]])[0][1]
        sp = (find(c, "sheetpath") or [[None, ["names", ""]]])[0]
        sheet = find(sp, "names")[0][1] if find(sp, "names") else ""
        comps[ref] = (fp, val, sheet)
    nets = {}
    for n in find(find(root, "nets")[0], "net"):
        name = find(n, "name")[0][1]
        nets[name] = [(find(nd, "ref")[0][1], find(nd, "pin")[0][1]) for nd in find(n, "node")]
    return comps, nets

def load_fp(fpid):
    lib, name = fpid.split(":", 1)
    path = PROJ_LIB if lib == "genctl" else os.path.join(STOCK, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {fpid} in {path}")
    return fp

def board_from_netlist(path):
    comps, nets = read_netlist(path)
    b = pcbnew.CreateEmptyBoard()
    fps = {}
    missing = []
    for ref, (fpid, val, sheet) in sorted(comps.items()):
        if not fpid:
            missing.append(ref); continue
        try:
            fp = load_fp(fpid)
        except RuntimeError as e:
            missing.append(f"{ref}:{fpid}"); continue
        fp.SetReference(ref); fp.SetValue(val); fp.SetSheetname(sheet)
        b.Add(fp); fps[ref] = fp
    for name, nodes in nets.items():
        ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni)
        for ref, pin in nodes:
            fp = fps.get(ref)
            if not fp: continue
            for pad in fp.Pads():
                if pad.GetNumber() == pin:
                    pad.SetNet(ni)
    if missing:
        print("WARN no footprint:", ", ".join(missing))
    return b

# ---------------------------------------------------------------- geometry helpers
def edge_rect(b, x0, y0, x1, y1, r=0.0, layer=pcbnew.Edge_Cuts):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if r <= 0:
        for a, c in zip(pts, pts[1:] + pts[:1]):
            s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(layer)
            s.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1]))); s.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
            s.SetWidth(MM(0.05)); b.Add(s)
        return
    segs = [((x0 + r, y0), (x1 - r, y0)), ((x1, y0 + r), (x1, y1 - r)),
            ((x1 - r, y1), (x0 + r, y1)), ((x0, y1 - r), (x0, y0 + r))]
    for a, c in segs:
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(layer)
        s.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1]))); s.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
        s.SetWidth(MM(0.05)); b.Add(s)
    for cx, cy, sx, sy in [(x0 + r, y0 + r, x0, y0 + r), (x1 - r, y0 + r, x1 - r, y0),
                           (x1 - r, y1 - r, x1, y1 - r), (x0 + r, y1 - r, x0 + r, y1)]:
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(layer)
        s.SetCenter(pcbnew.VECTOR2I(MM(cx), MM(cy))); s.SetStart(pcbnew.VECTOR2I(MM(sx), MM(sy)))
        s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T)); s.SetWidth(MM(0.05)); b.Add(s)

def rule_area(b, name, bbox, layers, tracks=False, vias=False, pads=False, fps=False, pour=False):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetZoneName(name)
    ls = pcbnew.LSET()
    for l in layers: ls.AddLayer(b.GetLayerID(l))
    z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(vias); z.SetDoNotAllowPads(pads)
    z.SetDoNotAllowFootprints(fps); z.SetDoNotAllowCopperPour(pour)
    x0, y0, x1, y1 = bbox
    ol = z.Outline(); ol.NewOutline()
    for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        ol.Append(MM(x), MM(y))
    b.Add(z)

def size_mm(fp):
    """max(courtyard, pads/graphics bbox) so parts without courtyards still pack safely"""
    bb = fp.GetBoundingBox(False)
    w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
    for lyr in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        cy = fp.GetCourtyard(lyr)
        if cy.OutlineCount():
            cb = cy.BBox(); w, h = max(w, pcbnew.ToMM(cb.GetWidth())), max(h, pcbnew.ToMM(cb.GetHeight()))
    return w + 0.3, h + 0.3   # 0.15 mm assembly margin each side

def rect_of(fp):
    bb = fp.GetBoundingBox(False)
    return (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))

def hits(r, rects):
    return any(not (r[2] <= q[0] or r[0] >= q[2] or r[3] <= q[1] or r[1] >= q[3]) for q in rects)

def put(fp, x, y, rot, side):
    if side == "B" and not fp.IsFlipped():
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT if hasattr(pcbnew, "FLIP_DIRECTION_LEFT_RIGHT") else False)
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    # centre courtyard on (x,y) rather than footprint origin
    c = fp.GetBoundingBox(False).GetCenter()
    fp.Move(pcbnew.VECTOR2I(MM(x) - c.x, MM(y) - c.y))

# ---------------------------------------------------------------- v3 helpers
def circle_area(b, name, x, y, r, layers, tracks=True, vias=True, pads=True, fps=True, pour=True, n=16):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetZoneName(name)
    ls = pcbnew.LSET()
    for l in layers: ls.AddLayer(b.GetLayerID(l))
    z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(vias); z.SetDoNotAllowPads(pads)
    z.SetDoNotAllowFootprints(fps); z.SetDoNotAllowCopperPour(pour)
    ol = z.Outline(); ol.NewOutline()
    rr = r / math.cos(math.pi / n)
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        ol.Append(MM(x + rr * math.cos(a)), MM(y + rr * math.sin(a)))
    b.Add(z)

def obround(b, cx, cy, w, l, vertical=True):
    """internal milled slot on Edge.Cuts, width w, overall length l"""
    r = w / 2; h = l / 2 - r
    if vertical:
        segs = [((cx - r, cy - h), (cx - r, cy + h)), ((cx + r, cy - h), (cx + r, cy + h))]
        arcs = [((cx, cy - h), (cx - r, cy - h)), ((cx, cy + h), (cx + r, cy + h))]
    else:
        segs = [((cx - h, cy - r), (cx + h, cy - r)), ((cx - h, cy + r), (cx + h, cy + r))]
        arcs = [((cx + h, cy), (cx + h, cy - r)), ((cx - h, cy), (cx - h, cy + r))]
    for a, c in segs:
        sh = pcbnew.PCB_SHAPE(b); sh.SetShape(pcbnew.SHAPE_T_SEGMENT); sh.SetLayer(pcbnew.Edge_Cuts)
        sh.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1]))); sh.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1]))); sh.SetWidth(MM(0.05)); b.Add(sh)
    for c, st in arcs:
        sh = pcbnew.PCB_SHAPE(b); sh.SetShape(pcbnew.SHAPE_T_ARC); sh.SetLayer(pcbnew.Edge_Cuts)
        sh.SetCenter(pcbnew.VECTOR2I(MM(c[0]), MM(c[1]))); sh.SetStart(pcbnew.VECTOR2I(MM(st[0]), MM(st[1])))
        sh.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(180, pcbnew.DEGREES_T)); sh.SetWidth(MM(0.05)); b.Add(sh)

def gfx_rect(b, bb, layer, w=0.15):
    x0, y0, x1, y1 = bb
    for a, c in [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]:
        sh = pcbnew.PCB_SHAPE(b); sh.SetShape(pcbnew.SHAPE_T_SEGMENT); sh.SetLayer(layer)
        sh.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1]))); sh.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1]))); sh.SetWidth(MM(w)); b.Add(sh)

def text(b, s, x, y, h, layer, mirror=False):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(layer)
    t.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y))); t.SetTextSize(pcbnew.VECTOR2I(MM(h), MM(h)))
    t.SetTextThickness(MM(h * 0.15)); t.SetMirrored(mirror); b.Add(t)

def pad_centroid(fp):
    ps = [p.GetPosition() for p in fp.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
    return (pcbnew.ToMM(sum(p.x for p in ps) / len(ps)), pcbnew.ToMM(sum(p.y for p in ps) / len(ps)))

def put_edge(fp, edge, along, side="B"):
    """place a terminal against an edge with its long axis along the edge and the body (wire/plug side,
    i.e. bbox centre relative to the pin centroid) pointing OUT of the board. along = centre coordinate."""
    best = None
    for rot in (0, 90, 180, 270):
        put(fp, 0, 0, rot, side)
        x0, y0, x1, y1 = rect_of(fp); w, h = x1 - x0, y1 - y0
        pcx, pcy = pad_centroid(fp); bcx, bcy = (x0 + x1) / 2, (y0 + y1) / 2
        if edge in "TB" and w < h: continue
        if edge in "LR" and h < w: continue
        out = {"T": bcy - pcy < 0, "B": bcy - pcy > 0, "L": bcx - pcx < 0, "R": bcx - pcx > 0}[edge]
        score = (out, -abs((bcx - pcx) if edge in "LR" else (bcy - pcy)) if not out else 0)
        if best is None or score > best[0]: best = (score, rot, w, h)
    _, rot, w, h = best
    m = 0.4
    if edge == "T": put(fp, along, Y0 + m + h / 2, rot, side)
    if edge == "B": put(fp, along, Y1 - m - h / 2, rot, side)
    if edge == "L": put(fp, X0 + m + w / 2, along, rot, side)
    if edge == "R": put(fp, X1 - m - w / 2, along, rot, side)
    return w, h

def fix_holes(b, fps):
    for ref, x, y in g.MOUNT_HOLES:
        old = fps.get(ref)
        net = old.Pads()[0].GetNet() if old and old.Pads() else None
        if ref == "H4":
            new = pcbnew.FootprintLoad(os.path.join(STOCK, "MountingHole.pretty"), "MountingHole_4.3mm_M4")
            p = new.Pads()[0]; p.SetDrillSize(pcbnew.VECTOR2I(MM(g.PE_HOLE_D), MM(g.PE_HOLE_D)))
            p.SetSize(pcbnew.VECTOR2I(MM(g.PE_HOLE_D), MM(g.PE_HOLE_D)))
            new.SetValue("PE boss clearance D9.5 NPTH")
        else:
            new = pcbnew.FootprintLoad(os.path.join(STOCK, "MountingHole.pretty"), "MountingHole_4.3mm_M4_Pad")
            for p in new.Pads():
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetDrillSize().x > MM(4):
                    p.SetSize(pcbnew.VECTOR2I(MM(g.M4_PAD_D), MM(g.M4_PAD_D)))
                if net: p.SetNet(net)
            new.SetValue("M4 bezel boss")
        new.SetReference(ref)
        if old:
            new.SetPath(old.GetPath()); b.Remove(old)
        b.Add(new); fps[ref] = new

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--netlist"); ap.add_argument("--pcb"); ap.add_argument("--out", required=True)
    ap.add_argument("--quilter", action="store_true", help="only fixed parts inside outline; rest parked outside")
    a = ap.parse_args()
    b = board_from_netlist(a.netlist) if a.netlist else pcbnew.LoadBoard(a.pcb)

    b.SetCopperLayerCount(6)
    for lid, nm in [(pcbnew.In1_Cu, "GND1"), (pcbnew.In2_Cu, "SIG_In2"), (pcbnew.In3_Cu, "PWR"), (pcbnew.In4_Cu, "GND2")]:
        b.SetLayerName(lid, nm)
    ds = b.GetDesignSettings()
    ds.m_TrackMinWidth = MM(0.10); ds.m_MinClearance = MM(0.10)
    ds.m_ViasMinSize = MM(0.30); ds.m_MinThroughDrill = MM(0.20)
    ds.m_HoleToHoleMin = MM(0.25); ds.m_CopperEdgeClearance = MM(0.30)
    edge_rect(b, *g.BOARD, r=g.BOARD_CORNER_R)

    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    fix_holes(b, fps)
    # thermal-via pads without a number/net inside an exposed pad: give them the EP net (footprint-internal DRC noise)
    for fp in fps.values():
        named = [p for p in fp.Pads() if p.GetNumber() and p.GetNetCode() > 0]
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and not p.GetNumber() and p.GetNetCode() <= 0:
                host = next((q for q in named if q.HitTest(p.GetPosition())), None)
                if host: p.SetNet(host.GetNet())
    placed = set()
    for ref, (x, y, rot, side) in FIXED.items():
        if ref in fps: put(fps[ref], x, y, rot, side); placed.add(ref)
        else: print("WARN fixed ref not in design:", ref)

    # isolators: HV-side pins (GND_AC) toward the HV box (x-)
    for ref, y in ISO_Y.items():
        iso = [r for r, f in fps.items() if "HV_Slot" in f.GetFPID().GetLibItemName().wx_str()]
        order = sorted(iso)
        if not order: break
        r = order[list(ISO_Y).index(ref)] if len(order) == len(ISO_Y) else ref
        fp = fps[r]
        for rot in (0, 180):
            put(fp, sum(BAR_X) / 2, y, rot, "B")
            hv = [p for p in fp.Pads() if "GND_AC" in p.GetNetname() or "_AC" in p.GetNetname()]
            if hv and all(pcbnew.ToMM(p.GetPosition().x) < sum(BAR_X) / 2 for p in hv): break
        placed.add(r); print(f"isolator {r} ({fp.GetValue()}) at x {sum(BAR_X)/2:.1f} y {y} rot {fp.GetOrientationDegrees():.0f}")

    warn = []
    # key-gap terminals
    for refs, edge in ((TOP_GAPS, "T"), (BOT_GAPS, "B")):
        for ref, x in zip(refs, g.KEY_GAP_X):
            if ref not in fps: warn.append(f"gap ref missing {ref}"); continue
            put_edge(fps[ref], edge, x); placed.add(ref)
            pads = [pcbnew.ToMM(p.GetPosition().x) for p in fps[ref].Pads()]
            half = g.KEY_GAP_W / 2
            if max(pads) + 1.25 > x + half or min(pads) - 1.25 < x - half:
                warn.append(f"{ref} pads intrude into switch keep-out")
    for ref, (edge, x) in END_SLOTS.items():
        if ref in fps: put_edge(fps[ref], edge, x); placed.add(ref)
    # left (600 V) and right edge strips
    for (refs, s0, s1), edge in ((LEFT, "L"), (RIGHT, "R")):
        refs = [r for r in refs if r in fps]
        lens = []
        for r in refs:
            w, h = put_edge(fps[r], edge, 0); lens.append(h)
        gap = ((s1 - s0) - sum(lens)) / max(1, len(refs) - 1)
        if gap < 0.3: warn.append(f"edge {edge} overflows: need {sum(lens):.1f} have {s1-s0:.1f}")
        pos = s0
        for r, L in zip(refs, lens):
            put_edge(fps[r], edge, pos + L / 2); placed.add(r); pos += L + max(gap, 0.3)
    # inter-phase slots under the 600 V headers J28/J29 (1.5 mm wide, between pad columns)
    phase_slots = []
    for ref in ("J28", "J29"):
        if ref not in fps: continue
        cols = {}
        for p in fps[ref].Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH: continue
            cols.setdefault(p.GetNumber(), []).append((pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)))
        cs = sorted(cols.values(), key=lambda v: sum(q[1] for q in v) / len(v))
        for c1, c2 in zip(cs, cs[1:]):
            ym = (sum(q[1] for q in c1) / len(c1) + sum(q[1] for q in c2) / len(c2)) / 2
            xs = [q[0] for q in c1 + c2]
            phase_slots.append((min(xs) - 1.5, ym, max(xs) + 1.5))
    for x0s, ym, x1s in phase_slots:
        obround(b, (x0s + x1s) / 2, ym, 1.5, x1s - x0s, vertical=False)

    # ---------- zone packing
    def nearest_zone(ref):
        p = fps[ref].GetPosition(); x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        def d(z):
            x0, y0, x1, y1 = z[1]
            return max(x0 - x, 0, x - x1) + max(y0 - y, 0, y - y1)
        return min(ZONES[:-1], key=d)
    def explicit(ref):
        z = next((z for z in ZONES[:-1] if any(re.match(p, ref) for p in z[3])), None)
        if z is None and "AC metering" in fps[ref].GetSheetname():
            nets = {p.GetNetname() for p in fps[ref].Pads()}
            if nets & {"GND", "+3V3"} and not any("_AC" in n for n in nets):
                return zone_by["ISO_LV"]          # SELV-side part drawn on the metering sheet
        if z is None:
            sh = fps[ref].GetSheetname()
            zn = next((zn for key, zn in SHEET_ZONE if key in sh), None)
            z = next((z for z in ZONES if z[0] == zn), None)
        return z
    zone_by = {z[0]: z for z in ZONES}
    def is_tht(fp): return any(p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) for p in fp.Pads())
    obst = {"F": [], "B": []}
    for r in placed:
        fp = fps[r]; side = "B" if fp.IsFlipped() else "F"
        obst[side].append(rect_of(fp))
        if is_tht(fp): obst["B" if side == "F" else "F"].append(rect_of(fp))
    for ref, x, y in g.buttons():   # switch clear areas: both sides for THT, F side for everything
        k = (x - g.SW_KO_W / 2, y - g.SW_KO_H / 2, x + g.SW_KO_W / 2, y + g.SW_KO_H / 2)
        obst["F"].append(k); obst["B"].append(k)
    for x, y in g.SHELL_POSTS:
        r = g.SHELL_POST_KO / 2; obst["B"].append((x - r, y - r, x + r, y + r))
    for _, x, y in g.MOUNT_HOLES:
        r = 6.0; obst["B"].append((x - r, y - r, x + r, y + r)); obst["F"].append((x - r, y - r, x + r, y + r))
    obst["B"] += [CM5, STRAP_KO, (140.0, 173.0, 215.0, KEY_BOT_Y0)]   # CM5 body, strap, title text
    for _, bb in barrier_areas(): obst["B"].append(bb); obst["F"].append(bb)
    for x0s, ym, x1s in phase_slots: obst["B"].append((x0s, ym - 1, x1s, ym + 1))

    def fits(zname, w, h, side, cur):
        x0, y0, x1, y1 = zone_by[zname][1]
        cx, cy, rowh = cur.get(zname, (x0, y0, 0))
        while True:
            if cx + w > x1: cx, cy, rowh = x0, cy + max(rowh, 0.5), 0
            if cy + h > y1: return None
            r = (cx, cy, cx + w, cy + h)
            if not hits(r, obst[side]): return cx, cy, rowh
            cx += 0.5
    overflow, cursor, used = {}, {}, {}
    parked_x = X1 + 20
    order = sorted(fps, key=lambda r: (re.sub(r"\d", "", r), int(re.sub(r"\D", "", r) or 0)))
    # big parts first inside each zone (better packing)
    order = sorted(order, key=lambda r: -size_mm(fps[r])[0] * size_mm(fps[r])[1])
    for ref in order:
        if ref in placed: continue
        fp = fps[ref]
        zone = explicit(ref) or ZONES[-1]
        zname, _, side, _ = zone
        w, h = size_mm(fp)
        if a.quilter:
            cx, cy, _ = cursor.get(zname, (parked_x + 60 * ZONES.index(zone), Y0, 0))
            put(fp, cx + w / 2, cy + h / 2, 0, side); cursor[zname] = (cx, cy + h + 0.5, 0); continue
        tried = [zname] + SPILL_ORDER.get(zname, [])
        res = None
        for zn in tried:
            res = fits(zn, w, h, side, cursor)
            if res: zname = zn; break
        if not res:
            overflow.setdefault(zone[0], []).append(ref)
            put(fp, parked_x + 10, Y0 + 10 * len(overflow[zone[0]]), 0, side); continue
        cx, cy, rowh = res
        put(fp, cx + w / 2, cy + h / 2, 0, side)
        obst[side].append((cx, cy, cx + w, cy + h))
        if is_tht(fp): obst["F" if side == "B" else "B"].append((cx, cy, cx + w, cy + h))
        cursor[zname] = (cx + w + 0.2, cy, max(rowh, h + 0.2))
        used[zname] = used.get(zname, 0) + w * h
        if zname != zone[0]: used.setdefault("spilled:" + zone[0] + "->" + zname, 0); used["spilled:" + zone[0] + "->" + zname] += 1
    for k, v in used.items():
        if k.startswith("spilled:"): print(f"  {k}: {v} parts")
    for zname, (x0, y0, x1, y1), side, _ in ZONES:
        print(f"zone {zname:14s} used {used.get(zname,0):7.0f} mm2 of {(x1-x0)*(y1-y0):7.0f}")
    for z, refs in overflow.items():
        warn.append(f"zone {z} overflow: {len(refs)} parts: {' '.join(refs[:12])}")

    # ---------- rule areas / keep-outs / marks
    for zname, bbox, side, _ in ZONES[:-1]:
        rule_area(b, "PR_" + zname, bbox, ["B.Cu" if side == "B" else "F.Cu"])
    for name, bbox, layers, t, v, p, f, pr in KEEPOUTS:
        rule_area(b, name, bbox, layers, t, v, p, f, pr)
    for i, (x, y) in enumerate(g.SHELL_POSTS):
        circle_area(b, f"SHELL_POST_{i+1}", x, y, g.SHELL_POST_KO / 2, ["B.Cu"], tracks=False, vias=False, pads=True, fps=True, pour=False)
    hx, hy = next((x, y) for r, x, y in g.MOUNT_HOLES if r == "H4")
    circle_area(b, "PE_BOSS_RING", hx, hy, g.PE_HOLE_D / 2 + 1.0, ALL_CU, pads=False, fps=False)
    for ref, x, y in g.buttons():
        gfx_rect(b, (x - g.SW_KO_W / 2, y - g.SW_KO_H / 2, x + g.SW_KO_W / 2, y + g.SW_KO_H / 2), pcbnew.F_CrtYd if False else pcbnew.Dwgs_User, 0.1)
    for bb in g.clamp_marks(): gfx_rect(b, bb, pcbnew.Cmts_User, 0.2)
    gfx_rect(b, CM5, pcbnew.Dwgs_User, 0.2); gfx_rect(b, STRAP_KO, pcbnew.Dwgs_User, 0.2)
    text(b, "CM5 55x40 (B side) - heat strap to H2 boss", (CM5[0] + CM5[2]) / 2, (CM5[1] + CM5[3]) / 2, 1.5, pcbnew.Dwgs_User)
    text(b, "PROJECT BLACKSTART", 177.5, 175.2, 3.0, pcbnew.B_SilkS, mirror=True)
    text(b, "genctl rev H  placement v3  CERN-OHL-S-2.0", 177.5, 179.0, 1.5, pcbnew.B_SilkS, mirror=True)
    text(b, "600V  HAZARDOUS VOLTAGE", 36.0, HV[1] - 3.5, 2.0, pcbnew.B_SilkS, mirror=True)

    for w_ in warn: print("WARN", w_)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    pcbnew.SaveBoard(a.out, b)
    # JLC 6-layer rules: Default netclass 0.10 mm clearance (KiCad default 0.20 flags fine-pitch footprints internally)
    import json
    pro = os.path.splitext(a.out)[0] + ".kicad_pro"
    if os.path.exists(pro):
        d = json.load(open(pro))
        for c in d.get("net_settings", {}).get("classes", []):
            if c.get("name") == "Default": c["clearance"] = 0.1
        json.dump(d, open(pro, "w"), indent=2)
    print(f"saved {a.out}: {len(fps)} footprints, {len(placed)} fixed/edge-placed, quilter={a.quilter}")

if __name__ == "__main__":
    main()
