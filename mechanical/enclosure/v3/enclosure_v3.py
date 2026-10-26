
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
PE = (FP["H4"]["x"], FP["H4"]["y"])          # H4: plain NPTH clearance hole since phase 14 (no PE function)
PE_NEW = (12.3, -7.5)    # phase 14: new bezel PE boss near J28/J29 (BCR-11 NPTH Ø9.5); (16, 3) is behind the glass -> moved
# ---------------- parameters (INFERRED design choices) ----------------
WIN_GAP = 0.5            # glass edge -> window wall per side
# PHASE 6 (Ethan, Oct 25): glass FLUSH with the PA12 ring face. The display moves 4 mm forward (DZ) into the ring opening.
DZ = -4.0                # = -(RING_GAP + RING_T); glass front at Z -3.95 (flush with ring face at -4.0, 0.05 nominal tape allowance)
SLEEVE = 1.5             # PA12 ring sleeve between glass edge and metal window (thermal break), 0.5 silicone bead gap to glass
LEDGE_Z, LEDGE_W = 9.5 + DZ, 4.0
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
CLAMPS = [(72.9, "T"), (203.5, "T"), (72.9, "B"), (203.5, "B"), (2.0, "L"), (118.0, "L"), (178.0, "L"), (90.0, "R")]   # phase 13: left clamps y 2 / 118 / 178 (slots y -7..11, 109..127, 169..187), none in y 15-105; insert >= 12.6 from J28/J29 plugs
CL_Z0, CL_Z1 = 37.5, 45.0   # above the 16-18 mm terminal plugs (top Z 35.6)
# PORT TUNNELS (phase 2, BCR-1 solved in the shell): sealed PA12 tunnels from the rear face down to 0.5 mm above each jack.
# (cx, cy, inner w, inner h, jack top Z). Sizes: see TOLERANCE_STACK.md section 3.
H_J10, H_J11 = 16.9, 10.0                         # INFERRED jack heights above PCB rear
REAR_PORTS = {"J10": (FP["J10"]["x"], FP["J10"]["y"], 20.0, 24.0, ZR + H_J10),   # RJ45 plug 11.68 x 8.0 + snagless boot + latch finger notch
              "J11": (FP["J11"]["x"], FP["J11"]["y"], 16.0, 10.0, ZR + H_J11)}   # USB-C overmold 12.85 x 7.0 max (R2.2 ECN), 13.0 x 7.4 seen
TUN_WALL, TUN_GAP, LEAD_IN = 2.0, 0.5, 1.5
SHELL_POSTS = [(100, 60), (100, 140), (240, 60), (240, 140)]
# PHASE 4 thermal option D: heat goes to a rear Al fin plate (not touched), PA12 front ring is the touch surface
RING_T, RING_GAP = 3.0, 1.0                       # PA12 ring 3 mm, 1 mm air thermal break in front of the bezel face
FP_T, FIN_H, FIN_T, FIN_PITCH = 4.75, 30.0, 2.0, 8.0   # 6061 base (laser/waterjet), laser-cut 2 mm fin slats in milled slots
FIN_PLATE = (16.0, 1.0, 258.0, 178.0)             # inside the terminal wiring windows
REAR_OPEN = (20.0, 4.0, 255.0, 176.0)             # PA12 rear wall opening under the plate
PILLAR = (210.0, 8.0, 250.0, 36.0)                # 6061 block heat bar -> fin plate
PORT_CLEAR = (196.0, 30.0, 256.0, 75.0)           # no fins around J10/J11 plugs
# PHASE 9 (Ethan GO, Oct 25): V6 = flat 4.75 mm 6061 plate + ATS-EXL1 strip + two 40 mm sealed fans (push-pull)
EXL1_W, EXL1_H, EXL1_N, EXL1_L = 100.76, 10.0, 40, 177.0   # MEASURED ATS R15_0121 (W, H, fin count); 177 cut from the 254 stick
EXL1_BASE, EXL1_FT = 2.0, 1.0                     # ASSUMED (base thickness / fin thickness not given in R15_0121); fin height = 10 - 2 = 8 mm
STRIP_X0 = FIN_PLATE[2] - EXL1_W                  # strip right edge flush with the plate edge, over the CM5 pillar (210-250)
STRIP_Y0 = FIN_PLATE[1]
STRIP_PAD = 0.5                                   # gap pad plate -> strip base (0.5 mm, ESTIMATED)
STRIP_SCREWS = [(STRIP_X0 + 6, STRIP_Y0 + 6), (STRIP_X0 + EXL1_W - 6, STRIP_Y0 + 6), (STRIP_X0 + 6, STRIP_Y0 + EXL1_L - 6), (STRIP_X0 + EXL1_W - 6, STRIP_Y0 + EXL1_L - 6)]
FAN_S, FAN_T, FAN_HOLE, FAN_PITCH = 40.0, 10.5, 38.0, 32.0   # Orion OD4010 envelope 40 x 40 x 10.5 (MEASURED datasheet), M3 holes on 32 mm
FAN_GASKET, FILTER_T = 1.0, 4.0                   # closed-cell gasket under each fan; washable foam filter in a PA12 snap cover
FANS = {"fan_exhaust": (128.0, 26.0), "fan_intake": (128.0, 152.0)}   # centres (x, y) on the plate outer face; push-pull in series
# ambient light sensor (BCR-8): window centre in the cover-glass frame
ALS = (138.18, -9.25); ALS_D, ALS_BORE = 4.0, 4.2   # phase 5: moved to SW11-SW12 gap centre (was 11.0)
ALS_Z_TOP = Z_PCB - 1.0                           # light-pipe rear face; sensor on PCB F side, <=0.7 mm tall + 0.3 gap

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
    b = b.union(cyl(*PE_NEW, 8.0, 0.5, ZR + 1.0))                                # phase 14 PE boss (H4 boss deleted)
    b = b.union(box(*BOSS, 0.5, Z_HB0))                                           # heat boss
    rim = box(BZ0[0], BZ0[1], BZ1[0], BZ1[1], FIELD_T - 0.01, RIM_Z).cut(
        box(BZ0[0] + RIM_W, BZ0[1] + RIM_W, BZ1[0] - RIM_W, BZ1[1] - RIM_W, 0, 20))
    b = b.union(rim)
    b = b.cut(box(W0 - SLEEVE, H0 - SLEEVE, W1 + SLEEVE, H1 + SLEEVE, -1, LEDGE_Z - 0.5))   # window + ring sleeve pocket
    b = b.cut(box(W0, H0, W1, H1, -1, LEDGE_Z))
    b = b.cut(box(W0 + LEDGE_W, H0 + LEDGE_W, W1 - LEDGE_W, H1 - LEDGE_W, -1, 30))
    b = b.cut(box(20.0, H1 - 31, 256.5, H1 + 0.01, LEDGE_Z - 0.01, 30))          # source-PCB band relief
    b = b.cut(box(225.0, H1 - 6, 248.0, H1 + 3.0, LEDGE_Z - 0.01, 30))           # touch tail notch (VERIFY vs STEP)
    b = b.cut(box(0.0, -3.0, 15.0, 4.5, LEDGE_Z - 0.01, 30))                     # backlight cable notch
    for _, x, y in KEYS:
        b = b.cut(box(x - CAP_W / 2 - GUIDE_CLR, y - CAP_H / 2 - GUIDE_CLR, x + CAP_W / 2 + GUIDE_CLR, y + CAP_H / 2 + GUIDE_CLR, -1, 30))
    for (x, y) in JOINT_SCREWS: b = b.cut(cyl(x, y, 3.3, 0.8, FIELD_T + 0.1))   # blind M4 taps, face intact
    b = b.cut(cyl(*ALS, ALS_BORE, -1, 30))                                        # ALS light-pipe bore
    for (x, y) in PCB_HOLES + [PE_NEW]: b = b.cut(cyl(x, y, 3.3, 3.0, Z_PCB + 3))
    for x in (256.0, 271.0): b = b.cut(cyl(x, (BOSS[1] + BOSS[3]) / 2, 3.3, Z_HB0 - 10, Z_HB0 + 0.1))  # heat-bar M4 taps
    # PHASE 9 compliance fix: display-tray rim (earthed Al) came within 1.52 mm of the J28/J29 THT lead tips
    # (basic 5.5 mm required). Trim the rim rear edge to Z <= HV_RIM_Z over y 10..115 (left side only).
    b = b.cut(box(BX0 - 6.0, 10.0, 12.0, 115.0, HV_RIM_Z, Z_PCB))
    return b

def display():
    z = 0.05 + DZ
    return box(0, 0, GLASS_W, GLASS_H, z, z + CTP_TFT).union(box(*SRC_BAND, z + CTP_TFT, z + MOD_D))

def keys():
    caps, memb, nibs = [], [], []
    for yc, sg in ((KEYS[0][2], -1), (KEYS[6][2], 1)):   # strip: 1.5 bond land on the outer side, 0.1 on the display-rim side
        a, b = yc - sg * (CAP_H / 2 + 0.1), yc + sg * (CAP_H / 2 + 1.5)
        memb.append(box(7.0, min(a, b), 267.5, max(a, b), GUIDE_L, GUIDE_L + MEMB_T).cut(box(BOSS[0] - 0.3, BOSS[1] - 1, BOSS[2] + 1, BOSS[3] + 0.3, 0, 30)).cut(cyl(*ALS, 5.0, 0, 30)).cut(cyl(*PE_NEW, 9.0, 0, 30)))   # phase 14: notch round PE boss   # notch round heat boss, ALS hole
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
    p = p.cut(cyl(*PE, 9.5, Z_PCB - 1, ZR + 1))      # H4 (stays, plain clearance)
    p = p.cut(cyl(*PE_NEW, 9.5, Z_PCB - 1, ZR + 1))  # BCR-11 proposed hole (not on the board yet)
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
    s = s.cut(box(BX1 - 18, 34, BX1 + 1, 182, zr0, SHELL_DEPTH + 1))           # right edge terminals J1/J23/J6/J7 (phase 14: back to y 182)
    s = s.cut(box(3.0, -21.0, 20.0, -1.0, zr0, SHELL_DEPTH + 1))              # phase 14: PE lug access window over PE_NEW (rear wall only)
    s = s.cut(box(BX0 - 1, 9, BX0 + 17, 164, zr0, SHELL_DEPTH + 1))            # left 600 V terminals J28/J29/J30
    s = s.cut(box(*REAR_OPEN, zr0, SHELL_DEPTH + 1))                          # phase 4: opening under the Al fin plate
    for (cx, cy, w, h, zt) in REAR_PORTS.values():
        s = s.union(box(cx - w / 2 - TUN_WALL, cy - h / 2 - TUN_WALL, cx + w / 2 + TUN_WALL, cy + h / 2 + TUN_WALL, zt + TUN_GAP, SHELL_DEPTH))
        s = s.cut(box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, zt, SHELL_DEPTH + 1))
        s = s.cut(box(cx - w / 2 - LEAD_IN, cy - h / 2 - LEAD_IN, cx + w / 2 + LEAD_IN, cy + h / 2 + LEAD_IN, SHELL_DEPTH - LEAD_IN, SHELL_DEPTH + 1))  # lead-in step
    # phase 15: the 2 x 12 chimney slots (pre-fan passive design) are DELETED: they were unfiltered side openings bypassing the
    # fan filters (PD2 basis). The phase-9 thermal model never credited them (both-failed path = stalled rotors + filters).
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
    M4 thumb screw pushes forward onto the customer panel rear. Phase 14: LEFT clamps (HV side) use all-nylon PA66 M4x35 screws (non-conductive); T/B/R keep nylon-tip steel."""
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

def front_ring():
    r = box(BZ0[0], BZ0[1], BZ1[0], BZ1[1], -RING_GAP - RING_T, -RING_GAP).cut(box(W0, H0, W1, H1, -10, 1))
    r = r.union(box(W0 - SLEEVE + 0.2, H0 - SLEEVE + 0.2, W1 + SLEEVE - 0.2, H1 + SLEEVE - 0.2, -RING_GAP - 0.01, LEDGE_Z - 1.0).cut(box(W0, H0, W1, H1, -10, 30)))   # sleeve
    for _, x, y in KEYS:
        r = r.cut(box(x - CAP_W / 2 - HEAD_OVER - 0.4, y - CAP_H / 2 - HEAD_OVER - 0.4, x + CAP_W / 2 + HEAD_OVER + 0.4, y + CAP_H / 2 + HEAD_OVER + 0.4, -10, 1))
    r = r.cut(cyl(*ALS, ALS_BORE, -10, 1))
    for (x, y) in JOINT_SCREWS[:6]: r = r.union(cyl(x, y - 6 if y < 0 else y + 6, 5.0, -RING_GAP - 0.01, 0))   # PA12 stand-off pips (thermal break)
    return r
def fin_plate():
    """V6: flat 4.75 mm 6061 plate (laser cut) closing the PA12 rear opening; fan holes; strip screw holes."""
    f = box(*FIN_PLATE, SHELL_DEPTH, SHELL_DEPTH + FP_T)
    for (cx, cy, w, h, zt) in REAR_PORTS.values():
        f = f.cut(box(cx - w / 2 - TUN_WALL - 0.5, cy - h / 2 - TUN_WALL - 0.5, cx + w / 2 + TUN_WALL + 0.5, cy + h / 2 + TUN_WALL + 0.5, 0, 200))
    for (x, y) in SHELL_POSTS: f = f.cut(cyl(x, y, 4.5, 0, 200))
    for (x, y) in FANS.values():
        f = f.cut(cyl(x, y, FAN_HOLE, 0, 200))
        for dx in (-1, 1):
            for dy in (-1, 1): f = f.cut(cyl(x + dx * FAN_PITCH / 2, y + dy * FAN_PITCH / 2, 2.5, 0, 200))   # M3 tapping 2.5
    for (x, y) in STRIP_SCREWS: f = f.cut(cyl(x, y, 2.5, 0, 200))
    return f
def exl1_strip():
    z0 = SHELL_DEPTH + FP_T + STRIP_PAD
    st = box(STRIP_X0, STRIP_Y0, STRIP_X0 + EXL1_W, STRIP_Y0 + EXL1_L, z0, z0 + EXL1_BASE)
    pitch = (EXL1_W - EXL1_FT) / (EXL1_N - 1)
    for i in range(EXL1_N):
        x = STRIP_X0 + i * pitch
        st = st.union(box(x, STRIP_Y0, x + EXL1_FT, STRIP_Y0 + EXL1_L, z0 + EXL1_BASE, z0 + EXL1_H))
    for (cx, cy, w, h, zt) in REAR_PORTS.values():       # notch around the J10/J11 tunnels and plugs
        st = st.cut(box(cx - w / 2 - TUN_WALL - 1.0, cy - h / 2 - TUN_WALL - 1.0, cx + w / 2 + TUN_WALL + 1.0, cy + h / 2 + TUN_WALL + 1.0, 0, 200))
    st = st.cut(box(*PORT_CLEAR, 0, 200))
    for (x, y) in STRIP_SCREWS: st = st.cut(cyl(x, y, 6.0, z0 + EXL1_BASE, 200)).cut(cyl(x, y, 3.4, 0, 200))   # fins milled away at the 4 screws
    return st
def strip_pad():
    z0 = SHELL_DEPTH + FP_T
    p = box(STRIP_X0 + 2, STRIP_Y0 + 2, STRIP_X0 + EXL1_W - 2, STRIP_Y0 + 40, z0, z0 + STRIP_PAD)   # pad over the pillar zone
    for (cx, cy, w, h, zt) in REAR_PORTS.values():
        p = p.cut(box(cx - w / 2 - TUN_WALL - 1.0, cy - h / 2 - TUN_WALL - 1.0, cx + w / 2 + TUN_WALL + 1.0, cy + h / 2 + TUN_WALL + 1.0, 0, 200))
    return p.cut(box(*PORT_CLEAR, 0, 200))
def fans():
    """two 40 x 40 x 10.5 fans on gaskets on the plate outer face, PA12 filter covers (washable foam) over each."""
    z0 = SHELL_DEPTH + FP_T
    fl, gk, cv, sc = [], [], [], []
    for (x, y) in FANS.values():
        h = FAN_S / 2
        gk.append(box(x - h, y - h, x + h, y + h, z0, z0 + FAN_GASKET).cut(cyl(x, y, FAN_HOLE, 0, 200)))
        fr = box(x - h, y - h, x + h, y + h, z0 + FAN_GASKET, z0 + FAN_GASKET + FAN_T).cut(cyl(x, y, 38.5, 0, 200)).union(cyl(x, y, 18, z0 + FAN_GASKET + 1, z0 + FAN_GASKET + FAN_T - 1))
        zc = z0 + FAN_GASKET + FAN_T
        c = box(x - h - 2, y - h - 2, x + h + 2, y + h + 2, zc, zc + FILTER_T).cut(box(x - h + 1, y - h + 1, x + h - 1, y + h - 1, zc - 1, zc + FILTER_T - 1.2))
        for i in range(-3, 4): c = c.cut(box(x - 17, y + i * 5 - 1.5, x + 17, y + i * 5 + 1.5, zc + FILTER_T - 1.5, zc + FILTER_T + 1))   # grille slots
        for dx in (-1, 1):
            for dy in (-1, 1):
                pc = cyl(x + dx * FAN_PITCH / 2, y + dy * FAN_PITCH / 2, 3.0, z0 - 3, zc + FILTER_T - 1.2)
                fr = fr.cut(pc); c = c.cut(pc); gk[-1] = gk[-1].cut(pc); sc.append(pc)
        fl.append(fr); cv.append(c)
    return U(fl), U(gk), U(cv), U(sc)
def heat_pillar():
    return box(*PILLAR, Z_HB1, SHELL_DEPTH)
HV_RIM_Z = 7.0                                     # phase 9: rim trimmed to Z 7.0 in the HV zone
# phase 11: PP film dropped (Compliance phase 9 ruling: not required; leads clipped to <= 1.0 mm instead)
PE_BOSS_D, PE_BOSS_Z = 8.0, ZR + 1.0            # bezel PE boss (existing) end face at Z 18.6, at H4
PE_MASK_D = 12.0                                  # anodise mask-off: boss end face spot face (whole 8 mm face) + thread
def pe_bond():
    """phase 14: PE bond at the NEW bezel boss PE_NEW = M4 A2 screw + flat washer + M4 ring terminal + internal-tooth star washer on the BARE boss face."""
    z = PE_BOSS_Z; P = PE_NEW
    sw = cyl(*P, 8.0, z, z + 0.6).cut(cyl(*P, 4.3, z - 1, z + 2))             # star washer DIN 6797 J M4 (OD 8, t 0.6)
    lug = cyl(*P, 8.0, z + 0.6, z + 1.4).cut(cyl(*P, 4.3, z, z + 2)).union(box(P[0] - 2.5, P[1] - 9.5, P[0] + 2.5, P[1] - 3.5, z + 0.6, z + 1.4))   # ring lug, tongue -y over the board top edge
    fw = cyl(*P, 9.0, z + 1.4, z + 2.2).cut(cyl(*P, 4.3, z, z + 3))           # flat washer
    sc = cyl(*P, 7.0, z + 2.2, z + 5.0).union(cyl(*P, 4.0, z - 8.0, z + 2.2))   # M4x10 head + shank into the 3.3 tap
    return U([sw, lug, fw, sc])
def hv_leads(lead=2.0):
    """J28/J29/J30 THT lead tips protruding from PCB F face (INFERRED 2.0 mm untrimmed, 1.0 trimmed)."""
    import json as _j
    P = _j.load(open(os.path.join(HERE, "hv_pads.json")))
    return U([cyl(x, y, 1.0, Z_PCB - lead, Z_PCB) for r in ("J28", "J29") for (num, x, y, d, net) in P[r]["pads"] if num])
def light_pipe():
    return cyl(*ALS, ALS_D, -RING_GAP - RING_T, ALS_Z_TOP)

def plug_envelopes():
    """Mated plug envelopes for checking only (not parts): RJ45 body 11.68 x 8.0 (Wikipedia 8P8C typ. / Canford 11.68 x 7.24 face),
    USB-C overmold 13.0 x 7.4 (largest measured, EE.SE 475901; spec max 12.85 x 7.0 per USB Type-C R2.2 ECN)."""
    cx, cy, _, _, zt = REAR_PORTS["J10"]; a = box(cx - 5.84, cy - 4.0, cx + 5.84, cy + 4.0, zt - 6.0, SHELL_DEPTH + 15)
    cx, cy, _, _, zt = REAR_PORTS["J11"]; b = box(cx - 6.5, cy - 3.7, cx + 6.5, cy + 3.7, zt + 0.3, SHELL_DEPTH + 15)
    return a.union(b)

# ---- phase 15: rear window covers (PA12 SLS) + 1.5 mm closed-cell EPDM gasket + grommets ----------------------------------
COV_T, COV_GSK = 3.0, 1.5                       # cover plate / gasket (ESTIMATED design values)
# name: (window x0, y0, x1, y1), cover (x0, y0, x1, y1), grommet: ("slot", x0, y0, x1, y1) or ("hole", x, y, D)
COVERS = {
    "PE":     ((3.0, -21.0, 20.0, -1.0),            (1.5, -22.5, 21.5, 0.5),   ("hole", 11.5, -15.0, 10.0)),
    "LEFT_HV":((BX0 - 1, 9, BX0 + 17, 164),          (-8.0, 6.0, 15.5, 167.0),  ("slot", 1.0, 14.0, 8.0, 159.0)),
    "TOP":    ((28, BY0 - 1, 248, BY0 + 13),          (25.0, BY0 - 4, 251.0, -0.27), ("slot", 33.0, BY0 + 2.0, 243.0, BY0 + 10.0)),
    "BOTTOM": ((28, BY1 - 13, 248, BY1 + 1),          (25.0, 178.5, 251.0, BY1 + 4), ("slot", 33.0, BY1 - 10.0, 243.0, BY1 - 2.0)),
    "RIGHT":  ((BX1 - 18, 34, BX1 + 1, 182),          (259.0, 31.0, 284.5, 185.0), ("slot", BX1 - 12.5, 39.0, BX1 - 4.5, 177.0)),
}
def _grom_cut(g, z0, z1):
    return cyl(g[1], g[2], g[3], z0, z1) if g[0] == "hole" else box(g[1], g[2], g[3], g[4], z0, z1)
COVER_HOOK_EDGES = {}
def covers():
    """PA12 cover plates (Z 49.5-52.5) on a 1.5 mm EPDM closed-cell gasket ring (Z 48-49.5), 2 snap tabs per long edge
    hooking under the 3 mm rear wall (tool release through the grommet slot). Grommet: split EPDM membrane strip in the slot
    (or split rubber grommet in the PE hole). Membrane modelled 1.0 mm thick with a 0.6 mm slit (non-rigid: ignored by finger_check)."""
    z = SHELL_DEPTH; cv, gk, mb = [], [], []
    for n, (w, c, g) in COVERS.items():
        plate = box(*c[:2], *c[2:], z + COV_GSK, z + COV_GSK + COV_T).cut(_grom_cut(g, 0, 200))
        x0, y0, x1, y1 = w; long_x = (x1 - x0) >= (y1 - y0)
        tabs = []
        iw = (SX0 + WALL, SY0 + WALL, SX1 - WALL, SY1 - WALL)       # inner wall faces: an edge < 2.5 mm from one gets no hook
        free = {"x0": x0 - iw[0] >= 2.5, "y0": y0 - iw[1] >= 2.5, "x1": iw[2] - x1 >= 2.5, "y1": iw[3] - y1 >= 2.5}
        fr = (0.2, 0.5, 0.8) if sum(free.values()) < 4 else (0.25, 0.75)
        COVER_HOOK_EDGES[n] = [k for k, v in free.items() if v]
        for f in fr:
            if long_x:
                xm = x0 + f * (x1 - x0)
                if free["y0"]: tabs += [box(xm - 4, y0 + 0.2, xm + 4, y0 + 1.7, z - WALL - 1.0, z + COV_GSK), box(xm - 4, y0 - 1.0, xm + 4, y0 + 1.7, z - WALL - 1.0, z - WALL)]
                if free["y1"]: tabs += [box(xm - 4, y1 - 1.7, xm + 4, y1 - 0.2, z - WALL - 1.0, z + COV_GSK), box(xm - 4, y1 - 1.7, xm + 4, y1 + 1.0, z - WALL - 1.0, z - WALL)]
            else:
                ym = y0 + f * (y1 - y0)
                if free["x0"]: tabs += [box(x0 + 0.2, ym - 4, x0 + 1.7, ym + 4, z - WALL - 1.0, z + COV_GSK), box(x0 - 1.0, ym - 4, x0 + 1.7, ym + 4, z - WALL - 1.0, z - WALL)]
                if free["x1"]: tabs += [box(x1 - 1.7, ym - 4, x1 - 0.2, ym + 4, z - WALL - 1.0, z + COV_GSK), box(x1 - 1.7, ym - 4, x1 + 1.0, ym + 4, z - WALL - 1.0, z - WALL)]
        cv.append(U([plate] + tabs))
        gk.append(box(*c[:2], *c[2:], z, z + COV_GSK).cut(box(x0 - 0.0, y0 - 0.0, x1, y1, 0, 200)))
        if g[0] == "hole":
            mb.append(cyl(g[1], g[2], g[3] + 4, z + COV_GSK + COV_T, z + COV_GSK + COV_T + 1.0).cut(cyl(g[1], g[2], 2.0, 0, 200)))
        else:
            gx0, gy0, gx1, gy1 = g[1:]; m = box(gx0 - 2, gy0 - 2, gx1 + 2, gy1 + 2, z + COV_GSK + COV_T, z + COV_GSK + COV_T + 1.0)
            if (gx1 - gx0) >= (gy1 - gy0): m = m.cut(box(gx0, (gy0 + gy1) / 2 - 0.3, gx1, (gy0 + gy1) / 2 + 0.3, 0, 200))
            else: m = m.cut(box((gx0 + gx1) / 2 - 0.3, gy0, (gx0 + gx1) / 2 + 0.3, gy1, 0, 200))
            mb.append(m)
    return U(cv), U(gk), U(mb)
def tunnel_seals():
    """phase 15: closed-cell foam ring closing the 0.5 mm TUN_GAP between each J10/J11 tunnel foot and the jack shell."""
    out = []
    for (cx, cy, w, h, zt) in REAR_PORTS.values():
        out.append(box(cx - w / 2 - TUN_WALL, cy - h / 2 - TUN_WALL, cx + w / 2 + TUN_WALL, cy + h / 2 + TUN_WALL, zt, zt + TUN_GAP)
                   .cut(box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 0, 200)))
    return U(out)

def build():
    caps, memb, nibs = keys(); cb, cs = clamps(); fn, fg, fc, fs = fans(); wc, wg, wm = covers()
    return {"bezel": (bezel(), (0.15, 0.15, 0.17)), "display": (display(), (0.05, 0.1, 0.3)),
            "key_caps": (caps, (0.6, 0.85, 1.0)), "key_membrane": (memb, (0.9, 0.9, 0.85)), "key_nibs": (nibs, (1, 1, 0.7)),
            "switches": (switches(), (0.3, 0.3, 0.3)), "pcb": (pcb(), (0.1, 0.5, 0.15)), "rear_parts": (rear_parts(), (0.2, 0.3, 0.6)),
            "heat_bar": (heat_bar(), (0.8, 0.5, 0.2)), "thermal_pads": (thermal_pads(), (0.9, 0.2, 0.6)),
            "gasket": (gasket(), (0.9, 0.3, 0.1)), "customer_panel": (customer_panel(), (0.7, 0.7, 0.7)),
            "rear_shell": (rear_shell(), (0.45, 0.45, 0.42)), "clamps": (cb, (0.75, 0.6, 0.2)), "clamp_screws": (cs, (0.85, 0.85, 0.9)),
            "front_ring": (front_ring(), (0.55, 0.55, 0.52)), "fin_plate": (fin_plate(), (0.75, 0.75, 0.78)),
            "heat_pillar": (heat_pillar(), (0.8, 0.55, 0.25)), "light_pipe": (light_pipe(), (0.9, 0.95, 1.0)),
            "exl1_strip": (exl1_strip(), (0.8, 0.8, 0.85)), "strip_pad": (strip_pad(), (0.9, 0.3, 0.6)),
            "fans": (fn, (0.1, 0.1, 0.1)), "fan_gaskets": (fg, (0.3, 0.3, 0.3)), "filter_covers": (fc, (0.4, 0.45, 0.42)), "fan_screws": (fs, (0.85, 0.85, 0.9)),
            "pe_bond": (pe_bond(), (0.85, 0.7, 0.2)),
            "window_covers": (wc, (0.35, 0.4, 0.5)), "cover_gaskets": (wg, (0.1, 0.1, 0.1)), "grommets": (wm, (0.2, 0.2, 0.2)),
            "tunnel_seals": (tunnel_seals(), (0.1, 0.1, 0.1))}

def vol(a, b):
    try: return a.intersect(b).val().Volume()
    except Exception: return 0.0

def dist(a, b):
    return round(a.val().distance(b.val()), 2) if hasattr(a.val(), "distance") else None
def hv_checks(parts):
    """phase 9 compliance: 3D clearances from J28/J29 hot metal to display, bezel (earthed), clamp metal, joint screws."""
    out = {}
    for lead in (2.0, 1.0):
        L = hv_leads(lead)
        out[f"lead_tips_{lead}mm_to_display_rear"] = dist(L, parts["display"][0])
        out[f"lead_tips_{lead}mm_to_bezel_metal (earthed, basic 5.5)"] = dist(L, parts["bezel"][0])
        out[f"lead_tips_{lead}mm_to_heat_pillar/plate"] = dist(L, parts["fin_plate"][0])
    # plug envelopes J28/J29 (conservative: whole plug body treated as hot)
    pl = U([box(max(FP[r]["bbox"][0], BX0), FP[r]["bbox"][1], FP[r]["bbox"][2], FP[r]["bbox"][3], ZR, ZR + 18.0) for r in ("J28", "J29")])
    pl30 = box(max(FP["J30"]["bbox"][0], BX0), FP["J30"]["bbox"][1], FP["J30"]["bbox"][2], FP["J30"]["bbox"][3], ZR, ZR + 16.0)
    ins = U([cyl(SX0 - 8, p, 5.6, CL_Z0, CL_Z1) for (p, sd) in CLAMPS if sd == "L"])   # M4 heat-set insert OD ~5.6 ESTIMATED
    out["J28J29_plug_envelope_to_left_clamp_screw (reinforced 8.0)"] = dist(pl, U([cyl(SX0 - 8, p, 4.0, Z_PANEL, CL_Z1 + 3) for (p, sd) in CLAMPS if sd == "L"]))
    out["J28J29_plug_envelope_to_left_clamp_insert (reinforced 8.0)"] = dist(pl, ins)
    out["J28J29_pads_to_left_clamp_insert"] = dist(hv_leads(0.01).translate((0, 0, PCB_T + 0.01)), ins)
    out["J30_plug_envelope_to_left_clamp_insert"] = dist(pl30, ins)
    out["pe_bond_hardware_to_nearest_HV_plug (earthed, basic 5.5)"] = dist(parts["pe_bond"][0], pl)
    out["pe_boss_to_J28J29_plug_envelope (earthed, basic 5.5)"] = dist(cyl(*PE_NEW, 8.0, 0.5, ZR + 1.0), pl)
    out["pe_bond_hardware_to_J30_plug_envelope"] = dist(parts["pe_bond"][0], pl30)
    out["pe_boss_to_display"] = dist(cyl(*PE_NEW, 8.0, 0.5, ZR + 1.0), parts["display"][0])
    out["pe_boss_to_switches"] = dist(cyl(*PE_NEW, 8.0, 0.5, ZR + 1.0), parts["switches"][0])
    out["pe_boss_to_key_caps"] = dist(cyl(*PE_NEW, 8.0, 0.5, ZR + 1.0), parts["key_caps"][0])
    out["pe_boss_to_light_pipe"] = dist(cyl(*PE_NEW, 8.0, 0.5, ZR + 1.0), parts["light_pipe"][0])
    out["pe_boss_to_front_ring_sleeve"] = dist(cyl(*PE_NEW, 8.0, 0.5, ZR + 1.0), parts["front_ring"][0])
    out["pe_boss_to_clamps"] = dist(cyl(*PE_NEW, 8.0, 0.5, ZR + 1.0), parts["clamps"][0])
    # J30 creepage, phase 14: surface path (MODELLED, hand-route over CAD surfaces; see CLAMP_RETENTION.md / README phase 14)
    ins118 = [p for (p, sd) in CLAMPS if sd == "L" and FP["J30"]["bbox"][1] - 15 < p < FP["J30"]["bbox"][3] + 15]
    leg1 = ((max(FP["J30"]["bbox"][0], BX0) - (BX0 - 1)) ** 2 + ((SHELL_DEPTH - WALL) - (ZR + 16.0)) ** 2) ** 0.5   # plug top-left edge -> rear-window rim (along field-wire insulation)
    path = leg1 + WALL + ((BX0 - 1) - SX0) + (SHELL_DEPTH - CL_Z1) + ((SX0 - (SX0 - 8 + 2.8)))                    # rim depth + rear face to corner + down outer wall + clamp top to insert edge
    out["J30_surface_path_to_left_clamp_insert_MODELLED (reinforced 12.6)"] = round(path, 2)
    out["J30_surface_path_legs [wire-insulation leg, rim, rear face, outer wall, clamp top]"] = [round(leg1, 2), WALL, round((BX0 - 1) - SX0, 2), round(SHELL_DEPTH - CL_Z1, 2), 5.2]
    out["J30_adjacent_left_clamps_y"] = ins118
    js = U([cyl(x, y, 4.0, FIELD_T - 6, FIELD_T + FL_T) for (x, y) in JOINT_SCREWS])
    out["J28J29_plug_envelope_to_joint_screws (earthed, basic 5.5)"] = dist(pl, js)
    # left shell wall solid y 15..105 (phase 9 condition (c)/(d))
    sh = parts["rear_shell"][0]
    zone = box(SX0, 15.0, SX0 + WALL, 105.0, Z_PANEL, SHELL_DEPTH)
    v_full = (WALL * 90.0 * (SHELL_DEPTH - Z_PANEL))
    out["left_wall_y15_105_solid_fraction (1.0 = no openings)"] = round(vol(sh, zone) / v_full, 4)
    out["left_wall_thickness_mm"] = WALL
    out["left_wall_inner_face_to_J28J29_pad_column_x4.215"] = round(4.215 - (SX0 + WALL), 2)
    out["left_wall_inner_face_to_J28J29_plug_body"] = round(max(FP["J28"]["bbox"][0], BX0) - (SX0 + WALL), 2)
    return out
def checks(parts):
    res = {}
    names = list(parts)
    allowed = {("pcb", "rear_parts"), ("pcb", "switches"), ("heat_bar", "thermal_pads"), ("bezel", "thermal_pads"),
               ("clamps", "rear_shell"), ("clamp_screws", "customer_panel"), ("heat_bar", "heat_pillar"),
               ("fan_screws", "fin_plate"), ("fan_screws", "fans"), ("fan_screws", "fan_gaskets"), ("fan_screws", "filter_covers"), ("pe_bond", "bezel")}
    for a, b in itertools.combinations(names, 2):
        if (a, b) in allowed or (b, a) in allowed: continue
        if "customer_panel" in (a, b) and "gasket" in (a, b): continue
        v = vol(parts[a][0], parts[b][0])
        if v > 1e-3: res[f"{a}&{b}"] = round(v, 3)
    pe = plug_envelopes()
    res["plug_envelopes&rear_shell"] = round(vol(pe, parts["rear_shell"][0]), 3)
    # clearances (positive = gap), computed from parameters
    clr = {
           "nib_to_plunger_free_gap": 0.1,
           "glass_front_vs_ring_face (neg = behind)": -0.05, "glass_edge_to_ring_sleeve (silicone bead)": WIN_GAP, "sleeve_to_metal_window_gap": 0.2,
           "CM5_top_to_heatbar (pad)": PAD_T,
           "rear_parts_tallest_to_shell_inner_rear": round(SHELL_DEPTH - WALL - (ZR + 18.0), 2),
           "J10_mouth_depth_below_rear_face (tunnel)": round(SHELL_DEPTH - (ZR + H['J10']), 2),
           "J11_mouth_depth_below_rear_face (tunnel)": round(SHELL_DEPTH - (ZR + H['J11']), 2),
           "J10_tunnel_clearance_per_side_to_RJ45_body_x_y": [round((20.0 - 11.68) / 2, 2), round((24.0 - 8.0) / 2, 2)],
           "J11_tunnel_clearance_per_side_to_USBC_overmold_x_y (13.0x7.4)": [round((16.0 - 13.0) / 2, 2), round((10.0 - 7.4) / 2, 2)],
           "clamp_screw_reach_panel_range_mm": [PANEL_MIN, PANEL_MAX],
           "shell_to_cutout_per_side": CUT_GAP,
           "ALS_pipe_to_nearest_cap_edge": round(min(abs(ALS[0] - x) for _, x, _ in KEYS) - CAP_W / 2 - ALS_D / 2, 2),
           "ALS_centre_to_glass_top_edge": round(-ALS[1], 2),
           "ALS_centre_to_active_area_top_left_corner (7.32, 8.03)": round(((ALS[0] - 7.32) ** 2 + (ALS[1] - 8.03) ** 2) ** 0.5, 2),
           "ALS_pipe_rear_face_to_PCB_F": round(Z_PCB - ALS_Z_TOP, 2),
           "V6_strip_rear_face_Z": SHELL_DEPTH + FP_T + STRIP_PAD + EXL1_H,
           "fan_filter_cover_rear_face_Z (total depth behind ring face = this + 4.0)": SHELL_DEPTH + FP_T + FAN_GASKET + FAN_T + FILTER_T,
           "display_rear_to_PCB_front_airgap_TFT_area (x<75 HV zone)": round(Z_PCB - (0.05 + DZ + CTP_TFT), 2),
           "display_rear_to_PCB_front_airgap_source_band (min)": round(Z_PCB - 0.05 - DZ - MOD_D, 2)}
    clr["HV"] = hv_checks(parts)
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
