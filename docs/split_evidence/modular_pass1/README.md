# Pass 1 fix evidence (Nov 23, 2026, HST)
Datasheet text copies (pdftotext) for every new or re-checked part, plus raw JLC parts-API search results (`search_*.json`) and the
live JLC prices used in `bom/lcsc_prices.csv` (`jlc_prices_pass1.json`, ~3:40 PM HST). LCSC stock was read from the LCSC detail API
the same afternoon (the raw pages are not kept; their values are below).

| Part | LCSC | LCSC stock | Key datasheet facts used | File |
|---|---|---|---|---|
| Nexperia 74LVC125APW,118 | C6059 | 19,935 | IOFF ±10 µA (−40…85 °C) / ±20 µA (−40…125 °C) at VCC 0 V, VI/VO 5.5 V; pinout = TI | nx125.txt |
| TI SN74LVC125A (rejected) | — | — | SCAS290T: no Ioff spec (VO max VCC+0.5 V) | sn74lvc125a.txt |
| SN74LVC1G125DBVR | C23654 | 200,230 | SCES223U, Ioff; 1 OE# 2 A 3 GND 4 Y 5 VCC | sn74lvc1g125.txt |
| SN74LVC1G07DBVR | C7829 | 33,010 | SCES296AG, Ioff, open drain; 1 NC 2 A 3 GND 4 Y 5 VCC | sn74lvc1g07.txt |
| SN74LVC1G04DBVR | C7827 | 26,950 | SCES214AF; 1 NC 2 A 3 GND 4 Y 5 VCC | sn74lvc1g04.txt |
| SN74LVC1G10DBVR | C403721 | 3,580 | SCES486F; 1 A 2 GND 3 B 4 Y 5 VCC 6 C | sn74lvc1g10.txt |
| SN74LVC1G11DBVR | C22046 | 31,550 | SCES487J; same pinout as 1G10 | sn74lvc1g11.txt |
| AO3400A | C20917 | 849,200 | VGS(th) 0.65/1.05/1.45 V, RDS(on) ≤ 48 mΩ @ 2.5 V, SOT-23 G1 S2 D3 | ao3400a.txt |
| Littelfuse SMDJ36CA | C224075 | 4,813 | VR 36 V, VBR 40.0–44.2 V @ 1 mA, VC 58.1 V @ 51.6 A (10/1000 µs), αT 0.1 %/°C | smdj.txt |
| HoJLR2512-3W-5mR-1% | C2903482 | 100,295 | 5 mΩ 3 W 2512 | search_HoJLR2512-3W-5mR.json |
| 0603WAF2432T5E 24.3k / 0603WAF1962T5E 19.6k | C23348 / C22898 | 37,000 / 7,800 | 1 % 0603 | search_*.json |
| 0805W8F1500T5E 150 Ω | C17471 | 41,900 | 125 mW 0805 | search_0805W8F1500T5E.json |
| CL21B474KBFNNNE 0.47 µF 50 V X7R | C13967 | 263,220 | 0805 | search_CL21B474KBFNNNE.json |
| TPS48100-Q1 | C43131316 | 728 | SLUSEW1C Eq 5 R_ISCP = (I_SC·R_SNS − 19 mV)/2 µA; latch-off with R across C_TMR | tps48100-q1_SLUSEW1C.txt |
| TPS1HTC30-Q1 | — | — | FAULT −1…7 V to GND (no VS reference); KCL 80/100/120 A·kΩ; KSNS 1300; V_SNSFH 3.0/3.3/3.82 V; C_IC ≥ 100 nF | tps1htc30-q1.txt |
| TPS26621 | — | — | FLT 62 V abs max to RTN, ±100 nA | tps26621.txt |
| TPS2553 | C55266 | — | SLVS841G: IN/OUT/EN/ILIM/FAULT −0.3…7 V; R_ILIM 210k → 110/130/150 mA | tps2553.txt |
| TMUX1208 | — | — | S/D −0.5…VDD+0.5 V, ±30 mA | tmux1208.txt |
| BAT54 (Diodes) | — | — | VF ≤ 240 mV @ 0.1 mA | bat54_diodes.txt |
| TCA9548A | C130026 | — | RESET tW(L) 6 ns min | tca9548a.txt |
| LM74700-Q1 | C2941042 | — | ANODE ±65 V abs max | lm74700.txt |
| AT24CS32-STUM-T | C147891 | 243 | alternates C615972 (SOIC-8, 92), C2061575 (UDFN, 228), not pin-compatible | search_AT24CS32.json |
| WingTAT DIN C96 male/female | C5173361 / C5173363 | 3,161 / 983 | 2 A per contact, 20 mΩ max, −55…+125 °C, 1000 VAC (drawing 9001D11001 R7); no derating curve | — |
