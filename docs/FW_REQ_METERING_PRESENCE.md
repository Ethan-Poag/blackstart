# Firmware requirement: metering daughter board missing or silent = fault, engine shutdown

Status: **requirement only, not implemented.** Branch m7-split, written Nov 21, 2026 (HST); bus-side ruling added Nov 22, 2026 HST (Batch 30). No firmware file was changed. The separately held overvoltage engine-shutdown change stays held until Ethan says go. This note defines the "metering board missing" fault that it will rely on.

## Why
With the two-board split, the generator AC metering (2x ADE9000: GEN U71, BUS U72) lives on the HV metering daughter board (`genctl_meter`). It reaches the STM32 through J31 → harness (Molex Micro-Fit 2x8) → J32. A harness that backs out, a broken crimp or a dead daughter board would leave the controller blind to generator voltage, current and frequency. That includes the AC overvoltage protection. "Blind" must never look like "normal".

## Signals (main board)
| Signal | MCU / expander | Meaning |
|---|---|---|
| MTR_DET_N | U73 TCA9555 @0x20, P14 (pin 17). R636 10k pull-up to +3V3_SAFE. U73 INT is shared on I2C_INT_N | LOW = daughter plugged in (J32.15 is strapped to GND on the daughter). HIGH = harness or board missing |
| ADE SPI | SPI1 PA5/PA6/PA7; CS1 PA4 (GEN), CS2 PC4 (BUS); RST PC5; IRQ PB0 (GEN only) | Unchanged pins; now through J31/J32 |

## Requirements
- **FW-MTR-1 (presence):** read MTR_DET_N at boot and on every U73 interrupt. Also poll it at least every 100 ms as a backstop, because the INT line is shared. HIGH → `METERING_MISSING`.
- **FW-MTR-2 (liveness):** each ADE9000 must answer at boot and every ≤500 ms while metering is enabled.
  - The check is a read of a fixed-value register (for example VERSION) that returns the expected value, plus a running-status/sample counter that advances.
  - Three consecutive failures on either ADE → `METERING_SILENT` (per device: GEN, BUS).
  - All-0x00 or all-0xFF reads count as failures (MISO floats or stuck behind a missing isolator supply).
- **FW-MTR-3 (fault action):** `METERING_MISSING` or `METERING_SILENT` (GEN) is a **shutdown-class latched fault**.
  - Engine running: enter FAULT with the existing shutdown outputs (FUEL_EN = 0, GCB open), log to FRAM, buzzer, notify CM5/UI with the cause text "Metering board missing / not responding".
  - Engine stopped: the same fault blocks start (no auto-start, no manual start) until it clears and the operator resets.
  - **BUS-ADE-only silence (`METERING_SILENT` BUS with GEN healthy, Ethan's ruling, Nov 22, 2026 HST):** alarm (buzzer, log to FRAM, CM5/UI cause text "Bus metering not responding") and **block breaker close**: inhibit every bus-sync / GCB / MCB close permissive that needs bus voltage. **Never a shutdown**, in any configured mode. The engine keeps running and a breaker that is already closed stays closed. The alarm latches like the others and clears per FW-MTR-5.
  - **Whole metering board missing or silent** (`METERING_MISSING`, or `METERING_SILENT` on GEN, or on both ADEs) is the latched shutdown described above, with start blocked (Ethan's ruling, Nov 22, 2026 HST).
- **FW-MTR-4 (no silent fallback):** never substitute last-known or zero values for live metering, and never treat a missing reading as "voltage OK".
- **FW-MTR-5 (recovery):** clearing needs MTR_DET_N LOW, both ADE liveness checks passing, a full ADE re-init (RST pulse on PC5, configuration rewrite and verify), and then an operator reset. No automatic restart.
- **FW-MTR-6 (debounce):** MTR_DET_N must be HIGH for ≥3 consecutive samples (≥30 ms) before the fault is raised, so a single glitch does not trip. The liveness timeout (FW-MTR-2) bounds total detection time to ≤1.5 s.
- **FW-MTR-7 (UNCONFIGURED state):** in the factory-default UNCONFIGURED state (AC trips inhibited), still raise and show the fault and still block start. Engine protections are unaffected.
- **FW-MTR-8 (test):** bench test by unplugging the harness at each end while running on the bench supply. The fault must appear within 1.5 s, outputs must go to the shutdown state, and the CM5 must show the cause. Record the result in BRINGUP_CHECKLIST.

## Open questions (Ethan)
1. ~~BUS ADE silent while the GEN ADE is fine: shutdown, or alarm plus breaker-close inhibit only?~~ **Answered by Ethan, Nov 22, 2026 HST:** alarm plus block breaker close, no shutdown (now in FW-MTR-3).
2. Should the same fault also open the GCB/MCB when the engine is already stopped? The default is that it only blocks starting.
