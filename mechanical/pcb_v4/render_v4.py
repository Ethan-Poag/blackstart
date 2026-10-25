#!/usr/bin/env python3
"""Render a v4 board: outline, parts (by sheet colour, B side outline / F side dashed), tracks + vias by layer colour,
rule areas. Usage: render_v4.py board.kicad_pcb out.png [x0 y0 x1 y1] [--title T]"""
import sys, pcbnew, re
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon
TM = pcbnew.ToMM
args = [a for a in sys.argv[1:] if not a.startswith("--")]
title = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--title=")), "")
b = pcbnew.LoadBoard(args[0]); out = args[1]
win = list(map(float, args[2:6])) if len(args) >= 6 else None
LC = {pcbnew.F_Cu: "#d62728", pcbnew.In1_Cu: "#8c564b", pcbnew.In2_Cu: "#2ca02c", pcbnew.In3_Cu: "#9467bd", pcbnew.In4_Cu: "#e377c2", pcbnew.B_Cu: "#1f77b4"}
SC = {"AC metering": "#ff9896", "Power": "#ffbb78", "Raspberry": "#98df8a", "Display": "#c5b0d5", "Comms": "#9edae5",
      "STM32": "#dbdb8d", "Front": "#c7c7c7", "Inputs": "#aec7e8", "Outputs": "#f7b6d2", "E-stop": "#e7969c"}
W = 24 if not win else 16
fig, ax = plt.subplots(figsize=(W, W * 0.75 if not win else W * (win[3] - win[1]) / (win[2] - win[0])), dpi=110)
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
        s, e = d.GetStart(), d.GetEnd(); ax.plot([TM(s.x), TM(e.x)], [TM(s.y), TM(e.y)], "k-", lw=1)
for z in b.Zones():
    o = z.Outline()
    if o.OutlineCount() == 0: continue
    pts = [(TM(o.CVertex(i).x), TM(o.CVertex(i).y)) for i in range(o.COutline(0).PointCount())]
    if z.GetIsRuleArea():
        n = z.GetZoneName()
        col = "#ff0000" if n.startswith("BARRIER") else "#888888"
        ax.add_patch(Polygon(pts, closed=True, fc=col, alpha=0.12 if n.startswith("BARRIER") else 0.05, ec=col, lw=0.4))
for fp in b.GetFootprints():
    bb = fp.GetBoundingBox(False)
    sh = fp.GetSheetname(); col = next((c for k, c in SC.items() if k in sh), "#dddddd")
    fl = fp.IsFlipped()
    ax.add_patch(Rectangle((TM(bb.GetLeft()), TM(bb.GetTop())), TM(bb.GetWidth()), TM(bb.GetHeight()), fc=col if fl else "none",
                           ec="#555555" if fl else "#00aa00", lw=0.3, ls="-" if fl else "--", alpha=0.7))
    for p in fp.Pads():
        ps = p.GetBoundingBox()
        ax.add_patch(Rectangle((TM(ps.GetLeft()), TM(ps.GetTop())), TM(ps.GetWidth()), TM(ps.GetHeight()), fc="#b8860b", ec="none", alpha=0.6))
    w = TM(bb.GetWidth())
    if w > 3 or win:
        c = bb.GetCenter(); ax.text(TM(c.x), TM(c.y), fp.GetReference(), fontsize=3.5 if not win else 5, ha="center", va="center")
order = [pcbnew.In1_Cu, pcbnew.In4_Cu, pcbnew.In3_Cu, pcbnew.In2_Cu, pcbnew.F_Cu, pcbnew.B_Cu]
tr = list(b.GetTracks())
for L in order:
    for t in tr:
        if t.GetClass() == "PCB_TRACK" and t.GetLayer() == L:
            s, e = t.GetStart(), t.GetEnd()
            ax.plot([TM(s.x), TM(e.x)], [TM(s.y), TM(e.y)], "-", color=LC[L], lw=max(0.25, TM(t.GetWidth()) * (3 if win else 1.6)), solid_capstyle="round", alpha=0.85)
for t in tr:
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition(); ax.add_patch(Circle((TM(p.x), TM(p.y)), TM(t.GetWidth(pcbnew.F_Cu)) / 2, fc="#444444", ec="none"))
from matplotlib.lines import Line2D
names = {pcbnew.F_Cu: "F.Cu (L1)", pcbnew.In1_Cu: "In1 GND", pcbnew.In2_Cu: "In2 SIG", pcbnew.In3_Cu: "In3 PWR", pcbnew.In4_Cu: "In4 GND", pcbnew.B_Cu: "B.Cu (L6)"}
ax.legend(handles=[Line2D([0], [0], color=LC[l], lw=2, label=names[l]) for l in order], loc="lower right", fontsize=7)
ax.set_aspect("equal"); ax.invert_yaxis()
if win: ax.set_xlim(win[0], win[2]); ax.set_ylim(win[3], win[1])
else:
    bb = b.GetBoardEdgesBoundingBox(); ax.set_xlim(TM(bb.GetLeft()) - 3, TM(bb.GetRight()) + 3); ax.set_ylim(TM(bb.GetBottom()) + 3, TM(bb.GetTop()) - 3)
ax.set_title(title or args[0], fontsize=9)
plt.tight_layout(); plt.savefig(out); print("wrote", out)
