# PE_BOND: bezel-to-PE bond (phase 11). Ethan confirmed Oct 25: bezel is grounded (bonded to PE).
Nothing here is certified; Compliance / NRTL to review.

## Where (MEASURED from genctl_v4_handrouted.kicad_pcb, read-only, and enclosure_v3.py)
- **H4** = "PE boss clearance D9.5 NPTH" at (272.0, 185.5), **no net, no copper**. The PCB does not carry PE; the board only has a 9.5 mm clearance hole for the bezel PE boss.
- **Bezel PE boss** (6061, part of the CNC bezel): Ø8.0, from the field Z 0.5 up through the PCB hole to its end face at **Z 18.6** (PCB rear 17.6 + 1.0). M4 tap Ø3.3, Z 3.0-19.
- **H1/H2/H3** (M4 bezel bosses, (2.0, -9.25), (274.56, -9.25), (2.0, 188.71)) carry the board net **CHASSIS** on Ø9 plated pads. CHASSIS goes to GND only via R33 1M // C48 4.7n (MEASURED). So CHASSIS = PE only through the bezel, via the H1-H3 screws.

## Stack at H4 (CAD part `pe_bond`, step/pe_bond.step), bottom to top
1. Bare boss end face Ø8 (**no anodise**).
2. Internal-tooth star washer DIN 6797 J M4, A2 stainless (OD 8, t 0.6). It bites the bare face.
3. M4 ring terminal on the PE conductor (Z 19.2-20.0); tongue points +x (x 275.5-281.5, clear of J1 at y ≤ 180), crimp barrel just inside the right wall.
4. M4 flat washer, M4x10 A2 pan/button head, torque per insert/tap (ESTIMATED 1.2 N·m), locked by the star washer plus torque (a second internal-tooth star washer under the head is allowed). **No thread-locker**: it would insulate the joint and is not an acceptable locking means for a bonding joint.
- **PE conductor size (phase 13):** green/yellow, field-wired, **at least as large as the 600 V sense wiring (L1-L3/N on J28/J29)** per IEC 61010-1 2nd ed §6.5.1.2 h). The sense wire gauge is not specified anywhere in the repo, so the value is **TBD**: "match or exceed the 600 V sense wire gauge". For reference, the J28/J29 plugs (Phoenix SPC 5/4-STF-7,62) accept 0.2-10 mm² (MEASURED, connectors_phoenix.md). The installation manual must state the size.

## Galvanic corrosion (phase 13)
- The stack mixes A2 stainless (screw, washers), tinned copper (ring terminal) and bare 6061 aluminium (boss face, M5 spot). Aluminium is anodic to both; with moisture or salt air (Hawaii site) the bare Al face can corrode and the bond resistance rises (INFERRED).
- Locking stays mechanical: star washer + torque only (see stack item 4).
- **Mitigation (SUGGESTION, not yet in CAD/BOM):** (a) a conductive chromate/TCP conversion coat (MIL-DTL-5541 Class 3, per Compliance, FROM-MEMORY there) on the masked areas M1-M5 instead of bare Al, ESTIMATED +$3-5 per bezel in the anodise lot; or (b) a corrosion-inhibiting compound approved for electrical aluminium joints applied to the assembled joint, then sealed/overcoated outside the contact area, ESTIMATED $0.20 per unit. Re-test the bond (per-unit test) after any rework.

## PE stud location: TBD (phase 13)
- IEC 61010-1 (2nd ed §6.5.1.2 d) wants the PE terminal **near** the terminals of the circuit needing protective earth. H4 (272, 185.5) is **276.8 mm** from the nearest J28/J29 pad (313.0 mm to the farthest) (MODELLED, pad coordinates from the board). Location is therefore **TBD**.
- Closer options (distances to the nearest / farthest J28/J29 pad, MODELLED):
  | Option | Position | Nearest / farthest | Needs |
  |---|---|---|---|
  | Keep H4 + written justification | (272, 185.5) | 276.8 / 313.0 | Compliance/NRTL acceptance |
  | Reuse H1 boss | (2.0, -9.25) | 32.7 / 105.6 | CAD (separate PE screw/longer boss) and a board change: H1 has a plated CHASSIS pad; PE current must not pass through it |
  | Reuse H3 boss | (2.0, 188.71) | 92.7 / 165.5 | Same as H1 |
  | New bezel PE boss near J28/J29, e.g. (16, 3) | example only | 21.2 / 93.8 | Board change request: new NPTH Ø9.5 clearance hole, copper ≥ 5.5 mm from hot copper; CAD: new boss + mask + rear window access |
- No redesign made; the choice goes to the lead (board change request text is in the phase 13 report).

- **Access:** the shell's right terminal window is extended from y 182 to **y 192** (x 262.3-281.3, rear wall), so the lug can be fitted and torqued from the rear after the shell is on. The PE hardware is 264.3 mm from the nearest HV plug envelope (MODELLED, checks.json).

## Anodise mask-off (CNC bezel drawing notes)
- **M1** PE boss end face (Ø8 full face) + its M4 thread, at (272.0, 185.5), Z 18.6. Use a masking plug/cap.
- **M2/M3/M4** H1, H2, H3 boss end faces (Ø9 spot faces, where the CHASSIS pads clamp) + threads. Without these, CHASSIS floats (the board's CAN/ETH/USB shield returns rely on it).
- **M5** bond test spot: Ø6 bare spot on the bezel's **right outer edge face** (x 302.8, y 185.5, Z ≈ 2-7), outside the gasket land and the PA12 ring, for a factory Kelvin probe before installation. (The rear field at x 293.8-302.8 is the gasket land and must stay sealed, so it was not used.)
- Alternative: anodise everything, then spot-face M1-M5 after anodise (ESTIMATED same cost).

## Continuity test (phase 13, per Compliance pe_bond_review.md)
- Applicable clause (Compliance, SECONDARY/VERIFIED 2nd ed): this unit is **permanently connected** (field-wired J28/J29 + PE stud), so the bond test is **IEC 61010-1 3rd ed §6.5.2.5 (2nd ed §6.5.1.4)**: test current **2× the external overcurrent protection** named in the installation instructions (the external fused terminals on the 600 V sense lines), 1 min, voltage drop **≤ 10 V**. The installation manual must name that fuse.
- Production recommendation (Compliance JUDGMENT):
  - **Type test (once):** 25 A, 60 s, PE lug barrel to M5, ≤ 0.1 Ω (covers both readings).
  - **Per unit:** 10 A DC, 4-wire (Kelvin), PE lug barrel to bare test spot M5, **≤ 0.1 Ω**. Record with the serial number.
  - **CHASSIS check:** ≤ 1 A 4-wire milliohm, M5 to each H1-H3 CHASSIS pad test point, ≤ 0.1 Ω. Never pass more than 1 A through the board's CHASSIS pads (functional earth, not the protective bond).

## Mismatches flagged
1. README/BCR language "H4 PE" means a **bezel** boss; the PCB has no PE net or PE terminal. No PE pin exists on any board connector (J28/J29 carry L1-L3/N only). The PE conductor therefore lands only on the bezel stud. OK, but the installation manual must say so.
2. H1-H3 CHASSIS pads bond to PE only if those boss faces are masked. This was not specified before phase 11.
3. The rim trim (Z 7.0, 7.0 mm at 2 mm leads) counts as **basic** only with this bond made and tested. With leads clipped to ≤ 1.0 mm it is 8.0 mm (reinforced), per Compliance phase 9.
