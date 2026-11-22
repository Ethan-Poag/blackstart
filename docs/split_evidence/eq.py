import re,json,sys
sys.path.insert(0,'/workspace/review/split/work')
def load(path):
    s=open(path).read()
    tok=re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+',s)
    def parse(i):
        out=[]
        while i<len(tok):
            t=tok[i]
            if t=='(':
                sub,i=parse(i+1); out.append(sub)
            elif t==')': return out,i+1
            else: out.append(t.strip('"') if t.startswith('"') else t); i+=1
        return out,i
    tree=parse(0)[0][0]
    f=lambda n,k:[x for x in n if isinstance(x,list) and x and x[0]==k]
    comps={}
    for c in f(f(tree,'components')[0],'comp'):
        d={x[0]:x[1] for x in c if isinstance(x,list) and len(x)>1 and isinstance(x[1],str)}
        comps[d['ref']]=d
    nets={}
    for n in f(f(tree,'nets')[0],'net'):
        nets[f(n,'name')[0][1]]=[(x[1][1],x[2][1]) for x in f(n,'node')]
    return comps,nets
SKIP=set(map(int,sys.argv[1:]))
oc,on=load('/workspace/review/split/work/genctl.net')
mc,mn=load('nets/genctl.net'); dc,dn=load('nets/genctl_meter.net')
print('parts orig',len(oc),'main',len(mc),'daughter',len(dc),'overlap refs',sorted(set(mc)&set(dc)))
daughter_refs=set(open('/workspace/review/split/work/daughter_refs.txt').read().split())
print('daughter refs kept', daughter_refs<=set(dc), 'extra in daughter',sorted(set(dc)-daughter_refs),'extra in main',sorted(set(mc)-(set(oc)-daughter_refs)),'missing from main',sorted((set(oc)-daughter_refs)-set(mc)))
# values/footprints unchanged for all original parts
diff=[r for r in oc if (r in mc or r in dc) and ((mc.get(r) or dc.get(r)).get('value'),(mc.get(r) or dc.get(r)).get('footprint'))!=(oc[r].get('value'),oc[r].get('footprint'))]
print('value/footprint changes',diff)
# union-find
par={}
def F(x):
    par.setdefault(x,x)
    while par[x]!=x: par[x]=par[par[x]]; x=par[x]
    return x
def Un(a,b): par[F(a)]=F(b)
for nets in (mn,dn):
    for n,nodes in nets.items():
        for a in nodes[1:]: Un(nodes[0],a)
        for a in nodes: F(a)
for k in [k for k in range(1,17) if k not in SKIP]: Un(('J31',str(k)),('J32',str(k)))  # harness, straight
# compare partitions over original nodes
orig_nodes={x for nodes in on.values() for x in nodes}
new_nodes=set(par)
print('orig nodes',len(orig_nodes),'missing in new',len(orig_nodes-new_nodes))
bad=[]
for n,nodes in on.items():
    roots={F(x) for x in nodes if x in par}
    if len(roots)!=1: bad.append(('split',n,len(roots)))
# merged: two original nets now in same group
grp={}
for n,nodes in on.items():
    r=F(nodes[0]); grp.setdefault(r,[]).append(n)
merged=[v for v in grp.values() if len(v)>1]
print('orig nets split',bad[:10],'merged groups',merged)
# extra nodes added to each original net
new_parts={r for r in set(mc)|set(dc) if r not in oc}
added={}
for x in new_nodes-orig_nodes:
    r=F(x); names=grp.get(r,['<new net>'])
    added.setdefault(tuple(names),[]).append(f'{x[0]}.{x[1]}')
for k,v in sorted(added.items()): print(k,sorted(v))
