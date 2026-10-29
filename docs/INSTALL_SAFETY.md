# Installation safety: output wiring and fusing

> Genctl is an open-source DIY design. It is NOT certified. Fuse and wire values below are
> inference, not certified. Wire table basis: ABYC E-11 Table 4B (105 °C wire, inside the engine space, bundled); not checked against SAE J1128, ISO 6722 or ISO 8820.

> **WARNING: Output copper on this board revision is not yet rated for the fuse values in this
> table. Do not build or load this revision beyond the bench-test limits until the routing plan's
> current targets are met (see ROUTING_PLAN.md).**

## Load dump / supply assumptions
(From review/hv/load_dump_external.md §(c), pasted exactly.)

> **Load dump / supply assumptions.** This controller assumes a battery-backed, suppressed 12 V or 24 V DC supply bus: a healthy battery permanently connected across the charging alternator, with the alternator's own regulator or centralised suppression limiting transients. The controller is **not designed to survive an unsuppressed load dump**, the high-energy surge (up to about 100 V on 12 V systems and about 200 V on 24 V systems, lasting hundreds of milliseconds) produced when the battery is disconnected while the alternator is charging. Do not run the generator with the battery disconnected. Do not open the battery master or isolator switch while the engine is running or the alternator is charging. Keep battery terminals clean and tight. Stop the engine before isolating the battery. If your installation can lose the battery while running, fit a separately designed load-dump surge protector on the battery feed after the 30 A battery fuse, feeding both the controller supply and the E-stop supply. The on-board TVS only covers short transients. Damage from load dump is not covered by any rating. This design is not certified to ISO 16750-2, SAE J1113 or any other standard. Have a qualified professional review the installation.

- Board battery input: **no fuse on the board** (on-board fuse and its Keystone 3557-2 clips removed; schematic m7-sch). Installer must fit an external fuse in the battery lead at J1: **<=10 A fast-acting, rated >=58 V DC** (schematic note "EXT FUSE <=10 A FAST, >=58 V DC" beside J1; the board silkscreen text is a pending board change). Voltage requirement: the fuse DC voltage rating must be at least 58 V DC, because the board relies on a declared central load-dump suppression of <=58 V (fixes_safety.md Rev 3 R3-1, §0); a 32 V DC automotive blade fuse does NOT meet this. The 10 A current rating is unchanged (a 15 A fuse was not approved).

## No on-board fusing
There is no on-board fusing on any output. The installer-supplied fuses are the only
overcurrent protection beyond each driver's electronic current limit. The electronic limit
does not protect against a failed (shorted-on) driver or a wiring fault.

## External fuse on every output
Every output must have its own external fuse, supplied and installed by the installer.
- Place it in a fuse holder rated for the fuse, as close to the battery/supply source as
  practical, ahead of the relay or solenoid it feeds.
- The values below are the MAXIMUM recommended per output. Size the fuse DOWN to the actual
  coil/load current; never fit a fuse above the table value.
- The wire must be rated above the fuse.

| Output | Connector.pin | Driver | Rating / electronic limit | Max external fuse |
|---|---|---|---|---|
| FUEL | J23.3 (supply J23.1/2 VBAT_ESTOP) | TPS48100-Q1 + 2 MOSFETs | 15 A | 15 A blade (ATO/ATC), >=58 V DC |
| CRANK | J23.4 | TPS48100-Q1 + 2 MOSFETs | 15 A | 15 A blade (ATO/ATC), >=58 V DC |
| GLOW | J24.1 | TPS1HTC30-Q1 | limit 4.02 A (3.18–4.87 A) | 2 A blade, >=58 V DC |
| GCB_CL, GCB_OP, MCB_CL, MCB_OP | J24.2, .3, .4, .5 | TPS1HTC30-Q1 | limit 4.02 A (3.18–4.87 A) | 2 A blade each, >=58 V DC |
| ESTOP_TRIP | J24.6 | TPS1HTC30-Q1 | relay drive, limit 2.1 A (1.7–2.6 A), ~0.5 s pulse | 2 A blade, >=58 V DC |
| AUX1–AUX6 | J26.1–6 | TPS1HTC30-Q1 | limit 4.02 A (3.18–4.87 A) | 2 A blade each, >=58 V DC |
| AUX7–AUX10 | J27.1–4 (J27.5/6 = GND) | TPS1HTC30-Q1 | limit 4.02 A (3.18–4.87 A) | 2 A blade each, >=58 V DC |
| Battery feed | to J23 VBAT_ESTOP via NC E-stop | — | system | 30 A (existing), >=58 V DC |

Every external fuse (battery feed, 30 A E-stop feed, and each output) must be rated **>=58 V DC**, because the suppressed load dump can reach 58 V. A 32 V DC blade fuse does not meet this. Amp ratings are unchanged (team-lead ruling R3-N1, m7-sch batch 4).

Total draw and ESTOP_TRIP (inference, not certified):
- The board battery path (J1 → BAT_IN → Q1 → Q2 → Q3) has **no on-board fuse**; the installer's external fuse (<=10 A fast-acting, >=58 V DC) is the only protection on this path and sets the maximum current. The 10 A copper capacity of J1 → Q1 is NOT demonstrated for the BAT_IN layout (board update pending; the old fused-path copper figure no longer applies). Caveat: if the installer uses a 10 A ATO, it carries at most about 8 A at 149 °F (65 °C) ambient (Littelfuse 287 ATOF derating, final_power_spec.md §1; datasheet pages UNVERIFIED). The battery wiring and the mating connector must be rated for the load as well. The 12 V electronics and all AUX/GCB/MCB/GLOW outputs share this limit.
- Load shedding (the controller switching outputs off) is a fault-only response, not a normal-operation behavior. Size the installation so the normal load stays within the limits on this page.
- AUX/GCB/MCB/GLOW outputs are for relay coils and indicators only, ≤ 0.5 A each, combined ≤ 1 A while the controller display is on (INFERRED). This is a load budget the installer must stay within by design; the controller does not drop or switch off outputs to meet it in normal operation. Outputs are switched off only by fault protection (overload/fault, e.g. a channel's current limit or the watchdog trip).
- ESTOP_TRIP (J24.6) drives an installer-supplied 12 V DC relay coil, ≤ 0.5 A, with a suppression diode. It must NOT drive a breaker shunt coil directly. The relay contact switches the shunt trip from the installer's own control supply.
- Hardware maximum per main output: interposing relay coil class <= 2.8 A (software trip 3.0 A). E-stop trip coil must draw < 1.70 A (U68 limit with R407 47k); measure on the bench. Where a circuit has a lower limit or a 2 A fuse, that lower limit governs.
- ESTOP_TRIP pulse: nominal 0.48 s (0.44–0.53 s from component tolerance). It must be measured on a built board, cold and hot, before relying on it. For a held signal, or a UVR, wire the UVR from the E-stop chain, never through the controller.

Connectors:
- J24, J26, J27 (Kefa KF2EDGRM-5.08-6P headers): rated 10 A UL / 15 A IEC per pin (Kefa drawing rev A). The rating is for a
  single pole; no derating is given for all poles loaded (UNVERIFIED for that case). The mating plug's wire range is
  unknown: Ethan has to check it.
- J23 (Phoenix 1720819, PC 5/4-GF-7.62): 32 A nominal, 41 A UL; covers 15 A (subject to the maker's derating curve).

**FUEL/CRANK fuse type (installer's check):** if the starter/fuel solenoid's pull-in current
exceeds its steady-state current, use a time-delay (slow-blow) 15 A blade fuse; otherwise a
standard 15 A blade. The 15 A rating lets small generators drive the starter relay/solenoid
directly without a second relay.

> **WARNING: the 30 A battery fuse does NOT protect the 15 A FUEL/CRANK channels, the small
> outputs, or their wiring.** A short on a 15 A channel can draw up to 30 A without blowing
> the 30 A fuse; board copper, connectors and wiring rated for 15 A can overheat first.
> Fit the per-output fuses.

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
1. Starter/fuel solenoid pull-in current and duration: standard or time-delay 15 A fuse.
2. GLOW: relay coil (2 A max fuse) or glow plugs driven directly (not supported: electronic limit 3.18 A minimum, see the table above; use an external relay).
3. ESTOP_TRIP relay: confirm the installer relay coil is 12 V DC, ≤ 0.5 A, with a suppression diode; size the 2 A fuse down to it. The relay contact, not ESTOP_TRIP, switches the breaker shunt trip.
4. Actual relay coil currents on GLOW/GCB/MCB/AUX: size each fuse down from 2 A.
