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

**Fusing:** Genctl has no on-board output fuses. Every output (FUEL, CRANK, GLOW, GCB/MCB,
AUX1–10, ESTOP_TRIP) needs an external fuse fitted by the installer ahead of the relay or
solenoid, no larger than the output's maximum (15 A FUEL/CRANK; 2 A small outputs; 2 A
ESTOP_TRIP relay drive) and sized down to the real load. The 30 A battery fuse does not protect individual
outputs. Fit a flyback diode across every external coil. See docs/INSTALL_SAFETY.md. Not certified.
