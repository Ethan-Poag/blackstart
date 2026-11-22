import re,sys,nl
RAILS={'GND','+3V3_SAFE','+3V3','+5V','CM5_3V3','GND_AC','VBAT_P','+12V'}
def conn(C,N,pin):
    f,net=C['U7']['pins'][pin]
    direct=[];follow=[]
    for r,p in sorted(N[net],key=lambda x:(x[0][0],int(re.sub(r'\D','',x[0]) or 0),x[1])):
        if r=='U7': continue
        c=C[r]
        if r.startswith('R') and len(c['pins'])==2:
            o=[x for x in c['pins'] if x!=p][0]; on=c['pins'][o][1]; s=nl.sh(on)
            if s in RAILS or on in RAILS: far='(rail)'
            else:
                far=' '.join(f"{rr}.{pp}({C[rr]['pins'][pp][0]})[{C[rr]['value'][:24].strip()}]" if C[rr]['pins'][pp][0] else f"{rr}.{pp}[{C[rr]['value'][:24].strip()}]" for rr,pp in sorted(N[on],key=lambda x:(x[0][0],int(re.sub(r'\D','',x[0]) or 0),x[1])) if rr!=r)
            follow.append(f"{r}[{c['value']}]->{s}: {far}")
        else:
            fn=c['pins'][p][0]
            direct.append(f"{r}.{p}({fn})[{c['value'][:24].strip()}]" if fn else f"{r}.{p}[{c['value'][:24].strip()}]")
    return ' / '.join(([' '.join(direct)] if direct else [])+follow)
if __name__=='__main__':
    C,N=nl.load(sys.argv[1]); md=open(sys.argv[2]).read().split('\n')
    ok=bad=0
    for i,l in enumerate(md):
        m=re.match(r'\| (\d+) \| (\w+) \| ([^|]*) \| ([^|]*) \|',l)
        if not m: continue
        pin=m.group(1); new=conn(C,N,pin)
        if new.strip()==m.group(4).strip(): ok+=1
        else:
            bad+=1
            if '-v' in sys.argv: print(pin,'\n  OLD',m.group(4)[:200],'\n  NEW',new[:200])
    print('match',ok,'differ',bad)
