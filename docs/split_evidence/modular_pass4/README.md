# Pass 4 evidence (Nov 23, 2026, HST)

Read-only data used for `docs/modular/tools/pass4_calc.py`, MOD §16 and the Pass 4 BOM. Nothing was ordered or pushed.

## TI TPS48100-Q1 (SLUSEW1C) and related TI sources
- The datasheet text is `../modular_pass1/tps48100-q1_SLUSEW1C.txt` (SLUSEW1C, Jan 2024, revised Jun 2026). Lines used: §5.1 abs max (VS, CS+, CS– to GND −65…100 V; SRC to GND −65…100 V; CS+ to CS– −1…100 V; no VS-to-CS or VS-to-SRC rating), §5.3 (VS ≥ 4 V for SCP; VS, SRC ≥ 22 nF; BST−SRC ≥ 0.1 µF, no maximum), §5.5 (VS POR, I(BST), BST UVLO, I(TMR)), §7.3.3.2 (latch reset), §8.3 (RVS ≈ 100 Ω with CVS). Quoted in MOD §16.1.
- `sffs636.pdf`, `sffs636_tps4810_fmea.txt`: TI SFFS636 functional-safety FMEA for the TPS4810-Q1 family. Table 4-2: CS– or SRC shorted to GND → "Short to GND protection starts".
- `e2e_1298005_tps4811_vs_series_R_1uF.txt`: TI E2E, 300 Ω in series with VS is fine with 1 µF at VS.
- `e2e_1399878_tps4811_vs_filter.txt`: TI E2E, C_VS is the VS decoupling/filter cap.
- `e2e_1621422_tps4810_scp_vg_good.txt`: TI E2E, SCP is gated by VG_GOOD (no SCP during the gate ramp).
- Not found anywhere: the SCP comparator's CS+/CS– common-mode range in high-side mode → bench test (MOD §16.7 #1).

## Linear-mode FET fallback (m1)
- `nexperia_asfet_note.txt`: Nexperia PSMN4R8-100YSE (LFPAK56E, enhanced-SOA "ASFET for hotswap", 175 °C) excerpts; the Nexperia PDFs return "Access Denied" to this box, so these are the indexed excerpts of the official pages. JLC stock 0 → consign.

## Capacitor DC bias
- The Samsung product pages returned "Server Error" for the DC-bias tool this pass. `pass4_calc.py` uses stated bounds instead: C_VS −40 % at 32 V / −15 % at 12 V, C_BST 2.2 µF −30 %, each with −10 % tolerance, −10 % temperature and −5 % aging. Bench-measure.

## JLC searches and live prices
`srch.py` runs the read-only JLC part search (`fetch/search_*.json`). `price4.py` refreshes live price and stock (`fetch/price_*.json`) into `bom/lcsc_prices.csv`, source "JLC parts API live (Pass 4)", keeping the table's row order.

| LCSC | Part | Use | JLC stock | Class | Unit USD |
|---|---|---|---|---|---|
| C50254 | CL31B225KBHNNNE 2.2 µF / 50 V 1206 | C_BST ×9 | 281,546 | basic | 0.061 |
| C13832 | CL31B105KCHNNNE 1 µF / 100 V 1206 | C_VS ×9 | 79,796 | extended | 0.0593 |
| C106246 | CC0603JRNPO9BN102 1 nF C0G 50 V | slot C_TMR ×8 | 1,347,732 | extended | 0.0054 |
| C81598 | 1N4148W | VS hold-up diode ×9 (28 total) | 4,362,644 | basic | 0.0123 |
| C22775 | 0603WAF1000T5E 100R | RVS ×9 (10 total) | 12,759,334 | basic | 0.0017 |
| C25804 | 0603WAF1002T5E 10k | R773 (59 total) | 41,793,187 | basic | 0.0017 |
| C43131316 | TPS48100QDGXRQ1 | bank + 8 slots + rail cut | **728** | extended | 3.1233 |
| C20345924 | TLV3012BIDBVR | overload comparator | **695** | extended | 2.9022 |
| C1517405 | INA281A2IDBVR | bank current monitor | 2,381 | extended | 5.6177 |
| C353035 | TS5A3166DBVR | ROOM switch | 5,706 | extended | 0.3769 |
| C534364 | BSC070N10NS5 | 27 per mainboard | 6,690 | extended | 0.4652 |
| C548409 | 74LVC1G74DP-Q100H | latches ×2 | 20,363 | extended | 0.4668 |

m7 alternatives checked (search files): TS5A3166QDCKRQ1 SC-70 only, 82 in stock; 74LVC1G66-Q100 V_IH 3.5 V at 5 V; TMUX1101 not AEC-Q100, SOT-23 stock 0.
