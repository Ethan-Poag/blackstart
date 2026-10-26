# GROUND: primary ground stud + backup clamp bond (Phase 20, Ethan's decision Oct 25 2026)
DIY open-source project, not a certified product.

## Primary: M4 ground stud (CAD `ground_stud`, `ground_stud_gasket`; `GS_X`, `GS_Z`, `GS_XY` in enclosure_v3.py)
- **Location:** horizontal stud through the **TOP side wall** at x 140.0, Z 30.0, pointing outward (-y) into the cabinet behind the panel.
- **Why there (MODELLED checks):**
  - The phase-14 spots don't work. (16, 3) is behind the display glass. (12.3, -7.5) needed a PCB hole (BCR-11) and sits in the HV corner.
  - The top-right corner (264, -19.6) is blocked by the heat bar (x 205-279.5, y to -22.77, Z 23.5-28.3).
  - A stud straight out the rear face anywhere along the top would sit under the TOP window cover (x 25-251).
  - The bottom and right have only 2 mm between the PCB and the wall.
  - x 140 is between keys SW11 and SW12. It is 65 mm from the 600 V barrier rib (x 73-75), and well away from the T72.9 / T203.5 clamps, the bond landings at x 92.9 / 223.5, J10 / J11, the fans and the filters.
- **Path (all inside the shell, no PCB involvement):**
  1. Bare bezel landing boss: Ø6, Z 4-10, at (140.0, -19.8), M3 tap. Anodise masked (bare spot).
  2. M3 A2 screw with an internal-tooth washer.
  3. Tinned-Cu strap, 0.5 x 6 mm, about 30 mm long. It has a foot on the landing, runs up the inner face of the top wall (y -23.27) to Z 34, and ends in an eye.
  4. Inside the shell: the head of an M4 x 30 A2 hex bolt clamps the strap eye plus an internal-tooth washer against the inner wall face.
  5. The bolt passes through a Ø4.5 hole in the 3 mm PA12 wall.
  6. Outside: an EPDM gasket washer (12 x 12 x 1.5), then an A2 washer and nut, which compress the gasket and seal the hole.
  7. Installer stack: ring terminal, A2 washer, nut (or wing nut).
  - No wire is permanently attached. No PCB hole, no PCB pad, not via H1-H3.
  - **No board change is needed. BCR-11 stays WITHDRAWN.**
- **Sealing:** the stud fills the Ø4.5 hole and the gasket is clamped under the outer nut, so there is no unfiltered opening. The finger check is unchanged: covers on, no entry.
- **Installer note:** Land one green/yellow wire (at least 2.5 mm2) on the stud to panel/cabinet earth. Supplied: one M4 ring terminal for 1.5-2.5 mm² (blue). Use a 4-6 mm² (yellow) ring for larger wire.
- **Label:** a simple printed ground-symbol sticker (IEC 60417-5019 symbol), about 10 x 10 mm, on the outer top wall next to the stud at x 150-160, Z 25-35.
- **Distances, MODELLED** (bounding boxes, conservative; to the hv_copper.json outer-layer live pads and tracks from the PCB, read-only; nearest is RV1 GEN_N). Rule: 38.0 mm.

| part | to live copper, mm |
|---|---|
| stud (M4 bolt + head) | 96.19 |
| strap | 95.1 |
| landing screw | 95.48 |
| outer washer + nut | 98.56 |
| ring terminal envelope (11 mm ring, tongue/barrel/wire to Z 57) | 99.51 |
| installer washer + nut | 101.19 |
| **minimum** | **95.1** |

  Other distances from the stud parts (MODELLED): to the J28/J29 plug envelopes ≥ 140 mm. Fans 32.85, filter covers 36.5, window covers 12.5 (TOP cover), clamps 48.0, key caps / light pipe 5.55, PCB 3.93 (strap, at the board edge gap), customer panel 4.01 (ring envelope above the panel rear).

## Backup: clamp-screw bond (Phase 19, 928bbe8, unchanged)
- TOP clamps x 72.9 and 203.5. A2 cup-point M4 screw biting the panel, then the M4 insert, bridge strip, M3 insert, M3 through-boss screw, internal strap, and finally a bare bezel landing at (92.9 / 223.5, -19.8). Details are in README Phase 19.
- **Installer note:** Mount to a bare-metal panel contact or scrape paint under the clamp tips; check continuity from bezel to panel with a meter (under 1 ohm).

## Removed (Phase 19, kept removed)
PE_NEW boss, rear PE window and its cover, grommet and gasket, PE wire spec, M1-M5 masks, bond-test procedure. H1-H3 CHASSIS bosses are unchanged; H4 is a plain hole.
