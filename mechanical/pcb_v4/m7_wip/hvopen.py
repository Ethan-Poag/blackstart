import sys;sys.path.insert(0,'/workspace/genctl/kicad/genctl/mechanical/pcb_v4')
import pcbnew,uf,collections
b=pcbnew.LoadBoard(sys.argv[1]);per,items,fd=uf.analyze(b);tot=0
for k in per:
  n=b.FindNet(k)
  if not n.GetNetClassName().startswith('HV'): continue
  c=n.GetNetCode();g=collections.defaultdict(list)
  for i,it in enumerate(items):
    if it[0]=='pad' and it[1]==c: g[fd(i)].append(it[2])
  tot+=per[k];print(k.split('/')[-1],list(g.values()))
print('HV opens',tot)
