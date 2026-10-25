#!/usr/bin/env python3
"""Critical-net hand router for genctl v4 (pcbnew python + numba grid A*).

Usage: python3 handroute_v4.py in.kicad_pcb out.kicad_pcb [group ...]
Groups: hv xtal ade eth usb lvds dsi  (default: all, in that order)

0.1 mm grid on F.Cu / In2.Cu / B.Cu (planes on In1/In3/In4 untouched).
Clearances follow genctl_v4.kicad_dru (3 mm outer / 1.5 mm inner from HV_LINE,
1.5 mm around HV_LINE_DIV).  Differential pairs: P is routed with a penalty for
cells where the whole pair would not fit, then N follows P at gap+w using a
distance band cost.  All produced tracks/vias are LOCKED so the Specctra export
marks them protected and Freerouting leaves them alone.
"""
import sys, re, math, heapq
import numpy as np, pcbnew
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt as edt
import numba

R = 0.1
LAY = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
OUTER = [True, False, True]
CLS = {"Default": (0.15, 0.15), "DIFF100": (0.11, 0.15), "DIFF90": (0.15, 0.15),
       "HV_LINE": (0.5, 1.5), "HV_LINE_DIV": (0.4, 1.5), "PWR": (0.5, 0.15)}
GAP = {"DIFF100": 0.15, "DIFF90": 0.18}
VIA_D, VIA_DR = 0.4, 0.2
HV_VIA_D, HV_VIA_DR = 0.8, 0.4
BARRIER_X = (60.0, 73.0)
MARGIN = 0.035
HV_MARGIN = 0.25   # covers KiCad raster error + Freerouting's octagon/additive clearance model
BGA_VIA_D, BGA_VIA_DR = 0.35, 0.2   # JLC POFV-compliant (hole >= 0.2, annular 0.075)
EDGE_CLR = 0.35
mm = pcbnew.ToMM; FM = pcbnew.FromMM

b = pcbnew.LoadBoard(sys.argv[1])
bb = b.GetBoardEdgesBoundingBox()
X0, Y0 = mm(bb.GetX()) - 1, mm(bb.GetY()) - 1
W = int((mm(bb.GetWidth()) + 2) / R) + 1; H = int((mm(bb.GetHeight()) + 2) / R) + 1
def gx(x): return (x - X0) / R
def gy(y): return (y - Y0) / R
def wx(i): return X0 + i * R

netclass = {}
for n, ni in b.GetNetsByName().items():
    netclass[ni.GetNetCode()] = ni.GetNetClassName()
def cls_of(code): return netclass.get(code, "Default")

# ---------------- rasterisation ----------------
lab = [Image.new("I", (W, H), 0) for _ in LAY]     # net code + 1 (0 = empty)
blk = [Image.new("L", (W, H), 0) for _ in LAY]     # track keepout / outside board
vblk = Image.new("L", (W, H), 0)                   # via keepout
padown = {}                                         # net -> list of (layer idx, polygon px)

def poly_px(sps):
    out = []
    for k in range(sps.OutlineCount()):
        o = sps.COutline(k)
        out.append([(gx(mm(o.CPoint(i).x)), gy(mm(o.CPoint(i).y))) for i in range(o.PointCount())])
    return out

def draw_seg(img, a, c, w, val):
    d = ImageDraw.Draw(img)
    r = w / 2 / R
    d.line([a, c], fill=val, width=max(1, int(round(w / R))))
    for p in (a, c): d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=val)

def draw_circle(img, p, rr, val):
    ImageDraw.Draw(img).ellipse([p[0] - rr / R, p[1] - rr / R, p[0] + rr / R, p[1] + rr / R], fill=val)

# board outside
ol = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ol)
inside = Image.new("L", (W, H), 0)
for pg in poly_px(ol): ImageDraw.Draw(inside).polygon(pg, fill=1)
inside = np.array(inside, bool)
inside = edt(inside) * R > EDGE_CLR + 0.1
bx0, bx1 = int(gx(BARRIER_X[0])), int(gx(BARRIER_X[1])) + 1

ALLZ = list(b.Zones()) + [z for f in b.GetFootprints() for z in f.Zones()]
for z in ALLZ:
    if not z.GetIsRuleArea(): continue
    pgs = poly_px(z.Outline())
    for li, L in enumerate(LAY):
        if z.IsOnLayer(L) and z.GetDoNotAllowTracks():
            for pg in pgs: ImageDraw.Draw(blk[li]).polygon(pg, fill=1)
    if z.GetDoNotAllowVias():
        for pg in pgs: ImageDraw.Draw(vblk).polygon(pg, fill=1)

for f in b.GetFootprints():
    for p in f.Pads():
        code = p.GetNetCode()
        for li, L in enumerate(LAY):
            if not p.IsOnLayer(L): continue
            for pg in poly_px(p.GetEffectivePolygon(L)):
                ImageDraw.Draw(lab[li]).polygon(pg, fill=code + 1 if code > 0 else 999999)
                padown.setdefault(code, []).append((li, pg))
        if p.GetDrillSize().x > 0:
            c = p.GetPosition(); rr = mm(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2 + 0.1
            for li in range(3):
                if not p.IsOnLayer(LAY[li]):
                    draw_circle(lab[li], (gx(mm(c.x)), gy(mm(c.y))), rr, code + 1 if code > 0 else 999999)
        # no vias through any pad of another part (via-in-pad handled per net)
        for pg in poly_px(p.GetEffectivePolygon(pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu)):
            ImageDraw.Draw(vblk).polygon(pg, fill=1)

def add_track_px(t):
    code = t.GetNetCode() + 1
    if t.Type() == pcbnew.PCB_VIA_T:
        p = (gx(mm(t.GetPosition().x)), gy(mm(t.GetPosition().y)))
        r = mm(t.GetWidth(pcbnew.F_Cu)) / 2
        for li in range(3): draw_circle(lab[li], p, r, code)
        return
    L = t.GetLayer()
    if L not in LAY: return
    li = LAY.index(L)
    a = (gx(mm(t.GetStart().x)), gy(mm(t.GetStart().y))); c = (gx(mm(t.GetEnd().x)), gy(mm(t.GetEnd().y)))
    draw_seg(lab[li], a, c, mm(t.GetWidth()), code)

for t in b.GetTracks(): add_track_px(t)

LAB = np.stack([np.array(i, np.int32) for i in lab])
BLK = np.stack([np.array(i, bool) for i in blk]) | ~inside[None]
VBLK = np.array(vblk, bool) | ~inside
VBLK[:, bx0:bx1] = True
CLSARR = {}
def class_mask(names):
    codes = [c + 1 for c, n in netclass.items() if n in names]
    return np.isin(LAB, codes)

# ---------------- numba A* ----------------
@numba.njit(cache=True)
def astar(free, vfree, cost, src, tgt, tpts, viac):
    L, Hh, Ww = free.shape
    INF = 1e18
    g = np.full(free.shape, INF)
    par = np.full(free.shape, -1, np.int64)
    cap = 1 << 20
    hk = np.empty(cap); hv = np.empty(cap, np.int64); n = 0
    def hfun(y, x):
        best = INF
        for k in range(tpts.shape[0]):
            dy = abs(y - tpts[k, 0]); dx = abs(x - tpts[k, 1])
            hh = 10.0 * max(dx, dy) + 4.142 * min(dx, dy)
            if hh < best: best = hh
        return best
    # seed
    for l in range(L):
        for y in range(Hh):
            for x in range(Ww):
                if src[l, y, x] and free[l, y, x]:
                    g[l, y, x] = 0.0
                    idx = (l * Hh + y) * Ww + x
                    if n >= cap:
                        cap *= 2; hk2 = np.empty(cap); hv2 = np.empty(cap, np.int64)
                        hk2[:n] = hk[:n]; hv2[:n] = hv[:n]; hk = hk2; hv = hv2
                    # push
                    i = n; hk[i] = hfun(y, x); hv[i] = idx; n += 1
                    while i > 0:
                        p = (i - 1) >> 1
                        if hk[p] <= hk[i]: break
                        hk[p], hk[i] = hk[i], hk[p]; hv[p], hv[i] = hv[i], hv[p]; i = p
    dys = np.array([-1, 1, 0, 0, -1, -1, 1, 1]); dxs = np.array([0, 0, -1, 1, -1, 1, -1, 1])
    dc = np.array([10.0, 10.0, 10.0, 10.0, 14.142, 14.142, 14.142, 14.142])
    found = -1
    while n > 0:
        k0 = hk[0]; idx = hv[0]
        n -= 1; hk[0] = hk[n]; hv[0] = hv[n]
        i = 0
        while True:
            a = 2 * i + 1; c = a + 1; m = i
            if a < n and hk[a] < hk[m]: m = a
            if c < n and hk[c] < hk[m]: m = c
            if m == i: break
            hk[m], hk[i] = hk[i], hk[m]; hv[m], hv[i] = hv[i], hv[m]; i = m
        l = idx // (Hh * Ww); r = idx % (Hh * Ww); y = r // Ww; x = r % Ww
        gc = g[l, y, x]
        if k0 - hfun(y, x) > gc + 1e-6: continue
        if tgt[l, y, x]:
            found = idx; break
        for d in range(9 + L - 1):
            if d < 8:
                nl = l; ny = y + dys[d]; nx = x + dxs[d]; st = dc[d]
                if ny < 0 or nx < 0 or ny >= Hh or nx >= Ww: continue
                if d >= 4 and not (free[l, y, nx] or free[l, ny, x]): continue
                st = st * cost[nl, ny, nx]
            else:
                nl = d - 8
                if nl >= l: nl += 1
                if nl >= L: continue
                ny = y; nx = x
                if not vfree[y, x]: continue
                st = viac
            if not free[nl, ny, nx]: continue
            ng = gc + st
            if ng < g[nl, ny, nx]:
                g[nl, ny, nx] = ng
                nidx = (nl * Hh + ny) * Ww + nx
                par[nl, ny, nx] = idx
                if n >= cap:
                    cap *= 2; hk2 = np.empty(cap); hv2 = np.empty(cap, np.int64)
                    hk2[:n] = hk[:n]; hv2[:n] = hv[:n]; hk = hk2; hv = hv2
                i = n; hk[i] = ng + hfun(ny, nx); hv[i] = nidx; n += 1
                while i > 0:
                    p = (i - 1) >> 1
                    if hk[p] <= hk[i]: break
                    hk[p], hk[i] = hk[i], hk[p]; hv[p], hv[i] = hv[i], hv[p]; i = p
    path = []
    while found >= 0:
        path.append(found)
        l = found // (Hh * Ww); r = found % (Hh * Ww)
        found = par[l, r // Ww, r % Ww]
    return path

# ---------------- per-net obstacle model ----------------
def disk_dist(occ):
    # distance (mm) from every cell to nearest True cell in occ (per layer)
    out = np.empty(occ.shape, np.float32)
    for l in range(occ.shape[0]):
        out[l] = edt(~occ[l]) * R if occ[l].any() else 1e3
    return out

HVN = set(c + 1 for c, n in netclass.items() if n == "HV_LINE")
DIVN = set(c + 1 for c, n in netclass.items() if n == "HV_LINE_DIV")

def free_map(code, w, win, extra_clear=0.0, allow_layers=(0, 1, 2)):
    y0, y1, x0, x1 = win
    lab_w = LAB[:, y0:y1, x0:x1]
    me = code + 1; cl = cls_of(code)
    other = (lab_w != 0) & (lab_w != me)
    hv = np.isin(lab_w, list(HVN - {me})) & other
    dv = np.isin(lab_w, list(DIVN - {me})) & other
    nrm = other & ~hv & ~dv
    own_c = CLS.get(cl, CLS["Default"])[1]
    dn, dh, dd = disk_dist(nrm), disk_dist(hv), disk_dist(dv)
    free = np.zeros(lab_w.shape, bool)
    for l in range(3):
        outer = OUTER[l]
        if cl == "HV_LINE":
            c_n = 3.0 if outer else 1.5; c_h = c_n; c_d = 1.5
        elif cl == "HV_LINE_DIV":
            c_n = c_h = c_d = 1.5
        else:
            c_n = max(own_c, 0.12) + extra_clear; c_h = 3.0 if outer else 1.5; c_d = 1.5
        hw = w / 2
        mn = HV_MARGIN if cl.startswith("HV") else MARGIN
        free[l] = (dn[l] > c_n + hw + mn) & (dh[l] > c_h + hw + HV_MARGIN) & (dd[l] > c_d + hw + HV_MARGIN)
        if l not in allow_layers: free[l] = False
    free &= ~BLK[:, y0:y1, x0:x1]
    free |= (lab_w == me)                      # own copper always enterable
    vd = (HV_VIA_D if cl.startswith("HV") else VIA_D)
    # via must clear others on all layers
    c_v = (1.5 if cl.startswith("HV") else max(own_c, 0.12))
    vfree = np.ones(lab_w.shape[1:], bool)
    for l in range(3):
        vfree &= (dn[l] > c_v + vd / 2 + 0.1) & (dh[l] > (3.0 if OUTER[l] else 1.5) + vd / 2 + HV_MARGIN) & (dd[l] > 1.5 + vd / 2 + HV_MARGIN)
    vfree_nopad = np.ones(lab_w.shape[1:], bool)
    for l in range(3):
        vfree_nopad &= (dn[l] > c_v + BGA_VIA_D / 2 + MARGIN) & (dh[l] > 3.0 + BGA_VIA_D / 2) & (dd[l] > 1.5 + BGA_VIA_D / 2)
    vfree &= ~VBLK[y0:y1, x0:x1]
    return free, vfree, (dn, dh, dd, vfree_nopad)

# ---------------- board writing ----------------
_u = b.FindFootprintByReference("U21")
_ub = _u.GetCourtyard(pcbnew.B_Cu if _u.IsFlipped() else pcbnew.F_Cu).BBox()
U21BB = (mm(_ub.GetX()), mm(_ub.GetY()), mm(_ub.GetRight()), mm(_ub.GetBottom()))
ds = b.GetDesignSettings(); ds.m_ViasMinSize = FM(0.35); ds.m_MinThroughDrill = FM(0.2); ds.m_ViasMinAnnularWidth = FM(0.075)
made = []
def add_track(code, li, a, c, w):
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(FM(a[0]), FM(a[1]))); t.SetEnd(pcbnew.VECTOR2I(FM(c[0]), FM(c[1])))
    t.SetWidth(FM(w)); t.SetLayer(LAY[li]); t.SetNetCode(code); t.SetLocked(True); b.Add(t); made.append(t); add_track_px_np(t)
def add_via(code, p, d, dr):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(FM(p[0]), FM(p[1])))
    v.Padstack().SetSize(pcbnew.VECTOR2I(FM(d), FM(d)), pcbnew.F_Cu); v.SetDrill(FM(dr))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(code); v.SetLocked(True); b.Add(v); made.append(v); add_track_px_np(v)

def add_track_px_np(t):
    # rasterise one new item straight into LAB (small local PIL image)
    code = t.GetNetCode() + 1
    if t.Type() == pcbnew.PCB_VIA_T:
        p = (gx(mm(t.GetPosition().x)), gy(mm(t.GetPosition().y))); rr = mm(t.GetWidth(pcbnew.F_Cu)) / 2 / R + 0.5
        yy, xx = np.ogrid[:H, :W]
        y0, y1 = int(p[1] - rr - 2), int(p[1] + rr + 3); x0, x1 = int(p[0] - rr - 2), int(p[0] + rr + 3)
        sub = (yy[y0:y1] - p[1]) ** 2 + (xx[:, x0:x1] - p[0]) ** 2 <= rr * rr
        for l in range(3): LAB[l, y0:y1, x0:x1][sub] = code
        return
    li = LAY.index(t.GetLayer())
    a = np.array([gx(mm(t.GetStart().x)), gy(mm(t.GetStart().y))]); c = np.array([gx(mm(t.GetEnd().x)), gy(mm(t.GetEnd().y))])
    rr = mm(t.GetWidth()) / 2 / R + 0.5
    x0, y0 = (np.minimum(a, c) - rr - 2).astype(int); x1, y1 = (np.maximum(a, c) + rr + 3).astype(int)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = c - a; L2 = max(d @ d, 1e-9)
    tt = np.clip(((xx - a[0]) * d[0] + (yy - a[1]) * d[1]) / L2, 0, 1)
    dist2 = (xx - a[0] - tt * d[0]) ** 2 + (yy - a[1] - tt * d[1]) ** 2
    LAB[li, y0:y1, x0:x1][dist2 <= rr * rr] = code

def emit_path(code, path, win, w):
    y0, y1, x0, x1 = win; Hh, Ww = y1 - y0, x1 - x0
    pts = []
    for idx in reversed(path):
        l = idx // (Hh * Ww); r = idx % (Hh * Ww)
        pts.append((l, wx(x0 + r % Ww), Y0 + (y0 + r // Ww) * R))
    cl = cls_of(code)
    vd, vdr = (HV_VIA_D, HV_VIA_DR) if cl.startswith("HV") else (VIA_D, VIA_DR)
    length = 0.0; nvia = 0
    i = 0
    while i < len(pts) - 1:
        if pts[i + 1][0] != pts[i][0]:
            x_, y_ = pts[i][1:]
            inbga = U21BB[0] <= x_ <= U21BB[2] and U21BB[1] <= y_ <= U21BB[3]
            add_via(code, pts[i][1:], *( (BGA_VIA_D, BGA_VIA_DR) if inbga else (vd, vdr))); nvia += 1; i += 1; continue
        j = i + 1
        d0 = (round((pts[j][1] - pts[i][1]) / R), round((pts[j][2] - pts[i][2]) / R))
        while j + 1 < len(pts) and pts[j + 1][0] == pts[i][0] and \
              (round((pts[j + 1][1] - pts[j][1]) / R), round((pts[j + 1][2] - pts[j][2]) / R)) == d0:
            j += 1
        add_track(code, pts[i][0], pts[i][1:], pts[j][1:], w)
        length += math.hypot(pts[j][1] - pts[i][1], pts[j][2] - pts[i][2]); i = j
    return length, nvia, pts

# ---------------- routing a net (tree growth) ----------------
def pad_mask(code, win, pads=None):
    y0, y1, x0, x1 = win
    m = np.zeros((3, y1 - y0, x1 - x0), bool)
    for li, pg in padown.get(code, []):
        if pads is not None and not any(_poly_hit(pg, p) for p in pads): continue
        img = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(img).polygon([(x - x0, y - y0) for x, y in pg], fill=1)
        m[li] |= np.array(img, bool)
    # BGA escape copper (pre-placed dog-bone / VIP via) counts as part of the U21 pad
    own = LAB[:, y0:y1, x0:x1] == code + 1
    for p in (pads if pads is not None else pads_of(code)):
        if p.GetParentFootprint().GetReference() != "U21": continue
        c = p.GetPosition(); cy, cx = gy(mm(c.y)) - y0, gx(mm(c.x)) - x0
        yy, xx = np.ogrid[:y1 - y0, :x1 - x0]
        m |= own & (((yy - cy) ** 2 + (xx - cx) ** 2) <= (0.8 / R) ** 2)[None]
    return m
def _poly_hit(pg, pad):
    c = pad.GetPosition(); x, y = gx(mm(c.x)), gy(mm(c.y))
    xs = [q[0] for q in pg]; ys = [q[1] for q in pg]
    return min(xs) - .5 <= x <= max(xs) + .5 and min(ys) - .5 <= y <= max(ys) + .5

def pads_of(code):
    return [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetCode() == code]

def window(pads, margin=8.0):
    xs = [mm(p.GetPosition().x) for p in pads]; ys = [mm(p.GetPosition().y) for p in pads]
    x0 = max(0, int(gx(min(xs) - margin))); x1 = min(W, int(gx(max(xs) + margin)) + 1)
    y0 = max(0, int(gy(min(ys) - margin))); y1 = min(H, int(gy(max(ys) + margin)) + 1)
    return (y0, y1, x0, x1)

def connected_groups(pads):
    # pads already joined by existing copper of this net are one group (rough: same footprint + same net = joined for ESD flow-through parts)
    groups = []
    for p in pads:
        groups.append([p])
    return groups

def route_net(code, w=None, cost=None, viac=300.0, margin=8.0, allow_layers=(0, 1, 2), order=None, extra_clear=0.0):
    pads = order or pads_of(code)
    cl = cls_of(code); w = w or CLS.get(cl, CLS["Default"])[0]
    if len(pads) < 2: return None
    win = window(pads, margin)
    y0, y1, x0, x1 = win
    free, vfree, (_, _, _, vnp) = free_map(code, w, win, extra_clear, allow_layers)
    # via-in-pad allowed in own BGA pads (U21)
    # U21 escape (vias/dog-bones) is pre-placed by bga_escape_u21.py; no in-router via-in-pad
    if cost is None: cost = np.ones(free.shape, np.float64)
    tree = [pads[0]]; rest = pads[1:]
    total = 0.0; vias = 0; allpts = []
    # group flow-through pads of same footprint as already connected (e.g. D17 pads 1 & 10)
    while rest:
        src = pad_mask(code, win, tree) | (LAB[:, y0:y1, x0:x1] == code + 1) & False
        for t in made:
            pass
        tgt = pad_mask(code, win, rest)
        tp = np.array([[gy(mm(p.GetPosition().y)) - y0, gx(mm(p.GetPosition().x)) - x0] for p in rest], np.float64)
        srcm = (src | own_new_copper(code, win)) & ~tgt   # escape copper at the target is not a source
        path = astar(free.astype(np.uint8), vfree.astype(np.uint8), cost, srcm, tgt, tp, viac)
        if not path:
            return dict(ok=False, length=total, vias=vias, failed=[f"{p.GetParentFootprint().GetReference()}.{p.GetNumber()}" for p in rest], pts=allpts)
        ln, nv, pts = emit_path(code, path, win, w); total += ln; vias += nv; allpts.append(pts)
        # which pad did we reach?
        l_end, ex, ey = pts[-1]
        reached = min(rest, key=lambda p: math.hypot(mm(p.GetPosition().x) - ex, mm(p.GetPosition().y) - ey))
        rref = reached.GetParentFootprint().GetReference()
        same = [p for p in rest if p.GetParentFootprint().GetReference() == rref] if rref[0] == "D" else [reached]
        for p in same: rest.remove(p); tree.append(p)
        free |= (LAB[:, y0:y1, x0:x1] == code + 1)
    return dict(ok=True, length=total, vias=vias, failed=[], pts=allpts)

def own_new_copper(code, win):
    y0, y1, x0, x1 = win
    return (LAB[:, y0:y1, x0:x1] == code + 1) & ~pad_any(win)
_pad_any = None
def pad_any(win):
    global _pad_any
    if _pad_any is None:
        img = [Image.new("L", (W, H), 0) for _ in LAY]
        for code, lst in padown.items():
            for li, pg in lst: ImageDraw.Draw(img[li]).polygon(pg, fill=1)
        _pad_any = np.stack([np.array(i, bool) for i in img])
    y0, y1, x0, x1 = win
    return _pad_any[:, y0:y1, x0:x1]

# ---------------- differential pairs ----------------
def route_pair(pn, nn, report):
    P = b.FindNet(pn).GetNetCode(); N = b.FindNet(nn).GetNetCode()
    cl = cls_of(P); w = CLS[cl][0]; gap = GAP[cl]; pitch = gap + w
    padsP = pads_of(P); padsN = pads_of(N)
    win = window(padsP + padsN, 10.0); y0, y1, x0, x1 = win
    # P cost: penalise cells where the N partner (offset pitch) would not fit on either side
    freeP_fat, _, _ = free_map(P, w + 2 * pitch, win)
    costP = np.where(freeP_fat, 1.0, 4.0).astype(np.float64)
    # temporarily hide N pads from P's obstacle set? no: N pads are real obstacles for P.
    rP = route_net(P, w, costP, viac=400.0, margin=10.0)
    # N follows: band cost around distance == pitch from P copper
    pm = (LAB[:, y0:y1, x0:x1] == P + 1) & ~pad_any(win)
    d = disk_dist(pm)
    costN = (1.0 + 6.0 * np.minimum(np.abs(d - pitch) / pitch, 3.0)).astype(np.float64)
    rN = route_net(N, w, costN, viac=400.0, margin=10.0)
    skew = abs(rP["length"] - rN["length"])
    report.append((pn, nn, rP["ok"], rN["ok"], round(rP["length"], 2), round(rN["length"], 2), round(skew, 2), rP["vias"], rN["vias"], rP["failed"] + rN["failed"]))
    return rP, rN


# ---------------- skew tuning (trombone serpentines) ----------------
def net_len(code):
    return sum(mm(t.GetLength()) for t in b.GetTracks() if t.GetNetCode() == code and t.Type() != pcbnew.PCB_VIA_T)

def tune_pair(P, N, tol=0.10):
    lp, ln = net_len(P), net_len(N)
    S, O = (P, N) if lp < ln else (N, P)
    delta = abs(lp - ln)
    if delta <= tol: return delta
    w = CLS[cls_of(S)][0]
    segs = sorted([t for t in made if t.GetNetCode() == S and t.Type() != pcbnew.PCB_VIA_T], key=lambda t: -t.GetLength())
    for t in segs:
        if delta <= tol: break
        a = np.array([mm(t.GetStart().x), mm(t.GetStart().y)]); c = np.array([mm(t.GetEnd().x), mm(t.GetEnd().y)])
        L = float(np.linalg.norm(c - a))
        if L < 1.4: continue
        u = (c - a) / L; nrm = np.array([-u[1], u[0]])
        li = LAY.index(t.GetLayer())
        win = (max(0, int(gy(min(a[1], c[1]) - 3))), min(H, int(gy(max(a[1], c[1]) + 3))), max(0, int(gx(min(a[0], c[0]) - 3))), min(W, int(gx(max(a[0], c[0]) + 3))))
        free, _, _ = free_map(S, w, win)
        def ok(pts):
            for q0, q1 in zip(pts[:-1], pts[1:]):
                n_ = max(2, int(np.linalg.norm(q1 - q0) / 0.04))
                for f_ in np.linspace(0, 1, n_):
                    q = q0 + f_ * (q1 - q0); yy, xx = int(round(gy(q[1]))) - win[0], int(round(gx(q[0]))) - win[2]
                    if not (0 <= yy < free.shape[1] and 0 <= xx < free.shape[2]) or not free[li, yy, xx]: return False
            return True
        sp = 0.6
        kmax = int((L - 0.4) / sp)
        if kmax < 1: continue
        done = False
        for side in (1, -1):
            m = (a + c) / 2 + side * nrm * (GAP[cls_of(S)] + w)
            if LAB[li, int(round(gy(m[1]))), int(round(gx(m[0])))] == O + 1: continue   # never bulge toward partner
            for hmax in (0.7, 0.5, 0.35, 0.25):
                k = min(kmax, int(math.ceil(delta / (2 * hmax))))
                h = delta / (2 * k)
                if h > hmax + 1e-9: continue
                o0 = (L - k * sp) / 2
                pts = [a]
                for i in range(k):
                    p0 = a + u * (o0 + i * sp)
                    pts += [p0, p0 + side * nrm * h, p0 + u * sp / 2 + side * nrm * h, p0 + u * sp / 2]
                pts.append(c)
                if not ok(pts[1:-1]): continue
                code = t.GetNetCode(); b.Remove(t); made.remove(t)
                for q0, q1 in zip(pts[:-1], pts[1:]):
                    if np.linalg.norm(q1 - q0) > 1e-6: add_track(code, li, (float(q0[0]), float(q0[1])), (float(q1[0]), float(q1[1])), w)
                delta = abs(net_len(P) - net_len(N)); done = True; break
            if done: break
    return abs(net_len(P) - net_len(N))


# ---------------- groups ----------------
def nets_matching(rx):
    return sorted(str(n) for n in b.GetNetsByName().keys() if re.search(rx, str(n)))

def jobs_for(gname):
    J = []
    if gname == "hv":
        names = [str(n) for n in b.GetNetsByName().keys() if cls_of(b.FindNet(str(n)).GetNetCode()) in ("HV_LINE", "HV_LINE_DIV")]
        names += nets_matching(r"Net-\(R4(25|32|39|51)-Pad2\)|_TAP$|(GEN|BUS)_V[ABCN]_[PN]$")
        J += [("net", n, dict(margin=10.0)) for n in sorted(set(names))]
    elif gname == "xtal":
        J += [("net", n, dict(viac=2000.0)) for n in nets_matching(r"HSE_IN|HSE_OUT|U7-PC14|U7-PC15|ADE_XI|ADE_XO")]
    elif gname == "ade":
        J += [("net", n, dict(margin=12.0)) for n in nets_matching(r"AC_(CS1_N|CS2_N|IRQ_N|MISO|MOSI|RST_N|SCK)$|ADE_(IRQ_N_I|MISO_I|MOSI_I|SCK_I)$|^ADE_(CS1_N|CS2_N|IRQ_N|MISO|MOSI|RST_N|SCK)$")]
    else:
        rx = {"eth": r"^ETH\d_P$", "usb": r"^USB3\d_DP$", "lvds": r"LVDS[0-3C]_P$", "dsi": r"^DSI_(C|D\d)_P$"}[gname]
        for pn in nets_matching(rx):
            nn = re.sub(r"_P$", "_N", pn) if not pn.endswith("_DP") else pn[:-2] + "DM"
            J.append(("pair", pn, dict(nn=nn)))
    return [(gname,) + j for j in J]

def run_job(job, rep):
    g, kind, name, kw = job
    if kind == "net":
        r = route_net(b.FindNet(name).GetNetCode(), **kw)
        if r: rep.append(dict(group=g, net=name, ok=r["ok"], length=round(r["length"], 2), vias=r["vias"], failed=r["failed"]))
        return (not r) or r["ok"]
    out = []; route_pair(name, kw["nn"], out)
    pn, nn, okp, okn, lp, ln, sk, vp, vn, fl = out[0]
    if okp and okn:
        P = b.FindNet(pn).GetNetCode(); N = b.FindNet(nn).GetNetCode()
        sk = round(tune_pair(P, N), 3); lp = round(net_len(P), 2); ln = round(net_len(N), 2)
    rep.append(dict(group=g, net=pn, pair=nn, ok=okp and okn, length=lp, length_n=ln, skew=sk, vias=vp, vias_n=vn, failed=fl))
    return okp and okn

if __name__ == "__main__":
    import json, time, os
    groups = sys.argv[3:] or ["dsi", "lvds", "eth", "usb", "xtal", "ade", "hv"]
    jobs = [j for g in groups for j in jobs_for(g)]
    prio = json.load(open(os.environ["PRIO"])) if os.environ.get("PRIO") else []
    jobs.sort(key=lambda j: (0 if j[2] in prio else 1, prio.index(j[2]) if j[2] in prio else 0))
    rep = []; failed = []
    t0 = time.time()
    for j in jobs:
        if not run_job(j, rep): failed.append(j[2])
    print(f"routed {len(jobs)-len(failed)}/{len(jobs)} jobs in {time.time()-t0:.0f}s; failed: {failed}")
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(sys.argv[2])
    json.dump(dict(report=rep, failed=failed), open(sys.argv[2] + ".route.json", "w"), indent=1)
    print("locked items added:", len(made))
