"""Batch 32: drafting-only tidy of the Batch 31 inputs-sheet gating block (pass-6 NOTE 8) + sheet-text WD_OK timing.
Moves Reference/Value text, hides overlapping Value text. No connectivity change (netlist diff must be empty)."""
import re,sys
sys.path.insert(0,'/workspace/review/fix29'); sys.path.insert(0,'/workspace/review/split/exec')
from geo import blocks
P='inputs.kicad_sch'; s=open(P).read()
def setprop(b,key,x,y,just=None,hide=False):
    m=re.search(r'\(property "%s" "([^"]*)" \(at [-\d.]+ [-\d.]+ 0\) \(effects \(font \(size 1\.27 1\.27\)\)( hide)?\)\)'%key,b); assert m,(key,b[:120])
    eff='(effects (font (size 1.27 1.27))'+(f' (justify {just})' if just else '')+(' hide' if hide else '')+')'
    return b[:m.start()]+f'(property "{key}" "{m.group(1)}" (at {x:.2f} {y:.2f} 0) {eff})'+b[m.end():]
out=[]; rn={}
for i,e,b in blocks(s,'(symbol (lib_id'):
    ref=re.search(r'\(property "Reference" "([^"]+)"',b).group(1)
    X,Y=map(float,re.match(r'\(symbol \(lib_id "[^"]+"\) \(at ([-\d.]+) ([-\d.]+)',b).groups()); unit=int(re.search(r'\(unit (\d+)\)',b).group(1))
    nb=b
    if ref in ('C320','C321','C322'):
        nb=setprop(nb,'Reference',X+3.81,Y-1.27,'left'); nb=setprop(nb,'Value',X+3.81,Y+1.27,'left')
    elif ref in ('RN1','RN2'):
        nb=setprop(nb,'Reference',X+5.08,Y-1.27,'left'); nb=setprop(nb,'Value',X+5.08,Y+1.27,'left'); rn[ref]=(X,Y)
    elif ref in ('U91','U92') and unit==5:
        nb=setprop(nb,'Value',X,Y+6.35,None,True)
    elif ref=='U93':
        nb=setprop(nb,'Reference',X+1.27,Y-7.62,'left'); nb=setprop(nb,'Value',X+1.27,Y+7.62,'left')
    if nb!=b: out.append((i,e,nb))
for i,e,b in blocks(s,'(symbol (lib_id "power:GND"'):
    ref=re.search(r'\(property "Reference" "(#PWR\d+)"',b).group(1)
    if not 3108<=int(ref[4:])<=3139: continue
    X,Y=map(float,re.match(r'\(symbol \(lib_id "[^"]+"\) \(at ([-\d.]+) ([-\d.]+)',b).groups())
    if any(abs(X-(rx-1.27))<=5 and abs(Y-ry)<=12 for rx,ry in rn.values()):
        m=re.search(r'\(property "Value" "GND" \(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\) \(effects \(font \(size 1\.27 1\.27\)\)\)\)',b); assert m,b[:200]
        out.append((i,e,b[:m.start()]+f'(property "Value" "GND" (at {m.group(1)} {m.group(2)} {m.group(3)}) (effects (font (size 1.27 1.27)) hide))'+b[m.end():]))
for i,e,nb in sorted(out,reverse=True): s=s[:i]+nb+s[e:]
a='first 0.70-1.06 s after\\npower-on.'
assert s.count(a)==1; s=s.replace(a,'first 0.70-1.06 s (worst case 0.40-1.35 s)\\nafter power-on.')
open(P,'w').write(s); print('edited',len(out))
