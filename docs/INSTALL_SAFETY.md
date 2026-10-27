# Installation safety: output wiring and fusing

> Genctl is an open-source DIY design. It is NOT certified. Fuse and wire values below are
> inference, not certified; the wire table has not been checked against SAE J1128 or ISO 8820.

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
| GLOW | J24.1 | TPS1HTC30-Q1 | limit 2.49 A (1.99–2.99 A) | 3 A blade, 32 V DC |
| GCB_CL, GCB_OP, MCB_CL, MCB_OP | J24.2, .3, .4, .5 | TPS1HTC30-Q1 | limit 2.49 A | 3 A blade each |
| ESTOP_TRIP | J24.6 | TPS1HTC30-Q1 | limit 7.5 A (6.0–9.0 A), ~2.2 s pulse | 10 A blade |
| AUX1–AUX6 | J26.1–6 | TPS1HTC30-Q1 | limit 2.49 A | 3 A blade each |
| AUX7–AUX10 | J27.1–4 (J27.5/6 = GND) | TPS1HTC30-Q1 | limit 2.49 A | 3 A blade each |
| Battery feed | to J23 VBAT_ESTOP via NC E-stop | — | system | 30 A (existing) |

32 V DC blade fuses suit 12 V and 24 V systems.

**FUEL/CRANK fuse type (installer's check):** if the starter/fuel solenoid's pull-in current
exceeds its steady-state current, use a time-delay (slow-blow) 15 A blade fuse; otherwise a
standard 15 A blade. The 15 A rating lets small generators drive the starter relay/solenoid
directly without a second relay.

> **WARNING: the 30 A battery fuse does NOT protect the 15 A FUEL/CRANK channels, the small
> outputs, or their wiring.** A short on a 15 A channel can draw twice its rating without blowing
> the 30 A fuse; board copper, connectors and wiring rated for 15 A can overheat first.
> Fit the per-output fuses.

## Wire size vs fuse (inference; not checked against SAE J1128 / ISO 8820)
| Fuse | Minimum copper |
|---|---|
| 3 A | 0.5 mm² (20 AWG) |
| 10 A | 0.82–1.3 mm² (18–16 AWG) |
| 15 A | 1.5–2.5 mm² (16–14 AWG) |
| 30 A | 4–6 mm² (12–10 AWG) |

## Coil flyback protection
Fit a diode (or bidirectional TVS) directly across every external relay and solenoid coil,
cathode to the + (output) side, so the on-board driver is protected from the inductive spike at
switch-off. The small-output drivers have an internal inductive clamp, but an external diode
at the coil keeps that energy off the board and the cable.

## Open for installer / Ethan (does not block this document)
1. Starter/fuel solenoid pull-in current and duration: standard or time-delay 15 A fuse.
2. GLOW: relay coil (3 A max fuse) or glow plugs driven directly (not supported at 2.49 A; use an external relay).
3. Shunt-trip coil current on ESTOP_TRIP: confirm the 10 A maximum, or size down.
4. Actual relay coil currents on GLOW/GCB/MCB/AUX: size each fuse down from 3 A.
