# Blackstart enclosure v3 (Phase 1, 2026-10-25) - nothing committed
Built against genctl_v4_handrouted.kicad_pcb @ f03c57a (read-only). Supersedes PANEL_V2 / rev C where Ethan's 2026-10-25 constraints differ; old files untouched.

## Design (all in `enclosure_v3.py`, parametric, reads `board_interface.json`)
- **Bezel**: CNC 6061-T6, 329 x 261, black anodise (alt: bonded laser-cut 3-plate stack). Flush glass window 277.56 x 180.46 with rear ledge at Z 9.5, notches for source-PCB band, touch tail (unverified), backlight cable. 12 pockets 24.2 x 12.2 x 8 deep at the board's switch positions. Bosses: H1-H3 PCB (M4), H4 PE, and a **heat boss** 29 x 6.2 mm outside the top PCB edge. Rim 9 mm at Z 4-9.5 = gasket land on the customer panel face. Face has no through-holes.
- **Rear shell**: SLS/MJF PA12, 294 x 226 x 48 (Z 4-48), 3 mm walls, front flange 8 mm joined to the bezel by **8 x M4 from the rear into blind bezel taps**. Rear windows for top/bottom/left/right terminal rows, J10 RJ45 (20 x 24) and J11 USB-C (15 x 10) at the rear, rear vent slots + side chimney slots, 4 anti-flex posts, 600 V barrier rib at x 73. Outer wall flush so it slides through the cutout from the front.
- **Clamp**: 6 SLS PA12 blocks hook into blind T-slots in inward wall bosses (Z 37.5-45), M4 heat-set insert, M4 x 35 nylon-tip screw pushes forward on the panel rear. Cutout **296 x 228 (+1/-0)**, panel **1-6 mm** (INFERRED parameters). Panel face clamped between gasket (2 mm silicone sponge) and screws.
- **Keys**: option A (KEYS_LIGHTGUIDE.md): SLA clear caps, laser-cut 1 mm translucent silicone strip, silicone nib, one CTS 228E per key.
- **Heat path**: CM5 (B side) -> 1 mm pad -> 4.75 mm laser-cut Al heat bar over the STRAP_CORRIDOR -> 2 x M4 to the bezel heat boss -> bezel face. HEAT_PATH.md.

## Phase 2
- **Flush glass is an ASSUMPTION Ethan has not confirmed yet.**
- BCR-1 solved in the rear shell: sealed port tunnels, RJ45 20 x 24 and USB-C 16 x 10 inner, 1.5 mm lead-in, 0.5 mm above the jacks. They sit inside the shell outline, so the fit through the 296 x 228 cutout (1.0 mm/side) and the clamp zone (Z 37.5-45 at the walls) are unchanged.
- Heat options: HEAT_PATH.md section "Options". BCR-4 table: BOARD_CHANGE_REQUESTS.md.

## Phase 3
- BCR-4 closed: geometry.py BTN_X now equals the board key x (+0.30 mm). front_panel.png/svg regenerated.
- Heat re-validated (HEAT_PATH.md, "Phase 3 re-check"). At the ESTIMATED 4 W dashboard load the CM5 throttles above about 41 C ambient with no change, 46 C with A, 53 C with B and 57 C with C. Under a full CPU stress load (8.5 W) only C holds 57 C.

## Phase 4 (cool-to-touch, ALS)
- Thermal design D: CM5 -> heat pillar -> rear 6061 fin plate behind the panel; display isolated from the bezel; 3 mm PA12 front ring on a 1 mm air break is the touch surface. Ring 44.4 C at 40 C ambient (4 W CM5, 70 % backlight). **The cover glass is 52 C and cannot meet 45 C with this display (its own ~10 W): needs Ethan's decision (firmware dimming or a 61010-1 glass limit).**
- **Deviations from Ethan's original constraints:** CM5 heat no longer goes to the bezel boss (D' keeps it); the glass is 4 mm behind the ring face (flush only if the bezel is recessed, not modelled); unit depth 82.75 mm instead of 48 mm.
- ALS window at (11.0, -9.25), sensor on the PCB F side at the same coordinates: BCR-8. Cost delta for D: +$227 at qty 1 / +$115 at qty 10 (ESTIMATED).
- Details: HEAT_PATH.md "Phase 4", thermal_v3.py, thermal_results.json.

## Phase 5 (not committed)
- Cheaper variants and duty-cycle results: HEAT_PATH.md "Phase 5". Flat laser-cut plate V4: +$59 / +$29, depth 52.75 mm, ring 110-115 F. The glass stays above 113 F in all variants.
- ALS moved to (138.18, -9.25). KiCad frame = cover-glass frame. See BCR-8 UPDATE.

## Phase 6: FLUSH glass (Ethan, Oct 25; not committed)
- The display moved 4 mm forward, so the glass is flush with the 3 mm PA12 ring face (Z -4).
- A PA12 ring sleeve (1.5 mm) with a 0.5 mm silicone bead isolates the glass edge from the metal window.
- Ring retention: M3 screws from the rear into heat-set inserts, plus PA12 pips giving a 1 mm air break. Pips are modelled; screws are not.
- Recommended: V1-flush. Details: HEAT_PATH.md "Phase 6", TOLERANCE_STACK.md §6.

## Phase 7 (not committed)
- Corrected costs with a line-by-line V1 breakdown: PARTS_COSTED.md, Phase 7.
- Cabinet-air cases: HEAT_PATH.md, Phase 7.

## Files
enclosure_v3.py, render_v3.py, board_interface.json, BOARD_INTERFACE.md, BOARD_CHANGE_REQUESTS.md, MISMATCH_LIST.md, KEYS_LIGHTGUIDE.md, HEAT_PATH.md, TOLERANCE_STACK.md, PARTS_COSTED.md/.csv, checks.json, enclosure_v3_assembly.step, step/*.step (15 parts), exploded_view_v3.png, iso_front_v3.png, iso_rear_v3.png, section_key_clamp_v3.png, section_key_detail_v3.png, section_heatpath_v3.png.
Rebuild: `/workspace/cqenv/bin/python enclosure_v3.py && /workspace/cqenv/bin/python render_v3.py`.

## Checks (computed in code, checks.json)
Pairwise boolean intersections of all 15 parts (intended contacts excluded: PCB/parts, pads): **0 interferences**. Customer panel at 1.0 and 6.0 mm: no clash with shell or clamps. Shell (behind panel) vs cutout: 1.0 mm/side nominal. Display-to-PCB air gap 11.44 mm under the TFT area (including the whole HV zone x < 75) and 7.27 mm minimum only under the source band (x 20.6-255.6, y 149.9-179.5); phase 9 CAD, checks.json (3.27 obsolete); nib-plunger gap 0.1; tallest rear part to shell inner rear 9.4. Renders are matplotlib (approximate shading).

## Open questions / blocked
1. BCR-1: J11/J10 sit 20.4 / 13.5 mm deep in the rear wall -> needs board change (port daughterboard or taller jacks). **Blocked on board.**
2. Thermal: at 40-50 C ambient the CM5 will throttle and the bezel will run >60 C (backlight 8.6 W dominates). Needs a prototype measurement and a brightness/clock policy.
3. "Glass 3.5 mm behind the bezel face" (lead) vs "flush" (Ethan): v3 is flush; please confirm.
4. Heights of J10/J11/Phoenix/CM5 are INFERRED (no 3D models) - BCR-5.
5. Touch-tail notch and ledge against the Riverdi STEP: not verified yet.
6. Cap fit: SLA +-0.2 vs 0.1 clearance -> fit-at-assembly; UV-stable cap material needed outdoors.
7. Gasket/IP rating not tested; vents reduce ingress rating (drip hoods from rev C not yet re-added).

## Phase 9 (V6 + dual fans, compliance checks). Not committed.
- Parts added: exl1_strip, strip_pad, fans, fan_gaskets, filter_covers, fan_screws, hv_sheet (0.43 mm PP, x -0.5..75 on display rear). fin_plate is now the V6 flat plate with fan holes.
- Depth behind ring face: shell 48 + plate 4.75 + strip 10.5 = 63.25 (+4 ring = 67.25); fans/filter covers 68.25 (+4 = 72.25 mm total).
- Bezel display-tray rim trimmed to Z 7.0 over y 10-115 (HV clearance fix). 0 interferences. New HV checks in checks.json["clearances_mm"]["HV"].
- Renders regenerated incl. section_fans_v3.png and section_hv_J28J29_v3.png. Thermal: thermal_dualfan_p9.json.

## Phase 10 (decisions)
- Fan: Orion OD4010-05HB10A 5 V with gaskets + filters (final). IP/sealed fan swap = OPTIONAL later change.
- BCR-10 reconciled with firmware/ARCHITECTURE.md section 11 (shared open-drain PWM, U76 P15/P16/P17, 3x TMP1075 U81-U83).
- TODO: EXL1 fin dims ASSUMED until the ATS drawing/sample.
- Open: +5V budget being checked by Layout/Firmware. Compliance ruling on the rim trim (Z 7.0), lead trim to 1 mm and the 0.43 mm PP film is PENDING.
