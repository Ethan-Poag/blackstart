#!/bin/bash
# usage: filldrc.sh name   (name.kicad_pcb)
n=$1
cp genctl_v4_handrouted.kicad_pro $n.kicad_pro; cp genctl_v4_handrouted.kicad_dru $n.kicad_dru
python3 -c "
import pcbnew;b=pcbnew.LoadBoard('$n.kicad_pcb');pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.Save('$n.kicad_pcb')" 2>&1 | grep -v 'leak\|Debug'
kicad-cli pcb drc --format json --severity-error -o $n.json $n.kicad_pcb 2>&1 | tail -3
python3 -c "
import json,collections;d=json.load(open('$n.json'));print(len(d['violations']),collections.Counter(v['type'] for v in d['violations']),'unconn',len(d.get('unconnected_items',[])))"
