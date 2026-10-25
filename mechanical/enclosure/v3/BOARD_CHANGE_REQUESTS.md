# Board-change requests from enclosure v3 (for Enginerd; NOT acted on, no KiCad file edited)
Board: genctl_v4_handrouted.kicad_pcb @ f03c57a (M6). Labels: MEASURED = read from board/datasheet; INFERRED = assumption.

| # | Request | Why | Data |
|---|---|---|---|
| BCR-1 | **SOLVED IN SHELL (phase 2) - no board change requested.** Rear shell now has sealed PA12 port tunnels (2 mm walls) from the rear face down to 0.5 mm above each jack, with a 1.5 mm lead-in step: J10 RJ45 tunnel 20 x 24 inner (mouth 13.5 mm deep), J11 USB-C tunnel 16 x 10 inner (mouth 20.4 mm deep). Plug envelopes (RJ45 11.68 x 8.0; USB-C overmold 13.0 x 7.4) check 0 mm3 interference. Fallback only if field tests fail (short-overmold USB-C cables, RJ45 latch access): port daughterboard 30 x 20 mm on 2 x M2.5 stand-offs, J10+J11 mouths flush with rear face Z=48. | Ethan: ports face out the back | J10/J11 positions MEASURED; heights 16.9/10.0 INFERRED |
| BCR-2 | Heat-bar keep-out on B: in x 205-256, y 3-39 (over CM5) and the STRAP_CORRIDOR x 247.5-279.5 (to board edge), no B part taller than **5.9 mm** (heat bar underside Z 23.54, PCB rear Z 17.6). Please add a height-limited rule area or confirm. SW3 (250.6, 40.7) and SW4 (185.7, 8.4) are adjacent; check their height. | CM5 -> bezel heat path | CM5 4.94 mounted (MEASURED cm5 datasheet); 1 mm pad INFERRED |
| BCR-3 | J4 fan header (270.34, 14.23, B): mark DNP or delete. | Ethan: no fan | MEASURED position |
| BCR-4 | CLOSED phase 3: geometry.py BTN_X changed to board values (table below shows the old delta). | consistency | MEASURED |
| BCR-5 | Provide/attach 3D models (or datasheet heights) for J10 HR963380AE, J11, J14/J15 FPC, Phoenix PC5/4, CM5 module. Several footprints have no 3D model; enclosure heights are INFERRED. | clearance checks are only as good as these | MEASURED: models list empty for J10, J11, J14, J1/J23/J28/J29 |
| BCR-6 | Display rear to PCB F-face air gap is **3.27 mm** in the model (PCB F at Z 16.0 INFERRED, display 12.68 MEASURED, glass flush). PROGRESS.md says "about 3.5 mm". F-side parts under the display must be <= 2.5 mm tall (INFERRED 0.75 mm margin) and HV parts must stay on B (already a rule). | creepage/clearance and mechanical | |
| BCR-7 | Keep outline 284 x 210, H1-H3/H4 and the 4 shell-post keep-outs frozen; the enclosure is built on them. Notify mechanical if anything moves. | | MEASURED |
No conflict found for: 24 mm caps at 43.52 pitch with one 228E per key (19.5 mm bezel web between pockets); connectors all on B; terminal rows reachable through rear windows.


## BCR-4 detail: switch centres, board vs geometry.py
Frame (both): mm, origin = cover-glass top-left corner, front view, +x right, +y down. Board coords from `mechanical/pcb_v4/genctl_v4_handrouted.kicad_pcb` @ commit f03c57a (pcbnew LoadBoard, read-only, MEASURED). Design coords from `mechanical/geometry.py` @ 422b756 (BTN_X, BTN_Y_TOP, BTN_Y_BOT).

| SW | board x,y | geometry.py x,y | dx | dy |
|---|---|---|---|---|
| SW9 | 29.38, -9.25 | 29.08, -9.25 | +0.30 | 0.00 |
| SW10 | 72.90, -9.25 | 72.60, -9.25 | +0.30 | 0.00 |
| SW11 | 116.42, -9.25 | 116.12, -9.25 | +0.30 | 0.00 |
| SW12 | 159.94, -9.25 | 159.64, -9.25 | +0.30 | 0.00 |
| SW13 | 203.46, -9.25 | 203.16, -9.25 | +0.30 | 0.00 |
| SW14 | 246.98, -9.25 | 246.68, -9.25 | +0.30 | 0.00 |
| SW15 | 29.38, 188.71 | 29.08, 188.71 | +0.30 | 0.00 |
| SW16 | 72.90, 188.71 | 72.60, 188.71 | +0.30 | 0.00 |
| SW17 | 116.42, 188.71 | 116.12, 188.71 | +0.30 | 0.00 |
| SW18 | 159.94, 188.71 | 159.64, 188.71 | +0.30 | 0.00 |
| SW19 | 203.46, 188.71 | 203.16, 188.71 | +0.30 | 0.00 |
| SW20 | 246.98, 188.71 | 246.68, 188.71 | +0.30 | 0.00 |


## BCR-8 (REQUEST ONLY, phase 4): ambient light sensor (ALS) position
- **Window centre (cover-glass frame: mm, origin at the glass top-left, front view, x right, y down): x = 11.0, y = -9.25.** It sits in the bezel key band left of SW9. The board uses the same frame, so the **sensor centre on the PCB is (11.0, -9.25), on the F side** (the side facing the display and front).
- Free space (MEASURED board_interface.json from genctl_v4_handrouted.kicad_pcb @ f03c57a): H1 pad bbox ends at x 6.58 and SW9 starts at x 23.18 on F. The nearest B-side THT is J24 at x ≥ 30.24. Keep-out request: 4 mm radius on F, sensor package ≤ 0.7 mm tall above the F face.
- Clearances (model, checks.json):
  - 4.38 mm from the light pipe to the SW9 cap edge, with a solid aluminium bore wall between them blocking key LED glow.
  - 9.25 mm to the glass top edge; 17.7 mm to the active-area corner.
  - Light pipe rear face 1.0 mm above the PCB F face (0.3 mm above a 0.7 mm-tall sensor).
- Window: Ø4.2 bore through the bezel and the PA12 ring, plus a Ø5 hole in the key membrane. Light pipe: Ø4.0 x 19 mm cast PMMA (or PC), turned or cut from rod, front face bead-blasted as a diffuser, flush with the ring face.
- Rain seal: 0.1 mm interference fit plus a neutral-cure silicone or UV-acrylic bead on the inside of the bore. Field of view about ±60 deg with a cosine-like response from the frosted face (ESTIMATED).
- Coupling loss over the 19 mm pipe plus diffuser: 40-70 % (ESTIMATED). Calibrate a gain in firmware.
- Sensor class (SUGGESTION only): digital I2C ALS with a photopic response. OPT3001 (2 x 2 mm USON, small aperture, suits a light pipe) or VEML7700.
- Alternative position if the left is unwanted: x 261.5, y -9.25 (between SW14 at 252.58 and H2 at 269.99). It is near the warm CM5/heat-boss corner, which matters little for an ALS. Not modelled.

## BCR-9 (REQUEST ONLY, optional, phase 4): display-rear heat spreader strap (option E)
Option E would cool the glass a further 1-2.5 K. It needs two PCB slots (about 20 x 3 mm) near the left and right board edges, clear of copper, so a 1.5 mm aluminium strap can run from a display-rear spreader to the fin plate. F-side part heights under the display must leave ≥ 1.8 mm, which is UNVERIFIED. Low value for the cost; listed for completeness.
