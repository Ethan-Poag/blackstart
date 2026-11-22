# Batch 29 evidence (2026-11-22 HST)
- batch29.py: schematic edit script (reruns cleanly from ade499e schematics); helpers ed.py, geo.py, nl.py, fsearch.py.
- erc_genctl.json, erc_genctl_meter.json: kicad-cli 9.0.2 ERC --severity-all, 0 violations each.
- ndiff_genctl.txt, ndiff_genctl_meter.txt: netlist diff vs ade499e (ndiff.py).
- bom_check.txt: tools/bom_from_sch.py check, 0 mismatches. pre_*_bom.csv: BOMs before Batch 29.
- bom_b29.py, bom_b29_run.txt, bom_split_totals*.json: priced controller BOM (/workspace/review/bom_split) update and totals.
- fetch/: JLC/LCSC API responses (C13167, C876535, C702145, C94571, C1588, C21190, C122538, C309650); lcsc.py, ti.py, fetch.py: fetch helpers.
