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
