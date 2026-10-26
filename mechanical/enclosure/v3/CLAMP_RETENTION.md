# CLAMP_RETENTION (phase 12): is the panel held adequately?
Hand calcs only. Labels: MEASURED (CAD/checks.json), ESTIMATED, ASSUMED. Nothing tested.

## Layout checked
- Phase 11 layout: T x 72.9/203.5, B x 72.9/203.5, R y 90, L y -2/178. **Left edge unsupported span 180 mm** (MEASURED), vs 130.6 mm between the top/bottom clamps.
- **Changed in phase 12:** L y **5 / 116 / 178** (slots y -4..14, 107..125, 169..187). Left spans 111 / 62 mm. No slot in y 15-105.
- After the change (MEASURED, checks.json): left wall y 15-105 solid fraction **1.000**; 0 interferences; panel 1.0 and 6.0 mm OK.
  - J28/J29 plug to nearest left insert 12.03 / screw 12.68 mm (≥ 8.0 reinforced).
  - J30 plug to insert 11.29 mm.
- Creepage via the HV terminal window (MODELLED, same route as PE_BOND/phase 11): y 116 clamp to J29 = 5.2 + 3.0 + 4.0 + 4.0 + 11.4 (air crossing > 1.5 mm X) = **27.6 mm** (≥ 12.6). To J30 = 26.7 mm.

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
