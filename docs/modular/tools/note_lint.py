#!/usr/bin/env python3
"""Pass 4 m3: Note-field lint across all 7 KiCad projects (genctl, genctl_meter, cards engine/di8/ai4/hso5/brk4).
Run from the repo root. Exits 1 on any finding.
Checks every placed symbol that has a `Note`:
  R1 provenance   - a carried part's Note must equal its baseline Note with only reference designators translated;
                    any other Note must be text a generator writes (literal in cards/tools/*.py).
  R2 ref tokens   - every reference designator named in a Note exists in THAT project, unless written "baseline Rxx".
  R3 DNP          - a Note that says DNP must sit on a part that is DNP, and a DNP part must not be called fitted.
  R4 diode pins   - a Note of the form "A = x, K = y" must match the nets on the diode's A/K pins.
  R5 stale words  - "symbol kept" (pre-Pass 3 N13 symbol swap) and similar known-stale phrases must not appear.
Baseline = git tag baseline-2026-11-23-locked (read via git archive into a temp dir; the tag is never modified)."""
import os,re,subprocess,sys,tempfile,glob
ROOT=os.getcwd()
TOK=re.compile(r'(?<![\w\-/.])((?:TP|JP|[RCDQUJLYF])\d{1,3})(?![\w\-])')
STALE=['symbol kept']
EDITS={'genctl_meter:C301':'Pass 4 m3 hand edit: baseline said "C297 exists", but C297 is not in the meter project'}
HIST=('baseline ','was ','spec ref ','spec name ')   # deliberately historical designators
def parse(path):
    tok=re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+',open(path).read()); st=[[]]
    for t in tok:
        if t=='(':st.append([])
        elif t==')':x=st.pop();st[-1].append(x)
        else: st[-1].append(t[1:-1].replace('\\"','"').replace('\\\\','\\') if t.startswith('"') else t)
    return st[0][0]
def get(l,k):
    for x in l:
        if isinstance(x,list) and x and x[0]==k: return x
def load(net):
    t=parse(net); comps={}; pins={}
    for c in get(t,'components')[1:]:
        props={}; dnp=False
        for p in c:
            if isinstance(p,list) and p[0]=='property':
                n=get(p,'name')[1]; v=get(p,'value')
                if n=='dnp': dnp=True
                elif v: props[n]=v[1]
        lib=get(c,'libsource')
        comps[get(c,'ref')[1]]=dict(val=get(c,'value')[1],props=props,dnp=dnp,lib=get(lib,'lib')[1]+':'+get(lib,'part')[1])
    for n in get(t,'nets')[1:]:
        for x in n:
            if isinstance(x,list) and x[0]=='node':
                pf=get(x,'pinfunction'); pins[(get(x,'ref')[1],get(x,'pin')[1])]=(get(n,'name')[1],pf[1] if pf else '')
    return comps,pins
def netlist(sch,out):
    subprocess.run(['kicad-cli','sch','export','netlist','-o',out,sch],check=True,capture_output=True); return load(out)
N13=[(r'symbol cards:\S+ \(Pass 3 N13\)','symbol kept'),(r'Symbol cards:74LVC1G74 \(Pass 3 N13\)','Stock symbol 74AUP1G74 used (no 74LVC1G74 in KiCad 9 libs)')]
def norm(s):
    for a,b in N13: s=re.sub(a,b,s)
    return re.sub(r'\s+',' ',TOK.sub('#',s.replace('baseline ',''))).strip()
def main():
    tmp=tempfile.mkdtemp(prefix='notelint_')
    base=os.path.join(tmp,'base'); os.mkdir(base)
    subprocess.run(f'git archive baseline-2026-11-23-locked | tar -x -C {base}',shell=True,check=True)
    B={}
    for s in ('genctl','genctl_meter'):
        c,_=netlist(os.path.join(base,s+'.kicad_sch'),os.path.join(tmp,'b_'+s+'.net')); B.update({r:v['props'].get('Note') for r,v in c.items()})
    gen=''.join(open(f).read() for f in glob.glob('cards/tools/*.py'))
    gen_unesc=gen.replace("\\'","'").replace('\\"','"')
    projects=[('genctl','genctl.kicad_sch'),('genctl_meter','genctl_meter.kicad_sch')]+[(c,f'cards/{c}/{c}.kicad_sch') for c in ('engine','di8','ai4','hso5','brk4')]
    bad=[]; nnotes=0
    for name,sch in projects:
        comps,pins=netlist(sch,os.path.join(tmp,name+'.net')); n_here=0
        for ref,c in sorted(comps.items()):
            note=c['props'].get('Note')
            if not note: continue
            nnotes+=1; n_here+=1
            def f(rule,msg): bad.append(f'{name}:{ref} [{rule}] {msg} | Note="{note[:110]}"')
            # R1 provenance
            bref=(c['props'].get('BaselineRef') or '').replace('copy:','') or (ref if name in ('genctl','genctl_meter') else None)
            bnote=B.get(bref) if bref else None
            if bnote and norm(bnote)==norm(note): pass
            elif note in gen or note in gen_unesc: pass
            elif f'{name}:{ref}' in EDITS: pass
            else: f('R1','not a baseline Note (ref-translated) and not generator text')
            # R2 ref tokens
            for m in TOK.finditer(note):
                if note[max(0,m.start()-10):m.start()].endswith(HIST): continue
                if m.group(1) not in comps: f('R2',f'names {m.group(1)}, which is not in this project')
            # R3 DNP
            says_dnp=bool(re.search(r'\bDNP\b(?![ -]?(?:option|alternative|pads? for))',note)) and not re.search(r'\b(fit|fitted|populate)\b[^.]*\binstead\b',note,re.I)
            if says_dnp and not c['dnp'] and not re.search(r'DNP\b[^.]{0,40}\b(on|for|if|when|unless)\b',note): f('R3','Note says DNP but the part is fitted')
            if c['dnp'] and re.search(r'\bfitted\b',note) and not says_dnp: f('R3','part is DNP but Note says fitted')
            # R4 diode pin claims
            m=re.search(r'\bA = ([\w+\-]+)[^,;]*, K = ([\w+\-]+)',note) or re.search(r'\bK = ([\w+\-]+)[^,;]*, A = ([\w+\-]+)',note)
            if m and ('A = ' in note and 'K = ' in note):
                a_word,k_word=(m.group(1),m.group(2)) if note[m.start()]=='A' else (m.group(2),m.group(1))
                pa=[n for (r,p),(n,pf) in pins.items() if r==ref and (pf=='A' or p=='2')]
                pk=[n for (r,p),(n,pf) in pins.items() if r==ref and (pf=='K' or p=='1')]
                qpin={'gate':'G','source':'S','drain':'D'}
                def match(word,nets):
                    w=word.lower()
                    if w in qpin: return any(nn in nets and r2[0]=='Q' and pf2==qpin[w] for (r2,p2),(nn,pf2) in pins.items())
                    return any(w in n.lower() for n in nets)
                if not (match(a_word,pa) and match(k_word,pk)): f('R4',f'claims A={a_word}, K={k_word}; nets A={pa} K={pk}')
            for w in STALE:
                if w in note: f('R5',f'stale phrase "{w}"')
        print(f'{name:13s} Notes checked: {n_here}')
    for b in bad: print('FINDING',b)
    print(f'note_lint: {nnotes} Notes in 7 projects, {len(bad)} findings')
    sys.exit(1 if bad else 0)
main()
