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
