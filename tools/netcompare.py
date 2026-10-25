import re,sys
def canon(f):
    t=open(f).read()
    i=t.index('(nets'); t=t[i:]
    out=set()
    for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)(?=\(net \(code|\Z)',t,re.S):
        nodes=tuple(sorted(re.findall(r'\(ref "([^"]+)"\) \(pin "([^"]+)"',m.group(2))))
        name=m.group(1)
        if name.startswith('Net-(') or name.startswith('unconnected-('): name='~'
        out.add((name,nodes))
    return out
a,b=canon(sys.argv[1]),canon(sys.argv[2])
print('nets',len(a),len(b),'only_base',len(a-b),'only_new',len(b-a))
for x in list(a-b)[:5]: print('-',x)
for x in list(b-a)[:5]: print('+',x)
A={n for _,n in a}; B={n for _,n in b}
print('connectivity: only_base',len(A-B),'only_new',len(B-A))
na={n:x for x,n in a}; nb={n:x for x,n in b}
bad=[(na[n],nb[n].split('/')[-1]) for n in A&B if na[n]!='~' and na[n].split('/')[-1]!=nb[n].split('/')[-1]]
print('named nets renamed:',len(bad),bad[:5]); print('auto->named:',sum(1 for n in A&B if na[n]=='~' and nb[n]!='~'))
