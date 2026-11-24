# Modular "card" architecture: Phase 1 proposal, Phase 2 cards, mainboard rework (§12)

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

> **Pass 1 update (§13):** +5V_SLOT is removed; a8/b8 are reserved (NC). `slot_pinout_LV.csv` is current.
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
| 15 | **OUT_EN_N** (active low, Phase 2), CARD_FAULT_N |
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

> **Pass 1 update (§13):** the slot shunt is now 5 mΩ (trip 10.7/13.6/16.6 A), the LV slots share a bank limiter (9.2/11.6/14.4 A), and +5V_SLOT is gone. The figures below are the Phase 1 proposal.
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
  - OUT_EN_N = NOT(WD_OK AND SLOT_EN_x AND PRESENT), also in hardware (Phase 2: active low with a 10k pull-up on every card, so an open or unplugged line means outputs off). Every card output buffer (SN74LVC541 OE) is off unless the watchdog is healthy, and every driver EN input has a pull-down on the card. That is today's fail-safe default (ARCHITECTURE §2, §13.2), carried onto the card.

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

> **Superseded:** the current cost is in §13 (`true_cost_delta.csv`). This section is the Phase 1 estimate.
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
1. **No rail-level watchdog cut** (baseline issue, carried over; **resolved and drawn, §11.1/§12.3**). Original proposal: a mainboard P-FET or ideal-diode controller in series with VBAT_ESTOP, gated by WD_OK AND ESTOP_OK. Then a shorted driver FET or a stuck card is cut by the watchdog as well, not only by the external E-stop. That is about 3-5 parts [E], and the parts aren't picked yet.
2. Glow now draws on VBAT_ESTOP (see §9.4 budget).
3. DI_BIAS_A is shared: DI1-4 on the engine card use it, and DI5-6 (DI-8 card) use bank A too. It crosses the slot on one contact (PTC-limited).
4. Mainboard terminals J17.1-2, J18 (whole), J19.1-4, J21.3 and J24.1 become NC when the engine card fits. J18 moves to the card, and the mainboard layout loses those terminal positions.

### 9.8 Updated cost delta (`modular/cost_delta.csv`)
The total is now **+$326 at qty 1 and +$120 per unit at qty 10** (it was +$276 / +$108). The engine-slot lines add $49.77 / $12.12: DIN pair, EEPROM, second I2C mux, 2 extra field headers, engine card PCB + fees, bay guide. Savings from parts removed from the mainboard are not subtracted.

### 9.9 Open questions
1. Add the rail-level watchdog cut (§9.7-1)? My pick: yes.
2. Glow on VBAT_ESTOP: OK to re-rate the VBAT_ESTOP path for 7.6 A?
3. HV meter: keep it as 2 sheets (my pick), or go to A2?

## 10. Phase 2: the four universal LV cards (Nov 23, HST)

Each card is one flat A3 sheet in `cards/<card>/` made by `cards/tools/lvcards.py`, ERC 0 errors / 0 warnings, rendered to `<card>.png` and `.pdf`.

### 10.1 Card type codes (AT24CS32 at 0x50, serial at 0x58, on the slot I2C bus)

| Code | Card | Parts | Where |
|---|---|---|---|
| 0x0001 | ENGINE (keyed slot) | 156 | cards/engine |
| 0x0010 | DI-8 | 76 | cards/di8 |
| 0x0011 | AI-4 | 104 | cards/ai4 |
| 0x0012 | HSO-5 | 76 | cards/hso5 (2 per example build: AUX1-5, AUX6-10) |
| 0x0013 | BRK-4 | 64 | cards/brk4 |
| 0x0020 | HV-METER | | genctl_meter |

### 10.2 Self-contained: nothing shared between cards
- **DI-8:** own bias switch/eFuse/PTC/TVS (copy of the bank-B block, fed from VBAT_FIELD), own 74HC14s (U33 moved plus a copy of U32 for IN1/IN2), own MCP23S17.
- **AI-4:** own ADS1115 (0x48), own VMID buffer, own VBAT_AI pre-regulator plus LM4040 current-source reference, own MCP23S17.
- **HSO-5 / BRK-4:** own SN74LVC541A enable buffer, own TMUX1208 current-sense mux to ANA_OUT, own MCP23S17.
- **Clamps:** the shared BAT54C clamps are split.
  - D128 GLOW half and D130 AUX1 half are left NC on BRK-4.
  - HSO-5 gets its own BAT54C for OUT1.
  - The mainboard gets a new BAT54C for GLOW_SNSM + ESTOP_TRIP_SNSM.
- **ESTOP_TRIP:** the current sense moves off HSO-B onto the mainboard safety path. U63 stays on the mainboard for glow + ESTOP_TRIP; U64 and D133-D135 go.

### 10.3 Universal LV pinout changes (docs/modular/slot_pinout_LV.csv)
- **15a OUT_EN → OUT_EN_N.** Active low, driven by the backplane, with a 10k pull-up on the card, so an open line means off. It gates the card '541 OE1/OE2.
- **18a RSVD → ID_WP.** EEPROM write protect, 10k pull-up to +3V3_ID on the card. The backplane pulls it low only for factory or calibration writes.
- On every card: FIELD_GND and PRESENT_N join GND; unused slot signals are NC on the card.

### 10.4 Intentional net changes (per card: `cards/<card>/net_changes.csv`; full accounting: `net_accounting.csv`, 0 unaccounted on every card)

| Baseline | On the card | Why |
|---|---|---|
| VBAT_P / +3V3_SAFE / OUT_FAULT_N | VBAT_FIELD / +3V3_SLOT / CARD_FAULT_N | slot-switched supply; fault is per card, with a card pull-up |
| DI5-DI12, DI_BIAS_B, DI_PU_B, DI_PD_B, DI_BIAS_FLT_N | IN1-IN8, BIAS, BIAS_ON, BIAS_DISCH, CARD_FAULT_N | DI-8 names |
| R222.1, R225.1 on DI_BIAS_A | BIAS | DI5/DI6 move off bank-A bias onto the card bias |
| J22.2-4 (DI_BIAS_B terminal) | IN1, IN2, GND | J22 becomes the IN1/IN2 terminal |
| DIx_N to STM32 pins; U31 (TCA9555) bias controls | card MCP23S17 | DI read over the slot SPI |
| AI3-AI6, AI_CS_DISx, AI_SH_ENx, AI_SH_Gx | IN1-IN4, CS_DIS1-4, SH_EN1-4, SH_G1-4 | AI-4 names; J17.3-6 become NC |
| SH_G = SH_EN AND SH_ALLOW (U91 '08) | SH_G = '541(SH_EN), OE = OUT_EN_N, RN pull-downs | shunt only closes while the slot is enabled (watchdog healthy) |
| AUX1-5_* / GCB_CL, GCB_OP, MCB_CL, MCB_OP_* | OUT1-5_* / OUT1-4_* | HSO-5 / BRK-4 names |
| *_EN from mainboard U41/U42 '541 | card '541 (OE = OUT_EN_N) | |
| *_RB_N to U62 TCA9555 | card MCP23S17 | |
| *_SNSM to U63/U64 TMUX | card TMUX1208, D → ANA_OUT | |
| DIAG_EN (one net, 15 drivers) | per-card DIAG_EN from MCP23S17 | |
| D128.1 GLOW_SNSM, D130.2 AUX1_SNSM | NC | clamp halves split (see 10.2) |

### 10.5 HSO-5 slot-ID straps
HSO-5 uses all 16 MCP23S17 GPIOs except two, so it reads only SLOT_ID0/1 (GPA6/7). Its slot identity also comes from the TCA9548A channel its EEPROM answers on. If Ethan wants all 4 straps read, the options are a second expander or a TCA9534 on the slot I2C bus [open].

### 10.6 HV meter ID EEPROM (genctl_meter, still 2 sheets, ERC 0/0)
- **Parts added on the SELV side (+3V3 / GND, not GND_AC):**
  - U94 AT24CS32-STUM-T (LCSC C147891, type 0x0020);
  - R650 10k WP pull-up (C98220);
  - TP3 EE_WP pad (short it to GND only for a calibration write);
  - C323 100n (C14663).
- **Harness pins:** J32.12 goes from GND to MTR_ID_SCL, and J32.16 goes from spare (NC) to MTR_ID_SDA.
  - J32.15 stays the MTR_DET_N GND strap.
  - 5 GND pins remain (3, 5, 7, 9, 15).
  - The harness is already 16 wires pin n to pin n, so it needs no change.
- **Mainboard side:** J31.12 and J31.16 must carry the same nets to the HV TCA9548A channel, with 4.7k pull-ups there (see §11).
- **Cost:** meter BOM goes from $63.90 to $65.33 at qty 1, and from $53.42 to $54.60 per board at qty 10 (bom/genctl_meter_bom.csv, 221 refs, 0 mismatches).

## 11. Phase 2: watchdog rail cut, Q70/Q71 thermal check, datasheet checks, true cost (Nov 23, HST)

> **Pass 1 update (§13):** D126 is now SMDJ36CA, and the rail-cut enable has an RC proof-test timer. The text below is the Phase 2 state.

### 11.1 Watchdog rail cut (now drawn: `estop.kicad_sch`, see §12)
- **Circuit:** a copy of the proven fuel-driver circuit, placed in series after Q70/Q71.
  - Parts: TPS48100QDGXRQ1 (C43131316), 2× BSC070N10NS5 in parallel (C534364, 100 V, 7.0 mΩ max), and an RLP25FEER002 2 mΩ 2 W 2512 shunt (C160590, LCSC stock 31,525).
  - Same 100 V FET rating, same SMDJ40CA TVS (D126) on the input, same EN/UVLO divider (100k/27k), TMR 4.7n, BST 470n, G1PU 10R, G1PD 0R.
- **Control:** INP = **WD_OK AND ESTOP_OK**, with ESTOP_OK = NOT ESTOP_DIG.
  - New 74LVC1G08 (C176929); the inverter is the spare U34 74HC14 gate on pins 9→8.
  - A 100k pull-down on INP means that losing logic or +3V3_SAFE opens the rail (fail-safe = no fuel).
  - FLT goes to OUT_FAULT_N.
- **Short-circuit trip:** R(ISCP) = 10.5k (RC0603FR-0710K5L, C137808). TPS4810-Q1 datasheet table: V(SCP) = 31.6 / 40 / 49.5 mV at 10.5 kΩ, so with 2 mΩ the trip is **15.8 / 20 / 24.8 A** (min/typ/max).
  - The minimum is above the 10 A F2 fuse, so the cut never nuisance-trips at the full fuse current. F2 stays the overcurrent device; the cut is the watchdog disconnect plus a backup trip.
- **Net split (intentional change):**

| Net | Nodes |
|---|---|
| VBAT_ESTOP_RP (new, pre-cut) | Q70.3, Q71.3, D126, D137 (Q70/Q71 gate clamp), C199, R251 (VESTOP_D, E-stop status), R400 (TRIP_QB), cut VS/CS+, shunt pin 1, EN divider |
| VBAT_ESTOP (post-cut) | cut FET sources, SRC, BST cap, C203, R411 (VESTOP_SNS to ADC), engine slot contacts 1-4 a/b/c |

  - The ESTOP_DIG status is taken from the pre-cut node, so the cut cannot latch itself off.
  - The ADC reading on the post-cut node lets firmware prove that the cut opened. That is a boot self-test: pull WD_OK low and expect VESTOP_SNS to read about 0 V.

### 11.2 Dissipation and junction temperature (ambient 104 °F; `modular/tools/railcut_thermal.py`)
TjMax is 347 °F for SQD40P10-40L and 302 °F for BSC070N10NS5. The 60/40 rows assume an uneven current split [E]; the 532 °F figure means thermal runaway.

| Total A | Part | A in part | Loss W | Tj °F | Rise °F |
|---|---|---|---|---|---|
| 7.6 | Q70/Q71 SQD40P10-40L (each, 50/50) | 3.8 | 0.86 | 182 | 78 |
| 7.6 | Q70/Q71 SQD40P10-40L (hot FET, 60/40) | 4.6 | 1.45 | 235 | 131 |
| 7.6 | Ideal-diode LM74700-Q1 + 1x BSC070N10NS5 (single FET, chosen §12.2) | 7.6 | 0.49 | 148 | 44 |
| 7.6 | Rail-cut BSC070N10NS5 (each, 50/50) | 3.8 | 0.11 | 114 | 10 |
| 7.6 | Rail-cut BSC070N10NS5 (hot FET, 60/40) | 4.6 | 0.16 | 119 | 15 |
| 7.6 | Shunt 2 mOhm 2512 (2 W) | 7.6 | 0.12 | - | - |
| 10.0 | Q70/Q71 SQD40P10-40L (each, 50/50) | 5.0 | 1.99 | 283 | 179 |
| 10.0 | Q70/Q71 SQD40P10-40L (hot FET, 60/40) | 6.0 | 4.75 | 532 | 428 |
| 10.0 | Ideal-diode LM74700-Q1 + 1x BSC070N10NS5 (single FET, chosen §12.2) | 10.0 | 0.94 | 189 | 85 |
| 10.0 | Rail-cut BSC070N10NS5 (each, 50/50) | 5.0 | 0.20 | 122 | 18 |
| 10.0 | Rail-cut BSC070N10NS5 (hot FET, 60/40) | 6.0 | 0.29 | 130 | 26 |
| 10.0 | Shunt 2 mOhm 2512 (2 W) | 10.0 | 0.20 | - | - |

| Current | 1 oz outer, 18 °F rise | 1 oz outer, 36 °F rise | 2 oz outer, 18 °F rise | 0.5 oz inner, 18 °F rise |
|---|---|---|---|---|
| 7.6 A | 4.9 mm | 3.2 mm | 2.5 mm | 25.6 mm |
| 10.0 A | 7.2 mm | 4.7 mm | 3.6 mm | 37.4 mm |

- **Q70/Q71 are not OK for a clean 10 A rating.**
  - At 7.6 A they are acceptable: 182 °F with an even split.
  - At 10 A they run about 283 °F junction even with a perfect split. With a 60/40 split they run away past TjMax. Their RthJA is 50 °C/W on 1 in² of copper.
  - SQD40P10-40L (C141570) also shows **0 LCSC stock** today.
  - **Decided and drawn (§12.2):** Q70/Q71 are replaced by an LM74700-Q1 ideal-diode controller + 1× BSC070N10NS5 (148 °F at 7.6 A, 189 °F at 10 A).
- **The rail cut is fine:** 122 °F junction at 10 A with an even split, 130 °F at 60/40. The shunt dissipates 0.20 W of its 2 W rating.
- **Copper (IPC-2221) for VBAT_ESTOP_IN → Q70/Q71 → cut → engine slot:** at least **7.2 mm** of 1 oz outer copper for 10 A at 18 °F rise (4.9 mm at 7.6 A).
  - Alternatives: 4.7 mm at 36 °F rise, or 3.6 mm on 2 oz.
  - A 0.5 oz inner layer is not practical (37 mm), so use outer layers or a pour. The 1 oz / 0.5 oz stackup is still ASSUMED (ROUTING_PLAN).

### 11.3 STM32 I2C2 pins [DS]
- The parent wrote "STM32G474 … DS12110". The MCU is the **STM32H743VIT6** (U7), and DS12110 is the STM32H742/743/753 datasheet. I checked the H743.
- DS12110 rev 10, Port B alternate functions: **PB10 AF4 = I2C2_SCL, PB11 AF4 = I2C2_SDA**. The rev 8 parsed table in firmware/tools agrees.
- On LQFP100 they are U7 pins 46 / 47. Today they go through R38/R39 to DI8/DI9, which move onto the DI-8 card, so both pins are free for the 2× TCA9548A (0x70/0x71) ID bus.

### 11.4 DIN 41612 C96 footprints [DS]
Checked against the WingTAT drawings 9001D11001 R7 (male RA, C5173361) and 9001D12003 R7 (female vertical, C5173363).
- **Correct before and after:** contact span 78.74 (2.54 × 31), row pitch 2.54 (a-c 5.08), contact drill 1.0 ±0.05, mounting holes Ø2.8.
- **Fixed:**
  - Female mounting holes are 90.0 apart (were 88.9), at 2.24 from row a (were at row b).
  - Male RA holes sit 2.54 beyond the outer row on the card-edge side (were at row b). The card edge is 5.30 from that row (now drawn on F.Fab).
  - Male contact 1 is at the right end of the drawing's PCB-layout view.
- **Still VERIFY:** the male drawing does not print row letters. I took the edge row as "a"; check it on a sample before layout.

### 11.5 True net cost delta (`modular/tools/true_cost.py` → `modular/true_cost_delta.csv`, `modular/combined_bom.csv`)
Per controller, example build (ENGINE + 2× HSO-5 + BRK-4 + DI-8 + AI-4 + HV), against the locked baseline:

| | qty 1 | qty 10 (per unit) |
|---|---|---|
| New parts on cards (moved parts are free; 2nd HSO-5 counted) | +$34.86 | +$29.02 |
| Backplane: 9 DIN sockets, 8 slot TPS48100 + FETs + shunts, TPS2553 ×16, ID muxes, clamp | +$63.86 | +$54.86 |
| Watchdog rail cut | +$4.84 | +$4.24 |
| HV meter EEPROM | +$1.43 | +$1.18 |
| Removed from the mainboard (U41, U42, U64, D133-135, RN2, J17, J19, J26) | −$2.90 | −$2.33 |
| Card PCBs + PCBA fees + extended-part loading (5 designs) [E] | +$200.80 | +$22.08 |
| Card bays, guides, faceplates [E] | +$29.00 | +$17.50 |
| **Total** | **+$331.90** | **+$126.57** |

- The combined build BOM has 214 lines and 1,290 parts, plus the 221-ref HV meter board.
- Every price comes from LCSC/JLC (dated in bom/lcsc_prices.csv) except the [E] lines: bare PCBs, fees, guides, the slot shunt part and passives.

### 11.6 Mainboard schematic rework: done, see §12
The items that were only specified here (slot sheets, ID muxes, presence/fault sensing, rail cut and VBAT_ESTOP split, relocated ESTOP_TRIP clamp, J31.12/16, removal of moved parts) are now drawn, ERC-clean and audited end to end. Details in §12. §11.5's estimate is superseded by the BOM-extracted figure in §12.6.

## 12. Phase 2 final: mainboard rework, ideal diode, full-system audit (Nov 23, HST)

### 12.1 Mainboard sheets (`genctl.kicad_sch`, ERC 0 errors / 0 warnings, `docs/modular/erc/genctl_main.rpt`)
> **Superseded in part by §13 (Pass 1 review fixes).** The slot power, slot fault lines, OUT_EN_N logic, ID_WP, rail-cut enable, D126 and limits below describe the Phase 2 state. §13 gives the current design.

Generator: `cards/tools/mainboard.py` (from the locked tag netlist plus the edits it lists; drawn by `schdraw.py`). Drawn-vs-intended check: `cards/tools/verify_mainboard.py` (2,716 pins, 0 errors). Renders: `docs/modular/img/mainboard/*.png` and `genctl_mainboard.pdf`.

| Sheet | Status | Content |
|---|---|---|
| power, cm5, comms, display | unchanged | |
| frontpanel | 3 global labels renamed | U76 P07/P10 spares (were AUX9/10_MCU), P12 spare pull-up (was AUX10_RB_N) |
| mcu (A3) | regenerated | PC10/11/12 = SPI3 slot bus, PE0/PE1/PD11 = CS decoder A0-A2, PD13 = decoder enable, PC9 = SLOT_RST_N, PB4 = SLOT_EXP_INT_N, PB10/11 = I2C2 (R38/R39 removed), PA ADC MUXB_OUT → SLOT_ANA; DI5-12 pins free |
| io_core (A2) | new (replaces inputs + outputs) | what stays: AI1/AI2 + COM ADCs, DI1-4 Schmitt, D+, MPU, U31/U62 expanders, fuel/crank/glow WD gating + latch, U63 sense mux (S1 GLOW, S2 ESTOP_TRIP), new BAT54C clamp GLOW_SNSM + ESTOP_TRIP_SNSM |
| estop (A3) | regenerated | J23 → LM74700-Q1 + BSC070N10NS5 → VBAT_ESTOP_PRE → rail cut → VBAT_ESTOP; trip driver, E-stop sense |
| backplane (A2) | new | ENGINE slot J48 (1:1 with `cards/engine/engine_slot_pinout.csv`: 12× VBAT_ESTOP, 8× FUEL_OUT, 8× CRANK_OUT), LV slots J40-J47 (`docs/modular/slot_pinout_LV.csv`, 15a OUT_EN_N, 18a ID_WP), 2× TCA9548A, SN74LVC138A CS decoder, 2× TCA9555, TMUX1208 ANA mux |
| slot_power (A1) | new | 8× (TPS48100 + 2× BSC070N10NS5 + 10 mΩ, 2× TPS2553, 74LVC1G02 + 74LVC1G00, pull-ups, 100R +3V3_ID) |
| mtr_if (A3) | regenerated | J31.12 = MTR_ID_SCL, J31.16 = MTR_ID_SDA (matching J32.12/16) |

**Slot wiring:**
- Slot n uses ID n−1. ID0..2 bits: 0 = strap to GND, 1 = open (card pull-up). IDP makes ID0+ID1+ID2+IDP odd, so all-open and all-shorted never decode as valid.
- **I2C2 (PB10/PB11 AF4)**, 2.2k root pull-ups.
  - TCA9548A 0x70: channels 0-7 = LV1-8 ID buses. TCA9548A 0x71: channel 0 = ENGINE, channel 1 = HV meter (J31.12/16); channels 2-7 are unused (NC).
  - 4.7k pull-ups on every used channel. Reset is a 10k pull-up.
  - Slot expanders on the same root bus: TCA9555 0x20 (P0 = SL1-8_EN_N, P1 = SL1-8_FAULT_N) and TCA9555 0x21 (P0 = SL1-8_INT_N, P1 spare). Their INTs go to SLOT_EXP_INT_N on PB4.
  - No address clash: the FRAM (0x50) and ADS1115s (0x48/0x49) stay on I2C1. Behind the muxes there are EEPROMs at 0x50/0x58 (one per channel) and the AI-4 ADS1115 at 0x48.
- **Per slot:** PWR_EN = NOT EN_N AND NOT PRESENT_N (74LVC1G02). It drives TPS48100 INP and both TPS2553 EN pins.
  - OUT_EN_N = NOT(PWR_EN AND WD_OK) (74LVC1G00), which is exactly the pinout rule.
  - EN_N has a 10k pull-up, so expander reset means the slot is off.
  - TPS48100 FLT, both TPS2553 FAULT pins and the card CARD_FAULT_N share SLn_FAULT_N (10k pull-up).
  - Freed U62 inputs read SL1-8_PRESENT_N (10k pull-ups on the backplane).
- **Limits:**
  - VBAT_FIELD: 10 mΩ + ISCP 30.1k gives 7.9 A typ.
  - +5V_SLOT: TPS2553 with 45.3k gives 523-638 mA. The datasheet equations are IOSmin = 25230/R^1.016 and IOSmax = 22980/R^0.94.
  - +3V3_SLOT: 80.6k gives 291-370 mA.
  - +3V3_ID: +3V3_SAFE through 100R.
- **Shared signals:**
  - SPI: SPI3 is shared by all slots. CS comes from the '138 (G1 = PD13 with a 100k pull-down, so nothing is selected at reset).
  - RST_N: one shared line from PC9 (100k pull-down, so slots are held in reset).
  - ANA_OUT: slots 1-8 go through the TMUX1208 to SLOT_ANA, the old MUXB_OUT ADC pin. It uses the same MUX_A0-2 lines as U63.
  - ID_WP: one net to all slots plus the engine slot, 10k pull-up (protected). Closing solder jumper JP10 allows factory writes.
- **Removed from the mainboard (not moved to a card):**
  - Q70, Q71, D137, R627: ideal-diode swap.
  - D151: DI_BIAS_B TVS; DI-8 has its own.
  - J27: AUX7-10 terminal.
  - Q44, R272-R274: WD_OE_N inverter for the removed '541s.
  - R536: PB4 pull-down; PB4 is now a pulled-up INT input.
  - R36-R41: DI series resistors.
  - The Phase 2a list (U41, U42, U64, D133-D135, RN2, J17, J19, J26).
- **Firmware notes** (to add to FW_REQ_CARDS):
  - Set U62 P13-P17 and TCA9555 0x21 port 1 to outputs, driven low (they are unconnected spares).
  - Treat U29 AIN2 and U30 AIN1-3 as unused.

### 12.2 Reverse-battery front end: LM74700-Q1 + BSC070N10NS5 (replaces Q70/Q71 SQD40P10-40L)
- **Part:** TI **LM74700QDBVRQ1**, LCSC **C2941042**, AEC-Q100, SOT-23-6 [DS: TI SNOSD17, `fetch/ds_C2941042.txt`].
  - JLC stock 8,307 on 2026-11-23. Price $2.7311 at 1 pc, $2.4562 at 10 pcs.
  - DBV pinout: 1 VCAP, 2 GND, 3 EN, 4 CATHODE, 5 GATE, 6 ANODE. EN is tied to ANODE (always on, allowed by the datasheet).
  - Ratings: ANODE −65 to +65 V abs max (recommended −60 to +60 V, operating 4-60 V); CATHODE−ANODE −5 to +75 V; GATE−ANODE 15 V max.
  - Caps: VCAP to ANODE 100n (≥ 0.1 µF required); 100n on ANODE (≥ 22 nF); C199 100n on CATHODE (≥ 0.1 µF).
- **FET:** BSC070N10NS5 (C534364, 100 V, 7.0 mΩ max). Source on the J23 side (VBAT_ESTOP_IN), drain on VBAT_ESTOP_PRE.
- **Reverse battery:**
  - With J23 negative, the controller holds GATE at ANODE, and the FET body diode (source → drain) is reverse-biased. VBAT_ESTOP_PRE and everything after it see no negative voltage: R251 (the VESTOP_D E-stop sense divider), R400, the rail cut, VBAT_ESTOP, R411 and the engine slot.
  - Reverse current (PRE above IN, for example when the E-stop opens with the caps charged) turns the gate off fast. The datasheet threshold is about −11 mV [DS].
  - D126 SMDJ40CA (bidirectional, 40 V standoff) moved ahead of the controller onto VBAT_ESTOP_IN. It does not conduct at −24 V and it clamps load dump for the controller and the FET.
- **Thermal (104 °F ambient, RthJA 50 K/W on 6 cm² of 2 oz copper per the BSC070N10NS5 datasheet; `modular/tools/railcut_thermal.py`):** one FET is enough.

| Current | Loss | Junction | Rise |
|---|---|---|---|
| 7.6 A | 0.49 W | 148 °F | 44 °F |
| 10 A | 0.94 W | 189 °F | 85 °F |

  - TjMax is 302 °F. For comparison, two in parallel would run 122 °F with an even split or 130 °F at 60/40 at 10 A. That is not needed.
  - Q70/Q71 were 283 °F (even split) and runaway (60/40) at 10 A.
- **SQD40P10-40L elsewhere:** only Q70/Q71 used it (main BOM line, CONSIGN, Mouser $3.71 each), so it is gone from the BOM. VBAT_P already uses an LM74800-Q1 (U1, C3215600) with back-to-back BSC070N10NS5 (Q1/Q2), so nothing changes there.

### 12.3 VBAT_ESTOP net split (as drawn)

| Net | Nodes |
|---|---|
| VBAT_ESTOP_IN | J23.1/2, D126, LM74700 ANODE/EN, FET source, 100n |
| VBAT_ESTOP_PRE | FET drain, LM74700 CATHODE, C199, R251 (E-stop status, pre-cut), R400 (TRIP_QB), rail-cut VS/CS+, 2 mΩ shunt, UVLO divider |
| VBAT_ESTOP | rail-cut FET sources, SRC, BST cap, C203, R411 (ADC readback, post-cut), ENGINE slot a/b/c 1-4 |

### 12.4 Full-system netlist audit (`modular/tools/system_audit.py` → `modular/system_audit.json`, `modular/system_net_changes.csv`)
- **Joined netlists** (kicad-cli export), through their mating connectors:
  - mainboard;
  - ENGINE in J48;
  - DI-8 in LV1, AI-4 in LV2, HSO-5 #1 (AUX1-5) in LV3, HSO-5 #2 (AUX6-10) in LV4, BRK-4 in LV5;
  - HV meter through the J31↔J32 1:1 harness.
- **Baseline mapping:** every baseline (ref, pin) from the locked tag (mainboard + meter, joined through J31/J32 too) is mapped to its new home:
  - refs that stay keep their name;
  - card refs go through refmap.json;
  - HSO-B refs pair to HSO-5 #2 by structural match (all 60 paired);
  - removed refs drop out.
- **Result:**
  - 1,062 baseline nets have identical connectivity.
  - 112 intentional splits/merges are each tied to a recorded reason: mainboard edit, card net_changes / net_accounting, universal-slot signal, the glow supply decision, or the meter EEPROM.
  - **0 unexplained.**
  - **0 orphaned or broken cross-connector contacts.** Of the 592 mating contacts: 423 are wired on both sides, 156 are open/NC on both sides (RSVD, unused), 7 are slot signals the card does not use (card NC), and 6 are ID straps left open (card pull-up = 1).

### 12.5 Part counts (fitted)

| Board | Parts |
|---|---|
| Mainboard (bom/genctl_main_bom.csv, 230 lines) | 908 (baseline 1,127) + 11 DNP |
| ENGINE / DI-8 / AI-4 / HSO-5 / BRK-4 | 156 / 76 / 104 / 76 (×2) / 64 |
| HV meter | 221 |
| **Example build, combined (docs/modular/combined_bom.csv, 226 lines)** | **1,681** |

### 12.6 True net cost delta, from the regenerated BOMs (`modular/tools/true_cost.py` → `modular/true_cost_delta.csv`)

| | qty 1 | qty 10 (per unit) |
|---|---|---|
| Baseline mainboard + meter BOM (tag) | −$330.25 | −$279.37 |
| Reworked mainboard BOM (includes backplane, slot power, ideal diode, rail cut) | +$231.40 | +$194.87 |
| HV meter BOM with ID EEPROM | +$65.33 | +$54.60 |
| Card BOMs (ENGINE, DI-8, AI-4, 2× HSO-5, BRK-4) | +$131.10 | +$110.51 |
| Card PCBs + PCBA fees + extended-part loading (5 designs) [E/DS] | +$200.80 | +$22.08 |
| Card bays, guides, faceplates [E] | +$29.00 | +$17.50 |
| **Total** | **+$327.38** | **+$120.19** |

The parts-only delta is +$97.58 at qty 1 and +$80.61 at qty 10. The rest is boards and mechanics for the five card designs.

### 12.7 Still open
- The PCB layout is not started. The DIN male row lettering needs checking on a sample (§11.4).
- The firmware items in §12.1 need to go into FW_REQ_CARDS.
- ~~The SPI3 slot bus runs to 8 slots with no series termination.~~ Done in Pass 1: 33R source resistors on SCK, MOSI and SLOT_RST_N (§13).

## 13. Pass 1 review fixes (Nov 23, 2026, HST; review `/workspace/review/modular_pass1.md`)
Checks after the fixes:
- ERC is 0 errors / 0 warnings on all 7 projects: genctl, genctl_meter, engine, di8, ai4, hso5, brk4.
- System audit: 1,057 nets the same as the baseline, 127 intentional changes, **0 unexplained, 0 orphans**.
- Mating contacts: 413 wired on both sides, 166 NC on both sides (+10 for the reserved a8/b8), 7 slot signals the card does not use, 6 open ID straps.
- Drawn-vs-intended: 2,797 mainboard pins, 0 errors.
- Datasheet and stock evidence: `docs/split_evidence/modular_pass1/`.

### 13.1 Slot isolation and slot power (B1, M3, N3, N6)
- **+5V_SLOT removed.** The 8 +5V TPS2553s, their ILIM resistors and their caps are gone. Contacts a8/b8 are reserved (NC on both sides).
- **+3V3_SLOT** comes from the TPS2553 on main **+3V3**, not +3V3_SAFE, with ILIM 210k: 110/130/150 mA.
  - The TPS2553 FAULT and EN abs max is −0.3 to 7 V to GND (SLVS841G), so a pulled-up FAULT with IN at 0 V is fine.
- **Every LV card buffers the slot bus through Ioff parts**, so an unpowered card is never back-powered and never loads the bus:
  - **Nexperia 74LVC125APW,118** (C6059): CS, SCK, MOSI and RST, OE tied to GND. IOFF is ±10 µA (−40…+85 °C) and ±20 µA (−40…+125 °C) at VCC 0 V, with VI/VO up to 5.5 V. TI's SN74LVC125A (SCAS290T) has no Ioff spec, so it is not used.
  - **SN74LVC1G125** (C23654): MISO, with OE# = the buffered CS and a 100k pull-down on the card side.
  - **SN74LVC1G07** (C7829): INT_N, open drain. The MCP23S17 INTA is push-pull (IOCON.ODR = 0).
- **OUT_EN_N pull-ups** (AI-4 R45, HSO-5 R36, BRK-4 R29) now go to +3V3_ID, which is always on.
- **CARD_FAULT_N pull-ups removed from the cards.** The pull-up is on the backplane (10k to +3V3_SAFE), read on the new 0x22 expander. Abs max at VS = 0:
  - TPS1HTC30-Q1 FAULT: −1 to 7 V to IC GND, with no VS reference.
  - TPS26621 FLT: 62 V to RTN, leakage ±100 nA.
  - The DI-8 MCP GPB2 no longer sits on CARD_FAULT_N. An unpowered MCP would have been back-powered through it.
- **+3V3_ID feed:** 150 Ω 0805 (C17471, 125 mW). With a short at the card it takes 22 mA, which is 72.6 mW in the resistor.
- **U105 '138 / U109 slot ANA mux on +3V3_SAFE:** fine. The card inputs they drive are Ioff buffers. The ANA mux only connects a selected channel, and firmware never selects an unpowered slot (FW_REQ C7.3).
- **N12:** 33R source resistors at the MCU on SLOT_SPI_SCK, SLOT_SPI_MOSI and SLOT_RST_N (R708-R710). The MCU side nets are SLOT_*_M.

### 13.2 Boot and reset safety (B2)
- **Cards:** 47k pull-downs on HSO-5 OUT1-5_REQ, DIAG_EN and MUX_A0-2; on BRK-4 OUT1-4_REQ, DIAG_EN and MUX_A0-2; and on AI-4 SH_EN1-4.
- **AI-4 CS_DIS polarity, from the netlist:** CS_DIS high → Q3 on → Q2 BSS84 on → IN_REF pulled to VBAT_AI → current source **off**. So the safe level is high, and CS_DIS1-4 get 47k pull-ups to +3V3_SLOT. That is the same state the baseline TCA9555 POR gave.
- **DI-8:** GPB2/GPB3 are unused: NC, with GPPU on.
  - Tying them to GND was rejected. A bidirectional pin on GND fails ERC (pin_to_pin), and it is a short if firmware ever drives it high.
  - Every unused MCP23S17 pin on every card is NC with GPPU = 1 (N4).
- **Mainboard:**
  - `GLOBAL_OUT_ALLOW = WD_OK AND NRST_S AND SLOT_RST_N`. It uses the spare U92 gate 4 (pins 12, 13 → 11) on SH_ALLOW, instead of a new 1G11.
  - `SLn_ARM_N` is on U107 (0x21) P10-P17, with 10k pull-ups to +3V3_SAFE.
  - `SLn_OUT_EN_N = NAND(PWR_EN, GLOBAL_OUT_ALLOW, NOT ARM_N)`, from an SN74LVC1G04 (C7827) plus an SN74LVC1G10 (C403721) per slot. These replace the 74LVC1G00.
  - Truth table and enable order: FW_REQ C2.3.

### 13.3 Decoupling (M1)
- 100 nF / 100 V X7R 0805 (CL21B104KCFNNNE, C28233) at every TPS1HTC30 VS: 5 on HSO-5, 4 on BRK-4, and 1 on the engine card glow driver U8. The TPS1HTC30-Q1 needs C_IC ≥ 100 nF.
- 2.2 µF / 100 V X7R 1206 (CL31B225KCHSNNE, C170101) bulk on VBAT_FIELD (HSO-5, BRK-4) and on VBAT_ESTOP (engine card).
- **Inrush:** at most about 2.7 µF per card × 32 V = 86 µC. Even at 10 A that charges in under 9 µs, far below the ~70 µs slot short-circuit blanking, so it cannot trip.
- Mainboard C205-C219 removed: they were the VS caps of drivers that now sit on the cards.

### 13.4 Current limits and the slot-bank limiter (M2, N13)
| Stage | Parts | Trip / limit (min / typ / max) | Latch |
|---|---|---|---|
| Card channel (HSO-5, BRK-4) | TPS1HTC30 ILIM 33.2k (KCL 80/100/120 A·kΩ) | 2.41 / 3.01 / 3.61 A | per channel |
| Slot switch (×8) | TPS48100 + 2× BSC070N10NS5 + 5 mΩ (C2903482) + ISCP 24.3k (C23348) | 10.7 / 13.6 / 16.6 A (V_SCP 53.4 / 67.6 / 83.0 mV) | 4.7 nF + 100k across TMR: latch-off, tSC ≈ 70 µs |
| Slot bank (new, VBAT_P → VBAT_SLOTS) | TPS48100 + 2× BSC070N10NS5 + 5 mΩ + ISCP 19.6k (C22898) | 9.2 / 11.6 / 14.4 A (V_SCP 45.8 / 58.2 / 71.9 mV) | 10 nF + 100k: latch-off, tSC ≈ 148 µs |
| Rail cut (VBAT_ESTOP) | unchanged, plus 100k across C_TMR | 15.8 / 20 / 24.8 A | latch-off; re-arm with RC_ALLOW |

- The equation is TPS48100 SLUSEW1C Eq 5: R_ISCP = (I_SC × R_SNS − 19 mV) / 2 µA. The tolerance rows come from the datasheet (10.5k → 31.6/40/49.5 mV; 28k → 58.8/75/91.8 mV), interpolated.
- **Why 9.2 A minimum for the bank, not 7 A:** the budget case is 5.0 A of slot load plus one shorted HSO channel at its 3.61 A maximum limit, which is 8.61 A. That stays under 9.2 A, so a single channel short never takes down every slot.
- **Selectivity:** a hard short in one slot trips that slot (~70 µs) before the bank timer (~148 µs) runs out. A slot overload between 9.2 A and 10.7 A trips the bank and takes every LV slot down (caveat).
- **F1:** worst case 14.4 A bank + 4.95 A base load = 19.4 A, which is under 200 % of F1 (10 A at room, 8 A at 149 °F). The INA237 (U86) firmware tiers cover the fuse time domain.
- **Bank control:**
  - BANK_EN = 0x22 P11, with a 10k pull-down: off at reset.
  - BANK_FAULT_N = 0x22 P12, with a 10k pull-up.
- **Bank FET thermal** (`modular/tools/railcut_thermal.py`; RthJA 50 K/W, RDS(on) 7 mΩ max):

| Ambient | Bank current | Hot FET (60/40) loss | Hot FET Tj | Rise | Shunt loss (3 W part) |
|---|---|---|---|---|---|
| 104 °F | 5.0 A | 0.07 W | 110 °F | 6 °F | 0.12 W |
| 104 °F | 8.61 A | 0.21 W | 123 °F | 19 °F | 0.37 W |
| 104 °F | 9.2 A (min trip) | 0.25 W | 126 °F | 22 °F | 0.42 W |
| 149 °F | 8.61 A | 0.24 W | 171 °F | 22 °F | 0.37 W |
| 149 °F | 9.2 A | 0.28 W | 174 °F | 25 °F | 0.42 W |

  TjMax is 302 °F. The slot switches carry at most one card's load, which is less than this.
- **N14 DIN contacts:** the WingTAT C96 contact rating is 2 A (LCSC parameter and drawing 9001D11001 R7; contact resistance 20 mΩ max at DC 100 mA; −67…+257 °F; 1000 VAC withstand).
  - A slot can never pass more than the bank's 14.4 A maximum. Across its 9 VBAT_FIELD contacts that is ≤ 1.6 A each.
  - **WingTAT publishes no temperature derating curve** (caveat).
- **N17 sense clamp:** V_SNSFH tracks DIAG_EN (3.0/3.3/3.82 V at DIAG_EN 3.3 V). Changing R_SNS alone does not bound the clamp current.
  - R_SNS 1.1k → **910 Ω** (C23264) keeps the 3.61 A I_CL at 3.61 A × 1300⁻¹ × 910 = 2.53 V, below the 3.0 V V_SNSFH minimum.
  - The series resistor 1k → **4.7k** (C23162) keeps the BAT54C clamp current ≤ 0.13 mA. That keeps the TMUX1208 S pin ≤ VDD + 0.25 V (BAT54 VF 240 mV max at 0.1 mA) inside its VDD + 0.5 V abs max, with about 0.33 V margin at −40 °F.
  - Cost: about 57 µs settling, so firmware waits 0.5 ms after a mux change (FW_REQ C7.3).
- **BRK-4 caveat:** the coil limit is now 2.41 A minimum. A coil above 2.4 A needs an interposing relay.

### 13.5 Faults, ID bus, write protect, rail cut (M4-M8, N8-N11)
- **M5 / N10, the third TCA9555 at 0x22** on I2C2 (A1 = +3V3_SAFE):
  - P00-P07 = SL1-8_CARD_FAULT_N (10k pull-ups);
  - P10 = ENG_PRESENT_N (engine slot c31; the card grounds it; 10k pull-up);
  - P11 = BANK_EN; P12 = BANK_FAULT_N; P13-P17 spare.
  - U106 (0x20) P1 = SLn_PWR_FAULT_N, shared by TPS48100 FLT and TPS2553 FAULT. U107 (0x21) P1 = SLn_ARM_N.
  - All three INTs go to SLOT_EXP_INT_N.
- **M4:** PB5 drives ID_MUX_RST_N. Its 100k pull-down R544 is removed; the 10k pull-up R707 stays. Recovery procedure: FW_REQ C7.4.
- **M6:** D126 is now an SMDJ36CA (Littelfuse, C224075, 4,813 in stock). Datasheet values:
  - VR 36 V; VBR 40.0-44.2 V at 1 mA.
  - VC 58.1 V at Ipp 51.6 A (10/1000 µs, 77 °F); αT 0.1 %/°C, so VC is about 60.4 V at 149 °F.
  - That stays under the LM74700 ANODE 65 V abs max: 6.9 V margin at 77 °F, 4.6 V hot. On the post-ideal-diode side it is also under the TPS1HTC30 VS 64 V continuous rating (81 V for < 100 µs).
  - For comparison, the SMDJ40CA clamps at 64.5 V at 46.5 A, so it had no margin.
  - **S7-N13, stated honestly:** this is a clamp at the 10/1000 µs rating only. It does not make the board load-dump proof (`docs/INSTALL_SAFETY.md`, load dump section). Standoff is now 36 V, at the top of the 36 V / 60 s jump-start window, so leakage rises there. That is acceptable for a TVS that is not continuously biased above 32 V.
- **M7:** PB6 (ID_WP_UNLOCK, 100k pull-down R545) drives an AO3400A (C20917).
  - AO3400A: VGS(th) 0.65 / 1.05 / 1.45 V; RDS(on) ≤ 48 mΩ at 2.5 V.
  - IRLML0100 was rejected: its 2.5 V maximum VGS(th) is marginal with a 3.3 V gate.
  - The FET pulls ID_WP low. The 10k ID_WP pull-up is kept; it is now R734 after renumbering. Solder jumper JP10 is removed.
  - **N8:** J31/J32 have no spare pin. J32.12 is now SCL and J32.16 is SDA, and the 4 GNDs are kept. So the HV meter WP stays on its TP3 bench pad (FW_REQ C4.3, INSTALL_SAFETY).
- **M8 / N9:** U102 is now an SN74LVC1G11 (C22046): RC_EN = WD_OK AND ESTOP_OK AND RC_ALLOW. RC_ALLOW is PB7, keeping the 100k pull-down R546. The rail cut latches off (100k across C_TMR). The pre-crank proof test and the OUT_FAULT_N masking rule are in FW_REQ C7.5.
- **N7:** C400 (LM74700 VCAP) is now 0.47 µF / 50 V X7R 0805 (C13967).
- **N11:** MUX_A0-2 are card-local MCP outputs. The mainboard SLOT_ANA mux selects the slot (FW_REQ C7.3).
- **N5:** SLOT_CS_EN ordering is in FW_REQ C7.1.
- **N1:** the AI-4 ADS1115 value now reads "@0x48".
- **N2 (dead logic removed):** U91 gates 3-4 and U92 gates 1-2 have their inputs on GND and their outputs NC. RN1 R3/R4 and U31 P10-P13 are NC. The AI_SH_EN3-6 pull-downs R160/R171/R182/R193 are removed.
- **Ref renumbering:** the mainboard uses one shared counter for new parts, so new refs from R700 / C400 / U100 / Q100 onward moved. Examples:
  - rail cut U101, U102 1G11;
  - ID muxes U103/U104, '138 U105, expanders U106 (0x20), U107 (0x21), U108 (0x22), slot ANA mux U109;
  - bank limiter U110, slot 1 U111-U115 (TPS48100, TPS2553, 1G02, 1G04, 1G10);
  - ID_WP FET Q103, bank FETs Q104/Q105;
  - 33R R708-R710, ID_WP pull-up R734.

  The full list is in the regenerated BOM.

### 13.6 Thin stock (N16)
| Part | Stock (Nov 23) | Alternate |
|---|---|---|
| AT24CS32-STUM-T (C147891, SOT-23-5, on every card) | 243 | AT24CS32-SSHM-T SOIC-8 (C615972, 92) or AT24CS32-MAHM-T UDFN (C2061575, 228). Neither is pin-compatible: a footprint change. Buy a reel for the build early. |
| TPS48100QDGXRQ1 (C43131316) | 728 (11 per controller now) | No stocked pin-compatible alternate found. Order ahead. |
| SN74LVC1G10DBVR (C403721) | 3,580 LCSC / 4,044 JLC (8 per controller) | No alternate verified this pass. Check the pinout of any other-brand 1G10 before substituting. |
| WingTAT DIN C96 female (C5173363) | 983 (9 per controller) | No alternate verified this pass (footprint is WingTAT-specific). |

### 13.7 Part counts and cost after Pass 1
| Board | Parts (fitted) |
|---|---|
| Mainboard (236 BOM lines) | 926 (was 908) + 11 DNP |
| ENGINE / DI-8 / AI-4 / HSO-5 / BRK-4 | 158 / 82 / 119 / 97 (×2) / 83 (was 156 / 76 / 104 / 76 / 64) |
| HV meter | 221 |
| **Example build, combined (236 lines)** | **1,783** (was 1,681) |

| True net cost delta | qty 1 | qty 10 (per unit) |
|---|---|---|
| Baseline mainboard + meter (tag) | −$330.25 | −$279.37 |
| Reworked mainboard BOM | +$232.97 | +$195.77 |
| HV meter BOM | +$65.33 | +$54.60 |
| Card BOMs | +$133.87 | +$112.88 |
| Card PCBs + PCBA fees + extended-part loading [E/DS] | +$200.80 | +$22.08 |
| Bays, guides, faceplates [E] | +$29.00 | +$17.50 |
| **Total** | **+$331.72** (was +$327.38) | **+$123.46** (was +$120.19) |

Prices are live JLC parts API prices taken Nov 23, 2026 ~3:40 PM HST (`bom/lcsc_prices.csv`).

### 13.8 Sheet sizes
- AI-4, HSO-5 and BRK-4 grew past A3 and are now one A2 page each, like the engine card. DI-8 stays A3.
- schdraw now masks label text bodies when packing, so clusters can no longer slide over a label. J31 nets on mtr_if are drawn as centred global labels.
