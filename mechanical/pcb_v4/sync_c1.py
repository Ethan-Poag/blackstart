import pcbnew,re,sys
src,dst=sys.argv[1],sys.argv[2]
b=pcbnew.LoadBoard(src)
t=open('/tmp/nl_new.net').read()
comps={}
for m in re.finditer(r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)\s*\(footprint "([^"]*)"\)',t): comps[m.group(1)]=(m.group(2),m.group(3))
pinnet={}
for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)(?=\(net \(code|\Z)',t,re.S):
    for r,p in re.findall(r'\(ref "([^"]+)"\) \(pin "([^"]+)"',m.group(2)): pinnet[(r,p)]=m.group(1)
nets=b.GetNetsByName()
def net(n):
    if nets.has_key(n): return nets[n]
    ni=pcbnew.NETINFO_ITEM(b,n); b.Add(ni); globals()['nets']=b.GetNetsByName(); return ni
fps={f.GetReference():f for f in b.GetFootprints()}
lib='/usr/share/kicad/footprints'
added=[]
for r,(v,fp) in comps.items():
    if r in fps or r.startswith('#'): continue
    l,n=fp.split(':')
    f=pcbnew.FootprintLoad(lib+'/'+l+'.pretty',n)
    if f is None: print('NOFP',r,fp); continue
    f.SetReference(r); f.SetValue(v); b.Add(f); fps[r]=f; added.append(r)
    f.SetPosition(pcbnew.VECTOR2I_MM(250,10))  # parking spot, placed later
changed=[]
for r,f in fps.items():
    for pad in f.Pads():
        k=(r,pad.GetNumber())
        if k not in pinnet: continue
        want=pinnet[k]
        if pad.GetNetname()!=want:
            changed.append((r,pad.GetNumber(),pad.GetNetname(),want)); pad.SetNet(net(want))
extra=[r for r in fps if r not in comps and not r.startswith(('H','#','kibuzzard','G'))]
print('added',added); print('extra on board',extra[:20])
for c in changed: print('pad',*c)
rm=[t for t in b.GetTracks() if t.GetNetname().endswith('DSI83_REFCLK_BUF')]
for t in rm: b.Remove(t)
for r in extra: b.Remove(fps[r])
print('removed fps',extra,'buf copper',len(rm))
b.Save(dst)
