# Firmware requirements from schematic Batch 29 (2026-11-22 HST)

Requirements only. No firmware exists on this branch. Source: pass-3 review (/workspace/review/sch_review/SCH_REVIEW_2026-11-22_pass3.md, m3, m4, NOTE 5) and the Batch 29 schematic changes (DESIGN_NOTES.md "m7-split Batch 29").

## FW-AI-1: per-channel calibration of the 4–20 mA range (pass-3 m3)
- **Why:** the shunt FETs Q15/Q19/Q23/Q27/Q31/Q35 (IRLML0100) are driven from U31 TCA9555 at about 3.2 V. The datasheet only specifies RDS(on) at 4.5 V (235 mΩ max) and 10 V, and VGS(th) can be up to 2.5 V. At 3.2 V the FET resistance is unspecified: estimate 0.3–2 Ω, i.e. +0.3 … +2 % on the 100 Ω shunt (R137/R148/R159/R170/R181/R192, 0.1 %). The ADC measures the AI terminal node, so the reading is I × (R_shunt + RDS(on)).
- **Requirement:**
  1. Store a gain and an offset per AI channel (AI1–AI6) for the 4–20 mA mode in FRAM (U8 FM24CL64B, I2C1 0x50) with a CRC and a calibration date.
  2. Calibrate at production (and after any repair of Q15–Q35, R137–R192, the 100k/18k dividers or the ADS1115s): inject 4.000 mA and 20.000 mA (calibrator, ≤ 0.02 %) into each AI terminal with its shunt enabled, at room temperature, after ≥ 10 min warm-up. Solve gain/offset from the two points.
  3. Without valid calibration, use nominal 100.5 Ω and flag the channel UNCAL to the CM5 (alarm text, not a shutdown).
  4. Accuracy target after calibration: ±0.2 % of span at 25 °C. Residual drift over −40…+85 °C ≈ ±0.3 % (FET RDS(on) tempco on ~1 Ω, plus the shunt's 25 ppm/K); acceptable, no temperature compensation required.
  5. The voltage (0–10 V) and resistive modes may use the same calibration table with their own gain/offset entries (optional; their errors are set by the 0.1 % dividers and the excitation source, not by the FET).
- **Related (Batch 29):** COM_A/COM_B dividers R196–R199 are now 0.1 % too, so AINx − AIN3 cancels VMID without a fixed offset term. Use differential ADS1115 conversions AINx − AIN3.

## FW-AI-2: 4–20 mA shunt over-range trip (pass-3 m4)
- **Why:** a miswired 24 V sensor supply on an AI terminal with the shunt enabled puts 240 mA / 5.8 W (29 V: 8.4 W) into the 100 Ω shunt. Batch 29 moved the shunts to 0.5 W 2010 thin-film parts (RT2010BKD07100RL, C876535), which survive ≤ 50 ms pulses at this level; the firmware must cut the shunt quickly. A PTC was rejected because it would sit inside the measurement (DESIGN_NOTES Batch 29).
- **Requirement:**
  1. With a shunt enabled, sample that channel at least every 20 ms (ADS1115 at ≥ 475 SPS; with 3 channels per ADS1115 and I2C at 100 kHz this is ≈ 8 ms per round).
  2. If the terminal voltage exceeds **2.6 V** (≈ 25.9 mA; normal 4–20 mA reads ≤ 2.04 V, NAMUR fault high ≥ 21 mA reads ≤ 2.2 V) on **two consecutive samples**, write the U31 shunt-enable bit low immediately. Total latency from fault to shunt off: **≤ 50 ms**.
  3. Report AI_OVERRANGE for that channel. Re-enable automatically after 5 s. After **3 trips in 60 s**, latch the shunt off until operator reset (CM5 command or power cycle). The trip stays active in every engine state, including the CRANK/VBUS blanking windows of §13.10 (blanking hides readings, not this protection).
  4. Boot: the U31 outputs must be written low before the configuration register makes them outputs (ARCHITECTURE.md §13.1 step 4 already requires this). U31 keeps its output state through an MCU reset (no reset pin), so this write must be one of the first I2C actions after every reset, including watchdog resets.
  5. **Dependency (Batch 30):** this trip only works while firmware runs. IWDG is a hard dependency, and the MCU-held-in-reset case is covered by docs/FW_REQ_BATCH30.md FW-WDG-1 and FW-AI-3.
- **Bench:** apply 24 V through a 1 Ω sense resistor to AI1 with the shunt enabled; measure the time to shunt-off (≤ 50 ms), the retry pattern and the latch after 3 trips. Check R137 for discoloration after 10 trip cycles.

## FW-I2C-1: I2C1 at 100 kHz (pass-3 NOTE 5)
- **Why:** I2C1 has 2.2k pull-ups (R46/R47) to +3V3_SAFE and 12 devices plus header J3 (estimated 150–200 pF). Rise time ≈ 0.85 × 2.2k × C = 280–370 ns, above the 300 ns Fast-mode limit. Standard mode (100 kHz) allows 1000 ns.
- **Requirement:** run I2C1 at **100 kHz** (STM32H7 I2C_TIMINGR for 100 kHz Standard mode). Do not use 400 kHz unless the pull-ups are changed to 1.5k (0603WAF1501T5E, LCSC C22843, not confirmed) and the rise time is measured < 300 ns.
- **Budgets at 100 kHz (supersede the 400 kHz figures in ARCHITECTURE.md §11 / §13.17 / §13.18):** one TCA9555 register read or write ≈ 0.4–0.6 ms. Fan tach edge counting via TCA9555 at 167 edges/s ≈ 7–10 % bus load. The DI_BIAS self-test 25 ms window holds ≈ 40–60 transactions; the immediate P17 read (one transaction) and a six-expander attribution scan (≈ 2.4–3.6 ms) still fit. AI scan per FW-AI-2 ≈ 8 ms per ADS1115 round. FRAM writes: plan for ≈ 0.1 ms per byte.

## FW-ADE-1: ZMCT103C current channels (Batch 29, B1)
- T1–T4 are ZMCT103C window CTs (1000:1, rated 50 Ω, ±0.2 %, phase ≤ 15′ at 5 A / 50 Ω, linear 0–15 A). Burden 49.8 Ω (2 × 24.9 Ω 1 %).
- Scaling: 5 A secondary-side → 249 mV rms at the ADE9000 (PGA gain 1). ADE full scale 0.707 V rms ↔ **14.2 A**. Use gain 1.
- Calibrate per channel: xIGAIN (CT ratio ±0.2 % + burden 1 %) and xPHCAL (CT phase ≤ 0.25° + the 0.69° voltage/current RC mismatch at 60 Hz, pass-3 NOTE 17). Store with the AI table (FW-AI-1).
- CT polarity depends on how the pigtail was landed at J30. The commissioning wiring check (ARCHITECTURE.md §10.7) must detect negative active power per phase and offer a per-channel sign flip in the configuration, with an alarm until it is confirmed.
