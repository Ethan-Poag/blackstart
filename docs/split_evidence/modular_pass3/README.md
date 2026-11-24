# Pass 3 evidence (Nov 23, 2026, HST)

Read-only data used for `docs/modular/tools/pass3_calc.py`, MOD §15 and the Pass 3 BOM. Nothing was ordered.

## Datasheet and curve evidence
- `pdf/ts5a3166.pdf`, `ts5a3166.txt`: TI SCDS186E. DBV pinout is 1 NO, 2 COM, 3 GND, 4 IN, 5 V+. At V+ 4.5-5.5 V, NO/COM off-leakage is ±100 nA max over -40..85 °C (-40..185 °F). IN is 5.5 V tolerant (VI 0-5.5 V). VIH is 2.4 V.
- `dcbias_curves.json`: the typical DC-bias curves taken from the Samsung product pages (the URL is recorded per part). `dcbias.py` prints `dcbias.txt` from it:
  - CL21B105KBFNNNE: -16.3 % at 12.83 V;
  - CL31B106KAHNNNE: -1.3 % at 1.5 V;
  - CL21B104KCFNNNE: -29.6 % at 32 V and -34.6 % at 36 V.
- Insulation resistance for Samsung class II parts is 10 GΩ or 500 MΩ·µF initially, and 1 GΩ or 50 MΩ·µF after the life test (Samsung reference spec sheets). The calc uses the 50 MΩ·µF floor.
- TPS1HTC30-Q1, TPS2553 (reverse-voltage FAULT 2-7 ms), TPS48100-Q1 and BSC070N10NS5 are the Pass 1 and Pass 2 copies in `../modular_pass1`.

## JLC searches and live prices
`srch.py` runs the read-only JLC part search; its outputs are `fetch/search_*.json`. `price3.py` refreshes live price and stock into `fetch/price_*.json` and `bom/lcsc_prices.csv`, with source "JLC parts API live (Pass 3)".

| LCSC | Part | Use | JLC stock | Class | Unit USD |
|---|---|---|---|---|---|
| C113804 | CC0603KRX7R0BB222 2.2 nF / 100 V | gate C1 ×9 | 133,717 | extended | 0.0065 |
| C81598 | 1N4148W | steering and BST clamp diodes ×18 | 4,363,950 | basic | 0.0123 |
| C2104 | BZT52C15 | G-S zener ×9 | 118,067 | extended | 0.0207 |
| C22935 | 1M 0603 | C1 bleed ×9 | 5,553,522 | basic | 0.0016 |
| C23179 | 470R 0603 | G1PU R1 ×9 | 3,947,825 | basic | 0.0019 |
| C28323 | CL21B105KBFNNNE 1 µF / 50 V | C_BST ×9 | 3,777,237 | basic | 0.0277 |
| C28233 | CL21B104KCFNNNE 100 nF / 100 V | MAJ-D ×17 mainboard, ×2 engine | 2,524,405 | basic | 0.0158 |
| C1621 | CL10B472KB8NNNC 4.7 nF | UVLO filters ×9 | 253,008 | extended | 0.0097 |
| C22880 | 0603WAF1582T5E 15.8k | overload filter R | 19,561 | extended | 0.0019 |
| C22920 | 0603WAF2552T5E 25.5k | ROOM resistor | 22,612 | extended | 0.0021 |
| C14860 | CL31B106KAHNNNE 10 µF / 25 V 1206 | overload filter C ×2 | 1,612,614 | extended | 0.1127 |
| C353035 | TS5A3166DBVR | ROOM switch (was AO3400A) | 5,706 | extended | 0.3769 |
| C20345924 | TLV3012BIDBVR | overload comparator, **pre-buy** | 695 | extended | 2.9022 |
| C1517405 | INA281A2IDBVR | bank current monitor | 2,381 | extended | 5.6177 |

Rejected candidates:
- 3.3 nF / 2.7 nF 100 V C1: too little BST margin (8.94 V at 3.3 nF), or the Samsung part was out of stock.
- MMSZ5245B and SMF13A clamps: BZT52C15 is already in the baseline.
- LMV331: open collector.
- TLV3012AIDBVR: only 49 in stock.
- No 15 µF or 22 µF 25 V 1206 X7R was available.
