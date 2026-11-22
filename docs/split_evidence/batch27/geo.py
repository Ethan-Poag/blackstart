import re,sys,math
sys.path.insert(0,'/workspace/review/split/exec')
from sx import block_at
def blocks(s,head):
    out=[];i=0
    while True:
        i=s.find(head,i)
        if i<0: return out
        e=block_at(s,i); out.append((i,e,s[i:e])); i=e
def libsyms(s):
    i=s.find('(lib_symbols'); e=block_at(s,i); L={}
    j=i+1
    while True:
        k=s.find('(symbol "',j)
        if k<0 or k>e: break
        ke=block_at(s,k); name=re.match(r'\(symbol "([^"]+)"',s[k:]).group(1); L[name]=s[k:ke]; j=ke
    return L,(i,e)
def libpins(b):
    out={}
    for m in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)',b):
        pb=b[m.start():block_at(b,m.start())]
        num=re.search(r'\(number "([^"]+)"',pb).group(1)
        un=None
        # unit from enclosing sub-symbol name NAME_u_s
        k=b.rfind('(symbol "',0,m.start()); nm=re.match(r'\(symbol "([^"]+)"',b[k:]).group(1)
        mm=re.search(r'_(\d+)_(\d+)$',nm); un=int(mm.group(1)) if mm else 0
        out.setdefault(num,[]).append((float(m.group(1)),float(m.group(2)),un))
    return out
def instances(s):
    L,(li,le)=libsyms(s); res=[]
    for i,e,b in blocks(s,'(symbol (lib_id'):
        lib=re.match(r'\(symbol \(lib_id "([^"]+)"\) \(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)',b)
        ref=re.search(r'\(property "Reference" "([^"]+)"',b).group(1)
        unit=int(re.search(r'\(unit (\d+)\)',b).group(1))
        mir=re.search(r'\(mirror (\w)\)',b[:300]); mir=mir.group(1) if mir else None
        X,Y,A=float(lib.group(2)),float(lib.group(3)),float(lib.group(4))
        pins={}
        for n,lst in libpins(L[lib.group(1)]).items():
            for px,py,u in lst:
                if u not in (0,unit): continue
                if mir=='y': px=-px
                if mir=='x': py=-py
                a=math.radians(A); rx=px*math.cos(a)-py*math.sin(a); ry=px*math.sin(a)+py*math.cos(a)
                pins[n]=(round(X+rx,2),round(Y-ry,2))
        res.append(dict(ref=ref,lib=lib.group(1),at=(X,Y,A),unit=unit,mir=mir,pins=pins,span=(i,e)))
    return res
def at_point(s,pt,tol=0.02):
    hits=[]
    for kind in ('(wire (pts','(global_label','(label','(hierarchical_label','(junction','(no_connect'):
        for i,e,b in blocks(s,kind):
            nums=[tuple(map(float,m)) for m in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)',b)] if kind.startswith('(wire') else [tuple(map(float,re.search(r'\(at ([-\d.]+) ([-\d.]+)',b).groups()))]
            for q in nums:
                if abs(q[0]-pt[0])<tol and abs(q[1]-pt[1])<tol: hits.append((kind,i,e,b[:160].replace('\n',' ')))
    return hits
if __name__=='__main__':
    s=open(sys.argv[1]).read()
    inst=instances(s)
    for ref in sys.argv[2:]:
        for d in inst:
            if d['ref']==ref:
                print(ref,d['lib'],d['at'],'unit',d['unit'],'mir',d['mir'])
                for n,p in sorted(d['pins'].items()):
                    print('  pin',n,p,[h[0]+' '+h[3][:110] for h in at_point(s,p)])
