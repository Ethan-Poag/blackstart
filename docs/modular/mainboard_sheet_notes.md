# Mainboard sheet notes carried over from the retired baseline sheets

The Phase 2 rework regenerated `mcu`, `estop`, `mtr_if` and replaced `inputs` + `outputs` with `io_core` (plus the new `backplane` and `slot_power`), using `cards/tools/mainboard.py`.
These are the free-text notes of the locked baseline sheets (tag `baseline-2026-11-23-locked`), verbatim. Notes about circuits that moved to a card now apply to that card (see `docs/MODULAR_ARCHITECTURE.md` §10-§12).

## inputs.kicad_sch (22 notes)

- J17 J1A analog in (PC 5/6)
- J18 COM_A/COM_B/MPU (6P 5.08, p6 NC)
- J19 DI1-6
- J20 DI7-12
- J21 J3A E-stop/D+/VBAT/bias
- J22 DI_BIAS_B (p2-6 NC)
- U29 ADS1115 @0x48
- U30 ADS1115 @0x49
- U31 TCA9555PWR @0x22
- misc / support
- misc / support
- misc / support
- misc / support
- misc / support
- misc / support
- misc
- INPUTS. AI: 1mA PNP current source (LM4040 2.5V ref from VBAT_P, LM2904, 2.49k), BSS84 disable; 4-20mA via 100R + DMN6075S shunt switch;
  100k/18k divider to VMID(1.65V) -> ADS1115 x2 (0x48/0x49). DI: 68k/33k + 100nF -> 74HC14; bank bias via SI2309 (pull-up) / DMN6075S (pull-down).
  MPU: 10k series, 1M bias to VMID, TLV1812 (RRI, push-pull; Batch 27) w/ hysteresis -> TIM2_CH1. D+: 50R 2512 pre-drop + LM317 125mA source (10R) + SS110, sense 100k/10k.
- DI_BIAS eFuses (Batch 18): Q36/Q39 drain -> U89/U90 TPS26621 (ILIM 33.2k = 0.20 A, auto-retry) -> F101/F102 1210L020/72 PTC backup -> DI_BIAS_A/B.
  Batch 21 (Safety S7-N13): RTN pin 5, PowerPAD (EP) and OVP pin 3 tied to GND (OVP disabled; reverse polarity is blocked upstream by U1 LM74800); dVdT/ILIM to GND; EP to GND plane with thermal vias. U89/U90 MUST stay on VBAT_P behind U1 LM74800, never on BAT_IN (62 V abs max vs ~64.5 V TVS clamp). FLT open-drain wired-OR = DI_BIAS_FLT_N -> U76 P17, one 10k R635 to +3V3_SAFE.
  FLT low = current limit / thermal shutdown / UVLO / start-up ramp; released (high) = normal on OR eFuse unpowered (bank switched off by Q36/Q39). Open wire to P17 also reads high.
- Batch 27: R638 100R isolates C129 (1u) from U25A output (TLV906x cap-load drive
  100 pF, SBOS839N p1); DC loads stay on VMID = feedback node, no offset.
- Batch 27: R639||R640 (2x 100R 1W 2512 = 50R) take 0.78 W of the D+ source loss
  (125 mA) off U36; full 125 mA down to ~10.8 V battery. Firmware: drop excitation
  if D+ not up within 30 s (charge-fail alarm).
- Batch 28: SMAJ40A at the DI_BIAS_A/B field pins (J21.6, J22.1). DI_BIAS = VBAT_P
  via Q36/Q39 + TPS26621 eFuse: max 40.1 V (LM74800 OV cut-off max) < VRWM 40 V +
  VBR 44.4 V min; clamp 64.5 V < IRLML0100 100 V. Unidirectional: the bias never
  goes negative. Place at the connector.
- Batch 31 hardware shunt-off gating (Ethan approved Nov 22, 2026 HST). Each 4-20
  mA shunt FET gate AI_SH_Gx = AI_SH_ENx (U31 TCA9555) AND SH_ALLOW. SH_ALLOW =
  WD_OK (U84, latched low on TPS3431 timeout until power cycle) AND NRST (MCU
  reset, through U93 Schmitt buffer as NRST_S). Shunts are therefore off while the
  MCU is in reset, after a watchdog trip, and for the first 0.70-1.06 s (worst case 0.40-1.35 s)
  after power-on. R138/R149/R160/R171/R182/R193 keep the U31-side enables low while U31
  pins are inputs; RN1/RN2 hold the FET gates low if U91/U92 are unpowered.
  Firmware: treat AI 4-20 mA channels as invalid while SH_ALLOW (WD_OK) is low.
  See docs/FW_REQ_BATCH30.md.

## outputs.kicad_sch (33 notes)

- U37 TPS3431SQDRBRQ1
- U38 74LVC1G08
- U39 74LVC1G08
- U40 74LVC1G08
- U41 SN74LVC541APWR
- U42 SN74LVC541APWR
- U43 TPS48100QDGXRQ1
- U44 INA281A2
- U45 TPS48100QDGXRQ1
- U46 INA281A2
- U47 TPS1HTC30QPWPRQ1
- U48 TPS1HTC30QPWPRQ1
- U49 TPS1HTC30QPWPRQ1
- U50 TPS1HTC30QPWPRQ1
- U51 TPS1HTC30QPWPRQ1
- U52 TPS1HTC30QPWPRQ1
- U53 TPS1HTC30QPWPRQ1
- U54 TPS1HTC30QPWPRQ1
- U55 TPS1HTC30QPWPRQ1
- U56 TPS1HTC30QPWPRQ1
- U57 TPS1HTC30QPWPRQ1
- U58 TPS1HTC30QPWPRQ1
- U59 TPS1HTC30QPWPRQ1
- U60 TPS1HTC30QPWPRQ1
- U61 TPS1HTC30QPWPRQ1
- U62 TCA9555PWR @0x23
- U63 TMUX1208PWR
- U64 TMUX1208PWR
- J24 J5A outputs
- J25 J5B returns
- J26 J6A AUX1-6
- J27 J6B AUX7-10 + returns
- OUTPUTS. All MCU enables gated by TPS3431 WDO (LVC1G08 for fuel/crank/glow, LVC541 OE for the rest). Fuel/crank: TPS48100 + 2x BSC070N10NS5 + 1mR shunt +
  INA281A2 from VBAT_ESTOP. Small outputs TPS1HTC30 from VBAT_P: ILIM 24.9k (3.18/4.02/4.87 A), SNS 1.1k -> TMUX1208 -> ADC. Readback via NPN to TCA9555 @0x23.

## estop.kicad_sch (6 notes)

- U65 TPS7B6950QDBVRQ1
- U66 TLC555QDRQ1
- U67 74LVC1G08
- U68 TPS1HTC30QPWPRQ1
- misc / support
- E-STOP (estop_notes v5). VBAT_ESTOP open -> Q 47k/10k releases 555 RESET; TRIG RC (100k/100n) fires one-shot 1.1*2.0M*220n(C0G) = 0.48s nom (spec 0.30-1.00s; ESTOP_TRIP_STUCK 1.20s).
  555 powered from +5V_TRIP (TPS7B6950 from VBAT_P via SS110 + hold-up). BAT54C OR of 555 Q and (MCU_TRIP AND WDO) -> TPS1HTC30 ESTOP_TRIP.
  ADDED: 4th LVC1G08 gates MCU_TRIP with WDO. Hold-up cap changed to 50V (BOM 25V part < 30V OV threshold).

## mcu.kicad_sch (9 notes)

- U7 STM32H743VIT6
- J2 SWD
- JP1 JP1 CM5->MCU SWD (opt)
- U8 FM24CL64B
- J3 Header B (MCU spare)
- misc
- MCU. STM32H743VIT6 LQFP-100. HSE 25MHz, LSE 32.768kHz. SWD header + JP1 (CM5 SWD, optional). CM5 reflash: USART1 PA9/PA10 bootloader, BOOT0 via 1k, NRST via NPN open-collector; PC2_C = CM5 heartbeat.
  Peripherals: SPI4 slave to CM5, USART2 to CM5, FDCAN1/2, USART3 RS-485, I2C1 (expanders/ADC/FRAM), SPI1 to ADE9000s via isolators.
- Batch 28: VREF+ (U7 pin 20) moved from +3V3_SAFE to VDDA_F (after FB1, same node
  as VDDA, so VREF+ <= VDDA always). C318 1u X7R + C319 100n at pin 20 (DS12110
  6.1.6 / AN5036).
- Batch 29 (pass-3 NOTE 10): R649 1k in series with BT1 (CR2032). With D7/D8
  (BAT54C) this gives two independent protections against charging the primary
  lithium cell (UL 1642 / IEC 62368-1 Annex M style): if a diode shorts, reverse
  current is <= (3.3 V - 2.0 V)/1k = 1.3 mA. VBAT load is a few uA, so the drop is
  < 10 mV.

## mtr_if.kicad_sch (4 notes)

- J31 -> harness (2x Molex 43025-1600 + 32x 43030-0001, ~80 mm, pin n to pin n) -> J32 on HV metering daughter (genctl_meter).
- All 16 pins are SELV. Pin 15 MTR_DET_N: daughter straps it to GND; R636 pulls high; read on U73 P14 (TCA9555 @0x20). Pin 16 spare (NC).
- Firmware: missing or silent metering board = fault -> engine shutdown (docs/FW_REQ_METERING_PRESENCE.md).
- Batch 28: R644-R648 33R source series resistors on the MCU-driven inter-board
  lines (place within 10 mm of U7 PA5/PA7/PA4/PC4/PC5): damp ringing on the ~80 mm
  harness and limit ESD current into the MCU. D152/D153 RClamp0524PA (same part as
  D17/D18, 0.3 pF, 5 V) fitted at J31 on all 8 signal lines: the harness is
  unplugged in service (FW-MTR-8) and MISO/IRQ/MTR_DET_N otherwise reach MCU/TCA
  pins unprotected.

