#!/bin/bash
# Blackstart v4: place -> critical (classes/planes/fan-out) -> Freerouting remainder -> DRC -> render
set -e
cd "$(dirname "$0")"; W=work; mkdir -p $W ../out
PASSES=${PASSES:-40}
[ "$SKIP_PLACE" = 1 ] || python3 place_v4.py --netlist genctl.net --out pcb_v4/genctl_v4.kicad_pcb ${SEEDS:+--seeds $SEEDS}
python3 refine_v4.py pcb_v4/genctl_v4.kicad_pcb pcb_v4/genctl_v4_ref.kicad_pcb 2>&1 | grep -v assert  # crystals + HV divider strings
python3 seat_iso_series.py pcb_v4/genctl_v4_ref.kicad_pcb pcb_v4/genctl_v4_ref.kicad_pcb 2>&1 | grep -v assert
python3 route_v4.py setup pcb_v4/genctl_v4_ref.kicad_pcb $W/crit.kicad_pcb 2>&1 | grep -v assert
python3 pcb_v4/handroute_iter.py $W/crit.kicad_pcb $W/hand.kicad_pcb 6   # critical nets, locked
python3 route_v4.py dsn $W/hand.kicad_pcb $W/genctl.dsn
sed -i 's/(type route)/(type protect)/g' $W/genctl.dsn   # hand routes fixed for Freerouting 2>&1 | grep -v assert
/workspace/tools/jre/bin/java -jar /workspace/tools/freerouting.jar -de $W/genctl.dsn -do $W/genctl.ses --router.fanout.enabled=false --router.autorouter.max_passes=$PASSES -mt 8 > $W/freerouting.log 2>&1 || true
python3 route_v4.py ses $W/hand.kicad_pcb $W/genctl.ses pcb_v4/genctl_v4_routed.kicad_pcb 2>&1 | grep -v assert
kicad-cli pcb drc --severity-error -o $W/drc.rpt pcb_v4/genctl_v4_routed.kicad_pcb > /dev/null; grep "Found" $W/drc.rpt
