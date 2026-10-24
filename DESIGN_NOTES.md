# genctl schematic – design notes, assumptions, open questions (draft A, 2026-10-24)

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
1. **4x TCA9555PWR I2C expanders** (new; not in any BOM). The STM32H743VIT6 does not have enough GPIO.
   - @0x20: 12 buttons.
   - @0x21: 10 front-panel LEDs.
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

**+3V3 (TPS629210)**
- Fed from +12V through an MBR0540. FB 100k/22.1k → 3.31 V.
- MODE/S-CONF tied to GND (*assumed*: external-FB, auto PFM).
- **Open:** 1 A is marginal for STM32 + DSI83 + panel VDD + touch + hub + expanders + CAN/RS-485 logic. Consider a 2–3 A buck.

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

**Ethernet — open question**
- The HR911130C pin map is UNVERIFIED (the datasheet is graphical only).
- It is a 10/100 jack, so CM5 pairs 2 and 3 are unused and the **link will run at 100M**. Choose a gigabit magjack if 1G is wanted.
- RClamp0524P ESD.

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
**Isolated supply and links**
- ADuM5020-5 (VISO = 5 V) → ADP150 3.3 V.
- **The ADuM5020 is 3 kVrms basic isolation, not the 5 kV reinforced in the spec.** This needs a part change or a decision.
- ADuM141E ×2 (pinout from memory, UNVERIFIED):
  - #1 carries SCK, MOSI and CS1 across, and brings MISO back.
  - #2 carries CS2 and RST across, and brings IRQ0 back. Only the GEN ADE drives IRQ0.

**ADE9000 ×2 (GEN and BUS)**
- Shared SPI bus. Clock: 24.576 MHz crystal on the GEN ADE; its CLKOUT feeds the BUS ADE's CLKIN.
- PM0 = PM1 = 0 (normal mode). NC1/NC2 tied to AGND.
- AVDDOUT, DVDDOUT and REF each get 4.7 µF + 100 nF.

**Voltage inputs**
- Per phase: 4 × 1M (1206 HV) to a 1k low-side resistor → 4001:1. 1k/33 nF anti-alias on both VxP and VxN. V20E385P MOV L–N.
- Fuses are external, on fused DIN terminals per the spec. No on-board fuse.

**Current inputs**
- AC1005 CTs on the PCB. Each external 5 A CT secondary (J9) loops through the core: symbol pins P1/P2 = the wire bridge.
- Burden 2 × 24.9R, centre-tapped to AGND. 1k/33 nF anti-alias.
- The BUS ADE current inputs are grounded (voltage-only measurement).

**Open question**
- GEN_N and BUS_N are both tied to GND_AC with 0R links. That bonds generator neutral to bus neutral on the board.
- If the neutrals can differ (for example, a separately derived system), fit only one link and use differential dividers.

## Front panel (frontpanel.kicad_sch)
- 12 KSC241J buttons go to the TCA9555 at 0x20, using its internal pull-ups.
- 10 LEDs are on the TCA9555 at 0x21, active low with 1k resistors: 6 green, 4 red.
- Buzzer: MLT-8530 driven by an MMBT3904 from PB3, with a 1N4148W flyback diode. It runs from +3V3.

## Global open questions / to verify before layout
1. **UNVERIFIED pinouts.** Check these against their datasheets:
   - ADuM141E
   - HR911130C
   - M.2 Key B
   - ACT45B choke
   - TMUX1208 pin 3
   - TPS7B6950 DBV pin 4
   - TPS1HTC30 exposed pad
   - USB3-A part
2. **Spec decisions to make:**
   - 3V3 rail current budget (TPS629210, 1 A).
   - Isolation rating on AC metering (ADuM5020 is 3 kVrms).
   - Gigabit vs 100M Ethernet.
   - Modem supply voltage on the M.2 3.3V pins.
3. **Loop compensation** for LM5176 and TPS61500, LM5176 MODE, and TPS56637 MODE: values are placeholders.
4. **Footprints** are set only for passives and well-known packages. Custom ICs need footprints assigned.
5. **LCSC fields** are blank on about half the grouped BOM lines (TBD).
6. **Expander defaults** at power-up are Hi-Z. The AI current sources therefore default ON and the shunts OFF. Confirm this is acceptable.
