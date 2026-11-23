# Modular "card" architecture: Phase 1 proposal + Phase 2 engine-card update

Branch `m7-modular`, from the locked baseline tag `baseline-2026-11-23-locked` (5bac9fe). Written Mon Nov 23, 2026, ~10:15 AM HST.
**Phase 2 (§9, Nov 23 ~10:40 AM HST):** the engine I/O moves to its own keyed card slot; card schematics now live in `cards/`. The baseline schematics, BOM and PCB are still untouched. Nothing has been ordered or pushed.

Ethan's asks (Nov 23, 10:00 and 10:01 AM HST):
- Make the parts of the controller that fail into swappable "cards" (LV inputs, HV inputs, LV outputs, and so on).
- Make it **configurable**: swap in different cards to suit the generator.

Tags used: **[M]** measured from repo files or live LCSC this session. **[R]** rule-based, from my net-name classifier (`modular/tools/classify_cards.py`). **[DS]** datasheet or listing. **[E]** estimate. **[I]** inferred.

Supporting files in `docs/modular/`:

| File | What it is |
|---|---|
| `card_layout.png` | Phone-readable diagram of the slots and what goes on each card |
| `img/connector_options.png` | Pictures of connector options A, B and C, with prices and ratings |
| `img/*.jpg` | LCSC product photos. `img/A_din41612_female_datasheet_drawing_9001-12xxx.png` is the WingTAT drawing |
| `cards.csv` | Card list: contents, channels, part counts |
| `slot_pinout_LV.csv` | Proposed 96-pin LV slot pinout |
| `cost_delta.csv` | Every cost line, with its source |
| `tools/cost_delta.py` | Builds the cost table |
| `card_assignment_baseline.json` | Every baseline main-board ref, assigned to a card or kept on the mainboard [R] |
| `tools/classify_cards.py` | Builds that assignment. It reads the netlist that the blocks study exported (kicad-cli 9.0.2) to `/tmp/blk/genctl.net` from 5bac9fe |
| `tools/card_layout.py` | Draws both PNGs |

---

## 0. Recommendation in one screen

- **Mainboard/backplane, fixed.** It keeps only what must never be removable:
  - STM32 safety core, watchdog and engine-stop latch, E-stop sense/latch and the E-stop feed (J23), FRAM;
  - power entry and supplies, CAN ×2, RS-485, CM5 + display + Ethernet/USB, front-panel keys.
- **1 dedicated, keyed ENGINE slot (Phase 2, §9).** Fuel, crank and glow drivers, MPU speed, D+, COM_A/B, DI1-4 and AI1-2 with their protection are on a card. Only an engine card fits (coding key + ID EEPROM type check), and the engine will not start without it. Its drivers are fed only from the mainboard's E-stop rail, so a missing card means no fuel.
- **8 universal LV slots.** Any LV card goes in any LV slot. Each card is identified by an ID EEPROM, and firmware configures itself from what it finds. Card types:
  - **DI-8:** 8 digital inputs.
  - **AI-4:** 4 analog, resistive or 4-20 mA inputs.
  - **HSO-5:** 5 high-side outputs at 2 A.
  - **BRK-4:** breaker open/close coils.
  - **PAR:** a future paralleling bias card for the governor and AVR.
- **1 dedicated HV slot.** This is the existing `genctl_meter` board, almost unchanged, plus an ID/calibration EEPROM. It keeps its own 600 V field plugs, and only SELV crosses to the mainboard on the existing Micro-Fit harness.
- **LV connector:** DIN 41612 type C, 96 pins.
  - Card side: WingTAT 9001-11961C00A (LCSC C5173361), right-angle male.
  - Mainboard side: 9001-12961C00A (C5173363), vertical female.
  - About $2.57 per pair at qty 1 [M-LCSC], 2 A per contact, AC 1000 V for 1 min [DS].
  - Chosen because it is rugged under vibration, cheap, solderable by hand, and needs no gold fingers.
- **Mechanical:** cards stand vertically in two rear "card bays" and load from the rear, like a PLC I/O rack. The field plug comes off, one screw comes out, and the card slides out. The bays stick out about **14 mm** past today's rear skin [E]. **Overall depth grows about 8 mm**: about 76 mm to the plug tips, against 68.25 mm today [E].
- **Safety:** swap only with power off.
  - Removing a card can only de-energize things. Hardware cuts slot power the moment PRESENT goes away.
  - The E-stop, watchdog and fuel/crank paths never pass through a card.
  - A card that is missing, wrong or unrecognized stays unpowered. Any function mapped to it is unavailable, and if that function is protection-class, the engine will not start.
- **Cost of the baseline-equivalent build** (5 LV cards + HV) against the one-board design: **about +$276 at qty 1 and about +$108 per unit at qty 10.**
  - That is +15.6 % and +8.6 % on the $1,767 / $1,259 controller totals in `review/bom_split/totals.json`.
  - More than half the qty-1 delta is fixed fees for 4 extra small PCB/PCBA orders.
  - **Part count:** about 1,583 against 1,367, so +216 or +16 % [R+E].

![card layout](modular/card_layout.png)

---

## 1. Card partition

### 1.1 What moves and what stays [R]
`classify_cards.py` assigns every one of the 1,147 baseline main-board parts by net name:
- `DIn` nets with n ≥ 5 go to DI-8; `AIn` with n ≥ 3 go to AI-4.
- `AUX1-5` and `AUX6-10` go to the two HSO-5 cards; `GCB_*` and `MCB_*` go to BRK-4.
- Everything else stays on the mainboard, in the blocks-study buckets.

Boundary parts (shared bias, decoupling) are heuristic, the same caveat as `review/springy/blocks/blocks_report.md`.

| Card | Slot | Channels | Moved from baseline [R] | Added [E] | Parts | Baseline parts cost moved, qty 1 / 10 [M-BOM] | What fails in the field |
|---|---|---|---|---|---|---|---|
| **Mainboard** | fixed | DI1-4, AI1-2, MPU/D+/COM, fuel, crank, glow, E-stop trip | 839 stay | +152 (8 slot power switches, sockets, ID mux, expanders) | **~991** | n/a | Low exposure. It keeps only the engine-core front ends |
| **DI-8** | any LV | 8 DI (today DI5-12) | 57 | +17 (DIN, EEPROM, MCP23S17, own DI bias switch, headers) | **~74** | $13.27 / $11.33 | TVS and front-end damage from surges and miswiring |
| **AI-4** | any LV | 4 AI: resistive sender, 4-20 mA, 0-10 V (today AI3-6) | 80 | +9 (DIN, EEPROM, TCA9555, header) | **~89** | $4.93 / $4.29 | Sender shorts, 4-20 mA loop faults, surges |
| **HSO-5** ×2 | any LV | 5 high-side outputs (AUX1-5, AUX6-10) | 59 / 62 | +12 (DIN, EEPROM, MCP23S17, '541 OE buffer, TMUX1208) | **~71 / 74** | $23.66 / $24.84 at qty 1 | Shorted loads, inductive kick, miswiring. These are the most likely cards to fail |
| **BRK-4** | any LV | GCB/MCB open/close coils | 48 | +12 | **~60** | $18.99 at qty 1 | Coil shorts |
| **PAR** (future) | any LV | 2-4 isolated governor/AVR bias outputs [E] | 0 | 40-60 [E] | 40-60 | n/a | Undesigned (see §7) |
| **HV meter** | dedicated HV | GEN V 3+N, BUS V 3+N, GEN I ×4 | 220 (the whole `genctl_meter`) | +4 (AT24CS32 + C + 2 pull-ups) | **~224** | $63.89 / $53.42 (meter BOM TOTAL) | 600 V transients, MOVs, CT wiring |

**Full build** (example 2 below): 991 + 74 + 89 + 71 + 74 + 60 + 224 = **~1,583 parts**, against 1,147 + 220 = 1,367 (+216, +16 %) [R+E]. The "added" counts don't subtract mainboard parts that become redundant, such as the shared '541 buffers, TMUX1208s and some TCA9555s. So they are conservative.

### 1.2 Why the engine core stays fixed
- **E-stop, watchdog, fuel and crank stay on the mainboard.** The battle-short scope is "E-stop + overspeed" (`docs/FW_REQ_BATTLESHORT.md`), and the narrow protection path is about 217 parts (blocks report §7). Keeping them fixed means no card swap, bad card or loose connector can touch the engine-stop path.
- **The 10 A fuel/crank copper stays where it is.** It runs on `VBAT_ESTOP` with its 10 A copper target (`docs/RAIL_PLAN.md`), and it shouldn't cross a connector.
- **DI1-4 and AI1-2 stay too,** so the minimum build can protect an engine with no LV cards:
  - DI1-4 covers low oil pressure, high coolant temp, low coolant level and an overspeed switch.
  - AI1-2 covers the oil pressure and coolant temperature senders.
  - Their front ends do take surges, so this is a trade. A failed DI1-4/AI1-2 channel means a mainboard repair. Any of those functions can be moved to a card channel in config if the user prefers (§3.3).
- **CAN and RS-485 stay too.** They are already isolated (CA-IS3062W), only 28 parts, and tied to STM32 FDCAN/USART pins that a universal slot does not carry.

### 1.3 Example builds (configurability)
| Build | Cards | LV slots used | Notes |
|---|---|---|---|
| **1. Small standby set** (single set on an ATS, no paralleling) | Mainboard + HV + 1× HSO-5 | 1 of 8 | DI1-4/AI1-2 cover engine protection. The HSO-5 drives alarm, fuel pump and block heater. The ATS does the transfer, so no BRK-4. |
| **2. Prime-power set with full metering** (the baseline's I/O) | Mainboard + HV + DI-8 + AI-4 + 2× HSO-5 + BRK-4 | 5 of 8 | Same I/O as today's single board: 12 DI, 6 AI, 10 AUX, 4 breaker coils. |
| **3. Paralleled set** (Ethernet paralleling, decided Nov 23) | Build 2 + PAR | 6 of 8 | BRK-4 is required for the GCB. PAR does the governor/AVR bias. Ethernet uses the CM5 port, so it needs no card. 2 spare slots remain, for example an extra DI-8 or AI-4. |

### 1.4 Minimum build (must always be present)
- **Mainboard,** which carries the safety core, watchdog latch, E-stop, fuel/crank/glow, speed, VBAT sense, DI1-4 and AI1-2.
- **HV meter card.** A missing meter is already a no-start/shutdown-class fault (`docs/FW_REQ_METERING_PRESENCE.md`), so nothing changes there.
- **The CM5 is not needed for the engine to run protected.** The existing `CM5_LOST` handling covers that. It is needed for the screen and for configuration.

---

## 2. Backplane and connector

### 2.1 Connector options (pictures: `docs/modular/img/connector_options.png`)
| | **A. DIN 41612 type C, 96 pins (recommended for LV slots)** | B. PCIe x1 card-edge socket | C. Molex Micro-Fit 3.0 2×8 cable (kept for the HV card) |
|---|---|---|---|
| Part | Card: WingTAT 9001-11961C00A (C5173361), RA male. Mainboard: 9001-12961C00A (C5173363), vertical female | Samtec PCIE-036-02-F-D-TH (C194068) | Molex 43045-1600 header (C277731) + 43025-1600 housing (already on the BOM as J31/J32) |
| Price, qty 1 / qty 10+ | $1.2659 / $1.061 + $1.3035 / $1.0953 [M-LCSC 10:09 AM HST] | $2.8379 / $2.5008 [M-LCSC], plus gold fingers on every card [E] | $1.35 / $1.15 per header (SPLIT_SCOPE §4) |
| Stock (LCSC) | 3,161 / 982 [M] | 27 [M] | 1,705 (SPLIT_SCOPE) |
| Rating | 2 A per contact, AC 1000 V for 1 min, 20 mΩ, -55 to +125 °C (-67 to 257 °F) [DS, WingTAT drawing] | 2.2 A per pin (2 adjacent pins powered), 7.65 mm insertion [DS Samtec F-219] | On the BOM today |
| Size | Female 95 mm long × 10.6 mm × 11.6 mm tall. Male RA 94 mm × 13.2 mm × 11.1 mm [DS] | About 25 mm long, 11 mm tall [DS/photo] | 2×8, 3.0 mm pitch |
| Good | Rugged in vibration (a railway/industrial standard). Polarized shroud. Through-hole, so easy for DIY. No gold fingers. Many pins for power and ground | Very compact cards | Positive latch, cable takes up tolerance, works at any position |
| Bad | 95 mm long, so the cards are about 100 mm long | Wiping contacts on a vibrating genset. Hard gold on every card. Low LCSC stock. 1.0 mm pitch is harder for DIY | A loose harness for every card, more handling, a crimp tool |

**Choice:** A for the 8 LV slots and C, unchanged, for the HV card. B is the fallback if the card bays have to shrink.

**Not checked this run:**
- DIN 41612 versions with staggered first-make/last-break contacts. These would make hot-swap cheaper.
- DigiKey/Mouser stock for any of the three.

### 2.2 LV slot pinout (`modular/slot_pinout_LV.csv`)
96 pins, rows a/b/c × 32 positions.

| Positions | Signals |
|---|---|
| 1-3 | **VBAT_FIELD** ×9, switched per slot |
| 4-6 | **FIELD_GND** ×9 |
| 7 | GND guard row |
| 8-9 | +5V_SLOT ×2, +3V3_SLOT ×2, both switched |
| 10 | +3V3_ID (always on, EEPROM only), PRESENT_N (tied to GND on every card) |
| 11-12 | SPI SCK/MOSI/MISO/CS_N (shared bus; CS decoded per slot) |
| 13 | I2C SDA/SCL. A **dedicated slot I2C bus**, one TCA9548A channel per slot |
| 14 | INT_N, RST_N |
| 15 | **OUT_EN**, CARD_FAULT_N |
| 16-17 | SLOT_ID0-2 + parity (backplane straps), ANA_OUT (to an STM32 ADC through a backplane TMUX1208) |
| 18-30 | Reserved. Every second b-row pin is GND |
| 31-32 | GND |

- **Why a separate I2C bus:**
  - The SOT-23-5 AT24CS32 has a fixed address that I believe is 0x50. That would collide with the FM24CL64B FRAM at 0x50 on I2C1 (`firmware/ARCHITECTURE.md` §9.3). Check the address in Phase 2.
  - An AI-4's ADS1115 (0x48) would collide with the mainboard ADS1115s.
  - So the card bus must go on its own STM32 I2C peripheral. Its pins are a Phase-2 check [I].
- **STM32 pins needed:** about 11 (SPI 3, CS decode 4, I2C 2, ADC 1, INT 1). The ~15 AUX/breaker EN and readback GPIOs that move onto cards are freed, so this should fit. That's an inference, to be checked against the U7 pin map in Phase 2.

### 2.3 Keying and identification
- **Wrong-slot keying isn't needed between LV slots,** because every LV slot is universal. The DIN shroud prevents a card going in backwards.
- **An LV card cannot reach the HV slot.** The HV card uses a different connector (Micro-Fit harness) in a separate bay behind the 600 V barrier rib, so the two can't be mixed up mechanically.
- **ID EEPROM on every card:** AT24CS32-STUM-T (C147891), 32 Kbit, SOT-23-5, $1.43 / $1.17, stock 243 [M-LCSC].
  - I believe the AT24CS family carries a factory 128-bit read-only serial number. I haven't re-read the datasheet this run, so treat that as [DS to verify].
  - Proposed record: `magic, format_ver, card_type(u16), hw_rev, variant (e.g. 12/24 V, channel count), declared VBAT_FIELD max current, declared +5V/+3V3 load, manufacture date, calibration block (per-channel gain/offset), CRC-16`. The serial number comes from the factory area.
  - **HV card:** the record also holds the ADE9000 calibration (gain/phase/offset per channel), so a replacement meter card brings its own calibration. The EEPROM sits on the SELV side, beside the ISOW7841 primaries. Its I2C crosses J31/J32, using the spare pin plus one of the 5 GND pins, or a 2×10 Micro-Fit [E]. That is the only HV-card change.
- **Slot detection:**
  - PRESENT_N is read through a backplane TCA9555.
  - SLOT_ID straps let the card report which slot it is in, so firmware can cross-check that slot n answered on mux channel n.
  - The HV card keeps `MTR_DET_N` as it is today.

### 2.4 Per-slot power budget
| Rail | Per-slot limit | Hardware | Notes |
|---|---|---|---|
| VBAT_FIELD | **6 A continuous [E]**; pulses up to the slot trip | TPS48100-Q1 + 2× BSC070N10NS5 + shunt, the same circuit as fuel/crank (`bom/design_spec.md`) | With a 10 mΩ shunt the trip scales to about 7.7/9.9/12.3 A (min/typ/max). I derived that from the 20 mΩ figure of 3.86/4.97/6.14 A; check it against the datasheet in Phase 2. 9 contacts × 2 A = 18 A rated, so 6 A leaves 3× margin |
| +5V_SLOT | 0.5 A | TPS2553 with RILIM 49.9k, about 0.52 A nominal (`RAIL_PLAN` §USB) | Enabled by firmware after the ID check |
| +3V3_SLOT | 0.25 A [E] | TPS2553, RILIM to pick | |
| +3V3_ID | < 5 mA | 100 Ω series | Always on, so the EEPROM can be read before the card is powered |

- **The system limits still apply on top:** F1 chain 10 A at room / 8 A hot, and AUX caps of 5.0 A room / 3.0 A hot (`firmware/ARCHITECTURE.md` §12).
- **At boot,** firmware adds up each card's declared draw from its EEPROM. If enabling a card would exceed the slot or system budget, that card stays off and raises a `CARD_BUDGET` alarm.
- **Output current ratings stay as today:**
  - HSO-5: 2.0 A per output (`aux_out_limit_A`), TPS1HTC30 ILIM 3.18/4.02/4.87 A at RILIM 24.9k (ARCHITECTURE §13.9).
  - BRK-4: 5 A coil pulses of 100 ms or less, one at a time through the existing queue.
  - The known open item carries over: the 5 A pulse is above the TPS1HTC30's ILIM.

### 2.5 HV isolation and creepage
- **The HV card is the existing `genctl_meter`** (82 × 167 mm coplanar side-car). Its rules are unchanged:
  - 600 V creepage between hot nets of 5.5/6.3 mm;
  - 8.0 mm clearance and 6.6 mm creepage from live parts;
  - reinforced 8.0/12.6 mm where earthed metal is involved (enclosure v3 README, Phase 14).
- **The isolation barrier is on the card:** the ISOW7841 isolators with their integrated DC-DC.
- **Only SELV crosses to the mainboard:** 7 SPI/control lines, +3V3, GND, detect (SPLIT_SCOPE §1), plus the new EEPROM I2C pair.
- **J28/J29/J30 stay on the card** as pluggable Phoenix plugs, so a swap needs no rewiring.
- **⚠ CT secondaries must be shorted before J30 is unplugged.** An open CT secondary on a loaded generator can produce dangerous voltage. The install guide must require a shorting terminal block in the CT circuit (INSTALL_SAFETY update in Phase 2).

---

## 3. Safety

### 3.1 Swap rule
- **Power off to swap, both battery and AC.** For the HV card, isolate the voltage-sense feeds and short the CTs first.
- **Hot-swap is not supported.** It is made *survivable*, which costs little:
  - Each slot's TPS48100 and TPS2553 enables are ANDed in hardware with PRESENT. Pulling a live card cuts its slot power immediately, with no firmware step.
  - OUT_EN = WD_OK AND SLOT_EN_x AND PRESENT, also in hardware. Every card output buffer (SN74LVC541 OE) is off unless the watchdog is healthy, and every driver EN input has a pull-down on the card. That is today's fail-safe default (ARCHITECTURE §2, §13.2), carried onto the card.

### 3.2 What the STM32 does
At boot every slot is unpowered. Firmware then reads PRESENT_N, then each EEPROM on +3V3_ID, then compares what it finds with the **commissioned configuration** stored in FRAM (slot → card type + serial):

| Case | Action |
|---|---|
| Card matches type and serial | Power the slot, run the card self-test (output-off readback, DI bias test), enable |
| **Same type, new serial** (a replaced card) | Power and self-test, load calibration from the card, show "Card replaced: slot n" on the UI. **The next start needs an operator acknowledgment** at the panel (recommended; open question 3) |
| Missing, wrong type, unknown type, bad CRC, fails self-test, or over budget | **Slot stays unpowered.** Raise `CARD_FAULT` slot n. Every function mapped to it is unavailable. If any of those functions is **protection-class** (a shutdown input, or the GCB on a paralleled set): **no start** (IDLE → PREHEAT refused, like the DI_BIAS lockout rule). Otherwise: alarm only |
| New card in a slot that wasn't commissioned | Power it, raise a "new card" notice. Its channels stay unmapped until they're assigned in the config suite |
| Card lost while running (PRESENT edge, failed SPI/CRC, CARD_FAULT_N) | Its slot power drops in hardware. If the card carried a protection-class function: shut down on the existing fault path (FUEL_EN = 0, GCB open; the EN gates and the VBAT_ESTOP feed are on the mainboard, so this always works, even if the lost card is the engine card: no engine card = no fuel). Otherwise: alarm. A missing BRK-4 blocks every breaker close but never opens a closed breaker by itself. That mirrors the METERING_SILENT BUS rule, and the ESTOP_TRIP breaker shunt-trip (U68) stays on the mainboard. Re-enumeration only happens after a power cycle |
| HV card | Existing `FW_REQ_METERING_PRESENCE` rules, plus `METERING_UNCALIBRATED` (blank or bad calibration CRC) → block breaker close until it's calibrated (open question 3 also covers this) |

### 3.3 Auto-configuration
- **Card drivers are picked by card type ID.** The channel map is `logical function → (slot, channel)` or `(MB, channel)`. It lives in FRAM with CRC and A/B copies, like the battle-short config, and can only be edited while stopped.
- **The CM5 config suite** shows the cards it found and lets the user map functions to channels. The STM32 validates the map against SAFE_MAX, as it does today.
- **Moving a card to a different slot** is allowed after an acknowledgment. The serial number follows the card, and the map follows by serial when the type is unique.

### 3.4 Paths that never cross a card
- E-stop loop, sense and latch, the J23 E-stop feed, ESTOP_TRIP, and the watchdog/latch (TPS3431, 74LVC1G74) with the WD_OK AND gates.
- Phase 2 change: fuel, crank, glow, MPU/D+ speed, DI1-4 and AI1-2 now cross the **keyed engine slot** (§9). Only VBAT_ESTOP (switched upstream) and already-gated EN signals go to the card, so no card fault can turn fuel on.
- External relays stay de-energize-to-stop (ARCHITECTURE §11.1). Pulling any card can only de-energize its outputs.

---

## 4. Mechanical (rough, [E] unless noted)
- **Today [M]:** board 284 × 210 at Z 16.0 (F) / 17.6 (B). Rear shell 294 × 226 × 48 (Z 4-48). 30.4 mm free behind the board. Total depth behind the front face 68.25 mm. The field plugs already exit through rear windows.
- **Recommended: rear-loading vertical cards in two bays.**
  - **Bays:** two of 4 slots each at 20 mm pitch.
    - Top bay at about x 108-188 / y −11..83, where the output terminal row J24-J27 is today.
    - Bottom bay at about x 108-188 / y 96..190, where the input row J19/J20 is today.
  - **Card:** about 100 × 30 mm, 1.6 mm, 4-layer, parts up to about 10 mm on the front side and 3 mm on the back. That gives 3,000 mm² per side, against a 1,100-1,350 mm² courtyard need per card [M fparea], so 20-45 % used.
  - **Height stack:** the card edge sits about 13 mm above the board in the 11.6 mm female (from the DS drawings). The card top lands at about Z 61, and a right-angle KF2EDGR-style header on the top edge takes the plug, mated, to about Z 76.
  - **Shell change:** the shell skin over the two bays moves from Z 48 to about Z 62 (**+14 mm**). Each card's PA12 faceplate sits flush in the skin, with card guides printed into the shell and one captive screw per card. The fin plate and CM5 heat path elsewhere are unchanged.
  - **Overall depth:** about 76 mm to the plug tips, against 68.25 mm (**+8 mm**). The outline (294 × 226) and panel cutout are unchanged.
  - **Swap:** unplug the field plug(s), loosen 1 screw, pull the card. The enclosure is never opened.
- **Mainboard area:** the bays take about 16,000 mm² (DIN sockets plus the space under the cards). Low parts (≤ 12 mm) can still go in the 9.4 mm strips between sockets, which is where the slot power switches go.
  - Outside the bays: about 42,000 − 16,000 = 26,000 mm² usable, for about 16,750 mm² of remaining mainboard courtyard plus about 1,200 mm² of slot switches. That's about **69 % used**, against 56 % today [E].
  - Tighter, but still fine. The blocks study found the problem was organization and rules, not area.
  - **Shell posts 1 and 2** (x 95-105) border the bays, so they may need to move slightly.
- **HV card:** stays in its coplanar side-car bay with the barrier rib at x 73. Swapping it means opening the rear shell. That's acceptable, because it should be rare and needs a full 600 V isolation anyway.

**Mechanical alternatives:**

| | A. Coplanar tiles (like the HV side-car) | **B. Rear-loading vertical bays (recommended)** | C. Stacked mezzanine |
|---|---|---|---|
| Depth change | 0 | +8 mm overall (+14 mm in the bays) | 0 if ≤ 22.8 mm stack over low-profile areas only (blocks report §8) |
| Swap without opening the shell | No (shell off, and the clamps hold through the shell) | **Yes** | No |
| Space | Tiles eat mainboard outline | Bays reuse today's terminal-row zones | Only over low-profile areas, and it fights the CM5 heat path |
| Verdict | Fallback if no depth change is allowed | **Pick** | Not recommended |

---

## 5. Cost and part-count delta (`modular/cost_delta.csv`)
Build 2 (baseline-equivalent I/O: DI-8, AI-4, 2× HSO-5, BRK-4, HV) against the one-board baseline:

| Group | qty 1 | qty 10 (per unit) | Source |
|---|---|---|---|
| Backplane, 8 slots (DIN female, TPS48100 + 2 FETs + shunt, 2× TPS2553, AND gate, passives) | $56.95 | $47.72 | M-LCSC / M-BOM, passives E |
| Backplane shared (TCA9548A, 2× TCA9555, TMUX1208, decoder) | $3.15 | $2.48 | M, decoder E |
| Card overhead (5 DIN males, 6 EEPROMs, 4 MCP23S17, 3 '541, 3 TMUX1208, TCA9555, DI bias copy, passives) | $29.50 | $24.36 | M, some E |
| 4 extra PCB/PCBA orders (PCB $8, fixed fees $13.74, extended-part loading about $18.42 per order) | $160.64 | $17.66 | E / DS (JLC fee table via SPLIT_SCOPE §7) |
| Mechanical (card bays, faceplates, guides) + HV harness tweak | $26.00 | $15.80 | E |
| **Total** | **≈ +$276** | **≈ +$108** | |

- **Against the controller totals** of $1,767.45 / $1,259.04 (`review/bom_split/totals.json`): **+15.6 % / +8.6 %**.
- **Savings not subtracted:** shared mainboard parts made redundant by cards ('541s, TMUX1208s, some TCA9555s).
- **Build 1** (1 HSO-5) needs only 1 card design ordered, so its delta is roughly backplane $60 + card $7 + 1 order $40 + mechanical $26, **about +$133 at qty 1 [E]**. It also has fewer parts than today's board.
- **Spares, parts only, qty 1** [M-BOM moved + overhead]:

  | Card | Cost |
  |---|---|
  | DI-8 | about $19 |
  | AI-4 | about $8 |
  | HSO-5 | about $29 |
  | BRK-4 | about $25 |

  Add about $3-40 of board and fees, depending on batch size [E]. **Compare: a single dead output on the one-board design means a whole new main board** (about $210 of fab/assembly estimate + $343 of parts, from SPLIT_SCOPE).

### Partition options compared
| | P1. Few big cards (IN, OUT, HV) | **P2. Universal function cards (recommended)** | P3. Per-channel plug-in modules | P4. Remote DIN-rail I/O over CAN/RS-485 |
|---|---|---|---|---|
| Cards in a full build | 3 | 6 | ~45 | n/a |
| Configurable per generator | Low | **High** (any LV card, any slot) | Highest | High |
| Spare cost when one channel dies | ~$45-55 [E] | ~$8-29 | ~$1-5 | Varies |
| Cost delta, qty 1 / qty 10 | ~+$125 / +$50 [E] | +$276 / +$108 | ~+$300 / +$150 [E]: 45 connectors, no room for per-module EEPROMs | Off-board modules |
| Safety | Simple | Simple; ID per card | Hard: 45 contacts to trust, no ID | **Protection must not depend on a bus**, so it only suits non-protection expansion |
| Fits the enclosure | Needs taller cards | Yes (+8 mm) | Yes but crowded | n/a |

**P2 wins on configurability, repair cost and safety.** P4 stays as a future add-on through the existing J7 expansion bus.

---

## 6. Fit with the other plans
- **Ethernet paralleling (decided Nov 23):** the network talk uses the CM5 Ethernet port, so it needs no card. The undesigned governor/AVR bias becomes the **PAR card**.
  - It needs an isolated bias output to suit each governor and AVR, from a DAC over the slot SPI, so it needs no timer pins.
  - It can go in any spare LV slot. The sync check and reverse-power trip stay local on the STM32, from HV-card readings.
- **Block-based layout plan:**
  - Every card is a natural, self-contained block: laid out once, with its own rules, and reused across builds.
  - The mainboard drops from about 33-36 blocks to about 25, plus 8 identical slot tiles (socket + power switch) that can be pre-baked.
  - The HV meter card is still the first test for the layout tool. Its only change here is the EEPROM.
- **Battle short:** unchanged. Its scope (E-stop + overspeed) stays entirely on the mainboard.

---

## 7. Phase 2 (after Ethan's OK, on this branch, local commits only)
1. Schematic: slot sheet (one hierarchical sheet × 8), card projects (DI-8, AI-4, HSO-5, BRK-4) built from the baseline sheets, EEPROM + I2C on the HV card.
2. STM32 pin plan for the slot SPI/I2C/ADC. Confirm the AT24CS32 address and serial-number area. Check the TPS48100 trip at 10 mΩ.
3. Firmware spec: FW_REQ_CARDS.md (§3 above), EEPROM format, config-suite mapping.
4. Enclosure v4 card bays (Mechanical). INSTALL_SAFETY: power-off swap and the CT shorting block.
5. Re-run ERC/BOM checks per project.

## 8. Open questions for Ethan
1. Is **about +8 mm overall depth** OK (the card bays stick out 14 mm) so cards can be swapped from the rear without opening the box?
2. ~~Keep the engine core fixed?~~ Decided Nov 23 10:24: engine I/O goes on a keyed card (§9). E-stop, watchdog and latch stay fixed.
3. A **replaced card of the same type**: require a panel acknowledgment before the next start (my pick), or auto-accept? The same goes for a blank-calibration HV card.
4. **8 LV slots** (5 used in a full build), or 6 to save about $14 per unit?
5. **Power-off swap only** OK? True hot-swap would need staggered-contact connectors, and I haven't priced those.

---

## 9. Phase 2: dedicated keyed ENGINE I/O card (Nov 23, 10:24 AM HST decision)

Why: Ethan asked whether fuel, crank, glow, speed and the core inputs are just as likely to fail or get shorted as the other I/O. They are: they face the same field wiring. So they go on a swappable card too, in a slot of their own.

### 9.1 What is where
| On the mainboard (fixed) | On the ENGINE card (`cards/engine/`, 156 parts [M]) |
|---|---|
| STM32, watchdog + WD_OK latch (U84), FUEL/CRANK/GLOW_EN AND gates (U38-U40) | Fuel + crank TPS48100 drivers, FETs, shunts, INA281 current sense |
| E-stop input J23 (VBAT_ESTOP_IN), reverse-block FETs Q70/Q71, E-stop sense/latch/trip | Glow driver TPS1HTC30 + its protection |
| FRAM, supplies, CM5/display/comms, front panel | MPU speed front end, D+ excitation (LM317) + sense, COM_A/B |
| J23 also carries FUEL_OUT/CRANK_OUT to the engine harness | DI1-4 and AI1-2 front ends, DI_BIAS_A input clamp |
| | Field headers: COM/MPU (moved J18), new DI1-4/AI1-2, new D+/GLOW/BIAS (same KF2EDGRM-5.08-6P part, C441292) |
| | ID EEPROM AT24CS32 (type 0x0001 = engine) |

### 9.2 E-stop cut location (checked against the baseline netlist) [M]
- **The cut is external and upstream.** J23.1-2 (VBAT_ESTOP_IN) comes from the external E-stop / power box F2 10 A. Q70/Q71 SQD40P10-40L are reverse-block FETs that make VBAT_ESTOP. VBAT_ESTOP feeds the fuel and crank TPS48100s (U43/U45 VS/CS+) through 20 mΩ shunts. So no driver sits upstream of the cut, and the boundary works as planned: **VBAT_ESTOP goes to the card, FUEL_OUT/CRANK_OUT come back, and J23 stays on the mainboard.**
- **Watchdog gating is logic-level only.** FUEL/CRANK/GLOW_EN = *_EN_MCU AND WD_OK, through U38-U40 on the mainboard. A watchdog trip turns the drivers off, but it does not remove the rail. A shorted driver FET keeps fuel on until the external E-stop opens, **the same as the baseline**. This is a design issue (§9.7, item 1).
- **Glow was on VBAT_P, not VBAT_ESTOP.** The E-stop did not cut glow. On the card, glow VS is moved to VBAT_ESTOP, as decided. This is the only intentional net change (`cards/engine/net_accounting.csv`, override listed in `cards/tools/card_engine.py`).

### 9.3 Fail-safe rules met
- The card's driver supply comes only from the mainboard VBAT_ESTOP over the slot. With no card, nothing can drive FUEL_OUT: fuel is energize-to-run, so the engine stops.
- EN signals arrive already gated by WD_OK. The card has its own pull-downs on them (baseline parts, moved).
- ENG_PRESENT_N is tied to GND on the card, and the ID EEPROM type must be 0x0001. If either is missing, the firmware blocks start and shows "ENGINE CARD MISSING" (FW_REQ_CARDS).
- Keying: the engine card edge has a coding notch at a different position from LV cards, with a matching rib in the engine bay. Two-way coding means an LV card can't go in the engine slot and the engine card can't go in an LV slot.

### 9.4 Contacts: parallel DIN 41612 contacts, no extra power connector
2 A per contact [DS], derated 50 % to 1 A:

| Net | Contacts | Rated / derated | Needs |
|---|---|---|---|
| VBAT_ESTOP | 12 (a/b/c 1-4) | 24 A / 12 A | ≥ 10 A F2 fuse ✓ |
| FUEL_OUT | 8 (a/b/c 5-6, a/c 7) | 16 A / 8 A | ≥ 6.14 A max short-circuit trip (TPS48100, 40.2k / 20 mΩ) ✓ |
| CRANK_OUT | 8 (a/b/c 8-9, a/c 10) | 16 A / 8 A | same ✓ |
| VBAT_P (MPU/D+ bias only) | 2 | 4 A / 2 A | < 0.2 A [E] ✓ |

The full pinout is in `cards/engine/engine_slot_pinout.csv`. Signals use rows a and c (positions 14-31), every b contact from 11 to 32 is GND (guard), and b7/b10 are GND between the power groups. The 4 extra output contacts came from the spare GND positions 30-31, so no pin is short. **Budget flag:** fuel 2.8 A + crank 2.8 A + glow ~2 A = 7.6 A, above the 6 A that the baseline allowed for the VBAT_ESTOP node. It is still under the 10 A F2 fuse and the 12 A contact rating, but the VBAT_ESTOP copper and the Q70/Q71 FETs need re-checking for glow (open question 9.8-2).

### 9.5 Datasheet checks done this phase
- **AT24CS32** (LCSC C147891 PDF) [DS]:
  - SOT-23-5 pinout: 1 SCL, 2 GND, 3 SDA, 4 VCC, 5 WP.
  - EEPROM at 0x50. In SOT-23 the A2..A0 bits are fixed at 0, so every card reads as 0x50 and each card needs its own mux channel.
  - 128-bit factory serial, read-only, at 0x58.
  - WP: 10k pull-up to 3V3 on the card. A slot ID_WP pin lets firmware write.
- **Slot ID mux count:** 8 LV + engine + HV = 10 ID buses, more than the TCA9548A's 8 channels. So a second TCA9548A (0x71) is needed, priced in.
- **TPS48100 LV-slot limit** (TI TPS4810-Q1 Eq. 5: RISCP = (ISC·RSNS − 19 mV)/2 µA) [DS]:
  - Baseline check: 40.2k with 20 mΩ gives 4.97 A ✓.
  - With 10 mΩ and 40.2k it would be 9.9 A typ, too high.
  - **Use 10 mΩ + 30.1k: 7.9 A typ, ~6.2-9.8 A min/max [E, tolerance scaled].** The minimum is above the 6 A slot budget.
- **STM32 pins:** all 100 pins of U7 are used. The slot ID bus goes on **I2C2 = PB10/PB11 (pins 46/47, AF4; confirm in DS12110)**. Those pins carry DI8/DI9 today and are freed when the DI-8 card serializes DI5-12 behind its SPI expander. This also keeps card EEPROMs (0x50) off I2C1, where the FRAM (0x50) and ADS1115s (0x48/0x49) already sit.

### 9.6 Schematic rule (Ethan, 10:26): one flat sheet per card
Each `cards/<name>/` project is one A3 sheet with no sub-sheets, using net labels and rendered to PNG/PDF. The engine card fits (156 parts, ERC 0 errors / 0 warnings): `cards/engine/engine.png`. **The HV meter card does not fit legibly on one sheet:** it has about 215 parts plus 600 V creepage notes, and is two sheets today (root + `ac_metering`). It stays a 2-sheet project, with the EEPROM added on its SELV side, unless Ethan wants it on A2 or split into two cards.

### 9.7 Design issues
1. **No rail-level watchdog cut** (baseline issue, carried over). Proposal: a mainboard P-FET or ideal-diode controller in series with VBAT_ESTOP, gated by WD_OK AND ESTOP_OK. Then a shorted driver FET or a stuck card is cut by the watchdog as well, not only by the external E-stop. That is about 3-5 parts [E], and the parts aren't picked yet.
2. Glow now draws on VBAT_ESTOP (see §9.4 budget).
3. DI_BIAS_A is shared: DI1-4 on the engine card use it, and DI5-6 (DI-8 card) use bank A too. It crosses the slot on one contact (PTC-limited).
4. Mainboard terminals J17.1-2, J18 (whole), J19.1-4, J21.3 and J24.1 become NC when the engine card fits. J18 moves to the card, and the mainboard layout loses those terminal positions.

### 9.8 Updated cost delta (`modular/cost_delta.csv`)
The total is now **+$326 at qty 1 and +$120 per unit at qty 10** (it was +$276 / +$108). The engine-slot lines add $49.77 / $12.12: DIN pair, EEPROM, second I2C mux, 2 extra field headers, engine card PCB + fees, bay guide. Savings from parts removed from the mainboard are not subtracted.

### 9.9 Open questions
1. Add the rail-level watchdog cut (§9.7-1)? My pick: yes.
2. Glow on VBAT_ESTOP: OK to re-rate the VBAT_ESTOP path for 7.6 A?
3. HV meter: keep it as 2 sheets (my pick), or go to A2?
