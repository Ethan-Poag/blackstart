# STM32H743VIT6 (U7, LQFP-100) pin / peripheral map

Generated 2026-10-25 from the KiCad schematic. No schematic or PCB file was edited.

## Sources and labels
- **[S] Schematic (read directly).** `kicad-cli sch export netlist --format kicadsexpr genctl.kicad_sch`, parsed by `firmware/tools/extract_pinmap.py`. The raw dump is `pins_raw_netlist.json`. All 100 U7 pins resolve to nets. Series resistors are followed one hop to show the far end.
- **[D] Datasheet (verified).** ST **DS12110 Rev 8** (April 2021), STM32H742xI/G / STM32H743xI/G, 358 pp.
  - Retrieved via the JLCPCB file mirror (`jlcpcb.com/api/file/downloadByFileSystemAccessId/8588901644754948096`). st.com could not be reached from the box.
  - AF numbers come from Table 10 (Port A, p.89), Table 11 (Port B, p.90), Table 12 (Port C, p.92), Table 13 (Port D, p.93) and Table 14 (Port E, p.95). They were parsed by column position into `../tools/ds12110_rev8_af_parsed.json`.
  - I/O structure and ADC channels come from Table 9 (Pin/ball definition, pp.64–88), with notes 5 and 6 on p.88.
- **[I] Inferred.** The intended function and direction are inferred from net names, connected parts and DESIGN_NOTES.md.
- **Not retrieved:** RM0433 (reference manual) and AN2606 (bootloader). Every statement that depends on them is marked **UNVERIFIED**.

## Peripheral summary
| Peripheral | Pins (AF) | Far end [S] | AF [D] |
|---|---|---|---|
| SPI4 slave ← CM5 SPI0 | PE2 SCK, PE4 NSS, PE5 MISO, PE6 MOSI (AF5). PE3 = MCU_IRQ GPIO with 10k pull-down | CM5 GPIO11/8/9/10/25, each through 1k | ✔ |
| SPI1 master → 2× ADE9000 | PA5 SCK, PA6 MISO, PA7 MOSI (AF5). PA4 CS1 / PC4 CS2 are GPIO. PC5 RST, PB0 IRQ (10k pull-up) | ISOW7841 U69 (SCK/MOSI/CS1/MISO), ISO7741 U70 (CS2/RST/IRQ), 1k each | ✔ |
| USART1 ↔ CM5 (bootloader port) | PA9 TX, PA10 RX (AF7) | CM5 GPIO15 RXD0 / GPIO14 TXD0, 1k | ✔ |
| USART3 RS-485 | PD8 TX, PD9 RX, PD12 DE (all AF7, so hardware DE is possible) | CA-IS2092W U17. DE has a 10k pull-down. **/RE is tied to GND** (always receiving) | ✔ |
| FDCAN1 | PD0 RX, PD1 TX (AF9) | CA-IS3062W U13 | ✔ |
| FDCAN2 | PB12 RX, PB13 TX (AF9) | CA-IS3062W U14 | TX ✔; RX partial (PDF cell is split across a page) |
| I2C1 | PB8 SCL, PB9 SDA (AF4), 2.2k pull-ups. PE7 I2C_INT_N | 6× TCA9555 (0x20–0x25), 2× ADS1115, FM24CL64B FRAM, header J3 | ✔ |
| Timers | PA15 MPU_SPEED = TIM2_CH1 (AF1). PB3 BUZZER = TIM2_CH2 (AF1). PC7 MPU_GATE can be TIM3_CH2 (AF2) or GPIO | TLV1812 U35 (push-pull, Batch 27; was LM393), buzzer NPN Q69 | ✔. TIM2 CH1 capture and CH2 PWM share one timer, so TIM2 needs a common timebase [I] |
| ADC | PA0 VBAT, PA1 VESTOP, PA2 D+, PA3 FUEL_ISNS, PB1 CRANK_ISNS, PC0 MUXA, PC1 MUXB | dividers (100k/10k), INA281, TMUX1208 | channels per Table 9 ✔ |
| SWD | PA13 SWDIO, PA14 SWCLK (AF0), NRST | J2 10-pin SWD, JP1 (CM5 SWD, optional) | ✔ |
| Clocks | PH0/PH1 HSE 25 MHz (Y1, 18p). PC14/PC15 LSE 32.768k (Y2, 18p) | — | HSE 4–48 MHz range per DS p.1 ✔ |
| Boot / reset | BOOT0: 10k pull-down, SW2, CM5 GPIO27 via 1k. NRST: SW1, J2, CM5 via Q7 open-collector | — | — |
| Outputs (GPIO) | PD2 FUEL, PD3 CRANK, PD4 GLOW, PD7 TRIP (each ANDed with WDO_N by LVC1G08). PC9–12 GCB/MCB, PE0/PE1/PB4–7/PD11/PD13 AUX1–8 (through LVC541 U41/U42 with /OE = WD_OE_N) | | |
| Inputs (GPIO) | DI1–12: PE9–15, PB10, PB11, PB14, PB15, PD10. PD14 ESTOP_DIG, PC6 ESTOP2_DIG, PD15 DPLUS_DIG, PB2 OUT_FAULT_N, PC3_C PSU_MAIN_OK, PC2_C CM5 heartbeat | 74HC14 on +3V3_SAFE | |
| Misc | PA8 DIAG_EN, PD5/PD6/PA11 MUX_A0–A2, PA12 WDI (TPS3431), PC8 DPLUS_EXC_EN, PC13 EXP_12V_EN, PE8 LED | | |

**Front panel [S]:** there is **no key/LED matrix on the MCU**. The 12 buttons (SW9–SW20) go to TCA9555 U73 @0x20 (for example BTN1 → P00). The RGB LED cathodes sit on @0x21, @0x24 and @0x25. Everything is reached over I2C1, with the shared I2C_INT_N on PE7.

## Full pin table
Power pins are omitted here; see the CSV. VDD/VREF+ = +3V3_SAFE, VDDA through FB1, VCAP1/2 each with 2.2 µF, VBAT from BAT54C (CR2032 / 3V3).
| Pin | Name | Net [S] | Connects to / far end [S] | Intended fn [I] | Dir [I] | AF [D] | I/O struct [D] | ADC [D] |
|---|---|---|---|---|---|---|---|---|
| 1 | PE2 | MCU_SPI_SCK | R51[1k]->CM5_SPI_SCK: U9.38(GPIO11)[CM5 (conn A)] | SPI4_SCK slave from CM5 GPIO11 | in | AF5 ✔ | FT_h |  |
| 2 | PE3 | MCU_IRQ | R49[10k]->GND: (rail) / R57[1k]->CM5_MCU_IRQ: U9.41(GPIO25)[CM5 (conn A)] | MCU_IRQ to CM5 GPIO25 (GPIO out, 10k pd) | out | GPIO | FT_h |  |
| 3 | PE4 | MCU_SPI_NSS | R54[1k]->CM5_SPI_CE0: U9.39(GPIO8)[CM5 (conn A)] | SPI4_NSS from CM5 CE0 | in | AF5 ✔ | FT_h |  |
| 4 | PE5 | MCU_SPI_MISO | R53[1k]->CM5_SPI_MISO: U9.40(GPIO9)[CM5 (conn A)] | SPI4_MISO to CM5 | out | AF5 ✔ | FT_h |  |
| 5 | PE6 | MCU_SPI_MOSI | R52[1k]->CM5_SPI_MOSI: U9.44(GPIO10)[CM5 (conn A)] | SPI4_MOSI from CM5 | in | AF5 ✔ | FT_h |  |
| 7 | PC13 | EXP_12V_EN | U15.1(IN)[TPS1H200AQDGNRQ1] | EXP_12V_EN -> TPS1H200 IN (GPIO) | out | GPIO | FT |  |
| 8 | PC14 | Net-(U7-PC14) | C63.1[18p] Y2.1(1)[32.768kHz] | LSE OSC32_IN 32.768k | analog | GPIO | FT (LSE) |  |
| 9 | PC15 | Net-(U7-PC15) | C64.1[18p] Y2.2(2)[32.768kHz] | LSE OSC32_OUT | analog | GPIO | FT (LSE) |  |
| 12 | PH0 | HSE_IN | C61.1[18p] Y1.1(1)[25MHz] | HSE OSC_IN 25 MHz | analog | GPIO | FT (HSE) |  |
| 13 | PH1 | HSE_OUT | C62.1[18p] Y1.3(3)[25MHz] | HSE OSC_OUT | analog | GPIO | FT (HSE) |  |
| 14 | NRST | NRST | C65.1[100n] J2.10(~{RESET})[SWD] Q7.3(C)[MMBT3904] SW1.1(1)[RESET] | Reset: SWD, SW1, CM5 via Q7 o/c | in | GPIO |  |  |
| 15 | PC0 | MUXA_OUT | C222.1[10n] U63.8(D)[TMUX1208PWR] | MUXA_OUT analog (TMUX1208 U63 D) - output current sense | analog | GPIO | FT_a | ADC123_INP10 |
| 16 | PC1 | MUXB_OUT | C224.1[10n] U64.8(D)[TMUX1208PWR] | MUXB_OUT analog (U64 D) | analog | GPIO | FT_ha | ADC123_INP11 |
| 17 | PC2_C | MCU_CM5_HB | R43[100k]->GND: (rail) / R61[1k]->Net-(U9-GPIO26): U9.24(GPIO26)[CM5 (conn A)] | CM5 heartbeat in (GPIO26, 100k pd) - needs analog switch closed | in | GPIO | ANA TT_a (note 6) | ADC3_INP0 |
| 18 | PC3_C | PSU_MAIN_OK | R32[100k]->+3V3_SAFE: (rail) | PSU_MAIN_OK in (TPS2116 ST, 100k pu) | in | GPIO | ANA TT_a (note 6) | ADC3_INP1 |
| 22 | PA0 | VBAT_SNS | R268[100k]->VBAT_SENSE: D66.1(A1)[SMAJ40CA] J21.4(Pin_4)[J3A E-stop/D+/VBAT/bias] / R269[10k]->GND: (rail) | VBAT_SNS analog 100k/10k | analog | GPIO | FT_a | ADC1_INP16 |
| 23 | PA1 | VESTOP_SNS | R411[100k]->VBAT_ESTOP: C199.1[100n] C203.1[100n] D126.1(A1)[SMBJ33CA] / R412[10k]->GND: (rail) | VESTOP_SNS analog 100k/10k | analog | GPIO | FT_ha | ADC1_INP17 |
| 24 | PA2 | DPLUS_SNS | R266[100k]->DPLUS: C187.1[100n] D63.1(A1)[SMBJ36CA] D64.1(K)[SS110] / R267[10k]->GND: (rail) | DPLUS_SNS analog 100k/10k | analog | GPIO | FT_a | ADC12_INP14 |
| 25 | PA3 | FUEL_ISNS | U44.1(OUT)[INA281A2] | FUEL_ISNS analog (INA281) | analog | GPIO | FT_ha | ADC12_INP15 |
| 28 | PA4 | ADE_CS1_N | R415[1k]->Net-(U69-INC): U69.5(INC)[ISOW7841DWER] | ADE_CS1_N (GPIO CS; HW alt SPI1_NSS) | out | AF5 ✔ | TT_a |  |
| 29 | PA5 | ADE_SCK | R413[1k]->ADE_SCK_I: U69.3(INA)[ISOW7841DWER] | SPI1_SCK -> ISOW7841 | out | AF5 ✔ | TT_ha |  |
| 30 | PA6 | ADE_MISO | R416[1k]->ADE_MISO_I: U69.6(OUTD)[ISOW7841DWER] | SPI1_MISO <- ISOW7841 | in | AF5 ✔ | FT_a |  |
| 31 | PA7 | ADE_MOSI | R414[1k]->ADE_MOSI_I: U69.4(INB)[ISOW7841DWER] | SPI1_MOSI -> ISOW7841 | out | AF5 ✔ | TT_a |  |
| 32 | PC4 | ADE_CS2_N | R417[1k]->Net-(U70-INA): U70.3(INA)[ISO7741DWR] | ADE_CS2_N GPIO -> ISO7741 | out | GPIO | TT_a |  |
| 33 | PC5 | ADE_RST_N | R418[1k]->Net-(U70-INB): U70.4(INB)[ISO7741DWR] | ADE_RST_N GPIO -> ISO7741 | out | GPIO | TT_a |  |
| 34 | PB0 | ADE_IRQ_N | R419[1k]->ADE_IRQ_N_I: U70.6(OUTD)[ISO7741DWR] / R48[10k]->+3V3_SAFE: (rail) | ADE_IRQ_N GPIO/EXTI0 in (10k pu) | in | GPIO | FT_a |  |
| 35 | PB1 | CRANK_ISNS | U46.1(OUT)[INA281A2] | CRANK_ISNS analog (INA281) | analog | GPIO | TT_u | ADC12_INP5 |
| 36 | PB2 | OUT_FAULT_N | R44.1[10k] U15.3(FAULT)[TPS1H200AQDGNRQ1] U16.3(FAULT)[TPS1H200AQDGNRQ1] U18.4(FAULT)[TPS2553DBVR] U19.4(FAULT | OUT_FAULT_N wired-OR in (10k pu) | in | GPIO | FT_ha |  |
| 37 | PE7 | I2C_INT_N | R45.1[10k] U31.1(~{INT})[TCA9555PWR @0x22] U62.1(~{INT})[TCA9555PWR @0x23] U73.1(~{INT})[TCA9555PWR @0x20] U74 | I2C_INT_N in, expanders wired-OR, EXTI7 (Rev 8j) | in | GPIO | TT_ha |  |
| 38 | PE8 | MCU_LED | R50[1k]->LED_HB_A: D6.2(A)[green] | MCU_LED heartbeat out | out | GPIO | TT_ha |  |
| 39 | PE9 | DI1_N | U32.2[74HC14] | DI1_N in (74HC14) | in | GPIO | TT_ha |  |
| 40 | PE10 | DI2_N | U32.4[74HC14] | DI2_N in | in | GPIO | FT_ha |  |
| 41 | PE11 | Net-(U7-PE11) | R34[1k]->DI3_N: U32.6[74HC14] | DI3_N in via 1k | in | GPIO | FT_ha |  |
| 42 | PE12 | Net-(U7-PE12) | R35[1k]->DI4_N: U32.8[74HC14] | DI4_N in via 1k | in | GPIO | FT_h |  |
| 43 | PE13 | DI5_N_M | R36[1k]->DI5_N: U32.10[74HC14] | DI5_N in via 1k | in | GPIO | FT_h |  |
| 44 | PE14 | DI6_N_M | R37[1k]->DI6_N: U32.12[74HC14] | DI6_N in via 1k | in | GPIO | FT_h |  |
| 45 | PE15 | DI7_N | U33.2[74HC14] | DI7_N in | in | GPIO | FT_h |  |
| 46 | PB10 | Net-(U7-PB10) | R38[1k]->DI8_N: U33.4[74HC14] | DI8_N in via 1k | in | GPIO | FT_f |  |
| 47 | PB11 | Net-(U7-PB11) | R39[1k]->DI9_N: U33.6[74HC14] | DI9_N in via 1k | in | GPIO | FT_f |  |
| 51 | PB12 | CAN2_RX | R91[1k]->CAN2_RX_T: U14.5(RXD)[CA-IS3062W] | FDCAN2_RX <- CA-IS3062W U14 | in | AF9 ✔ (partial, see note) | FT_u |  |
| 52 | PB13 | CAN2_TX | R90[1k]->Net-(U14-TXD): U14.3(TXD)[CA-IS3062W] | FDCAN2_TX -> U14 | out | AF9 ✔ | FT_u |  |
| 53 | PB14 | DI10_N_M | R40[1k]->DI10_N: U33.8[74HC14] | DI10_N in via 1k | in | GPIO | FT_u |  |
| 54 | PB15 | DI11_N_M | R41[1k]->DI11_N: U33.10[74HC14] | DI11_N in via 1k | in | GPIO | FT_u |  |
| 55 | PD8 | RS485_TX | R98[1k]->Net-(U17-DI): U17.6(DI)[CA-IS2092W] | USART3_TX -> CA-IS2092W DI | out | AF7 ✔ | FT_h |  |
| 56 | PD9 | RS485_RX | R99[1k]->Net-(U17-RO): U17.3(RO)[CA-IS2092W] | USART3_RX <- RO | in | AF7 ✔ | FT_h |  |
| 57 | PD10 | DI12_N | U33.12[74HC14] | DI12_N in | in | GPIO | FT_h |  |
| 58 | PD11 | AUX7_MCU | U42.4(A3)[SN74LVC541APWR] | AUX7 enable -> LVC541 U42 | out | GPIO | FT_h |  |
| 59 | PD12 | RS485_DE | R100[1k]->Net-(U17-DE): R101.1[10k] U17.5(DE)[CA-IS2092W] | USART3_DE (HW DE) -> U17 DE (10k pd); /RE tied GND | out | AF7 ✔ | FT_fh |  |
| 60 | PD13 | AUX8_MCU | U42.5(A4)[SN74LVC541APWR] | AUX8 enable -> U42 | out | GPIO | FT_fh |  |
| 61 | PD14 | ESTOP_DIG | U34.6[74HC14] | ESTOP_DIG in (VBAT_ESTOP via HC14) | in | GPIO | FT_h |  |
| 62 | PD15 | DPLUS_DIG | U34.4[74HC14] | DPLUS_DIG in | in | GPIO | FT_h |  |
| 63 | PC6 | ESTOP2_DIG | U34.2[74HC14] | ESTOP2_DIG in (NC2 sense) | in | GPIO | FT_h |  |
| 64 | PC7 | MPU_GATE | R260[2.2k, DNP Batch 27]->+3V3_SAFE: (rail) | MPU_GATE in (TLV1812 B, push-pull) | in | AF2 ✔ | FT_h |  |
| 65 | PC8 | DPLUS_EXC_EN | R263[10k]->DPX_NB: Q43.1(B)[MMBT3904] R264.1[100k] | DPLUS_EXC_EN out (NPN) | out | GPIO | FT_h |  |
| 66 | PC9 | GCB_CL_MCU | U41.2(A1)[SN74LVC541APWR] | GCB close enable -> U41 | out | GPIO | FT_fh |  |
| 67 | PA8 | DIAG_EN | U47.3(DIAG_EN)[TPS1HTC30QPWPRQ1] U48.3(DIAG_EN)[TPS1HTC30QPWPRQ1] U49.3(DIAG_EN)[TPS1HTC30QPWPRQ1] U50.3(DIAG_ | DIAG_EN out to 13x TPS1HTC30 | out | GPIO | FT_h? |  |
| 68 | PA9 | MCU_UART_TX | R56[1k]->CM5_UART_RX: U9.51(GPIO15)[CM5 (conn A)] | USART1_TX -> CM5 GPIO15 RXD0 (bootloader port) | out | AF7 ✔ | FT_u |  |
| 69 | PA10 | MCU_UART_RX | R55[1k]->CM5_UART_TX: U9.55(GPIO14)[CM5 (conn A)] | USART1_RX <- CM5 GPIO14 TXD0 | in | AF7 ✔ | FT_u |  |
| 70 | PA11 | MUX_A2 | U63.15(A2)[TMUX1208PWR] U64.15(A2)[TMUX1208PWR] | MUX_A2 out | out | GPIO | FT_u |  |
| 71 | PA12 | WDI | U37.6(WDI)[TPS3431SQDRBRQ1] | WDI kick -> TPS3431 | out | GPIO | FT_u |  |
| 72 | PA13 | SWDIO | J2.2(SWDIO/TMS)[SWD] JP1.2(Pin_2)[JP1 CM5->MCU SWD (opt)] | SWDIO | bidir | AF0 ✔ | FT? (not parsed) |  |
| 76 | PA14 | SWCLK | J2.4(SWCLK/TCK)[SWD] JP1.4(Pin_4)[JP1 CM5->MCU SWD (opt)] | SWCLK | in | AF0 ✔ | FT? (not parsed) |  |
| 77 | PA15 | MPU_SPEED | R258[1M]->MPU_PH: R257.2[10k] U35.3(+)[TLV1812] / R259[2.2k, DNP Batch 27]->+3V3_SAFE: (rail) | MPU_SPEED in (TIM2_CH1 capture) | in | AF1 ✔ | FT? (not parsed) |  |
| 78 | PC10 | GCB_OP_MCU | U41.3(A2)[SN74LVC541APWR] | GCB open enable -> U41 | out | GPIO | FT_ha |  |
| 79 | PC11 | MCB_CL_MCU | U41.4(A3)[SN74LVC541APWR] | MCB close enable | out | GPIO | FT_h |  |
| 80 | PC12 | MCB_OP_MCU | U41.5(A4)[SN74LVC541APWR] | MCB open enable | out | GPIO | FT_h |  |
| 81 | PD0 | CAN1_RX | R86[1k]->CAN1_RX_T: U13.5(RXD)[CA-IS3062W] | FDCAN1_RX <- U13 | in | AF9 ✔ | FT_h |  |
| 82 | PD1 | CAN1_TX | R85[1k]->Net-(U13-TXD): U13.3(TXD)[CA-IS3062W] | FDCAN1_TX -> U13 | out | AF9 ✔ | FT_h |  |
| 83 | PD2 | FUEL_EN_MCU | U38.1[74LVC1G08W5-7] | FUEL_EN (AND WDO_N) | out | GPIO | FT_h |  |
| 84 | PD3 | CRANK_EN_MCU | U39.1[74LVC1G08W5-7] | CRANK_EN (AND WDO_N) | out | GPIO | FT_h |  |
| 85 | PD4 | GLOW_EN_MCU | U40.1[74LVC1G08W5-7] | GLOW_EN (AND WDO_N) | out | GPIO | FT_h |  |
| 86 | PD5 | MUX_A0 | U63.1(A0)[TMUX1208PWR] U64.1(A0)[TMUX1208PWR] | MUX_A0 out | out | GPIO | FT_h |  |
| 87 | PD6 | MUX_A1 | U63.16(A1)[TMUX1208PWR] U64.16(A1)[TMUX1208PWR] | MUX_A1 out | out | GPIO | FT_h |  |
| 88 | PD7 | MCU_TRIP | R405[100k]->GND: (rail) | MCU_TRIP out (100k pd, AND WDO_N) | out | GPIO | FT_h |  |
| 89 | PB3 | BUZZER_PWM | R529[1k]->Net-(Q69-B): Q69.1(B)[MMBT3904] R530.1[100k] | BUZZER_PWM (TIM2_CH2) -> NPN | out | AF1 ✔ | FT? (not parsed) |  |
| 90 | PB4 | AUX3_MCU | U41.8(A7)[SN74LVC541APWR] | AUX3 enable -> U41 | out | GPIO | FT? (not parsed) |  |
| 91 | PB5 | AUX4_MCU | U41.9(A8)[SN74LVC541APWR] | AUX4 enable | out | GPIO | FT |  |
| 92 | PB6 | AUX5_MCU | U42.2(A1)[SN74LVC541APWR] | AUX5 enable -> U42 | out | GPIO | FT_f |  |
| 93 | PB7 | AUX6_MCU | U42.3(A2)[SN74LVC541APWR] | AUX6 enable | out | GPIO | FT_fa |  |
| 94 | BOOT0 | BOOT0 | R42[10k]->GND: (rail) / R62[1k]->Net-(U9-GPIO27): U9.48(GPIO27)[CM5 (conn A)] | BOOT0: 10k pd, SW2, CM5 GPIO27 via 1k | in | GPIO |  |  |
| 95 | PB8 | I2C1_SCL | J3.5(Pin_5)[Header B (MCU spare)] R46.1[2.2k] U29.10(SCL)[ADS1115 @0x48] U30.10(SCL)[ADS1115 @0x49] U31.22(SCL | I2C1_SCL (2.2k pu) | od | AF4 ✔ | FT_fh |  |
| 96 | PB9 | I2C1_SDA | J3.6(Pin_6)[Header B (MCU spare)] R47.1[2.2k] U29.9(SDA)[ADS1115 @0x48] U30.9(SDA)[ADS1115 @0x49] U31.23(SDA)[ | I2C1_SDA | od | AF4 ✔ | FT_fh |  |
| 97 | PE0 | AUX1_MCU | U41.6(A5)[SN74LVC541APWR] | AUX1 enable -> U41 | out | GPIO | FT_h |  |
| 98 | PE1 | AUX2_MCU | U41.7(A6)[SN74LVC541APWR] | AUX2 enable | out | GPIO | FT_h |  |
PB12 note: in DS12110 Table 11 (p.90) the AF9 cell reads "FDCAN2_" and its second line is lost at the page break in the text extraction. The RX suffix follows from PB13 = FDCAN2_TX at AF9 [I]. Check the PDF visually.

## Issues for Enginerd (not fixed)
1. **[S vs doc] DESIGN_NOTES "Pin map" section is out of date.** The schematic and the Rev (e) table say otherwise:
   - It lists "USART2 to the CM5: PD5/PD6". The schematic has USART1 on PA9/PA10, and PD5/PD6 are MUX_A0/A1.
   - It lists "PA9–11 mux address". Actually PD5, PD6 and PA11.
   - It lists "PC2_C/PC3_C go to header B". Actually CM5 heartbeat and PSU_MAIN_OK.
   - The mcu.kicad_sch text note still says "USART2 to CM5".
2. **[D] PC2_C / PC3_C are `ANA`, TT_a pads on LQFP-100** (Table 9 p.64ff, note 6 p.88). Digital use needs the SYSCFG analog switch closed. Whether GPIO input is reliable on these pads must be confirmed in RM0433 (**UNVERIFIED**). They are used for the safety-relevant PSU_MAIN_OK and the CM5 heartbeat. Option: move them to true GPIOs, or tie the heartbeat to an EXTI-capable pin.
3. **[S] Only the GEN ADE9000 (U71) IRQ0 reaches the MCU** (AC_IRQ_N → U70 → PB0). The BUS ADE (U72) has no IRQ, so firmware must poll it. Confirm this is intended.
4. **[D] 3.6 V-only (TT) pins:** PA4, PA5, PA7, PC4, PC5, PB1, PE7, PE8, PE9, PC2_C and PC3_C. Every source on the schematic is 3.3 V (74HC14, isolators, expanders on +3V3_SAFE), so there is no violation today. Keep any future 5 V signal off these pins.
5. **[I/UNVERIFIED] Bootloader port scanning.** DESIGN_NOTES already flags PB14/PB15 and PE11–14. Per AN2606 (not retrieved), the H7 bootloader may also listen on FDCAN1 PD0/PD1 and on USART3 PB10/PB11 (DI8/DI9). Live CAN traffic during BOOT0=1 could capture the bootloader. Verify against AN2606.
6. **[I] JTAG reset-state pulls (RM0433, UNVERIFIED).** PB4 (AUX3 enable) is NJTRST, which has an internal pull-up at reset, so AUX3's enable input is high until firmware reconfigures it. This is safe only if WD_OE_N keeps the LVC541 disabled through boot. Bench-check it (see the bring-up plan). PA15/JTDI has a pull-up and drives into an open-collector comparator output, which is benign. **Update 2026-10-28:** PB4 = NJTRST pull-up 30/40/50 kΩ [S DS12110 p138]. WD_OE_N does NOT hold through an MCU-only reset. Fix spec: R536 4.7k pull-down plus 100k on the other enables (fixes_firmware.md §2).
7. **[S] RS-485 /RE is tied to GND**, so the MCU receives its own transmissions. Firmware must discard the echo, or use it for collision checking.
8. **[S] Cosmetic:** PE11, PE12, PB10 and PB11 carry auto-named nets (`Net-(U7-PE11)` and so on) instead of `DIx_N_M`, unlike PE13, PE14, PB14 and PB15.
9. **[S] VREF+ is tied directly to +3V3_SAFE.** ADC accuracy then depends on the rail; consider a reference (design choice).
10. **[UNVERIFIED] PC13 drive limits.** PC13 is in the backup domain with limited sink/source and speed (RM0433). It drives the TPS1H200 IN, a CMOS input, so this is probably fine.


## Added 2026-10-28 (fixes_firmware.md)
- U76 (TCA9555 @0x25) **P15 (pin 18) = WD_OK input via R559 4.7k** (watchdog latch U84 Q; 0 = latched, power cycle required). **P16 (pin 19) = BL_ALLOW** (Rev 8d/8f): output, default HIGH (enabled). **U88** (Diodes **74LVC1G08W5-7**, C307; all board 74LVC1G08s are this MPN) ANDs BL_PWM (CM5 GPIO12) with P16 to **BL_EN**, which drives U24 EN. **R121 100 kΩ is on BL_EN. R629** 10 kΩ pull-up P16 to +3V3_SAFE. **R630** is a **CONFIRMED** 100 kΩ BL_PWM to GND (Enginerd 1:37 AM). It closes part of the GPIO12 reset-pull bench item; the bench item stays. MCU drives P16 LOW on CM5_LOST (1 s, ARCHITECTURE §5) or over-temp. **P17 (pin 20) = DI_BIAS_FLT_N** (Rev 8i/8j): both TPS26621 FLT lines wired-OR, active-low open-drain, 10 kΩ pull-up to +3V3_SAFE (part and polarity confirmed). Use PE7 EXTI7 to catch the pulse (ARCHITECTURE §13.17). (P16 is not FAN2_TACH; §11 withdrawn.)
- PB4 AUX3_MCU: external 4.7k pull-down (R536). Other enables: 100k (R534–R548, R551); AUX9/10 10k (R549/R550).
- PA9 → R56 and PE3 → R57 change from 1k to 10k. PA9/PE3/PE5 are Hi-Z until the CM5 heartbeat (PC2_C).
- PB2 OUT_FAULT_N: the INA238 (U86 @0x40) ALERT is added to the wired-OR.- PC13 EXP_12V_EN: R551 100k pull-down; **not watchdog-gated** (Ethan ruling 2026-10-28).
- INA238/INA237 @0x40: SOVL 9.5 A = 0x3B60 (Safety R3-1); load-shed spec in load_shedding_spec.md §13.

## ADC full scale (Rev 3, 2026-10-28 HST)
VREF+ = +3V3_SAFE [M]; 16-bit. Source: fixes_firmware.md §18.2.

| Path | Pin | Transfer | FS (at 3.300 V) | Counts per unit | Resolution (1 LSB) | Clamp / note |
|---|---|---|---|---|---|---|
| FUEL_ISNS (U44 INA281A1, 20 mΩ) | PA3 | 0.40 V/A | 8.25 A (linear only to 7.87 A, swing) | **7944 counts/A** | 0.126 mA | INA281 output ≤ VS = ADC rail, no clamp needed [I] |
| CRANK_ISNS (U46) | PB1 | same | same | **7944 counts/A** | 0.126 mA | same |
| MUXA_OUT / MUXB_OUT (TPS1HTC30 SNS → 1.1 kΩ → TMUX1208 U63/U64 D) | PC0 / PC1 | I/KSNS × 1.1 kΩ. KSNS from table **≈1200** (0.833 mA @1 A, 1.66 mA @2 A, 3.3 mA @4 A; nominal 1300 A/A) → **0.916 V/A** | **3.60 A** | **18 197 counts/A** | 55 µA | KSNS accuracy ±3–4 % (2–4 A), ±6 % @6 A, SLVSGL4A p.8–9 [M]. D128–D135 BAT54C clamps (§5). **Fault-high SNS saturates (≥ FS)** |
| VBAT_SNS (R268 100k / R269 10k, ×11) | PA0 | V/11 | **36.3 V** | 1805.4 counts/V | 0.554 mV | D67 BAT54S, C190 100 nF. **≥ 36.3 V reads saturated**: 36 V jump-start (≤ 60 s) is at FS; hardware OV trip 36.35/38.18/40.06 V is at or above FS, so use INA VBUS (BOVL 40 V) for OV. Do not treat saturation as a firmware OV shutdown |
| VESTOP_SNS (R411/R412, ×11) | PA1 | V/11 | 36.3 V | 1805.4 counts/V | 0.554 mV | D125 BAT54S, C234 |
| DPLUS_SNS (R266/R267, ×11) | PA2 | V/11 | 36.3 V | 1805.4 counts/V | 0.554 mV | D65 BAT54S, C189 |

## Rev 4 (2026-10-28 HST)
- U76 pin 18 = P15 = WD_OK (via R559 4.7k). Pin 16 = P13 = USB0_EN (unchanged).
- **Rev 8d:** U76 pin 19 = P16 = **BL_ALLOW** (see ARCHITECTURE §13.11 / fixes_firmware §23.5a).
- PA12 (pin 71) = WDI: add R560 100k to GND (static when the MCU pin is Hi-Z/bootloader).
- BOOT0 (pin 94): R42 10k to GND, SW2 to +3V3_SAFE, R62 1k from CM5 GPIO27.
- Bootloader-shared pins (AN4938 Table 3 [I]; AN2606 Table 135 [U]): PC9 GCB_CL, PC10/11/12 GCB_OP/MCB_CL/MCB_OP, PA15 MPU_SPEED, PA8 DIAG_EN, PB5 AUX4, PB6 AUX5, PD12 RS485_DE, PD13 AUX8, PA9/PA10 UART, PA12 WDI.
- EN pull-downs R277–R291: 47k (was 100k).

### Rev 5 (m7-sch): TPS1HTC30 RILIM 24.9k
- ILIM is 3.18/4.02/4.87 A on U47–U61; U68 (47k) is 1.70/2.13/2.55 A.
- Readback saturates at 3.60 A (0.916 V/A). At current limit, SNS goes to VSNSFH 3.0–3.82 V, clamped by the BAT54C to ≈3.3 V+Vf.
- Linear range ≤ 2.7 V (≈2.95 A).
- Software FAULT 3.0 A reading for 100 ms; declared ≤ 2.8 A; SNS ≥ 2.9 V for 1 ms = limit/fault. See fixes_firmware §20.

### Rev 8d (2026-11-21 ~1:22 AM HST): BL_ALLOW
- U76 P16 (pin 19) = **BL_ALLOW**, MCU output, default HIGH. **U88** (Diodes **74LVC1G08W5-7**, C307) ANDs BL_PWM with P16 into **BL_EN** → U24 EN. R121 on BL_EN; R629 10 kΩ pull-up; **R630 CONFIRMED** 100 kΩ to GND. Details: ARCHITECTURE §13.11, fixes_firmware §23.5a.

### Rev 8e (2026-11-21): D66 and OV wording
- D66 on VBAT_SNS is **SMAJ40CA** (m7-sch MEASURED, was documented as SMAJ36CA). Hardware OV trip 36.35/38.18/40.06 V, release 33.19/35.04/36.65 V. See ARCHITECTURE §13.12.

### Rev 8f (2026-11-21): RELAY_KIT_V, Layout backlight refdes, P16 cleanup
- `RELAY_KIT_V` and the GLOW/CRANK/FUEL kit inhibit: ARCHITECTURE §13.13 / fixes_firmware §24 (Rev 8g updates mid-run and thresholds).
- Layout final: **U88** Diodes **74LVC1G08W5-7** + **C307**; net **BL_EN** = BL_PWM AND BL_ALLOW; R121 on BL_EN; **R629** 10 kΩ P16 pull-up. U76 P16 is **BL_ALLOW**, not FAN2_TACH.
- **U83** TMP1075 I2C1 0x4A, **C306**, ALERT NC — firmware polls. **F101 / F102** are the present PTCs on DI_BIAS_A / DI_BIAS_B (Batch 17: TI **TPS26621DRCR**, §13.17).

### Rev 8g (2026-11-21 ~1:37–1:38 AM HST)
- Mid-run kit OV does not stop the engine (FUEL / K2 stays on; latched `RELAY_KIT_OV`). 12 V kit inhibit 16/15 V; 24 V kit GLOW, CRANK and FUEL all **30.0 / 28.5 V**. INA237 VBUS primary; ADC fallback blocks all starts. Glow on-time capped at 60 s + 60 s cooldown (ASSUMED). MCU_TRIP / K4 firmware drive pulse **0.48 s**; `ESTOP_TRIP_STUCK` at **1.20 s** (Rev 8k, was 0.53 s); hardware one-shot **0.30–1.00 s**. See ARCHITECTURE §13.14 / §13.18.
- **R630 CONFIRMED** 100 kΩ BL_PWM to GND. Closes part of the GPIO12 reset-pull bench item; the bench item stays.
- **FUEL is K2** (Hella 4RA 003 437-191 on the 24 V kit, 16–30 V).

### Rev 8h (2026-11-21 ~1:51 AM HST): DI_BIAS rails, one-shot, LVC MPN
- **DI_BIAS_A** (J21.6, F101): **DI1–DI6**. **DI_BIAS_B** (J22.1, F102): **DI7–DI12**. MEASURED from m7-sch `inputs.kicad_sch` wetting resistors. E-stop is not on these rails. Rail-fault firmware: ARCHITECTURE §13.15–§13.19 / fixes_firmware §25.
- ESTOP one-shot: **Rev 8k (§13.18) supersedes 0.37–0.53 s / pending C0G.** C229 **220 nF C0G**, R404 **2.0 MΩ**, hardware range **0.30–1.00 s**; `ESTOP_TRIP_STUCK` at **1.20 s**. Firmware MCU_TRIP drive stays 0.48 s.
- All 74LVC1G08 gates (U38, U39, U40, U67, U88) are Diodes **74LVC1G08W5-7**, same pinout.

### Rev 8i (2026-11-21 ~2:01 AM HST)
- U76 **P17 = DI_BIAS_FLT_N**: both eFuse fault lines wired-OR, active-low open-drain with a pull-up. Part and polarity confirmed in Rev 8j (§13.17). On a P17 fault, inference names the rail; if it cannot, both rails are FAULTED.
- TPS48100 trip with 20 mΩ shunts is 3.86/4.97/6.14 A (the 90 A figure is withdrawn). Load dump is not supported (9–32 V continuous, 36 V ≤ 60 s).

### Rev 8j (2026-11-21 ~2:09 AM HST): TPS26621, U31 enables, PE7 EXTI7
- DI_BIAS eFuse is TI **TPS26621DRCR**. U76 **P17 (pin 20) = DI_BIAS_FLT_N**, 10 kΩ to +3V3_SAFE, polarity confirmed. Latch on the first FLT outside the enable blank; the 50 ms debounce is withdrawn.
- Bank enables (MEASURED, m7-sch `eaa89df`): U31 (TCA9555 @0x22) **P14 → DI_PU_A → Q37 → Q36** (bank A); **P15 → DI_PU_B → Q40 → Q39** (bank B). Start the self-test / blank timer at the U31 I2C write.
- U76 ~INT is on shared **I2C_INT_N** (U31, U62, U73, U74, U75, U76, R45 10 kΩ) into **PE7 (EXTI7)** — MEASURED, pending mark cleared. INT may release when the pin returns to its original level (SCPS200E p.16); the Input Port register is live only (p.24). Clear INT by reading the expander and port that raised it (P17 is port 1).
- Approved sequential self-test and 60 s IDLE re-cycle: ARCHITECTURE §13.17. **Rev 8k:** 25 ms window, C(dVdT) 10 nF; one-shot 0.30–1.00 s (§13.18).

### Rev 8k (2026-11-21 ~2:19 AM HST): 10 nF dVdT, 25 ms window, one-shot 0.30–1.00 s
- C(dVdT) **stays at 10 nF**. FLT self-test blank/capture window is **exactly 25 ms** after each bank enable (timer at the U31 write). Expected FLT low (INFERRED): **8.3 ms at 9 V**, **11.4 ms at 24 V**, **13.9 ms at 36 V**. Pulse width ASSUMED; bench-measure at 9/24/36 V. tPGOOD(degl) at 10 nF is 6.48 ms (SLVSDT4F p.23/p.8). I2C budget: on the order of 160–250 expander transactions in 25 ms; self-test remains viable.
- One-shot: C229 **220 nF C0G**, R404 **2.0 MΩ**, range **0.30–1.00 s** (nominal 0.48 s). Expected-pulse checks **0.30–1.00 s**. `ESTOP_TRIP_STUCK` is **1.20 s**. Firmware MCU_TRIP drive stays **0.48 s**. The pending Enginerd / Batch 18 C0G note is withdrawn.

### Rev 8l (2026-11-21 ~2:24 AM HST): DI_BIAS 3-in-10 s lockout
- If a bank sees **3 FLT events in a rolling 10 s**, deassert its enable (A: U31 P14; B: U31 P15) and latch `DI_BIAS_A_LOCKOUT` / `DI_BIAS_B_LOCKOUT`. Self-test pulses inside the 25 ms blank do not count. Ambiguous wired-OR attribution locks out both banks. Mid-run: alarm only, do not stop the engine. **Rev 8m:** P17 held low > 2 s outside the blank also locks out that bank (or both, if ambiguous). Ack is accepted only while stopped and re-runs the self-test before clearing (**RULED**). Lockout is FRAM-persistent until an ack passes (**RULED**). Details: ARCHITECTURE §13.19–§13.20.

### Rev 8m (2026-11-21 ~2:26 AM HST): stuck-low lockout, ack and FRAM RULED
- A continuous P17 low is still one 3-in-10 s event. P17 held low **> 2 s** outside the 25 ms blank also locks out that bank directly (ambiguous attribution → both). Mid-run: alarm only, FUEL stays on.
- **RULED (Enginerd 2:26):** ack is accepted only while stopped, and re-runs the bank self-test before clearing. Lockout is FRAM-persistent until an ack passes.
