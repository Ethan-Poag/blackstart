# PE_BOND: bezel-to-PE bond (phase 14: moved to a new bezel boss next to J28/J29). Ethan confirmed Oct 25: bezel is grounded (bonded to PE).
Nothing here is certified; Compliance / NRTL to review.

## Where (phase 14)
- **New bezel PE boss `PE_NEW` at (12.3, -7.5)** (6061, part of the CNC bezel): bare Ø8.0, from the field Z 0.5 up through a new PCB NPTH Ø9.5 (BCR-11, not on the board yet) to its end face at **Z 18.6** (PCB rear 17.6 + 1.0). M4 tap Ø3.3, Z 3.0-19. The boss merges into the key band / H1 boss metal of the bezel.
- **Why not (16, 3):** it lies inside the display glass outline (glass x 0-277.56, y 0-180.46, MEASURED CAD). The bezel has its window and the display there, so a front boss would pass through the glass. On the board, (16, 3) is inside rule area BARRIER_top (x -3.7..73, y -1.2..11, keep-out), which would have been fine electrically. Nearest valid bezel metal is above the glass in the key band, between the H1 boss and the SW9 key opening.
- **Distances (MODELLED, pad centres):** PE_NEW to the nearest J28/J29 pad **31.0 mm**, farthest **103.9 mm** (old H4: 276.8 / 313.0).
- **H4** (272.0, 185.5) stays a plain NPTH Ø9.5 clearance hole: **no PE function, H4 bezel boss deleted in CAD**. The board rule area PE_BOSS_RING around H4 can be released by Layout (optional).
- **H1/H2/H3** (M4 bezel bosses at (2.0, -9.25), (274.56, -9.25), (2.0, 188.71)) carry the board net **CHASSIS** on Ø9 plated pads (functional earth via R33 1M // C48 4.7n, MEASURED). They are **not** part of the PE path: the PE conductor lands on the PE_NEW boss face only, on bare Al, and touches no PCB pad (hole is NPTH, no copper; lug sits 1.0 mm above the board rear on the boss).

## What is around PE_NEW (MEASURED, genctl_v4_handrouted.kicad_pcb read-only; distances to the Ø9.5 hole edge)
- Board top edge web: 3.02 mm. H1 CHASSIS pad: 1.05 mm (FR4 web; same potential as the bezel, OK electrically, thin mechanically).
- **Conflicts that need Layout (BCR-11):** D5 SMBJ5.0A (+5V TVS, B side, body (8.7, -12.9)-(13.3, -5.6)) sits under the hole; 4 GND stitching vias at (10.55/11.45, -10.91/-11.93) and GND F.Cu tracks cross the hole; inner fills GND1/GND2 (GND) and PWR (+3V3_SAFE) cover it (they will clear automatically around an NPTH).
- Nearby SELV parts: R492 1.9 mm (body), R490/R491/R492 pads 2.2-4.0 mm (SW9 backlight nets), SW9 body 9.7 mm (CAD switch).
- **Hot copper:** none nearby. Nearest 600 V divider parts (R437-R439, B side, y ≥ 13.6) are about 17 mm from the hole edge (MEASURED bbox), ≥ 5.5 clearance / 6.6 creepage (basic, earthed).
- CAD (checks.json): boss to display 3.5 mm, to front-ring sleeve 1.5, to key caps 1.08, to switches 9.68, to the ALS light pipe 119.9, to clamps 22.8; boss to J28/J29 plug envelope 14.5 and PE hardware to it 14.0 (≥ 5.5 basic); 0 interferences (key membrane notched Ø9 round the boss).

## Stack at PE_NEW (CAD part `pe_bond`, step/pe_bond.step), bottom to top
1. Bare boss end face Ø8 (**no anodise**).
2. Internal-tooth star washer DIN 6797 J M4, A2 stainless (OD 8, t 0.6). It bites the bare face.
3. M4 ring terminal on the PE conductor (Z 19.2-20.0); tongue points **-y** over the board top edge (crimp barrel in the 8 mm top gap, y -11 to -17).
4. M4 flat washer, M4x10 A2 pan/button head, ESTIMATED 1.2 N·m (Compliance: IEC 61010-1 Table 2, M4). Locked by the star washer plus torque (a second internal-tooth star washer under the head is allowed). **No thread-locker**: it would insulate the joint and is not an acceptable locking means for a bonding joint.
- **Access:** new rear-wall window x 3-20, y -21 to -1 (rear wall only, Z 44-48) over the boss; the lug is fitted and torqued from the rear with the shell on (reach about 27 mm). The right terminal window is back to its phase 10 size (y 34-182). This window, like the existing J28/J29/J30 wiring window next to it, opens into the cabinet behind the gasketed panel; the left wall y 15-105 stays solid (1.000) and the front seal (gasket) is unchanged. It is not closed by a cover (same justification as the terminal windows; INFERRED). Option: a PA12 snap cover with a grommet for the PE wire (ESTIMATED $1).
- Mark the IEC 60417-5019 PE symbol on the shell beside the window (Compliance recommendation).

## PE conductor (phase 14, Compliance hv_rulings_phase13.md §2)
- Green/yellow **copper**, at least **2.5 mm² (14 AWG)** and **no smaller than the 600 V sense wire** (whichever is larger). Use **4 mm² (12 AWG)** where the PE run is not mechanically protected (outside conduit/cabinet). 1.5 mm²/16 AWG is not acceptable.
- Basis (per Compliance): IEC 61010-1 2nd ed §6.5.1.2 h)1) (VERIFIED there), IEC 60364-5-54 §543.1.3 (VERIFIED there), NEC Table 250.122 (VERIFIED there).
- **Ring terminal check:** the BOM row said only "M4 ring terminal" (no size). Correction: **M4 (4.3 hole) insulated ring, 1.5-2.5 mm² (blue, 16-14 AWG) for a 2.5 mm² PE; 4-6 mm² (yellow, 12-10 AWG) for a 4 mm² PE**, tin-plated Cu. ESTIMATED $0.15 (blue) / $0.25 (yellow) each; supply both or the one the installation manual names. A yellow M4 ring is about 9-10 mm wide (ESTIMATED), wider than the Ø8 face; it bears on the star washer; fits the access window.
- Install note: PE conductor connected first and removed last, on its own screw (2nd ed §6.5.1.2 g), per Compliance).

## Anodise mask-off (CNC bezel drawing notes)
- **M1** PE_NEW boss end face (Ø8 full face) + its M4 thread, at (12.3, -7.5), Z 18.6. Use a masking plug/cap. (Old M1 at H4 deleted; H4 boss no longer exists.)
- **M2/M3/M4** H1, H2, H3 boss end faces (Ø9 spot faces, where the CHASSIS pads clamp) + threads.
- **M5** bond test spot: Ø6 bare spot on the bezel's **left outer edge face** (x -26.22, y -7.5, Z ≈ 2-7), outside the gasket land and the PA12 ring, close to the new PE boss (moved from the right edge at x 302.8, y 185.5).
- Alternative: anodise everything, then spot-face M1-M5 after anodise (ESTIMATED same cost).

## Continuity test (phase 13, per Compliance pe_bond_review.md)
- Applicable clause (Compliance, SECONDARY/VERIFIED 2nd ed): this unit is **permanently connected** (field-wired J28/J29 + PE stud), so the bond test is **IEC 61010-1 3rd ed §6.5.2.5 (2nd ed §6.5.1.4)**: test current **2× the external overcurrent protection** named in the installation instructions (the external fused terminals on the 600 V sense lines), 1 min, voltage drop **≤ 10 V**. The installation manual must name that fuse.
- Production recommendation (Compliance JUDGMENT):
  - **Type test (once):** 25 A, 60 s, PE lug barrel to M5 (new position, left edge), ≤ 0.1 Ω (covers both readings).
  - **Per unit:** 10 A DC, 4-wire (Kelvin), PE lug barrel to bare test spot M5, **≤ 0.1 Ω**. Record with the serial number.
  - **CHASSIS check:** ≤ 1 A 4-wire milliohm, M5 to each H1-H3 CHASSIS pad test point, ≤ 0.1 Ω. Never pass more than 1 A through the board's CHASSIS pads (functional earth, not the protective bond).

## Galvanic corrosion (phase 13)
- The stack mixes A2 stainless (screw, washers), tinned copper (ring terminal) and bare 6061 aluminium (boss face, M5 spot). Aluminium is anodic to both; with moisture or salt air (Hawaii site) the bare Al face can corrode and the bond resistance rises (INFERRED).
- Locking stays mechanical: star washer + torque only (see stack item 4).
- **Mitigation (SUGGESTION, not yet in CAD/BOM):** (a) a conductive chromate/TCP conversion coat (MIL-DTL-5541 Class 3, per Compliance, FROM-MEMORY there) on the masked areas M1-M5 instead of bare Al, ESTIMATED +$3-5 per bezel in the anodise lot; or (b) a corrosion-inhibiting compound approved for electrical aluminium joints applied to the assembled joint, then sealed/overcoated outside the contact area, ESTIMATED $0.20 per unit. Re-test the bond (per-unit test) after any rework.

## PE stud location (phase 14)
- Resolved in CAD by PE_NEW (pending BCR-11 and Compliance/NRTL view of "near"). The phase 13 option table (H4 / H1 / H3 / (16, 3)) is superseded.

## Mismatches flagged
1. README/BCR language "H4 PE" (phase 11-13) meant a **bezel** boss; from phase 14 the PE boss is PE_NEW; the PCB has no PE net or PE terminal. No PE pin exists on any board connector (J28/J29 carry L1-L3/N only). The PE conductor therefore lands only on the bezel stud. OK, but the installation manual must say so.
2. H1-H3 CHASSIS pads bond to PE only if those boss faces are masked. This was not specified before phase 11.
3. The rim trim (Z 7.0, 7.0 mm at 2 mm leads) counts as **basic** only with this bond made and tested. With leads clipped to ≤ 1.0 mm it is 8.0 mm (reinforced), per Compliance phase 9.
