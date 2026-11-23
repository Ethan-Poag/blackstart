#!/bin/sh
# render one card sheet: ERC report + PDF + PNG (150 dpi) next to the schematic
set -e
d=$(dirname "$0")/../$1; n=$1
kicad-cli sch erc --severity-all -o $d/erc.rpt $d/$n.kicad_sch >/dev/null
grep "ERC messages" $d/erc.rpt
kicad-cli sch export pdf -o $d/$n.pdf $d/$n.kicad_sch >/dev/null
pdftoppm -r 150 -png -singlefile $d/$n.pdf $d/$n
ls -la $d/$n.png
