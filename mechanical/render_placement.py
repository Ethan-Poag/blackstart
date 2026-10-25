#!/usr/bin/env python3
"""Top-view (front view, F side toward viewer; B-side parts drawn as seen through the board) placement PNG.
python3 render_placement.py out/genctl_placed_v3.kicad_pcb out/placement_v3.png"""
import sys, re, pcbnew, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon
import geometry as g, place as P

src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
T = pcbnew.ToMM
COL = {"HV_METER": "#e53935", "CT_AT_BARRIER": "#b71c1c", "OUTPUTS": "#fb8c00", "CM5": "#8e24aa", "FRONT": "#43a047",
       "MCU": "#1e88e5", "COMMS": "#00acc1", "DISPLAY": "#d81b60", "SPILL": "#9e9e9e", "INPUTS": "#fdd835",
       "POWER": "#6d4c41", "ISO_LV": "#3949ab"}
SHEET_COL = {"AC metering": "#e53935", "Power:": "#6d4c41", "Raspberry Pi CM5": "#8e24aa", "Display:": "#d81b60",
             "Comms:": "#00acc1", "STM32": "#1e88e5", "Front panel": "#43a047", "Inputs:": "#fdd835",
             "Outputs:": "#fb8c00", "E-stop": "#ff7043"}
fig, ax = plt.subplots(figsize=(20, 15.5), dpi=110)
x0, y0, x1, y1 = g.BOARD
ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=2", fc="#0b3d20", ec="k", lw=2))
sx0, sy0 = x0 - g.SHELL_CLR, y0 - g.SHELL_CLR
ax.add_patch(Rectangle((sx0, sy0), x1 - x0 + 2 * g.SHELL_CLR, y1 - y0 + 2 * g.SHELL_CLR, fill=False, ec="#555", ls="--", lw=1))
for name, bb, side, _ in P.ZONES[:-1]:
    ax.add_patch(Rectangle(bb[:2], bb[2] - bb[0], bb[3] - bb[1], fill=False, ec=COL.get(name, "w"), lw=1.2, ls=":"))
    ax.text(bb[0] + 0.8, bb[1] + 2.5, name, color=COL.get(name, "w"), fontsize=8, weight="bold")
# HV box + barrier
hv = P.HV
ax.add_patch(Rectangle(hv[:2], hv[2] - hv[0], hv[3] - hv[1], fc="#e53935", alpha=0.10, ec="#e53935", lw=2))
for n, bb in P.barrier_areas():
    ax.add_patch(Rectangle(bb[:2], bb[2] - bb[0], bb[3] - bb[1], fc="white", alpha=0.35, hatch="////", ec="#ffeb3b", lw=1))
ax.text(hv[0] + 2, hv[1] + 6, "600 V METERING\n(hot zone)", color="#ff8a80", fontsize=11, weight="bold")
ax.text(P.BAR_X[0] + 1, 140, "13 mm\nbarrier", color="#ffeb3b", fontsize=8, rotation=90)
# footprints
for fp in b.GetFootprints():
    bb = fp.GetBoundingBox(False)
    fx0, fy0, fw, fh = T(bb.GetLeft()), T(bb.GetTop()), T(bb.GetWidth()), T(bb.GetHeight())
    sh = fp.GetSheetname(); ref = fp.GetReference()
    c = next((v for k, v in SHEET_COL.items() if k in sh), "#bbbbbb")
    if ref.startswith("SW"): c = "#ffffff"
    if ref.startswith("H"): continue
    ax.add_patch(Rectangle((fx0, fy0), fw, fh, fc=c, alpha=0.55 if not fp.IsFlipped() else 0.75, ec="k", lw=0.2))
    if fw * fh > 120 or ref.startswith(("J", "SW", "U9", "U10", "T", "U69", "U70", "U2", "U7", "U21", "U71", "U72")):
        ax.text(fx0 + fw / 2, fy0 + fh / 2, ref, fontsize=6 if fw * fh < 300 else 8, ha="center", va="center", color="k")
# slots (Edge.Cuts inside the outline)
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
        s, e = d.GetStart(), d.GetEnd()
        if x0 + 1 < T(s.x) < x1 - 1 and y0 + 1 < T(s.y) < y1 - 1:
            ax.plot([T(s.x), T(e.x)], [T(s.y), T(e.y)], color="cyan", lw=1.5)
for fp in b.GetFootprints():
    for it in fp.GraphicalItems():
        if it.GetLayer() == pcbnew.Edge_Cuts and it.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            s, e = it.GetStart(), it.GetEnd(); ax.plot([T(s.x), T(e.x)], [T(s.y), T(e.y)], color="cyan", lw=1.5)
# switch keep-outs, caps
for ref, x, y in g.buttons():
    ax.add_patch(Rectangle((x - g.SW_KO_W / 2, y - g.SW_KO_H / 2), g.SW_KO_W, g.SW_KO_H, fill=False, ec="w", lw=1, ls="--"))
    ax.add_patch(Rectangle((x - g.CAP_W / 2, y - g.CAP_H / 2), g.CAP_W, g.CAP_H, fill=False, ec="#90caf9", lw=0.8))
# holes, posts, clamps
for ref, x, y in g.MOUNT_HOLES:
    if ref == "H4":
        ax.add_patch(Circle((x, y), g.PE_HOLE_D / 2, fc="k", ec="#76ff03", lw=2)); ax.text(x - 9, y - 6, "H4 PE boss D9.5", color="#76ff03", fontsize=8)
    else:
        ax.add_patch(Circle((x, y), g.M4_PAD_D / 2, fc="#ffd54f", ec="k")); ax.add_patch(Circle((x, y), g.M4_HOLE_D / 2, fc="k"))
        ax.text(x + 5, y + 1, ref + " M4", color="#ffd54f", fontsize=8)
for x, y in g.SHELL_POSTS:
    ax.add_patch(Circle((x, y), g.SHELL_POST_KO / 2, fc="none", ec="#ff4081", lw=1.5, hatch="xx")); ax.text(x + 5.5, y, "post", color="#ff4081", fontsize=7)
for bb in g.clamp_marks():
    ax.add_patch(Rectangle(bb[:2], bb[2] - bb[0], bb[3] - bb[1], fc="#9e9e9e", alpha=0.6, ec="w", lw=0.5))
# CM5 + strap
c = P.CM5
ax.add_patch(Rectangle(c[:2], c[2] - c[0], c[3] - c[1], fc="#8e24aa", alpha=0.35, ec="#e1bee7", lw=2))
ax.text((c[0] + c[2]) / 2, (c[1] + c[3]) / 2, "CM5 55x40 + heatsink\n(B side)", ha="center", va="center", color="w", fontsize=10, weight="bold")
s = P.STRAP_KO
ax.add_patch(Rectangle(s[:2], s[2] - s[0], s[3] - s[1], fc="#b0bec5", alpha=0.5, ec="#eceff1", lw=1.5, hatch=".."))
ax.annotate("", xy=P.H2, xytext=(c[2] - 6, c[1] + 6), arrowprops=dict(arrowstyle="-|>", color="#eceff1", lw=3))
ax.text(s[0] + 1, s[3] + 3.5, "Al/Cu heat strap\nto H2 bezel boss", color="#eceff1", fontsize=8)
ax.text((x0 + x1) / 2, y1 + 9, "PROJECT BLACKSTART  genctl  placement v3 (enclosure rev C)  284 x 210 mm  front view, y down; "
        "colour = schematic sheet; dotted = zones; hatched yellow = 13 mm barrier; cyan = slots",
        ha="center", fontsize=10)
ax.set_xlim(x0 - 8, x1 + 8); ax.set_ylim(y1 + 13, y0 - 8); ax.set_aspect("equal"); ax.axis("off")
plt.tight_layout(); plt.savefig(dst, facecolor="white"); print("wrote", dst)
