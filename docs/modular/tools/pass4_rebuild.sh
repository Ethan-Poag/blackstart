#!/bin/sh
# Pass 4: full regenerate + verify pipeline (cards, mainboard, ERC x7, renders, BOMs, audit, cost). Run from the repo root.
set -e
cd cards && python3 tools/mklib.py && python3 tools/card_engine.py && for c in di8 ai4 hso5 brk4; do python3 tools/lvcards.py $c; done && python3 tools/mainboard.py && cd ..
for c in engine di8 ai4 hso5 brk4; do sh cards/tools/render.sh $c | head -1; sh cards/tools/bom.sh $c; pdfinfo cards/$c/$c.pdf | grep -E "^Pages"; done
kicad-cli sch erc --severity-all -o docs/modular/erc/genctl_main.rpt genctl.kicad_sch >/dev/null; grep "ERC messages" docs/modular/erc/genctl_main.rpt
kicad-cli sch erc --severity-all -o docs/modular/erc/genctl_meter.rpt genctl_meter.kicad_sch >/dev/null; grep "ERC messages" docs/modular/erc/genctl_meter.rpt
D=docs/modular/img/mainboard; kicad-cli sch export pdf -o $D/genctl_mainboard.pdf genctl.kicad_sch >/dev/null
for x in "1 root" "3 mcu" "7 io_core" "8 backplane" "9 slot_power" "10 estop" "11 mtr_if"; do set -- $x; pdftoppm -r 150 -png -singlefile -f $1 -l $1 $D/genctl_mainboard.pdf $D/$2; done
python3 docs/modular/tools/system_audit.py | grep -E "same|changes|unexplained|orphans"
python3 cards/tools/verify_mainboard.py | tail -1
python3 tools/bom_from_sch.py --write | tail -1
python3 docs/modular/tools/true_cost.py | tail -3
python3 docs/modular/tools/pass4_calc.py > docs/modular/pass4_calc.txt
python3 docs/modular/tools/note_lint.py | tail -3
