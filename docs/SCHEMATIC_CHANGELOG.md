# Schematic / BOM changelog — branch m7-sch (base 5e8f97d)

Format: ref | old | new | reason | source. Board file mechanical/pcb_v4/genctl_v4_handrouted.kicad_pcb is NOT modified on this branch (md5 49a6a6a78d3982dc24093687e5e54c0c).

## Item 1 — TPS1HTC30 exposed pad to GND
| ref | old | new | reason | source |
|---|---|---|---|---|
| U47–U61 (outputs.kicad_sch), U68 (estop.kicad_sch) pin 15 (EP) | no-connect flag, net unconnected-(Uxx-EP-Pad15) | wire + power:GND symbol (#PWR1034–#PWR1049); net GND (same as pin 1) | Thermal pad is internally shorted to ground; datasheet says tie it to board GND | TI SLVSGL4A (TPS1HTC30-Q1) p4 pin table "Thermal Pad ... Tie to IC ground externally"; p33 s9.4.2.1 "tie the thermal pad directly to the board GND copper" |
| BOARD (out of scope) | pad 15 of U47–U61/U68 has no net on the .kicad_pcb | — | Board will later need the EP pads assigned to GND plus thermal vias/copper under these pads; NOT done here (board change, out of scope) | — |

## Item 2 — F1/Keystone removal, VBAT_F→BAT_IN merge, CAN2 termination (SW6/R92/R93/C92) deletion
Schematic/BOM/doc parts re-applied from commit 9af66ad (m7-step12) and the uncommitted m7/s12 doc edits; the .kicad_pcb part of 9af66ad was NOT applied.
| ref | old | new | reason | source |
|---|---|---|---|---|
| F1 (power.kicad_sch) | Device:Fuse "10A ATO (3557-2 clips)", fp genctl:Keystone_3557-2_ATO_clips, LCSC C352820, MPN 3557-2 | deleted; replaced by a wire (69.85,82.55)-(69.85,90.17) | All fuses external (Ethan) | 9af66ad power.kicad_sch diff |
| net VBAT_F | VBAT_F (power symbols #PWR0005, #PWR0009, #PWR1030, #PWR1031, #PWR1032) | BAT_IN (J1 BAT_IN now feeds U1/Q1/C297/R1 directly) | Merge after F1 removal | 9af66ad |
| text note at J1 (power.kicad_sch, 35.56/287.02) | — | "EXT FUSE <=10 A FAST, >=32 V DC" | Installer must fit external fuse | task brief; review/hv/f1_12a.md rating as quoted in review_9af66ad.md §3.10 |
| POWER sheet note text | "J0 battery in -> 10A ATO -> SMDJ36CA ..." | "J0 battery in (BAT_IN; NO on-board fuse: installer fits an external fuse <=10 A fast-acting, >=32 V DC in the battery lead) -> SMDJ36CA ..." | stale | s12 uncommitted edit |
| C297 Note property | "CIN on VBAT_F ..." | "CIN on BAT_IN (LM74800 A/VSNS input) ..." | stale net name | s12 edit; TI SNOSD95C p23 as already cited |
| SW6, R92, R93, C92 (comms.kicad_sch) | CAN2 switchable split termination (DIP SW6 C367376, 2x62R 1206 C17971, 4.7nF C1621) | deleted (L7, D13, shield RC kept) | CAN2 has no on-board termination; Ethan's decision: loose terminator plugs in the daughter-board sockets | 9af66ad comms.kicad_sch diff |
| COMMS sheet note text | "split termination via DIP" for CAN1/CAN2 | CAN1 DIP; CAN2 no on-board termination, loose terminator plugs in daughter-board sockets | stale | s12 edit + brief |
| bom/power_bom.csv row "Input fuse holder" (3557-2, qty 2) | present | removed | F1 removed | 9af66ad |
| bom/power_bom.csv row 3 (LM74800) / row 4 (BSC070N10NS5 "at F1 10 A") / row 39 ("Input CIN on VBAT_F (C297)") | F1/VBAT_F wording | BAT_IN / "external fuse max" wording | stale (review_9af66ad §3.9) | s12 edit |
| bom/power_bom.csv TOTAL | 46.85 | 43.93 (as computed in 9af66ad) | 3557-2 pair removed | 9af66ad |
| bom/comms_bom.csv 4.7nF C1621 | qty 3 | qty 2 | C92 removed | 9af66ad |
| bom/comms_bom.csv DIP DSHP02TSGER | qty 3 "CAN1, CAN2, RS-485" | qty 2 "CAN1, RS-485" (further changed in item 3) | SW6 removed | 9af66ad |
| bom/comms_bom.csv "CAN2: split termination" 62R | qty 2 | row removed | R92/R93 removed | 9af66ad |
| docs/genctl_bom.csv, mechanical/bom.csv | F1 row; "C86,C92" 2; "R87,R88,R92,R93" 4; "SW5,SW6" 2 | F1 row removed; "C86" 1; "R87,R88" 2; "SW5" 1 | match schematic | s12 edit |
| docs/INSTALL_SAFETY.md l.15, l.44 | F1 10 A ATO / "F.Silk at J1"; "F1 → Q1 → Q2 → Q3 is a 10 A path" | no on-board fuse, external <=10 A fast >=32 V DC, schematic note at J1, silk pending board change; path J1→BAT_IN→Q1…, 10 A copper capacity NOT demonstrated for BAT_IN layout | stale (review_9af66ad §3.9/3.10) | — |
| BOARD (out of scope) | .kicad_pcb still has F1 (Keystone clips), net VBAT_F, SW6/R92/R93/C92 | — | Board must be updated later (remove F1/clips, merge VBAT_F copper into BAT_IN, delete SW6/R92/R93/C92, add EXT FUSE silk near J1). Schematic and board are out of sync until then. | — |
| bom/ac_metering_bom.csv l.15 (6x 600 V fuse) | unchanged | **DELETED in m7-sch 3b (team lead ruling 2026-10-28)** | Was an open question: bom/design_spec.md:40 says the voltage inputs use external DIN fused terminals, but nothing says to drop the line | — |

## Item 3 — SW5/SW7/SW8 termination DIP switches → solder jumpers; bias deleted
Spec: /workspace/review/cur/failsafe_latch.md Part 2 (§2.1) and Loose ends L4.
| ref | old | new | reason | source |
|---|---|---|---|---|
| SW5 (comms.kicad_sch) | DSHP02TSGER DIP2 "TERM", C367376: CAN1_HB↔CAN1_TH, CAN1_LB↔CAN1_TL | deleted | DIP → solder jumpers | failsafe_latch.md L4 |
| JP2 (new) | — | Jumper:SolderJumper_2_Open, fp genctl:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm, CAN1_HB↔CAN1_TH (R87), open by default, in_bom no | CAN1 H leg of split termination | failsafe_latch.md L4 ("two jumpers (H and L)") |
| JP3 (new) | — | same, CAN1_LB↔CAN1_TL (R88), open by default | CAN1 L leg | failsafe_latch.md L4 |
| C86, R87, R88 | unchanged | unchanged (C86 KEPT) | brief | — |
| SW7 | DSHP02TSGER "TERM/BIAS": RS485_A↔RS485_TA, RS485_B↔RS485_TB | deleted | DIP → solder jumper | failsafe_latch.md §2.1, L4 |
| JP4 (new) | — | same symbol/fp, RS485_A↔RS485_TA (R102 pin 1), open by default | RS-485 termination in series A→TA | failsafe_latch.md L4 ("one jumper, in series A → TA; TB stays hard-wired to B") |
| R102 pin 2 | net RS485_TB | net RS485_B (net RS485_TB no longer exists) | TB re-tied to B | failsafe_latch.md L4 |
| SW8 | DSHP02TSGER "BIAS": VISO↔RS485_BIASP, GND_485↔RS485_BIASN | deleted, with its VISO stub wire/junction and GND_485 symbol | "Bias: no jumper" | failsafe_latch.md L4 |
| R103, R104 | 680R 0603 C23228 (BIASP→RS485_A, BIASN→RS485_B) | deleted (nets RS485_BIASP/BIASN gone) | "Delete R103/R104" | failsafe_latch.md L4 / §2.3 |
| genctl.pretty/SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm.kicad_mod (new) | — | copy of the KiCad 9.0.2 stock Jumper.pretty footprint (/workspace/kicad-libs/kicad-footprints-9.0.2) | footprint in repo lib | brief; the /workspace/routing-lab copy is a modified variant (B-side flipped, Value "16/32", no F.Mask bridge rect), not used |
| comms.kicad_sch text | — | TERMINATION note: JP2/JP3 open by default; "Measure J6 powered off: about 60 ohm leave open, about 120 ohm bridge both"; JP4 bridge only at a bus end; no on-board bias; CAN2 loose terminator plugs | installer guidance | brief; failsafe_latch.md L4 |
| COMMS sheet note | "CAN1: split termination via DIP"; "DIP for 120R term + 680R bias" | solder jumpers JP2/JP3; JP4, no on-board bias | stale | — |
| bom/comms_bom.csv DSHP02TSGER line | qty 2 (after item 2) | removed | no DIP switches remain | schematic |
| bom/comms_bom.csv "RS-485: termination 120R" note | "via DIP switch pole 1; 680R bias pair via pole 2" | via JP4, bias deleted | stale | — |
| bom/comms_bom.csv TOTAL | 27.86 | 26.71 (−2×0.5741) | DIP line removed | arithmetic on BOM rows |
| docs/genctl_bom.csv, mechanical/bom.csv | rows SW5, SW7, SW8, "R103,R104" | removed (JP2–JP4 are in_bom no, not listed) | match schematic | schematic |
| BOARD (out of scope) | SW5/SW7/SW8, R103/R104 still on .kicad_pcb; no JP2–JP4 | — | Board must later delete them and place JP2/JP3/JP4 (windows in failsafe_latch.md L4) on F.Cu: the footprint genctl:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm is front-side, pads on F.Cu/F.Mask [corrected 3b, N6; previously wrongly said B.Cu] | — |

## Item 4: tools/design.py generator sync (no schematic change)
- design.py pnp() | lcsc C2940 | C2143 | match schematic MMBT3906 | schematic LCSC field
- design.py MPNLCSC (18 entries) | BSS84 C8545, DMN6075S C2832191, SI2309CDS C10487, AO3401A C15127, BAT54S C85099, BAT54C C37704, SM712 C29359, NUP2105L C14223, TLV9062IDR C693209, LM317MDT-TR C15622, INA281A2 C2862726, SMBJ5.0A C114063, SMAJ36CA C114047, SMBJ58CA C114034, SMDJ24A C2963997, SS110 C2847, SK1010C C2847480, SM04B-SRSS-TB C160390 | C8492, C155242, C10493, C347476, C8592, C2135, C12067, C14486, C398355, C3015165, C2908677, C78423, C10757, C114007, C362107, C2482, C3018527, C51940130 | match the single code used in the schematic | schematic LCSC fields
- design.py 1G08 | C7813 | C7666 | match schematic U SN74LVC1G08DBVR | s12 working-tree diff
- design.py F1 / VBAT_F | F1 fuse, VBAT_F net | REFC['F']+=1, BAT_IN | regen must not undo item 2 | item 2
- design.py CAN2 termination | SW6/R92/R93/C92 | refs reserved, none placed | regen must not undo item 2 | item 2
- design.py SW5 | DIP | JP2/JP3 SolderJumper_2_Open (SW ref reserved) | regen must not undo item 3 | item 3
- design.py SW7/SW8/R103/R104 | DIP term + DIP bias + 2x680R | JP4 (A->TA), R102 TA->B, refs reserved | regen must not undo item 3 | item 3
- design.py TPS1HTC30 x16 | EP NC | EP->GND | regen must not undo item 1 | item 1
- Verified MEASURED: scratch regen (/tmp/regen, LIBDIR repointed) netlist has no F1/SW5-8/R92/R93/R103/R104/C92/VBAT_F; JP2/JP3/JP4 and R102 nets match schematic; all 16 TPS1HTC30 pin 15 on GND; no C2940. EXT FUSE text near J1 is not generated by design.py (free text only).

## Fix A: comms_bom sync to schematic (BOM only)
- comms_bom C1621 (C86) | qty 2 | qty 1 | schematic has only C86 (C92 deleted m7-step12, RS-485 bias deleted m7-sch) | netlist 30e624d
- comms_bom CAN1 62R (R87/R88) | 0603WAF620JT5E C23222 0603 $0.0019 | 1206W4F620JT5E C17971 1206, price/stock UNVERIFIED | schematic R87/R88 are 1206 C17971 (review_9af66ad pre-existing note) | schematic + https://www.lcsc.com/product-detail/C17971.html (fetched 2026-10-28, MPN only)
- comms_bom RS-485 120R (R102) | 0603WAF1200T5E C22787 0603 $0.0019 | 1206W4F1200T5E C17909 1206, price/stock UNVERIFIED | schematic R102 is 1206 C17909 | schematic + https://www.lcsc.com/product-detail/C17909.html (fetched 2026-10-28, MPN only)
- comms_bom TOTAL | 26.71, 3 excluded rows | 26.69, 5 excluded rows | arithmetic above | -

## Fix B: other_bom tactile switch qty (BOM only)
- other_bom TS-1187A-B-A-B C318884 | qty 3 (RESET, BOOT0, nRPIBOOT) | qty 4 (+SW4 CM5 PWR); TOTAL 407.87 -> 407.89 | schematic has SW1-SW4 all TS-1187A C318884 | netlist 62d7793, existing line price 0.0207

## Fix C: Phoenix 1720819 header LCSC column (BOM only)
- power_bom J0 BATTERY header (sch J1) and outputs_bom J4 header (sch J23) | LCSC "none (not at LCSC)" | C3579760, price/stock UNVERIFIED (DigiKey price 7.46 kept) | schematic J1/J23/J28/J29 carry LCSC C3579760, MPN 1720819 | https://www.lcsc.com/product-detail/C3579760.html (fetched 2026-10-28: Phoenix Contact 1720819, 4P 7.62 mm, colour listed Green)

## FW-1: watchdog trip latch (FW-001 / FW-027)
**Re-arm part of this entry (ENOUT RC, R554 100k, C298 10n, U37.8 → WD_REARM_RC) is SUPERSEDED by FW-1 Rev 2 below.**
Spec: /workspace/review/schematic_audit/fixes_firmware.md §1 (option A, ENOUT RC; option B POR-RC NOT applied, pending bench check 1c). Net name for the RC node is WD_REARM_RC (brief) where the spec says WD_RC.
| ref | old | new | reason | source |
|---|---|---|---|---|
| U84 (new, outputs) | — | 74LVC1G74DP-Q100H, Nexperia, LCSC C548409, Package_SO:TSSOP-8_3x3mm_P0.65mm, symbol 74xGxx:74AUP1G74 (no 74LVC1G74 in KiCad 9.0.2 libs; same pin numbers). 1 CP=WD_REARM, 2 D=+3V3_SAFE, 3 /Q NC, 4 GND, 5 Q=WD_OK, 6 /RD=WDO_N, 7 /SD=+3V3_SAFE, 8 VCC=+3V3_SAFE | latch watchdog trip until power cycle | fixes_firmware.md §1.1/§1.2; https://www.lcsc.com/product-detail/C548409.html (fetched 2026-10-28: Nexperia 74LVC1G74DP-Q100H, TSSOP-8; price/stock not shown, spec 21071 / $0.486) |
| U85 (new, outputs) | — | SN74LVC1G17DBVR, TI, LCSC C7836, SOT-23-5; 2 A=WD_REARM_RC, 4 Y=WD_REARM, 5 +3V3_SAFE, 3 GND, 1 NC | clean CP edge from the 1 ms RC | §1.1; https://www.lcsc.com/product-detail/C7836.html (fetched: TI SN74LVC1G17DBVR SOT-23-5; price/stock not shown) |
| R554 (new) | — | 100k 0603 C25803, +3V3_SAFE → WD_REARM_RC | ENOUT open-drain pull-up, τ = 1 ms | §1.1 |
| C298 (new; spec C293) | — | 10n 0603 X7R CL10B103KB8NNNC C1589, WD_REARM_RC → GND | re-arm RC | §1.1; https://www.lcsc.com/product-detail/C1589.html (fetched: Samsung CL10B103KB8NNNC 10nF 50V X7R 0603) |
| C299, C300 (new; spec C294, C295) | — | 100n 0603 C14663, +3V3_SAFE/GND at U84, U85 | decoupling | §1.1. Renumbered: C293–C297 already exist in the schematic |
| U37 pin 8 ENOUT | no-connect flag | net WD_REARM_RC | arm source | §1.2 |
| U38.2, U39.2, U40.2, R272.1 (outputs), U67.2 (estop) | WDO_N | WD_OK | gates/OE driven by latched Q | §1.2 |
| U76 pin 18 (P15, frontpanel) | no-connect flag | WD_OK (readback) | firmware reads latch state | §1.2 (spec writes "U76.16 (P15)"; pin 16 is P13 = USB0_EN, P15 is pin 18; pin 18 used) |
| net WDO_N | U37.7, R271, R272, U38.2, U39.2, U40.2, U67.2 | U37.7, R271, U84.6 | — | §1.2 / checklist (a) |
| bom/outputs_bom.csv | — | +5 rows (U84, U85, R554, C298, C299/C300); TOTAL 159.32 → 159.97 | BOM | prices from spec §1.1, UNVERIFIED |
| docs/genctl_bom.csv, mechanical/bom.csv | — | regrouped from netlist | match schematic | netlist |
| tools/design.py | — | ENOUT=WD_REARM_RC, gates/R272/U67 on WD_OK, U76 P15=WD_OK, U84/U85/R554/C298–C300 with fixed refs | regen must not undo | — |

## FW-2: enable pull-downs (FW-002 / FW-003 / FW-004 / FW-015 / FW-028)
| ref | old | new | reason | source |
|---|---|---|---|---|
| R534, R535, R537–R548 (new, outputs) | — | 100k 0603 C25803 to GND on FUEL_EN, CRANK_EN, GLOW_EN, GCB_CL, GCB_OP, MCB_CL, MCB_OP, AUX1, AUX2, AUX4–AUX8 _MCU | enables LOW while MCU pins Hi-Z (reset/boot) | fixes_firmware.md §2 table |
| R536 (new, outputs) | — | 4.7k 0603 C23162, AUX3_MCU to GND | PB4 = NJTRST has internal pull-up at reset | §3.1 |
| R549, R550 (new, outputs) | — | 10k 0603 C25804, AUX9_MCU / AUX10_MCU to GND | TCA9555 (U76) POR = input with ~100k pull-up | §3.2 |
| R551 (new, comms) | — | 100k 0603 C25803, EXP_12V_EN to GND | PC13 → U15 IN; spec marks it "extra" beyond the 17 | §2 |
| R552, R553 (new, cm5) | — | 10k 0603 C25804, CM5_OFF / CM5_PWRBTN_MCU to GND | TCA9555 POR pull-up would hold CM5 off / power button | §3.3 |
| bom/outputs_bom.csv, comms_bom.csv, other_bom.csv | — | +3 / +1 / +1 rows (4.7k price UNVERIFIED, left out of total) | BOM | — |
| tools/design.py | — | same parts with fixed refs | regen | — |

## FW-3: CM5 boundary resistors (FW-019 / FW-012)
| ref | old | new | reason | source |
|---|---|---|---|---|
| R56 (cm5, CM5_UART_RX ↔ MCU_UART_TX) | 1k C21190 | 10k C25804 | limits PA9 injection into an unpowered CM5 to ≤0.27 mA | fixes_firmware.md §3.4, table line 592 |
| R57 (cm5, CM5_MCU_IRQ ↔ MCU_IRQ) | 1k C21190 | 10k C25804 | same, PE3 | §3.4 |
| bom/other_bom.csv | — | +1 row (2x 10k) | BOM | — |
| tools/design.py | — | 10k for the CM5_UART_RX and CM5_MCU_IRQ pairs | regen | — |

## FW-1 Rev 2: watchdog re-arm from a power-on RC (FW-001 / FW-027)
Spec: fixes_firmware.md Rev 2 §1.1/§1.2 (Ethan/Safety ruling 2026-10-28 3:34 PM HST: POR RC primary, ENOUT superseded). Arms 0.70–1.06 s after power-up (INFERRED, spec §1.3); re-arms only after a power cycle.
| ref | old | new | reason | source |
|---|---|---|---|---|
| U37 pin 8 ENOUT | WD_REARM_RC | no-connect flag | arming no longer uses ENOUT | Rev 2 §1.1 |
| net WD_REARM_RC | R554.2, C298.1, U85.2, U37.8 | renamed WD_RC = R554.2, C298.1, D136.2 (A), U85.2 | spec net name | Rev 2 §1.2 |
| R554 | 100k C25803 | 220k 0603 C22961 | τ = 220k × 4.7 µF = 1.03 s | Rev 2 §1.1 (stock/price from spec, not re-checked) |
| C298 (spec C293) | 10n C1589 | 4.7 µF 16 V X5R 0603 CL10A475KO8NNNC C19666 | POR RC | Rev 2 §1.1; DC-bias derating UNVERIFIED |
| D136 (new) | — | BAT54WS-7-F C124205, Diode_SMD:D_SOD-323, symbol Device:D_Schottky; A = WD_RC, K = +3V3_SAFE | discharges C298 into a collapsing rail | Rev 2 §1.1 |
| bom/outputs_bom.csv | — | R554/C298 rows replaced, D136 row added; TOTAL 159.98 → 160.11 | BOM | spec prices |
| tools/design.py | — | ENOUT None, WD_RC, R554 220k, C298 4.7u, D136 | regen | — |

## FW-4: TMUX1208 S-pin clamps (FW-007 / FW-014 / S-L1)
| ref | old | new | reason | source |
|---|---|---|---|---|
| D128–D131 (new, outputs) | — | BAT54C,215 Nexperia C37704 SOT-23; anodes U63 S1/S2, S3/S4, S5/S6, S7/S8 (GLOW/GCB_CL, GCB_OP/MCB_CL, MCB_OP/AUX1, AUX2/AUX3 _SNSM), cathode +3V3_SAFE | TPS1HTC30 SNS fault-high 3.82 V > TMUX1208 VS max 3.8 V | fixes_firmware.md §5; https://www.lcsc.com/product-detail/C37704.html (fetched 2026-10-28; price/stock not shown) |
| D132–D135 (new, outputs) | — | same; U64 S1/S2 … S7/S8 (AUX4/AUX5, AUX6/AUX7, AUX8/AUX9, AUX10/ESTOP_TRIP _SNSM) | same | §5 |
| bom/outputs_bom.csv | — | +1 row (8x, $0.015 from spec) | BOM | — |
| tools/design.py | — | D128–D135 pairs from the mux lists | regen | — |

## FW-5: CAN isolator VISO capacitance (FW-008, APPROVED/CLOSED by Safety + Reviewer 2026-10-28 ~3:34 PM HST)
| ref | old | new | reason | source |
|---|---|---|---|---|
| C85 (U13 VISO, comms) | 10u 0805 C15850 | 47u 10 V X5R 1206 Samsung CL31A476MPHNNNE C96123 | CA-IS3062W p15 recommends 47 µF on VISO | fixes_firmware.md Rev 2 §6; https://www.lcsc.com/product-detail/C96123.html (fetched 2026-10-28; price/stock not shown) |
| C91 (U14 VISO, comms) | 10u 0805 C15850 | same | same | same |
| bom/comms_bom.csv | — | +1 row (2x $0.17 from spec); TOTAL 26.69 → 27.03 | BOM | — |
| tools/design.py | — | VISO bulk 47u 1206 | regen | — |
Footprint grows 0805 → 1206: the PCB is not changed in this branch; layout must follow.

## FW-6: 32.768 kHz LSE drive margin (FW-013)
| ref | old | new | reason | source |
|---|---|---|---|---|
| Y2 (mcu) | X321532768KGD2SI YXC C620155, CL 12.5 pF | SC-32S32.768kHz20PPM7pF, C97604, CL 7 pF, same 3215 footprint | lower gm_crit for STM32H7 LSE | fixes_firmware.md §9; https://www.lcsc.com/product-detail/C97604.html (fetched 2026-10-28: manufacturer Seiko, 7 pF, -40..+85 °C; spec says "YXC"; price/stock not shown) |
| C63, C64 (mcu, LSE load) | 18p 0402 C1549 | 6.8p C0G 0603 FH 0603CG6R8C500NT C1679 | CL_eff 6.4–8.4 pF (INFERRED) | §9; https://www.lcsc.com/product-detail/C1679.html (fetched) |
| bom/other_bom.csv | — | LSE row replaced (price UNVERIFIED, removed from total 407.89 → 407.65), +1 load-cap row | BOM | — |
| tools/design.py | — | Y2 / LSE caps | regen | — |
Crystal ESR still UNVERIFIED (spec §9: gain margin 2.8 < AN2867's 5). Footprint 0402 → 0603 for C63/C64; PCB not changed here.

## FW-7: ADE9000 U72 CLKIN buffer (S-M1) and BUS_VA_P net name (§14)
| ref | old | new | reason | source |
|---|---|---|---|---|
| U87 (new, ac_metering) | — | SN74LVC1GU04DBVR TI C81934, SOT-23-5, on +3V3_AC / GND_AC; 2 A = ADE_XO_AC, 4 Y = ADE_CLK_Y | ADE9000 p11: buffer CLKOUT when driving external circuits | fixes_firmware.md §11; https://www.lcsc.com/product-detail/C81934.html (fetched 2026-10-28) |
| C301 (new; spec C297) | — | 100 pF C0G 0603 CL10C101JB8NNNC C14858, ADE_XO → ADE_XO_AC | AC coupling | §11. Renumbered: C297 already exists (power) |
| R556 (new) | — | 1M 0603 C22935, ADE_CLK_Y ↔ ADE_XO_AC | self-bias | §11 |
| R557 (new) | — | 33 Ω 0603 0603WAF330JT5E C23140, ADE_CLK_Y → ADE_CLK_BUF | series R | §11; LCSC page fetched |
| C302 (new; spec C298) | — | 100n 0603 C14663, +3V3_AC/GND_AC at U87 | decoupling | §11. Renumbered: C298 is the watchdog cap |
| U72 pin 29 CLKIN | ADE_XO | ADE_CLK_BUF | removed from the crystal node | §11 |
| U72 pin 20 VAP | Net-(U72-VAP) (R453.2, C265.1) | BUS_VA_P | consistent naming (net-only) | §14 |
| bom/ac_metering_bom.csv | — | +5 rows (only U87 priced; this file has no TOTAL row) | BOM | — |
| tools/design.py | — | U87 block; BUS CLKIN = ADE_CLK_BUF. CORRECTED in batch 4 (reviewer R3-N7): design.py does NOT contain BUS_VA_P (grep count 0); the U72 VAP net name exists only in the schematic, which is the source of truth | regen | — |

## FW-8: Rev 3 part choices for the watchdog cap and VISO caps (fixes_firmware.md §18.3/§18.4)
Ref mapping: spec "C293" = real **C298** (schematic C293 is an existing LM5176 22 µF COUT and is not touched). PCB footprint change deferred (deferred_layout.md D6).
| ref | old | new | reason | source |
|---|---|---|---|---|
| C298 (spec C293, outputs) | 4.7 µF 16 V X5R 0603 CL10A475KO8NNNC C19666 | 4.7 µF 25 V X7R 1206 CL31B475KAHNNNE C1872 | X7R for > 85 °C, less DC-bias loss | §18.3 (recommended), parent ruling 2026-10-28 3:46 PM HST; stock 101175 per §18.4 |
| C85, C91 (comms, U13/U14 VISO, verified in netlist) | 47 µF 10 V X5R 1206 C96123 | 47 µF 16 V X5R 1210 CL32A476KOJNNNE C2932477 | 10 V part at 47–55 % of rating | §18.3/§18.4 (stock 66634); parent ruling |
| bom/outputs_bom.csv, comms_bom.csv | — | rows updated; prices not in spec → UNVERIFIED, removed from totals (160.23 → 160.21; 27.03 → 26.69) | BOM | — |
| tools/design.py | — | pkg 1206 / 1210 + LCSC | regen | — |

## FW-9: INA281 gain 20 (FW-010 / FW-011, APPROVED)
| ref | old | new | reason | source |
|---|---|---|---|---|
| U44 (FUEL_ISNS), U46 (CRANK_ISNS), outputs | INA281A2 (50 V/V) INA281A2QDBVRQ1 C2908677, symbol Amplifier_Current:INA281A2 | INA281A1 (20 V/V) INA281A1QDBVRQ1 C2862615, symbol Amplifier_Current:INA281A1 (same pins/footprint) | keeps the 3.86–6.14 A trip band linear with the 20 mΩ shunt | fixes_firmware.md §10.2, §18.1 (gain 20 V/V from TI SBOSA29A p.4), parent ruling "value field must read INA281A1" (§18.1 had said to only flag it) |
| bom/outputs_bom.csv | 2x 2.3975 | 2x 2.92 (spec, stock 2092); TOTAL 160.21 → 161.25 | BOM | §10.2 |
| tools/design.py | — | INA281A1 + LCSC map | regen | — |
Dependency: the 0.40 V/A scaling needs R297/R303 = 20 mΩ (Safety batch 3; still 1 mΩ in this branch).

## FW-10: CM5 EEPROM write-protect (S-L2, Rev 2: fitted)
| ref | old | new | reason | source |
|---|---|---|---|---|
| U9 pin 20 EEPROM_nWP (cm5) | no-connect flag (internal 100k pull-up) | net CM5_EEPROM_NWP | hold EEPROM write-protected | fixes_firmware.md Rev 2 §12; CM5 datasheet §2.12.2, §3.1 (quoted in spec) |
| R558 (new, cm5) | — | 0 Ω 0603 0603WAF0000T5E C21189, CM5_EEPROM_NWP → GND, FITTED | same; lift for bench update | §12, parent update 2026-10-28 3:42 PM HST |
| bom/other_bom.csv | — | +1 row (price UNVERIFIED) | BOM | — |
| tools/design.py | — | EEPROM_nWP net + R558 | regen | — |
Software WP must also be set in the CM5 image (spec, UNVERIFIED).

## FW-11: LM5176 BIAS and ISNS (FW-009, APPROVED/CLOSED 2026-10-28 ~3:34 PM HST)
| ref | old | new | reason | source |
|---|---|---|---|---|
| U2 pin 24 BIAS (power) | no-connect flag (unconnected) | +12V | VBIAS > 8 V supplies VCC (lm5176 p4) | fixes_firmware.md §7, parent ruling "BIAS to +12V with 0.1 µF". NOTE: §7 says a.net already had BIAS = +12V; this schematic had it unconnected (MEASURED, 7f2a8df netlist) |
| U2 pins 13 ISNS−, 14 ISNS+ | +12V | GND (the board has one ground net; U2.10 AGND is on GND) | lm5176 p17: disable the average-current loop by shorting ISNS± to AGND | §7 |
| C303 (new; spec C299) | — | 100 nF 50 V X7R 0603 C14663, +12V → GND at U2.24 | lm5176 p30 | §7. Renumbered: C299 is the U84 decoupling cap |
| bom/power_bom.csv | — | +1 row (price UNVERIFIED) | BOM | — |
| tools/design.py | — | BIAS +12V, ISNS± GND, C303 | regen | — |

## B3-1: external battery fuse voltage rating >=58 V DC (Reviewer N1)
Spec: fixes_safety.md Revision 3, "Changes" item 1 and R3-1 (label text); reviewer.md N1. Board/fuse current stays 10 A (15 A NOT approved; Rev 2 15 A item superseded).
| ref | old | new | reason | source |
|---|---|---|---|---|
| power.kicad_sch text at J1 (35.56/287.02) | "EXT FUSE <=10 A FAST, >=32 V DC" | "EXT FUSE <=10 A FAST, >=58 V DC" | fuse must withstand the declared <=58 V suppressed load dump | fixes_safety.md R3-1 |
| power.kicad_sch POWER sheet note | "... >=32 V DC in the battery lead" | "... >=58 V DC in the battery lead" | same | R3-1 |
| tools/design.py POWER note | same | same | regen | — |
| docs/INSTALL_SAFETY.md l.15, l.44 | ">=32 V DC" | ">=58 V DC" + voltage-requirement sentence (32 V DC blade fuse does not meet it; 10 A unchanged) | installer doc | R3-1, §0 |
| bom/power_bom.csv row 4 (BSC070N10NS5) note | "at 10 A (external fuse max;" | "... 10 A FAST rated >=58 V DC per fixes_safety.md Rev 3 R3-1;" | BOM note | R3-1 |
Not changed (open question, see report): INSTALL_SAFETY.md output-fuse table (l.32–34, l.41) still says 32 V DC blade fuses for FUEL/CRANK/GLOW; fixes_safety.md l.12 says external fuses DC-rated >=58 V, but item A/R3-1 covers only the battery-lead fuse.

## B3-2: R3 LM7480 OV divider 9.76k -> 8.66k (Safety H3)
| ref | old | new | reason | source |
|---|---|---|---|---|
| R3 (power) | 9.76k 0603WAF9761T5E C23128 | 8.66k 1 % 0603 0603WAF8661T5E C23114 (LIVE LCSC 2026-10-28 ~3:55 PM HST: UNI-ROYAL, stock 10800) | OV trip 36.36/38.17/40.11 V so the board runs at 36 V | fixes_safety.md §1 H3, R2-5 (code), Notes "LM7480 OV" |
| POWER sheet note + design.py note | OV 34.0/31.2 V, UV 5.56/5.12 V (9.76k) | OV 38.17 V rise typ (36.36–40.11 V spec), 35.04 V fall typ, UV 5.65/5.18 V | INFERRED arithmetic: ratio (210+49.9+8.66)/8.66 = 31.01; 1.231×31.01 = 38.17; 1.13×31.01 = 35.04; UV 1.231×268.56/58.56 = 5.65, 1.13×4.586 = 5.18 | spec equation H3 notes |
| bom/power_bom.csv row 3 note | — | Rev 3 prefix (new R3, OV, old figures superseded) | BOM | — |

## B3-3: TVS uprate SMBJ33CA/SMDJ36CA -> SMBJ40CA/SMDJ40CA (Safety H4/H5)
| ref | old | new | reason | source |
|---|---|---|---|---|
| D2, D74, D76, D78, D80, D82, D84, D86, D88, D90, D92, D94, D96, D98, D100, D102, D123 (17) | SMBJ33CA C78420 D_SMB | SMBJ40CA MDD C114004 D_SMB (LIVE LCSC 2026-10-28: stock 41590, $0.056 @10) | OV trip now 36.4–40.1 V; SMBJ40CA cold VBR min 41.5 V stays off in normal running | fixes_safety.md H4 table l.448 |
| D1 | SMDJ36CA C224075 D_SMC | SMDJ40CA Littelfuse C224077 D_SMC (LIVE: stock 1990, $0.2803 @5) | same | fixes_safety.md H4 l.447 |
| D68, D69, D126 | SMBJ33CA C78420 D_SMB | SMDJ40CA C224077 **D_SMC** | 3 kW on the VBAT_ESTOP side (no OV cut-off) | fixes_safety.md H5 l.449. Spec says "on VBAT_ESTOP"; MEASURED nets: D126 = VBAT_ESTOP, D69 = CRANK_OUT, D68 = Net-(D68-A1) (FUEL clamp side). Refs are explicit so applied as listed |
| POWER sheet note, design.py | "-> SMDJ36CA ->" | "-> SMDJ40CA ->" | doc sync | — |
PCB: D68/D69/D126 footprint SMB -> SMC, see deferred_layout.md D9. outputs_bom/power_bom TOTAL lines updated by delta.

## B3-4: VBAT_P-side capacitor voltage uprate (Safety R3-7(b), M6)
| ref | old | new | reason | source |
|---|---|---|---|---|
| C3, C4 | 100u 50V EEHZA1H101P C109086 | 100u 63V Panasonic EEETG1J101UP C178628 (LIVE LCSC 2026-10-28: stock 3323, $0.7511 @1); footprint CP_Elec_10x10.5 kept | 40.1 V OV max on 50 V part | fixes_safety.md l.30, l.170. Land match INFERRED (D10); ESR 0.8 Ω vs 28 mΩ polymer, ripple to re-check |
| C5, C6, C7, C8, C225 | 10u 1210 CL32B106KBJNNNE C138687 (50 V) | Murata GRM32EC72A106KE05L C576517 10u 100V X7S 1210 (LIVE: stock 6144, $0.5403 @1) | M6 | fixes_safety.md l.463 |
| C131 | 100n 0603 C14663 (50 V) | Samsung CL10B104KC8NNNC C15725 100 V 0603 (LIVE: 335750, $0.0134 @50) | M6 | l.465 |
| C39, C144–C146, C205–C219, C233 (19) | — | **NOT CHANGED** | Spec row l.466 says these are "100 nF 50 V 0805 (C28233)", but LIVE LCSC shows C28233 = Samsung CL21B104KCFNNNE **100 V** X7R 0805 (stock 27450), so they are already 100 V. Skipped; reported | live LCSC |
power_bom row 7 qty 6 -> 5 (netlist count). inputs_bom C14663 row 32 -> 31 + new C131 row.

## B3-5: USB TPS2553 RILIM 40.2k -> 49.9k (Safety S-L4)
| ref | old | new | reason | source |
|---|---|---|---|---|
| R109 (U18 ILIM), R111 (U19 ILIM) | 40.2k 0603 C12447 | 49.9k 1 % 0603 0603WAF4992T5E C23184 (LIVE LCSC 2026-10-28: stock 1,310,800, $0.0029 @100) | limit ≈0.52 A typ instead of ≈0.70 A max; still ≥ 500 mA USB 2.0 | fixes_safety.md l.537, l.573 |
Ref mapping: spec "U18/U19 RILIM" = R109/R111 (MEASURED: Net-(U18-ILIM) = R109.1+U18.5, Net-(U19-ILIM) = R111.1+U19.5). Same footprint; no layout change.

## B3-6: H6 AC voltage dividers 4 x 1M -> 12 x 330k per leg (Safety H6, R2-3) — schematic/design.py in 24568d7, BOM/doc in the next commit
| ref | old | new | reason | source |
|---|---|---|---|---|
| R422–R425, R429–R432, R436–R439, R443–R446, R448–R451, R455–R458, R462–R465, R469–R472 (32) | 1M 1206 C17927 | 330k 1 % 1206 UNI-ROYAL 1206W4F3303T5E C17929 (LIVE LCSC 2026-10-28: stock 401,700, $0.0046 @100) | 12 × 330k = 3.96 MΩ/leg; per-part ≤ 55 Vrms steady, ≈207 V pulse < 400 V overload (spec, INFERRED) | fixes_safety.md l.24, l.121, R2-3 l.316 |
| new R559–R566 (GEN_L1), R567–R574 (GEN_L2), R575–R582 (GEN_L3), R583–R590 (GEN_N), R591–R598 (BUS_L1), R599–R606 (BUS_L2), R607–R614 (BUS_L3), R615–R622 (BUS_N) (64) | — | 330k C17929, chained <leg> → <leg>_C1 … <leg>_C8 → old first resistor (R422 etc., pin-1 label renamed <leg> → <leg>_C8) | 8 added links per leg | same |
Refs: next free after R558 (R555 kept for the INA237 shunt). Ratio change −1 % (calibration). ac_metering_bom row 6 replaced (old row stale: 24 × HVC1206). Layout D11.

## B3-7: battery current monitor U86 INA237 + R555 2 mΩ shunt (FW-006, Safety R2-1/R3-3)
| ref | old | new | reason | source |
|---|---|---|---|---|
| Q2 pins 1-3 (S) | VBAT_P | **VBAT_PS** (new net; global label at Q2 S renamed) | shunt in series with Q2 source | fixes_firmware.md §4.1 |
| R555 (new; spec ref R555) | — | 2m 2512 Bourns CSS2H-2512K-2L00F C2093761 (LIVE LCSC 2026-10-28: stock 2590, $0.801 @1), VBAT_PS → VBAT_P | full VBAT_P input current sense | §4.1, R2-1 |
| U86 (new; spec ref U86) | — | INA237AIDGSR C2864837 (LIVE: 7325, $1.8659 @1), Sensor_Energy:INA237, VSSOP-10. IN+ (10)=INA_INP, IN− (9)=INA_INN, VBUS (8)=VBAT_P, VS=+3V3_SAFE, A0=A1=GND (0x40), SDA/SCL=I2C1_SDA/I2C1_SCL, ALERT (3)=OUT_FAULT_N (R44 10k to +3V3_SAFE exists) | load-shed measurement | §4.1, R3-3 (INA238 C2868250 preferred, stock 0) |
| R623, R624 (new) | — | 10R 0603 C22859: VBAT_PS→INA_INP, VBAT_P→INA_INN | 10 Ω input filter | R2-1 "10 Ω + 100 nF"; part code is repo-standard (spec gives none) |
| C305 (new) | — | 100n 0603 C14663 INA_INP–INA_INN | differential filter | same |
| C304 (new; **spec C296**, which is taken by a +12V cap) | — | 100n 0603 C14663 +3V3_SAFE–GND | VS decoupling | §4.1 |
Ref mapping: spec C296 → C304; filter parts have no spec refs → R623, R624, C305. I2C1 pull-ups 2.2k to +3V3 already exist (design.py:155). Layout D12.

## B3-8: TPS48100 fuel/crank short-circuit trip (Safety H2, FW-010/011)
| ref | old | new | reason | source |
|---|---|---|---|---|
| R297, R303 | 1m WSLP25121L000FEA C844705 | 20m 1 % 2 W 2512 PSA FMF25FPJR020-LH C105360 (LIVE LCSC 2026-10-28: 42,340, $0.0662 @10) | ISC 90 A → 4.97 A typ | fixes_safety.md l.452, l.519; fixes_firmware.md l.489 |
| R294, R300 | 35.7k C23027 | 40.2k 0603WAF4022T5E C12447 (LIVE: 52,400) | V(SCP) 99.4 mV typ | l.453, l.518 |
| C197, C201 | 68n C5137586 | 4.7n CC0603KRX7R9BB472 C106218 (LIVE: 2,377,600) | tSC ≈ 65 µs (INFERRED) | l.454, l.527 |
INA281A1 gain 20 V/V × 20 mΩ = 0.40 V/A (INFERRED arithmetic; U44/U46 value already INA281A1). Same footprints; no layout change.

## B3-9: mounting holes M3 -> M4; H4 off CHASSIS (fixes_mechanical.md §5)
| ref | old | new | reason | source |
|---|---|---|---|---|
| H1, H2, H3 | MountingHole_3.2mm_M3_Pad, pin 1 CHASSIS | MountingHole:MountingHole_4.3mm_M4_Pad, pin 1 CHASSIS | PCB and enclosure use M4 (MEASURED by mech reviewer) | fixes_mechanical.md §5 l.80-84 |
| H4 | Mechanical:MountingHole_Pad 3.2mm M3 Pad on CHASSIS | Mechanical:MountingHole (0-pin) MountingHole:MountingHole_4.3mm_M4; CHASSIS label + wire removed | 4.3 mm NPTH PE-boss clearance, no pad | same |
design.py: H1-H3 loop range(3), H4 separate 0-pin symbol; footprint map updated. PCB: already deferred as D3 (H4) in deferred_layout.md; H1-H3 PCB pads are already 4.3 mm per spec (MEASURED by mech).

## B3-10: connector sourcing and mating-plug properties (fixes_mechanical.md §3, §7; fixes_mates.csv)
| ref | old | new | reason | source |
|---|---|---|---|---|
| J4, J12, J13 | SM04B-SRSS-TB C51940130 (XY clone; design.py CONNFP had C160390 = BM04B vertical, wrong) | JST SM04B-SRSS-TB(LF)(SN) C160404 (LIVE LCSC 2026-10-28: 59,830, $0.2168 @5) | footprint is the horizontal SM04B; genuine part | §3 N2 l.57-62 |
| J1, J23, J28, J29 | — | Mate_MPN "SPC 5/4-STF-7,62 (1996142)", Mate_LCSC C5481482 (LIVE: stock 100, $6.789 @1), Mate_Qty 1 | plug in BOM | fixes_mates.csv |
| J6 / J7 / J8 / J9 | — | Mate WJ15EDGK-3.81-04P C7244 / -06P C7247 / -02P C8466 / -03P C8413, qty 1 | same | fixes_mates.csv (header MPNs match schematic, MEASURED) |
| J17–J22, J24–J27 | — | Mate KF2EDGKNM-5.08-6P C2974985, qty 1 (screw plug) | same | fixes_mates.csv |
| J30 | KF2EDGRM-5.08-8P C441294 | **NOT CHANGED; no Mate props** | spec header is Phoenix 1720851 (C6651769, stock 0) but genctl.pretty has no 1720851 footprint; header/plug decision held | §1 |
tools/design.py: MATES dict keyed by header MPN sets pt.extra; tools/gen.py fields_xml emits pt.extra as hidden props. power_bom/outputs_bom 1720819 rows: LCSC column now C3579760 (LIVE: stock 49, $5.5261 @1; row price kept at DigiKey $7.46); plug rows LCSC C5481482. "not at LCSC": 0 hits (MEASURED). SW1–SW4 qty already 4; SW5–SW8 no longer exist in the netlist (MEASURED), so the comms qty fix does not apply.

## R2-N1: WD_OK series resistor to U76 P15 (team lead ruling 2026-10-28; overrides the earlier "do not touch WD_OK pin 18")
| ref | old | new | reason | source |
|---|---|---|---|---|
| U76.18 (P15) | on WD_OK | on new net WD_OK_MCU | TCA9555 P15 powers up as input, but a firmware/POR fault driving it as output would fight the WD_OK latch output | reviewer.md R2-N1 |
| R625 (new; next free R) | — | 10k 0603 1% RC0603FR-0710KL C98220 (YAGEO), WD_OK → WD_OK_MCU | series isolation; gates U38/U39/U40/U67, R272, U84.5 stay on WD_OK (MEASURED from netlist) | LIVE LCSC 2026-10-28: stock 3,801,900, $0.0027 @100 |
design.py: U76 P15 → WD_OK_MCU, R625 added with fixed ref.

## R2-N2: output EN pull-downs 100k -> 47k (team lead ruling 2026-10-28)
| ref | old | new | reason | source |
|---|---|---|---|---|
| R277–R291 (GLOW, GCB_CL/OP, MCB_CL/OP, AUX1–AUX10 _EN; MEASURED from netlist) | 100k C25803 | 47k 0603 1% 0603WAF4702T5E C25819 (LIVE LCSC 2026-10-28: stock 609,800, $0.0020 @100) | stiffer default-off on TPS1HTC30 EN | reviewer.md R2-N2 |
| R549 / R550 (AUX9/AUX10_MCU) | 10k | unchanged | ruling | — |
FUEL_EN/CRANK_EN pull-downs stay 100k (not in the ruled list). outputs_bom row 24 qty 36 → 21, row 32 qty 1 → 16.

## R2-N5 / steering: 10k 0603 C25804 out of stock -> C98220 (all parts)
| ref | old | new | reason | source |
|---|---|---|---|---|
| all 77 10k 0603 parts that carried C25804 (incl. R56/R57, R549/R550, R552/R553, R274, readback bottoms, FB/MUX dividers; list = netlist val:10k + LCSC C25804 at f8d92af, MEASURED) | 0603WAF1002T5E C25804 (UNI-ROYAL) | RC0603FR-0710KL C98220 (YAGEO), same 0603 1% 100 mW | C25804 LIVE LCSC 2026-10-28: stock **0** | LIVE LCSC 2026-10-28: C98220 stock 3,801,900, $0.0027 @100 |
Spec note: steering called C25804 "0402"; LCSC lists it as 0603 (MEASURED), and all affected footprints are R_0603_1608Metric, so the 0603 replacement is the same package. 10k 1206 C17902 and 0.1% 10k (PREC) parts are untouched. design.py/gen.py RLCSC and explicit lcsc= entries updated.

## Correction (team lead 2026-10-28) + fixes_firmware.md Rev 4: R625 4.7k, R626 WDI pull-down
| ref | old | new | reason | source |
|---|---|---|---|---|
| R625 (spec R559; R559 already used by the H6 divider chain, so next free ref kept) | 10k C98220 | 4.7k 0603 1% 0603WAF4701T5E C23162 (LIVE: stock 3,664,500, $0.0028 @100) | 10k: 0.1 mA × 10k + 0.1 V = 1.10 V > 0.99 V VIL (fails); 4.7k → 0.67 V | fixes_firmware.md §19.1 (TI SCPS200E IIL/VIL, MEASURED there) |
| R626 (new; spec R560 taken) | — | 100k 0603 1% C25803 WDI → GND (LIVE: stock 8,411,500, $0.0031 @100) | WDI (U7.71 PA12 → U37.6) had no pull; floats in reset/bootloader | fixes_firmware.md §19.4 |
| U2.24 BIAS | +12V + C303 (batch 2) | unchanged, re-checked in the netlist | spec C299 = real C303 | §19.2 |
Rev 3 approvals and Rev 4 items checked: see report.

## Steering (3): BAT54C one LCSC code per part number
| ref | old | new | reason | source |
|---|---|---|---|---|
| outputs_bom row 41 (D121) | LCSC C19190 (= GATEMODE YD3082EESA, RS-485 IC; wrong code, MEASURED live) | C2135 (JSCJ BAT54C), matching schematic D121 | code error | LIVE LCSC 2026-10-28: C2135 stock 212,020, $0.0248 @20 |
| comms_bom row 48 | qty 1 (D8 uncounted) | qty 2 (D7 + D8), $0.0248 live | qty matches schematic | netlist |
Mapping now: BAT54C (JSCJ) → C2135 on D7, D8, D121; BAT54C,215 (Nexperia) → C37704 on D128–D135 (LIVE: 137,400, $0.0156 @50). Schematic, docs/genctl_bom.csv and design.py (MPNLCSC BAT54C→C2135, D128–D135 explicit C37704) already agreed; no codes swapped.

## R2-N3 / steering (4): category BOM TOTALs recomputed exactly from rows
TOTAL = round(sum(qty × unit price), 2) over rows with a numeric qty and price; rows priced UNVERIFIED/ESTIMATE/blank are excluded and named in the TOTAL label.
| BOM | old TOTAL | new TOTAL | excluded rows |
|---|---|---|---|
| power_bom | 46.94 | 46.94 | 1 (C303, price UNVERIFIED; label no longer claims 0 unpriced) |
| outputs_bom | 162.10 | 162.10 | 2 |
| inputs_bom | 24.87 | 24.88 | 0 |
| comms_bom | 27.07 | 28.18 | 7 (old running total had drifted by $1.11 through incremental edits) |
| other_bom | 407.83 | 407.85 | 7 (incl. 4 ESTIMATE fab/assembly/enclosure/bezel rows) |
| ac_metering_bom | none | 45.75 (new TOTAL row) | 20 |
Also fixed outputs_bom row 22: an unquoted comma in "(U38-U40, U67)" had shifted every column (qty read as text).

### m7-sch: design.py/gen.py regen consistency (R2-N3/N5/N7)
| ref | old | new | reason | source |
|---|---|---|---|---|
| R559-R622 (design.py H6 loop) | auto-numbered (collided with fixed R531-R558 → duplicate refs on regen) | fixed refs R559+(chain*8+j), order GEN L1,L2,L3,N then BUS L1,L2,L3,N | regen must reproduce the committed refs | scratch regen /workspace/m7regen |
| D2,D68,D69,D74-D98(even),D100,D102,D123,D126 (tvs()) | mfr blank in generator | MDD / Littelfuse per MPN | match committed schematic | Rev 3 H4/H5 commits |
| C304,C305 | no MPN in generator | CC0603KRX7R9BB104 / YAGEO | match schematic | BIAS/INA commits |
| C131 | mfr 'Samsung' | 'Samsung Electro-Mechanics' | match schematic | — |
| J4,J12,J13 | gen.py LCSC table (reads /workspace/genctl/*.csv in the main checkout) gives C51940130 | forced C160404 / JST SM04B-SRSS-TB(LF)(SN) | match af42672 | — |

Regen proof (INFERRED from scratch netlist compare, kicadxml, ref-based): all diffs left after this change are also in the 187984d baseline regen: 110 connectivity diffs from the generator's capacitor auto-numbering drift starting at C200 (regen is off by one ref from the committed schematic), duplicate U25-U28/U32-U35, and 2-pin nets left unnamed ('~'/Net-(...)) by the generator (name-only). This drift was there before this branch and is NOT fixed here. Open issue: gen.py builds its LCSC lookup from the main-checkout CSVs (/workspace/genctl/*.csv), not from this repo's bom/.

### m7-sch: spec-error notes (no schematic change)
- fixes_firmware.md :91 and :611 say U76.16; the WD_OK_MCU net actually lands on U76 pin 18 (R625 → U76.18, netlist-confirmed). The spec pin number is wrong.
- fixes_firmware.md :439: BIAS (U2.24) was unconnected at 7f2a8df; the current schematic has +12V with C303 (netlist-confirmed, not redone).
- Spec refs R559/R560 were already used by the H6 divider chain, so the parts are R625 (4.7k WD_OK series) and R626 (100k WDI pull-down).

### 3b-a: DO-NOT-REGENERATE headers (team lead decision; no schematic change)
- tools/design.py and tools/gen.py get a header: the schematic is the source of truth and regen drifts (C200 numbering, unnamed 2-pin nets, external LCSC table).
- The U25-U28/U32-U35 duplicate refs reported earlier were a false positive. They are multi-unit symbols; (ref, unit) is unique in the committed schematic (1319 instances) and in the regen. The netlist has 1291 comps and 0 duplicate refs. ERC e75218d: 0 violations, none of type duplicate_reference.
- Generator fix: deferred, GEN-1 in deferred_layout.md.

### 3b-5: ac_metering_bom.csv "Fuse per V input" row deleted (team lead ruling 2026-10-28)
| ref | old | new | reason | source |
|---|---|---|---|---|
| bom/ac_metering_bom.csv l.15 | 6x 0685H0500-01 / 0215.500 600 VAC fuse, UNVERIFIED price | row deleted | the six metering fuses were never on the board; the voltage inputs use external DIN fuses (design.py J28/J29 note, bom/design_spec.md:40) | team lead ruling |
- Scrubbed: the TOTAL excluded list (20 -> 19 rows; the total stays $45.75 because the row was unpriced) and the changelog l.31 open question (now marked DELETED). No other text references found (git grep 0685H/0215.500/"Fuse per V"). The binary PDF/PNG hits are byte coincidences; pdftotext shows no fuse text.

### 3b-3: L3 (+3V3 TPS56637 buck) -> Sunlord MWSA1004S-3R3MT C408483 (fixes_safety.md M3, R3-6)
| ref | old | new | reason | source |
|---|---|---|---|---|
| L3 | 2.2u MWSA0503S-2R2MT C408408, genctl:L_MWSA0503S | 3.3u MWSA1004S-3R3MT C408483 Sunlord, genctl:L_MWSA1004S (same as L2) | Isat 5.6 A < IOCL 8.6 A max; R3-6 confirms that C408483 IS the MWSA1004S | fixes_safety.md M3 l.460, R3-6 l.157-161, Rev 3 change 6 |
- C408483 stock/price are UNVERIFIED because the LCSC page is 404 (a live scrape this turn returned an unrelated recommended part). The power_bom L3 row is excluded from the TOTAL (6.94 -> $46.79, the old $0.1547 row is gone). L2's existing $0.2691 is also unverified (not changed).
- Spec M3: check TPS56637 loop stability with 3.3 uH (internal compensation, UNVERIFIED). PCB: D-m7-6.

### 3b-1: E-stop feed reverse-polarity block, H1 (fixes_safety.md H1 l.450, R3-8 l.175-189, Rev 3 change 8)
| ref | old | new | reason | source |
|---|---|---|---|---|
| J23.1/J23.2 | net VBAT_ESTOP | net VBAT_ESTOP_IN (new; the name is not given in the spec) | the FET goes between the connector and the load | H1 "drain to J23, source to load side" |
| Q70, Q71 (new; spec "Q", next free) | none | SQD40P10-40L_GE3 Vishay C141570, TO-252 (Package_TO_SOT_SMD:TO-252-2, KiCad SUD50P06-15 symbol G1/D2/S3), in parallel: D=VBAT_ESTOP_IN, S=VBAT_ESTOP, G=ESTOP_RPF_G | -100 V vs the 64.5 V SMDJ40CA clamp; thermal: 2 in parallel at 0.67 W each | R3-8 |
| R627 (new) | none | 10k 0603 C98220 RC0603FR-0710KL YAGEO, ESTOP_RPF_G -> GND | gate drive | H1 "gate -> 10k -> GND" |
| D137 (new) | none | BZT52C15 C2104 JSCJ SOD-123, A=gate, K=source (VBAT_ESTOP) | Vgs clamp 15 V < 20 V | H1 "BZT52C15 G-S (anode at gate)", R3-8 Gate |
- NOT CMD60P06 / SUD50P06 (rejected by R3-8). Live LCSC 2026-10-28 (HST): C141570 stock 206 1@$1.5676; C2104 stock 10,600 50@$0.0212; C98220 stock 3,801,900 100@$0.0027. outputs_bom +3 rows, TOTAL $162.10 -> $165.26.
- Kept as is (not specified): D126 SMDJ40CA and all other VBAT_ESTOP loads (R251 sense, R411, TPS48100s, INA281s, C199/C203) stay on the load side (VBAT_ESTOP). Only J23.1/2 moved.
- Pinout of SQD40P10-40L vs the KiCad SUD50P06-15 symbol (G1, D2/tab, S3) is INFERRED from the TO-252 standard; the spec asks Layout to check it. PCB: D-m7-7.

### 3b-4a: CT input clamps, 2x BAV99 per CT channel (fixes_safety.md M5 l.462)
| ref | old | new | reason | source |
|---|---|---|---|---|
| D138/D139 (IA), D140/D141 (IB), D142/D143 (IC), D144/D145 (IN) new | no clamp | BAV99 C2500 Nexperia SOT-23, anti-parallel across GEN_Ix_P/GEN_Ix_N at the ADE side of the 1k (R476/R477 etc.); pin1->pin2 series string, pin3 NC | ADE9000 inputs +/-2 V abs; clamp about +/-1.2-1.5 V (INFERRED) | M5 |
- SPEC CONFLICT: M5 says "8 channels / +16 SOT-23", but the schematic has only 4 CT channels (U71 IA/IB/IC/IN; U72 current inputs are tied to GND_AC, bus V only). I fitted 2 per real CT channel = 8 parts, per the brief ("2 per CT channel").
- Live LCSC C2500: stock 100 (LOW), 50@$0.0119. ac_metering_bom gets +1 row (8 pcs), total +$0.10. PCB: D-m7-8.
- Firmware (M5): confirm the ADE full-scale is below the clamp onset.

### 3b-6/7a: reviewer notes N5/N6/N8, R558 value
| ref | old | new | reason | source |
|---|---|---|---|---|
| R12 Note (power) + design.py | "8mR -> ~9.4A peak limit" | LM5176 thresholds / 8 mOhm: boost PEAK 100/120/140 mV -> 12.5/15.0/17.5 A; buck VALLEY 66/80/94 mV -> 8.25/10.0/11.75 A | 9.4 A matches no LM5176 threshold (75 mV/8 mOhm). The reviewer's 12.5 A = min boost peak (0.100 V / 0.008 Ohm). Old note clearly wrong. | N8, TI LM5176 DS Rev D sec 6.5 |
| R558 Value | 0 | 0R | BOM/value consistency with the other 4 zero-ohm parts | 3b item 7 |
| changelog line 53 (JP2-JP4 side) | B.Cu | F.Cu (footprint pads F.Cu/F.Mask) | text error | N6 |
| fixes_mechanical.md:90 (review dir, not in repo) | "SW6 termination stays on the main board" | CAN2 has no on-board termination (SW6/R92/R93/C92 deleted, Item 2); loose terminator plugs go in the daughter-board sockets | text error | N5 |

### 3b-7b/c: MPN fill and TPS1HTC30 reconcile
| ref | old | new | reason | source |
|---|---|---|---|---|
| 314 parts across C14663/C14858/C23184/C25803/C23162/C98220/C21189/C12447/C22859 | MPN blank | MPN copied from the same-LCSC parts (one MPN per code) | BOM consistency | 3b item 7 |
| U47-U61, U68 Value+MPN (+design.py) | TPS1HTC30QPWPRQ1 | TPS1HTC30AQPWPRQ1 (lib symbol id unchanged) | TI part-details: TPS1HTC30AQPWPRQ1 is ACTIVE; TPS1HTC30QPWPRQ1 returns 404 (not orderable). LCSC C22414694 = TPS1HTC30AQPWPRQ1. BOM already had the A suffix. | ti.com 2026-10-28, LCSC live |
| outputs_bom rows 12, 28 price | 7.0093 | 14.2804 (LIVE LCSC 10+, stock 36 vs 16 needed) | live price rule | LCSC 2026-10-28 |
- Not filled: H1-H4 and JP2-JP4 (no LCSC/MPN; they are mechanical or not in the JLC BOM).

### 3b-9c: BOM reconciled against the committed schematic (tools/bom_from_sch.py)
- Before (at e75218d-era baseline): 135 mismatches (QTY 39, SCH_ONLY 51, BOM_ONLY 45). Right before this commit (with D138-D145 and the MPN fill): 132 mismatches (QTY 40 / SCH_ONLY 50 / BOM_ONLY 42).
- Fixed: 26 single-row QTY rows set to the schematic count (each row note has "3b bom_from_sch: qty a->b"), plus inputs_bom BAV99 15->10 (the multi-row case, resolved by the refs). 44 SCH_ONLY LCSC groups added to other_bom.csv as rows with UNVERIFIED prices (excluded from totals).
- After: 63 mismatches (QTY 13, SCH_ONLY 7, BOM_ONLY 43). The rest need a ruling:
  - multi-row QTY groups (100n/100k/1k/10k/MMBT3904 etc.), where it is unclear which row owns the delta;
  - C28233 (24x 100n 0805), whose code is only a URL placeholder in other_bom's "small passives lump" row ($8.68). Its qty is left at 1, because adding a row would double-count the lump.
  - T1-T4/Y3/J30: stale ac_metering rows with a different MPN (rows 9/4/19).
  - CM5 U9/U10 and H1-H4 are off-BOM.
  - BOM_ONLY: off-board plugs, display, CM5, the PCB and estimates, and the stale ac_metering ADuM141E/ADuM5020/ADP150/ERA-3AEB rows (not in the schematic).
- Totals (bom_retotal): comms 28.18->28.37, inputs 24.88->24.65 (incl. BAV99 15->10), other 407.85->407.83, outputs 281.59->281.69, power 46.79->46.57, ac 45.85 unchanged.

### 3b-4b: spec checklist
- docs/SPEC_CHECKLIST_3b.md: each fixes_safety.md (Rev 3/2/§1/§6) and fixes_mechanical.md item, with its hash or skip reason.

## Batch 3c (lead ruling 2026-10-28 16:33 HST)
### 3c-2: J30 -> Phoenix PC 5/8-GF-7,62 1720851
| ref | old | new | reason | source |
|---|---|---|---|---|
| J30 (ac_metering) | KF2EDGRM-5.08-8P C441294, genctl:KF2EDGRM-5.08-8P, no Mate props | MPN 1720851, Phoenix Contact, LCSC C6651769, Mate_MPN "SPC 5/8-STF-7,62 (1996184)", Mate_LCSC UNVERIFIED (no LCSC listing), Mate_Qty 1, footprint **genctl:PLACEHOLDER_PhoenixContact_PC5_8-GF-7.62_1720851** | Lead ruling; fixes_mechanical s1, R3-9, fixes_mates.csv l.6 | |
- Symbol stays Connector_Generic:Conn_01x08. Pins 1-8 = CT1_S1..CT4_S2, unchanged per s1; there is no Phoenix-specific symbol in the stock libs.
- Footprint search in kicad-footprints 9.0.2: there is no PC 5 / 1720851 footprint. The closest stock parts, Connector_Phoenix_GMSTB ..._8-GF-7,62_1x08_P7.62mm, are the GMSTB 2.5 family: 1 pin per position and a different body. The 1720851 has 3 pins per position, a 1.3 mm drill and is 77.06 mm wide (fixes_mechanical s1), so it is NOT a match and was not used.
- Added genctl.pretty/PLACEHOLDER_PhoenixContact_PC5_8-GF-7.62_1720851.kicad_mod: NO PADS, marked DO-NOT-FAB. It exists only so ERC's footprint-link check passes (a missing footprint gives ERC footprint_link_issues=1). The real footprint is deferred_layout D-m7-9.
- ac_metering_bom row 19 (MSTB 2.5/8-GF-5.08 + plug, stale) replaced with J30 1720851 C6651769 x1 @ $9.8499. LIVE 2026-10-28 16:33 HST, **stock 0** (procurement note). No 2x1720819 fallback. design.py CONNFP 'J9 CT' and MATES updated. PCB untouched.

### 3c-1/3: cost notes, BAV99 count
- docs/COST_NOTES.md created; outputs_bom has a NOTE row (no qty/price, so it is excluded from the total). TPS1HTC30AQPWPRQ1 C22414694 is kept at the live $14.2804@10 (lead ruling).
- BAV99 CT clamps stay at **8 parts (4 CT channels)**. Lead ruling: Safety's M5 "8 channels / +16 SOT-23" was wrong, because only U71 has CT inputs and U72's current inputs are tied to GND_AC.

### 3c-5: BOM consolidation, one row per LCSC code with the exact schematic qty (lead ruling)
- **Before (0797a5e): 61 mismatches (QTY 13, SCH_ONLY 6, BOM_ONLY 42). After: 0 mismatches (QTY 0 / SCH_ONLY 0 / BOM_ONLY 0)**, with 199 schematic groups = 199 BOM groups (tools/bom_from_sch.py vs the committed schematic).
- Schematic: H1-H4 mounting holes set to (in_bom no). They are bare holes, not purchased parts, and they were 2 of the SCH_ONLY groups. Not mirrored in design.py (DO NOT REGENERATE).
- Every on-board row now has qty = the schematic count for exactly its LCSC code. The notes column gives "3c: SCH refs (n): ..." plus a live-price stamp. Codes whose refs carry different Values are label-only variants of one part (connector labels, I2C addresses, button names, CM5 conn A/B); each has a single row.
- Live LCSC at 2026-10-28 16:38 HST: the unit price is the break for max(qty, MOQ). There is no live price for C408483, C83451, C1002, C7471020, C79272, so those are UNVERIFIED and excluded.
- Multi-row groups merged into one row (the kept row is in the file of the refs' dominant sheet; the merged rows' function/qty is recorded in its notes): C654559 <- ac_metering_bom.csv:3(qty 1); C22916 <- other_bom.csv:47(qty 8); C22935 <- ac_metering_bom.csv:22(qty 1); C14663 <- inputs_bom.csv:18(qty 31), outputs_bom.csv:51(qty 2), power_bom.csv:40(qty 1), power_bom.csv:44(qty 2); C2500 <- ac_metering_bom.csv:25(qty 8); C2890050 <- comms_bom.csv:9(qty 1); C76584 <- comms_bom.csv:10(qty 1); C14486 <- comms_bom.csv:11(qty 1); C2653785 <- comms_bom.csv:49(qty 1); C160404 <- other_bom.csv:12(qty 1); C15850 <- comms_bom.csv:46(qty 2), comms_bom.csv:60(qty 2); C131941 <- comms_bom.csv:38(qty 1); C2135 <- outputs_bom.csv:41(qty 1); C2482 <- comms_bom.csv:50(qty 1), inputs_bom.csv:35(qty 1); C25803 <- comms_bom.csv:58(qty 2), outputs_bom.csv:24(qty 21), outputs_bom.csv:52(qty 14), outputs_bom.csv:57(qty 1); C20526 <- outputs_bom.csv:46(qty 2), inputs_bom.csv:10(qty 10), other_bom.csv:21(qty 1), power_bom.csv:38(qty 5); C155242 <- inputs_bom.csv:32(qty 2); C98220 <- other_bom.csv:24(qty 2), inputs_bom.csv:19(qty 40), outputs_bom.csv:25(qty 17), outputs_bom.csv:54(qty 2), outputs_bom.csv:60(qty 1); C441292 <- outputs_bom.csv:44(qty 4); C23162 <- outputs_bom.csv:53(qty 1); C21190 <- outputs_bom.csv:15(qty 15), outputs_bom.csv:27(qty 17); C534364 <- power_bom.csv:9(qty 4), outputs_bom.csv:3(qty 4); C12447 <- outputs_bom.csv:13(qty 15); C3018527 <- outputs_bom.csv:10(qty 1); C224077 <- outputs_bom.csv:19(qty 1), power_bom.csv:2(qty 1); C22414694 <- outputs_bom.csv:28(qty 1); C114004 <- power_bom.csv:5(qty 1); C25819 <- outputs_bom.csv:32(qty 16); C3579760 <- power_bom.csv:23(qty 1); C12891 <- power_bom.csv:16(qty 4), power_bom.csv:37(qty 5); C841386 <- power_bom.csv:17(qty 1); C408483 <- power_bom.csv:25(qty 1).
- C28233 placeholder resolved: the other_bom "Small passives ... previously unpriced" lump (1 x $8.68, URL C28233) and power_bom "Misc R/C" lump (1 x $0.40) are deleted. They are replaced by real per-code rows, e.g. C28233 CL21B104KCFNNNE 100n 0805 x24.
- New per-code rows: 4 (C6117861 AC1005 T1-T4, C70568 Y3, C597931 U9/U10 = DF40C-100DS-0.4V(51) per LCSC; the schematic MPN field says "SC1xxx CM5 (variant TBD)", flagged; C28233).
- ac_metering_bom.csv converted to the 13-column format so it carries an LCSC column.
- New bom/off_board_external_bom.csv is EXCLUDED from all totals and from bom_from_sch (both tools skip off_board*). It holds the 45 rows moved there: ac_metering_bom.csv:4 Crystal [ABM8-24.576MHZ-B2-T (or equiv 24.576 MHz]; ac_metering_bom.csv:5 Crystal load caps [GRM1555C1H220JA01D]; ac_metering_bom.csv:7 V divider low side [ERA-3AEB1001V]; ac_metering_bom.csv:9 Aux CT (5A secondary -> mA) [UNKNOWN (e.g. Talema AC1005 / CR Magneti]; ac_metering_bom.csv:10 Anti-alias RC [ERJ-2RKF1001X + GRM155R71H333KA88D]; ac_metering_bom.csv:11 Isolated DC-DC [ADuM5020-5BRWZ]; ac_metering_bom.csv:12 LDO hot side [ADP150AUJZ-3.3]; ac_metering_bom.csv:13 Digital isolator SPI [ADuM141E1BRWZ]; ac_metering_bom.csv:14 Digital isolator CS2/IRQ/reset [ADuM141E1BRWZ]; ac_metering_bom.csv:16 TVS at ADC inputs [SMAJ3.3CA or internal clamp]; ac_metering_bom.csv:17 Terminal block HV (gen) [MSTB 2.5/4-GF-7.62 header + MSTB 2.5/4-S]; ac_metering_bom.csv:18 Terminal block HV (bus) [MSTB 2.5/4-GF-7.62 + MSTB 2.5/4-STF-7.62]; comms_bom.csv:8 CAN1 field plug [WJ15EDGK-3.81-04P-14-00A]; comms_bom.csv:13 CAN2: EXP_12V TVS [SMF5.0A (use SMF15A equivalent)]; comms_bom.csv:15 CAN2 expansion plug [WJ15EDGK-3.81-06P-14-00A]; comms_bom.csv:20 RS-485 plug [WJ15EDGK-3.81-03P-14-00A]; comms_bom.csv:21 Ethernet: RJ45 magjack w/ LEDs, 1000BASE-T (CM5 has on-modul [HR911131A]; comms_bom.csv:23 USB-C service port (CM5 USB2 OTG: rpiboot flashing + gadget) [TYPE-C-31-M-12]; comms_bom.csv:25 STM32<->CM5 link level/isolation [none (both 3.3 V)]; comms_bom.csv:29 Display: DSI83 REFCLK oscillator 25 MHz 1.8 V (DNP option) [ASDMB-25.000MHZ-LC-T]; comms_bom.csv:33 Display: DSI83 decoupling 100 nF [CL05B104KO5NNNC]; comms_bom.csv:39 Display: touch I2C/RST/INT pull-ups 2.2k [0402WGF2201TCE]; comms_bom.csv:52 ROUTER_12V plug [WJ15EDGK-3.81-02P-14-00A]; inputs_bom.csv:21 AI: series protection after blocking diode [1206W4F1001T5E]; inputs_bom.csv:36 VBAT / E-stop rail / D+ sense divider bottom [RT0805BRD0710KL]; inputs_bom.csv:38 Connector plug J1-J3 (6 plugs) [KF2EDGKNM-5.08-6P]; other_bom.csv:2 UI processor [CM5104032 (SC1595)]; other_bom.csv:3 Front display (aTouch, inset mount, touch-ready) [RVT121HVLNWCA0-B]; other_bom.csv:11 CM5 cooling: passive heatsink [SC1752]; other_bom.csv:13 PCB fabrication (6-layer, ~240x180 mm, qty 5) [ESTIMATE]; other_bom.csv:14 JLC assembly (setup, stencil, Extended part fees, THT, globa [ESTIMATE]; other_bom.csv:15 Enclosure (DSE 8610 cutout, rear housing) [ESTIMATE]; other_bom.csv:16 Bezel + button overlay + gasket (no separate glass: display  [ESTIMATE]; other_bom.csv:19 Button backlight resistors B [0603WAF2000T5E]; outputs_bom.csv:20 Bulk/decoupling on each switch VS [0603B104K500NT]; outputs_bom.csv:30 E-stop trip: sense resistor / freewheel / TVS [(reuse 1.1k C22764, SS110 C2482, SMBJ40C]; outputs_bom.csv:37 E-stop one-shot: LDO input hold-up C [CL31B106KAHNNNE]; outputs_bom.csv:39 E-stop one-shot: TRIG pull/RC + Q1 collector [0603WAF1003T5E / 0603WAF1002T5E]; outputs_bom.csv:40 E-stop one-shot: TRIG/CONT/LDO caps [0603B104K500NT / CL21B225KBFNNNE]; outputs_bom.csv:43 Connector plug J4 FUEL/CRANK/VBAT_ESTOP x2 (>=15 A/pin) [SPC 5/4-STF-7,62 (1996142)]; outputs_bom.csv:45 Connector plug J5-J6 (4 plugs) [KF2EDGKNM-5.08-6P]; power_bom.csv:13 Display 12V load switch/feed [(use 12V bus direct + fuse)]; power_bom.csv:18 3V3 diode-OR [MBR0540]; power_bom.csv:19 LDO backup option 3V3 [NCV8730ASN330T1G]; power_bom.csv:24 Connector plug J0 BATTERY [SPC 5/4-STF-7,62 (1996142)].
- MPN text differences kept as-is (the BOM has the orderable suffix; the schematic has a short form), reported: C2500 BOM "BAV99,215" vs sch "BAV99"; C7245 BOM "WJ15EDGRC-3.81-04P-14-00A" vs sch "WJ15EDGRC-3.81-04P"; C7246 BOM "WJ15EDGRC-3.81-06P-14-00A" vs sch "WJ15EDGRC-3.81-06P"; C7955 BOM "LM393DR2G" vs sch "LM393DR"; C8387 BOM "WJ15EDGRC-3.81-02P-14-00A" vs sch "WJ15EDGRC-3.81-02P"; C8406 BOM "WJ15EDGRC-3.81-03P-14-00A" vs sch "WJ15EDGRC-3.81-03P"; C8492 BOM "LBSS84LT1G" vs sch "BSS84"; C12067 BOM "SM712.TCT" vs sch "SM712"; C40960 BOM "RCLAMP0524PATCT" vs sch "RCLAMP0524P.TCT"; C155242 BOM "DMN6075S-7" vs sch "DMN6075S"; C485339 BOM "SM02B-BHSS-1-TB(LF)(SN)" vs sch "SM02B-BHSS-1-TB"; C597931 BOM "DF40C-100DS-0.4V(51)" vs sch "SC1xxx CM5 (variant TBD)"; C3015165 BOM "LM317MDT" vs sch "LM317MDT-TR"; C3579760 BOM "PC 5/4-GF-7,62 (1720819)" vs sch "1720819"; C7498149 BOM "BS-CR2032-8" vs sch "CR2032 holder".
- Totals (bom_retotal, exact): ac_metering 55.70 -> 308.39 (ADE9000 x2, AC1005 x4, MOVs and C14663 x112 are now live-priced on this row set); comms 28.37 -> 50.01; inputs 24.65 -> 27.58; other 407.83 -> 142.27 (CM5 $105 and display $226.04 moved off-board); outputs 281.69 -> 298.15; power 46.57 -> 40.33. On-board sum 844.81 -> 866.73.

### 3c-6: N4 stale F1 / VBAT_F documentation (docs only; .kicad_pcb untouched)
- Current state: no on-board fuse; battery net BAT_IN (J1.1/2, Q1.1-3, U1.2-4, D1.1, C297.1, R1.1, from net.xml); installer fits an external fuse <=10 A fast-acting, >=58 V DC.
- Rewritten: DESIGN_NOTES.md l.38 (fuse line), l.39/43/44/46/53/397 VBAT_F -> BAT_IN; l.529 F1 10 A ruling marked SUPERSEDED; bom/design_spec.md:17; mechanical/LAYOUT_PLAN.md:42.
- Marked superseded, not rewritten, because they are records of the unchanged as-built board copper (F1 clips and net VBAT_F still exist on the .kicad_pcb): header banner in docs/RAIL_PLAN.md, docs/ROUTING_PLAN.md and mechanical/pcb_v4/README.md; a note under the F1 row in mechanical/enclosure/v3/BOARD_INTERFACE.md.
- place_v4.py: only the comment on l.40 (U1 placement) was edited; no code references F1.
- Not edited (not in scope): mechanical/enclosure/v3/board_interface.json F1 entry (generated from the PCB).

### 3c-7: SPEC_CHECKLIST_3b.md updated: R3-9/§1 J30 DONE (c4c54d2), §3 J30 mate DONE; C28233 resolved (see 3c-5, 2fa36b7).

## Batch 4
### 4-1: VBAT_AI clamped rail for the AI current sources and LM2904B (fixes_safety.md Rev 3 corrections (a); safety_rereview_30dd932.md (a), HIGH-1)
| Item | Before | After | Source |
|---|---|---|---|
| Q72 (new) | none | BCP56-16 (BCP56-16TX, Nexperia, LCSC C426787), SOT-223-3_TabPin2: C (pins 2, 4) = VBAT_P, B = VBAT_AI_B, E = VBAT_AI | Rev 3 (a) |
| R628 (new) | none | 10k 0603 C98220 (RC0603FR-0710KL): VBAT_P to VBAT_AI_B | Rev 3 (a) |
| D146 (new) | none | BZT52C33 (JSCJ, C2110) SOD-123: K = VBAT_AI_B, A = GND. Not BZT52C36. | Rev 3 (a) |
| #FLG (new) | none | PWR_FLAG on VBAT_AI. The rail is driven by a passive BJT emitter, so without the flag ERC raises power_pin_not_driven on U26.8. | ERC |
| 26 VBAT_P global labels on inputs.kicad_sch -> VBAT_AI | VBAT_P | VBAT_AI: U26/U27/U28 pin 8; their decoupling caps C144/C145/C146; D23.1 (LM4040 K); Q13/Q17/Q21/Q25/Q29/Q33 pin 2; R130/R133/R141/R144/R152/R155/R163/R166/R174/R177/R185/R188 pin 1; **C131** | Rev 3 (a) list |
| VBAT_P (unchanged) | | Q36/Q39/Q42 sources and R200/R205/R261 (DI bias) remain on VBAT_P. Not in the Safety list. | |
- **Deviation from the literal Safety list, flagged for Safety:** C131 (100n, D23 K to AI_VSET, the reference bypass) was moved with D23. Leaving it on VBAT_P would bridge VBAT_P to the AI_VSET reference node once D23.K is on VBAT_AI. Revert = rename one label (inputs.kicad_sch 862.33,74.93).
- Labels mapped per pin by probe-renaming each of the 32 VBAT_P labels on the sheet and exporting the netlist (MEASURED). VBAT_AI net now = C131 C144 C145 C146 D23 Q13 Q17 Q21 Q25 Q29 Q33 Q72 R130 R133 R141 R144 R152 R155 R163 R166 R174 R177 R185 R188 U26 U27 U28.
- BOM: inputs_bom +Q72 (1 @ $0.1310 at MOQ 5; stock 28,260), +D146 (1 @ $0.0239 at MOQ 50; stock 3,600), LIVE LCSC 16:44 HST. JLC class UNVERIFIED. C98220 78 -> 79. inputs 27.58 -> 27.73, other 142.27 -> 142.29.
- design.py not regenerated/mirrored (schematic is source of truth).
- Open (Safety, INFERRED in their file): AI compliance at 9 V battery with the rail about 2 V lower.

### 4-2: BZT52C15 gate-source clamps on Q36/Q39/Q42 only (fixes_safety.md Rev 3 corrections (b); safety_rereview_30dd932.md (b), HIGH-2)
| Ref | Part | Nets | Source |
|---|---|---|---|
| D147 (new) | BZT52C15 JSCJ C2104 SOD-123 | K = VBAT_P (Q36 source), A = Q36_G | Rev 3 (b) |
| D148 (new) | same | K = VBAT_P (Q39 source), A = Q39_G | Rev 3 (b) |
| D149 (new) | same | K = VBAT_P (Q42 source), A = Q42_G | Rev 3 (b) |
- The gate nets were unnamed (Net-(Q36-G) etc.). A local label Q36_G/Q39_G/Q42_G was placed on each gate pin, so they are now named. Members unchanged apart from the zener (R200/R201 etc.). MEASURED netlist diff: 4 connectivity diffs, all the added zener pins.
- **None on Q2/Q3** (per ruling). Q70/Q71 keep D137.
- BOM: outputs_bom C2104 row qty 1 -> 4, price $0.0212 at the 50+ break (LIVE 16:44 HST, stock 10,600).

### 4-3: D63 SMBJ40CA; U26-U28 Value; MPN fields; FUEL_OUT label (Safety re-review M4/L10; Design Reviewer re-audit 3 L1/L2)
| Item | Before | After | Source |
|---|---|---|---|
| D63 (DPLUS TVS) | SMBJ36CA, LCSC C78421, Brightking | SMBJ40CA, LCSC C114004, MDD (same code as D2/D74-D102/D123) | safety_rereview MEDIUM-4 |
| U26/U27/U28 Value | LM2904 | LM2904B (MPN LM2904BIDR, C1849422, unchanged) | reviewer L1 |
| R277-R291 (47k, C25819) MPN/Manufacturer | empty | 0603WAF4702T5E / UNI-ROYAL (LIVE LCSC 16:48 HST) | safety_rereview LOW-10 |
| R554 (220k, C22961) | empty | 0603WAF2203T5E / UNI-ROYAL (LIVE) | same |
| R556 (1M, C22935) | empty | 0603WAF1004T5E / UNI-ROYAL (LIVE) | same |
| H4 MPN | empty | "NONE (NPTH mounting hole, no purchased part)". H4 has no LCSC; it is in_bom no (3c). | same |
| Fuel output net | Net-(D68-A1) | FUEL_OUT. Local label on J23.3 (outputs.kicad_sch 986.79,119.38). Members unchanged: C198.2 D68.1 D71.2 J23.3 Q45 Q46 (S) R349 R350 U43.13 (TPS48100 FUEL stage, FUEL_DRN/FUEL_GPD). Matches the ROUTING_PLAN:315 "(= FUEL_OUT)". | reviewer L2 |
- BOM:
  - other_bom row "SCH-only part added by 3b reconcile: D63" (SMBJ36CA C78421) deleted;
  - outputs_bom C114004 17 -> 18;
  - outputs_bom R554 row MPN "(C22961)" -> 0603WAF2203T5E.
- Board: the PCB still names the net Net-(D68-A1); this becomes a rename at the next board update (PCB not touched).

### 4-4: BAV99 symbol pin names corrected (safety_rereview LOW-12 / (c); item 6)
- DATASHEET: Nexperia BAV99_SER Rev 8, Table 3 p2 (fetched 2026-10-28): pin 1 = anode (diode 1), pin 2 = cathode (diode 2), pin 3 = cathode (diode 1) + anode (diode 2).
- The KiCad stock Diode:BAV99 symbol names the pins 1 K, 2 A, 3 K, which is wrong. Its graphic is right (pin1 -|>|- pin3 -|>|- pin2).
- Wiring check (MEASURED netlist, all 18 BAV99):
  - D26/D29/D32/D35/D38/D41/D43/D45/D60/D62: pin1 = GND, pin2 = +3V3_SAFE, pin3 = signal. This is correct for the real pinout (A to GND, K to the rail).
  - D138-D145: pin1/pin2 across GEN_Ix_P/N, alternating, with pin3 NC (2 diodes in series, anti-parallel pairs). Correct.
  - **No wiring change needed.**
- Fix: new project symbol genctl:BAV99 (in genctl.kicad_sym and embedded) with pin names 1 A1, 2 K2, 3 K1/A2 and the same graphic and pin numbers/positions. All 18 instances repointed from Diode:BAV99, because pin numbers are unchanged.
- Netlist: 0 connectivity changes. NC net names change (unconnected-(D138-K-Pad3) -> unconnected-(D138-K1/A2-Pad3), etc.).

### 4-5: Documentation items (batch 4 rulings R3-N1, R3-N5; reviewer R3-N3/N4/N6/N7; Mechanical H4)
- **R3-N1 (ruling): every external fuse is >=58 V DC; amp ratings unchanged.** docs/INSTALL_SAFETY.md:
  - output-fuse table, l.32-34: FUEL/CRANK "15 A blade (ATO/ATC), 32 V DC" and GLOW "2 A blade, 32 V DC" -> ">=58 V DC";
  - GCB/MCB, ESTOP_TRIP, AUX1-6, AUX7-10 rows: ", >=58 V DC" appended;
  - battery feed row "30 A (existing)" -> "30 A (existing), >=58 V DC";
  - l.41: "32 V DC blade fuses suit 12 V and 24 V systems." replaced by the >=58 V DC requirement sentence.
  - l.15 (board feed) already said >=58 V DC.
  - Schematic text: the only fuse label is power.kicad_sch "EXT FUSE <=10 A FAST, >=58 V DC" plus the POWER note (">=58 V DC"). grep for "32 V" in *.kicad_sch and bom/*.csv finds no fuse text, so no schematic or BOM change was needed.
- **R3-N5 (ruling, accepted note, no schematic change):** new docs/FAILURE_MODES.md row: R627 open / D137 short -> Q70/Q71 body-diode conduction, about 2.4 W per FET, about 216 °F rise (INFERRED). The Design Reviewer's own table in review/schematic_audit/reviewer.md was not edited because that file is under concurrent audit.
- **R3-N7:** changelog l.164 "design.py already named BUS_VA_P" corrected in place. design.py has 0 occurrences.
- **R3-N4:** python csv check on HEAD: every bom/*.csv row has the header's 13 fields except power_bom.csv:3 (14 fields). Cause: an unquoted comma split the BSC070N10NS5 note at 30dd932 line 4, and 2fa36b7 then dropped the second half while leaving a duplicate LCSC field. Fixed: the note is rejoined (second half restored) and the duplicate field removed; totals unchanged.
  - other_bom.csv:22 (the C28233 lump) was deleted in 2fa36b7.
  - ac_metering_bom.csv:15 (the 6x 600 V fuse row) was deleted in 3b; the file has had a 13-column header since 2fa36b7.
  - After the fix, all 7 files parse with 13 fields per row.
- **R3-N3:** bom_from_sch on HEAD reports 0 mismatches (QTY 0 / SCH_ONLY 0 / BOM_ONLY 0). The batch-3 short quantities listed by the reviewer (C23162, C25819, C12447, C114004, C3579760, C98220) were set to the schematic count in 2fa36b7; later batch-4 changes are in 4-1..4-3.
- **Item 7, H4 off CHASSIS: intentional.** review/schematic_audit/fixes_mechanical.md §5 l.83: "H4 → `MountingHole:MountingHole_4.3mm_M4` (no pad, a 0-pin symbol). **Remove H4 from the CHASSIS net.** CHASSIS then = H1–H3, J10.15, C48, C87, C93." Also l.81: "H4 is a 4.3 mm NPTH PE-boss clearance, D9.5". The PE strategy (Safety MEDIUM-8) is still for Mechanical/Safety to confirm.
- **R3-N6: itemised list of every BOM row moved or deleted in 2fa36b7.** "Stale" = on-board BOM_ONLY row whose LCSC/MPN is carried by no schematic part.
| Was | Function | MPN | LCSC | Qty | Why | Now |
|---|---|---|---|---|---|---|
| ac_metering_bom.csv:4 | Crystal | ABM8-24.576MHZ-B2-T (or equiv 24.576 MHz | - | ? | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| ac_metering_bom.csv:5 | Crystal load caps | GRM1555C1H220JA01D | - | 2 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| ac_metering_bom.csv:7 | V divider low side | ERA-3AEB1001V | - | 6 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| ac_metering_bom.csv:9 | Aux CT (5A secondary -> mA) | UNKNOWN (e.g. Talema AC1005 / CR Magneti | - | ? | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| ac_metering_bom.csv:10 | Anti-alias RC | ERJ-2RKF1001X + GRM155R71H333KA88D | - | 26 R + 26 C | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| ac_metering_bom.csv:11 | Isolated DC-DC | ADuM5020-5BRWZ | - | 1 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| ac_metering_bom.csv:12 | LDO hot side | ADP150AUJZ-3.3 | - | 1 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| ac_metering_bom.csv:13 | Digital isolator SPI | ADuM141E1BRWZ | - | 1 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| ac_metering_bom.csv:14 | Digital isolator CS2/IRQ/reset | ADuM141E1BRWZ | - | 1 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| ac_metering_bom.csv:16 | TVS at ADC inputs | SMAJ3.3CA or internal clamp | - | 0-14 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| ac_metering_bom.csv:17 | Terminal block HV (gen) | MSTB 2.5/4-GF-7.62 header + MSTB 2.5/4-S | - | ? | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| ac_metering_bom.csv:18 | Terminal block HV (bus) | MSTB 2.5/4-GF-7.62 + MSTB 2.5/4-STF-7.62 | - | 1 set | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| comms_bom.csv:8 | CAN1 field plug | WJ15EDGK-3.81-04P-14-00A | C7244 | 1 | off-board item (mating plug, module, accessory or cost estimate) | bom/off_board_external_bom.csv (excluded from totals) |
| comms_bom.csv:13 | CAN2: EXP_12V TVS | SMF5.0A (use SMF15A equivalent) | none | 1 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| comms_bom.csv:15 | CAN2 expansion plug | WJ15EDGK-3.81-06P-14-00A | C7247 | 1 | off-board item (mating plug, module, accessory or cost estimate) | bom/off_board_external_bom.csv (excluded from totals) |
| comms_bom.csv:20 | RS-485 plug | WJ15EDGK-3.81-03P-14-00A | C8413 | 1 | off-board item (mating plug, module, accessory or cost estimate) | bom/off_board_external_bom.csv (excluded from totals) |
| comms_bom.csv:21 | Ethernet: RJ45 magjack w/ LEDs, 1000BASE-T (CM5 has on-modul | HR911131A | - | ? | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| comms_bom.csv:23 | USB-C service port (CM5 USB2 OTG: rpiboot flashing + gadget) | TYPE-C-31-M-12 | C165948 | 1 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| comms_bom.csv:25 | STM32<->CM5 link level/isolation | none (both 3.3 V) | none | 0 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| comms_bom.csv:29 | Display: DSI83 REFCLK oscillator 25 MHz 1.8 V (DNP option) | ASDMB-25.000MHZ-LC-T | - | 0 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| comms_bom.csv:33 | Display: DSI83 decoupling 100 nF | CL05B104KO5NNNC | C1525 | 6 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| comms_bom.csv:39 | Display: touch I2C/RST/INT pull-ups 2.2k | 0402WGF2201TCE | C25879 | 4 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| comms_bom.csv:52 | ROUTER_12V plug | WJ15EDGK-3.81-02P-14-00A | C8466 | 1 | off-board item (mating plug, module, accessory or cost estimate) | bom/off_board_external_bom.csv (excluded from totals) |
| inputs_bom.csv:21 | AI: series protection after blocking diode | 1206W4F1001T5E | C4410 | 6 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| inputs_bom.csv:36 | VBAT / E-stop rail / D+ sense divider bottom | RT0805BRD0710KL | C110775 | 3 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| inputs_bom.csv:38 | Connector plug J1-J3 (6 plugs) | KF2EDGKNM-5.08-6P | C2974985 | 6 | off-board item (mating plug, module, accessory or cost estimate) | bom/off_board_external_bom.csv (excluded from totals) |
| other_bom.csv:2 | UI processor | CM5104032 (SC1595) | none | 1 | off-board item (mating plug, module, accessory or cost estimate) | bom/off_board_external_bom.csv (excluded from totals) |
| other_bom.csv:3 | Front display (aTouch, inset mount, touch-ready) | RVT121HVLNWCA0-B | none | 1 | off-board item (mating plug, module, accessory or cost estimate) | bom/off_board_external_bom.csv (excluded from totals) |
| other_bom.csv:11 | CM5 cooling: passive heatsink | SC1752 | none | 1 | off-board item (mating plug, module, accessory or cost estimate) | bom/off_board_external_bom.csv (excluded from totals) |
| other_bom.csv:13 | PCB fabrication (6-layer, ~240x180 mm, qty 5) | ESTIMATE | none | 1 | off-board item (mating plug, module, accessory or cost estimate) | bom/off_board_external_bom.csv (excluded from totals) |
| other_bom.csv:14 | JLC assembly (setup, stencil, Extended part fees, THT, globa | ESTIMATE | - | ? | off-board item (mating plug, module, accessory or cost estimate) | bom/off_board_external_bom.csv (excluded from totals) |
| other_bom.csv:15 | Enclosure (DSE 8610 cutout, rear housing) | ESTIMATE | none | 1 | off-board item (mating plug, module, accessory or cost estimate) | bom/off_board_external_bom.csv (excluded from totals) |
| other_bom.csv:16 | Bezel + button overlay + gasket (no separate glass: display  | ESTIMATE | - | ? | off-board item (mating plug, module, accessory or cost estimate) | bom/off_board_external_bom.csv (excluded from totals) |
| other_bom.csv:19 | Button backlight resistors B | 0603WAF2000T5E | C8218 | 12 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| outputs_bom.csv:20 | Bulk/decoupling on each switch VS | 0603B104K500NT | C30926 | 17 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| outputs_bom.csv:30 | E-stop trip: sense resistor / freewheel / TVS | (reuse 1.1k C22764, SS110 C2482, SMBJ40C | - | ? | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| outputs_bom.csv:37 | E-stop one-shot: LDO input hold-up C | CL31B106KAHNNNE | C13585 | 1 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| outputs_bom.csv:39 | E-stop one-shot: TRIG pull/RC + Q1 collector | 0603WAF1003T5E / 0603WAF1002T5E | - | 1 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| outputs_bom.csv:40 | E-stop one-shot: TRIG/CONT/LDO caps | 0603B104K500NT / CL21B225KBFNNNE | C30926 | 1 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| outputs_bom.csv:43 | Connector plug J4 FUEL/CRANK/VBAT_ESTOP x2 (>=15 A/pin) | SPC 5/4-STF-7,62 (1996142) | C5481482 | 1 | off-board item (mating plug, module, accessory or cost estimate) | bom/off_board_external_bom.csv (excluded from totals) |
| outputs_bom.csv:45 | Connector plug J5-J6 (4 plugs) | KF2EDGKNM-5.08-6P | C2974985 | 4 | off-board item (mating plug, module, accessory or cost estimate) | bom/off_board_external_bom.csv (excluded from totals) |
| power_bom.csv:13 | Display 12V load switch/feed | (use 12V bus direct + fuse) | - | 0 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| power_bom.csv:18 | 3V3 diode-OR | MBR0540 | C77337 | 0 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| power_bom.csv:19 | LDO backup option 3V3 | NCV8730ASN330T1G | C893327 | 0 | stale on-board row: no schematic part carries this LCSC code / MPN (superseded design text) | bom/off_board_external_bom.csv (excluded from totals) |
| power_bom.csv:24 | Connector plug J0 BATTERY | SPC 5/4-STF-7,62 (1996142) | C5481482 | 1 | off-board item (mating plug, module, accessory or cost estimate) | bom/off_board_external_bom.csv (excluded from totals) |
| other_bom.csv:22 | Small passives all sheets (R/C/ferrite/LEDs/load caps) previ | (lump) | C28233 placeholder | 1 @ $8.68 | placeholder lump replaced by real per-code rows | deleted |
| power_bom.csv:22 | Misc R/C (dividers comp soft-start) | (lump) | C28233 placeholder | 1 @ $0.40 | placeholder lump replaced by real per-code rows | deleted |

### 4-6: docs/ERC_AUDIT.md (item 8)
- Added docs/ERC_AUDIT.md. Findings: no exclusions or severity overrides in the project; 220 no_connect flags; 23 PWR_FLAGs; an all-error scratch run gives 75 default-ignored items (four_way_junction 17, footprint filter 58). One real finding, left open: D3/D4 BAS70 2-pin symbol on SOT-23, pinout likely wrong.
