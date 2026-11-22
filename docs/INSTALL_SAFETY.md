# Installation safety: output wiring and fusing

> Genctl is an open-source DIY design. It is NOT certified. Fuse and wire values below are
> inference, not certified. Wire table basis: ABYC E-11 Table 4B (105 °C wire, inside the engine space, bundled); not checked against SAE J1128, ISO 6722 or ISO 8820.

> **WARNING: Output copper on this board revision is not yet rated for the fuse values in this
> table. Do not build or load this revision beyond the bench-test limits until the routing plan's
> current targets are met (see ROUTING_PLAN.md).**

## Load dump / supply assumptions
(From review/hv/load_dump_external.md §(c), pasted exactly.)

> **Load dump / supply assumptions.** This controller assumes a battery-backed 12 V or 24 V DC supply bus (9–32 V DC continuous; up to 36 V for at most 60 s): a healthy battery permanently connected across the charging alternator, with the alternator's own regulator or centralised suppression limiting transients. The controller is **not designed to survive an unsuppressed load dump**, the high-energy surge (up to about 100 V on 12 V systems and about 200 V on 24 V systems, lasting hundreds of milliseconds) produced when the battery is disconnected while the alternator is charging. Do not run the generator with the battery disconnected. Do not open the battery master or isolator switch while the engine is running or the alternator is charging. Keep battery terminals clean and tight. Stop the engine before isolating the battery. If your installation can lose the battery while running, fit a separately designed load-dump surge protector on the battery feed after the 30 A battery fuse, feeding both the controller supply and the E-stop supply. The on-board TVS only covers short transients. Damage from load dump is not covered by any rating. This design is not certified to ISO 16750-2, SAE J1113 or any other standard. Have a qualified professional review the installation.

- Board battery input: no fuse on the board. The battery lead to J1 is fused in the power box at F1: 10 A standard (non-time-delay) ATO/ATC, 58 V DC. Every battery-side blade and stud fuse in the power box (F1–F25, and the main battery-cable fuse) must be rated 58 V DC. A 32 V DC blade is not acceptable: the declared supply includes 36 V for 60 s (24 V jump-start), and a fuse must be able to interrupt at that voltage. The 58 V rating is the next common automotive class; it is margin, not a supported bus voltage. Load dump is not supported. (Safety FINAL Round 6.) The board silkscreen text beside J1 is a pending board change; the 10 A current rating is unchanged (a 15 A fuse was not approved).

## Power box fuse positions (Ethan ruling 2026-11-21)
Genctl is two modules: the controller (this board, including the 600 V sensing) and a separate power box that holds every fuse and the power relays (draft BOM: review/bom_final/BOM_powerbox.csv). Rules:
- No fuses on the controller board. The only exception is a PTC resettable fuse on a small signal or sensor supply output where it is useful (fitted: F101/F102 1210L020/72 on DI_BIAS_A/B as backup behind the U89/U90 TPS26621 active current limit, 0.20 A, m7-sch Batch 18). U89/U90 must stay on the protected VBAT_P rail behind the LM74800 (U1) and must never be moved to the raw battery input BAT_IN: their 62 V absolute maximum is below the ~64.5 V clamp of the battery-input TVS (Safety S7-N13).
- Battery and low-voltage fuses are ATO/ATC blades from the 32–58 V DC family; this design must use the 58 V DC members only (F1–F25 and the main battery-cable fuse F0; see the battery input bullet).
- The 600 V metering fuses must state a 600 V rating (power box F26–F31): SIBA 6003305.1 1 A 600 V AC 10x38 ceramic aR, 200 kA at 600 V AC, in Eaton CHM3DU (or equal) 600 V IP20 finger-safe holders; or Littelfuse KLKD001 600 V AC/DC.
- Do not plug or unplug the 600 V voltage-sense plugs J7/J8 (board J28/J29, Phoenix PC 5/4 1720819) live. Open the metering fuses (power box F26–F31) or isolate the generator/bus source first; the plugs are not rated for making or breaking a live 600 V circuit (Safety R7-N12).
- J7/J8 (board J28/J29) field wire: use wire insulated for at least 600 V, in the Phoenix PC 5/4-STF1-7,62 (1777859) plug. Strip it to the plug's stated stripping length, **10 mm** (Phoenix 1777859 catalog data, "Stripping length 10 mm"; conductor 0.2–6 mm² flexible / 24–10 AWG; screw torque 0.5–0.8 Nm). No bare copper may show past the plug body; if it does, cut and re-strip.
- The LEFT_HV enclosure window (over J28/J29) must have its hood fitted, and the hood must be removable only with a tool. This is enclosure hardware (Mechanical's scope), not part of this board.
- Every wire that leaves a module is fused at its source, below what the copper and the wire can carry.
- How "fused at its source" is applied: (1) each field cable that leaves the power box is fused at the power-box terminal that starts that cable (F3–F22, F23–F25, F26–F31); (2) each cable that leaves the power box for the controller (J1, J23.1/2, and the 600 V sense tails after the metering fuses) is fused at the power-box end (F1, F2, F26–F31); (3) the short loom from the controller outputs back to the power-box fuse holders is protected by the upstream supply fuse (F1 or F2) and must be kept short, in a protected trough, and not used as a field run; (4) the 600 V conductors are fused at their origin — the generator and bus terminals, or a fused terminal block immediately there. The power box may be that origin only if it is mounted at the switchgear with short, mechanically protected tails. Do not run unfused 600 V cable between the bus and a remote power box; (5) EXP_12V and ROUTER_12V are current-limited at the controller (TPS1H200, 1.5 A and 2.0 A). CT secondaries are not fused.
- The board stays rated 10 A total.

## No on-board fusing
There is no on-board fusing on any output. The power box fuses are the only
overcurrent protection beyond each driver's electronic current limit. The electronic limit
does not protect against a failed (shorted-on) driver or a wiring fault.

## External fuse on every output
Every output has its own fuse position in the power box (F3–F20).
- Place it in a fuse holder rated for the fuse, as close to the battery/supply source as
  practical, ahead of the relay or solenoid it feeds.
- The values below are the MAXIMUM recommended per output. Size the fuse DOWN to the actual
  coil/load current; never fit a fuse above the table value.
- The wire must be rated above the fuse.

| Output | Connector.pin | Driver | Rating / electronic limit | Max fuse (power box position) |
|---|---|---|---|---|
| FUEL | J23.3 (supply J23.1/2 VBAT_ESTOP) | TPS48100-Q1 + 2 MOSFETs | 2.8 A max (fuel solenoid incl. pull-in) | F3: 5 A standard (non-time-delay) ATO/ATC, 58 V DC (OptiFuse ANR58-UL-5A) |
| CRANK | J23.4 | TPS48100-Q1 + 2 MOSFETs | 2.8 A max (interposing crank relay coil only; never the starter solenoid directly) | F4: 5 A standard (non-time-delay) ATO/ATC, 58 V DC (OptiFuse ANR58-UL-5A) |
| GLOW | J24.1 | TPS1HTC30-Q1 | limit 4.02 A (3.18–4.87 A) | F5: 2 A blade, >=58 V DC (glow plugs switched by power box K3) |
| GCB_CL, GCB_OP, MCB_CL, MCB_OP | J24.2, .3, .4, .5 | TPS1HTC30-Q1 | limit 4.02 A (3.18–4.87 A) | 2 A blade each, >=58 V DC |
| ESTOP_TRIP | J24.6 | TPS1HTC30-Q1 | relay drive, limit 2.1 A (1.7–2.6 A), 0.30–1.00 s pulse (0.48 s nominal) | 2 A blade, >=58 V DC |
| AUX1–AUX6 | J26.1–6 | TPS1HTC30-Q1 | limit 4.02 A (3.18–4.87 A) | 2 A blade each, >=58 V DC |
| AUX7–AUX10 | J27.1–4 (J27.5/6 = GND) | TPS1HTC30-Q1 | limit 4.02 A (3.18–4.87 A) | 2 A blade each, >=58 V DC |
| Battery feed (E-stop/fuel) | J23.1/2 VBAT_ESTOP via NC E-stop | — | FUEL + CRANK 5.6 A max | F2: 10 A standard (non-time-delay) ATO/ATC, 58 V DC, in the power box after the 30 A battery fuse; wire >= 16 AWG / 1.31 mm² |
The E-stop/fuel feed (J23.1/2) is NOT disconnected by the controller's over-voltage cut-off. Its only on-board protection is a 40 V TVS diode, which starts to conduct at about 44 V and can then fail short or partly short. The 30 A battery fuse will not protect the board against such a fault. Keep this feed within the declared supply range (9–32 V DC continuous, up to 36 V for at most 60 s) and never above about 40 V, and always fit the 10 A J23 fuse (power box F2): it protects the board copper and wiring; the 30 A fuse protects only the main battery cable. A partly shorted TVS can still overheat below the 10 A fuse rating. If the board shows heat damage near the J23 connector, take the controller out of service.

The 30 A (or other) battery-cable fuse protects only the cable that feeds the controller and E-stop distribution in the power box. Starter-solenoid and glow-plug currents use separate cables from the battery, each fused at the battery (or at a power-box input next to it) by F23–F25, sized to the engine. Do not put the starter or the glow bank behind the 30 A controller feed.

Every external fuse in this table must be rated >=58 V DC (a 32 V DC blade fuse does not meet this); the extra voltage rating is margin, not a supported supply voltage. The controller is declared for 12 V and 24 V battery systems with the battery always connected: Supply 9–32 V DC continuous; up to 36 V for at most 60 s (24 V jump-start), during which the controller may switch itself off; above its over-voltage trip point, 36.35-40.06 V (component tolerance), it disconnects its internal supply, and after such an over-voltage trip the supply must fall below about 33 V before the controller restarts by itself. Load dump, including a centrally suppressed 58 V load dump (ISO 16750-2 Test B), is not supported. Every TVS-protected port can fail short-circuit if the supply goes above the declared range (TVS conduction starts at about 44 V): the battery input J1 (D1, D2, D63; protected by the 10 A battery-input fuse), the FUEL/CRANK outputs (D68, D69; protected by the output fuses and the electronic trip), the E-stop/fuel feed J23 (D126; 10 A J23 fuse) and the switch and sensor inputs (TVS at the connector pins; protected only by the field-supply fuse in the power box, F21/F22). The external fuses are then what disconnects the fault, so every feed to the controller, including switch and sensor supplies wired to its inputs, must be fused at the values in this table. Use energize-to-run fuel solenoids only (team-lead ruling R5-N1; not certified).

Declared limit: 12 V and 24 V DC battery systems only, with the battery permanently connected as the buffer. Supply 9–32 V DC continuous; up to 36 V for at most 60 s (24 V jump-start), during which the controller may switch itself off; above its over-voltage trip point, 36.35-40.06 V (component tolerance), it disconnects its internal supply, and after such an over-voltage trip the supply must fall below about 33 V before the controller restarts by itself. Short ISO 7637-type pulses are tolerated. Load dump of any kind, including a centrally suppressed 58 V load dump (ISO 16750-2 Test B), is not supported and has not been tested. The fuel solenoid must be energize-to-run.

Total draw and ESTOP_TRIP (inference, not certified):
- The board battery path (J1 → BAT_IN → Q1 → Q2 → Q3) has **no on-board fuse**; the power box fuse F1 (10 A standard (non-time-delay) ATO/ATC, 58 V DC) is the only protection on this path and sets the maximum current. The 10 A copper capacity of J1 → Q1 is NOT demonstrated for the BAT_IN layout (board update pending; the old fused-path copper figure no longer applies). Caveat: with a 10 A ATO, it carries at most about 8 A at 149 °F (65 °C) ambient (Littelfuse 287 ATOF derating, final_power_spec.md §1; datasheet pages UNVERIFIED). The battery wiring and the mating connector must be rated for the load as well. The 12 V electronics and all AUX/GCB/MCB/GLOW outputs share this limit.
- Load shedding (the controller switching outputs off) is a fault-only response, not a normal-operation behavior. Size the installation so the normal load stays within the limits on this page.
- AUX/GCB/MCB outputs are for relay coils, solenoids and indicators of 2.8 A maximum each (including pull-in current); the GLOW output is for a relay coil only (2.8 A maximum including pull-in); glow plugs themselves must be switched by an external relay. Loads above 2.8 A must be switched through an interposing relay whose coil is <= 2.8 A. Every inductive load needs a suppression diode or the protection described in this section. Where a circuit's own row above lists a lower limit or fuse (for example AUX 2.0 A, 2 A fuse), the lower limit governs.
- Power box K3 glow contactor (Altran ALEV100-B 12 V / ALEV100-C 24 V, standard option): the **main load terminals are polarised** (marked +A1 / -A2 on the cover). Observe polarity: +A1 to the fused battery (+) feed, -A2 to the glow-plug bank, so load current flows +A1 -> -A2. Reversed wiring is outside the contactor rating. The coil leads (white wires) are non-polar. If non-polar load terminals are wanted, order the "N" option (e.g. ALEV100-CN). Source: Altran ALEV100 datasheet Rev K 30-Oct-2024, nomenclature and outline-drawing notes ("Contact terminals are polarized so refer to drawing during connecting").
- ESTOP_TRIP (J24.6) drives a 12 V or 24 V DC relay (power box K4, Finder 38.51 or equal) or shunt-trip coil that draws less than 1.70 A (including pull-in), with a suppression diode across the coil. 1.70 A is the minimum current limit of the trip output (U68 with R407 47k: 1.70 / 2.13 / 2.55 A min/typ/max). A coil drawing more may not operate reliably.
- Hardware maximum per main output: interposing relay coil class <= 2.8 A (software trip 3.0 A). E-stop trip coil must draw < 1.70 A (U68 limit with R407 47k); measure on the bench. Where a circuit has a lower limit or a 2 A fuse, that lower limit governs.
- ESTOP_TRIP pulse: 0.30–1.00 s, 0.48 s nominal. This only has to outlast the K4 relay pickup, and its coil is continuous-rated. It must be measured on a built board, cold and hot, before relying on it. For a held signal, or a UVR, wire the UVR from the E-stop chain, never through the controller.

- DI bias terminals (DI_BIAS_A at J21.6, DI_BIAS_B at J22.1): **no external loads.** Use them only as the common return/feed for the volt-free contacts of the 12 digital inputs. Do not power sensors, lamps or relays from them. Each bias line has an on-board PTC (F101/F102, 0.10 A hold at 73 °F / 23 °C, about 0.048 A at 185 °F / 85 °C); the inputs themselves already use up to about 0.046 A per bank at 36 V with all six contacts closed, so there is no spare current for an external load.
Connectors:
- J24, J26, J27 (Kefa KF2EDGRM-5.08-6P headers): rated 10 A UL / 15 A IEC per pin (Kefa drawing rev A). The rating is for a
  single pole; no derating is given for all poles loaded (UNVERIFIED for that case). The mating plug's wire range is
  unknown: Ethan has to check it.
- J23 (Phoenix 1720819, PC 5/4-GF-7.62): 32 A nominal, 41 A UL; covers the 2.8 A FUEL/CRANK channels (subject to the maker's derating curve).

**FUEL/CRANK fuse type (installer's check):** FUEL and CRANK are limited to 2.8 A each
(including pull-in). Use a 5 A standard (non-time-delay) ATO/ATC blade, 58 V DC (OptiFuse ANR58-UL-5A or equal), at power box F3/F4. The starter motor/solenoid must never be driven directly: use the interposing crank
relay in the power box (K1) whose coil is <= 2.8 A (Safety Round 4, R4-N3).

> **WARNING: the 30 A battery fuse does NOT protect the FUEL/CRANK channels, the small
> outputs, or their wiring.** A short on a channel can draw far more than its rating without
> blowing the 30 A fuse; board copper, connectors and wiring can overheat first.
> Fit the per-output fuses, and the 10 A fuse in the J23 (E-stop/fuel) branch.

## Wire size vs fuse (inference, not certified; basis ABYC E-11 Table 4B, 105 °C wire, engine space, bundled)
| Fuse | Minimum copper |
|---|---|
| 2 A | 18 AWG / 0.82 mm² |
| 5 A | 18 AWG / 0.82 mm² |
| 10 A | 16 AWG / 1.31 mm² |
| 15 A | 14 AWG / 2.08 mm² |
| 30 A | 10 AWG / 5.26 mm² |

For circuits under 50 V, also check voltage drop.

Never use wire smaller than the stated mm², whatever AWG is used.

## Coil flyback protection
Fit a diode (or bidirectional TVS) directly across every external relay and solenoid coil,
cathode to the + (output) side, so the on-board driver is protected from the inductive spike at
switch-off. The small-output drivers have an internal inductive clamp (TPS1HTC30-Q1 datasheet only; TPS48100 inferred), but an external diode
at the coil keeps that energy off the board and the cable.

## CT circuits and J30 (Batch 29)
> **WARNING: NEVER OPEN A CT LOOP OR DISCONNECT J30 WITH THE GENERATOR LIVE.** An open 5 A CT secondary under load develops a lethal voltage (kilovolts peak) and can destroy the CT. Before touching the CT wiring, the meter board or the controller: short every CT at the J30 shorting block first (or stop the generator and open the breaker).

- J30 is the CT shorting/test terminal block in the genset panel (site-supplied, as is normal switchgear practice). It is **not** on the controller board any more.
- Each CT circuit runs as a factory-fitted 600 V pigtail (UL1015, 14 AWG max) through a window CT on the meter board. Land the pigtail ends on J30 so that the external CT's **S1** feeds the pigtail end marked **P1** (the P1* face of T1-T4). Wrong polarity shows as negative power at commissioning (firmware wiring check).
- Earth the CT secondaries at J30 (S2 side), per local code. Use the shorting links when removing the controller or the meter board.
- Do not re-thread, cut or extend the pigtails inside the enclosure. Keep them tied down; damaged insulation is the only barrier between the earthed CT loop and the 600 V metering circuit.

## Open for installer / Ethan (does not block this document)
1. Fuel solenoid pull-in current and duration: must be <= 2.8 A (5 A standard (non-time-delay) ATO/ATC, 58 V DC, OptiFuse ANR58-UL-5A or equal); the starter is switched via an interposing relay only.
2. GLOW: relay coil (2 A max fuse) or glow plugs driven directly (not supported: electronic limit 3.18 A minimum, see the table above; use an external relay).
3. ESTOP_TRIP relay: confirm the installer relay coil is 12 V DC, ≤ 0.5 A, with a suppression diode; size the 2 A fuse down to it. The relay contact, not ESTOP_TRIP, switches the breaker shunt trip.
4. Actual relay coil currents on GLOW/GCB/MCB/AUX: size each fuse down from 2 A.
