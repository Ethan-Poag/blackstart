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
- Where it goes: into the LED bar, the module frame and the cover glass. The glass radiates and convects to the front. The module rear passes heat across the 3.27 mm air gap to the PCB. The module frame conducts into the bezel ledge.
- Other board loads:
  - SN65DSI83 ICC 77 mA typ at 1.8 V = 0.14 W (MEASURED, sn65dsi83.txt).
  - Backlight driver loss about 10 % of backlight power (ESTIMATED).
  - Other loads about 0.5 W (ESTIMATED).

### 2. Design D (recommended): heat goes to the back; the front becomes plastic
- **Rear fin plate.** 6061 base 242 x 177 x 4.75 mm (laser or waterjet), with 2 mm laser-cut fin slats at 8 mm pitch and 30 mm tall, bonded or pressed into milled slots. The plate is screwed to the 4 shell posts on the outside of the PA12 rear wall, which has a 235 x 172 opening under it. It sits behind the customer panel inside the cabinet, so it is not touched in normal use. It stays inside the shell outline, so the front-slide fit through the cutout is unchanged (checked: 1.0 mm/side). Fins are omitted around the J10/J11 plugs, and the plate is cut around the port tunnels. Total depth behind the bezel face becomes 82.75 mm (was 48). **The cabinet must allow this depth.**
- **Heat path.** A 6061 heat pillar (40 x 28 mm) runs from the CM5 heat bar to the fin plate. Chain: junction-to-case 2.0 + pad 0.2 + bar/pillar 0.8 + joint 0.3 = 3.3 K/W (ESTIMATED).
- **Thermal break at the front.**
  - Display mounted on the bezel ledge with foam VHB tape instead of metal contact (about 0.1 W/K, ESTIMATED).
  - A 3 mm SLS PA12 front ring covers all exposed metal of the bezel face, held off it by a 1 mm air gap on PA12 stand-off pips.
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
