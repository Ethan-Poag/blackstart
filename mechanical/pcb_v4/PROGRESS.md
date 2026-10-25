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
