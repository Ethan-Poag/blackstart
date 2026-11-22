# Firmware requirements from schematic Batch 30 (2026-11-22 HST)

Requirements only. Updated in Batch 31 (2026-11-22 HST) for the new hardware shunt-off gating and in Batch 32 (bench test, WD_OK timing, wording). No firmware exists on this branch and no firmware file was changed. The held overvoltage engine-shutdown change is not touched. Source: pass-4 review (/workspace/review/sch_review/SCH_REVIEW_2026-11-22_pass4.md, m3).

## Facts (netlist at Batch 31; the Batch 30 state is noted where it differs)
- **NRST** = U7.14, C65, J2.10 (SWD), SW1 (reset button), Q7 collector (CM5 GPIO22 CM5_NRST → R63 → Q7). Nothing else drives NRST.
- **WDO_N** (U37 TPS3431 pin 7) = R271 pull-up and U84.6 (~CLR) only. A TPS3431 timeout latches **WD_OK** (U84 Q) low. WD_OK gates U38/U39/U40/U67 (outputs) and, from Batch 31, U92 gate 3 (SH_ALLOW, the AI shunts) and is read on U76 P15. **The TPS3431 never resets the MCU.**
- **Shunt enables:** AI_SH_EN1–6 = U31 TCA9555 (@0x22, TSSOP-24) **P06, P07** (pins 10, 11, port 0) and **P10–P13** (pins 13–16, port 1) → gates of Q15/Q19/Q23/Q27/Q31/Q35, each with a 10k pull-down (R138/R149/R160/R171/R182/R193). At Batch 30 they were **not** gated by WD_OK. **Batch 31 adds hardware gating** (see the Batch 31 section below): the FET gates are now the new nets AI_SH_G1–6 = AI_SH_ENx AND SH_ALLOW.
- **U31 has no reset pin.** It keeps its output latches through an MCU reset. At power-on its pins are inputs, so the pull-downs hold every shunt **off**.

## FW-WDG-1: IWDG is mandatory (hard dependency of FW-AI-2)
1. Enable the IWDG in BOOT before any shunt can be enabled, and never stop it (ARCHITECTURE.md §4 item 1: LSI, ≈ 100–250 ms timeout, refreshed only from the main loop after every task has checked in). Prefer the hardware-start option byte (IWDG1_SW = 0) so the IWDG runs from reset [U RM0433: behaviour in the ROM bootloader].
2. Set DBGMCU so the IWDG is **not** frozen when the core is halted, except on a bench build flagged DEBUG. A DEBUG build must refuse to enable any shunt (the AI channels then read voltage mode only).
3. The IWDG timeout plus the boot-to-first-U31-write time must be **≤ 300 ms** in total. Measure it on the bench (reset with a shunt enabled, scope the Q15 gate).

## FW-AI-3: shunt default state on every reset
1. **First I2C action after every reset** (power-on, IWDG, NRST from the CM5, SWD, SW1, BOR): write U31 output port 0 bits 6–7 (P06/P07) and output port 1 bits 0–3 (P10–P13), i.e. all six AI_SH_EN bits, to **0** (keep the other bits at their safe defaults), then read both ports back. Only then continue boot. This is already FW-AI-2 item 4; it is restated here because it is the only thing that clears a shunt left on by the previous run.
2. Read RCC_RSR and log the reset cause to FRAM (ARCHITECTURE.md §4 item 4). If the cause was not a power-on reset and any AI_SH_EN bit read back as 1 before the clear, log `AI_SHUNT_HELD_THROUGH_RESET` with the channel mask.
3. **CM5 rule (CM5 software requirement):** before the CM5 asserts CM5_NRST or BOOT0 for a reflash, it must command the MCU to disable all shunts and wait for the acknowledgement. If the MCU does not answer, the CM5 may still reset it, but must hold NRST for **≤ 50 ms** per attempt and must not leave the MCU in the ROM bootloader longer than needed. Log every forced reset.
4. **SWD/bench rule (BRINGUP_CHECKLIST):** do not connect a 24 V sensor supply to any AI terminal while a debugger can halt or hold the MCU.

## Residual risk (Batch 30 text, superseded by Batch 31)
- Batch 30: while the MCU was **held in reset** (CM5 via Q7, SWD, SW1), **halted by a debugger**, or **sitting in the ROM bootloader**, U31 kept any enabled shunt on and nothing in hardware turned it off. With a miswired 24 V supply on that AI terminal the 100 Ω 0.5 W shunt (RT2010BKD07100RL) would dissipate 5.8 W (8.4 W at 29 V) until it failed open. **Batch 31 closes this in hardware** (below). What remains is listed under "Residual risk after Batch 31".

## Batch 31: hardware shunt-off gating (done, Ethan approved Nov 22, 2026 HST)
**Circuit (inputs sheet, main board, all on +3V3_SAFE):**
- **SH_ALLOW = WD_OK AND NRST** (U92 gate 3: pin 9 = WD_OK, pin 10 = NRST_S, pin 8 = SH_ALLOW). NRST reaches the gate through **U93**, a SN74LVC1G17 Schmitt buffer (NRST → NRST_S): NRST rises slowly (C65 100 nF with the MCU's ≈ 40k pull-up, a few ms), and an LVC08 input needs edges faster than 10 ns/V or its output can oscillate during the transition.
- **AI_SH_Gx = AI_SH_ENx AND SH_ALLOW** for x = 1–6: U91 gates 1–4 (AI_SH_EN1–4 → AI_SH_G1–4), U92 gates 1–2 (AI_SH_EN5–6 → AI_SH_G5–6). AI_SH_Gx drives the gate of Q15/Q19/Q23/Q27/Q31/Q35 (unchanged FETs).
- U92 gate 4 spare: inputs to GND, output not connected.
- Pull-downs both sides: R138/R149/R160/R171/R182/R193 (10k, unchanged) keep the U31-side AI_SH_ENx low while U31 pins are inputs; **RN1/RN2** (10k × 4 arrays, 6 elements used, 2 spare with both ends on GND) hold every FET gate low if U91/U92 are unpowered or an output floats. Default = shunt **off**.
- Parts: U91, U92 = Nexperia **74LVC08APW,118** (TSSOP-14, LCSC **C6053**, JLC extended, 12,517 in stock 2026-11-22 ~12:37 PM HST); C320, C321 = 100 nF 0603 YAGEO CC0603KRX7R9BB104 (**C14663**, basic); RN1, RN2 = UNI-ROYAL **4D03WGJ0103T5E** 10k × 4 0603 convex (**C29718**, basic, 1.27 M in stock); U93 = TI **SN74LVC1G17DBVR** (SOT-23-5, **C7836**, extended but already on the order as U85, JLC 2,322) with C322 100 nF (C14663). 8 parts, ≈ $0.41 per board + one JLC extended-part loading fee for C6053 ($3.07 per order).

**Behaviour:**
- **MCU held in reset** (CM5 via Q7, SWD, SW1): NRST low → NRST_S low → SH_ALLOW low → all six shunts off within two gate delays (< 20 ns), regardless of what U31 still latches.
- **Internal resets** (IWDG, software reset, BOR): the STM32 pulls NRST low for its internal reset pulse (≥ 20 µs). Whether that short pulse discharges C65 (100 nF) below U93's VT− (0.89–1.2 V) is **not guaranteed** by any datasheet figure (INFERRED: likely; check on the bench). Nothing relies on it: FW-AI-3 clears the shunt bits after every reset.
- **Watchdog trip** (TPS3431 timeout, ≈ 170–230 ms without PA12 kicks: firmware stuck, core halted by a debugger, MCU sitting in the ROM bootloader): WD_OK latches low → all six shunts off **until a power cycle**, the same latch that already disables the outputs.
- **Power-on:** WD_OK is low for the first **0.70–1.06 s typical, 0.40–1.35 s worst case** (POR RC R554 220k / C298 4.7 µF X7R 1206 / U85; ARCHITECTURE.md §13.7), so the shunts cannot turn on in that window even if firmware writes AI_SH_ENx = 1.
- **+3V3_SAFE down:** U31, U91, U92 unpowered, RN1/RN2 hold the gates low → off.
- **Reset release (not off):** U31 has no reset pin and keeps AI_SH_ENx = 1 through an MCU reset. When NRST rises past U93's VT+ (1.48–1.92 V), SH_ALLOW returns high (WD_OK is still high after a non-POR reset), so an enabled shunt **comes back on** and stays on until firmware's first U31 write (FW-AI-3 item 1). That pulse is bounded by FW-WDG-1 item 3 (≤ 300 ms) and is measured in the bench test below.

## Metering power-dip rule (Batch 31)
- The main 3.3 V dip / brownout rule for the meter board (supply fault, not "meter missing"; recheck, then latch only if it still fails) is **FW-MTR-9** in docs/FW_REQ_METERING_PRESENCE.md.

## FW-AI-4: firmware rules for the gated shunts (new, Batch 31)
1. While running, SH_ALLOW equals WD_OK (NRST is high whenever code runs). Read WD_OK on U76 P15. **While WD_OK is low, flag all six AI 4–20 mA channels INVALID** (not "open loop", not "0 mA"): show "AI shunts disabled by watchdog" on the CM5/UI, suppress 4–20 mA open-loop / under-range alarms, and never use those readings for protection or control. Resistive/voltage-mode AI channels are unaffected.
2. **Power-on:** do not judge any 4–20 mA channel until WD_OK has gone high (0.70–1.06 s typical, ≤ 1.35 s worst case after power-on; LATCHED if still low at 1.5 s, ARCHITECTURE.md §4 item 5) plus one settle period (≥ 50 ms). Writing AI_SH_ENx earlier is harmless but has no effect.
3. **After a TPS3431 trip** WD_OK stays low until power cycle: log `AI_SHUNTS_WD_LATCHED` once to FRAM, keep the channels INVALID, and tell the operator a power cycle is needed to restore 4–20 mA inputs (same message path as the outputs' WD_OK latch).
4. FW-AI-3 items 1–2 (clear all AI_SH_EN bits first after every reset) **still apply**: they stop a shunt coming back on by itself when SH_ALLOW returns, and they are the only protection while a debugger holds the core with the watchdog not yet expired.
5. FW-AI-2 over-range trip (> 25 mA → shunt off within 50 ms) is unchanged.

## Residual risk after Batch 31
- **First ≈ 170–230 ms of a hang or debugger halt**, before the TPS3431 times out: a shunt that was on stays on. With a 24 V miswire that is ≤ 0.23 s × 8.4 W ≈ 1.9 J in the 2010 resistor (≈ 4.5 × the 0.42 J of the FW-AI-2 50 ms case). Survival is not verified; the worst case is that the thin-film resistor fails open (two faults needed: a miswire plus a hang).
- **Stuck-high gate or shorted FET** (U91/U92 output stuck, Q15-type FET short): not covered, same as any single-part failure; FW-AI-2 over-range detection still flags it.
- **Bench DEBUG builds** with the IWDG frozen are still covered by the TPS3431 (it does not see the debugger), so a halted core loses the shunts after ≈ 230 ms. This is wanted.
- After a watchdog trip the 4–20 mA inputs stay off until power cycle (FW-AI-4 item 3). This is a deliberate fail-safe choice matching the outputs.
- **Reset-release pulse:** after any non-POR reset, a shunt that was on comes back on from NRST release until the first U31 write (≤ 300 ms by FW-WDG-1 item 3). With a 24 V miswire that is ≤ 0.3 s × 8.4 W ≈ 2.5 J, the same order as the hang case. Removing it would need an expander with a reset pin (e.g. TCA6416A) or a firmware arm bit; not done (small residual, needs a miswire too).

## Bench test (BRINGUP_CHECKLIST)
- With a shunt enabled and 10 mA flowing: hold SW1 → Q-gate (AI_SH_Gx) drops low immediately. **Release → AI_SH_Gx goes high again** (U31 still holds AI_SH_ENx = 1) and stays high until firmware's first U31 write, then low. Scope NRST and AI_SH_Gx and **measure the shunt-on pulse from NRST release (U93 output rising) to AI_SH_Gx falling**; it must be **≤ 300 ms** (FW-WDG-1 item 3). Repeat for an IWDG reset (stop refreshing in a test build) and a CM5_NRST pulse. Record the times in BRINGUP_CHECKLIST.
- Stop PA12 kicks (debug halt) → AI_SH_Gx low within ≈ 230 ms and stays low after resume until power cycle.
- Power-on: scope WD_OK and AI_SH_G1; G1 must stay low until WD_OK rises.
