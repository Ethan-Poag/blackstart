# J30 replacement: Phoenix PC 5/8-GF-7,62 (1720851) + SPC 5/8-STF-7,62 (1996184). Data for the CAD update
Ethan approved (phase 16). Layout is relocating J30 or splitting it into 2 × 4-pin; **no footprint yet; the CAD J30 model is unchanged**.
All values are VERIFIED from the Phoenix product pages, fetched 2026-10-25 (manufacturer, MEASURED by the vendor) unless marked otherwise. The PDF drawing and 3D model were not downloaded (STEP/DXF need a page download, not tried).

## Plug SPC 5/8-STF-7,62, 1996184: https://www.phoenixcontact.com/en-us/products/pcb-plug-spc-5-8-stf-762-1996184
- 8 pos, pitch 7.62 mm. **Push-in spring** connection (not screw), with a screw-locking flange (flange torque 0.3–0.7 N·m). Conductor entry at 0°, parallel to the PCB / mating axis.
- Dimensions: **width 76.18 mm, height 19.8 mm, length 38.5 mm** (the axis mapping of w/h/l to our board axes needs the drawing: UNVERIFIED).
- Electrical: nominal 32 A, 1000 V; rated III/3 and III/2 1000 V / 8 kV; II/2 1000 V / 6 kV. **cULus 600 V / 35 A, AWG 24–8** (E60425).
- Wire: **rigid 0.2–10 mm²; flexible 0.2–6 mm²**; ferrule without sleeve 0.25–6, with sleeve 0.25–4 mm²; AWG 24–8; strip 15 mm; gauge 4.3 × 4.0 mm.
- Housing: PA, group I, CTI 600, UL94 V0, GWFI 850 °C.
- Clearance/creepage stated (IEC 60664-1): III/3 8 mm / 12.5 mm; III/2 8 / 8 mm.
- Note: "must not be plugged in or disconnected when carrying voltage or under load" (IEC 61984, no switching capacity).
- **Finger-safe / IP20: NO statement found on the product page** ⇒ UNVERIFIED. Must come from the datasheet PDF or a Phoenix statement, or from a probe-B test.

## Header PC 5/8-GF-7,62, 1720851: https://www.phoenixcontact.com/en-us/products/pcb-header-pc-5-8-gf-762-1720851
- 8 pos, pitch 7.62 mm, threaded flange (plug screw-lock), wave solder, **3 solder pins per potential**, pin 0.8 × 1 mm, length 5 mm, **hole Ø1.3 mm**.
- Dimensions: **width 77.06 mm, height 19.29 mm, length 29.25 mm, installed height 14.29 mm**.
- PCB attachment screw: DFK-PC 16-SS (1705449), 0.3 N·m.
- Electrical: nominal 32 A, **630 V**; rated III/3 and III/2 630 V / 6 kV; II/2 1000 V. UL (E60425), as listed: 300 V / 41 A (B), 150 V / 41 A (C), 600 V / 5 A (D), 600 V / 41 A (F); the use-group meaning is not explained on the page.
- Housing PA, CTI 600, UL94 V0. Clearance/creepage stated: III/3 5.5 / 8 mm; III/2 5.5 / 5.5 mm.

## Mated stack (INFERRED, needs the drawing)
- Mated height above the PCB is about installed header 14.29 mm + plug overhang; the plug's 19.8 mm "height" may be along another axis. **Do not model until the drawing is read.** Current CAD plug tops are at ZR + 18 = 35.6 vs clamps at Z 37.5. If the mated height is > 19.9 mm, the clamp Z or plug orientation must change.
- ~77 mm long (8 pos) vs the current J30 envelope: the J28–J30 window y 9–164 and the clamp at y 118 / 178 must be re-checked; a 2 × 4-pin split (PC 5/4-GF, same as J28/J29) is ≈ 38 mm each.

## Redo list when the footprint arrives
First download the Phoenix drawing / 3D model for 1996184 and 1720851, so the mated height is verified, not inferred.
CAD J30 model (Phoenix 3D/drawing) → J28–J30 window/slot/cover and wrap-lip segment positions → clamp clearances y 118 / y 178 → creepage and J30 surface path (26.69 mm now) → finger_check → checks.json, STEP, PNGs.
