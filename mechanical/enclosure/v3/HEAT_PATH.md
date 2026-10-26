# Heat path v3: CM5 -> pad -> laser-cut Al heat bar -> bezel heat boss -> bezel face -> ambient (no fan)
Power (cm5-datasheet.pdf §3.3, MEASURED, local copy in /workspace/genctl/datasheets): idle ~400 mA, operating ~900 mA at 5 V -> **2.0 W idle, 4.5 W typical**. §B.3: supply must allow 5 V x 2.5 A = 12.5 W (supply budget, not dissipation). §4.4: SoC throttles to stay < 85 C; module range -20..+85 C.
Design load used: **6 W sustained CM5** (INFERRED, heavy UI + Ethernet). Other heat into the bezel: display backlight 23-26.5 V x ~360 mA = **~8.6 W** (MEASURED from display_mech.md / Riverdi DR; full brightness) is bonded to the bezel ledge; board LV electronics ~3 W (INFERRED) mostly to shell air.

| Element | R (K/W) | Label |
|---|---|---|
| SoC junction->case (BCM2712, no RPi figure published) | 2.00 | INFERRED |
| Pad CM5->heat bar 1.0 mm, k=6 W/mK, over 17x17 mm SoC | 0.58 | INFERRED k/area |
| Heat bar 6061 4.75 mm, 40 mm path, 32 mm wide (k=167) | 1.58 | INFERRED geometry from model |
| Bar->boss joint, 2x M4 + thermal grease, 29x6.2 mm | 0.30 | INFERRED |
| Bezel boss 29x6.2 mm, 19.5 mm long (k=167) | 0.65 | MEASURED geometry from model, k INFERRED |
| Spreading in 4 mm bezel field to full face | 0.70 | INFERRED |
| Bezel front 329x261 mm to ambient, h=9 W/m2K (nat. conv.+rad., black anodise) | 1.29 | INFERRED h |
| **Sum SoC junction -> bezel face (CM5 path only)** | **5.80** | |
| Bezel -> ambient | 1.29 | |

Results (bezel carries CM5 6 W + backlight 8.6 W = 14.6 W, INFERRED share 100 % front):
| Ambient | Bezel face | SoC junction @6 W | SoC @4.5 W |
|---|---|---|---|
| 25 C | 44 C | 79 C | 68 C |
| 40 C | 59 C | 94 C | 83 C |
| 50 C | 69 C | 104 C | 93 C |

**Conclusion (INFERRED, ±30 %):** fine at 25 C; at 40-50 C ambient the SoC reaches/exceeds the 85 C throttle point and the bezel face gets hot to touch (>60 C). Biggest terms: bezel-to-air (fixed by size) and the backlight load. Mitigations, cheapest first: dim backlight (50 % -> -4 W), cap CM5 clock, CNC heat bar 8 mm or copper (-1 K/W), add fins on the heat bar facing the rear vents (shell air path), keep the vent chimney. No sun-load included: a black bezel in direct sun adds ~+20-30 K (INFERRED). **Measure on a prototype.**


## Options (phase 2)
Method: the same 1-D series resistance model as above. T_SoC = Ta + P_bezel x R_bezel-air + P_CM5 x R_chain. P_bezel = 6 W CM5 + 8.6 W backlight = 14.6 W. Throttle onset 80 C (Raspberry Pi firmware soft throttle at 80 C, harder at 85 C; Pi docs, not re-checked this turn). Baseline: R_chain 5.80, R_bezel-air 1.29 -> T_SoC = Ta + 53.6 -> **throttles above 26 C ambient**. This replaces the earlier 40-50 C wording: at 6 W the CM5 throttles well before 40 C. All deltas are ESTIMATED.

| Option | R_chain K/W | R_bezel-air K/W | throttle ambient (6 W) | +cost qty1 / qty10 |
|---|---|---|---|---|
| Base | 5.80 | 1.29 | 26 C | 0 |
| A: bar 4.75 -> 8 mm and wider, 6 W/mK 0.5 mm pad, bigger boss | 4.41 (bar 0.79, pad 0.20, boss 0.40) | 1.29 | 35 C | +$14 / +$9 |
| B: A + rear bezel fins (20 x 15 mm, eff. 0.8, h 6) + shell vents | 4.41 | 0.75 | 42 C | +$74 / +$39 |
| C: B + CM5 limit to 3.5 W (arm_freq cap, power INFERRED) + backlight 70 % | 4.41 | 0.75 | 3.5 x 4.41 + 12.0 x 0.75 = 24.4 K -> 56 C | +$74 / +$39 (firmware only) |

Only C keeps the SoC below throttle at 50 C ambient. Fins on a laser-cut stack bezel are not practical, so B and C imply the CNC bezel.

## Bezel touch temperature (safety)
Bezel rise = 14.6 W x R_bezel-air: 18.8 K base, 11 K with fins (B), 9 K with C.
IEC 62368-1 Table 38, accessible metal surfaces, TS1 limits (UNVERIFIED, from memory, check the standard): about 43 C for contact over 8 h, 48 C for 10 min to 8 h, 51 C for 1-10 min and 60 C under 1 min. IEC 60950-1 Table 4C, handles held briefly, metal: 55 C (UNVERIFIED).
- Base at 40 C ambient gives a 59 C bezel: fails the 48 C limit.
- C at 40 C ambient gives 49 C: borderline.
- At 50 C ambient no option meets 48 C, so a hot-surface warning label or a non-metal touch zone is needed.

## Phase 3 re-check: validated inputs (2026-10-25)
| Input | Value | Label | Source |
|---|---|---|---|
| CM5 module idle | 2.0 W (400 mA x 5 V) | datasheet typical | https://datasheets.raspberrypi.com/cm5/cm5-datasheet.pdf §3.3 |
| CM5 module "operating" | 4.5 W (900 mA x 5 V) | datasheet typical | same |
| CM5 idle at the wall (includes the CM5 IO board) | 2.3-2.4 W | MEASURED on a CM5 | Geerling https://github.com/geerlingguy/sbc-reviews/issues/58 ; CNX https://www.cnx-software.com/2024/12/22/raspberry-pi-cm5-review-different-cooling-solutions/ |
| CM5 under stress-ng / HPL, at the wall | 8.5 / 9.4 W | MEASURED on a CM5 (board power, not module only) | Geerling issue 58 |
| CM5 under stress, passive heatsink, at the wall | 6.66 W (SoC 63.7 C) | MEASURED on a CM5 | https://shumeipai.nxez.com/2024/12/11/raspberry-pi-compute-module-5-review.html |
| Our workload: Qt/Wayland dashboard at 1280x800, Ethernet, light CPU | 2.5 low / 4.0 typ / 8.5 high (stress, worst case) W | ESTIMATED (no CM5 measurement for this load was found) | interpolated from the rows above |
| Backlight | 8.6 W, kept separate from the CM5 | from the earlier display data, unchanged | above |
| Throttle | soft (Arm) 80-85 C, hard (Arm + GPU) 85 C; the limit can be lowered but not raised | MEASURED (documentation) | https://github.com/raspberrypi/documentation/blob/master/documentation/asciidoc/computers/raspberry-pi/frequency-management.adoc ; https://www.raspberrypi.com/news/heating-and-cooling-raspberry-pi-5/ |
| BCM2712 junction-to-case | not published (2.0 K/W kept) | ESTIMATED | none found |
| CM5 heatsink K/W | no K/W published. Official passive cooler: 79.3 C under CPUminer at 25-26 C ambient, no throttling. That is about 54 K at about 8.5 W (power from Geerling's test, a different run), roughly 6 K/W SoC-to-air | INFERRED cross-check | CNX link above |
| Our chain SoC to bezel 5.80 + bezel to air 1.29 (per W of CM5, about 7.1 K/W, plus the backlight load) | | ESTIMATED | about 15 % worse than the official cooler, which is plausible for a conduction path to a shared bezel |

### Throttle ambient at 80 C soft limit (T_SoC = Ta + (P + 8.6) R_ba + P R_chain)
| Option | 2.5 W low | 4.0 W typical | 8.5 W high |
|---|---|---|---|
| No change | 51 C | 41 C | 9 C |
| A | 55 C | 46 C | 20 C |
| B | 61 C | 53 C | 30 C |
| C (cap 3.5 W, backlight 70 %) | 63 C | 57 C | 57 C |

Conclusion: the phase-2 figure of 26 C assumed a 6 W load. For the real dashboard load (about 4 W, ESTIMATED), no change throttles at about 41 C and B at about 53 C. Only C stays clear at 50 C ambient whatever the software does. Next step: measure the CM5 power on the real dashboard (`vcgencmd pmic_read_adc`).


## Phase 4: cool-to-touch redesign (Ethan: nothing uncomfortably hot; 60 C is not acceptable)
**Target.** At 40 C ambient and typical load (CM5 4 W, backlight 70 %), every surface an operator touches stays at or below 45 C.
- Basis: Ethan's requirement. It is stricter than IEC 62368-1 Table 38 TS1 (48 C for metal, glass or plastic touched > 1 min, defined at 25 C) and IEC/UL 61010-1 Table 19 at 40 C ambient (55 C metal knobs, 65 C glass knobs, 65 C accidentally touched uncoated metal). Source: /workspace/compliance/touch_temperature.md.
- Margin: with Ta = 40 C the 45 C target leaves 5 K of rise.
- Worst case, stated: CM5 8.5 W (MEASURED stress figure), backlight 100 %, 500 W/m2 sun on the face (ESTIMATED: partial sun through a cabinet door or window). Absorptivity 0.9 for black glass and anodise, 0.5 for a light-grey PA12 ring (ESTIMATED).

### 1. Display and board heat (MEASURED from /workspace/genctl/datasheets/DS_RVT121HVLNWCA0-B_Rev.1.1.txt unless marked)
- Backlight: 48 LEDs, Vf 25.6 V typ (23.0-26.5), If 360 mA. **WBL 8.28 / 9.22 / 9.54 W** (min/typ/max). The earlier 8.6 W is replaced by 9.22 W.
- TFT logic: 3.3 V x 210 mA = 0.69 W. Touch controller: 3.3 V x 100 mA = 0.33 W. Display total about 10.2 W typical at full backlight.
- Light out: about 5 % of backlight power leaves through the LCD as light (ESTIMATED: LED radiant efficiency about 35 % times LCD transmission about 5-8 %). So **about 95 % of the backlight, roughly 8.8 W, becomes heat inside the display module**.
- Where it goes: into the LED bar, the module frame and the cover glass. The glass radiates and convects to the front. The module rear passes heat across the 11.44 mm air gap to the PCB (7.27 mm at the source band; 3.27 mm was the pre-flush value). The module frame conducts into the bezel ledge.
- Other board loads:
  - SN65DSI83 ICC 77 mA typ at 1.8 V = 0.14 W (MEASURED, sn65dsi83.txt).
  - Backlight driver loss about 10 % of backlight power (ESTIMATED).
  - Other loads about 0.5 W (ESTIMATED).

### 2. Design D (recommended): heat goes to the back; the front becomes plastic
- **Rear fin plate.** 6061 base 242 x 177 x 4.75 mm (laser or waterjet), with 2 mm laser-cut fin slats at 8 mm pitch and 30 mm tall, bonded or pressed into milled slots. The plate is screwed to the 4 shell posts on the outside of the PA12 rear wall, which has a 235 x 172 opening under it. It sits behind the customer panel inside the cabinet, so it is not touched in normal use. It stays inside the shell outline, so the front-slide fit through the cutout is unchanged (checked: 1.0 mm/side). Fins are omitted around the J10/J11 plugs, and the plate is cut around the port tunnels. Total depth behind the bezel face becomes 82.75 mm (was 48). **The cabinet must allow this depth.**
- **Heat path.** A 6061 heat pillar (40 x 28 mm) runs from the CM5 heat bar to the fin plate. Chain: junction-to-case 2.0 + pad 0.2 + bar/pillar 0.8 + joint 0.3 = 3.3 K/W (ESTIMATED).
- **Thermal break at the front.**
  - Display mounted on the bezel ledge with foam VHB tape instead of metal contact (about 0.1 W/K, ESTIMATED).
  - *(REMOVED in Phase 23; Ethan never approved it.)* A 3 mm SLS PA12 front ring covered all exposed metal of the bezel face, held off it by a 1 mm air gap on PA12 stand-off pips.
  - The metal bezel stays as the structural frame and display carrier but is no longer a touch surface.
  - Keys sit in ring pockets with 0.4 mm clearance around the cap heads.
- **DEVIATIONS from Ethan's original constraints:**
  1. The CM5 heat no longer goes through a strap to a bezel boss. The boss is kept in the model but carries no heat in D.
  2. The PA12 ring stands 4 mm in front of the glass, so the glass is no longer flush with the outer face. A production version could recess the metal bezel 4 mm to restore flush glass; that is not modelled.
  3. The unit is deeper: 82.75 mm instead of 48 mm.
- **Variant D'** (compatible with the original constraint): the CM5 strap to the bezel boss is kept, and two 6061 bars inside the shell (about 2 W/K) tie the bezel frame to the fin plate. The PA12 ring and display isolation are the same as D.
- **Option E / E'** = D / D' plus a 1.5 mm aluminium spreader on the display rear, strapped to a larger fin plate. **Not buildable without a board change.** The strap has to get past the PCB: side clearance is only 2 mm, and the top band holds the switches and THT terminals. See BCR-9 (request only).

### 3. Results at 40 C ambient (model: thermal_v3.py, results in thermal_results.json; all conductances ESTIMATED)
Cabinet air behind the panel is assumed to be ambient + 5 C (ESTIMATED). "touch" means the glass, the metal bezel face (none/A/B), or the PA12 ring (D/E). Throttle point is the 80 C soft limit.

| Option | CM5 W | BL | case | glass | metal bezel | PA12 ring | SoC | throttle Ta |
|---|---|---|---|---|---|---|---|---|
| none | 4.0 | 100 % | no sun | 55.3 | 54.7 |  | 77.9 | 42.1 |
| none | 4.0 | 70 % | no sun | 52.6 | 52.4 |  | 75.6 | 44.4 |
| none | 4.0 | 40 % | no sun | 49.8 | 50.1 |  | 73.3 | 46.7 |
| none | 2.5 | 70 % | no sun | 51.4 | 50.8 |  | 65.3 | 54.7 |
| none | 8.5 | 100 % | no sun | 59.1 | 59.7 |  | 109.0 | 11.0 |
| none | 8.5 | 100 % | sun 500 W/m2 | 94.5 | 96.0 |  | 145.3 | -25.3 |
| A | 4.0 | 100 % | no sun | 55.3 | 54.7 |  | 72.4 | 47.6 |
| A | 4.0 | 70 % | no sun | 52.6 | 52.4 |  | 70.1 | 49.9 |
| A | 4.0 | 40 % | no sun | 49.8 | 50.1 |  | 67.7 | 52.3 |
| A | 2.5 | 70 % | no sun | 51.4 | 50.8 |  | 61.8 | 58.2 |
| A | 8.5 | 100 % | no sun | 59.1 | 59.7 |  | 97.2 | 22.8 |
| A | 8.5 | 100 % | sun 500 W/m2 | 94.5 | 96.0 |  | 133.5 | -13.5 |
| B | 4.0 | 100 % | no sun | 51.1 | 49.1 |  | 66.8 | 53.2 |
| B | 4.0 | 70 % | no sun | 49.0 | 47.7 |  | 65.3 | 54.7 |
| B | 4.0 | 40 % | no sun | 46.9 | 46.2 |  | 63.9 | 56.1 |
| B | 2.5 | 70 % | no sun | 48.3 | 46.7 |  | 57.7 | 62.3 |
| B | 8.5 | 100 % | no sun | 53.4 | 52.2 |  | 89.7 | 30.3 |
| B | 8.5 | 100 % | sun 500 W/m2 | 78.4 | 74.7 |  | 112.2 | 7.8 |
| D | 4.0 | 100 % | no sun | 55.7 | 47.9 | 45.4 | 63.6 | 56.4 |
| D | 4.0 | 70 % | no sun | 52.2 | 46.4 | 44.4 | 63.1 | 56.9 |
| D | 4.0 | 40 % | no sun | 48.7 | 44.9 | 43.3 | 62.6 | 57.4 |
| D | 2.5 | 70 % | no sun | 52.0 | 46.2 | 44.2 | 56.7 | 63.3 |
| D | 8.5 | 100 % | no sun | 56.5 | 48.5 | 45.8 | 82.8 | 37.2 |
| D | 8.5 | 100 % | sun 500 W/m2 | 87.7 | 74.0 | 72.0 | 87.4 | 32.6 |
| E | 4.0 | 100 % | no sun | 53.4 | 47.0 | 44.8 | 63.3 | 56.7 |
| E | 4.0 | 70 % | no sun | 50.9 | 45.8 | 44.0 | 62.4 | 57.6 |
| E | 4.0 | 40 % | no sun | 48.4 | 44.7 | 43.2 | 61.5 | 58.5 |
| E | 2.5 | 70 % | no sun | 50.5 | 45.6 | 43.8 | 56.5 | 63.5 |
| E | 8.5 | 100 % | no sun | 54.9 | 47.8 | 45.3 | 81.0 | 39.0 |
| E | 8.5 | 100 % | sun 500 W/m2 | 77.1 | 69.9 | 69.2 | 89.1 | 30.9 |
| E' | 4.0 | 100 % | no sun | 53.6 | 50.5 | 47.1 | 68.1 | 51.9 |
| E' | 4.0 | 70 % | no sun | 51.1 | 49.5 | 46.5 | 67.1 | 52.9 |
| E' | 4.0 | 40 % | no sun | 48.6 | 48.5 | 45.8 | 66.2 | 53.8 |
| E' | 2.5 | 70 % | no sun | 50.6 | 48.3 | 45.6 | 59.3 | 60.7 |
| E' | 8.5 | 100 % | no sun | 55.1 | 54.2 | 49.7 | 91.7 | 28.3 |
| E' | 8.5 | 100 % | sun 500 W/m2 | 77.0 | 66.7 | 67.1 | 104.2 | 15.8 |
| D' | 4.0 | 100 % | no sun | 56.2 | 50.7 | 47.3 | 68.3 | 51.7 |
| D' | 4.0 | 70 % | no sun | 52.8 | 49.8 | 46.7 | 67.4 | 52.6 |
| D' | 4.0 | 40 % | no sun | 49.4 | 48.9 | 46.0 | 66.5 | 53.5 |
| D' | 2.5 | 70 % | no sun | 52.3 | 48.3 | 45.7 | 59.4 | 60.6 |
| D' | 8.5 | 100 % | no sun | 57.5 | 55.0 | 50.2 | 92.5 | 27.5 |
| D' | 8.5 | 100 % | sun 500 W/m2 | 86.7 | 67.6 | 67.7 | 105.1 | 14.9 |

**Reading the table:**
- **The PA12 ring meets 45 C in D:** 44.4 C typical, 43.3-45.4 C across backlight levels, 45.8 C at CM5 8.5 W. **The metal bezel face in none/A/B does not:** 46-60 C.
- **The cover glass misses 45 C in every option:** 48-57 C at 40 C ambient. The cause is the display's own ~9-10 W plus warm cabinet air behind it, not the CM5. Even with the backlight off, the model gives 45.1 C (E). A spacer or second cover glass is not possible because the PCAP touch is bonded to the glass. What is left:
  - Firmware brightness derating at high ambient (40 % backlight gives 48.7 C in D).
  - Accept the 61010-1 glass limits (65 C for normal-use contact at 40 C ambient), or the 62368-1 48 C rule at 25 C ambient (the glass is about 36 C at 25 C ambient). **Ethan needs to decide.**
- CM5 throttle ambient in D: 56.4-57.4 C at 4 W, 63 C at 2.5 W, 37 C at 8.5 W. B gives 53-56 C at 4 W.
- **Sun worst case:** no option keeps the face below 45 C. In D the glass reaches about 88 C and the ring about 72 C (light grey). A sun hood or shading is needed if direct sun is possible.

### 4. Validation plan and uncertainty
- **Bench test:**
  - CM5 on its IO board, or the real board, inside a printed shell. Mock bezel: the real CNC part or a 4 mm 6061 plate of the same outline. Real display at 100/70/40 % backlight.
  - Instruments: type-T thermocouples (±0.5 C) taped with Kapton on the glass centre, bezel face, ring face, fin plate, heat pillar and the interior air. SoC temperature from `vcgencmd measure_temp`. CM5 power from `vcgencmd pmic_read_adc` plus a USB/inline power meter on 5 V. Backlight V and I measured at LEDA.
  - Conditions: in an environmental chamber or a still-air box at 40 ± 1 C (or at 25 C, scaling rises linearly), panel vertical, no forced air, about 2 h to steady state. Workloads: the dashboard and `stress-ng --matrix 0`. Optional IR camera with emissivity tape.
  - The test would fit the ESTIMATED conductances (h_front, interior coupling, the fin plate's K/W).
- **Uncertainty (ESTIMATED):** h_front 9 ± 3 W/m2K moves the glass by about ±4 K. Fin plate K/W ±30 % moves SoC by about ±3 K. Cabinet ΔT of 0-10 K moves the rear-path nodes by about ±5 K. Overall: **touch temperatures ±5 K, SoC ±8 K, throttle ambient ±8 K.** The 45 C ring result is therefore marginal (0.6 K margin at typical load); the glass result is clearly above 45 C.

## Phase 5: cheaper variants and duty-cycled backlight (°F, with °C in brackets; model inputs unchanged except the fin-plate conductance per variant)
Fin-plate conductance is scaled from ATS catalogue natural-convection R per inch (MEASURED, ATS Extrusions R15_0121, https://media.digikey.com/pdf/Data%20Sheets/Advanced%20Thermal%20Solutions%20PDFs/Extrusions%20R15_0121.pdf: EXL424 4.0, EXL109 3.09, EXL117 6.9 °C/W per inch) to a 177 mm cut using R ∝ L^-0.7 (ESTIMATED).
Prices are Digi-Key figures from the qats.com distributor table on 2026-10-25 (MEASURED): EXL424 $79.37 / $70.23 and EXL109 $120.09 / $106.25 (qty 1 / qty 10).
Machining (saw cut, 4 holes, port notches) adds about $30 / $15 (ESTIMATED). No variant needs tooling.

Ambient 104 F (40 C), CM5 4 W. Touch = PA12 ring. Results: thermal_variants_p5.json.

| Variant | Ring at 100/70/40 % BL | Throttles above | Delta vs baseline, qty 1/10 | Depth |
|---|---|---|---|---|
| D (laser-cut fin plate) | 114/112/110 F | 134 F (56.9 C) | +$227 / +$115 | 82.75 mm |
| V1 EXL424, 16.5 mm fins | 114/112/110 | 135 F (57.4 C) | +$146 / +$100 | 64.5 |
| V2 EXL109, 32 mm fins | 113/112/110 | 137 F (58.3 C) | +$187 / +$136 | 80.05 |
| V3 = V1 + laser-cut stacked block | 114/112/110 | 133 F (56.2 C) | +$133 / +$94 | 64.5 |
| V4 flat 4.75 mm laser-cut plate + stacked block | 115/113/111 | 123 F (50.8 C) | +$59 / +$29 | 52.75 |
| V5 EXL117, 12.5 mm fins | 114/112/110 | 131 F (55.0 C) | price not checked | 60.5 |

Findings:
- The ring temperature hardly depends on the fins; the fins mainly set the CM5 throttle point.
- Depth can drop from 82.75 to 52.75 mm (flat plate). The cost is a lower CM5 throttle point: 134 F → 123 F at 4 W, and 99 F → 77 F (37 → 25 C) at 8.5 W.
- Fins beside the shell are impossible: anything must stay inside the 294 x 226 slide-in outline.
- The PA12 ring is already the cheapest option at $30 / $26 (MJF stand-in price). A machined ring would cost about $150 (ESTIMATED).

### Duty-cycled backlight (Ethan's idea): 90 % of the time at idle brightness, 10 % at 100 %
Steady state uses time-averaged power.
- Time constants (ESTIMATED): display/glass about 474 s (0.7 kg × 840 J/kgK ÷ 1.24 W/K); ring plus bezel about 40 min.
- Peak during a 2-minute bright period: average + (1 − e^(−120/474)) × (step to full) = average + 22 % of the step.
- Results: thermal_dutycycle_p5.json.

| Variant | Ring, idle 10/25/40 % | Glass avg (2-min peak), idle 25 % | Always 100 %: ring / glass | 1 h alarm: ring / glass | CM5 SoC, idle 25 % |
|---|---|---|---|---|---|
| none (metal face) | 119/121/123 F | 120 (123) F | 131 / 132 F | 128 / 132 | 163 F |
| D | 109/109/110 | 118 (121) | 114 / 132 | 113 / 132 | 144 F |
| V1 | 109/109/110 | 118 (121) | 114 / 132 | 113 / 132 | 144 F |
| V4 flat | 110/110/111 | 120 (123) | 115 / 134 | 114 / 134 | 154 F |
| D' (keeps boss) | 114/115/115 | 119 (122) | 117 / 133 | 117 / 133 | 151 F |
| D' + flat plate | 116/117/117 | 121 (124) | 121 / 135 | 120 / 135 | 154 F |

Results with duty cycling:
- **The ring meets 113 F (45 C)** with D, V1 or V4 at every idle level. Only V4 goes about 1-2 F over, and only under a long alarm or with the screen always bright.
- **D' does not meet the target:** the boss heats the bezel, giving a 114-117 F ring.
- **The glass still does not reach 113 F:** 115-123 F average and 119-125 F peaks, against 118-135 F before. The floor is the warm cabinet air (ESTIMATED ambient + 9 F) heating the display from behind, plus the 1 W of display logic.
- Under a 1 h or continuous alarm the glass reaches its full-bright steady state, 132-135 F (56-57 C). That is inside IEC 61010-1's 149 F (65 C) glass-knob limit, but not Ethan's 113 F.
- Reaching 113 F at the glass would need cooler cabinet air (ventilated cabinet) or idle at ≤10 % with the cabinet at ambient. Both are site-dependent and need measuring.

## Phase 6: FLUSH glass (Ethan's decision, Oct 25). Overrides Design D's 4 mm recess. °F, with °C in brackets.
Model change: the ring is now a real node, coupled to the glass edge through the 0.5 mm silicone bead and the 1.5 mm PA12 sleeve. Coupling g = 0.3 W/K (ESTIMATED); 0.1 W/K in variant G, where a 2 mm metal lip separates glass and ring. All other inputs are as in phase 5 (cabinet air = ambient + 9 F). Results: thermal_flush_p6.json.

Ambient 104 F (40 C), CM5 4 W. Entries are ring / glass at average backlight, with the 2-minute bright peak in brackets; idle backlight 10 / 25 / 40 %, 90 % of the time idle.

| Variant | idle 10 % | idle 25 % | idle 40 % | Always or 1 h alarm: ring / glass | CM5 throttles above (idle 25 %) | 8.5 W: throttles above | Sun 500 W/m2: ring / glass | Δ$ qty 1/10 | Depth |
|---|---|---|---|---|---|---|---|---|---|
| D-flush | 111/114 (118) | 112/117 (120) | 113/119 (122) | 119/129 | 136 F | 99 F | 170/186 | +227/+115 | 82.75 |
| **V1-flush (EXL424)** | **110/114 (118)** | **112/117 (119)** | **113/119 (121)** | 119/129 | 136 F | 101 F | 169/185 | **+146/+100** | **64.5** |
| V4-flush (flat plate) | 112/116 (119) | 113/118 (121) | 114/121 (123) | 120/131 | 126 F | 78 F | 173/191 | +59/+29 | 52.75 |
| D'-flush (boss kept) | 115/116 | 116/118 | 117/121 | 121/130 | 128 F | 81 F | 161/182 | +247/+125 | 82.75 |
| G: glass on metal ledge, bezel tied to EXL424, ring outside a 2 mm metal lip | 113/116 (118), metal lip 116 | 114/118, lip 117 | 115/120, lip 119 | 118/127, lip 124 | 138 F | 101 F | 158/168 | +166/+110 | 64.5 |
| G4: G with flat plate | 114/118 | 116/120 | 117/123 | 123/132 | 134 F | 89 F | 173/186 | +79/+39 | 52.75 |

What flush changes:
- The ring now picks up heat from the glass edge. The ring rises about 2-5 F against the recessed D, mostly at its inner edge, which runs near glass temperature.
- Glass averages fall about 1-3 F, because the glass now also sheds heat into the ring.
- Sun: the glass is fully exposed, so 168-191 F (76-88 C). A hood is needed if direct sun is possible.
- D' no longer meets 113 F (115-117 F) and is dropped.
- G (metal lip next to the glass) puts touchable metal at 116-124 F, so it fails the target.
- V4 is marginal: 112-114 F, failing at 40 % idle and under alarms.

Best option for flush glass: **V1-flush.** The ring stays ≤113 F (45 C) at idle 10-40 % with duty cycling. Under a long alarm or always-bright it reaches 119 F (48 C), which is still under the 61010-1 plastic limits. It is cheaper and shallower than D.

Best achievable glass temperature: 114 F (45.6 C) at 10 % idle, peaking at 118 F after 2 minutes bright. The glass does not reach 113 F with the cabinet at ambient + 9 F. What would get it there, from this model:
- A ventilated cabinet at ambient (ΔT 0): glass 111 F (44.1 C) at 10 % idle in G-type coupling. Always-bright is still 122 F.
- A cabinet 9 F below ambient: 107 F (41.5 C) idle, 118 F always-bright.
- A firmware dimming cap of 10 % idle and ≤2 min bright. An alarm still gives 127-129 F.
- A display-rear spreader (BCR-9) adds only 2-4 F of improvement and needs PCB slots.


## Phase 7: cabinet air at or below ambient (Ethan: the engine fan moves air around the OUTSIDE of the cabinet)
**ASSUMPTION TO VERIFY:** the cabinet air temperature is not measured. Verify it on a real generator with a thermocouple or logger inside the cabinet, next to the unit, during a full-load run. Earlier phases assumed cabinet air = ambient + 9 F.
Conditions: front ambient 104 F (40 C), CM5 4 W. Entries are ring / glass in F (C) at idle 10 / 25 / 40 % (90 % idle), then alarm (continuous 100 %).
A 1 h alarm reaches about the same glass temperature (time constant about 8 min); the ring reaches about 80 % of its rise (time constant about 40 min, ESTIMATED).
Throttle ambient is the front ambient at which the CM5 reaches 80 C at idle 25 %; the cabinet air at that point is shown in brackets. Data: thermal_cabinet_p7.json.

```
V1-flush cab 104 (40.0): 108 (42.4)/111 (44.1) | 110 (43.2)/114 (45.5) | 111 (44.0)/116 (46.9) | alarm 117 (47.1)/127 (52.5) | throttle ambient 145 (62.6) (cabinet 145 (62.6))
V1-flush cab 95 (35.0): 106 (41.3)/109 (42.6) | 108 (42.1)/111 (44.0) | 109 (42.9)/114 (45.4) | alarm 115 (46.0)/124 (51.0) | throttle ambient 153 (67.1) (cabinet 144 (62.1))
V1-flush cab 86 (30.0): 104 (40.2)/106 (41.1) | 106 (41.0)/108 (42.5) | 107 (41.8)/111 (43.9) | alarm 113 (44.9)/121 (49.5) | throttle ambient 161 (71.6) (cabinet 143 (61.6))
V4-flush cab 104 (40.0): 110 (43.2)/113 (45.1) | 111 (44.0)/116 (46.5) | 113 (44.8)/118 (48.0) | alarm 118 (48.0)/129 (53.8) | throttle ambient 133 (56.2) (cabinet 133 (56.2))
V4-flush cab 95 (35.0): 108 (42.1)/111 (43.7) | 109 (42.9)/113 (45.1) | 111 (43.8)/116 (46.6) | alarm 117 (47.0)/126 (52.4) | throttle ambient 140 (60.0) (cabinet 131 (55.0))
V4-flush cab 86 (30.0): 106 (41.1)/108 (42.3) | 107 (41.9)/111 (43.7) | 109 (42.7)/113 (45.2) | alarm 115 (46.0)/124 (51.0) | throttle ambient 147 (63.8) (cabinet 129 (53.8))
```
Result: with cabinet air 9 F or more below ambient, the V1-flush glass meets 113 F at 10-25 % idle, and at 40 % idle once the cabinet is 18 F below. In alarm the glass stays at 121-127 F.


## Phase 8: display-rear spreading, and a fan (DELIBERATE DEVIATION Ethan is evaluating: the original rule was no fan, vents OK)
Model: thermal_v3 with V6 settings (fin-plate conductance 0.45 W/K, ring-glass coupling 0.3 W/K). Data: thermal_fan_p8.json.

Columns: glass F at idle 10/25/40 % and at alarm 100 %; ring at idle 25 % / alarm; CM5 throttle ambient. Cabinet air = ambient, then ambient −9 F. **Cabinet air temperature is an ASSUMPTION to verify on a real generator.**

```
a V6 | cab=amb: 112 115 117 128 ring 111/118 thr 138 | cab-9F: 110 112 115 125 ring 109/116 thr 146
b V6+display spreader strapped to plate (gfp .55) | cab=amb: 113 116 118 126 ring 111/117 thr 139 | cab-9F: 110 112 114 123 ring 108/115 thr 145
b' upper bound: display rear perfectly tied to plate | cab=amb: 114 116 118 125 ring 111/116 thr 140 | cab-9F: 110 112 113 121 ring 108/114 thr 145
b'' upper bound: display rear at cabinet air (infinite sink) | cab=amb: 104 104 104 104 ring 104/104 thr 142 | cab-9F: 95 95 95 95 ring 99/99 thr 151
c V6 + 40mm fan (interior flushed) | cab=amb: 108 110 111 117 ring 107/111 thr 144 | cab-9F: 103 105 106 112 ring 104/108 thr 153
c2 fan + full finned plate | cab=amb: 108 110 111 117 ring 107/111 thr 147 | cab-9F: 103 104 106 112 ring 104/108 thr 155
d fan + CM5/hot-part heatsinks only, flat plate | cab=amb: 109 110 112 118 ring 107/111 thr 148 | cab-9F: 103 105 107 113 ring 104/108 thr 156
fan FAILED (c, passive) | cab=amb: 112 115 117 128 ring 111/118 thr 138 | cab-9F: 110 112 115 125 ring 109/116 thr 146
Qd 3.87 front 2.71 rear(GI) 0.25 ring 0.73 bezel 0.18 G_GTA 0.447
UB rear->cabinet air 3.1W/K 0 105 106 107 109 ring 105 107
UB rear->cabinet air 3.1W/K -5 98 98 99 101 ring 101 102
display own fins passive 1 W/K 0 107 109 110 115 ring 107 111
display own fins passive 1 W/K -5 102 103 104 110 ring 103 107
display own fins + fan 3 W/K 0 106 107 108 111 ring 106 108
display own fins + fan 3 W/K -5 99 100 101 104 ring 101 104
```

**Heat split, V6 at idle 25 % (MODELLED):** the display makes 3.87 W.
- 2.71 W leaves through the front glass.
- 0.73 W goes into the ring.
- 0.18 W goes into the bezel.
- Only 0.25 W (about 6 %) leaves through the rear, because the interior air is almost as warm as the display.

**What is on the display's back (from the datasheet):**
- The -B part is "N – Without Mounting Metal Frame" (DS Rev1.1 p.3).
- The edge-lit backlight has 48 LEDs (MEASURED). The datasheet text does not give the LED bar's position.
- The backlight cable exits at the top left (INFERRED from the drawing and our CAD notch). The source-PCB band and FPC are at the bottom (SRC_BAND in the CAD).
- The rear surface is the backlight tray, presumably sheet metal or plastic (INFERRED, not stated).

**Display module rear conductance:** about 3 W/K through the roughly 3 mm PMMA light guide (ESTIMATED).

**Upper bound for any rear spreader** (display rear tied through 3.1 W/K to a perfect sink at cabinet air): glass 105–109 F at cabinet air = ambient. That would need a dedicated sink below 0.3 K/W behind the PCB, which is not achievable passively.
- A dedicated passive 1 W/K display sink gives glass 107–115 F.
- Strapping the display to the V6 plate (which the CM5 warms) changes glass by −2 to +1 F. At cabinet air = ambient and low idle, it pushes heat the wrong way (glass +1 F).
- The display-to-PCB gap is now 11.44 mm (7.27 mm at the source band), so a sheet fits, but the strap must pass the PCB (BCR-9 slots or around the edges).

**Fan (ESTIMATED):**
- A 40 mm fan rated about 8 CFM free-air delivers about 3 CFM through the vents and PCB restriction. That is m·cp of about 1.7 W/K for the interior air.
- Inside surfaces: h about doubles (display rear 0.69 → 1.5 W/K). Fins in the airflow: 0.45 → 0.75 W/K.
- **Fan failure:** the unit falls back to passive V6 (glass 112–128 F, throttle above 138 F), so it stays safe. Firmware should read the tach on J4 and, on a fault, cap the backlight at 25 % and the CM5 power.
- A clogged filter behaves the same as a failed fan.
- Vents for the airflow open the rear shell to cabinet air; the front stays sealed by the panel gasket.
- Salt air in Hawaii: use an IP68 fan plus a washable filter, or accept a shorter life.
- **Phase 13 filters (both fans, PD2 basis):** washable open-cell foam, PPI not specified (ESTIMATED 30-45 PPI), ≤ 4.0 mm (CAD filter cover depth; ESTIMATED 3 mm foam), optional stainless/nylon mesh. Filter face ≈ 1600 mm² vs Ø38 hole 1134 mm² (MODELLED). Pressure drop ESTIMATED 5-15 Pa clean (~10-25 % flow loss, ESTIMATED). The fan conductances 2.2 / 1.3 / 0.20 W/K were ESTIMATED including filter restriction; no model change. Clean monthly at salt-air/dusty sites (recommendation, ESTIMATED). Spare: foam + PA12 snap cover, $8 / $6 for two (ESTIMATED). Removal: unclip the PA12 snap cover.
- **Conformal coating (board assembly requirement):** coat the HV section x < 73 behind the barrier (J28/J29/J30 area) per Compliance conformal_coating_spec.md (acrylic AR baseline, 30–75 µm dry, both sides, mating contacts and H1–H3 faces masked, UV-inspected). The coating is a humidity/salt-air/contamination mitigation that supports the PD2 decision together with the enclosure seal and washable fan filters. It is **not** qualified to IEC 60664-3 and **no clearance or creepage credit is taken**: all spacings remain per IEC 60664-1 (6.6 mm PD2 basic, 12.6 mm reinforced). Any future coating credit would need IEC 60664-3 qualification and Compliance/NRTL agreement, and would not reduce the 6.6 mm board rule. (PCB-assembly step outside enclosure scope.)

## Phase 9: V6 + TWO 40 mm fans, push-pull in series (Ethan GO, Oct 25). Data: thermal_dualfan_p9.json
CAD: 4.75 mm flat plate + ATS-EXL1 strip (x 157.2-258, y 1-178, fins vertical, base 2.0 / fin 8.0 / t 1.0 mm ASSUMED), exhaust fan centre (128, 26), intake fan (128, 152), both on the plate outer face in cabinet air with gasket + washable filter cover. Front stays sealed (panel gasket, flush glass).
Fan conductances are ESTIMATED: both 2.2 W/K interior flush, one failed 1.3 W/K (survivor pulls through the windmilling rotor, ~60 %), both failed 0.20 W/K (stalled rotors + filters restrict the passive path). Ta 104 F (40 C), CM5 4 W. Glass F at idle 10/25/40 %, alarm; ring at idle 25 / alarm; throttle ambient at idle 25 %; throttle ambient at CM5 8.5 W.
```
both fans  | cab=amb: 108 109 111 | 116 | ring 107/110 | thr 145 | 8.5W thr 110 ; cab-9F: 102 104 105 | 111 | ring 103/107 | thr 153 | 8.5W thr 119
one failed | cab=amb: 109 111 112 | 119 | ring 108/112 | thr 143 | 8.5W thr 107 ; cab-9F: 104 106 108 | 114 | ring 104/109 | thr 151 | 8.5W thr 115
both failed| cab=amb: 113 115 118 | 129 | ring 111/118 | thr 138 | 8.5W thr  98 ; cab-9F: 110 113 115 | 126 | ring 109/116 | thr 145 | 8.5W thr 106
```
Series vs parallel: in series one dead fan only adds rotor drag; in parallel the dead fan's opening becomes a short-circuit (backflow through the dead fan), so most of the survivor's flow recirculates. Series chosen.
Cabinet air temperature remains an ASSUMPTION to verify with a thermocouple during a full-load run.

## Phase 10 notes
- Fan final: Orion OD4010-05HB10A (5 V, standard) + washable filters; an IP/sealed fan is an OPTIONAL later swap (same envelope; thermal unchanged).
- TODO: EXL1 fin dims ASSUMED until the ATS drawing/sample; strip conductance carries that uncertainty.
- Fan control/derating per firmware/ARCHITECTURE.md section 11 (one fan failed: survivor 100 %, backlight cap 60 %; both failed: backlight 25 %).
- Compliance ruled (phase 9): rim trim OK as basic with a tested PE bond (PE_BOND.md), leads clipped to <= 1.0 mm (8.0 mm), PP film dropped (no thermal effect either way); +5V budget being checked by Layout/Firmware.

## Phase 15 notes
- Chimney slots (2 × 12, 4 × 12 mm, top/bottom walls) **deleted in CAD**: they were unfiltered inlets bypassing the fan filters (PD2). The phase-9 model did not credit them, so results are unchanged (INFERRED). The both-fans-failed case keeps 0.20 W/K (stalled rotors + filters).
- All wiring windows now have gasketed covers. **No positive pressure is claimed** (push-pull series, not computed). The PD2 basis is that every opening is filtered or sealed.


## Phase 23: PA12 front ring REMOVED, bare black-anodised 6061 bezel is the front (Ethan). Data: thermal_bare_bezel_p23.json
Model: `thermal_v3.py` `solve_p23` with nodes SoC, heat bar, glass, bezel, interior air and fin plate. Current design: V6 flat plate + EXL1 strip + two 40 mm fans in push-pull series, flush glass, bare bezel face to front air (h 9 W/m²K, ESTIMATED).
- Glass to bezel: 0.4 W/K (VHB tape plus the kept PA12 sleeve/bead, ESTIMATED).
- Fan conductances are ESTIMATED (phase 9: 2.2 / 1.3 / 0.20 W/K). With no heat into the bezel, the model reproduces the phase 9 numbers to within 1 F.
- Conditions: Ta 104 F (40 C), CM5 4 W, cabinet air = ambient (ASSUMPTION). Idle = 90 % idle + 10 % full backlight; alarm = continuous 100 %. No sun.
- **All results below are MODELLED**, about ±5 F on surfaces.

**New finding: the CAD still has the heat bar tab screwed (2x A2 M4, 0.5 mm pad) onto the bezel heat boss.** Phases 4-9 assumed this boss carries no heat. With a bare bezel that matters, so the as-CAD path is modelled at 2.75 K/W (ESTIMATED). The as-CAD row is the design as built.

| Case (as CAD) | Bezel face idle 10 / 25 / 40 % | Bezel face alarm | Glass idle 10 / 25 / 40 % | Glass alarm | Throttle ambient 4 W / 8.5 W |
|---|---|---|---|---|---|
| Both fans | 109 (42.7) / 109 (43.1) / 110 (43.4) | 113 (44.8) | 109 / 110 / 111 | 117 | 149 F (65.0 C) / 120 F (48.8 C) |
| One fan failed | 110 (43.2) / 111 (43.6) / 111 (44.1) | 114 (45.8) | 110 / 111 / 113 | 120 | 148 F (64.3 C) / 118 F (47.7 C) |
| Both failed | 113 (44.8) / 114 (45.6) / 115 (46.4) | 121 (49.4) | 114 / 116 / 119 | 129 | 144 F (62.1 C) / 112 F (44.3 C) |

**Comparison with phase 9 (both fans, ring):**
- Glass: was 108 / 109 / 111 F at idle and 116 F at alarm; now 109 / 110 / 111 and 117 (+0 to +1 F).
- Throttle ambient at 4 W: was 145 F, now 149 F (+4 F, because the bezel now also sinks CM5 heat).
- Cabinet air 9 F below ambient: bezel 104 / 105 / 105 F at idle, 108 F at alarm.

**Touch (source: /workspace/compliance/touch_temperature.md, read-only):**
- IEC/UL 61010-1 Table 19 at 40 C ambient: 55 C (131 F) for metal knobs and handles; 65 C (149 F) for an outer enclosure of uncoated or anodised metal.
- IEC 62368-1 TS1, metal held more than 1 min: 48 C (118.4 F), at a 25 C room.
- ISO 13732-1 burn thresholds for uncoated metal: 51 C (1 min), 48 C (10 min), 43 C (8 h).
- With fans running, the bezel is 109-114 F (43-46 C): under every limit above except the 8 h threshold. With both fans failed and the backlight at full, it reaches 121 F (49.4 C): over the 10 min burn threshold, under the 1 min threshold and under both 61010-1 limits.
- **Sun is not included.** Phase 4 put direct sun at +20-30 K on a black face, which would put a bare black bezel in direct sun well above all of these. A sun hood or shade is needed at sunny sites (same conclusion as before).

**Optional fix that keeps the bare look (NOT implemented):** replace the boss pad with 2 G10 1.5 mm spacer washers and use nylon M4 screws at the boss, so the heat bar is held but thermally isolated (about 50 K/W).
- Effect, both fans: bezel −2 to −3 F (106 / 107 / 108, alarm 111 F).
- Cost: throttle ambient 145 F (−4 F); both failed at alarm: 119 F (48.4 C).
- Cost about +$2 / +$1 (ESTIMATED).
- Not needed for the fans-running cases.
