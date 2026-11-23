#!/bin/sh
# per-card BOM grouped by Value+Footprint+LCSC (kicad-cli); then list rows without an LCSC number
set -e
d=$(dirname "$0")/../$1; n=$1
kicad-cli sch export bom -o $d/${n}_bom.csv --fields 'Reference,Value,Footprint,LCSC,MPN,${QUANTITY},BaselineRef' \
  --labels 'Refs,Value,Footprint,LCSC,MPN,Qty,BaselineRefs' --group-by 'Value,Footprint,LCSC' --ref-range-delimiter '' $d/$n.kicad_sch >/dev/null
python3 - $d/${n}_bom.csv <<'P'
import csv,sys
r=list(csv.DictReader(open(sys.argv[1])))
print(sys.argv[1].split('/')[-1],'lines',len(r),'qty',sum(int(x['Qty']) for x in r),'no-LCSC',[x['Value'] for x in r if not x['LCSC'].strip()])
P
