> Working plan, not certified; copper weights ASSUMED. Revision 4, 2026-10-27 HST (copied from review/cur/rail_plan.md).

> **SUPERSEDED (N4, m7-sch 3c, 2026-10-28):** the schematic has no on-board fuse; battery net BAT_IN; installer fits an external fuse <=10 A fast-acting, >=58 V DC in the battery lead. Every F1 / VBAT_F / "fuse F1 10 A" / "10 A ATO" mention in this file describes the as-built .kicad_pcb (which still carries F1 clips and net VBAT_F until the board update) and is historical; the VBAT_F copper becomes BAT_IN when the board is updated. The 10 A copper figures remain a copper-capacity record only.


# Rail plan and audit: Project Blackstart pcb_v4 (analysis only, no copper changed)

Board: `git show 3a8237f:mechanical/pcb_v4/genctl_v4_handrouted.kicad_pcb` (md5 3a67a66eef532ecd4e80807f4d596dc6), refilled in a scratch copy (`/workspace/m7/scen/railplan/refilled.kicad_pcb`). KiCad 9.0.2 pcbnew python. Scripts and raw outputs are in `/workspace/m7/scen/railplan/`: `stats.py`→stats.json (pads, track length per width per layer, zone fill area, vias), `comp.py`→islands.json (copper islands), `wpath.py`→wpath.out (widest path: the narrowest track on the best path from the source pad to each sink), `necks_c6c.py` (from /tmp/rv)→necks_c6c.out (erosion necks on the battery path), `misc.py` (BAT_IN neck, vias near pads), `prov.py`→prov.json (the commit where each track/via uuid first appears).

## Answer to Ethan's question
**No.** The power rails were not planned and placed by hand before any router touched them. Evidence:
- The first copper on most rails came from our own grid A* router: commit f03c57a "M6: LV re-place/re-route", PROGRESS.md:24 "handroute_v4.py is a pcbnew-python and numba grid A* router", and f16d8de "verified router". This applies to +5V, +5V_HU, +5V_TRIP, all 15 *_OUT, ESTOP_TRIP_OUT, FUEL, CHASSIS and the ground spurs. Afterwards widen.py widened what had room (ce06efd, adae893). PROGRESS.md:336 says many 0.15 mm segments could not be widened.
- +12V was routed one branch at a time with the same in-house A* router (route_m7), with the width and order chosen by a person (dc24539, 5e16d5b, f073f61, e650336; PROGRESS "rt exhausts at cl .18-.2"; PLAN_12V.md:2 "grid A* trial routes"). That is supervised auto-routing, not hand placement.
- Only the battery path (BAT_IN→VBAT_F→VBAT_DD→VBAT_P Q2→Q3) was built as a planned structure: coordinate-defined pours and stitching vias whose coordinates are in the commit messages (4aeee4b, b5637a5, 815c989, 46c4541, 212923c, 2c7a1b0, 47ab938, ae30af3). This happened after the router had already run.
- ROUTING_PLAN.md §7.2 lists the power batch as "OPEN — power batch" for crank/fuel, +12V, +5V, the outputs and ESTOP_TRIP_OUT. The plan exists. The structured execution has not been done.
- External autorouters did not touch the board. FreeRouting was killed with no SES (routing-lab STATUS 23:10, REPORT §2). The Quilter package is stale and was never merged (PROGRESS M6). The routing-bot merge G_U18 (90d8a8e) excluded every power net: v18/EXCLNET18.txt contains +12V, +3V3*, +5V*, VBAT_*, GND*, the *_OUT nets and others, and copper_diff reported "0 excluded".

Labels: HAND-BUILT = placed by a person in the GUI. SCRIPTED-HAND = our own scripts at coordinates a person chose. AUTO-ROUTED = an automatic path search (here our in-house A* router, not FreeRouting). UNROUTED = no copper. No rail's copper is evidenced as GUI hand-placed. The track files carry no locked flags or other provenance (not checked beyond uuid first-seen).

## Basis (state of knowledge)
- Stackup: none is defined in the board. ASSUMED outer 1 oz (1.378 mil, k=0.048) and inner 0.5 oz (0.689 mil, k=0.024). IPC-2221 I = k·ΔT^0.44·A^0.725 with ΔT 10 °C (18 °F) and A in mil². Outer: 0.15 mm 0.60 A, 0.25 mm 0.88 A, 0.3 mm 1.00 A, 0.4 mm 1.23 A, 0.5 mm 1.45 A, 0.8 mm 2.03 A, 1.0 mm 2.39 A, 1.5 mm 3.21 A. Inner 0.5 mm 0.44 A. Width needed (outer / inner): 1 A 0.30/1.56 mm, 2 A 0.78/4.07 mm, 2.55 A 1.09/5.68 mm, 3 A 1.37/7.11 mm, 3.7 A 1.83/9.5 mm, 4.7 A 2.54/13.2 mm, 10 A 7.19/37.4 mm, 15 A 12.6/65.5 mm (INFERRED, computed).
- Via basis: about 0.76 A per 0.3 mm drill via at 18 °F (10 °C) and 1.03 A at 36 °F (20 °C), INFERRED (our earlier basis, not datasheet). Vias needed = ceil(I/0.76) per layer transition.
- All vias on the board are through vias F.Cu–B.Cu (MEASURED; there are no blind/buried vias), so each "layer transition" is a through via. Sizes are 0.3/0.6 mm and 0.2/0.4 mm (the latter counted at the same 0.76 A here, which is optimistic, INFERRED).
- Layers: F.Cu, GND1, SIG_In2, PWR, GND2, B.Cu.
- "Path min" = widest-path bottleneck from the source pad (wpath.py, MEASURED). Zone fill is treated as wide there, so pour necks come from necks_c6c/tneck (erosion method).
- Islands = copper-connected pad groups from our geometric graph (comp.py, MEASURED by our tool, not KiCad's ratsnest). It agrees with the documented counts (+5V 13→12, VBAT_P many opens, GND 4 open pads R115/U70.2/R204/U21.H9).
- Current sources: [FPS] /workspace/review/cur/final_power_spec.md, [DN] DESIGN_NOTES.md, [DS] bom/design_spec.md, [RP] docs/ROUTING_PLAN.md (its [A] marks mean ASSUMED).

## Rail table (MEASURED unless marked)

| Rail (pads) | Current (source) | Copper by layer (MEASURED) | Path min / neck (MEASURED) → capacity at 18 °F (INFERRED) | Vias (MEASURED, all TH) → needed | Islands | Origin (evidence) | Verdict |
|---|---|---|---|---|---|---|---|
| BAT_IN (8) J1→F1 | 10 A (F1 10 A ATO, Ethan's requirement [FPS §1, RP §7.2]) | pours F 520.6 / B 517.7 mm²; 0.5 mm stubs F 12 mm | erosion neck J1→F1 F 5.40 / B 5.40 mm → 8.1 + 8.1 = 16.2 A (J1/F1 are TH, so both layers feed directly) | 61 (58× 0.3/0.6); 14 within 5 mm of J1, 8 of F1 → need 14 for full F↔B sharing: met at J1, not at F1 (8 = 6.1 A) | 1 | SCRIPTED-HAND (4aeee4b "pours F+B + 60 stitch vias", 86bdd44); 0.5 mm stubs AUTO-ROUTED (f03c57a 28, f16d8de 7 items) | OK |
| VBAT_F (11) F1→Q1 | 10 A [RP §8] | pours F 222 / B 261 / PWR 267 mm² | neck F 1.924, B 8.021, PWR 8.952 mm → F 3.84, B 10.82, PWR(inner) 3.54 A | 56 (0.3/0.6); 19 within 5 mm of F1, **3 within 5 mm of Q1** (necks tool: 4) → need 14 at Q1 for F/PWR to share | 1 | SCRIPTED-HAND (b5637a5, 815c989, 03cdea5, 46c4541 "+65 stitching vias", 47ab938, ae30af3) | **B alone 10.8 A, 8 % margin.** F and PWR only add about 2.3 A because only 3 vias reach Q1 |
| VBAT_DD (6) Q1→Q2 | 10 A [RP §8] | pours F 89.9 / B 114.1 mm²; 0.3 mm GND2 link 13.7 mm (C1 CVS, small signal) | F 7.538 / B 7.509 → 10.34 / 10.32 A (20.7 A combined) | 20; 16/16 near Q1/Q2 → need 14 | 1 | SCRIPTED-HAND (212923c, 2c7a1b0, 47ab938, a3e6bfa, ae30af3) | OK |
| VBAT_P (116) Q2→Q3 and onward | 10 A system [RP §7.2]; loads: 15 output switches at 1.99/2.49/2.99 A each, LM5176 input ≤3.56 A with limit [FPS §2–3] | pours F 1420.9 / B 763.2 / SIG_In2 20933.1 / PWR 403.2 mm²; B tracks 0.3 mm 104 mm | Q2→Q3 F 8.76 / B 4.535 → 11.53 / 7.16 A (B alone < 10 A); In2 neck 1.384 mm (RP Batch 1a) | 165 (110× 0.3/0.6, 55× 0.2/0.4); 23 near Q2, **14 within 5 mm of Q3** → need 14 (exactly met); U2.2/U2.3 2 vias | **61 (largest 27)**: [REV3 corrected] U49.12–14, U50.12/.13, U68.13/.14 and U5.4 ARE in the Q3 group, but only through 0.3 mm B tracks (1.0 A) or In2 necks 0.75 mm (0.59 A) / U68.14 0.55 mm (0.47 A); U2.2/U2.3, U5.3, U50.14, U68.12 and every other switch's VS pins are isolated | SCRIPTED-HAND pours (fd8485b, 2c7a1b0, 00f1e66); In2 stitch vias placed by route_m7 STITCH=1 = AUTO (NOTES.md:50; 0ac2ed5 114, 54ecc12 77 items) | Q2→Q3 meets 10 A only with F+B sharing. **Distribution to the loads is OPEN** |
| +12V (36) Q6→U3/U4/U15/U16/U24/L8 | 3.7 A ASSUMED [RP §5]; ~44 W realistic [FPS §2] → 3.7 A at 12 V (INFERRED); U15 ≤1.5 A; U16 router 2.0 A limit [DN:406]; U4 ~0.9 A est [PROGRESS] | F: 2.0 mm 38 mm, 1.5 mm 28, 1.0 mm 22, 0.8 mm 69, ≤0.6 mm 26 mm; B: 2.0 mm 23, 1.5 mm 20, 1.0 mm 16, 0.8 mm 74, ≤0.6 mm 85 mm; PWR zone P12V_WEST 935.5 mm² + B pours 35 mm² | Q6→U3.8 **1.0 mm (2.39 A)**; →R13/C34 trunk 1.5 mm (3.21 A); →U15.8 0.8 mm (2.03 A); →U16.8 **0.5 mm (1.45 A)**; →U4.8 0.4 mm (1.23 A); P12V_WEST PWR neck **1.41 mm inner (0.93 A at 0.5 oz ASSUMED)** [REV3: re-measured Q6.5→U4.8 = 1.412 mm (pneck.py); the earlier 2.106 mm/1.24 A was from PROGRESS and is withdrawn] | 42 (0.3/0.6). Q6 8 (6.1 A OK); **U3 1** (need 5 at 3.7 A); U4 4 (OK at 0.9 A); U15 1 (need 2); **U16 0** (need 3 if it changes layer) | 1 | AUTO-ROUTED, supervised in-house A* (dc24539 168, 5e16d5b 374, f073f61 156, e650336 125 items; widen f527dd4) | **Short:** trunk 3.21 < 3.7 A; U3 branch 2.39 A; U16 1.45 < 2.0 A |
| +5V (28) L2→loads | 4.7 A [RP §7.1, A]; backlight ≤0.306 A [DN:327]; USB 2×0.68 A [DN:464] | F 0.5–2.7 mm (2.7 mm 50 mm); B 0.5–2.7 mm; **SIG_In2 0.5 mm 137 mm**; no pour | **L2 reaches only C24** (2.15 mm); the other islands are 0.5 mm min (1.45 A outer, 0.44 A on the In2 hops) | 46 (44× 0.2/0.4); **L2 0** within 5 mm; U12 3 → need 7 per transition at 4.7 A | **12 (largest 7)** | AUTO-ROUTED (f03c57a 284, 80844d6 67, f16d8de 44; widened ce06efd/adae893) | **Fails:** not connected to its source; 0.5 mm / 0.44 A In2 links vs 4.7 A |
| +5V_HU (6) U11 boost→U12 | ~1.5 A hold-up path [DN:429, INFERRED there] | 0.5 mm F 89 / B 26 / In2 14 mm | U11→U12.2 0.5 mm B (1.45 A); C77/C78/R80 via In2 0.5 mm (0.44 A) | 10 (0.2/0.4); 3 near U11 → need 2 | 1 | AUTO-ROUTED (f03c57a 84, f16d8de 7) | Marginal: 1.45 < 1.5 A |
| +5V_TRIP (7) U65→U66 | UNKNOWN (555 and logic, small) | 0.5 mm F 13 / B 13 / In2 5 mm | 0.5 mm (1.45 A outer; 0.44 A where on In2) | 5 (0.2/0.4); 1 near U65 | 1 | AUTO-ROUTED (f03c57a 45, f16d8de 16) | OK for mA loads (INFERRED) |
| +5V_CM5 (12) U12→CM5 | ≈3 A [RP, A]; CM5 0.9 A operating [DN:423] | **none** | — | 0 → need 4 per transition at 3 A | 12 | UNROUTED | **Open** |
| +3V3 (27) U4 TPS56637/L3→U6, U20, U22/23, U69, U70, U17, BZ1 | **RESOLVED (REV3): copper ≥3 A**; derived load bound ≤1.47 A (DN:18/DS:17 '≥3 A' is the regulator capability, U4 6 A; RP '≤1 A' is below the bound). See Derived currents | **none** | — | 0 → need 4 at 3 A (or 2 at 1 A) | 27 | UNROUTED | **Open; the main 3.3 V rail has no copper** |
| +3V3_SAFE (119) U6 mux→MCU, logic | UNKNOWN | PWR plane LV_+3V3_SAFE_PWR 41813.9 mm²; 0.25 mm B fanout stubs 121 mm | plane; U6 output stub **0.25 mm (0.88 A)** | 119 (116× 0.2/0.4); 5 near U6 | 2 (R47.2 open) | Plane = SCRIPTED-HAND zone; stubs SCRIPTED fanout (cca514f 146 items; PROGRESS "1,111 plane fan-out vias", fanout_lv.py) + AUTO (f03c57a 76, f16d8de 16) | Capacity UNKNOWN; flag if the load is > 0.88 A |
| +3V3_BK (6) L4→U6 | UNKNOWN | none | — | 0 | 6 | UNROUTED | Open |
| +3V3_PANEL (6), +3V3_TOUCH (6) | UNKNOWN | none | — | 0 | 6 / 6 | UNROUTED | Open |
| CM5_3V3 (17) | ≤0.6 A [RP, A] | none | — | 0 | 17 | UNROUTED | Open |
| +1V8_DSI (26) U20→U21 etc. | ≤0.3 A [RP, A] | 0.25 mm B 3 mm | — | 1 | 24 | Y4 stub only (da8bdeb, cca514f) | Open |
| +3V3_AC (16) U69 ISOW7841→ADE9000s/ISO7741 | ~40 mA load of 75 mA available [DN:300, 367] | PWR zone HV_+3V3_AC_PWR 8075.7 mm²; 0.25–0.3 mm B 22 mm | plane | 18 (0.2/0.4); 2 near U69 | **5: the source U69.16 is isolated**, plus C255, C256, U71.27 | SCRIPTED fanout (cca514f 28) + stitch (34fa5b6 8) | **Connection fault (source cut off)**, not a capacity issue |
| VBAT_ESTOP (22) J23→U43/U45 | 15 A behind the external 30 A fuse [RP §7.2, FPS] | none | — | 0 → need 20 per transition at 15 A | 22 | UNROUTED | **Open** |
| CRANK_OUT (15) Q47/Q48→J23.4 | 15 A [RP §7.2] | none | — | 0 → 20 | 15 | UNROUTED | **Open** |
| FUEL = Net-(D68-A1) (15) Q45/Q46→J23.3 | 15 A [RP §7.2] | 0.15 mm F 2 / B 64 / In2 8 mm | **0.15 mm (0.60 A)** | 4 (0.2/0.4) → 27 at 0.57 A/0.2 mm via | **3** [REV3: 5 counted J23.3's 3 pad objects separately; by unique pin: Q46+U43.13+R349/R350, Q45+D68/D71/C198, J23.3] | AUTO-ROUTED (f03c57a 53, f16d8de 26) | **Fails (0.6 vs 15 A)** |
| CRANK_DRN / FUEL_DRN (5/5) | 15 A path (shunt/FET drain) [RP §7.2] | pours F 133.9/176.3, B 117.6/150.1 mm²; 0.15 mm F/In2 tracks | pour necks NOT MEASURED in this job | 18 / 30 | 1 / 1 | pours SCRIPTED-HAND (8d6659f); tracks AUTO (f03c57a) | UNKNOWN, measure the necks |
| 15 outputs GLOW, GCB_OP/CL, MCB_OP/CL, AUX1–10 (8 each) | 2 A external fuse; driver limit 1.99/2.49/2.99 A [FPS §3, RP §7.2] | 0.15–0.8 mm; 14 of 15 nets have 0.15 mm segments (0.60 A outer, 0.18 A inner), most with In2 0.15 mm hops; **GLOW_OUT min is 0.25 mm (0.88 A)** [REV3 re-measured] | **0.15 mm (0.60 A outer, 0.18 A on In2)**, e.g. AUX1 0.15 mm at B (177.76,29.81–33.61) | 0–5 each (0.2/0.4) → need 4 at 2.99 A | 2–3 each; **the connector J pin is open on each** (e.g. J26.1) | AUTO-ROUTED (f03c57a + f16d8de on every *_OUT) | **Fail** |
| ESTOP_TRIP_OUT (7) U68→J24.6 | limit 1.70/2.13/2.55 A, ≤0.5 A coil, pulse 0.48 s [FPS §1] | 0.15 mm B 19 / In2 5 mm | 0.15 mm (0.60 A; In2 0.18 A); J24.6 open | 3 → need 4 at 2.55 A | 2 | AUTO-ROUTED (f03c57a 30, f16d8de 10) | **Fails at the limit current** (OK for a 0.5 A coil on outer layers only) |
| EXP_12V (4) U15→J7 | ≤1.5 A (U15 CL) [PLAN_12V:9] | 0.15 mm B/In2 | J7.1 and D14 open | 1 | 3 | AUTO-ROUTED (f03c57a) | Open / fails |
| ROUTER 12V = Net-(D15-K) (4) U16→J8 | 2.0 A limit [DN:406] | none | — | 0 | 4 | UNROUTED | Open |
| VLED (5) D22→J16 | UNKNOWN | 0.15 mm | 0.15 mm (0.60 A) | 2 | 3 | AUTO-ROUTED | UNKNOWN load |
| GND (831) | return for all of the above (10 A battery return) | GND1 43874 / GND2 43865 mm² planes; B tracks min 0.15 mm | planes | 948 (898× 0.2/0.4, 49× 0.3/0.6) | 5 (R115.2, U70.2, R204.2, U21.H9 open, as in RP 7.7) | Planes SCRIPTED-HAND zones; fanout SCRIPTED (cca514f 1000) + AUTO (f03c57a 568) + stitch (34fa5b6, 2dab1e7) | Return-via count at the battery negative / LM5176 / FET sources NOT MEASURED (the battery-negative pin was not identified in this job) |
| GND_AC (90) | mA (ADE side) | GND1/GND2 zones 8107.5 mm² each | planes | 82 (0.2/0.4) | 8 (U70.9, C269, C263, C255, C256, C250, C249 open) | SCRIPTED fanout (cca514f 134) + stitch (34fa5b6 43) | Connection opens |
| GND_CAN1/2, GND_485 (8 each) | signal-level isolated grounds | 0.15 mm | — | 5–6 | 2 / 2 / 3 | AUTO-ROUTED (f03c57a) | Opens |
| CHASSIS (14) | ESD/shield only [RP] | 0.15 mm | — | 5 | 11 | AUTO-ROUTED | Open |

- Note (m7-sch batch 8, R5-N4): FUEL/CRANK copper sized for 15 A; 7 A would suffice for a 2.8 A load on a 5 A fuse; deferred layout item (D-m7-14). Numbers above unchanged. VBAT_ESTOP keeps its rating (30 A-fused feed).

Small "power-like" nets, all AUTO-ROUTED by f03c57a/f16d8de, no rating, at most mA (INFERRED): Net-(U11-EN), Net-(C74-Pad2), Net-(U17-VISO), Net-(U7-VDDA), MUXA/B_OUT, VBAT_SENSE, VBAT_CELL, VBAT_SNS (UNROUTED), HSE_OUT. Full numbers are in stats.json and islands.json.

## Flags (auto-routed or under spec)
1. **Unrouted rails (no copper):** +3V3 (≥3 A copper target, REV3), +5V_CM5 (3.76 A limit), VBAT_ESTOP (15 A), CRANK_OUT (15 A), CM5_3V3, +3V3_BK, +3V3_PANEL, +3V3_TOUCH, ROUTER_12V Net-(D15-K), VBAT_SNS. +1V8_DSI is effectively unrouted (24 islands).
2. **Auto-routed and short:** +5V (source L2 cut off, 0.5 mm / In2 0.44 A vs 4.7 A); FUEL (0.15 mm, 0.6 A vs 15 A); all 15 *_OUT (0.15 mm, 0.6 A vs 2–2.99 A, connector pin open); ESTOP_TRIP_OUT (0.6 A vs 2.55 A); +12V (trunk 3.21 A vs 3.7 A ASSUMED, U3 branch 2.39 A, U16 branch 1.45 A vs 2.0 A, U3 has 1 via); +5V_HU (1.45 vs ~1.5 A).
3. **Battery path:** it meets 10 A only through layer sharing. VBAT_P Q2→Q3 B is 7.16 A, so it needs F; the Q3 end has 14 vias, exactly the requirement. VBAT_F has B 10.82 A alone with only 3 vias at Q1. VBAT_P does not reach the LM5176 input pins or any output switch (61 islands).
4. **Connection faults on planes:** the +3V3_AC source U69.16 is isolated; there are 4 GND opens, 7 GND_AC opens and 1 +3V3_SAFE open (R47.2).

## Proposed hand-placement order (plan only)
1. **VBAT_P distribution** (Q3 → U2 VIN and the VS pins of U47–U61 and U68) as a planned F+B pour tree with ≥4 vias per output switch (2.99 A / 0.76 A), and ≥5 at U2.2/U2.3 (3.56 A). This comes first because every downstream rail and output depends on it. Sources: FPS §3, RP §7.2.
2. **VBAT_ESTOP → shunts → Q45/Q46 (FUEL) and Q47/Q48 (CRANK_OUT) → J23**, 15 A: F+B pours ≥6.3 mm each (RP target; IPC 12.6 mm on one outer layer), ≥20 vias at each FET/shunt transition. Remove the auto-routed 0.15 mm FUEL tracks.
   Note (m7-sch batch 8, R5-N4): FUEL/CRANK copper sized for 15 A; 7 A would suffice for a 2.8 A load on a 5 A fuse; deferred layout item (D-m7-14). Numbers above unchanged. VBAT_ESTOP keeps its rating (30 A-fused feed).
3. **+12V trunk Q6 → U3** at ≥1.83 mm (3.7 A) on both outer layers, or a pour. Add 4 vias at U3.8 (about 226.3–226.7, 63.3–64.3; the area west/south of the pad, DRC-check first) to reach 5. Widen the U16 branch to ≥0.78 mm (2 A) and add 3 vias near U16.8 (257.4,160.2) if it changes layer.
4. **+5V L2 → U12/U13/U14/U18/U19/J3/J4/J5**: one planned pour or ≥2.54 mm outer trunk (4.7 A). No In2 hops (0.5 mm In2 carries 0.44 A). 7 vias per transition, starting at L2.2 (222.5,76.1), which has 0 today.
5. **+3V3 (≥3 A copper target, REV3) from U4/L3** and **+5V_CM5 (3.76 A limit)**: +3V3 trunk ≥1.37 mm outer, 4×0.3 mm or 6×0.2 mm vias per transition; +5V_CM5 ≥1.87 mm outer, 5 vias per transition. The +3V3 conflict is resolved in 'Derived currents'.
6. **Outputs and ESTOP_TRIP_OUT**: ≥1.09 mm outer (2.55–2.99 A), outer layers only. Connect the J pins, 4 vias wherever a layer change is unavoidable. Rip up the 0.15 mm auto-routed copper.
7. The small rails (+1V8_DSI, CM5_3V3, +3V3_BK/PANEL/TOUCH, ROUTER_12V, EXP_12V) at 0.3–0.8 mm per current. Fix the +3V3_AC source tie (U69.16 (61.36,57.55)) and the GND/GND_AC pad opens.

Multiple vias in parallel are the right fix in these places (measured shortfalls):
- **VBAT_F at Q1:** 3 vias within 5 mm today; add about 11 to reach 14 so F (3.84 A) and PWR (3.54 A) share with B. Region around the Q1 pads (255.1–257.6, 140.6), on the F1 side of Q1 (y ≈ 136–140, x 254–259). Clearance to the U1/C1/C2 parts must be checked.
- **VBAT_P at Q3** (228.02,140.07): 14, which is exactly the need. Add 4–6 for margin.
- **+12V at U3.8:** 1 → 5. **U15.8** (205.3,77.1): 1 → 2. **U16.8:** 0 → 3 if a layer change is kept.
- **+5V at L2.2** (222.5,76.1): 0 → 7.
- **BAT_IN at F1.1** (243.6,126.5/129.9): 8 near → 14 for full F/B sharing (both are TH, so this is margin, not a requirement).
- Vias do not fix the 0.15 mm necks or the In2-only hops. Those need width on outer layers.

## Unknowns / not measured
- Currents for +3V3_SAFE, +3V3_BK, +3V3_PANEL/TOUCH, +5V_TRIP and VLED are UNKNOWN (no source found). The +3V3 rating conflicts: ≥3 A in DN/DS vs ≤1 A in RP. The +12V 3.7 A and +5V 4.7 A figures are ASSUMED in RP.
- Copper weight and stackup are not defined in the board. The IPC figures are only as good as the 1 oz / 0.5 oz assumption.
- Pour necks of CRANK_DRN/FUEL_DRN, the +3V3_SAFE and GND planes, and the GND return paths (battery negative pin, FET source returns, return via counts) were not measured in this job.
- Islands come from our geometric graph, not KiCad's ratsnest. No KiCad DRC was run here.
- The 0.2/0.4 mm vias are counted at the 0.3 mm basis (optimistic).
- final_power_spec.md §2 "neck 3.6 A at 18 °F" (shared neck, q2q3_copper) predates S3c/c6b; whether it still applies to today's copper was not re-checked.
- Origin labels come from uuid first-seen commits plus commit/PROGRESS text. GUI hand edits inside a router commit could not be separated out.

## Derived currents (turn 2, 2026-10-27)

Labels: **DERIVED** means datasheet, BOM or design note plus arithmetic, with the source cited. **ASSUMED** means no source; it is a bound picked to be safe, so verify it. **UNKNOWN** means no figure exists. **FW-Q** means it depends on firmware (questions below). Widths are IPC-2221 outer 1 oz at 18 °F (10 °C) rise. Pin lists are MEASURED from board 3a8237f (`scen/railplan/pins.txt`). Datasheet paths are under /workspace/genctl/datasheets/.

### Which regulator feeds which net (MEASURED netlist and BOM)
| Net | Source | Source rating (DERIVED) |
|---|---|---|
| +12V | U2 LM5176 buck-boost (L1 SPM10065VT-4R7M, Isat 19.3 A [power_bom:11]) | Input limited by 16 mΩ: 2.69/3.12/3.56 A on VBAT_P [final_power_spec §2, LM5176 Eq. 4] |
| +5V | U3 TPS56637 + L2 MWSA1004S-3R3MT | 6 A continuous; valley limit 6.3/7.5/8.6 A [tps56637 p1, l.301]. L2 Isat "~15 A, verify mfr" [power_bom:16] = **UNVERIFIED** |
| +3V3 | U4 TPS56637 + L3 MWSA1004S-3R3MT C408483 (3.3 µH; was MWSA0503S-2R2MT, changed 52e8028) | 6 A [tps56637 p1]; L3 Isat 12.8 A typ (Sunlord p17, Safety R4-N4). 3.3 µH deviates from TI Table 4 (p19, 2.2 µH for 3.3 V): bench load-step 0.5-3 A at 9/12/32 V in required; fallback 2.2 µH same footprint |
| +3V3_BK | U5 LMR36506 (VBAT_P) + L4 SWPA6045S330MT | 0.6 A; LS limit 0.6/0.7/0.752 A, HS 0.87–1.11 A [lmr36506 l.4, l.355]; L4 Isat 1.65/1.80 A, Irms 1.45/1.60 A [swpa6045 l.934] |
| +3V3_SAFE | U6 TPS2116 mux (+3V3 priority, +3V3_BK backup) | 2.5 A continuous [tps2116 p1] |
| +3V3_PANEL / +3V3_TOUCH | U22 / U23 TPS22918 from +3V3 | 2 A each [tps22918 p1] |
| +3V3_AC | U69 ISOW7841 isolated DC-DC from +3V3 | ≥75 mA at 3.3→3.3 V [isow7841 l.24] |
| +1V8_DSI | U20 TLV75518 from +3V3 | 500 mA; RθJA 100.8 °C/W DBV JEDEC [tlv755p l.4, l.241] |
| CM5_3V3 | CM5 internal regulator (U9) | 600 mA to peripherals [cm5-datasheet l.826, 872] |
| +5V_CM5 | U12 TPS2121 (IN1 +5V, IN2 +5V_HU) | ILM 3.76 A (RILM 29.4k) [current_budget, tps2121 p13]; DN:427 says 3.5 A |
| +5V_HU | U11 TPS61023 boost from supercaps + L5 FNR5020S1R0MT | Valley limit 3.7 A typ [tps61023 p1]; ~1.5 A out at 5 V [DN:429]; L5 "1 µH 5 A" [power_bom:33], Isat-vs-Irms basis UNVERIFIED |
| +5V_TRIP | U65 TPS7B6950 from VBAT_P | 150 mA; RθJA 210.4 °C/W DBV [tps7b69 l.20, l.210] |
| VLED | U24 TPS61500 + L8 SWPA6045S100MT + D22 SS36 | Switch ILIM 3/3.8/5 A [tps61500 l.327]; L8 Isat 3.20/3.50 A, Irms 2.45/2.70 A [swpa6045 l.927] |
| EXP_12V / ROUTER_12V Net-(D15-K) | U15 / U16 TPS1H200A from +12V | Limit 1.5 A (R95 1.33k) / 2.0 A (R96 1k) [DN:406, tps1h200a p11] |

### Per-net load sums
**+3V3 (U4).** All of its loads are listed. The sum is the worst-case bound.
- +3V3_SAFE through U6: **≤0.55 A** (DERIVED + ASSUMED).
  - STM32H743 at VOS1 400 MHz with all peripherals on: 220 mA max at TJ 77 °F (25 °C), 400 mA at 185 °F (85 °C), 500 mA at 221 °F (105 °C) [DS12110 Rev 7 Table 30, read through a web extract; the 480 MHz row was not in the extract, so it is UNVERIFIED].
  - Plus GPIO source current: UNKNOWN (FW-Q1).
  - Plus logic and pull-ups (6× TCA9555 ≤1 mA quiescent [tca9555 l.446]; 2× ADS1115; 74HC14/LVC541/INA281/TMUX/FRAM; I²C 2.2k pull-ups at 1.5 mA each): ASSUMED ≤50 mA.
  - The button LEDs are sunk from +5V, not +3V3_SAFE (DN:325–327).
- +1V8_DSI through U20: **0.12 A** (DERIVED). SN65DSI83 ICC max 112 mA [sn65dsi83 l.383]. Y4 is DNP [DN rev j]. The level shifters take µA.
  - LDO dissipation: (3.3−1.8) V × 0.12 A = 0.18 W.
  - Junction rise: 0.18 W × 100.8 °C/W = 18 °C, i.e. 33 °F. OK.
- +3V3_PANEL through U22: 210 mA typical operating; the datasheet gives no max [DS_RVT121HVLNWCA0-B Rev 1.1 l.281]. **ASSUMED ≤0.30 A.**
- +3V3_TOUCH through U23: **UNKNOWN**, not in the panel datasheet extract. ASSUMED ≤0.05 A.
- U69 ISOW7841 primary:
  - Isolated-side load is ≤60 mA (DERIVED): 2× ADE9000 at 17 mA max [ade9000 l.413], ISO7741 ICC2 ≤25 mA at the 100 Mbps worst case [iso7741 l.689], and 10k pull-ups at 0.7 mA. That is under 75 mA.
  - Primary current: ICC = VISO·IISO/(η·VCC) + Iinp [isow7841 l.2531]. η is only given as a curve, so it is ASSUMED at 0.4, giving **≤0.18 A ASSUMED**.
- U70 ISO7741 side 1: ≤14.4 mA [iso7741 l.687] (DERIVED).
- U17 CA-IS2092W (RS-485 with isolated power, SEL tied to VISO, so SEL=1): 69 mA at 3.3 V with SEL=0 and 54 Ω load [ca-is2092w l.401]. The SEL=1 case at 3.3 V is not tabulated (at 5 V it is 96 mA). **ASSUMED ≤0.15 A.**
- BZ1 MLT-8530 through MMBT3904: **UNKNOWN** (no datasheet on the box). ASSUMED ≤0.10 A.
- **Sum: ≤1.47 A** (worst case, mostly bounds). Typical is about 0.7 A (MCU 0.22 + panel 0.21 + RS-485 0.07 + ISOW 0.1 + DSI 0.08).
- **Copper target: 2 A** (1.47 × ~1.35 margin), i.e. a 0.78 mm outer trunk at L3 and 3 vias per layer change.
  - Branches: U6 0.55 A → 0.25 mm OK; U22 0.3 A; U17/U69 0.2 A; U20 0.12 A.
  - **The +3V3 conflict is resolved.** The "≥3 A" in DN:18/DS:17 is the regulator's capability (TPS56637 6 A), not a load. ROUTING_PLAN's "≤1 A" is below the 1.47 A worst-case bound. Route for 2 A.
- +3V3_SAFE capacity: same ≤0.55 A. The U6 output stub of 0.25 mm (0.88 A) is adequate.
- +3V3_BK: on backup it carries the whole SAFE load, ≤0.55 A. That is 92 % of LMR36506's 0.6 A at the 221 °F MCU bound, and 0.45 A (75 %) at 185 °F. The margin is thin but not over.
- +3V3_AC: ≤60 mA DERIVED of ≥75 mA. OK.
- CM5_3V3: LVC1T45 ×2, R105/R106 330R and R59/R60 1k pull-ups (ASSUMED ≤20 mA), plus J5.1 (Header A) external load, which is UNKNOWN (FW-Q5). Of 600 mA available.

**+5V (U3).** Each item is the protected limit of its branch.
- U12 → CM5: ≤3.76 A, the DERIVED ILM. The CM5 itself draws 0.9 A typical operating and 0.4 A idle [cm5 Table 9, l.1508]. It is specified up to 5 A at 5 V [cm5 l.253]. Peak is FW-Q2.
- U18/U19 TPS2553 USB headers: 2 × 0.71 A = 1.42 A (DERIVED, 40.2k) [current_budget, tps2553 p15].
- Button backlight through Q68: 0.306 A [DN:327] (DERIVED: 36 × 8.5 mA).
- 2× CA-IS3062W: 2 × 29 mA max = 0.06 A [ca-is3062w l.385–391].
- Supercap charge through D11/50R: ≤0.092 A [DN:425].
- J4 fan: **UNKNOWN** (FW-Q3).
- J3.8 and J5.2 header pins: **UNKNOWN** external loads (FW-Q5).
- **Sum of limits: 5.64 A + fan + headers** (DERIVED part). That is under the U3 6 A rating, with 0.36 A left for the fan and headers.
  - Realistic: 0.9 + 0.3 + 0.06 + USB ≈ 1.5–3 A.
  - Copper: the L2 node and trunk need ≥5.64 A → 3.27 mm outer (or F+B pour). The U12 branch needs 3.76 A → 1.87 mm. Each TPS2553 branch needs 0.71 A → 0.25 mm OK.
- +5V_CM5: 3.76 A limit → 1.87 mm outer, and ≥5 vias at any layer change. The CM5 has 6 pins (U9.77–87).
- +5V_HU: ~1.5 A out [DN:429] → 0.52 mm.
  - The supercap side, Net-(U11-EN)/HU_SW, carries up to the switch valley limit of 3.7 A typ plus ripple (DERIVED) → ≥1.9 mm outer.
- +5V_TRIP: TLC555 plus R402 10k / R404 200k gives ASSUMED ≤5 mA.
  - Dissipation at the 35.74 V OV max: (35.74 − 5) V × 5 mA = 0.154 W.
  - Rise at 210.4 °C/W: 32 °C, i.e. 58 °F. OK against the 150 mA rating.
  - Copper 0.15 mm is fine.
- +1V8_DSI: 0.12 A (above) → 0.15 mm outer OK. The current 24-island state is a connection fault, not a capacity issue.

**+12V (U2 LM5176).** The demand, as a sum of limits:
- U3 +5V: 5.64 A × 5 V / (12 V × η 0.9 ASSUMED) = 2.61 A.
- U4 +3V3: 1.47 × 3.3 / (12 × 0.9) = 0.45 A.
- ROUTER_12V: 2.0 A (the TPS1H200 limit).
- EXP_12V: 1.5 A (limit).
- VLED: the panel backlight is 48 LEDs, Vf 25.6 V, If 360 mA [DS_RVT l.256, l.292], so 9.2 W DERIVED. At η 0.85 ASSUMED that is 1.08 A from +12V.
- **Total 7.64 A** (sum of limits).
- Realistic (CM5 0.9 A, panel 0.21 A, router and EXP UNKNOWN) is about 2.5–3.6 A.

Supply side: the LM5176 input limit of 3.56 A max gives at most about 3.56 × VIN/12 × 0.9 A out. That is 3.2 A at 12 V battery input and 6.4 A at 24 V (DERIVED; 24 V is allowed by the 32–35.7 V OV trip).

**Copper target:**
- 12 V battery: 3.6 A → 1.73 mm, which matches the current_budget figure of 3.7 A.
- 24 V battery: up to 7.64 A → 4.96 mm outer, or an F+B pour.
- The battery voltage decides which (FW-Q4/Ethan).
- U3 branch: 2.61 A → 1.15 mm. Today it is 1.0 mm with 1 via, which is short.
- U16/J8 ROUTER_12V: 2.0 A → 0.78 mm. Today 0.5 mm, short.
- U15/J7 EXP_12V: 1.5 A → 0.52 mm.
- VLED (D22 → J16): 0.36 A → 0.15 mm OK. The U24 input is 1.08 A → 0.31 mm.

**15 A rails (VBAT_ESTOP, FUEL Net-(D68-A1)/FUEL_DRN, CRANK_OUT/CRANK_DRN).**
- 15 A per channel is the design rating [design_spec:25]. The real solenoid load is UNKNOWN [current_budget Q3]. Pull-in is 60 A pulse [design_spec:101].
- VBAT_ESTOP carries both channels: **30 A if fuel and crank are on together** (DERIVED 2 × 15). The external fuse is 30 A [design_spec:31].
  - J23.1/J23.2 are separate pins, but the J23→R297/R303 copper splits per channel. So each channel's branch is 15 A, and the J23 pin node is 30 A.
- **15 outputs plus ESTOP_TRIP:**
  - Copper must carry the driver limit max, 2.99 A (ILIM 40.2k: 1.99/2.49/2.99 A) [tps1htc30 p8] → 1.36 mm outer.
  - The external 2 A blade [RP §7.2, INFERRED] opens before then on a sustained overload, but the driver will hold up to 2.99 A until it does.
  - "Unfused" outputs: per DN:315 there is no on-board fuse. If an installer omits the DIN fuse, the driver's ICL (2.99 A) and its thermal shutdown are the only limit, and 2.99 A copper covers that.
  - ESTOP_TRIP_OUT: 2.55 A max (47k) → 1.09 mm.

## Part/rating changes needed (tell the lead before any copper)
None of these is required in order to lay the copper. Items 1–2 change the copper target, and items 3–6 are rating mismatches the lead should rule on.
1. **+12V supply versus demand (rating/decision, not a part).**
   - The sum of downstream limits is 7.64 A, but the LM5176 can deliver only about 3.2 A at a 12 V battery.
   - Either accept that the converter limit is the real limit (copper for 3.6 A), or, for 24 V installs, size the copper at 7.64 A.
   - This decision is needed before the +12V trunk is laid.
2. **VBAT_ESTOP J23 node at 30 A** if fuel and crank can be on at once. J23 PC 5 is 41 A (OK) [design_spec:44]. The shunts are 54.8 A each (OK). The copper at the J23 pins needs 30 A (F+B pour), not 15 A. Ethan should confirm simultaneity.
3. [SUPERSEDED: L3 is now MWSA1004S-3R3MT C408483, Isat 12.8 A typ > 8.6 A + ripple; it deviates from TI Table 4 (2.2 µH), bench load-step 0.5-3 A at 9/12/32 V in required, fallback 2.2 µH same footprint.] **L3 MWSA0503S-2R2MT Isat 7 A < U4 TPS56637 valley limit max 8.6 A.** The inductor saturates before the regulator limits on a short or overload. The load is only 1.47 A, so this is fault behaviour only.
   - Option A: swap to an inductor with Isat ≥10 A in the same footprint family (UNVERIFIED availability).
   - Option B: accept it.
4. **L8 SWPA6045S100MT Isat 3.2/3.5 A < TPS61500 switch ILIM 3/3.8/5 A.** Normal peak at 12 V in is about 1.3 A (ASSUMED), so this too is fault-only. The same accept-or-swap choice applies. The bom/comms_bom:44 already marks it UNVERIFIED.
5. **L2 MWSA1004S-3R3MT Isat "~15 A, verify mfr"** [power_bom:16]. It is UNVERIFIED; the datasheet is not on the box. It must exceed the 8.6 A valley limit plus ripple.
6. **D72 SK1010C (10 A) on CRANK_OUT** against a 15 A crank channel. If it is the solenoid freewheel diode, it carries the full load current as it decays at turn-off. Pulse rating and role are UNVERIFIED. Check the IFSM and the role. FUEL uses D71 SMDJ24A (a TVS, not in the load path).
7. Watch item (no change yet): +3V3_BK LMR36506 0.6 A versus the ≤0.55 A SAFE bound, which is 92 % at a 221 °F MCU. If FW-Q1 shows GPIO source loads above 50 mA, U5 needs a larger part.
8. UNVERIFIED ratings to close: KF2EDGRM 15 A (C441292) and WJ15EDGRC 3.81 (J7/J8) current basis; CA-IS2092W SEL=1 current at 3.3 V; MLT-8530 current; touch-panel current; BSC070N10NS5 ID (not re-read this turn).
- No change is needed: J1/J23 PC 5 41 A; WSLP2512 shunts 54.8 A; TPS2116 2.5 A; TPS22918 2 A; TLV755 500 mA at 0.12 A (33 °F rise); TPS7B69 150 mA at ≤5 mA; TPS56637 ×2 6 A; L1 Isat 19.3 A; L4 Isat 1.65 A > LMR36506 HS limit 1.11 A.

## Firmware questions (exact wording)
- FW-Q1: "What is the worst-case total current sourced by STM32 GPIOs (sum over all pins driving loads high), and what core clock and VOS will the firmware run (400 MHz VOS1, or 480 MHz VOS0)?"
- FW-Q2: "What is the CM5 peak 5 V current under your heaviest workload (all cores, USB loads, Wi-Fi TX), and is the TPS2121 3.5–3.76 A limit acceptable as the cap?"
- FW-Q3: "Is the J4 fan fitted, which fan model, and what is its rated current at 5 V?"
- FW-Q4 (Ethan): "Is the system 12 V or 24 V battery (or both)? Can fuel and crank be energized at the same time?"
- FW-Q5: "What, if anything, is connected to Header A pin 1 (CM5_3V3) and pin 2 (+5V), and to Header B pin 8 (+5V), and at what current?"
- FW-Q6: "What maximum backlight brightness and duty will the firmware command for the TPS61500 (100 % = 360 mA)?"
- FW-Q7: "What are the expected router (ROUTER_12V) and expansion-bus (EXP_12V) load currents, versus the 2.0 A and 1.5 A limits?"
- FW-Q8: "What is the maximum on-time and duty for the buzzer (BZ1)?"

## Outline/corridor check (MEASURED, `scen/railplan/corr.py`, `corr.out`, `blk.py`)
**Method.** Take a straight line from the source pad to the destination pad, trimmed by 1.5 mm at each end. Usable width = 2 × (distance to the nearest foreign obstacle − 0.2 mm clearance).
- "asis" counts all foreign pads, tracks, vias and non-GND pours on refilled.kicad_pcb.
- "padsonly" assumes other nets' tracks can be rerouted and GND pours retreat.
- A straight line is conservative: a bent route may exist where the straight one is blocked. Bent routes were not measured.

**Results.**
- **As-is: every corridor is 0 on both F and B.** Auto-routed tracks of other nets cross every power path, so rip-up and re-route is needed in all cases.
- **The 15 A power stage is entirely on B.** J23, R297, R303, Q45–Q48, D68, D71 and R295 are all bottom-side. So the B straight corridors are blocked by the parts themselves (e.g. J23→R303 crosses R295; Q47→J23 crosses D68/D71/R303). The F side is clear in pads-only terms:

  | Path | Length | F free width |
  |---|---|---|
  | VBAT_ESTOP J23→R297 | 10.4 mm | 13.38 mm |
  | VBAT_ESTOP J23→R303 | 30.5 mm | 12.97 mm |
  | FUEL Q45→J23 | 16.9 mm | 9.98 mm |
  | FUEL Q46→J23 | 28.1 mm | 10.92 mm |
  | CRANK Q47→J23 | 41.6 mm | **7.07 mm** |
  | CRANK Q48→J23 | 34.8 mm | 9.73 mm |

- **What 15 A needs:** 12.6 mm on F alone at 18 °F, or 8.26 mm at 36 °F (20 °C), or F + B at 6.3 mm each.
  - **F alone at 18 °F fits only VBAT_ESTOP.** It does not fit FUEL/CRANK (7.1–10.9 < 12.6).
  - At 36 °F it fits everything except CRANK Q47 (7.07 < 8.26).
  - **Smallest change:** F-side pours at the measured widths, plus B-side pour flowing around the bottom parts (B width around the parts was not measured; the prior FEM measured B 4.05–6.57 mm at the drains). Stitch with ≥20 vias per branch (15 A / 0.76 A). If that falls short, either move D68/D71/R295 off the B line between Q47/Q45 and J23, or accept a 36 °F rise.
  - **The J23 node at 30 A** needs F + B ≥ 12.6 mm each at 18 °F. The F corridor near J23→R297 is 13.38 mm, which is just enough.
- **Outputs (need 1.36 mm outer, F pads-only straight):**
  - OK: AUX7 8.59, AUX2 6.22, AUX8 6.63, AUX3 3.02, GCB_CL 4.47, AUX4 5.88, AUX1 1.79, ESTOP_TRIP 6.98, AUX9 5.32, AUX6 6.39, GCB_OP 4.65, AUX5 5.80, MCB_CL 2.08 mm.
  - **Short: MCB_OP_OUT 1.26 mm** (meets 0.89 mm at 36 °F). **GLOW_OUT 0** (U47→J24 crosses C74 and J16/VLED, and passes 0.26 mm from J24's GCB_CL pin). **AUX10_OUT 0.**
  - B is 0 for all, because the drivers and J24 are bottom-side parts.
  - For GLOW, AUX10 and MCB_OP a bent route is needed, which was not measured. The smallest change is a detour around C74/J16, or moving C74 (a hold-up supercap) off the GLOW line.
- Rails with 0.15 mm necks (FUEL, outputs, +12V branches): the widths above apply. The +12V corridors were not measured this turn.

## REVISION 3 (2026-10-27 18:00 HST): the Design Reviewer's audit folded in
**Inputs and identity.**
- Audit: /workspace/review/rail/rail_audit.md.
- **The copper on f7a6c86 is identical to 3a8237f.** The f7a6c86 file was extracted with `git -C /workspace/m7wt show` to `scen/railplan/f7.kicad_pcb`.
  - The files differ (md5 49a6a6a7 vs 3a67a66e).
  - All 25,967 tracks and vias match by net, endpoints, width and layer, and the zone sets match (`ver.py`).
  - So every measurement below was made on our refilled 3a8237f copy.
- Scripts: `isl2.py` (islands and widths per net), `pneck.py` (erosion neck between via groups on one layer), `wpath.py`.
- The derived-currents and part-change job from turn 2 is complete (sections above). It is kept, with the corrections below.
- **Copper weight and plating are still ASSUMED:** 1 oz outer, 0.5 oz inner, 20 µm via plating.

**Where the audit and this plan disagree, the board was re-measured:**

| Audit point | Re-measured here | Result |
|---|---|---|
| (a) BB_CS has no copper | 8 pads, 8 islands, 0 tracks | **agree** (missed before) |
| (a) BB_SW2 is in 4 pieces | [Q6.1-3 + Q5.5] with 0.4 mm B tracks; U2.18, C16.2 and L1.2 each isolated | **agree** |
| (a) BB_SW1 is only 0.5 mm | 1 island; all tracks 0.5 mm (F 16, B 27, In2 14 segments) | **agree** |
| (a) USB0_5V/USB1_5V are open at J12.1/J13.1 | USB0: [J12.1] alone + [U18.6, D20.5, C105.1]. USB1: 4 islands, every pad isolated (J13.1, D21.5, C107.1, U19.6) | **agree**, and USB1_5V is worse than the audit states |
| (a) VESTOP_SNS, U71/U72 AVDDOUT/DVDDOUT and U72-VAP have no copper | VESTOP_SNS 5 pads / 5 islands; the 5 ADE nets have 3 pads / 3 islands each; 0 tracks | **agree** |
| (b) +12V PWR neck Q6→U4 | 1.412 mm (8 vias at Q6.5, 4 at U4.8) → 0.93 A inner 0.5 oz | **agree.** 2.106 mm / 1.24 A was taken from PROGRESS and is withdrawn |
| (c) VBAT_P: which switches reach Q3 | The Q3 group holds U1.9, U49.12/.13/.14, U50.12/.13, U5.4 and U68.13/.14. Isolated: U2.2, U2.3, U5.3, U50.14, U68.12 and all other switches' VS pins | **agree.** The turn-1 row was wrong and is corrected |
| (c) VBAT_P path widths | 0.3 mm B tracks to U68.13, U50.12, U49.12/.14 (1.0 A). In2 necks Q3→U49.13, U50.13 and U5.4 are 0.753 mm (0.59 A), Q3→U68.14 is 0.552 mm (0.47 A) | **agree** except U68.14: audit 0.39 mm / 0.37 A, mine 0.55 mm / 0.47 A. The endpoint definition differs (I used the vias within 3 mm of each pad). Either way it is far below 2.99 A. The 0.753 value equals the via-annulus size, so the real limit may be the via (INFERRED, as the audit says) |
| (d) 14 outputs with 0.15 mm segments; GLOW min 0.25 mm | Every output except GLOW has 0.15 mm on B and/or In2 (MCB_OP: B only). GLOW minimum 0.25 mm B (0.88 A). AUX5_OUT has 3 islands (others 2: the J pin is open) | **agree.** The "every net" claim is corrected. New: AUX5 has an extra break |
| (d) FUEL has 3 islands, not 5 | 3 by unique pin. My 5 came from counting J23.3's three pad objects separately | **agree**, corrected |
| (e) +3V3 at ≥3 A; RP:96 "≤1 A" stale | U4 TPS56637 6 A confirmed (tps56637 p1). RP:96 does read "+3V3 ≤ 1 A" | **Adopted ≥3 A as the copper target** (1.37 mm outer). Remaining disagreement: the derived load bound is ≤1.47 A, so 3 A is about 2× margin, not a load. That is fine for copper |
| (e) +5V_CM5 ≈3 A (CM5 design 2.5 A), not 0.9 A | cm5-datasheet §B.3 (l.2021): "accommodate 5 V at up to 2.5 A". The 0.9 A is Table 9 typical operating | **agree that 0.9 A must not size copper.** This plan keeps **3.76 A** (the TPS2121 ILM, which is what the switch can pass) → 1.87 mm. The audit's ≈3 A is a little lower; 3.76 A is the conservative choice |
| (f) 0.2 mm vias at 0.57–0.67 A | Not re-derived numerically; the audit's π·d·t method matches our 0.3 mm basis | **adopted at 0.57 A (conservative)** |

**Via sizing restated** (18 °F rise, plating 20 µm ASSUMED):
- Basis: a 0.3/0.6 mm via counts 0.76 A; a 0.2/0.4 mm via counts **0.57 A** (0.67 A at 25 µm).
- Count needed per layer change, as 0.3 mm vias / 0.2 mm vias:

  | Current | Example net | 0.3 mm | 0.2 mm |
  |---|---|---|---|
  | 1 A | | 2 | 2 |
  | 2 A | | 3 | 4 |
  | 2.55 A | ESTOP_TRIP | 4 | 5 |
  | 2.99 A | outputs | 4 | 6 |
  | 3 A | +3V3 | 4 | 6 |
  | 3.56 A | LM5176 VIN | 5 | 7 |
  | 3.76 A | +5V_CM5 | 5 | 7 |
  | 5.64 A | +5V trunk | 8 | 10 |
  | 7.64 A | +12V, 24 V case | 11 | 14 |
  | 10 A | VBAT | 14 | 18 |
  | 15 A | fuel/crank | 20 | 27 |
  | 30 A | J23 node | 40 | 53 |

- Existing counts that used 0.76 A for 0.2 mm vias are 25 % optimistic. Q3's 14 vias at 5 mm hold mixed sizes, so recount them by size before calling 10 A met.

**Nets added to the plan** (all measured above):

| Net | Current | Status / action |
|---|---|---|
| BB_CS (LM5176 sense / low-side path) | Carries the LM5176 inductor current: up to the converter limit, about 3.56 A input-referred (INFERRED; L1 peak higher) | 0 copper. Route as a short, wide pour with a Kelvin sense pickup to U2 |
| BB_SW1 / BB_SW2 (switch nodes) | Inductor current, same order as BB_CS (INFERRED) | BB_SW1 0.5 mm (1.45 A outer) is short of it. BB_SW2 is open at L1.2, C16.2 and U2.18. Both need compact pours on the U2 side. This is a power-stage layout item and belongs before the +12V trunk |
| USB0_5V / USB1_5V | 0.71 A each (TPS2553 limit) | 0.25 mm minimum; connect J12.1 and J13.1. USB1 has every pad isolated |
| VESTOP_SNS, U71/U72 AVDDOUT/DVDDOUT, U72-VAP | mA (sense or LDO decoupling) | Signal width is enough. They must be connected (the ADE LDO output decoupling caps are currently unconnected) |

**Doc fixes needed (NOT edited; the repo is read-only for this job):**
1. docs/ROUTING_PLAN.md:96 "+3V3 ≤ 1 A" → "+3V3 ≥3 A copper (U4 TPS56637 6 A; derived load ≤1.5 A)".
2. ROUTING_PLAN:96 "+5V_CM5 ≈ 3 A" → "3.76 A (TPS2121 ILM; CM5 design 2.5 A)".
3. DN:423's 0.9 A should be marked "typical; do not size copper with it".
4. The PROGRESS P12V_WEST 2.106 mm neck → 1.41 mm.

**Hand-placement order:** one change. Insert the **LM5176 power stage (BB_CS, BB_SW1, BB_SW2)** before the +12V trunk, because the trunk is meaningless while U2's switch nodes and sense path are open. The rest of the order stands.

## REVISION 4 (2026-10-27 ~18:10 HST): FINAL copper targets, 12 V battery only
**Scope.**
- Ethan: the board is for a 12 V battery only. A 24 V installation uses a separate step-down module ahead of the board, so **24 V is out of scope** and no 24 V figures are given here.
- The OV thresholds and the 31 V maximum stay as built. No part changes come from this revision.
- Supersedes the 12/24 V decision items in turn 2 and FW-Q4a. The pre-REV4 copy is `scen/railplan/rail_plan.pre_rev4.md`.

**Battery voltage basis.**
- **Minimum 9 V** (cranking sag, ASSUMED) is used for every input-side current.
- The 5.32/5.56/5.86 V UV rising threshold [DN:51] is only the protection point, not a sizing point.
- Reference column: nominal 12–13 V.

**Copper and via basis.**
- Outer 1 oz and inner 0.5 oz are ASSUMED. IPC-2221 widths at 18 °F rise, with 36 °F as the alternate.
- F+B means each layer carries I/2. Note: turn 2's "6.3 mm each" for 15 A halved the width, not the current. I/2 per layer gives **4.84 mm each**.
- Vias are per layer change, counted at 0.76 A per 0.3 mm via and 0.57 A per 0.2 mm via.

### LM5176: the delivered +12V limit, recomputed (DERIVED from SNVSAI1D and the board)
**As built (MEASURED on the board, and DN:62):**
- U2.12/.13/.14 (VOSNS/ISNS) are all on +12V, so the average input/output current loop is **not used**. The 16 mΩ input limit in final_power_spec §2 is a proposal and is **not on the board** (no VIN_BB net exists).
- The only limit is cycle-by-cycle, set by R12 8 mΩ (BB_CS–GND) [D p16 §7.3.5]:
  - Buck valley: 66/80/94 mV → **8.25/10.0/11.75 A**.
  - Boost peak: 100/120/140 mV → **12.5/15.0/17.5 A** [D p7].
- Switching frequency: RT 27.4k gives fsw = 1/(27.4k × 116 pF + 190 ns) = 297 kHz [Eq. 5, D p17]. L1 is 4.7 µH.

**At a 9 V battery (boost mode):**
- D = 1 − 9/12 = 0.25.
- Ripple ΔIL = 9 × 0.25 / (4.7 µH × 297 kHz) = 1.61 A.
- Output limit = (12.5 − 0.81) × 0.75 = **8.77 A min** (lossless, at the minimum threshold). The inductor's average current is then 11.69 A.

**At 12–13 V (buck or buck-boost):**
- The output is valley-limited at **≥8.25 A min**.

**So the as-built converter can deliver ≈8.3–8.8 A**, which covers the 7.64 A sum of downstream limits.
- The "~3.2 A" figure only applies if the FPS 16 mΩ input limit is fitted: 3.56 A max × V × 0.9 / 12 gives **2.40 A at 9 V** and 3.20 A at 12 V.
- **The real +12V constraint is on the input side:**
  - 7.64 A × 12 V / (η 0.9 ASSUMED × 9 V) = **11.3 A at 9 V**.
  - 8.5 A at 12 V, 7.8 A at 13 V.
  - All of these exceed F1's 10 A ATO rating, or about 8 A derated at 149 °F (65 °C).

### Final per-rail targets (12 V system; the governing case is listed)
| Rail | I at 9 V min | I at 12–13 V | Label / source | Governing | Width outer 18 °F (36 °F) | F+B each, 18 °F | Vias 0.3 / 0.2 per change |
|---|---|---|---|---|---|---|---|
| VBAT_F / F1 / VBAT_P trunk to Q3 | demand 11.3 + outputs; **capped by F1 10 A** | 8.5 + outputs; F1 10 A | F1 10 A (BOM; Ethan); ~8 A at 149 °F derated (given) | 9 V input, capped at the fuse → **10 A** | 7.19 (4.72) | 2.77 | 14 / 18 |
| VBAT_P → U2 VIN (Q3 drain, U2.2/.3) | 11.3 A demand; 11.69 A at the converter limit | 8.5 / 7.8 A | DERIVED above | 9 V; capped by F1 → **10 A** | 7.19 (4.72) | 2.77 | 14 / 18 |
| BB_SW1, BB_SW2, BB_CS, L1, R12 (power stage) | IL avg 11.69 A at the limit; peak up to 17.5 A | ≤ valley + ripple, about 8.25–11.75 A | DERIVED, D p7/p16 | 9 V → **11.7 A** | 8.93 (5.87); keep as compact pours | 3.43 | 16 / 21 |
| +12V trunk (U2 → branches) | 7.64 A sum of limits (converter can give 8.77) | 7.64 A (converter ≥8.25) | DERIVED | Not battery dependent. **Width NOT decided here** (see options) | 4.96 (3.26) at 7.64 A; 1.73 (1.14) at 3.6 A realistic | 1.91 at 7.64 A | 11 / 14 at 7.64 A |
| +12V → U3 (+5V buck) | 2.61 A | 2.61 A | DERIVED (turn 2) | — | 1.15 (0.75) | — | 4 / 5 |
| +12V → U4 (+3V3 buck), ≥3 A copper on +3V3 | 0.92 A (3 A × 3.3 / (12 × 0.9)) | same | DERIVED | — | 0.33 | — | 2 / 2 |
| ROUTER_12V (U16, J8) | 2.0 A | 2.0 A | TPS1H200 limit [DN:406] | — | 0.78 (0.51) | — | 3 / 4 |
| EXP_12V (U15, J7) | 1.5 A | 1.5 A | DERIVED limit | — | 0.52 | — | 2 / 3 |
| U24 input / VLED | 1.08 A / 0.36 A | same | panel DS l.256/292; η ASSUMED | — | 0.31 / 0.15 | — | 2 / 2 |
| +5V trunk (L2) | 5.64 A | 5.64 A | DERIVED limits | — | 3.27 (2.14) | 1.26 | 8 / 10 |
| +5V_CM5 | 3.76 A | 3.76 A | TPS2121 ILM (kept) | — | 1.87 (1.23) | 0.72 | 5 / 7 |
| +3V3 | ≥3 A | ≥3 A | REV3 target | — | 1.37 (0.90) | 0.53 | 4 / 6 |
| +3V3_SAFE / +3V3_BK | 0.55 A | 0.55 A | DERIVED/ASSUMED | — | 0.25 | — | 1 / 1 |
| +1V8_DSI, CM5_3V3, +3V3_AC, +5V_TRIP | ≤0.12 A each | same | DERIVED | — | 0.15 OK | — | 1 / 1 |
| USB0_5V / USB1_5V | 0.71 A | 0.71 A | TPS2553 limit | — | 0.25 | — | 1 / 2 |
| U5 LMR36506 input (VBAT_P) | 0.6 × 3.3 / (9 × 0.85 ASSUMED) = 0.26 A | 0.19 A | DERIVED | 9 V | 0.15 OK | — | 1 / 1 |
| 15 outputs + ESTOP_TRIP_OUT (from VBAT_P) | 2.99 A / 2.55 A | same | TPS1HTC30 ICL [p8] | Current limit, not battery dependent | 1.36 (0.89) / 1.09 | 0.52 | 4 / 6 (ESTOP 4 / 5) |
| FUEL, CRANK branches (per channel) | 15 A | 15 A | design_spec:25. A solenoid is resistive, so it draws **most at 12–14.4 V**, not 9 V (INFERRED) | 12–14.4 V | 12.59 (8.26) | 4.84 | 20 / 27 |
| VBAT_ESTOP J23 node (fuel + crank at once, Q4b) | 30 A | 30 A | 2 × 15, planning node | 12–14.4 V | 32.7 (21.5) | 12.59 | 40 / 53 |

**Where the low battery (9 V) is the worse case:**
- VBAT_F, F1 and the VBAT_P trunk.
- VBAT_P → U2 VIN.
- The LM5176 power stage: BB_SW1, BB_SW2, BB_CS, L1, R12 (boost mode, highest average inductor current).
- The U5 LMR36506 input.
- The LM5176 output limit itself is *lower* at 12 V (≥8.25 A valley-limited) than at 9 V (8.77 A). Both are above 7.64 A, so it does not govern.

**Where nominal 12–14.4 V is the worse case:** FUEL, CRANK and the J23 30 A node (resistive solenoid loads).

**Not dependent on battery voltage (regulated or current-limited):** all +12V/+5V/+3V3 rails and the 16 output channels.

### Rails that cannot reach their target on the current outline
These use the REV2 straight-line corridors, pads-only; bent routes were not measured.
- **J23 30 A node:** needs 12.59 mm per layer on F+B. F has 13.38 mm toward R297 but only 12.97 mm toward R303. B is blocked by the bottom-side power stage (J23, R295 and others). **It cannot reach 30 A at 18 °F with F alone (32.7 mm)**, and B is blocked. Options: a 36 °F rise with F+B at 8.4 mm each; inner-layer help (inner needs about 4.8× the width); or moving B-side parts.
- **CRANK Q47→J23:** F 7.07 mm against 4.84 mm F+B each. F is fine, but B is blocked straight (D68/D71/R303). F alone needs 12.59 mm and has 7.07, so it fails unless B pours flow around the parts. FUEL and Q48 are the same: F 9.7–10.9 mm, B straight blocked.
- **VBAT_P / power stage at 10–11.7 A:** today it is 0.3 mm tracks / 0.75 mm In2 to the loads, and BB_SW1 is 0.5 mm. The free area around U2/Q3–Q6 was not measured this revision (another executor has scratch work in `scen/vbatp/`). **UNVERIFIED whether 7.2–8.9 mm single-layer, or 2.8–3.4 mm F+B, fits.**
- **GLOW_OUT and AUX10_OUT:** 0 mm straight. **MCB_OP_OUT:** 1.26 mm, against 1.36 mm needed. Detours are needed (REV2).

### +12V rail problem: OPTION LIST (for decision; trunk width is not decided)
The problem, restated:
- The as-built converter **can** supply ≈8.3–8.8 A.
- The constraint is battery-side: 7.64 A out needs 11.3 A at 9 V (8.5 A at 12 V), against F1's 10 A (≈8 A derated). That is before any VBAT_P output channel is on.
- Fitting the FPS 16 mΩ input limit would instead cap +12V at 2.40 A (9 V) to 3.20 A (12 V), below the 7.64 A sum of limits.

**(1) Loads that are never on at the same time** (facts only; no normal-operation shedding):
- Schematic: no +12V loads are mutually exclusive. U15 (EXP), U16 (router), U24 (backlight), U3 and U4 have independent enables (MEASURED nets). The only hardware exclusivity is TPS2121 IN1/IN2, which is on the 5 V side.
- INFERRED: the downstream limits are fault values, not loads. Realistic simultaneous draw is about 3.6 A out (CM5 0.9 A typical, panel 0.21 + backlight 1.08 A, router and EXP UNKNOWN; FW-Q7). The 7.64 A is reached only if several branches sit in current limit at once, which is a fault case.
- So: size the trunk for the faults the hardware allows, or for realistic load plus one branch in limit. The decision needs FW-Q7 (real router and EXP current).

**(2) Loads that could move off +12V (to VBAT_P):**
- **Router and EXP (U16/U15 TPS1H200A, 3.4–40 V operating [tps1h200a p1]):** feeding them from VBAT_P removes 3.5 A from the converter (+12V demand 7.64 → 4.14 A).
  - Battery-side totals are almost unchanged: at 9 V, 4.14 × 12 / (0.9 × 9) = 6.1 A, plus 3.5 A direct = 9.6 A, against 11.3 A. Only the conversion loss is saved.
  - The router and EXP loads would then see 9–14.4 V (and up to 31 V at OV), which needs their input range (UNKNOWN).
  - Net: it relieves the converter and power-stage copper, not F1 or VBAT_P.
- **Backlight TPS61500: cannot move.** Its VIN max is 18 V (abs 20 V) [design_spec:140], and VBAT_P can reach 31 V.
- **U3 and U4 (TPS56637 VIN max) on VBAT_P:** UNVERIFIED; VIN max was not re-read. That would also lose the buck-boost hold-through at 9 V.

**(3) Converter or part changes** (each needs the lead's approval; numbers DERIVED):
- **(a) Leave it as built.** No input limit; the converter limits at 8.77 A out at 9 V. F1 then does the battery-side protection and the copper must carry 10 A (the table above). The converter can then draw above the derated F1.
- **(b) Fit an input-limit sense resistor sized to F1.** RSNS = 57 mV / 8 A ≈ 7.1 mΩ gives an ICL of 6.0/7.0/8.0 A [Eq. 4, D p17; VSNS 43/50/57 mV, D p7]. The guaranteed (min-threshold) +12V output is then 6.0 × 9 × 0.9 / 12 = **4.05 A at 9 V** and 5.4 A at 12 V.
  - Same VIN_BB layout change as final_power_spec §2: about 2 × 2512 parts plus a new island.
  - The 16 mΩ value gives 2.40/3.20 A and is too low for the realistic 3.6 A at 9 V.
- **(c) Raise F1 and the copper together**, e.g. a 15 A ATO in the same clips. Ethan's 10 A requirement stands, so this is listed only. Copper would then need about 12.6 mm single layer, or 4.84 mm F+B.
- **(d) Change R12 (cycle-by-cycle limit):** this alters the inductor and short-circuit current, not the average input. 8 mΩ already gives ≥8.25 A out. Raising R12 to 10 mΩ (D p7 thresholds → valley 6.6 A, peak 10 A) gives about 6.9 A out at 9 V ((10 − 0.81) × 0.75). That is below 7.64 A but above the realistic 3.6 A. It lowers L1/BB stress, and power-stage copper could then target about 9.2 A.
- **(e) Bigger or second converter:** not needed for capability (the as-built limit already covers 7.64 A). It does not help the F1/VBAT_P constraint.
- **(f) Router/EXP to VBAT_P:** see (2).
