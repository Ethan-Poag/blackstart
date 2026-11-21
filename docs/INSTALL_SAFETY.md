# Installation safety: output wiring and fusing

> Genctl is an open-source DIY design. It is NOT certified. Fuse and wire values below are
> inference, not certified. Wire table basis: ABYC E-11 Table 4B (105 °C wire, inside the engine space, bundled); not checked against SAE J1128, ISO 6722 or ISO 8820.

> **WARNING: Output copper on this board revision is not yet rated for the fuse values in this
> table. Do not build or load this revision beyond the bench-test limits until the routing plan's
> current targets are met (see ROUTING_PLAN.md).**

## Load dump / supply assumptions
(From review/hv/load_dump_external.md §(c), pasted exactly.)

> **Load dump / supply assumptions.** This controller assumes a battery-backed 12 V or 24 V DC supply bus (9–32 V DC continuous; up to 36 V for at most 60 s): a healthy battery permanently connected across the charging alternator, with the alternator's own regulator or centralised suppression limiting transients. The controller is **not designed to survive an unsuppressed load dump**, the high-energy surge (up to about 100 V on 12 V systems and about 200 V on 24 V systems, lasting hundreds of milliseconds) produced when the battery is disconnected while the alternator is charging. Do not run the generator with the battery disconnected. Do not open the battery master or isolator switch while the engine is running or the alternator is charging. Keep battery terminals clean and tight. Stop the engine before isolating the battery. If your installation can lose the battery while running, fit a separately designed load-dump surge protector on the battery feed after the 30 A battery fuse, feeding both the controller supply and the E-stop supply. The on-board TVS only covers short transients. Damage from load dump is not covered by any rating. This design is not certified to ISO 16750-2, SAE J1113 or any other standard. Have a qualified professional review the installation.

- Board battery input: **no fuse on the board** (on-board fuse and its Keystone 3557-2 clips removed; schematic m7-sch). The battery lead to J1 is fused in the power box at position **F1: <=10 A fast-acting, rated >=58 V DC** (schematic note "EXT FUSE <=10 A FAST, >=58 V DC" beside J1; the board silkscreen text is a pending board change). Voltage requirement: the fuse DC voltage rating must be at least 58 V DC, because the board relies on a declared central load-dump suppression of <=58 V (fixes_safety.md Rev 3 R3-1, §0); a 32 V DC automotive blade fuse does NOT meet this. The 10 A current rating is unchanged (a 15 A fuse was not approved).

## Power box fuse positions (Ethan ruling 2026-11-21)
Genctl is two modules: the controller (this board, including the 600 V sensing) and a separate power box that holds every fuse and the power relays (draft BOM: review/bom_final/BOM_powerbox.csv). Rules:
- No fuses on the controller board. The only exception is a PTC resettable fuse on a small signal or sensor supply output where it is useful (proposed: DI_BIAS_A/B, ECO pending).
- Battery and low-voltage fuses are ATO/ATC blades rated 32–58 V DC; this design requires the 58 V DC rating (see below).
- The 600 V metering fuses must state a 600 V rating; ceramic body (power box F26–F31, SIBA 6003305.1 1 A 600 V AC 10x38 or equal).
- Every wire that leaves a module is fused at its source, below what the copper and the wire can carry.
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
| FUEL | J23.3 (supply J23.1/2 VBAT_ESTOP) | TPS48100-Q1 + 2 MOSFETs | 2.8 A max (fuel solenoid incl. pull-in) | F3: 5 A blade ATO/ATC, >=58 V DC |
| CRANK | J23.4 | TPS48100-Q1 + 2 MOSFETs | 2.8 A max (interposing crank relay coil only; never the starter solenoid directly) | F4: 5 A blade ATO/ATC, >=58 V DC |
| GLOW | J24.1 | TPS1HTC30-Q1 | limit 4.02 A (3.18–4.87 A) | F5: 2 A blade, >=58 V DC (glow plugs switched by power box K3) |
| GCB_CL, GCB_OP, MCB_CL, MCB_OP | J24.2, .3, .4, .5 | TPS1HTC30-Q1 | limit 4.02 A (3.18–4.87 A) | 2 A blade each, >=58 V DC |
| ESTOP_TRIP | J24.6 | TPS1HTC30-Q1 | relay drive, limit 2.1 A (1.7–2.6 A), ~0.5 s pulse | 2 A blade, >=58 V DC |
| AUX1–AUX6 | J26.1–6 | TPS1HTC30-Q1 | limit 4.02 A (3.18–4.87 A) | 2 A blade each, >=58 V DC |
| AUX7–AUX10 | J27.1–4 (J27.5/6 = GND) | TPS1HTC30-Q1 | limit 4.02 A (3.18–4.87 A) | 2 A blade each, >=58 V DC |
| Battery feed (E-stop/fuel) | J23.1/2 VBAT_ESTOP via NC E-stop | — | FUEL + CRANK 5.6 A max | F2: 10 A ATO/ATC (standard or fast), >=58 V DC, in the power box after the 30 A battery fuse; wire >= 16 AWG / 1.31 mm² |
The E-stop/fuel feed (J23.1/2) is NOT disconnected by the controller's over-voltage cut-off. Its only on-board protection is a 40 V TVS diode, which starts to conduct at about 44 V and can then fail short or partly short. The 30 A battery fuse will not protect the board against such a fault. Keep this feed within the declared supply range (9–32 V DC continuous, up to 36 V for at most 60 s) and never above about 40 V, and always fit the 10 A J23 fuse (power box F2): it protects the board copper and wiring; the 30 A fuse protects only the main battery cable. A partly shorted TVS can still overheat below the 10 A fuse rating. If the board shows heat damage near the J23 connector, take the controller out of service.

Every external fuse in this table must be rated >=58 V DC (a 32 V DC blade fuse does not meet this); the extra voltage rating is margin, not a supported supply voltage. The controller is declared for 12 V and 24 V battery systems with the battery always connected: Supply 9–32 V DC continuous; up to 36 V for at most 60 s (24 V jump-start), during which the controller may switch itself off; above about 36 V it disconnects its internal supply, and after such an over-voltage trip the supply must fall below about 33 V before the controller restarts by itself. Load dump, including a centrally suppressed 58 V load dump (ISO 16750-2 Test B), is not supported. Every TVS-protected port can fail short-circuit if the supply goes above the declared range (TVS conduction starts at about 44 V): the battery input J1 (D1, D2, D63; protected by the 10 A battery-input fuse), the FUEL/CRANK outputs (D68, D69; protected by the output fuses and the electronic trip), the E-stop/fuel feed J23 (D126; 10 A J23 fuse) and the switch and sensor inputs (TVS at the connector pins; protected only by the field-supply fuse in the power box, F21/F22). The external fuses are then what disconnects the fault, so every feed to the controller, including switch and sensor supplies wired to its inputs, must be fused at the values in this table. Use energize-to-run fuel solenoids only (team-lead ruling R5-N1; not certified).

Declared limit: 12 V and 24 V DC battery systems only, with the battery permanently connected as the buffer. Supply 9–32 V DC continuous; up to 36 V for at most 60 s (24 V jump-start), during which the controller may switch itself off; above about 36 V it disconnects its internal supply, and after such an over-voltage trip the supply must fall below about 33 V before the controller restarts by itself. Short ISO 7637-type pulses are tolerated. Load dump of any kind, including a centrally suppressed 58 V load dump (ISO 16750-2 Test B), is not supported and has not been tested. The fuel solenoid must be energize-to-run.

Total draw and ESTOP_TRIP (inference, not certified):
- The board battery path (J1 → BAT_IN → Q1 → Q2 → Q3) has **no on-board fuse**; the power box fuse F1 (<=10 A fast-acting, >=58 V DC) is the only protection on this path and sets the maximum current. The 10 A copper capacity of J1 → Q1 is NOT demonstrated for the BAT_IN layout (board update pending; the old fused-path copper figure no longer applies). Caveat: with a 10 A ATO, it carries at most about 8 A at 149 °F (65 °C) ambient (Littelfuse 287 ATOF derating, final_power_spec.md §1; datasheet pages UNVERIFIED). The battery wiring and the mating connector must be rated for the load as well. The 12 V electronics and all AUX/GCB/MCB/GLOW outputs share this limit.
- Load shedding (the controller switching outputs off) is a fault-only response, not a normal-operation behavior. Size the installation so the normal load stays within the limits on this page.
- AUX/GCB/MCB outputs are for relay coils, solenoids and indicators of 2.8 A maximum each (including pull-in current); the GLOW output is for a relay coil only (2.8 A maximum including pull-in); glow plugs themselves must be switched by an external relay. Loads above 2.8 A must be switched through an interposing relay whose coil is <= 2.8 A. Every inductive load needs a suppression diode or the protection described in this section. Where a circuit's own row above lists a lower limit or fuse (for example AUX 2.0 A, 2 A fuse), the lower limit governs.
- ESTOP_TRIP (J24.6) drives a 12 V or 24 V DC relay (power box K4, Finder 38.51 or equal) or shunt-trip coil that draws less than 1.70 A (including pull-in), with a suppression diode across the coil. 1.70 A is the minimum current limit of the trip output (U68 with R407 47k: 1.70 / 2.13 / 2.55 A min/typ/max). A coil drawing more may not operate reliably.
- Hardware maximum per main output: interposing relay coil class <= 2.8 A (software trip 3.0 A). E-stop trip coil must draw < 1.70 A (U68 limit with R407 47k); measure on the bench. Where a circuit has a lower limit or a 2 A fuse, that lower limit governs.
- ESTOP_TRIP pulse: nominal 0.48 s (0.44–0.53 s from component tolerance). It must be measured on a built board, cold and hot, before relying on it. For a held signal, or a UVR, wire the UVR from the E-stop chain, never through the controller.

Connectors:
- J24, J26, J27 (Kefa KF2EDGRM-5.08-6P headers): rated 10 A UL / 15 A IEC per pin (Kefa drawing rev A). The rating is for a
  single pole; no derating is given for all poles loaded (UNVERIFIED for that case). The mating plug's wire range is
  unknown: Ethan has to check it.
- J23 (Phoenix 1720819, PC 5/4-GF-7.62): 32 A nominal, 41 A UL; covers the 2.8 A FUEL/CRANK channels (subject to the maker's derating curve).

**FUEL/CRANK fuse type (installer's check):** FUEL and CRANK are limited to 2.8 A each
(including pull-in). Use a 5 A ATO/ATC blade, >=58 V DC, at power box F3/F4. The 58 V DC blades found
(OptiFuse ANR58) are fast-acting; a fast 5 A fuse on a <=2.8 A coil with no large inrush is
acceptable (inference; Safety to confirm). The starter motor/solenoid must never be driven directly: use the interposing crank
relay in the power box (K1) whose coil is <= 2.8 A (Safety Round 4, R4-N3).

> **WARNING: the 30 A battery fuse does NOT protect the FUEL/CRANK channels, the small
> outputs, or their wiring.** A short on a channel can draw far more than its rating without
> blowing the 30 A fuse; board copper, connectors and wiring can overheat first.
> Fit the per-output fuses, and the 10 A fuse in the J23 (E-stop/fuel) branch.

## Wire size vs fuse (inference, not certified; basis ABYC E-11 Table 4B, 105 °C wire, engine space, bundled)
| Fuse | Minimum copper |
|---|---|
| 2 A | 18 AWG / 0.82 mm² |
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

## Open for installer / Ethan (does not block this document)
1. Fuel solenoid pull-in current and duration: must be <= 2.8 A (5 A standard non-fast fuse); the starter is switched via an interposing relay only.
2. GLOW: relay coil (2 A max fuse) or glow plugs driven directly (not supported: electronic limit 3.18 A minimum, see the table above; use an external relay).
3. ESTOP_TRIP relay: confirm the installer relay coil is 12 V DC, ≤ 0.5 A, with a suppression diode; size the 2 A fuse down to it. The relay contact, not ESTOP_TRIP, switches the breaker shunt trip.
4. Actual relay coil currents on GLOW/GCB/MCB/AUX: size each fuse down from 2 A.
