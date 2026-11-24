# Firmware requirements: Batch 34 (P7) Q2 hold-off and U5 enable (m7-split-p7)

Status: requirement only, not implemented. Written Nov 24, 2026 (HST). Hardware: power.kicad_sch, Batch 34 (docs/SCHEMATIC_CHANGELOG.md). Same behaviour as m7-modular FW_REQ_CARDS C7.13.

## What the hardware now does
- **Slow Q2 turn-on.** R1001 1k + C601 22 nF on the LM74800 HGATE. VBAT_P now ramps in about 10–22 ms; it used to rise in well under 1 ms with 36–53 A of inrush.
- **Q2 hold-off.** When BAT_IN − VBAT_P > 2.5–3.8 V for ≥ 46–270 µs, D402 pulls down:
  - U2 EN/UVLO (BB_UVLO, C602 1 µF);
  - U5 EN (U5_EN).

  Both regulators stay off until Q2 has nearly finished its ramp. Typical triggers are the battery coming back after an interruption, and U1 recovering from UVLO or OV.
- **U5 enable.** U5 LMR36506 (+3V3_BK) EN is no longer tied to VBAT_P. It is a 100k / 47k divider: the regulator runs above VBAT_P 3.63–4.25 V and stops below about 2.5–3.3 V.

## Requirements
- **FW-P7-1 Supply-interruption resets.**
  - Battery interruptions longer than about 0.15–0.35 ms now always reset the controller. Before this change the cutoff was about 1–2 ms.
  - The reason: +3V3_SAFE (both U2's +3V3 and the U5 backup) drops while the hold-off is active.
  - On the reset that follows:
    - Apply the existing warm-reset rules: outputs start off and the U31 shunt bits are cleared first (FW-AI-3).
    - If the RTC/FRAM shows the previous session was running, log `SUPPLY_INTERRUPTION`.
  - Firmware cannot override the hold-off and must not try.
- **FW-P7-2 Restart timing.** After the hold-off releases:
  - U2 restarts 1.3–3.2 ms later at 32 V and 6.4–17 ms later at 9 V, then soft-starts over 7.5 ms.
  - +3V3_BK can come up first.
  - Boot code must not assume +12V or +5V is present when the MCU starts. This rule is unchanged, but the gap is now longer.
- **FW-P7-3 Battle short.** The hold-off is hardware (FW_REQ_BATTLESHORT §2, H8). Battle short cannot bypass it. After a hold-off reset, battle short state is restored by the D1/D2 persistence rules, as after any reset.

## Bench checks (BRINGUP_CHECKLIST)
1. Power up at 12 V and at 24 V:
   - VBAT_P ramps in ≥ 8 ms (scope).
   - BAT_IN inrush stays ≤ 1 A (current probe), apart from the C297/TVS edge.
2. With the controller running at 24 V, break BAT_IN for 1 ms and reconnect:
   - HO_K goes low within ≤ 0.3 ms.
   - BB_UVLO and U5_EN are ≤ 0.5 V.
   - The MCU resets.
   - Record the Q2 case temperature rise (thermocouple) against the model's ≤ 30 mJ for this case (docs/split_evidence/p7/p7_calc.txt).
3. VBAT_P slowly ramped from 0 V: U5 (+3V3_BK) starts at 3.6–4.3 V.
