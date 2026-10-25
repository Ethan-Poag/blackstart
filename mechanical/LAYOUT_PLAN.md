# Blackstart (genctl) — PCB layout plan

Status: pre-layout plan, written against a **read-only snapshot** of the schematic taken 2026-10-24 15:52 HST
(`layout_prep/snap/`, netlist `genctl.net`, BOM `bom.csv`: ~1123 footprints, ~3960 pads). The schematic is still being
edited (modem removal, router power, outputs 8→10). Re-export the netlist and re-run `place.py` once it is final.
Geometry source of truth: `geometry.py`. Mechanics: `display_mech.md`, `front_panel.png`.

## 1. Board, sides, coordinates
- Outline **284 x 198 mm**, R2 corners, 6 layers, 1.6 mm. Origin = top-left of display glass, front view.
- **F side faces the display / front panel**: the 12 keys (SW9-SW20), display connectors J14 (LVDS 40p FFC), J15 (touch 10p),
  J16 (backlight), J12 (touch USB SM04B). Only low parts here: the gap to the display back is small, and the
  TFT source-PCB band (x 20-256, y 150-179) is the tallest part of the module — keep F side clear under it except J14 just above it.
- **B side = rear / wiring side**: everything else, including CM5 (on DF40 connectors U9/U10) and all terminal blocks.
- Interior part area (courtyard sum) ≈ 18,500 mm² vs ≈ 45,000 mm² interior → ~40 %: OK for single-side B placement plus F-side display parts.

## 2. Floorplan zones (B side unless noted; mm, see `place.py` ZONES)
| Zone | Box (x0,y0,x1,y1) | Contents |
|---|---|---|
| Left edge strip | x −3.7…10, y 7…188 | J29 GEN V, J30 BUS V, J31 CT (5.08 mm, 600 V) top→down, then J1 battery (7.62) |
| HV_METER | 12,8 … 70,128 | AC metering sheet: 2x ADE9000, 1 MΩ divider strings, CTs T1-T4, MOVs RV1-6, Y4. Referenced to the metering side, **no LV copper on any layer** |
| ISO_BARRIER | 70,8 … 84,128 | ISOW7841 (U67) and ISO7741 (U68) straddle it; **milled slot 2 mm wide x 112 mm** at x 77-79 under the isolator bodies; all-layer copper keepout |
| POWER_IN | 12,136 … 100,178 | reverse/ideal-diode LM74800, LM5176 buck-boost, TPS56637 x2, LMR36506, TPS2116/2121, supercaps, fuse clips F1, TVS |
| MCU | 100,118 … 140,178 | STM32H743, FRAM, watchdog, SWD J2, headers J3/J5, RTC battery, buzzer |
| CM5_DISPLAY | 140,70 … 215,135 | CM5 (55x40) + DSI→LVDS bridge SN65DSI83 close to J14 (F side, via short via field), panel power, TPS61500 backlight |
| COMMS | 215,50 … 266,135 | CAN x2, RS-485 isolators (CA-IS3062W), CMCs, Ethernet magjack area, USB hub/ESD |
| OUTPUTS | 84,8 … 266,50 | 13x TPS1HTC30 + TPS48100 fuel/crank with sense/readback; high-current pours toward the top edge and J24 |
| FRONT | 140,50 … 215,70 | button LED drivers / TCA9555 for keys; route to keys on inner layers |
| SPILL | 88,50 … 140,118 | overflow for power/inputs/outputs |
| Top edge (between keys) | 7 slots at x 9.9, 50.8, 94.4, 137.9, 181.4, 224.9, 266.7 | slot 0 empty (HV buffer), J21, J22 (E-stop/D+), J25, J26, J27 outputs |
| Bottom edge (between keys) | same x slots | J17 analog, J18 COM/MPU, J19, J20 DI, J7 expansion; slots 0 and 6 spare |
| Right edge | x 266…280, y 8…175 | J24 fuel/crank (7.62), J28 AUX, J8 router 12 V, J9 RS-485, J6 CAN, **J10 RJ45**, **J11 USB-C service** |
| Antenna | — | none (modem removed); no RF keep-out needed; CM5 has on-module antenna only if a wireless CM5 is fitted → ideally fit a non-wireless CM5 or keep a 10 mm no-copper area at the CM5 antenna corner (CM5 datasheet §4.1.2) |

Edge-connector notes: the 6P 3.81 headers are 24 mm wide; the gaps between key land patterns are ~32 mm, so one header fits per gap.
Terminal THT pins must not land under key pads on the F side (place.py checks THT blocks both sides).
Wire-entry direction of every terminal must be checked in pcbnew (TODO in `place.py`).

## 3. 600 V metering and isolation
- Requirement given: **≥ 8 mm creepage** HV↔LV with a slot. Plan: 12 mm wide barrier band, 2 mm slot through the middle;
  ISOW7841/ISO7741 in SOIC-16W (8 mm package creepage) — slot runs under the package between the pin rows.
- Between phases (L1/L2/L3/N, up to 600 V L-L) on the HV side: ≥ 3.0 mm clearance, ≥ 6 mm creepage between phase nets at the
  terminal and divider top resistors; use slots between J29/J30 terminal pins if the pitch (5.08) is insufficient for creepage.
  Divider strings as series 1206 (R33… 1 MΩ) laid out in straight lines, no vias under them.
- Keep ≥ 8 mm from HV copper to: the top-row key SW9 (y ≤ −0.8), mounting hole H1, the board edge region used by LV connectors, chassis.
- Inner layers: no plane crosses the barrier; HV side has its own local ground (metering AGND) on In1/In4.
- Conformal coat recommended; standards check (IEC 61010-1 / UL 61010 or IEC 60255-27, CAT III 600 V, PD2) is **not done** —
  the 8 mm figure is the requirement given, not a verified standards value.

## 4. Stackup (JLCPCB 6-layer, 1.6 mm, JLC06161H-3313 — JLC's default impedance stackup)
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

## 5. JLCPCB 6-layer rules for DRC (from jlcpcb.com/6-layer-pcb and /impedance, 2026-10)
| Rule | JLC capability | Use in board setup |
|---|---|---|
| Min trace / space | 0.09 mm (3.5 mil) | **0.10 / 0.10** (0.127 default class) |
| Min via drill / diameter | 0.15 / 0.25 mm (0.2 mm on impedance page) | **0.20 / 0.40** default; 0.15/0.30 only under DF40/BGA if needed |
| BGA pad min | 0.25 mm | SN65DSI83 nFBGA-64 0.5 mm pitch → via-in-pad (free on 6L) or dog-bone with 0.15/0.30 |
| Via-in-pad | yes, free on 6L | |
| Drill range | 0.15–6.3 mm, tol +0.13/−0.08 | |
| Board size max | 660 x 475 mm | 284 x 198 OK |
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

## 6. Keep-outs
- HV barrier band x 70-84, y 8-128: no copper, no vias, all layers; slot at x 77-79 (`place.py --slots`).
- F side under the TFT source-PCB band (x 20.6-255.6, y 150-179.5): no parts taller than the gap; J14 just above it.
- Mounting holes H1-H4 (M3 pad, CHASSIS): 1 mm copper ring keep-out from other nets; add more mid-board holes.
- Key land patterns on F side: no THT pins of B-side terminals inside them (already avoided by the slot layout).
- 3 mm from board edge for pours except chassis guard ring.

## 7. Scripted placement (tooling status on the box)
- **KiCad 9.0.2 is installed** (`kicad-cli` at /usr/bin, `python3 -c 'import pcbnew'` works, stock footprint libs at /usr/share/kicad/footprints). No install needed, no sudo needed.
- No Java → Freerouting (autorouter) not runnable as-is; a portable JRE could be dropped into ~ without sudo if wanted (not done).
- `place.py` (works today on the snapshot):
  `python3 place.py --netlist genctl.net --out out/genctl_placed.kicad_pcb` → outline, 6 layers + JLC rules, fixed keys/holes/display connectors,
  edge connectors in slots, every other part binned into its zone by schematic sheet (fallback: net BFS), Quilter-style placement-region rule areas, HV keep-out.
  `--quilter` parks all non-fixed parts outside the outline (what Quilter wants). `--slots` adds the HV slot (add only after Quilter; it wants one outline).
  Current result: 1123 footprints, 0 zone overflows, DRC = only silk warnings + 12 footprint-internal clearance hits (fine-pitch footprints vs 0.10 rule / pad defs; J10 RJ45 padstack/annular warning) — worth a look by the footprint-verification work.
  It is a **binning packer, not a real placer**: parts in a zone are shelf-packed in ref order, not next to their IC. Real placement = Quilter or manual.
- Placeholders in `place.py` (TODO): U9/U10 CM5 connector offset (take from the official CM5 IO board KiCad files), terminal wire-entry rotation, J15 tail fit.
- KiCad MCP servers (GitHub, checked 2026-10-24):
  - mixelpixx/KiCAD-MCP-Server — ~2.9k stars, MIT, active (push 2026-10-01); pcbnew SWIG + KiCad 9 IPC; place/move/array/align components, outline, holes. Most mature.
  - lamaalrajih/kicad-mcp — ~530 stars, last push 2025-10; mostly project/analysis/DRC/BOM.
  - blwfish/kicad-mcp — 27 stars, active; placement audit, FreeRouting, JLC/LCSC search.
  - ProductOfAmerica/mcp-server-kicad — 15 stars, GPL-3, careful file-level footprint placement; "maintenance mode".
  Honest take: for this board they add little over `place.py` — they wrap the same pcbnew calls one footprint at a time, and an LLM driving 1100 parts via MCP calls is slow and no better at placement. Useful later for interactive tweaks/DRC loops. None installed (would need the user to add it as a connector to the bot; `uv` is available on the box so it could run here).

## 8. Order of work once the schematic is final
1. Re-export netlist from the final schematic (copy first), re-run `place.py`; update CM5 offset & terminal rotations.
2. Open in pcbnew: Update PCB from Schematic (to bind symbols↔footprints properly — the script's board has nets but not schematic UUID links; **use "Update PCB from Schematic" on a board that already has the outline/fixed parts, then run place.py --pcb** for a fully linked board).
3. Hand-place HV section, isolation, display/CM5 high-speed parts; pre-route HV and DSI/LVDS.
4. Either Quilter (see QUILTER.md) for the rest, or manual.
