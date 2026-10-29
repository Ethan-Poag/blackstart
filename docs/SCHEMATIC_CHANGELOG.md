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
