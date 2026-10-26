import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np, cadquery as cq
import enclosure_v3 as E
parts = E.build()
EXPL = {"key_caps": 60, "bezel": 0, "display": 30, "key_membrane": -30, "key_nibs": -45, "switches": -90, "pcb": -90, "rear_parts": -90,
        "thermal_pads": -130, "heat_bar": -150, "gasket": -200, "customer_panel": -250, "rear_shell": -320, "clamps": -420, "clamp_screws": -440}
def view(fname, expl, title, skip=()):
    fig = plt.figure(figsize=(16, 11)); ax = fig.add_subplot(projection="3d")
    for n, (wp, col) in parts.items():
        if n in skip: continue
        v, t = wp.val().tessellate(0.8, 0.5)
        V = np.array([(p.x, p.y, p.z + (EXPL.get(n, {"front_ring": 80, "light_pipe": 40, "fin_plate": -170, "heat_pillar": -130, "strip_pad": -185, "exl1_strip": -200, "fan_gaskets": -185, "fans": -215, "fan_screws": -215, "filter_covers": -240, "pe_bond": -60}.get(n, 0)) if expl else 0)) for p in v])
        a = 0.3 if n == "customer_panel" else 1
        ax.add_collection3d(Poly3DCollection(V[np.array(t)], facecolor=col + (a,), edgecolor="none"))
        if expl: ax.text(V[:, 0].max() + 10, V[:, 1].mean(), V[:, 2].mean(), n, fontsize=8)
    zl = (-480, 100) if expl else (-120, 40)
    ax.set_xlim(-40, 320); ax.set_ylim(-260, 100); ax.set_zlim(*zl)
    ax.set_box_aspect((360, 360, zl[1] - zl[0])); ax.view_init(elev=18 if expl else (-25 if "rear" in fname else 25), azim=-58 if expl else (-130 if "rear" in fname else -60)); ax.set_axis_off()
    ax.set_title(title, fontsize=10); fig.savefig(fname, dpi=110, bbox_inches="tight"); plt.close(fig)
view("exploded_view_v3.png", True, "Blackstart enclosure v3 exploded: CNC Al bezel (heat spreader) + SLA caps/silicone strips/nibs + PCB v4 + Al heat bar + PA12 SLS shell + 6 PA12 rear clamps + PA12 front ring + Al rear fin plate (phase 4)")
view("iso_rear_v3.png", False, "v3 assembled, rear iso (customer panel 3 mm translucent)", skip=())
view("iso_front_v3.png", False, "v3 front", skip=("customer_panel",))
# fix front view angle
def section(X, fname, xlim, ylim):
    fig, ax = plt.subplots(figsize=(15, 8))
    for n, (wp, col) in parts.items():
        sl = wp.intersect(cq.Workplane("YZ").workplane(offset=X - 0.01).rect(2000, 2000).extrude(0.02))
        try: fl = sl.faces(">X").vals()
        except Exception: fl = []
        for f in fl:
            v, t = f.tessellate(0.05)
            for tri in t:
                P = np.array([(-v[i].y, -v[i].z) for i in tri]); ax.fill(P[:, 0], P[:, 1], color=col, lw=0, alpha=0.95)
    ax.set_aspect("equal"); ax.invert_yaxis(); ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_xlabel("y (front view, mm)"); ax.set_ylabel("Z behind bezel face (mm)")
    ax.set_title(f"Section x = {X}"); fig.savefig(fname, dpi=130, bbox_inches="tight"); plt.close(fig)
section(72.9, "section_key_clamp_v3.png", (-50, 230), (66, -6))
section(72.9, "section_key_detail_v3.png", (-40, 10), (45, -4))
section(230.0, "section_heatpath_v3.png", (-40, 60), (72, -6))
section(128.0, "section_fans_v3.png", (-30, 200), (72, -6))
section(4.215, "section_hv_J28J29_v3.png", (5, 115), (50, -6))
print("ok")
