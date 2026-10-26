# Phase 15: rear/side openings, covers, grommets, finger probe (2026-10-25)
Input: Compliance hv_rulings_phase15.md (read-only). Nothing certified; NRTL / qualified HV engineer review required.
**J30 connector swap: pending Ethan's decision; NOT acted on.**

## 1. Every opening in the rear shell (enumerated from `rear_shell()` / `fin_plate()` / `fans()`, enclosure coords mm, +y down)
| # | opening | x | y | size | through | Phase 15 treatment |
|---|---|---|---|---|---|---|
| 1 | PE lug window | 3.0 – 20.0 | −21.0 – −1.0 | 17 × 20 | rear wall Z 44–48 | **PE cover**: PA12 plate 20 × 23 (x 1.5–21.5, y −22.5–0.5), Ø10 hole + split EPDM grommet (wire OD ≈ 3–6 mm) |
| 2 | J28/J29/J30 wiring window | −4.72 – 13.28 | 9 – 164 | 18 × 155 | rear wall | **LEFT_HV cover**: x −8.0–15.5, y 6–167; slot 9 × 145 (x 0–9, y 14–159; phase 16 widened from 7 mm for 10 mm² wire) + slit EPDM membrane |
| 3 | top terminal row window | 28 – 248 | −16.27 – −2.27 | 220 × 14 | rear wall | **TOP cover**: x 25–251, y −19.27–−0.27; slot 210 × 8 + membrane |
| 4 | bottom terminal row window | 28 – 248 | 180.73 – 195.73 | 220 × 15 | rear wall | **BOTTOM cover**: x 25–251, y 178.5–198.73; slot 210 × 8 + membrane |
| 5 | right terminal window (J1/J23/J6/J7) | 262.28 – 281.28 | 34 – 182 | 19 × 148 | rear wall | **RIGHT cover**: x 259–284.5, y 31–185; slot 8 × 138 + membrane |
| 6 | REAR_OPEN under fin plate | 20 – 255 | 4 – 176 | 235 × 172 | rear wall | closed by the 4.75 mm Al FIN_PLATE (16–258, 1–178). Land 3–4 mm: **add FIP silicone bead** (doc only, Z stack unchanged, ASSUMED ≤ 0.1 mm) |
| 7 | 2 fan holes in fin plate | (128, 26), (128, 152) | | Ø FAN_HOLE | plate | fans on gaskets + **washable filter covers** (the PD2 filtered path, unchanged) |
| 8 | fan / strip / post screw holes in plate | various | | Ø2.5–4.5 | plate | filled by their screws |
| 9 | J10 RJ45 tunnel | 20 × 24 at J10 | | | sealed tunnel; 0.5 mm TUN_GAP at foot | **new closed-cell foam ring** (`tunnel_seals`) closes the 0.5 mm gap to the jack shell; open mouth leads only into the jack (rubber dust cap when unused, recommended) |
| 10 | J11 USB-C tunnel | 16 × 10 at J11 | | | same | same foam ring |
| 11 | **chimney slots (2 × 12)** | x 100 + 9i, 4 wide | top wall y −26.27, bottom wall y 199.73 | 4 × 12 (Z 22–34) | **side walls** | **DELETED in CAD.** Legacy pre-fan passive vents; they were unfiltered side inlets. The phase-9 thermal model never credited them (both-failed path = stalled rotors + filters, 0.20 W/K), so thermal results are unchanged (INFERRED). |
| 12 | clamp T-slots (8) | | | | blind | no through path |
| 13 | flange joint-screw holes | | | | flange, outside the cutout, in front of the panel gasket | filled by M4 screws |

All 5 wiring windows now have covers (Compliance option (b)). **Pressure statement:** the fans are push-pull in series (intake and exhaust both through filters on the same plate). No positive pressure is computed or claimed; the design relies on **no unfiltered opening**, not on pressure. Residual leaks (ESTIMATED): membrane slits around wires, cover gaskets, plate land; all small compared with the fan holes, but not quantified.

## 2. Cover design (CAD parts `window_covers`, `cover_gaskets`, `grommets`, `tunnel_seals`)
- PA12 SLS plate 3.0 mm (Z 49.5–52.5) on a 1.5 mm closed-cell EPDM/foam gasket ring (Z 48–49.5) bearing on the rear face around the window (ESTIMATED design values; compression set not modelled).
- **Fixing: snap hooks, no metal** (no new unearthed metal near HV). 8 × 1.5 mm hook tabs pass through the window edge and catch under the 3 mm rear wall (Z 44–45). Release with a flat screwdriver through the slot ⇒ **tool required** to open the HV window.
- Hook edges (CAD): PE x0/x1; LEFT_HV x1 only; TOP all four; BOTTOM y0 only; RIGHT x0 only. Edges within 2.5 mm of the inner wall face have no room for a hook. **Phase 16:** LEFT_HV, BOTTOM and RIGHT hook on one edge (3 hooks). Their far edge is now held by **outer wrap lips** (§4).
- Grommets: split EPDM membrane strip 1.0 mm with a centre slit (wires push through, membrane seals around the jacket); PE uses a split rubber grommet in a Ø10 hole.
- Wire sizing (ESTIMATED jacket ODs, H07V-K class): 2.5 mm² ≈ 3.4–4.2, 4 mm² ≈ 3.9–4.8, 10 mm² ≈ 5.6–6.8 mm. The J28/J29 SPC 5/4 plug accepts 0.2–10 mm² (connectors_phoenix.md). The slot is 7–8 mm wide, so it accepts up to 10 mm² single wires. **J30 (phase 16): Ethan approved Phoenix PC 5/8-GF-7,62 + SPC 5/8-STF-7,62; rigid 0.2–10 mm², flexible 0.2–6 mm² VERIFIED (Phoenix product page, see J30_PHOENIX_DATA.md).** The LEFT_HV slot is widened to 9 mm, which takes a 10 mm² jacket (≈ 5.6–6.8 mm, ESTIMATED) with ≥ 1.1 mm per side. The finger still cannot enter (9 < 12). LEFT_HV carries 16 field wires (8 + 8) along 145 mm.
- Serviceability: plugs stay pluggable. Unsnap the cover, slide it up the wires (the membrane slit opens), unplug. PE: unsnap the PE cover for lug access; the M5 test spot on the bezel edge is unchanged.
- Interference re-run: **0** (checks.json). Left wall y 15–105 solid 1.000. HV distances unchanged (7.0/8.0, 9.44/10.44, 13.48/14.14, 11.29, PE 14.0/14.5). J30 surface path 26.69 mm: the LEFT_HV cover now covers the "rear face 4.0" leg with PA12/EPDM. The path can only get longer along the cover joint (INFERRED, not re-modelled).

## 3. Test-finger check (`finger_check.py` → `finger_check.json`; live copper from `finger/export_hv_copper.py` → `finger/hv_copper.json`, read-only pcbnew)
Probe (MODELLED): **straight rigid Ø12 × 80 mm, flat tip**. The IEC 61032 probe B dimensions Ø12 / 80 / stop face Ø50 × 20 come from vendor pages (SECONDARY; the standard itself was not read): bndtestequipment.com (probe B), merhein.com (IEC61032 Fig. 2), ormity.com. **Joint lengths and tip radius not verified ⇒ the articulated finger is NOT modelled.** Sweep: 1 mm grid, 9 directions (normal; 30°/45° toward ±x, ±y), 25 rays per finger cross-section. Live set (ASSUMED conservative): outer-layer copper of every AC-metering net + GND_AC + +3V3_AC + U22/U23 CT. Pass rule (ASSUMED, Compliance to set): no contact and ≥ 8.0 mm.

**Without covers (worst case: cover removed):**
| opening | finger entry | min dist to live copper, mm (MODELLED) | nearest live | touches J28-J30 plug body | result |
|---|---|---|---|---|---|
| PE_window | 287 positions; worst 30deg+y, entry [13.0, -10.0], depth 31.64 mm, stopped by pcb | **8.39** | track GEN_N (F.Cu) | no | PASS |
| LEFT_HV_window | 5931 positions; worst normal, entry [6.28, 134.0], depth 14.4 mm, stopped by rear_parts | **8.3** | J30 CT3_S1 (B.Cu) | J28, J29, J30 | PASS |
| TOP_window | 2514 positions; worst normal, entry [47.0, -9.27], depth 14.4 mm, stopped by rear_parts | **24.25** | RV1 GEN_N (B.Cu) | no | PASS |
| BOTTOM_window | 2295 positions; worst normal, entry [34.0, 187.73], depth 14.4 mm, stopped by rear_parts | **31.18** | RV3 GEN_L3 (B.Cu) | no | PASS |
| RIGHT_window | 6444 positions; worst 30deg-x, entry [271.28, 40.0], depth 25.21 mm, stopped by heat_bar | **9.89** | U23 Net-(U23-CT) (B.Cu) | no | PASS |
| J10_port_tunnel | 664 positions; worst normal, entry [217.0, 47.07], depth 13.5 mm, stopped by rear_parts | **13.96** | U22 Net-(U22-CT) (B.Cu) | no | PASS |
| J11_port_tunnel | NO ENTRY: opening smaller than the 12 mm finger | – | – | – | PASS |
| fan_fan_exhaust_through_filter_cover_slots(3mm) | NO ENTRY: opening smaller than the 12 mm finger | – | – | – | PASS |
| fan_fan_intake_through_filter_cover_slots(3mm) | NO ENTRY: opening smaller than the 12 mm finger | – | – | – | PASS |

**Covers fitted (membranes treated as absent, rigid edges only):**
| opening | finger entry | min dist to live copper, mm (MODELLED) | nearest live | touches J28-J30 plug body | result |
|---|---|---|---|---|---|
| PE_cover_grommet | NO ENTRY: opening smaller than the 12 mm finger | – | – | – | PASS |
| LEFT_HV_cover_grommet | NO ENTRY: opening smaller than the 12 mm finger | – | – | – | PASS |
| TOP_cover_grommet | NO ENTRY: opening smaller than the 12 mm finger | – | – | – | PASS |
| BOTTOM_cover_grommet | NO ENTRY: opening smaller than the 12 mm finger | – | – | – | PASS |
| RIGHT_cover_grommet | NO ENTRY: opening smaller than the 12 mm finger | – | – | – | PASS |
| J10_port_tunnel | 664 positions; worst normal, entry [217.0, 47.07], depth 13.5 mm, stopped by rear_parts | **13.96** | U22 Net-(U22-CT) (B.Cu) | no | PASS |
| J11_port_tunnel | NO ENTRY: opening smaller than the 12 mm finger | – | – | – | PASS |

Findings:
- With covers fitted, no wiring window admits the finger: every rigid slot is 7–8 mm wide and the PE hole is Ø10, all less than 12 mm. J10 (20 × 24) admits the finger to the RJ45 jack body only (13.96 mm from the nearest live copper, U22 CT). This is SELV, unchanged by design.
- Without covers, nothing touches copper and every opening is ≥ 8.0 mm from it, but the margins are thin. **LEFT_HV is 8.30 mm and the finger lands on the J28/J29/J30 plug bodies.** PE is 8.39 mm, via a 30° path under the wall to the GEN_N F.Cu track near (14.8, 19.6). RIGHT is 9.89 mm.
- **J28/J29/J30 live pins through the field-wire window:** with the cover on, the finger cannot reach the plugs. With the cover off (installer service), it reaches the plug rear faces, where the clamp screw heads and wire entries are live metal recessed in the plug housing. **This CAD does not model screw heads, so it cannot show whether they are finger-safe.** Protection rests on: (1) the Phoenix SPC 5/4-STF and Kefa plug housings' own IP20 / finger-safe design (datasheet statement still to be obtained); (2) the snap cover needs a tool to remove; (3) the window faces the cabinet interior (installer area, INFERRED per Compliance). **For Compliance to accept:** the plug datasheets' IP20 / finger-safe claim for J28/J29 and the J30 replacement; a real probe-B test on a printed shell with plugs fitted and covers both on and off; a ruling on whether "cover removed" counts as operator-accessible; and a warning label on the LEFT_HV cover ("Hazardous voltage, disconnect J28/J29 sources before removing").
- Limitations: rigid finger only; flat tip; the 10 N push through a membrane is not simulated (rigid slot edges stop the finger regardless); live screw metal is not modelled.

## 4. Phase 16: outer wrap lips (CAD `window_covers`; grooves in `rear_shell`)
- Far edges: LEFT_HV x0 (outer wall x −8.72), BOTTOM y1 (y 199.73), RIGHT x1 (x 285.28).
- Each lip is a 10 mm segment: the cover plate extends over the shell edge, then a 1.5 mm PA12 lip runs down the OUTER wall face (0.2 mm gap) from Z 52.5 to 43.3. A 0.6 mm bead on the lip snaps into a **blind 0.8 mm groove** cut in the outer wall at Z 43.8–45.0 and holds the far edge down.
- Segments (along the edge): LEFT_HV y 140 and 157 (outside y 15–105, clear of the clamp slots at y 109–127 and 169–187); BOTTOM x 40, 138 and 235 (clear of the B clamps at x 72.9 and 203.5); RIGHT y 50, 140 and 170 (clear of the R clamp at y 90). All values are ESTIMATED design values.
- Checks (MODELLED): 0 interferences (shell, clamps, inserts, screws, panel 1–6 mm). Lips to clamps 6.0 mm, to clamp screws 15.2 mm. Left wall y 15–105 solid 1.000. HV distances, the J30 surface path of 26.69 mm and the clamp clearances are unchanged. The finger check is unchanged: with covers on, nothing can enter. The lips sit outside the shell perimeter at Z ≥ 43.3, behind the panel, so the cover still goes on after the unit is installed. The shell still passes through the cutout (lips are on the cover, not the shell).
- Note: the left grooves at y 140/157 thin the 3 mm wall to 2.2 mm locally, next to the J30 plug (inner face 2.4 mm from the plug body). This is solid insulation and the surface path gets longer, not shorter. **Compliance to confirm** a 2.2 mm PA12 thickness is acceptable there (reinforced solid insulation thickness was not checked). If not, the alternative is lips without beads (location only).
- **FIRST PRINT FIT TEST REQUIRED** for the wrap lip: (1) snap-on / removal force (bead 0.6 mm in PA12; target: firm by hand, tool to release, ASSUMED); (2) flatness of the far edge, gap ≤ 0.2 mm to the gasket all along; (3) gasket compression ≈ 25–40 % everywhere (ESTIMATED target for closed-cell EPDM), checked with feeler/witness; (4) no lip whitening or cracking after 10 cycles.

## Phase 17: LEFT lip bead and groove DEFERRED (pending Compliance ruling on the 2.2 mm wall next to J30)
- `LEFT_LIP_BEAD = False` in enclosure_v3.py. The LEFT_HV lips at y 140 / 157 are **locating lips only** (no bead), and there is **no groove** in the left outer wall. The left wall is the full 3.0 mm there (MODELLED: wall volume Z 43–46, y 130–165 = 315.0 of 315.0 mm³), and y 15–105 is still 1.000 solid. BOTTOM and RIGHT keep their beads and grooves.
- **Restore:** set `LEFT_LIP_BEAD = True` and re-run enclosure_v3.py, finger_check.py and render_v3.py. This restores the bead on the cover and the blind groove in the shell.
- **Retention, LEFT_HV cover:** it is held by 3 snap hooks on the x1 edge only. The far edge (x0) has only the two locating lips, which stop sideways movement but **do not hold the edge down**. Gasket compression at the far edge depends on plate stiffness alone, so **far-edge hold-down is reduced**. It is not quantified; the **FIRST PRINT FIT TEST** must check far-edge lift / flatness and gasket compression along x0. If that fails and Compliance does not accept the groove, options are: a thicker or ribbed cover plate, or a PA66 nylon screw into a boss outside y 15–105 (both need a Compliance check).
- Re-run (MODELLED): 0 interferences; HV distances, the 26.69 mm J30 surface path and the clamp clearances unchanged; finger check unchanged (covers on: no entry; covers off: worst 8.30 mm LEFT_HV).
