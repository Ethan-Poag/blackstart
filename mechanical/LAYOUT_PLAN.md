# Blackstart (genctl) — PCB layout plan (placement v3, enclosure rev C)

Status 2026-10-25: rough placement **v3** done from the final schematic (repo commit bc99852 + mechanical commit 4ef4c52).
Netlist `genctl.net` exported from `snap/` (fresh copy of the repo schematic + `genctl.pretty`, 42 footprints): **1167 footprints,
all load, 0 missing** (the 7 missing in the V2 trial were a stale `snap/genctl.pretty`; it now holds the Phoenix 1720819,
SOIC-16W HV_Slot, DF40C-100DS-0.4V_B (pads 101-200), KF2EDGRM 5.08 6P/8P, etc.).
Board: `out/genctl_placed_v3.kicad_pcb` (+ `.kicad_pro` with JLC 0.10 mm Default clearance). Picture: `placement_v3.png`.
Scripts: `geometry.py` (source of truth), `place.py` (placer), `render_placement.py` (PNG). Mechanics: `PANEL_V2.md`, `enclosure/ENCLOSURE_DFM.md` rev C.

## 1. Board, sides, coordinates
- Outline **284 x 210 mm** (x −3.72…280.28, y −15.27…194.73), R2 corners, 6 layers, 1.6 mm. Origin = top-left of the display glass, front view, y down.
- Enclosure check: rev C shell is **294 x 220 outer** = board + 2 x (2.0 clearance + 3.0 wall); inside 288 x 214 = board + 2 mm per side. **Consistent** — no change.
  (294 x 220 is the outer size, not the inside.)
- **F side faces the display**: 12 x CTS 228E keys SW9-SW20 at x 29.08 … 246.68 (43.52 pitch), y −9.25 / 188.71; 24 x 12 caps (rev C);
  **13 x 16 mm clear area per switch** (no other parts either side, no THT pins). Display connectors J14 (LVDS), J15 (touch), J16 (backlight), J12 (touch USB) on F.
- **B side (rear)**: everything else. Wiring through the shell's rear windows.

## 2. Mechanical keep-outs (all in `place.py` / `geometry.py`)
| Item | Where | Implementation |
|---|---|---|
| H1, H2, H3 | (2.0, −9.25), (274.56, −9.25), (2.0, 188.71) | M4 D4.3 PTH, 9 mm pad, net CHASSIS (bezel bosses) |
| H4 PE boss | **moved to (272.0, 185.5)** (was 274.56, 188.71 = 0.97 mm web to the edge) | D9.5 NPTH, 1 mm copper-free ring (`PE_BOSS_RING`). Webs now 3.5 mm (right) / 4.5 mm (bottom). `enclosure.py` takes PE_BOSS from geometry, so the bezel boss moves with it |
| Mid holes | — | **removed** (rev C: no bezel behind the display) |
| Shell posts | (100,60) (100,140) (240,60) (240,140) | D10 B-side rule areas, no pads/footprints |
| Hook clamps (6) | top/bottom at x 72.6 & 203.16, left/right at y 89.73 | rev C hooks stay **outside** the shell (blind pockets), so nothing reaches the PCB. Marked on Cmts.User only (24 x 4 mm at the edge) as a reminder; no copper rule |
| Key gaps | 5 per row, centres 50.84 94.36 137.88 181.40 224.92, **30.52 mm** wide between switch keep-outs | one KF2EDGRM-5.08-6P per gap: pin row 27.9 mm fits; flanged body (40.9 mm) overhangs 5.2 mm per side on the **B side** behind the switches (switches are SMD on F) |

## 3. Floorplan (B side unless noted)
| Block | Box (x0,y0 … x1,y1) | Contents / notes |
|---|---|---|
| 600 V metering (hot) | −3.7,11 … 60,162 (top-left) | J28 GEN V, J29 BUS V (Phoenix 1720819), J30 CT 8P on the left edge (wire entry outward/rear); ADE9000 x2, dividers, MOVs; T1-T4 AC1005 in `CT_AT_BARRIER` (26.5,112 … 60,162), at the barrier edge next to J30 |
| Barrier | U-shape round the hot box: top band y −1.25…11, vertical x 60…73, bottom band y 162…175 | **13 mm copper-free on all layers** (rule areas `BARRIER_*`, no tracks/vias/pads/pours/footprints) |
| Isolators | U69 ISOW7841 (66.5, 62), U70 ISO7741 (66.5, 98) | straddle the vertical band, HV pins (9-16) toward the hot side, 8.10 mm pad gap + 21 mm footprint slot; barrier opens ±11 mm round each |
| ISO_LV | 74,52 … 86,95 | SELV decoupling of the isolators (C235/C236/C239) |
| Outputs | 74,−1 … 200,52 | TPS1HTC30 x16, TPS48100, readback → J24-J27 + J21 in the top key gaps |
| CM5 | module 203,1 … 258,41 (DF40 U9/U10 at y 4 / 38) + parts zone 200,41.5 … 262,62 | heat strap to **H2** (see §5) |
| Comms | 200,62 … 262,135 | CAN/RS-485 isolators, USB hub, magjack side; right-edge J10 RJ45, J11 USB-C, J6 CAN, J7 expansion |
| MCU | 135,52 … 200,100 | STM32H743, FRAM, watchdog, SWD, CR2032 |
| Front | 86.5,52 … 135,95 | key LED drivers / expanders |
| Display | 135,100 … 200,135 | SN65DSI83 + panel power, close to J14 (F, x 128, y 142) |
| Inputs | 74,135 … 190,180 | AI/DI/MPU → J17-J20, J22 in the bottom key gaps |
| Power | 190,135 … 262,180 | LM74800, **LM5176**, TPS56637 x2, LMR36506, supercaps, F1; next to J1 battery (right edge, bottom) |
| Spill | 74,95 … 135,135 | overflow (45 input parts) |
| Edge: right | x 262…280, y 38…180 | J6 CAN, J7 expansion, J23 fuel/crank (Phoenix), J1 battery (Phoenix). J10/J11 moved to rear-facing positions at (214,53) / (240,50) (v4) |
| Edge: end slots | bottom-left x 7…23: J9 RS-485; bottom-right x 253…266: J8 router 12 V | |
| Silkscreen | B.SilkS (140…215, 173…180) | "PROJECT BLACKSTART" / "genctl rev H placement v3 CERN-OHL-S-2.0"; "600V HAZARDOUS VOLTAGE" above the hot zone |
Thermal: LM5176 + inductors bottom-right, CM5 top-right (~100 mm apart), output FETs spread along the top band, ADE9000s cool.
The packer is a shelf packer (parts binned by sheet, big parts first), not a real placer: use it as the rough start for hand placement / Quilter.

## 4. 600 V barrier / isolation (docs/ISOLATION_CHECK.md)
- Approach: **≥13 mm copper-free barrier on plain FR-4** (needed 12.6 mm creepage at 600 V working, group IIIa) — no CTI≥400 laminate and no full-length slot needed.
  At the isolators the barrier is bridged only by the isolator body; there creepage comes from the footprint slot (~14.4 mm), clearance 8.1 mm ≥ 8.0.
- **1.5 mm milled slots between the potentials of J28 and J29** (3 per header, Edge.Cuts) fix the 0.7 mm creepage shortfall L-L.
- LV copper ≥13 mm from hot copper also toward the top-left key band, H1 and the J24 terminal (checked by script).
- **AC1005 CTs (open)**: loop pads 4/5 are 4.6 mm from the hot secondary pins and the part has no insulation rating, so the CTs cannot straddle a barrier.
  They are placed **entirely inside the hot zone at the barrier edge** with J30 also in the hot zone, i.e. the external CT loop is treated as hot
  (finger-safe plug, CT secondaries not earthed). If the CT loops must stay earthed/SELV, the AC1005 must be replaced by a CT with a reinforced
  rating and J30 moved to the LV side — **Ethan's decision**.
- Shell rib: rev C rib at x = 12.28 with a cross rib at y ≈ 124.7 does **not** match v3: the Phoenix bodies occupy x −3.3…12.8 and J30 runs to y 161.
  Move `BARRIER_X` to ~BOARD_X0 + 18 and the cross rib to y ≈ 163 in `enclosure.py` (not changed here).

## 5. CM5 thermal strap
- CM5 at the **top-right, next to H2** (274.56, −9.25). Why H2: H1 is in the 600 V corner, H3 is bottom-left beside the barrier and 70 mm+ from any
  free LV area, H4 is the PE boss (not a heat path through the PCB stack). H2 is in the LV corner nearest the right-edge Ethernet/USB (short MDI/USB runs),
  at the top where the shell exhaust vents are, and ~100 mm from the LM5176 power stage.
- Strap: Al or Cu strip from a thermal pad on the CM5 heatsink (top-right corner) up to the H2 boss; bolts under the H2 M4 head (B side).
  **Keep-out `STRAP_CORRIDOR` x 247…279.8, y −14.8…3.8 on B: no parts** (rule area); the KF terminal in gap 5 ends at x 245.4.
- DF40 positions follow the CM4/CM5 datasheet (centres 34 mm apart, 3 mm in from the long edges). **TODO**: the ±2.5 mm x offset and which connector is A — copy from the CM5 IO board KiCad files.

## 6. Stackup (JLCPCB 6-layer, 1.6 mm, JLC06161H-3313 — JLC's default impedance stackup)
| Layer | Use | Dielectric below |
|---|---|---|
| L1 F.Cu (1 oz) | display connectors, keys, short routes | 3313 prepreg 0.0994 mm, εr 4.1 |
| L2 In1 **GND** | solid reference for L1 | core 0.55 mm (εr 4.6) |
| L3 In2 SIG | low-speed routing, key/LED lines | 2116 prepreg 0.1088 mm |
| L4 In3 **PWR** | 12 V / 5 V / 3V3 pours (split) | core 0.55 mm |
| L5 In4 **GND** | solid reference for L6 | 3313 prepreg 0.0994 mm |
| L6 B.Cu (1 oz) | CM5, DSI, LVDS, USB, Ethernet, most parts | — |
Layer names in the board are GND1/PWR/GND2 so Quilter recognises planes (it looks for "gnd"/"pwr").
Optional: outer 2 oz for the output section (JLC offers 1/2 oz outer, 0.5/1/2 oz inner) — check cost.

High-speed on outer layers as microstrip over the adjacent solid GND (Quilter only does microstrip anyway).
**Approximate** widths (Hammerstad/Wadell estimate, me — confirm in JLC's impedance calculator before release):
| Interface | Target | L1/L6 over 0.0994 mm |
|---|---|---|
| Single-ended | 50 Ω | w ≈ 0.15 mm |
| MIPI DSI (CM5→SN65DSI83), LVDS (→J14), Ethernet MDI (CM5→RJ45) | 100 Ω diff | w ≈ 0.11, s ≈ 0.15 mm |
| USB 2.0 (USB-C, hub, touch) | 90 Ω diff | w ≈ 0.15, s ≈ 0.18-0.20 mm |
Length matching per CM5 datasheet: intra-pair ≤ 0.15 mm (DSI/Ethernet ≤ 0.1-0.15), inter-pair DSI lanes loose (< 25-50 mm).
Order JLC "impedance control" with the chosen stackup.

## 7. JLCPCB 6-layer rules for DRC (from jlcpcb.com/6-layer-pcb and /impedance, 2026-10)
| Rule | JLC capability | Use in board setup |
|---|---|---|
| Min trace / space | 0.09 mm (3.5 mil) | **0.10 / 0.10** (0.127 default class) |
| Min via drill / diameter | 0.15 / 0.25 mm (0.2 mm on impedance page) | **0.20 / 0.40** default; 0.15/0.30 only under DF40/BGA if needed |
| BGA pad min | 0.25 mm | SN65DSI83 nFBGA-64 0.5 mm pitch → via-in-pad (free on 6L) or dog-bone with 0.15/0.30 |
| Via-in-pad | yes, free on 6L | |
| Drill range | 0.15–6.3 mm, tol +0.13/−0.08 | |
| Board size max | 660 x 475 mm | 284 x 210 OK |
| Thickness | 0.8/1.0/1.2/1.6/2.0 | 1.6 |
| Copper | outer 1/2 oz, inner 0.5/1/2 oz | |
| Copper to edge | (not stated on 6L page; JLC general 0.3 mm) | 0.30 mm (0.5 for HV) |
| Hole-to-hole | — | 0.25 mm |
| Surface | ENIG (free) | |
Set these in Board Setup › Constraints; add net classes: HV (clearance 3.0 mm), HV_ISO (8 mm via custom rule), PWR_HI (≥ 1 mm), DIFF100, DIFF90.
Custom DRC rule sketch (`.kicad_dru`):
```
(rule "HV to LV" (constraint clearance (min 8mm)) (condition "A.NetClass == 'HV' && B.NetClass != 'HV'"))
(rule "HV creepage" (constraint creepage (min 8mm)) (condition "A.NetClass == 'HV' && B.NetClass != 'HV'"))
```
(KiCad 9 has a `creepage` constraint; verify it behaves with the slot on Edge.Cuts.)

## 8. DRC on out/genctl_placed_v3.kicad_pcb (kicad-cli 9.0.2, 2026-10-25)
| Type | Count | Note |
|---|---|---|
| errors (clearance, courtyard, hole/edge, keep-out) | **0** | |
| silk_overlap / silk_over_copper | 199 / 199 | refdes text of densely packed passives; fix during hand placement |
| silk_edge_clearance | 4 | isolator silkscreen crosses its own slot (footprint-internal) |
| unconnected (ratsnest) | 2917 | expected, unrouted (the JSON report lists the first 499) |

## 9. Open items for Ethan
1. AC1005 / J30 hot vs earthed CT loop (§4).
2. Shell changes for v3: barrier rib x / cross-rib y (§4); rear windows: top/bottom window x 38…243 should become ~28…248 (KF flanges reach x 30.4 and 245.4)
   and the end-slot terminals J9 (x 7…23) / J8 (x 253…266) need their own openings; the right window y 20…175 should start at ~4 (J10 RJ45).
3. DONE (rev D): J10 is now the vertical HR963380AE RJ45 and J11 the vertical TYPE-C-31-D-06B. Both mate through **rear-wall** wells (see ENCLOSURE_DFM §3); no side-wall opening. The right edge keeps only J6, J7, J23 and J1.
4. KF2EDGRM flanges sit behind the switches on B: confirm the 228E locating pegs don't protrude past the PCB rear (1.0 mm NPTH), else trim pegs or shorten the flange.
5. Wire-entry direction: script points each terminal body at the board edge; verify in pcbnew against the plug drawings (plug choice decides rear vs edge entry).
6. CM5 DF40 offset (§5).

## 10. Scripted placement (tooling status on the box)
- **KiCad 9.0.2 is installed** (`kicad-cli` at /usr/bin, `python3 -c 'import pcbnew'` works, stock footprint libs at /usr/share/kicad/footprints). No install needed, no sudo needed.
- No Java → Freerouting (autorouter) not runnable as-is; a portable JRE could be dropped into ~ without sudo if wanted (not done).
- `place.py` (works today on the snapshot):
  `python3 place.py --netlist genctl.net --out out/genctl_placed.kicad_pcb` → outline, 6 layers + JLC rules, fixed keys/holes/display connectors,
  edge connectors in slots, every other part binned into its zone by schematic sheet (fallback: net BFS), Quilter-style placement-region rule areas, HV keep-out.
  `--quilter` parks all non-fixed parts outside the outline (what Quilter wants). Slots: isolator slots come with the footprints; inter-phase slots under J28/J29 are added by `place.py` (Quilter wants one outline: remove them for the Quilter pass and re-add).
  v3 result: 1167 footprints, 0 overflows, DRC 0 errors (silk warnings only), see §8.
  It is a **binning packer, not a real placer**: parts in a zone are shelf-packed in ref order, not next to their IC. Real placement = Quilter or manual.
- Placeholders in `place.py` (TODO): U9/U10 CM5 connector offset (take from the official CM5 IO board KiCad files), terminal wire-entry rotation, J15 tail fit.
- KiCad MCP servers (GitHub, checked 2026-10-24):
  - mixelpixx/KiCAD-MCP-Server — ~2.9k stars, MIT, active (push 2026-10-01); pcbnew SWIG + KiCad 9 IPC; place/move/array/align components, outline, holes. Most mature.
  - lamaalrajih/kicad-mcp — ~530 stars, last push 2025-10; mostly project/analysis/DRC/BOM.
  - blwfish/kicad-mcp — 27 stars, active; placement audit, FreeRouting, JLC/LCSC search.
  - ProductOfAmerica/mcp-server-kicad — 15 stars, GPL-3, careful file-level footprint placement; "maintenance mode".
  Honest take: for this board they add little over `place.py` — they wrap the same pcbnew calls one footprint at a time, and an LLM driving 1100 parts via MCP calls is slow and no better at placement. Useful later for interactive tweaks/DRC loops. None installed (would need the user to add it as a connector to the bot; `uv` is available on the box so it could run here).

## 11. Order of work from here
1. Open `out/genctl_placed_v3.kicad_pcb`; hand-place and pre-route the hot zone, isolators, DSI/LVDS, Ethernet, LM5176 loop.
2. `python3 place.py --netlist genctl.net --out out/genctl_quilter_input.kicad_pcb --quilter` for a Quilter input (fixed parts inside, rest parked), see QUILTER.md.
3. The board is built from the netlist (no schematic UUID links). Before release, run "Update PCB from Schematic" in pcbnew on this board to link symbols.

## v4 (2026-10-25): connectivity-driven placement + route pipeline
See `pcb_v4/README.md`. Placement is no longer block-by-size. Hard constraints are locked first, then parts are placed by connectivity: each IC goes to the centroid of what it connects to, and each small part goes to the pin it serves. After that comes the critical routing (planes and fan-out), then Freerouting, DRC and render.
