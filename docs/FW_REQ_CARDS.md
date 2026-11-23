# Firmware requirements: swappable cards (M-mod Phase 2, branch m7-modular)

Status: requirements only. Nothing is implemented. Source: `docs/MODULAR_ARCHITECTURE.md` §3 and §9. Written Nov 23, 2026, HST.

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
- C1.4 Writes are allowed only while stopped, with ID_WP driven low, from the config suite.

## C2 Boot and auto-configuration
- C2.1 At boot every LV slot is unpowered and every output is off (OUT_EN low).
- C2.2 Read PRESENT_N, then each EEPROM, then compare with the commissioned map in FRAM: slot → type + serial, CRC, A/B copies.
- C2.3 Matching card: power the slot, run the self-test (outputs-off readback, DI bias test), then enable.
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
- C4.3 An HV card with blank or bad calibration raises `METERING_UNCALIBRATED`. Breaker close stays blocked until it is calibrated.

## C5 Running faults
- C5.1 Any card: PRESENT edge, CARD_FAULT_N or SPI/CRC failure → the slot power drops in hardware. Firmware then applies C2.5's protection-class rule.
- C5.2 A missing BRK-4 blocks every breaker close. It never opens a closed breaker by itself. ESTOP_TRIP stays on the mainboard.
- C5.3 Cards are re-enumerated only after a power cycle. There is no hot-plug.
