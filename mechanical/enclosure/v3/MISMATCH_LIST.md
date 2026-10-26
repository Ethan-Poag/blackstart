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
| 31 | Flush glass (superseded by #54: ring removed, glass flush with the bare bezel face) | **Confirmed by Ethan (phase 6).** Glass flush with the PA12 ring face (-0.05 mm). Display-to-PCB gap 11.44 mm (TFT/HV area) / 7.27 mm (source band); 3.27 mm obsolete | closed (phase 9) |
| 32 | Display-tray rim vs J28/J29 lead tips | Phase 9 3D check: earthed Al rim was 1.52 mm from the 600 V THT lead tips (basic needs 5.5). Fixed in CAD: rim trimmed to Z 7.0 over y 10-115 -> 7.0 mm (2 mm leads) / 8.0 mm (trimmed 1 mm) | fixed in model; leads clipped <= 1.0 mm -> 8.0 mm; basic only with tested H4 PE bond (PE_BOND.md); PP film dropped (phase 11) |
| 33 | Left PA12 wall y 15-105 | Phase 11: left clamp moved (y 90 -> y -2 and y 178); wall now solid fraction 1.000 at 3.0 mm over y 15-105. Inner face 9.94 mm from J28/J29 pad column, 2.4 mm from plug body | closed (phase 11) |
| 34 | J4 fan header | no load switch or fuse on J4 +5V (direct on +5V net); CM5 has one FAN_PWM/FAN_TACH only -> BCR-10 rev phase 10 (U76 P15-17, open-drain PWM); +5V budget being checked by Layout/Firmware | open |
| 35 | H4 / PE | H4 is an NPTH clearance with no net; PE lands only on the bezel boss. H1-H3 CHASSIS pads need bare (masked) boss faces to bond. See PE_BOND.md | phase 11 |
| 36 | PE stud location | Phase 13 option table (H4 276.8 mm from J28/J29). Phase 14: lead's (16, 3) lies behind the display glass (no bezel metal). New boss PE_NEW (12.3, -7.5), 31.0 / 103.9 mm to J28/J29 pads; H4 PE boss deleted (H4 = plain NPTH); needs BCR-11 (hole, move D5, GND vias). Phase 15 correction (Compliance MEASURED): web to H1 CHASSIS pad **1.20 mm** (was 1.05), hot copper **19.0 mm from the hole centre** (was "≈ 17 mm from the edge"). See PE_BOND.md | phase 14/15 |
| 37 | Clamp count | CLAMP_RETENTION phase 12 said 9 clamps; CAD has 8 (T2, B2, L3, R1) -> 65 N per clamp | phase 14 |
| 38 | Coating wording | Phase 13 README called the coating "IEC 60664-3-qualified" and "required for the PD2 creepage assumption"; replaced with Compliance's text (no spacing credit, not qualified) | phase 14 |
| 39 | PE ring terminal | BOM said "M4 ring terminal" with no wire range; now blue 1.5-2.5 mm² / yellow 4-6 mm² M4 for the 2.5 / 4 mm² PE | phase 14 |
| 40 | J30 KF2EDGRM rating | ≥ 600 V finger-safe rating not verified (Compliance open item) | open |

| 41 | Chimney slots | 2 × 12 unfiltered side-wall slots were still in CAD after the fan change (phase 9); they bypass the PD2 filters. Deleted in phase 15 | phase 15 |
| 42 | Rear windows | Phase 14 called the PE cover optional and left the terminal windows open (unfiltered inlets). Phase 15: all 5 covered, tunnel feet foam-sealed | phase 15 |
| 43 | One-edge cover hooks | LEFT_HV, BOTTOM and RIGHT covers can only hook on 1 edge (other edge < 2.5 mm from the inner wall). Phase 16: outer wrap lips with bead and groove added; FIRST PRINT FIT TEST required | phase 16 (fit test open) |
| 44 | Plug finger safety | J28/J29/J30 plug-face live metal (screws) not modelled; IP20 / finger-safe datasheet statements not obtained; finger reaches the plug bodies with the cover off | open |
| 45 | J30 wire range | Was ASSUMED 0.2–2.5 mm² (Kefa). Phase 16: J30 → Phoenix SPC 5/8-STF-7,62, rigid 0.2–10 / flexible 0.2–6 mm² VERIFIED (phoenixcontact.com 1996184) | phase 16 |

| 46 | **PENDING: J30 footprint** | Ethan approved PC 5/8-GF-7,62 + SPC 5/8-STF-7,62 (7.62 mm pitch, plug 76.18 wide; or 2 × 4-pin). Layout has not given the footprint. When it does, redo: CAD J30 model (Phoenix 3D/drawing), J28–J30 window/slot/cover and wrap-lip positions, clamp clearances y 118 / y 178, creepage + J30 surface path, finger_check. Also **download the Phoenix drawing / 3D model for 1996184 and 1720851 so the mated height is verified, not inferred**. CAD still has the old KF2EDGRM J30 | **PENDING** |
| 47 | J30 finger safety / header voltage | The Phoenix pages carry no finger-safe / IP20 statement. Header 1720851: rated III/3 630 V, but its UL listing is mixed (300 V/41 A, 150 V, 600 V/5 A, 600 V/41 A by use group). The plug is UL 600 V/35 A. Compliance to rule | open |
| 48 | Left wall groove | Wrap-lip grooves would thin the left wall to 2.2 mm at y 140/157 next to J30. Phase 17: **left groove and bead DEFERRED pending a Compliance ruling** (`LEFT_LIP_BEAD = False`; set it to True to restore). Left wall full 3.0 mm; left cover far-edge hold-down reduced (locating lips only), first print fit test required | **CLOSED** phase 18: Compliance hv_rulings_phase16.md §B(e): 2.2 mm acceptable (no minimum in IEC 61010-1, dielectric test only; design minimum 2.0 mm). `LEFT_LIP_BEAD = True`; MODELLED wall minimum 2.2 mm |

| 49 | J28–J30 cover tool-only | Snap hooks alone could not be proven finger-proof. Phase 18: captive PA66 M3 slotted screw latch added; hand-pry / retention / drop test on the first print | phase 18 (test open) |
| 50 | Probe B articulated | CAD uses a rigid finger; the physical jointed-finger test is still required (WINDOW_COVERS checklist) | open |

## Phase 19 closures (Ethan's decision, Oct 25 2026: DIY open-source, not a certified product). Rows above kept for history.
| # | Status |
|---|---|
| 35 | CLOSED/REMOVED: no PE path. H4 stays a plain NPTH; H1-H3 are unchanged (CHASSIS bosses). The bezel bonds to the panel through the top clamps (README Phase 19). |
| 36 | CLOSED/REMOVED: PE_NEW boss deleted; BCR-11 WITHDRAWN. |
| 37 | CLOSED: 8 clamps confirmed in CAD (T2, B2, L3, R1). |
| 38 | CLOSED: certification wording softened throughout. |
| 39 | CLOSED/REMOVED: no ring terminal (PE hardware removed). |
| 40 | CLOSED by decision: no rating claim is made (DIY). J30 data stays in J30_PHOENIX_DATA.md. |
| 46 | still PENDING (J30 footprint from Layout; the J30 CAD model is not touched). |
| 47 | CLOSED by decision: informational only (J30_PHOENIX_DATA.md). |
| 48 | CLOSED/REMOVED: wrap lips, beads and grooves removed; the left wall is plain (solid fraction y15-105 = 1.000). |
| 49 | CLOSED/REMOVED: captive latch screw, tab and boss removed; the J28-J30 cover is snap-only again (3 hooks). |
| 50 | CLOSED/REMOVED: the probe-B checklist is removed; finger_check.py is kept as an informal CAD sanity check. |

## Phase 20
| # | Status |
|---|---|
| 51 | NEW/CLOSED: a primary earth path is reinstated as an M4 ground stud through the top side wall at x 140, Z 30, strapped to a bare bezel landing at (140, -19.8) (GROUND.md). The old PE_NEW location (12.3, -7.5) is not reused because it needed a PCB hole and sat near HV; the top-right corner is blocked by the heat bar. No board change. The clamp bond is unchanged as the backup. |
| 52 | CLOSED (Phase 21): stud moved to the rear face at (257.5, -19.2). Strap joint is metal-to-metal, hex-pocket anti-rotation plus nylock, joint compound on the landings, test spot reused (GROUND.md). |
| 53 | CLOSED (Phase 22): the stud pocket was a round Ø9 and is now a true hex, AF 7.2. Two printed strap clips added at x 186 and x 235. |
| 54 | Phase 23: PA12 front ring (thermal design D, never approved by Ethan) removed. The glass is flush with the bare bezel face again (display DZ 0); the PA12 glass-edge sleeve is kept. |
| 55 | OPEN, for Ethan. The CAD screws the heat bar tab to the bezel heat boss through a pad, but phases 4-9 modelled that boss as carrying no heat. Phase 23 models it as built (+2-3 F on the bezel face, +4 F throttle ambient). Optional G10/nylon isolation is in HEAT_PATH Phase 23. |
