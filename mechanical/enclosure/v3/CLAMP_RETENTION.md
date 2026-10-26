# CLAMP_RETENTION (phase 12): is the panel held adequately?
Hand calcs only. Labels: MEASURED (CAD/checks.json), ESTIMATED, ASSUMED. Nothing tested.

## Layout checked
- Phase 11 layout: T x 72.9/203.5, B x 72.9/203.5, R y 90, L y -2/178. **Left edge unsupported span 180 mm** (MEASURED), vs 130.6 mm between the top/bottom clamps.
- **Changed in phase 12:** L y **5 / 116 / 178** (slots y -4..14, 107..125, 169..187). Left spans 111 / 62 mm. No slot in y 15-105.
- After the change (MEASURED, checks.json): left wall y 15-105 solid fraction **1.000**; 0 interferences; panel 1.0 and 6.0 mm OK.
  - J28/J29 plug to nearest left insert 12.03 / screw 12.68 mm (≥ 8.0 reinforced).
  - J30 plug to insert 11.29 mm.
- Creepage (phase 13): route figures removed. Straight-line distance is used as a lower bound for creepage (my own conservative method, not a standard rule; PD2 assumed on the enclosure seal + filters; coating gives no spacing credit). See the phase 13 update below.

## Loads
- **Mass, ESTIMATED 3.2 kg.**
  - Al 531.6 cm3 × 2.70 = 1.44 kg (CAD volumes).
  - Display 1.0 kg ASSUMED (mass not in our data; envelope 451 cm3).
  - PA12 329 cm3 × 1.0 = 0.33 kg; PCB 95 cm3 × 1.85 = 0.18 kg; rear parts 0.15 kg ASSUMED; fans, keys and hardware about 0.1 kg.
- **Gasket force.** Rim land 9 mm × about 1150 mm perimeter = 10 350 mm2 (MEASURED geometry). 2.0 mm gasket at 30 % compression (GASKET_C 0.7). Closed-cell sponge CFD **50 kPa ASSUMED** (supplier datasheet needed) → **≈ 520 N total**, ≈ 0.45 N/mm line load. With 9 clamps ≈ 58 N per clamp.
- **Clamp capacity.**
  - M4 nylon-tip thumb screw, hand torque 0.3 N·m ASSUMED, K 0.2 ASSUMED → about 375 N available per screw. The gasket needs about 58 N.
  - M4 heat-set insert pull-out in PA12: several hundred N ESTIMATED (insert vendor data needed).
  - Margin is ample. The risk is over-torque cracking a thin panel, so a torque note is needed.
- **Vibration: no spec cited** (IEC 60068-2-6 values not verified). **ASSUMED 3 g** generic peak, out of plane.
  - Out-of-plane force 3.2 × 9.81 × 3 = 94 N, against 520 N gasket preload → no lift-off.
  - Rocking moment with CG about 30 mm behind the panel (ESTIMATED) = 94 N × 0.03 m = 2.8 N·m, against a preload couple of about 520 N × 0.12 m ≈ 62 N·m → no rocking.
  - In-plane load is carried by the shell bearing on the cutout (1.0 mm/side gap) plus friction μ 0.2 ASSUMED × 520 N ≈ 104 N, against 94 N at 3 g. Bearing governs; the gap allows ≤ 1 mm shift before bearing.

## Panel/bezel bowing between left clamps (ASSUMED simply supported, conservative)
- **Bezel** (6061; rim 9 × 9.5 plus 30 mm of 4 mm field, I ≈ 1000 mm4 ESTIMATED): δ = 5qL⁴/384EI.
  - L 180 mm: 0.089 mm, i.e. 15 % of the 0.6 mm gasket compression.
  - L 111 mm: 0.013 mm (2 %).
- **Thin panel** (1 mm Al, 20 mm effective edge strip ASSUMED): the panel's own edge strip cannot resist the gasket alone over 180 mm. The beam calc gives tens of mm, meaning the panel edge lifts until the gasket force redistributes. So sealing between widely spaced clamps relies on the bezel and on panel plate action.
  - Deflection ∝ L⁴: 180 vs 130.6 mm = 3.6× worse than the top edge.
  - 111 mm is 0.52× the top span.

## Conclusion
- The phase 11 layout (left 180 mm span) is probably adequate on a 3-6 mm panel. It is **marginal for 1-1.5 mm sheet panels** (INFERRED: gasket lift at mid-left, the HV side).
- **Recommendation, implemented in CAD:** use three left clamps at y 5 / 116 / 178 instead of a y 90 clamp. Max left span 111 mm; wall y 15-105 stays solid (1.000); HV clearances ≥ 11.3 mm and creepage ≥ 26.7 mm.
- **Cost:** +1 clamp set (PA12 block, M4 insert, nylon-tip thumb screw) ≈ **$4 / $3** at qty 1/10 (ESTIMATED).
- No tab or rib is needed.
- **Assembly note:** thumb screws finger-tight, ≈ 0.3 N·m.
- **Open:** gasket CFD, display mass, insert pull-out and a real vibration spec. Verify with a shake/peel test on a 1 mm panel.

## Phase 13 update
- Left clamps moved y 5 / 116 -> **y 2 / 118** (slots y -7..11, 109..127), y 178 unchanged. Left spans 116 / 60 mm (was 111 / 62); retention conclusions unchanged (INFERRED, same span class).
- checks.json (MODELLED): 0 interferences; wall y 15-105 solid 1.000; J28/J29 plug to insert **13.48** / screw **14.14 mm** (≥ 12.6 reinforced, ≥ 6.6 PD2 basic); J30 to insert 11.29 mm (≥ 6.6; class for J30 CT secondaries for Compliance).

## Phase 14: current layout with nylon screws
- **Layout (MEASURED, CAD):** T x 72.9/203.5, B x 72.9/203.5, R y 90, **L y 2 / 118 / 178** (unchanged in phase 14; J30 creepage passed without a move). 8 clamps in total. Left spans 116 / 60 mm; top/bottom span 130.6 mm.
- **Correction:** earlier text said 9 clamps. CAD has **8**, so the gasket load is 520 N / 8 ≈ **65 N per clamp** (gasket CFD still ASSUMED 50 kPa).
- **Left clamp screws are now all-nylon PA66 M4x35 thumb screws** (no metal tip). T/B/R clamps keep the nylon-tip steel screws.
- **Nylon M4 data (supplier data, typical, dry, 23 °C (73 °F), not guaranteed):**
  - RGA Fasteners, PA6.6: recommended tightening torque **0.30 N·m**, ultimate tensile **0.50 kN** (https://rgafasteners.com/media/011M/Nylon-Allthread.pdf).
  - TR Fastenings, nylon 6/6 screws: torsional strength **0.2 N·m** (https://www.trfastenings.com/knowledge-base/metric-screws/torsional-performance-pa66-screws).
  - plasticnutsandbolts.com: maximum torque 0.45 N·m; 0.36-0.43 N·m before deformation (https://www.plasticnutsandbolts.com/mechtech.html).
  - PA66 tensile modulus 2.4-3.0 GPa dry; continuous use 95 °C (203 °F) (Caterpillar Red PA66 datasheet).
- **Torque and thrust:**
  - Assembly torque **≤ 0.15 N·m**, finger-tight, no tool. This is ASSUMED, below the lowest cited limit of 0.2 N·m.
  - Thrust F = T / (K·d) = 0.15 / (0.2 × 0.004) ≈ **188 N**. K 0.2 is ASSUMED. Friction at the tip on the panel lowers this, so the ESTIMATED range is 100-190 N.
  - Against 65 N needed, the margin is **≈ 1.5-2.9×** (ESTIMATED). It was ≈ 5.8× with 0.3 N·m steel.
- **Buckling of the nylon shank:**
  - Root Ø3.2 mm, I = 5.15 mm⁴ (ESTIMATED). Free length 25.6 / 20.6 mm for 1 / 6 mm panels (MEASURED CAD: Z 37.5 minus the panel rear).
  - Tip seated (fixed-pinned, K 0.7): **190 N wet** (E 1.2 GPa ASSUMED) / 380 N dry at 25.6 mm. ≥ 65 N, OK.
  - Free tip (fixed-free, K 2): 23 N wet / 47 N dry at 25.6 mm. **< 65 N**: a loose or unseated tip can buckle. The screw must be seated on the panel; the thrust also keeps it seated (INFERRED).
- **Vibration:** 3 g ASSUMED gives 94 N out of plane, against ≥ 520 N total gasket preload. Unchanged, no lift-off (ESTIMATED).
- **Bowing:**
  - Bezel over 116 mm: 0.089 × (116/180)⁴ = **0.015 mm** (2.6 % of the 0.6 mm gasket compression).
  - Thin-panel edge over 116 mm: 0.62× the top-span severity.
- **Verdict (phase 14):** **adequate**, with less margin than steel.
  - Risks: nylon creep and stress relaxation under sustained thrust, made worse by humidity (Hawaii) and heat near 50 °C (122 °F) ambient. Expect preload loss over time (ESTIMATED; no creep data cited).
  - Mitigations:
    - Check or re-snug at commissioning and at the first filter clean.
    - If a shake/peel test on a 1 mm panel shows lift, use glass-filled PA66 or PEEK M4 screws, which are non-conductive and stiffer (ESTIMATED +$1-2 each).
  - **Assembly note changed:** nylon thumb screws are finger-tight, ≤ 0.15 N·m. Do not use a driver.
- **Open:** gasket CFD, nylon creep data, a real vibration spec, and a shake/peel test.
