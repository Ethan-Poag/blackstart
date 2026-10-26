# Mismatch list: existing mechanical files vs current board (genctl_v4_handrouted @ f03c57a) and Ethan's 2026-10-25 constraints
Inventory checked: geometry.py, PANEL_V2.md, display_mech.md, draw_front_panel.py/draw_section.py (use geometry.py), enclosure/enclosure.py, render.py, cap_metal.py, ENCLOSURE_DFM.md, enclosure/step/*, DESIGN_NOTES.md.

| # | File | Item | Old value | Current board / constraint | Label |
|---|---|---|---|---|---|
| 1 | display_mech.md | PCB outline | 284 x 198, y -9.27..188.73 | 284 x 210, y -15.27..194.73 | MEASURED |
| 2 | display_mech.md | key rows | y -4.40 / 183.86 | y -9.25 / 188.71 | MEASURED |
| 3 | display_mech.md | holes H1-H4 | (3.5,-4.4) (273.06,-4.4) (3.5,183.86) (273.06,183.86), M3 | (2,-9.25) (274.56,-9.25) (2,188.71) M4; H4 (272,185.5) 9.5 NPTH | MEASURED |
| 4 | geometry.py / display_mech / PANEL_V2 | key x centres | was 29.08 ... 246.68 | RESOLVED phase 3: geometry.py now = board 29.38 ... 246.98 | MEASURED |
| 5 | PANEL_V2.md | cap width | 43.02 x 12 wide caps, one long slot per row, actuator bar + wire stabiliser | 24 mm caps, one switch/key, own pocket (Ethan) | MEASURED (constraint) |
| 6 | PANEL_V2.md | panel build / mounting | CNC panel with 8 M4 PEM studs to housing; no clamp | self-contained unit, front slide-in, rear clamps | constraint |
| 7 | PANEL_V2.md / geometry.py | geometry.py header comment "PANEL V2" + GUIDE_DX 17 / stabiliser params | still present | obsolete (24 mm caps) | MEASURED (file) |
| 8 | geometry.py | CLAMPS L/R position uses `_cy` (=89.73) for L/R | ok | v3 uses y 90 | MEASURED |
| 9 | enclosure.py | shell size | 294 x 220 (2 mm clr all round) | v3 294 x 226 (top clr 8 for heat boss/bar) | design change |
| 10 | enclosure.py | customer cutout | 295 x 221 (+1/-0), 0.5 gap | 0.5 gap < SLS/MJF tolerance +-0.4 % (~+-1.2 mm on 294) -> v3 1.0 gap, 296 x 228 | MEASURED tol (JLC3DP PA12 page) |
| 11 | enclosure.py | clamp pads protrude 2.5 mm OUTSIDE the shell at Z 20-34 | shell + pads wider than cutout -> **cannot slide in from the front** | v3: inward bosses, outer wall flush; checked in code (min gap 1.0 mm) | MEASURED (model) |
| 12 | enclosure.py | clamp brackets | bent 2 mm stainless + PEM nut | allowed (not Al shell) but v3 uses SLS PA12 blocks + M4 heat-set insert (no bending) | design change |
| 13 | enclosure.py | CM5 + heatsink | at x 150-205, y 75-115, on board REAR with off-the-shelf heatsink | CM5 body x 203-258, y 1-41 B side; heat strap to H2 boss per board note | MEASURED |
| 14 | enclosure.py | heat path | none to bezel (passive heatsink in shell) | Ethan: strap/pad to bezel boss | constraint |
| 15 | enclosure.py | rear vents at x 150-205 | over old CM5 position | v3 vents x 120-190 y 70-130 + side chimney slots | INFERRED placement |
| 16 | enclosure.py | terminals simplified at x 40/85/128/172/215 (26 wide) | | real KF2EDGRM rows x 30-245 top/bottom, Phoenix J28/J29/J30 left, J1/J23/J6/J7 right | MEASURED |
| 17 | enclosure.py | SHELL_DEPTH 62 | J10/J11 wells 27.5 / 34.4 deep | v3 48 (wells 13.5 / 20.4, still too deep -> BCR-1) | MEASURED (model) |
| 18 | enclosure.py | REAR_PORTS J10 (214,53.1) J11 (240,49.5) | | J10 (214.0,53.07), J11 (240.0,50.0) | MEASURED (0.5 mm off on J11) |
| 19 | DESIGN_NOTES.md rev (c) | "J11 USB3 Type-A HC-USB3.0-L168-WP" | | board J11 = USB-C TYPE-C-31-D-06B vertical; rev (e) says USB-C service is the only external USB. Notes internally inconsistent | MEASURED |
| 20 | enclosure.py | shell posts | (100,60)(100,140)(240,60)(240,140) | match board SHELL_POST keepouts | MEASURED (match) |
| 21 | enclosure.py | 600 V barrier rib at x BOARD_X0+16 = 12.3 | | board barrier areas x 60-73 (v0..v2) and HV box x < 73 -> v3 rib at x 73 | MEASURED |
| 22 | all | HV parts side | assumed B | J28/J29/J30, T1-T4, HV dividers on B (MEASURED); PROGRESS says HV must stay B | MEASURED |
| 23 | all | display F-side gap | "about 3.5" (PROGRESS) | 11.44 in TFT/HV area, 7.27 at source band (phase 9 CAD; 3.27 was pre-flush) | INFERRED (Z_PCB 16) |
| 24 | lead's brief | "display glass ~3.5 mm behind front face" | | Ethan's brief says FLUSH glass; v3 is flush (glass 0.05 below face). I read "3.5 mm" as the F-side air gap (#23). **Needs lead/Ethan confirmation.** If a 3.5 mm recess is wanted, set glass Z offset: LEDGE_Z 9.5 -> 13.0 and rim depth +3.5 | INFERRED |
| 25 | display_mech.md | touch-tail notch position "verify vs STEP" | not verified | still not verified in v3 (notch modelled x 225-248) | INFERRED |
| 26 | cap_metal.py | metal caps option | | not used in v3 | n/a |
| 27 | ENCLOSURE_DFM.md | costs "rough" | not sourced | v3 PARTS_COSTED with sources | — |
| 28 | geometry.py | MOUNT_HOLES H4 | (272.0,185.5) | match | MEASURED (match) |
| 29 | board | J4 fan header present | | no fan (BCR-3) | MEASURED |

| 30 | Rear ports 13.5 / 20.4 mm deep | BCR-1 solved in shell: sealed port tunnels with lead-in, plug envelopes 0 interference, no board change | phase 2 |
| 31 | Flush glass | **Confirmed by Ethan (phase 6).** Glass flush with the PA12 ring face (-0.05 mm). Display-to-PCB gap 11.44 mm (TFT/HV area) / 7.27 mm (source band); 3.27 mm obsolete | closed (phase 9) |
| 32 | Display-tray rim vs J28/J29 lead tips | Phase 9 3D check: earthed Al rim was 1.52 mm from the 600 V THT lead tips (basic needs 5.5). Fixed in CAD: rim trimmed to Z 7.0 over y 10-115 -> 7.0 mm (2 mm leads) / 8.0 mm (trimmed 1 mm) | fixed in model; leads clipped <= 1.0 mm -> 8.0 mm; basic only with tested H4 PE bond (PE_BOND.md); PP film dropped (phase 11) |
| 33 | Left PA12 wall y 15-105 | Phase 11: left clamp moved (y 90 -> y -2 and y 178); wall now solid fraction 1.000 at 3.0 mm over y 15-105. Inner face 9.94 mm from J28/J29 pad column, 2.4 mm from plug body | closed (phase 11) |
| 34 | J4 fan header | no load switch or fuse on J4 +5V (direct on +5V net); CM5 has one FAN_PWM/FAN_TACH only -> BCR-10 rev phase 10 (U76 P15-17, open-drain PWM); +5V budget being checked by Layout/Firmware | open |
| 35 | H4 / PE | H4 is an NPTH clearance with no net; PE lands only on the bezel boss. H1-H3 CHASSIS pads need bare (masked) boss faces to bond. See PE_BOND.md | phase 11 |
