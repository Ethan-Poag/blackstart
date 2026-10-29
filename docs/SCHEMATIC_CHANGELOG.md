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
| bom/ac_metering_bom.csv l.15 (6x 600 V fuse) | unchanged | unchanged | Left as an open question: bom/design_spec.md:40 says the voltage inputs use external DIN fused terminals, but nothing says to drop the line | — |

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
| BOARD (out of scope) | SW5/SW7/SW8, R103/R104 still on .kicad_pcb; no JP2–JP4 | — | Board must later delete them and place JP2/JP3/JP4 (windows in failsafe_latch.md L4) on B.Cu | — |

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
| tools/design.py | — | U87 block; BUS CLKIN = ADE_CLK_BUF (design.py already named BUS_VA_P) | regen | — |

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
