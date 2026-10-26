# GROUND: primary rear-face ground stud + backup clamp bond (Phases 20-21, Ethan's decisions Oct 25 2026)
DIY open-source project, not a certified product.

## Primary: M4 ground stud on the REAR face (Phase 21; CAD `ground_stud`, `ground_stud_gasket`, shell `gs_boss()`)
The Phase 20 side-wall stud (x 140, Z 30) is replaced; it is in git history (47c94e7).
- **Final location:** a vertical stud through the **rear face at (257.5, -19.2)**, top-right. It sits right of the TOP cover (x ≤ 251) and above the heat bar (Z ≤ 28.3). It is outside the RIGHT window/cover (y ≥ 31) and away from J10/J11 (y ≥ 30) and the fans/filters (46 / 49 mm). It is about 200 mm from the J28-J30 window. The ring terminal tongue points -y, out over the top edge.
- **Path (inside the shell, no PCB, no H1-H3; no board change, BCR-11 stays withdrawn):**
  1. Bare (masked) bezel landing boss: Ø6, Z 4-10, at (182, -19.8), between keys SW12 and SW13. M3 A2 screw with a tooth washer.
  2. Tinned-Cu strap 0.5 x 6 (3 mm²), about 120 mm, one bent piece. It runs up the inner top wall to Z 35, then along the wall at Z 30-35 over the heat bar (1.7 mm gap) to x 257.5, then up and into the stud joint through a slot in the boss.
  3. **Stud joint (metal-to-metal, item 1):** M4 x 25 A2 hex bolt. Stack from the bottom: head (Z 37-39.8), tooth washer, strap eye, tooth washer, A2 nylock nut (to Z 44.8). The strap is clamped between the bolt head and the inner nut only. No plastic or gasket is in that clamp, so the joint does not loosen as the PA12 relaxes.
  4. **Anti-rotation (item 2):** the hex head sits in a hex pocket of a PA12 cup boss under the rear wall (Ø13, Z 36.5-45, pocket modelled Ø9). The bolt cannot turn, so the installer's outer nut can't spin it. The inner nylock is a separate locked nut.
  5. The bolt passes a Ø4.5 hole in the 3 mm rear wall. Outside, an EPDM gasket washer, A2 washer and seal nut close the hole, so there is no unfiltered opening.
  6. Installer stack: ring terminal, A2 washer, nut, about **1.2 N·m** (ESTIMATED). Hold the seal nut with a spanner while torquing.
- **Corrosion (item 3):** a simple assembly step. Before fitting, put a thin dab of anti-oxidant joint compound (e.g. a zinc-loaded electrical joint paste) on each bare landing face and on the strap eyes: the stud landing (182, -19.8), the two clamp-bond landings (92.9 / 223.5, -19.8), and the stud strap eye. Alternative: chromate/trivalent conversion coat on the masked spots at the anodiser. Wipe the excess off.
- **Test spot (item 4):** reuse the Ø6 bare test spot on the bezel outer edge at the top-left, from 928bbe8. It costs nothing extra. Meter bezel test spot ↔ stud and ↔ panel, under 1 ohm.
- **Installer note:** Land one green/yellow wire (at least 2.5 mm2) on the stud to panel/cabinet earth. A blue 1.5-2.5 mm² M4 ring is supplied; use a yellow 4-6 mm² ring for larger wire.
- **Label:** a printed ground-symbol sticker (IEC 60417-5019 symbol), about 10 x 10 mm, on the rear face next to the stud at x 266-276, y -24 to -14.
- **Distances, MODELLED** (bounding boxes, conservative; to hv_copper.json live outer-layer copper, read-only; nearest is C119 / U23 CT net). Rule: 38.0 mm.

| part | to live copper, mm |
|---|---|
| bolt + head | 43.2 |
| inner joint (washers, eye, nylock) | 44.5 |
| strap (bbox of the whole bent strip) | **40.33 (minimum)** |
| landing screw | 77.49 |
| outer washer + seal nut | 49.58 |
| ring terminal envelope | 51.46 |
| installer washer + nut | 53.24 |

  Other gaps (MODELLED, none touching): TOP window cover 1.41 (outside, beside the outer washer), heat bar 1.71 (strap run), clamps 2.5, clamp-bond hardware 4.55, rear parts 5.55, PCB 3.93, key caps 6.94.

## Backup: clamp-screw bond (Phase 19, 928bbe8, unchanged)
- TOP clamps x 72.9 and 203.5. A2 cup-point M4 screw biting the panel, then the M4 insert, bridge strip, M3 insert, M3 through-boss screw, internal strap, and finally a bare bezel landing at (92.9 / 223.5, -19.8). Details are in README Phase 19.
- **Installer note:** Mount to a bare-metal panel contact or scrape paint under the clamp tips; check continuity from bezel to panel with a meter (under 1 ohm).

## Removed (Phase 19, kept removed)
PE_NEW boss, rear PE window and its cover, grommet and gasket, PE wire spec, M1-M5 masks, bond-test procedure. H1-H3 CHASSIS bosses are unchanged; H4 is a plain hole.

## Phase 22 (Compliance re-check of e4eece6): true hex pocket + strap clips
- **Hex pocket (MODELLED):** a TRUE hex, **7.2 mm across flats** (`GS_HEX_AF`), Z 36.0-39.8. It holds the full 2.8 mm head height of the M4 x 25 A2 **ISO 4017** hex bolt: s = 7.0 max / 6.78 min, e ≥ 7.66, k 2.8 (standard values, ESTIMATED from the ISO 4017 table, not measured).
  - The pocket continues as a 7.2 mm parallel slot open toward +y (the shell interior). The pre-assembled stack (head, tooth washer, strap eye, tooth washer, nylock) slides in sideways, and the head flats bear on the slot walls like a spanner.
  - Above the pocket is a Ø10 counterbore with a 10 mm slot (Z 39.8-44.8) for the washers, eye and nut. The Ø8 tooth washer and the nylock sit there, not in the hex.
  - CAD check: the head in place gives 0 overlap. Rotating it 10° collides with the pocket (0.71 mm³), so it cannot turn.
- **SLS PA12 tolerance:** about ±0.3 mm (ESTIMATED, typical). The pocket prints 6.9 to 7.5 AF.
  - At 7.5 (loose) the pocket is still below the head's 7.66 mm across-corners minimum, so the head still cannot turn.
  - At 6.9 (tight) the head (up to 7.0) needs a light file or press-in.
  - Check on the first print.
- **Strap clips (MODELLED):** 2 PA12 hooks printed into the inner top wall, at **x 186 and x 235**. Each is 4 mm wide, with a hook from above (Z 35-35.8) and a front lip (y -22.37 to -21.77, Z 31-35) holding the strap run (Z 30-35) against the wall.
  - Nothing is below Z 31, so the clips are 10.84 mm from the heat bar, 6.49 mm from the clamps and 8.45 mm from the clamp-bond hardware.
  - Snap the strap in behind the lips at assembly.
- **Distances (MODELLED, unchanged):** strap to the heat bar 1.71 mm, stud metal to the clamps 2.5 mm, outer washer to the TOP cover 1.41 mm. Metal to live copper: minimum 40.33 mm (strap, rule 38). Bolt 43.18, inner joint 44.5, seal nut 49.58, ring 51.46, installer nut 53.24.
