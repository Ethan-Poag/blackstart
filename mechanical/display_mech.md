# Riverdi RVT121HVLNWCA0-B — mechanical summary (for Blackstart front panel / PCB)

Sources (already in `/workspace/genctl/datasheets/`, not re-downloaded):
`DR_RVT121HVLNWCA0-B_Rev.1.1.pdf` (mechanical drawing, 2025-02-03), `DS_RVT121HVLNWCA0-B_Rev.1.1.pdf`
(datasheet), `AN_RVT121HVLNWCA0-B_Rev1.0.pdf`, `3D_RVT121HVLNWCA0-B_Rev.1.0.stp`.
Render of the drawing at 300 dpi: `layout_prep/riverdi_drawing_300dpi.png`.
The -B part has **no mounting metal frame** (DS §ordering: "FRAME N – Without Mounting Metal Frame").

Coordinates below: mm, front view, origin = top-left of cover glass, y down (same as `geometry.py` and KiCad).

| Item | Value | Note |
|---|---|---|
| Cover glass / TFT outline (W x H) | **276.56 x 179.46** | tol ±0.3 (general) |
| Touch sensor outline | 275.56 x 178.46 | inset 0.50 |
| Module depth | **12.68 max** (incl. TFT source-PCB band + cable) | CTP+TFT = 8.51 ±0.5; CG 1.8; TFT 5.56 |
| TFT active area | **261.12 x 163.20** | 1280x800 @ 0.204 mm |
| CG viewing area (unprinted) | 261.92 x 163.30 | |
| Sensor active area | 262.52 x 164.60 | |
| AA border: top / bottom / left / right | **8.03 / 8.23 / 7.32 / 8.12** | top & right given; left = 276.56-261.12-8.12; bottom = 179.46-163.2-8.03. AA centre at (137.88, 89.63) — matches drawing |
| VA border: top / right | 7.63 / 7.72 | black mask RAL9005 outside VA |
| Corner radius (glass) | 4x R0.50 | |
| Mounting | none on module (no frame). Mount by bonding the 7-8 mm black-mask border (VHB/OCA tape) to the panel, or clamp the glass edge | |

## Rear features (drawing shows REAR view; mirrored here into front-view x)
| Feature | Front-view location | Drawing value |
|---|---|---|
| TFT source-PCB band (thickest part) | x 20.6 … 255.6, y 149.9 … 179.46 (bottom 29.5 mm, 235 mm wide) | 235.00 ±1, 20.95 ±1 from edge, 29.52 ±1 |
| **LVDS ZIF 40p 0.5 mm**, down-side contact, flip lock, on the band | pin-1 ref ≈ (118.4, 164.9) | 118.38 ±0.5 from edge, 14.57 ±0.5 from bottom. Needs a 40p 0.5 mm FFC jumper to our J14 |
| **Backlight cable** BHSR-02VS-1 (mates SM02B-BHSS) | exits at top-left corner (front view), 200 ±5 mm long | LEDA 23-26.5 V, ~360 mA (48 LEDs) |
| **Touch FPC tail** (ILI2511 controller on stiffened tail; CN1 SM04B USB, CN2 SM06B I2C, plus 10p 0.5 mm FPC contact end) | exits bottom edge, ≈ x 217 … 245, extends ≈ 37 mm below glass, then folds back | 59.53 / 32.03 ±1, 37.00; 72.24/84.54 ±1 are tail lengths whose datum I could not read unambiguously — **verify against the STEP** |
| Cable vs TFT clearance | max 4.0 | |

Unverified / to check in STEP: exact touch-tail x position and fold length; whether 12.68 is reached only at the band (assumed) or across the back.

## Buttons (CTS 228EMV…RGB…, SMD gull-wing, vertical)
Body 6.8 (x) x 7.2 (y), **height 5.5 mm**, travel 0.7, land pattern 11.2 mm wide (from `cts228e.pdf` p3; our footprint `genctl:CTS_228E_RGB` matches 11.2 x 6).

Proposed layout (`geometry.py`, drawing `front_panel.png/.svg`):
- 6 above + 6 below, **pitch 43.52 mm = AA width / 6** → each key centred under one sixth of the screen so on-screen soft-key labels line up.
- Button x centres: 29.38, 72.90, 116.42, 159.94, 203.46, 246.98 (BCR-4 2026-10-25: AA sixths + 0.30 mm, locked to board f03c57a).
- Rows at y = −4.40 (top) and 183.86 (bottom): body 0.8 mm from glass edge → **centre 12.43 mm above the AA top edge and 12.63 mm below the AA bottom edge**.
- Front panel outline **292.56 x 201.46 mm** (≈293 x 202), border 8.0 L/R and 11.0 T/B, R3 corners. 11 mm T/B is the minimum that holds a 7.2 mm key + 0.8 mm glass gap + ~3 mm to edge; L/R could go to 5 mm if the enclosure allows.
- **PCB outline 284.0 x 198.0 mm**, centred on the glass: x −3.72 … 280.28, y −9.27 … 188.73. Board sits behind the display and spans the button rows; M3 standoffs H1-H4 at (3.5, −4.4), (273.06, −4.4), (3.5, 183.86), (273.06, 183.86) — in the button rows, outside the glass footprint. Recommend adding 2-4 more holes mid-board (e.g. through the board behind the display) to stop flex on a 284 mm board.

## Height-stack issue (needs a decision)
Buttons are 5.5 mm tall, but if the PCB sits behind the display the PCB front face is ≈ panel thickness + 0.5 (tape) + 12.68 (module) + ~1 (gap) ≈ **16-17 mm behind the panel front** (3 mm panel). The key tops would be ~11 mm short. Options:
1. Keep keys on the main board, use ~11 mm plunger/light-pipe actuators in the panel (common, cheapest; RGB light must pass through — use clear/diffuse plungers).
2. Move the 12 keys + LED resistors to two thin strip boards (≈ 284 x 12 mm) mounted to the panel, connected by FFC/board-to-board. Board outline then shrinks to ~ display size (≈ 278 x 181).
3. Put the display in a pocket so the board can move forward only in the strip areas — not possible on a flat PCB.
Option 1 keeps the current schematic; option 2 changes it (other executor's area).
