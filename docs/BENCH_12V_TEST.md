# Bench test plan: 12 V LM5176 buck-boost (U2)

Source: the reviewer's analysis /workspace/review/c65/lm5176_compensation_analysis.md, lightly tidied.
Current compensation: R8 = 4.7k (changed from 22.1k), C11 = 33n, C12 = 220p.

Assumptions (not measured):
- The 12 V load is about 3.7 A (ASSUMED).
- Ceramic DC-bias derating values are assumed.
- The compensation figures are model estimates. Only a Bode measurement confirms stability.
- C17 and C18 (470 uF) are connected to +12V in the schematic but are open (not routed) on this board.

**Safety and limits (apply to every step):**
- Power off and discharge the input and output capacitors before any rework, including lifting R9 or fitting the 20 Ω injection resistor.
- Isolate the loop analyser: inject only through an isolating injection transformer, and do not ground-reference the analyser to the injection point.
- Injection amplitude: start small, 10–20 mV at the injection point. Raise it only if the measurement is noisy, and keep the output perturbation well inside the ±5% band.
- Thermal limits (ASSUMED, check the part datasheets): stop if any part exceeds 212 °F (100 °C). Stop if U2's case surface exceeds 230 °F (110 °C): a surface reading is below the junction temperature, and 257 °F (125 °C) is the recommended maximum junction temperature, so the surface limit is set lower. Stop if L1 exceeds 230 °F (110 °C) or Q3–Q6 exceed 257 °F (125 °C).
- First power-up: set the bench-supply current limit to 0.5 A. Raise it only for the load steps.
- ESD (general practice): use a grounded wrist strap and mat when handling the board or reworking R9.
- Eye protection (general practice): wear safety glasses while powered, especially near the electrolytics and when soldering.
- Thermocouple placement (general practice): attach fine-gauge (e.g. type K) thermocouples with Kapton tape and a dab of thermal paste. Place them on the U2 package top, the Q3–Q6 package tops or drain tabs, the L1 body and the R12 body. Route the leads away from the SW nodes and log the ambient air separately.
- Do not run a sustained output short. MODE (R6 93.1k) disables hiccup and ISNS+/- are tied to +12V, so a short only heats parts.

**Expected loop figures (model estimates from the c65 compensation analysis, R8 = 4.7k, C11 33n, C12 220p; model uncertainty about ±1.5x on fc and ±10–15° on PM):**
- 8 V in (boost): crossover 3.7–12.9 kHz, PM 64–74° (A1 12.9 kHz/64°, A3 5.1 kHz/74°, C 3.7 kHz/72°).
- 12 V and 30 V in (buck): crossover 5.4–18.7 kHz, PM 72° or better (72–78° in the summary).

1. **Equipment:**
   - bench supply 0–35 V with a current limit;
   - electronic load with slew control (≥ 1 A/µs);
   - scope at 20 MHz bandwidth limit, probe with a tip-and-barrel ground spring at the output caps;
   - current probe (optional);
   - FRA or network analyser with an isolating injection transformer, if available;
   - thermocouple or thermal camera.
2. **Bode injection:** the board has no TP footprints near U2/FB. No board change: lift the +12V-side end of R9 (140k) and bridge the gap with a 20 Ω 0603 resistor on this build. Inject across the 20 Ω, measuring A at the R9 side and R at the +12V side.
3. **First power-up:**
   - Vin 8 V, no load, with the supply current limit set to 0.5 A (see Safety);
   - confirm 12.0 V ±2%, soft-start without overshoot, PGOOD high, and output ripple;
   - then ramp Vin to 12 V and 30 V.
4. **Load ramp:** at 8 V, ramp the load 0 → 3.7 A in 0.5 A steps. Watch the supply current, SW1/SW2 jitter, and any pulse skipping.
5. **Step load:** step 0.37 ↔ 3.33 A at 1–2 A/µs, at Vin 8, 12 and 30 V. Record:
   - over- and undershoot in mV;
   - recovery time;
   - number of ringing cycles and the ringing frequency. Compare it with the estimated fc (model estimate 3–13 kHz with R8 = 4.7k) and with any high-frequency path resonance.
6. **Mode transition:** sweep Vin slowly from 10 to 14 V at 3.7 A. Look for buck/boost chatter, sub-harmonics, and audible noise.
7. **Ripple:** measure output and input ripple at 8 V, full load.
8. **Bode (if an FRA is available):** 8 V and 30 V, at full load and at 10% load.
9. **Pass/fail (ASSUMED):** deviation < 5% (600 mV) on the step; ≤ 2 ringing cycles with no sustained ringing; PM ≥ 45° and GM ≥ 10 dB; ripple < 1% of Vout.
10. **C17/C18:** temporarily wire them to the +12V rail and to GND near Q6. Repeat steps 5 and 8, and record the change in undershoot and PM.
11. **Thermal:** run 30 min at 8 V, 3.7 A. Record L1, R12, Q3–Q6 and U2 temperatures in °F, and the ambient in °F.
12. **If it fails:**
    - low PM or ringing near fc: R8 is already 4.7k; reduce it further only per the analysis, and raise C11 if you see low-frequency overshoot;
    - ringing well above fc: add local ceramics near Q6 or connect bulk;
    - re-test after each change.

## Sources
- Texas Instruments SNVSAI1D: LM5176 55-V wide-VIN synchronous 4-switch buck-boost controller datasheet.
- Infineon BSC070N10NS5 datasheet: OptiMOS 5 100 V N-channel power MOSFET (Q3–Q6).
- TDK SPM10065VT-4R7M-D datasheet: 4.7 uH SMD power inductor (L1).
- Compensation figures: /workspace/review/c65/lm5176_compensation_analysis.md (model estimates).
- Items marked "general practice" are not taken from a datasheet.
