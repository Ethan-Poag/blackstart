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
4. M4 flat washer, M4x10 A2 pan/button head, torque per insert/tap (ESTIMATED 1.2 N·m), plus thread-locker or a second star washer under the head.
- PE conductor size and colour (green/yellow) per installation rules; field-wired. The cross-section is not chosen here (Compliance to state).
- **Access:** the shell's right terminal window is extended from y 182 to **y 192** (x 262.3-281.3, rear wall), so the lug can be fitted and torqued from the rear after the shell is on. The PE hardware is 264 mm from the nearest HV plug (CAD).

## Anodise mask-off (CNC bezel drawing notes)
- **M1** PE boss end face (Ø8 full face) + its M4 thread, at (272.0, 185.5), Z 18.6. Use a masking plug/cap.
- **M2/M3/M4** H1, H2, H3 boss end faces (Ø9 spot faces, where the CHASSIS pads clamp) + threads. Without these, CHASSIS floats (the board's CAN/ETH/USB shield returns rely on it).
- **M5** bond test spot: Ø6 bare spot on the bezel's **right outer edge face** (x 302.8, y 185.5, Z ≈ 2-7), outside the gasket land and the PA12 ring, for a factory Kelvin probe before installation. (The rear field at x 293.8-302.8 is the gasket land and must stay sealed, so it was not used.)
- Alternative: anodise everything, then spot-face M1-M5 after anodise (ESTIMATED same cost).

## Continuity test (production, each unit)
- Between the PE ring-terminal barrel and **M5**, then between M5 and each H1-H3 pad's CHASSIS net (a test point on the board).
- Method and limit: protective-bond test per **IEC 61010-1 §6.5.2.4 (test current 25 A or 2× rated, ≤ 0.1 Ω)**. **This citation is from memory, UNVERIFIED; Compliance to confirm the clause and limit.** Any number used before confirmation is ESTIMATED.
- Record the result with the serial number. A low-current 4-wire milliohm check (ESTIMATED target < 0.1 Ω) can also be used for incoming inspection of the bezel masking.

## Mismatches flagged
1. README/BCR language "H4 PE" means a **bezel** boss; the PCB has no PE net or PE terminal. No PE pin exists on any board connector (J28/J29 carry L1-L3/N only). The PE conductor therefore lands only on the bezel stud. OK, but the installation manual must say so.
2. H1-H3 CHASSIS pads bond to PE only if those boss faces are masked. This was not specified before phase 11.
3. The rim trim (Z 7.0, 7.0 mm at 2 mm leads) counts as **basic** only with this bond made and tested. With leads clipped to ≤ 1.0 mm it is 8.0 mm (reinforced), per Compliance phase 9.
