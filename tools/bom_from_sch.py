#!/usr/bin/env python3
"""Check the category BOMs (bom/*.csv) against the COMMITTED schematic, not the generator.
Usage: python3 tools/bom_from_sch.py [--kicad-cli PATH] [--net net.xml]
Exports a kicadxml netlist of genctl.kicad_sch with kicad-cli, groups the BOM-included parts
by LCSC code (or by MPN when there is no LCSC), and compares:
  - qty: number of schematic refs vs the sum of 'qty per board' over the category-BOM rows with that code;
  - codes present in only one side.
The category BOMs have no refdes or value column, so refs and values are reported from the schematic only.
Rows with no LCSC code (ac_metering_bom.csv, off-board items) are matched on part number when possible."""
import csv,sys,os,re,subprocess,tempfile,collections,glob
import xml.etree.ElementTree as ET
here=os.path.dirname(os.path.abspath(__file__)); root=os.path.dirname(here)
cli='/workspace/bin/kicad-cli'; net=None; a=sys.argv[1:]
if '--kicad-cli' in a: cli=a[a.index('--kicad-cli')+1]
if '--net' in a: net=a[a.index('--net')+1]
if not net:
    net=os.path.join(tempfile.mkdtemp(),'net.xml')
    subprocess.run([cli,'sch','export','netlist','--format','kicadxml','-o',net,os.path.join(root,'genctl.kicad_sch')],check=True,capture_output=True)
r=ET.parse(net).getroot()
sch=collections.defaultdict(list); info={}
for c in r.iter('comp'):
    ref=c.get('ref'); f={x.get('name'):(x.text or '') for x in c.iter('field')}
    props={p.get('name'):p.get('value') for p in c.iter('property')}
    if 'exclude_from_bom' in props or 'dnp' in props or ref.startswith('#'): continue
    k=f.get('LCSC','').strip() or ('MPN:'+f.get('MPN','').strip().upper() if f.get('MPN','').strip() else 'VAL:'+(c.findtext('value') or ''))
    sch[k].append(ref); info.setdefault(k,(c.findtext('value'),f.get('MPN',''),c.findtext('footprint')))
bom=collections.defaultdict(float); rows=collections.defaultdict(list); bompn={}
for p in sorted(glob.glob(os.path.join(root,'bom','*.csv'))):
    for i,row in enumerate(csv.DictReader(open(p,encoding='utf-8',errors='replace')),start=2):
        fn=(row.get('function') or '')
        if fn.startswith('TOTAL'): continue
        l=(row.get('LCSC part') or '').strip(); pn=(row.get('part number') or '').strip()
        try: q=float(row.get('qty per board') or 0)
        except ValueError: q=None
        if re.match(r'^C\d+$',l): k=l
        elif pn: k='MPN:'+pn.upper()
        else: continue
        rows[k].append('%s:%d'%(os.path.basename(p),i))
        if q is None: bom[k]=float('nan')
        else: bom[k]+=q
        bompn[k]=pn
# MPN-keyed BOM rows may match a schematic LCSC group with the same MPN
for k in list(bom):
    if k.startswith('MPN:') and k not in sch:
        for sk,(v,m,fp) in info.items():
            if m and m.upper()==k[4:]: bom[sk]+=bom.pop(k); rows[sk]+=rows.pop(k); break
mism=[];
for k in sorted(set(sch)|set(bom)):
    n=len(sch.get(k,[])); b=bom.get(k)
    if b is None: mism.append(('SCH_ONLY',k,n,0,info[k],sch[k],[]))
    elif k not in sch: mism.append(('BOM_ONLY',k,0,b,bompn.get(k),[],rows[k]))
    elif b!=b or abs(b-n)>1e-9: mism.append(('QTY',k,n,b,info[k],sch[k],rows[k]))
for m in mism: print('%-8s %-22s sch=%-4s bom=%-6s %s refs=%s rows=%s'%(m[0],m[1],m[2],m[3],m[4],','.join(m[5][:12])+('…' if len(m[5])>12 else ''),';'.join(m[6])))
print('SUMMARY schematic groups %d, bom groups %d, mismatches %d (QTY %d, SCH_ONLY %d, BOM_ONLY %d)'%(len(sch),len(bom),len(mism),
  sum(m[0]=='QTY' for m in mism),sum(m[0]=='SCH_ONLY' for m in mism),sum(m[0]=='BOM_ONLY' for m in mism)))
