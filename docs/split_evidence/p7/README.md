# Batch 34 (P7) evidence: Q2 front-end fix ported from m7-modular

- `erc_genctl.json`, `erc_genctl_meter.json`: kicad-cli 9.0.2 `sch erc --severity-all`, 0 violations each.
- `ndiff_vs_5bac9fe.txt`: netlist diff vs m7-split 5bac9fe. 1147 → 1161 parts (14 added, none removed or changed). Net changes are only:
  - the new parts;
  - U2 EN/UVLO, R4 and R5 now on the named net BB_UVLO (was Net-(U2-EN/UVLO));
  - U5.3 EN/UVLO moved from VBAT_P to U5_EN.
- `bom_check.txt`: `tools/bom_from_sch.py` after `--write`, 0 mismatches. Main board parts $266.36 → $266.48 per board at qty 1.
- `p7_calc.txt`: `tools/p7_calc.py`, Q2 start-up model and drawn-value check. Worst Q2 SOA ratio is 0.91 across all corners (before P7: 0.97–0.99 at a 32 V hot cold start).
- Patch: `tools/p7_power_patch.py`. It edits power.kicad_sch only and is idempotent.
