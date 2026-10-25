"""Blackstart (genctl) low-part-count enclosure concept, CadQuery. Parametric.
Run: /workspace/cqenv/bin/python enclosure.py   -> step/*.step, enclosure_assembly.step, PNG renders.
Coords: front-view geometry.py coords (x right, y DOWN, mm, origin = glass top-left)
mapped to CadQuery X = x, Y = -y, Z = -depth behind the panel face (front face at Z=0)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cadquery as cq
import geometry as G

# ---------------- parameters (change freely) ----------------
BOARD_W, BOARD_H = G.BOARD_W, G.BOARD_H          # PCB outline; may change
BOARD_X0, BOARD_Y0 = G.BOARD[0], G.BOARD[1]
PCB_T = 1.6
Z_PCB = G.Z_BOARD_FRONT                          # 16.0 behind face
BEZEL_T = 4.0                                    # flange/field thickness
# --- MOUNTING (Ethan 2026-10-24 rev B): self-contained unit; rear body slides in from the FRONT through the
# customer cutout; customer panel sits BEHIND the bezel rim + gasket, clamped from the back by hook clamps.
SHELL_CLR, SHELL_WALL = 2.0, 3.0                 # PCB -> shell inner wall; rev C: SLS PA12 shell, 3 mm walls
SHELL_W, SHELL_H = BOARD_W + 2 * (SHELL_CLR + SHELL_WALL), BOARD_H + 2 * (SHELL_CLR + SHELL_WALL)  # 294 x 220 outer
CUT_GAP = 0.5                                    # shell -> cutout per side (nominal)
CUT_W, CUT_H = SHELL_W + 2 * CUT_GAP, SHELL_H + 2 * CUT_GAP   # customer cutout 295 x 221 (+1.0/-0)
SH_FLANGE_W, SH_FLANGE_T = 8.0, 2.5              # shell front flange (outward), sits on the bezel field rear
RIM_W, RIM_Z = 9.0, 9.5                          # bezel outer rim: 9 wide, rear face at Z 8 (gasket land)
BEZEL_W = SHELL_W + 2 * (SH_FLANGE_W + 0.5 + RIM_W)   # 322
BEZEL_H = SHELL_H + 2 * (SH_FLANGE_W + 0.5 + RIM_W)   # 248
GASKET_T, GASKET_W = 2.0, 8.0                    # closed-cell silicone sponge, 30 % compression -> 1.4
PANEL_T = 2.0                                    # customer panel shown; clamp range 1.0 ... 5.0
SHELL_DEPTH = 62.0                               # rear face Z
SCREW_D, SCREW_HEAD_D = 4.0, 7.6                 # all M4 (ISO 7380 button head, head 2.2)
N_CLAMPS = 6
PE_BOSS = (G.MOUNT_HOLES[3][1], G.MOUNT_HOLES[3][2])  # H4 becomes the dedicated PE boss (bezel boss through PCB hole D9.5)
SHELL_POSTS = [(100, 60), (100, 140), (240, 60), (240, 140)]   # shell-integral posts, 0.3 mm off PCB rear (anti-flex)
PE_BOSS_Z = Z_PCB + PCB_T + 1.0                  # boss top 1 mm proud of PCB rear; ring lug + M4x10 + serrated washer
BARRIER_X = BOARD_X0 + 16.0                      # shell-integral 600 V barrier rib (rear of metering strip)
POCKET_PAD = 2.5                                 # clamp pads on the shell outside; hook pockets are BLIND (nothing pokes inside)
# KEYS (single switch per key, Ethan 2026-10-24): rigid cap guided in its OWN machined pocket.
# Anti-jam ("drawer") rule: off-centre press at e stays straight if e < L/(2*mu). L=8, mu<=0.3 -> e<13.3 -> cap <= 26.
CAP_W = 24.0                                     # chosen cap width (pitch stays 43.52 -> 19.52 aluminium between caps)
CAP_H = 12.0
GUIDE_L = 8.0                                    # pocket depth = key band thickness (bezel locally 8 mm)
GUIDE_CLR = 0.10                                 # cap -> pocket per side (SLA caps, fit/sand at assembly)
HEAD_OVER = 1.0                                  # head flange overhang per side (also the hard stop on the face)
HEAD_T, HEAD_GAP = 1.0, 1.3                      # head thickness; head-to-face gap = hard-stop travel
WEB_T = 1.0                                      # cast silicone keypad web bonded to cap rear and band rear
def key_rects():
    return [(r, x, y) for r, x, y in G.buttons()]

cx = BOARD_X0 + BOARD_W / 2; cy = BOARD_Y0 + BOARD_H / 2   # board centre (front coords)

def box(x0, y0, x1, y1, z0, z1):
    """front coords x0..x1, y0..y1 (y down), depth z0..z1 behind face (positive numbers)."""
    return (cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0)
            .translate(((x0 + x1) / 2, -(y0 + y1) / 2, -(z0 + z1) / 2)))

def cyl(x, y, d, z0, z1):
    return cq.Workplane("XY").circle(d / 2).extrude(z1 - z0).translate((x, -y, -z1))

bx0, by0 = cx - BEZEL_W / 2, cy - BEZEL_H / 2
sx0, sy0 = cx - SHELL_W / 2, cy - SHELL_H / 2
fo = 4.5                              # flange centre-line offset from the shell wall
SCREWS = [(x, y) for x in (sx0 + 30, cx, sx0 + SHELL_W - 30) for y in (sy0 - fo, sy0 + SHELL_H + fo)]
SCREWS += [(sx0 - fo, cy), (sx0 + SHELL_W + fo, cy)]       # 8 x M4x8 joint screws, from the REAR into blind taps
Z_PANEL = RIM_Z + GASKET_T * 0.7                 # customer panel front face
CLAMPS = [(G.BTN_X[1], "T"), (G.BTN_X[4], "T"), (G.BTN_X[1], "B"), (G.BTN_X[4], "B"), (cy, "L"), (cy, "R")]
PCB_HOLES = [(h[1], h[2]) for h in G.MOUNT_HOLES[:3]]   # H1-H3 screwed; mid holes dropped (behind the display there is no bezel to screw into)

def bezel():
    w0, w1 = G.WINDOW[0], G.WINDOW[2]; h0, h1 = G.WINDOW[1], G.WINDOW[3]
    b = box(bx0, by0, bx0 + BEZEL_W, by0 + BEZEL_H, 0, BEZEL_T)
    b = b.union(box(w0 - G.WEB, h0 - G.WEB, w1 + G.WEB, h1 + G.WEB, 0, G.RIM_DEPTH))  # rim
    for (x, y) in PCB_HOLES:                                  # integral PCB bosses to Z_PCB
        b = b.union(cyl(x, y, 7.0, 0.5, Z_PCB))
    b = b.cut(box(w0, h0, w1, h1, -1, G.LEDGE_Z))             # window (glass seat)
    lw = G.LEDGE_W
    b = b.cut(box(w0 + lw, h0 + lw, w1 - lw, h1 - lw, -1, 30))  # ledge opening
    b = b.cut(box(20.0, h1 - 30, 256.0, h1 + 0.01, G.LEDGE_Z - 0.01, 30))  # bottom ledge only at corners
    for yc in (G.BTN_Y_TOP, G.BTN_Y_BOT):             # 8 mm key band behind the field
        b = b.union(box(G.AA_LEFT - 2, yc - CAP_H / 2 - 1.5, G.AA_LEFT + G.AA_W + 2, yc + CAP_H / 2 + 1.5, 0, GUIDE_L))
    for r, x, y in key_rects():                       # one guide pocket per key
        b = b.cut(box(x - CAP_W / 2 - GUIDE_CLR, y - CAP_H / 2 - GUIDE_CLR, x + CAP_W / 2 + GUIDE_CLR, y + CAP_H / 2 + GUIDE_CLR, -1, 30))
    rim = box(bx0, by0, bx0 + BEZEL_W, by0 + BEZEL_H, BEZEL_T - 0.01, RIM_Z)
    rim = rim.cut(box(bx0 + RIM_W, by0 + RIM_W, bx0 + BEZEL_W - RIM_W, by0 + BEZEL_H - RIM_W, 0, 20))
    b = b.union(rim)
    for (x, y) in SCREWS:                             # blind M4 taps, face stays intact
        b = b.cut(cyl(x, y, 3.3, 0.8, BEZEL_T + 0.1))
    for (x, y) in PCB_HOLES:
        b = b.cut(cyl(x, y, 3.3, 3.0, Z_PCB + 1))             # M4 tap drill, blind (face intact)
    b = b.union(cyl(*PE_BOSS, 8.0, 0.5, PE_BOSS_Z)).cut(cyl(*PE_BOSS, 3.3, 3.0, PE_BOSS_Z + 1))  # PE boss
    return b

def display():
    d = box(0, 0, G.GLASS_W, G.GLASS_H, 0.05, 0.05 + 8.51)
    x0, y0, x1, y1 = G.SRC_PCB_BAND
    return d.union(box(x0, y0, x1, y1, 8.56, 0.05 + G.MODULE_DEPTH_MAX))

def keypad():
    """Rev C keypad, no mould: 12 SLA clear caps + 2 laser-cut 1.0 mm translucent silicone strips (seal + return)
    + 12 laser-cut silicone nib discs (D4, 1.5 mm), all bonded with the display RTV. Returns (silicone, caps)."""
    z0, z1 = GUIDE_L, GUIDE_L + WEB_T
    sil = None
    for yc in (G.BTN_Y_TOP, G.BTN_Y_BOT):
        r = box(G.AA_LEFT - 2, yc - CAP_H / 2 - 1.5, G.AA_LEFT + G.AA_W + 2, yc + CAP_H / 2 + 1.5, z0, z1)
        sil = r if sil is None else sil.union(r)
    caps = None
    for r, x, y in key_rects():
        sil = sil.union(cyl(x, y, 4.0, z1, Z_PCB - 5.5 - 0.1))     # silicone nib disc (0.1 free gap)
        c = box(x - CAP_W / 2, y - CAP_H / 2, x + CAP_W / 2, y + CAP_H / 2, -HEAD_GAP, GUIDE_L)
        c = c.union(box(x - CAP_W / 2 - HEAD_OVER, y - CAP_H / 2 - HEAD_OVER, x + CAP_W / 2 + HEAD_OVER,
                        y + CAP_H / 2 + HEAD_OVER, -HEAD_GAP - HEAD_T, -HEAD_GAP))
        caps = c if caps is None else caps.union(c)
    return sil, caps

def switches():
    s = None
    for ref, x, y in G.buttons():
        b = box(x - 3.4, y - 3.6, x + 3.4, y + 3.6, Z_PCB - 5.5 + 0.8, Z_PCB)
        b = b.union(cyl(x, y, 3.8, Z_PCB - 5.5, Z_PCB - 4.7))
        s = b if s is None else s.union(b)
    return s

def pcb():
    p = box(BOARD_X0, BOARD_Y0, BOARD_X0 + BOARD_W, BOARD_Y0 + BOARD_H, Z_PCB, Z_PCB + PCB_T)
    for (x, y) in PCB_HOLES:
        p = p.cut(cyl(x, y, 4.3, Z_PCB - 1, Z_PCB + 3))
    p = p.cut(cyl(*PE_BOSS, 9.5, Z_PCB - 1, Z_PCB + 3))          # PE boss clearance
    zb = Z_PCB + PCB_T
    p = p.union(box(150, 75, 205, 115, zb, zb + 6))           # CM5 (simplified)
    p = p.union(box(158, 80, 197, 110, zb + 6, zb + 6 + 10))  # off-the-shelf CM5 passive heatsink (simplified)
    for xs in (40, 85, 128, 172, 215):                         # pluggable terminals, edges
        p = p.union(box(xs, BOARD_Y0 + 1, xs + 26, BOARD_Y0 + 11, zb, zb + 16))
        p = p.union(box(xs, BOARD_Y0 + BOARD_H - 11, xs + 26, BOARD_Y0 + BOARD_H - 1, zb, zb + 16))
    p = p.union(box(BOARD_X0 + BOARD_W - 18, 20, BOARD_X0 + BOARD_W - 1, 175, zb, zb + 16))  # right edge I/O
    p = p.union(box(BOARD_X0 + 1, 10, BOARD_X0 + 14, 120, zb, zb + 18))   # 600 V metering terminals
    return p

def gasket():
    g = box(bx0 + 0.5, by0 + 0.5, bx0 + BEZEL_W - 0.5, by0 + BEZEL_H - 0.5, RIM_Z, RIM_Z + GASKET_T * 0.7)
    return g.cut(box(bx0 + 0.5 + GASKET_W, by0 + 0.5 + GASKET_W, bx0 + BEZEL_W - 0.5 - GASKET_W, by0 + BEZEL_H - 0.5 - GASKET_W, 0, 30))

def customer_panel():
    p = box(bx0 - 25, by0 - 25, bx0 + BEZEL_W + 25, by0 + BEZEL_H + 25, Z_PANEL, Z_PANEL + PANEL_T)
    return p.cut(box(cx - CUT_W / 2, cy - CUT_H / 2, cx + CUT_W / 2, cy + CUT_H / 2, 0, 30))

def rear_shell():
    z0 = BEZEL_T
    s = box(sx0 - SH_FLANGE_W, sy0 - SH_FLANGE_W, sx0 + SHELL_W + SH_FLANGE_W, sy0 + SHELL_H + SH_FLANGE_W, z0, z0 + SH_FLANGE_T)
    s = s.cut(box(sx0, sy0, sx0 + SHELL_W, sy0 + SHELL_H, 0, 30))
    t = box(sx0, sy0, sx0 + SHELL_W, sy0 + SHELL_H, z0, SHELL_DEPTH)
    t = t.cut(box(sx0 + SHELL_WALL, sy0 + SHELL_WALL, sx0 + SHELL_W - SHELL_WALL, sy0 + SHELL_H - SHELL_WALL, z0 - 1, SHELL_DEPTH - SHELL_WALL))
    s = s.union(t)
    for (x, y) in SCREWS:
        s = s.cut(cyl(x, y, 4.5, z0 - 1, z0 + 3))
    zr0 = SHELL_DEPTH - SHELL_WALL - 1               # rear wiring windows + vents
    s = s.cut(box(38, BOARD_Y0 - 1, 243, BOARD_Y0 + 13, zr0, SHELL_DEPTH + 1))
    s = s.cut(box(38, BOARD_Y0 + BOARD_H - 13, 243, BOARD_Y0 + BOARD_H + 1, zr0, SHELL_DEPTH + 1))
    s = s.cut(box(BOARD_X0 + BOARD_W - 20, 20, BOARD_X0 + BOARD_W + 1, 175, zr0, SHELL_DEPTH + 1))
    for i in range(8):
        s = s.cut(box(150 + i * 7, 60, 153 + i * 7, 130, zr0, SHELL_DEPTH + 1))
    for (p, side) in CLAMPS:                          # outside pads + BLIND hook pockets (3.5 deep of 5.5)
        for d in (-7, 7):
            if side in "TB":
                y = sy0 if side == "T" else sy0 + SHELL_H; sg = -1 if side == "T" else 1
                s = s.union(box(p - 12, min(y, y + sg * POCKET_PAD), p + 12, max(y, y + sg * POCKET_PAD), 20, 34)) if d < 0 else s
                yo = y + sg * POCKET_PAD
                s = s.cut(box(p + d - 3, min(yo, yo - sg * 3.5), p + d + 3, max(yo, yo - sg * 3.5), 26, 28.5))
            else:
                x = sx0 if side == "L" else sx0 + SHELL_W; sg = -1 if side == "L" else 1
                s = s.union(box(min(x, x + sg * POCKET_PAD), p - 12, max(x, x + sg * POCKET_PAD), p + 12, 20, 34)) if d < 0 else s
                xo = x + sg * POCKET_PAD
                s = s.cut(box(min(xo, xo - sg * 3.5), p + d - 3, max(xo, xo - sg * 3.5), p + d + 3, 26, 28.5))
    # integral 600 V barrier rib behind the metering strip (stops 1.0 mm off the PCB rear / parts)
    s = s.union(box(BARRIER_X, sy0 + SHELL_WALL, BARRIER_X + 2.0, BOARD_Y0 + 142, Z_PCB + PCB_T + 1.0, SHELL_DEPTH - 1))
    s = s.union(box(sx0 + SHELL_WALL, BOARD_Y0 + 140, BARRIER_X + 2.0, BOARD_Y0 + 142, Z_PCB + PCB_T + 1.0, SHELL_DEPTH - 1))
    for (x, y) in SHELL_POSTS:
        s = s.union(cyl(x, y, 6.0, Z_PCB + PCB_T + 0.3, SHELL_DEPTH - 1)).union(cyl(x, y, 12.0, SHELL_DEPTH - 8, SHELL_DEPTH - 1))
    # chimney vents: bottom face intake + top face exhaust slots, each under a 6 mm drip hood
    for i in range(10):
        xv = 120 + i * 9
        for yy, sg in ((sy0, -1), (sy0 + SHELL_H, 1)):
            s = s.cut(box(xv, yy - 2, xv + 4, yy + 4 if sg < 0 else yy + 2, 44, 56) if sg < 0 else box(xv, yy - 4, xv + 4, yy + 2, 44, 56))
    for yy, sg in ((sy0, -1), (sy0 + SHELL_H, 1)):  # drip hoods (outside, above each slot row)
        s = s.union(box(118, min(yy, yy + sg * 6), 211, max(yy, yy + sg * 6), 40, 42))
    # PE access in the right-side wiring window
    s = s.cut(box(BOARD_X0 + BOARD_W - 22, 170, BOARD_X0 + BOARD_W + 1, 186, SHELL_DEPTH - SHELL_WALL - 1, SHELL_DEPTH + 1))
    return s

def clamps():
    """6 hook clamps: laser-cut + bent 2 mm stainless L bracket, 2 hooks into shell slots, PEM M4 nut,
    M4x16 screw pushing forward onto the panel rear. Returns (brackets, screws)."""
    br = sc = None
    zr = Z_PANEL + PANEL_T
    for (p, side) in CLAMPS:
        sgn = -1 if side in "TL" else 1
        if side in "TB":
            yf = (sy0 if side == "T" else sy0 + SHELL_H) + sgn * POCKET_PAD          # pad outer face
            b = box(p - 10, min(yf, yf + sgn * 12), p + 10, max(yf, yf + sgn * 12), 26.2, 28.4)   # arm (in line with hooks)
            for d in (-7, 7):
                b = b.union(box(p + d - 2.8, min(yf, yf - sgn * 3.4), p + d + 2.8, max(yf, yf - sgn * 3.4), 26.2, 28.4))
            ys = yf + sgn * 8
            c = cyl(p, ys, SCREW_D, zr, 28.4).union(cyl(p, ys, 7.0, 28.4, 32.4))
        else:
            xf = (sx0 if side == "L" else sx0 + SHELL_W) + sgn * POCKET_PAD
            b = box(min(xf, xf + sgn * 12), p - 10, max(xf, xf + sgn * 12), p + 10, 26.2, 28.4)
            for d in (-7, 7):
                b = b.union(box(min(xf, xf - sgn * 3.4), p + d - 2.8, max(xf, xf - sgn * 3.4), p + d + 2.8, 26.2, 28.4))
            xs = xf + sgn * 8
            c = cyl(xs, p, SCREW_D, zr, 28.4).union(cyl(xs, p, 7.0, 28.4, 32.4))
        br = b if br is None else br.union(b); sc = c if sc is None else sc.union(c)
    return br, sc

def screws():
    out = None
    for (x, y) in SCREWS:      # joint screws from the rear: head on the shell flange (inside the rim, under nothing)
        sc = cyl(x, y, SCREW_HEAD_D, BEZEL_T + SH_FLANGE_T, BEZEL_T + SH_FLANGE_T + 2.2).union(cyl(x, y, SCREW_D, 1.0, BEZEL_T + SH_FLANGE_T))
        out = sc if out is None else out.union(sc)
    for (x, y) in PCB_HOLES:   # PCB screws from rear into tapped bezel bosses
        out = out.union(cyl(x, y, SCREW_HEAD_D, Z_PCB + PCB_T, Z_PCB + PCB_T + 2.2).union(cyl(x, y, SCREW_D, Z_PCB - 8, Z_PCB + PCB_T)))
    x, y = PE_BOSS                                    # PE screw M4x10 + serrated washer + customer ring lug
    out = out.union(cyl(x, y, SCREW_HEAD_D, PE_BOSS_Z + 1.5, PE_BOSS_Z + 3.7)).union(cyl(x, y, SCREW_D, PE_BOSS_Z - 6, PE_BOSS_Z + 1.5))
    return out

def build():
    sil, caps = keypad()
    return {"bezel": (bezel(), (0.15, 0.15, 0.17)), "display": (display(), (0.05, 0.1, 0.25)),
            "keypad_silicone": (sil, (0.85, 0.85, 0.8)), "keypad_caps": (caps, (0.6, 0.85, 1.0)),
            "switches": (switches(), (0.3, 0.3, 0.3)), "pcb": (pcb(), (0.1, 0.5, 0.15)),
            "gasket": (gasket(), (0.9, 0.3, 0.1)), "customer_panel": (customer_panel(), (0.7, 0.7, 0.7)),
            "rear_shell": (rear_shell(), (0.55, 0.55, 0.5)), "screws_M4": (screws(), (0.8, 0.8, 0.85)),
            "clamp_brackets": (clamps()[0], (0.75, 0.6, 0.2)), "clamp_screws_M4": (clamps()[1], (0.85, 0.85, 0.9))}

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__)); os.makedirs(os.path.join(here, "step"), exist_ok=True)
    parts = build(); asm = cq.Assembly()
    for n, (wp, col) in parts.items():
        cq.exporters.export(wp, os.path.join(here, "step", n + ".step"))
        cq.exporters.export(wp, os.path.join(here, "step", n + ".stl"), tolerance=0.3)
        asm.add(wp, name=n, color=cq.Color(*col))
    asm.save(os.path.join(here, "enclosure_assembly.step"))
    print("ok", {k: round(v[0].val().Volume() / 1000, 1) for k, v in parts.items()}, "cm3")
