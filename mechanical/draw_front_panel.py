"""Front view of the V2 panel (flush glued display, wide caps). python3 draw_front_panel.py"""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle
import geometry as g
W = g.PANEL[2]-g.PANEL[0]; H = g.PANEL[3]-g.PANEL[1]
fig = plt.figure(figsize=((W+60)/25.4, (H+50)/25.4))
ax = fig.add_axes([0,0,1,1]); ax.set_xlim(g.PANEL[0]-30, g.PANEL[2]+30); ax.set_ylim(g.PANEL[3]+38, g.PANEL[1]-12)
ax.set_aspect("equal"); ax.axis("off")
def rect(x0,y0,x1,y1,**k): ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,**k))
ax.add_patch(FancyBboxPatch((g.PANEL[0],g.PANEL[1]),W,H,boxstyle=f"round,pad=0,rounding_size={g.PANEL_CORNER_R}",fc="#d9d9d9",ec="k",lw=1.2))
rect(*g.BOARD, fill=False, ec="green", ls="--", lw=1)
rect(*g.WINDOW, fc="#111", ec="k", lw=0.5)                       # 0.5 sealant joint (black silicone)
rect(0,0,g.GLASS_W,g.GLASS_H, fc="#202020", ec="#555", lw=0.4)
rect(g.VA_LEFT,g.VA_TOP,g.VA_LEFT+g.VA_W,g.VA_TOP+g.VA_H, fc="#2f4f6f", ec="none")
rect(g.AA_LEFT,g.AA_TOP,g.AA_LEFT+g.AA_W,g.AA_TOP+g.AA_H, fill=False, ec="cyan", lw=0.6)
for s in (g.SLOT_TOP, g.SLOT_BOT): rect(*s, fc="#444", ec="k", lw=0.5)
for ref,x0,y0,x1,y1 in g.caps():
    rect(x0,y0,x1,y1, fc="#e8f2ff", ec="#3a6ea5", lw=0.6)
    cx=(x0+x1)/2; cy=(y0+y1)/2
    ax.add_patch(Circle((cx,cy),1.9,fill=False,ec="#3a6ea5",lw=0.4,ls=":"))        # switch plunger / light pipe
    for dx in (-g.GUIDE_DX, g.GUIDE_DX): ax.add_patch(Circle((cx+dx,cy),g.GUIDE_D/2,fill=False,ec="#888",lw=0.3,ls=":"))
    ax.text(cx,cy+0.4,ref,ha="center",va="center",fontsize=5)
    ax.text(cx,y0-1.2 if cy<0 else y1+2.6,f"x {cx:.2f}  y {cy:.2f}",ha="center",fontsize=3.5)
for x in (g.AA_LEFT, g.AA_LEFT+g.AA_W): ax.plot([x,x],[g.SLOT_TOP[1]-3,g.SLOT_BOT[3]+3],color="cyan",lw=0.4,ls="--")
for ref,x,y in g.MOUNT_HOLES:
    ax.add_patch(Circle((x,y),1.6,fc="none",ec="green",lw=0.5)); ax.text(x,y+4,ref,ha="center",fontsize=3.5,color="green")
for x,y in g.PANEL_SCREWS: ax.add_patch(Circle((x,y),2.0,fc="none",ec="k",lw=0.4,ls="--"))
ax.text(g.GLASS_W/2,g.GLASS_H/2,
 f"Display glass {g.GLASS_W} x {g.GLASS_H} FLUSH with panel face, glued to rear ledge {g.LEDGE_Z} deep\n"
 f"window {g.WINDOW[2]-g.WINDOW[0]:.2f} x {g.WINDOW[3]-g.WINDOW[1]:.2f} (0.5 joint each side, black silicone)\n"
 f"Active area {g.AA_W} x {g.AA_H} (cyan). Key rows span exactly the active width (dashed cyan lines)\n"
 f"12 caps {g.CAP_W:.2f} x {g.CAP_H} mm, pitch {g.BTN_PITCH:.2f}, gap {g.CAP_GAP}; key centres {g.BTN_Y_TOP:.2f} / {g.BTN_Y_BOT:.2f}",
 color="white",ha="center",va="center",fontsize=7)
y=g.PANEL[3]+8
ax.text(g.PANEL[0],y,f"PANEL V2 outline {W:.2f} x {H:.2f} mm, R{g.PANEL_CORNER_R}  |  PCB (green dashed) {g.BOARD_W} x {g.BOARD_H} mm  |  origin (0,0)=glass top-left, front view, mm, y down",fontsize=6)
ax.text(g.PANEL[0],y+6,"blue=caps (clear PC, diffused face); dotted circle=switch plunger/light pipe, small dotted=guide stems +-17; dashed black=M4 blind studs (rear); green=PCB holes. See section_view.png, PANEL_V2.md",fontsize=5)
ax.plot([g.PANEL[0],g.PANEL[0]+100],[y+14,y+14],"k",lw=1.5); ax.text(g.PANEL[0]+50,y+19,"100 mm (print at 100% = 1:1)",ha="center",fontsize=6)
fig.savefig("front_panel.svg"); fig.savefig("front_panel.png",dpi=150)
