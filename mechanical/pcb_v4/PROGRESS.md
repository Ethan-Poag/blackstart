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

## Milestone 5 (2026-10-25 ~11:00 HST): relief, critical re-route, DRC clean-up, Freerouting attempt
Board: **genctl_v4_handrouted.kicad_pcb**, opens in plain KiCad 9 with no plugins.
- **Relief (relieve_v4.py):**
  - 23 small passives near U21/U9/U10 moved from B to F.
  - DNP REFCLK oscillator Y4 + R531 + C286 added on F.
  - HV divider resistors reassigned among their existing slots (hvslots_v4.py). Total string length went from 819 to about 606 mm. Line-side resistors are kept more than 9 mm from the ADEs.
  - ADE GND pins stubbed into EP41.
  - The barrier rules (13 mm, slots) are unchanged.
- **Critical routing:** best result is 86 of 91 critical jobs OK. The 5 that hard-fail:
  - AC_SCK, BUS_VC_P, ADE_XO
  - LVDSC_P, LVDS0_P (U21 C9/F9 escape)
- **LVDS1_P is also effectively open.** The report marks it OK, but it has only 0.6 mm of copper (a false hit at the dog-bone). That makes **6 open critical nets**.
- Negotiated-priority ordering was tried and rejected: the best pass had 9 failures, against 5 for the previous order. Passes oscillate between the U21 LVDS-escape set and the U72 SPI/XTAL set. This needs a manual pass or placement change.
- **Unrouted / routed %** (pcbnew, after zone fill):
  - 1809 of 2936 pad connections are unrouted, so **38.4 % routed** overall.
  - Most of the remainder is plain low-speed nets.
  - 3888 track segments, 1267 vias.
- **DRC (kicad-cli, errors only): 0 violations.** It was 36 before the clean-up:
  - **16 via/annular/drill errors.** Root cause: handroute rewrote the .kicad_pro and dropped the 0.30/0.15/0.075 board minimums needed by the U21 via-in-pad. The minimums are restored; outside U21 the .dru still enforces 0.4/0.2/0.1.
  - **4 Y4/C54 errors** (short, mask bridge, 2 courtyard). Fixed by moving C54 1.3 mm up.
  - **3 genuine HV 3 mm errors.** GEN_N/GEN_L1 pads were 2.63-2.98 mm from the *low-voltage* tap nodes R439/R425-Pad2 (Default class, so 3 mm applies) and from the CT4 secondary. Fixed by moving R443, R422, R439 and R425 by 0.15-0.45 mm with their tracks dragged.
  - **13 clearance errors** that were 0.005-0.02 mm short. Fixed by via/segment nudges, the ADE_CS1_N exit from U7.28, and a zone refill.
  - Scripts: drcfix_v4.py, drcfix2_v4.py.
  - Unconnected count unchanged by the fixes (1810 → 1809).
- **Skew** (track length, P vs N, measured on the board): DSI C/D0-D3, ETH0-3, LVDS2/3 are all ≤0.05 mm, so track-only skew is within 0.15 mm.
- **Skew including vias: NOT met.** Via counts differ within pairs:
  - DSI_D0 3/10, DSI_D2 2/6, DSI_D1 2/5, USB31 2/4, ETH1 4/6, LVDS2 1/3, others ±1.
  - At about 1.6 mm per through-via that is up to about 11 mm electrical skew on DSI_D0.
  - Needs coupled re-routing in KiCad's interactive diff-pair router.
  - The GEN/BUS V± analog inputs have 10-14 mm skew; that does not matter for them.
- **Freerouting** (low-speed remainder):
  - Hand routes were marked protect, and the run had a hard 60-minute timeout (09:56-10:56 HST).
  - It **timed out (exit 124) without writing an SES.** It logged no completed pass on 2784 unrouted items, so **no Freerouting result was imported.**
  - Next try: split by region/net subset, or run longer on a bigger machine.
  - Note: the DSN still contained the open critical nets. Delete any of their Freerouting tracks on import.
- **Plot:** routed_tracks_v4.png (tracks only, planes not shown), from plot_routes_v4.py.
- **Open safety item for review:** HV parts may sit under the display (about 3.5 mm air gap on the F side), so HV parts must stay on B. The 600 V spacing rules still need professional compliance review.
- **Naming:** the DSI83 bridge is **U21** on the board. U19 is a TPS2553.

## Milestone 6: LV re-placement and re-route, plus review C1 (2026-10-25)
Rules and sources: LAYOUT_RULES.md (AN4938, AN2867, the TPS56637/LM74800 datasheets, and /workspace/research/layout_notes.md). LM74800 U1 RTN pad 13 stays floating. HV 3.0 mm outer / 1.5 mm inner rules and the U21 via scoping (0.3/0.15/0.075 only inside U21; 0.4/0.2/0.1 elsewhere) are unchanged. The .kicad_dru is byte-identical to the one used for DRC.

**Before/after** (metrics measured with `GetConnectivity().GetUnconnectedCount(True)` after zone fill, and `audit.py`):

| metric | before (da8bdeb) | after (M6) |
|---|---|---|
| unconnected | 1805 | **1119** |
| routed % = 1 - unconnected/2936 | 38.52 % | **61.89 %** |
| KiCad DRC errors (severity error, project .kicad_pro/.kicad_dru) | 0 | **0** (drc_v4_m6.json) |
| decap/power passive to owner pin: median / p90 / max | 4.8 / 23.3 / 131.6 mm | 2.2 / 6.2 / 81.3 mm |
| decap/power > 5 mm / > 10 mm | 65 / 31 | 19 / 6 |
| signal passive: median / p90 / max | 6.2 / 34.3 / 164.4 mm | 3.5 / 10.4 / 63.3 mm |
| signal passive > 5 mm / > 10 mm | 378 / 199 | 155 / 64 |
| locked tracks/vias | 3108 | 3108 (identical count) |
| footprints | 1169 | 1181 (+U77-U79, R113, R532, R533, C287-C292) |

Full audit outputs: audit_before_m6.txt and audit_after_m6.txt. The new tracks plot is routed_tracks_v4_m6.png (also at layout_prep/out/routed_tracks_v4.png).

**What moved:** 470 R/C passives (place_lv.py and place_new.py). No IC, connector, isolator, terminal or HV-class part moved, and no part changed layer (checked by comparing positions against da8bdeb). Outline, holes, keepouts and locked copper were not edited. HV parts stay on B.Cu.

**Pipeline** (scripts are in this folder):
1. place_lv.py, then fanout_lv.py.
2. route_rest.py: grid A*, MG=12, VC=60.
3. sync_c1.py and fixcu_c1.py: netlist sync for C1, then removing stale DISP_SDA copper.
4. place_new.py.
5. filldrc.sh: copies the project .pro/.dru first, then fill and DRC.
6. drcfix.py: removes only the unlocked router item in each DRC violation. It removed 99 items in one pass, which gave DRC 0.

heal.py (dedupe plus gap bridging) was tried and rejected: no connectivity gain. The `prune.py` dangling-prune was abandoned (it over-prunes T-junctions) and was not used.

**C1, review change (schematic, commits eca5dac and 31598c6):**
- DSI83 1.8 V I/O is level-translated; CM5 GPIO_VREF stays 3.3 V.
- U77 PCA9306 handles the I2C, with R119/R120 2.2k to +1V8_DSI and R532 200k / C287 100 pF on VREF2.
- U78 SN74LVC1T45 translates EN, with R533 47k pulldown on the 1.8 V side.
- U79 SN74LVC1T45 translates IRQ, with R115 100k pulldown on the 1.8 V side.
- REFCLK: R113 10k to GND is fitted (datasheet p.5). Y4/R531/C286 are a DNP footprint option. No buffer is fitted.
  - The stock Linux sn65dsi83 driver always uses the DSI clock. Fitting Y4 needs a driver patch and an oscillator with edges of 1 ns or less (the ASDMB is 1.8-3 ns).
  - The DSI HS clock must be exactly 3x the pixel clock, and CM5 clock rounding must be confirmed on hardware (DESIGN_NOTES Rev j).

**Unverified or unmet:**
- 1119 connections are still unrouted (38 % of 2936). DRC reports them as "unconnected items" (capped at 499 in the report). The board is NOT fab-ready.
- drcfix removed 99 router segments, so some nets that were routed before are open again (unconnected went from 1064 before DRC fix to 1119 after).
- The router output still contains 219 exact duplicate segments. They are harmless (same net, same geometry) and DRC-clean.
- Diff-pair skew and impedance were not re-measured in M6. The locked pair copper is unchanged, so the M4 figures still apply.
- HV clearance values are still not certified against IEC 60664-1 / UL 61010.
- The new C1 parts were placed on B near U21 but are not yet fully routed.
- **The Quilter package (job 6ade7072) is now STALE.** It predates the C1 netlist and the M6 placement and must not be used.


## Milestone 7, step 1 (2026-10-25): CR1 CT clearance, J28/J29 slots, CR2 passive moves

**Done:**
- CR1: BUS_VC_TAP and GEN_VC_P ripped (71 locked items, flagged: locked copper touched) and rerouted with a CT-pad keepout (route_m7.py, CTKEEP). Min distance to T1-T4/J30 pads: BUS_VC_TAP 0.117 -> 3.134 mm, GEN_VC_P 0.184 -> 6.177 mm (ctclr.py).
- J28/J29 inter-pin slots widened 1.5 -> 2.0 mm and lengthened (x 2.72-11.50 -> 2.00-12.50) per sheet. Outline edited (flagged). 11 locked BUS_L1 In2 segments crossing the new slot were ripped and BUS_L1 rerouted.
- CR2: mover.py moved 109 passives next to their owner pin (plan from reviewer decap.json + L2/L3/L4/C17/C18/R506). 44 found no legal closer spot (incl. L2, L4, C17, C18, C3, C4, C136, C138); HV-class parts (R462/R448/R455/R443) not moved. C17/C18 owner taken as Q6 (LM5176 output FET), an inference.
- DRU: sheet rules added at severity warning. LAYOUT_RULES.md section 4 added.

**Metrics (before f03c57a -> after):**
- Unconnected (unc.py): 1119 -> 1277; routed 61.89 % -> 56.51 %. Worse because moved parts lost their copper; bulk re-route not yet done.
- DRC errors (kicad-cli, severity error): 0 -> 0. Footprints 1181 -> 1181. Locked tracks+vias 3108 -> 2899 (ripped CR1/BUS_L1 + moved-part copper).
- place_audit.py decaps median/p90/max 2.2/6.2/81.3 -> 2.3/6.5/81.3 mm; signal 3.5/10.4/63.3 -> 3.5/8.2/63.3 mm; signal >10 mm 64 -> 48.
- Reviewer decap.py (pad edge to owner pin): decaps 1.61/15.5/78.31 -> 1.47/6.08/78.31 mm, >5 mm 39 -> 20, >10 mm 21 -> 4; signal 2.95/31.9/140.32 -> 2.68/12.26/216.69 mm, >10 mm 138 -> 73. Signal max rose because R506 now sits at SW14 (its LED end); the TCA9555 end is inherently far.
- hvrules.py: hv-hv 26 -> 21 net-pairs (592 -> 477 raw); hot-edge 16 (J28/J29 pads 6.94 mm from left edge); hot-SELV 2 groups (R471 9.0 mm from U70.12, an unconnected comparator output).

**Unmet / unverified:**
- 21 HV net-pairs still below the sheet (divider chains not re-spaced per phase; planned together with the new MOV footprint).
- J28/J29 pads are 6.94 mm from the board edge (< 8.0 mm). Fix needs a connector move, frozen by BCR-7: lead decision.
- Slot-end creepage ~6.9 mm (right) / 7.15 mm (left) between adjacent phases: meets 6.6 mm only by ~0.3 mm, marginal against fab tolerance.
- NOT fab-ready.

## M7 WIP step (2026-10-25 ~18:30 HST, branch m7-wip only, NOT for master yet)
Board = /workspace/m7/u25 (from t20 = 32b12c7 board).

**Measured (before d151ff7 -> t20 -> now):**
- Unconnected (own unc.py, KiCad GetUnconnectedCount after zone fill): 1277 -> 1280 -> 973; routed 56.51 % -> 56.40 % -> 66.86 %.
- HV opens (hvopen.py, pad islands): 17 -> 20 -> 9.
- HV pairs, my hvrules.py: 21 net-pairs -> 0 -> 0. Reviewer hvsheet.py (m7): 28 pairs (21 chain) -> n/a -> 13 pairs (0 chain); the 13 are 191-382 V divider-node vs CT/GND_AC/BUS_VC_N gaps that my checker does not model -> NOT 0 by the reviewer's method.
- hot-edge<8 mm: 48 groups (J28/J29 pads 6.94 mm on all layers = accepted, no edge plating) + GEN_L1 via 7.675 mm (open item).
- KiCad DRC errors with the repo .kicad_pro: 0 -> 0 (warnings 860 -> 891, mostly track_dangling/copper_edge_clearance/silk). With the stricter work .kicad_pro (min hole 0.2/via 0.35) 4 errors: two pre-existing DSI83_REFCLK vias 0.3/0.15 at (161.5,126.7),(162.0,125.65), also in d151ff7. Footprints 1181 -> 1181. Locked tracks 2899 -> 2541 (earlier M7 rips, already flagged).
- Reviewer unconn.py crashes (GetConnectedItems SWIG) - not measured that way.

**What changed:**
- Router fix (route_m7.py): source = pads + own copper actually connected to them (3D label) - stub bug gone; J28/J29 multi-pad pins now picked by position; every run reports uf-verified completion (router "ok" matched verified on all HV runs).
- fixends.py: ~3300 track ends stopping <=0.35 mm short of their own pad (mostly PRE-EXISTING copper, incl. d151ff7) joined to the pad centre; 30 joins that DRC flagged were dropped (dropbad.py). => Earlier unconnected/"OK" counts were inflated by these near-misses; this, not new routing, is most of the 1280 -> 973 gain.
- Moved (HV area, B side): R429, R448, R456, RV6 (slot-corner rule on own pads), R422, R423, R449 (courtyard overlap with new MOVs), RV3 +1.5 mm y, RV4 +1.25 mm y (RV4/RV5 overlap). R436 move tried and reverted (it caused HV pair fails). Unlocked copper of the affected HV nets ripped and rerouted with HVSHEET rules. Locked HV items touched in this step: none.

**Unmet:**
- RV3 (GEN_L3-GEN_N MOV) sits at y~154 in the BUS area since d151ff7 = misplaced; no legal spot in the GEN HV area found by search (needs a placement decision). 9 HV opens remain incl. GEN_L1 (its divider chain R422-R425 walls J28.1 off from R422.1/RV1), GEN_L3/GEN_N at RV3.
- Net-(R436-Pad2) B.Cu 3.55 mm from slot corner (13.5,27.2), own phase needs 3.62. 24 locked F.Cu segments = accepted deviations.
- Bulk low-speed router is NOT DRC-clean (test run gave 317 clearance errors) - not used.
- NOT fab-ready.

## 2026-10-25 ~6:20 PM HST — m7-wip: reviewer's 13 divider pairs fixed (layout executor)
Board only on m7-wip. Not fab-ready.

| metric | f16d8de | this commit |
|---|---|---|
| KiCad unconnected (pcbnew connectivity) | 973 | 965 |
| uf.analyze open (my method) | 943 | 935 |
| HV opens (hvopen.py) | 9 | 9 |
| reviewer hvsheet.py pairs | 13 | 0 |
| my hvrules (excluding accepted edge items) | 0 | 0 |
| DRC errors, repo .kicad_pro | 0 | 0 |
| DRC errors, working pro (min via 0.2/0.35) | — | 4 (the 2 DSI83_REFCLK 0.15/0.3 vias; still open) |
| DRC warnings | 891 | 891 |

What changed:
- Moved R487 (0.96, −0.80 mm), R478 (−0.17, −0.99), C275 (−0.71, −0.26) and R486 (−0.25, −0.43). None of them is locked. No connectors, holes, outline, rule areas or locked tracks were touched, and J30 was not changed. Footprint count is 1181.
- Ripped and rerouted copper near the flagged divider nodes: R448, R449, R456, R430-Pad2, GND_AC, BUS_VC_N, AC_IRQ_N and GEN_CTN_1. The R430 and R449-Pad2 copper was then restored from f16d8de. The Net-(R449-Pad2) via moved from y 99.205 to 98.855.
- fixends added 79 joins. 30 of them hit clearance DRC errors (all low-voltage nets) and were removed.

Still open: 9 HV opens (GEN_L3, GEN_N, BUS_N, BUS_L3 and others), the R436-Pad2 spacing (3.55 vs 3.62 mm), the GEN_L1 chain re-place and the rest of the queue.

### J28/J29 slot change (reviewer re-audit item a)
- d151ff7 had routed slots between adjacent J28/J29 pins at x 2.00–12.50 mm. They are now x 2.0–13.5 mm (2.0 × 11.5 mm), 1.0 mm longer toward the board interior.
- The change was made in 32b12c7 with slots.py/slotmove.py, following the reviewer's sheet. **Reason for the 12.5 → 13.5 extension: not recorded.** slots.py still contains the 12.5 value, and my notes give no reason.
- Copper that crossed the new slot area was ripped and rerouted in the u1–u6 steps. This mainly meant HV pad copper, and parts R429, R448, R456 and RV6 were moved off the slot-corner zone. I did not record an exact item list.
- This change exists only on m7-wip, not on master.

## 2026-10-25 ~6:30 PM HST — m7-wip: R436 slot-corner fixed; slot centres corrected in my tools
Board only on m7-wip. Not fab-ready.
- **Tool bug found:** my slot-corner tools (route_m7.py, slotmove.py, slotchk.py) used slot y centres about 1.0 mm off (28.2/35.81/43.44/78.01/85.63/93.25). The real centres, measured from Edge.Cuts, are 27.195/34.815/42.435/77.013/84.6325/92.252. All three tools are fixed. slotchk2.py is a new pad/track/via checker with the two-tier rule: other phases ≥7.1 mm from a slot corner, the slot's own two phases ≥3.62 mm. Earlier slot-corner results from my own tools are therefore unreliable; the reviewer's hvsheet.py uses the real outline and was unaffected.
- **R436:** moved +1.0 mm in x. **R424** (GEN_L1 chain) moved +0.5 mm in x to keep the 4.38 mm chain spacing to R436.1. Nets Net-(R436-Pad2), Net-(R423-Pad2) and Net-(R424-Pad2) were ripped and rerouted, and the router verified all 3 complete.
  - Before, slotchk2 found 5 unlocked slot-corner violations, all R436 pads and tracks; the worst was R436.1 at 2.64 mm vs 3.62 mm. After, there are 0 unlocked violations.
  - 1 locked item remains: a GEN_N F.Cu track at 3.594 mm vs 3.62 mm. It is one of the accepted locked F.Cu segments.
- **GEN_L1:** J28.1, R422.1 and RV1.1 are already connected (hvopen no longer lists GEN_L1), so the chain did not need re-placing for reach. No GEN_L1 via is within 8.0 mm of the edge on this board (checked with my hvrules and a via-to-Edge.Cuts scan). The 7.675 mm via from the earlier review no longer exists.
- **Metrics (measured):** KiCad unconnected 965, geometric 935, HV opens 9, hvsheet 0 pairs. DRC errors: 0 with the repo project file; 4 with the working project file (the 2 DSI83_REFCLK vias, still open); 891 warnings.

## 2026-10-25 ~6:45 PM HST — m7-wip: GEN_N partly joined, HV opens 9 → 7
Board only on m7-wip. Not fab-ready.
- **GEN_N:** J28.4, RV1.2 and RV2.2 are now one copper island. Routed with VC=2000; the run with VC=200 put a GEN_N via 2.23 mm from a GEN_L3-chain track, which breaks the 3 mm .kicad_dru rule, so it was discarded. The router now has an EXCL option to skip named pads.
- **Still open:**
  - R443.1 (GEN_N): not reachable under the HV rules.
  - RV3.1 and RV3.2: RV3 sits in the BUS area. Waiting for the RV3 study.
  - GEN_L3, J28.3 to R436.1: the inner-layer path reaches R436, but there is no legal via spot near R436.1.
  - BUS_L3, R462.1 / J29.3 / RV6.1: nothing reachable from R462.1.
- **Router limits found:**
  - Without HVSHEET=1, the router does not apply the slot-corner rule (a test route gave 13 violations), so HV nets must always be routed with HVSHEET=1.
  - The HVSHEET model does not include the .kicad_dru 3 mm "HV line outer" rule against divider nodes, so DRC is still needed on every batch.
- **Metrics (measured):** KiCad unconnected 963, geometric 933, HV opens 7, hvsheet 0 pairs, slotchk2 0 unlocked. DRC errors: 0 with the repo project file; 4 with the working project file (the DSI83 vias); 891 warnings.

## 2026-10-25 ~7:00 PM HST — DSI83_REFCLK vias: kept at 0.15/0.3 (0.2/0.35 does not fit)
- Trial: enlarging both vias to 0.2/0.35 caused 8 DRC errors (DIFF100 clearance 0.125 mm, hole clearance 0.18 mm, zone clearance 0.176 mm). Reverted; the board is unchanged.
- My working .kicad_pro had min hole/via 0.2/0.35; I set it to the repo values (0.15/0.30). Both files now agree, so the 4 working-file DRC errors are gone: DRC errors are 0 with either file. The fab note (JLC "smaller via" option) is in README.md.

## 2026-10-25 ~7:15 PM HST — .kicad_dru rule order fixed; four severities back to error
Rules/project files only; the board is unchanged.
- **Override bug fixed.** The 5.5 mm line-to-neutral rule used to match every pair of different HV nets. Because it came after the 6.6 mm phase-to-phase rule, KiCad applied 5.5 mm to phase-to-phase pairs too. Now:
  - the line-to-neutral rule only matches pairs where one net is a neutral (`_N`);
  - the 6.6 mm phase-to-phase rule comes after it;
  - no 600 V value was lowered.
- **New divider rule (warning).** Divider-chain nodes (HV_LINE_DIV) vs line copper, outer layers: 2.5 mm floor. The exact node-voltage requirement stays with hvsheet.py.
- **Severities back to error:** net_conflict, hole_to_hole, copper_sliver and isolated_copper, in the repo .kicad_pro (my working copy matches).
- **HV-sheet rules NOT raised to error (flagged).** Test-raised, they gave 379 errors, all false positives, because DRC cannot model slot creepage, chain membership or node voltage:
  - 199 edge errors: the internal J28/J29 slots counted as board edge;
  - 111 phase-to-phase: J28/J29 pin pairs across the slots, and the L-L MOV RV5's own pads;
  - 69 divider: nodes next to their own chain's line.
  They stay at warning, with the reason written in the file. hvsheet.py stays the arbiter, and it reports 0 pairs.
- **Result: DRC now shows 63 hole_to_hole errors.** They come from the severity change, not from a board change. They are real DFM items: vias too close to connector THT holes (J26 12, J20 8, J27 8, J21 6, J18 4, J1 4, …). They are on the fix list (DFM hole spacing). Warnings: 1008.

## 2026-10-25 ~7:35 PM HST — m7-wip: 63 hole_to_hole DRC errors fixed (0 left); fixends made safe
Board only on m7-wip. Not fab-ready.
- **Inherited, not new (measured).** I ran d151ff7 with today's rules. It has 70 hole_to_hole violations (35 unique pairs). The board before this fix had 63 (32 unique pairs). 31 pairs are common to both, and 1 is new: the duplicate BUS_L2 vias at (16.86/17.16, 56.81), which overlap with a 0 mm gap.
- **Fix (h2h.py):**
  - 31 of the 32 pairs are a via on the same net as a nearby connector through-hole pad (J18–J23, J26, J27, J1, J7, BAT_IN). Each of these vias has an inner-layer track that the pad doesn't connect to on that layer, so the via was moved away from the pad by 0.05–0.13 mm, with its tracks following, to give a ≥0.31 mm hole gap.
  - The duplicate BUS_L2 via was removed, and its tracks re-ended on the via that stays.
  - No connectors or holes were moved.
- **Correction to my 6:20 PM entry ("79 joins / 30 dropped").** The 79 is the union of two separate runs: 75 joins added on v3 and 4 on v8. 30 of those 79 were dropped by dropbad.py because they hit DRC errors. The fixends.py committed in f16d8de was not idempotent; it re-adds segments on every run (the reviewer measured 6607 and 6673 joins on repeat runs). My later working copy skipped ends that were already joined, but it was not committed. The committed fixends.py now:
  - is idempotent: a second run adds 0 joins (measured);
  - has a clearance guard: it never adds a join within 0.2 mm of copper on another net. On the current board it adds 7 joins and blocks 30, so the CRANK_EN–GND (0.008 mm) and TOUCH_INT_N–DISP_SDA (0.039 mm) near-shorts cannot come back.
- **Metrics (measured):** KiCad unconnected 963, geometric 933, HV opens 7, hvsheet 0 pairs. DRC errors 0 with both project files (they are now identical); warnings 1008.

## 2026-10-25 ~8:05 PM HST — m7-wip: reviewer d28ac0a items, RV3 decision recorded, C275 courtyard, GEN_CTB_1 crosstalk
Board only on m7-wip. Not fab-ready.
- **RV3 (Ethan's decision):** RV3 stays where it is, and the 13.1 mm growth is declined. Its two pads are **unrouted**: there is no legal 600 V path, because GEN_L3/GEN_N would have to cross the BUS HV copper. This is recorded in HV_ACCEPTED_DEVIATIONS.md item 3 (reason, plus the open item to HV-check its pads once routed) and as a builder note in README.md. bom/ is not my file, so I did not edit it; the RV1–RV6 BOM line may want a pointer to the note.
- **.kicad_dru rule-order proof (m7_wip/drutest.py):** on a copy, I added GEN_L1 and GEN_L2 0.5 mm F.Cu tracks 6.0 mm apart.
  - Current rules: DRC flags them, "HV sheet: line-line outer 6.6mm … actual 6.0000 mm" (warning by design).
  - Pre-fadf9e4 rules: no violation, because 5.5 mm won. This confirms the bug and the fix.
- **Five pads the reviewer listed as open (U7.47 PB11, U9.26 HDRA_SPI_MISO, U45.12 BST, U7.98 AUX2_MCU, J15.9 TOUCH_INT_N):**
  - On the current board, all 5 pads have own-net copper ending inside the pad.
  - Only TOUCH_INT_N is still open as a net (geometric check: 1 open). Routing it added 6 clearance and 4 hole_to_hole errors, so I discarded that batch; it stays open.
  - The near-shorts can't come back: the fixends clearance guard blocks every join within 0.2 mm of other-net copper.
- **C275/C276 courtyard overlap:** C275 moved +0.1 mm in x (its two track ends moved with it). No courtyard collision now (pcbnew courtyard check).
- **GEN_CTB_1 vs AC_MOSI:** I cut 5 GEN_CTB_1 segments (y 81–104) and rerouted them while keeping them away from AC_MOSI. My measurement: the F.Cu length within 1 mm of AC_MOSI is now 8.0 mm, and the minimum gap rose from 0.486 to 0.699 mm. The reviewer measured 19.8 mm before; mine counts duplicate segments differently, so the before numbers don't compare exactly.
- **Metrics (measured):** KiCad unconnected 963, geometric 933, HV opens 7, hvsheet 0 pairs. DRC errors 0 with both project files; warnings 1008.

## M7 gate checkpoints, 2026-10-26 (HST)
- **c41fce7** — BUS_L2 (12 segments) and GEN_L1 (1 segment) moved off the J28/J29 isolation slots on SIG_In2. Measured: KiCad unconnected 791, HV opens 7, hvsheet 0. DRC: project rules 0 errors / 0 shorts; repo pro without custom rules 0 errors (0 copper_edge_clearance) / 0 shorts. Co-located drills 0, dangling vias 12, geometric slot check 0.
- **212923c** — Q2 moved beside Q1 (260, 165, rot 270, B.Cu). The drains are joined by a B.Cu VBAT_DD pour (10 A; INFERRED 33–48 °F rise at an assumed 1 oz). HGATE goes U1.8 → Q2.4 through In2. A B.Cu VBAT_P pour covers the Q2 sources. Measured: unconnected 789, HV opens 7, hvsheet 0, DRC project and no-custom-rules both 0 errors (edge 0) / 0 shorts, co-located 0, dangling 12, slot check 0, viachk 0. Open: the VBAT_P 10 A feed from the Q2 sources to the loads is not sized yet.
- **Tight HV spots for the safety review (measured):**
  - BUS_L2 to BUS_N on SIG_In2: 1.5025 mm, only 0.0025 mm over the 1.5 mm inner rule (1.900 mm before the slot reroute).
  - BUS_L2 is 0.3025 mm and GEN_L1 0.355 mm from the J28/J29 slot walls.
  - The c41fce7 reroute was a deliberate HV copper change and needs qualified safety review.
- **KiCad 9.0.2 limit:** KiCad applies one edge-clearance value per copper item, so a 0.3 mm slot-wall error and an 8 mm outer-edge warning cannot both be expressed. Every attempt either dropped the outer warning or never fired the slot error, and KiCad also misses copper lying entirely inside a slot. The rules are enforced by verify.sh: the no-custom-rules DRC must show copper_edge_clearance = 0, plus the geometric slot check. The .kicad_dru is unchanged.
- **03cdea5** — D1 (TVS) rotated 90° to (258.0, 135.6) B.Cu, its GND vias moved with pad 2. VBAT_F erosion (mneck.py) B.Cu 1.705 → 1.999 mm; F.Cu 2.435 unchanged. Full gate passed.
- **815c989** — VBAT_F_PWR pour on PWR (priority 10; x 258.5–265.1 y 125.3–175.5 plus x 248–258.5 y 153.5–175.5). +3V3_SAFE island count unchanged (2, the R47.2 one pre-existing). Erosion F 2.435 / B 1.999 / PWR 2.435 mm. Full gate passed.
- **(this commit)** — VBAT_P parallel F.Cu pour VBAT_P_FCU_PAR (x 224–251.6, y 134–163.5) + 65 stitching vias (0.6/0.3) to the In2 VBAT_P plane. In2 FEM (fem.py, F pour treated as ideal — INFERRED optimistic): Q2 sources→Q3 path 2.531 → 0.789 squares; peak-density effective width 2.59 → 3.45 mm at (252.08, 156.43). Full gate passed; GND/+3V3_SAFE/VBAT_P island counts unchanged.

### Known current limits (IPC-2221, 10 °C / 18 °F rise, 1 oz outer, 0.5 oz inner — copper weights INFERRED, no stackup in file)
- **VBAT_F F1→Q1:** erosion necks F 2.435 + B 1.999 + PWR 2.435 mm → ≈4.56 + 3.95 + 1.38 = **≈9.9 A continuous** (INFERRED). Short of 10 A. Limited by B-side fanout vias (UVLO/HGATE/GND) in the F pour, the HGATE via at (262.6, 158.8), and the VBAT_P_Q2S via field.
- **VBAT_P Q2→Q3 (In2 hop to the new F pour):** peak-density width 3.45 mm on 0.5 oz In2 → **≈1.8 A by IPC internal** (INFERRED, IPC internal is very conservative for planes). Not a 10 A path.
- Builder options: 2 oz outer/1 oz inner, or a lower system rating. Not hidden; open.
- **(crank/fuel drains)** — CRANK_DRN and FUEL_DRN F.Cu+B.Cu pours (priority 3; hull of shunt pad 2 + both FET drain tabs, FET source/gate side excluded) + 13/24 stitching vias. Erosion (mneck.py, F terminals = 3 mm halo of B pads, INFERRED): CRANK R303→Q47 B 4.05 mm; R303→Q48 F 6.60 mm (B split by a crossing track); FUEL R297→Q45 B 6.57 mm; R297→Q46 F 4.57 mm. IPC-2221 1 oz ext 10 °C: 6.6 / 9.4 / 9.4 / 7.2 A per branch. Each pair is two FETs in parallel, so ~7.5 A per branch at 15 A total (INFERRED even split). The full 15 A at the 2512 shunt pad needs 12.6 mm at 1 oz: **not reached** (known limit; the 30 A inrush is a short pulse, not rated here). Was 0.15 mm tracks.
- **(output widening, partial)** — widen.py: tracks of AUX1–10/GCB/MCB/GLOW *_OUT stepped up toward 0.8 mm (2 A, IPC 1 oz ext 10 °C INFERRED) and +5V toward 2.7 mm (4.7 A), only where ≥0.25 mm to other-net copper on the same layer; 582 of 734 segments widened. Length at target: outputs 12–71 %, +5V 11 %. **Every output still has 0.15 mm bottleneck segments (≈0.5 A IPC) and +5V a 0.50 mm one (≈1.8 A): not yet 2 A / 4.7 A paths.** Needs rerouting at the pinch points.

## M7 buck move (5 V TPS56637 U3 group into Mechanical box, B.Cu x224-235 y53.3-67.8)
- Moved U3 (227.7,64.0,180), C33/C25 (225.02,60.05/63.9,-90), C34/C26 (227.8,59.3/61.28), C23 (227.2,66.8), R17 (230.1,66.28,-90), R13/R14/R19/R15/R16/R18 east column x233.45 y59.08..66.93. Courtyards inside box (x224.0-235.03 courtyard, >=2.0 mm from shell post 3 edge); no part in J10 strip x224-226 except 0805 caps C33/C25 (not tall). L2 not moved.
- Rip-up: local buck nets only (EN, FB, SW, BOOT, PG_5V, MODE_5V, C24-Pad2, NC) + dangling +5V/GND/+3V3_SAFE remnants at old site (incl. R15.2 GND via at 251.69,150.64 - removed). BAT_IN/VBAT_F pours and widths untouched.
- USB31 pair NOT rerouted: DP 43.504 / DM 43.489 mm, skew 0.016 mm, width 0.15, gap unchanged (identical before/after). Transition vias (231.46,56.91)/(232.06,57.51): nearest GND via 4.46/5.09 -> 4.00/3.74 mm. Nearest new same-layer copper to the pair 0.47 mm (>= previous min 0.345 mm CAN2_RX). New F.Cu crossings over the B.Cu pair are referenced through GND1 (impedance effect negligible - inferred).
- SW node track length 84.66 -> 21.54 mm (C23.2 -> L2.1, 1.2 mm wide, 2 vias). Input caps C25/C26/C33/C34 adjacent to U3 VIN with direct GND vias.
- VBAT_F erosion F/B/PWR 2.435/1.999/2.435 mm unchanged. VBAT_P In2-only fem.py: R 2.531->2.043 sq, w_eff 2.59->4.87 mm (~2.3 A IPC internal 0.5 oz, 10 C rise - inferred).
- +12V local groups 29->24; unconnected 771->765. Gate: DRC 0/0, no-dru 0 edge 0, HV opens 7, hvsheet 0, dangling vias 12, slot 0/1, viachk 0.

## M7 reviewer items after 80844d6
- (1) DRN necks by erosion (mneck.py, per path, no copper change): CRANK R303->Q47 B 4.05 mm (~6.6 A), R303->Q48 F 6.60 mm (~9.4 A); FUEL R297->Q45 B 6.57 mm (~9.4 A), R297->Q46 F 4.57 mm (~7.2 A). IPC-2221 external 1 oz, 10 C rise (inferred copper weight). Parallel FET paths -> ~16 A per channel only if current splits evenly (inferred); 30 A inrush not met as continuous rating.
- (2) widen.py CL=0.20 (>= board netclass clearance): 364 of 813 output/drain/+5V segments widened. Remaining 0.15 mm segments on power nets: CRANK_DRN 14, FUEL_DRN 14, AUX7_OUT 11, AUX2_OUT 11, MCB_CL_OUT 10, AUX5_OUT 9, AUX4_OUT 7, AUX9_OUT 5, AUX1_OUT 4, MCB_OP_OUT 4, GCB_CL_OUT 3, GCB_OP_OUT 3, AUX6_OUT 2, AUX3/AUX8/AUX10/HSE_OUT 1 each (was 60 DRN + ~103 OUT). They stay thin because no width >=0.20 fits with 0.20 mm clearance to neighbouring copper (pin escapes, between pads/vias). A 0.15 mm segment carries ~0.6 A (IPC ext 1 oz, 10 C, inferred) - known limit; DRN segments run in parallel with the DRN pours.
- GND islands: 29 groups on both ce06efd and 80844d6 (unchanged; not a new break). C33/C25: C_0805_2012Metric, model Capacitor_SMD C_0805_2012Metric.step offset z 0, scale 1; model file not installed on the box - body height 1.25 mm per KiCad library spec (inferred).
- (3) VBAT_F PWR feed: F1.2 pad copper exists only on F.Cu/B.Cu (pad layer set), so the PWR pour cannot touch it without a footprint edit (not done). Instead added 65 VBAT_F 0.6/0.3 stitching vias inside the VBAT_F_PWR zone where F and B fills overlap (stitch.py, pitch 1.0): VBAT_F vias within 8 mm of F1.2 10 -> 35, in zone 35 -> 100. Feed scales ~5.8 A -> ~18 A by via count (inferred, linear). Erosion F/B/PWR unchanged 2.435/1.999/2.435 mm (erosion does not model via feed). GND 29, +3V3_SAFE 2, VBAT_P 63 groups unchanged.
- Buck follow-ups: SW stub at U3.6 (227.3,64.9)-(227.6,65.2) narrowed 0.6->0.3 mm: SW->BOOT pad clearance 0.134 -> 0.284 mm. SW reference planes: GND2 under B.Cu SW, GND1 under F.Cu SW continuous except 1.58 mm2 each = clearance holes around SW/ nearby vias (inferred from equal areas); no plane split crossed.
- Courtyard "overlaps" U3-C25/R17-U3/C34-C26: built courtyards (BuildCourtyardCaches) show 0 overlaps on ce06efd and 80844d6; reviewer misc.py falls back to footprint bbox (incl. pads) when caches are not built, which gives the 24->27. Not a real courtyard overlap; left as is.
- +3V3_SAFE track+via in box = R19.2 (PG pull-up) 0.1 mm stub + via to PWR plane, buck copper added in 80844d6. CAN2_RX untouched.
- GND 29 groups = isl.py (counts pour fragments); 29 on ce06efd and 80844d6 alike - counter difference, no new island.
- U3 +12V group: the whole +12V net has no tracks on the board (24 pad groups); nearest other +12V pads U15/C94 ~26 mm, main source U2/Q6 ~90-100 mm away. Not joined in this step (needs a planned +12V distribution route) - known open.
- HSE_OUT restored: adae893 width pass had widened 9 HSE_OUT segments (0.15 -> 0.25..0.8 mm); restored to 0.15 mm (80844d6 widths). No other HSE*/LSE*/OSC*/XTAL*/CLK* net was touched (segment diff k2 vs q0). Stray C (parallel-plate, copper area incl pads, FR4 er 4.3, 0.2 mm to adjacent GND plane - stackup inferred): HSE_IN 0.577 pF unchanged; HSE_OUT 0.597 -> 0.983 (adae893) -> 0.597 pF. Y1 X322525MOB4SI CL=12 pF (schematic Note field); C61/C62 18 pF (DESIGN_NOTES, assumed): 18||18 series = 9 pF + strays + MCU pin C; adae893 shifted effective CL by ~+0.1 pF (inferred), now back.

## M7 LM5176 output caps (review e65), on 90d8a8e (G_U18 merge)
- [CORRECTED below: this net-only check missed 36 reverted RV1-RV6/R297/R303 fields] Schematic (tools/design.py + regenerated sheets): C293-C295 22u 1206 (C12891) + C296 100n 0603 (C14663) on +12V/GND, power sheet, fixed refs. Netlist diff vs HEAD: only +12V and GND gain C293-C296 (netcompare.py: 2 nets changed, 0 renamed). ERC 0 errors. BOMs: docs/genctl_bom.csv (22u 18->21, 100n 106->107), mechanical/bom.csv (21 / 108), bom/power_bom.csv 12V bus ceramics 6->9 (edited in place; a full kicad-cli re-export also differs on pre-existing stale rows, e.g. RV1-RV6 and C286 DNP, so not regenerated wholesale).
- Board: C293/C294/C295 at (249.6, 140.85/143.2/145.55), C296 at (253.0,145.6) rot 90, all B.Cu, 6.2-10 mm from Q6.5 (centre to pad edge, measured). +12V: 1.0 mm B.Cu bus over C293-C295 pin 1, rt.py C295.1 -> F.Cu +12V trunk (251.0,150.5) 0.6 mm 6.14 mm 1 via; C296.1 -> trunk 0.4 mm 4.95 mm 1 via. GND: 8 new 0.6/0.3 GND vias (2 per cap) with 0.4 mm stubs into GND1/GND2.
- Pours (zarea.py g18 -> this): VBAT_P In2 20979.2 -> 20947.8 mm2 (18 pieces), VBAT_P F 652.9 -> 649.0, VBAT_F F 719.0 -> 716.9, +3V3_SAFE PWR 42187.0 -> 42179.1 (1 piece), GND1/GND2 -1.5 each (1 piece). Piece counts unchanged. Area loss = via antipads/new +12V F stubs.
- Duplicate stacked +12V vias removed at (243.6,149.2) and (147.875,64.175) (exact duplicates, same position/size).
- Q6 drain-pad +12V vias: distinct positions are (242.2,148.0) and (243.6,149.2) (the latter was the duplicate pair); both sit in B.Paste windows. Not moved: they are the drain's F.Cu/PWR feed; relocating needs reworking the F trunk stubs. Free site seen just outside the pad at about (246.3,149.3) (~0.65 mm to ROUTER_12V_EN, ~1.5 mm to VBAT_P via, hand-measured). Fab note: tent/plug these vias or reduce paste.
- U2.24 BIAS: schematic ties it to +12V (VOUT), board leaves it open (no legal path without touching BB_BOOT1/BB_HDRV1 or committed pours; nearest +12V copper 7.31 mm). Schematic/board MISMATCH, known; BIAS open is functionally OK per LM5176 DS (VCC from VIN). No 0.1 uF BIAS cap in schematic.
- Gate: DRC project 0 errors, no-custom-rules 0 errors with copper_edge_clearance 0 (KiCad default rules with no .kicad_pro: 14 copper_edge errors, re-measured by the reviewer on 0ee8934, /workspace/review/0ee/master_gate_check_0ee8934.md, with --all-track-errors. Project rules: 0 copper_edge errors but copper_edge warnings at the DRC report cap: 200 per that report with --all-track-errors, 199 in my own 0ee8934 DRC run without that flag), unconnected 664, HV opens A 7 / B 23, VBAT_P opens 70 / 23 pieces, dangling vias 12 (same set), hvsheet 0, slot 0 / corner 1 (inherited), VIACHK 10 bad 0, courtyards (KiCad polygons) 0, islands GND 29 / +3V3_SAFE 2 / +5V 13 / VBAT_P 63 / VBAT_F 2 / +12V 4.

### Correction (review c65 of c657c59)
The c657c59 note "Netlist diff vs HEAD: only +12V and GND gain C293-C296" was incomplete: that check (tools/netcompare.py) compared nets only and missed field/footprint changes. Regenerating from tools/design.py had silently reverted the manual schematic edits of 32b12c7/7eaa27d: RV1-RV6 TMOV20RP460E (LCSC C3260792, Littelfuse TMOV20RP460EL2T7, fp genctl:TMOV20RP_P7.5mm_inline) went back to V20E385P (C1527447, fp Varistor:RV_Disc_D21.5mm_W7.5mm_P10mm), and R297/R303 Vishay WSLP25121L000FEA (C844705) went to C2933264 (36 field diffs).
Fix: design.py now emits the 90d8a8e values for RV1-RV6 and the TPS48100 shunts (R297/R303); schematic regenerated. A full field diff of all 11 sheets (every property, lib_id, dnp, in_bom) against 90d8a8e shows 0 field diffs, the only change being C293-C296 added. Netlist vs 90d8a8e: only the +12V and GND nets differ (C293-C296). ERC 0. Board RV1-RV6/R297/R303 footprints match the schematic footprint fields (the board stores R297/R303 as R_2512_6332Metric without the library prefix). The full field diff (90d8a8e vs regenerated) found no other reverted fields. .kicad_pcb byte-identical to c657c59.

### LM5176 compensation (review c65 / Enginerd)
- R8 (Rc, BB_COMP to BB_COMP_RC) changed from 22.1k to 4.7k 0603 1%: UNI-ROYAL 0603WAF4701T5E, LCSC C23162 (read from the LCSC product page). Changed in tools/design.py, docs/genctl_bom.csv and mechanical/bom.csv. bom/power_bom.csv has no R8 row. C11 33n and C12 220p are unchanged.
- Board: the R8 footprint is already R_0603_1608Metric, so no copper change. The board R8 Value text was stale at 22.1k; RESOLVED in 0ee8934 (Value text set to 4.7k, one text line changed, no copper).
- The 12 V load of about 3.7 A is an ASSUMED value. Ceramic derating is ASSUMED. The compensation is MODEL-ESTIMATED. Only a Bode measurement confirms stability; see docs/BENCH_12V_TEST.md.
- C17/C18 (470 uF) are connected to +12V/GND in the schematic and are open only on the board (not routed).

### Smallest copper gap (review 0ee)
- The board-wide minimum gap is 0.1016 mm (B.Cu, U4-FB to GND), the same at 14c9c43 and 90d8a8e, per the reviewer's 0ee8934 report. The 0.1328 mm figure was only 90d8a8e's smallest NEW gap, not the overall minimum. Smallest gap for the C293-C296 items: 0.2177 mm (R97, B.Cu).
