# Safety-MCU firmware architecture (STM32H743VIT6, U7)

Status: **design plan, no code yet**. Licence for firmware: GPL-3.0.

Labels used throughout:
- **[S]** read directly from the schematic or netlist (see `docs/pinmap.md`).
- **[N]** stated in DESIGN_NOTES.md.
- **[I]** inferred or proposed here.
- **[U]** unverified. It depends on a datasheet or app note not checked here (RM0433, AN2606, TPS3431, ADE9000).

## 1. Hardware facts this design relies on
- **Supply.** MCU, FRAM, TPS3431, E-stop logic, expanders and front panel all run on **+3V3_SAFE**, a TPS2116 mux of +3V3 and the battery buck [N][S]. PSU_MAIN_OK, the TPS2116 ST output, goes to **PC3_C** [S]. When it is low, the CM5, comms and isolator primaries may be unpowered. Firmware must then **tri-state** the CM5 SPI4/USART1, FDCAN, USART3 and ADE SPI pins [N].
- **Hardware watchdog [S].**
  - TPS3431 U37: WDI ← **PA12**. WDO_N goes to:
    - the LVC1G08 AND gates on **FUEL_EN (PD2)**, **CRANK_EN (PD3)**, **GLOW_EN (PD4)** and **MCU_TRIP (PD7)**;
    - Q44 → **WD_OE_N**, the /OE of the LVC541s U41/U42 that carry GCB/MCB (PC9–12) and AUX1–8.
  - If kicks stop, every output is cut independently of the MCU.
  - Timeout uses factory CWD timing: "EN and SET1 tied high, CWD 10k pull-up" [N]. The actual value is [U] (TPS3431 datasheet).
- **E-stop [S][N].**
  - Hardware chain: VBAT_ESTOP feeds the fuel and crank drivers. The 555 one-shot plus MCU_TRIP drives the trip output (BAT54C OR).
  - MCU inputs: **PD14 ESTOP_DIG** (VBAT_ESTOP present), **PC6 ESTOP2_DIG** (NC2 sense contact) and **PA1 VESTOP_SNS** analog (100k/10k divider).
  - The E-stop removes actuator power in hardware, so firmware only *observes* it and latches state. FUEL/CRANK are now relay-coil outputs (spec §11.1): opening VBAT_ESTOP drops the relay coils.
- **Outputs.** All are active-high enables; MCU_TRIP has a 100k pull-down [S]. TCA9555 pins reset to Hi-Z inputs [N], so the router and USB rails come up ON through their pull-ups, which is the intended default [N].
- **Fault inputs.** PB2 OUT_FAULT_N is a wired-OR of every high-side switch FAULT [S]. Per-channel current comes from DIAG_EN (PA8) plus the TMUX1208 address lines PD5/PD6/PA11, read on PC0/PC1 by ADC [S]. The INA238 ALERT also shares this line (Enginerd 2026-10-27); for discrimination, see /workspace/review/fw/output_current_sense.md §(g).

## 2. Fail-safe output defaults [I, derived from S]
| Output | Pin | Reset / fault state | Rationale |
|---|---|---|---|
| FUEL_EN | PD2 | LOW (fuel solenoid de-energized = stop) | energize-to-run assumed. Since Oct 27 FUEL drives an external relay only (coil class, spec §11.1): the relay must be de-energise-to-stop |
| CRANK_EN | PD3 | LOW | never crank without explicit command |
| GLOW_EN | PD4 | LOW | |
| MCU_TRIP | PD7 | LOW (100k pd [S]) | trip only on command; hardware E-stop is independent |
| GCB/MCB open/close | PC9–12 | LOW (no coil pulse) | breaker keeps its last mechanical state |
| AUX1–8 | PE0, PE1, PB4–7, PD11, PD13 | LOW | PB4 = NJTRST, internal pull-up 30/40/50 kΩ at reset [S DS12110 p138]. **Spec: R536 4.7k pull-down (0.49 V worst case), others 100k** (fixes_firmware.md §2/§3.1). SystemInit drives PB4 LOW first |
| DPLUS_EXC_EN | PC8 | LOW | |
| EXP_12V_EN | PC13 | LOW until self-test passes [I] | |
| BUZZER | PB3 | LOW | |
- **Startup order [I]:**
  1. Configure all output GPIOs as push-pull LOW *before* the first WDI kick, so the outputs are already safe when WD_OE_N enables the LVC541s.
  2. The GPIO ODR is written before MODER is switched to output.
- **On any fault or E-stop:** drive the outputs LOW in software **and** stop kicking WDI only if software integrity is in doubt. A deliberate watchdog trip is the last-resort hard cut.

## 3. State machine [I]
States: `BOOT → SELFTEST → IDLE → PREHEAT → CRANK → RUN_WARMUP → RUN → (TRANSFER sub-states) → COOLDOWN → STOPPING → IDLE`, plus the latched `FAULT` and `ESTOP`.

| State | Entry actions | Exit / transitions |
|---|---|---|
| BOOT | clocks (HSE 25 MHz → PLL), outputs LOW, IWDG start, load config/latched faults from FRAM (I2C1 0x50) | → SELFTEST |
| SELFTEST | ADC rails (VBAT PA0), PSU_MAIN_OK, expander presence on I2C, INA238 DEVICE_ID and SHUNT_CAL read-back, ADE9000 ID over SPI1, TPS3431 kick, OUT_FAULT_N high, E-stop inputs sane (PD14/PC6/PA1 consistent) | pass → IDLE; fail → FAULT |
| IDLE | all outputs LOW, poll front panel and CM5 | START cmd (panel or CM5) and permissives OK → PREHEAT |
| PREHEAT | GLOW_EN=1 for configured time | timeout → CRANK; stop/E-stop → STOPPING/ESTOP |
| CRANK | FUEL_EN=1, CRANK_EN=1; monitor MPU_SPEED (TIM2_CH1 capture on PA15), D+ (PD15/PA2), CRANK_ISNS (PB1) | speed > crank-disconnect → RUN_WARMUP; crank timeout → rest, retry N times → FAULT(fail-to-start) |
| RUN_WARMUP | CRANK_EN=0, D+ excitation PC8 as needed | timer → RUN |
| RUN | protections active (over/under speed, V/f from ADE9000 GEN, oil/temp DIs, overcurrent) | stop → COOLDOWN; protection → FAULT |
| TRANSFER | sync-check GEN vs BUS ADE9000 (V, f, phase); pulse GCB/MCB close/open (PC9–12), confirm via readback expanders | success → RUN; fail → FAULT(breaker) |
| COOLDOWN | open GCB, run unloaded for configured time | timer → STOPPING |
| STOPPING | FUEL_EN=0, verify speed→0 | speed 0 → IDLE; fail-to-stop → FAULT + MCU_TRIP |
| FAULT (latched) | outputs per fault class (shutdown = FUEL_EN=0, GCB open), log to FRAM, buzzer, notify CM5 | operator reset (panel/CM5) when the cause clears → IDLE |
| ESTOP (latched) | entered from any state when ESTOP_DIG/ESTOP2_DIG asserts or VESTOP_SNS drops; all outputs LOW, MCU_TRIP=1 [I] | E-stop released **and** operator reset → IDLE |

- **Main loop [I]:**
  - Fixed 1 ms tick.
  - Inputs are debounced at 10 ms. E-stop inputs are also on EXTI for immediate action.
  - State logic runs every 10 ms.
- **Data persistence.** Fault log, run hours and config go in FRAM. BOR is used for brown-out [N].

## 4. Watchdogs
1. **IWDG [I]:**
   - LSI-clocked, independent of the HSE. About 100–250 ms window, enabled in BOOT and never stopped.
   - Refreshed only from the main loop after every task has checked in (task-alive bitmask).
   - Option bytes: IWDG_SW = hardware start, and IWDG frozen-in-stop **off** [U RM0433].
2. **WWDG [I]:** optional. Catches the main loop running too *fast* (runaway). Use it only if timing analysis allows; otherwise rely on IWDG plus the external watchdog.
3. **External TPS3431 [S]:**
   - Kicked on PA12 from the same checked-in point, at a different rate than IWDG.
   - Cuts outputs in hardware even if the MCU is held in reset or wedged with its clocks stopped.
   - **Test it on the bench** (see the bring-up plan) because the timeout is [U].
4. **Reset cause:** read RCC_RSR at boot and log it to FRAM. Three watchdog resets within N minutes → stay in FAULT with outputs LOW [I].
5. **Watchdog latch (2026-10-28, fixes_firmware.md §1; hardware pending):**
   - U84 74LVC1G74 latches the TPS3431 trip. **WD_OK** (U84 Q) replaces WDO_N at the four LVC1G08 gates and at Q44/WD_OE_N.
   - Re-arm is by **power cycle only**.
   - Firmware reads WD_OK on **U76 P15** (input port 1, bit 5) every 100 ms. After power-on it is LOW for 0.70–1.06 s (POR-RC re-arm: R554 220k / C293 4.7 µF / U85 Schmitt; D136 discharge). LATCHED is declared only if it is still LOW at 1.5 s, or if it falls after having been HIGH.
   - If WD_OK = 0: state LATCHED; stop all output writes; log RCC_RSR + timestamp to FRAM; show **"WATCHDOG LATCHED: power cycle required"** on the CM5 UI (status frame flag + text).
   - There is no software clear.

## 5. MCU ↔ CM5 link
**Physical [S].**
- SPI4 slave, with the CM5 as master: PE2/4/5/6 to CM5 GPIO11/8/9/10.
- **MCU_IRQ PE3** goes to CM5 GPIO25 (data-ready / alert).
- USART1 PA9/PA10 goes to CM5 TXD0/RXD0. It is used for the ROM bootloader reflash and for a debug console [I].
- Heartbeat: CM5 GPIO26 → PC2_C.
- CM5 also controls NRST (Q7) and BOOT0 (GPIO27).
- Every line has a 1k series resistor, which limits SPI to **≤4 MHz** [N].

**Framing (SPI) [I].**
- Fixed 64-byte full-duplex transactions, so the slave DMA always has a known length.
- Frame layout: `SOF(0xA5) | ver | seq | type | len | payload[≤56] | CRC-16/CCITT-FALSE`.
- The STM32 hardware CRC unit is configured to the same polynomial (0x1021).
- The MCU pre-loads its next TX frame (status snapshot) into DMA. NSS (PE4) rising edge marks the end of a frame.
- Bad CRC or SOF: drop the frame, count the error, and NAK in the next reply.
- Commands carry `seq` and must be ACKed. Safety-relevant commands (START, STOP, breaker ops) need a two-step arm/execute with matching seq inside 500 ms.

**Heartbeat / timeouts [I].**
- The CM5 toggles GPIO26 (PC2_C) at 2–10 Hz *and* sends a valid SPI frame at least every 200 ms.
- The MCU flags `CM5_LOST` after **1 s** with no valid frame **or** no heartbeat edge.
- PC2_C needs the analog switch closed. If that proves unreliable [U], use the SPI heartbeat alone.

**If the CM5 dies [I].**
- The MCU remains the authority.
- Running set: keep running under local protections. The front panel (TCA9555 @0x20) stays usable for STOP and RESET.
- A START from the CM5 is never auto-repeated.
- Configurable policy: "CM5 lost while running → continue" (default) or "→ cooldown/stop".
- Recovery escalation after 30 s lost [N]:
  1. pulse CM5_PWRBTN (TCA9555 @0x25 P06);
  2. then CM5_OFF (P05) power-cycle.
- When PSU_MAIN_OK is low, tri-state the link pins and stop expecting a heartbeat.

**Reflash path [N].**
1. The CM5 drives BOOT0 = 1 and pulses NRST.
2. It sends 0x7F on USART1 immediately and waits for ACK.
3. On failure it retries with NRST.
- The SPI4 lines and DI pins are also scanned by the bootloader [N/U AN2606].

## 6. ADE9000 driver plan
**Hardware [S].**
- SPI1 master: PA5 SCK, PA6 MISO, PA7 MOSI.
- Chip selects are **GPIO**: PA4 = CS1 → GEN ADE (U71) via ISOW7841; PC4 = CS2 → BUS ADE (U72) via ISO7741.
- PC5 RST_N is shared by both. PB0 IRQ_N comes from **U71 IRQ0 only**.
- 24.576 MHz crystal on U71; U71 CLKOUT drives U72 CLKIN [N].

**Driver [I].**
- SPI mode 0 or 3 [U ADE9000 DS]. Start at ≤2 MHz: the isolator propagation delay plus the 1k/pin capacitance limit the MISO turnaround.
- Each transaction is a 16-bit command word (address<<4 | R/W bit) plus 16/32-bit data [U ADE9000 DS].
- Init:
  1. Hold PC5 low for at least the minimum reset time, then release.
  2. Wait for RSTDONE.
  3. Write the config (gains, PGA, line frequency).
  4. Write the run register.
  5. Read back the config and verify the CRC register.
- Acquisition:
  - GEN: use the IRQ (EXTI0 on PB0) for the zero-crossing / energy-ready events.
  - BUS: has no IRQ wired, so poll its RMS/period/phase registers every 10–20 ms.
  - DMA-driven SPI1 with CS toggled in the DMA-complete ISR.
- Sync-check for TRANSFER compares GEN vs BUS frequency, RMS voltage and the angle registers. Both run from a common clock, so the phase comparison is coherent [I].
- Fault handling: on a read-back/CRC mismatch or SPI timeout, mark metering invalid, inhibit TRANSFER, and keep the engine protections that do not depend on the ADE (MPU speed).

## 7. Front panel "key/LED matrix" scan plan
**Hardware [S].**
- **Not a matrix.** 12 individual sealed tact switches go to TCA9555 U73 @0x20 (BTN1 = P00 … BTN12 = P13).
- RGB cathodes are on @0x21, @0x24 and @0x25. The interrupt lines are wire-ORed onto **PE7 I2C_INT_N**, which also carries expanders @0x22/@0x23 [S].

**Plan [I].**
- I2C1 at 400 kHz (PB8/PB9, AF4).
- On a falling edge of PE7 (EXTI), read input registers 0x00/0x01 of the expanders whose INT is wired. The read clears INT.
- Also poll every 20 ms as a fallback, in case an edge is missed.
- Debounce in software: 3 consecutive samples, or 20 ms.
- Long press (STOP held ≥1 s) is required for safety-relevant actions. E-stop is hardware and does not depend on the panel.
- LEDs:
  - ON = output register 0 with that pin configured as output.
  - **OFF = configure the pin as input (Hi-Z)**. Driving it high leaves a faint glow [N].
  - Blink patterns come from a 100 ms LED task that batches register writes per expander.
- I2C bus recovery: after a timeout, clock out 9 SCL pulses (PB8 as GPIO), then re-init. Count the errors. If expanders are missing, raise FAULT(panel) but keep running.

## 8. Peripheral / pin allocation summary (verified AFs, DS12110 Rev 8 Tables 10–14)
SPI4 AF5 (PE2/4/5/6) · SPI1 AF5 (PA5/6/7, PA4 alt NSS) · USART1 AF7 (PA9/10) · USART3 AF7 (PD8/9 + PD12 DE) · FDCAN1 AF9 (PD0/1) · FDCAN2 AF9 (PB12/13, PB12 partial) · I2C1 AF4 (PB8/9) · TIM2 AF1 (PA15 CH1, PB3 CH2) · TIM3_CH2 AF2 (PC7, optional) · SWD AF0 (PA13/14). ADC: ADC1_INP16/17 (PA0/PA1), ADC12_INP14/15 (PA2/PA3), ADC12_INP5 (PB1), ADC123_INP10/11 (PC0/PC1).

---

## 9. Display auto-brightness (added 2026-10-25, Ethan's requirement via Enginerd)

Labels: **[S]** schematic/netlist · **[N]** repo notes · **[D]** datasheet (the document is cited) · **[I]** inferred/proposed · **[U]** unverified · **[L]** LCSC live stock, read 2026-10-25 13:48 HST.

### 9.1 What is on the board today [S]
- **BL_PWM.** CM5 GPIO12 (U9.31) → TPS61500 U24 **EN**, with R121 100k to GND. There is **C121 1 µF on DIMC**, so the TPS61500 runs in **analog-dimming mode**:
  - The PWM duty scales the FB reference through an internal 25 kΩ / C_DIM filter, so the LED current is DC [D: TI SLVS893F §7.4.2].
  - Recommended EN frequency in this mode is 200 Hz–40 kHz [D: SLVS893F Recommended Operating Conditions].
  - Minimum duty after start-up is 1%, and minimum on-time at start-up is 200 µs [D: §7.4.2].
- **BTN_BL_PWM.** CM5 GPIO13 → R526 1k → Q67 (100k base pull-down R527) → AO3401A Q68 → BTN_LED_V. This is a **pure on/off PWM** of the key-LED anodes [S][N], so key LEDs *do* flicker at the PWM frequency.
- **No ambient light sensor.** There is also **no dedicated temperature sensor IC**: no TMP/LM75/NTC parts appear in the netlist [S].
- **Temperature sources that do exist [I]:**
  - CM5 SoC thermal zone (Linux `thermal_zone0`);
  - STM32H743 internal temperature sensor (ADC3 internal channel, [U RM0433]), which can be forwarded over the MCU link;
  - TPS61500 internal thermal shutdown (protection only, not readable).
- **Display I2C bus [S]:**
  - CM5 GPIO2/GPIO3 (DISP_SDA/DISP_SCL, 3.3 V side). On it: touch FPC J15 (Riverdi ILI2511 controller [N display_mech.md]) and PCA9306 U77, which feeds the 1.8 V side DISP_SCL/SDA_1V8 with R119/R120 2.2k to +1V8_DSI and **SN65DSI83 at 0x2C**.
  - The 3.3 V side has no on-board pull-ups; it relies on the CM5 on-module 1.8k pull-ups to 3.3 V [N].
- **MCU I2C1 PB8/PB9 [S]:** 2.2k pull-ups (R46/R47) to +3V3_SAFE. On it: TCA9555 at 0x20–0x25, ADS1115 at 0x48/0x49, FM24CL64B FRAM at 0x50, and header J3. **Planned: INA238 at 0x40** (approved; spec §12.1, no conflict; the display bus is separate).

### 9.2 Sensor comparison
LCSC stock was read live from lcsc.com product pages at 13:48 HST [L]. **JLCPCB assembly stock could not be confirmed**: the JS page could not be parsed reliably. All parts appear to be "Extended" class (from search snippets) [U].

| Part (LCSC#) | LCSC stock [L] | Supply / I2C levels [D] | Address [D] | Range / resolution [D] | Package [D/L] | IR / flicker / spectral [D] | Note |
|---|---|---|---|---|---|---|---|
| **TI OPT3001DNPR (C90462)** | 2,636 | 1.6–3.6 V. VIH ≥ 0.7×VDD, I/O **5.5 V tolerant**. Pull-ups to 1.6–5.5 V. Open-drain INT | **0x44 / 0x45 / 0x46 / 0x47** (ADDR to GND/VDD/SDA/SCL) | 0.01–83k lux, 23-bit effective, auto full-scale | USON-6 2.0×2.0×0.65 mm, top-facing | Human-eye matched, rejects >99 % IR (850 nm response 0.2 %). 100 or 800 ms integration rejects 50/60 Hz | **Recommended** [D: SBOS681C, Features, Pin Functions, §6.5, §7.1, Table 1] |
| TI OPT4001DNPRQ1 (C20199903) | 2,897 | 1.6–3.6 V [L] | 0x44 (GND) … [D: SBOSA93E] | 400 µlux–107k lux (USON variant) | USON-6 2×2 | Eye-matched | Newer/higher range; automotive grade. Good alternate |
| TI OPT3004DNPR (C2655153) | 14,902 | 1.6–3.6 V [L] | not read | 83 klx [L] | WSON-6 2×2 | — | Best stock, but its datasheet was not read here [U] |
| Vishay VEML7700-TR (C504893) | 3,082 | 2.5–3.6 V. VIH 1.3 V min at VDD 3.3 V | **0x10 fixed** | 0–~140 klx, 0.0042 lx/ct at best | 6.8×2.35×3.0 mm, **4 pins: no INT** | 100/120 Hz flicker rejection | Big package, no interrupt [D: Vishay doc 84286 rev 1.8] |
| Lite-On LTR-329ALS-01 (C284894) | 6,552 | 2.4–3.6 V | 0x29 fixed | 0.01–64k lux | VDFN-4 2×2, no INT | 2-channel (vis+IR / IR), 50/60 Hz rejection | Needs lux math from ch0/ch1 [D: LTR-329 DS] |
| Lite-On LTR-303ALS-01 (C364577) | 14,591 | 2.4–3.6 V | 0x29 fixed | 0.01–64k lux | DFN-6 2×2 with INT | as LTR-329 | LCSC flags it "not recommended for new designs" [search snippet, U] |
| ams TSL25911FN (C176812) | **0** | VDD bus | 0x29 | 600M:1 dynamic range, "suited behind dark glass" | DFN-6 | — | Out of stock: rejected |
| ROHM BH1750FVI-TR (C78960) | 40,712 | 2.4–3.6 V, VIH 0.7×DVI | 0x23 / 0x5C | 1–65535 lx (0.11–100 klx extended) | WSOF-6 | — | Poor low-lux floor (1 lx) for night dimming |
| Broadcom APDS-9306-065 (C2649498) | 4,528 | VIH 1.5 V min | 0x52 fixed | 0.01 lux min | UDFN-6 2×2 | 50/60 Hz immunity, INT | OK alternate |

**Recommendation: OPT3001DNPR (C90462).** Reasons:
- best eye-matched IR rejection, which matters behind a tinted window;
- 0.01 lux floor for night dimming;
- autoranging, a selectable address and an interrupt;
- 5.5 V-tolerant I/O;
- a mainline Linux IIO driver (`opt3001`) exists [I/U: confirm it is enabled in the rpi-6.x kernel config].

Second source: OPT4001DNPRQ1 (same footprint class, and its default address is also 0x44 [D: SBOSA93E address table]; check the pinout before treating it as a drop-in [U]).

### 9.3 Bus choice and address check
**Chosen: CM5 display/touch bus, 3.3 V side** (DISP_SDA/DISP_SCL, CM5 GPIO2/3; Linux i2c-1 [U]).
- The CM5 owns both PWM pins, so the control loop stays on one processor with no link dependency.
- The 3.3 V side matches the OPT3001 at VDD = 3.3 V (VIH 0.7×VDD = 2.31 V).
- **Not** the 1.8 V side: the OPT3001 VIH would need VDD = 1.8 V, which adds a regulator dependency on +1V8_DSI.

| Bus | Devices [S] | OPT3001 @0x44 |
|---|---|---|
| CM5 DISP (3.3 V + 1.8 V via PCA9306; the PCA9306 passes all addresses) | SN65DSI83 0x2C (ADDR=GND [S]; 0x2D alternative unused); ILI2511 touch: Riverdi DS Rev 1.1 lists "I2C slave address 0x82", which is 8-bit write form → **7-bit 0x41** [D+I]; new TMP1075 0x48/0x49 (§9.7) | **free**. 0x44 is ≥3 away from the touch address 0x41 and its plausible alternatives 0x40–0x42 [I], so ADDR=GND stays the strap |
| MCU I2C1 (alternative) | 0x20–0x25, 0x48, 0x49, 0x50; 0x4A U83 (proposed); **0x40 INA238 (approved, spec §12)** | also free, but rejected: the MCU has no backlight control path |

Pull-ups:
- No new pull-ups are needed on DISP_SDA/SCL. The CM5 1.8k pull-ups to 3.3 V are within the OPT3001 1.6–5.5 V pull-up range [D].
- INT is left NC because the sensor is polled (see 9.4), so no INT pull-up is fitted.

Supply: OPT3001 VDD = **CM5_3V3**, not +3V3_TOUCH (that rail is switched by PANEL_VDD_EN), so the sensor is powered whenever the bus pull-ups are [I].

### 9.4 Control loop: owned by the CM5 [I]
Rationale:
- Both PWM outputs (GPIO12/13) and the sensor bus are CM5 pins [S]. The MCU has no connection to the backlight.
- Brightness is not a safety function. The safety MCU should not take on UI work, or gain a link dependency for it.

Implementation is a userspace daemon (`blackstart-brightness`), or the kernel `pwm-backlight` driver plus an IIO consumer:
1. **Sensor.**
   - OPT3001 in continuous mode, 800 ms conversion (best 50/60 Hz averaging), automatic full-scale.
   - **Polled at 1 Hz; INT not routed.** All 28 CM5 GPIOs (GPIO0–27) are already used [S]; only CAM_GPIO0/1 are unconnected, and they are not general-purpose Linux GPIOs [U].
2. **Window compensation.** `lux_ambient = lux_raw / T_window`, where T_window is calibrated per enclosure (§9.6).
3. **Perceptual curve.** Brightness follows log10(lux):
   - `L = clamp((log10(max(lux,0.1)) − log10(1)) / (log10(20000) − log10(1)), 0, 1)`, i.e. 1 lux → 0 and 20 klux → 1.
   - `duty = D_min + (D_max − D_min) · L^γ`, with γ ≈ 1.0–1.5 tuned by eye, D_min = night level and D_max = 100 %.
   - The curve is stored as a 6–8 point table so it can be tuned without a code change.
4. **Minimum night level.**
   - D_min ≥ **3 %** (above the TPS61500 1 % minimum duty in analog-dimming mode [D]; margin for analog-dimming nonlinearity at low duty [U]). Tune to "readable at 0 lux".
   - Never 0 % while the UI is active.
5. **Smoothing and hysteresis.**
   - Filter: EMA on log-lux, τ ≈ 2 s when brightening and 8 s when dimming.
   - Dead-band: only update the target when |Δlog10(lux)| > 0.1 (≈ 26 %).
   - Duty slew is limited to 5 %/100 ms, so steps are not visible.
6. **User override.**
   - A ±offset slider (−30…+30 % in L space) is persisted.
   - "Manual" mode freezes auto.
   - An offset set at a given lux decays back toward the curve over hours (optional).
7. **Key backlight tracking (GPIO13).**
   - `duty_keys = k · duty_display`, where k is calibrated so the keys match the screen. Same minimum, and keys off when the screen blanks.
   - PWM frequency ≥ 20 kHz (inaudible; well above the sensor integration time, so it averages) [I].
8. **Display PWM frequency.**
   - 5–20 kHz on GPIO12. In analog-dimming mode the C121 1 µF filter makes the LED current DC [D §7.4.2], so the **backlight does not optically flicker** and cannot alias with the sensor.
   - The keys are the only pulsed light source: keep them optically isolated from the sensor (§9.6). An 800 ms integration averages ≥16 000 PWM periods anyway.
9. **Self-illumination.**
   - The sensor must not see panel or key light (§9.6).
   - Firmware check [I]: step the duty ±20 % while ambient is stable. If the measured lux moves by more than 5 %, flag optical leakage, log it, and subtract a calibrated `k_leak·duty` term.
10. **Thermal derating.** Uses the TMP1075 sensors (§9.7) plus the CM5 SoC temperature. This is a hard ceiling applied after the user offset.
11. **Failsafes:**
    - **Sensor failure** (NACK, stuck value, or >10 s without data): fall back to a fixed 60 % (or the last good value) plus the user offset, and show an icon.
    - **CM5 crash:** GPIO12 Hi-Z → R121 100k pulls EN low → backlight **off**; keys off too (R527) [S]. The keys keep working, but their LEDs go dark too; see the ⚠ issue in §9.8. The MCU sees CM5_LOST and does not depend on the display.
    - **MCU/link loss:** only the STM32 temperature input is lost. Derate on CM5 temperature alone, with a conservative ceiling (e.g. 80 %) [I].

### 9.5 MCU involvement
None in the control loop. Optional: the MCU reports its die temperature and the PSU_MAIN_OK state in the link status frame. When PSU_MAIN_OK is low (on battery backup), the CM5 can cap brightness to save power [I].

### 9.6 Optical placement requirements [I unless noted]
- **Location.**
  - Front-panel border, not under the display. The PCB face is ~16–17 mm behind the panel front [N display_mech.md], so the sensor needs a **light pipe** of about 11–13 mm (same depth as the key plungers [N PANEL_V2.md]) through a Ø2–3 mm window in the 4 mm aluminium panel.
  - Proposed spot: top key row, halfway between the keys at x 116.42 and 159.94, i.e. **x ≈ 138.2 mm, y ≈ −9.25 mm** (glass-origin coordinates), or on the board edge between the top keys and the panel rim.
  - Keep it ≥ 15 mm from the backlight-cable notch at the top-left and away from the touch tail at x 217–245 on the bottom.
- **Light-pipe design.**
  - Opaque black sleeve, or a black-filled pipe holder sealed to the PCB with foam or gasket, so key-LED light (RGB, inside clear plungers) cannot enter the pipe.
  - Gap to the nearest key ≥ 15 mm. Keys at a 43.52 mm pitch leave ≈ 21 mm each side of the midpoint [I from N].
  - No line of sight to the display edge or glass. The window sits in the aluminium field, ≥ 5 mm from the display window.
- **Cover / tint attenuation.**
  - A dark IR-transmissive window cuts visible light to T ≈ 5–30 %. The OPT3001 IR rejection keeps the reading accurate [D §7.3.1], but the low-lux floor rises to 0.01/T (e.g. 0.1 lux at T = 10 %). That is still fine for night dimming.
  - The 83 klux ceiling becomes 83k/T, so direct sun no longer saturates the sensor.
  - Calibrate T_window per enclosure batch against a lux meter at 2 points (≈ 50 lux and ≈ 5 klux).
- **Field of view.** The OPT3001 has a near-cosine response [U: check the angular-response figure]. The pipe narrows it, so aim the pipe forward and normal to the panel.
- **Environment.** Outdoor panel: the window must be sealed (IP rating like the display), UV-stable PC or glass, and kept free of conformal coat on the sensor face. Clean optical surface [D §7.1 note].

### 9.7 Board temperature sensors (Ethan approved; HCR in `docs/HCR_sensors.md`)

**Rev 8 / 8b (2026-11-21):** U81/U82 and U80 were never fitted (m7-sch 1676f11 netlist, MEASURED). **U83 is being added to the BOM** as the cabinet ambient sensor (TMP1075DSGR C2870250, MCU I2C1 address **0x4A**; no conflict with INA237 0x40 / TCA9555 0x20–0x25 / ADS1115 0x48–0x49 / FRAM 0x50). It is not yet in that netlist. Fanless derating is `/workspace/review/fw/fanless_thermal_spec.md` and fixes_firmware §23: dimming follows the U83 reading (SoC estimate is fallback on `U83_FAULT`). The U81/U82 rules below remain historical.
Three TI TMP1075DSGR parts (LCSC C2870250), polled every 2 s. Accuracy is ±1 °C max over −40…+75 °C (±1.8 °F, −40…167 °F) for the DSG package [D SBOS854F Table 4-1].

| Ref | Spot | Bus / address | Read by |
|---|---|---|---|
| U81 | CM5 / heat strap | DISP bus, 0x48 | CM5 |
| U82 | TPS61500 U24 + inductor | DISP bus, 0x49 | CM5 |
| U83 | cabinet ambient, rear | MCU I2C1, 0x4A | MCU, forwarded to the CM5 over the link |

**Derating (proposed, °F; not yet checked against component limits [U]).** Verified limits:
- TPS61500: TA ≤ 185 °F (85 °C), TJ ≤ 257 °F (125 °C), thermal shutdown 320 °F (160 °C) [D SLVS893F].
- Panel: operating ≤ 158 °F (70 °C) [D Riverdi DS Rev 1.1].
- CM5 throttling points: not verified here [U].

Rules:
- **Backlight, U82:** full brightness ≤ 140 °F. Linear derate to a 40 % ceiling at 158 °F. At 167 °F, drop to D_min and raise an alarm. Hysteresis 5 °F.
- **CM5 area, U81:** warn at 158 °F; above 167 °F, cap the backlight at 60 % (cuts the 5 V load and heat near the strap).
- **Cabinet, U83:** warn at 131 °F and alarm at 149 °F. The MCU logs it; it is advisory only and never trips the generator.
- **Sensor failure** (NACK, >10 s stale, or reading outside −40…257 °F): treat that sensor as hot. Cap the backlight at 60 % and flag a fault. If all sensors fail, use the CM5 SoC temperature only.

### 9.8 Idle-dim / wake-bright behavior (Ethan's idea; proposal [I])

**Correction to the premise.** The touch controller *does* have an interrupt line: TOUCH_INT_N is on CM5 GPIO4, with a 10k pull-up to +3V3_TOUCH [S]. Only the OPT3001 lacked a spare GPIO. So touch wake needs **no polling**:
- The Linux `ili210x` driver (compatible `ilitek,ili251x`) [U: confirm in the rpi kernel] reports events through evdev (`/dev/input/eventX`).
- The brightness daemon `poll()`s that fd. Wake latency is one touch report plus one PWM update, < 50 ms [I].
- Polling the ILI2511 over I2C is not needed. It would also add bus traffic shared with the DSI83 and the sensors.

**States** (target duty before the thermal ceiling):

| State | Target | Entry |
|---|---|---|
| BRIGHT | `ambient_curve(lux) + user_offset` | touch event, key-press event from the MCU link, any forced-bright event |
| HOLD | same as BRIGHT | no input; timer `T_hold` (default 60 s, range 10 s–30 min) |
| FADE | ramp to IDLE over `T_fade` = 3 s (log-domain ramp) | T_hold expired |
| IDLE | `min(ambient_curve(lux), idle_cap)`; default idle_cap 20 %, never below D_min (3 %) | fade complete |
| ALARM (forced) | `max(ambient_curve(lux), D_alarm)`; D_alarm default 60 %. Hold while active + 60 s | alarm, warning, fault, E-stop, transfer in progress, CM5_LOST-recovered, MCU link lost |

- Wake from IDLE/FADE ramps up within 250 ms; brightening is never slowed.
- **The first touch in IDLE only wakes the display** and is not passed to the UI, so a stray touch can't act [I].
- **Key presses** come from the MCU (the TCA9555 interrupt on PE7 → the MCU front-panel task → a link event). They always wake. The key's function still executes, because the keys are physical controls.
- **Forced-bright source:** the MCU's link status frame (alarm level, E-stop, transfer state) plus the CM5's own UI alarms.
  - This does **not** depend on the touch path.
  - The link timeout itself also forces ALARM. A dead link is shown as a fault screen at D_alarm.
- **Thermal derating (§9.7):** the ceiling applies in all states, but **in ALARM the ceiling is floored at D_alarm** unless the U82 reading exceeds 167 °F [I]. The TPS61500 has its own 320 °F (160 °C) thermal shutdown [D SLVS893F p.6].
- **Key backlight:** follows the same state (k·duty), with IDLE level = key idle cap (default 10 %). In ALARM the keys go to full brightness, with the alarm key colors set by the MCU via the TCA9555.
- **User settings:** idle dim on/off, idle_cap, T_hold, D_alarm (lower bound limited to 40 %).
  - Stored on the CM5 in `/etc/blackstart/display.json` (atomic write).
  - They are not safety settings, so they don't go in MCU FRAM. A factory reset restores the defaults.

**CM5 crash failsafe and issue for Enginerd:**
- **Backlight, power-off or genuine Hi-Z:** GPIO12 Hi-Z → R121 100k pulls EN low → after > 10 ms below 0.4 V the TPS61500 shuts down [D SLVS893F §7.3.3, p.10]. A powered-off CM5 also stops the DSI stream. **A dark screen in that case is acceptable.**
- **Backlight, CM5 hung but still powered [Rev 8c]:** PWM typically **holds the last duty** (INFERRED), which can be full brightness. The MCU has **no dedicated kill** on BL_PWM; only CM5_OFF. See §13.11 / fixes_firmware §23.5.
- **The MCU can still alert** through the buzzer (PB3 BUZZER_PWM → MLT-8530 [S][N]) and the PE8 heartbeat LED [N]. Proposal: a distinct cadence for "display/CM5 lost", plus an alarm via relay/modem if configured.
- **⚠ Issue → Enginerd:** the key RGB LEDs can't be used as an MCU fallback indicator. Their common anode supply BTN_LED_V is switched only by CM5 GPIO13 (BTN_BL_PWM → Q67/Q68; R527 pull-down keeps it off) [S]. With the CM5 dead, the keys are dark even though the MCU drives the cathodes. Suggested fix: OR an MCU GPIO or TCA9555 pin into the Q67 base (diode-OR), so the MCU can light the keys in an alarm. That is a schematic change; I am not making it.

**Duty-cycle assumptions for the Mechanical heat calculation [assumptions, I]:**
- Backlight: 48 LEDs, Vf 25.6 V typ, If 360 mA [D Riverdi RVT121HVLNWCA0-B DS Rev 1.1 drawing notes] → **≈ 9.2 W LED power at 100 %**.
- TPS61500 efficiency is "up to 93 %" [D SLVS893F p.1]. Assume 88 % at this operating point [U], giving **≈ 10.5 W input at 100 %**.
- In analog-dimming mode, LED current scales with duty [D SLVS893F §7.4.2 Eq.1]. At 20 % duty: ≈ 1.8 W LED. Vf falls at lower current, but efficiency at light load is unknown, so assume ≈ 2.4 W input [U].
- Profile (assumed): 90 % of the time IDLE at 20 %, 10 % BRIGHT at 100 % → **≈ 0.9·2.4 + 0.1·10.5 ≈ 3.2 W average**, about 31 % of continuous full-bright.
- **Worst case for the enclosure: 10.5 W continuous.** A long alarm in direct sun forces bright at 100 %. Size the heat path for that; use the average only for energy/battery hold-up.
- Excluded: panel logic, touch (100 mA × 3.3 V = 0.33 W typ, active [D Riverdi DS]) and key LEDs.

---

## 10. Selectable AC system type: wye / delta / high-leg / split-phase (proposal; source: /workspace/compliance/system_types_research.md)

Labels:
- [S] netlist
- [D] ADE9000 datasheet Rev. A (`datasheets/ade9000.pdf`), page = printed "Page x of 72"
- [I] inferred
- [U] unverified

### 10.1 ADE9000 configuration per system
Register ACCMODE 0x492 [D p.65–66]:
- **SELFREQ** (bit 8): 50/60 Hz.
- **ICONSEL** (bit 7): "IB = −IA − IC" [D p.65].
- **VCONSEL** [6:4] [D p.66]:
  - 000 4-wire wye
  - 001 3-wire delta, VB' = VA − VC
  - 010 4-wire wye non-Blondel, VB' = −VA − VC
  - 011 4-wire delta non-Blondel, VB' = −VA
  - 100 3-wire delta, VA' = VA − VB, VB' = VA − VC, VC' = VC − VB

**Compliance's "3-wire = 100" is confirmed**, on p.66 (Compliance cited p.65; that is where the ACCMODE table starts).

| System | Wiring at J28/J29 | VCONSEL | ICONSEL | CTs | Why |
|---|---|---|---|---|---|
| 4-wire wye (208Y/120, 480Y/277, 600Y/347) | L1, L2, L3, N | **000** | 0 | 3 (A, B, C); IN optional | all three are true L-N voltages: 3-element, Blondel compliant |
| 3-wire delta / ungrounded / HRG | L1, L2, L3; **N open** | **100** | 1 if 2 CTs | 2 (A, C) | our inputs see L-to-floating-star, so only the differences are meaningful; 100 creates all three L-L voltages |
| 240 V high-leg delta (4-wire, 120/208/120) | L1, L2 (high leg), L3, N | **000** | 0 | 3 | N is real; three measured elements. 011 does not apply (it synthesizes VB from VA for the 2-sensor case) [I] |
| Single-phase 120/240 | L1→A, L2→C, N; B unused | **000** (VB ignored) | 0 | 2 (A, C) | real voltages on A and C. 011 is the datasheet's non-Blondel 4-wire delta option, but B isn't needed [I] |

**001 is not used:** it implies phase B is wired as the voltage reference (to VN), and our hardware wires VN to the system neutral [I].

### 10.2 Neutral input on 3-wire, checked against the schematic [S]
- Each ADE9000 channel is differential: VAP/VAN, VBP/VBN, VCP/VCN (U71 GEN pins 19–24, U72 BUS) [S].
- All three VxN of a system come from its own neutral tap: GEN_VN_TAP feeds R428/R435/R442, from the N divider (R443…R446 to GEN_N J28.4, with R447 1k to GND_AC) [S].
- With N open, no current flows in the 4 × 1M chain, so **GEN_VN_TAP = GND_AC through R447 (1k)**. It is defined, not floating.
- **This works without a hardware change** [I from S]. Each VxP − VxN reads (Lx − floating star)/4001. VCONSEL 100 differences cancel the star offset.
- GND_AC is the resistor-weighted mean of all connected conductors of GEN + BUS (DESIGN_NOTES l.310). The resulting common mode is ≈ 0.15 V for a 600 V star offset (Compliance [I]), inside the ADE9000 ±2 V abs-max input-to-GND [D, quoted by Compliance; page not re-checked [U]].
- **Hardware caveats (flag only, no change):**
  1. The RV1–RV3 MOVs are L-N to GEN_N [S]. With N open they form a floating star at ≈ L-L/√3 (OK). If an installer bonds N to PE on a corner-earthed or faulted IT system, they see full L-L. This needs the J28/J29 silkscreen "N: leave open on 3-wire, never to PE" (Compliance D3).
  2. The divider resistors have no MPN or voltage rating yet (Compliance D5).
- **Firmware "N-open" check:** in 3-wire mode, the raw (VCONSEL 000-style) L-to-star readings must be ≈ equal (within ±10 %) and ≈ VLL/√3. If one is ≈ 0, a line is bonded to N or the system is mis-wired → configuration fault.

### 10.3 2-CT metering and power math
- **Current channels:** CTs on lines A and C → IA, IC. With ICONSEL = 1, the IB channel is computed as −IA − IC [D p.27, p.65]; it is valid only with no neutral or earth current [I].
- **IN channel:** no neutral exists, so IN is unused. Optionally it can use a residual or core-balance CT for an earth-leakage indication (needs an external CT [I]).
- **Power (two-wattmeter / Aron, theory [I]):** with VCONSEL 100, phase A power = V_AB·I_A and phase C power = V_CB·I_C.
  - **P_total = AWATT + CWATT** (likewise VAR, and the energy accumulators).
  - The B-phase power (V_AC·I_B) is discarded. The datasheet table defines the voltages but **does not state the power behaviour for VCONSEL 100** [U]. Validate on a bench three-phase source.
  - **Individual "per-phase" W, VAR and PF are not meaningful** in 3-wire mode. Show only totals, plus total PF = P/S with S = √3·V_LL,avg·I_avg (or the vector sum).
- **Derived L-L voltages:** the AVRMS/BVRMS/CVRMS registers after VCONSEL 100 give V_AB, V_AC, V_CB. Firmware relabels them as V_AB, V_BC (= |V_CB|) and V_CA (= |V_AC|).
- **In 4-wire modes,** firmware computes L-L from the waveform or phasor difference (or reads the angle registers).

### 10.4 240 V high-leg delta specifics [I; NEC references from memory, U]
- **Phase naming.** The high leg is **phase B** (NEC panelboard convention, orange marking [U]). Utility meters often use C, so the high-leg phase is a setting (B default, C selectable).
- **Nominal L-N:** A-N = 120 V, C-N = 120 V (180° apart, "lighting phases"). High-leg B-N = 240·√3/2 = **207.8 V**, at ±90° to A.
- **L-L:** all 240 V, 120° apart.
- Protections use **per-phase nominal**: 120/208/120 L-N, plus L-L 240. **Never connect 120 V loads to the high leg** (the UI warns about it).

### 10.5 Protections by system type
| System | Nominal for UV/OV | Rule |
|---|---|---|
| 4-wire wye | L-N (and L-L derived) | existing thresholds in % of nominal L-N |
| 3-wire delta | **L-L only** | L-N is not meaningful (floating star) |
| high-leg | per-phase L-N table + L-L | each phase vs. its own nominal |
| split-phase | L1-N, L2-N 120; L1-L2 240 | B channel ignored |

- Phase-loss, unbalance, rotation and frequency checks are computed from whatever voltages are valid for the type.
- The thresholds themselves stay as defined elsewhere (percent of nominal).

### 10.6 Storage and ownership
- `ac_system_type` {UNCONFIGURED, WYE4, DELTA3, HIGHLEG4, SPLIT1} + high-leg phase + CT count + nominal V. Stored in **MCU FRAM** (FM24CL64B, 0x50), in a versioned record with CRC and A/B copies [I].
- **The MCU owns it.** The CM5 may *request* a change over the link. The MCU accepts it only when:
  - the generator is stopped and the breaker/transfer is open,
  - the request carries an operator confirmation token,
  - the live voltages are consistent with the requested type (or both systems are dead).
- After a change, the MCU rewrites ACCMODE and requires the commissioning test (§10.7) before enabling AC-based protections.
- **UNCONFIGURED** (factory default): metering is displayed, and AC UV/OV trips are inhibited, with a "commission AC system" warning. E-stop and engine protections are unaffected.

### 10.7 Commissioning wiring check (MCU-run, results shown on the CM5)
1. **Magnitudes vs. type:** within ±10 % of nominal.
   - Wye: 3 × L-N equal, L-L = √3·L-N.
   - Delta: 3 × L-L equal.
   - High-leg: 120/208/120, L-L 240.
   - Split: 120/120/240.
2. **Phase angles:** from the ADE9000 angle registers (names/pages [U]).
   - Wye/delta: V_B lags V_A by 120° ±5° and V_C by 240° ±5° (ABC rotation). 240/120 means ACB: warn "reverse rotation", and block sync/transfer.
   - High-leg: A–C 180°, B at ±90°.
   - Split: L1–L2 180°.
3. **Generator vs. bus:** the same rotation and the same type before any sync or transfer permissive.
4. **CT polarity**, with a known resistive load ≥ 10 % rated:
   - Each element's P must be positive, and the per-phase PF > 0.8 in wye.
   - In 3-wire Aron, with a balanced unity-PF load the two elements read ≈ equal (element A leads by 30°, element C lags by 30°: P_A ≈ P_C).
   - P_total ≈ √3·V_LL·I.
   - A negative element means a reversed CT. A swapped CT shows as PF ≈ 0.5 or negative power on one element.
5. **2-CT:** the computed IB is ≈ IA ≈ IC (±10 %) on a balanced load.
6. **3-wire:** the N-open check passes (§10.2).

Results are logged in FRAM with a timestamp; protections are enabled only after a pass.

---

### 10.8 ADE9000 input scaling (full-scale correction, 2026-10-25)
- **Full scale [D]:** ±1 V peak differential at PGA gain 1, which is 707 mV rms with VREF 1.25 V. Gain 2 halves this to ±0.5 V, gain 4 to ±0.25 V. Sources: ADE9000 Rev A p.1 and the p.6 spec table ("−1/Gain … +1/Gain V, 707 mV rms"). PGA_GAIN is reg 0x4B9 (p.71). A grep of firmware/ found no use of a 0.5 V full scale, so nothing needed correcting. Any 0.5 V figure seen elsewhere is the gain-2 value.
- **Codes [D]:** full-scale xRMS = 52,702,092 (p.28/p.33), and waveform (x_PCF) full scale = ±74,532,013 (p.31). Conversion: V_in,rms = xRMS / 52,702,092 × 0.7071 / Gain. Apply calibration gains (xIGAIN/xVGAIN) on top of this.
- **CT channel [S, netlist]:** a Talema AC1005 on the PCB (T1–T4). The burden is R474 + R475 = 2 × 24.9 Ω (49.8 Ω differential), centre-tapped to GND_AC. 1 k/33 nF anti-alias (R476/R477, C271/C272).
- **AC1005 [D, Talema AC1005 datasheet, single page, read via the talema.com PDF text]:** 1000:1 nominal; 5 A nominal, 60 A max primary; rated burden 100 Ω; DCR 41.8 Ω; RCF 1.010. With 49.8 Ω we are below the rated burden, which is good for accuracy [I]. The CT ratio is no longer [U].
- **Burden check [I, arithmetic]:** 5 A → 5 mA × 49.8 Ω = 0.249 V rms = 0.352 V peak, which is 35 % of the gain-1 full scale. Clipping at 1 V peak = 0.707 V rms corresponds to 14.2 A secondary-referred (2.84× nominal). **Use gain 1.** Gain 2 clips at 7.1 A (1.42×), which is too little for overcurrent/short-circuit capture.
- **Flag to Enginerd [I]:** the AC1005 is rated to 60 A primary. At 60 A, 60 mA × 49.8 Ω ≈ 3.0 V rms (4.2 V pk). That is above the ±1 V linear range and also above the ADE ±2 V abs max (page unverified, §10.2). The 1 k series resistors limit the current to about 2 mA at the pins, but the clamp path and abs-max need checking. Fault currents (e.g. 20× on a 5 A CT secondary) are not measurable above ≈14 A. If fault-level metering is required, consider a smaller burden.

## 11. Cooling fans: two 5 V fans, redundant (Ethan decided; proposal [I] unless labelled)

**Rev 8: SUPERSEDED.** The design is FANLESS (HEAT_PATH Phase 24; J4 DNP in BOM_final / m7-sch 1676f11). Do not implement this section. Thermal policy is fixes_firmware §23 / fanless_thermal_spec.md.


Labels:
- [S] netlist
- [N] repo notes
- [M] Mechanical BOARD_CHANGE_REQUESTS.md
- [D] datasheet
- [A] **assumed**
- [U] unverified

### 11.0 Inputs
- **BCR-10** (`mechanical/enclosure/v3/BOARD_CHANGE_REQUESTS.md`) [M] only asks to keep and populate **J4** (270.34, 14.23, B side, JST SM04B):
  - pinout 1 GND, 2 +5V, 3 FAN_TACH, 4 FAN_PWM;
  - **one** fan header;
  - it gives no tach, PWM or fan-current details.
- Netlist [S]: J4.3 FAN_TACH → **CM5 U9.16 Fan_Tacho**; J4.4 FAN_PWM → **CM5 U9.19 Fan_PWM**. These are dedicated CM5 fan pins, not part of GPIO0–27. No other parts are on those nets: no pull-up, series resistor or clamp.
- **Assumed fan [A]:** standard 4-pin 5 V fan; tach open-collector, 2 pulses/rev; PWM input 25 kHz with the fan's internal pull-up (floating or high = full speed); ≤ 0.2 A each; nominal 5000 rpm at 100 %; minimum stable duty 20 %.
  - Replace these with the BCR-10 fan datasheet once it is chosen.

### 11.1 Header and pin mapping, conflicts
**STM32 has no free pins** [S + N]. Every LQFP100 I/O is used. The only auto-named nets (PE11, PE12, PB10, PB11) are DI3/DI4/DI8/DI9 through 1k, and DESIGN_NOTES l.429 says "no free STM32 pins". So:
- no timer input capture/ETR or PWM output is available on the MCU for fans;
- TIM2 is taken (PA15 CH1 = MPU_SPEED capture, PB3 CH2 = buzzer);
- TIM3_CH2 (PC7) is MPU_GATE.
- **Freeing a DI pin is not proposed:** DIs are field inputs.

**Free resources found [S]:**
- TCA9555 **U76 (@0x25) P15, P16, P17** are unconnected today (MCU I2C1, INT on the shared I2C_INT_N). **P15 is now reserved for WD_OK readback (fixes_firmware.md §1, 2026-10-28)**, so only P16/P17 remain for the fans.
- CM5 Fan_PWM/Fan_Tacho (J4) are already wired.

**Proposed mapping [I], needs a schematic change by the layout/hardware owner:**

| Function | Pin | Notes |
|---|---|---|
| FAN1 header | existing **J4** | |
| FAN2 header | **new J-next** (SM04B, same pinout), placed per Mechanical | |
| FAN_PWM (both fans) | CM5 **Fan_PWM** (U9.19), through an open-drain buffer (e.g. 74LVC1G07 or a 2N7002 per fan [I]) | open-drain, so the fan's internal 5 V pull-up never back-drives the CM5 pin |
| FAN1_TACH | CM5 **Fan_Tacho** (U9.16) | via 10k pull-up to CM5_3V3 + 1k series + BAT54S clamp to 3.3 V/GND, in case a fan has an internal 5 V tach pull-up |
| FAN2_TACH | **U76 P16** (TCA9555, 6 V abs-max I/O [N l.323]) | 10k pull-up to +3V3_SAFE. Counted by the MCU from I2C_INT_N edges (see 11.3) |
| FAN_FORCE_FULL | **U76 P17** → open-drain buffer OE/gate | **MCU override**: forces the PWM line Hi-Z, so the fan pull-ups give 100 % |
| Default state | TCA9555 pins are Hi-Z inputs at reset [N l.405] | a 100k pull to the "force-full" state makes **fans run 100 % at power-up and whenever the MCU or CM5 is not commanding** |
| FAN_PWR_EN (optional) | ~~U76 P15~~ **DROPPED 2026-10-28: P15 = WD_OK.** No free expander bit; fan power-cycle not available | — |

**Conflicts / hardware issues → Enginerd:**
1. Only one fan header exists (J4). The second fan needs a new header and nets.
2. The CM5 has a single Fan_Tacho input, so fan 2 cannot be measured on the CM5.
3. There is no MCU timer pin for tach or PWM. TCA9555 edge counting is a compromise:
   - I2C1 load: each tach edge costs one TCA9555 read, ≈ 100 µs at 400 kHz [I]. With 2 edges/rev, 5000 rpm gives ≈ 167 edges/s, ≈ 2 % bus duty [A/I].
   - Edges are lost if the interrupt is serviced late. It is good enough for stall/low-RPM detection, not precise RPM.
   - The proper fix needs a freed STM32 timer pin.
4. J4 has no level protection [S]. The voltage tolerance and pull-up of CM5 Fan_PWM/Fan_Tacho are not verified [U]. A 4-pin fan pulls its PWM input up internally, often to 5 V [A].
5. +5V budget [U]: +5V is a TPS56637 (FB 75k/10k → 5.1 V [N l.64]). The 6 A rating is quoted for the sibling +3V3 part [N l.69]; the +5V rating is not verified.
   - Loads: CM5 (Raspberry Pi specifies up to 5 A for the CM5 [U, not verified here]), key LEDs ≤ 306 mA [N l.324], USB headers ~0.68 A ILIM each [N l.461], plus 2 fans ≈ 0.4 A [A].
   - **Re-check the +5V current budget.**

### 11.2 Control: the CM5 owns it; the MCU is the failsafe
**CM5 control (normal).** The Linux `pwm-fan` driver, or a daemon on the CM5 fan PWM [U], runs at 25 kHz [A]. Duty = max of the per-sensor curves, plus a backlight term.

Temperature curves (all °F, proposed [U]):

| Sensor | Duty curve |
|---|---|
| U83 cabinet ambient | 20 % at ≤ 86 °F, linear to 100 % at 122 °F |
| U81 CM5 / heat strap | 20 % at ≤ 113 °F, linear to 100 % at 149 °F |
| U82 TPS61500 area | 20 % at ≤ 113 °F, linear to 100 % at 140 °F |

- **Backlight term:** + 0.2 × backlight duty, because the backlight is ≈ 10.5 W at 100 % (§9.8).
- **Minimum 20 %** while running (stable-spin assumption [A]). Fans may stop (0 %) only if all sensors are < 77 °F and the backlight is < 30 %, with the fans then kicked every 10 min. Default setting: never stop.
- **Hysteresis:** the duty decreases only after the controlling temperature falls 4 °F below the point where it rose.
- **Ramp limits:** up 10 %/s, down 2 %/s.
- **Noise:** avoid duty in the 25–35 % band if resonance is found in the enclosure test [A]. Night or quiet mode caps the duty at 60 % unless any sensor exceeds 122 °F.

**MCU failsafe [I]:**
- The MCU asserts FAN_FORCE_FULL (100 %) when any of these happens:
  - link timeout > 2 s;
  - CM5 heartbeat (PC2_C) lost;
  - U83 > 122 °F;
  - both tachs stale;
  - power-up until the CM5 reports fan control active.
- The MCU never *reduces* fan speed.
- The CM5 crash case is covered: with FAN_FORCE_FULL asserted, the fans run 100 % whatever state the Fan_PWM pin is left in.

### 11.3 Tach measurement and fault detection
**Measurement:**
- **FAN1:** CM5 Fan_Tacho through the `pwm-fan` or `hwmon` tach input [U: confirm the CM5 kernel exposes it]. RPM = pulses/s × 60 / 2 [A].
- **FAN2:** the MCU counts TCA9555 U76 P16 transitions on I2C_INT_N. On each INT it reads input port 1 and counts rising edges. RPM is computed over a 2 s window.
  - Debounce: ignore edges < 1 ms apart (> 30 000 rpm equivalent).
  - The result goes to the CM5 in the link status frame.

**Faults** (evaluated after 5 s settling at each new duty):

| Code | Condition | Debounce | Clears |
|---|---|---|---|
| FAN1_STALL / FAN2_STALL | < 300 rpm at duty ≥ 20 % | 3 s | auto, after 30 s good, logged |
| FAN1_LOW / FAN2_LOW | RPM < 60 % of the expected RPM(duty) from the stored baseline | 30 s | auto, after 60 s good |
| FAN1_FILTER / FAN2_FILTER (clogged filter / ageing) | 24 h moving average of RPM at 100 % > 12 % above the commissioning baseline (lower air load → higher RPM), **or** the U83→U81 delta at a fixed duty rises > 9 °F above baseline | 24 h | manual acknowledge after service |
| FAN_TACH_STALE (FAN2 path) | no TCA9555 edges and no I2C error flag | 10 s | auto |
| FAN_BOTH_FAIL | both STALL or LOW | 3 s | **latched** until both pass the spin test |

Notes:
- Fan RPM rising when a filter clogs is fan- and enclosure-dependent [U]. Confirm by test. The temperature-delta criterion is the primary one.
- The baseline RPM(duty) table is learned at commissioning: a sweep of 20/40/60/80/100 % with a clean filter, stored in MCU FRAM.

### 11.4 Degraded behaviour
**One fan failed:**
- The remaining fan goes to 100 %.
- Warning alarm, logged; auto-clears per the table.
- Backlight ceiling 60 %.
- CM5 CPU frequency capped at 1.5 GHz via cpufreq `scaling_max_freq` [I; value U].

**Both fans failed:**
- **Backlight ceiling 25 %.**
- CM5 governor `powersave` / `scaling_max_freq` at the minimum OPP. Non-essential services stop (camera, video, USB peripherals via TCA9555 USB0/1_EN [S]).
- Fault alarm and buzzer [S PB3], latched.
- **Last resort:** if U81 > 176 °F, or the CM5 SoC temperature reaches its throttle point and keeps rising for 60 s, the MCU does a **graceful then hard CM5 power-off** via TCA9555 U76 P06 CM5_PWRBTN_MCU, then P05 CM5_OFF (PMIC_Enable) [S][N l.415–416].
- The MCU keeps running generator protection on +3V3_SAFE. The display is lost; the buzzer and heartbeat LED remain.

**Reconciling with §9.8's "always bright on fault":**
- In FAN_BOTH_FAIL the ALARM floor D_alarm is **lowered to 25 %**: the panel's 850 cd/m² [D Riverdi] × 25 % ≈ 210 cd/m² [I]. That is still readable indoors, though weak in sun.
- Thermal protection wins **only** above U82 167 °F, where the backlight goes to D_min (3 %) and the buzzer cadence signals "check panel".
- **Rationale:** a backlight cooked into shutdown (TPS61500 TSD 320 °F / 160 °C [D SLVS893F p.6]) or a panel beyond 158 °F (70 °C) operating [D Riverdi] gives *no* display. A dim display plus audible alarm is better [I].

### 11.5 Power-up spin test
Run by the MCU, because the CM5 is still booting.
1. At reset FAN_FORCE_FULL is in its default 100 % state (11.1).
2. After 5 s, sample both tachs for 2 s. Pass: each ≥ 70 % of the baseline RPM at 100 %. Before commissioning, use a fixed ≥ 3000 rpm [A].
3. When the CM5 reports ready, it commands 30 %; the MCU releases FORCE_FULL. After 5 s, check each fan is within ±25 % of the baseline at 30 % (verifies PWM control).
4. **Result:**
   - Both pass → normal.
   - One fails → FAN_x_STALL plus the one-fan rules. Generator operation is allowed with a warning.
   - Both fail → FAN_BOTH_FAIL rules. The generator may still start (prime power must not be blocked by cooling of the controller [I]), and the alarm is shown.
   - PWM step fails but 100 % works → FAN_PWM_FAULT: stay at FORCE_FULL, warning.
5. The result is logged with a timestamp in FRAM.

### 11.6 Unverified / open
- The BCR-10 fan model (current, tach ppr, PWM frequency, minimum duty).
- CM5 Fan_PWM/Fan_Tacho electrical levels and the Linux driver.
- The +5V converter rating and the CM5 5 V current.
- TCA9555 tach-counting accuracy.
- All °F thresholds.
- RPM behaviour of a clogged filter.
- All hardware changes listed in 11.1, which are for Enginerd. Nothing is changed in the schematic.

## 12. Load shedding (summary; full spec: /workspace/review/fw/load_shedding_spec.md)
- Policy (Ethan, 2026-10-27): there is no shedding in normal conditions, and the copper is being redesigned for the full 10 A chain. Shedding happens only on an abnormal condition: VBAT < 9.5 V sustained (L3/L4), a faulted converter, or an over-current fault. The normal-operation "≤ 2 outputs on" cap is removed. The only remaining limit is total-current supervision, which treats Σ output current above the copper rating as a fault [D].
- Total-current supervision (spec §8). Battery: 12 V and 24 V both integrated (target), with 12 V-only plus an external 24 V step-down as the fallback (Ethan final, Oct 27). The class is detected from VBAT_SNS (< 16 V → 12 V, > 18 V → 24 V; ×11 divider, full scale 36.3 V). The 24 V thresholds are 2× (spec §10, ASSUMED). The current limits are unchanged, and 12 V is the worst case. Chain F1/copper is 10 A at an 18 °F rise [REVIEWER]. I_r = 10 A at room, 8 A at 149 °F (Littelfuse ATO table). Firmware picks I_r from U83 (TMP1075 @0x4A, MCU I2C1, PROPOSED) + 18 °F [A], falling back to 8 A if U83 is missing. Tiers: WARN 0.9·I_r/5 s (9.0/7.2 A); FAULT 1.0·I_r/5 s (10/8 A); FAST 1.25·I_r/100 ms (12.5/10 A); plus an I²t budget of 50 % of the fuse's 115 A²s. I_Σ is estimated today (Σ ISNS + P12_est/(0.85·V_bat) + 0.64 A, +12V PLACEHOLDER). F1 chain = VBAT_P: LM5176, U5, U65 and all 16 TPS1HTC30. FUEL/CRANK (U43/U45) are on VBAT_ESTOP and excluded [SCHEMATIC]. Base load 4.95 A at 12 V / 6.46 A at 9 V; worst normal 10.95 A (B1 PLACEHOLDER), over both ratings. Levers for Ethan are in spec §8.2a. Chain-level current sense is a RECOMMENDATION only (spec §8.5a), with no schematic/BOM change.
- AUX caps (spec §9, Ethan approved Oct 27): `aux_out_limit_A` 2.0 A; `aux_total_cap_room_A` 5.0 / `aux_total_cap_hot_A` 3.0 (U83 F1 state, HOT if U83 is missing). These are MCU-validated against SAFE_MAX; the CM5 may request ≤ SAFE_MAX. Coil pulses: one at a time, 5 A / ≤ 100 ms, FIFO depth 2 (OPEN ahead of CLOSE, CLOSE times out at 2 s). FAST is re-based to 1.5·I_r for ≤ 120 ms per admitted pulse, and non-essential AUX pause if I_Σ + 5 A > 1.5·I_r. ESTOP_TRIP is never queued, aborts a CLOSE, and may overlap an OPEN pulse. Totals with caps exceed the limits (hot 9 V 9.66 A > 8 A; B1 PLACEHOLDER). The low-V derate option (< 10.0 V / > 10.5 V: hot 1.34 A, room 3.34 A at 9 V) is pending Ethan. TPS1HTC30 ILIM 2.99 A < the 5 A pulse is flagged to Enginerd.
- FUEL/CRANK coil class (spec §11.1, DECIDED Oct 27, values ASSUMED): relay-only, on VBAT_ESTOP (outside the main chain). Limits are 2.8 A declared per output (Rev 6; FAULT 3.0 A vs 3.6 A trip conflict flagged) and 6.0 A at the node. Tiers: FAULT 3.0 A/100 ms → off, latch, ≤ 3 retries; FAST 3.75 A/10 ms; node 6 A/100 ms; WARN 1.5 × the expected coil current. Open-load detection is disabled at the 1 mΩ shunt (unresolvable; INA281 offset unverified). Readback FUEL_RBB/CRANK_RBB checks stuck-on. HW flag: the TPS48100 trip is 90 A and needs re-scaling (R297/R303, R294/R300, C197/C201). External relays must be de-energise-to-stop, with a TVS/diode at each relay.
- Two-layer protection (spec §11.2, PROPOSAL pending the no-onboard-fuse decision):
  - Layer 1 is the fixed board-protect `I_bmax` 10/8 A, MCU-enforced.
  - Layer 2 is the user-fuse coordination (`fuse_rating_A`, `fuse_type`, FRAM + CRC), which can only lower the thresholds. NONE means layer 1 only.
  - A VBAT_P upstream short cannot be stopped by firmware.
  - **INA238 battery-input sense: APPROVED** (Oct 27 6:36 PM); part variant and shunt pending (spec §12).
    - I2C1 address 0x40 (A0 = A1 = GND). **Rev 2026-10-28 (Safety R2-1/R3-1, fixes_firmware.md §4):** 2 mΩ R555 (C2093761), ADCRANGE 1 (±40.96 mV, FS 20.48 A), CURRENT_LSB 0.625 mA, power LSB 0.125 mW, SHUNT_CAL 0x1000, CONFIG 0x0010, ADC_CONFIG 0xFB6B, **SOVL 9.5 A = 0x3B60**, BOVL 0x3200 (40 V), BUVL 0x0BE0 (9.5 V, advisory). INA237AIDGSR substitute accepted (it has no DEVICE_ID register). *Superseded: the 20 mΩ/8.19 A and the 14.5 A/0x5AA0 values.* Load-shed: §13.5.
    - **Rev 7 (OPTIONAL event):** `SUPPLY_ABOVE_DECLARED` when VBUS > 32.5 V for > 60 s: log and show in the UI, **no shutdown** (the hardware OV cut-off at 36.35 V worst case does that, releasing at ≤ 33.19 V). BOVL 0x3200 (40 V) unchanged.
    - Firmware reads CURRENT, VBUS and DIAG_ALRT every 10 ms for WARN/FAULT/I²t.
    - *(Superseded 2026-10-28 by §13.5: SOVL 9.5 A = 0x3B60.)* Fast hardware trip: SOVL at 125 % of I_bmax, ALERT latched, averaged compare (SLOWALERT = 1, ≈ 8.6 ms; Enginerd 2026-10-27 9:34 PM HST), so cranking and inrush do not trip it. ALERT is wire-ORed into OUT_FAULT_N PB2 (EXTI2) because no free pin exists.
    - Optional hardware gate to WD_OE_N, recommended only.
    - INA_FAULT → estimate fallback +15 %, tiers −10 %.
- Exempt from the cap and never shed: FUEL, CRANK, ESTOP_TRIP, GCB_OP/MCB_OP. MCU, ADE9000 and fans (§11) stay up.
- Levels on VBAT_SNS (×11, J21.4 external sense [S]): L1 11.8 V/2 s and L2 11.0 V/0.5 s are advisory only (log, no shedding); L3 9.5 V/0.2 s, L4 8.0 V/50 ms, each with ≥ 0.6 V and ≥ 10 s restore hysteresis. Restore is staggered (≥ 250 ms for 12 V loads, ≥ 100 ms for outputs) [I].
- Crank: no pre-shed. Dips are ignored except below 6.5 V (abort if > 500 ms).
- CM5 commands that would exceed the total-current fault limit are refused (NACK BUDGET). The state machine pre-empts low-priority AUX outputs; stop/open actions always proceed.
- PSU_MAIN_OK fault: shed within 1 ms, abort a crank, finish open pulses, abort close pulses, back off 2–32 s, lock out the 12 V loads only after 5 faults in 10 min.
- ESTOP_TRIP: a real emergency adds ≤ 1 ms of shedding before MCU_TRIP. The pulse is capped at 500 ms by a hardware timer, a main-loop check and WDO_N. Retries are ≥ 15 s apart, at most 3.
- Hardware gaps: no on-board VBAT_P ADC (the approved INA238 adds VBUS and total current, spec §12), no converter current sense, LM5176 PGOOD/PG_5V/PG_3V3 not routed to the MCU (spare U76 P16–P17; P15 = WD_OK since 2026-10-28), ESTOP_TRIP dead on VBAT_P loss.


## 13. Fix-spec firmware changes (2026-10-28, source: /workspace/review/schematic_audit/fixes_firmware.md)
All items are [I] until the hardware respin. Labels follow fixes_firmware.md.

### 13.1 Boot order
1. Reset vector / SystemInit: drive PB4 LOW (output), disable NJTRST (keep SWD). Every enable pin is already LOW via the external pull-downs (R534–R551).
2. Clocks: HSE, then LSE with **LSEDRV = 11 (high)**, kept high. LSERDY timeout 5 s → fall back to LSI and log "RTC crystal fault" (§9 there).
3. Set PA9 (UART TX), PE3 (MCU_IRQ) and PE5 (SPI4 MISO) to **analog/Hi-Z**. Enable them only after the CM5 heartbeat on PC2_C or NSS activity. Return them to Hi-Z on CM5_OFF, or when the heartbeat is lost for more than 2 s (FW-019).
4. I2C1: for every TCA9555, write the Output registers (all 0 for enables; P05/P06 = 0) **before** the Configuration registers. U76 P15 is an input (WD_OK).
5. Read WD_OK (U76 P15, pin 18, via R559 4.7k). After a POR it is expected LOW until about 1.35 s worst case (§13.7). If it is still 0 at 1.5 s → LATCHED (§4 item 5). After a non-POR reset (RCC_RSR) it should already be 1.
6. INA238/INA237 init: probe 0x40; MANUFACTURER_ID 0x5449; 3Fh = 0x2381 → INA238, otherwise INA237 (no DEVICE_ID). Write CONFIG 0x0010, ADC_CONFIG 0xFB6B, SHUNT_CAL 0x1000, SOVL 0x3B60, BOVL 0x3200, BUVL 0x0BE0, DIAG_ALRT (ALATCH, SLOWALERT); read every register back. Failure → INA_FAULT (shed AUX, use the estimate).
7. Read U72 (BUS ADE9000) through the buffered clock ADE_CLK_BUF. No response → "ADE BUS clock fault".
8. SELFTEST, then IDLE.

### 13.2 Fail-safe states (after the fix)
- Power-up, MCU reset and bootloader: every engine/breaker/AUX enable is held LOW by the pull-downs (AUX3 4.7k; AUX9/10 and CM5_OFF/PWRBTN 10k). WD_OK is LOW for the first ~200 ms.
- Watchdog trip: WD_OK latches LOW, so the gates and U41/U42 OE are blocked until a power cycle.
- The CM5 boots by default (R552/R553 keep Q8/Q9 off at TCA POR).
- Full table: fixes_firmware.md §3.5.

### 13.3 Mux fault handling (TMUX1208 U63/U64)
- The SNS clamp (BAT54C D128–D135) limits the S pins to ≤ 3.62 V.
- An ADC reading ≥ 3.25 V means "SNS fault-high": mark the channel faulted, cross-check PB2, and never convert it to amps.
- Settle ≥ 20 µs after each address change.

### 13.4 New pin/bit assignments
- U76 P15 (TSSOP pin 18; pin 16 is P13 = USB0_EN) = WD_OK (input) via R559 4.7k series.
- PB2 OUT_FAULT_N also carries INA238 ALERT (read DIAG_ALRT on a falling edge to tell them apart).
- PA9 and PE3 now have 10k series resistors (R56/R57).
- FUEL/CRANK_ISNS: **INA281A1 (approved) × 20 mΩ = 0.40 V/A, so I = 2.5 A/V × V_out.** Software trip 3.6 A (< 3.9 A), hardware trip 3.86/4.97/6.14 A, declared limit 2.8 A (Rev 6) per channel.
- **EXP_12V (PC13 → U15) is NOT watchdog-gated** (Ethan ruling): only actuating outputs (FUEL, CRANK, GLOW, TRIP, GCB/MCB, AUX1–10) are. It is held OFF at reset by R551.
- Isolators U69/U70/U17 stay on +3V3: **accepted exception** (Safety). Firmware sets their MCU drive pins to Hi-Z when PSU_MAIN_OK goes low or ADE/RS-485 timeouts occur, and restores them after 100 ms of good power.
- ADE9000 full scale is ±1 V peak differential (see §10.8). The U72 VAP net is named BUS_VA_P.

### 13.5 Battery load-shed (Safety R3-1; loads ASSUMED by Safety; full spec load_shedding_spec.md §13)
- External fuse 10 A FAST ≥ 58 V DC. Keep the battery input ≤ 10 A, **target 9.0 A**. I_in = P_elec/(η·V) + I_small + I_out.
- Allowed total output current at worst electronics load: **2.86 A @ 9 V, 4.62 A @ 12 V, 6.76 A @ 24 V, 7.28 A @ 32 V (max continuous), 7.46 A @ 36 V (jump-start ≤ 60 s)** (5.05 A @ 9 V typical). Used only for admission (refusing new ON commands, interpolated on VBUS clamped to 9–36 V).
- **Shed on measured INA current:** > 9.0 A for 100 ms → shed the next output; ALERT (SOVL 9.5 A, 0x3B60) → shed at once (read DIAG_ALRT 0x0B, because PB2 is shared). Restore one output each time I_in < 8.0 A holds for 2 s.
- **Order:** AUX10…AUX1 → EXP_12V → GLOW → abort pending GCB/MCB close. **Never shed** FUEL, CRANK, ESTOP/MCU_TRIP or open pulses (they are on VBAT_ESTOP, outside the shunt).
- INA_FAULT → shed AUX and use the estimate.

### 13.6 What the watchdog does on a hang (fixes_firmware.md §1.5)
- **No firmware code exists yet**, so IWDG is planned, not implemented.
- The external TPS3431 does **not** reset the MCU (WDO_N is not on NRST, MEASURED).
- Today it gates FUEL/CRANK/GLOW/TRIP and tri-states GCB/MCB/AUX, but **re-opens after every 170–230 ms tRST**.
- After the fix, U84 latches the outputs off until a power cycle. An IWDG reset leaves the pins Hi-Z, and the pull-downs hold the outputs OFF.
- "Watchdog resets the firmware with outputs defaulting off" is **false today** and **partly true after the fix plus IWDG code**.

### 13.7 ADC reference and full-scale table (Rev 3, 2026-10-28 ~3:45 PM HST)
- **VREF+ = +3V3_SAFE [M netlist U7.20]**, VDDA via FB1. Keep VREFBUF disabled/high-Z. Correct every conversion with VREFINT_CAL. ADC1/2 are 16-bit (65535 counts). The old "12-bit" statements are superseded.
- The 3.6 A FUEL/CRANK software trip maps to true 3.48–3.72 A worst case (< 3.86 A hardware minimum). See review fixes_firmware.md §18.1.
- Watchdog CP arm window is worst case **0.40–1.35 s**; the LATCHED check stays at 1.5 s (§18.3).

| Path | Pin | Transfer | FS (at 3.300 V) | Counts per unit | Resolution (1 LSB) | Clamp / note |
|---|---|---|---|---|---|---|
| FUEL_ISNS (U44 INA281A1, 20 mΩ) | PA3 | 0.40 V/A | 8.25 A (linear only to 7.87 A, swing) | **7944 counts/A** | 0.126 mA | INA281 output ≤ VS = ADC rail, no clamp needed [I] |
| CRANK_ISNS (U46) | PB1 | same | same | **7944 counts/A** | 0.126 mA | same |
| MUXA_OUT / MUXB_OUT (TPS1HTC30 SNS → 1.1 kΩ → TMUX1208 U63/U64 D) | PC0 / PC1 | I/KSNS × 1.1 kΩ. KSNS from table **≈1200** (0.833 mA @1 A, 1.66 mA @2 A, 3.3 mA @4 A; nominal 1300 A/A) → **0.916 V/A** | **3.60 A** | **18 197 counts/A** | 55 µA | KSNS accuracy ±3–4 % (2–4 A), ±6 % @6 A, SLVSGL4A p.8–9 [M]. D128–D135 BAT54C clamps (§5). **Fault-high SNS saturates (≥ FS)** |
| VBAT_SNS (R268 100k / R269 10k, ×11) | PA0 | V/11 | **36.3 V** | 1805.4 counts/V | 0.554 mV | D67 BAT54S, C190 100 nF. **≥ 36.3 V reads saturated**: 36 V scope is at FS; OV (40 V) is not measurable here, so use INA238 VBUS (BOVL 40 V) for OV |
| VESTOP_SNS (R411/R412, ×11) | PA1 | V/11 | 36.3 V | 1805.4 counts/V | 0.554 mV | D125 BAT54S, C234 |
| DPLUS_SNS (R266/R267, ×11) | PA2 | V/11 | 36.3 V | 1805.4 counts/V | 0.554 mV | D65 BAT54S, C189 |

### 13.8 Rev 4 (2026-10-28 ~4:05 PM HST): Reviewer items
- WD_OK enters U76 **pin 18 (P15)** through **R559 4.7k**. 10k would fail VIL against the TCA9555 −100 µA pull-up current.
- EN pull-downs R277–R291 → **47k**, so a latched EN is ≤ 0.43 V versus the TPS1HTC30 VIL of 0.8 V with LVC541 IOZ 10 µA at 185 °F.
- LM5176 BIAS: a new +12V connection on m7-wip (NC there).
- **Bootloader (BOOT0 via SW2 or CM5 GPIO27):**
  - The bootloader never kicks WDI periodically, so the latch drops all outputs. After any bootloader/DFU session a power cycle is required to re-arm. The CM5 update flow must expect outputs OFF.
  - R560 100k WDI pull-down added.
  - Bootloader pins overlap GCB_CL (PC9), GCB_OP/MCB_CL/MCB_OP (PC10–12), AUX4/5/8 (PB5/PB6/PD13); all of these are gated by WD_OK.
  - See review fixes_firmware.md §19.4. Bench test required.

### 13.9 Rev 5 (m7-sch): TPS1HTC30 RILIM 24.9k
- ILIM is 3.18/4.02/4.87 A on U47–U61; U68 (47k) is 1.70/2.13/2.55 A.
- Readback saturates at 3.60 A (0.916 V/A). At current limit, SNS goes to VSNSFH 3.0–3.82 V, clamped by the BAT54C to ≈3.3 V+Vf.
- Linear range ≤ 2.7 V (≈2.95 A).
- Software FAULT 3.0 A reading for 100 ms; declared ≤ 2.8 A; SNS ≥ 2.9 V for 1 ms = limit/fault. See fixes_firmware §20.

### 13.10 Rev 7 (Oct 28 ~5:38 PM HST)
- Supply: 9–32 V DC continuous, 36 V ≤ 60 s (jump-start); OV cut-off ≤ 36.35 V, release ≤ 33.19 V. Admission table adds 7.28 A @ 32 V; VBUS is clamped to 9–36 V.
- FUEL/CRANK: INA281A1 × 20 mΩ, software FAULT 3.6 A. 2.8 A is the MAXIMUM declared for main outputs; AUX 2.0 A, the fused circuits and the INSTALL_SAFETY 0.5 A wording keep their lower limits.
- **AI blanking:** AI1–AI6 current-mode readings (LM2904B U26–U28 on VBAT_AI, via ADS1115 U29/U30) are STALE during CRANK, VBUS < 10.0 V or > 32.5 V, and for 500 ms after (ASSUMED; recovery UNVERIFIED). VBAT_SNS/INA238 VBUS are not affected and keep driving load-shed/UV. See fixes_firmware §22.

### 13.11 Rev 8 / 8b (2026-11-21 ~1:08–1:13 AM HST): fanless thermal
- Re-baseline: m7-sch **1676f11**. Study: HEAT_PATH.md Phase 24. CM5 cap **≤ 4 W** (uncapped throttles ~110 °F ambient, capped ~144 °F).
- `arm_freq=1500` is **PROVISIONAL**; freeze only after the 4.0 W bench on +5V_CM5. No `over_voltage`, no `temp_soft_limit`, `camera_auto_detect=0`, `dtoverlay=disable-bt`.
- **Wi-Fi off by default**, user-enableable in Settings with no reboot: `nmcli radio wifi off/on` plus `rfkill`, persisted in `/etc/blackstart/network.json` (`wifi_enabled` default false). Do not ship `dtoverlay=disable-wifi` (config.txt needs a reboot; official config.txt page). Bookworm uses NetworkManager/`nmcli` (Raspberry Pi Ltd Bookworm migration guide, p.11).
- Backlight: CM5 GPIO12 → TPS61500 EN. Cap 40 % at 104 °F ambient, linear to a **15 % minimum** at 118 °F. Thermal cap wins over the §9.8 ALARM floor.
- **U83** TMP1075DSGR C2870250 on MCU I2C1 at **0x4A** (MCU reads, forwards to the CM5). Dimming uses that reading; SoC-ΔT estimate is fallback on `U83_FAULT`. Optional glass NTC (NCP18XH103F03RB C13564) has **no free ADC**.
- Over-temp: SoC 158 / 167 / 176 °F (60 s) or 185 °F. **Heat never trips the engine**; no MCU_TRIP. One AUX may be a configurable over-temp contact (`aux_overtemp_ch` default 0 = unassigned; default polarity energize-on-alarm; triggers on ALARM or UI_SHUTDOWN). See fanless_thermal_spec.md.
- **Rev 8c — boot brightness / hung CM5 (MEASURED, m7-sch 1676f11).** U24 VIN is hard on +12 V. EN (BL_PWM) is only CM5 GPIO12 + R121 100 kΩ to GND. With GPIO12 Hi-Z the boost is off (Ren typ 800 kΩ, EN < 0.4 V for 10 ms, SLVS893F p.5 and §7.3.3 p.10). **No STM32 net touches EN, VIN, or FB.** Indirect MCU lever only: U76 CM5_OFF / CM5_PWRBTN_MCU → PMIC_EN, which also kills the UI. A hang can leave the last PWM duty, including 100 %. Boot: leave the pulldown (do not `gpio=12=op,dh`); start PWM at **50 %** via `pwm-backlight` `default-brightness-level` / `dtoverlay=pwm-pio,gpio=12` (Pi 5 overlay; `gpio=` is on/off only, official config.txt GPIO control). Preferred hardware fix: AND a free U76 P16/P17 into EN. Details in fanless_thermal_spec.md and fixes_firmware §23.5.
