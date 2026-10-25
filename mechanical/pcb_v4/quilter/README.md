# Blackstart pcb_v4 → Quilter input package

**Purpose:** let Quilter (app.quilter.ai) route the remaining *plain low-voltage* connections on the
best hand-routed board. Source: `mechanical/pcb_v4/genctl_v4_handrouted.kicad_pcb` at commit 34d0eff, DRC 0 errors.
Nothing has been uploaded. The user uploads manually.

## Build
```
cd mechanical/pcb_v4
kicad-cli pcb drc --severity-all --format json -o w6/drc_all.json genctl_v4_handrouted.kicad_pcb   # dangling list (~8 min)
python3 quilter/quilter_prep.py genctl_v4_handrouted.kicad_pcb w6/drc_all.json /workspace/genctl/layout_prep/quilter_v4
```
The output is loose files in one flat directory. Per docs.quilter.ai, **zips and nested directories are not accepted** (except Xpedition).
Upload all of these at once:

| file | what |
|---|---|
| `genctl.kicad_pcb` | input board (KiCad 9). 1170 footprints, 5112 track/via items, 1809 unrouted connections |
| `genctl.kicad_pro` | project: schematic settings from the repo's genctl.kicad_pro, board and netclass settings from the hand-routed board |
| `genctl.kicad_sch` + 10 sub-sheets | full hierarchical schematic. Sheet references are flat filenames |
| `genctl.kicad_dru` | custom rules (600 V spacing, U21 via minimums). Quilter probably ignores this; it is kept for KiCad |

## Quilter requirements (docs.quilter.ai, read 2026-10-25) and status
| requirement | status |
|---|---|
| Complete schematic plus linked board; **netlist must match the schematic** | ✅ `kicad-cli sch export netlist` vs board: 1170/1170 refs, every pad's net maps 1:1, no split or merged nets. Fixed on the way: the board had `DSI83_REFCLK` split into a short-name and a full-path net, and `DSI83_REFCLK_OSC` short-named. |
| **Single closed outline on Edge.Cuts** | ✅ one outline, 0 holes. The 6 internal HV creepage slots (x 2.7–11.5 mm) and the U69/U70 isolator slots were moved to **Dwgs.User** in this copy, because Quilter only supports one closed outline. Each slot area is a copper keep-out rule area (`QUILTER_SLOT_n`). **The master board keeps the real slots. Never send a Quilter board to fab.** |
| Footprints loaded | ✅ all 1170 placed inside the outline, so all are fixed. Connectors (Ethernet/USB-C rear, CM5 U9/U10, etc.) are pre-placed. |
| Plane layers named "ground"/"gnd" and "power"/"pwr" | ✅ In1 `GND1`→`gnd`, In4 `GND2`→`ground`, In3 `PWR`→`pwr` (+3V3_SAFE stays on In3), In2 `SIG_In2`→`sig`. This affects layer user names only. |
| Pre-routes are kept, orphans must be removed | ✅ 43 dangling track/via segments (DRC track_dangling/via_dangling) deleted; unconnected count unchanged at 1809. All tracks, vias and footprints are also set **locked**. |
| **Inner-layer pre-routes and pours survive only with "preserve stack-up"** | ⚠ Must be chosen in the UI. In the Stackups step, **select the stack-up from the input file**. Otherwise Quilter deletes all inner copper, including hand-routed In2 critical traces and the planes. |
| Pours are kept only if named **and** added to the "Preserved pours" table | ⚠ UI step. Add all six: `LV_GND_GND1`, `LV_GND_GND2`, `LV_+3V3_SAFE_PWR`, `HV_GND_AC_GND1`, `HV_GND_AC_GND2`, `HV_+3V3_AC_PWR`. |
| High voltage | ❌ **Not supported by Quilter.** It has no creepage/clearance physics and recommends ≤48 V; unconstrained nets are treated as generic low-voltage signals. See below. |
| KiCad 9 | ⚠ Docs say "KiCAD" and give no version; KiCad 9 is not confirmed. If parsing fails, re-save with KiCad 8 (File → Save As won't downgrade, so it would need a manual export). |

## What is excluded from Quilter's job, and how
- **600 V area (HV box x −3.7…60 mm, y 11…162 mm, 127 parts).** A rule-area keep-out `QUILTER_HV_KEEPOUT_600V` covers it on all 6 copper layers, blocking new **tracks and vias** (pours allowed so the HV planes can be preserved).
  - Existing HV copper inside it is fixed pre-route. In KiCad this shows as 199 "items not allowed" (all `QUILTER_HV_KEEPOUT_600V`, nothing else) DRC errors on the *Quilter copy only*. That is expected and absent on the master.
  - The barrier strips (x 60–73 and top/bottom bands) were already full keep-outs (`BARRIER_*`, unchanged: 13 mm, slots).
  - Quilter cannot finish HV-box nets. They will show as incomplete. **Finish them by hand in KiCad against the 3 mm / 1.5 mm rules.**
  - A keep-out is the only control Quilter documents. The docs say "we'll steer clear of it", but do not say whether it honours KiCad's per-object flags (tracks/vias vs pours). **Check the candidate preview for any copper in the HV box.** The merge script rejects it anyway.
- **Isolator crossings:** AC_SCK/MISO/MOSI/CS1_N/CS2_N/IRQ_N/RST_N, +3V3_AC and GND_AC run from the ADEs inside the HV box to U69/U70 at the barrier gaps. Quilter cannot route these through the keep-out. They stay manual/critical.
- **Critical / diff-pair / power nets:** DSI, LVDS, ETH, USB (DIFF100/DIFF90), HV_LINE/HV_LINE_DIV, PWR classes, and the ADE SPI/XTAL/REFCLK nets are pre-routed and locked.
  - Still open: LVDSC_P, LVDS0_P, LVDS1_P (and AC_SCK, BUS_VC_P, ADE_XO in/near HV). Quilter may try to route these as generic or detected pairs. **Those results are discarded at merge.** Optionally mark the pairs in Circuit Comprehension so the preview is meaningful.

## Merging a candidate back
1. Download the candidate (.kicad_pcb, same format). Do **not** open-and-save it over the master.
2. Run:
   ```
   cd mechanical/pcb_v4
   python3 quilter/merge_back.py genctl_v4_handrouted.kicad_pcb <candidate>.kicad_pcb w6/merged.kicad_pcb
   kicad-cli pcb drc --severity-error -o w6/merged_drc.rpt w6/merged.kicad_pcb
   ```
   `merge_back.py` copies only *new* tracks/vias whose master netclass is `Default`, whose net is not in its CRITICAL list, and which lie entirely outside x<73 mm within y −1.3…175 (HV box + barrier).
   - Quilter pours, layer names and the slot-to-Dwgs.User change are **not** brought back: the master keeps its slots, names and zones (refilled).
   - Footprints are never touched. Quilter does not move pre-placed parts, and all 1170 are pre-placed.
   - Self-tests: feeding the input board back adds 0 items; a synthetic LV track is added and connects.
3. Fix the DRC (the Quilter widths/clearances use its fab profile, and the master .dru is stricter near HV). Re-run the pcbnew unconnected count (after zone fill), then commit.
4. Recompute skew for the diff pairs (unchanged by the merge) and update PROGRESS.md.
