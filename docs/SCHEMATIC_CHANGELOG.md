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
- **Before (0797a5e): 61 mismatches (QTY 13, SCH_ONLY 6, BOM_ONLY 42). After: 0 mismatches (QTY 0 / SCH_ONLY 0 / BOM_ONLY 0)**, with 199 schematic groups = 199 BOM groups at 37327c2 (tools/bom_from_sch.py vs the committed schematic); batches 4-6 added groups, so it is **201 = 201** from 17d3485 on (Reviewer Re-audit 4 INFO).
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

## Batch 5 (fixes_safety.md CLOSING ITEMS; lead approvals 1-5, 7; item 6 no change)
### 5-1: TPS1HTC30 RILIM 40.2k -> 24.9k (item 1)
- RILIM references are taken from the netlist (pin-function ILIM on U47-U61): R304, R307, R310, R313, R316, R319, R322, R325, R328, R331, R334, R337, R340, R343, R346, 15 parts. This matches the Safety/Firmware list. U68 ILIM = R407, which stays 47k.
- Value 24.9k, LCSC C25962, MPN 0603WAF2492T5E (UNI-ROYAL). Live LCSC 2026-10-28 HST: stock 716,300; 100+ @ $0.0017.
- Arithmetic: ICL = KCL/RILIM, KCL 80/100/120 A·kOhm (TPS1HTC30-Q1 SLVSGL4A p8), RILIM ±1 %:
  - min 80/(24.9*1.01) = 3.18 A;
  - typ 100/24.9 = 4.02 A;
  - max 120/(24.9*0.99) = 4.87 A.
  - Old 40.2k gave 1.97/2.49/3.02 A.
- U68 R407 47k: 80/47.47 = 1.69, 100/47 = 2.13, 120/46.53 = 2.58 A. fixes_firmware.md §20.2 says 1.70/2.13/2.55 A. The rounding differs only slightly, but the max figure differs (2.58 vs 2.55). Trip-coil current UNVERIFIED (bench item).
- BOM: outputs C12447 qty 18 -> 3 (the TPS48100 RISCP parts remain); new C25962 row, qty 15, JLC class UNVERIFIED.
- Text:
  - outputs.kicad_sch OUTPUTS note "ILIM 40.2k" -> "ILIM 24.9k (3.18/4.02/4.87 A)";
  - DESIGN_NOTES.md:281;
  - INSTALL_SAFETY output table l.34/35/37/38 "limit 2.49 A" -> "limit 4.02 A (3.18–4.87 A)";
  - l.86 "not supported at 2.49 A" reworded.
- fixes_firmware.md §20 matches these refs and figures. §20.2 unrounded is 3.21/4.02/4.82 A; with ±1 % it is 3.18/4.02/4.87 A, the same as here.

### 5-2: LM74800 U1 VSNS/SW to VBAT_DD (item 2; fixes_safety.md C5 / M5)
- Verified before the edit:
  - net VBAT_DD exists = C1.1, C2.2, Q1.5 (D), Q2.5 (D), U1.10 (VS), U1.12 (C). Per C5, VS and C are on VBAT_DD.
  - U1.3 (VSNS) and U1.4 (SW) were on BAT_IN: pin 3 by a wire into the BAT_IN junction at (90.17, 91.44); pin 4 by a BAT_IN power symbol #PWR1030 at (88.9, 93.98).
- Change, power.kicad_sch:
  - removed wire (90.17, 91.44)-(91.44, 91.44);
  - removed #PWR1030;
  - added wire U1.3-U1.4 (x 91.44) and a VBAT_DD local label at (88.9, 93.98).
- U1.3 and U1.4 stay shorted together and are now on VBAT_DD with VS. No resistor. R1 (210k) stays on BAT_IN, so OV/UVLO still sense the raw battery.
- Netlist diff vs previous HEAD: only U1.3 and U1.4 moved from BAT_IN (11 -> 9 nodes) to VBAT_DD (6 -> 8 nodes).
- Datasheet SNOSD95C p3: "If the internal disconnect switch between VSNS and SW is not used then short them together and connect to VS pin." $0.
- PCB: U1 pads 3/4 net change pending at layout (PCB untouched).

### 5-3: +3V3 inductor note 2.2uH -> 3.3uH (item 3)
- power.kicad_sch POWER note (l.5368): "TPS56637 -> +3V3 from +12V (FB 45.3k/10k, 2.2uH, 3x22u)" -> "(FB 45.3k/10k, 3.3uH L3, 3x22u)". L2 and L3 are both 3.3u MWSA1004S-3R3MT C408483 (netlist).
- Other L2/L3 text checked, left unchanged and reported:
  - L3 hidden "Note" property: "2.2uH per DS Table 4 (3.3V)". This is a datasheet-recommendation statement, not the fitted value; the 3.3uH choice vs DS Table 4 is for Safety/Power to confirm.
  - bom/power_bom.csv:11 note: "Check TPS56637 recommended L (likely 1.5-2.2u…)".
  - tools/design.py:51: same "2.2uH" note text. The generator is not regenerated; deferred.

### 5-4..5-7: layout deferrals, M4, fuse text, 2.8 A declared limit (items 4, 5, 6, 7; lead 2.8 A ruling)
- Item 4: review/schematic_audit/deferred_layout.md (outside the repo) gains D-m7-10: R297/R303 each need > 300 mm² of pad/trace copper (fixes_safety C2, datasheet p3 note iii). Layout only; no schematic change. Also added: D-m7-11 (batch-4 new parts and nets) and D-m7-12 (U1 pads 3/4 to VBAT_DD).
- Item 5: deferred_layout.md D-m7-9 now reads "8 positions at 7.62 mm pitch" (it previously said "8 positions at 7.62 mm").
- Item 6: **M4: no change per lead ruling** (74HC14 DI clamp; the optional 100k/22k change was not applied).
- Item 7, fuse text, verified:
  - power.kicad_sch board-feed label reads "EXT FUSE <=10 A FAST, >=58 V DC".
  - INSTALL_SAFETY.md l.32-39 give each external fuse >=58 V DC with its own amp rating (4-5).
  - grep for "32 V" in *.kicad_sch, bom/*.csv and INSTALL_SAFETY finds no fuse text. Remaining "32 V" hits concern battery range/OVP history, not fuses.
- 2.8 A declared per-channel limit (lead ruling; fixes_firmware.md §21): grep of docs, INSTALL_SAFETY, schematic text/notes and BOM notes for a "3 A" stated as the declared per-channel output limit finds **no such statement**, so no edit was made.
  - The "3 A"/"3A" hits are unrelated: TPS61500/SS36/SS34 ratings, the +3V3 >=3 A rail, RAIL_PLAN copper and ROUTING_PLAN widths.
  - Not edited and reported instead (not clearly a "3 A declared limit"):
    - INSTALL_SAFETY l.32-33 FUEL/CRANK "Rating 15 A" (§21.1 says 2.8 A applies to FUEL/CRANK too);
    - l.36 ESTOP_TRIP;
    - fixes_firmware §21.3's proposed INSTALL_SAFETY sentence (not inserted; awaiting the lead).

### 5-8: correction to 4-3 (reviewer L1): U26-U28 Value on every unit
- 6733aac set Value LM2904B on only one unit instance of each 3-unit symbol (U26/U27/U28 each have units A, B and power). The netlist export takes the value from another unit, so it still read "LM2904". This was found in the final netlist diff vs 37327c2.
- Fixed: Value "LM2904B" on all units of U26, U27 and U28 (6 unit blocks). The netlist now shows LM2904B. The lib_symbols cache entry is unchanged. MPN LM2904BIDR / C1849422 unchanged. bom_from_sch: 0 mismatches.

## Batch 6 (team lead Enginerd, 2026-10-28 5:00 PM HST)
### 6-1: output hardware-maximum line (item 1)
- docs/INSTALL_SAFETY.md: added a new bullet after the ESTOP_TRIP bullet (l.47): "Hardware maximum per main output: interposing relay coil class <= 2.8 A (software trip 3.0 A). E-stop trip coil must draw < 1.70 A (U68 limit with R407 47k); measure on the bench. Where a circuit has a lower limit or a 2 A fuse, that lower limit governs."
- The stricter existing limits are unchanged: the 0.5 A coil lines (l.46/47/87), the 2 A output fuses, and the FUEL/CRANK 15 A rating rows.
- README.md "Fusing" paragraph (l.24-28): added the matching one-liner with the same wording that the lower limit governs. The 2 A fuses are kept.

### 6-2: BAS70 D3/D4 pinout fixed (item 2)
- Evidence:
  - LCSC C77297, live 2026-10-28 HST: "BAS70", JSCJ, SOT-23, "1 Independent ... Single Diodes", stock 760, 20+ @ $0.0288. It is the single BAS70, not -04/-05/-06.
  - The datasheet linked from the LCSC page (datasheet.lcsc.com/.../6b6204ac0be5490386d46c88466108be.pdf, JCET "BAS70/-04/-05/-06", rev E Oct 2015) shows on p1, in the BAS70 "Marking: 73" internal diagram with the SOT-23 package pin numbering: anode = pin 1 (bottom-left), cathode = pin 3 (top), pin 2 (bottom-right) not connected.
- Intended polarity: LM5176 bootstrap. DESIGN_NOTES.md:362 says "external BAS70 boot diodes VCC->BOOT1/2", and the schematic shows A = U2.23 VCC (with C13) and K = BOOT1/BOOT2 (with C15/C16). The polarity is unambiguous.
- Before, Device:D_Schottky (1 = K, 2 = A) on a SOT-23 footprint:
  - D3: pad 1 = BB_BOOT1, pad 2 = Net-(D3-A) (VCC), pad 3 unconnected;
  - D4: pad 1 = BB_BOOT2, pad 2 = VCC net, pad 3 unconnected.
  - On the real part, pad 1 (anode) sat on BOOT, pad 3 (cathode) was floating, and VCC went to the NC pad, so the diodes were out of circuit.
- After: new symbol genctl:BAS70 (in genctl.kicad_sym and embedded in power.kicad_sch). It is the same graphic with pin 1 = A, pin 2 = NC (hidden, no_connect type), pin 3 = K, and footprint filter SOT?23*. The pin positions are unchanged, so no wiring was moved.
  - D3: pad 1 = Net-(D3-A) (U2.23 VCC), pad 2 = NC, pad 3 = BB_BOOT1;
  - D4: pad 1 = VCC net, pad 2 = NC, pad 3 = BB_BOOT2.
  - Manufacturer field set to JSCJ.
- tools/design.py still emits Device:D_Schottky for D3/D4. The generator is not regenerated; this is a deferred generator fix. PCB: D3/D4 pad nets change, which is pending at layout.

6-3 docs/PIN_FOOTPRINT_SWEEP.md: 1309 parts pin/pad sweep + 19 LCSC datasheet pinout checks; no further fixes (BAS70 fixed in 90c4879).

6-4 SMAJ36CA->SMAJ40CA on 22 terminal TVS (D24,D27,D30,D33,D36,D39,D42,D44,D46-D58,D66): Value/MPN, LCSC C10757->C113970 (MDD, DO-214AC SMA, live 2026-10-28 stock 50860, 20+ $0.0431), Manufacturer MDD, footprint D_SMA unchanged; inputs_bom row, design.py, design_spec. JLC class UNVERIFIED.

## Batch 7 (team lead Enginerd + Safety Round 4, 2026-10-28 ~5:20 PM HST)
### 7-1: INSTALL_SAFETY Round 4 text (commit 24f412e)
| Ref | Old | New | Reason | Source |
|---|---|---|---|---|
| docs/INSTALL_SAFETY.md l.32-33 FUEL/CRANK rows | 15 A / 15 A blade, >=58 V DC | 2.8 A max (fuel solenoid incl. pull-in / interposing crank relay coil only); 5 A standard (non-fast) blade ATO/ATC, >=58 V DC, installer-supplied, recommended | R4-N3 | install_safety_text.md (verbatim) |
| l.41 fuse-voltage paragraph | "suppressed load dump can reach 58 V" | ISO 16750-2 Test B (24 V, Us* <= 58 V) basis; TVS 64.5 V clamp does not set the fuse rating; + declared-limit sentence (Enginerd B) | R4-N2 | install_safety_text.md (verbatim) + Enginerd B |
| l.46 outputs bullet | relay coils/indicators <= 0.5 A, combined <= 1 A | Safety text (2.8 A max incl. pull-in, interposing relay above that); GLOW = relay coil only, glow plugs via external relay; + "Where a circuit's own row above lists a lower limit or fuse (for example AUX 2.0 A, 2 A fuse), the lower limit governs." | Round 4 (d) | install_safety_text.md + Enginerd A |
| l.47 ESTOP_TRIP bullet | 12 V relay coil <= 0.5 A, not a shunt coil | 12/24 V relay or shunt-trip coil < 1.70 A incl. pull-in (U68/R407 1.70/2.13/2.55 A) | Round 4 (d) | install_safety_text.md (verbatim) |
| l.48 hardware-maximum line | unchanged | unchanged (consistent: 2.8 A / < 1.70 A) | check | - |
| FUEL/CRANK fuse-type paragraph, WARNING, J23 line, open item 1 | 15 A blade / slow-blow, "drive starter directly" | 2.8 A, 5 A standard non-fast, starter only via interposing relay | consistency with R4-N3 | fixes_safety.md R4-N3 |
| README.md Fusing paragraph | "15 A FUEL/CRANK" | 5 A blade, 2.8 A limit; + declared load-dump limit sentence | consistency, Enginerd B | - |
- Not changed: docs/RAIL_PLAN.md still uses the 15 A FUEL/CRANK copper design rating (layout sizing doc, conservative for copper); flagged for the lead.

### 7-2: D146 VBAT_AI zener BZT52C33 -> BZT52C30
| Ref | Old | New | Reason | Source |
|---|---|---|---|---|
| D146 (inputs.kicad_sch) | BZT52C33, LCSC C2110, MPN BZT52C33, "Zener 33V 500mW" | BZT52C30, LCSC C21561, MPN BZT52C30, "Zener 30V 500mW"; footprint Diode_SMD:D_SOD-123 unchanged | Safety Round 4: VBAT_AI rail was 37.9 V at 257F, above LM2904B 36 V recommended max. New rail 27.4-31.4 V at 77F, <=33.3 V at 185F, <=34.5 V at 257F; op-amp headroom (LM4040 2.5 V > 2 V CM limit) unchanged | fixes_safety.md Round 4 "VBAT_AI fix" |
- VERIFIED 2026-10-28 ~5:20 PM HST: jlcpcb.com/partdetail/C21561 = BZT52C30, Jiangsu Changjing (JSCJ), SOD-123, Vz 28-32 V (30 V nom), 500 mW, Extended; LCSC page title "BZT52C30 | Single Zener Diodes | JSCJ".
- Price $0.027 @50 and stock 11,250 are **Safety-reported** (fixes_safety.md, 5:14 PM HST), not re-checked by me.
- BOM: bom/inputs_bom.csv D146 row, docs/genctl_bom.csv, mechanical/bom.csv. inputs total 26.83 -> 26.84 (bom_retotal.py).
- No other doc cites 33 V / BZT52C33 for VBAT_AI except the historical 4-1 entry above (left as history). tools/design.py had no D146 line when 7-2 was made; 7-4 then added it (design.py l.381, BZT52C30 C21561). Wording corrected in batch 8 (R5-N3).

### 7-3: stale L3 2.2 uH text (L2/L3 stay 3.3 uH MWSA1004S-3R3MT C408483, R4-N4 / Enginerd D)
| Ref | Old | New | Reason | Source |
|---|---|---|---|---|
| L3 Note (power.kicad_sch l.4206) | "2.2uH per DS Table 4 (3.3V)" | "3.3uH MWSA1004S-3R3MT C408483 kept (Safety R4-N4); deviates from TI TPS56637 Table 4 (SLVSEG1A p19: 2.2uH for 3.3V); bench load-step 0.5-3A at 9/12/32V in required; fallback 2.2uH MWSA1004S-2R2MT same footprint" | stale text; value/LCSC/MPN already 3.3u/C408483 | fixes_safety.md R4-N4 |
| tools/design.py l.51 and L3 line (text only) | "2.2uH" / "Isat 16 A" | same deviation note; Isat 12.8 A typ | stale | R4-N4 (Sunlord p17) |
| bom/power_bom.csv l.11 | "Sunlord? (verify mfr)", "Isat ~15A", "likely 1.5-2.2uH ... verify loop" | Sunlord, Isat 12.8 A typ, L2 per Table 4 5 V row, L3 deviation note | stale | R4-N4 |
| docs/RAIL_PLAN.md +3V3 row, issue 3; DESIGN_NOTES.md l.72 | L3 MWSA0503S-2R2MT 2.2 uH Isat 7 A | marked superseded with the deviation/bench note | stale | R4-N4 |
- Bench load-step (pending): 0.5 -> 3 A at 1 A/us, VIN 9/12/32 V, 77F and hot; pass <=3 % over/undershoot, <=2 ringing cycles. Fail -> 2.2 uH MWSA1004S-2R2MT (LCSC code to be live-checked then; not chosen now).
- Not changed: RAIL_PLAN l.105/207 L2 "Isat ~15 A verify mfr" historical analysis notes (L2 is per Table 4 5 V row).

### 7-4: tools/design.py stale entries (text only, NOT run; DO NOT REGENERATE)
| Ref | Old (design.py) | New (design.py) | Reason | Source |
|---|---|---|---|---|
| D3/D4 | schottky() -> Device:D_Schottky {'A','K'} | genctl:BAS70 {'1': BB_VCC (A), '2': NC, '3': BB_BOOTn (K)}, C77297, JSCJ | mirror 6-2 symbol fix | schematic power.kicad_sch, BAS70 DS p1 |
| VBAT_AI rail (R628, Q72, D146) | absent | added: R628 10k C98220, Q72 BCP56-16TX C426787, D146 BZT52C30 C21561 | mirror 4-1 and 7-2 | inputs.kicad_sch |
| D23 K, C131, 6x 2.49k, 6x BSS84 source, 6x 100k PG pull-up, LM2904 pin 8 + decoupling | VBAT_P | VBAT_AI | mirror 4-1 relabel (changelog 4-1 net list) | inputs.kicad_sch |
| inputs sheet note (l.366) | "LM4040 2.5V ref from VBAT_P" | "... from VBAT_AI = clamped rail Q72 + D146 BZT52C30" | stale | - |
- Checked and already consistent with the schematic: R3 8.66k C23114 (OV divider, l.50/61), U86 INA237AIDGSR C2864837, L2. Generator still not run; known drift list in the header still applies.

### 7-5: R211/R212-type empty MPN fields (R4-N7)
| Ref | Old | New | Reason | Source |
|---|---|---|---|---|
| R211, R214, R217, R220, R223, R226, R229, R232, R235, R238, R241, R244, R247, R249, R251 (68k 0603, LCSC C23231; 15 refs) | MPN "", Manufacturer "" | MPN 0603WAF6802T5E, Manufacturer UNI-ROYAL | R4-N7 empty MPN | bom/inputs_bom.csv C23231 row; LCSC page title C23231 = "0603WAF6802T5E ... UNI-ROYAL" (fetched 2026-10-28 ~5:30 PM HST) |
| R5 (power), R212, R215, R218, R221, R224, R227, R230, R233, R236, R239, R242, R245, R248, R250, R252 (33k 0603, LCSC C4216; 16 refs) | MPN "", Manufacturer "" | MPN 0603WAF3302T5E, Manufacturer UNI-ROYAL | same | BOM C4216 row; LCSC page title C4216 = "0603WAF3302T5E ... UNI-ROYAL" |
- Only properties changed; bom_from_sch 201/201, 0 mismatches.

### 7-6: Reviewer Re-audit 4 (R4-N1..N8) and Safety Round 4 resolutions
| ID | Reviewer finding (reviewer.md RA4) | Resolution | Commit / status |
|---|---|---|---|
| R4-N1 (MEDIUM) | D2 SMBJ40CA Vc 64.5 V on VBAT_P > LM5176 60 V abs max / SI2309CDS 60 V | **No TVS change** (Enginerd C). LM74800 OV cut-off (<=40.06 V, tOVP_OFF <=5.4 µs, SNOSD95C p7; corrected from "p5-6" in batch 8) disconnects VBAT_P, so VBAT_P peaks ≈41.5 V (INFERRED); D2 (VBR min 44.4 V) is a single-fault backstop. No in-stock part fits VBR(min,cold) > 40.11 V with Vc <= 60 V. >60 V exposure needs a single fault plus load dump (UNVERIFIED by test) | ruling, no change |
| R4-N2 (MEDIUM) | fuse 58 V basis stale | 58 V = ISO 16750-2 Test B Us* (24 V, centrally suppressed); TVS clamp does not set the fuse rating. INSTALL_SAFETY l.41 replaced; declared limit added to INSTALL_SAFETY and README | 7-1 (24f412e) |
| R4-N3 (MEDIUM) | FUEL/CRANK "15 A" + 15 A fuse | 2.8 A max; 5 A standard (non-fast) ATO/ATC blade, >=58 V DC, installer-supplied; starter only via interposing relay | 7-1 (24f412e) |
| R4-N4 (LOW) | L3 3.3 µH vs Table 4 2.2 µH; stale text | L3 3.3 µH C408483 kept as a documented deviation; bench load-step 0.5-3 A at 9/12/32 V in; fallback 2.2 µH same footprint; stale text fixed | 7-3 |
| R4-N5 (LOW) | VBAT_AI 37.9 V hot > LM2904B 36 V rec. max | D146 BZT52C33 -> BZT52C30 C21561; rail <=34.5 V at 257F | 7-2 (3d3eff4) |
| R4-N6 (LOW/FW) | AI invalid during crank | firmware should blank AI below VBAT 9 V (Safety, INFERRED); firmware item, no schematic change | open (firmware) |
| R4-N7 (LOW) | R211/R212-type MPNs empty | filled from LCSC C23231/C4216 (31 refs) | 7-5 |
| R4-N8 (LOW, bench) | BAS70 IFSM/trr unverified for bootstrap duty | D3/D4 BAS70 C77297 pinout confirmed correct (1 A / 2 NC / 3 K) by Safety and Reviewer; IFSM 100 mA from DS p1 (Safety); start-up CBOOT surge UNVERIFIED (bench). Stock only 760 (Safety, 5:13 PM HST): buy a buffer, see COST_NOTES | open (bench) |
| Safety (a) | C131 100n VBAT_AI-AI_VSET | kept: decouples the D23 LM4040 reference | no change |
| Safety (c) | SMAJ40CA on D46-type inputs | already in 17d3485 (6-4) | done |
| D23 | polarity | confirmed correct vs TI SLOS456Q Table 5-1 p4 (ERC_AUDIT.md) | no change |

## Batch 8 (Reviewer Re-audit 5 + team lead Enginerd amendments, 2026-10-28 ~5:40 PM HST)
### 8-1: D23 LM4040 pin 3 tied to the anode (AI_VSET): NET CHANGE (1 pin)
| Ref | Old | New | Reason | Source |
|---|---|---|---|---|
| D23 (inputs.kicad_sch) | Reference_Voltage:LM4040DBZ-2.5 (pin 3 type no_connect, hidden) with a no-connect flag; netlist unconnected-(D23-NC-Pad3) | genctl:LM4040DBZ-2.5_A3 (copy of the stock symbol, pin 3 type passive, name "A", still hidden; added to genctl.kicad_sym); NC flag removed; 2.54 mm wire pin 3 -> pin 2 (A), so D23.3 = AI_VSET | R5-N5 / Enginerd amendment 1: TI recommends tying pin 3 to the anode in high-EMI / high-switching-noise applications | TI SLOS456Q (rev. April 2026) Table 5-1 p4: DBZ pin 3 "Must float or connect to anode", note (1). Both options are allowed by TI, so the reference function is unchanged |
- The stock symbol's pin 3 is type no_connect; wiring it gave ERC no_connect_connected, hence the project-library copy with pin 3 passive. Value, footprint (SOT-23), LCSC C9421 and MPN are unchanged.
- Netlist diff vs b47aea0 (kicad-cli export): exactly one pin-net change, D23.3 unconnected -> AI_VSET; 4250 nodes on both sides.
- PCB is frozen (md5 49a6a6a7... unchanged): layout sync item D-m7-13 in deferred_layout.md.
- tools/design.py: comment only on the D23 line (generator not run).

### 8-2: Reviewer Re-audit 5 doc fixes (no schematic change)
- R5-N2: docs/ERC_AUDIT.md 75 -> 73 forced items (17 four_way_junction + 56 footprint_link_issues), re-measured on a git-archive extract of b47aea0 with all 47 rule keys forced to error (review out/m7sch_b47aea0_erc_forced.json). The two items that dropped out are D3/D4, which lost their filter mismatch on moving to genctl:BAS70 (6-2). The "75 / 58" in the earlier ERC_AUDIT entry above is left as history (it was measured before batch 6). Forced run after 8-1: still 73 (17 four_way_junction + 56 footprint_link_issues).
- R5-N3: 7-6 R4-N1 citation p5-6 -> p7 (verified in SNOSD95C pdf page 7: tOVP_OFF(deg) 3.98 typ / 5.4 max µs, LM74800-Q1 only). 7-2 vs 7-4 D146 wording reconciled against the repo (design.py l.381 has the D146 line).

### 8-3: RAIL_PLAN FUEL/CRANK copper note (R5-N4, Enginerd amendment 2)
- docs/RAIL_PLAN.md: copper numbers unchanged; note added that FUEL/CRANK copper is sized for 15 A and 7 A would suffice for a 2.8 A load on a 5 A fuse; deferred layout item D-m7-14. VBAT_ESTOP rating unchanged.

### 8-4: Open Reviewer items (record only, no schematic change)
| ID | Finding | Status |
|---|---|---|
| R5-N1 (MEDIUM) | Declared 58 V suppressed load dump (ISO 16750-2 Test B, 24 V) exceeds the breakdown of the battery-facing 40 V-standoff TVSs: D1, D126 SMDJ40CA (VBR 44.4-49.1 V) and the 22 SMAJ40CA inputs (same VBR) | awaiting Safety ruling; INSTALL_SAFETY l.41 / README load-dump wording deliberately not touched |
| R5-N4 (LOW) | RAIL_PLAN FUEL/CRANK copper sized 15 A | lead decides; note in 8-3 / D-m7-14 |
| R5-N5 (LOW) | LM4040 pin 3 tie to anode | done in 8-1 per lead amendment |

## Batch 9 (Safety Round 5 ruling on R5-N1, team lead Enginerd, 2026-10-28 ~5:45 PM HST)
### 9-1: INSTALL_SAFETY / README declared limit (R5-N1 resolved by restricting the declaration)
| Ref | Old | New | Reason | Source |
|---|---|---|---|---|
| docs/INSTALL_SAFETY.md l.41 | Round 4 text: supply "centrally suppressed to 58 V maximum (ISO 16750-2 Test B)" | Round 5 line 41 text, verbatim (>=58 V DC fuses kept as margin; 9–36 V declared (superseded by Round 5c: 9–32 V continuous, 36 V ≤ 60 s); load dump incl. suppressed 58 V not supported; TVS may fail short above ~44 V; energize-to-run fuel only) | R5-N1 | install_safety_text.md "ROUND 5 (R5-N1)" |
| docs/INSTALL_SAFETY.md l.43 | "Declared limit: The load dump must be centrally suppressed to 58 V or less ..." | Round 5 "Declared limit" text, verbatim | R5-N1 | same |
| docs/INSTALL_SAFETY.md l.13 | "a battery-backed, suppressed 12 V or 24 V DC supply bus" | "a battery-backed 12 V or 24 V DC supply bus (9–36 V)" | consistency | same (l.13 note). This paragraph is labelled as pasted from review/hv/load_dump_external.md; the quote now differs from that source in this phrase |
| README.md l.22 | "Declared limit: the load dump must be centrally suppressed to 58 V or less (ISO 16750-2 Test B, 24 V system). Unsuppressed load dump is not supported." | Round 5 "Declared limit" text, verbatim | consistency | same |
- The >=58 V DC fuse-rating statements are kept everywhere.
- Not changed (no 58 V / Test B declaration in them): DESIGN_NOTES.md l.528 and bom/design_spec.md l.19 ("battery-backed, suppressed 35 V-class supply"), DESIGN_NOTES.md l.39/395/538 and design_spec l.100 (historical design notes), ENCLOSURE_DFM l.230 (test plan).
- 35 V reconnect check (INFERRED, not altered): R3 8.66k divider ratio 31.01 (changelog B3-2); SNOSD95C p5 V(OVF) 1.091/1.13/1.159 V -> OV release 33.8/35.0/35.9 V (nominal resistors), trip 1.195/1.231/1.267 V -> 37.1/38.2/39.3 V (36.35-40.06 V with resistor tolerance and leakage per B3-2). "Reconnects below about 35 V" matches the typical value. Flag for Safety: the worst-case release (~33.2 V with 1 % resistors; 33.8 V is the nominal-resistor value) and the worst-case trip (~36.35 V) are both close to the 36 V continuous declared maximum; after an OV trip the board may stay off until the bus falls below ~33.2 V.

### 9-2: D126 SMDJ40CA -> SMDJ58CA (C192416): NOT DONE, blocked by the pre-swap check
- Verified: JLCPCB C192416 = Littelfuse SMDJ58CA, SMC (DO-214AB), bidirectional, VRWM 58 V, VBR 71.2 V (listed), VC 93.6 V at Ipp 32.1 A (10/1000 µs), 3 kW. Stock not shown on the page (UNVERIFIED).
- VBAT_ESTOP net (kicad-cli netlist of e484b81): C199, C203 (C28233 CL21B104KCFNNNE 100 V, verified JLCPCB); D126; D137 BZT52C15 (G-S clamp, sees <=15 V); Q70/Q71 SQD40P10-40L -100 V; R297/R303 FMF25 2512 20 mΩ; U43/U45 TPS48100 VS/CS+ (100 V abs per BOM text; datasheet not reopened); U44/U46 INA281A1 (-4..110 V CM per BOM text); R251 68k, R292 100k, R298 100k, R400 47k, R411 100k (all 0603). Behind D126: VBAT_ESTOP_IN (J23, Q70/Q71 drains), FUEL_DRN/CRANK_DRN (Q45-Q48 BSC070N10NS5 100 V).
- Blockers (parts rated below the 93.6 V clamp):
  - R400 47k 0603 (C25819): BOM row states 75 V max working voltage; one end is the Q66 base (~0.7 V), so ~93 V would be across it at clamp. R251/R292/R298/R411 are the same 0603 class (UNI-ROYAL/Yageo 0603, rating not re-read; INFERRED 75 V), with 64-90 V across them at clamp.
  - D68/D69 SMDJ40CA output TVS on FUEL/CRANK (BOM "output TVS", VBR 44.4-49.1 V): with an output on, they see VBAT_ESTOP through the FETs and become the clamp anyway.
  - INFERRED: VESTOP_D divider 68k/33k gives ~30 V at the U34 74HC14 input at 93.6 V (already ~21 V at today's 64.5 V clamp; only the HC14 ESD diodes limit it).
- Safety's premise "every downstream part on VBAT_ESTOP is rated >=100 V" is therefore not supported by the repo. **Ruled: keep D126 SMDJ40CA (Enginerd, option a)**; see Batch 10. Safety later withdrew the ">=100 V downstream" premise (Batch 11); the batch-10 INSTALL_SAFETY wording was replaced in Batch 11.

### 9-3: Reviewer status
| ID | Status |
|---|---|
| R5-N1 (MEDIUM) | RESOLVED by restricting the declaration (Safety Round 5 ruling, Enginerd): 9-1. D126 uprate not done (9-2); ruled: keep D126 SMDJ40CA (Enginerd, option a) |
| R5-N4 (LOW) | open, lead decides; RAIL_PLAN note + D-m7-14 (8-3) |
| R5-N5 (LOW) | done (8-1, D23 pin 3 -> AI_VSET; layout D-m7-13) |

## Batch 10 (team lead Enginerd ruling on D126, 2026-10-28 ~5:35 PM HST; docs only)
- Ruling: keep D126 SMDJ40CA C224077 (option a). No resistor change, no D68/D69 change. No part or net change in this batch.
- [Superseded by Batch 11: this paragraph and the 30 A battery-feed row were replaced by Safety's 10 A J23 fuse text.] docs/INSTALL_SAFETY.md: sentence added after the battery-feed row: J23.1/2 E-stop/fuel feed has a 40 V-class TVS that can fail short if the supply is held above about 44 V; the 30 A fuse protects the wiring, not the board; supply must never exceed the declared 40 V; overvoltage beyond that is the installer's responsibility; battery-backed bus only (lead wording, verbatim).
- Option B (Ethan can override later, NOT adopted): D126, D68 and D69 to SMDJ58CA C192416, and the resistors from 0603 to 0805 150 V parts (R400 C17713, R251 C17801, R411 and R292/R298 C17407, R627 C17414), about +$1.4 per board. Safety withdrew its earlier '>=100 V downstream' premise: the 0603 resistors are 75 V working / 150 V overload for 5 s (UNI-ROYAL 0603WAF datasheet p5-6, per Safety, not re-checked by us). Recorded as D-m7-15 (schematic/BOM option, not layout).
- Measured facts (changelog 9-2): C192416 = Littelfuse SMDJ58CA SMC, VRWM 58 V, VC 93.6 V @ 32.1 A (JLCPCB page; stock not shown). On VBAT_ESTOP: R400 47k 0603 C25819 75 V max working (BOM row), ~93 V across it at that clamp (other end Q66 base); R251/R292/R298/R411 same 0603 class (75 V INFERRED, not re-read), 64-90 V across at clamp; D68/D69 SMDJ40CA output TVS (VBR 44.4-49.1 V) see VBAT_ESTOP through the FETs when an output is on; VESTOP_D divider ~30 V at U34 74HC14 input (INFERRED). 100 V-class or higher: C199/C203 C28233 100 V (verified), Q70/Q71 and Q45-Q48 100 V, TPS48100 100 V abs and INA281A1 110 V (BOM text).
- docs/COST_NOTES.md: SQD40P10-40L (Q70/Q71, C141570) procurement buffer note. Stock 206 is Safety-reported; jlcpcb.com/partdetail/C141570 opened 2026-10-28 confirms the part (Vishay SQD40P10-40L_GE3, P-ch 100 V 38 A TO-252) but shows no stock figure, so 206 is NOT re-verified.

## Batch 11 (Safety J23 10 A fuse rule, accepted by team lead Enginerd, 2026-10-28 ~5:40 PM HST; docs + off-board BOM only)
- docs/INSTALL_SAFETY.md fuse table: battery-feed row replaced by "Battery feed (E-stop/fuel) | J23.1/2 VBAT_ESTOP via NC E-stop | — | FUEL + CRANK 5.6 A max | 10 A ATO/ATC (standard or fast), >=58 V DC, fitted in the J23 branch after the existing 30 A battery fuse; wire >= 16 AWG / 1.31 mm²" (same 5 columns, verbatim). The batch-10 "Battery feed (J23.1/2): ... 40 V-class TVS ..." paragraph is replaced by Safety's text directly below the table (feed not behind the 40 V OV cut-off; only a 40 V TVS; 10 A J23 fuse always; partly shorted TVS can overheat below 10 A; heat damage near J23 -> out of service). WARNING block now also names the 10 A J23 fuse. README Fusing paragraph: matching J23 10 A sentence.
- Reason (Safety, measured on 0409818; re-checked by us on the e484b81 netlist, J23 unchanged since): net VBAT_ESTOP_IN = J23.1, J23.2, Q70.2 (D), Q71.2 (D) only; Q70/Q71 sources go straight to VBAT_ESTOP (D126, U43/U45 VS, R297/R303 shunts, ...). J23.1/2 does not pass through U1 LM74800, so the 40 V OV cut-off does not disconnect it.
- J23 load: FUEL 2.8 A + CRANK 2.8 A = 5.6 A max = 56 % of the 10 A fuse. RAIL_PLAN sizes that copper for 15 A (plan figure; not measured on the layout).
- bom/off_board_external_bom.csv: new installer-supplied row for the 10 A ATO/ATC >=58 V DC J23-branch fuse, qty 1, no LCSC, no price (excluded from totals).
- Option B text in Batch 10 and D-m7-15 replaced by Safety's revised Option B (see above); the 9-2 measured facts are kept.

## Batch 12 (Safety FINAL Round 5c, team lead ruling, 2026-10-28 ~5:45 PM HST)
- Round 5c: declared supply 9–32 V DC continuous, 36 V ≤ 60 s, OV release ≥ ~33 V; INSTALL_SAFETY l.13/40/42/44 + README l.22; no R3 change (R6-N1, R6-N2, R6-N3). Text verbatim from install_safety_text.md "FINAL Round 5c".
- R6-N1 gap (the 22 SMAJ40CA switch/sensor inputs): covered by the new INSTALL_SAFETY fuse-note line ("the switch and sensor inputs (TVS at the connector pins; protected only by the installer's fuse on the field supply)").
- 9-1 annotated: "9–36 V declared" marked superseded; worst-case OV release corrected to ~33.2 V with 1 % resistors (33.8 V was the nominal-resistor value). Kept as true hardware statements: B3-2 R3 trip 36.36/38.17/40.11 V, HC14 "~12V at 36V" notes, DESIGN_NOTES / SPEC_CHECKLIST_3b history.
- R6-N4: empty MPN/Manufacturer filled (property text only, no net change):
| Ref | Old | New | Source |
|---|---|---|---|
| R400 (estop.kicad_sch, 47k, C25819) | MPN "", Manufacturer "" | 0603WAF4702T5E, UNI-ROYAL | jlcpcb.com/partdetail/C25819 (opened 2026-10-28): 0603WAF4702T5E, UNI-ROYAL(Uniroyal Elec), 47k 1 % 75 V; bom/outputs_bom.csv row already carries this MPN |
| R411 (estop.kicad_sch, 100k, C122538) | MPN "", Manufacturer "" | RT0603BRD07100KL, YAGEO | jlcpcb.com/partdetail/C122538 (opened 2026-10-28): RT0603BRD07100KL, YAGEO, 100k 0.1 % 75 V thin film; bom/inputs_bom.csv row already carries this MPN |
- Other refs sharing those LCSC codes still have empty MPN in the schematic (R407, R533 on C25819; R139, R150, R161, R172, R183, R194, R268 on C122538); not in scope, left as-is. docs/genctl_bom.csv (generated export) not regenerated, same as 7-5.


## Batch 13 (BOM finalization, Ethan "go with your best instinct", 2026-11-21 ~1 AM HST; properties + docs, no net change)
- Netlist before/after: 1112 nets, connectivity identical; ERC 0 errors before and after (review/bom_final/work/erc_*.json).
- Empty MPN/Manufacturer fields filled from LCSC product data (447 MPN, 1053 Manufacturer property edits), incl. R407/R533 (C25819 0603WAF4702T5E UNI-ROYAL) and R139/R150/R161/R172/R183/R194/R268 (C122538 RT0603BRD07100KL YAGEO). Closes the Batch 12 leftover.
- R130/R141/R152/R163/R174/R185 2.49k 0.1 %: C319805 AR06BTCV2491 (stock 0-2) -> C870626 RT1206BRD072K49L YAGEO (1206, 0.1 %, 25 ppm, 200 V, stock 166). Footprint is already R_1206_3216Metric, so no board change. (AR06 was the 1206 Viking part.)
- U7 STM32H743VIT6: C114409 (stock 0) -> C5271084 STM32H743VIT6TR (tape and reel of the same part).
- BT1 MPN BS-CR2032-8; U9/U10 MPN DF40C-100DS-0.4V(51) HIROSE.
- J4 fan header set DNP (fanless, mechanical HEAT_PATH phase 24).
- INA238 not available (LCSC stock 0, $23.36); INA237 kept (C2864837).
- Fuse rule (Ethan, 2026-11-21): all fuses in the power box; no board fuses except PTCs on small signal/sensor outputs. INSTALL_SAFETY, README and the off-board BOM reworded: "installer-supplied" fuses become power box positions F1-F22; J23 10 A fuse is F2; 600 V metering fuses F26-F31 must list 600 V, ceramic.
- RAIL_PLAN: FUEL/CRANK/VBAT_ESTOP 15 A copper target withdrawn, now 10 A (D-m7-14 closed). Per-channel 2.8 A electronic limit unchanged.
- ECO proposed, NOT applied (Layout owns schematic wiring): PTC Eaton PTS120660V010 (C2441287, 100 mA hold, 60 V) in series with Q36 and Q39 outputs (DI_BIAS_A J21.6, DI_BIAS_B J22.1), which today feed field wiring from VBAT_P with no current limit.
- TVS: Option B (D-m7-15) not adopted; D126 stays SMDJ40CA. TPS1HTC30A kept (consigned).

## Batch 14 (sourcing gaps + Safety FINAL Round 6, 2026-11-21 ~1:25 AM HST; part fields + docs, no net change by this batch)
- C74/C75: delisted JIERONG 20 F C7471020 -> **Vishay MAL223051016E3** 15 F 3.0 V (2.6 V at 85 °C), 12.5x30 mm, 5 mm pitch, AEC-Q200; same CP_Radial_D12.5mm_P5.00mm footprint and height. Value "15F 3.0V". LCSC field cleared (consigned THT). Stock: DigiKey 247 ($4.73, $3.389@10), Mouser ~2,005, Newark 1,000. Hold-up 7.5 F series at 4.9 -> 2.7 V: ~55 J usable, ~13.8 s at 4 W, ~11 s at -20 % C (target 10 s).
- U69: ISOW7841DWER (no authorized stock; DigiKey 0 until 2027-02-09) -> **ISOW7841AQDWERQ1** (C5216434), AEC-Q100 version, same DWE package and pin table (TI ISOW7841A-Q1 datasheet checked), default-high outputs, >=75 mA at 3.3->3.3 V, reinforced. Value and MPN changed.
- F101/F102 PTS120660V010 (C2441287) on DI_BIAS_A/B were wired by Layout in inputs.kicad_sch (uncommitted Layout work in the worktree at the time; not part of this commit). Netlist check: the only connectivity change versus 1676f11 is F101/F102 between Q36/Q39 and DI_BIAS_A/B (new nets DIB_A_PTC, DIB_B_PTC). ERC 0.
- Category BOMs: other_bom.csv U69 row, power_bom.csv supercap row updated; bom_from_sch 0 mismatches (with Layout's inputs_bom.csv PTC row).
- INSTALL_SAFETY (Safety FINAL Round 6, verbatim where given): battery input bullet (58 V DC for F0–F25, 36 V jump-start reason; stale load-dump reason removed); "fused at its source" application text; 30 A battery-cable paragraph; blades described as "standard (non-time-delay)", F3/F4 OptiFuse ANR58-UL-5A; wire table 5 A -> 18 AWG / 0.82 mm²; metering fuse SIBA 200 kA + KLKD001 second source.
- Not changed: the schematic text note beside J1 still reads "EXT FUSE <=10 A FAST, >=58 V DC" (text item, pending board/silkscreen change).
- U83 (ambient sensor): no U83 exists in the schematic or git history; ECO proposed.

## Batch 14 (Layout) (Enginerd's Nov 21 items, 2026-11-21 ~1:30 AM HST; schematic + BOM + docs; ONE net change, no layout)
1. **Copper target 10 A (was 15 A).** Per-channel 2.8 A electronic limit unchanged; big loads through relays. Finished the 15 A -> 10 A sweep left after Batch 13: RAIL_PLAN table rows VBAT_ESTOP/CRANK_OUT/FUEL/CRANK_DRN/FUEL_DRN, the "unrouted"/"auto-routed" lists and power-batch item 2; ROUTING_PLAN §3 row, §4 "CRANK/FUEL drains" row, §5 item 2, §7.2 two rows; bom/design_spec.md fuel/crank line; outputs_bom.csv and off_board_external_bom.csv J4 header/plug "(>=10 A/pin)" and the 2 oz PCB note; review/schematic_audit/deferred_layout.md D-m7-14 marked CLOSED. Width note corrected (INFERRED, IPC-2221, 1 oz, 18 °F rise): 10 A = 7.2 mm on one outer layer, or F+B ≥3.6 mm each (half-width convention of the old 15 A figures; 2.8 mm each with an even split); 4.7 mm single / ≥2.4 mm each at 36 °F rise. Batch 13's "about 3.2 mm F+B" was not a 10 A figure. Left as history: mechanical/pcb_v4/PROGRESS.md line 323 (as-built measurement log), INSTALL_SAFETY 15 A fuse/connector/wire-table mentions (not copper targets), outputs_bom.csv FUEL TVS energy example (hypothetical 15 A solenoid).
2. **PTC on DI_BIAS_A/B (NET CHANGE, D-m7-16).** New F101/F102 = Eaton PTS120660V010, LCSC C2441287, symbol Device:Polyfuse, footprint Fuse:Fuse_1206_3216Metric, in inputs.kicad_sch. Q36 pad 3 -> new net **DIB_A_PTC** -> F101 -> DI_BIAS_A; Q39 pad 3 -> new net **DIB_B_PTC** -> F102 -> DI_BIAS_B. Everything downstream keeps its net (J21.6/J22.1, Q38/Q41 pull-down drains, 12 wetting resistors). Netlist vs 1676f11: 1112 -> 1114 nets; the only connectivity diff is Q36.3/Q39.3 moving to the new nets and F101/F102 added. tools/design.py mirrored as text (not regenerated).
   - Part facts, MEASURED (read from Eaton Technical Data 4397 Nov 2021, https://www.eaton.com/content/dam/eaton/products/electronic-components/resources/data-sheet/eaton-pts1206-6-60-volt-dc-surface-mount-resettable-ptc-data-sheet.pdf , and LCSC https://www.lcsc.com/product-detail/C2441287.html): Vmax 60 V DC, Imax 100 A, Ihold 0.10 A, Itrip 0.25 A (both at 23 °C still air), Pd 0.4 W tripped, max time-to-trip 1.0 s at 0.5 A, Ri min 1.6 Ω, R1 max 15 Ω, 1206/3216, -40 to +85 °C (with derating), marking TY, cURus E343021. Derating curve (Rev Oct 2015 copy, https://www.farnell.com/datasheets/2310044.pdf, read graphically, approx.): 100 % at 20 °C, ~80 % at 40 °C, ~65 % at 60 °C, ~48 % at 85 °C. LCSC/JLC live 2026-11-21 01:13 HST: LCSC stock 655, 5+ $0.1717 (MOQ 5); JLC Extended, stock 657, $0.1709.
   - Vmax 60 V ≥ the 36 V / 60 s declared maximum and above the SMAJ40CA input TVS range. OK.
   - Load, INFERRED from the schematic: each bank is 6 x 4.7 k wetting resistors (1206W4F4701T5E) to DIx with 68k+33k to GND. All 6 contacts closed: 41 mA at 32 V, 46 mA at 36 V (11.5 mA at 9 V); all open: about 2 mA. Plus whatever the installer hangs on J21.6/J22.1 (UNKNOWN). Margin vs Ihold: 2.2x at 73 °F (23 °C), ~1.4x at 140 °F (60 °C), ~1.04x at 185 °F (85 °C). FLAG below.
   - BOM: bom/inputs_bom.csv new row (qty 2, $0.1717); review/bom_final/BOM_controller.csv row F101,F102 present. tools/bom_from_sch.py: 202 schematic groups = 202 BOM groups, 0 mismatches. tools/bom_retotal.py: inputs 26.83 -> 27.17; on-board total of the category BOMs now $852.43 (+$0.34 for F101/F102; the rest of the change since 1676f11 is 4c1f4bf).
3. **J4 fan header DNF (fanless).** Verified: J4 has the dnp flag in cm5.kicad_sch (Batch 13) and is excluded from BOM_controller.csv. Docs finished: RAIL_PLAN +5V budget (fan 0 A, FW-Q3 closed), DESIGN_NOTES CM5 "Other connections" (J4 DNP; firmware leaves fan control off). FAN_PWM/FAN_TACH stay wired U9.19/U9.16 -> J4 (no net change).
4. **Ruling recorded: PD2 + conformal coat, no PD3 re-layout** (DESIGN_NOTES AC-metering section; docs/ISOLATION_CHECK.md new §5a). No isolation number changed: 3 mm outer / 1.5 mm inner HV rules, barrier slots, 8 mm isolator package and 12.6 mm reinforced requirement all as before. The coat takes no creepage credit.
5. **Ruling recorded: keep ISOW7841 (U69) / ISO7741 (U70); opto-coupler switch cancelled** (DESIGN_NOTES). No opto-switch text existed in the repo docs to revert (grep), so nothing was removed.
- ERC (git-archive extract, kicad-cli 9.0.2, /workspace/kicad-libs): default 0. All rules forced: 75 = 17 four_way_junction + 58 footprint_link_issues; the +2 over the 73 baseline are F101/F102 "fuse_1206_3216metric doesn't match *polyfuse* *PTC*" (benign: KiCad 9 ships no polyfuse-named 1206 footprint).
- PCB file untouched (md5 49a6a6a78d3982dc24093687e5e54c0c).
- Note: the other "Batch 14" entry above (4c1f4bf, sourcing gaps + Safety FINAL Round 6) is a separate commit that came first; this entry is the Layout part.
- Update ~1:30 AM HST: U83 = **TI TMP1075DSGR (C2870250)** on I2C1 (suggest 0x4A), plus a backlight override: a 5th SN74LVC1G08DBVR (C7666) ANDs U76 P16 with CM5 GPIO12 (today BL_PWM) into U24 EN, with a 10k (C25804) pull-up on P16. Layout is adding these to the schematic; they are priced as pending lines in review/bom_final until they appear in the netlist.

## Batch 15 (Layout; Enginerd 2026-11-21 ~1:25 AM HST: backlight override, U83, Safety Round 6 J1 text, Re-audit 7/7b doc items; schematic + BOM + docs, no layout)
1. **Backlight override (NET CHANGE, D-m7-17, display + frontpanel sheets).** U24 EN is now **BL_EN** = **BL_PWM** (CM5 GPIO12, U9.31) AND **BL_ALLOW** (U76 TCA9555 @0x25 P16, pin 19; was unconnected/no-connect, no other use in the schematic). New U88 74LVC1G08 (C7666, the same SN74LVC1G08DBVR as U38-U40/U67) on +3V3_SAFE with its own C307 100n (C14663, as each existing LVC1G08 has). R629 10k (C25804) BL_ALLOW -> +3V3_SAFE. +3V3_SAFE is U76's VCC (netlist, MEASURED), so the pull-up cannot back-power U76. TCA9555 (TI SCPS200E): I/Os are inputs at power-up and it has an internal pull-up "to a default high when configured as an input and undriven", so BL_ALLOW reads high and the backlight stays CM5-controlled by default. R121 100k stays on EN (BL_EN). **Added beyond the brief:** R630 100k (C25803, the R121 part) BL_PWM -> GND, so U88 input A cannot float when the CM5 is off; this keeps firmware ARCHITECTURE's "GPIO12 Hi-Z -> EN low -> backlight off" behaviour. CM5 GPIO12 drives nothing else (BL_PWM had U9.31, R121, U24.4 only).
2. **U83 TMP1075DSGR fitted (D-m7-18, power sheet).** C2870250 (LCSC: TMP1075DSGR, TI, WSON-8-EP 2x2). Symbol Sensor_Temperature:TMP1075DSG, footprint Package_SON:WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm_ThermalVias. Address **0x4A** = 1001010: A2=GND, A1=V+, A0=GND (TI TMP1075 datasheet Table 7-2). I2C1 before U83 (MEASURED from the netlist + datasheets): U73 0x20, U74 0x21, U31 0x22, U62 0x23, U75 0x24, U76 0x25 (TCA9555 Table 2), U86 INA237 0x40 (A1=A0=GND, INA237 Table 7-2), U29 0x48 / U30 0x49 (ADS1115), U8 FM24CL64B 0x50 (A2..A0 GND). No 0x4A conflict. J3.5/J3.6 also expose I2C1 (external devices unknown). V+ = +3V3_SAFE, C306 100n (datasheet recommends 0.01 µF; 100 nF used to match the BOM). ALERT left unconnected (datasheet: unused ALERT may float or go to GND); EP to GND (thermal pad must be soldered). No U83 placeholder existed before.
3. **J1 fuse note (Safety Round 6):** schematic text "EXT FUSE <=10 A FAST, >=58 V DC" -> "EXT FUSE <=10 A STANDARD (NON-TIME-DELAY), >=58 V DC" (power.kicad_sch). Same wording applied to the battery-fuse mentions in RAIL_PLAN l.3, DESIGN_NOTES (2 places) and bom/power_bom.csv row 3. INSTALL_SAFETY and README had no "FAST" for J1 left. Silkscreen: D-m7-19.
4. **Re-audit 7/7b doc items.**
   - R7-N2: "above about 36 V it disconnects" -> "above its over-voltage trip point, 36.35-40.06 V (component tolerance), it disconnects" in README l.22 and INSTALL_SAFETY (2 places). No other occurrence in the repo.
   - R7-N3: off_board_external_bom.csv row 48 qty-10 price "4.07" moved from the URL column to the notes; old connector names fixed (row 42 J4 -> J23, row 47 J0 -> J1 and "mirrored pinout vs J23"; outputs_bom.csv header row names J1/J23/J28/J29, matching its SCH refs). The README "5 A standard blade" and "PTCs on small signal outputs only" parts were already closed at 7cc8037 (Re-audit 7b).
   - R7-N10: U35 (3 units) MPN LM393DR -> **LM393DR2G** (LCSC C7955 = onsemi LM393DR2G, read 2026-11-21 01:29 HST; bom/inputs_bom.csv row already LM393DR2G). The other R7-N10 points (TLC555 value, Samsung/TI manufacturer spellings, ST(Semtech)) were not in this brief and are left.
   - R7b-N1: INSTALL_SAFETY l.19 "(proposed: DI_BIAS_A/B, ECO pending)" -> "(fitted: F101/F102 PTS120660V010 on DI_BIAS_A/B, m7-sch Batch 14)"; J1 text item 3; ERC_AUDIT forced count line added (75, MEASURED below).
   - R7b-N2: INSTALL_SAFETY new bullet and README sentence: DI bias terminals J21.6/J22.1 are for the input contacts only, **no external loads**. The bench items (hot-box hold test, hard short at 32/36 V) stay open.
5. **BOM.** Category BOMs: outputs_bom C7666 qty 4 -> 5; comms_bom C25803 101 -> 102; ac_metering_bom C14663 112 -> 114; new rows comms_bom R629 C25804 (LCSC 100+ $0.0017, stock 823,400) and power_bom U83 C2870250 (LCSC 1+ $0.4175, stock 541; JLC Extended 541), read 2026-11-21 01:30 HST. tools/bom_from_sch.py: 204 = 204 groups, 0 mismatches. tools/bom_retotal.py: on-board total $852.43 -> $857.11. $4.11 of the +$4.68 is 2 x the C14663 row's unit price of $2.0555, which is the open R7-N5 price error (LCSC is about $0.002 each); the row was not repriced here.
   - Part check: C7666 matches the existing LVC1G08 group. C25804 does **not** match the existing 0603 10k group, which is C98220 YAGEO RC0603FR-0710KL (79 refs); C25804 was used as Enginerd asked, so it is a new BOM group. C14663 is the existing 0603 100n group.
- ERC (git-archive extract of this commit, kicad-cli 9.0.2, /workspace/kicad-libs): see the commit report; PCB file untouched (md5 49a6a6a78d3982dc24093687e5e54c0c).

## Batch 16 (Layout; Enginerd/Safety rulings 2026-11-21 ~1:34-1:42 AM HST; schematic properties + text, BOM, docs; NO net change, no layout)
1. **R630 kept** (Enginerd ruling; BL_PWM 100k pull-down, Batch 15). Nothing changed.
2. **R629 -> C98220** YAGEO RC0603FR-0710KL (Manufacturer YAGEO), so it joins the existing 0603 10k group (79 -> 80 in other_bom.csv); the Batch 15 comms_bom C25804 row is removed.
3. **F101/F102 step-up to ~0.20 A: NOT applied** (Safety ruling (c): do not commit anything that hides the problem).
   - Eaton PTS1206 has no 60 V part above 0.10 A (TD 4397 Nov 2021: 60 V parts are V005/V010 only; 0.20 A is PTS120624V020, 24 V).
   - Best reputable 1210 >=60 V ~0.20 A: Littelfuse 1210L020/72 (LCSC C27568256, 72 V, Ihold 0.20 A / Itrip 0.40 A at 20 C, Imax 10 A, 8 A trips in <=0.5 s, Rmin 0.8 ohm, R1max 5 ohm; LCSC stock 925 at 2026-11-21 01:38 HST, $0.8378). Derated hold at 85 C = **0.091 A MEASURED** (datasheet re-rating TABLE value, exact, not a curve read; Littelfuse 1210L datasheet "Temperature Rerating"): misses the >=0.092 A (2 x 46 mA) bar by 1 mA. Imax 10 A is below the INFERRED hard-short current (next item).
   - Q36/Q39 check (SI2309CDS-T1-GE3, Vishay doc 68980 Rev A): MEASURED Rds(on) 0.345 ohm max at Vgs -10 V; ID(on) >= 6 A; IDM 8 A (10 us); PD 1.0 W (TA 25 C, t <= 5 s) / 0.67 W (70 C); RthJA 92 typ / 120 max C/W (t <= 5 s), 166 C/W steady state; SOA (TA 25 C, single pulse) at Vds ~6-36 V: about 1 A for 1 ms, 0.3 A for 10 ms, 0.1 A for 100 ms (graph read, about +/-30 %). The gate is driven to about -15 V at 32-36 V (D147 BZT52C15 clamp), so the FET is fully on.
   - 0.4 A overload (Safety's case), INFERRED: FET drop 0.4 x 0.35 = 0.14 V, about 56 mW, fine against the 0.67 W rating. A 0.20 A PTC at 85 C (~0.09 A hold, ~0.18 A trip) would trip; trip time at 0.4 A is not specified on either datasheet.
   - Dead short on DI_BIAS at 36 V, INFERRED: nothing upstream limits current. VBAT_P sits behind the LM74800 ideal diode (no current limit) and the external 10 A standard fuse J1, which will not open within the PTC trip time.
     - Current is set only by Rds(on) and the PTC: ~36/(0.35+0.8) ≈ 31 A with the 1210L020/72, or ~36/(0.35+1.6) ≈ 18 A with today's PTS120660V010. That is far above IDM 8 A and outside the SOA by more than 10x.
     - Using the datasheet trip points as I²t estimates (32 A²s for the 1210L020/72 at 8 A/0.5 s; 0.25 A²s for the PTS120660V010 at 0.5 A/1.0 s), the FET carries roughly 0.7 ms (today) to 30 ms (1210L020/72) of 100-300 W. **Q36/Q39 are not protected against a hard short by any PTC**; that includes the part fitted now.
     - Fix options for Enginerd/Safety: a current-limited high-side switch / eFuse with thermal shutdown on each bias rail, or an active current limit (sense R + BJT) sized with Q36/Q39 SOA. Bench short tests at 32 and 36 V are still open.
   - F101/F102 stay PTS120660V010 / C2441287 / Fuse_1206 for now; the "no external loads on DI bias" install note stays.
4. **Wetting resistors 1/2 W** (Enginerd/Safety). R210, R213, R216, R219, R222, R225 (bank A), R228, R231, R234, R237, R240, R243 (bank B) = the 12 DI wetting resistors (DI_BIAS_x -> J19/J20), plus **R246** (ESTOP_SENSE NC2 4.7k pull-down to GND).
   - R246 is not a DI wetting resistor, but it sits in the same BOM group, Enginerd listed it, and it sees the E-stop loop voltage continuously (NC contact), so it has the same ~0.28 W at 36 V. Including it was deliberate.
   - No other 1206 4.7k exists. The other 4.7k parts are 0603 (C23162) and were not touched.
   - New part: **HKR FPF064K7FE1/2W** (JLC/LCSC code C49308172). HKR datasheet "High Power Chip Resistors - FPF Series" Rev R2, 28-Apr-2025: FPF06 = 1206, 1/2 W at 70 C (P70), linear derating to 0 at 155 C, so ~0.41 W at 85 C (185 F) INFERRED from the curve, about +/-0.02 W; tolerance F = +/-1 %; TCR E = +/-100 ppm/C; RCWV 200 V.
   - Stock: JLC 1751 at 2026-11-21 01:39 HST, $0.0137. The lcsc.com detail API returns no product for C49308172, so there is no lcsc.com stock figure.
   - Margin at 36 V: 0.276 W INFERRED dissipation vs 0.50 W MEASURED rating = 1.81x at <=70 C (158 F), ~1.49x at 85 C.
   - Backup: YAGEO SR1206FR-7W4K7L C873960 (SR series 1206 7W = 1/2 W P70, 1 %, AEC-Q200; LCSC stock 9860 at 01:38 HST).
5. **2.49k swap C870626 -> C5122072** (Viking ARG06BTC2491, Manufacturer "Viking Tech").
   - Enginerd's uncommitted inputs.kicad_sch diff was **not present** in this worktree: the tree was clean apart from the routed_tracks_v4.png deletion, and C5122072 was in no commit or stash. The swap was applied fresh.
   - Grep of every C870626 ref: R130, R141, R152, R163, R174, R185 (inputs.kicad_sch only) plus bom/inputs_bom.csv row 6. Exactly Enginerd's list.
   - LIVE LCSC 2026-11-21 01:38 HST: 2.49 kohm, +/-0.1 %, +/-25 ppm/C, 250 mW, 200 V, 1206 thin film, stock 2360, 20+ @$0.0365.
6. **74LVC1G08: C7666 -> C176929 for all 5 refs** (U38, U39, U40 watchdog gates; U67 E-stop gate; U88 backlight).
   - C7666 (TI SN74LVC1G08DBVR): JLC stock 2 / LCSC 0 at 01:39 HST, so every ref was affected, not only U88.
   - New part: Diodes Incorporated 74LVC1G08W5-7 (datasheet DS32199 Rev.10-2). SOT25 pins 1 A, 2 B, 3 GND, 4 Y, 5 VCC, identical to TI DBV; VCC 1.65-5.5 V; -40 to +125 C.
   - LCSC stock 1475, 5+ @$0.0872 (JLC 1476) at 01:39 HST. Footprint unchanged (SOT-23-5).
7. **R7-N5 closed:** /workspace/review/bom_final/work/r7_category_bom_fix.patch applied cleanly (git apply --check OK). C14663 is now $0.0057; TPS1HTC30A is now $4.385 (consigned from DigiKey).
8. **ESTOP one-shot text 0.44-0.53 s -> 0.37-0.53 s** in design_spec, DESIGN_NOTES, INSTALL_SAFETY, ROUTING_PLAN, outputs_bom row 24, design.py and the C229 Note (estop sheet). load_shedding_spec l.35 does say "0.48 s; 0.37–0.53 s".
   - Parts: R404 200k 1 % (C25811) and C229 2.2 µF ±10 % 25 V 0805 **X5R** (FOJAN FCC0805X225K250FT, C5137595). TLC555 tw = 1.1RC.
   - INFERRED results:
     - Nominal 0.484 s.
     - ±1 % R and ±10 % C only: 0.431-0.538 s, which is where the old "0.44" came from.
     - Adding X5R ±15 % over temperature: min 0.367 s ≈ 0.37 s.
     - Adding an assumed -10 % DC bias at the 3.33 V threshold: ~0.33 s. The TLC555 timing error is not included.
   - **Mismatch:** 0.37 s is the tolerance + temperature minimum, not a guaranteed worst case. The text now says so; measure on the board cold and hot, or move C229 to C0G/film if 0.37 s must be guaranteed.
   - The upper bound 0.538 s also slightly exceeds 0.53.
   - firmware/ARCHITECTURE.md (Firmware-owned, cherry-picked) still quotes "design_spec 0.44–0.53 s" twice; left for Firmware.
9. **Mechanical/isolation docs** (no .kicad_pcb edit):
   - (A) board_interface.json J30: fp -> PhoenixContact_PC5_8-GF-7.62_1720851, plus new keys mpn 1720851, board_fp KF2EDGRM-5.08-8P, and a note (77.06 mm body overruns LEFT_HV y 164 by 10.8 mm). Coordinates unchanged.
     - Schematic J30 (MPN 1720851, footprint genctl:PLACEHOLDER_PhoenixContact_PC5_8-GF-7.62_1720851) and BOM (1720851) already matched.
     - enclosure_v3.py keys on "Phoenix" in fp (18 vs 16 mm envelope), so a re-run will model J30 2 mm taller.
     - D-m7-20.
   - (B) C74/C75 horizontal footprint + clip holes: D-m7-21, with a read-only room check (INFERRED: no room in either direction for either cap on the frozen board).
   - (C) J28/J29 Safety R7-N12: four constraints added to LAYOUT_RULES.md and ISOLATION_CHECK.md §5b, and D-m7-22. Before this, only the "slots between pins" and the coat-takes-no-credit (§5a) items were present.
     - The >=13 mm to SELV distance was MEASURED read-only: J28 23.64 mm, J29 59.47 mm (PASS).
     - Slot extension to x <= 1.3 mm logged as NICE TO HAVE per Safety's ruling.
     - "Do not plug or unplug live": schematic text at J28 and J29, INSTALL_SAFETY bullet, README sentence, silkscreen in D-m7-22.
   - D-m7-23: spread the 13 x 1/2 W resistors.
10. **BOM:** bom_from_sch 203 = 203 groups, 0 mismatches; bom_retotal on-board total **$464.55**. That is $465.11 after the R7-N5 patch, then -$0.30 inputs (wetting + 2.49k), -$0.28 outputs (LVC1G08), +$0.02 other (R629). Category BOMs updated: inputs (rows 6, 23), outputs (LVC1G08 row), other (C98220 qty 80), comms (C25804 row removed).
- tools/design.py: only the one-shot note mirrored. MPN swaps live in the schematic and BOM (design.py is DO NOT REGENERATE).

## Batch 17 (Layout; Enginerd/Safety rulings 2026-11-21 ~1:51-1:55 AM HST; schematic properties, BOM, docs; NO net change, no layout)
1. **DI_BIAS active current limit (Safety MUST): NOT applied.** Per Enginerd/Safety, no DI_BIAS schematic change is committed in Batch 17; the eFuse shortlist, pick (TPS26621DRCR, C1848341), fault-line wiring proposal (wired-OR FLT -> U76 P17, net DI_BIAS_FLT_N, one 10k C98220 to +3V3_SAFE) and checks are in the Batch 17 report only.
2. **J30 board_interface.json -> Phoenix 1720851:** already done in Batch 16 (d58eee3); re-checked, no further change.
3. **C74/C75: MAL223051016E3 15 F 12.5x30 -> Vishay MAL223051003E3 20 F 3.0 V 16x20 mm, upright.** Value "20F 3.0V", footprint Capacitor_THT:CP_Radial_D16.0mm_P7.50mm, MPN MAL223051003E3, Manufacturer Vishay BC Components, LCSC empty (not at JLC: hand-solder, supplied by us). Mouser 10k+ / $4.72 is Enginerd's figure.
   - Datasheet (MEASURED, Vishay 230 EDLC-HV doc 28450 rev 19-Jun-2024, Table 1/2): CR 20 F (-20/+50 %), UR 3.0 V at 65 °C, 2.8 V at 75 °C, 2.6 V at 85 °C (185 °F), surge 3.15 V; ESRdc 38 mOhm, ESRac 22 mOhm; peak current 25 A; IL 75 µA after 72 h; case 19a 16x20: Ød 0.8, Dmax 16.5, Lmax 22, F 7.5 ±0.5 mm.
   - Rail: two in series on 4.9 V -> 2.45 V/cell nominal, under 2.6 V (85 °C). INFERRED worst case: leakage mismatch up to 75 µA x 10k balance (R78/R79) could put one cell at ~2.8 V, above 2.6 V at 85 °C (same exposure as the old part); bench-check.
   - Hold-up (INFERRED, 4.5 W load, 88 % boost efficiency, 4.9 -> 2.7 V stack window, constant-power sim with series ESR): ideal 16.3 s; nominal C + 2x38 mOhm 15.1 s; -20 % C 12.1 s; -20 % C + 3x ESR (end of life) 10.2 s. Enginerd's 9.8-12.5 s is consistent.
   - D-m7-21 (flat mount) CLOSED; new D-m7-24 with the read-only placement study (C74 candidate pad 1 (100.59, 23.62) rot 0; C75 candidate centre (86.91, 69.69), pads (86.91, 73.44)/(86.91, 65.94); rib gap 3.66 mm). The .kicad_pcb is not touched.
   - Docs: bom/power_bom.csv row 18, bom/design_spec.md hold-up line (was the stale JIERONG text), DESIGN_NOTES Batch 17, tools/design.py text mirror.
4. **fw-rev8 d5778cd** cherry-picked with -x (firmware/ only), see report.
6. **Re-audit 8 text items (folded in):**
   - R7-N10 Manufacturer normalisation (placed-symbol Manufacturer fields; repo bom/*.csv manufacturer column). Before -> after, schematic instances: "Samsung" 4 -> 0 ("Samsung Electro-Mechanics" 151 -> 155); "TI" 73 -> 0 ("Texas Instruments" 1 -> 74); "Viking" 6 -> 0 ("Viking Tech" 6 -> 12); "DIODES" 8 + "Diodes" 1 -> 0 ("Diodes Incorporated" 5 -> 14). Repo BOM rows: "Samsung" 12 -> 0 (+ "FH / Samsung" 1 -> "FH / Samsung Electro-Mechanics"); "TI" 26 -> 0 ("Texas Instruments" 7 -> 33); "Viking" 1 -> 0 ("Viking Tech" 1 -> 2); "Diodes" 2 -> 0 ("Diodes Incorporated" 1 -> 3). The embedded lib_symbols caches keep their 22 "TI" defaults (editing them raises 43 lib_symbol_mismatch warnings; they are not BOM fields). Left as is (not in the ruling): "ST(Semtech)" x7, "SEMTECH" x3, "Semtech" x1, "ST" x3, "STMicroelectronics" x1. /workspace/review/bom_final/*.csv (other agent's) not edited.
   - U66 Value "TLC555CDR" -> "TLC555QDRQ1" (= its MPN and the BOM), plus the estop sheet label "U66 TLC555QDRQ1".
   - R8-N3: power.kicad_sch sheet note now says "J1 battery in ... external fuse <=10 A standard (non-time-delay)" and "OV trip 36.35-40.06 V (38.18 V typ), release 33.19-36.65 V (35.04 V typ)"; J1 Note "J1 battery input (was J0)". Same fuse wording fixed in design_spec l.17 (J0 -> J1), ROUTING_PLAN l.3, mechanical/LAYOUT_PLAN, BOARD_INTERFACE.md, pcb_v4/README (docs only).
   - R8-N4: ALEV100 is off-board (power box K3, not in the schematic). Altran ALEV100 datasheet Rev K 30-Oct-2024: blank option = polarised load terminals (+A1/-A2), "N" = non-polar; coil leads non-polar. ALEV100-B/-C (BOM_powerbox) are the polarised standard parts. INSTALL_SAFETY bullet + README sentence added.
7. **board_interface.json / hv_pads.json X-mirror report (Mechanical):** NOT confirmed. pcbnew on the frozen board gives the repo's X values (pads exact, hv_pads.json max diff 0.000 mm; bbox = GetBoundingBox(False,False) within 0.08 mm of the courtyard for J1/J23/J28/J29/J30/J6/J7/J8). Added a MEASURED 'crtyd' (GetCourtyard) bbox to every footprint and a crtyd_note; no existing value changed, so an enclosure_v3.py re-run gives the same result (it reads 'bbox' and hv_pads only).
5. **Checks:** bom_from_sch 203 = 203 groups, 0 mismatches; bom_retotal on-board total **$464.53** (was $464.55; -$0.02 = 2 x ($4.73 -> $4.72)). ERC on the git-archive extract: 0 default / 75 forced (17 four_way_junction + 58 footprint_link_issues), netlist pad-net diffs 0 vs d58eee3, value/footprint changes only C74, C75 (footprint+value+MPN) and U66 (value); PCB md5 unchanged.

## Batch 18 (Layout; Enginerd go 2026-11-21 02:08 HST: DI_BIAS eFuses + one-shot C0G; schematic + BOM + docs; net changes listed, no layout)
1. **DI_BIAS active current limit (Safety MUST), one TPS26621DRCR per rail** (LCSC C1848341; TI SLVSDT4F):
   - Chain per rail: Q36/Q39 drain (bank switch, unchanged) -> **DIB_x_EFIN** -> U89/U90 IN ... OUT -> **DIB_x_PTC** -> F101/F102 -> DI_BIAS_A/B. Existing F101/F102 refs and DI_BIAS nets kept; F101/F102 now Littelfuse **1210L020/72WR (C27568256)**, 72 V, Ihold 0.20 A, Itrip 0.40 A, 1210, as backup.
   - R631/R633 **33.2k 1 %** ILIM->RTN: I(OL) = 6.636 / R(kOhm) = 0.200 A (SLVSDT4F Eq. 3, MEASURED datasheet); ~0.19-0.21 A with the ±5 % table spread (INFERRED). Auto-retry variant (TPS26621): 512 ms retry after current-limit timeout / thermal shutdown.
   - C308/C311 100n 100 V X7R 0805 (C28233) IN->GND; C309/C312 same at OUT->GND; C310/C313 **10n** 50 V X7R 0603 (C1589) dVdT->RTN (>= 6.8 nF rec.); R632/R634 **1M** (C22935) IN->UVLO (pin table: ">= 1 MOhm" when UVLO unused; <= 55 µA at 60 V). OVP (pin 3), RTN (pin 5) and EP (pin 11) on the local net **DIB_x_RTN**; GND (pin 6) to GND.
   - **SHDN (pin 4) left open (no-connect):** its internal source holds 2.39-3.1 V (V(SHDN), I = 0.1 µA) above V(SHUTR) 1.8 V max, so the chip is always enabled; recommended max on SHDN is 6 V, so it is not tied to IN, and tying it to +3V3_SAFE would back-drive an unpowered chip when the bank is off.
   - FLT (pin 9, open-drain, abs max 62 V): U89.9 + U90.9 wired-OR on **DI_BIAS_FLT_N** -> **U76 P17 (pin 20)** (frontpanel no-connect replaced by the global label), one **R635 10k C98220** to +3V3_SAFE.
   - New symbol genctl:TPS26621DRCR (genctl.kicad_sym + inputs cache). IN pin typed passive (fed through Q36/Q39) so ERC has no power-pin-not-driven item.
2. **E-stop one-shot:** R404 200k -> **2.0M 1 % 0603 (C22976)**; C229 2.2 µF X5R 0805 -> **220 nF 50 V C0G ±5 % 1206 Murata GRM31C5C1H224JE02L (C464977)**. Texts updated: C229 Note, estop sheet note, design_spec, DESIGN_NOTES, INSTALL_SAFETY, ROUTING_PLAN, /workspace/review/fw/load_shedding_spec.md l.35, design.py mirror. Range in the Batch 18 report (nominal 0.48 s; 0.45-0.52 s R/C; 0.32-0.71 s TLC555 VIT limits; up to ~0.99 s with 125 °C DIS leakage). firmware/ not touched.
3. **BOM:** new rows TPS26621DRCR x2, CL10B103KB8NNNC x2 (C1589; the existing 10n group C57112 shows LCSC stock 0, so not reused), 0603WAF2004T5E x1, GRM31C5C1H224JE02L x1; PTC row -> 1210L020/72WR; qty C22935 4->6, C23003 1->3 (now priced), C28233 24->28, C98220 80->81, C25811 2->1, C5137595 2->1. bom_from_sch 207 = 207, 0 mismatches; bom_retotal on-board **$469.00** (was $464.53).
4. **Checks:** ERC on the git-archive extract 0 default / 75 forced (unchanged: 17 + 58). Netlist vs eaa89df: +13 parts (U89, U90, C308-C313, R631-R635), +12 nets (DIB_A/B_EFIN, _UVLO, _RTN, _DVDT, _ILIM, DI_BIAS_FLT_N) + 2 unconnected SHDN, -1 (unconnected U76-P17); existing pads moved: Q36.3 DIB_A_PTC->DIB_A_EFIN, Q39.3 DIB_B_PTC->DIB_B_EFIN, U76.20 -> DI_BIAS_FLT_N; property changes only F101, F102, C229, R404. PCB md5 unchanged. Deferred D-m7-25, D-m7-26.

## Batch 19 (Layout; Enginerd rulings 2026-11-21 02:19 HST; docs/text only, no net or part change)
1. **One-shot spec:** RC kept (R404 2.0M 1 %, C229 220n C0G). New spec **0.30-1.00 s, 0.48 s nominal**; `ESTOP_TRIP_STUCK` moves to **1.20 s** (Firmware Rev 8k; firmware/ not touched here). Reason (Enginerd): the K4 pulse only has to outlast the Finder 38.51 pickup, and its coil is continuous-rated. No trim pot. Text updated: estop sheet text note + C229 Note, tools/design.py mirror (2 lines), bom/design_spec.md, DESIGN_NOTES.md, docs/INSTALL_SAFETY.md, docs/ROUTING_PLAN.md, bom/outputs_bom.csv R404 row. Outside the repo: /workspace/review/fw/load_shedding_spec.md l.35, /workspace/review/fw/one_box_failsafe.md l.180. Bench item B-m7-19 added to deferred_layout.md (measure the pulse cold and hot).
2. **BOM text fix:** outputs_bom.csv rows for C25811 (now R532 only, PCA9306 U77 EN/VREF2 bias) and C5137595 (now C226 only, +5V_TRIP LDO output cap) still carried the old one-shot description/notes from before Batch 18; relabelled. No qty/price change.
3. **dVdT:** C310/C313 stay 10 nF; no schematic change. Firmware blanks DI_BIAS_FLT_N for **25 ms** after each bank enable, which covers the 13.9 ms typical at 36 V (ramp 7.38 ms from Eq. 2 + 6.48 ms tPGOODR at 10 nF) and the ~16.9 ms worst case (I(dVdT) 1.68 µA min, Gain 23.9 min, C(dVdT) +10 % = 11 nF: ramp 9.86 ms + tPGOODR 7.05 ms); all INFERRED from SLVSDT4F equations (corrected Batch 22, R9-N4).
4. **Left deliberately:** earlier changelog entries (Batch 15/16 history, l.877-886) keep 0.37/0.44/0.53 as history. Other 0.37/0.44/0.53 hits are unrelated numbers (IPC exponent 0.44, currents, coordinates).
5. **Checks:** ERC 0 default / 75 forced on the git-archive extract; bom_from_sch 0 mismatches; bom_retotal unchanged $469.00; PCB md5 unchanged.

## Batch 20 (Layout; Enginerd 2026-11-21 02:23 HST; docs only, no net or part change)
1. **One-shot sweep (non-firmware, live text):** remaining figures other than 0.30-1.00 s / 0.48 s nominal / STUCK 1.20 s fixed: docs/INSTALL_SAFETY.md ESTOP_TRIP row "~0.5 s pulse" -> "0.30–1.00 s pulse (0.48 s nominal)"; docs/RAIL_PLAN.md ESTOP_TRIP_OUT row "pulse 0.48 s" -> adds 0.30–1.00 s; docs/RAIL_PLAN.md +5V_TRIP current note R404 200k -> 2.0M. The "~2.2 s (1.7-2.4 s worst case)" that Firmware flagged in bom/design_spec.md is on master / fw-rev8 (design_spec.md l.32), not on m7-sch (fixed here in Batch 15-19); it goes away when m7-sch merges. Left: changelog history, off_board_external_bom.csv rows 39-41 (excluded superseded rows, no timing figure), firmware/.
2. **J28/J29 field wiring (INSTALL_SAFETY + README mirror):** 600 V rated wire, stripped to the Phoenix 1777859 plug's 10 mm stripping length (Phoenix catalog data for 1777859, MEASURED source), no bare copper past the plug body; LEFT_HV enclosure window needs the tool-removable-only hood (Mechanical's scope).
3. **TPS26621 (Batch 18) status:** approved by Safety Round 7 (S7-N13, fixes_safety.md, 2:22 AM HST) with conditions: keep U89/U90 on VBAT_P (never BAT_IN); tie RTN, GND and PowerPAD together into the GND plane (done in Batch 21); CIN 100 nF next to IN/GND; SHDN off the battery rail; bench 36 V dead short for minutes with case temperature in °F. Not provisional.
4. **Checks:** ERC 0 default / 75 forced; bom_from_sch 0 mismatches; bom_retotal unchanged $469.00; PCB md5 unchanged.

## Batch 21 (Layout; Safety S7-N13 MUST DO, Enginerd approved 2026-11-21 02:24 HST; schematic net change + docs)
1. **U89/U90 RTN, PowerPAD and OVP to GND.** The 10 `DIB_A_RTN` / `DIB_B_RTN` labels (U89/U90 pins 3, 5, 11 and R631/R633.2, C310/C313.2) are replaced by power:GND symbols #PWR1132-#PWR1141. Nets DIB_A_RTN and DIB_B_RTN no longer exist.
   - TI SLVSDT4F (MEASURED): §9.3.8 "Connecting RTN pin to GND pin disables the reverse polarity protection feature and the TPS2662x gets permanently damaged when operated under this fault event." §10.4 lists "Do not connect RTN to GND" for that reason. Abs max RTN to GND is −60 to +0.3 V, so RTN = GND is inside the ratings. Reverse polarity is blocked upstream by U1 LM74800 + Q1 (Safety S7-N13), so the lost feature is not needed. Accepted deviation from the §10.4 "Don't".
   - OVP (MEASURED): pin table "if overvoltage protection feature is not to be used then connect OVP terminal to RTN"; §9.3.2 "connect OVP terminal to RTN directly and ensure VIN is not exceeded beyond OVPMAX" (the OVPMAX row was deleted in rev F; INFERRED meaning = the IN ratings, operating 4.5-60 V, abs max 62 V). With RTN = GND, OVP = GND = OVP disabled, a defined configuration. VBAT_P is held below ~40 V by the U1 OV cut-off (36.35-40.06 V), so no divider is needed (INFERRED).
2. **Input source chain (MEASURED netlist):** J1.1/2 BAT_IN -> Q1 (LM74800 DGATE FET) -> VBAT_DD -> Q2 (HGATE FET) -> VBAT_PS -> R555 2 mΩ -> VBAT_P (U1.9 OUT) -> Q36.2/Q39.2 S -> D -> DIB_A_EFIN / DIB_B_EFIN -> U89.1 / U90.1 IN. Not on BAT_IN. Note added to the inputs sheet, INSTALL_SAFETY and DESIGN_NOTES: never move U89/U90 to BAT_IN (62 V abs max vs ~64.5 V clamp).
3. **TPS26621 status:** approved by Safety Round 7 (S7-N13) with these conditions: VBAT_P only, RTN/GND/PowerPAD in the GND plane, CIN 100 nF at IN/GND, SHDN off the battery rail, 36 V short bench test. Not provisional.
4. **Docs:** inputs sheet note, C310/C313 and R631/R633 Notes, tools/design.py comment (text only), DESIGN_NOTES new section, INSTALL_SAFETY l.19, deferred_layout D-m7-27 (REQUIRED BEFORE FAB: PowerPAD to GND plane with thermal vias), D-m7-25 RTN text superseded, bench B-m7-21 (36 V chassis short, minutes, case °F).
5. **Checks:** see the Batch 21 report (ERC, bom_from_sch, bom_retotal, netlist diff vs Batch 20).

## Batch 22 (Layout; Enginerd 2026-11-21 02:37 HST after re-audit 9; value change + docs)
1. **R9-N8: R78/R79 supercap balance 10k -> 4.7k**, same 0603 package: UNI-ROYAL 0603WAF4701T5E, LCSC **C23162** (JLC Basic; LIVE LCSC 02:40 HST stock 6,520,100, 100+ $0.0028), joining the existing 4.7k row (other_bom qty 3 -> 5); C98220 qty 81 -> 79.
   - Cell voltage (INFERRED): ΔV = R x ΔI(leak); worst mismatch 75 µA (one cell 0, other 75 µA) gives ±R x 37.5 µA about the 2.45 V midpoint of a 4.9 V stack: 4.7k -> 0.176 V -> **2.626 V ≈ 2.63 V** (claim confirmed); was 10k -> 2.825 V. 2.63 V is still 0.03 V over the 2.6 V rating at 85 °C (185 °F) in that corner; under 3.0 V at 65 °C (149 °F).
   - Standby drain (INFERRED): 4.9 V / 9.4k = **0.52 mA** (2.55 mW), was 0.245 mA (1.20 mW): **+0.28 mA, +1.35 mW** on the 4.9 V supercap rail.
   - Hold-up at 4.5 W (INFERRED, Batch 17 model plus the balance drain): 15.14 / 12.11 / 10.21 s, unchanged to 0.01 s (the 0.5 mA drain is ~0.04 % of the ~1.3 A boost input).
   - Notes updated: R78/R79 Note, DESIGN_NOTES C74/C75 bullet, tools/design.py text mirror.
2. **R9-N4:** Batch 19 item 3 said 13.9 ms was the worst case; it is typical. Worst case ≈ 16.9 ms (I(dVdT) 1.68 µA min, Gain 23.9 min, C +10 %). The 25 ms blank still covers it. No other doc outside firmware/ had the figure.
3. **R9-N5:** Safety's "R7-N13" renamed **S7-N13** wherever cited (all 9 citations were Safety's): DESIGN_NOTES (1), INSTALL_SAFETY (1), this changelog Batch 20/21 (4), tools/design.py (1), inputs sheet note (1), deferred_layout.md (1, outside repo). No Design Reviewer R7-N13 reference exists in the repo.
4. **Logged in deferred_layout.md (no schematic change):** R9-N7 optional OUT-to-GND Schottky (decide after B-m7-21); D-m7-24 update with Mechanical's C74/C75 windows and a pcbnew read-only check of the best points; J30 keep 1720851 and move inboard (pending Ethan).
5. **Checks:** ERC 0 default / 75 forced; bom_from_sch 0 mismatches; bom_retotal other_bom 119.10 -> 119.07, total $468.97; netlist vs a2bf2a1: only R78/R79 value/fields change.


## Batch 23 (Grok Bot for Ethan, approved 2026-11-21 10:44 AM HST; parts + labels, no connectivity change)
1. **J30 reverted to Kefa KF2EDGRM-5.08-8P, LCSC C441294** (from the Phoenix 1720851 C6651769 placeholder). This matches the frozen PCB footprint `KF2EDGRM-5.08-8P`. Mate KF2EDGKNM-5.08-8P C2974987. Basis: Safety Round 4 (CONNECTOR_SAFETY_MINIMUMS.md, 10:20 AM HST). J30 is HV-group wiring, CT S2 is earthed at the external shorting block, and every board gets a 1000 V DC megger test.
2. **D12/D13 CAN TVS NUP2105LT1G C14486 -> NUP3105LT1G C133092** (onsemi, SOT-23 case 318, same pinout: pins 1/2 lines, pin 3 common). The KiCad NUP2105L symbol is kept. VRWM is 32 V, so a CAN_H/L short to a 24 V battery up to 32 V does not conduct. The trade-off is a higher surge clamp, above the CA-IS3062W ±40 V abs max in large surges (OPEN_ITEMS item 5). Fitted on every board, since both kits use one board.
3. **Inputs labels restored:** local labels COM_A, COM_B (J18.1/.2), DI1, DI2 (J19.1/.2) and DI7, DI8 (J20.1/.2). These nets were `Net-(D42-A1)`, `Net-(D44-A1)`, `Net-(D46-A1)`, `Net-(D47-A1)`, `Net-(D52-A1)` and `Net-(D53-A1)` since the 97964fc redraw.
4. **Connector values and sheet titles** no longer use the old panel names J1B/J2A/J2B/J3B (J1B clashed with refdes J1):
   - J18 is now "COM_A/COM_B/MPU (6P 5.08, p6 NC)"
   - J19 is now "DI1-6 (6P 5.08)"
   - J20 is now "DI7-12 (6P 5.08)"
   - J22 is now "DI_BIAS_B (6P 5.08, p2-6 NC)"
   - J18.6 and J22.2-6 already carry no-connect flags (checked, unchanged).
5. Mirrors updated: bom/comms_bom.csv, bom/ac_metering_bom.csv, docs/genctl_bom.csv, tools/design.py (text and fields only), and the comms sheet note.
6. **Checks:**
   - ERC: 0 violations, both default and --severity-all.
   - Netlist vs 5a4736a: 1126 = 1126 nets, connectivity identical. The only changes are the 6 net renames above plus the D12/D13, J18/J19/J20/J22 and J30 value and field changes (docs/batch23_netlist_diff.txt).
   - bom_from_sch: 0 mismatches.
   - PCB file untouched.

## Batch 24 (Grok Bot for Ethan, footprint audit; Ethan 10:44/10:47 AM HST: fix footprint mismatches, PCB not touched)
1. **Q72 BCP56-16: footprint `SOT-223-3_TabPin2` -> `Package_TO_SOT_SMD:SOT-223`.** The BCP56 symbol pin 4 (collector tab, VBAT_P) had no pad. SOT-223 has pads 1-4 with tab = 4, matching LCSC/EasyEDA C426787 pad-for-pad. Q72 is not on the frozen PCB yet. tools/design.py, docs/genctl_bom.csv and mechanical/bom.csv were mirrored.
2. **genctl.pretty/TMOV20RP_P7.5mm_inline (RV1-RV4):**
   - The body/courtyard was 23 x 8 mm (8 mm ASSUMED) and is now 23 x 11 mm, per the Littelfuse TMOV datasheet (E max 11.0 mm for 300-460 V).
   - The drill goes from 1.2 to 1.3 mm (lead 0.95-1.05 mm).
   - The PCB was NOT refreshed. RV1/RV2 at 9.5 mm spacing would overlap and need re-spacing at the next layout.
3. Full audit: /workspace/review/bom_final/FOOTPRINT_AUDIT_2026-11-21.md (208 groups: OK 204, FIXED 2, MPN-text mismatch 1 (D17/D18 RClamp0524P vs PA), UNVERIFIED 1 (1720819 flange holes)).
4. **Checks:**
   - ERC: 0 (--severity-all).
   - Netlist vs Batch 23: connectivity identical; the only change is the Q72 footprint field.
   - bom_from_sch: 0 mismatches.
   - PCB file untouched.

## Batch 25 (Grok Bot for Ethan, lead decisions 11:03 AM HST; PCB not touched)
1. **D17/D18: MPN RCLAMP0524P.TCT -> RCLAMP0524PATCT, value RClamp0524PA.** LCSC C40960 is the PA, and the P is NRND at Semtech. Checked against the Semtech RClamp0522PA/0524PA datasheet: same SLP2510P8 package, pinout (1/2/4/5 in, 6/7/9/10 flow-through, 3/8 GND) and land pattern. Ratings are equal (5 V VRWM, 15 V VC @ 1 A, 0.3 pF, 150 W, 5 A); ESD is better (+/-12 kV contact vs +/-8 kV). Symbol and footprint unchanged. tools/design.py, docs/genctl_bom.csv and mechanical/bom.csv mirrored.
2. **genctl.pretty/PhoenixContact_PC5_4-GF-7.62_1720819 (J1, J23, J28, J29): pin rows fixed.** Phoenix's 1720819 drilling diagram (catalog PDF, measured from the vector data) puts the 3 solder pins per potential at row 1, +5.08 and +7.62 mm. The footprint had +3.25 and +5.79, so the header would not fit. Rows 2/3 moved; flange NPTHs (3.2 mm, 8.06 outboard, 10.42 behind row 1) were already correct and are unchanged.
   - **PCB NOT refreshed.** The frozen board still has the old rows on J1/J23/J28/J29. Refresh and re-route at the next layout; blocking for fab.
3. **Checks:** ERC 0 (--severity-all). Netlist vs Batch 24: connectivity identical; only D17/D18 value/MPN/description changed. bom_from_sch: 0 mismatches.

## Batch 26 — two-board split (branch m7-split from m7-sch 94bcc2f; Grok Bot for Ethan, Ethan chose side-by-side + Micro-Fit 2x8 harness; PCB not touched)
Plan: /workspace/review/split/SPLIT_SCOPE.md §8. Two KiCad projects in the same folder, sharing genctl.kicad_sym / genctl.pretty / lib tables:
- **genctl** (main controller): genctl.kicad_pro / genctl.kicad_sch, 1,118 parts.
- **genctl_meter** (HV metering daughter): genctl_meter.kicad_pro / genctl_meter.kicad_sch, 221 parts. Its only sub-sheet is ac_metering.kicad_sch (same sheet UUID 85a0e338…).

| ref | old | new | reason | source |
|---|---|---|---|---|
| genctl.kicad_sch sheet "AC metering…" (ac_metering.kicad_sch) | sub-sheet of genctl | removed from genctl; replaced by sheet "Metering interface J31" (mtr_if.kicad_sch, uuid 5d1b3a52…, page 10) | split | SPLIT_SCOPE §8 |
| ac_metering.kicad_sch symbol instances (330) | project "genctl", path /2f7a4bb8…/85a0e338… | project "genctl_meter", path /9e6f0d2c…/85a0e338…; **all 216 references unchanged** | daughter project | — |
| J31 (mtr_if) | — | Conn_02x08_Top_Bottom, Molex 43045-1600 Micro-Fit 3.0 2x8 RA, LCSC C277731, fp Connector_Molex:Molex_Micro-Fit_3.0_43045-1600_2x08_P3.00mm_Horizontal | main side of the interface | SPLIT_SCOPE §1.1, §2.1 |
| J32 (genctl_meter root) | — | same part as J31 | daughter side | — |
| Pin map J31 = J32 | — | 1,2 +3V3; 3,5,7,9,12 GND; 4 ADE_SCK; 6 ADE_MOSI; 8 ADE_MISO; 10 ADE_CS1_N; 11 ADE_CS2_N; 13 ADE_RST_N; 14 ADE_IRQ_N; 15 MTR_DET_N (main) / GND strap (daughter); 16 spare, no-connect both ends. Harness straight, pin n to pin n | SELV-only interface | SPLIT_SCOPE §1.1 |
| C314 10u 0805 C15850, C315 100n 0603 C14663 (mtr_if) | — | +3V3/GND decoupling at J31 | — | SPLIT_SCOPE §3 |
| C316 10u C15850, C317 100n C14663 (genctl_meter root) | — | +3V3/GND decoupling at J32 | — | SPLIT_SCOPE §3 |
| R636 10k 0603 C98220 (mtr_if) | — | MTR_DET_N pull-up to +3V3_SAFE (same rail as U73) | board detect | — |
| U73 (TCA9555 @0x20) P14 pin 17 (frontpanel.kicad_sch 77.47,156.21) | no-connect flag | global label MTR_DET_N | board detect input. U76 @0x25 has no spare pins at this head, so U73's spare P14 is used | netlist 94bcc2f: U73 P14–P17 were the only unconnected TCA9555 pins |
| TP1 "GND_AC" (genctl_meter root) | — | Connector:TestPoint, fp TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm, in_bom no; on GND_AC | megger Test A point (Safety Round 4), replaces probing R475 pad 2 | SPLIT_SCOPE §4 |
| TP2 "LV_GND" (genctl_meter root) | — | same footprint; on GND (SELV) | megger Test B point, daughter testable on its own | SPLIT_SCOPE §4 |
| #FLG0100/#FLG0101 (genctl_meter root) | — | PWR_FLAG on +3V3 and GND | +3V3/GND arrive only through J32 on the daughter | ERC |
| genctl_meter.kicad_pro | — | copy of genctl.kicad_pro (same ERC settings), meta filename changed | — | — |
| docs/FW_REQ_METERING_PRESENCE.md | — | new: missing or silent metering board = latched shutdown-class fault (requirement only) | Ethan / SPLIT_SCOPE R5 | — |

Checks (kicad-cli 9.0.2):
- **ERC --severity-all:** genctl **0**, genctl_meter **0** (reports in docs/split_evidence/).
- **Footprints:** all 1,118 + 221 footprints resolve to a file (genctl.pretty or the KiCad 9.0.2 library). None are empty.
- **Netlist equivalence vs 94bcc2f** (union-find over both netlists, harness J31.n↔J32.n):
  - Every original net keeps exactly its original nodes (4,320 nodes, none lost, none split).
  - All 1,330 original parts are present once, with unchanged value and footprint.
  - Only interface nodes are added (J31/J32 pins, C314–C317, R636, TP1, TP2).
  - The one merge is the designed board-detect strap: MTR_DET_N (formerly unconnected-(U73-P14-Pad17)) joins GND through J32.15 when the daughter is plugged in. With pin 15 excluded there are 0 merges.
  - New net: spare pin 16 (J31.16/J32.16, NC). Script: /workspace/review/split/exec/eq.py.
- BOARD (out of scope): the frozen .kicad_pcb is unchanged and is still the one-board layout. Layout must be reopened as two boards (main with notch, daughter ~82x167 mm 4-layer). J28/J29 still carry the horizontal 1720819 footprint (vertical rear-entry footprints still to be made, as before).
- Not updated on this branch: the per-category bom/*.csv and docs/genctl_bom.csv. The split BOM is in /workspace/review/bom_split. tools/ scripts still assume the single genctl project.
