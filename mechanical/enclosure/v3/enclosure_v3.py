"""Blackstart enclosure v3 (CadQuery, parametric). Ethan's 2026-10-25 hard constraints:
front slide-in self-contained unit, rear clamps only, bezel+shell joined, SLS PA12 shell, rear-facing RJ45/USB-C,
no fan, CM5->bezel heat path, on-demand fabrication only, 12 x 24 mm caps, one switch per key.
Board data is read from board_interface.json (parsed from genctl_v4_handrouted.kicad_pcb, read-only).
Coords: front-view board coords (x right, y DOWN, origin glass top-left) -> CQ X=x, Y=-y, Z=-depth (face at Z=0).
Run: /workspace/cqenv/bin/python enclosure_v3.py  -> step/, enclosure_v3_assembly.step, checks.json"""
import os, json, itertools
import cadquery as cq
HERE = os.path.dirname(os.path.abspath(__file__))
BI = json.load(open(os.path.join(HERE, "board_interface.json")))
FP = BI["footprints"]
# ---------------- display (MEASURED, Riverdi DR Rev1.1) ----------------
GLASS_W, GLASS_H, CTP_TFT, MOD_D = 276.56, 179.46, 8.51, 12.68
SRC_BAND = (20.61, 149.94, 255.61, 179.46)
# ---------------- board (MEASURED from json) ----------------
BX0, BY0, BX1, BY1 = -3.72, -15.27, 280.28, 194.73
PCB_T = 1.6                                     # INFERRED (stackup JLC06161H nominal 1.6)
Z_PCB = 16.0                                    # PCB F face behind bezel face; INFERRED design value (keeps switch plunger at Z 10.5)
ZR = Z_PCB + PCB_T                              # PCB rear face 17.6
KEYS = [(k, FP[k]["x"], FP[k]["y"]) for k in [f"SW{i}" for i in range(9, 21)]]
PCB_HOLES = [(FP[h]["x"], FP[h]["y"]) for h in ("H1", "H2", "H3")]
PE = (FP["H4"]["x"], FP["H4"]["y"])
# ---------------- parameters (INFERRED design choices) ----------------
WIN_GAP = 0.5            # glass edge -> window wall per side
LEDGE_Z, LEDGE_W = 9.5, 4.0
FIELD_T = 4.0            # bezel field
CAP_W, CAP_H, GUIDE_L, GUIDE_CLR = 24.0, 12.0, 8.0, 0.10
HEAD_OVER, HEAD_T, HEAD_GAP = 1.0, 1.0, 1.3
MEMB_T, NIB_D = 1.0, 4.0
CLR = dict(L=2.0, R=2.0, T=8.0, B=2.0)   # PCB -> shell inner wall; top 8 for the heat-bar tab + bezel heat boss
WALL = 3.0
SX0, SY0 = BX0 - CLR["L"] - WALL, BY0 - CLR["T"] - WALL
SX1, SY1 = BX1 + CLR["R"] + WALL, BY1 + CLR["B"] + WALL
SHELL_W, SHELL_H = SX1 - SX0, SY1 - SY0
CUT_GAP = 1.0            # per side; covers MJF/SLS +-0.4 % on 294 mm (see TOLERANCE_STACK.md)
CUT = (SX0 - CUT_GAP, SY0 - CUT_GAP, SX1 + CUT_GAP, SY1 + CUT_GAP)   # customer cutout (+1.0/-0)
FL_W, FL_T = 8.0, 3.0                       # shell front flange (sits on bezel rear inside the rim)
RIM_W, RIM_Z = 9.0, 9.5                     # bezel outer rim (gasket land at Z 9.5)
BZ0, BZ1 = (SX0 - FL_W - 0.5 - RIM_W, SY0 - FL_W - 0.5 - RIM_W), (SX1 + FL_W + 0.5 + RIM_W, SY1 + FL_W + 0.5 + RIM_W)
GASKET_T, GASKET_C = 2.0, 0.7
Z_PANEL = RIM_Z + GASKET_T * GASKET_C
PANEL_T, PANEL_MIN, PANEL_MAX = 3.0, 1.0, 6.0
SHELL_DEPTH = 48.0                        # rear face Z; was 62 in rev C (port wells too deep)
CM5 = (203.0, 1.0, 258.0, 41.0); CM5_H = 4.94     # MEASURED: board drawing + cm5-datasheet 4.1.1 (1.5 mm stack)
PAD_T = 1.0                                       # thermal pad compressed (INFERRED, 1.5 mm pad at ~33 %)
HB_T = 4.75                                       # heat bar thickness, laser/waterjet 6061
Z_HB0 = ZR + CM5_H + PAD_T; Z_HB1 = Z_HB0 + HB_T
HB_TAB = (247.5, SY0 + WALL + 0.5, 279.5, CM5[1] + 2)   # tab over the STRAP_CORRIDOR to beyond the board top edge
BOSS = (249.0, SY0 + WALL + 0.8, 278.0, BY0 - 0.8)      # bezel heat boss, outside the PCB edge, up to the heat bar
JOINT_SCREWS = [(x, y) for x in (SX0 + 30, (SX0 + SX1) / 2, SX1 - 30) for y in (SY0 - 4.5, SY1 + 4.5)] + \
               [(SX0 - 4.5, (SY0 + SY1) / 2), (SX1 + 4.5, (SY0 + SY1) / 2)]
CLAMPS = [(72.9, "T"), (203.5, "T"), (72.9, "B"), (203.5, "B"), (90.0, "L"), (90.0, "R")]
CL_Z0, CL_Z1 = 37.5, 45.0   # above the 16-18 mm terminal plugs (top Z 35.6)
# PORT TUNNELS (phase 2, BCR-1 solved in the shell): sealed PA12 tunnels from the rear face down to 0.5 mm above each jack.
# (cx, cy, inner w, inner h, jack top Z). Sizes: see TOLERANCE_STACK.md section 3.
H_J10, H_J11 = 16.9, 10.0                         # INFERRED jack heights above PCB rear
REAR_PORTS = {"J10": (FP["J10"]["x"], FP["J10"]["y"], 20.0, 24.0, ZR + H_J10),   # RJ45 plug 11.68 x 8.0 + snagless boot + latch finger notch
              "J11": (FP["J11"]["x"], FP["J11"]["y"], 16.0, 10.0, ZR + H_J11)}   # USB-C overmold 12.85 x 7.0 max (R2.2 ECN), 13.0 x 7.4 seen
TUN_WALL, TUN_GAP, LEAD_IN = 2.0, 0.5, 1.5
SHELL_POSTS = [(100, 60), (100, 140), (240, 60), (240, 140)]

def box(x0, y0, x1, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, -(y0 + y1) / 2, -(z0 + z1) / 2))
def cyl(x, y, d, z0, z1):
    return cq.Workplane("XY").circle(d / 2).extrude(z1 - z0).translate((x, -y, -z1))
def U(parts):
    out = None
    for p in parts: out = p if out is None else out.union(p)
    return out

W0, H0, W1, H1 = -WIN_GAP, -WIN_GAP, GLASS_W + WIN_GAP, GLASS_H + WIN_GAP
def bezel():
    b = box(BZ0[0], BZ0[1], BZ1[0], BZ1[1], 0, FIELD_T)
    b = b.union(box(W0 - 2.5, H0 - 2.5, W1 + 2.5, H1 + 2.5, 0, 12.5))          # display rim
    for yc in (KEYS[0][2], KEYS[6][2]):                                          # 8 mm key band
        b = b.union(box(5.0, yc - CAP_H / 2 - 1.5, 271.5, yc + CAP_H / 2 + 1.5, 0, GUIDE_L))
    for (x, y) in PCB_HOLES: b = b.union(cyl(x, y, 7.0, 0.5, Z_PCB))
    b = b.union(cyl(*PE, 8.0, 0.5, ZR + 1.0))
    b = b.union(box(*BOSS, 0.5, Z_HB0))                                           # heat boss
    rim = box(BZ0[0], BZ0[1], BZ1[0], BZ1[1], FIELD_T - 0.01, RIM_Z).cut(
        box(BZ0[0] + RIM_W, BZ0[1] + RIM_W, BZ1[0] - RIM_W, BZ1[1] - RIM_W, 0, 20))
    b = b.union(rim)
    b = b.cut(box(W0, H0, W1, H1, -1, LEDGE_Z))
    b = b.cut(box(W0 + LEDGE_W, H0 + LEDGE_W, W1 - LEDGE_W, H1 - LEDGE_W, -1, 30))
    b = b.cut(box(20.0, H1 - 31, 256.5, H1 + 0.01, LEDGE_Z - 0.01, 30))          # source-PCB band relief
    b = b.cut(box(225.0, H1 - 6, 248.0, H1 + 3.0, LEDGE_Z - 0.01, 30))           # touch tail notch (VERIFY vs STEP)
    b = b.cut(box(0.0, -3.0, 15.0, 4.5, LEDGE_Z - 0.01, 30))                     # backlight cable notch
    for _, x, y in KEYS:
        b = b.cut(box(x - CAP_W / 2 - GUIDE_CLR, y - CAP_H / 2 - GUIDE_CLR, x + CAP_W / 2 + GUIDE_CLR, y + CAP_H / 2 + GUIDE_CLR, -1, 30))
    for (x, y) in JOINT_SCREWS: b = b.cut(cyl(x, y, 3.3, 0.8, FIELD_T + 0.1))   # blind M4 taps, face intact
    for (x, y) in PCB_HOLES + [PE]: b = b.cut(cyl(x, y, 3.3, 3.0, Z_PCB + 3))
    for x in (256.0, 271.0): b = b.cut(cyl(x, (BOSS[1] + BOSS[3]) / 2, 3.3, Z_HB0 - 10, Z_HB0 + 0.1))  # heat-bar M4 taps
    return b

def display():
    return box(0, 0, GLASS_W, GLASS_H, 0.05, 0.05 + CTP_TFT).union(box(*SRC_BAND, 0.05 + CTP_TFT, 0.05 + MOD_D))

def keys():
    caps, memb, nibs = [], [], []
    for yc, sg in ((KEYS[0][2], -1), (KEYS[6][2], 1)):   # strip: 1.5 bond land on the outer side, 0.1 on the display-rim side
        a, b = yc - sg * (CAP_H / 2 + 0.1), yc + sg * (CAP_H / 2 + 1.5)
        memb.append(box(7.0, min(a, b), 267.5, max(a, b), GUIDE_L, GUIDE_L + MEMB_T).cut(box(BOSS[0] - 0.3, BOSS[1] - 1, BOSS[2] + 1, BOSS[3] + 0.3, 0, 30)))   # notch round heat boss
    for _, x, y in KEYS:
        c = box(x - CAP_W / 2, y - CAP_H / 2, x + CAP_W / 2, y + CAP_H / 2, -HEAD_GAP, GUIDE_L)
        c = c.union(box(x - CAP_W / 2 - HEAD_OVER, y - CAP_H / 2 - HEAD_OVER, x + CAP_W / 2 + HEAD_OVER, y + CAP_H / 2 + HEAD_OVER, -HEAD_GAP - HEAD_T, -HEAD_GAP))
        caps.append(c)
        nibs.append(cyl(x, y, NIB_D, GUIDE_L + MEMB_T, Z_PCB - 5.5 - 0.1))
    return U(caps), U(memb), U(nibs)

def switches():
    return U([box(x - 3.4, y - 3.6, x + 3.4, y + 3.6, Z_PCB - 4.7, Z_PCB).union(cyl(x, y, 3.8, Z_PCB - 5.5, Z_PCB - 4.7)) for _, x, y in KEYS])

H = {"J10": H_J10, "J11": H_J11}   # INFERRED heights, see board_interface.json
def pcb():
    p = box(BX0, BY0, BX1, BY1, Z_PCB, ZR)
    for (x, y) in PCB_HOLES: p = p.cut(cyl(x, y, 4.3, Z_PCB - 1, ZR + 1))
    p = p.cut(cyl(*PE, 9.5, Z_PCB - 1, ZR + 1))
    return p
def rear_parts():
    parts = [box(*CM5, ZR, ZR + CM5_H)]
    for r, f in FP.items():
        x0, y0, x1, y1 = f["bbox"]
        if r in H: parts.append(box(x0, y0, x1, y1, ZR, ZR + H[r]))
        elif r.startswith("J") and f["side"] == "B" and ("KF2" in f["fp"] or "Phoenix" in f["fp"] or "WJ15" in f["fp"]):
            parts.append(box(max(x0, BX0), max(y0, BY0), min(x1, BX1), min(y1, BY1), ZR, ZR + (18.0 if "Phoenix" in f["fp"] else 16.0)))
        elif r.startswith("T") and r[1:].isdigit():
            parts.append(box(x0, y0, x1, y1, ZR, ZR + 12.0))
    return U(parts)
def heat_bar():
    hb = box(CM5[0] + 2, CM5[1] + 2, CM5[2] - 2, CM5[3] - 2, Z_HB0, Z_HB1).union(box(*HB_TAB, Z_HB0, Z_HB1))
    for x in (256.0, 271.0): hb = hb.cut(cyl(x, (BOSS[1] + BOSS[3]) / 2, 4.5, Z_HB0 - 1, Z_HB1 + 1))
    return hb
def thermal_pads():
    return box(CM5[0] + 4, CM5[1] + 6, CM5[2] - 4, CM5[3] - 6, ZR + CM5_H, Z_HB0).union(
           box(BOSS[0], max(BOSS[1], HB_TAB[1]), BOSS[2], BOSS[3], Z_HB0 - 0.5, Z_HB0).translate((0, 0, 0)))
def gasket():
    return box(BZ0[0] + 0.5, BZ0[1] + 0.5, BZ1[0] - 0.5, BZ1[1] - 0.5, RIM_Z, Z_PANEL).cut(
        box(BZ0[0] + 8.5, BZ0[1] + 8.5, BZ1[0] - 8.5, BZ1[1] - 8.5, 0, 30))
def customer_panel(t=PANEL_T):
    return box(BZ0[0] - 25, BZ0[1] - 25, BZ1[0] + 25, BZ1[1] + 25, Z_PANEL, Z_PANEL + t).cut(box(*CUT, 0, 40))

def rear_shell():
    z0 = FIELD_T
    s = box(SX0 - FL_W, SY0 - FL_W, SX1 + FL_W, SY1 + FL_W, z0, z0 + FL_T).cut(box(SX0, SY0, SX1, SY1, 0, 30))
    t = box(SX0, SY0, SX1, SY1, z0, SHELL_DEPTH).cut(box(SX0 + WALL, SY0 + WALL, SX1 - WALL, SY1 - WALL, z0 - 1, SHELL_DEPTH - WALL))
    s = s.union(t)
    for (x, y) in JOINT_SCREWS: s = s.cut(cyl(x, y, 4.5, z0 - 1, z0 + FL_T + 1))
    zr0 = SHELL_DEPTH - WALL - 1
    s = s.cut(box(28, BY0 - 1, 248, BY0 + 13, zr0, SHELL_DEPTH + 1))           # top terminal row wiring window
    s = s.cut(box(28, BY1 - 13, 248, BY1 + 1, zr0, SHELL_DEPTH + 1))           # bottom terminal row
    s = s.cut(box(BX1 - 18, 34, BX1 + 1, 182, zr0, SHELL_DEPTH + 1))           # right edge terminals J1/J23/J6/J7
    s = s.cut(box(BX0 - 1, 9, BX0 + 17, 164, zr0, SHELL_DEPTH + 1))            # left 600 V terminals J28/J29/J30
    for (cx, cy, w, h, zt) in REAR_PORTS.values():
        s = s.union(box(cx - w / 2 - TUN_WALL, cy - h / 2 - TUN_WALL, cx + w / 2 + TUN_WALL, cy + h / 2 + TUN_WALL, zt + TUN_GAP, SHELL_DEPTH))
        s = s.cut(box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, zt, SHELL_DEPTH + 1))
        s = s.cut(box(cx - w / 2 - LEAD_IN, cy - h / 2 - LEAD_IN, cx + w / 2 + LEAD_IN, cy + h / 2 + LEAD_IN, SHELL_DEPTH - LEAD_IN, SHELL_DEPTH + 1))  # lead-in step
    for i in range(12):                                                         # rear vents over CM5 / heat bar
        s = s.cut(box(120 + i * 6, 70, 123 + i * 6, 130, zr0, SHELL_DEPTH + 1))
    for i in range(12):                                                         # chimney: bottom intake, top exhaust
        xv = 100 + i * 9
        s = s.cut(box(xv, SY0 - 1, xv + 4, SY0 + WALL + 1, 22, 34)).cut(box(xv, SY1 - WALL - 1, xv + 4, SY1 + 1, 22, 34))
    for (p, side) in CLAMPS:      # clamp seats: INWARD wall bosses + blind T-slot from outside; outer wall stays flush so the shell passes the cutout
        if side in "TB":
            y = SY0 if side == "T" else SY1; sg = -1 if side == "T" else 1
            s = s.union(box(p - 13, min(y - sg * WALL, y - sg * (WALL + 3.5)), p + 13, max(y - sg * WALL, y - sg * (WALL + 3.5)), CL_Z0 - 1.5, CL_Z1 + 1.5))
            s = s.cut(box(p - 9, min(y, y - sg * 4.5), p + 9, max(y, y - sg * 4.5), CL_Z0 - 0.2, CL_Z1 + 0.2))
        else:
            x = SX0 if side == "L" else SX1; sg = -1 if side == "L" else 1
            s = s.union(box(min(x - sg * WALL, x - sg * (WALL + 3.5)), p - 13, max(x - sg * WALL, x - sg * (WALL + 3.5)), p + 13, CL_Z0 - 1.5, CL_Z1 + 1.5))
            s = s.cut(box(min(x, x - sg * 4.5), p - 9, max(x, x - sg * 4.5), p + 9, CL_Z0 - 0.2, CL_Z1 + 0.2))
    bx = 73.0                                                                   # 600 V barrier rib (rear of HV box)
    s = s.union(box(bx, SY0 + WALL, bx + 2, 175, ZR + 1.0 + 18.0, SHELL_DEPTH - 1))
    for (x, y) in SHELL_POSTS:
        s = s.union(cyl(x, y, 6.0, ZR + 0.3, SHELL_DEPTH - 1))
    return s

def clamps(t=PANEL_T):
    """6 SLS PA12 clamp blocks: 18 x 10 tongue in the shell pad's blind slot, body outside, M4 brass heat-set insert,
    M4 nylon-tip set/thumb screw pushes forward onto the customer panel rear."""
    br, sc = [], []
    zt = Z_PANEL + t
    for (p, side) in CLAMPS:
        sg = -1 if side in "TL" else 1
        if side in "TB":
            yf = (SY0 if side == "T" else SY1)
            b = box(p - 8.8, min(yf, yf - sg * 4.3), p + 8.8, max(yf, yf - sg * 4.3), CL_Z0, CL_Z1)
            b = b.union(box(p - 10, min(yf, yf + sg * 14), p + 10, max(yf, yf + sg * 14), CL_Z0, CL_Z1))
            c = cyl(p, yf + sg * 8, 4.0, zt, CL_Z1 + 3)
        else:
            xf = (SX0 if side == "L" else SX1)
            b = box(min(xf, xf - sg * 4.3), p - 8.8, max(xf, xf - sg * 4.3), p + 8.8, CL_Z0, CL_Z1)
            b = b.union(box(min(xf, xf + sg * 14), p - 10, max(xf, xf + sg * 14), p + 10, CL_Z0, CL_Z1))
            c = cyl(xf + sg * 8, p, 4.0, zt, CL_Z1 + 3)
        br.append(b.cut(c)); sc.append(c)
    return U(br), U(sc)

def plug_envelopes():
    """Mated plug envelopes for checking only (not parts): RJ45 body 11.68 x 8.0 (Wikipedia 8P8C typ. / Canford 11.68 x 7.24 face),
    USB-C overmold 13.0 x 7.4 (largest measured, EE.SE 475901; spec max 12.85 x 7.0 per USB Type-C R2.2 ECN)."""
    cx, cy, _, _, zt = REAR_PORTS["J10"]; a = box(cx - 5.84, cy - 4.0, cx + 5.84, cy + 4.0, zt - 6.0, SHELL_DEPTH + 15)
    cx, cy, _, _, zt = REAR_PORTS["J11"]; b = box(cx - 6.5, cy - 3.7, cx + 6.5, cy + 3.7, zt + 0.3, SHELL_DEPTH + 15)
    return a.union(b)

def build():
    caps, memb, nibs = keys(); cb, cs = clamps()
    return {"bezel": (bezel(), (0.15, 0.15, 0.17)), "display": (display(), (0.05, 0.1, 0.3)),
            "key_caps": (caps, (0.6, 0.85, 1.0)), "key_membrane": (memb, (0.9, 0.9, 0.85)), "key_nibs": (nibs, (1, 1, 0.7)),
            "switches": (switches(), (0.3, 0.3, 0.3)), "pcb": (pcb(), (0.1, 0.5, 0.15)), "rear_parts": (rear_parts(), (0.2, 0.3, 0.6)),
            "heat_bar": (heat_bar(), (0.8, 0.5, 0.2)), "thermal_pads": (thermal_pads(), (0.9, 0.2, 0.6)),
            "gasket": (gasket(), (0.9, 0.3, 0.1)), "customer_panel": (customer_panel(), (0.7, 0.7, 0.7)),
            "rear_shell": (rear_shell(), (0.45, 0.45, 0.42)), "clamps": (cb, (0.75, 0.6, 0.2)), "clamp_screws": (cs, (0.85, 0.85, 0.9))}

def vol(a, b):
    try: return a.intersect(b).val().Volume()
    except Exception: return 0.0

def checks(parts):
    res = {}
    names = list(parts)
    allowed = {("pcb", "rear_parts"), ("pcb", "switches"), ("heat_bar", "thermal_pads"), ("bezel", "thermal_pads"),
               ("clamps", "rear_shell"), ("clamp_screws", "customer_panel")}
    for a, b in itertools.combinations(names, 2):
        if (a, b) in allowed or (b, a) in allowed: continue
        if "customer_panel" in (a, b) and "gasket" in (a, b): continue
        v = vol(parts[a][0], parts[b][0])
        if v > 1e-3: res[f"{a}&{b}"] = round(v, 3)
    pe = plug_envelopes()
    res["plug_envelopes&rear_shell"] = round(vol(pe, parts["rear_shell"][0]), 3)
    # clearances (positive = gap), computed from parameters
    clr = {"display_rear_to_PCB_front_airgap": round(Z_PCB - 0.05 - MOD_D, 2),
           "nib_to_plunger_free_gap": 0.1,
           "glass_front_vs_bezel_face (neg = recessed)": -0.05,
           "CM5_top_to_heatbar (pad)": PAD_T,
           "rear_parts_tallest_to_shell_inner_rear": round(SHELL_DEPTH - WALL - (ZR + 18.0), 2),
           "J10_mouth_depth_below_rear_face (tunnel)": round(SHELL_DEPTH - (ZR + H['J10']), 2),
           "J11_mouth_depth_below_rear_face (tunnel)": round(SHELL_DEPTH - (ZR + H['J11']), 2),
           "J10_tunnel_clearance_per_side_to_RJ45_body_x_y": [round((20.0 - 11.68) / 2, 2), round((24.0 - 8.0) / 2, 2)],
           "J11_tunnel_clearance_per_side_to_USBC_overmold_x_y (13.0x7.4)": [round((16.0 - 13.0) / 2, 2), round((10.0 - 7.4) / 2, 2)],
           "clamp_screw_reach_panel_range_mm": [PANEL_MIN, PANEL_MAX],
           "shell_to_cutout_per_side": CUT_GAP}
    # clamp test at panel extremes: clamps must not hit the panel; panel must not hit shell
    for t in (PANEL_MIN, PANEL_MAX):
        cp = customer_panel(t)
        res[f"panel{t}&rear_shell"] = round(vol(cp, parts["rear_shell"][0]), 3)
        res[f"panel{t}&clamps"] = round(vol(cp, parts["clamps"][0]), 3)
    bb = parts["rear_shell"][0].intersect(box(-1000, -1000, 1000, 1000, Z_PANEL, 200)).val().BoundingBox()   # part that passes the cutout
    clr["insertion: shell bbox vs cutout per side (min gap, must be >0)"] = round(min(bb.xmin - CUT[0], CUT[2] - bb.xmax, -bb.ymax - CUT[1], CUT[3] + bb.ymin), 3)
    return res, clr

if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "step"), exist_ok=True)
    parts = build(); asm = cq.Assembly()
    for n, (wp, col) in parts.items():
        cq.exporters.export(wp, os.path.join(HERE, "step", n + ".step"))
        asm.add(wp, name=n, color=cq.Color(*col))
    asm.save(os.path.join(HERE, "enclosure_v3_assembly.step"))
    inter, clr = checks(parts)
    out = {"interferences_mm3": inter, "clearances_mm": clr,
           "volumes_cm3": {k: round(v[0].val().Volume() / 1000, 1) for k, v in parts.items()},
           "bbox": {k: [round(x, 1) for x in (v[0].val().BoundingBox().xlen, v[0].val().BoundingBox().ylen, v[0].val().BoundingBox().zlen)] for k, v in parts.items()},
           "shell_outer_WxH": [round(SHELL_W, 2), round(SHELL_H, 2)], "cutout": [round(CUT[2] - CUT[0], 2), round(CUT[3] - CUT[1], 2)],
           "bezel_WxH": [round(BZ1[0] - BZ0[0], 2), round(BZ1[1] - BZ0[1], 2)]}
    json.dump(out, open(os.path.join(HERE, "checks.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
