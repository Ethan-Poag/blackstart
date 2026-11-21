# HCR-SENS-01: Ambient light sensor + board temperature sensors (supersedes HCR-ALS-01)

From: Ethan Poag (owner) / firmware. To: Layout Engineer (via Enginerd). 2026-10-25. Status: proposed, not yet in the schematic. **Rev 8b (2026-11-21):** U81/U82/U80 still not in m7-sch 1676f11 (MEASURED). **Rev 8f:** U83 is fitted (TMP1075DSGR C2870250, I2C1 0x4A, decoupler **C306**) as the ambient sensor for fanless dimming (fixes_firmware §23). **ALERT is not connected**; firmware must poll it.

Labels:
- [S] netlist / schematic
- [N] repo notes (DESIGN_NOTES, LAYOUT_PLAN, display_mech)
- [D] datasheet
- [L] LCSC live stock, read 13:53 HST today
- [I] inferred
- [U] unverified

## 1. Parts
| Ref | MPN | LCSC # | Stock [L] | Package / footprint |
|---|---|---|---|---|
| U80 | TI OPT3001DNPR (ambient light) | C90462 | 2,636 (read 13:48) | USON-6 2×2 mm (TI DNP land pattern) |
| U81, U82, U83 | TI TMP1075DSGR (temperature) | C2870250 | 36,374 | WSON-8 2×2 mm (TI DSG land pattern) |
| alt. temp | TI TMP102AIDRLR | C99269 | 33,412 | SOT-563. ±2 °C max over −13…185 °F (−25…85 °C) [D SBOS397I]; addresses 0x48–0x4B |

JLCPCB assembly stock and Basic/Extended class are not confirmed for any of these [U]. Refs continue the schematic numbering: the highest existing refs are U79, C292 and R533 [S].

## 2. Bus and address map
**CM5 display bus** (DISP_SDA = GPIO2, DISP_SCL = GPIO3, 3.3 V side of U77) [S]:

| Address | Device |
|---|---|
| 0x2C | SN65DSI83 (through U77 to the 1.8 V side) |
| 0x41 | touch ILI2511 [D Riverdi RVT121HVLNWCA0-B DS Rev 1.1: "I2C slave address 0x82", the 8-bit form → 7-bit 0x41, I] |
| **0x44** | **U80 OPT3001 (ADDR = GND)** |
| **0x48** | **U81 (A2/A1/A0 = GND)** |
| **0x49** | **U82 (A0 = V+, A1/A2 = GND)** [D SBOS854F Table 7-2] |

- No other devices are on this bus. CM5 I2C0 (SDA0/SCL0, pads 80/82) is unconnected [S].
- 0x44 stays clear of 0x41 and its plausible straps 0x40–0x42.
- **Pull-ups: add none.** The CM5 on-module 1.8k to 3.3 V is used, and board pull-ups are DNP [N].

**MCU I2C1** (PB8/PB9, R46/R47 2.2k to +3V3_SAFE, already fitted: **add no pull-ups**) [S]. Existing devices:

| Address | Device |
|---|---|
| 0x20–0x25 | TCA9555 ×6 |
| 0x48, 0x49 | ADS1115 |
| 0x50 | FRAM |
| **0x4A** | **U83 (A1 = V+, A0/A2 = GND), new** |

## 3. Connections
**U80 OPT3001:**

| Pin | Connect to |
|---|---|
| 1 VDD | CM5_3V3, with C293 100 nF |
| 2 ADDR | GND |
| 3 GND | GND |
| 4 SCL | DISP_SCL |
| 6 SDA | DISP_SDA |
| 5 INT | **NC** |

- Polling is used: all 28 CM5 GPIOs are used [S], and CAM_GPIO0/1 are not general-purpose GPIOs [U].
- SBOS681C describes INT only as an open-drain output that needs a pull-up when used. It does not explicitly say an unused INT may float; leaving an output NC is inferred safe [I]. The earlier 10k INT pull-up is dropped.
- Exposed-pad connection: per the datasheet [U].

**TMP1075 (WSON-8):** pin 1 SDA, 2 SCL, 3 ALERT, 4 GND, 5 A2, 6 A1, 7 A0, 8 V+ [D Table 5-1].

| Ref | V+ (100 nF to GND) | SDA / SCL | A2 / A1 / A0 | ALERT |
|---|---|---|---|---|
| U81 | CM5_3V3, C294 | DISP_SDA / DISP_SCL | GND / GND / GND | NC (polled; open-drain output [D]) |
| U82 | CM5_3V3, C295 | DISP_SDA / DISP_SCL | GND / GND / V+ | NC |
| U83 | +3V3_SAFE, **C306** (Layout final; was C296 in the HCR proposal) | I2C1_SDA / I2C1_SCL (PB9/PB8; use the existing net names) | GND / V+ / GND | **NC** (firmware polls; no ALERT interrupt) |

Exposed pad: per TI DSG land pattern [U]. U83 is placed on the MCU bus so the safety MCU sees cabinet temperature even if the CM5 is down.

## 4. Placement
Board coordinates are from mechanical/LAYOUT_PLAN.md. All parts are SELV/LV.

**600 V rule [N]:** the hot box is x −3.7…60, y 11…162. It is surrounded by a 13 mm copper-free barrier (bands y −1.25…11, x 60…73, y 162…175), and LV copper must be ≥13 mm from hot copper. **Every part below is outside the barrier by more than 25 mm.**

| Ref | Position (side) | Reason |
|---|---|---|
| U80 | F side, top key row, midway between keys (glass coords x ≈ 138.2, y ≈ −9.25) + black light pipe to a Ø2–3 mm panel window | Sees the room, not the screen. ≥15 mm from key LEDs. ~78 mm right of the barrier [I] |
| U81 | B side, CM5 parts zone (200…262, 41.5…62), ≈ 5 mm below the module edge near the heatsink pad, **outside STRAP_CORRIDOR** (x 247…279.8, y −14.8…3.8) | Tracks the CM5 / heat-strap temperature. ≥140 mm from the barrier |
| U82 | B side, display block (135…200, 100…135), ≤5 mm from U24 TPS61500 exposed pad / inductor, on the same GND pour | Tracks backlight-driver heat. ≥60 mm from the barrier |
| U83 | B side (rear), spill zone ≈ (110, 120), ≥15 mm from any power part, thermal relief, no pour under it | Cabinet air. ≥37 mm from the barrier |

## 5. Firmware use
See firmware/ARCHITECTURE.md §9 and §9.7.
- Auto-brightness on the CM5.
- Derating thresholds in °F are proposed only [U].
- A failed sensor is treated as hot (backlight capped at 60 %, fault flagged).
- There is no MCU safety action on temperature.

## 6. BOM delta
- Add: U80 OPT3001DNPR (C90462); U81–U83 TMP1075DSGR (C2870250); C293–C296 100 nF 0402 X7R (use the project's existing code).
- No resistors are added.
- Mechanical BOM: light pipe and panel window.
