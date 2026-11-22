# Batch 31 evidence (2026-11-22 HST)
- batch31.py: schematic edit script (run once on 956a998): shunt-off gating U91/U92/U93/C320/C321/C322/RN1/RN2 on inputs, AI_SH_G1-6 relabel, R531 MPN/Manufacturer, J2/U71/U72 footprint attr smd.
- gating_block.png: render of the new inputs-sheet block (kicad-cli SVG → PNG).
- fetch/jlc_live.txt: live JLC parts API for C6053, C29718, C14663, C23345, C7836 (12:37-12:50 PM HST). q.py: search helper.
- erc_genctl.json, erc_genctl_meter.json: kicad-cli 9.0.2 ERC --severity-all, 0 violations each.
- ndiff_genctl.txt, ndiff_genctl_meter.txt: netlist diff vs 956a998 (fix29/ndiff.py): 8 added parts, R531 properties, AI_SH_EN split, SH_ALLOW, NRST_S, WD_OK/NRST +1 node each; meter unchanged.
- bom_check.txt: tools/bom_from_sch.py check after --write, 0 mismatches.
- bom_b31.py, bom_b31_run.txt, bom_split_totals*.json: priced controller BOM update (/workspace/review/bom_split), crosscheck 0.
