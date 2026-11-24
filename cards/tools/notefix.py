"""Pass 4 m3: keep schematic `Note` fields honest.
- New parts (added by a generator) carry only the Note the generator wrote for them; copy helpers strip inherited Notes.
- Carried baseline parts keep their baseline Note, but every reference designator in it is translated to the ref the part (or the
  referenced part) has in THIS project; a ref that no longer exists here is marked "baseline Rxx".
- Pass 3 N13 symbol swaps: the old "symbol kept" wording is replaced by the symbol actually used.
docs/modular/tools/note_lint.py checks the written schematics independently."""
import re
TOK=re.compile(r'(?<![\w\-/.])((?:TP|JP|[RCDQUJLYF])\d{1,3})(?![\w\-])')
KEEP_BEFORE=('baseline ',)
def translate(note,refmap,present):
    def sub(m):
        t=m.group(1); pre=note[max(0,m.start()-9):m.start()]
        if pre.endswith(KEEP_BEFORE): return t
        if t in refmap and refmap[t] in present: return refmap[t]
        if t in present and t not in refmap: return t
        return 'baseline '+t
    return TOK.sub(sub,note)
def fix(card,present=None):
    present=present or {p['ref'] for p in card.parts}
    refmap=dict(getattr(card,'refmap',{})); refmap.update(getattr(card,'copymap',{}))
    for p in card.parts:
        n=p['props'].get('Note')
        if not n: continue
        if p.get('carried'):
            n=n.replace('Same SOT-23 G-S-D pinout; symbol kept',f"Same SOT-23 G-S-D pinout; symbol {p['lib_id']} (Pass 3 N13)") if p['lib_id'].startswith('cards:') else n
            n=translate(n,refmap,present)
        p['props']['Note']=n
