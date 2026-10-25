#!/bin/sh
# render full board + two close-ups from $1 (default genctl_v4.kicad_pcb)
P=${1:-genctl_v4.kicad_pcb}
python3 render_v4.py $P genctl_v4_board.png "--title=$P"
python3 render_v4.py $P genctl_v4_cm5_display.png 150 20 245 145 "--title=CM5 / display"
python3 render_v4.py $P genctl_v4_600V.png -4 11 62 162 "--title=600 V metering"
