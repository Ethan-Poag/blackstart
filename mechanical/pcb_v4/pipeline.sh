#!/bin/bash
# Blackstart v4: place -> critical (classes/planes/fan-out) -> Freerouting remainder -> DRC -> render
set -e
cd "$(dirname "$0")"; W=work; mkdir -p $W ../out
PASSES=${PASSES:-40}
[ "$SKIP_PLACE" = 1 ] || python3 place_v4.py --netlist genctl.net --out pcb_v4/genctl_v4.kicad_pcb ${SEEDS:+--seeds $SEEDS}
python3 route_v4.py setup pcb_v4/genctl_v4.kicad_pcb $W/crit.kicad_pcb 2>&1 | grep -v assert
python3 route_v4.py dsn $W/crit.kicad_pcb $W/genctl.dsn 2>&1 | grep -v assert
/workspace/tools/jre/bin/java -jar /workspace/tools/freerouting.jar -de $W/genctl.dsn -do $W/genctl.ses --router.fanout.enabled=false --router.autorouter.max_passes=$PASSES -mt 8 > $W/freerouting.log 2>&1 || true
python3 route_v4.py ses $W/crit.kicad_pcb $W/genctl.ses pcb_v4/genctl_v4_routed.kicad_pcb 2>&1 | grep -v assert
kicad-cli pcb drc --severity-error -o $W/drc.rpt pcb_v4/genctl_v4_routed.kicad_pcb > /dev/null; grep "Found" $W/drc.rpt
