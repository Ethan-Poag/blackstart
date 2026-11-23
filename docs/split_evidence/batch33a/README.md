# Batch 33a evidence (2026-11-22 HST): battle short decisions D1–D6 + editable settings, docs only
- erc_genctl.json, erc_genctl_meter.json: kicad-cli 9.0.2 ERC --severity-all, 0 violations each.
- ndiff_genctl.txt, ndiff_genctl_meter.txt: netlists exported from the working tree vs 5bd77c4: 1147 / 220 parts, identical apart from the header (date/source).
- bom_check.txt: tools/bom_from_sch.py check, 0 mismatches (all six BOM files).
- All *.kicad_sch, genctl.kicad_sym, genctl.pretty, bom/ and tools/ files are byte-identical to 5bd77c4 (git diff --quiet).
- Changed: docs/FW_REQ_BATTLESHORT.md, firmware/ARCHITECTURE.md (battle-short overlay text only), docs/INSTALL_SAFETY.md, DESIGN_NOTES.md, docs/SCHEMATIC_CHANGELOG.md.
