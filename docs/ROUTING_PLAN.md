# ROUTING_PLAN — genctl_v4_handrouted (m7-wip)

> **SUPERSEDED (N4, m7-sch 3c, 2026-10-28):** the schematic has no on-board fuse; battery net BAT_IN; installer fits an external fuse <=10 A fast-acting, >=58 V DC in the battery lead. Every F1 / VBAT_F / "fuse F1 10 A" / "10 A ATO" mention in this file describes the as-built .kicad_pcb (which still carries F1 clips and net VBAT_F until the board update) and is historical; the VBAT_F copper becomes BAT_IN when the board is updated. The 10 A copper figures remain a copper-capacity record only.


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
| power rails: +3V3 / +1V8_DSI / CM5_3V3 / +5V / +5V_CM5 / +3V3_* (≈110) | +3V3 copper target ≥ 3 A (derived loads ≤ 1.47 A [DERIVED, docs/RAIL_PLAN.md Rev 4]; U4 TPS56637 capability is the earlier '≥ 3 A'), +1V8_DSI ≤ 0.3 A, CM5_3V3 ≤ 0.6 A, +5V 4.7 A, +5V_CM5 3.76 A (TPS2121 current limit; CM5 design figure 2.5 A, FW 3.2 A from the CM5) [A] | outer tracks; In2 only for short hops; existing pours where present | 0.3–0.5 mm low-current rails; +5V ≥ 2.7 mm, +5V_CM5 ≥ 1.4 mm [I] | 2nd |
| VBAT_ESTOP (21), CRANK_OUT (14), *_OUT loads, CHASSIS (10) | outputs 2 A each, CRANK/FUEL 10 A (Batch 14, was 15 A; 2.8 A per channel electronic limit) [A]; CHASSIS: ESD/shield only | outer layers; pours for CRANK | outputs 0.8 mm; CRANK pour; CHASSIS 0.5 mm | 2nd |
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
| CRANK/FUEL drains | **Marginal at 10 A** (was "No at 15 A") [M-prev/I] | 7.2 mm is needed at the 2512 shunt pad at 1 oz for 10 A (12.6 mm for the old 15 A); branches measure 6.6–9.4 A each, so two FETs in parallel carry ~5 A each at 10 A (INFERRED even split) |
| +12V trunk | **No at 3.7 A ASSUMED** [R] | 3.2 A capacity vs 3.7 A assumed load (brief; not re-measured here) |
| VBAT_P 62 | Connectivity yes [I]; **10 A yes at 18 °F (S3c/c6b, see §8)** [I] | VBAT_P Q2→Q3 F 8.76 / B 4.54 mm (11.5 / 7.2 A; F+B 18.7 A per the reviewer's tight-pad neck method, review/s3c6c/review.md, same on base and c6c; the earlier B 5.22 mm / 7.9 A / F+B 19.5 A was a method artefact, B alone < 10 A, so F+B sharing through the VBAT_P transfer vias is required: VBAT_P vias at the Q2 / Q3 ends, MEASURED with review/s3c6b/via_count.py (all 0.3/0.6 mm vias): primary method via-edge-to-pad-edge (any part of the via pad within r of any edge of the FET pads used: Q2 pads 1-3, Q3 pad 5) 25 / 25 within 5 mm and 40 / 35 within 8 mm; reviewer method via-centre-to-point (via centre within r of Q2 point (254.6, 151.0) / Q3 point (228.02, 140.07)) 17 / 14 within 5 mm and 34 / 25 within 8 mm; identical at 950b8a1 and S3c/c6c; 14 is met at both ends within 5 mm, exactly at the Q3 end), VBAT_DD Q1→Q2 F 7.54 / B 7.51 mm (10.3 / 10.3 A; F+B 20.7 A), VBAT_F F1→Q1 B 8.02 mm (10.8 A, reviewer tight-pad method; B only at Q1; F 8.95 mm before c6c, 1.92 mm after c6c, not counted) [M widths, tneck erosion on gate/s3c6b; amps I by IPC-2221 outer k 0.048 at 18 °F (10 °C) rise, 1 oz ASSUMED]. Superseded: the old In2 hop (≈ 1.8 A) no longer carries VBAT_P |
| HV/hot 88 | **No for at least 7 HV_LINE opens (hvopen2 A = 7)** [M-prev + decision] | RV3 has no legal 600 V path (GEN_L3/GEN_N would cross BUS HV copper; growth declined, HV_ACCEPTED_DEVIATIONS.md); the GEN_L1 divider chain walls J28.1 off. The other ~81 hot-side LV opens (ADE, CT, LDO, XO) are routable inside the hot region [E, unverified] |

**Cannot be completed in the current area, with today's placement and stackup:**
1. **HV:** at least 7 HV_LINE opens (hvopen2 A), including the RV3 pads.
2. **VBAT_P and CRANK/FUEL:** current capacity, not connectivity. VBAT_P now ≥ 10 A at 18 °F with F+B sharing (S3c/c6b, §8); CRANK/FUEL 6.6–9.4 A per branch vs ~5 A per branch at the 10 A target (was 15 A; INFERRED even split, not re-measured).
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
- VBAT_P: superseded by S3c/c6b (§8). The In2 VBAT_P zone was removed; Q2→Q3 now runs on F+B (F+B 18.7 A at 18 °F [I], reviewer tight-pad method; was stated as 19.5 A).

### 7.2 Power targets for the later power batch (NOT routed; lead must confirm the power batch) [A]
Assumptions: 18 °F rise, 1 oz outer / 0.5 oz inner ASSUMED, no stackup defined. System rating: **"fuse F1 10 A; battery-path copper 10 A at 18 °F rise [I]"** (S3c/c6b, §8). Caveat: the 10 A figure is the copper only. Continuous load is also limited by F1: a 10 A ATO carries at most about 8 A at 149 °F (65 °C) ambient (Littelfuse 287 ATOF derating, final_power_spec.md §1; datasheet pages UNVERIFIED). The battery wiring and the mating connector must be rated for the load as well.

| Net / branch | Current | Min width | Layers | Stitching | Status |
|---|---|---|---|---|---|
| VBAT_F / VBAT_DD copper (S3c/c6b) | 10 A cont. | VBAT_F B 8.09 mm ≈ 10.9 A [M/I]; VBAT_DD F 7.54 / B 7.51 mm, F+B ≈ 20.7 A [M/I] | per §8 | per §8 | Copper OK for 10 A at 18 °F [I]; continuous load limited by F1 (10 A ATO ≈ 8 A max at 149 °F (65 °C)) and installer wiring/connector |
| VBAT_P Q2 (260,165) → Q3 (227,140), ~41 mm | ≤5 A per layer | ≥2.9 mm each | F.Cu + B.Cu pours (+ In2) | ≥8 vias each end | see 7.3 |
| Crank/fuel branches, VBAT_ESTOP → shunts/FETs → J23 | 10 A (Batch 14; was 15 A) | ≥3.6 mm each, or 2.4 mm at 36 °F (was 6.3 / 4.2 mm for 15 A) | F + B pours | per pour | OPEN — power batch |
| +12V trunk | — | ≥1.9 mm | outer | — | OPEN — power batch |
| +5V L2 → every +5V load | — | ≥1.4 mm (2.6 mm for 4.7 A) | outer | — | OPEN — power batch |
| 15 small outputs (GLOW, GCB/MCB, AUX1–10; U47–U61) | 2 A external fuse (driver limit 2.49 A) | ≥1.0 mm (no 0.15 mm necks, no In2-only hops) | outer | — | OPEN — with the power batch |
| ESTOP_TRIP_OUT (U68) | relay drive: limit 1.70/2.13/2.55 A (R407 47k), pulse 0.48 s nom (0.44–0.53 s; measure cold/hot); 2 A external fuse (was 7.5 A) | ≥2 mm (target kept at ≥2 mm; relay drive, 2 A fuse); 1.2 mm In2 feed now | outer | — | OPEN — with the power batch |
| FUEL (Net-(D68-A1)), CRANK_OUT, VBAT_ESTOP | 10 A (was 15 A) | the 10 A pours above (≥3.6 mm F+B, or 2.4 mm at 36 °F) | F + B | per pour | OPEN — with the power batch |

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
- **Batch 1b — nameless signal nets (this commit, parent e6d5e70):** Net-(D3-A) 2 opens (C13.1, D4.2; 0.20 mm B.Cu) and Net-(D46-A1) 2 opens (R211.1 and the R210/D46 fragment; 0.25 mm B.Cu, field-input surge net) routed: 58 B.Cu segments, no vias. Gate [M], vs 2dab1e7: DRC 0 errors in project rules and pro-only rules (unconnected_items 499/499 both); default-rules DRC timed out at 25 min (NOT MEASURED); KiCad unconnected 636 → **632**; nameless 21 → 17; all other classes unchanged; HV A/B 7/23; hvsheet 0; dangling vias 12; slot-edge 0 / corner 1; courtyards 0; isl.py, VBAT_F necks (F 2.435 / B 1.999) and VBAT_P fem (12.253 sq) unchanged.
- **Left open in Batch 1b:** Net-(U22-CT) U22.4 (B) ↔ C117.1 (F), 0.77 mm apart on opposite sides: the only via site the router found is inside U22.4 (via-in-pad) → needs a via-in-pad decision. Net-(U24-OVP) (R123.2, U24.11): no legal path at 0.15 mm / 0.12 mm clearance on F or B in the U24 area (router FAIL) → needs rip-up or a part nudge. Net-(Q42-G): R262.1 fragment (y≈12) to R261/Q42 (y≈152) is a ~140 mm cross-board run at ≥0.25 mm and ≥0.3 mm from VBAT copper; not attempted in this batch.
- Excluded from "nameless" as current/power nets (power batch): Net-(D68-A1) (= FUEL_OUT), Net-(D15-K) (router 12 V out, J8.1), Net-(U11-EN) (supercap boost input), Net-(C74-Pad2) (series supercap midpoint), Net-(D22-A) (boost switch node).

### 7.7 Batch 1c — small nudges (≤1.0 mm) [M]
- **Routed:** GND U21 B9 → U21 A8, 0.15 mm B.Cu track, 0.71 mm long (BGA escape; no via, no nudge). GND opens 5 → 4; KiCad unconnected 632 → 631.
- **No nudge made.** Every nudge that was legal on courtyard and pads still left the route blocked:
  - U22-CT: no legal via site on any C117 (dy ±0.5…+1.0) or U22 (±0.25/0, −0.25) nudge; via-in-pad is not allowed → **OPEN**.
  - U24-OVP: R123 nudges up to 0.5/0.75 mm pass courtyard checks, but the router fails (track-caged); R124 has no legal nudge → **OPEN**.
  - R115.2, R204.2, U21 H9 (GND): caged by DI2_D, DSI83_IRQ_1V8, AI_SH_EN4, DI_PD_B and LVDS3 tracks. They need signal rip-up, not a nudge → **OPEN**.
  - U70.2 (GND): U70 is the ISO7741 with a hot +3V3_AC pin, so it is not moved → **OPEN**.
- **Gate:** project and pro-only DRC 0 errors, unconnected_items 499 unchanged. Default-rules DRC timed out at 25 min (not measured). HV A/B 7/23, hvsheet 0, slot-edge 0 / corner 1, viachk clean, courtyards 0, VBAT_F F 2.435 / B 1.999, In2 neck 1.384, fem unchanged.

### 7.8 Batch 1d — rip-up attempts for the boxed-in GND pins (no board change) [M]
Through-via sites within ±1 mm of each pad, checked at 0.15 mm clearance on all 6 layers, 0.45 mm hole-to-hole, landing in GND1/GND2: **0 sites** for R115.2, R204.2 and U21 H9. Other-net copper blocks every site on F, B and In2. Local rip-up and reroute with the grid router (0.15 mm), routing the GND link first (0.30 mm):
- **R204.2 → R209.2 (GND, B):** the link routes (1.74 mm), but DI_PD_B (113 mm, U31.20/R209.1 → Q41.1) then cannot be reconnected. The U31/R209 pocket is sealed even with a 45 × 40 mm search area. **OPEN.**
- **R115.2 → C115.2 (GND, F):** the link routes (1.97 mm), but DSI83_IRQ_1V8 (R115.1/U21.J9 → U79.3) cannot be reconnected (54k cells searched). **OPEN.**
- **U21 H9:** inside the BGA field, under the LVDS2/LVDS3/LVDSC pair vias. Not touched, so pair matching is kept. **OPEN.**
- **U70.2:** stays open (ISO7741, hot side).
- **U22-CT and U24-OVP:** need a bigger change, after the hot-side batch.
These need placement or multi-net rework, not small reroutes.

## 8. S3c/c6b battery-path move — status (2026-10-27, HST)
Accepted by Ethan: c6 (including the S3b Q1/Q2 move) as the 10 A battery path. Design rule 18 °F (10 °C) rise. Scratch work: /workspace/m7/scen/s3c (c6) and /workspace/m7/scen/s3c6b (c6b). Not fab-ready, not certified.
- **Parts moved (all B.Cu, no pad net changes) [M]:** Q1 (255.46,171.45,0° → 257.0,143.5,−90°), Q2 (260.0,165.0,−90° → 257.5,151.0,0°), U16 (→258.4,158.0), R96 (→261.2,156.6,−90°), R97 (→255.4,155.0,180°), C96 (→255.1,158.6,0°), C293 (→251.8,156.6,−90°), C294 (→247.0,156.6,−90°), C295 (→249.4,156.6,−90°), C296 100 nF (→244.6,156.6,−90°).
- **Copper changed vs 0087a67 (uuid diff) [M]:** tracks +76/−286 (219 removed are +12V), vias +109/−127, zones +11/−2/4 modified. Nets: +12V, +3V3_SAFE, GND, VBAT_P, VBAT_F, VBAT_DD, LM748_DGATE, LM748_HGATE, BAT_IN, Net-(U16-CL), ROUTER_12V_EN. No HV net touched; nearest changed item to HV copper 162.66 mm, to a barrier slot 211.33 mm.
- **Necks [M widths / I amps]:** VBAT_P Q2→Q3 F 8.76 / B 4.54 mm (11.5 / 7.2 A; F+B 18.7 A per the reviewer's tight-pad neck method, review/s3c6c/review.md, same on base and c6c; the earlier B 5.22 mm / 7.9 A / F+B 19.5 A was a method artefact, B alone < 10 A, so F+B sharing through the VBAT_P transfer vias is required: VBAT_P vias at the Q2 / Q3 ends, MEASURED with review/s3c6b/via_count.py (all 0.3/0.6 mm vias): primary method via-edge-to-pad-edge (any part of the via pad within r of any edge of the FET pads used: Q2 pads 1-3, Q3 pad 5) 25 / 25 within 5 mm and 40 / 35 within 8 mm; reviewer method via-centre-to-point (via centre within r of Q2 point (254.6, 151.0) / Q3 point (228.02, 140.07)) 17 / 14 within 5 mm and 34 / 25 within 8 mm; identical at 950b8a1 and S3c/c6c; 14 is met at both ends within 5 mm, exactly at the Q3 end), VBAT_DD Q1→Q2 F 7.54 / B 7.51 mm (10.3 / 10.3 A; F+B 20.7 A), VBAT_F F1→Q1 B 8.02 mm (10.8 A, reviewer tight-pad method; B only at Q1; F 8.95 mm before c6c, 1.92 mm after c6c, not counted) [M widths, tneck erosion on gate/s3c6b; amps I by IPC-2221 outer k 0.048 at 18 °F (10 °C) rise, 1 oz ASSUMED]. Every per-layer width ≥ 3.6 mm.
- **Output-loop (LM5176 boost) risk [M/I]:** the 100 nF C296 is in the west spot nearest the Q6 tab (center 6.62 mm) and R12 GND; C293 moved to the east end, 7.87 mm edge from BB_SW1 (was 0.67 mm in c6). C296 is 1.09 mm from BB_SW1 (Q4.5). Each cap GND pad has 3 GND vias (one added per cap). Loop inductance and ringing are not measured; this is a layout trade-off (see review/s3c/c6_review.md).
- **Gate (gate/s3c6b, on a byte copy of the saved file) [M]:** DRC 0 errors on repo / own / no-.dru rule sets, default set 1119 (= baseline), unconnected 631, cls 631 / VBAT_P 62, HV opens 7/23, hvsheet 0, dangling vias 12, courtyards 0, viachk 0 bad, slot-edge 0 / slot-corner 1 (= baseline), uuid net-swap 0, hidden via shorts 0, schematic/netlist unchanged. Correction: c6b (2c7a1b0) carried stale board Values R407 13.3k and C229 10u from the S3b scratch base (built on 2ccfb7d, before e207b20/2692ed7); restored to 47k / 2.2u in the following board commit, together with R115 100k, L8 LCSC C79272 and R15/R22 DNP to match the schematic.

### 8.1 S3c/c6c — LM74800 (U1) controller moved next to Q1/Q2 (2026-10-27, HST). Not certified, not fab-ready.
- **Parts moved (F.Cu, no pad net changes) [M]:** U1 (250.352,165.0,0° B → 257.0,136.41,180° F); C1 (249.875,170.149,−90° → 253.5,133.9,0° F); C2 (252.911,166.893,−90° → 253.9,137.6,180° F). R1–R3 not moved.
- **Copper vs 950b8a1 (uuid diff) [M]:** tracks −55/+54, vias −12/+11 (nets LM748_DGATE/HGATE, VBAT_F, VBAT_DD, VBAT_P, GND, CAP, EN/UVLO, OV, OVUV_TOP). EN/OV/OVUV_TOP return to R1–R3 on SIG_In2 (0.15 mm). No pad net changes, no net swaps, no zone outline changes, no HV-class copper touched; D1 and its GND vias untouched.
- **U1 link lengths, final board (links.py, track length from the U1 pin) [M]:** DGATE 2.9 mm (F 1.9 + B 1.0), HGATE 18.5 mm (F 17.0 + B 1.5, 0.3 mm), VBAT_F sense 5.7, VBAT_DD (C) 5.0, VBAT_P (OUT) 10.5, CAP 0.7, OVUV_TOP 40.7, OV 56.2, EN/UVLO 47.0.
- **HGATE deviation from TI layout wording ("short gate traces") [M/I]:** HGATE is 18.5 mm (950b8a1: 19.1 mm). The ~17.6 mm accepted target is NOT met. Constraint: Q1 and Q2 gates are 9.5 mm apart with the Q1 tab between them, and HGATE (U1 pin 8) must pass outside the OUT (pin 9) lane, which must run between HGATE and the C2 pad 2 edge (x 252.675); with 0.15 mm PWR clearance this keeps HGATE at x ≤ 252.075, giving a minimum of about 18.4 mm on the outer layer.
- **C2 [M]:** 2.10 mm pad-edge to pad-edge from Q1 in plan, F side, not over Q1.
- **Necks (tneck, filled copy) [M], all = 950b8a1:** VBAT_P Q2→Q3 F 8.76 / B 4.55, VBAT_DD Q1→Q2 F 7.54 / B 7.51, VBAT_F F1→Q1 B 8.07 mm. Uncounted: VBAT_F F1→Q1 F.Cu 1.92 mm (tneck) / 2.40 mm (mneck; 950b8a1 7.43).
- **Via counts (review/s3c6b/via_count.py) [M], 950b8a1 → c6c:** primary via-edge-to-pad-edge ≤5/≤8 mm: VBAT_P Q2 25/40 → 25/40, Q3 25/35 → 25/35; VBAT_DD Q1 15/18, Q2 16/18 (unchanged); VBAT_F Q1 pads 1–3 2/19 → 4/21. Reviewer via-centre-to-point (Q2 point 254.6,151.0; Q3 point 228.02,140.07; Q1 point 257.0,144.55; Q2-DD point 258.55,151.0): VBAT_P 17/34 and 14/25, VBAT_DD 8/15 and 13/16 (unchanged).
- **Gate (gate/c6c_r7, byte copy refilled in its own process) [M]:** DRC 0 errors repo / own / no-.dru; default-rule set 1119 saved / 1120 refilled. The match to the baseline 1119 is coincidental: c6c adds 34 new default-rule items on the U1 nets (29 clearance, 5 hole_clearance; smallest 0.104 mm, OV F.Cu track to U1 pad 6), all passing the 0.1 mm repo rule, and the default set is not stable (a rerun on identical copper shifts about 57 items); unconnected 499, dangling vias 12, HV opens 7/23, hvsheet 0, slot-edge 0, slot-corner 1 (= baseline), viachk 0 bad, courtyards 0, hidden shorts 0 of 3367, ERC 0, netlist 1049 nets, field diff 17 known mismatches (no new). **cls 630 / VBAT_P 61 vs baseline 631 / 62: deliberate improvement** — per-net island diff shows the only removed open is pad U1.9 (OUT, VBAT_P), now connected; every other net unchanged.
- **Harmless cleanup pending (later copper pass) [M, read-only on the committed board]:** VBAT_P (OUT) has two overlapping 0.15 mm F.Cu segments, 443e3692 (253.9,140.1)–(253.9,141.5) and 1e1ae7aa (253.9,140.2)–(253.9,141.5); 1e1ae7aa is the leftover OUT stub from the r6 route. Remove 1e1ae7aa in a later copper pass. No DRC or connectivity effect (fully covered by 443e3692, same net).

### 8.2 s3c6d VS wiring fix (2026-10-27)
- U1.10 (VS), C2.2 and C1.1 are now VBAT_DD (TI SNOSD95C p3; review/hv/lm74800_pins.md). C1 position unchanged; C1.1 reaches VBAT_DD by via (250.0,132.0) and a 0.3 mm PWR-layer track to the VBAT_DD via (261.9,142.6). (Superseded by §8.3: that link now runs on GND2.) VS/C2.2 tie to the U1.12 VBAT_DD track on F.Cu (253.125,137.6→253.125,138.6→255.6,138.6). [M] necks/vias unchanged.

### 8.3 s3c6h CIN and VBAT_DD layer change (2026-10-27)
- C297 (now 220 nF / 100 V X7R 0805, YAGEO CC0805KKX7R0BB224, LCSC C513710, since s3c6i; was 100 nF CL21B104KCFNNNE C28233) is the LM74800 input capacitor on VBAT_F (TI SNOSD95C p23 §10.2.3.3: 0.1 µF min). It sits at F.Cu (249.6, 137.0), about 9 mm from U1.2/U1.3. Pad 2 lands on the existing GND trace/via at (249.8, 139.5), so it adds no new via.
- The C1.1 VBAT_DD link (via (250.0,132.0)) no longer uses the PWR layer. It now runs as 0.3 mm GND2 tracks (250.0,132.0)→(256.4,138.4)→(256.4,143.0) to a new VBAT_DD via at (256.4,143.0). An In2 route was tried first and rejected because it split the In2 VBAT_P plane (19→20 pieces). With GND2: In2 19 pieces, GND1 and GND2 1 piece each, VBAT_F_PWR 1 piece (267.1 mm²). [M]
- Necks [M, necks_c6c.py]: VBAT_F F1→Q1 PWR 1.66 → 8.952 mm, B 8.021 (tneck 8.07), F 1.924; VBAT_DD 7.538/7.509; VBAT_P 8.76/4.535 (unchanged). Via counts: VBAT_F and VBAT_P unchanged, VBAT_DD +1. Gate at baseline. Not certified.

### 8.4 s3c6i cut-off In2 VBAT_P islands, C297 220 nF, refilled board (2026-10-27)
- The SIG_In2 plane LV_VBAT_P_SIG_In2 fills in 19 pieces. Two of them, pieces 8 and 10, are cut-off VBAT_P islands, not floating copper (MEASURED, Design Reviewer review/s3c6c/f7a6c86.md, scripts/isl_via.py): each has a flashed 0.2/0.4 mm VBAT_P via whose annulus overlaps the piece by about 0.10 mm, piece 8 via (190.27, 153.15) to R163.1, piece 10 via (185.14, 147.90) to C146.1. They are not joined to the main VBAT_P copper, so they are part of the 61 VBAT_P opens and R163 and C146 get no VBAT_P. (An earlier version of this section called them floating; that came from review/s3c6c/3a8/scripts/zisl.py, which counts a via only when its centre lies inside the piece. The correct test is via pad/annulus area overlapping the piece. zisl.py, outside this repo, still uses the centre test and was not changed.)
  - Piece 8: 5.30 mm², bbox x 188.86–191.63, y 149.60–153.38 mm.
  - Piece 10: 97.51 mm², bbox x 184.73–196.08, y 122.68–148.93 mm.
- They were the same before s3c6h. Both are in the low-voltage VBAT_P area, away from HV copper. They are an open, not harmless copper: R163 and C146 need VBAT_P joined to these islands (or another feed). Not fixed here.
- C297 is now 220 nF / 100 V X7R 0805 (YAGEO CC0805KKX7R0BB224, LCSC C513710). This is a value change only, on the same 0805 footprint, with no copper change.
- The committed board is now refilled and saved in place, with the .kicad_pro/.kicad_dru beside it, and gated on those exact bytes. The s3c6h file (md5 3a67a66e) had a stale fill: 204 HV_LINE vs GND_AC clearance errors in the repo, own and no-dru rule sets.

