# Refdes-independent compare: each component -> (value, footprint, sorted (pin, net-name-leaf)); auto nets -> '~'
import re,sys
from collections import Counter
def sig(f):
    t=open(f).read(); i=t.index('(nets'); comps,nets=t[:i],t[i:]
    meta={}
    for m in re.finditer(r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)\s*\(footprint "([^"]*)"\)',comps): meta[m.group(1)]=(m.group(2),m.group(3))
    pins={}
    for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)(?=\(net \(code|\Z)',nets,re.S):
        n=m.group(1); n='~' if n.startswith(('Net-(','unconnected-(')) else n.split('/')[-1]
        for r,p in re.findall(r'\(ref "([^"]+)"\) \(pin "([^"]+)"',m.group(2)): pins.setdefault(r,[]).append((p,n))
    return Counter((meta.get(r,('?','?')),tuple(sorted(v))) for r,v in pins.items())
a,b=sig(sys.argv[1]),sig(sys.argv[2])
print('components',sum(a.values()),sum(b.values()))
for x in (a-b).elements(): print('-',x)
for x in (b-a).elements(): print('+',x)
