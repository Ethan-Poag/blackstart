# Project Blackstart

Open-source diesel generator controller: STM32 safety MCU, Raspberry Pi CM5 for UI and connectivity,
dual ADE9000 metering (600 V class), 12.1" display, 12 backlit keys, external LTE router over Ethernet.

Status: schematic complete (ERC 0/0), layout and enclosure in progress. Prototype for the maintainer's own use first.

**Board status on the m7 branches (m7-wip):** gate checkpoint only — 789 KiCad-unconnected items (was 791), NOT fab-ready, NOT safety-reviewed, NOT certified (600 V sign-off by a qualified safety engineer outstanding).
Not certified. Do not rely on it for safety until independently tested and reviewed.

See DESIGN_NOTES.md, docs/, and LICENSING.md.

## +12V rail notes (m7-wip, 2026-10-26)
- The 470 uF bulk caps C17/C18 (CP_Elec_10x10.5) on +12V sit about 160 mm (C17) and 174 mm (C18) from the LM5176 output FET Q6. The builder may want to move them near Q6. No ceramic bulk sits at Q6: the nearest +12V caps are C96 100 nF (11.6 mm) and C14 1 uF (24.6 mm).
- Trunk limit (inferred, IPC-2221 10 C, 1 oz outer assumed): narrowest trunk segment 1.5 mm, about 3.2 A supported against roughly 3.7 A estimated for U3+U15.
- Still unpowered on +12V: U24.3/C125 (backlight boost), U2.24 (LM5176 BIAS), C17, C18.

**Fusing:** Genctl has no on-board fuses (PTCs on small signal outputs only). The DI bias terminals (J21.6, J22.1) are for the digital-input contacts only: no external loads. The power-box K3 glow contactor (ALEV100-B/-C) has polarised load terminals: observe +A1 / -A2 (see docs/INSTALL_SAFETY.md). Do not plug or unplug the 600 V sense plugs J7/J8 (J28/J29) live: isolate the source or open the metering fuses first. All fuses and the power relays sit in the separate power box (docs/INSTALL_SAFETY.md, review/bom_final/BOM_powerbox.csv). Every output (FUEL, CRANK, GLOW, GCB/MCB,
AUX1–10, ESTOP_TRIP) has its own power box fuse position ahead of the relay or
solenoid, no larger than the output's maximum (5 A standard blade for FUEL/CRANK, which are limited to 2.8 A; 2 A small outputs; 2 A
ESTOP_TRIP relay drive) and sized down to the real load. The 30 A battery fuse does not protect individual
outputs. The J23.1/2 E-stop/fuel feed has its own 10 A ATO/ATC fuse (>=58 V DC, >=16 AWG wire) at power box position F2, after the 30 A battery fuse; that feed is not behind the over-voltage cut-off and must stay within the declared supply range (9–32 V continuous, up to 36 V for at most 60 s), never above about 40 V. Hardware maximum per main output: interposing relay coil class <= 2.8 A (software trip 3.0 A); E-stop trip coil < 1.70 A (U68, R407 47k; bench-measure); where a circuit has a lower limit or a 2 A fuse, that lower limit governs. Fit a flyback diode across every external coil. Declared limit: 12 V and 24 V DC battery systems only, with the battery permanently connected as the buffer. Supply 9–32 V DC continuous; up to 36 V for at most 60 s (24 V jump-start), during which the controller may switch itself off; above its over-voltage trip point, 36.35-40.06 V (component tolerance), it disconnects its internal supply, and after such an over-voltage trip the supply must fall below about 33 V before the controller restarts by itself. Short ISO 7637-type pulses are tolerated. Load dump of any kind, including a centrally suppressed 58 V load dump (ISO 16750-2 Test B), is not supported and has not been tested. The fuel solenoid must be energize-to-run. See docs/INSTALL_SAFETY.md. Not certified.
