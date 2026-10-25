"""METAL KEY CAP OPTION (alternative; baseline = SLA clear caps in enclosure.py, unchanged).
One key, local coords: X along the cap (24), Y across (12), Z = depth behind panel face (CQ Z = -depth).
Variant M1 (CNC): 6061 cap with head flange, rear cavity, front light slot; clear SLA light piece snaps in from behind.
Variant M2 (simpler): same cap, light piece = laser-cut clear acrylic strip glued into the slot (no clip).
Run: /workspace/cqenv/bin/python cap_metal.py -> step/metal_cap_*.step, metal_cap.png"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cadquery as cq
import enclosure as E   # baseline params (CAP_W, CAP_H, GUIDE_L, HEAD_*, WEB_T, Z_PCB)

CW, CH, L = E.CAP_W, E.CAP_H, E.GUIDE_L
HO, HT, HG = E.HEAD_OVER, E.HEAD_T, E.HEAD_GAP
CLR_M = 0.10                     # cap -> pocket per side AFTER finishing (PTFE-impregnated Type III on cap)
FRONT_WALL = 2.0                 # metal behind the face (incl. head) at the slot
SLOT_L, SLOT_W = 16.0, 1.6       # light slot through the face
CAV_W, CAV_H = CW - 2 * 1.5, CH - 2 * 1.5   # rear cavity 21 x 9, walls 1.5
GROOVE_Z, GROOVE_D, GROOVE_W = 2.0, 0.40, 1.0   # snap undercut: groove 0.40 deep, 1.0 wide, 2.0 from cap rear
TAB_L, TAB_T, TAB_W, TAB_I = 4.5, 1.0, 5.0, 0.35  # cantilever snap tab (length, thickness, width, interference)
FIT = 0.05                       # light piece -> cavity/slot clearance per side

def b(x0, y0, x1, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, -(z0 + z1) / 2))

def metal_cap(variant="M1"):
    zf, zr = -HG, L                              # cap face Z (in front of panel) .. rear Z
    c = b(-CW / 2, -CH / 2, CW / 2, CH / 2, zf, zr)
    c = c.union(b(-CW / 2 - HO, -CH / 2 - HO, CW / 2 + HO, CH / 2 + HO, zf - HT, zf))   # head = hard stop
    ztop = zf - HT
    c = c.cut(b(-CAV_W / 2, -CAV_H / 2, CAV_W / 2, CAV_H / 2, ztop + FRONT_WALL, zr + 1))   # rear cavity
    c = c.cut(b(-SLOT_L / 2, -SLOT_W / 2, SLOT_L / 2, SLOT_W / 2, ztop - 1, ztop + FRONT_WALL + 0.1))  # light slot
    if variant == "M1":   # undercut grooves on both long cavity walls for the snap tabs
        for s in (-1, 1):
            y0 = s * CAV_H / 2
            c = c.cut(b(-TAB_W / 2 - 0.3, min(y0, y0 + s * GROOVE_D), TAB_W / 2 + 0.3, max(y0, y0 + s * GROOVE_D),
                        zr - GROOVE_Z - GROOVE_W, zr - GROOVE_Z))
    return c

def light_piece(variant="M1"):
    ztop = -HG - HT
    if variant == "M2":   # laser-cut acrylic strip, 16 x 1.6 slot -> strip (16-0.1) x (FRONT_WALL+1.0), 1.5 thick acrylic on edge
        return b(-SLOT_L / 2 + FIT, -SLOT_W / 2 + FIT, SLOT_L / 2 - FIT, SLOT_W / 2 - FIT, ztop, ztop + FRONT_WALL + 3.0)
    zr = L
    p = b(-SLOT_L / 2 + FIT, -SLOT_W / 2 + FIT, SLOT_L / 2 - FIT, SLOT_W / 2 - FIT, ztop, ztop + FRONT_WALL)  # rib flush with face
    p = p.union(b(-CAV_W / 2 + FIT, -CAV_H / 2 + FIT, CAV_W / 2 - FIT, CAV_H / 2 - FIT, ztop + FRONT_WALL, zr))  # body
    p = p.cut(b(-CAV_W / 2 + 1.2, -CAV_H / 2 + 1.2 + TAB_T, CAV_W / 2 - 1.2, CAV_H / 2 - 1.2 - TAB_T, zr - 4.0, zr + 1))  # rear core-out (light guide stays solid at front)
    for s in (-1, 1):     # cantilever tabs: slot each side so the tab can flex inward, barb = TAB_I
        y_out = s * (CAV_H / 2 - FIT)
        p = p.cut(b(-TAB_W / 2 - 0.5, min(y_out - s * TAB_T, y_out - s * (TAB_T + 0.6)), -TAB_W / 2, max(y_out - s * TAB_T, y_out - s * (TAB_T + 0.6)), zr - TAB_L, zr + 1))
        p = p.cut(b(TAB_W / 2, min(y_out - s * TAB_T, y_out - s * (TAB_T + 0.6)), TAB_W / 2 + 0.5, max(y_out - s * TAB_T, y_out - s * (TAB_T + 0.6)), zr - TAB_L, zr + 1))
        p = p.union(b(-TAB_W / 2, min(y_out, y_out + s * TAB_I), TAB_W / 2, max(y_out, y_out + s * TAB_I),
                      zr - GROOVE_Z - GROOVE_W + 0.1, zr - GROOVE_Z - 0.1))   # barb (lead-in chamfer in drawing)
    return p

def silicone_strip_piece():
    return b(-CW / 2 - 4, -CH / 2 - 1.5, CW / 2 + 4, CH / 2 + 1.5, L, L + E.WEB_T).union(
        cq.Workplane("XY").circle(2.0).extrude(E.Z_PCB - 5.5 - 0.1 - L - E.WEB_T).translate((0, 0, -(E.Z_PCB - 5.5 - 0.1))))

def pocket_section():
    blk = b(-CW / 2 - 8, -CH / 2 - 1.5, CW / 2 + 8, CH / 2 + 1.5, 0, L)
    blk = blk.cut(b(-CW / 2 - CLR_M, -CH / 2 - CLR_M, CW / 2 + CLR_M, CH / 2 + CLR_M, -1, L + 1))
    return blk.cut(b(-50, 0, 50, 50, -5, 20))    # half section (y>0 removed)

def mass_g(wp, rho):
    return wp.val().Volume() * rho / 1000

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__)); os.makedirs(os.path.join(here, "step"), exist_ok=True)
    parts = {"metal_cap_M1": metal_cap("M1"), "metal_cap_lightpiece_M1_SLA": light_piece("M1"),
             "metal_cap_M2": metal_cap("M2"), "metal_cap_lightstrip_M2_acrylic": light_piece("M2"),
             "metal_cap_silicone_strip_piece": silicone_strip_piece(), "metal_cap_pocket_section": pocket_section()}
    for n, w in parts.items():
        cq.exporters.export(w, os.path.join(here, "step", n + ".step"))
    print("Al cap M1 %.1f g, stainless %.1f g, light piece %.2f g" % (mass_g(parts["metal_cap_M1"], 2.70),
          mass_g(parts["metal_cap_M1"], 7.95), mass_g(parts["metal_cap_lightpiece_M1_SLA"], 1.18)))
    # ---- render ----
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(20, 8))
    ax = fig.add_subplot(1, 3, 1, projection="3d")
    show = [("metal_cap_pocket_section", (0.2, 0.2, 0.22), 0), ("metal_cap_M1", (0.55, 0.57, 0.62), 32),
            ("metal_cap_lightpiece_M1_SLA", (0.55, 0.85, 1.0), -22), ("metal_cap_silicone_strip_piece", (0.9, 0.9, 0.8), -42)]
    for n, col, dz in show:
        v, t = parts[n].val().tessellate(0.05, 0.3)
        V = np.array([(p.x, p.y, p.z + dz) for p in v])
        ax.add_collection3d(Poly3DCollection(V[np.array(t)], facecolor=col, edgecolor=(0, 0, 0, 0.15), lw=0.2))
        ax.text(V[:, 0].max() + 3, 0, V[:, 2].mean(), n.replace("metal_cap_", ""), fontsize=8)
    ax.set_xlim(-25, 25); ax.set_ylim(-25, 25); ax.set_zlim(-60, 40); ax.set_box_aspect((50, 50, 100))
    ax.view_init(elev=-25, azim=-60); ax.set_axis_off()
    ax.set_title("Metal cap option M1 - exploded, viewed from behind/below\n(pocket shown half-sectioned)", fontsize=10)
    ax2 = fig.add_subplot(1, 3, 2)
    for n, col in [("metal_cap_pocket_section", (0.2, 0.2, 0.22)), ("metal_cap_M1", (0.55, 0.57, 0.62)),
                   ("metal_cap_lightpiece_M1_SLA", (0.55, 0.85, 1.0)), ("metal_cap_silicone_strip_piece", (0.85, 0.85, 0.7))]:
        sl = parts[n].intersect(cq.Workplane("XY").box(100, 0.02, 100))
        try: fl = sl.faces(">Y").vals()
        except Exception: fl = []
        for f in fl:
            v, t = f.tessellate(0.02)
            for tri in t:
                P = np.array([(v[i].x, -v[i].z) for i in tri]); ax2.fill(P[:, 0], P[:, 1], color=col, lw=0)
    ax2.axhline(0, color="k", lw=0.5, ls=":"); ax2.text(-27, -0.4, "panel face Z0", fontsize=7)
    ax2.axhline(E.Z_PCB - 5.5, color="g", lw=0.6, ls="--"); ax2.text(-27, E.Z_PCB - 5.6, "switch plunger top Z10.5", fontsize=7)
    def dim(x, z0, z1, s):
        ax2.annotate("", (x, z0), (x, z1), arrowprops=dict(arrowstyle="<->", lw=0.7)); ax2.text(x + 0.4, (z0 + z1) / 2, s, fontsize=7)
    dim(14.5, -HG, 0, f"stop {HG}"); dim(-15, 0, L, f"guide {L}"); dim(19, -HG - HT, -HG - HT + FRONT_WALL, f"front wall {FRONT_WALL}")
    ax2.text(-12, -4.2, f"slot {SLOT_L} x {SLOT_W} (light rib flush)", fontsize=7)
    ax2.text(-12, 6.4, f"snap barb {TAB_I} into groove {GROOVE_D}x{GROOVE_W}", fontsize=7)
    ax2.text(-12, 8.9, "silicone strip (primed) + nib", fontsize=7)
    ax2.set_aspect("equal"); ax2.invert_yaxis(); ax2.set_xlim(-28, 28); ax2.set_ylim(12, -5)
    ax2.set_xlabel("x along cap (mm)"); ax2.set_ylabel("Z behind panel face (mm)")
    ax2.set_title(f"Section y=0: 6061 cap {CW}x{CH} (PTFE hard-anodise, clr {CLR_M}/side), clear SLA light piece", fontsize=10)
    ax3 = fig.add_subplot(1, 3, 3)
    for n, col in [("metal_cap_M1", (0.55, 0.57, 0.62)), ("metal_cap_lightpiece_M1_SLA", (0.55, 0.85, 1.0)),
                   ("metal_cap_silicone_strip_piece", (0.85, 0.85, 0.7))]:
        sl = parts[n].intersect(cq.Workplane("XY").box(0.02, 100, 100).translate((0.0, 0, 0)))
        try: fl = sl.faces(">X").vals()
        except Exception: fl = []
        for f in fl:
            v, t = f.tessellate(0.02)
            for tri in t:
                P = np.array([(v[i].y, -v[i].z) for i in tri]); ax3.fill(P[:, 0], P[:, 1], color=col, lw=0)
    pk = pocket_section().union(pocket_section().mirror("XZ"))
    sl = pk.intersect(cq.Workplane("XY").box(0.02, 100, 100))
    for f in sl.faces(">X").vals():
        v, t = f.tessellate(0.02)
        for tri in t:
            P = np.array([(v[i].y, -v[i].z) for i in tri]); ax3.fill(P[:, 0], P[:, 1], color=(0.2, 0.2, 0.22), lw=0)
    ax3.axhline(0, color="k", lw=0.5, ls=":")
    ax3.annotate("barb 0.35 / groove 0.40 x 1.0\n2.0 from cap rear; tab 1.0 x 4.5 x 5 wide", (CAV_H / 2, L - 2.5), (9, 3),
                 fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6))
    ax3.set_aspect("equal"); ax3.invert_yaxis(); ax3.set_xlim(-14, 22); ax3.set_ylim(12, -5)
    ax3.set_xlabel("y across cap (mm)"); ax3.set_title("Section x=0 (through snap tabs and slot)", fontsize=10)
    fig.savefig(os.path.join(here, "metal_cap.png"), dpi=130, bbox_inches="tight"); print("png ok")
