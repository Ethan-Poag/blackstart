# genctl schematic – design notes, assumptions, open questions (Rev B, 2026-10-24)

Status: every block is captured with full connectivity. kicad-cli 9.0.2 ERC: **0 errors, 0 warnings** (all severities).
The exported netlist was checked against the generator's net model: 714 named nets, 0 mismatches, 0 single-pin nets.
The ERC is clean partly because **all custom-symbol pins are passive**, so ERC cannot catch driver conflicts on custom parts.
Values marked *assumed* were chosen from datasheet equations or typical application circuits and still need a design review.

## Conventions
- Nets used on more than one sheet are global labels. Nets used on one sheet are local labels.
- +3V3, +5V, +12V and GND use power symbols. Other rails (VBAT_P, VBAT_ESTOP, +5V_TRIP, +3V8_MDM, +1V8_DSI, CM5_3V3, isolated grounds) are global labels.
- PWR_FLAGs are placed automatically on any rail that has power-input pins but no driver.
- Every unused pin has a no-connect flag. The full list is in `docs/auto_nc_pins.log` (112 pins). Most are unused CM5 SD/HDMI/PCIe/MIPI1 pins and unused M.2 pins.
- KiCad standard symbols are used wherever one exists. The 30 custom symbols in `genctl.kicad_sym` carry LCSC/MPN/Manufacturer fields.
  LCSC numbers come from the project BOM CSVs, or are basic-part codes for common passives. A blank LCSC field means TBD (about half the grouped BOM lines).
- File format is 20231120 (KiCad 8), so KiCad 8 and 9 can both open it. KiCad 9 offers to upgrade it on save.

## New or changed parts versus the BOMs (please approve)
0. **Rev B changes (2026-10-24):** RGB-backlit IP67 buttons instead of discrete LEDs; gigabit magjack; separate gen/bus neutral references; 5 kVrms reinforced metering isolation; +3V3 rail >=3 A. Details in each section below.
1. **6x TCA9555PWR I2C expanders** (LCSC C465732; 0x24/0x25 are costed in other_bom, 0x20-0x23 are still not in any BOM). The STM32H743VIT6 does not have enough GPIO.
   - @0x20: 12 buttons.
   - @0x21, @0x24, @0x25: 36 button-backlight cathodes (12 buttons x R/G/B).
   - @0x22: 16 AI/DI mode controls.
   - @0x23: 15 output readbacks.
2. **Output readback.** Each readback uses a 100k/10k divider into an MMBT3904, which pulls the expander pin low (inverted logic).
   A plain 100k/10k divider gives only about 1.1 V at 12 V, which is below the expander's VIH, and up to 3.3 V at 36 V.
3. **Output status LEDs.** The series resistor is now **10k 1206**, not 1k. With 1k the resistor dissipates about 0.5 W at 24 V.
4. **E-stop hold-up cap.** Changed to **10 µF 50 V 1210**. The BOM part (CL31B106KAHNNNE) is rated 25 V, but VBAT_P can reach the OV trip (now 32.39-35.74 V with R3 9.76k, s3c6f; was 30.3 V at the time of this note).
5. **4th SN74LVC1G08** gates MCU_TRIP with the watchdog (WDO), so a hung MCU cannot fire the trip.
   - The 555 hardware path still goes straight to the BAT54C OR, as in estop_notes v5.
6. **Watchdog inverter.** An MMBT3904 drives the LVC541 /OE from WDO. A watchdog fault puts all small-output enables into Hi-Z, and 100k pull-downs turn the outputs off.
7. **RS-485 DIP switches.** Added one for the 120R termination and one for the 680R fail-safe bias.
8. **SMBJ28CA on VBAT_P** (per outputs BOM), replacing the SMDJ33CA in the spec.
9. **ADS1115 ALERT pins left NC.** The ADCs are polled. ADS1115 ALERT is push-pull by default, so it cannot share the I2C_INT_N wire-OR.
10. **Two 2 mΩ buck-boost sense resistors.** One is fitted and one is DNP (BOM qty 2).

## Power (power.kicad_sch)
**Input protection**
- J0 → BAT_IN (N4/m7-sch 3c: no on-board fuse; battery net BAT_IN; the battery lead is fused in the power box (F1) at <=10 A standard (non-time-delay), >=58 V DC; F1 10 A ATO / Keystone 3557-2 clips removed from the schematic in 9af66ad).
- SMDJ36CA (bidirectional, Littelfuse C224075) TVS on BAT_IN (s3c6f; was SMDJ58CA). Suppressed transients only.

**Ideal diode (LM74800-Q1)**
- Two BSC070N10NS5 back-to-back, common drain (VBAT_DD).
- A and VSNS on BAT_IN; **VS on VBAT_DD** (common-drain midpoint). Wiring fix 2026-10-27 (s3c6d) per TI SNOSD95C p3 and review/hv/lm74800_pins.md: VS abs max is -1 V to GND, so it must sit behind Q1. Before this, VS was on BAT_IN.
- CVS: C1 100 nF 0805 100 V from VS (VBAT_DD) to GND (moved from BAT_IN with VS).
- CAP: C2 100 nF from CAP to VS (now VBAT_DD; *assumed*, typical application).
- Ladder top R1.1 on **BAT_IN** (2026-10-27 s3c6e, review/s3c6c/divider_check.md: EN/UVLO was fed only from SW, so the EN-gated VSNS–SW switch latched off, TI SNOSD95C p13/p16). SW (U1.4) strapped to VSNS (U1.3), both BAT_IN; OVUV_TOP net removed. Trip points unchanged (R(SW) ≤ 46 Ω); always-on divider drain 44.5 µA at 12 V, 115 µA at 31 V [I]. Was: SW → ladder.
- 210k / 49.9k / **9.76k** ladder to EN/UVLO and OV (s3c6f 2026-10-27: R3 10k→9.76k; was 191k/45.3k/10k then 210k/49.9k/10k). Max operating battery **31 V**.
  - DS (SNOSD95C p5-6): V(OVR) 1.231 V typ (1.195-1.267), V(OVF) 1.13 V; V(UVLOR) 1.231 V, V(UVLOF) 1.132 V.
  - OV trip (rising) **32.39 / 34.01 / 35.74 V** min/typ/max (1 % R + Vref spread; max incl. 200 nA pin leakage) [I].
  - OV release (falling) **29.57 / 31.22 / 32.70 V** [I]. OV-min margin vs 31 V = 1.39 V; 0.1 % resistors are an option.
  - UV rising **5.32 / 5.56 / 5.86 V** [I].
  - Ladder drain 44.5 µA at 12 V, 115 µA at 31 V [I]. R1 210k = C22952 (extended), R2 49.9k = C23184 (basic), R3 9.76k = 0603WAF9761T5E C23128.
- CIN: **C297 220 nF 0805 100 V X7R (YAGEO CC0805KKX7R0BB224, LCSC C513710) BAT_IN→GND** (s3c6i: changed from 100 nF CL21B104KCFNNNE C28233 because X7R 0805 DC-bias loss at 13–31 V may take 100 nF below the 0.1 µF minimum; the C-V curve was not opened, INFERRED; s3c6h; TI SNOSD95C p23 §10.2.3.3 "A minimum input capacitance CIN of 0.1 µF … is recommended", read this pass). F.Cu at (249.6, 137.0), GND pad on the existing C1/U1.7 GND trace and via (249.8,139.5); about 9 mm from U1.2/U1.3.
- Check the 5.5 V UV against cold-crank requirements.

**+12V (LM5176)**
- FB 140k/10k with 0.8 V reference → 12.0 V.
- RT 27k gives about 290 kHz (*interpolated*: 40k = 200 kHz, 20k = 390 kHz).
- EN 100k/33k (about 5 V turn-on).
- SS 47 nF. COMP 10k + 22 nF ∥ 220 pF (*assumed*, needs a loop design). SLOPE 100 pF (*assumed*).
- MODE strap 93.1k is TBD from the datasheet table. DITH tied to GND.
- ISNS+/ISNS− tied to VOUT: the average current loop is not used.
- Four BSC070N10NS5, 4.7 µH inductor.
- **Open:** inductor part number, ripple and current-limit calculation for the 8–30 V input range.

**+5V (TPS56637)**
- FB 75k/10k → 5.1 V. EN 100k/27k.
- MODE resistor 100k is TBD per the datasheet table.
- SMBJ5.0A on the rail.

**+3V3 (TPS56637, Rev B)**
- Second TPS56637RPAR (6 A part) from +12V. Per DS Table 4 for 3.3 V: FB 45.3k/10k (3.32 V), L 2.2 µH (Sunlord MWSA0503S-2R2MT, Isat 7 A) [SUPERSEDED: L3 is now 3.3 µH MWSA1004S-3R3MT C408483, a deviation from TI Table 4 (p19, 2.2 µH); bench load-step 0.5-3 A at 9/12/32 V in required; fallback 2.2 µH same footprint], 3x22 µF out, 2x10 µF in, feed-forward 150 pF + 20k (check the topology against the DS figure). EN 100k/27k, MODE 100k (placeholder, same as the 5V rail).
- The rail now supports >=3 A. The MBR0540 diode-OR path is gone, so the STM32 no longer has an always-on 3V3 independent of the 12 V bus. **Open:** is that acceptable?

**Chassis**
- CHASSIS goes to 4 mounting holes, bonded to 0V through 1M ∥ 4.7 nF (*assumed*).

## MCU (mcu.kicad_sch)
**Pin map**
- **SPI and serial links**
  - SPI4 slave to the CM5: PE2 SCK, PE4 NSS, PE5 MISO, PE6 MOSI. PE3 = MCU_IRQ.
  - USART2 to the CM5: PD5/PD6.
  - FDCAN1: PD0/PD1. FDCAN2: PB12/PB13.
  - USART3 (RS-485): PD8/PD9, with DE on PD12.
- **I2C and AC-metering SPI**
  - I2C1: PB8/PB9 with 2.2k pull-ups. I2C_INT_N on PE7.
  - SPI1 to the ADE9000s: PA5–7. PA4/PC4 are the two CS lines, PC5 RST, PB0 IRQ.
- **Analog inputs**
  - PA0 VBAT, PA1 VESTOP, PA2 D+, PA3 FUEL_ISNS.
  - PB1 CRANK_ISNS.
  - PC0/PC1 mux outputs.
- **Digital inputs**
  - DI1–7: PE9–15.
  - DI8–12: PB10, PB11, PB14, PB15, PD10.
- **E-stop, D+ and MPU**
  - PD14 ESTOP_DIG (VBAT_ESTOP via HC14), PC6 ESTOP2_DIG (J3 NC2 sense), PD15 DPLUS_DIG.
  - PA15 MPU_SPEED (TIM2_CH1), PC7 MPU_GATE, PC8 DPLUS_EXC_EN.
- **Output enables**
  - Fuel, crank and glow: PD2–4.
  - Trip: PD7.
  - Breakers: PC9–12.
  - AUX1–8: PE0, PE1, PB4–7, PD11, PD13.
- **Diagnostics and watchdog**
  - PA8 DIAG_EN, PB2 OUT_FAULT_N, PA9–11 mux address.
  - PA12 WDI.
- **Misc**
  - PB3 buzzer (TIM2_CH2), PC13 EXP_12V_EN, PE8 heartbeat LED.
  - PC2_C/PC3_C go to header B.
- **Note:** SWO is not available because PB3 drives the buzzer.

**Support circuitry**
- HSE: 25 MHz with 18 pF load caps (*assumes CL = 12 pF*). LSE: 32.768 kHz with 18 pF caps (*assumes CL = 12.5 pF*). Check the crystal datasheets.
- VCAP1/VCAP2: separate 2.2 µF caps.
- VDDA through a ferrite bead. VREF+ tied to +3V3.
- VBAT: BAT54C OR of +3V3 and the CR2032.
- JP1 (2x4 header) lets the CM5 drive SWD, NRST and BOOT0 for in-field reflash. It is open by default.
- FM24CL64B FRAM at 0x50 sits on this sheet. It uses the KiCad FM24C64B symbol, which has the same pinout.

## CM5 (cm5.kicad_sch)
- The CM5 symbols are generated from the CM5 datasheet pin table: all 200 pins, split into connector A and connector B.

**GPIO map**

| GPIO | Function |
|---|---|
| 0/1 (ID_SD/ID_SC) | Header A I2C |
| 2/3 | Display I2C (on-module 1.8k pull-ups; board pull-ups DNP) |
| 4 | TOUCH_INT_N |
| 5 | TOUCH_RST_N |
| 6 | DSI83_EN |
| 7 | DSI83_IRQ |
| 8–11 | SPI0 to MCU |
| 12 | BL_PWM |
| 13 | Spare (NC) |
| 14/15 | UART0 to MCU |
| 16 | PANEL_VDD_EN |
| 17 | TOUCH_PWR_EN |
| 18–21 | SPI1 to header A |
| 22 | MCU NRST |
| 23/24 | MCU SWCLK/SWDIO |
| 25 | MCU_IRQ |
| 26 | MODEM_PWR_EN |
| 27 | MCU BOOT0 |

- **CM5 ↔ MCU links:** every link has a 33R series resistor.
- **Spec deviation:** BL_EN is not needed. TPS61500 PWM dimming goes through its EN pin.

**Other connections**
- VBAT: CR2032 through a BAT54C and 1k.
- Buttons: nRPIBOOT and PWR_Button.
- Fan header J4 on Fan_PWM/Fan_Tacho: **DNP** (fanless design, 2026-11-21, HEAT_PATH phase 24). Firmware leaves fan control disabled.
- ACT and PWR LEDs.

**Unused pins**
- SD, HDMI, PCIe and MIPI1 are NC.
- CC1/CC2 are NC.
- Also NC: SCL0/SDA0, PMIC_Enable, WL/BT_nDisable, CAM_GPIO, EEPROM_nWP.

**Open questions**
- Is VBUS sensing needed on the USB-C service port for rpiboot? USB_OTG_ID is left NC.
- Which CM5 variant (eMMC/RAM)?

## Comms (comms.kicad_sch)
**CAN (×2)**
- CA-IS3062W with VCC = +5V. **Its VCC range is 4.5–5.5 V**, so it cannot run from 3V3. TXD/RXD swing to 5 V.
  The STM32 FDCAN RX pins PD0 and PB12 are 5 V tolerant.
- Bus path: ACT45B choke (winding pinout UNVERIFIED) → NUP2105L → DIP-switched split termination (62R + 62R, 4.7 nF to the isolated ground).
- Shield → CHASSIS through 1M ∥ 4.7 nF (2 kV).

**RS-485**
- CA-IS2092W powered from +3V3. SEL tied to VISO (5 V bus side, *assumed*). RE# tied to GND (always receiving). DE has a 10k pull-down.
- SM712 protection.

**Expansion 12V**
- TPS1H200A, CL = 1.33k (about 1.5 A). DELAY is NC (assumed auto-retry). FAULT goes to OUT_FAULT_N.

**Ethernet (gigabit, Rev B)**
- HanRun **HR911131A** (LCSC C5184934). The datasheet states "Meets or Exceeds IEEE802.3ab standards for 1000Base-T", 4x 1CT:1CT, 1500 Vrms.
- Pin map from the DS schematic: P1/P2 = MDI0 (J1/J2), P3/P4 = MDI1 (J3/J6), P7/P8 = MDI2 (J4/J5), P9/P10 = MDI3 (J7/J8). Centre taps are common on P5/P6. Green LED 11(A)/12(K), yellow LED 14(A)/13(K). P/N polarity within a pair was read from the drawing; the BCM54210PE corrects polarity automatically anyway.
- Centre taps: AC-decoupled only (100 nF + 10 nF to GND; voltage-mode PHY, no CT bias). LEDs: 330R from CM5_3V3 to the anode, cathode to Ethernet_nLED2/3.
- 2x RClamp0524P cover all 4 pairs. Shield → CHASSIS. The shield tab pin numbers depend on the footprint.

**USB**
- **USB-C service port:** 5.1k CC pull-downs, USBLC6-2SC6. VBUS goes only to the ESD part; the board is not powered from it.
- **USB3-0 → USB3 Type-A:** custom symbol, part TBD. TPS2051C is enabled by VBUS_EN. SSTX has 100 nF AC-coupling caps (check whether they are already on the CM5).
- **USB3-1 HS → USB2514B hub**
  - 24 MHz crystal, 18 pF caps (*assumed*). RBIAS 12k 1%.
  - Configuration straps all pulled down (default internal configuration). OCS_N pulled up, PRTPWR NC (ports always powered).
  - RESET is an RC on the 3V3 rail (no GPIO left).
  - Ports: DN1 → M.2 modem, DN2 → SM04B internal header, DN3/DN4 → spare header.

**Modem**
- **Supply:** TPS56637 at 3.8 V (FB 53.6k/10k), 1000 µF bulk.
  - EN uses a two-NPN level shift from MODEM_PWR_EN, so the rail is off by default.
- **M.2 Key B connections:**
  - **The M.2 "3.3V" pins are fed 3.8 V**, per the BOM/notes. This must match the chosen modem.
  - FULL_CARD_POWER_OFF# tied high. RESET# and W_DISABLE1# NC.
  - LED1# drives an LED.
  - The M.2 pinout is from memory: UNVERIFIED.
- **SIM:** nano-SIM, SRV05-4 ESD, SIM_DETECT NC.

## Display (display.kicad_sch)
**Bridge (SN65DSI83)**
- 1.8 V from a TLV75518. VCORE gets 1 µF.
- ADDR (ball A1) = GND (address 0x2C). RSVD2 = GND. REFCLK default = R113 10k to GND (clock from DSI, HS_CLK_SRC=1); Y4 oscillator + R531 + C286 are a DNP footprint option (Linux driver always uses DSI clock). See Rev (j) below (review C1: all DSI83 CMOS I/O is translated to 1.8 V).
- EN: U78 SN74LVC1T45 3.3 V -> 1.8 V; R533 47k + C116 10 nF on the 1.8 V side, R114 100k on the GPIO6 side. See Rev (j).
- LVDS lanes go to the 40-pin FPC per the RVT121 datasheet:
  - Lanes: Rxin0 on 8/9, Rxin1 11/12, Rxin2 14/15, CLK 17/18, Rxin3 20/21.
  - Power and ground: VDD on 2–4; GND on 6, 7, 10, 13, 16, 19, 22, 25, 28 and 31–33.
  - All other pins NC.

**Panel and touch power**
- TPS22918 switches with QOD tied to VOUT and CT = 1 nF.
- The touch FPC is used in I2C mode: USB pins NC, RST/INT pulled up to +3V3_TOUCH.

**Backlight (TPS61500)**
- VIN = +12V. EN = BL_EN = BL_PWM (CM5 GPIO12) AND BL_ALLOW (U76 P16, MCU) via U88 74LVC1G08 (m7-sch Batch 15). R629 10k pulls BL_ALLOW high (default enabled), R630 100k holds BL_PWM low when the CM5 is off, R121 100k keeps EN low.
- RFREQ 160k → about 600 kHz (*interpolated*: 80k = 1.2 MHz, 480k = 0.2 MHz).
- OVP 232k/10k → 29.7 V.
- Sense 2 × 1.1R in parallel → about 360 mA at 200 mV FB.
- SS 100 nF and COMP 470 nF (*assumed*). DIMC 1 µF.
- 6.8 µH inductor, SS34 diode.
- **Open:** confirm the backlight string voltage and current from the RVT121 datasheet. OVP and current scale with them.

## Inputs (inputs.kicad_sch)
**Analog inputs (AI ×6)**
- 1 mA current source:
  - LM4040-2.5 hangs from VBAT_P, so AI_VSET = VBAT_P − 2.5 V.
  - LM2904 forces the MMBT3906 emitter (2.49k to VBAT_P) to VSET.
  - Output path: 1N4148W + 1k to the terminal.
- Disable: a BSS84 pulls the op-amp + input to VBAT_P. Its gate is driven by a 100k/100k divider and an NPN, which keeps |Vgs| ≤ 15 V.
  - **The default state is source ON**: the expander powers up Hi-Z, so the NPN is off.
- 4–20 mA: 100R shunt switched by a DMN6075S. **The gate is driven at only 3.3 V**; check RDS(on) at that Vgs.
- Measurement chain: 100k/18k divider referenced to VMID (1.65 V, TLV9062 buffer), BAV99 clamp, ADS1115 ×2 (0x48/0x49).
  - The divided COM_A/COM_B commons go to AIN3.

**Digital inputs (DI ×12)**
- Terminal → 68k/33k + 100 nF → 74HC14.
- Bank bias:
  - Pull-up through SI2309 (AO3401A symbol) to VBAT_P.
  - Pull-down through DMN6075S.
  - 4.7k wetting resistor on each pin.
- **Open:** at 36 V input the HC14 pin sees about 12 V, which relies on the input clamp current through 68k. Consider a lower ratio or a series clamp.

**E-stop sense and terminal assumptions**
- J3A ESTOP_SENSE (NC2): 4.7k pull-down → HC14 → ESTOP2_DIG.
- VBAT_ESTOP is also squared up through a spare HC14 gate → ESTOP_DIG.
- **Assumed:** ESTOP_RTN, VBAT_SENSE− and the MPU screen all go to 0V. J3 BIAS_A/BIAS_B are the DI bank bias outputs.

**MPU (magnetic pickup)**
- SMBJ58CA, 10k series, 1M bias to VMID, 1 nF differential, BAV99 clamps.
- LM393 A has 10k/1M hysteresis → MPU_SPEED. LM393 B compares against VMID → MPU_GATE.

**D+ excitation and sense**
- Excitation: SI2309 switch → LM317M current source (10R, 125 mA) → SS110 → D+.
- Sense: 100k/10k → PA2.

**VBAT sense**
- 100k/10k divider → PA0.

## Outputs (outputs.kicad_sch) and E-stop (estop.kicad_sch)
**Watchdog (TPS3431)**
- EN and SET1 tied high. CWD has a 10k pull-up (*assumed*: factory timing).
- WDO gates fuel, crank, glow and MCU_TRIP through LVC1G08s, and the other 12 outputs through the LVC541 /OE.

**Fuel and crank (TPS48100)**
- Each channel:
  - Driver powered from VBAT_ESTOP. G1 drives two parallel BSC070N10NS5.
  - 1 mΩ shunt, INA281A2 (gain 50) to the ADC.
  - BST 470 nF, TMR 68 nF.
  - EN/UVLO 100k/27k (about 5.7 V).
- **Assumed pin strapping:**
  - G2 unused: INP2 = GND.
  - CS_SEL = GND.
  - SCP_TEST = GND.
- **Open:** the ISCP 35.7k is wired ISCP → CS−, and its reference node is *assumed*. Verify CS_SEL and ISCP wiring against the datasheet.
- Fuel clamp: SK1010C + SMDJ24A in series (the TVS cathode sits at the Schottky). Crank: SK1010C freewheel diode.

**Small outputs (TPS1HTC30 ×13)**
- Channels: glow, GCB/MCB open/close, AUX1–8.
- ILIM 24.9k (m7-sch batch 5-1; was 40.2k): ICL 3.18/4.02/4.87 A min/typ/max. LATCH = GND (auto-retry). SNS 1.1k, then 1k into the TMUX1208s.
- SS110 freewheel diode, SMBJ28CA TVS.
- **Open:** the exposed pad is not modelled; check the datasheet for whether it goes to GND or VS.
- **Open:** TMUX1208 pin 3 is missing from the datasheet table. It is tied to GND here; verify.

**E-stop trip (follows estop_notes v5)**
- Supply: TPS7B6950 (SOT-23 pin 4 assumed NC) fed from VBAT_P through SS110 and a 10 µF/50 V hold-up cap.
- Detection and timing:
  - VBAT_ESTOP → 47k/10k → NPN holds the 555 RESET low.
  - TRIG RC is 100k/100 nF. One-shot (Batch 18: R404 2.0M 1 %, C229 220 nF C0G 5 %) = 0.30-1.00 s, 0.48 s nominal (1.1 x 2.0M x 220n C0G; Enginerd Batch 19 spec; it only has to outlast the K4 Finder pickup, coil continuous-rated; ESTOP_TRIP_STUCK 1.20 s). Basis (INFERRED): R/C tolerance 0.45-0.52 s; TLC555-Q1 VIT 2.7-3.9 V and DIS leakage <= 275 nA give 0.32-0.99 s. No trim pot; measure on a built board, cold and hot.
- Output:
  - BAT54C OR of the 555 and the gated MCU_TRIP → TPS1HTC30 (ILIM 47k: 1.70/2.13/2.55 A relay-drive limit; was 13.3k).
  - The trip current-sense line goes to MUXB S6.
- VESTOP_SNS: 100k/10k divider + BAT54S clamp → PA1.

## AC metering (ac_metering.kicad_sch)
**Isolated supply and links (Rev B: 5 kVrms reinforced)**
- **TI ISOW7841DWER** (C179690): 5 kVrms reinforced, integrated DC-DC, SOIC-16 DWE, 8 mm creepage/clearance. VCC = +3V3 (logic levels match the STM32). SEL = GND2 → VISO = 3.3 V, which feeds +3V3_AC directly. Channels: SCK, MOSI, CS1 forward; MISO back.
- **TI ISO7741DWR** (C571196): 5 kVrms reinforced, SOIC-16 DW. Channels: CS2, RST forward (INC tied low); IRQ0 back. EN1/EN2 tied high.
- Power budget: 2x ADE9000 at 17 mA max + ISO7741 side 2 + pull-ups ≈ 40 mA, against ~75 mA available (3.3 V→3.3 V). Check this against the DS curves.
- ADuM5020, ADP150 and both ADuM141E are removed.
- **Layout:** keep a >=8 mm creepage and clearance keep-out across the barrier on every layer, with a milled slot under the isolators. Keep the HV dividers' 1206 chains along the hot side. Reinforced CAT III 300 V needs ≥5.5 mm clearance / ≥6 mm creepage (PD2, material group III). 600 V-class (347/600 V) systems need more and must be re-checked.
- **JLC stock of the ISOW7841 is only 38.** Order or consign early.
- **Ruling (Enginerd, 2026-11-21, Batch 14):** keep the ISOW7841 (U69) and ISO7741 (U70) digital isolators. The proposed switch to opto-couplers is cancelled; no opto-coupler replaces either part.
- **Ruling (Enginerd, 2026-11-21, Batch 14):** insulation basis stays at **pollution degree 2** (sealed fanless enclosure) **plus conformal coat** over the HV section. No PD3 re-layout. The coat is a contamination/humidity mitigation; no creepage or clearance credit is taken for it, and the isolation numbers are unchanged (3 mm outer / 1.5 mm inner HV rules, barrier slots, 8 mm isolator package creepage, 12.6 mm reinforced per ISOLATION_CHECK.md).

**ADE9000 ×2 (GEN and BUS)**
- Shared SPI bus. Clock: 24.576 MHz crystal on the GEN ADE; its CLKOUT feeds the BUS ADE's CLKIN.
- PM0 = PM1 = 0 (normal mode). NC1/NC2 tied to AGND.
- AVDDOUT, DVDDOUT and REF each get 4.7 µF + 100 nF.

**Voltage inputs**
- Per phase: 4 × 1M (1206 HV) to a 1k low-side resistor → 4001:1. MOV L–N: TMOV20RP460E C3260792 (M7; was V20E385P).
- **Separate neutrals (Rev B):** GEN_N and BUS_N each have their own 4 × 1M / 1k divider (GEN_VN_TAP, BUS_VN_TAP). Each VxN input is fed from its own system's neutral tap through 1k/33 nF, and each VxP from the line tap through 1k/33 nF. Gen phases are therefore measured against N-gen and bus phases against N-bus, fully differentially.
- The 0R neutral → GND_AC links are removed. GND_AC is defined by the dividers' 1k low sides and floats at about the mean of the 8 conductors / 4001. The ADE9000 needs all inputs within ±0.6 V of AGND and ±1 V differential. The full-scale tap is about 0.1 Vrms, and even 1 kV of neutral-to-neutral difference gives only ~0.25 V of common mode. The CT inputs are referenced to GND_AC through their burden.
- The 1k/33 nF networks on P and N see slightly different source impedances (tap ∥ 1k each), but both legs match within a system.
- Fuses are external, on fused DIN terminals per the spec. No on-board fuse.

**Current inputs**
- AC1005 CTs on the PCB. Each external 5 A CT secondary (J9) loops through the core: symbol pins P1/P2 = the wire bridge.
- Burden 2 × 24.9R, centre-tapped to AGND. 1k/33 nF anti-alias.
- The BUS ADE current inputs are grounded (voltage-only measurement).

## Front panel (frontpanel.kicad_sch) — Rev B backlit buttons
- 12x **CTS 228EMVARGBFR** (C6077135): IP67 sealed SMD tactile switch, 7.2x6.8 mm, RGB backlight, common anode. Pins from CTS 228E Rev H fig. 1: switch A/B; L1 anode, L2 green K, L3 red K, L4 blue K. Vf is red 1.7–2.4 V, green 1.9–2.4 V, blue 3.0–3.6 V at 20 mA. The switch rating is 12 V / 50 mA and it is used at 3.3 V.
- Switches go to the TCA9555 at 0x20, using its internal pull-ups (unchanged).
- Backlight: all anodes are on BTN_LED_V. +5V is switched through an AO3401A PFET (10k gate pull-up), and an MMBT3904 driven from **CM5 GPIO13 (BTN_BL_PWM, PWM0_CHAN1)** pulls the gate. A 100k base pull-down keeps the backlight off by default. This is the global dimming line.
- Per-LED cathode resistors: R and G 330R (~8.5 mA), B 200R (~8.5 mA). TCA9555 @0x21 holds BTN1–5 RGB + BTN6 R; @0x24 holds BTN6 G/B – BTN11 G; @0x25 holds the rest (12 spare pins). ON = pin output low. **OFF = configure the pin as an input (Hi-Z).** Driving it high (3.3 V) would leave 1.7 V across a red LED, which can glow faintly. TCA9555 I/O is 6 V abs max, so 5 V on the pin is fine.
- Worst case all on: 36 x 8.5 mA = 306 mA from +5V, and 16 x 8.5 = 136 mA sunk by one TCA9555. **Check the TCA9555 total GND current limit (DS)**; lower the current if needed (e.g. 470R).
- Colours: green = running/active, red = alarm, plus blue/mixed (amber = R+G) for extra states. The red-green bi-colour 228EMVARGFR (C6401338) is out of stock at JLC, so RGB is used.
- JLC stock of 228EMVARGBFR is 597 (~49 boards). The footprint and pad numbering need to follow the CTS land pattern (8 pads).
- The 10 discrete front-panel LEDs and their 1k resistors are removed.
- Buzzer: MLT-8530 driven by an MMBT3904 from PB3, with a 1N4148W flyback diode. It runs from +3V3.

## Global open questions / to verify before layout
1. **UNVERIFIED pinouts.** Check these against their datasheets:
   - HR911131A shield-tab pin numbering (footprint); 228EMVARGBFR pad numbering (footprint)
   - M.2 Key B
   - ACT45B choke
   - TMUX1208 pin 3
   - TPS7B6950 DBV pin 4
   - TPS1HTC30 exposed pad
   - USB3-A part
2. **Spec decisions to make:**
   - Loss of always-on 3V3 diode-OR (Rev B 3V3 runs only from the 12 V bus).
   - Modem supply voltage on the M.2 3.3V pins.
3. **Loop compensation** for LM5176 and TPS61500, LM5176 MODE, and TPS56637 MODE: values are placeholders.
4. **Footprints** are set only for passives and well-known packages. Custom ICs need footprints assigned.
5. **LCSC fields** are blank on about half the grouped BOM lines (TBD).
6. **Expander defaults** at power-up are Hi-Z. The AI current sources therefore default ON and the shunts OFF. Confirm this is acceptable.

## Rev 2026-10-24: always-on safety 3.3 V, datasheet pass

### +3V3_SAFE domain (restored battery backup)
- +3V3 (TPS56637 from +12V) and +3V3_BK (LMR36506RRPER, EN tied to VBAT_P, runs 4.2-65 V so covers 6-32 V battery incl. cranking) feed a TPS2116 priority mux -> +3V3_SAFE.
- Powers: STM32H743, FRAM, TPS3431 watchdog, E-stop logic, input/output expanders, front-panel logic. CM5, display, comms, modem stay on +3V3/+5V/+12V.
- LMR36506: RT 40.2k (18286/400^1.021 = 40.4k -> ~400 kHz); FB 100k/43.2k -> 1.0*(1+100/43.2)=3.315 V; L 33 uH; 2x47 uF; CIN 2.2 uF/100 V + 100n.
- TPS2116: VIN1=+3V3 priority, PR1 divider 18.7k/10k -> switchover when +3V3 < 1.0*28.7/10 = 2.87 V (2.64-3.10 V over tol). ST -> PSU_MAIN_OK (STM32 PC3_C, 100k pull-up to SAFE) so firmware knows it is on backup.
- Dissipation on backup ~0.2 W vs ~8.6 W for an LDO from 28 V. BOM add ~$2.56.
- Alternative considered: LMR51606 (C21260865) at 3.265 V + 2x LM66100 ideal-diode OR. Rejected: TPS2116 gives priority (no load sharing), a status pin and one part.
- Back-powering at the domain boundary: every SAFE<->unpowered-domain signal (CM5 SPI/UART/links, CAN/RS-485 TX/RX/DE, ADE isolator I/O) goes through 1k series -> injection < 3 mA/pin into unpowered clamp diodes (within abs max of CM5/transceivers). SPI to CM5 limited to <=4 MHz by the 1k + pin C. Firmware must tri-state these pins when PSU_MAIN_OK is low.

### Calculations replacing placeholders
- LM5176: RT 27.4k; slope 220p; comp 22.1k/33n/220p; sense single 8 mOhm 2512; MODE 93.1k; external BAS70 boot diodes VCC->BOOT1/2.
- TPS56637 (5V, 3V3, modem): EN 121k/16k -> 12*16/137 = 1.40 V > 1.2 V rising (modem: DS-suggested 27k also acceptable, kept 121k/16k for consistency); MODE 0R DNP (float = valid; 100k was in the invalid band); 3.3 uH; feed-forward 100p+20k. 5V FB kept 75k/10k (5.1 V; 73.2k gives 5.0 V if preferred).
- TPS48100: RISCP 35.7k -> Isc = (35.7k*2 uA + 19 mV)/1 mOhm = 90 A.
- TPS61500: VIN max 18 V (abs 20 V) on +12 V OK; FREQ 180k (~580 kHz; 176k low stock); SS 47n; L 10 uH SWPA6045S100MT; SS36 diode.
- TCA9555: 18 mA/pin, ~96 mA/package worst case, under 160 mA GND limit.
- ISOW7841: 75 mA available vs ~42 mA load.

### ERC
- Before: 2 errors (CA-IS3062W pins 11/16 both power-out). After: 0 errors, 0 warnings (kicad-cli --severity-all).
- Auto PWR_FLAGs (gen.py): only on nets with power_in but no power_out, i.e. rails sourced through passive pins (inductor/fuse) or module-internal; list in tools output. Note gen.py was extended with a `types` arg.

### Open items
- (History; superseded by s3c6f OV 32.39-35.74 V.) OVP raised to 33.2 V (done, Rev c). TVS/op-amp items below are RESOLVED in Rev d: SMBJ28CA on VBAT_P and VBAT_ESTOP (schematic) has Vbr min 31.1 V, so it will conduct when charging at 32 V; power_bom lists SMDJ33CA (Vbr min 36.7 V), so the schematic and BOM disagree. Replace with SMBJ33CA/36CA. LM2904DR (non-V, 26 V max) on VBAT_P: change to LM2904B/LM2904V (36 V) or a 40 V op-amp.
- EasyEDA footprints unverified (esp. CTS 228E holes, AC1005 pads, M.2 pinout); 1720819 low stock (50); USB3-A replaced by HC-USB3.0-L168-WP C7501850 (Rev c); V20E385P stock 2 (superseded M7: RV1-RV6 = TMOV20RP460E C3260792, 25 in stock per reviewer).

## Rev 2026-10-24 (b): schematic redrawn with real wires
- tools/layout.py (enabled by gen.WIRED=True): ICs anchor functional clusters; passives attach to the IC they share a local net with (chains followed), decoupling caps attach to the IC whose rail they bypass and are wired to its rail pin. Clusters flow left->right in design order, wrapped onto the smallest A-size paper.
- Router: A* maze router on the 1.27 mm grid; symbol bodies and label/power-symbol areas are obstacles; other nets may only be crossed perpendicular at straight segments (no T onto a crossing); bend and crossing penalties; junctions at every node of degree >= 3.
- Labels kept only for: off-sheet nets (global labels), power/ground and isolated rails (power symbols; rails with a driver/PWR_FLAG such as GND_AC use power symbols named for the rail), wide buses (SPI/I2C/DSI/LVDS/MDI/expander ports -> stub + local label), and the few nets the router could not complete (label fallback, 10 nets total).
- Verified: netlist partition identical to the label-only version (1082 nets), ERC 0 errors/0 warnings, BOM identical. Local nets lost their label names (now auto Net-(...)).

## Rev 2026-10-24 (c): OVP raised for 24 V charging; USB3-A part swap
- (History; superseded by s3c6f R3 9.76k.) LM74800 OV/UV ladder 191k/45.3k/10k -> 210k/49.9k/10k: OV 33.2 V rise / 30.5 V release, UV 5.55 V / 5.10 V (see Ideal diode section).
- Fixed wrong LCSC codes in gen.py RLCSC: 191k was C25860 (actually 1.1k 0402), now C22932. 45.3k was C23171 (actually 432k), now C23058, which affects the +3V3 FB R23.
- (History, at OV 33.2 V; now OV max 35.74 V.) Voltage ratings on VBAT_P at 33.2 V + margin: BSC070N10NS5 100 V, LM5176 55 V, LMR36506 65 V, TPS1HTC30 64 V, TPS48100, INA281 and SS110 fine, EEHZA1H101P 50 V, 10u 1210 CL32B106KBJNNNE 50 V, 100n 0603 C14663 50 V, 2.2u 1206 100 V: all OK.
  NOT OK: SMBJ28CA (VBAT_P, VBAT_ESTOP; Vbr min 31.1 V) and LM2904DR (26 V supply). See Open items. 0805 100n on VBAT rails has no LCSC code assigned; specify 50 V or higher.
- J11 USB3 Type-A: Molex 48393-0003 / C3032863 (no stock) -> Hong Cheng HC-USB3.0-L168-WP, LCSC C7501850 (JLC extended, 20,774 stock, $0.1249 qty 1 on 2026-10-24). THT right-angle, 9 pins + 2 shell pegs.
  Per DS: 1 VBUS, 2 D-, 3 D+, 4 GND, 5 SSRX-, 6 SSRX+, 7 GND_DRAIN, 8 SSTX-, 9 SSTX+, shell = pad 10 -> CHASSIS. Net mapping unchanged.
  Footprint genctl.pretty/USB3_A_HC-USB3.0-L168-WP.kicad_mod comes from EasyEDA C7501850 (pitch 2.0/2.5 mm, rows 1.5 mm apart, shell 13.14 mm, all consistent with the DS). Check pin-1 orientation against the DS drawing before layout. Rated op temp is only -25..70 C.
- Cost total now $755.36 (comms +$0.12 for the now-priced USB-A; resistors sit in the misc lump).

## Rev 2026-10-24 (d): 33 V-safe TVS, 36 V op-amp, 0805 cap codes
- All 18 SMBJ28CA -> SMBJ33CA, Brightking C78420 (JLC extended, 132,283 stock, $0.0575). That covers VBAT_P, VBAT_ESTOP and the 16 output TVS, which also see raw battery when on. Vbr min 36.7 V > 33.2 V OVP (now > 35.74 V OV max, s3c6f); Vc 53.3 V @ 11.3 A < TPS1HTC30 64 V / FETs 100 V. Same package (DO-214AA), footprint Diode_SMD:D_SMB unchanged.
- power_bom aligned to the schematic: post-cutoff TVS is SMBJ33CA (SMB), not SMDJ33CA. SMB 600 W is enough because the input TVS (now SMDJ36CA, s3c6f) absorbs suppressed transients and the LM74800 opens on OV (no longer true for an unsuppressed load dump, which is out of scope: see docs/INSTALL_SAFETY.md and the s3c6f section), so the downstream TVS only takes cutoff overshoot and local inductive transients (mJ level).
- U24-U26 LM2904DR -> LM2904BIDR (TI) C1849422 (extended, 4,110 stock, $0.1046), 3-36 V supply (datasheets/lm2904b.pdf, Family Comparison table: LM2904 = 26 V). SOIC-8 pinout identical (1 OUT1, 2 IN1-, 3 IN1+, 4 V-, 5 IN2+, 6 IN2-, 7 OUT2, 8 V+).
- All 0805 100 nF (22 pcs, incl. BAT_IN/VBAT_P/VBAT_ESTOP/DPX_VI) -> Samsung CL21B104KCFNNNE 100 V X7R C28233 (basic, 1.5M stock), via gen.CLCSC.
- Cost total $755.07 (was $755.36): outputs and power TVS cheaper, inputs op-amp +$0.12.

## Rev 2026-10-24 (e) - modem removed, router power, CM5 reflash/control, 5V hold-up, no USB hub, 10 aux outputs

**Removed:** M.2 Key B socket, nano-SIM + SRV05-4, 3.8 V TPS56637 buck/inductor/ceramics/1000 uF bulk, MDM LED, U.FL/standoff BOM rows,
MODEM_PWR_EN. Also removed USB2514B hub (+24 MHz crystal, straps), USB3 Type-A host port, TPS2051C, its 100 uF cap and ESD. CM5 USB3 SS pairs NC.
**USB:** USB-C service = CM5 USB2 OTG (rpiboot with nRPIBOOT button) is the only external USB. CM5 USB3-0 HS -> internal SM04B header
(display touch), USB3-1 HS -> internal SM04B spare; each with USBLC6-2SC6. Header VBUS = +5V unswitched.
**Router:** external router on RJ45, powered from ROUTER_12V: TPS1H200A-Q1 (C2653785) from +12V, RCL 1.0k -> 0.8*2500/1k = 2.0 A limit
(+ thermal shutdown = electronic fuse), SS110 freewheel, 10 nF, FAULT wired-OR to OUT_FAULT_N. IN = ROUTER_12V_EN, 100k pull-up to +3V3_SAFE
so it is ON at power-up (TCA9555 pins are Hi-Z inputs at reset); STM32 power-cycles it via TCA9555 @0x25 P04. Connector WJ15EDGRC-3.81-02P (C8387) +
plug WJ15EDGK-3.81-02P (C8466), same 3.81 family as CAN/RS-485/expansion (polarized plug; no locking flange).
**CM5 <-> STM32 lines:**
| Function | CM5 | STM32 / other | Circuit |
|---|---|---|---|
| UART (bootloader-capable) | GPIO14 TXD0 / GPIO15 RXD0 | PA10 USART1_RX / PA9 USART1_TX | 1k series each (moved from PD5/PD6; MUX_A0/A1 moved PA9/PA10 -> PD5/PD6) |
| BOOT0 | GPIO27 CM5_BOOT0 | BOOT0 | 1k series; existing 10k pull-down -> 3.0 V when CM5 drives high, 0 V when CM5 off/Hi-Z |
| NRST | GPIO22 CM5_NRST | NRST | 10k -> MMBT3904 base (100k pull-down), collector on NRST (open-drain; cannot back-power) |
| Heartbeat | GPIO26 CM5_HB | PC2_C (was MCU_SPARE1; Header B pin 3 now NC) | 1k series, 100k pull-down at MCU |
| Power-fail warning | GPIO17 CM5_PWR_FAIL (in) | TCA9555 @0x25 P07 PWR_FAIL_MCU (INT) | TPS2121 ST -> two NPN inverters, pull-ups to CM5_3V3 / +3V3_SAFE; high = on hold-up |
| Hard power-off | PMIC_Enable (pin 99, int. 100k to 5V) | TCA9555 @0x25 P05 CM5_OFF | 10k -> NPN o/c; Hi-Z = CM5 on |
| Power button | PWR_Button (pin 92) | TCA9555 @0x25 P06 CM5_PWRBTN_MCU | 10k -> NPN o/c (in parallel with SW) |
SWD header kept; JP1 reduced to CM5 SWD (pins 5-8 NC). Touch power TPS22918 now shares PANEL_VDD_EN (frees GPIO17).
Note: H743 bootloader also scans USART1 PB14/PB15 (DI10/DI11) and other ports when BOOT0=1; field input activity could select the wrong port - CM5 should
assert BOOT0/NRST and send 0x7F promptly.
**Hold-up (CM5 only, +5V_CM5):** CM5 datasheet: ~0.9 A (4.5 W) operating (typical, not for sizing copper), ~0.4 A idle, 1.3 mA with PMIC_EN low. 10 s at 4.5 W = 45 J.
Bulk options rejected: 5 V bulk gives only 0.5*C*(5.0^2-4.75^2) = 1.2 J/F (needs ~40 F); VBAT_P bulk 35->8 V needs ~0.15 F/50 V. TPS61094 rejected
(1.7-2.6 A valley limit -> <1 A at 5 V). Chosen: 2x Eaton HV1030-2R7106-R 10 F/2.7 V in series (5 F, 10k balancing), charged from +5V via SS34 + 50R
(<=92 mA, tau 250 s) to ~4.9 V; TPS61023 boost (C919459, Vout = 0.595*(1+715k/100k) = 4.85 V, 1 uH FNR5020S1R0MT) -> TPS2121 (C485916) IN2;
IN1 = +5V with PR1 33.2k/10k (IN1 preferred above 4.58 V rising / 4.49 V falling), RILM 29.4k = 3.5 A, 5 us switchover.
Usable energy 0.5*5*(4.9^2-2.7^2) = 41.8 J x 0.88 = 36.8 J -> ~8 s at 4.5 W, ~18 s at 2 W idle (-10% cap tol: ~7 s). TPS61023 output limit at 2.7 V in:
(1-D)*(ILIM_min 2.7 A + ripple/2) ~ 1.5 A -> 7 W, OK. Hold-up isolated from +5V (no backfeed into TPS56637/USB/fan). STM32 is NOT held up (accepted:
the LM5176 already rides through cranking down to ~4 V; hold-up covers full battery disconnect). On PWR_FAIL the CM5 runs `shutdown -h`; if power returns
after halt the STM32 sees no heartbeat and pulses CM5_OFF (PMIC_EN low) to reboot it. Supercaps are not JLC-stocked: hand-solder (DigiKey $3.39 qty-1), 65 C rated - mount away from hot parts.
**Outputs:** aux smart outputs 8 -> 10 (15 TPS1HTC30 + E-stop trip). AUX9/AUX10 enables come from TCA9555 @0x25 P10/P11 (no free STM32 pins) through the
LVC541 watchdog gate. SNS mux now 16/16 used (MUXA 8, MUXB 7 + E-stop trip). Readback: @0x23 all 16 pins, AUX10_RB_N on @0x25 P12.
J6B = AUX7-10 + 2 GND, J5B = 6 GND (was 4 + 2 NC): output pins 16 (+ fuel/crank on J4), returns 8; connectors unchanged (4x KF2EDGRM-5.08-6P + plugs).
**Cost:** $755.07 -> $769.41 (comms 36.58 -> 28.45, outputs 145.41 -> 159.66, power 44.61 -> 52.83).

## Rev 2026-10-24 (f) - footprint verification fixes (see docs/FOOTPRINT_CHECK.md)
- CM5 connector B: new genctl:DF40C-100DS-0.4V_B with pads 101-200. Before this, all of conn B was unconnected on the PCB.
- Field I/O headers J17-J22 and J24-J27 now use KF2EDGRM-5.08-6P (was 3.81 mm WJ15).
- J0, J4, J7 and J8 now use the true Phoenix PC 5/4-GF-7,62 (1720819) pattern: 3 pins per potential, Ø1.3 mm holes, Ø3.2 mm flange holes. J7/J8 had been on a 5.08 mm Kefa footprint with a 2.6 mm gap at 600 V.
- HR911131A locating holes changed to NPTH.
- Removed the unused M.2, SIM and USB3-A footprints.
- Power BOM 22u price corrected. Grand total is now $769.87.
- Open item (resolved rev g): SOIC-16W isolator pads gave a 7.25 mm gap; see docs/ISOLATION_CHECK.md.

## Rev 2026-10-24 (f2) - schematic beautification (connectivity unchanged)
- Each functional group (an anchor IC with its satellites) is drawn inside a dashed, titled box. Repeated channels (outputs, inputs) tile into rows.
- Wires are kept inside one group. Nets that span groups, or would need a detour longer than 36 grid cells per connection, use short orthogonal stubs with local labels.
- There is a second routing pass that blocks the label areas of those nets, so wires no longer run through their text.
- Big-IC Ref/Value fields are moved below the body, off the top-pin numbers.
- Verified with tools/netcompare.py (pre-beautify netlist vs new):
  - 1030/1030 nets, identical node sets, 0 named nets renamed.
  - 419 nets that were auto-named Net-(...) now carry their design net name because they are labelled.
- ERC is 0/0.

## Rev 2026-10-24 (g) - isolation footprint (see docs/ISOLATION_CHECK.md)
- ISOW7841 / ISO7741 now use genctl:SOIC-16W_7.5x10.3mm_P1.27mm_HV_Slot: TI DW0016B "HV/isolation option" pads (1.65 x 0.6 at 9.75 mm) -> 8.1 mm copper gap (was 7.25 mm), plus a 2.0 x 21.0 mm routed slot and an all-layer copper keep-out between the rows. Netlist identical, ERC 0/0.
- Barrier: plan >=13 mm (FR-4 IIIa, 600 V working, reinforced) instead of 12 mm, or call out CTI>=400 laminate. J7/J8 inter-phase slot. AC1005 CT insulation unproven (open).

## Rev 2026-10-24 (h)
- Hold-up: 2x HV1030 10F/2.7V (65 C, not JLC) -> 2x JIERONG JRCD3R0206N120030E 20F/3.0V, 85 C 1000 h, LCSC C7471020 (JLC stock 4176). Series = 10 F at 4.9 V (2.45 V/cell, under 3.0 V rating; check 85 C derating). Usable energy 0.5*10*(4.9^2-2.7^2) = 83.6 J, x0.88 boost eff = 73.6 J -> ~16 s at 4.5 W, ~13 s at -20% C. Charge via 50R: tau = 500 s (~25 min to full; first-boot shutdown time is shorter). Footprint CP_Radial_D12.5mm_P5.00mm - verify lead pitch.
- BOOT0: DI3-6 (PE11-14 = SPI4 bootloader) and DI8-11 (PB10/11 USART3, PB14/15 USART1-alt; bootloader v9.1 echoes TX on PB14) now go through 1k series R (nets DIx_N_M) so a pin the bootloader drives can only fight the 74HC14 at <=3.3 mA. Firmware/CM5: send 0x7F straight after reset-into-bootloader, check ACK, retry with NRST. No free pins to move the DIs.
- STM32 hold-up: not added. SAFE rail runs to ~5.1 V input (LM74800 UV) so it rides cranking; below that the outputs drop and fuel de-energizes (fail-safe). Use BOR + FRAM state save. Option if wanted later: feed the SAFE LDO from the held-up rail.
- Internal USB headers: each fed from its own TPS2553DBVR (C55266), ILIM 40.2k = ~0.68 A nominal, EN from TCA9555 @0x25 P13/P14 with 100k pull-up to +3V3_SAFE (on by default), FAULT wired to OUT_FAULT_N, 1u in / 10u out. USBLC6 VBUS pin moved to the switched rail.
- Netlist changes are intentional; tools/netcompare_sig.py (refdes-independent) shows only these parts changed.

## Rev 2026-10-25 (i) - SN65DSI83 REFCLK oscillator fitted (SUPERSEDED by Rev (j): Y4 back to DNP, R113 restored)

Source: TI SN65DSI83 datasheet SLLSEC1I (rev. Oct 2020), pin table (REFCLK, H2), Sec. 6.x REFCLK timing, Sec. 7.3.1, CSR map; Abracon ASDMB datasheet (initial release 1/8/2025).

- **Fitted:** Y4 ASDMB-25.000MHZ-LC-T, which is 25 MHz, ±50 ppm, −40..+85 °C, powered from +1V8_DSI with OE tied high. Its output goes through R531 (22R, at the oscillator) to REFCLK (U21 H2). C286 (100n) decouples Y4's VDD. None of these parts is DNP any more.
- **Removed:** R113, the 10k REFCLK pulldown. The datasheet requires the pulldown only "if an external reference clock is not used". It also asks for the clock source "as close as possible with a series resistor near the source". A pulldown on a driven clock line only adds load, so R113 is gone from the schematic, the board and the BOMs.
- **Register settings (all registers are written over I2C at 0x2C, with PLL_EN = 0 and REFCLK already stable):**
  - HS_CLK_SRC, 0x0A bit 0 = 0, so the LVDS clock comes from REFCLK. This is the reset default.
  - REFCLK_MULTIPLIER, 0x0B bits 1:0 (00 = ×1, 01 = ×2, 10 = ×3, 11 = ×4). DSI_CLK_DIVIDER, 0x0B bits 7:3, stays 00000.
    - The panel needs 66.3–78.9 MHz (72.4 MHz typ). From a 25 MHz reference the choices are 25/50/75/100 MHz, so the plan is **×3 = 75 MHz** (0x0B = 0x02).
    - The CM5 DSI video timing must then be generated for a 75 MHz pixel clock: blanking is adjusted so the frame rate stays about 60 Hz.
  - LVDS_CLK_RANGE, 0x0A bits 3:1 = 010 (62.5–87.5 MHz). The table is 000 = 25–37.5, 001 = 37.5–62.5, 010 = 62.5–87.5, 011 = 87.5–112.5, 100 = 112.5–137.5 and 101 = 137.5–154 MHz.
  - CH_DSI_CLK_RANGE, 0x12, is still set to the DSI channel A clock range.
  - Set PLL_EN (0x0D bit 0) last, then wait until it reports locked (≥3 ms). The PLL must be disabled whenever 0x0A or 0x0B is changed.
  - The pixel/LVDS clock range with REFCLK is 25–154 MHz. REFCLK also accepts SSC (0.5–2 % center spread, 30–60 kHz).
  - A benefit of using REFCLK is that the DSI clock lane no longer has to run continuously in HS mode.
- **OPEN, datasheet mismatch to resolve before ordering:**
  - DSI83 REFCLK limits: tr/tf 100 ps–1 ns and peak-to-peak phase jitter ≤50 ps.
  - At 1.8 V and 15 pF, the ASDMB specifies Tr 1.8 ns typ / 3.0 ns max and Tf 1.0 / 3.0 ns, so its rated edges exceed the 1 ns limit. The real load (one BGA input plus about 3 mm of trace, roughly 3–5 pF) will be faster than the rated figure, but that is not guaranteed.
  - The ASDMB gives no peak-to-peak jitter figure, only 60 ps cycle-to-cycle and 10 ps RMS period jitter at 100 MHz, so compliance is unproven.
  - The candidate alternate is SiTime SiT1602BI-13-18S-25.000000 (2.5×2.0, 1.8 V, ±50 ppm, −40..85 °C): peak-to-peak period jitter 30 ps max at 1.8 V and Tr/Tf 1.3 ns typ / 2.5 ns max. Its edge rate is also not guaranteed under 1 ns at 15 pF.
  - Either part must be checked on the bench: scope the edges at H2 and confirm the PLL locks.
  - The footprint and pinout are standard 4-pad 2520 (OE, GND, OUT, VDD), so the two parts swap without a board change.


## Rev 2026-10-25 (j) - Review C1: SN65DSI83 1.8 V CMOS I/O level translation

Problem (review C1): SN65DSI83 CMOS pins (SCL/SDA/EN/IRQ/ADDR/REFCLK) are 1.8 V logic, abs max 2.175 V, VIL 0.3xVCC / VIH 0.7xVCC (SLLSEC1I). The CM5 GPIO bank stays at GPIO_VREF = 3.3 V, so EN, SCL/SDA (CM5 1.8k on-module pull-ups to 3.3 V) and IRQ (R115 10k to CM5_3V3) put 3.3 V on 1.8 V pins. Only 1.8 V rail: +1V8_DSI (U20 TLV75518, EN = +3V3).

Sources read this session: SN65DSI83 SLLSEC1I; PCA9306 SCPS113O; SN74LVC1T45 SCES515N; SN74LVC1G34 SCES519O; SN74AUP1G34 SCES603K. SN74AUC1G34 datasheet could not be downloaded (ti.com returned HTML).

- **I2C (U77 PCA9306DCUR, LCSC C33196):**
  - Pins (DCU): 1 GND, 2 VREF1 = +1V8_DSI, 3 SCL1 = DISP_SCL_1V8 (U21.H1), 4 SDA1 = DISP_SDA_1V8 (U21.J1), 5 SDA2 = DISP_SDA, 6 SCL2 = DISP_SCL, 7 VREF2 + 8 EN = PCA_VREF2.
  - R532 200k from PCA_VREF2 to CM5_3V3, C287 100 pF at VREF2 (SCPS113O Fig 8-1 and layout section; the brief's "0.1 uF" was from memory, and the datasheet value is 100 pF). C288 100n on VREF1.
  - R119/R120 2.2k fitted, pulling the 1.8 V side to +1V8_DSI. The 3.3 V side (CM5 GPIO2/3, touch J15) keeps the CM5 1.8k pull-ups.
  - VREF1 = 1.8 V is inside the 1.2 V..VREF2-0.6 V window.
  - Sequencing: EN follows CM5_3V3 through 200k. If +1V8_DSI is still 0 V, the pass-FET gate (VREF1 + Vth) holds the 1.8 V side near 0.6 V at most, below the DSI83 abs max. The DSI83 is only accessed after EN, so this is not a functional issue. NOT bench-verified.
- **EN (U78 SN74LVC1T45DBVR, C7843):**
  - VCCA = CM5_3V3, A = DSI83_EN (GPIO6, U9.30), DIR = VCCA (high = A->B, DIR referenced to VCCA per SCES515N), VCCB = +1V8_DSI, B = DSI83_EN_1V8 (U21.B1).
  - R533 47k pulldown at U21.EN against the internal 200k pull-up gives about 0.33 V, below VIL 0.54 V. C116 10 nF stays at U21.EN; R114 100k stays on the GPIO6 side.
  - Sequencing: if either VCC is 0 V, both ports are Hi-Z (SCES515N), so EN is held low by R533 until +1V8_DSI is up. The datasheet requires EN to rise after VCC >= 1.65 V. Because the B output can only drive once VCCB is up, EN rises together with +1V8_DSI only if GPIO6 is already high at that moment. +1V8_DSI comes up with +3V3 at power-on, long before Linux drives GPIO6, and R114 holds GPIO6 low. Firmware must still not raise GPIO6 before +1V8_DSI is up (it is always up when +3V3 is). The power-up timing is NOT measured.
- **IRQ (U79 SN74LVC1T45DBVR):**
  - VCCA = +1V8_DSI, A = DSI83_IRQ_1V8 (U21.J9), DIR = VCCA (A->B), VCCB = CM5_3V3, B = DSI83_IRQ (GPIO7, U9.37).
  - R115 changed from 10k to CM5_3V3 to 100k to GND on the 1.8 V side; the ref is kept so annotation stays stable. U21 IRQ is Hi-Z by default and active high, so the pulldown defines an idle low.
  - Decoupling: C289-C292 100n, one per VCC pin.
- **REFCLK (revised 12:38 after driver research, /workspace/research/dsi83_fix.md addendum "REFCLK from DSI clock"):**
  - The stock Linux sn65dsi83 driver (mainline and rpi-6.12.y) ALWAYS sets HS_CLK_SRC = 1 (CSR 0x0A bit 0, LVDS clock derived from the DSI HS clock) and has no external-REFCLK option. An oscillator would be unused without a driver patch. No REFCLK buffer is added.
  - **Default build:** REFCLK (U21.H2) strapped to GND by R113 10k, as the datasheet requires when REFCLK is unused (SLLSEC1I p.5). No oscillator populated.
  - **DNP footprint option:** Y4 25 MHz 1.8 V oscillator -> R531 22R -> REFCLK, plus C286 100n, kept exactly as in Rev (i) but all DNP.
  - Fitting Y4 later needs (a) a patched driver (HS_CLK_SRC = 0, REFCLK_MULTIPLIER; Rev (i) register plan) and (b) an oscillator with tr/tf <= 1 ns at 1.8 V. The ASDMB is rated 1.8-3 ns at 15 pF, so a faster part is needed. A SN74LVC1G34/AUP1G34 buffer was considered, but TI specifies no output tr/tf for either (SCES519O, SCES603K), so it could not be verified and was dropped.
  - DSI-clock mode constraints: the DSI HS clock must be exactly 3x the pixel clock for single-link 24 bpp at 4 lanes (DSI_CLK_DIVIDER, 0x0B bits 7:3), and the CM5 DSI clock lane must run continuously in HS mode. The CM5 PLL rounding of the requested DSI clock must be confirmed on hardware (panel 66.3-78.9 MHz pixel clock).
- **ADDR:** ball A1 tied to GND, giving 0x2C. Checked in the netlist.
- **Checks:** ERC 0 errors. Netlist diff vs the previous revision shows only the intended nets (DISP_SCL/SDA_1V8, DSI83_EN/IRQ_1V8, PCA_VREF2 [auto-named Net-(U77-EN)], R113 back on DSI83_REFCLK). Pin-by-pin rail check: /workspace/w8/c1_railcheck.txt, 0 connectivity mismatches.
- **Unverified:** JLC basic/extended class and stock for C33196, C7843 and C840096 (LCSC numbers for PCA9306/LVC1T45 are taken from the brief); PCA9306 behaviour with VREF1 unpowered; the real EN power-up timing; the I2C rise time at 400 kHz with 2.2k + 1.8k and unknown bus capacitance.

### s3c6f (2026-10-27): D1 SMDJ36CA, R3 9.76k, supply assumptions, open risks
- D1 SMDJ58CA (C152071) -> **SMDJ36CA (Littelfuse, LCSC C224075, Extended)**, same D_SMC footprint, D1 GND vias untouched. Reason: SMDJ58CA clamps at 93.6 V, above the 70 V abs max of U1 A/VS/VSNS/SW/C (TI SNOSD95C p4). SMDJ36CA: VR 36 V, VBR 40.0-44.2 V, VC 58.1 V @ 51.6 A, 3 kW (product page/tables per review/s3c6c/divider_check.md; manufacturer PDF NOT opened; JLCPCB parts search 2026-10-27 MEASURED: stock 4730, qty-1 $0.5438).
- R3 10k -> **9.76k (0603WAF9761T5E, LCSC C23128)**. Recomputed here (OV = Vth·ΣR/R3, UV = Vth·ΣR/(R2+R3), 1 % R worst case, DS p5-6 thresholds) [INFERRED, matches the reviewer]: OV rising 32.39 / 34.01 / 35.69 V (35.74 V with 200 nA leakage), OV falling 29.57 / 31.22 / 32.65 V (reviewer 32.70 with leakage), UV rising 5.32 / 5.56 / 5.82 V (5.86 with leakage).
- Max operating battery 31 V. OV-trip minimum margin vs 31 V = 32.39 − 31 = **1.39 V** (4.5 %) [INFERRED]. Resistor TCR is not in the stack; 0.1 % resistors are an option.
- After an OV trip the load may stay off until the battery falls below OV falling (as low as **29.57 V** min) [INFERRED, divider_check.md §7].
- **OPEN RISK (needs surge test):** D1 clamp (old SMDJ58CA 93.6 V; new SMDJ36CA 58.1 V per product page, PDF not opened) can still reach VBAT_P during the 4-5.4 µs OV turn-off (DS p7). LM2904B on VBAT_P is 40 V abs max (Compliance citation, not opened) and D2 SMBJ33CA clamps at 53.3 V. NOT VERIFIED.
- **Supply assumption:** a 3 kW SMC TVS will not survive an unsuppressed 24 V alternator load dump. The board assumes a battery-backed, suppressed 35 V-class supply; it is NOT designed for an unsuppressed load dump (Ethan's decision 2026-10-27). See docs/INSTALL_SAFETY.md.
- SUPERSEDED (N4/m7-sch 3c): no on-board fuse; battery net BAT_IN; the battery lead is fused in the power box (F1) at <=10 A standard (non-time-delay), >=58 V DC. Historical: F1 is **10 A** (Ethan's requirement). Any 5 A F1 figure in reviewer files (review/cur/final_power_spec.md) is not adopted.

### Future work: inline surge module (short faithful summary of review/hv/load_dump_external.md §(b); see that file for SM8S datasheet figures)
**Where it goes.** Fit it on the battery positive feed downstream of the external 30 A battery fuse, at the point that feeds *both* J0 (BAT_IN) and the E-stop/VBAT_ESTOP branch. If the TVS fails short, the 30 A fuse clears it.

**What it must handle.** For 12 V it should withstand ISO 16750-2 Test A 12 V: up to 101 V, Ri ≥ 0.5 Ω, 400 ms, 10 pulses. For 24 V the equivalent is up to 202 V, Ri ≥ 1 Ω, 350 ms. With either system, it should hold the bus ≤ 50 V. The 50 V caps and VBAT_DD are the weakest pre-cutoff parts; the location of the 50 V EEHZA1H101P is UNVERIFIED, so that number needs checking.

**Suggested approach.** The simplest fit is a bank of automotive load-dump TVS (Vishay SM8S series, DO-218AB, AEC-Q101). The best is an active surge stopper with series FETs, e.g. TI LM74800 with OV cutoff (the 200 V topology in SNOSD95C Fig 10-25, p29) or LTC4366. The active route also covers 24 V Test A, where TVS energy gets large. SM8S33A preferred over SM8S36A (see the source file for datasheet figures and LCSC listings).

**Limits.** A 48 V jump start on a 24 V system (TI SNOSD95C p34) would destroy any 33-36 V TVS. So would the 24 V 58-65 V suppressed level. For 24 V systems the active surge stopper is required, not a TVS (INFERRED).
(ISO levels are SECONDARY sources, not read from the standard; separate project, not part of this board.)

## m7-sch Batch 17 (2026-11-21)
- C74/C75 hold-up supercaps: Vishay MAL223051003E3 (230 EDLC-HV, doc 28450 rev 19-Jun-2024): 20 F -20/+50 %, UR 3.0 V (65 °C) / 2.6 V (85 °C, 185 °F), ESRdc 38 mOhm, ESRac 22 mOhm, case 16x20 (Dmax 16.5, Lmax 22), F 7.5 ±0.5 mm, Ød 0.8, IL 75 µA after 72 h. Mounted upright (22 mm max fits where the 33.5 mm 12.5x30 part was 3.1 mm too tall; flat mount D-m7-21 dropped). 2.45 V/cell at 4.9 V nominal. Balance R78/R79 4.7k (Batch 22, R9-N8; was 10k): worst-case leakage mismatch 75 µA shifts a cell by up to 4.7k x 37.5 µA = 0.18 V, so the high cell is ~2.63 V at a 4.9 V stack (INFERRED; was ~2.82 V with 10k) - still 0.03 V over the 2.6 V 85 °C rating in that corner, well under 3.0 V at 65 °C; bench-check leakage. Standby drain 4.9 V / 9.4k = 0.52 mA (was 0.245 mA; +0.28 mA, +1.3 mW). Footprint CP_Radial_D16.0mm_P7.50mm; board still has D12.5/P5.0 until layout (D-m7-24).

## m7-sch Batch 18-21 (2026-11-21): DI_BIAS eFuses U89/U90
- U89 (DI_BIAS_A) and U90 (DI_BIAS_B) are TI TPS26621DRCR eFuses (I(OL) 0.20 A with 33.2k, auto-retry), fed VBAT_P -> Q36/Q39 -> eFuse IN, with F101/F102 1210L020/72 PTCs downstream as backup. Approved by Safety Round 7 (S7-N13).
- **U89/U90 must stay on VBAT_P behind U1 LM74800 (J1 -> BAT_IN -> Q1 -> VBAT_DD -> Q2 -> VBAT_PS -> R555 -> VBAT_P) and must never be moved to BAT_IN:** the TPS26621 abs max is 62 V (IN to RTN), below the ~64.5 V clamp of the 40 V TVS class on BAT_IN.
- Batch 21: RTN (pin 5), PowerPAD (pin 11) and OVP (pin 3) are tied to GND. TI SLVSDT4F §9.3.8 says this disables the eFuse's own input reverse-polarity protection (and the part is damaged by a reverse input in that configuration); reverse polarity is blocked upstream by U1/Q1. OVP tied to RTN = OVP not used (§9.3.2, pin table). The PowerPAD must go to the GND plane with thermal vias (D-m7-27, required before fab). Bench B-m7-21: 36 V chassis short on each rail for several minutes, case temperature in °F.

