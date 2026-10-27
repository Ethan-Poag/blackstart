# ROUTING_PLAN — genctl_v4_handrouted (m7-wip)

**PLAN ONLY. NO ROUTING STARTED.** This commit changes no board, schematic, copper, or rules.

- Board: `mechanical/pcb_v4/genctl_v4_handrouted.kicad_pcb` at 8ccfa7c.
  - md5 d971c3af428c95042d132aab9522f452.
  - 6 copper layers: F.Cu / GND1 / SIG_In2 / PWR / GND2 / B.Cu.
  - Bounding box 284 × 210 mm; outline area 59 416 mm².
- Written 2026-10-26, about 9:20–10:30 PM HST.
- Labels:
  - **[M]** measured this session on a scratch copy;
  - **[M-prev]** measured earlier, cited from PROGRESS.md or routing-lab REPORT.md;
  - **[I]** inferred;
  - **[A]** assumed;
  - **[E]** estimate;
  - **[R]** reported in the brief and not re-measured here.
- Temperatures are in °F.

Ethan's rules govern this plan:
- Component changes are decided **before** routing continues.
- Board growth is the last resort.
- Place and route together, iteratively.
- Free autorouters only on plain low-speed nets (the 111-net allow list), with honest reporting of what they routed.
- Never relax 600 V isolation: 3 mm outer / 1.5 mm inner, barrier slots, `/workspace/compliance/hv_layout_rules_600V.md`.
- Never invent data.

---

## 1. Recount of the 659 unconnected [M]

### Method
- **Scratch copy only:** `/workspace/m7/rp/`, with the board plus .kicad_pro/.kicad_dru copied beside it.
- **Refill:** `refill.py` (pcbnew ZONE_FILLER in its own process) printed "refilled 33". The md5 was unchanged by the refill, so the committed fills are current.
- **Per-net count, `rn2.py`:**
  - `BuildConnectivity()`, then union-find over the direct `GetConnectedPads/GetConnectedTracks` neighbours of every pad, track and via.
  - **Every zone filled island on every layer is its own node.** An item joins an island only if its layer shape collides with that island polygon.
  - Per net, opens = (number of copper clusters) − 1.
- **Result:** the sum over nets is **659**, equal to `GetUnconnectedCount(True)` = 659. The two counts agree exactly.
  - Of these, 642 are pad-to-pad island opens. The other 17 involve copper-only clusters: zone islands or stub tracks with no pad.
  - DRC's `unconnected_items` reports 499. That is DRC's own grouping, not used here.
- **Classification, `cls.py`.** The first matching rule wins, in this order:
  1. **HV/hot:**
     - netclass HV_LINE, or
     - any pad on the hot side of the barrier (x < 60.0 mm and 11.0 < y < 162.0 mm, taken from the BARRIER_* rule areas, the same rule as routing-lab `allow.py`), or
     - name GND_AC or +3V3_AC.
  2. **VBAT_P.**
  3. **GND:** exactly `GND`.
  4. **diff:** netclass DIFF100 or DIFF90.
  5. **power:**
     - netclass PWR, or
     - a short name (last hierarchical segment) that matches either of these:
       - starts with `+`, `VBAT` (not VBAT_SNS), `GND_` (isolated grounds), `CHASSIS`, `VLED`, or `BB_BOOTn`;
       - ends with `_5V`, `_12V`, `_3V3`, `VCORE`, `_SWn`, or `_OUT` (load outputs; ESTOP_TRIP_OUT excluded).
     - Nameless `Net-(..-BOOT|SW|VISO|VDDA)` nets also count as power.
  6. **nameless:** `Net-(...)` or `unconnected-(...)`. No `unconnected-(...)` net has an open.
  7. **signal:** everything else.
- Hierarchical names are matched on their last segment, after the final `/`.

### Class table [M]
| Class | Nets with opens | Opens | Top nets (opens) |
|---|---|---|---|
| signal | 121 | **254** | OUT_FAULT_N 23, DIAG_EN 16, I2C1_SDA 11, I2C_INT_N 7, BB_CS 7, NRST 5, DPLUS_SNS 5, BOOT0 4, AI2 4, DI_BIAS_B 4, USB_SVC_N 4, VBAT_SNS 4 |
| power | 41 | **188** | +3V3 26, +1V8_DSI 23, VBAT_ESTOP 21, CM5_3V3 16, CRANK_OUT 14, +5V 12, +5V_CM5 11, CHASSIS 10, +3V3_PANEL 5, +3V3_TOUCH 5, +3V3_BK 5, U7-VDDA 3 |
| HV/hot | 44 | **88** | GND_AC 7, +3V3_AC 4, BUS_VN_TAP 4, GEN_L3 3, GEN_N 3, GEN_VN_TAP 3, BUS_L3 3, ADE_XO 3, then 2 each on the GEN_I*/GEN_CT*/REF_*/U71-U72 LDO nets, then 1 each on CT1..CT4_S1/S2 and the GEN/BUS_V*_N nets |
| VBAT_P | 1 | **62** | 61 pad-island opens plus 1 copper-only island |
| GND | 1 | **28** | — |
| nameless | 10 | **21** | D68-A1 4, D15-K 3, U11-EN 3, D46-A1 2, U24-OVP 2, C74-Pad2 2, D3-A 2, U22-CT 1, Q42-G 1, D22-A 1 |
| diff | 17 | **18** | LVDS1_P 2; 1 each on LVDS0_P/N, LVDSC_P/N, USB30_DP/DM, ETH0–3_P/N, DSI_D0_P, DSI_D2_P |
| **Total** | **235** | **659** | |

- **HV_LINE netclass opens:** GEN_L3 3, GEN_N 3, BUS_L3 3. HV opens A/B by hvopen2.py are 7/23 [M-prev, unchanged at 8ccfa7c].
- **Comparison with the reviewer's inferred split:** signal ~313 / power ~117 / hot ~71 / VBAT_P 70 / nameless ~33 / GND ~28. The totals differ mainly through the class rules: the hot side here is geometric, and the load outputs and rails count as power. VBAT_P measures **62**, not 70. GND agrees at 28.

### Autorouter-eligible nets (the 111-net allow list) [M]
- Source: `/workspace/routing-lab/runs/8ccfa7c/allow/allow.json`, built by allow.py (the Enginerd rule).
- **77 of the 111 are already complete.** Only **34 nets / 58 opens** remain, all in the signal class:
  - I2C1_SDA 11, BOOT0 4, I2C1_SCL 4;
  - 2 each on MCU_IRQ, DISP_SCL/SDA, CM5_NRPIBOOT, DI12_D, MPU_PH, MCU_CM5_HB, MUX_A2;
  - 1 each on MCU_SPI_*, MCU_UART_*, BTN1/10/11/12, WDI, AUX7/8_MCU, ESTOP2_DIG, DI2_D, DI3_D, GLOW/AUX8/AUX10_SNSM, CM5_SPI_MISO, CM5_NRST, HDRA_SPI_CE0, AI_CS_DIS2.
- **The autorouter can therefore remove at most 58 of the 659 opens (8.8 %).**
- Under the filtered allow list, its measured gain so far is **0** [M-prev, REPORT.md "8ccfa7c rebase"]: every A/B candidate's added copper failed the build.py clearance/courtyard filter.
- WDI has an exact CP-SAT infeasibility proof with the other copper fixed [M-prev, REPORT §21.4]. It needs rip-up or a part move.

## 2. Strategy per class

### Current and width basis [A/I]
- IPC-2221 at 18 °F (10 °C) rise.
- **1 oz outer / 0.5 oz inner, ASSUMED**: the board file defines no stackup.
- Rough external 1 oz widths, IPC-2221 [I]: 0.5 A ≈ 0.15 mm; 1 A ≈ 0.3 mm; 2 A ≈ 0.8 mm; 3 A ≈ 1.4 mm; 5 A ≈ 2.9 mm.
- Internal 0.5 oz needs about 2.6× the external 1 oz width at the same current [I].

| Class | Assumed current per net [A] | Layers / method | Width / vias | Ordering |
|---|---|---|---|---|
| GND (28) | return only | Stitch to the GND1/GND2 planes with a via at the pad | 0.3/0.15 or 0.4/0.2 via, short neck ≥ 0.3 mm | **1st** |
| VBAT_P (62) | 10 A system rating [A] | F.Cu pour + In2 plane, stitching vias | pours, not tracks | **1st** (safety/power) |
| power rails: +3V3 / +1V8_DSI / CM5_3V3 / +5V / +5V_CM5 / +3V3_* (≈110) | +3V3 ≤ 1 A, +1V8_DSI ≤ 0.3 A, CM5_3V3 ≤ 0.6 A, +5V 4.7 A, +5V_CM5 ≈ 3 A [A] | outer tracks; In2 only for short hops; existing pours where present | 0.3–0.5 mm low-current rails; +5V ≥ 2.7 mm, +5V_CM5 ≥ 1.4 mm [I] | 2nd |
| VBAT_ESTOP (21), CRANK_OUT (14), *_OUT loads, CHASSIS (10) | outputs 2 A each, CRANK/FUEL 15 A [A]; CHASSIS: ESD/shield only | outer layers; pours for CRANK | outputs 0.8 mm; CRANK pour; CHASSIS 0.5 mm | 2nd |
| HV/hot (88) | signal level except the line nets (mA) | B/F on the hot side only; respect 3 mm outer / 1.5 mm inner, the barrier slots and J28/J29 conditions | 0.25 mm (ADE analog), lines per HV rule file | **3rd, after power**; each batch is a creepage check |
| signal (254) | < 50 mA | F.Cu/B.Cu + SIG_In2 | 0.15–0.2 mm | 4th |
| nameless (21) | local (diode/FET/EN nodes) | local single-layer | 0.2–0.3 mm | with their owner block |
| diff (18) | — | keep existing locked pair copper; finish the last segment as a pair | per netclass (DIFF100/DIFF90), symmetric vias | last, with the skew recheck |

### Can each class be completed without part moves or board growth?
**Headline [M + I]:** total copper area is **not** what limits routing; local congestion and the HV geometry are.
- **Free area per layer [M]**, after pads and tracks get a 0.15 mm halo:

  | Layer | Free (mm²) | Occupied |
  |---|---|---|
  | F.Cu | 49 211 | 17 % |
  | SIG_In2 | 32 564 | 45 % (VBAT_P plane included) |
  | B.Cu | 45 050 | 24 % |
  | GND1 / PWR / GND2 | ~6 000 each | 90 % (planes) |

- **Demand [M]:** the Euclidean pad-cluster MST length of all opens is **15.8 m**:

  | Class | MST length (m) |
  |---|---|
  | signal | 9.24 |
  | power | 3.88 |
  | HV/hot | 1.51 |
  | diff | 0.42 |
  | VBAT_P | 0.34 |
  | nameless | 0.28 |
  | GND | 0.14 |

  Real routes are longer: ×1.3–1.6 [E].
- **Comparison [E]:** at a 0.30 mm pitch (0.15 mm track plus 0.15 mm gap), 15.8 m × 1.5 needs about 7 100 mm². That is under 6 % of the raw free outer/In2 area.
- **The routers' record [M-prev]:** they still stall locally.
  - Best gated results were 64/196 jobs (fd4a608 B, unconnected 659 → 638).
  - Negotiated ordering oscillates between the U21 LVDS escape and the U72 SPI/XTAL sets.
  - WDI is proven infeasible with the other copper fixed.

| Class | Without moves / growth? | Reason (label) |
|---|---|---|
| GND 28 | **Yes, likely** [I] | Via drops to two planes; the planes are 90 % filled |
| nameless 21 | Yes, likely [I] | Local nodes inside their own blocks |
| diff 18 | Yes for connectivity [I]; skew-with-vias is already NOT met [M-prev] | Last segments only |
| signal 254 | **Mostly, with rip-up**; not all [E] | Ceiling of 58 opens for the autorouter; WDI infeasible as placed; U7 escape: 31 open MCU signal nets with far ends 22–113 mm [M]. Estimate: 10–30 opens will need a passive nudge or a pin remap [E] |
| power rails 188 | Connectivity yes [I]; **current targets no** for +5V (0.50 mm neck ≈ 1.8 A vs 4.7 A) and the outputs (0.15 mm necks ≈ 0.5 A vs 2 A) [M-prev] | Pinch points need rerouting; see §5 |
| CRANK/FUEL drains | **No at 15 A in this area** [M-prev/I] | 12.6 mm is needed at the 2512 shunt pad at 1 oz; branches measure 6.6–9.4 A each |
| +12V trunk | **No at 3.7 A ASSUMED** [R] | 3.2 A capacity vs 3.7 A assumed load (brief; not re-measured here) |
| VBAT_P 62 | Connectivity yes [I]; **10 A no** | Q2→Q3 In2 hop ≈ 1.8 A by IPC internal (In2-only FEM ≈ 2.3 A), and VBAT_F F1→Q1 ≈ 9.9 A [M-prev/I]. Fixes: 2 oz outer / 1 oz inner, a lower rating, or area |
| HV/hot 88 | **No for at least 7 HV_LINE opens (hvopen2 A = 7)** [M-prev + decision] | RV3 has no legal 600 V path (GEN_L3/GEN_N would cross BUS HV copper; growth declined, HV_ACCEPTED_DEVIATIONS.md); the GEN_L1 divider chain walls J28.1 off. The other ~81 hot-side LV opens (ADE, CT, LDO, XO) are routable inside the hot region [E, unverified] |

**Cannot be completed in the current area, with today's placement and stackup:**
1. **HV:** at least 7 HV_LINE opens (hvopen2 A), including the RV3 pads.
2. **VBAT_P and CRANK/FUEL:** current capacity, not connectivity. 1.8 A vs 10 A; 6.6–9.4 A per branch vs 15 A.
3. **+12V trunk:** 3.2 A vs 3.7 A [R].
4. **Signals:** an estimated 10–30 opens need moves or a pin remap [E].

Everything else is estimated completable with rip-up. That estimate is not yet backed by a trial.

## 3. Batch plan
- **Batch size:** ≤ 10 nets or ≤ 25 opens, from one class and one board region per batch.
- **Order:**
  1. GND;
  2. VBAT_P;
  3. power rails, then outputs;
  4. HV/hot (Compliance review per batch);
  5. nameless with their blocks;
  6. signals, region by region: U7 MCU, U21 display, CM5, outputs, inputs;
  7. the autorouter pass on the remaining allow-list nets only;
  8. diff last.
- **Gate after every batch** (the mandatory procedure):
  1. Refill ALL zones with pcbnew ZONE_FILLER in its own process: `refill.py <committed path>` must print "refilled 33" (or the current zone count). Save in place.
  2. Byte-copy the saved file (md5 equal to the committed file) next to the pro+dru. Delete the old JSON first.
  3. Run DRC one at a time and check exit codes:
     - project rules: 0 errors;
     - no custom rules: 0 errors, copper_edge 0.
  4. KiCad unconnected (`cnt.py`) must drop by at least the batch's planned opens. Run the per-net recount `rn2.py`.
  5. HV opens A/B (`hvopen2.py`): must stay ≤ 7/23. Also hvsheet = 0, dangling vias ≤ 12, viachk 0 bad, slot-edge 0, slot-corner ≤ 1 (locked).
  6. Courtyards by KiCad polygons (`cyo.py`): total 0.
  7. Diff vs the parent commit, categorised (fill vs non-fill lines).
  8. Reviewer verification, then commit, then push m7-wip (fast-forward only).
- **STOP a batch and report on any of:**
  - a new DRC error in either rule set;
  - any change to HV copper, HV rules, rule areas or slots;
  - unconnected not decreasing by the planned amount, or any increase;
  - hvsheet > 0 or HV A/B up;
  - a needed part move, footprint change or board growth (a decision for Ethan);
  - a zone piece count going up (a plane split);
  - DRC running over 10 min (it points to unrefilled zones).

## 4. Effort and risk [E]
**Assumptions:**
- One operator with scripted gates.
- A measured gate takes about 6 min: refill plus 2 DRCs 79 s, gate scripts 273 s [M].
- 2–4 batches per day of manual routing, including review.
- No part moves inside these ranges.

| Work | Days (range) | Risk |
|---|---|---|
| GND + nameless | 0.5–1 | low |
| VBAT_P connectivity | 0.5–1.5 | medium (via field vs pours) |
| Power rails + outputs (connectivity) | 2–4 | medium; widths limited at pinch points |
| HV/hot (81 LV opens) + Compliance review | 2–4 + review wait | high (creepage) |
| Signals (254) incl. the autorouter pass (≤ 58) | 4–8 | high at U7/U21/U72 escapes |
| Diff last segments + skew recheck | 0.5–1.5 | medium |
| **Total** | **≈ 10–20 working days** | excludes the current-capacity fixes, which need decisions |

### Wanted before starting
- **Mechanical:**
  - final keepouts and component height limits per side;
  - shell posts and screw-boss positions;
  - whether any extra board area or edge relief is available (last resort);
  - J2 programming access (the enclosure must be open).
- **Compliance:**
  - hot-side rules for the ADE/CT LV nets inside the hot region;
  - the RV3 decision (stay unrouted, or move it with a growth or placement study);
  - J30 and T1–T4 creepage status;
  - acceptance of RV1–RV6 placement;
  - review of the c41fce7 HV reroute;
  - the copper weight decision (2 oz/1 oz) for VBAT_P, CRANK and +12V.
- **Firmware:** the nets show 31 open MCU (U7, STM32H743VIT6) signal nets. Any pin swap or AF remap that moves a far end closer would help. Candidates by measured far-end distance:

  | Net(s) | Far end (mm) |
  |---|---|
  | OUT_FAULT_N | 113 |
  | RS485_RX / RS485_TX | 109 / 106 |
  | MCU_CM5_HB | 107 |
  | I2C_INT_N | 106 |
  | DIAG_EN | 106 |
  | I2C1_SDA / I2C1_SCL | 101 / 100 |
  | MCU_SPI_* | 91–100 |
  | MCU_UART_* | 90–93 |
  | CAN1_TX / CAN2_TX | 76 / 84 |

  I have not checked which alternate pins are actually possible. That is for Firmware.

## 5. Lessons that shape this plan
- **Stale zone fills were once committed** (c8caadf..fd4a608). From now on, refill and save, then DRC the saved file.
- **Unrefilled boards make DRC hang** about 40 min [R]. A long DRC run is a stop signal.
- **`tools/netcompare.py` compares nets only.** It missed 36 reverted fields, so every regeneration also needs the full field diff plus ERC on the root sheet.
- **Courtyards must be checked as KiCad polygons**, after `BuildCourtyardCaches()`, not as bounding boxes. Bboxes read as 0 or overstate.
- **Router candidates need the .kicad_pro beside the board.** Without it, the zone fill ignores HV_LINE (the invalid FG_A/FG_B result: 204 errors, hvsheet 54).
- **KiCad 9.0.2 applies one edge-clearance value per item**, so slot and outer-edge rules can't both be expressed in DRC. Use the slot scripts.

## 6. Known open items NOT covered by this plan
- U2.24 BIAS is open by decision; the schematic ties it to +12V, a known mismatch.
- 12 dangling vias.
- 153 thin segments [R; not re-measured here].
- Every *_OUT has 0.15 mm bottlenecks; +5V has a 0.50 mm neck.
- Diff skew including vias is not met.
- The USB31 pair was not rerouted.
- RV3 is unrouted (accepted deviation).
- J11 courtyard: R107 is 0.009 mm from the J11 shield pad.
- The slot-corner item (1, locked).
- 63 hole_to_hole DFM items, recorded under the severity change.
- L1 is NRND.
- Burden accuracy is undetermined.
- C7471020 stock is unknown.
- The +12V 3.7 A load is ASSUMED, and loop stability is unverified (BENCH_12V_TEST.md).

## Not verified here
- The +12V trunk 3.2 A, 153 thin segments and the 40-minute hang: taken from the brief, not re-measured.
- That the 81 hot-side LV opens are routable.
- The 10–30 signal opens needing moves.
- All day estimates.

Scratch scripts for the recount: `/workspace/m7/rp/{rn2.py,cls.py,cap.py,occ.py}`. They are not committed.

## 7. Routing Batch 1 — status, budgets, targets (2026-10-26, HST)

Tags: [M] measured on the committed board, [I] inferred, [A] assumed.

### 7.1 Current budget used for Batch 1 copper [A/I]
- Basis: IPC-2221, I = k·ΔT^0.44·A^0.725, k 0.048 outer / 0.024 inner, ΔT 18 °F. Copper 1 oz outer / 0.5 oz inner **ASSUMED** (no stackup defined). Source table: /workspace/review/cur/current_budget.md.
- GND pad-to-plane links (Batch 1a): 0.30 mm outer track (~1.0 A at 18 °F [I]) + one 0.6/0.3 via (0.76–0.90 A [I]) or 0.45/0.2 via (0.57–0.67 A [I]). Assumed current per link: return of a signal/decoupling pad or a connector GND pin carrying ≤0.5 A [A]. Connector GND pins (J1/J7/J8/J18/J21/J25/J27) carry their circuit return through one via each; if any connector return exceeds ~0.8 A this is NOT sufficient [I] (not checked per pin).
- VBAT_P: known capacity ~1.8 A through In2 effective width (Q2→Q3 In2 1.384 mm ≈ 0.92 A at 18 °F per current_budget.md). Nothing in this file claims more.

### 7.2 Power targets for the later power batch (NOT routed; lead must confirm the power batch) [A]
Assumptions: 18 °F rise, 1 oz outer / 0.5 oz inner ASSUMED, no stackup defined. System rating: **"fuse 10 A, continuous 8 A or less"**.

| Net / branch | Current | Min width | Layers | Stitching | Status |
|---|---|---|---|---|---|
| VBAT_F / VBAT_DD existing copper | ≤8 A cont. | existing (VBAT_F ~9.9 A [I], VBAT_DD 5.29 mm B ≈ 8.0 A [I]) | existing | existing | OK up to 8 A continuous |
| VBAT_P Q2 (260,165) → Q3 (227,140), ~41 mm | ≤5 A per layer | ≥2.9 mm each | F.Cu + B.Cu pours (+ In2) | ≥8 vias each end | see 7.3 |
| Crank/fuel branches, VBAT_ESTOP → shunts/FETs → J23 | 15 A real | ≥6.3 mm each, or 4.2 mm at 36 °F | F + B pours | per pour | OPEN — power batch |
| +12V trunk | — | ≥1.9 mm | outer | — | OPEN — power batch |
| +5V L2 → every +5V load | — | ≥1.4 mm (2.6 mm for 4.7 A) | outer | — | OPEN — power batch |
| Outputs U47–U61 | — | ≥0.3 mm each; 1.37 mm for full limit; 1.0 mm where room | outer | — | OPEN — power batch |
| U68 ESTOP_TRIP | 7.5 A pulse ~2.2 s | 1.2 mm In2 feed now; widen to ≥2 mm if easy | In2 | — | NOTE: not widened in Batch 1 |

### 7.3 RV3 — documented exception (bodge wire)
- Do NOT route the 124 mm inner-layer GEN_L3 run (J28.3→RV3.1) or the 125 mm GEN_N run at +1.0 mm margin on a 1.5 mm rule.
- RV3 is wired with a **600 V insulated bodge wire, ≥0.5 mm², sleeved and tied down, ≥12.6 mm from SELV**.
- **Until it is wired, the GEN input has NO surge protection.**
- Also recorded in PROGRESS.md and docs/BENCH_12V_TEST.md (no dedicated bring-up checklist exists in docs/; BENCH_12V_TEST.md is the closest bench doc).

### 7.4 Hot-side / HV batch — recorded approach only (not started; lead confirmation required)
Cut back and re-pour hot zones; HV on inner layers; nudge R436/R443 if needed; no vias in barrier areas; 6.6 mm L-L and 5.5 mm L-N outer, 1.5 mm inner, 12.6 mm hot-to-SELV, 6.6 mm to edge. HV opens A/B (7/23) untouched in Batch 1.

### 7.5 Status table — opens per class (rn2.py/cls.py union-find; KiCad GetUnconnectedCount) [M]
cls.py counts on the gated boards (its signal split differs from §1: 138 nets / 272 opens; same tool both columns).

| Class | 2f4c9ec | Batch 1a |
|---|---|---|
| signal | 272 | 272 |
| power | 188 | 188 |
| HV/hot | 88 | 88 |
| VBAT_P | 62 | 62 |
| GND | 28 | **5** |
| nameless | 21 | 21 |
| **KiCad unconnected** | 659 | **636** |

### 7.6 Batch log
- **Batch 1a — GND (this commit, parent b84eb0e):** 23 GND pad-to-plane links (0.30 mm track + via; 22 × 0.6/0.3, 1 × 0.45/0.2 at U21 D5) into the GND1/GND2 fill. Zones refilled (33). Gate [M]: DRC 0 errors with project rules and with pro-only rules (unconnected_items 499 both before/after); KiCad default-rules DRC timed out at 25 min before and after (NOT MEASURED); HV opens A/B 7/23 unchanged; hvsheet 0; dangling vias 12; viachk 23 checked 0 bad; slot-edge 0, slot-corner 1 (unchanged); courtyard overlaps 0; isl.py unchanged; VBAT_F necks F 2.435 / B 1.999 mm unchanged. VBAT_P fill −39.1 mm² of 21 664 mm² (−0.18 %, accepted by the lead under 0.5 %); VBAT_P Q2→Q3 In2 neck (review/cur scripts/neck.py, erosion) 1.384 mm on HEAD, 1.384 mm with the new vias, 1.384 mm with the six vias near Q2 (x 268–274, y 160–168) removed → unchanged.
- **Remaining GND opens (5): R115.2, U70.2, R204.2, U21 B9, U21 H9 — needs a part nudge or via-in-pad decision** (no legal via site within ~4 mm at 0.15 mm clearance without via-in-pad).
