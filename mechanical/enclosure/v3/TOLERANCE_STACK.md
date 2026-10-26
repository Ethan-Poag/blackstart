# Tolerance stack v3 (mm). WC = worst case (linear sum), RSS = root-sum-square.
Process tolerances: CNC 6061 bezel +-0.05 (INFERRED, typical ISO 2768-m on features <300 is +-0.2 on size; pockets/window specified +-0.05 as toleranced features); laser-cut Al (alt bezel) +-0.13 (MEASURED SendCutSend ".005 in" 6061 page); SLS/MJF PA12 +-0.3 within 100 mm, +-0.4 % above (MEASURED JLC3DP PA12-HP page); SLA 8001 +-0.2 or 0.3 % (MEASURED JLC3DP 8001 page); glass +-0.3 (MEASURED Riverdi DR general tol); module CTP+TFT 8.51 +-0.5 (MEASURED).

## 1. Glass in bezel window (per axis, total gap)
Nominal: window 277.56 - glass 276.56 = 1.00 (0.50/side).
| contributor | +- |
|---|---|
| glass outline | 0.30 |
| window CNC | 0.05 |
| WC total gap | 1.00 +- 0.35 -> 0.65..1.35 (fit always OK) ; RSS +-0.30 |
Laser-cut alt: +-0.43 WC -> 0.57..1.43 OK. Glass is centred by 3-4 VHB spacers/fixture; per-side gap 0.3..0.7 if centred.
Flush (Z): set by fixture (face-down on a plate), bond line 1.0 nominal absorbs CTP+TFT +-0.5 -> 0.5..1.5 bond line (OK for neutral-cure silicone). Glass target 0 / -0.15 under face.

## 2. Cap in pocket (per axis, total clearance)
Nominal: pocket 24.20 - cap 24.00 = 0.20.
| contributor | +- |
|---|---|
| cap SLA (24 mm -> max(0.2, 0.072)) | 0.20 |
| pocket CNC | 0.05 |
| WC | 0.20 +- 0.25 -> **-0.05..0.45 -> interference possible** ; RSS +-0.21 -> -0.01..0.41 |
Action: print caps +0.1 oversize, sand/fit to pocket (or cut pockets last, matched). Max clearance 0.45 -> rest tilt atan(0.45/8) = 3.2 deg; drawer rule still met (e < 13.3 mm). Laser-cut pocket: +-0.33 WC -> must fit caps per unit.

## 3. Port cutouts vs connectors (rear wall, x/y position of J10/J11 vs its window)
Chain: PCB located by H1-H3 M4 screws in 4.3 holes into bezel bosses (+-0.15 float); bezel boss position +-0.05; bezel taps to shell flange via 8 x M4 in 4.5 clearance holes (+-0.25); shell window position relative to its flange holes, ~150 mm span: 0.4 % = +-0.60; footprint placement +-0.10 (INFERRED).
WC = 0.15+0.05+0.25+0.60+0.10 = **+-1.15**, RSS = **+-0.68**.
Margins: J10 window 20 x 24 vs RJ45 plug ~11.7 x 13.5 + latch finger (INFERRED) -> 4.1 / 5.2 per side, OK. J11 window 13 x 8 vs USB-C overmold ~12.4 x 6.5 (INFERRED typical) -> 0.3 / 0.75 per side -> **WC fails, RSS fails on x** -> widen J11 window to 15 x 10 (or adopt BCR-1 daughterboard). Depth of wells is the bigger issue (BCR-1).

### 3a. Port tunnels (phase 2)
Tunnel position vs jack (WC 1.15 mm, from above). USB-C tunnel 16 x 10 vs overmold 13.0 x 7.4 (largest measured, EE.SE 475901; USB Type-C R2.2 ECN max 12.85 x 7.0): 1.5 / 1.3 mm per side > 1.15 WC -> passes. RJ45 tunnel 20 x 24 vs plug 11.68 x 8.0: 4.16 / 8.0 per side, extra height is the latch/boot finger notch. Overmold off-centre on cheap cables: not covered (INFERRED risk).

## 4. Shell through customer cutout
Cutout 296 x 228 (+1.0/-0, INFERRED customer spec). Shell 294 x 226 nominal, SLS +-0.4 % = +-1.18 / +-0.90.
WC min gap per side = (296 - 294 - 1.18)/2 = **0.41** (x), (228 - 226 - 0.90)/2 = 0.55 (y) -> always passes. Max gap (cutout +1, shell -tol) = (297 - 292.8)/2 = 2.1 per side; bezel overlap on panel face = (329 - 297)/2 = 16 per side; gasket land 8 -> covered.

## 5. Clamp range
Panel face Z = rim 9.5 + gasket 2.0 x 0.7 = 10.9 (gasket 1.4..1.6 for 25-35 % compression, INFERRED target). Clamp block front face Z 37.5 fixed; M4 nylon-tip screw through a heat-set insert.
Panel t range **1.0 .. 6.0 mm (INFERRED design parameter)**: screw tip must reach Z 11.9..16.9 -> screw protrusion in front of block 20.6..25.6 -> **M4 x 35** (block 7.5 + insert) gives 27 mm usable, OK. Bezel rim flatness / panel bow: gasket compression range 0.6 mm (30 % of 2.0) covers +-0.3 panel waviness (INFERRED). Clamp checked in code at t = 1 and 6: no shell or clamp interference (checks.json).


## 6. Flush glass (phase 6): glass front vs ring face, target ±0.15 mm
The chain if each part is built to nominal and stacked: ring thickness ±0.2 (MJF/SLS local, ESTIMATED), pip/air gap ±0.1, bezel ledge Z ±0.05 (CNC), VHB foam tape 0.9 ±0.1, module CTP+TFT 8.51 ±0.2 (INFERRED, no tolerance in the datasheet).
- WC ±0.65, RSS ±0.33 mm. **This fails ±0.15.**
- **Process to meet ±0.15:** assemble face-down on a flat plate (±0.05) so the glass and the ring face share the datum. Bond the module to the ledge with foam tape that takes up the gap, then screw the ring down onto the bezel.
- What remains: ring face flatness and local thickness at the glass edge. MJF gives about ±0.2, which still fails. An SLA ring (±0.1) or a CNC face-skim of the MJF ring meets ±0.15 by RSS (0.05 fixture + 0.1 ring = ±0.11).
- Cost: SLA ring about +$40 / +$20 (ESTIMATED).

Where the display touches: the TFT rear rests at Z 4.56 on a 4 mm metal ledge lip (Z 5.5 seat, 0.94 mm foam tape). The glass edge touches only the silicone bead and PA12 sleeve, never metal. The module's 12.68 mm depth now ends at Z 8.73. The display-to-PCB air gap is 11.44 mm under the TFT area (including the whole HV zone x < 75) and 7.27 mm minimum only under the source band (x 20.6-255.6, y 149.9-179.5); phase 9 CAD, checks.json. The old 3.27 mm figure (recessed glass) is obsolete.

## 7. Phase 9 stack (V6 + dual fans)
Z behind bezel face: shell rear 48.0 | plate 48.0-52.75 | strip pad 0.5 | EXL1 base 2.0 + fins 8.0 (ASSUMED) -> 63.25 | fan gasket 1.0 + fan 10.5 + filter cover 4.0 -> 68.25. Ring face at -4.0, so overall depth 72.25 mm (strip-only 67.25). Display-to-PCB gap: 11.44 mm (TFT/HV area), 7.27 mm (source band). HV: J28/J29 lead tips clipped to <= 1.0 mm -> 8.0 mm to the trimmed bezel rim (7.0 at 2 mm); 10.44 to display rear. Phase 12 left clamps at y 5/116/178: J28/J29 plug envelope to insert 12.03 mm, screw 12.68 mm; J30 11.29 mm. Note 8.0 at 1.0 mm leads has no margin vs Z_PCB tolerance (Compliance).
