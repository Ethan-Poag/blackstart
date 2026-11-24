# Evidence for the Pass 2 fixes (branch m7-modular, Nov 23, 2026, HST)

Review: `/workspace/review/modular_pass2.md`. Every number in the docs comes from `docs/modular/tools/pass2_calc.py`; its output is in `docs/modular/pass2_calc.txt`.

## Datasheets (`pdf/`, text extracts `*.txt`)
| File | Part | Used for |
|---|---|---|
| `ina281.pdf` | TI INA281 (SBOSA19) | A2 gain 50 V/V, gain error, VOS, swing to VS; DBV pinout 1 OUT, 2 GND, 3 IN+, 4 IN−, 5 VS |
| `tlv3011.pdf` | TI TLV3011/TLV3012 | 1.242 V reference tolerance, VOS, hysteresis; DBV-6 pinout 1 OUT, 2 V−, 3 IN+, 4 IN−, 5 REF, 6 V+; TLV3012 push-pull; output low during power-up (≤ 1.9 ms) |
| `tlv3012b_lcsc.pdf` | TLV3012B (LCSC copy) | the B-suffix DBV ordering code C20345924 |
| `74lvc1g74_nexperia.pdf` | Nexperia 74LVC1G74-Q100 | DP (TSSOP-8) pinout 1 CP, 2 D, 3 Q̅, 4 GND, 5 Q, 6 R̅D, 7 S̅D, 8 VCC; S̅D = R̅D = L gives Q = Q̅ = H; 5.5 V tolerant inputs; Ioff |
| `sn74lvc1g74.pdf` | TI SN74LVC1G74 | cross-check of the function table |
| `irlml0100pbf.pdf` | Infineon IRLML0100 | bleeder FET: 100 V, VGS(th) 1.0–2.5 V, RDS(on) 235 mΩ at 4.5 V |
| `bsc070n10ns5.pdf` | Infineon BSC070N10NS5 | bank FET RDS(on), Qg, SOA for the bank SCP and dV/dt checks |
| `at24cs32.pdf` | Microchip AT24CS32 | ICC2 write 3 mA max at 5 V; VIH max VCC + 0.5 V (+3V3_ID 68R sizing) |

The TPS48100 (SLUSEW1C), TPS2553, TPS1HTC30 and TMUX1208 datasheets are in the Pass 1 evidence folders (`docs/split_evidence/`).

## JLC parts API responses (`fetch/`), Nov 23, 2026, HST
Read-only `selectSmtComponentList` searches on jlcpcb.com. Stock is JLC stock on the day; LCSC stock can differ.

| LCSC | MPN | Maker | Use | JLC stock | Class | Unit $ (1+) |
|---|---|---|---|---|---|---|
| C1517405 | INA281A2IDBVR | TI | U111 bank current sense | 2,381 (LCSC 1,165) | extended | 5.62 |
| C20345924 | TLV3012BIDBVR | TI | U112 overload comparator | **705 (LCSC 15)** | extended | 2.90 |
| C548409 | 74LVC1G74DP-Q100H | Nexperia | U113 overload latch | 20,363 | extended | 0.47 |
| C53658 | IRLML0100TRPBF | Infineon | Q104 bleeder FET | 21,897 | extended | 0.30 |
| C20917 | AO3400A | AOS | Q103 bleeder driver, Q108 ROOM, Q109 UVLO pull | 1,455,338 | basic | 0.08 |
| C421608 | 25121WF2201T4E 2.2k 1 W 2512 | UNI-ROYAL | R709/R710 bleeder | 35,235 | extended | 0.045 |
| C23091 | 0603WAF6192T5E 61.9k | UNI-ROYAL | R764 bank ISCP | 14,742 | extended | 0.002 |
| C31658 | CL10B683KB8NNNC 68 nF | Samsung | C413 bank C_TMR | 105,498 | extended | 0.019 |
| C22808 | 0603WAF1500T5E 150R | UNI-ROYAL | gate G1PU R (bank + 8 slots) | 1,007,857 | basic | 0.002 |
| C21122 | CL10B223KB8NNNC 22 nF | Samsung | gate dV/dt C (bank + 8 slots) | 1,093,868 | basic | 0.006 |
| C22961 | 0603WAF2203T5E 220k | UNI-ROYAL | R770 overload filter | 868,614 | basic | 0.002 |
| C29936 | CL10B105KA8NNNC 1 µF | Samsung | C416 overload filter | 3,770,892 | extended | 0.010 |
| C23031 | 0603WAF3653T5E 365k | UNI-ROYAL | R771 ROOM resistor | **4,717** | extended | 0.002 |
| C23056 | 0603WAF4422T5E 44.2k | UNI-ROYAL | R773 threshold divider | 224,728 | extended | 0.002 |
| C17976 | 1206W4F680JT5E 68R | UNI-ROYAL | +3V3_ID feed per slot | 76,314 | extended | 0.014 |

Alternates that were checked and not used:
- TLV3011BIDBVR (C20345920, 827 in stock): open-drain. That loses the push-pull POR-low fail-safe, so it needs an added pull-up and a re-check.
- INA281A2QDBVRQ1 (C2908677, $2.17): only 35 in stock.
- Other files in `fetch/` (BSS123, TLV7031, TLV3011/TLV3012 keyword searches) are the candidate searches behind these choices.

Card parts (C25804 10k 0603, C23140 33R, C21190 1k) are high-stock basic parts already priced in `bom/lcsc_prices.csv`.
