# Firmware requirements: swappable cards (M-mod P3, branch m7-modular)

Status: requirements only. Nothing is implemented. Source: `docs/MODULAR_ARCHITECTURE.md` §3 and §9. Written Nov 23, 2026, HST. Updated Nov 23, 2026, HST, for the Pass 1 review fixes (`/workspace/review/modular_pass1.md`): C2.3, C4.3, C5.1, C6 and the new C7. Updated again Nov 23, 2026, HST, for the Pass 2 review fixes (`/workspace/review/modular_pass2.md`): C2.3, C2.5, C5.1, C5.4, C6.2, C7.3-C7.5 and the new C7.7-C7.12. The numbers come from `docs/modular/tools/pass2_calc.py` (output in `docs/modular/pass2_calc.txt`). Updated again Nov 23, 2026, HST, for the Pass 4 review fixes (`/workspace/review/modular_pass4.md`): C2.3 (TDRV_EN), C5.1, C5.4, C6.2 (multi-channel rule) and C7.9; numbers from `docs/modular/tools/pass4_calc.py` (`docs/modular/pass4_calc.txt`). Updated again Nov 23, 2026, HST, for Pass 5 (Ethan: slot switches become TPS16630 eFuses, no per-slot blade fuse): C2.3, C5.1, C5.4, C6.2 2a, C7.9; numbers from `docs/modular/tools/pass5_calc.py` (`docs/modular/pass5_calc.txt`) and `kick_calc.txt`.

## C1 Card identification
- C1.1 Every card has an AT24CS32 ID EEPROM at 0x50, reached through its own TCA9548A channel. There are 2 muxes, at 0x70 and 0x71: 8 LV slots + engine + HV. The bus is the slot I2C bus on I2C2 (PB10/PB11), never the FRAM/ADS1115 bus on I2C1.
- C1.2 The card serial is the 128-bit factory serial at 0x58, which is read-only. Firmware never writes a serial.
- C1.3 Header in EEPROM page 0, CRC-16 protected:
  - magic
  - format version
  - card type: 0x0001 ENGINE, 0x0010 DI-8, 0x0011 AI-4, 0x0012 HSO-5, 0x0013 BRK-4, 0x0020 HV-METER
  - hardware revision
  - channel count
  - calibration block offset + CRC
- C1.4 Writes are allowed only while stopped, from the config suite. Firmware drives PB6 (ID_WP_UNLOCK) high, which turns on the AO3400A that pulls ID_WP low for every LV slot and the engine card. PB6 has a 100k pull-down, so ID_WP is high (protected) at reset and whenever the MCU is not driving it. Drive PB6 low again straight after the write and read back.

## C2 Boot and auto-configuration
- C2.1 At boot every LV slot is unpowered and every output is off. OUT_EN_N is high, from the card pull-up on +3V3_ID and from the gate below.
- C2.2 Read PRESENT_N, then each EEPROM, then compare with the commissioned map in FRAM: slot → type + serial, CRC, A/B copies.
- C2.3 Matching card: power the slot, run the self-test (outputs-off readback, DI bias test), then enable. The hardware output enable is:
  - `SLn_OUT_EN_N = NAND(PWR_EN, GLOBAL_OUT_ALLOW, NOT SLn_ARM_N)`, built from a 74LVC1G04 and a 74LVC1G10 per slot.
  - `PWR_EN = NOT SLn_EN_N AND NOT SLn_PRESENT_N` (74LVC1G02).
  - `GLOBAL_OUT_ALLOW = WD_OK AND NRST_S AND SLOT_RST_N` (U92 gate 4 on SH_ALLOW).
  - `SLn_ARM_N` is on 0x21 port 1 with a 10k pull-up. Expander reset or input mode = disarmed.

  | PWR_EN | GLOBAL_OUT_ALLOW | ARM_N | OUT_EN_N | Card outputs |
  |---|---|---|---|---|
  | 0 | x | x | 1 | off |
  | x | 0 | x | 1 | off |
  | x | x | 1 | 1 | off |
  | 1 | 1 | 0 | 0 | enabled (the card MCP23S17 REQ bits still decide each output) |

  Boot rule (Pass 2 m2), before SLOT_RST_N is released for the first time:
  1. Write U107 (0x21) port 1 output register = 0xFF (every SLn_ARM_N high), then set port 1 to outputs.
  2. Read back the U106 (0x20), U107 (0x21) and U108 (0x22) configuration and output registers. Port 1 of 0x21 must read 0xFF, every EN_N must be high, BANK_EN low, BANK_OVL_ROOM low.
  3. Only then release SLOT_RST_N. On any mismatch: `SLOT_EXP_FAULT`, slots stay off, no start.

  Cold-start setup must not assume that an MCU reset reset the expanders. On **every warm reset** (Pass 3 N7), hold SLOT_RST_N low / GLOBAL_OUT_ALLOW low and SLOT_CS_EN low; write ARM_N = 0xFF first, EN_N = 0xFF, BANK_EN = 0, BANK_OVL_ROOM = 0; configure those pins as outputs and verify their readback. The expander registers can survive NRST, so overwrite them even when their IODIR bits already say output. Clear card REQ state only after powering it with ARM_N high; never briefly re-arm old requests. A failure keeps the system disarmed, `SLOT_EXP_FAULT`, no start.

  Enable order (cold or warm):
  1. Finish the expander safe-state/readback checks above. BANK_EN high only with every EN_N and ARM_N high.
  2. SLn_EN_N low, one slot at a time (C7.9). Mask PWR_FAULT_N while bank off/ramping or slot off/ramping (C5.1).
  3. **Pass 4 m4 (TDRV_EN):** FLT stays low until each controller's charge pump has charged C_BST (2.2 µF) to BST_UVLOR: TDRV_EN = C_BST × 9.93 V / 190 µA = **126 ms worst** (57 ms typical). It applies to the bank after BANK_EN and to the first slot enabled after a bank (re)start. Treat BANK_FAULT_N / SLn_PWR_FAULT_N low as "charging", not a short, for the first **150 ms**; then require it high continuously for 10 ms. Timeout **250 ms** -> cut that slot (or the bank), `SLOT_SHORT_LOCKOUT`; do not keep retrying. (Was 20 ms / 10 ms / 100 ms.) **Pass 5:** the 126 ms TDRV_EN now applies to the bank (U110) only. A slot eFuse holds SLn_PWR_FAULT_N low after PWR_EN until PGOOD rises: ≤ 1.9 ms turn-on delay + ≤ 8.4 ms dVdT ramp + ≤ 13 ms deglitch ≈ **24 ms worst**; keep the same 150 / 10 / 250 ms window (it covers both). Enabling into a shorted card leaves PGOOD low (eFuse thermal regulation), so the 250 ms timeout gives `SLOT_SHORT_LOCKOUT` well before the eFuse's own 1.1–1.5 s latch.
  4. Release SLOT_RST_N only after the safe-state verification. This releases MCP reset but not hardware ARM_N.
  5. Configure the powered card MCP23S17: IOCON.ODR = 0, all REQ bits 0, unused GPIO inputs with GPPU = 1. Read back and self-test outputs-off.
  6. Drive that slot's ARM_N low only after its configured protection functions and valid readings are ready.

  To disarm: ARM_N high, REQ = 0 only if still powered, EN_N high. Do not use SPI once unpowered.
- C2.4 Same type with a new serial (a replaced card):
  - power it and self-test it;
  - load calibration from the card;
  - show "Card replaced: slot n";
  - **block the next start until the operator acknowledges at the panel.**
- C2.5 Missing card, wrong type, unknown type, bad CRC, failed self-test or over power budget: the slot stays unpowered and `CARD_FAULT(slot)` is raised. Then:
  - If the card carries a protection-class function: **no start**.
  - Otherwise: alarm only.
  - **+3V3 lost while running (Pass 2 m8).** The slot +3V3 comes from main +3V3 through the TPS2553s, so PSU_MAIN_OK low takes every LV card's logic down at once (outputs fail off; DI/AI readings become invalid). Firmware raises `PSU_MAIN_FAULT` at once and runs a controlled shutdown on the safety core, which stays on +3V3_SAFE: FUEL_EN = 0 within 1 s (no cool-down), ARM_N high and EN_N high on every slot. BRK-4 cannot be commanded while its +3V3_SLOT is gone. The ESTOP_TRIP path stays on the mainboard and is unaffected. Restart needs PSU_MAIN_OK and an acknowledgment.
- C2.6 Uncommissioned slot with a card in it: show a "new card" notice. Its channels stay unmapped until they are assigned in the config suite.
- C2.7 The channel map is `logical function → (slot, channel)`. It can only be edited while stopped, and is validated against SAFE_MAX.

## C3 Engine card (dedicated keyed slot)
- C3.1 The engine card is mandatory. If ENG_PRESENT_N is high, or the EEPROM type is not 0x0001, then:
  - `ENGINE_CARD_MISSING` is raised;
  - IDLE → PREHEAT is refused;
  - FUEL_EN, CRANK_EN and GLOW_EN are held at 0.
  - The hardware fails safe anyway: no card = no fuel driver.
- C3.2 Engine card lost while running (PRESENT edge, ID read failure, readback mismatch): shutdown on the existing fault path. FUEL_EN = 0 and GCB open. Restart needs a power cycle and an acknowledgment.
- C3.3 Engine card replaced:
  - C2.4 applies (acknowledgment before the next start).
  - Then a forced self-test: fuel/crank/glow outputs-off readback (FUEL/CRANK/GLOW_RB_N), MPU/D+ input sanity, and a DI_BIAS_A test.
- C3.4 Glow is now fed from VBAT_ESTOP, so an E-stop removes glow too. Firmware must not report that as a glow-driver fault while ESTOP_OK = 0.

- C3.5 **Engine slot feeds (Pass 6 M3, MOD §19.3).** J48 +3V3 comes through U160 TPS2553 (110–150 mA, auto-retry) and J48 VBAT_P through U161 TPS16630 (0.54–0.66 A, auto-retry every 648 ms after a thermal trip). Their FAULT/FLT#/PGOOD are wired-OR onto **ENG_PWR_FAULT_N = 0x22 P15** (input, 10k pull-up). Low while running = engine card supply fault: treat as C3.2 (engine card lost) and shut down on the existing path; do not wait for the auto-retry. At boot, mask it until VBAT_P ≥ 6 V and 20 ms after U161 has ramped (dVdT 10 nF: ~7 ms at 32 V); PGOOD is also low below the 5.64 V UVLO, so a deep crank dip pulls it low: classify like C7.9 (crank window) before declaring a fault. The engine lines to U7 now have series resistors (10k on FUEL_ISNS, CRANK_ISNS, MPU_GATE, MPU_SPEED, DPLUS_EXC_EN, DIAG_EN; 1k on DPLUS_SNS) and 1 nF at the FUEL/CRANK_ISNS pins: on PA2/PA3 (FUEL/CRANK_ISNS, 1 nF at the pin) convert twice back-to-back and use the second result, or use a sample time ≥ 810.5 cycles (Pass 7 m1: one conversion otherwise carries ≤ 0.42 % of the previous channel's voltage); use ≥ 64.5 cycles on DPLUS_SNS, and allow ±20 mV hot clamp leakage error on the ISNS lines.

## C4 Card swap acknowledgment (UI)
- C4.1 The acknowledgment screen shows: slot, old type/serial, new type/serial, and the calibration source (card or default).
- C4.2 The acknowledgment is logged with an RTC time, in FRAM and on the CM5.
- C4.3 An HV card with blank or bad calibration raises `METERING_UNCALIBRATED`. Breaker close stays blocked until it is calibrated. The J31/J32 harness has no spare pin, so the HV meter ID EEPROM WP is not on PB6. It is written only on the bench, with the meter TP3 pad grounded (`docs/INSTALL_SAFETY.md`). Firmware refuses an HV meter calibration write in the field and tells the operator to use the bench procedure.

## C5 Running faults
- C5.1 Any card: PRESENT edge, SLn_PWR_FAULT_N, SLn_CARD_FAULT_N or SPI/CRC failure.
  - PRESENT high removes PWR_EN in hardware (74LVC1G02).
  - **Pass 5: each slot switch is a TPS16630 eFuse** (TI SLVSET9G; no per-slot fuse, Ethan 2026-11-23). R_ILIM 4.02k: current limit **4.19/4.50/4.82 A** (4.14–4.86 A with the 1 % resistor). Hard short: fast-trip at 2 × I_OL / 45 A, FET off in 1 µs typ (soft short 2.2–4.5 µs), then it regulates at I_OL; **FLT# low after 1.09–1.6 ms** in current limit; thermal shutdown (ms at 32 V) or **129–202 ms** in current limit → **latched off** (MODE open). Start into a short: thermal regulation 277–309 °F (136–154 °C) for 1.1–1.5 s, then latched off. OVP cut-off **53.4/55.6/57.8 V** (453k/10k, auto-on below 49.5–53.9 V); UVLO 5.64 V on / 5.28 V off (unchanged divider). SHDN# = SLn_PWR_EN (10k pull-down: off if the 1G02 is unpowered).
  - **SLn_PWR_FAULT_N wiring (Pass 2 m10, Pass 5):** eFuse FLT#, eFuse **PGOOD** and the TPS2553 FAULT are open drain, wired-OR onto SLn_PWR_FAULT_N with one 10k pull-up to +3V3_SAFE. Low means: slot off (PGOOD is low whenever SHDN# is low — masked, below), eFuse in current limit / latched / thermal, OVP, UVLO, ILIM pin fault, PGOOD not yet up after enable (rising deglitch 8–13 ms; line high ≤ 24 ms after PWR_EN), +3V3_SLOT overcurrent/overtemperature, or TPS2553 **reverse voltage** (VOUT exceeds VIN by 95–190 mV; FAULT deglitch 2–7 ms). Firmware cannot tell which from the line alone. **OVP/UVLO hit all slots at once:** if two or more slots go low within one scan, or INA237 VBAT_P > 50 V or < 6 V, classify as a supply event (C7.9), not eight CARD_FAULTs. IMON (15k, 0.42 V/A) is a bench test point only; there is no slot-current ADC.
  - **Pass 5 review m3 (latch release without firmware):** the eFuse latch also clears when its UVLO goes low and high again (VBAT_SLOTS below 5.05–5.50 V, e.g. a deep crank dip or a bank off/on). Firmware must therefore hold EN_N high on any slot that reported a fault (that keeps SHDN# low, so a UVLO release cannot re-enable it). With firmware dead, a shorted card gets one hardware retry per deep dip: it is limited to 4.86 A and re-latches by TSD or within 1.5 s; the bank and F1 are not involved.
  - **Pass 6 M2 (fixed, MOD §19.2): R_ILIM 3.09k, eFuse I_OL 5.36–6.30 A.** A shorted HSO-5/BRK-4 channel (≤ 3.61 A, TPS1HTC30 limit) now leaves 1.75 A for the rest of its card before the eFuse limits, so a channel short is handled by the channel rule (C6.2) and the card stays up. If the card's total does exceed I_OL, FLT# falls in 1.09–1.6 ms and the rule below cuts the card; the bank overload cannot trip before 29.9 ms (ROOM) / 31.7 ms (HOT), so cutting the card within 20 ms keeps the other slots up.
  - **Pass 3 N8 masking:** mark SLn_PWR_FAULT_N invalid while BANK_EN = 0, bank UVLO/off/ramping, or SLn_EN_N = 1 / slot ramping. Keep ARM_N high in that window. After bank/slot on, apply the C2.3 step 3 window (150 ms charging mask, then 10 ms high) before arming; a persistent low ends the attempt in `SLOT_SHORT_LOCKOUT`, not an endless mask. A falling bank fault immediately starts C7.9; do not latch all eight card faults from the consequent lows.
  - **Rule:** any SLn_PWR_FAULT_N low immediately drives that slot's ARM_N high and EN_N high (PWR_EN off), then raises CARD_FAULT(slot), unless C7.9 classifies it as a supply dip.
  - SLn_CARD_FAULT_N is read on 0x22 port 0. Firmware drops the slot itself (EN_N high, ARM_N high).
  - Firmware then applies C2.5's protection-class rule.
  - Re-arm a latched slot only after the operator acknowledges and removes the fault: EN_N high for at least 20 ms (SHDN# low resets the eFuse latch; 20 ms also lets PGOOD and the dVdT cap reset), then C2.3. No automatic retry into a latched eFuse.
- C5.4 Slot bank limiter and bank overload cutoff (Pass 3 MAJ-A/N1/N3). One TPS48100 (U110) feeds VBAT_SLOTS to all 8 LV slots.
  - SCP: **21.2/28.6/36.3 A**, latch-off 466–1490 µs (68 nF + 100k; 466 µs includes −10 % temperature). Pass 5: a slot short is cut by its eFuse in ≈1–4.5 µs and then held at ≤ 4.86 A, so the bank SCP (466 µs minimum) never trips on a card fault (> 100× timing margin) and current grading is no longer needed. Residual: a short on VBAT_SLOTS itself (mainboard bus) is still cleared by F1/U110 (pass4_calc.txt).
  - Overload hardware: INA281A2 on the **bank** shunt -> 15.8k / 2×10 µF filter -> TLV3012B -> 74LVC1G74 latch -> AO3400A pulls BANK_UVLO low. ROOM adds 25.5k to ground through a TS5A3166.
    - HOT default: **3.15–3.76 A**, tau 316 ms. ROOM: **5.11–6.08 A**, tau 195 ms.
    - Use **t = tau·ln((I−I0)/(I−Ith))**, where I0 is the settled pre-fault preload, not zero. The INA281 saturates at ~19 A equivalent. With 2.4/4.0 A preloaded, +3.61 A channel fault: earliest hardware trip 58.4/56.6 ms. Firmware must isolate the channel <=25 ms (C6.2).
  - BANK_EN = 0x22 P11 (10k pull-down), BANK_FAULT_N = P12 (SCP/UVLO/overload cutoff), BANK_OVL_ROOM = P13, BANK_OVL_N = P14 (low = overload latch set). BANK_EN low resets the latch. +5V_TRIP POR/brownout sets the TLV3012B output low for up to 1.9 ms and fails the bank off.
  - **ROOM only** with valid U83, F1 state ROOM (<=77 °F estimate), **VBAT_P >=12.4 V**. Below this, or with U83 invalid: HOT. On leaving ROOM, disarm/cut enough outputs or slots to the 2.4 A budget first; if the fault cannot be assigned safely, cut the whole bank. Do not infer bank current by subtracting a fixed base from INA237: converter draw varies.
  - **No per-slot shunt or aggregate slot-current ADC exists.** Pass 5: each eFuse limits its slot to 4.14–4.86 A and flags it on SLn_PWR_FAULT_N within 1.6 ms, so a slot drawing more than its limit is now located selectively (that slot's FLT#); an overload below the limit but above the bank budget is still bank-wide. BANK_IMON feeds only the analogue comparator, not an MCU ADC. HSO/BRK SNS is per-channel and multiplexed; DI/AI currents are declared estimates. The INA237 measures the whole F1 chain, not an individual slot. Firmware can enforce declared budgets and channel SNS faults; it cannot locate an overload that stays below every eFuse limit (for example two slots at 2.5 A each in HOT). An unassignable overload is deliberately a **bank-wide** shutdown, `SLOT_BANK_OVERLOAD`. Do not claim selective containment for it.
  - Bank trip: disarm and turn every slot off, then C7.9. No start / stop if protection-class readings are lost (C2.5). Wait >=3 s before clearing BANK_EN (filter decay), low >=20 ms. One classified crank-dip exception is permitted by C7.9; otherwise operator acknowledgment required.
  - INA237 chain tiers remain fuse-level backup, not a substitute for C6.2.
- C5.2 A missing BRK-4 blocks every breaker close. It never opens a closed breaker by itself. ESTOP_TRIP stays on the mainboard.
- C5.3 Cards are re-enumerated only after a power cycle. There is no hot-plug.

## C6 LV card register maps (MCP23S17 on the slot SPI chip select; ADS1115 / EEPROM on the slot I2C channel)
- **DI-8 (0x0010):**
  - GPA0-7 = IN1_N..IN8_N.
  - GPB0 BIAS_ON (out), GPB1 BIAS_DISCH (out), GPB2-3 unused (NC: leave as inputs, GPPU = 1), GPB4-7 SLOT_ID0-2/IDP (in, pull-ups on). The card fault (TPS26621 FLT) is read on the mainboard 0x22 port 0, not through the MCP23S17. The MCP is unpowered while the slot is off, so it must not see a pulled-up line.
  - Debounce in firmware, as today.
- **AI-4 (0x0011):**
  - GPA0-3 CS_DIS1-4 (out, 1 = current source OFF; 47k pull-ups keep it off while the MCP is in reset), GPA4-7 SH_EN1-4 (out, 47k pull-downs: shunt open at reset); GPB0-3 SLOT_ID0-2/IDP; GPB4-7 unused (NC, GPPU = 1).
  - ADS1115 at 0x48: AIN0-3 = IN1-4.
  - The 4-20 mA shunt only closes while the backplane drives OUT_EN_N low.
- **HSO-5 (0x0012):**
  - GPA0-4 OUT1-5_REQ, GPA5 DIAG_EN, GPA6-7 SLOT_ID0/1; GPB0-4 OUT1-5_RB_N, GPB5-7 MUX_A0-2.
  - Current: select MUX_A, then read ANA_OUT through the backplane ADC mux (see C7.3).
  - REQ, DIAG_EN and MUX_A have 47k pull-downs, so they stay low while the MCP is reset or Hi-Z.
- **BRK-4 (0x0013):**
  - GPA0-3 OUT1-4_REQ, GPA4 DIAG_EN, GPA5-7 SLOT_ID0-2; GPB0-3 OUT1-4_RB_N, GPB4-6 MUX_A0-2, GPB7 SLOT_IDP. Same 47k pull-downs as HSO-5.
  - Channel current limit: 2.41 A min / 3.01 A typ / 3.61 A max (ILIM 33.2k), the same on HSO-5 and BRK-4. Firmware `aux_out_limit_A` stays 2.0 A.
  - **Every GCB/MCB trip, close and motor-operator coil is switched through an external interposing relay (Pass 2 MAJ-6).** BRK-4 drives only the relay coil (≤ 2.4 A including pull-in). The relay-coil pulse is <=2.4 A including pull-in, <=100 ms. The channel limits at 2.41 A minimum; high-current breaker coils are external to the controller.
- **C6.1** Firmware writes the EEPROM only while PB6 holds ID_WP low (C1.4; commissioning and calibration only).
- **C6.2 SLn_CARD_FAULT_N handling (Pass 3 MAJ-A).** Read on 0x22 port 0; expanders share SLOT_EXP_INT_N (PB4).
  - **HSO-5/BRK-4 attention signal:** each TPS1HTC30 limits its channel to 2.41/3.01/3.61 A and asserts SNS/FAULT within <=60 µs. A faulted OPEN relay is not exempt from the isolation deadline.
    1. Blank no longer than **15 ms** after one REQ rising edge. Poll continuously; outside blanking, CARD_FAULT_N low starts immediate diagnosis.
    2. Complete the SNS scan and set faulted REQ = 0 within the next **10 ms**, total **<=25 ms from fault** (including I2C/SPI scheduling, expander interrupt, mux settling and ADC). Five channels ×0.8 ms settling fits within 10 ms, but scheduler/ADC latency must be measured.
    2a. **Pass 4 m9, more than one channel:** if the first scan finds more than one channel of the card faulted (for example a shared harness short), do not scan on: set that card's ARM_N high and EN_N high **within ≤ 20 ms of the fault**, then `CH_FAULT` for every faulted channel. Pass 5: the card's eFuse caps it at ≤ 4.86 A, so the bank overload trips in ≥ 41.9 ms HOT / 40.0 ms ROOM (was 27.4 / 25.8 ms): ≥ 20 ms margin; the eFuse FLT# (≤ 1.6 ms) normally ends it first.
    3. Latch `CH_FAULT(slot,ch)` until acknowledgment. Keep healthy channels on only if the faulted channel is positively identified. If the scan cannot identify/isolate it by 25 ms, set ARM_N high and EN_N high for the card by that deadline.
    4. **Stagger REQ turn-ons:** no second new channel until the first's 25 ms observation window is complete; no overlapping blanking windows across cards. Admission includes the **whole 2.4 A HOT / 4.0 A ROOM bank budget**, including relay pull-in and declared card bias.
    5. Lamps or other loads that need >15 ms in current limit must use an external driver/inrush limiter. Do not lengthen the mask to accommodate them; that would destroy bank selectivity. A relay that cannot operate within this rule is not an admitted load.
    6. Persistent CARD_FAULT_N after REQ = 0, unidentifiable SNS or communication loss: cut the slot. No 200 ms delay.
  - **DI-8 TPS26621 FLT:** mask >=30 ms after BIAS_ON rises (worst startup 14.4 ms at 32 V). Then low >10 ms -> BIAS_ON = 0, `DI_BIAS_FAULT`, readings invalid. Slot stays powered.
  - **AI-4:** no CARD_FAULT_N driver; low means `ID/CARD` fault -> disarm and cut the slot.
- **C6.3** MCP23S17 setup on every LV card:
  - IOCON.ODR = 0: INTA push-pull, active low, into the card 74LVC1G07, which is the open-drain INT_N on the backplane.
  - Unused GPIO stay inputs with GPPU = 1. Never configure an unused pin as an output.
  - Re-write IOCON after every SLOT_RST_N release.

## C7 Pass 1 bus and safety rules (Nov 23, 2026, HST)
- **C7.1 SLOT_CS_EN ordering.** PD13 (SLOT_CS_EN, 100k pull-down) stays low until SLOT_CS_A0-A2 are set; then raise CS_EN for the transfer and lower it before changing the address. Never change A0-A2 while CS_EN is high: the '138 would glitch a second card's CS.
- **C7.2 Slot SPI with unpowered cards.** Every LV card buffers CS/SCK/MOSI/RST and MISO/INT through Ioff parts (Nexperia 74LVC125A, 74LVC1G125, 74LVC1G07). So the MCU may clock the bus while some slots are off. MISO is driven only by the selected card (its 1G125 OE# = its buffered CS); a 100k pull-down on the mainboard keeps MISO low when no card drives it. SCK, MOSI and SLOT_RST_N have 33R source resistors at the MCU (N12). **Pass 3 N14:** an unpowered card's INT_N input buffer is not guaranteed to release its open-drain output. Ignore SLn_INT_N whenever that slot is off/ramping, bank off/ramping, or reset is asserted. Never address an unpowered slot on SPI or treat its default MISO = 0 as a response. Mask its interrupt in software, not by disabling the shared expander IRQ. Before power removal, CS_EN low, ARM_N high and remove pending card transactions; only re-enable after C2.3.
- **C7.3 MUX_A sharing and ANA_OUT settling.**
  - MUX_A0-2 are card-local MCP outputs; each card has its own mux.
  - The mainboard SLOT_ANA mux (U109) selects one slot ANA_OUT.
  - Pass 2 m1: each SLn_ANA reaches U109 through a 1k series resistor. U109 EN is PE13 (SLOT_ANA_EN) with a 100k pull-down, so every switch is open at MCU reset. The mainboard MUX_A0-2 lines have 100k pull-downs.
  - Order: set the card MUX_A, drive MUX_A0-2 for the slot, drive SLOT_ANA_EN high, then wait at least **0.8 ms** before converting. The source is 4.7k + 910R + 1k + 2 × 7 Ω RON ≈ 6.6 kΩ into C224 (10 nF ±10%). That gives τ = 66-73 µs (1τ). Full 12-bit settling (9.0 τ) takes 0.60-0.66 ms, so 0.8 ms has margin. The old "57 µs" was 1τ without the 1k, not full settling.
  - Drive SLOT_ANA_EN low after the conversion. Never select the ANA channel of an unpowered slot. The 1k limits an unpowered or faulty slot to ≤ 3.3 mA into U109 anyway.
- **C7.4 ID mux bus recovery (M4).**
  - PB5 drives ID_MUX_RST_N (10k pull-up on the backplane, R717 in this build, R711 in the Pass 1 build; R707 is the RC_EN pull-down): the muxes run while the MCU is in reset.
  - If an ID read times out or SDA is held low: drive PB5 low for 10 µs (TCA9548A datasheet tW(L) = 6 ns min, so this has wide margin), release it, then clock SCL 9 times with SDA released and send a STOP.
  - Then re-select the channel and retry once.
  - Two failures: `ID_BUS_FAULT` (C2.5 rules).
- **C7.5 Rail-cut proof test and RC_ALLOW (M8/N9).**
  - The rail cut (U101) is enabled by `RC_EN = WD_OK AND ESTOP_OK AND RC_ALLOW` (74LVC1G11).
  - RC_ALLOW is PB7, with a 100k pull-down: the rail is off at reset.
  - U101 latches off after a short (100k across C_TMR). Re-arm by toggling RC_ALLOW low for at least 10 ms, then high.
  - Pre-crank proof test, every start, in IDLE before PREHEAT:
    1. With ESTOP_OK = 1 and WD_OK = 1, drive RC_ALLOW low.
    2. Check that the VBAT_ESTOP readback (R411 ADC) falls below 2 V within 20 ms. The switched bleeder (Pass 2 MAJ-3) makes the decay 3.6-6.6 ms; see below.
    3. Drive RC_ALLOW high and check that VBAT_ESTOP returns within 5 % of VBAT_ESTOP_PRE within 50 ms.
    4. If either check fails: `RAIL_CUT_FAULT`, no start.
  - **Switched bleeder (Pass 2 MAJ-3).** Whenever RC_EN is low (E-stop, WD_OK low, RC_ALLOW low), Q103 AO3400A turns off and Q104 IRLML0100 (100 V) gets 5 V from +5V_TRIP through 100k. That puts 2 × 2.2k 2512 1 W (1.1 kΩ) across VBAT_ESTOP.
    - With the 40.3k passive path, R = 1.07 kΩ. With about 1.85 µF (+20%), τ = 1.98-2.38 ms.
    - Time to 2 V: 12.6 V 3.6-4.4 ms; 24 V 4.9-5.9 ms; 28.8 V 5.3-6.3 ms; 32 V 5.5-6.6 ms. All under 10 ms.
    - If Q101/Q102 are stuck on, the bleeder stays on across the battery: 32 V → 0.93 W (0.47 W per 1 W resistor, 47%); 36 V → 1.18 W (0.59 W each). Firmware sees that as VBAT_ESTOP not falling: `RAIL_CUT_FAULT`, no start, and an alarm to remove battery power.
  - **OUT_FAULT_N masking rule (Pass 2 m5).** OUT_FAULT_N is a wired-OR: the U101 FLT and the engine card U4/U6 FLT all assert on UVLO at an E-stop and during the proof test. So a "rail-cut-only" mask is not possible.
    - Mask OUT_FAULT_N as a whole from any RC_EN falling cause (ESTOP_OK falling, WD_OK falling, RC_ALLOW low) until 20 ms after RC_EN is back high.
    - Discriminate with readback. With ESTOP_OK = 0 or VBAT_ESTOP_PRE < 6.5 V, OUT_FAULT_N low is expected. With ESTOP_OK = 1, RC_ALLOW = 1, VBAT_ESTOP_PRE ≥ 9 V and VBAT_ESTOP < 2 V, OUT_FAULT_N low is a real `RAIL_CUT_TRIP`.
    - Any OUT_FAULT_N outside the window that fails this check is a real fault.
  - **E-stop also turns off the LV HSO outputs (Pass 2 m7).** The E-stop does not cut VBAT_SLOTS in hardware. On ESTOP_OK falling, firmware sets every HSO-5 REQ = 0 and drives the HSO-5 ARM_N high within 10 ms. BRK-4 stays armed only for an OPEN pulse.
- **C7.6 Slot power budget.** The VBAT_SLOTS budget is **4.0 A ROOM / 2.4 A HOT** (149 °F fuse state). This includes all LV field loads and declared card bias, not just the switched outputs. Firmware refuses a commissioned map over budget (C2.5).
- **C7.7 Slot SPI clock (Pass 2 m4).** The MISO return path is about 62.5 ns: MCP23S17 TV 45 ns, plus the 1G125 delay, plus backplane flight. Each card now also has a 33R footprint in series with its 1G125 MISO output. SPI3 must run at **≤ 6.25 MHz**; use 5 MHz.
- **C7.8 ID_WP (Pass 2 m13).** Unlock one EEPROM write at a time: PB6 high, then one page write, then ACK polling for at most 100 ms, then PB6 low. If it times out: PB6 low, `ID_WRITE_FAULT`. Never leave ID_WP low across several cards or across a power state change.
- **C7.9 Supply dips, bank trips and safe sequential restoration (Pass 3 MAJ-B/N6).** **Pass 6 (eFuse slots):** a dead slot short is cut by that slot's TPS16630 in 1–4.5 µs and held at ≤ 6.30 A, so the bank and the other slots ride through with no hiccup (model, bench-verify MOD §17.9 #1/#2). Each eFuse latch (MODE open) clears on SHDN# low-high **or on a UVLO low-high**: a VBAT_SLOTS dip below 5.05–5.50 V, and every bank off/on, re-arms every latched eFuse, which is why C5.1 holds EN_N high on a faulted slot. (Pass 4 text about the TPS48100 slot timers and VS hold-ups is history: the slots no longer use them; only the bank U110 does.) VBAT_SNS is too slow to prove that a dip was a crank rather than a short; classify a crank only from an active commanded CRANK window plus valid voltage history and no prior SCP/slot lockout.
  1. On any bank fault, correlated power faults or suspected dip: **ARM_N high and EN_N high for every slot, BANK_EN low; mark all LV readings invalid.** Apply C2.5 protection-loss rules. Never restore BANK_EN with the previous slot enables still asserted.
  2. Log `SLOT_UV_DIP` only for that qualified crank history. A coincident low VBAT measurement alone is not permission to retry a short. All other events: `SLOT_BANK_FAULT` / `SLOT_BANK_OVERLOAD`, require acknowledgment.
  3. After VBAT_P >=8 V and +5V_TRIP stable >=100 ms, every slot off >=20 ms and **>=3 s filter decay**, one automatic BANK_OVL unlatch is permitted **once per classified crank event** (BANK_EN low >=20 ms). Keep ROOM low until all ROOM conditions return. Any repeat -> manual lockout.
  4. Enable the empty bank and validate it; then restore **one slot at a time**, ARM_N high, using C2.3. Wait >=30 ms healthy after each ramp, self-test outputs-off, then admit the next. Outputs are not restored from stale REQ state.
  5. A slot that faults during restoration gets EN_N high, ARM_N high and **`SLOT_SHORT_LOCKOUT(slot)`**. If it collapses the bank, first cut every slot again; exclude the candidate and do not retry it. Any further bank fault ends automatic recovery. A latched SCP is never automatically retried. Acknowledge only after finding/removing the cause.
  6. An unpowered/ramping slot's PWR_FAULT_N, INT_N, SPI and analogue readings are invalid (C5.1/C7.2); do not blame healthy neighbours for the bank-off UVLO lows.
- **C7.10 ROOM/HOT:** BANK_OVL_ROOM low at reset, with U83 absent/invalid, any non-ROOM F1 state, or VBAT_P <12.4 V. See C5.4.
- **C7.11 Budget margin:** 2.4 A HOT / 4.0 A ROOM vs hardware min 3.15/5.11 A. Preloaded minimum hardware trip 58.4/56.6 ms is >2.2× the 25 ms isolation deadline; verify this on the real firmware. **Pass 6 (R_ILIM 3.09k):** a card-level overload at the eFuse limit (≤ 6.30 A) on top of the preload trips the bank no sooner than 31.7 ms HOT / 29.9 ms ROOM; cut that card on SLn_PWR_FAULT_N (C5.1) or by the 20 ms rule (C6.2 2a): margin ≥ 9.9 ms.
- **C7.13 Q2 hold-off restarts (Pass 6 B1, MOD §19.1).** When BAT_IN − VBAT_P > 2.5–3.8 V for ≥ 46–270 µs (battery returning after an interruption, U1 UVLO/OV recovery), hardware holds U2 and U5 off until Q2 has nearly finished its ramp: +3V3_SAFE drops and the MCU resets. Interruptions longer than about 0.15–0.35 ms now always reset the controller (before, about 1–2 ms). On the following reset apply the warm-reset rules (C2, Pass 3 N7) and log `SUPPLY_INTERRUPTION` if the RTC/FRAM shows the previous session was running. No firmware action can or should override the hold-off.
- **C7.12 Back-power (Pass 2 m9, `docs/INSTALL_SAFETY.md`).**
  - An AI-4 with live loops but slot power off back-feeds ≤ 0.94 mA through its input clamps into +3V3_SLOT. A 1k bleeder holds the rail at ≤ 0.94 V, so firmware may see AI-4 inputs at about 0 V while the slot is off, and must ignore them.
  - An HSO-5/BRK-4 output wired to an externally energized load back-feeds through the TPS1HTC30 body diode into VBAT_FIELD, then through the slot eFuse's internal FET body diode (TPS16630 has no reverse blocking) and the bank FET body diodes into VBAT_SLOTS/VBAT_P. That is an install rule (never wire an output to an externally energized load), not something firmware can prevent.
