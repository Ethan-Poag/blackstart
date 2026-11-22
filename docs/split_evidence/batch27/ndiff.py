import sys; sys.path.insert(0,'/workspace/review/fix27'); import nl
A,NA=nl.load(sys.argv[1]); B,NB=nl.load(sys.argv[2])
print('parts',len(A),'->',len(B))
for r in sorted(set(A)-set(B)): print('REMOVED',r)
for r in sorted(set(B)-set(A)): print('ADDED',r,B[r]['value'],B[r]['fp'],B[r]['props'].get('LCSC'))
for r in sorted(set(A)&set(B)):
    a,b=A[r],B[r]
    for k in ('value','fp'):
        if a[k]!=b[k]: print('CHG',r,k,a[k],'->',b[k])
    for k in sorted(set(a['props'])|set(b['props'])):
        if a['props'].get(k)!=b['props'].get(k): print('PROP',r,k,repr(a['props'].get(k))[:80],'->',repr(b['props'].get(k))[:80])
# connectivity: compare per-pin net membership via net "signature" (sorted nodes)
def pin2net(N): return {n:name for name,nodes in N.items() for n in nodes}
pa,pb=pin2net(NA),pin2net(NB)
# group equivalence: for each net in A, nodes set; in B same
sa={name:frozenset(v) for name,v in NA.items()}; sb={name:frozenset(v) for name,v in NB.items()}
setsA=set(sa.values()); setsB=set(sb.values())
for name,v in sorted(sa.items()):
    if v not in setsB:
        # find B nets containing these nodes
        bn=sorted({pb.get(n,'?') for n in v})
        print('NET A',nl.sh(name),'not identical in B -> B nets',[nl.sh(x) for x in bn])
for name,v in sorted(sb.items()):
    if v not in setsA:
        an=sorted({pa.get(n,'<new>') for n in v})
        extra=sorted(n for n in v if n not in pa or pa[n]!=None and n not in sa.get(pa.get(n),()))
        print('NET B',nl.sh(name),len(v),'nodes from A nets',[nl.sh(x) for x in an],'| B nodes:',sorted(v) if len(v)<8 else len(v))
