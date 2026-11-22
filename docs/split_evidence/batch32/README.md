# Batch 32 evidence (2026-11-22 HST)
- tidy32.py: drafting-only edit of the Batch 31 inputs-sheet block (text positions, hidden overlapping values, sheet-note WD_OK timing). Run once on d08d49f.
- gating_block.png: render of the tidied block (kicad-cli SVG → PNG).
- erc_genctl.json, erc_genctl_meter.json: kicad-cli 9.0.2 ERC --severity-all, 0 violations each.
- ndiff_genctl.txt, ndiff_genctl_meter.txt: netlist diff vs d08d49f (fix29/ndiff.py): part counts only, no part/property/net change.
- bom_check.txt: tools/bom_from_sch.py check after --write, 0 mismatches; the regenerated BOM files are byte-identical to d08d49f.
