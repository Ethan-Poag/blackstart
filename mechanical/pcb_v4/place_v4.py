#!/usr/bin/env python3
"""Blackstart / genctl placement v4: hard constraints first, then CONNECTIVITY-driven placement.
 (a) lock: outline, holes, keys, display connectors, CM5 DF40s, 600 V box + 13 mm barrier + isolators/slots,
     edge terminals (wire entry), keep-outs (shell posts, strap, PE ring). J10 RJ45 / J11 USB-C are now
     vertical (rear-facing) parts, placed by function next to the CM5 (no longer on the side edge).
 (b) primaries (ICs, FETs, inductors, crystals, connectors not on an edge) placed in signal-flow order:
     explicit seeds (STM32, DSI83, power chain, ADE9000s) then greedy: the unplaced primary with the most
     connections to already-placed parts goes to the weighted centroid of those connections (power/GND nets ignored),
     legalised by a spiral search, with a halo sized for its own passives.
 (c) each passive/small part belongs to the primary nearest to it ON THE SCHEMATIC (the schematic generator draws
     every IC with its own passives), and is placed next to the owner pad it shares a net with (decaps at their
     power pin). Then a few relaxation passes move small parts to the centroid of their connections.
Usage: python3 place_v4.py --netlist genctl.net --out pcb_v4/genctl_v4.kicad_pcb [--seeds seeds.json]
"""
import re, argparse, json, math, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import pcbnew
import geometry as g
import place as P
MM = pcbnew.FromMM; TM = pcbnew.ToMM
REPO = "/workspace/genctl/kicad/genctl"
P.PROJ_LIB = os.path.join(REPO, "genctl.pretty")

POWER_NETS = re.compile(r"^(GND.*|\+.*|VBAT.*|CM5_3V3|CM5_5V|.*_VISO|VDDA|VISO.*|CHASSIS|DSI83_VCORE|SC_TOP)$")
SMALL = re.compile(r"^(R|C|D|FB|LED|TP|JP)\d+$")
def is_small(ref, fp):
    if SMALL.match(ref): return True
    if ref.startswith("Q") and "SOT-23" in fp.GetFPID().GetLibItemName().wx_str(): return True
    if ref.startswith("U") and re.search(r"SOT-23|SOT-563|SOT-583", fp.GetFPID().GetLibItemName().wx_str()): return False
    return False

# functional seeds (board coords, mm). Everything else follows connectivity.
SEEDS = {
    "J10": (214.0, 53.0, 0),     # vertical RJ45 under the CM5 (MDI from the CM5 PHY, conn A), opening to the rear window
    "J11": (240.0, 50.0, 0),     # vertical USB-C service port beside it
    "U7":  (165.0, 80.0, 0),     # STM32H743: centre of the LV area (outputs above, inputs below, CM5/comms right, front-panel left)
    "U21": (160.0, 128.0, 0),    # SN65DSI83 between CM5 conn B and J14 (LVDS FPC, F side at 128,142)
    "U2":  (225.0, 160.0, 0),    # LM5176 buck-boost next to the battery input chain
    "U1":  (250.0, 165.0, 0),    # LM74800 ideal diode right behind J1 / F1
    "U71": (40.0, 62.0, 0),      # ADE9000 GEN next to U69 (SPI isolator)
    "U72": (40.0, 98.0, 0),      # ADE9000 BUS next to U70
    # AC1005 CTs (32 x 12 incl. wire loop) stacked at the barrier edge next to J30, entirely in the hot zone (v3 rule kept)
    "T1": (43.0, 118.0, 0), "T2": (43.0, 130.0, 0), "T3": (43.0, 142.0, 0), "T4": (43.0, 154.0, 0),
    "RV1": (42.0, 20.0, 0), "RV2": (42.0, 29.0, 0), "RV3": (42.0, 38.0, 0), "RV4": (17.0, 148.0, 90), "RV5": (26.0, 148.0, 90), "RV6": (54.5, 80.0, 90),   # line MOVs right behind the HV inputs
    "BT1": (120.0, 60.0, 0),     # CR2032 for the STM32 VBAT: big, few nets -> seed so it is not squeezed out
}

def sch_positions():
    pos = {}
    for f in os.listdir(REPO):
        if not f.endswith(".kicad_sch"): continue
        t = open(os.path.join(REPO, f)).read()
        for m in re.finditer(r'\(symbol \(lib_id "[^"]+"\) \(at ([-\d.]+) ([-\d.]+)[^\n]*\n\(property "Reference" "([^"]+)"', t):
            pos[m.group(3)] = (f, float(m.group(1)), float(m.group(2)))
    return pos

def rect_at(w, h, x, y, m=0.0): return (x - w / 2 - m, y - h / 2 - m, x + w / 2 + m, y + h / 2 + m)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--netlist", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--seeds"); ap.add_argument("--halo", type=float, default=0.6)
    ap.add_argument("--small_gap", type=float, default=0.3)
    a = ap.parse_args()
    seeds = dict(SEEDS)
    if a.seeds and os.path.exists(a.seeds):
        seeds.update({k: tuple(v) for k, v in json.load(open(a.seeds)).items()})
    b = P.board_from_netlist(a.netlist)
    b.SetCopperLayerCount(6)
    for lid, nm in [(pcbnew.In1_Cu, "GND1"), (pcbnew.In2_Cu, "SIG_In2"), (pcbnew.In3_Cu, "PWR"), (pcbnew.In4_Cu, "GND2")]:
        b.SetLayerName(lid, nm)
    ds = b.GetDesignSettings()
    ds.m_TrackMinWidth = MM(0.10); ds.m_MinClearance = MM(0.10)
    ds.m_ViasMinSize = MM(0.40); ds.m_MinThroughDrill = MM(0.20)
    ds.m_HoleToHoleMin = MM(0.25); ds.m_CopperEdgeClearance = MM(0.30)
    P.edge_rect(b, *g.BOARD, r=g.BOARD_CORNER_R)
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    P.fix_holes(b, fps)
    for fp in fps.values():
        named = [p for p in fp.Pads() if p.GetNumber() and p.GetNetCode() > 0]
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and not p.GetNumber() and p.GetNetCode() <= 0:
                host = next((q for q in named if q.HitTest(p.GetPosition())), None)
                if host: p.SetNet(host.GetNet())
    placed = set()
    for ref, (x, y, rot, side) in P.FIXED.items():
        if ref in fps: P.put(fps[ref], x, y, rot, side); placed.add(ref)
    for ref, y in P.ISO_Y.items():
        fp = fps[ref]
        for rot in (0, 180):
            P.put(fp, sum(P.BAR_X) / 2, y, rot, "B")
            hv = [p for p in fp.Pads() if "_AC" in p.GetNetname()]
            if hv and all(TM(p.GetPosition().x) < sum(P.BAR_X) / 2 for p in hv): break
        placed.add(ref)
    for refs, edge in ((P.TOP_GAPS, "T"), (P.BOT_GAPS, "B")):
        for ref, x in zip(refs, g.KEY_GAP_X):
            P.put_edge(fps[ref], edge, x); placed.add(ref)
    for ref, (edge, x) in P.END_SLOTS.items():
        P.put_edge(fps[ref], edge, x); placed.add(ref)
    RIGHT = (["J6", "J7", "J23", "J1"], 38.0, 180.0)  # J1 body must end above the H4 PE boss (y 180.8)      # J10/J11 are rear-facing now; right edge keeps the wire terminals
    for (refs, s0, s1), edge in ((P.LEFT, "L"), (RIGHT, "R")):
        lens = [P.put_edge(fps[r], edge, 0)[1] for r in refs]
        gap = ((s1 - s0) - sum(lens)) / max(1, len(refs) - 1); pos = s0
        for r, L in zip(refs, lens):
            P.put_edge(fps[r], edge, pos + L / 2); placed.add(r); pos += L + max(gap, 0.3)
    phase_slots = []
    for ref in ("J28", "J29"):
        cols = {}
        for p in fps[ref].Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH: continue
            cols.setdefault(p.GetNumber(), []).append((TM(p.GetPosition().x), TM(p.GetPosition().y)))
        cs = sorted(cols.values(), key=lambda v: sum(q[1] for q in v) / len(v))
        for c1, c2 in zip(cs, cs[1:]):
            ym = (sum(q[1] for q in c1) / len(c1) + sum(q[1] for q in c2) / len(c2)) / 2
            xs = [q[0] for q in c1 + c2]; phase_slots.append((min(xs) - 1.5, ym, max(xs) + 1.5))
    for x0s, ym, x1s in phase_slots: P.obround(b, (x0s + x1s) / 2, ym, 1.5, x1s - x0s, vertical=False)

    # ---------- obstacles
    def is_tht(fp): return any(p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) for p in fp.Pads())
    obst = {"F": [], "B": []}
    def block(fp, m=0.0):
        side = "B" if fp.IsFlipped() else "F"; r = P.rect_of(fp); r = (r[0] - m, r[1] - m, r[2] + m, r[3] + m)
        obst[side].append(r)
        if is_tht(fp): obst["F" if side == "B" else "B"].append(r)
    for r in placed: block(fps[r], 0.3)
    for ref, x, y in g.buttons():
        k = (x - g.SW_KO_W / 2, y - g.SW_KO_H / 2, x + g.SW_KO_W / 2, y + g.SW_KO_H / 2); obst["F"].append(k); obst["B"].append(k)
    for x, y in g.SHELL_POSTS:
        r = g.SHELL_POST_KO / 2; obst["B"].append((x - r, y - r, x + r, y + r))
    for _, x, y in g.MOUNT_HOLES:
        r = 6.0; obst["B"].append((x - r, y - r, x + r, y + r)); obst["F"].append((x - r, y - r, x + r, y + r))
    CM5_IN = (P.CM5[0], P.CM5[1] + 6.0, P.CM5[2], P.CM5[3] - 6.0)   # under the module between the DF40s: 1.5 mm stack -> no parts
    obst["B"] += [CM5_IN, P.STRAP_KO, (140.0, 173.0, 215.0, P.KEY_BOT_Y0)]
    for _, bb in P.barrier_areas(): obst["B"].append(bb); obst["F"].append(bb)
    for x0s, ym, x1s in phase_slots: obst["B"].append((x0s, ym - 1, x1s, ym + 1))
    X0, Y0, X1, Y1 = g.BOARD
    inner = (X0 + 1.0, Y0 + 1.0, X1 - 1.0, Y1 - 1.0)
    HVB = P.HV
    def region_ok(r, hot):
        if r[0] < inner[0] or r[1] < inner[1] or r[2] > inner[2] or r[3] > inner[3]: return False
        inside_hv = r[0] >= HVB[0] - 5 and r[2] <= HVB[2] and r[1] >= HVB[1] and r[3] <= HVB[3]
        overlaps_hv = not (r[2] <= HVB[2] + 0.0 and False) and not (r[0] >= P.BAR_X[1] or r[2] <= HVB[0] or r[3] <= HVB[1] or r[1] >= HVB[3])
        return inside_hv if hot else not overlaps_hv
    def hvline(fp): return any(re.search(r'(GEN|BUS)_(L\d|N)$', p.GetNetname()) for p in fp.Pads())
    def spiral(w, h, tx, ty, side, hot, tht, m, maxr=120.0):
        step = 0.5
        for k in range(int(maxr / step)):
            rr = k * step
            n = max(1, int(2 * math.pi * rr / step)) if rr else 1
            for i in range(n):
                ang = 2 * math.pi * i / n
                x, y = tx + rr * math.cos(ang), ty + rr * math.sin(ang)
                r = rect_at(w, h, x, y, m)
                if not region_ok(r, hot): continue
                if P.hits(r, obst[side]): continue
                if tht and P.hits(r, obst["F" if side == "B" else "B"]): continue
                return x, y
        return None

    # ---------- connectivity
    netpads = {}
    for ref, fp in fps.items():
        for p in fp.Pads():
            n = p.GetNetname()
            if n: netpads.setdefault(n, []).append((ref, p))
    sig_nets = {n: v for n, v in netpads.items() if not POWER_NETS.match(n) and 2 <= len({r for r, _ in v}) <= 12}
    def hot_part(ref): return "AC metering" in fps[ref].GetSheetname() and any("_AC" in p.GetNetname() or p.GetNetname().startswith(("V_", "I_", "GEN_", "BUS_")) for p in fps[ref].Pads()) and not any(p.GetNetname() in ("GND", "+3V3") for p in fps[ref].Pads())
    hot = {r for r in fps if "AC metering" in fps[r].GetSheetname() and not any(p.GetNetname() in ("GND", "+3V3", "+5V") for p in fps[r].Pads())}
    def pad_xy(p): v = p.GetPosition(); return TM(v.x), TM(v.y)
    def conn_centroid(ref, only=None):
        sx = sy = sw = 0.0
        for p in fps[ref].Pads():
            n = p.GetNetname()
            if n not in sig_nets: continue
            others = [(r, q) for r, q in sig_nets[n] if r != ref and (only is None or r in only)]
            if not others: continue
            w = 1.0 / len(sig_nets[n])
            for r, q in others:
                x, y = pad_xy(q); sx += w * x; sy += w * y; sw += w
        return (sx / sw, sy / sw, sw) if sw else None

    # ---------- ownership via schematic proximity
    sp = sch_positions()
    small = {r for r, fp in fps.items() if r not in placed and is_small(r, fp)}
    primaries = [r for r in fps if r not in placed and r not in small and not r.startswith(("H", "MH"))]
    anchors_for_owner = set(primaries) | placed
    owner = {}
    for r in small:
        if r not in sp: continue
        f, x, y = sp[r]
        cand = [(math.hypot(sp[o][1] - x, sp[o][2] - y), o) for o in anchors_for_owner if o in sp and sp[o][0] == f and not o.startswith("SW") or (o in sp and sp[o][0] == f and o.startswith("SW") and not o in [b_[0] for b_ in g.buttons()])]
        # prefer an owner the part actually shares a signal net with
        nets = {p.GetNetname() for p in fps[r].Pads()}
        shared = [(d * (0.5 if nets & {q.GetNetname() for q in fps[o].Pads()} else 1.0), o) for d, o in cand]
        if shared: owner[r] = min(shared)[1]
    kids = {}
    for r, o in owner.items(): kids.setdefault(o, []).append(r)
    def area(ref): w, h = P.size_mm(fps[ref]); return w * h

    # ---------- place primaries
    report = []
    def place_primary(ref, tx, ty, rot=None):
        fp = fps[ref]; side = "B"
        if rot is not None: P.put(fp, tx, ty, rot, side)
        else: P.put(fp, tx, ty, fp.GetOrientationDegrees(), side)
        w, h = P.size_mm(fp)
        ka = sum(area(k) for k in kids.get(ref, []))
        halo = a.halo + min(3.0, 0.25 * math.sqrt(ka)) if ka else a.halo
        res = spiral(w + 2 * halo, h + 2 * halo, tx, ty, side, ref in hot, is_tht(fp), 0.0)
        if res is None: res = spiral(w + 1.0, h + 1.0, tx, ty, side, ref in hot, is_tht(fp), 0.0, maxr=320)
        if res is None:   # last resort: rotate 90 deg
            P.put(fp, tx, ty, fp.GetOrientationDegrees() + 90, side); w, h = P.size_mm(fp)
            res = spiral(w + 1.0, h + 1.0, tx, ty, side, ref in hot, is_tht(fp), 0.0, maxr=320)
        if res is None:
            report.append(f"NO ROOM {ref}"); return False
        x, y = res
        P.put(fp, x, y, fp.GetOrientationDegrees(), side)
        # block only the body + small margin; the halo is reserved for its own passives first (placed right after)
        block(fp, 0.4); placed.add(ref)
        place_kids(ref)
        return True
    def place_kids(o):
        ks = sorted(kids.get(o, []), key=lambda r: -area(r))
        ofp = fps[o]; ocx, ocy = P.pad_centroid(ofp) if len(ofp.Pads()) else (TM(ofp.GetPosition().x), TM(ofp.GetPosition().y))
        for k in ks:
            fp = fps[k]
            onets = {}
            for p in ofp.Pads(): onets.setdefault(p.GetNetname(), []).append(p)
            tgt = None
            for p in fp.Pads():
                n = p.GetNetname()
                if n in onets and n and not n.startswith("GND"):
                    q = onets[n][0]; tgt = pad_xy(q); break
            if tgt is None:
                c = conn_centroid(k, placed); tgt = (c[0], c[1]) if c else (ocx, ocy)
            # push target slightly outward from the owner centre so the part lands at the pin, outside the body
            dx, dy = tgt[0] - ocx, tgt[1] - ocy; d = math.hypot(dx, dy) or 1.0
            tx, ty = tgt[0] + dx / d * 1.5, tgt[1] + dy / d * 1.5
            # orient 2-pin parts radially
            P.put(fp, tx, ty, 0 if abs(dx) > abs(dy) else 90, "B")
            w, h = P.size_mm(fp)
            g_ = 1.4 if hvline(fp) else a.small_gap   # HV parts keep >=1.5 mm (IPC-2221B B2, 600 V) between foreign HV copper
            res = spiral(w, h, tx, ty, "B", k in hot, is_tht(fp), g_, maxr=60) or spiral(w, h, tx, ty, "B", k in hot, is_tht(fp), min(g_, 1.0) if k in hot else 0.2, maxr=320)
            if res is None: report.append(f"NO ROOM small {k}"); continue
            P.put(fp, res[0], res[1], fp.GetOrientationDegrees(), "B"); block(fp, 0.15); placed.add(k)

    # place children of already-fixed parts (edge connectors, isolators, CM5 connectors, display connectors)
    # big seeded parts first (CTs/MOVs need contiguous room), then children of fixed parts
    for ref, (x, y, rot) in seeds.items():
        if ref in fps and ref not in placed: place_primary(ref, x, y, rot)
    for r in list(placed):
        if r in kids: place_kids(r)
    todo = [r for r in primaries if r not in placed]
    while todo:
        best = None
        for r in todo:
            c = conn_centroid(r, placed)
            score = c[2] if c else 0.0
            if best is None or score > best[0]: best = (score, r, c)
        score, r, c = best
        if c is None:
            sp_ = sp.get(r); tx, ty = (140.0, 90.0)
        else: tx, ty = c[0], c[1]
        if r in hot: tx, ty = min(max(tx, HVB[0] + 8), HVB[2] - 5), min(max(ty, HVB[1] + 5), HVB[3] - 5)
        place_primary(r, tx, ty); todo.remove(r)
    # orphans (no owner found)
    for r in small:
        if r in placed: continue
        fp = fps[r]; c = conn_centroid(r, placed); tx, ty = (c[0], c[1]) if c else (140, 90)
        w, h = P.size_mm(fp)
        res = spiral(w, h, tx, ty, "B", r in hot, is_tht(fp), 1.4 if hvline(fp) else a.small_gap, maxr=320)
        if res: P.put(fp, res[0], res[1], 0, "B"); block(fp, 0.15); placed.add(r)
        else: report.append(f"NO ROOM orphan {r}")

    # ---------- rule areas / keep-outs / marks (same as v3)
    for name, bbox, layers, t, v, p, f, pr in P.KEEPOUTS:
        if name == "CM5_BODY": continue
        P.rule_area(b, name, bbox, layers, t, v, p, f, pr)
    P.rule_area(b, "CM5_UNDER", CM5_IN, ["B.Cu"], fps=True)
    for i, (x, y) in enumerate(g.SHELL_POSTS):
        P.circle_area(b, f"SHELL_POST_{i+1}", x, y, g.SHELL_POST_KO / 2, ["B.Cu"], tracks=False, vias=False, pads=True, fps=True, pour=False)
    hx, hy = next((x, y) for r, x, y in g.MOUNT_HOLES if r == "H4")
    P.circle_area(b, "PE_BOSS_RING", hx, hy, g.PE_HOLE_D / 2 + 1.0, P.ALL_CU, pads=False, fps=False)
    for ref, x, y in g.buttons():
        P.gfx_rect(b, (x - g.SW_KO_W / 2, y - g.SW_KO_H / 2, x + g.SW_KO_W / 2, y + g.SW_KO_H / 2), pcbnew.Dwgs_User, 0.1)
    P.gfx_rect(b, P.CM5, pcbnew.Dwgs_User, 0.2); P.gfx_rect(b, P.STRAP_KO, pcbnew.Dwgs_User, 0.2)
    P.text(b, "CM5 55x40 (B side) - heat strap to H2 boss", (P.CM5[0] + P.CM5[2]) / 2, (P.CM5[1] + P.CM5[3]) / 2, 1.5, pcbnew.Dwgs_User)
    P.text(b, "PROJECT BLACKSTART", 177.5, 175.2, 3.0, pcbnew.B_SilkS, mirror=True)
    P.text(b, "genctl rev H  layout v4  CERN-OHL-S-2.0", 177.5, 179.0, 1.5, pcbnew.B_SilkS, mirror=True)
    P.text(b, "600V  HAZARDOUS VOLTAGE", 36.0, HVB[1] - 3.5, 2.0, pcbnew.B_SilkS, mirror=True)
    for r in report: print("WARN", r)
    unplaced = [r for r in fps if r not in placed and not r.startswith("H")]
    print(f"placed {len(placed)}/{len(fps)}; unplaced: {unplaced[:30]}")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    pcbnew.SaveBoard(a.out, b)

if __name__ == "__main__":
    main()
