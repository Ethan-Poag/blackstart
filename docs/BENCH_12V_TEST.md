# Bench test plan: 12 V LM5176 buck-boost (U2)

Source: the reviewer's analysis /workspace/review/c65/lm5176_compensation_analysis.md, lightly tidied.
Current compensation (**Batch 29**): R8 = **2.7k** (was 4.7k, before that 22.1k), C11 = 33n, C12 = **1n** (was 220p). Sections 1–12 below were written for 4.7k/220p; run them with the new values and use §B29 for the pass criteria and the TPS56637 tests.

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
- Do not run a sustained output short. MODE (R6 93.1k) sets CCM with hiccup ENABLED (LM5176 SNVSAI1D pin table p3: 93.1 kΩ = hiccup enabled; 200 kΩ or VCC = disabled). ISNS+/- are tied to +12V, so output-current limiting is not used. Under a short the controller cycles in hiccup, but each restart still drives peak current through Q3–Q6, L1 and the sense resistor, so a sustained short repeatedly stresses and heats parts. Keep any short test brief and current-limited at the bench supply.

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

## B29: Batch 29 bench tests (LM5176 compensation, TPS56637 output capacitance)
Why: pass-3 review m1/m2 (SCH_REVIEW_2026-11-22_pass3.md). All loop numbers are model estimates (LM5176 DS eq. 44, COUT(eff) ≈ 70 µF assumed); the bench is the proof.

**B29-1 LM5176 (U2, +12V), compensation 2.7k / 33n / 1n.**
- Expected (DS eq. 44, COUT(eff) 70 µF): boost Vin 6 V, 4 A: fc ≈ 6.7 kHz (limit fRHP/3 ≈ 8.5 kHz); Vin 9 V: ≈ 10 kHz (limit fsw/20 = 15 kHz); buck (12–30 V): ≈ 13 kHz. The c65 model figures above scale by about 2.7/4.7 = 0.57.
- Load step 0.37 ↔ 3.7 A at 1–2 A/µs (as step 5, full 12 V load) at **Vin 6, 9, 12, 24 and 30 V**. 6 V is the crank case (VBAT_P UV ≈ 5.5 V); keep the 6 V step short (thermal).
- Bode (if an FRA is available) at the same Vin, full load and 10 % load, injection as in step 2.
- **Pass:** deviation ≤ 5 % (600 mV); recovery < 1 ms; ≤ 2 ringing cycles; PM ≥ 45°, GM ≥ 10 dB at every Vin; measured fc at 6 V ≤ 8.5 kHz.
- **If it fails:** PM low at 6 V → R8 2.2k (0603WAF2201T5E C4190, already in the BOM), or fit C17/C18 bulk (step 10) and re-measure; slow recovery with good PM → R8 back toward 3.3k only if the 6 V case still passes. Record the effective COUT you infer from the ripple.

**B29-2 TPS56637 U3 (+5V) and U4 (+3V3), C29/C30/C36/C37 DNP.**
- Load steps: +5V 0.3 ↔ 2.5 A (CM5 + USB + fan class), +3V3 0.3 ↔ 2.5 A, 1 A/µs, at Vin (+12V) = 12 V. Measure at the far end too: +5V_CM5 (after TPS2121) and +3V3_SAFE (after TPS2116).
- Bode if possible (inject at the top of R16 / R23).
- **Pass:** deviation ≤ 3 % (150 mV on +5V, 100 mV on +3V3), no sustained ringing, PM ≥ 45°.
- **If undershoot is too large but PM is fine:** fit C29 (+5V) or C36 (+3V3) (22 µF 1206 C12891) one at a time and repeat; never refit both caps of a rail without a Bode plot (Table 4 maximum is 100 µF effective, our estimate with all fitted is 100–120 µF).
- **If it rings (PM low):** check that the feed-forward parts R18/C24 (+5V) and R25/C32 (+3V3) are fitted; then refit C30/C37 one at a time (more C lowers fc) and re-measure.
- Record the results in docs/split_evidence/ when measured.

## B30: meter board CT insulation and temperature (Batch 30, Safety review ZMCT103C_isolation.md)
**B30-1 Megger, every built meter board (production test, not just the prototype).** Pigtails fitted, board not powered, J31/J32 harness unplugged.
- **A:** all four CT pigtails shorted together (both ends) vs **GND_AC** (test pad; until the next layout adds one, use the GND_AC side of a burden resistor, e.g. R474/R475 common node, with a probe clip, not a solder blob). **1000 V DC, 60 s, ≥ 100 MΩ.**
- **B:** the same shorted pigtails vs **SELV GND** (J32 GND pin). **1000 V DC, 60 s, ≥ 100 MΩ.**
- Record both readings per board serial (docs/split_evidence/ or the build log). **Below 100 MΩ: the board must not be installed live.** Inspect the pigtail jacket in and near the window, then retest.
- 1000 V DC is well under the ZMCT103C's 4500 V datasheet withstand. Do not use an AC hi-pot on production boards.

**B30-2 Prototype temperature near T1-T4.** ZMCT103C limit **85 °C (185 °F)** (datasheet), lower than the wire's 105 °C (221 °F).
- In the closed enclosure at the worst ambient case of HEAT_PATH.md (104–122 °F), generator metering live (or 5 A injected on all four CT loops), CM5 at full load: log the board temperature next to each of T1-T4 (thermocouple taped to the board within 5 mm of the CT body) until stable (≥ 1 h).
- **Pass:** ≤ 158 °F (70 °C) at the CTs, which leaves 27 °F (15 °C) margin to the 185 °F limit. Above that, move the CTs away from the dividers/MOVs or improve the enclosure airflow before release.

## Sources
- Texas Instruments SNVSAI1D: LM5176 55-V wide-VIN synchronous 4-switch buck-boost controller datasheet.
- Infineon BSC070N10NS5 datasheet: OptiMOS 5 100 V N-channel power MOSFET (Q3–Q6).
- TDK SPM10065VT-4R7M-D datasheet: 4.7 uH SMD power inductor (L1).
- Compensation figures: /workspace/review/c65/lm5176_compensation_analysis.md (model estimates).
- Items marked "general practice" are not taken from a datasheet.

## Before any generator (GEN) AC connection
- **RV3 is not PCB-routed.** It must be wired with a 600 V insulated bodge wire, ≥0.5 mm², sleeved and tied down, ≥12.6 mm from SELV (see docs/ROUTING_PLAN.md §7.3). **Until it is wired, the GEN input has NO surge protection.**
