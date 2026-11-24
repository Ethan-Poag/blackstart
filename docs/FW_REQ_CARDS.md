# Firmware requirements: swappable cards (M-mod Phase 2, branch m7-modular)

Status: requirements only. Nothing is implemented. Source: `docs/MODULAR_ARCHITECTURE.md` §3 and §9. Written Nov 23, 2026, HST. Updated Nov 23, 2026, HST, for the Pass 1 review fixes (`/workspace/review/modular_pass1.md`): C2.3, C4.3, C5.1, C6 and the new C7.

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

  Enable order:
  1. SLn_EN_N low.
  2. Wait for PWR_FAULT_N to stay high.
  3. Release SLOT_RST_N.
  4. Configure the card MCP23S17: IOCON.ODR = 0, all REQ bits 0, unused GPIO left as inputs with GPPU = 1.
  5. Read back.
  6. Drive SLn_ARM_N low.

  To disarm, reverse the order: ARM_N high, then the REQ bits to 0, then EN_N high.
- C2.4 Same type with a new serial (a replaced card):
  - power it and self-test it;
  - load calibration from the card;
  - show "Card replaced: slot n";
  - **block the next start until the operator acknowledges at the panel.**
- C2.5 Missing card, wrong type, unknown type, bad CRC, failed self-test or over power budget: the slot stays unpowered and `CARD_FAULT(slot)` is raised. Then:
  - If the card carries a protection-class function: **no start**.
  - Otherwise: alarm only.
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

## C4 Card swap acknowledgment (UI)
- C4.1 The acknowledgment screen shows: slot, old type/serial, new type/serial, and the calibration source (card or default).
- C4.2 The acknowledgment is logged with an RTC time, in FRAM and on the CM5.
- C4.3 An HV card with blank or bad calibration raises `METERING_UNCALIBRATED`. Breaker close stays blocked until it is calibrated. The J31/J32 harness has no spare pin, so the HV meter ID EEPROM WP is not on PB6. It is written only on the bench, with the meter TP3 pad grounded (`docs/INSTALL_SAFETY.md`). Firmware refuses an HV meter calibration write in the field and tells the operator to use the bench procedure.

## C5 Running faults
- C5.1 Any card: PRESENT edge, SLn_PWR_FAULT_N, SLn_CARD_FAULT_N or SPI/CRC failure.
  - PRESENT high removes PWR_EN in hardware (74LVC1G02).
  - Each slot switch latches off on its own short-circuit trip: TPS48100 with 100k across C_TMR, trip 10.7/13.6/16.6 A. Firmware reads that latch as SLn_PWR_FAULT_N low on 0x20 port 1. The TPS48100 FLT and the TPS2553 FAULT share that line.
  - SLn_CARD_FAULT_N is read on 0x22 port 0. Firmware drops the slot itself (EN_N high, ARM_N high).
  - Firmware then applies C2.5's protection-class rule.
  - Re-arm a latched slot only after the operator acknowledges it: EN_N high for at least 10 ms, then low again.
- C5.4 Slot bank limiter. One TPS48100 feeds VBAT_SLOTS to all 8 LV slots and trips at 9.2/11.6/14.4 A. It latches off after about 148 µs, longer than the slot trips (about 70 µs), so a slot short trips its own slot first.
  - BANK_EN is on 0x22 P11, with a 10k pull-down: the bank is off until firmware enables it after the boot checks.
  - BANK_FAULT_N is on 0x22 P12, with a 10k pull-up.
  - A bank trip removes every LV slot. That is `SLOT_BANK_FAULT`, which means no start, and a stop if running when any protection-class card is affected.
  - Re-arm after an acknowledgment: BANK_EN low for at least 10 ms, then high.
  - The INA237 (U86, F1 chain) tiers still cover the fuse time domain above the bank trip.
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
  - Coil current limit: 2.41 A min / 3.01 A typ / 3.61 A max (ILIM 33.2k). A coil that needs more than 2.4 A needs an interposing relay.
- **C6.1** Firmware writes the EEPROM only while PB6 holds ID_WP low (C1.4; commissioning and calibration only).
- **C6.2** SLn_CARD_FAULT_N (0x22 port 0) low for longer than 10 ms:
  - firmware drives ARM_N high, then EN_N high (that slot's TPS48100 off);
  - firmware raises CARD_FAULT(slot).

  SLn_PWR_FAULT_N (0x20 port 1) low means the slot switch has already latched off (C5.1). All three expanders share SLOT_EXP_INT_N (PB4).
- **C6.3** MCP23S17 setup on every LV card:
  - IOCON.ODR = 0: INTA push-pull, active low, into the card 74LVC1G07, which is the open-drain INT_N on the backplane.
  - Unused GPIO stay inputs with GPPU = 1. Never configure an unused pin as an output.
  - Re-write IOCON after every SLOT_RST_N release.

## C7 Pass 1 bus and safety rules (Nov 23, 2026, HST)
- **C7.1 SLOT_CS_EN ordering.** PD13 (SLOT_CS_EN, 100k pull-down) stays low until SLOT_CS_A0-A2 are set; then raise CS_EN for the transfer and lower it before changing the address. Never change A0-A2 while CS_EN is high: the '138 would glitch a second card's CS.
- **C7.2 Slot SPI with unpowered cards.** Every LV card buffers CS/SCK/MOSI/RST and MISO/INT through Ioff parts (Nexperia 74LVC125A, 74LVC1G125, 74LVC1G07). So the MCU may clock the bus while some slots are off. MISO is driven only by the selected card (its 1G125 OE# = its buffered CS); a 100k pull-down on the mainboard keeps MISO low when no card drives it. SCK, MOSI and SLOT_RST_N have 33R source resistors at the MCU (N12).
- **C7.3 MUX_A sharing and ANA_OUT settling.**
  - MUX_A0-2 are card-local MCP outputs; each card has its own mux.
  - The mainboard SLOT_ANA mux (U109) selects one slot ANA_OUT.
  - Order: set the card MUX_A, select the slot on the mainboard mux, then wait at least 0.5 ms before converting. The 4.7k + 910R sense network into about 10 nF settles in about 57 µs; 0.5 ms gives margin.
  - Never select the ANA channel of an unpowered slot.
- **C7.4 ID mux bus recovery (M4).**
  - PB5 drives ID_MUX_RST_N (R707 10k pull-up: the muxes run while the MCU is in reset).
  - If an ID read times out or SDA is held low: drive PB5 low for 10 µs (TCA9548A datasheet tW(L) = 6 ns min, so this has wide margin), release it, then clock SCL 9 times with SDA released and send a STOP.
  - Then re-select the channel and retry once.
  - Two failures: `ID_BUS_FAULT` (C2.5 rules).
- **C7.5 Rail-cut proof test and RC_ALLOW (M8/N9).**
  - The rail cut (U101) is enabled by `RC_EN = WD_OK AND ESTOP_OK AND RC_ALLOW` (74LVC1G11).
  - RC_ALLOW is PB7, with a 100k pull-down: the rail is off at reset.
  - U101 latches off after a short (100k across C_TMR). Re-arm by toggling RC_ALLOW low for at least 10 ms, then high.
  - Pre-crank proof test, every start, in IDLE before PREHEAT:
    1. With ESTOP_OK = 1 and WD_OK = 1, drive RC_ALLOW low.
    2. Check that the VBAT_ESTOP readback (R411 ADC) falls below 2 V within 50 ms.
    3. Drive RC_ALLOW high and check that VBAT_ESTOP returns within 5 % of VBAT_ESTOP_PRE within 50 ms.
    4. If either check fails: `RAIL_CUT_FAULT`, no start.
  - **OUT_FAULT_N masking rule:** OUT_FAULT_N also carries the U101 FLT. During the proof test (RC_ALLOW low) and for 20 ms after RC_ALLOW returns high, firmware ignores OUT_FAULT_N for the rail-cut path only. Any OUT_FAULT_N outside that window is a real fault.
- **C7.6 Slot power budget.** The VBAT_SLOTS budget is 5.0 A at room and 3.0 A at 149 °F, the existing AUX cap. Firmware refuses a commissioned map over budget (C2.5).
