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
4. **E-stop hold-up cap.** Changed to **10 µF 50 V 1210**. The BOM part (CL31B106KAHNNNE) is rated 25 V, but VBAT_P can reach the 30.3 V OV threshold.
5. **4th SN74LVC1G08** gates MCU_TRIP with the watchdog (WDO), so a hung MCU cannot fire the trip.
   - The 555 hardware path still goes straight to the BAT54C OR, as in estop_notes v5.
6. **Watchdog inverter.** An MMBT3904 drives the LVC541 /OE from WDO. A watchdog fault puts all small-output enables into Hi-Z, and 100k pull-downs turn the outputs off.
7. **RS-485 DIP switches.** Added one for the 120R termination and one for the 680R fail-safe bias.
8. **SMBJ28CA on VBAT_P** (per outputs BOM), replacing the SMDJ33CA in the spec.
9. **ADS1115 ALERT pins left NC.** The ADCs are polled. ADS1115 ALERT is push-pull by default, so it cannot share the I2C_INT_N wire-OR.
10. **Two 2 mΩ buck-boost sense resistors.** One is fitted and one is DNP (BOM qty 2).

## Power (power.kicad_sch)
**Input protection**
- J0 → 10 A ATO blade fuse in Keystone 3557-2 clips → VBAT_F.
- SMDJ58CA (bidirectional) TVS on VBAT_F.

**Ideal diode (LM74800-Q1)**
- Two BSC070N10NS5 back-to-back, common drain (VBAT_DD).
- VS, A and VSNS all on VBAT_F.
- CAP: 100 nF from CAP to VS (*assumed*, typical application).
- SW → 191k / 45.3k / 10k ladder to EN/UVLO and OV:
  - OV = 1.231 × 246.3/10 = **30.3 V**
  - UV = 1.231 × 246.3/55.3 = **5.5 V**
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
- Second TPS56637RPAR (6 A part) from +12V. Per DS Table 4 for 3.3 V: FB 45.3k/10k (3.32 V), L 2.2 µH (Sunlord MWSA0503S-2R2MT, Isat 7 A), 3x22 µF out, 2x10 µF in, feed-forward 150 pF + 20k (check the topology against the DS figure). EN 100k/27k, MODE 100k (placeholder, same as the 5V rail).
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
- Fan header on Fan_PWM/Fan_Tacho.
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
- ADDR = GND (address 0x2C). REFCLK = GND (clock taken from DSI). RSVD2 = GND.
- EN: 100k + 10 nF RC.
- LVDS lanes go to the 40-pin FPC per the RVT121 datasheet:
  - Lanes: Rxin0 on 8/9, Rxin1 11/12, Rxin2 14/15, CLK 17/18, Rxin3 20/21.
  - Power and ground: VDD on 2–4; GND on 6, 7, 10, 13, 16, 19, 22, 25, 28 and 31–33.
  - All other pins NC.

**Panel and touch power**
- TPS22918 switches with QOD tied to VOUT and CT = 1 nF.
- The touch FPC is used in I2C mode: USB pins NC, RST/INT pulled up to +3V3_TOUCH.

**Backlight (TPS61500)**
- VIN = +12V. EN = BL_PWM.
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
- ILIM 40.2k. LATCH = GND (auto-retry). SNS 1.1k, then 1k into the TMUX1208s.
- SS110 freewheel diode, SMBJ28CA TVS.
- **Open:** the exposed pad is not modelled; check the datasheet for whether it goes to GND or VS.
- **Open:** TMUX1208 pin 3 is missing from the datasheet table. It is tied to GND here; verify.

**E-stop trip (follows estop_notes v5)**
- Supply: TPS7B6950 (SOT-23 pin 4 assumed NC) fed from VBAT_P through SS110 and a 10 µF/50 V hold-up cap.
- Detection and timing:
  - VBAT_ESTOP → 47k/10k → NPN holds the 555 RESET low.
  - TRIG RC is 100k/100 nF. One-shot = 1.1 × 200k × 10 µF ≈ 2.2 s.
- Output:
  - BAT54C OR of the 555 and the gated MCU_TRIP → TPS1HTC30 (ILIM 13.3k).
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

**ADE9000 ×2 (GEN and BUS)**
- Shared SPI bus. Clock: 24.576 MHz crystal on the GEN ADE; its CLKOUT feeds the BUS ADE's CLKIN.
- PM0 = PM1 = 0 (normal mode). NC1/NC2 tied to AGND.
- AVDDOUT, DVDDOUT and REF each get 4.7 µF + 100 nF.

**Voltage inputs**
- Per phase: 4 × 1M (1206 HV) to a 1k low-side resistor → 4001:1. V20E385P MOV L–N.
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
- OVP 30.3 V vs 32 V max operating battery: either raise OVP or define 30 V max.
- EasyEDA footprints unverified (esp. CTS 228E holes, AC1005 pads, M.2 pinout); 1720819 low stock (50); USB3-A C3032863 no stock; V20E385P stock 2.

## Rev 2026-10-24 (b): schematic redrawn with real wires
- tools/layout.py (enabled by gen.WIRED=True): ICs anchor functional clusters; passives attach to the IC they share a local net with (chains followed), decoupling caps attach to the IC whose rail they bypass and are wired to its rail pin. Clusters flow left->right in design order, wrapped onto the smallest A-size paper.
- Router: A* maze router on the 1.27 mm grid; symbol bodies and label/power-symbol areas are obstacles; other nets may only be crossed perpendicular at straight segments (no T onto a crossing); bend and crossing penalties; junctions at every node of degree >= 3.
- Labels kept only for: off-sheet nets (global labels), power/ground and isolated rails (power symbols; rails with a driver/PWR_FLAG such as GND_AC use power symbols named for the rail), wide buses (SPI/I2C/DSI/LVDS/MDI/expander ports -> stub + local label), and the few nets the router could not complete (label fallback, 10 nets total).
- Verified: netlist partition identical to the label-only version (1082 nets), ERC 0 errors/0 warnings, BOM identical. Local nets lost their label names (now auto Net-(...)).
