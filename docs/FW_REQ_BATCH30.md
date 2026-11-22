# Firmware requirements from schematic Batch 30 (2026-11-22 HST)

Requirements only. No firmware exists on this branch and no firmware file was changed. The held overvoltage engine-shutdown change is not touched. Source: pass-4 review (/workspace/review/sch_review/SCH_REVIEW_2026-11-22_pass4.md, m3).

## Facts (netlist at Batch 30, unchanged since Batch 29)
- **NRST** = U7.14, C65, J2.10 (SWD), SW1 (reset button), Q7 collector (CM5 GPIO22 CM5_NRST → R63 → Q7). Nothing else drives NRST.
- **WDO_N** (U37 TPS3431 pin 7) = R271 pull-up and U84.6 (~CLR) only. A TPS3431 timeout latches **WD_OK** (U84 Q) low. WD_OK gates U38/U39/U40/U67 (outputs) and is read on U76 P15. **The TPS3431 never resets the MCU.**
- **Shunt enables:** AI_SH_EN1–6 = U31 TCA9555 (@0x22, TSSOP-24) **P06, P07** (pins 10, 11, port 0) and **P10–P13** (pins 13–16, port 1) → gates of Q15/Q19/Q23/Q27/Q31/Q35, each with a 10k pull-down (R138/R149/R160/R171/R182/R193). They are **not** gated by WD_OK.
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

## Residual risk (accepted for now, documented)
- While the MCU is **held in reset** (CM5 via Q7, SWD, SW1), **halted by a debugger**, or **sitting in the ROM bootloader**, U31 keeps any enabled shunt on. Nothing in hardware turns it off. If that AI terminal is also miswired to a 24 V supply, the 100 Ω 0.5 W shunt (RT2010BKD07100RL) dissipates 5.8 W (8.4 W at 29 V) until it fails open (thin film; seconds, INFERRED). The board near it may discolour. It needs two faults at once (a miswire plus a stuck/held MCU), so it is minor.
- The TPS3431 does time out in this case (≈ 170–230 ms with no kicks on PA12) and latches WD_OK low, but WD_OK does not reach the shunt gates.

## Hardware option (proposed only, not done in Batch 30)
- Gate the six AI_SH_EN lines with **WD_OK**, so a TPS3431 timeout (MCU stuck, held in reset, or in the bootloader) also drops every shunt within ≈ 230 ms. Cheapest clean form: two 74LVC08 quad AND gates (or six 74LVC1G08, the part already used at U38–U40/U67) between U31 P06/P07/P10–P13 and the FET gates; keep the 10k pull-downs on the gate side. About 8 parts, a few cents each, plus layout.
- Not done now: it is not a two-part change, it touches the AI front end that passed three reviews, and the layout is frozen anyway. Recommend it for the next layout if Ethan wants the extra margin.
