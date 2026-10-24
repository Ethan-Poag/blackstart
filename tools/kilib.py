import os, copy, re
from sexp import parse, find, find1, Sym
LIBDIR='/usr/share/kicad/symbols'
_cache={}
def load_lib(path):
    if path not in _cache:
        _cache[path]={e[1]:e for e in find(parse(open(path).read())[0],'symbol')}
    return _cache[path]
def get_symbol(libid, custom=None):
    lib,name=libid.split(':')
    syms = custom if lib=='genctl' else load_lib(os.path.join(LIBDIR,lib+'.kicad_sym'))
    s=copy.deepcopy(syms[name])
    ext=find1(s,'extends')
    if ext:
        parent=copy.deepcopy(syms[ext[1]])
        if find1(parent,'extends'):
            parent=get_symbol(lib+':'+ext[1],custom); parent[1]=ext[1]
        # props from child override
        cprops={p[1]:p for p in find(s,'property')}
        new=[Sym('symbol'),name]
        for e in parent[2:]:
            if isinstance(e,list) and e[0]=='property' and e[1] in cprops:
                new.append(cprops.pop(e[1]))
            elif isinstance(e,list) and e[0]=='symbol':
                sub=copy.deepcopy(e); sub[1]=sub[1].replace(ext[1],name,1); new.append(sub)
            else: new.append(e)
        for p in cprops.values(): new.insert(len(new)-0,p)
        s=new
    s=[e for e in s if not (isinstance(e,list) and e[0] in ('embedded_fonts',))]
    return s
def pins(sym):
    """return list of dict(num,name,x,y,ang,len,unit,type)"""
    out=[]
    name=sym[1]
    for sub in find(sym,'symbol'):
        m=re.match(r'.*_(\d+)_(\d+)$',sub[1]); unit=int(m.group(1)); style=int(m.group(2))
        if style not in (0,1): continue
        for p in find(sub,'pin'):
            at=find1(p,'at'); ln=find1(p,'length')
            nm=find1(p,'name')[1]; nu=find1(p,'number')[1]
            hidden = any((isinstance(e,Sym) and e=='hide') or (isinstance(e,list) and e[0]=='hide' and e[1]=='yes') for e in p)
            out.append(dict(num=nu,name=nm,x=float(at[1]),y=float(at[2]),ang=int(float(at[3])) if len(at)>3 else 0,len=float(ln[1]),unit=unit,type=str(p[1]),hidden=hidden))
    return out
def units(sym):
    us=set()
    for sub in find(sym,'symbol'):
        m=re.match(r'.*_(\d+)_(\d+)$',sub[1]); us.add(int(m.group(1)))
    us.discard(0)
    return sorted(us) or [1]
