# Blackstart (genctl) front panel V2: flush glued display, wide keys (2026-10-24)

Files: `geometry.py` (source of truth), `draw_front_panel.py` -> `front_panel.png/.svg` (1:1 front view),
`draw_section.py` -> `section_view.png/.svg` (side section through a top-row key). V1 files are kept in `v1_backup/`.
Coordinates: mm, origin = top-left of the cover glass, front view, y down. Z = mm behind the panel face.

## 1. Overall
| Item | V1 | V2 |
|---|---|---|
| Front panel outline | 292.56 x 201.46 | **300.56 x 226.46**, R3 (x -12...288.56, y -23.5...202.96) |
| Panel build | 3 mm plate | CNC 6061-T6: 4.0 mm field, 12.5 mm deep rim round the display window with a rear ledge |
| Display window | - | 277.56 x 180.46 (glass + 0.5 per side) |
| PCB | 284 x 198 | **284 x 210** (x -3.72...280.28, y -15.27...194.73). Grown 12 mm because the key rows moved ~5 mm further out |
| Key centres x | 29.08 72.60 116.12 159.64 203.16 246.68 (unchanged, pitch 43.52 = active width / 6) | same |
| Key centres y | -4.40 / 183.86 | **-9.25 / 188.71** |
| PCB mount holes H1-H4 | (3.5, row y) | (2.0, -9.25) (274.56, -9.25) (2.0, 188.71) (274.56, 188.71). Add 2-4 mid-board holes still recommended |
| Panel-to-housing | - | 8 M4 blind studs (PEM CFHC type) pressed into the rear; no holes through the face |

## 2. Display: flush, glued
Key fact: on this Riverdi part the cover glass and TFT have the **same outline** (276.56 x 179.46, "CG TFT O.D.").
The glass does not overhang the TFT, so you can't glue it to a lip sitting just behind the glass border.
Instead the module drops in from the front into a window, and the lip (ledge) is at the **TFT's rear**:
- Window wall: 0.5 mm gap per side to the glass (glass tolerance ±0.3 gives a 0.2-0.8 joint).
- Ledge face at **Z = 9.5** (CTP+TFT 8.51 ±0.5, plus a 1.0 nominal bond line). It overlaps the TFT rear by **4.0 mm** and is 3.0 thick (rim rear at Z 12.5).
  Top, left and right are full length (with a ~15 mm notch top-left for the backlight cable). **At the bottom the ledge is only at the two corners**
  (x < 20 and x > 256): the TFT source-PCB band (x 20.6-255.6, bottom 29.5 mm, the thickest part) sits there. The touch FPC tail
  exits the bottom edge at about x 217-245 and needs a matching notch. **Check the ledge against the STEP model** for flat rear metal before cutting.
- Flush is set by the **fixture, not by the stack-up**: lay the panel face-down on a flat plate (glass on the plate too), then fill
  the bond line. Target flush 0 / -0.15 mm (glass may sit up to 0.15 below the face, never proud). The 0.5-1.5 bond line takes up the ±0.5 module thickness.
- Adhesive (recommendation): **one-part neutral-cure structural silicone, e.g. DOWSIL 7091** (or Sikasil SG-20 / Dowsil 995 class)
  on the ledge, plus 3-4 small pieces of 3M VHB 4611 (high-temperature grey, 1.1 mm) as spacers/instant hold while it cures.
  Why silicone: it handles rain, UV, -40...+85 °C and vibration, stays elastic (Al and glass expand differently over 277 mm: about 0.3 mm over 60 K),
  neutral cure does not corrode ITO or the bonding, and it **can be cut out**. Avoid acetoxy (vinegar-smell) RTV and rigid epoxy.
  Full VHB bonding is possible but harder to remove and to keep flush.
- Front seal: the 0.5 joint gets a **black neutral-cure silicone bead** (same 7091 black), tooled flush. This is the rain seal for the display.
- **Serviceability, honestly:** semi-serviceable. To replace the display you cut the front bead and the ledge bond with a plastic blade or
  cutting wire from the rear. The old display will probably not survive, and the panel must be cleaned and re-bonded in the fixture. Everything
  else (keys, carrier, PCB) is serviceable without touching the display. If you want the display to be removable, use a screwed rear
  clamp frame with a foam gasket instead of glue. The face can still be flush.

## 3. Keys: 12 wide caps
- 2 rows x 6. Each row spans **exactly the 261.12 mm active width** (outer cap edges line up with the active-area edges).
- **Cap 43.02 x 12.0 mm**, gap **0.5 mm** between caps (a slot clearance, not a visible border). One long slot per row in the panel,
  261.62 x 12.5 (0.25 clearance per side). Cap face 0.5 mm proud of the panel (easier with gloves), 4.0 thick through the panel, 1.0 flange behind
  on the outer side and ends (keeps it from being pushed out from the rear).
- Material: clear PC, with the face diffused or printed and the legend/colour left to the screen labels. Light reaches it through the light pipe.
- Web between the key slot and the display window: 2.5 mm aluminium.

### Anti-wobble: options compared
| Option | Wobble | Robust/outdoor | Service | Verdict |
|---|---|---|---|---|
| Cap on the switch plunger only | bad: 3.8 mm plunger under a 43 mm cap; an end press tilts it and may not actuate | - | easy | **no** |
| Cap + 2 guide stems in bushings, no coupling | needs guide engagement L >= 2·µ·e = 2·0.25·21.5 ≈ **11 mm** to avoid binding at the end, but only ~5-6 mm fits in the 10.5 mm stack | ok | easy | marginal |
| Hinge/rocker (pivot along the outer edge) | very stiff against twist, but the travel at the switch varies with the press point and the feel is uneven; a hinge in rain/ice is a weak point | fair | fair | no |
| 2-3 switches per cap in parallel | good | good | easy | works, but adds 12-24 switches and changes the schematic |
| **Cap + rigid actuator bar + 2 guide stems + wire stabiliser** (like a keyboard spacebar) | **good**: the wire forces both ends to move the same, so the cap moves straight back wherever it is pressed | good | good | **chosen** |

### Chosen mechanism (see `section_view.png`)
Front to back:
1. **Cap** (clear PC) in the panel slot (0.25 clearance per side, which also guides the face).
2. **Silicone sheet**, one per row: translucent, 1.0 mm, Shore 50-60A. It has a flat plateau behind each cap, rolling convolutions in the 0.5 gaps
   and at the ends, and a perimeter bead clamped between the carrier and the panel rear. This is the rain seal: everything behind it stays dry.
3. **Actuator bar** (clear PC, 2.0 thick, about 41 x 10.6). It is screwed to the cap with **2 x M2** through moulded thickened bosses in the sheet.
   The bosses are compressed about 25 % so they seal like gaskets. Cap, sheet and bar form one rigid sandwich, and you can unscrew it to service.
4. On the bar: a **centre light pipe Ø3.6** down to the switch plunger (0.1 gap at rest), and **two guide stems Ø3.0 at x = centre ±17**
   (span 34 of 43.02) running in **Ø3.15 PTFE-filled POM bushings**, with 6 mm engagement, in the carrier.
5. **Stabiliser**: Ø1.0 stainless spring wire (keyboard-stabiliser style, U shape, 34 mm span). It clips into the carrier and its ends sit
   in slots at the two stem roots. The wire turns as one piece, so both ends of the bar have to move the same distance. Lightly grease it (stops rattle).
6. **Carrier**: PC-GF30 moulding or a machined Al bar, one per row. It holds the bushings and the wire, clamps the sheet, and has the hard stop.
   It is screwed to M3 studs on the panel rear.
7. **Switch** CTS 228EMV RGB on the main PCB, F side at Z = 16.0, so the plunger top is at Z = 10.5.

Geometry rule (why it does not tilt or bind): when you press at distance e from the centre, the force tries to tilt the bar.
- Without coupling, the guides avoid binding only if engagement L > 2·µ·e. The worst case is e = 21.5 (cap end) and µ ≈ 0.25 (PC on POM), so L would need to be about 11 mm. That does not fit.
- With the wire stabiliser, the tilting moment F·e goes into the wire as torsion, not into the bushings. So the bushings only take side loads, and the cap moves straight back.
- Leftover tilt is about (bore clearance 0.15 + wire play ~0.1) / span 34 ≈ 0.4°, which is about **0.15 mm at the cap end**. Side wobble is set by the 0.25 slot clearance.
- Keep the guide span at least 0.75 x cap width (34/43 = 0.79), and keep the press point within the cap, which the slot guarantees.

Travel and force (CTS datasheet): travel 0.7 ± 0.2, operating force 200 ± 50 gf, actuator strength 2 kgf max, life 100k cycles.
Free gap 0.1 at rest, so the switch makes at 0.8 ± 0.2 of cap travel. **Hard stop at 1.2** (bar shoulder on the carrier), so the switch is never
over-pressed past its own bottom (0.9 max) and a glove punch or hail goes into the carrier, not the switch.
Feel: about 2.0-3.0 N total (switch + sheet), with a click.
Light: the switch's RGB LED shines up the clear light pipe, through the bar and the translucent sheet plateau, into the diffused cap.
Expect a bright centre spot. Add a diffuser texture on the cap back, or a white print on the cap's inner face except a window, to spread it.

## 4. Electrical / board
- No schematic change needed with the chosen mechanism: still 12 x 228EMV, one per key, and the same nets.
  (If you prefer 2 switches per cap instead of the wire stabiliser, that is a schematic change for the other worker: add SW21-SW32 in parallel.)
- Board **284 x 210** (was 198). Switch footprints move to y = -9.25 / 188.71 (same x). Edge-connector slots shift with the new board edge.
- `place.py` uses `geometry.py`, so the inputs update automatically. A test run against a netlist exported from a **copy** of the current repo state
  (commit db1e115 plus another worker's uncommitted edits) gave 1142 footprints, but it was **not clean**:
  - 7 footprints missing in the lib snapshot: PC5_4-GF-7.62 for J1/J23/J28/J29, DF40C-100DS for U10, SOIC-16W_HV_Slot for U67/U68.
  - U10 is gone from the design.
  - The 3.81 headers J17-J22/J25-J27 are now 41.5 mm wide, wider than the 32 mm slot between key lands.
  - The SPILL zone overflows (U71-U74).
  So `out/genctl_placed.kicad_pcb` was left at V1, and the trial is saved as `out/genctl_placed_v2_DRAFT.kicad_pcb`.
  Re-run once the schematic is settled and `snap/genctl.pretty` is refreshed, then do "Update PCB from Schematic" in pcbnew.

## 5. Open questions
1. Check against the Riverdi STEP: is there flat rear metal under a 4 mm ledge on the top/left/right? What are the exact touch-tail and backlight-cable notch positions?
2. Is 12 mm cap height and 0.5 proud OK? Do you want caps fully flush instead (harder to press with gloves)?
3. Light-pipe hot spot: test a cap sample. A per-key opaque divider in the bar may be needed to stop light bleeding between keys through the sheet.
4. Ice/dirt in the 0.25 slot gap: a drain lip at the bottom of each slot is suggested.
5. The housing depth and gasket are not designed yet; the drawing is schematic only.
6. Material check: PC caps outdoors need a UV-stabilised grade or a hard-coat.
7. Prototype the stabiliser first (a 3D-printed bar + wire + one switch) to confirm wobble and feel before tooling the silicone sheet.
