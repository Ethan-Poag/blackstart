# pcb_v4 progress

## Checkpoint 1 (2026-10-25 01:20 HST): placed, planes, critical power fan-out
- All 1167/1167 footprints placed by `place_v4.py`, connectivity-driven, with decaps at their pins.
- Netclasses, plane zones and 1,111 plane fan-out vias added. 10 pads had no room: isolator U69/U70 GND pins at the barrier, U21.F4 and D67.2. Those are left for hand or autorouting.
- DRC errors: 2. Both are HV_LINE 1.5 mm clearances in the HV divider strings (R469/R470 and R464/R422), which need a nudge. Unconnected: 499 (the report is capped at 499).
- Freerouting run 1 on the remaining signals is in progress.
- **Still not done:**
  - hand-routed diff pairs (ETH, USB, LVDS, DSI)
  - crystals
  - ADE9000 SPI and isolator links
  - 600 V divider traces

  They are currently left to Freerouting, which gives no impedance or length control.

## Milestone 1 — refined placement + HV rules (2026-10-25)
- refine_v4.py re-seats Y1/Y2/Y3 + load caps next to their IC pins and lays the 8 x 4-resistor 600 V divider strings (hv.py) in a line from terminal toward the ADE9000 input.
- HV spacing (Ethan's decision), implemented in genctl_v4.kicad_dru: 3.0 mm on OUTER layers for full-600 V HV_LINE copper; 1.5 mm between series divider nodes (HV_LINE_DIV) and on inner layers. Small manual nudges (R446, R425, R462) cleared the last 2 errors.
- **The HV creepage/clearance values have NOT been verified against IEC 60664-1 / UL 61010 / the actual pollution degree and overvoltage category. They need professional review before fabrication.**
- +3V3_SAFE stays on inner layer 3 (PWR). Panel jacks left as placed; a small jack daughterboard is recommended (see ENCLOSURE_DFM).
- DRC: 0 errors, 499 unconnected (unrouted). Fanout had no room for 15 pads (listed in route_v4 output).
