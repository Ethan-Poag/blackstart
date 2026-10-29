# Spec checklist: fixes_safety.md + fixes_mechanical.md vs branch m7-sch (3b, 2026-10-28)
Status: DONE = schematic/BOM commit; DOC = declaration or firmware only, no schematic change; LAYOUT = deferred_layout.md; SKIP = not done (reason).

## fixes_safety.md, Rev 3 (governing)
| item | status | hash / reason |
|---|---|---|
| R3-1 external fuse + load-shed | DONE (label) / DOC | f03e334 (fuse label >=58 V DC); load-shed is firmware; silk label LAYOUT |
| R3-2 coil limit | DOC | declaration, no schematic content |
| R3-3 INA237AIDGSR | DONE | 0d838ea (U86 + R555 2 mOhm) |
| R3-4 H6 dividers approved | DONE | 24568d7, b171320 |
| R3-5 U69/U70 creepage exception | NO CHANGE (decision) | engineer item; slot/keep-out LAYOUT |
| R3-6 L2/L3 MWSA1004S-3R3MT C408483 | DONE | L2 already; L3 52e8028. C408483 live page dead -> price UNVERIFIED |
| R3-7(a) BZT52C36 -> BORN C511892 | SKIP | no BZT52C36 / BCP56 / VBAT_AI rail exists in the schematic (the L1/L2 36 V rail was never implemented), so no refs to change. Needs a ruling on whether to implement L1 (VBAT_AI) |
| R3-7(b) C3/C4 EEETG1J101UP C178628 | DONE | 5da6f56 |
| R3-8 H1 2x SQD40P10-40L + 10k + BZT52C15 | DONE | 4e4c84f (Q70/Q71, R627, D137; J23 on VBAT_ESTOP_IN) |
| R3-9 J30 Phoenix 1720851 | SKIP | J30 is still KF2EDGRM-5.08-8P C441294: there is no 1720851 footprint in genctl.pretty, and C6651769 has 0 stock (changelog l.283). Needs a footprint and a buy decision |
| R3 layout checklist | LAYOUT | D-m7-6 (L3), D-m7-7 (H1), D-m7-8 (BAV99), R3-5 slot |
| R3 firmware checklist | DOC | firmware |

## fixes_safety.md, Rev 2 items not superseded
| R2-1 INA238 fitted | DONE as INA237 (R3-3) | 0d838ea |
| R2-2 TPS48100 trip | DONE | d60c548 |
| R2-3 H6 1 % chains | DONE | 24568d7 |
| R2-4 S-H1 slot | NO CHANGE (U69/U70 decision) | — |
| R2-5 live codes | used per item | — |
| R2-6 J28/J29 slot ruling | LAYOUT | milled slot, deferred_layout D4 |

## fixes_safety.md, §1 fix table
| H1 | DONE | 4e4c84f (SQD40P10 per R3-8, not SUD50P06/CMD60P06) |
| H1 gate Dz | DONE | 4e4c84f D137 BZT52C15 C2104 |
| H2 shunt/RISCP/CTMR | DONE | d60c548 |
| H3 R3 8.66k | DONE | 4ccfbcf |
| H4 D1 + 17x SMBJ40CA | DONE | 278eb57 |
| H5 D126/D68/D69 SMDJ40CA | DONE | 278eb57 |
| H6 dividers | DONE | 24568d7/b171320 |
| H6 RV1-RV6 keep | NO CHANGE (spec) | footprint TMOV20RP_P7.5mm_inline in sch; PCB LAYOUT D2 |
| H7 -> S-H1 | NO CHANGE (decision) | — |
| M1 F1 removal | DONE | changelog Item 2 (pre-batch) |
| M2 TPS1HTC30 no BOM change | DOC | MPN corrected to TPS1HTC30AQPWPRQ1 in 06d1d4b (TI orderable) |
| M3 L3 | DONE | 52e8028 |
| M4 J30 keep KF2EDGRM | as-is | superseded by R3-9 (Phoenix), see SKIP above |
| M5 CT clamps 2x BAV99 | DONE | d35e330 (8 parts: the board has 4 CT channels, not 8) |
| M6 C3/C4/C5-C8/C225/C131 | DONE | 5da6f56 |
| M6 C39/C144-146/C205-219/C233 | SKIP (not needed) | C28233 is already 100 V (live LCSC); changelog B3-4 |
| L1/L2 36 V VBAT_AI rail | SKIP | not implemented; large topology change; "R130…R205" range is not enumerated. Needs a ruling |
| L2 BZT52C15 on Q2/Q3/Q36/Q39/Q42 | SKIP | spec says "confirm which ones", which is ambiguous |
| M7 shunt trip UV-release | DOC | installer declaration |
| M8 INA238 | DONE | 0d838ea |

## fixes_safety.md, §6 S-items
| S-H1 | NO CHANGE (decision) | — |
| S-M3 | DONE | d60c548 (same fix as H2) |
| S-L4 | DONE | 2e57ab7 |
| S-M2 U3 thermal | LAYOUT | deferred D5 |
| S-L1/S-L2/S-M1 (Rev 3 header refs) | DONE | 5f080c9 (S-L1), bc778a6 (S-L2 R558), 8736729 (S-M1) |

## fixes_mechanical.md
| §1 J30 Phoenix 1720851 | SKIP | see R3-9 |
| §2 RV1-6 7.5 mm footprint | DONE in sch (no change); PCB LAYOUT D2 |
| §3 mating plugs | DONE | af42672 (J30 has no Mate props; it waits on §1) |
| §4 J28/J29 gap | LAYOUT | D4 slot |
| §5 H1-H4 M4 | DONE | 9743dec (CHASSIS = C48,C87,C93,H1-H3,J10,J11,R33,R89,R94; no H4) |
| §6 CAN2 daughter board | separate board files; text corrected (N5, line 90): SW6 deleted, no on-board CAN2 termination |
| §7 BOM consistency | DONE | af42672 (1720819 C3579760; "not at LCSC" count 0); 8ffcc67 (tools/bom_from_sch.py reconcile) |
