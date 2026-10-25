#!/usr/bin/env python3
"""Blackstart / genctl scripted placement skeleton (KiCad 9 pcbnew API).

Builds a .kicad_pcb from a KiCad XML/S-expr netlist (kicad-cli sch export netlist)
OR re-places footprints in an existing .kicad_pcb, then:
  * draws the board outline (Edge.Cuts, rounded rect) from geometry.py
  * places FIXED parts (buttons, mounting holes, display connectors, edge connectors)
  * packs every other footprint into its ZONE (shelf packing, courtyard bbox)
    or, with --quilter, leaves non-fixed parts OUTSIDE the outline (Quilter
    treats anything inside the outline as locked and places the rest itself)
  * adds Quilter-style placement regions (rule areas, all keepout items off)
    and real keepouts, 6-layer stackup with GND/PWR named planes.

Usage:
  kicad-cli sch export netlist -o genctl.net <copy>/genctl.kicad_sch
  python3 place.py --netlist genctl.net --out out/genctl_placed.kicad_pcb [--quilter] [--slots]
  python3 place.py --pcb existing.kicad_pcb --out out/x.kicad_pcb       # re-place only
Coordinates: see geometry.py (mm, origin glass top-left, front view; F side faces display).
STATUS: skeleton. Edge-connector rotations and CM5 connector offset are PLACEHOLDERS (marked TODO).
"""
import argparse, os, re, sys
import pcbnew
import geometry as g

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ_LIB = os.path.join(HERE, "snap", "genctl.pretty")   # read-only snapshot of repo lib
STOCK = "/usr/share/kicad/footprints"
MM = pcbnew.FromMM

# ---------------------------------------------------------------- tables
# FIXED: ref -> (x, y, rot_deg, side)   side 'F' (toward display) or 'B' (rear)
FIXED = {ref: (x, y, 0, "F") for ref, x, y in g.buttons()}
FIXED.update({ref: (x, y, 0, "F") for ref, x, y in g.MOUNT_HOLES})
FIXED.update({
    # display interconnect, F side (in the gap behind the display), short cables
    "J14": (g.LVDS_ZIF_PIN1[0] + 10, g.SRC_PCB_BAND[1] - 8, 0, "F"),  # LVDS 40p FFC, just above source-PCB band
    "J15": (sum(g.TOUCH_TAIL_X) / 2, g.GLASS_H - 6, 0, "F"),          # touch 10p, tail folds back (VERIFY tail length)
    "J16": (12.0, 14.0, 0, "F"),                                        # backlight, 200 mm cable reaches anywhere
    "J12": (sum(g.TOUCH_TAIL_X) / 2 - 20, g.GLASS_H - 6, 0, "F"),     # touch USB alt (SM04B)
    # CM5 carrier connectors, B side. TODO: copy exact U9/U10 offset from RPi CM5 IO board design files
    "U9":  (160.0, 85.0, 0, "B"),
    "U10": (160.0, 85.0 + 28.0, 0, "B"),   # PLACEHOLDER spacing
})

# EDGE strips: connectors auto-spaced along an edge (B side, wire entry outward).
# Long axis is aligned to the edge automatically; ROT is an extra per-edge offset
# (0/180) to point the wire entry outward. TODO verify entry direction per footprint in pcbnew.
TB_SLOTS = [(g.BOARD[0] + g.BTN_X[0] - 5.6) / 2] + \
           [(a + b) / 2 for a, b in zip(g.BTN_X, g.BTN_X[1:])] + \
           [(g.BTN_X[-1] + 5.6 + g.BOARD[2]) / 2]           # 7 slots between button land patterns
EDGES = {
    # name: (refs in order, edge, rotation, start, end)  start/end along the edge (mm)
    "left":   (["J29", "J30", "J31", "J1"], "L", 0, 7.0, 187.8),     # HV metering top, battery bottom
    "right":  (["J24", "J28", "J8", "J9", "J6", "J10", "J11"], "R", 180, 8.0, 175.0),
    "top":    ({1: "J21", 2: "J22", 3: "J25", 4: "J26", 5: "J27"}, "T", 0, None, None),  # slot0 = HV creepage buffer
    "bottom": ({1: "J17", 2: "J18", 3: "J19", 4: "J20", 5: "J7"}, "Bt", 180, None, None),
}

# ZONES: name -> (x0, y0, x1, y1, side, ref-regex list). First match wins; order matters.
ZONES = [
    # interior: x 10..266, y 1..178 (edge strips hold the connectors). Sized from parts-area x ~2.
    ("ISO_BARRIER", (70.0, 8.0, 84.0, 128.0), "B", [r"^U67$", r"^U68$"]),
    ("HV_METER", (12.0, 8.0, 70.0, 128.0), "B", []),           # AC metering sheet; >=8 mm to everything else
    ("POWER_IN", (12.0, 136.0, 100.0, 178.0), "B", []),
    ("MCU", (100.0, 118.0, 140.0, 178.0), "B", []),
    ("CM5_DISPLAY", (140.0, 70.0, 215.0, 135.0), "B", []),      # CM5 55x40 + DSI83 + display power
    ("INPUTS", (140.0, 135.0, 266.0, 178.0), "B", []),
    ("COMMS", (215.0, 50.0, 266.0, 135.0), "B", []),
    ("OUTPUTS", (84.0, 8.0, 266.0, 50.0), "B", []),
    ("SPILL", (88.0, 50.0, 140.0, 118.0), "B", []),             # overflow for POWER/INPUTS/OUTPUTS/FRONT (never HV)
    ("FRONT", (140.0, 50.0, 215.0, 70.0), "B", []),             # button LED drivers; route to buttons via inner layers
    ("MISC", (84.0, 178.0, 130.0, 178.5), "B", [r".*"]),        # catch-all (should end up empty)
]

SPILL_FROM = {"POWER_IN", "INPUTS", "OUTPUTS", "FRONT", "MCU", "COMMS"}

KEEPOUTS = [  # (name, bbox, layers, no_tracks, no_vias, no_pads, no_fp, no_pour)
    ("HV_creepage_band", (72.0, 8.0, 84.0, 128.0), ["F.Cu", "B.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu"], True, True, False, False, True),
]
SLOTS = [  # milled isolation slots (internal Edge.Cuts cutouts) - add AFTER Quilter (it wants one outline)
    (77.0, 12.0, 79.0, 124.0),
]

# schematic sheet (substring of sheet name) -> zone; used after explicit regexes, before net BFS
SHEET_ZONE = [("AC metering", "HV_METER"), ("Power:", "POWER_IN"), ("Raspberry Pi CM5", "CM5_DISPLAY"),
              ("Display:", "CM5_DISPLAY"), ("Comms:", "COMMS"), ("STM32", "MCU"), ("Front panel", "FRONT"),
              ("Inputs:", "INPUTS"), ("Outputs:", "OUTPUTS"), ("E-stop", "OUTPUTS")]

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

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--netlist"); ap.add_argument("--pcb"); ap.add_argument("--out", required=True)
    ap.add_argument("--quilter", action="store_true", help="only fixed parts inside outline; rest parked outside")
    ap.add_argument("--slots", action="store_true", help="add HV isolation slots as internal Edge.Cuts")
    a = ap.parse_args()
    b = board_from_netlist(a.netlist) if a.netlist else pcbnew.LoadBoard(a.pcb)

    # stackup / layers: 6 copper, Quilter-friendly plane names
    b.SetCopperLayerCount(6)
    for lid, nm in [(pcbnew.In1_Cu, "GND1"), (pcbnew.In2_Cu, "SIG_In2"), (pcbnew.In3_Cu, "PWR"), (pcbnew.In4_Cu, "GND2")]:
        b.SetLayerName(lid, nm)
    ds = b.GetDesignSettings()
    ds.m_TrackMinWidth = MM(0.10); ds.m_MinClearance = MM(0.10)       # JLC 6L: 0.09/0.09 abs min; use 0.10
    ds.m_ViasMinSize = MM(0.30); ds.m_MinThroughDrill = MM(0.20)       # 0.2/0.3-0.45 mm vias (JLC min 0.15/0.25)
    ds.m_HoleToHoleMin = MM(0.25); ds.m_CopperEdgeClearance = MM(0.30)

    edge_rect(b, *g.BOARD, r=g.BOARD_CORNER_R)
    if a.slots:
        for s in SLOTS: edge_rect(b, *s, r=0.99)

    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    placed = set()
    for ref, (x, y, rot, side) in FIXED.items():
        if ref in fps: put(fps[ref], x, y, rot, side); placed.add(ref)
        else: print("WARN fixed ref not in design:", ref)

    # edge strips
    for name, (refs, edge, rot, s0, s1) in EDGES.items():
        if isinstance(refs, dict):   # top/bottom: fixed slots between buttons
            for slot, ref in refs.items():
                if ref not in fps: print("WARN edge ref missing:", ref); continue
                w, h = size_mm(fps[ref]); base = 0 if w >= h else 90
                if base: w, h = h, w
                rot = base + rot
                y = g.BOARD[1] + 0.5 + h / 2 if edge == "T" else g.BOARD[3] - 0.5 - h / 2
                put(fps[ref], TB_SLOTS[slot], y, rot, "B"); placed.add(ref)
                if w > 30: print(f"WARN {ref} {w:.1f} mm wide > slot width")
        else:
            refs = [r for r in refs if r in fps]
            lens = [max(size_mm(fps[r])) for r in refs]
            gap = max(1.0, ((s1 - s0) - sum(lens)) / max(1, len(refs) - 1)) if len(refs) > 1 else 0
            pos = s0
            for r, L in zip(refs, lens):
                w, h = size_mm(fps[r]); depth = min(w, h); rr = (0 if h >= w else 90) + rot
                x = g.BOARD[0] + 0.5 + depth / 2 if edge == "L" else g.BOARD[2] - 0.5 - depth / 2
                put(fps[r], x, pos + L / 2, rr, "B"); placed.add(r); pos += L + gap
            if pos - gap > s1: print(f"WARN edge {name} overflows by {pos-gap-s1:.1f} mm")

    # zone assignment: explicit regex first; otherwise inherit from a connected IC/connector
    def nearest_zone(ref):
        p = fps[ref].GetPosition(); x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        def d(z):
            x0, y0, x1, y1 = z[1]
            return max(x0 - x, 0, x - x1) + max(y0 - y, 0, y - y1)
        return min(ZONES[:-1], key=d)
    def explicit(ref):
        z = next((z for z in ZONES[:-1] if any(re.match(p, ref) for p in z[3])), None)
        if z is None and ref in placed and not ref.startswith(("SW", "H")):
            z = nearest_zone(ref)      # anchor passives to the zone nearest their (fixed) connector
        if z is None:
            sh = fps[ref].GetSheetname()
            zn = next((zn for key, zn in SHEET_ZONE if key in sh), None)
            z = next((z for z in ZONES if z[0] == zn), None)
        return z
    netmap = {}
    for ref, fp in fps.items():
        for pad in fp.Pads():
            n = pad.GetNetname()
            if n: netmap.setdefault(n, set()).add(ref)
    def zone_of(ref, max_depth=4):
        """BFS over small (<=8 node) nets until a part with an explicit zone is found."""
        seen, frontier = {ref}, [ref]
        for _ in range(max_depth + 1):
            nxt = []
            for r in frontier:
                z = explicit(r)
                if z: return z
                for pad in fps[r].Pads():
                    peers = netmap.get(pad.GetNetname(), ())
                    if len(peers) > 8: continue
                    for p in sorted(peers):
                        if p not in seen: seen.add(p); nxt.append(p)
            frontier = nxt
        return None
    overflow = {}
    # obstacles: fixed/edge parts on the same side (THT parts block both sides)
    def is_tht(fp): return any(p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) for p in fp.Pads())
    obst = {"F": [], "B": []}
    for r in placed:
        fp = fps[r]; side = "B" if fp.IsFlipped() else "F"
        obst[side].append(rect_of(fp))
        if is_tht(fp): obst["B" if side == "F" else "F"].append(rect_of(fp))
    # zones
    parked_x = g.BOARD[2] + 20
    cursor = {}
    for ref in sorted(fps, key=lambda r: (re.sub(r"\d", "", r), int(re.sub(r"\D", "", r) or 0))):
        if ref in placed: continue
        fp = fps[ref]
        zone = zone_of(ref) or ZONES[-1]
        zname, (x0, y0, x1, y1), side, _ = zone
        w, h = size_mm(fp)
        if a.quilter:   # park outside the outline, grouped by zone in columns
            cx, cy, rowh = cursor.get(zname, (parked_x + 60 * ZONES.index(zone), g.BOARD[1], 0))
            put(fp, cx + w / 2, cy + h / 2, 0, side); cursor[zname] = (cx, cy + h + 0.5, 0)
            continue
        cx, cy, rowh = cursor.get(zname, (x0, y0, 0))
        while True:
            if cx + w > x1: cx, cy, rowh = x0, cy + max(rowh, 1.0), 0
            if cy + h > y1 or not hits((cx, cy, cx + w, cy + h), obst[side]): break
            cx += 1.0
        if cy + h > y1 and zname in SPILL_FROM:
            cursor[zname] = (cx, cy, rowh)
            zname = "SPILL"; x0, y0, x1, y1 = next(z[1] for z in ZONES if z[0] == "SPILL")
            cx, cy, rowh = cursor.get(zname, (x0, y0, 0))
            if cx + w > x1: cx, cy, rowh = x0, cy + rowh + 0.4, 0
        if cy + h > y1: overflow.setdefault(zname, []).append(ref)
        put(fp, cx + w / 2, cy + h / 2, 0, side)
        obst[side].append((cx, cy, cx + w, cy + h))
        if is_tht(fp): obst["F" if side == "B" else "B"].append((cx, cy, cx + w, cy + h))
        cursor[zname] = (cx + w, cy, max(rowh, h))

    area = {}
    for ref in fps:
        if ref in placed: continue
        z = (zone_of(ref) or ZONES[-1])[0]; w, h = size_mm(fps[ref]); area[z] = area.get(z, 0) + w * h
    for zname, (x0, y0, x1, y1), side, _ in ZONES:
        print(f"zone {zname:12s} parts-area {area.get(zname,0):8.0f} mm2  zone-area {(x1-x0)*(y1-y0):8.0f} mm2")
    for z, refs in overflow.items():
        print(f"WARN zone {z} overflow: {len(refs)} parts (enlarge zone / use --quilter): {' '.join(refs[:12])}...")
    # placement regions (Quilter: rule area, keepout with ALL items off) + real keepouts
    for zname, bbox, side, _ in ZONES:
        rule_area(b, "PR_" + zname, bbox, ["B.Cu" if side == "B" else "F.Cu"])
    for name, bbox, layers, t, v, p, f, pr in KEEPOUTS:
        rule_area(b, name, bbox, layers, t, v, p, f, pr)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    pcbnew.SaveBoard(a.out, b)
    print(f"saved {a.out}: {len(fps)} footprints, {len(placed)} fixed/edge-placed, quilter={a.quilter}")

if __name__ == "__main__":
    main()
