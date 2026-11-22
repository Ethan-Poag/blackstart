# Firmware requirements from schematic Batch 27 (2026-11-22 HST)

Requirements only. No firmware exists on this branch.

1. **CM5 boot EEPROM lock (U73 TCA9555 @0x20, P15 = CM5_EEPROM_LOCK_N).**
   - Input, or output high: the EEPROM is writable. This is the TCA9555 power-on default (internal 100k pull-up), so Q73 is on, Q74 is off and nWP floats high through the CM5's internal 100k.
   - Output low: Q74 pulls EEPROM_nWP low, which locks the EEPROM.
   - The CM5 only latches write protection if nWP is low before its 5 V rail and PMIC_EN rise (CM5 datasheet §3.1). To lock in service, drive P15 low before you release CM5_OFF (U76 P05).
   - To allow an rpi-eeprom update: set P15 to input, then power-cycle the CM5 (pulse CM5_OFF).
   - R558 (0R to GND) is DNP. Fit it only for a build that must be locked for good.
2. **D+ excitation time limit.**
   - Q42/U36 (EXC enable) may stay on only from crank until D+ (PA2) shows the alternator has excited, and for at most 30 s.
   - If D+ is still low after that: turn excitation off and raise the charge-fail alarm.
   - At 24-32 V, U36 dissipates 2.4-2.9 W when the alternator never excites, and relies on its internal thermal limit.
3. **Power-fail warning now works.**
   - With R637 fitted, TPS2121 ST is high while IN1 (+5V) feeds the CM5. That makes CM5_PWR_FAIL (GPIO17) and PWR_FAIL_MCU (U76 P07) low in normal running.
   - Both go high only on hold-up (or when U12 is off).
   - CM5 software must debounce for at least 50 ms before it runs `shutdown -h`.
   - The MCU must ignore PWR_FAIL_MCU while it holds the CM5 off.
4. **MPU comparator U35 is now push-pull (TLV1812).**
   - MPU_SPEED (PA15) and MPU_GATE (PC7) are driven both ways. Do not enable an internal pull-down.
   - Leave the inputs as plain floating inputs, or as TIM2_CH1/TIM3_CH2 capture.
