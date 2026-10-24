# genctl – KiCad schematic (draft A)

KiCad 8/9 hierarchical schematic for the genctl diesel generator controller.
Open `genctl.kicad_pro` in KiCad 8 or 9.

* `genctl.kicad_sch` – root sheet (10 sub-sheets, connectivity via global labels)
* `*.kicad_sch` – power, mcu, cm5, comms, display, inputs, outputs, estop, ac_metering, frontpanel
* `genctl.kicad_sym` – project symbols (non-library ICs/connectors) with LCSC/MPN fields
* `docs/genctl_schematic.pdf` – PDF export, `docs/erc_report.txt` – ERC, `docs/genctl_bom.csv` – BOM export
* `docs/auto_nc_pins.log` – every pin the generator left as no-connect (review list)
* `DESIGN_NOTES.md` – all assumptions, value choices and open questions
* `tools/` – generator (`python3 tools/run.py` from `tools/` regenerates every sheet; UUIDs change on each run)

Schematic was generated programmatically; it is wiring-by-label (short stubs + net labels), not hand-routed.
