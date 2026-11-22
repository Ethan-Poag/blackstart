# Bills of materials (m7-split, Batch 28 onward)

Two KiCad projects since the split: **genctl** (main board) and **genctl_meter** (HV metering daughter board).
All on-board BOMs are generated from the committed schematics. Do not hand-edit them.

| File | Content | Written by |
|---|---|---|
| `genctl_main_bom.csv` | Main board, priced: refs, qty, value, footprint, MPN, manufacturer, LCSC, JLC class, unit/ext price at qty 1 and qty 10, DNP groups, TOTAL | `tools/bom_from_sch.py --write` |
| `genctl_meter_bom.csv` | Metering daughter board, same columns | same |
| `harness_bom.csv` | J31–J32 Micro-Fit harness (2× 43025-1600, 32× 43030-0001, wire), off-board | same (table in the script) |
| `lcsc_prices.csv` | Price/stock table the generator reads (board, LCSC or MPN key) | hand-maintained; Batch 28 rows from the JLC parts API |
| `off_board_external_bom.csv` | Historic off-board/estimate rows (CM5, display, plugs, enclosure). Excluded from all totals and checks | — |
| `design_spec.md` | Design spec (section headings still name the old category BOMs) | — |

Also generated: `docs/genctl_bom.csv`, `docs/genctl_meter_bom.csv` (Refs/Value/Footprint/MPN/LCSC/Qty/DNP) and
`mechanical/bom.csv`, `mechanical/bom_meter.csv` (Reference/Value/Footprint/QUANTITY).

Check (runs kicad-cli, regenerates in memory, diffs against the files, and cross-checks every ref's value,
footprint, MPN, LCSC and DNP flag plus each row's qty against the netlists; exit 1 on any mismatch):

    python3 tools/bom_from_sch.py
    python3 tools/bom_retotal.py     # TOTAL rows = sum(qty x unit)

The six category BOMs (`power_bom.csv`, `inputs_bom.csv`, `outputs_bom.csv`, `comms_bom.csv`, `other_bom.csv`,
`ac_metering_bom.csv`) were removed in Batch 28: they had no refdes column and had drifted from the schematic
(missing the split and Batch 27 parts). Their sourcing notes are in git history (commit 91ccb62 and earlier).
`tools/gen.py` (the retired schematic generator, marked DO NOT REGENERATE) still names them and is not used.

The priced controller BOM with off-board items (CM5, display, enclosure, PCB/PCBA fees) is kept outside the repo
in `/workspace/review/bom_split` (BOM_main.csv, BOM_daughter.csv, totals.json), rebuilt from the same netlists.
