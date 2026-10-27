# Installation safety: output wiring and fusing

> Genctl is an open-source DIY design. It is NOT certified. Fuse and wire values below are
> inference, not certified. Wire table basis: ABYC E-11 Table 4B (105 °C wire, inside the engine space, bundled); not checked against SAE J1128, ISO 6722 or ISO 8820.

> **WARNING: Output copper on this board revision is not yet rated for the fuse values in this
> table. Do not build or load this revision beyond the bench-test limits until the routing plan's
> current targets are met (see ROUTING_PLAN.md).**

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
| FUEL | J23.3 (supply J23.1/2 VBAT_ESTOP) | TPS48100-Q1 + 2 MOSFETs | 15 A | 15 A blade (ATO/ATC), 32 V DC |
| CRANK | J23.4 | TPS48100-Q1 + 2 MOSFETs | 15 A | 15 A blade (ATO/ATC), 32 V DC |
| GLOW | J24.1 | TPS1HTC30-Q1 | limit 2.49 A (1.99–2.99 A) | 2 A blade, 32 V DC |
| GCB_CL, GCB_OP, MCB_CL, MCB_OP | J24.2, .3, .4, .5 | TPS1HTC30-Q1 | limit 2.49 A | 2 A blade each |
| ESTOP_TRIP | J24.6 | TPS1HTC30-Q1 | relay drive, limit 2.1 A (1.7–2.6 A), ~0.5 s pulse | 2 A blade |
| AUX1–AUX6 | J26.1–6 | TPS1HTC30-Q1 | limit 2.49 A | 2 A blade each |
| AUX7–AUX10 | J27.1–4 (J27.5/6 = GND) | TPS1HTC30-Q1 | limit 2.49 A | 2 A blade each |
| Battery feed | to J23 VBAT_ESTOP via NC E-stop | — | system | 30 A (existing) |

32 V DC blade fuses suit 12 V and 24 V systems.

Total draw and ESTOP_TRIP (inference, not certified):
- The board battery path (F1 → Q1 → Q2 → Q3) is a 10 A path (F1 10 A) at 18 °F (10 °C) copper rise. This is INFERRED from the measured copper widths by IPC-2221 with 1 oz outer copper ASSUMED; it is not certified and not measured on a built board. The 12 V electronics and all AUX/GCB/MCB/GLOW outputs share this limit.
- Load shedding (the controller switching outputs off) is a fault-only response, not a normal-operation behavior. Size the installation so the normal load stays within the limits on this page.
- AUX/GCB/MCB/GLOW outputs are for relay coils and indicators only, ≤ 0.5 A each, combined ≤ 1 A while the controller display is on (INFERRED). This is a load budget the installer must stay within by design; the controller does not drop or switch off outputs to meet it in normal operation. Outputs are switched off only by fault protection (overload/fault, e.g. a channel's current limit or the watchdog trip).
- ESTOP_TRIP (J24.6) drives an installer-supplied 12 V DC relay coil, ≤ 0.5 A, with a suppression diode. It must NOT drive a breaker shunt coil directly. The relay contact switches the shunt trip from the installer's own control supply.
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
2. GLOW: relay coil (2 A max fuse) or glow plugs driven directly (not supported at 2.49 A; use an external relay).
3. ESTOP_TRIP relay: confirm the installer relay coil is 12 V DC, ≤ 0.5 A, with a suppression diode; size the 2 A fuse down to it. The relay contact, not ESTOP_TRIP, switches the breaker shunt trip.
4. Actual relay coil currents on GLOW/GCB/MCB/AUX: size each fuse down from 2 A.
