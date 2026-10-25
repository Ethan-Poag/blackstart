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

## Milestone 2: critical nets hand-routed (2026-10-25)
- handroute_v4.py is a pcbnew-python and numba grid A* router: 0.1 mm grid on F.Cu, In2 and B.Cu, through vias, and clearances that follow genctl_v4.kicad_dru. handroute_iter.py reruns it up to 6 times with failed jobs moved to the front (rip-up and retry) and keeps the best pass.
- seat_iso_series.py: moved R413 to R419, the MCU-side isolator series resistors, out of the HV box (around x 58) to the LV side (x 75 or more). The placer had put LV parts on the HV side of the barrier, which was a real isolation bug.
- U21 (SN65DSI83, 0.5 mm BGA) uses 0.3/0.15 mm filled via-in-pad. The board-setup via minimum is lowered for this, and genctl_v4.kicad_dru still enforces 0.4/0.2 mm everywhere else.
- All hand-routed tracks and vias are LOCKED. In the Specctra DSN they are marked (type protect) so Freerouting cannot move them.
- Result: 75/91 jobs (nets or pairs) fully routed. Partially routed or failed: GEN_VA_N, ADE_XO, AC_RST_N, LVDS1_P, LVDS2_P, LVDSC_P, DSI_D0_P, DSI_D1_P, DSI_D2_P, AC_MOSI, DSI_D3_P, Net-(R455-Pad2), Net-(R471-Pad2), BUS_VB_P, Net-(R464-Pad2), ETH2_P.
- Pair method: P is routed first. N then follows P at gap+w using a distance-band cost. This is not a true coupled router, so coupling breaks near vias and pins. No serpentine length tuning has been done yet. Intra-pair skew (mm):

| pair | ok | P len | skew | vias P/N |
|---|---|---|---|---|
| LVDS1_P | False | 0.0 | 39.37 | 0/1 |
| LVDS2_P | False | 0.0 | 39.34 | 0/2 |
| LVDSC_P | False | 0.0 | 0.0 | 0/0 |
| DSI_D0_P | False | 0.0 | 120.53 | 0/2 |
| DSI_D1_P | False | 0.0 | 120.21 | 0/2 |
| LVDS3_P | True | 42.52 | 1.84 | 1/1 |
| DSI_C_P | True | 119.93 | 0.62 | 2/2 |
| ETH3_P | True | 68.19 | 1.64 | 0/4 |
| DSI_D2_P | False | 0.0 | 119.4 | 0/4 |
| DSI_D3_P | False | 0.0 | 119.24 | 0/2 |
| ETH1_P | True | 62.8 | 1.72 | 2/6 |
| USB31_DP | True | 45.96 | 3.19 | 2/5 |
| LVDS0_P | True | 41.47 | 3.49 | 1/5 |
| USB30_DP | True | 143.22 | 0.14 | 4/5 |
| ETH0_P | True | 56.19 | 4.46 | 3/5 |
| ETH2_P | False | 77.07 | 9.02 | 4/3 |

**These skews are far above the usual targets (around 0.1 to 0.15 mm intra-pair for USB, DSI and LVDS). Before fab, every pair needs coupled re-routing and tuning in KiCad's interactive router (Route → Differential Pair, Tune Skew).** The LVDS and DSI escape from the U21 BGA is the bottleneck.
- DRC on genctl_v4_handrouted.kicad_pcb: see drc_v4_handrouted.rpt.

## Milestone 3: U21 (DSI83) BGA escape (bga_escape_u21.py)
- The 0.5 mm-pitch 9x9 BGA cannot be fully dog-boned: a 0.45/0.2 via does not fit between 0.5 mm balls, and even 0.40/0.20 vias only fit on a checkerboard of interstitial sites. The result is a mixed escape:
  - 5 dog-bones at 0.40/0.20 (H4->G4, H6->G6, D8->D7, F8->F7, GND E4->E3). GND balls E4-F4-F5 are tied on B.Cu.
  - 8 via-in-pad: H2 (DSI83_REFCLK) at 0.30/0.15; H3, H5, H7, C8, E8, G8, E6 at 0.35/0.20.
- Cost: JLC POFV (epoxy-filled, copper-capped) via-in-pad is free on 6-20 layer boards but applies board-wide (from JLC pages found by web search in 2026; confirm when quoting). The 0.35/0.2/0.075 minimum is scoped to the U21 courtyard by the .kicad_dru rule "via min outside U21 BGA". Only the board-setup floor was lowered.
- DRC on genctl_v4_escaped: 0 errors (drc_v4_escaped.rpt).

## Milestone 4: critical re-route on the escaped board (handroute_iter, best of passes 0-3; pass 4 crashed)
- Base: genctl_v4_escaped. Result: genctl_v4_handrouted.kicad_pcb (pass 0 was the best for pairs). 1810 connections unrouted (pcbnew, after zone fill). KiCad DRC: 13 errors (drc_v4_handrouted.rpt). These are raster clearance shortfalls of 0.11-0.148 mm against 0.15 mm (DIFF/PWR next to existing GND/+3V3_SAFE vias), plus 2 DSI_D3_N hole-clearance errors at J10 NPTH. There are no HV 1.5/3 mm errors now.
- Skew (track length only, vias excluded), P/N mm:
  | pair | P | N | skew |
  |---|---|---|---|
  | DSI_C | 122.759 | 122.759 | 0.000 |
  | DSI_D0 | 122.255 | 122.255 | 0.000 |
  | DSI_D1 | 125.168 | 125.168 | 0.000 |
  | DSI_D2 | 122.918 | 122.918 | 0.000 |
  | DSI_D3 | 125.093 | 125.093 | 0.000 |
  | LVDS0 | 42.521 | 42.521 | 0.000 |
  | LVDS3 | 42.355 | 42.355 | 0.000 |
  | ETH0 | 66.929 | 66.929 | 0.000 |
  | ETH1 | 60.355 | 60.355 | 0.000 |
  | ETH2 | 81.267 | 81.267 | 0.000 |
  | ETH3 | 71.397 | 71.397 | 0.000 |
  | LVDS1, LVDSC | 0.6 (P not really routed: the router accepts a false 0.6 mm hit at the dog-bone pads) | ~40 | OPEN |
  | LVDS2, USB30, USB31 | failed | | OPEN |
- Still unrouted critical nets: LVDS1/LVDSC/LVDS2 P, USB30/USB31, AC_MISO, AC_MOSI, AC_SCK, ADE_SCK, BUS_VC_N, GEN_VA_N, GEN_VC_P, and divider nodes R437/R455/R456/R464/R471-Pad2. Passes trade one failure for another, so a congestion-aware ordering or a manual pass is needed.
- Freerouting pre-existing violations on the new DSN: 317, down from 396. The listed examples are same-net fixed-via pairs (e.g. Net-(R430-Pad2) via<->via), which is a Freerouting artefact and not a real spacing problem.
