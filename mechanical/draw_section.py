"""Side section through a TOP-row key centre (plane x = key centre), V2 panel. python3 draw_section.py
Horizontal = Z (mm behind panel face, front at left), vertical = y (front-view y; up = panel top edge)."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import geometry as g
fig, ax = plt.subplots(figsize=(18, 12)); ax.set_aspect("equal")
def R(z0,z1,y0,y1,fc,ec="k",lw=0.6,**k): ax.add_patch(Rectangle((z0,-y1),z1-z0,y1-y0,fc=fc,ec=ec,lw=lw,**k))
def lab(z,y,t,**k): k.setdefault("fontsize",7); ax.text(z,-y,t,**k)
def dim(z0,y0,z1,y1,t,off=(0,0)):
    ax.annotate("",(z0,-y0),(z1,-y1),arrowprops=dict(arrowstyle="<->",lw=0.6,color="#b00"))
    ax.text((z0+z1)/2+off[0],-(y0+y1)/2+off[1],t,fontsize=6.5,color="#b00",ha="center")
cy=g.BTN_Y_TOP; c0=cy-g.CAP_H/2; c1=cy+g.CAP_H/2; s0,s1=g.SLOT_TOP[1],g.SLOT_TOP[3]
AL="#c8c8c8"
# panel field above slot, web+rim, ledge
R(0,g.PANEL_T,g.PANEL[1],s0,AL); lab(0.3,g.PANEL[1]+2,"Al 6061 front panel 4.0")
R(0,g.RIM_DEPTH,s1,-g.WINDOW_GAP,AL)                                   # web + rim wall
R(g.LEDGE_Z,g.RIM_DEPTH,-g.WINDOW_GAP,g.LEDGE_W,AL)                   # ledge
lab(g.RIM_DEPTH+0.5,1.5,"ledge: 4.0 overlap on TFT rear,\n3.0 thick, face 9.5 behind panel face")
# display
R(0,1.8,0,30,"#7fb3d5"); R(1.8,8.51,0,30,"#555"); lab(2.2,24,"TFT (5.56)\n+ CTP",color="w")
lab(-11,20,"cover glass 1.8\n(optically bonded)\nFLUSH with panel face\n0 / -0.15 mm")
R(8.51,g.LEDGE_Z,0.3,g.LEDGE_W,"#f4d03f",lw=0.3); lab(8.4,6.5,"structural silicone bond line 1.0 (0.5-1.5)\nDOWSIL 7091 / 3M VHB 4611 tabs as spacers",color="#7d6608")
R(0,2.5,-g.WINDOW_GAP,0,"#111",lw=0.2); lab(-15,-1.2,"0.5 joint, black neutral-cure\nsilicone bead, tooled flush")
R(8.51,12.68,0.0,30,"none",ec="#555",ls=":"); lab(9.5,27,"module max depth 12.68\n(source-PCB band at bottom)")
# key
R(-g.CAP_PROUD,g.PANEL_T,c0,c1,"#d6eaf8",ec="#2e86c1"); R(g.PANEL_T,5.0,c0-1.5,c1,"#d6eaf8",ec="#2e86c1")
lab(-14,cy-3.5,f"cap {g.CAP_W:.2f} x {g.CAP_H} (clear PC,\ndiffused/printed face),\n0.5 proud, flange 1.0")
R(5.0,6.0,s0-5,s1,"#f5b7b1",ec="#922b21"); lab(19,-12.2,"<- translucent silicone sheet 1.0 (50-60A), one per row,\n   convolutions between caps, bead clamped by carrier",color="#922b21")
R(4.0,5.0,s0-5,s0-2,"#f5b7b1",ec="#922b21")                           # clamp bead
R(6.0,8.0,c0+0.7,c1-0.7,"#aed6f1",ec="#2e86c1"); lab(19,-5.0,"<- "+"actuator bar 2.0 (clear PC)\n2x M2 through sheet bosses\nto cap = rigid sandwich",color="#1b4f72")
R(8.0,10.4,cy-1.8,cy+1.8,"#aed6f1",ec="#2e86c1"); lab(19,-8.0,"<- centre light pipe Ø3.6 onto switch plunger (0.1 gap)",color="#1b4f72")
R(6.5,10.5,s0-4.5,c0+0.3,"#a9cce3",ec="k",hatch="//",lw=0.4); R(9.5,10.5,c0+0.3,c1-0.5,"#a9cce3",ec="k",hatch="//",lw=0.4)
lab(19,-16.2,"<- "+"carrier (PC-GF30 or Al): guide bushings Ø3.15 for stems Ø3.0 at x±17,\nstabiliser wire clips, hard stop. Screwed to panel studs, clamps sheet")
# switch + PCB
z=g.Z_BOARD_FRONT; R(z-5.5,z-3.6,cy-1.9,cy+1.9,"#fdebd0"); R(z-3.6,z,cy-3.6,cy+3.6,"#f0b27a")
lab(19,-10.0,"<- CTS 228EMV RGB, 5.5 h, travel 0.7±0.2, 200±50 gf")
R(z,z+1.6,g.BOARD[1],30,"#27ae60"); lab(z+1.9,25,"PCB 1.6\n(F side at Z=16.0)",color="#145a32")
R(z+1.6,z+14,-2,10,"none",ec="#888",ls=":"); lab(z+2,8,"B-side parts")
# housing
R(z+1.6+45,z+1.6+48,g.PANEL[1],30,"#bbb"); R(4,z+1.6+48,g.PANEL[1],g.PANEL[1]+3,"#bbb")
R(4,6,g.PANEL[1]+0.5,g.PANEL[1]+3,"#222"); lab(19,g.PANEL[1]+2.6,"<- EPDM/silicone housing gasket (black)",fontsize=6)
lab(19,g.PANEL[1]+5.4,"rear housing (Al/ powder-coated), M4 studs\non panel rear; panel face has no holes")

# dims
yd=g.PANEL[1]-3
dim(0,yd,z,yd,f"panel face -> PCB F side {z}",(0,0.5))
dim(0,yd-4,g.LEDGE_Z,yd-4,"9.5 ledge",(0,0.5))
dim(0,yd-8,z-5.5,yd-8,"10.5 = switch top",(0,0.5))
dim(-g.CAP_PROUD-2,c0,-g.CAP_PROUD-2,c1,"",); lab(-g.CAP_PROUD-7,cy,f"{g.CAP_H}")
dim(-1.5,c1,-1.5,0,"",); lab(-4,(c1)/2+0.3,f"{-c1:.2f}")
ax.plot([-20,45],[0,0],"c--",lw=0.3); lab(30,-0.6,"y=0 glass top edge",color="c")
fig.text(0.1,0.04,"Rest: bar-to-carrier stop gap 1.2; stem-to-plunger 0.1; switch makes at 0.8±0.2 cap travel; hard stop at 1.2 (switch bottoms at 0.9 max -> protected).\n"
 "Guide stems (not in this plane, at x = key ±17): Ø3.0 PC in Ø3.15 PTFE-filled POM bushings, 6.0 engagement; stainless wire stabiliser Ø1.0 couples both stems.",fontsize=7)
ax.set_xlim(-20,70); ax.set_ylim(-32,-g.PANEL[1]+14); ax.invert_yaxis() if False else None
ax.set_title("PANEL V2 section through top-row key centre (dimensions mm). Bottom row is the mirror image.",fontsize=10)
ax.set_xlabel("Z behind panel face (mm)"); ax.set_yticks([]); ax.grid(alpha=0.15)
fig.savefig("section_view.png",dpi=150,bbox_inches="tight"); fig.savefig("section_view.svg",bbox_inches="tight")
