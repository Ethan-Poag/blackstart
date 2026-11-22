import re,sys
sys.path.insert(0,'/workspace/review/split/exec')
from sx import block_at
SW={'LED_O_A':'12','LED_O_K':'11','LED_G_A':'14','LED_G_K':'13'}
OLD={'LED_O_A':'11','LED_O_K':'12','LED_G_A':'13','LED_G_K':'14'}
def fix(path,head):
    s=open(path).read(); i=s.find(head); assert i>=0,(path,head); e=block_at(s,i); b=s[i:e]; n=0
    def rep(m):
        global_n=None
        pb=m.group(0)
        nm=re.search(r'\(name "([^"]+)"',pb).group(1)
        if nm in SW:
            num=re.search(r'\(number "([^"]+)"',pb).group(1); assert num==OLD[nm],(nm,num)
            return pb.replace(f'(number "{num}"',f'(number "{SW[nm]}"',1)
        return pb
    out=[];j=0;cnt=0
    for m in re.finditer(r'\(pin \w+ \w+',b):
        if m.start()<j: continue
        pe=block_at(b,m.start()); pb=b[m.start():pe]
        nb=rep(re.match(r'(?s).*',pb)); cnt+= nb!=pb
        out.append(b[j:m.start()]); out.append(nb); j=pe
    out.append(b[j:]); nb=''.join(out); assert cnt==4,(path,cnt)
    open(path,'w').write(s[:i]+nb+s[e:]); print(path,'pins renumbered',cnt)
fix('comms.kicad_sch','(symbol "genctl:HR963380AE"')
fix('genctl.kicad_sym','(symbol "HR963380AE"')
