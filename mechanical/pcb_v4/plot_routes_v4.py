import pcbnew, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import sys
b=pcbnew.LoadBoard(sys.argv[1])
mm=lambda v:v/1e6
cols={pcbnew.F_Cu:"#d33",pcbnew.B_Cu:"#36c",pcbnew.In1_Cu:"#2a2",pcbnew.In2_Cu:"#c80",pcbnew.In3_Cu:"#a3a",pcbnew.In4_Cu:"#0aa"}
fig,ax=plt.subplots(figsize=(20,15),dpi=110); ax.set_facecolor("#111"); fig.patch.set_facecolor("#111")
segs={}; vias=[]
n=0
for t in b.GetTracks():
    if t.GetClass()=="PCB_VIA":
        p=t.GetPosition(); vias.append((mm(p.x),mm(p.y)))
    else:
        s,e=t.GetStart(),t.GetEnd(); segs.setdefault((t.GetLayer(),t.GetNetClassName()=="Default"),[]).append(((mm(s.x),mm(s.y)),(mm(e.x),mm(e.y)))); n+=1
for (l,d),sg in segs.items():
    ax.add_collection(LineCollection(sg,colors=cols.get(l,"#fff"),linewidths=0.7 if d else 1.4,alpha=0.9))
ax.scatter([v[0] for v in vias],[v[1] for v in vias],s=1.5,c="#ccc",linewidths=0)
for fp in b.GetFootprints():
    bb=fp.GetBoundingBox(False,False)
    ax.add_patch(plt.Rectangle((mm(bb.GetX()),mm(bb.GetY())),mm(bb.GetWidth()),mm(bb.GetHeight()),fill=False,ec="#777",lw=0.3))
eb=b.GetBoardEdgesBoundingBox()
ax.set_xlim(mm(eb.GetX())-3,mm(eb.GetRight())+3); ax.set_ylim(mm(eb.GetBottom())+3,mm(eb.GetY())-3); ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Project Blackstart pcb_v4 %s (tracks only; planes not shown)  red F.Cu blue B.Cu green In1 orange In2 purple In3 teal In4"%sys.argv[1].split("/")[-1],color="w")
fig.savefig(sys.argv[2],bbox_inches="tight",facecolor="#111"); print(n,len(vias))
