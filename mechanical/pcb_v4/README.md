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
VBAT_F (F1→Q1) supports ≈9.9 A continuous and the VBAT_P inner path ≈1.8 A by IPC-2221 at 18 °F rise with 1 oz outer / 0.5 oz inner (INFERRED copper weights). Neither is a verified 10 A path. See PROGRESS.md "Known current limits". The builder may choose heavier copper or a lower rating.
