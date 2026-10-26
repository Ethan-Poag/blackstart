# Blackstart enclosure v3 (Phase 1, 2026-10-25) - nothing committed

> **DIY open-source project, not a certified product.** Build and install it at your own risk. The design rules used are 8.0 mm clearance and 6.6 mm creepage from live parts. Earlier phases mention compliance reviews; Phase 19 removed those requirements.
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
- *(Superseded in Phase 23: the PA12 front ring is REMOVED; the bare aluminium bezel is the front face.)* Thermal design D: CM5 -> heat pillar -> rear 6061 fin plate behind the panel; display isolated from the bezel; 3 mm PA12 front ring on a 1 mm air break is the touch surface. Ring 44.4 C at 40 C ambient (4 W CM5, 70 % backlight). **The cover glass is 52 C and cannot meet 45 C with this display (its own ~10 W): needs Ethan's decision (firmware dimming or a 61010-1 glass limit).**
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
- Parts added: exl1_strip, strip_pad, fans, fan_gaskets, filter_covers, fan_screws (hv_sheet PP film DROPPED in phase 11). fin_plate is now the V6 flat plate with fan holes.
- Depth behind ring face: shell 48 + plate 4.75 + strip 10.5 = 63.25 (+4 ring = 67.25); fans/filter covers 68.25 (+4 = 72.25 mm total).
- Bezel display-tray rim trimmed to Z 7.0 over y 10-115 (HV clearance fix). 0 interferences. New HV checks in checks.json["clearances_mm"]["HV"].
- Renders regenerated incl. section_fans_v3.png and section_hv_J28J29_v3.png. Thermal: thermal_dualfan_p9.json.

## Phase 10 (decisions)
- Fan: Orion OD4010-05HB10A 5 V with gaskets + filters (final). IP/sealed fan swap = OPTIONAL later change.
- BCR-10 reconciled with firmware/ARCHITECTURE.md section 11 (shared open-drain PWM, U76 P15/P16/P17, 3x TMP1075 U81-U83).
- TODO: EXL1 fin dims ASSUMED until the ATS drawing/sample.
- Open: +5V budget being checked by Layout/Firmware. Compliance phase 9 ruling received (see Phase 11).

## Phase 11 (not committed)
- **PE bond** at H4 designed (superseded in Phase 14: PE_NEW boss, H4 plain NPTH): bare bezel boss + star washer + ring terminal + M4x10; masks M1-M5; continuity test. See PE_BOND.md. CAD part `pe_bond`; right terminal window extended to y 192 for access.
- **Left wall y 15-105 now solid (fraction 1.000, was 0.9574).** The only opening was the left clamp blind T-slot (x -8.72..-4.22, y 81-99, Z 37.3-45.2). Left clamp y 90 removed; phase 12: three left clamps at y 2 / 118 / 178 (phase 13) (CLAMP_RETENTION.md).
- **J28/J29/J30 leads clipped to <= 1.0 mm** (assembly note, inspect): 8.0 mm to the trimmed tray rim. The rim trim (Z 7.0) passes basic only with the H4 PE bond bare-metal and continuity-tested (PE_BOND.md).
- **PP film dropped** (not required per Compliance phase 9): removed from CAD (hv_sheet, step/hv_sheet.step) and docs.
- Creepage clamp insert -> HV plugs: superseded, see Phase 13.

## Phase 12
- Clamp retention check: CLAMP_RETENTION.md. Left clamps were y 5 / 116 / 178; moved in Phase 13 to y 2 / 118 / 178.

## Phase 13 (PD2 decision, PE bond review)
- **Pollution degree:** Ethan decided Oct 25: the fan air path is treated as **PD2**. PD2 rests on the enclosure seal plus washable filters on both fans; the HV conformal coat is supplementary protection only (no spacing credit, see Phase 14). The board's 6.6 mm creepage rule stays (6.6 mm PD2 basic L-L; 12.6 mm reinforced).
- **Creepage method:** straight-line distances (checks.json) are used as a lower bound for creepage. Any surface path between the same parts is ≥ the straight line. Where an older route bridged a wide gap straight across, that was **my own conservative method, not a standard rule** (IEC groove X is PD2 1.0 mm; a gap ≥ X is followed along its contour, so a straight jump is shorter = conservative). The old 24.7 mm figure is deleted.
- **Clamps moved (CAD):** left clamps y 5 / 116 -> **y 2 / 118** (slots y -7..11, 109..127), y 178 unchanged; wall y 15-105 still solid 1.000; 0 interferences.
- **Current straight-line minimums (MODELLED, checks.json):** J28/J29 plug envelope to y 2 left clamp insert **13.48 mm**, to its screw **14.14 mm** (were 12.03 / 12.68 at y 5); J28/J29 pads to insert 35.26 mm; J30 (CT secondaries) plug envelope to y 118 insert **11.29 mm**. All exceed 6.6 mm (PD2 basic); J28/J29 also exceed 12.6 mm reinforced (insert is unearthed accessible metal). J30: reinforced applies (Compliance phase 13); surface path 26.69 mm, see Phase 14.
- **PE bond test** corrected to IEC 61010-1 3rd ed §6.5.2.5 (2nd ed §6.5.1.4), permanently connected: 2× the external fuse rating, ≤ 10 V. Production: 10 A 4-wire, PE lug to M5, ≤ 0.1 Ω per unit; one 25 A type test; ≤ 1 A through CHASSIS pads. See PE_BOND.md.
- **PE wire** ≥ 600 V sense wire gauge (value TBD; not in repo). **No thread-locker** on the PE joint. Galvanic-corrosion note + suggested mitigation. **PE stud location TBD**: H4 is 276.8 mm from the nearest J28/J29 pad; options in PE_BOND.md.
- **Fan filters (both fans):** washable open-cell foam, PPI **not specified (ESTIMATED 30-45 PPI, typical for fan filters)**, thickness up to the 4.0 mm filter cover depth in CAD (ESTIMATED 3 mm foam). Optional stainless or nylon support mesh. Filter face ≈ 40 x 40 = 1600 mm² vs the Ø38 fan hole 1134 mm² (MODELLED, ~1.4x). Pressure drop ESTIMATED 5-15 Pa clean, reducing fan flow ~10-25 % (ESTIMATED); the thermal model's fan conductances 2.2 / 1.3 / 0.20 W/K were ESTIMATED **including** filter restriction (HEAT_PATH.md). Cleaning: monthly at a salt-air or dusty site (recommendation, ESTIMATED); a clogged filter acts like a failed fan. Replacement: foam + PA12 snap cover, $8 / $6 for two (ESTIMATED, PARTS_COSTED row). Removal: unclip the PA12 snap cover, no tools.
- **Conformal coating (board assembly requirement):** coat the HV section x < 73 behind the barrier (J28/J29/J30 area) per Compliance conformal_coating_spec.md (acrylic AR baseline, 30–75 µm dry, both sides, mating contacts and H1–H3 faces masked, UV-inspected). The coating is a humidity/salt-air/contamination mitigation that supports the PD2 decision together with the enclosure seal and washable fan filters. It is **not** qualified to IEC 60664-3 and **no clearance or creepage credit is taken**: all spacings remain per IEC 60664-1 (6.6 mm PD2 basic, 12.6 mm reinforced). Any future coating credit would need IEC 60664-3 qualification and Compliance/NRTL agreement, and would not reduce the 6.6 mm board rule.

## Phase 14 (J30 creepage, nylon clamp screws, PE boss moved, coating wording)
- **J30 to y 118 clamp (reinforced 8.0 / 12.6, insert not earthed):** clearance = straight line 11.29 mm (≥ 8.0, MODELLED). **Surface (creepage) path 26.69 mm (MODELLED, ≥ 12.6)**: J30 is inside the closed PA12 shell and the 2.4 mm wall gap is ≥ X (1.0 mm PD2), so no surface joins the plug to the left wall; the only surface route to the outside clamp runs out through the rear J28-J30 wiring window. Legs (method: shortest route over CAD surfaces, live metal taken at the plug envelope top-left edge = conservative): field-wire insulation from plug top-left edge (x -3.32, Z 33.6) to the window rim (x -4.72, Z 45) 11.49 + rim depth 3.0 + rear face to shell corner 4.0 + outer left wall down to the clamp top (Z 48 -> 45) 3.0 + clamp top face to insert edge 5.2. No air leg in the route. Insert therefore not moved.
- **Clamp screws:** all three left clamps (y 2 / 118 / 178) now use **all-nylon PA66 M4x35 thumb screws** (non-conductive, no metal tip). Brass insert kept (creepage OK). Retention re-checked: CLAMP_RETENTION.md phase 14.
- **PE boss moved to PE_NEW (12.3, -7.5)** (bare Ø8, same stack). (16, 3) is behind the display glass (no bezel metal there). H4 PE boss deleted (H4 = plain NPTH); right terminal window back to y 182; new rear-wall PE access window x 3-20, y -21..-1; M5 test spot moved to the bezel left edge (x -26.22, y -7.5). Nearest/farthest J28/J29 pad 31.0 / 103.9 mm. Board change BCR-11 (hole + move D5 and GND vias). See PE_BOND.md.
- **PE wire:** green/yellow Cu ≥ 2.5 mm² (14 AWG) and ≥ the sense wire; 4 mm² (12 AWG) where not mechanically protected. Ring terminal specified (blue 1.5-2.5 / yellow 4-6 mm², M4).
- **Coating wording** replaced everywhere with Compliance's text (conformal_coating_spec.md): no spacing credit, not IEC 60664-3 qualified, PD2 rests on filters + seal, 6.6 mm rule stays.
- checks.json: 0 interferences; left wall y 15-105 solid 1.000; HV lead-tip/clamp clearances unchanged (7.0/8.0, 13.48/14.14, 11.29).
- Open: KF2EDGRM (J30) voltage rating ≥ 600 V not verified (Compliance open item).

## Phase 15 (window covers, finger probe, nylon screw docs, BCR-11 numbers)
- **All 5 rear wiring windows are covered:** PA12 SLS snap covers on 1.5 mm closed-cell EPDM gaskets, with grommet slots (split EPDM membrane) or a Ø10 split grommet for PE. The **2 × 12 chimney slots in the top/bottom walls are deleted** (they were unfiltered side inlets). J10/J11 tunnels have foam rings at the 0.5 mm foot gap, and the fin-plate land gets a FIP silicone bead. No positive pressure is claimed (the fans are push-pull in series); the PD2 basis is "no unfiltered opening". Full list: **WINDOW_COVERS.md**.
- **Finger probe:** `finger_check.py` (straight rigid Ø12 × 80; articulation not modelled) → `finger_check.json`. With covers on, no window admits the finger. With covers off, the minimum distance is 8.30 mm (LEFT_HV, the finger reaches the J28–J30 plug bodies), PE 8.39, RIGHT 9.89. Plug screw heads are not modelled; see WINDOW_COVERS.md §3.
- **Assembly notes:**
  - Left clamp PA66 nylon screws: finger-tight, ≤ 0.15 N·m, UL94 V-2 or better (supplier datasheet to be confirmed). Re-check at annual service. Humidity-soak retention test in CLAMP_RETENTION.md.
  - Fit the covers after wiring. Thread the wires through the membrane slit, press the cover until all hooks click, then check that the gasket is compressed all round.
  - Opening a cover needs a flat screwdriver. Disconnect the J28/J29 sources before opening LEFT_HV.
- BCR-11 / PE_BOND numbers corrected to Compliance MEASURED values: web to H1 is 1.20 mm; hot copper is 19.0 mm from the hole centre.
- J30 connector swap: pending Ethan; not acted on.

## Phase 16 (NOT committed; lead has not said commit)
- **Outer wrap lips** on the LEFT_HV / BOTTOM / RIGHT covers: 10 mm PA12 lip segments with a 0.6 mm bead in blind 0.8 mm outer-wall grooves (WINDOW_COVERS.md §4). 0 interferences, left wall 1.000, HV and finger results unchanged. **FIRST PRINT FIT TEST REQUIRED** (snap force, far-edge flatness, gasket compression).
- LEFT_HV grommet slot widened from 7 to 9 mm for J30 wire up to 10 mm².
- **J30 = Phoenix PC 5/8-GF-7,62 (1720851) + SPC 5/8-STF-7,62 (1996184)** (Ethan approved). Wire range is rigid 0.2–10 mm², flexible 0.2–6 mm² (VERIFIED, Phoenix page). Data in J30_PHOENIX_DATA.md. The CAD J30 model is NOT changed yet.
- **PENDING (new J30 footprint from Layout):** redo the CAD J30 model from the Phoenix 3D/drawing; the J28–J30 window, slot and cover size (plus the wrap-lip positions); clamp clearances at y 118 and y 178; the creepage / J30 surface-path numbers; and the finger check. Download the Phoenix drawing / 3D model for 1996184 and 1720851 first, so the mated height is verified. See MISMATCH #46.

## Phase 17
- **LEFT cover lip bead and groove deferred** until Compliance rules on the 2.2 mm wall next to J30 (`LEFT_LIP_BEAD = False`; set it to True to restore). The left lips only locate the cover, so far-edge hold-down is reduced and the first print fit test must cover it. BOTTOM and RIGHT keep their beads and grooves. Details in WINDOW_COVERS.md.
- PENDING J30 redo (MISMATCH #46) also requires: **download the Phoenix drawing / 3D model for plug 1996184 and header 1720851 so the mated height is verified, not inferred.**
- Costs unchanged (removing the bead and groove has no cost effect; ESTIMATED).

## Phase 18
- **Left lip bead and groove restored** (`LEFT_LIP_BEAD = True`; Compliance hv_rulings_phase16 §B(e)). Wall minimum 2.2 mm vs the 2.0 mm design minimum. Left wall y 15–105 solid 1.000. MISMATCH #48 closed.
- **J28–J30 cover is tool-only:** a captive PA66 M3 slotted screw at (6, 173) into a PA12 boss, plus screwdriver-release hooks. All plastic.
- **Cover-off warning label** (verbatim, hv_rulings_phase16.md §B(c)): "DANGER: Hazardous voltage up to 600 V AC. Isolate all voltage inputs and short CT secondaries at the external shorting terminals before removing this cover or unplugging J28/J29/J30. Do not plug or unplug under voltage." W012 + IEC 61010-1 symbols 14/12. One label on the cover outside face (5.5 × 140 mm) and one on the shell beside the window (30 × 15 mm). UL 969 laminated PET/polyimide for salt air. See WINDOW_COVERS.md.
- The physical IEC 61032 probe-B test is still required (checklist in WINDOW_COVERS.md).
- **UL note, J30 header 1720851:** at 600 V it may be used only under **UL use group D (600 V / 5 A) or group F (600 V / 41 A)**; groups B and C are 300 / 150 V. The plug 1996184 is cULus 600 V / 35 A. The NRTL decides the group. If group D governs, CT continuous current must be ≤ 5 A (Compliance §B(b)).

## Phase 19 (Ethan's decisions, Oct 25 2026): DIY cleanup + bezel-to-panel bond through the clamps
**Removed (history in git, a915be1):**
- PE: the PE_NEW boss (12.3, -7.5), rear PE window, PE cover and grommet, ring terminals, star washer, screw, lug, PE wire spec, bond-test masks M1-M5 and the bond-test procedure. PE_BOND.md is now a short note. BCR-11 is **WITHDRAWN**. MISMATCH #35-40 and #47-50 are closed by decision (#46, the J30 footprint, is still pending). H1-H3 CHASSIS bosses stay; H4 stays a plain hole.
- Nylon clamp screws, the UL94 note, the 0.15 N·m limit and the humidity soak test. All clamps are ordinary steel M4 x 35 (CLAMP_RETENTION.md). L118 metal is 11.29 mm from the J30 envelope (≥ 8.0), so no nylon is needed.
- Wrap lips, beads and grooves (`WRAP_LIPS_ON = False`; left wall plain). The captive nylon latch screw, tab and boss (the J28-J30 cover is snap-only, 3 hooks). The probe-B checklist and probe-B language. `finger_check.py` stays as an informal sanity check.
- Restored PE-only geometry: the key membrane is no longer notched for the PE boss. The right window is already at y 182 (since Phase 14).
- Kept: snap covers with gaskets and membranes, one simple printed label (verbatim text, WINDOW_COVERS.md), and J30_PHOENIX_DATA.md.

**Bezel-to-panel bond (CAD part `bond_hw` plus 2 landings on `bezel`; `BOND_CLAMPS` in enclosure_v3.py):**
- **Bond clamps: TOP x 72.9 and TOP x 203.5 (2 in parallel).**
  - BOTTOM (x 72.9, 203.5) and RIGHT (y 90) are not used. Their inward wall bosses overhang the PCB edge (inner boss face y 193.23 vs PCB edge 194.73; x 278.78 vs 280.28), so an internal strap would have to pass within about 0.8 mm of the PCB edge, between the board and the 2 mm wall gap. That does not fit with margin. The top has an 8 mm gap between the inner wall and the PCB (y -23.27 to -15.27).
  - The 3 left clamps are not bond clamps (steering).
- **Path, per bond clamp:**
  1. **A2 stainless M4 x 35 cup-point screw.** The cup bites through the paint on the rear panel face.
  2. **M4 brass heat-set insert** in the clamp block.
  3. **Tinned-Cu bridge strip** 0.5 x 6 mm, on top of the clamp block, from the M4 insert to the M3 insert. Its eye is captured under the M4 insert flange (pressed through the eye while heat-setting).
  4. The bridge strip bends into the tongue to an **M3 brass heat-set insert** in the clamp block just outside the wall, at Z 41.25 (x = clamp x - 5, so the strap clears the 600 V barrier rib at x 73-75; y -30.8 to -26.8).
  5. **M3 x 8 A2 screw** from INSIDE the shell, through a Ø3.4 hole (modelled as a 3.4 mm square) in the shell wall and the 2 mm PA12 web of the wall boss between the T-slot end (y -21.77) and the boss inner face (y -19.77), into that M3 insert.
  6. Its head clamps the eye of an **internal tinned-Cu strap** 0.5 x 6 mm. The strap runs down the inside of the top wall in the plane y -17.77 to -17.27, from Z 44.75 to Z 10, then turns into a foot along +x (Z 10-10.5) to the landing.
  7. **M3 x 6 A2 screw** with an internal-tooth washer into a **bare tapped landing boss** on the bezel: Ø6, Z 4-10, at (x+20, -19.8), i.e. (92.9, -19.8) and (223.5, -19.8). That is between the key caps (they reach y -16.2) and the inner shell wall (y -23.27).
  - The key membrane is notched Ø8 around each landing.
  - Nothing passes through H1-H3, any PCB pad or the PCB. There is no wire out the back and nothing goes through the panel.
  - The path has several thread joints, so it relies on the meter check below.
- **Anodise:** mask off each landing face and its M3 tap (2 spots), plus one Ø6 **bare test spot** on the bezel outer edge at the top-left corner, for the meter probe. All three can be plugs or caps, or a post-anodise spot-face.
- **Installer note:** Mount to a bare-metal panel contact or scrape paint under the clamp tips; check continuity from bezel to panel with a meter (under 1 ohm).

**Checks (checks.json, MODELLED):**
- 0 interferences, with 1 mm and 6 mm panels, the sealed shell, the PCB, parts, keys and membrane. The bond hardware is allowed to touch only the bezel landing and its own clamp; it is checked against the shell, which has Ø3.4 holes for the bond screws.
- Left wall y 15-105 solid fraction 1.000.
- Bond-path metal minimum distance to live copper and the J28-J30 envelopes:
  - T72.9: 38.18 mm (strap vertical)
  - T203.5: 54.86 mm (strap foot)
  - Both ≥ 8.0. The right clamp is not in the bond set; its steel screw is 67.5 mm away (≥ 13).
- Per-clamp screw/insert minimum (mm): L2 13.48, L118 11.29, L178 18.49, T72.9 54.97, T203.5 80.94, B72.9 60.16, B203.5 155.6, R90 67.5.
- Finger check (informal): covers off, worst LEFT_HV 8.30. Covers on: no entry.
- HV values unchanged: lead tips 1.0 mm to the bezel 8.0 and to the display 10.44; J30 surface path 26.69.
- Thermal: no relevant geometry changed, so the thermal docs are not updated.
- Costs: PARTS_COSTED.md "Phase 19".

## Phase 20 (Ethan's decision, Oct 25 2026): primary ground stud + clamp bond kept as backup
- **Primary earth:** M4 x 30 A2 stud (hex bolt) through a gasketed Ø4.5 hole in the TOP side wall at x 140, Z 30. Inside, a tinned-Cu strap runs from the stud head to a bare (masked) bezel landing at (140, -19.8). See GROUND.md for the geometry, parts and why this location.
  - No board change; BCR-11 stays withdrawn.
  - Ground-symbol sticker (IEC 60417-5019 symbol) next to the stud.
- **Installer notes:**
  - Primary: Land one green/yellow wire (at least 2.5 mm2) on the stud to panel/cabinet earth.
  - Backup (clamp bond, unchanged from Phase 19): Mount to a bare-metal panel contact or scrape paint under the clamp tips; check continuity from bezel to panel with a meter (under 1 ohm).
- **Checks (MODELLED):**
  - 0 interferences with 1 mm and 6 mm panels.
  - Left wall y15-105 solid 1.000.
  - Stud stack minimum to live copper 95.1 mm (rule 38.0).
  - Clamp bond 38.18 / 54.86 mm (unchanged).
  - HV values unchanged: lead tips to the bezel 8.0, to the display 10.44.
  - Finger check: covers on, no entry; covers off, unchanged (LEFT_HV 8.30, TOP 24.25, BOTTOM 31.18, RIGHT 9.89, J10 13.96).
  - Thermal: geometry near the heat path is unchanged (the stud is 65 mm from the heat bar), so the thermal numbers are unchanged.
- Costs: PARTS_COSTED.md "Phase 20".

## Phase 21: stud moved to the REAR face; Compliance phase 20 notes folded in (DIY, cheap parts)
- **Stud:** vertical M4 x 25 A2 hex bolt through the rear face at (257.5, -19.2), top-right.
  - The strap (~120 mm tinned Cu) runs from a new bare bezel landing at (182, -19.8), along the inner top wall over the heat bar.
  - The strap joint is metal-to-metal: bolt head, tooth washer, strap eye, tooth washer, nylock. No plastic or gasket is in that clamp.
  - The hex head is held in a PA12 hex pocket (anti-rotation). The outer gasket and seal nut close the hole. Installer nut about 1.2 N·m (ESTIMATED).
  - See GROUND.md.
- **Assembly step:** dab anti-oxidant joint compound on the bare landings (stud landing, both clamp-bond landings) and the strap eyes before fitting. Or conversion-coat the masked spots.
- **Test spot:** the existing bare spot (928bbe8, top-left bezel edge) is reused.
- **Clamp backup unchanged.** Installer notes unchanged (stud primary, clamp bond backup).
- **Checks (MODELLED):**
  - 0 interferences with 1 mm and 6 mm panels.
  - Left wall 1.000.
  - Stud stack minimum to live copper 40.33 mm (rule 38).
  - Clamp bond 38.18 / 54.86 (unchanged).
  - Lead tips 8.0 / 10.44 (unchanged).
  - Finger check: covers on, no entry; covers off unchanged.
  - Thermal: heat-path geometry unchanged (the strap passes 1.7 mm above the heat bar, not touching it), so the thermal numbers are unchanged.

## Phase 22
- Stud anti-rotation pocket is now a true hex, 7.2 mm AF, sized for the ISO 4017 M4 head (7.0 AF), with a side-entry slot. Two printed PA12 strap clips on the inner top wall at x 186 and x 235. Details in GROUND.md.
- **Checks (MODELLED):**
  - 0 interferences with 1 mm and 6 mm panels.
  - Left wall 1.000.
  - Finger check unchanged (covers on: no entry).
  - Stud metal minimum 40.33 mm (rule 38).
  - Clearances unchanged: heat bar 1.71, clamps 2.5.
  - HV unchanged: 8.0 / 10.44; clamp bond 38.18 / 54.86.
  - Thermal geometry unchanged.
- Cost: $0 (printed in the shell).

## Phase 23: PA12 front ring removed (Ethan)
- **Removed:**
  - `front_ring` part (3 mm PA12 face cover, 1 mm air break, stand-off pips and key/ALS pockets) and `RING_T` / `RING_GAP`.
  - step/front_ring.step.
  - The ring's BOM line.
- **Front is now the bare black-anodised 6061 bezel face (Z 0).**
- **Knock-on changes (reported, not silent):**
  - **Glass:** to stay flush with the bare face, the display (part unchanged) moves back 4 mm to DZ = 0. Glass front is at Z 0.05 (−0.05 vs the face), the phase 1-5 position.
    - Display-to-PCB air gap is now 7.44 mm (TFT/HV area) and 3.27 mm (source band), down from 11.44 / 7.27.
    - Glass ledge back at Z 9.5. 0 interferences.
  - **Glass edge:** the 1.5 mm PA12 sleeve that was part of the ring is kept as its own `glass_sleeve` part (Z 0-8.5, front flush). It keeps the glass-edge isolation and the 0.5 mm silicone bead. A thin PA12 line is visible around the glass.
  - **Keys:** caps unchanged. The heads (Z −2.3 to −1.3) now stand 1.3-2.3 mm proud of the bezel face; before, they sat 1.7 mm recessed in ring pockets. Key travel and guides are unchanged.
  - **ALS light pipe:** front moved from Z −4 to Z 0 (flush with the face). Same pipe otherwise.
  - **Depth:** total depth behind the front face is 68.25 mm (was 72.25 including the ring).
  - **Unaffected:** retention, panel gasket and bezel rim (Z 4-9.5), clamps. The ring had no screws (pips only).
- **Checks (MODELLED):**
  - 0 interferences with 1 mm and 6 mm panels; display, sleeve, light pipe and caps clash with nothing.
  - Left wall 1.000; finger check unchanged.
  - HV/clamp/bond/stud distances unchanged: stud minimum 40.33 mm, clamp bond 38.18 / 54.86.
- **Thermal:** HEAT_PATH.md Phase 23 (the bezel face reaches 109-114 F with fans running). The CAD heat bar is screwed to the bezel boss; this was unmodelled before, now modelled.
- Ground stud, hex pocket, clamp bond and clips are unchanged.
