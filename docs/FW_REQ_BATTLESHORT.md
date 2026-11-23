# Battle short mode: keep the genset running, protections overridden (firmware spec)

Status: **requirement/spec only, not implemented.** Branch m7-split, Batch 33, Nov 22, 2026 (HST); Ethan's decisions D1–D6 recorded in Batch 33a (Nov 22, 2026, ≈ 2:55 PM HST). Feature and rulings from Ethan, relayed by Enginerd at 1:28 PM HST. No schematic, BOM or firmware file changed. The held overvoltage engine-shutdown change and the held master reset are not touched.

Battle short works like the switch on military generators. When it is on, the controller keeps the engine running and the breaker closed, and it ignores the protection trips that would normally stop the engine or open the breaker. It is meant for emergencies where losing power costs more than the engine does.

## 1. Ethan's rulings
- **Still active in battle short:** E-stop and engine overspeed. Nothing else.
- **Overridden:** low oil pressure, high coolant/oil temperature, over/undervoltage, overcurrent, over/underfrequency, every metering fault including the whole meter board missing (FW-MTR-3), the power-dip latches (FW-MTR-9), and the breaker trips.
- **Software only.** No new hardware. Enabled through a hard-to-trigger local action (Ethan suggested a secret button combination; method chosen in §4).
- Many settings are editable in the controller's configuration suite (Ethan's earlier remark). Battle short uses that: its availability and options are configuration settings (§4, §12).
- **Follow-up decisions D1–D6** (Nov 22, 2026, ≈ 2:55 PM HST): Ethan accepted all the Batch 33 suggestions. They are recorded in §14 and written into §5–§8 and §12. D7 (key mapping) is pending until the front-panel legend exists.

## 2. Hardware audit: what can stop the engine or open a breaker without firmware consent
The firmware cannot override hardware. This table lists every path on the m7-split schematic (netlist at Batch 32, 2c7a495) that can stop the engine or open a breaker by itself, and whether battle short can bypass it.

| # | Hardware path | What it does | Battle short can bypass it? |
|---|---|---|---|
| H1 | **TPS3431 watchdog (U37) → U84 74LVC1G74 latch → WD_OK** | A firmware hang of ≈ 170–230 ms with no PA12 kicks latches WD_OK low. WD_OK gates FUEL_EN (U38), CRANK_EN (U39), GLOW_EN (U40) and MCU_TRIP (U67), and tri-states the GCB/MCB/AUX drivers (U41/U42 via Q44, WD_OE_N). **Fuel drops, so the engine stops.** The breakers get no pulse and keep their last mechanical state. | **No, by design (Ethan's requirement).** U84 is set only by its CP input from the power-on RC (R554/C298/U85) and cleared by WDO_N. No MCU pin reaches it, so firmware cannot re-arm it. It re-arms only after a power cycle. |
| H2 | **U84 power-cycle-only re-arm** | After a trip, WD_OK stays low until the controller loses power and restarts (WD_OK low for 0.70–1.06 s typical, 0.40–1.35 s worst case after power-on). | **No.** Same as H1. Restart needs a power cycle, which also stops the engine (fuel relay de-energises). |
| H3 | **E-stop chain: VBAT_ESTOP cut + TLC555 one-shot (U66) → K4 ESTOP_TRIP (breaker shunt trip)** | Pressing E-stop removes VBAT_ESTOP, which powers the FUEL/CRANK drivers (TPS48100 U43 FUEL, U45 CRANK), and fires a 0.30–1.00 s K4 pulse through U68 that trips the breaker. No firmware in the path. | **No, and it must not be.** E-stop stays active in battle short (Ethan's ruling). Firmware also keeps its ESTOP state. |
| H4 | **CRANK/TRIP AND gating (U39, U67 74LVC1G08 with WD_OK)** | Part of H1. U67 means the watchdog can only **block** MCU_TRIP (an MCU-commanded breaker trip), never fire it. U39 removes cranking on a watchdog trip. | **No** (part of H1). U67 cannot open a breaker by itself. |
| H5 | **Keep-alive / readback "3 mismatches → drop KA"** | **Not on m7-split.** This came from the two-module proposals (review/fw/link_failsafe.md, simplify_module2_link.md) and was not built. On this board the output readbacks (xx_RB_N → U73/@0x23) are inputs only. Any action on a readback mismatch is firmware. | n/a in hardware. If a future two-module version adds a hardware keep-alive, it is a watchdog-class stop and must **not** be bypassable, like H1. A firmware readback-mismatch rule is a protection and is overridden (§5), but firmware still rewrites the outputs. |
| H6 | **D+ excitation 30 s cap** | **Firmware only** (FW_REQ_BATCH27 item 2). DPLUS_EXC_EN is PC8 directly, not watchdog-gated. It only removes alternator excitation (charge-fail alarm). It does **not** stop the engine. | **Keep it active.** It protects U36 (LM317M) from overheating and cannot stop the engine. Raise the charge-fail alarm as usual. |
| H7 | **4–20 mA shunt gating (Batch 31: AI_SH_Gx = AI_SH_ENx AND WD_OK AND NRST)** | Turns the six AI shunts off in reset, after a watchdog trip, and at power-on. It never touches fuel or the breakers. | Not needed. It cannot stop the engine. With the shunts off, the 4–20 mA sensors read INVALID, and their protections are overridden in battle short anyway. |
| H8 | **Controller supply limits** | The MCU runs on +3V3_SAFE from +3V3 or the +3V3_BK buck (EN on VBAT_P, 4.2–65 V). VBAT_P sits behind the LM74800 with its OV cut-off at 36.4–40.1 V. The TPS48100 FUEL/CRANK drivers have EN/UVLO ≈ 5.7 V on VBAT_ESTOP. Battery OV above ≈ 36 V, or a battery collapse below ≈ 4–6 V, drops FUEL_EN. | **No.** Without power the controller cannot hold the fuel relay. Install note: a healthy battery is mandatory (INSTALL_SAFETY load-dump note). |
| H9 | **FUEL/CRANK driver short-circuit protection (TPS48100, RISCP 40.2k ≈ 4.97 A, TMR 4.7 nF)** and TPS1HTC30 current limit / thermal shutdown on GLOW, GCB/MCB pulses, AUX | A short on the fuel relay circuit cuts FUEL. The breaker pulse drivers limit at ≈ 3.2–4.9 A. | **No.** These protect the board from a wiring fault. A shorted fuel circuit cannot run the engine anyway. |
| H10 | **External devices** (the genset's own thermal-magnetic breaker or MCCB trip unit, engine-mounted mechanical shutdowns, the breaker's undervoltage release) | Outside the controller. | **No.** Battle short overrides only the controller's own trips. State this in the manual (§11). |

**Audit result.** Battle short cannot override:
- the watchdog latch (H1, H2, H4);
- the E-stop chain (H3);
- loss of controller supply (H8);
- the driver short-circuit limits (H9);
- external devices (H10).

All of these either are required by Ethan's rulings (E-stop, watchdog) or are a physical limit (no supply, short circuit). **No schematic change is needed and no blocker was found.**

## 3. Firmware hang in battle short (limitation, stated plainly)
- **A firmware hang still stops the engine.** If the main loop stops checking in for ≈ 170–230 ms, the TPS3431 times out, U84 latches WD_OK low and FUEL_EN drops. Battle short cannot prevent this, and Ethan ruled that it must not. The engine stays stopped until someone power-cycles the controller and restarts the set.
- Reason it stays this way: a hung controller cannot run overspeed protection, and overspeed must stay active in battle short. A runaway diesel with no overspeed protection is the one failure battle short must not allow.
- **MCU resets that are not a hang** (an IWDG reset that recovers before the TPS3431 times out, a brown-out reset on +3V3_SAFE):
  - During reset all MCU outputs fall LOW, so the fuel relay drops for the reset plus early-boot time.
  - The engine may stall or ride through, depending on the fuel system. Firmware should keep that gap short:
    1. Set the IWDG timeout below the TPS3431 minimum (≈ 100 ms), so a single glitch is caught by the IWDG first.
    2. **Warm-restart rule (BS-11):** if the reset cause is not a power-on reset, battle short is active in FRAM, and MPU speed is above crank-disconnect, re-assert FUEL_EN **before** the slow boot items (LSE start, INA238 init, self-test). Target ≤ 50 ms from reset release. Skip PREHEAT/CRANK and go straight to RUN with battle short still active.
  - A power cycle or a watchdog latch always means a cold start (§6).
- **The CM5 must not reset the MCU while battle short is active and the engine is running.** CM5 software refuses CM5_NRST/BOOT0 (reflash) requests and shows "Battle short active: stop the engine before updating firmware". This extends FW_REQ_BATCH30 FW-AI-3 item 3.

## 4. How battle short is enabled (two steps, local)
**Step 1: pre-authorise in the configuration suite** (done once, at commissioning):
- Setting `BS_AVAILABLE` = **off** by default. Turning it on needs the configuration suite's admin credential and a typed confirmation of the warning text (§11).
- It is stored in MCU FRAM with CRC and A/B copies, like the other safety settings, and is logged with who changed it and when.
- While `BS_AVAILABLE` is off, the local action in step 2 does nothing except log `BS_ATTEMPT_NOT_AUTHORISED`.

**Step 2: local action at the front panel** (each time it is needed). It is run by the MCU from the 12 front-panel keys (U73), so it also works when the CM5 or the display is dead.
1. **Arm:** press and hold the **top-left and bottom-right keys together for 5 s**. These are diagonally opposite corners about 270 mm apart, so it needs two hands and cannot happen by leaning on the panel. While held, those two key LEDs flash amber. After 5 s, every key LED flashes red, the buzzer chirps twice, and the display (if alive) shows "BATTLE SHORT: CONFIRM? Protections will be OFF".
2. **Confirm within 10 s:** either tap "ENABLE BATTLE SHORT" on the display (plus the PIN, if `BS_PIN_REQUIRED` is on), **or**, with no display, press and hold the **centre-top key** for 3 s. If nothing happens within 10 s, it cancels and logs `BS_ARM_TIMEOUT`.
3. The combination is not secret, so security does not rely on it. It is documented in the operator manual and printed on the inside of the enclosure door. What makes it safe is step 1 (pre-authorisation) plus the two-hand hold, the confirm and the loud warning.
- The final mapping of these keys to BTN1–BTN12 follows the front-panel legend (TBD with the panel artwork; **decision D7, pending**). The STOP key is never part of the combination.

**Remote enable:**
- Not allowed unless the setting `BS_REMOTE_ENABLE` is on. It is a second setting, off by default, admin-only, and it also needs `BS_AVAILABLE` on.
- With it on, an authenticated remote command (CM5 network or Modbus/CAN with the remote-control permission) can enable battle short. The local panel still shows the full warning and sounds the buzzer.
- Without it, every remote enable request is refused and logged (`BS_REMOTE_REFUSED`).

**Preconditions:** E-stop not active, and no ESTOP state latched. Battle short can be enabled with the engine stopped (it then applies to the next start, including auto-starts) or running.

## 5. What battle short changes (overrides)
| Protection / latch | Normal action | In battle short |
|---|---|---|
| **E-stop** (hardware + ESTOP state) | Stop, K4 trip | **Unchanged, active** |
| **Overspeed** (MPU speed; backup: GEN frequency × pole pairs if the ADE is valid) | Shutdown | **Unchanged, active.** If the MPU signal is lost while running, use the GEN-frequency backup. If both are lost, keep running and alarm `BS_OVERSPEED_UNPROTECTED` (**Ethan's decision D5**). |
| Low oil pressure, high coolant/oil temperature, other engine DIs/AIs | Shutdown | Alarm and log only, keep running |
| Over/undervoltage, over/underfrequency (GEN) | Shutdown and/or GCB open | Alarm and log only, keep running, GCB stays closed |
| Overcurrent / short-circuit (controller-measured) | GCB open and/or shutdown | Alarm and log only. **Fire and cable risk, see §9** |
| Breaker trips (any controller-commanded GCB/MCB open for a protection) | Open pulse | Not sent. Alarm and log. **One exception (Ethan's decision D6): the reverse-power trip on a paralleled set stays active (§8)** |
| Metering faults: `METERING_SILENT` GEN/BUS, `METERING_MISSING` (whole meter board) | Latched shutdown / start block (FW-MTR-3) | Alarm and log only, keep running, starts allowed. Voltage/frequency/current protections are blind and already overridden |
| Power-dip latches (FW-MTR-9: 2 s running cap, 5 dips in 10 min) | Latched shutdown | Alarm and log only. The recheck still runs, so metering comes back automatically |
| Start inhibits: `RELAY_KIT_*`, `INA_VBUS_FAULT`, DI_BIAS faults, panel faults, latched FAULT from before | Block start | Do not block the start. Log the start as "started over inhibit X" |
| Fail-to-start (overcrank) | FAULT after N attempts | **Retry indefinitely with rest breaks (Ethan's decision D4)**: crank ≤ `BS_CRANK_MAX_S`, rest `BS_CRANK_REST_S` between attempts, long rest `BS_CRANK_LONG_REST_S` after every 3 attempts (§12); alarm `BS_OVERCRANK_RETRYING`. Starter overheating risk is accepted |
| Firmware readback mismatch on outputs | FAULT | Rewrite the output, alarm, keep running |
| **Kept active** (they cannot stop the engine): D+ 30 s excitation cap, glow 60 s cap and cooldown, battery load-shed of AUX/EXP_12V/GLOW (FUEL and CRANK are never shed), PSU_MAIN_OK load-shed and back-off | as normal | as normal |
| **Breaker close permissives** (sync-check, dead-bus check) | Block close | **Not overridden.** See §8 |

Operator commands are not protections. **The local STOP key (long press) always stops the engine in battle short.** A remote stop works only with the remote-control permission. An ATS "mains returned" stop works as normal, with cooldown.

## 6. Disabling, persistence and reboot
- **Disable locally:** hold the same two corner keys for 3 s (no confirm step; turning it off is the safe direction), or tap "Disable battle short" on the display.
- **Disable remotely:** allowed whenever the remote-control permission exists, even if `BS_REMOTE_ENABLE` is off.
- **When it turns off:** protections come back after a grace period, `BS_DISABLE_GRACE_S` (default 5 s, 2–30 s, §12). Any fault that is still present then acts normally. For example, low oil pressure still present → shutdown 5 s after disable. The display warns about this before confirming ("3 faults are active and will stop the engine").
- **E-stop:** pressing E-stop stops the engine (hardware) and **clears battle short** (**Ethan's decision D2**). After the E-stop is reset, battle short must be enabled again with step 2.
- **Survives an MCU reset:** **yes.** The battle-short state is stored in FRAM (CRC, A/B), so an IWDG or brown-out reset does not silently bring protections back mid-run (BS-11 warm restart).
- **Survives a power cycle:** **no, by default.** A power-on reset clears it to OFF and logs `BS_CLEARED_BY_POWER_CYCLE`.
  - A power cycle is also the only way out of a watchdog latch, so the restart after a hang comes back with full protection, and a technician servicing the set never finds protections off without knowing.
  - Option `BS_PERSIST_POWER_CYCLE` (admin, off by default) keeps it on across power cycles for unattended remote sites. **Ethan's decision D1:** clears on a power cycle by default; the admin setting can make it persist.
- **Optional auto-expiry:** `BS_TIMEOUT_H` (0 = never, default 0). If set, battle short turns off after that many hours, with a 10 min warning.

## 7. Warning, alarm output and remote status (cannot be missed)
- **Display/HMI:**
  - A red banner on every screen, which cannot be dismissed: "BATTLE SHORT ACTIVE – ENGINE AND BREAKER PROTECTIONS OVERRIDDEN".
  - The banner shows how long battle short has been on and the number of faults overridden in this session, and opens the list of faults overridden right now.
- **Front panel without the display:** one dedicated key LED (the centre-top key) flashes red, 1 s on / 1 s off, all the time.
- **Buzzer:** three chirps when it is enabled, then one chirp every `BS_BUZZER_REPEAT_S` (default 30 s). Silencing the alarm mutes it for `BS_SILENCE_MIN` (default 15 min), then it resumes. A **new** overridden fault always sounds the full alarm pattern until it is acknowledged.
- **Alarm output:** configuration setting `BS_ALARM_AUX` assigns one AUX output (AUX1–10) as "battle short active" (steady on), for a beacon or a common-alarm relay. Default: none assigned; the installer must choose (§11).
- **Remote status:** a status bit and the session counters in the Modbus/CAN map and the CM5 status frame. An event message goes out on enable, disable and every newly overridden fault, through the CM5 network/modem if alerts are configured. The status is sent whether or not remote enable is allowed.

## 8. Auto-start / ATS, paralleling and the bus-side rules
- **Auto-start/ATS:** unchanged logic. Starts requested while battle short is active are not blocked by inhibits (§5). E-stop still blocks them.
- **Breaker closing is not overridden.**
  - Closing out of phase onto a live bus wrecks the alternator and the coupling, and can hurt people. Battle short overrides trips (opening), not close permissives.
  - A GCB/MCB close still needs a valid sync-check (both ADEs good) or a verified dead bus. With the BUS ADE silent (FW-MTR-3), no close is possible, as before.
  - **Ethan's decision D3: no dead-bus close without proof that the bus is dead.** Proof = a valid BUS ADE reading below the dead-bus threshold. With the BUS ADE silent there is no close, in battle short too. (An external ATS/interlock "utility open" input could become a second proof later; it does not exist on this board and is not part of this spec.)
- **A closed breaker stays closed.** That is already the bus-side rule (FW-MTR-3), and battle short also suppresses the protection opens.
- **Paralleling (two or more sets on one bus): exception to "all breaker trips overridden" (Ethan's decision D6).** On a paralleled set the **reverse-power breaker trip stays active in battle short**. Every other breaker trip is still overridden.
  - Why: a set that loses its engine but keeps its breaker closed is driven as a motor by the other sets. That pulls the bus down and can damage both sets, which defeats the purpose of battle short.
  - It opens **only that set's GCB** and never stops an engine.
  - Not editable (§12).
  - **Note:** no reverse-power function is specified in ARCHITECTURE.md yet, because paralleling is not specified. When paralleling is added, it must include a reverse-power trip, and this rule applies to it.

## 9. Overcurrent: overridden, with a fire and cable warning
- Per Ethan, controller overcurrent and short-circuit trips are overridden.
- **Risk:** the controller will no longer protect the generator windings, the output cables or the load. A sustained overload or a fault can overheat cables and windings and cause a fire.
- **What still protects:** the generator's own thermal-magnetic breaker or MCCB, which is outside the controller and still trips (§2 H10).
- **Install requirement:** fit one, sized for the generator rating and the cable, and do not rely on the controller in battle short.
- Firmware logs every overcurrent minute in battle short (peak current, duration) for the warranty record.

## 10. Logging and counters (never cleared)
- **Event log (FRAM ring buffer, mirrored to the CM5 log):** one record for:
  - enable and disable (how: local / remote / timeout / E-stop / power cycle; who, if known);
  - every overridden fault: fault code, RTC timestamp, measured value (e.g. oil pressure, temperature, voltage, current, frequency), its trip threshold, and how long it lasted.
- **Lifetime counters (FRAM, CRC, A/B, write-once-increment):** never cleared by an operator reset, a configuration reset, a factory reset or a firmware update. A firmware update must carry them over.
  - battle-short activations;
  - total battle-short engine hours;
  - overridden faults per class (oil, temperature, voltage, frequency, overcurrent, metering, power-dip, breaker, start inhibit, overcrank);
  - total minutes run with each fault class present.
- **Visibility:** the counters appear on a service screen and in the configuration suite as read-only "Battle short history" for warranty and engine-life records.

## 11. Installation and manual warning text (paste as is)
> **WARNING – BATTLE SHORT.** Battle short turns OFF the controller's engine and breaker protections: low oil pressure, high temperature, over/undervoltage, over/underfrequency, overcurrent, metering-fault and breaker trips. Only the emergency stop and engine overspeed stay active (plus, on generators run in parallel, the reverse-power breaker trip). If the engine will not start, the controller keeps cranking with rest breaks until it starts or is stopped. Running in battle short can destroy the engine, the generator or the connected equipment, and an overload or short circuit can overheat cables and start a fire. Use it only when losing power is more dangerous than losing the generator. Fit an external generator circuit breaker sized for the generator and the cable; the controller does not protect them in battle short. A controller fault (firmware hang) still stops the engine, and the controller must then be power-cycled to restart. Every use of battle short and every fault overridden is permanently recorded in the controller. Battle short is off unless enabled in the configuration suite by an administrator.

Also in the manual: the two-step enable procedure (§4), how to turn it off (§6), what the 5 s grace on disable means, and "assign a battle-short beacon output" (§7).

## 12. Configuration settings: what the configuration suite can and cannot edit
All battle-short settings live in MCU FRAM (CRC, A/B copies), like the other safety settings.
- **Who can change them:** only with the configuration suite's admin credential. Remotely, only if the configuration-edit permission allows it.
- **When:** not while battle short is active. The one exception is turning `BS_AVAILABLE` off, which also turns battle short off at once.
- **Logging:** every change is logged with who, when, the old value and the new value.
- **Out-of-range values** are refused, not clamped. The suite shows the limit.

**Editable (admin):**
| Setting | Default | Allowed values (hard limits) | Notes |
|---|---|---|---|
| `BS_AVAILABLE` | off | on / off | Pre-authorises the local enable (§4 step 1). Turning it on needs a typed confirmation of the §11 warning |
| `BS_REMOTE_ENABLE` | off | on / off; can be on only while `BS_AVAILABLE` is on | Allows an authenticated remote enable (§4). Remote **disable** never needs it |
| `BS_PIN_REQUIRED` | off | on / off; PIN 4–8 digits | Display confirm also asks for the PIN. The no-display key confirm is unaffected |
| `BS_PERSIST_POWER_CYCLE` (D1) | off | on / off | Off = a power cycle clears battle short (Ethan's D1 default). On = it persists, for unattended sites |
| `BS_TIMEOUT_H` | 0 (never) | 0, or 1–168 h | Auto-expiry with a 10 min warning (§6) |
| `BS_DISABLE_GRACE_S` | 5 s | 2–30 s | Delay before protections return after disable (§6). Cannot be 0, so a still-present fault never acts the instant the operator lets go of the keys |
| `BS_CRANK_MAX_S` (D4) | 10 s | 3–15 s, and never above the normal crank-time setting | Length of one crank attempt in battle short |
| `BS_CRANK_REST_S` (D4) | 30 s | 20–300 s, and at least 2 × `BS_CRANK_MAX_S` | Rest between attempts (starter cooling) |
| `BS_CRANK_LONG_REST_S` (D4) | 120 s | 60–600 s, and at least `BS_CRANK_REST_S` | Longer rest after every 3 failed attempts |
| `BS_ALARM_AUX` | none | none, or one of AUX1–AUX10 not already assigned | AUX output held on while battle short is active, for a beacon or common-alarm relay (§7). The installer should assign one |
| `BS_BUZZER_REPEAT_S` | 30 s | 10–120 s | Chirp interval while active (§7). The buzzer cannot be switched off for battle short |
| `BS_SILENCE_MIN` | 15 min | 1–60 min | How long "silence" mutes the repeat chirp. A **new** overridden fault always sounds the full alarm, whatever this is set to |

**Fixed (not editable in the configuration suite or anywhere else):**
| Item | Fixed behaviour |
|---|---|
| E-stop | Always active. Pressing it stops the engine and clears battle short (D2) |
| Overspeed | Always active. Uses the normal engine overspeed setpoint; battle short cannot raise or disable it. Speed lost (MPU and GEN frequency): keep running and alarm (D5) |
| Watchdog latch (TPS3431/U84) | Always stops the engine on a firmware hang until power cycle (hardware; §2–3) |
| Breaker close permissives | Sync-check, or a dead bus proven by a valid BUS ADE reading (D3). Never relaxed |
| Reverse-power trip on paralleled sets | Stays active in battle short (D6) |
| Overcrank retries | Indefinite (D4); only the timing above is editable |
| Local STOP key | Always stops the engine |
| Enable sequence | Two-hand 5 s corner hold, 10 s confirm window, 3 s confirm-key hold (§4). Key mapping per D7 (pending) |
| Warnings | Banner, flashing key LED and remote status bit (§7) cannot be turned off |
| Logging and lifetime counters | Always on; never cleared (§10) |
| Kept-active items | D+ 30 s excitation cap, glow 60 s cap/cooldown, load-shed (§5) |

## 13. Requirements index (for the firmware writer)
- **BS-1** Mode flag in FRAM (CRC, A/B). An overlay on the state machine, not a state.
- **BS-2** Enable per §4 (two-step, local; remote only with `BS_REMOTE_ENABLE`).
- **BS-3** Override table §5. E-stop and overspeed stay active, the STOP key always works, close permissives stay.
- **BS-4** Disable per §6, with the `BS_DISABLE_GRACE_S` grace and the warning.
- **BS-5** Warnings per §7.
- **BS-6** Logging and lifetime counters per §10.
- **BS-7** Auto-start/ATS/paralleling per §8.
- **BS-8** The watchdog latch is never bypassed. Firmware never writes WD_OK, U84 or WDO_N (none are reachable), and keeps kicking the TPS3431 only from the checked-in main-loop point, as in normal mode.
- **BS-9** CM5 refuses MCU reset or reflash while battle short is active and the engine is running (§3).
- **BS-10** Power cycle clears battle short unless `BS_PERSIST_POWER_CYCLE` is on (§6).
- **BS-11** Warm-restart fuel re-assert ≤ 50 ms after a non-POR reset with the engine turning (§3).
- **BS-12** Bench test (BRINGUP_CHECKLIST):
  - enable and disable by both methods;
  - simulate each overridden fault and check it alarms and logs without a stop;
  - check overspeed still stops the engine;
  - check E-stop still stops and clears battle short;
  - with the engine unable to start, check cranking retries past the normal limit with the configured crank, rest and long-rest times;
  - with the BUS ADE silent, check no dead-bus close happens in battle short (D3);
  - when paralleling exists: check a reverse-power condition opens the GCB in battle short (D6);
  - stop PA12 kicks and check the engine stops and stays stopped until power cycle;
  - force an IWDG reset while running and measure the FUEL_EN gap (≤ 50 ms target);
  - check the counters survive a factory reset.
- **BS-13** Configuration settings, defaults and hard limits per §12. Out-of-range values are refused. The fixed items in §12 have no setting at all.

## 14. Decisions (Ethan, Nov 22, 2026, ≈ 2:55 PM HST: "Yes, go with all your battle short suggestions")
- **D1** Battle short clears on a power cycle. The admin setting `BS_PERSIST_POWER_CYCLE` can make it persist (§6, §12).
- **D2** E-stop also clears battle short (§6).
- **D3** No dead-bus close without proof that the bus is dead (a valid BUS ADE reading) (§8).
- **D4** Cranking retries indefinitely, with rest breaks (§5, §12).
- **D5** If the speed signal is lost (MPU and the GEN-frequency backup), keep running and raise an alarm (§5).
- **D6** The reverse-power breaker trip stays active on paralleled sets: the one exception to "all breaker trips overridden" (§5, §8).
- **D7 (pending)** Front-panel combination keys: corners plus centre-top as proposed; final BTN mapping once the front-panel legend exists.
