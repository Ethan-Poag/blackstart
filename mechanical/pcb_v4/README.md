# Blackstart PCB v4: connectivity-driven placement and route pipeline

The board opens in KiCad 9/10 with `genctl_v4_routed.kicad_pcb` and `genctl_v4.kicad_pro`. The footprints are embedded and no plugins are needed.

## Pipeline (`pipeline.sh`)
Run it on the build box with KiCad 9 pcbnew python, Freerouting 2.5 and Java 25.

1. **place** (`place_v4.py`): hard constraints are locked first:
   - edges, keys, CM5 and display connectors
   - the 600 V box with its 13 mm barrier and slots, plus the isolators straddling it
   - posts, holes and the strap corridor

   After that come the **functional seeds**:
   - STM32, DSI83, bucks and ideal diode
   - ADE9000s, the CT stack and MOVs
   - J10/J11, which are rear-facing

   Every other IC goes to the weighted centroid of the parts it is already connected to (greedy, most-connected first). Each R/C/D/FB is assigned to its nearest IC on the same schematic sheet and lands right at the IC pin it shares, so decaps sit tight to their pins. Hot parts are confined to the HV box. Parts touching the line nets keep ≥1.4 mm between each other.
2. **critical** (`route_v4.py setup`):
   - **Netclasses:**
     - PWR 0.5 mm
     - DIFF100 0.11/0.15 (Ethernet, LVDS, DSI)
     - DIFF90 0.15/0.18 (USB)
     - HV_LINE 1.5 mm clearance (IPC-2221B B2, 600 V, inside the HV box)
   - **Plane zones:**
     - LV area: GND on In1/In4, +3V3_SAFE on In3
     - HV box: GND_AC on In1/In4, +3V3_AC on In3
   - **Plane fan-out:** a short stub and via from every SMD pad on a plane net, plus a via-in-pad grid on exposed pads.
3. **autoroute**: the remaining nets go to Freerouting via DSN/SES (`--router.fanout.enabled=false`).
4. **DRC**: `kicad-cli pcb drc`.
5. **render**: `render_v4.py`.

Rules: 0.10 mm track/space minimum, 0.20/0.40 mm vias. The impedance widths are **estimates** for JLC06161H-3313 and must be checked in JLC's impedance calculator.

**Fab note (m7-wip, 2026-10-25):** two DSI83_REFCLK vias, at (161.5, 126.7) and (162.0, 125.65) mm, are **0.15 mm drill / 0.30 mm pad**. Every other via is ≥0.2/0.35. I tried enlarging them to 0.2/0.35, but they do not fit: that breaks the DIFF100 clearance (0.125 vs 0.15 mm), the hole clearance (0.18 vs 0.20 mm) and the zone clearance (0.176 vs 0.20 mm). The board therefore needs JLC's "smaller via" option (0.15/0.25–0.3 mm class) at order time, which may add cost; check the JLC quote. The project's minimums are min through-hole 0.15 mm and min via 0.30 mm. The working and repo .kicad_pro files now agree on these values.

**Builder note (m7-wip, 2026-10-25): RV3 is NOT wired.** The GEN-side MOV RV3, at (25.26, 154.08) mm on B.Cu, is placed, but its pads RV3.1 (GEN_L3) and RV3.2 (GEN_N) have no copper. There is no legal 600 V path to its spot in the BUS area; it is an accepted placement exception (see HV_ACCEPTED_DEVIATIONS.md item 3). Do not assume GEN-side L3–N surge protection from RV3 on this board revision, and do not bodge-wire it without an HV spacing check.

## Known limit (m7-wip, 2026-10-26)
Superseded (2026-10-27, S3c/c6b): the board battery path is a 10 A path (F1 10 A) at 18 °F (10 °C) rise, INFERRED from the measured copper with 1 oz outer ASSUMED, not certified: VBAT_P Q2→Q3 F 8.76 / B 4.54 mm (11.5 / 7.2 A; F+B 18.7 A per the reviewer's tight-pad neck method, review/s3c6c/review.md, same on base and c6c; the earlier B 5.22 mm / 7.9 A / F+B 19.5 A was a method artefact, B alone < 10 A, so F+B sharing through the VBAT_P transfer vias is required: VBAT_P vias at the Q2 / Q3 ends, MEASURED with review/s3c6b/via_count.py (all 0.3/0.6 mm vias): primary method via-edge-to-pad-edge (any part of the via pad within r of any edge of the FET pads used: Q2 pads 1-3, Q3 pad 5) 25 / 25 within 5 mm and 40 / 35 within 8 mm; reviewer method via-centre-to-point (via centre within r of Q2 point (254.6, 151.0) / Q3 point (228.02, 140.07)) 17 / 14 within 5 mm and 34 / 25 within 8 mm; identical at 950b8a1 and S3c/c6c; 14 is met at both ends within 5 mm, exactly at the Q3 end), VBAT_DD Q1→Q2 F 7.54 / B 7.51 mm (10.3 / 10.3 A; F+B 20.7 A), VBAT_F F1→Q1 B 8.02 mm (10.8 A, reviewer tight-pad method; B only at Q1; F 8.95 mm before c6c, 1.92 mm after c6c, not counted) [M widths, tneck erosion on gate/s3c6b; amps I by IPC-2221 outer k 0.048 at 18 °F (10 °C) rise, 1 oz ASSUMED]. Caveat: the 10 A figure is the copper only. Continuous load is also limited by F1: a 10 A ATO carries at most about 8 A at 149 °F (65 °C) ambient (Littelfuse 287 ATOF derating, final_power_spec.md §1; datasheet pages UNVERIFIED). The battery wiring and the mating connector must be rated for the load as well. See docs/ROUTING_PLAN.md §8. Load shedding is fault-only, not a normal-operation behavior.
