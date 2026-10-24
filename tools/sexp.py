import re
class Sym(str): pass
def parse(s):
    toks = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', s)
    stack=[[]]
    for t in toks:
        if t=='(':
            stack.append([])
        elif t==')':
            x=stack.pop(); stack[-1].append(x)
        elif t[0]=='"':
            stack[-1].append(t[1:-1].replace('\\"','"').replace('\\\\','\\'))
        else:
            stack[-1].append(Sym(t))
    return stack[0]
def q(s):
    return '"'+str(s).replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')+'"'
def dump(x, ind=0):
    if isinstance(x,list):
        if not x: return '()'
        simple = all(not isinstance(e,list) for e in x)
        if simple and len(x)<8:
            return '('+' '.join(dump(e) for e in x)+')'
        out='('+dump(x[0])
        for e in x[1:]:
            if isinstance(e,list): out+='\n'+'\t'*(ind+1)+dump(e,ind+1)
            else: out+=' '+dump(e)
        return out+')'
    if isinstance(x,Sym): return str(x)
    if isinstance(x,bool): return 'yes' if x else 'no'
    if isinstance(x,(int,float)):
        if isinstance(x,float):
            s=('%.4f'%x).rstrip('0').rstrip('.')
            return s if s not in ('-0','') else '0'
        return str(x)
    return q(x)
def find(x, key):
    return [e for e in x if isinstance(e,list) and e and e[0]==key]
def find1(x,key):
    r=find(x,key); return r[0] if r else None
