import re,json,sys,os,pickle
def parse(s):
    tok=re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+',s)
    st=[[]]
    for t in tok:
        if t=='(':st.append([])
        elif t==')':x=st.pop();st[-1].append(x)
        else: st[-1].append(t[1:-1].replace('\\"','"') if t.startswith('"') else t)
    return st[0][0]
def find(n,k): return [c for c in n if isinstance(c,list) and c and c[0]==k]
def load(path):
    r=parse(open(path).read())
    comps={}
    for c in find(find(r,'components')[0],'comp'):
        d={x[0]:x[1] for x in c if isinstance(x,list) and len(x)>1 and isinstance(x[1],str)}
        props={}
        for p in find(c,'property'):
            dd={x[0]:x[1] for x in p if isinstance(x,list)}
            props[dd.get('name')]=dd.get('value')
        sp=find(c,'sheetpath'); sheet=sp[0][1][1] if sp else ''
        comps[d['ref']]=dict(value=d.get('value'),fp=d.get('footprint'),props=props,sheet=sheet,pins={})
    nets={}
    for n in find(find(r,'nets')[0],'net'):
        nm=[x[1] for x in n if isinstance(x,list) and x[0]=='name'][0]
        nets[nm]=[]
        for nd in find(n,'node'):
            dd={x[0]:x[1] for x in nd if isinstance(x,list)}
            nets[nm].append((dd['ref'],dd['pin']))
            if dd['ref'] in comps: comps[dd['ref']]['pins'][dd['pin']]=(dd.get('pinfunction',''),nm)
    return comps,nets
sh=lambda n: re.sub(r'^/[^/]*/','',n)
def dump(C,ref):
    c=C[ref]; print('==',ref,c['value'],'MPN=',c['props'].get('MPN'),'LCSC=',c['props'].get('LCSC'),c['fp'],c['sheet'][:30])
    for p in sorted(c['pins'],key=lambda x:(len(x),x)): f,n=c['pins'][p]; print(f'  {p:>4} {f:14} {sh(n)}')
def net(C,N,a):
    ns=[n for n in N if n==a or sh(n)==a or n.endswith('/'+a)]
    for n in ns:
        out=[]
        for r,p in sorted(N[n]):
            pins=C[r]['pins']
            if len(pins)==2 and r[0] in 'RCLDF':
                o=[x for x in pins if x!=p][0]; out.append(f"{r}[{C[r]['value']}]->{sh(pins[o][1])}")
            else: out.append(f"{r}.{p}({C[r]['pins'][p][0]})")
        print(f"## {sh(n)} ({len(N[n])}): "+'; '.join(out))
if __name__=='__main__':
    C,N=load(sys.argv[1])
    for a in sys.argv[2:]:
        if a in C: dump(C,a)
        else: net(C,N,a)
