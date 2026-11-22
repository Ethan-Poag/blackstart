#!/usr/bin/env python3
"""Check the TOTAL rows of the generated per-board BOMs (bom/genctl_main_bom.csv, bom/genctl_meter_bom.csv,
bom/harness_bom.csv): each TOTAL must equal sum(qty x unit price) over the priced fitted rows.
The files themselves are written by tools/bom_from_sch.py --write (Batch 28: two projects, main + meter);
this script never edits them. Exit code 1 if a TOTAL does not match."""
import csv,os,sys
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); bad=0
for f,qcol,u1,u10,e1,e10 in (('bom/genctl_main_bom.csv','Qty','Unit USD qty1','Unit USD qty10','Ext USD qty1','Ext USD qty10'),
                             ('bom/genctl_meter_bom.csv','Qty','Unit USD qty1','Unit USD qty10','Ext USD qty1','Ext USD qty10'),
                             ('bom/harness_bom.csv','Qty','Unit USD qty1','Unit USD qty10','Ext USD qty1','Ext USD qty10')):
    rows=list(csv.DictReader(open(os.path.join(root,f),encoding='utf-8'))); t1=t10=0.0; tot=None
    first=list(rows[0].keys())[0]
    for r in rows:
        if r[first].startswith('TOTAL'): tot=r; continue
        if r.get('DNP')=='DNP': continue
        try: t1+=float(r[qcol])*float(r[u1]); t10+=float(r[qcol])*float(r[u10])
        except ValueError: pass
    ok=abs(float(tot[e1])-t1)<0.006 and abs(float(tot[e10])-t10)<0.006
    bad+=not ok
    print(f'{f:28s} TOTAL qty1 {tot[e1]:>8s} (sum {t1:.2f})  qty10 {tot[e10]:>8s} (sum {t10:.2f})  {"OK" if ok else "MISMATCH"}')
sys.exit(1 if bad else 0)
