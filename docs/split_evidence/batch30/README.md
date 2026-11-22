# Batch 30 evidence (2026-11-22 HST)
- src30.py: Sourcing-field edit script (J2, U15, U16, U5, U21, RV1-RV6). q.py: JLC parts search helper.
- fetch/: live JLC (jlc_live.txt), TI store (ti_live.txt) and LCSC detail (lcsc_*.json) responses, ~12:08-12:16 HST.
- erc_genctl.json, erc_genctl_meter.json: kicad-cli 9.0.2 ERC --severity-all, 0 violations each.
- ndiff_genctl.txt, ndiff_genctl_meter.txt: netlist diff vs fa8aced (batch29/ndiff.py): property changes only.
- bom_check.txt: tools/bom_from_sch.py --write then check, 0 mismatches.
- bom_b30.py, bom_b30_run.txt, bom_split_totals*.json: priced controller BOM (/workspace/review/bom_split) update and totals.
