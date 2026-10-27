# Bench test plan: 12 V LM5176 buck-boost (U2)

Source: the reviewer's analysis /workspace/review/c65/lm5176_compensation_analysis.md, lightly tidied.
Current compensation: R8 = 4.7k (changed from 22.1k), C11 = 33n, C12 = 220p.

Assumptions (all inferred, not measured):
- The 12 V load is about 3.7 A.
- Ceramic DC-bias derating values are assumed.
- The compensation figures are model estimates. Only a Bode measurement confirms stability.
- C17 and C18 (470 uF) are unconnected on this board by design.

1. **Equipment:**
   - bench supply 0–35 V with a current limit;
   - electronic load with slew control (≥ 1 A/µs);
   - scope at 20 MHz bandwidth limit, probe with a tip-and-barrel ground spring at the output caps;
   - current probe (optional);
   - FRA or network analyser with an isolating injection transformer, if available;
   - thermocouple or thermal camera.
2. **Bode injection:** the board has no TP footprints near U2/FB, which I checked. No board change: lift the +12V-side end of R9 (140k) and bridge the gap with a 20 Ω 0603 resistor on this build. Inject across the 20 Ω, measuring A at the R9 side and R at the +12V side.
3. **First power-up:**
   - supply limit 0.5 A, Vin 8 V, no load;
   - confirm 12.0 V ±2%, soft-start without overshoot, PGOOD high, and output ripple;
   - then ramp Vin to 12 V and 30 V.
4. **Load ramp:** at 8 V, ramp the load 0 → 3.7 A in 0.5 A steps. Watch the supply current, SW1/SW2 jitter, and any pulse skipping.
5. **Step load:** step 0.37 ↔ 3.33 A at 1–2 A/µs, at Vin 8, 12 and 30 V. Record:
   - over- and undershoot in mV;
   - recovery time;
   - number of ringing cycles and the ringing frequency. Compare it with the estimated fc (model estimate 3–13 kHz with R8 = 4.7k) and with any high-frequency path resonance.
6. **Mode transition:** sweep Vin slowly from 10 to 14 V at 3.7 A. Look for buck/boost chatter, sub-harmonics, and audible noise.
7. **Faults:** UVLO turn-on and turn-off thresholds; short-circuit hiccup and recovery; start-up into full load at 8 V.
8. **Ripple:** measure output and input ripple at 8 V, full load.
9. **Bode (if an FRA is available):** 8 V and 30 V, at full load and at 10% load.
10. **Pass/fail (ASSUMED):** deviation < 5% (600 mV) on the step; ≤ 2 ringing cycles with no sustained ringing; PM ≥ 45° and GM ≥ 10 dB; ripple < 1% of Vout.
11. **C17/C18:** temporarily wire them to the +12V rail and to GND near Q6. Repeat steps 5 and 9, and record the change in undershoot and PM.
12. **Thermal:** run 30 min at 8 V, 3.7 A. Record L1, R12, Q3–Q6 and U2 temperatures in °F, and the ambient in °F.
13. **If it fails:**
    - low PM or ringing near fc: R8 is already 4.7k; reduce it further only per the analysis, and raise C11 if you see low-frequency overshoot;
    - ringing well above fc: add local ceramics near Q6 or connect bulk;
    - re-test after each change.
