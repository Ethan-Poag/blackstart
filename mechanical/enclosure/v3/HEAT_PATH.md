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
