import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np, cadquery as cq
import enclosure as E, geometry as G
parts = E.build()
EXPL = {"bezel": 0, "display": 60, "keypad_silicone": -40, "keypad_caps": -40, "switches": -110, "pcb": -110,
        "gasket": -170, "customer_panel": -230, "rear_shell": -300, "screws_M4": 80, "clamp_brackets": -380, "clamp_screws_M4": -380}
fig = plt.figure(figsize=(16, 11)); ax = fig.add_subplot(projection="3d")
for n, (wp, col) in parts.items():
    v, t = wp.val().tessellate(0.8, 0.5)
    V = np.array([(p.x, p.y, p.z + EXPL[n]) for p in v])
    pc = Poly3DCollection(V[np.array(t)], facecolor=col, edgecolor="none", alpha=0.35 if n == "customer_panel" else 0.95)
    pc.set_facecolor(col + ((0.35,) if n == "customer_panel" else (1,))) ; ax.add_collection3d(pc)
    ax.text(V[:,0].max() + 10, V[:,1].mean(), V[:,2].mean(), n, fontsize=9)
ax.set_xlim(-30, 330); ax.set_ylim(-260, 100); ax.set_zlim(-460, 120)
ax.set_box_aspect((360, 360, 580)); ax.view_init(elev=18, azim=-58); ax.set_axis_off()
ax.set_title("genctl enclosure concept - exploded (rev C: SLS PA12 shell, front slide-in, rear hook clamps, cut-sheet keypad)\n"
             "unit = bezel (PE boss) + display + 12 SLA caps/2 silicone strips/12 nibs + PCB + PA12 shell (8 rear M4) + gasket; panel behind; 6 hook clamps")
fig.savefig("exploded_view.png", dpi=110, bbox_inches="tight")

# ---- section at x through the right switch of key SW9 ----
X = G.BTN_X[1]
fig, ax = plt.subplots(figsize=(15, 8))
for n, (wp, col) in parts.items():
    pass
    sl = wp.intersect(cq.Workplane("YZ").workplane(offset=X - 0.01).rect(1000, 1000).extrude(0.02))
    try: fl = sl.faces(">X").vals()
    except Exception: fl = []
    for f in fl:
        v, t = f.tessellate(0.05)
        for tri in t:
            P = np.array([(-v[i].y, -v[i].z) for i in tri])
            ax.fill(P[:,0], P[:,1], color=col, alpha=0.6 if n=="customer_panel" else 0.95, lw=0)
ax.set_aspect("equal"); ax.invert_yaxis()
ax.set_xlabel("y (front view, mm, down = +)"); ax.set_ylabel("depth behind panel face Z (mm)")
def dim(y, z0, z1, txt):
    ax.annotate("", (y, z0), (y, z1), arrowprops=dict(arrowstyle="<->", lw=0.8)); ax.text(y + 1.5, (z0+z1)/2, txt, fontsize=8)
zp = E.Z_PANEL
dim(-44, 0, E.BEZEL_T, f"field {E.BEZEL_T}"); dim(-40, 0, E.RIM_Z, f"rim {E.RIM_Z}")
dim(-36, 0, E.Z_PCB, f"PCB front {E.Z_PCB}"); dim(-52, zp, zp + E.PANEL_T, f"panel {E.PANEL_T} (1-5)")
dim(-60, 0, E.SHELL_DEPTH, f"overall depth {E.SHELL_DEPTH}"); dim(-48, E.RIM_Z, zp, "gasket 2.0->1.4")
dim(20, 0, G.LEDGE_Z, f"glass seat/ledge {G.LEDGE_Z}"); dim(30, 0, G.MODULE_DEPTH_MAX, f"display {G.MODULE_DEPTH_MAX}")
yc = E.sy0
ax.annotate("", (-(yc) , 40), (-(yc - E.CUT_GAP), 40), arrowprops=dict(arrowstyle="<->", lw=0.6))
ax.text(-yc - 30, 42, f"cutout {E.CUT_W:.0f} x {E.CUT_H:.0f} (+1/-0); shell {E.SHELL_W:.0f} x {E.SHELL_H:.0f}", fontsize=8)
ax.text(-yc - 30, 25, "hook clamp: 2 mm SS bracket in BLIND pockets of a\n2.5 mm PA12 pad (nothing enters the shell); M4x16 on panel", fontsize=8)
ax.text(-8, -4, f"cap head 1.3 above face, pocket clr {E.GUIDE_CLR}/side", fontsize=8)
ax.text(-8, 12.5, f"1 switch/key; SLA cap {E.CAP_W}x{E.CAP_H} in {E.GUIDE_L} mm pocket", fontsize=8)
ax.text(-yc + 2, 6.8, "PA12 flange 2.5 + 8 M4 (flanged head) from rear", fontsize=7)
ax.set_xlim(-75, 215); ax.set_ylim(70, -10)
ax.set_title(f"Section at x = {X:.2f} (key SW10 centre + top clamp). bezel dark, glass blue, keypad grey/cyan, PCB green, gasket orange, door grey, shell")
fig.savefig("section_view.png", dpi=130, bbox_inches="tight")
# zoom
ax.set_xlim(-75, 30); ax.set_ylim(46, -6); fig.savefig("section_view_detail.png", dpi=150, bbox_inches="tight")
print("ok")
