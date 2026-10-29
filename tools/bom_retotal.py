#!/usr/bin/env python3
"""Recompute each bom/*.csv TOTAL row exactly from its rows: sum(qty per board x unit price USD) over
rows whose price parses as a number; every other row is listed as EXCLUDED (unpriced/UNVERIFIED/ESTIMATE).
The total goes in column 11 (13-column files) or 5 (ac_metering). Line endings are preserved."""
import csv,io,glob,os,sys
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in sorted(glob.glob(os.path.join(root,'bom','*.csv'))):
    if 'off_board' in os.path.basename(p): continue  # excluded from all totals by design
    raw=open(p,newline='',encoding='utf-8').read(); nl='\r\n' if '\r\n' in raw else '\n'
    L=list(csv.reader(io.StringIO(raw))); ti=[i for i,r in enumerate(L) if r and r[0].startswith('TOTAL')][0]
    tot=0.0; ex=[]
    for r in L[1:]:
        if not r or r[0].startswith('TOTAL') or not any(r): continue
        try: tot+=float(r[4])*float(r[5])
        except (ValueError,IndexError): ex.append(r[0][:40])
    col=11 if len(L[0])>=13 else 5; f=os.path.basename(p)
    L[ti][0]='TOTAL (%s; m7-sch 2026-10-28: recomputed exactly from the rows = sum(qty x unit price) over priced rows, rounded to cents; EXCLUDED unpriced/UNVERIFIED/ESTIMATE rows (%d): %s)'%(f,len(ex),'; '.join(ex) or 'none')
    old=L[ti][col]; L[ti][col]='%.2f'%tot
    o=io.StringIO(); w=csv.writer(o,lineterminator=nl); [w.writerow(r) for r in L]
    if '--check' not in sys.argv: open(p,'w',newline='',encoding='utf-8').write(o.getvalue())
    print('%-22s TOTAL %s -> %.2f  excluded %d'%(f,old,tot,len(ex)))
