# Board-change requests from enclosure v3 (for Enginerd; NOT acted on, no KiCad file edited)
Board: genctl_v4_handrouted.kicad_pcb @ f03c57a (M6). Labels: MEASURED = read from board/datasheet; INFERRED = assumption.

| # | Request | Why | Data |
|---|---|---|---|
| BCR-1 | **SOLVED IN SHELL (phase 2) - no board change requested.** Rear shell now has sealed PA12 port tunnels (2 mm walls) from the rear face down to 0.5 mm above each jack, with a 1.5 mm lead-in step: J10 RJ45 tunnel 20 x 24 inner (mouth 13.5 mm deep), J11 USB-C tunnel 16 x 10 inner (mouth 20.4 mm deep). Plug envelopes (RJ45 11.68 x 8.0; USB-C overmold 13.0 x 7.4) check 0 mm3 interference. Fallback only if field tests fail (short-overmold USB-C cables, RJ45 latch access): port daughterboard 30 x 20 mm on 2 x M2.5 stand-offs, J10+J11 mouths flush with rear face Z=48. | Ethan: ports face out the back | J10/J11 positions MEASURED; heights 16.9/10.0 INFERRED |
| BCR-2 | Heat-bar keep-out on B: in x 205-256, y 3-39 (over CM5) and the STRAP_CORRIDOR x 247.5-279.5 (to board edge), no B part taller than **5.9 mm** (heat bar underside Z 23.54, PCB rear Z 17.6). Please add a height-limited rule area or confirm. SW3 (250.6, 40.7) and SW4 (185.7, 8.4) are adjacent; check their height. | CM5 -> bezel heat path | CM5 4.94 mounted (MEASURED cm5 datasheet); 1 mm pad INFERRED |
| BCR-3 | J4 fan header (270.34, 14.23, B): mark DNP or delete. | Ethan: no fan | MEASURED position |
| BCR-4 | CLOSED phase 3: geometry.py BTN_X changed to board values (table below shows the old delta). | consistency | MEASURED |
| BCR-5 | Provide/attach 3D models (or datasheet heights) for J10 HR963380AE, J11, J14/J15 FPC, Phoenix PC5/4, CM5 module. Several footprints have no 3D model; enclosure heights are INFERRED. | clearance checks are only as good as these | MEASURED: models list empty for J10, J11, J14, J1/J23/J28/J29 |
| BCR-6 | Display rear to PCB F-face air gap (flush glass, phase 9 CAD) is **11.44 mm** under the TFT area incl. the HV zone and **7.27 mm** under the source band (x 20.6-255.6, y 149.9-179.5) (PCB F at Z 16.0 INFERRED, display 12.68 MEASURED). 3.27 mm was the pre-flush value. F-side parts under the source band must be <= 6.5 mm tall (INFERRED 0.75 mm margin) and HV parts must stay on B (already a rule). | creepage/clearance and mechanical | |
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


## BCR-8 UPDATE (phase 5): ALS moved to the SW11/SW12 gap. Supersedes (11.0, -9.25).
- **Frames:** the KiCad board frame and the cover-glass frame are identical; the offset is 0.
  - Evidence (read-only pcbnew, genctl_v4_handrouted.kicad_pcb @ f03c57a): SW9 at KiCad (29.38, -9.25) = cover-glass (29.38, -9.25); H1 at (2.0, -9.25); aux and grid origins (0, 0); Edge.Cuts bbox (-3.745, -15.295)-(280.305, 194.755), including line width.
  - Formula: x_kicad = x_glass, y_kicad = y_glass.
  - The Firmware Engineer's 138.2 is valid in both frames.
- **OPT3001 centre: (138.18, -9.25) in both frames**, on the PCB **F side** (facing the display and front). This is the exact midpoint of SW11 (116.42) and SW12 (159.94).
- **Keep-out:** 4 mm radius on F; nothing taller than the 0.65 mm OPT3001 within 3 mm.
- **Neighbours within 8 mm:** J26 (KF2EDGRM 6P THT, B side). Its pads 3 and 4 are at (135.36, -3.76) and (140.44, -3.76), Ø2.5, about 5.5 mm from the sensor in y. B-side tracks BL4_B pass at y about -5.1 to -5.4. No F-side parts.
- **Old position (11.0, -9.25), for comparison:** D5 (D_SMB, B side) sits directly under it, and 4 GND vias at (10.55/11.45, -10.91/-11.93) are about 0.7 mm from the sensor body edge.
- **Why the gap is better:** 7.76 mm from the pipe to each cap edge (was 4.38 mm), solid aluminium on both sides, no parts on either side directly under it, and it is the Firmware Engineer's proposal.
- **Against it:** a hand pressing SW11/SW12 shadows the sensor briefly. Firmware should median-filter over about 2 s.
- Glass-edge backlight spill (9.25 mm) and exposure to sun are the same at both positions.


| BCR-10 | **REQUEST (rev phase 10, reconciled with firmware/ARCHITECTURE.md section 11; Ethan GO on V6 + TWO fans, reverses BCR-3).** Fan: Orion OD4010-05HB10A, 5 V, 4-wire, 0.10 A run / 0.30 A start each, tach open-collector 2 pulses/rev, PWM 1-100 kHz with internal pull-up (open = full speed) (MEASURED Mouser DS). (1) **Headers:** keep and populate **J4** (JST SM04B-SRSS-TB, (270.34, 14.23), B) = FAN1 exhaust: 1 GND, 2 +5V_FAN, 3 FAN_TACH, 4 FAN1_PWM_OD. Add **J4B** (same SM04B, same pinout, B side next to J4, Layout to place) = FAN2 intake: 1 GND, 2 +5V_FAN, 3 FAN2_TACH, 4 FAN2_PWM_OD. (2) **PWM (shared):** CM5 **Fan_PWM (U9.19)** drives both fans through an open-drain buffer (74LVC1G07, or one 2N7002 per fan), so the fans' internal 5 V pull-ups never back-drive the CM5 pin. (3) **FAN_FORCE_FULL:** TCA9555 **U76 (@0x25) P17** drives the buffer OE/gate and forces the PWM outputs Hi-Z (fans run 100 % on their own pull-ups). Add a 100k pull to the force-full state, so the fans run 100 % at power-up and whenever the MCU/CM5 is not commanding. (4) **FAN1 tach:** J4.3 FAN_TACH to CM5 **Fan_Tacho (U9.16)** with 10k pull-up to CM5_3V3, 1k series and a BAT54S clamp to 3.3 V/GND. (5) **FAN2 tach:** J4B.3 FAN2_TACH to **U76 P16** (TCA9555 input, 6 V abs-max) with 10k pull-up to +3V3_SAFE. The MCU counts edges on I2C_INT_N; there is NO free STM32 timer pin, so no timer capture. This is good for stall/low-RPM detection, not precise RPM. (6) **Fan power:** **U76 P15** FAN_PWR_EN drives one high-side load switch feeding +5V_FAN to both headers (e.g. TPS2553DBVR, already on BOM, ILIM ~0.8 A for the 0.6 A two-fan start), 100k pull-up so it is ON by default. The MCU can power-cycle a jammed fan. The current limit isolates a shorted fan from +5V. (7) **Fault detect:** per-fan STALL/LOW/FILTER from the two independent tachs (firmware 11.3). The load-switch FAULT_N has no free I/O (U76 P15-P17 used), so leave it unconnected or wire it to a test point. (8) **Temperature sensors:** 3x TMP1075 (I2C, firmware refs U81/U82/U83, not yet on the board): U81 at CM5 / heat strap, U82 at the TPS61500 (U24) backlight boost, U83 cabinet ambient (near the intake fan / rear wall). (9) **+5V budget:** two fans 0.20 A run / 0.60 A start. +5V is a TPS56637 (FB 75k/10k = 5.1 V). The 6 A figure is the part's catalogue rating, but firmware notes it is quoted for the +3V3 instance, so the +5V rating and load (CM5 up to 5 A, USB, key LEDs) are **being checked by Layout/Firmware**. | V6 + dual-fan option, firmware section 11 | J4 pins / CM5 U9 pins MEASURED from netlist; U81-U83, J4B and new nets PROPOSED |

## BCR-11: **WITHDRAWN** (Phase 19, Ethan's decision: no PE wire or boss; the bezel bonds to the panel through the top clamps, with no board change). Layout: do NOT add the hole; D5, the vias and the fills stay as they are. Original text kept below for history.
| BCR-11 (WITHDRAWN) | ~~Add an NPTH Ø9.5 clearance hole near (16, 3) for a bezel PE boss; keep copper at least 5.5 mm from hot copper.** Validated position: **(12.3, -7.5)** (board/enclosure coordinates, same frame as H1 (2.0, -9.25)). (16, 3) itself is behind the display glass (no bezel metal), so the hole moves to the nearest valid spot in the key band between H1 and SW9. At (12.3, -7.5), to the hole edge: board top edge 3.02 mm, H1 CHASSIS pad **1.20 mm** (web, Compliance phase 15 MEASURED; fab ≥ 1.0 mm), R490-R492 pads ≥ 2.2 mm, nearest hot copper **19.0 mm from the hole centre** (GND_AC / +3V3_AC zones, 14.25 mm from the edge; R438.1 17.57 mm from the edge) (≥ 5.5 / 6.6; Compliance phase 15 MEASURED). Board file d151ff7 does not yet contain BCR-11; re-run Compliance pe15.py on the revised board. Needed for it: **move D5 (SMBJ5.0A, +5V TVS, B side, now at (11.0, -9.27), directly under the hole)**, move the 4 GND stitching vias at (10.55/11.45, -10.91/-11.93) and reroute the GND F.Cu tracks crossing the hole; inner GND1/GND2/PWR fills to clear the hole (≥ 0.5 mm, ASSUMED fab). Add a B-side keep-out Ø14 round the hole for the ring lug + star washer (Z ≤ 2.4 mm above the B face; no parts) and a 5 x 10 mm keep-out from the hole toward the top edge (lug tongue, -y). No copper, no net, no plating: the PE current must not pass any PCB pad (H1-H3 stay CHASSIS-to-bezel only). H4 (272.0, 185.5) remains a plain NPTH; its PE_BOSS_RING rule area can be released. | Compliance hv_rulings_phase13 §3 ("near" J28/J29), PE_BOND.md phase 14 | MEASURED (board read-only) + MODELLED (CAD) |
