# COST NOTES (m7-sch, 2026-10-28)
Ethan decides on cost. All figures are per board, in USD, from the committed bom/*.csv TOTAL rows (tools/bom_retotal.py, exact). Only MEASURED (live LCSC or computed from rows) values are listed.

## TPS1HTC30AQPWPRQ1 (LCSC C22414694): kept, at the live price (lead ruling)
- 16 parts: U47-U61, U68 (outputs_bom rows "Glow + GCB..." x15 and "E-STOP BREAKER TRIP" x1).
- Old BOM price $7.0093 -> live LCSC **$14.2804 @10+** (1+ $15.2288, 30+ $13.7038). **Stock 36** at the check, 2026-10-28 16:33 HST (also 36 at the first check in 06d1d4b).
- Delta: 16 x ($14.2804 - $7.0093) = **+$116.34**. outputs_bom TOTAL went **$165.26 -> $281.69** (commit 06d1d4b; it includes +$0.10 from the 8ffcc67 qty fixes).
- The MPN changed from TPS1HTC30QPWPRQ1 (404 at TI, not orderable) to TPS1HTC30AQPWPRQ1 (TI ACTIVE).

## Other cost-significant changes this session (from SCHEMATIC_CHANGELOG)
| change | commit | before -> after |
|---|---|---|
| H1 E-stop reverse block: 2x SQD40P10-40L C141570 (1@$1.5676 live) + R627 + D137 | 4e4c84f | outputs_bom $162.10 -> $165.26 |
| L3 -> MWSA1004S-3R3MT C408483 (price UNVERIFIED, so excluded) | 52e8028 | power_bom $46.94 -> $46.79 (the old L3 price dropped out; the real cost is unknown) |
| M5 CT clamps 8x BAV99 C2500 @ $0.0119 | d35e330 | ac_metering $45.75 -> $45.85 |
| J30 -> Phoenix 1720851 C6651769 1@$9.8499 (stock 0) | c4c54d2 | ac_metering $45.85 -> $55.70 |
| BOM reconcile qty fixes (27 rows) | 8ffcc67 | comms $28.18 -> $28.37; inputs $24.88 -> $24.65; other $407.85 -> $407.83; outputs $281.59 -> $281.69; power $46.79 -> $46.57 |
| BOM consolidation 3c | see changelog 3c-5 | see changelog 3c-5 |

Not MEASURED, so not listed with a figure: the J30 mate plug 1996184 (no LCSC listing) and the JLC extended-part fees.
