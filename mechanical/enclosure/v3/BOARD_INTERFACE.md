# Board interface (v3) - from the CURRENT board, read-only

Source: `mechanical/pcb_v4/genctl_v4_handrouted.kicad_pcb` (mtime 2026-10-25 13:17 HST, git HEAD f03c57a), parsed with KiCad 9.0.2 `pcbnew` python (`LoadBoard`, no save). Machine copy: `board_interface.json`.
Frame: mm, origin = cover-glass top-left, front view, x right, y down (same as geometry.py). Side F = toward display, B = rear.
**All positions/rotations/sides/bboxes in the table are MEASURED (board file).** Heights are separate (below).

## Outline and holes (MEASURED)
- Edge.Cuts bbox: x -3.745..280.305, y -15.295..194.755 (incl. line width) -> outline **284.0 x 210.0**, R2 corners, x -3.72..280.28, y -15.27..194.73.
- No edge notches. 6 internal 1.5 mm isolation slots (HV barrier), x 3.465..10.755, y centres 27.195 / 34.815 / 42.435 / 77.01 / 84.63 / 92.25.
- Holes: H1 (2.0, -9.25), H2 (274.56, -9.25), H3 (2.0, 188.71): M4 4.3 plated, 9 mm pad (bezel bosses). H4 (272.0, 185.5): 9.5 NPTH for the bezel PE boss.
- Rule areas: CM5_UNDER (203,7)-(258,35); CM5 body drawing (203,1)-(258,41) B side "heat strap to H2 boss"; STRAP_CORRIDOR (247,-14.8)-(279.8,3.8); SHELL_POST_1..4 D10 at (100,60) (100,140) (240,60) (240,140); PE_BOSS_RING; 600 V BARRIER areas x -3.7..73.

## Heights
| Part | Height above its PCB face | Label / source |
|---|---|---|
| CTS 228E switch (F) | 5.5 | MEASURED cts228e.pdf p3; Digi-Key "Actuator height 5.50 mm" |
| Display module depth | 12.68 max | MEASURED Riverdi DR Rev1.1 |
| CM5 mounted (1.5 mm stack DF40) | 4.94 | MEASURED cm5-datasheet.pdf §4.1.1 |
| J10 RJ45 HR963380AE vertical | 16.9 | INFERRED (rev D enclosure.py comment; no datasheet in repo) |
| J11 USB-C HRO TYPE-C-31-D-06B vertical | 10.0 | INFERRED (rev D comment) |
| KF2EDGRM-5.08 + plug | 16.0 | INFERRED |
| Phoenix PC5/4-GF-7.62 + plug | 18.0 | INFERRED |
| ZMCT103C CTs T1-T4 (meter board, Batch 29) | **19.2** | DATASHEET (Zeming C94571: 18.2 × 19.2 H × 10.2 mm; window Ø5 mm, centre ≈ 10 mm above the board). Add room for the pigtails: ≥ 10 mm straight each side of the window, tie-downs, and the CT gland (ISOLATION_CHECK §5c). **Height correction (Batch 30, Mechanical review ZMCT103C_fit.md):** the old "AC1005 12.0 INFERRED" was a misread of the AC1005's 11.12 mm thickness; Talema's drawing gives a **23.80 mm** installed height. So the ZMCT103C is about **4.6 mm shorter** than the part it replaced, not taller. |
| PCB thickness | 1.6 | INFERRED |
| PCB F face Z (behind bezel face) | 16.0 | INFERRED design value (geometry.py Z_BOARD_FRONT) |

## Volatility (PROGRESS.md M6)
Board is 61.9 % routed, 1119 unconnected, "NOT fab-ready". M6 moved only R/C passives; outline, holes, ICs, connectors, keys were not moved (MEASURED statement in PROGRESS.md). Likely to move (INFERRED): C1 parts near U21; possibly J10/J11 or U21 if the LVDS/DSI escape needs re-placement; J4 fan header (no fan per Ethan); heights of unmodelled parts.

## Mechanically relevant footprints (MEASURED)
> **STALE pending the two new board outlines (genctl + genctl_meter); do not use for clearance checks until re-extracted.** Missing from this extraction: J31/J32 Molex 43045-1600 2×8 RA (courtyard ≈ 29.2 × 13.7 mm), C74/C75 upright supercaps (22 mm, main board) and the heat-strap boss (main board).
>
> **Batch 30 note (2026-11-22 HST):** this table is the pre-split v4 single board. Since the split (09b60d3) and Batch 29, T1-T4 are **ZMCT103C** window CTs on the separate **genctl_meter** board (19.2 mm tall), and **J30 is off-board** (a shorting-type CT block in the genset panel). The J30 and AC1005 T1-T4 rows below are historic; the CT pigtails leave the enclosure through one gland instead of J30. The enclosure CAD (enclosure_v3.py J30 envelope, left window) still models the old J30/AC1005 and needs Mechanical's re-check for the two-board layout. The CT pigtails leave through **one M25 cable gland** near the old J30 left-edge spot, away from the J32/SELV side.
| Ref | Value | Footprint | x | y | rot | side | bbox x0,y0,x1,y1 |
|---|---|---|---|---|---|---|---|
| H1 | M4 bezel boss | MountingHole_4.3mm_M4_Pad | 2.0 | -9.25 | 0.0 | F | [-2.58, -13.82, 6.58, -4.67] |
| H2 | M4 bezel boss | MountingHole_4.3mm_M4_Pad | 274.56 | -9.25 | 0.0 | F | [269.99, -13.82, 279.13, -4.67] |
| H3 | M4 bezel boss | MountingHole_4.3mm_M4_Pad | 2.0 | 188.71 | 0.0 | F | [-2.58, 184.13, 6.58, 193.28] |
| H4 | PE boss clearance D9.5 NPTH | MountingHole_4.3mm_M4 | 272.0 | 185.5 | 0.0 | F | [267.25, 180.75, 276.75, 190.25] |
| J10 | HR963380AE | HR963380AE_RJ45 | 214.0 | 53.07 | 0.0 | B | [205.78, 42.95, 222.22, 63.05] |
| J11 | USB-C service | USB_C_Receptacle_HRO_TYPE-C-31-D-0 | 240.0 | 50.0 | 0.0 | B | [235.41, 47.2, 244.59, 52.8] |
| U9 | CM5 (conn A) | DF40C-100DS-0.4V | 230.5 | 4.0 | 0.0 | B | [219.07, 2.05, 241.93, 5.95] |
| U10 | CM5 (conn B) | DF40C-100DS-0.4V_B | 230.5 | 38.0 | 0.0 | B | [219.07, 36.05, 241.93, 39.95] |
| J14 | LVDS FPC 40p 0.5mm | FPC_40P_0.5_05A20L40P | 128.38 | 140.29 | 0.0 | F | [115.94, 138.5, 140.82, 145.38] |
| J15 | Touch FPC 10p 0.5mm | FPC_10P_0.5_05B20L10P | 230.78 | 172.49 | 0.0 | F | [225.37, 170.71, 236.19, 176.22] |
| J16 | Backlight (JST SM02B-BHSS) | SM02B-BHSS-1-TB | 81.92 | 18.0 | 0.0 | F | [76.59, 14.12, 87.41, 21.88] |
| J12 | Internal USB0 touch (SM04B) | JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.0 | 210.78 | 173.46 | 0.0 | F | [206.85, 170.16, 214.71, 176.76] |
| J1 | PC 5/4-GF-7,62 (battery in) | PhoenixContact_PC5_4-GF-7.62_17208 | 266.56 | 144.75 | -90.0 | B | [264.2, 132.37, 279.88, 180.0] |
| J23 | J4 E-stop/fuel/crank (PC 5/4-7.62) | PhoenixContact_PC5_4-GF-7.62_17208 | 266.56 | 95.0 | -90.0 | B | [264.2, 82.61, 279.88, 130.24] |
| J28 | J7 GEN voltage (L1 L2 L3 N) | PhoenixContact_PC5_4-GF-7.62_17208 | 10.01 | 46.24 | 90.0 | B | [-3.32, 11.0, 12.36, 58.63] |
| J29 | J8 BUS voltage (L1 L2 L3 N) | PhoenixContact_PC5_4-GF-7.62_17208 | 10.01 | 96.06 | 90.0 | B | [-3.32, 60.82, 12.36, 108.45] |
| J30 | J9 CT secondaries (5A) | KF2EDGRM-5.08-8P | 7.79 | 136.3 | 90.0 | B | [-3.32, 110.64, 9.24, 162.0] |
| J6 | CAN1 (PC 5/4) | WJ15EDGRC-3.81-4P | 272.2 | 46.19 | -90.0 | B | [270.48, 38.0, 279.88, 54.37] |
| J7 | Expansion bus (PC 5/6) | WJ15EDGRC-3.81-6P | 272.2 | 68.49 | -90.0 | B | [270.48, 56.5, 279.88, 80.49] |
| J8 | Router 12V (3.81/2) | WJ15EDGRC-3.81-2P | 262.56 | 189.96 | 90.0 | B | [254.89, 185.58, 264.29, 194.33] |
| J9 | RS-485 (PC 5/3) | WJ15EDGRC-3.81-3P | 14.68 | 186.66 | 180.0 | B | [8.4, 184.93, 20.95, 194.33] |
| J17 | J1A analog in (PC 5/6) | KF2EDGRM-5.08-6P | 50.82 | 183.22 | 180.0 | B | [30.24, 181.76, 71.44, 194.33] |
| J18 | J1B COM/MPU (PC 5/6) | KF2EDGRM-5.08-6P | 94.34 | 183.22 | 180.0 | B | [73.76, 181.76, 114.96, 194.33] |
| J19 | J2A DI1-6 | KF2EDGRM-5.08-6P | 137.86 | 183.22 | 180.0 | B | [117.28, 181.76, 158.48, 194.33] |
| J20 | J2B DI7-12 | KF2EDGRM-5.08-6P | 181.38 | 183.22 | 180.0 | B | [160.8, 181.76, 202.0, 194.33] |
| J21 | J3A E-stop/D+/VBAT/bias | KF2EDGRM-5.08-6P | 224.94 | -3.76 | 0.0 | B | [204.32, -14.87, 245.52, -2.3] |
| J22 | J3B | KF2EDGRM-5.08-6P | 224.9 | 183.22 | 180.0 | B | [204.32, 181.76, 245.52, 194.33] |
| J24 | J5A outputs | KF2EDGRM-5.08-6P | 50.86 | -3.76 | 0.0 | B | [30.24, -14.87, 71.44, -2.3] |
| J25 | J5B returns | KF2EDGRM-5.08-6P | 94.38 | -3.76 | 0.0 | B | [73.76, -14.87, 114.96, -2.3] |
| J26 | J6A AUX1-6 | KF2EDGRM-5.08-6P | 137.9 | -3.76 | 0.0 | B | [117.28, -14.87, 158.48, -2.3] |
| J27 | J6B AUX7-10 + returns | KF2EDGRM-5.08-6P | 181.42 | -3.76 | 0.0 | B | [160.8, -14.87, 202.0, -2.3] |
| J4 | Fan header (SM04B) | JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.0 | 270.34 | 14.23 | 0.0 | B | [266.41, 10.92, 274.26, 17.53] |
| J2 | SWD | FTSH-105-01_SWD | 197.36 | 69.71 | 0.0 | B | [193.55, 66.27, 200.72, 73.14] |
| J3 | Header B (MCU spare) | PZ254-2-05-S_2x05_SMD | 127.98 | 93.09 | 0.0 | B | [121.26, 88.84, 134.69, 97.34] |
| J5 | Header A (CM5 I2C/SPI) | PZ254-2-05-S_2x05_SMD | 191.07 | 18.91 | 0.0 | B | [184.35, 14.66, 197.78, 23.16] |
| JP1 | JP1 CM5->MCU SWD (opt) | PinHeader_2x04_P2.54mm_Vertical | 198.05 | 83.49 | 0.0 | B | [196.25, 74.07, 202.39, 85.28] |
| SW1 | RESET | SW_Push_1P1T_XKB_TS-1187A | 196.7 | 53.57 | 0.0 | B | [192.93, 50.74, 200.48, 56.39] |
| SW2 | BOOT0 | SW_Push_1P1T_XKB_TS-1187A | 163.83 | 18.99 | 0.0 | B | [160.06, 16.16, 167.61, 21.81] |
| SW3 | nRPIBOOT | SW_Push_1P1T_XKB_TS-1187A | 250.6 | 40.74 | 0.0 | B | [246.82, 37.91, 254.37, 43.56] |
| SW4 | CM5 PWR | SW_Push_1P1T_XKB_TS-1187A | 185.67 | 8.35 | 0.0 | B | [181.9, 5.52, 189.45, 11.17] |
| F1 | 10A ATO (3557-2 clips) | Keystone_3557-2_ATO_clips | 250.35 | 128.2 | 0.0 | B | [240.32, 124.7, 260.39, 131.69] |
| BT1 | CR2032 | BS-CR2032-8 | 120.88 | 60.0 | 0.0 | B | [105.8, 52.02, 134.21, 67.98] |
| T1 | AC1005 | AC1005_CT | 41.59 | 118.51 | 0.0 | B | [25.59, 112.83, 57.59, 124.2] |
| T2 | AC1005 | AC1005_CT | 40.28 | 138.05 | 0.0 | B | [24.28, 132.37, 56.28, 143.74] |
| T3 | AC1005 | AC1005_CT | 39.37 | 79.1 | 0.0 | B | [23.37, 73.42, 55.37, 84.79] |
| T4 | AC1005 | AC1005_CT | 36.5 | 43.69 | 0.0 | B | [20.5, 38.01, 52.5, 49.38] |
| SW9 | BTN1 | CTS_228E_RGB | 29.38 | -9.25 | 0.0 | F | [23.18, -12.91, 34.98, -5.59] |
| SW10 | BTN2 | CTS_228E_RGB | 72.9 | -9.25 | 0.0 | F | [66.7, -12.91, 78.5, -5.59] |
| SW11 | BTN3 | CTS_228E_RGB | 116.42 | -9.25 | 0.0 | F | [110.22, -12.91, 122.02, -5.59] |
| SW12 | BTN4 | CTS_228E_RGB | 159.94 | -9.25 | 0.0 | F | [153.74, -12.91, 165.54, -5.59] |
| SW13 | BTN5 | CTS_228E_RGB | 203.46 | -9.25 | 0.0 | F | [197.26, -12.91, 209.06, -5.59] |
| SW14 | BTN6 | CTS_228E_RGB | 246.98 | -9.25 | 0.0 | F | [240.78, -12.91, 252.58, -5.59] |
| SW15 | BTN7 | CTS_228E_RGB | 29.38 | 188.71 | 0.0 | F | [23.18, 185.05, 34.98, 192.37] |
| SW16 | BTN8 | CTS_228E_RGB | 72.9 | 188.71 | 0.0 | F | [66.7, 185.05, 78.5, 192.37] |
| SW17 | BTN9 | CTS_228E_RGB | 116.42 | 188.71 | 0.0 | F | [110.22, 185.05, 122.02, 192.37] |
| SW18 | BTN10 | CTS_228E_RGB | 159.94 | 188.71 | 0.0 | F | [153.74, 185.05, 165.54, 192.37] |
| SW19 | BTN11 | CTS_228E_RGB | 203.46 | 188.71 | 0.0 | F | [197.26, 185.05, 209.06, 192.37] |
| SW20 | BTN12 | CTS_228E_RGB | 246.98 | 188.71 | 0.0 | F | [240.78, 185.05, 252.58, 192.37] |

> SUPERSEDED (N4, m7-sch 3c): F1 above is extracted from the unchanged .kicad_pcb. The schematic has no on-board fuse; battery net BAT_IN; installer fits an external fuse <=10 A standard (non-time-delay), >=58 V DC in the battery lead; F1/clips go when the board is updated.
