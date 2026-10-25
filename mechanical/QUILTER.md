# Quilter for Blackstart — how it works today and what Ethan has to do

Researched 2026-10-24 from quilter.ai (pricing, free-tier page, blog) and docs.quilter.ai (raw pages saved in `qdocs/`).
Nothing was signed up for, uploaded, or paid.

## What Quilter is
Cloud service: you upload a prepared board file + schematic (+ project), confirm "circuit comprehension" constraints,
pick stackups/fabricator, submit; it returns several placed-and-routed **candidates in the same native format (KiCad in → KiCad out)**,
with "physics rule check" (PRC) reports. Iterate 2-5 times typically. It does not edit schematics or footprints.

## Inputs (KiCad)
- `.kicad_pcb` "starter" board: **exactly one closed outline on Edge.Cuts** (no internal slots/cutouts on Edge.Cuts at upload — they can confuse the parser; add our HV slot afterwards), all footprints present, netlist current.
- `.kicad_sch` (used to auto-detect diff pairs, bypass caps, crystals, switchers) and `.kicad_pro` (optional, recommended). Upload files individually (zip only for Xpedition).
- **Anything inside the outline at upload is treated as locked**; parts left *outside* the outline are the ones it places. → `place.py --quilter` produces exactly this (`out/genctl_quilter_input.kicad_pcb`).
- Placement regions = KiCad **Rule Areas set as keepout with all keepout boxes unticked**, on F.Cu/B.Cu; components are associated to regions manually in the web UI by refdes. `place.py` writes these as `PR_<zone>`.
- Real keepouts (rule areas with boxes ticked) are respected. Pre-routed traces and pours can be preserved.
- Plane detection needs layer names containing "gnd"/"ground" and "pwr"/"power" (our board: GND1, PWR, GND2).
- Stackup + DRC rules: either a pre-defined fabricator profile (**JLCPCB is pre-supported**) or "detected from input files" (beta).

## Capabilities relevant to us
| Topic | Quilter today | Impact on Blackstart |
|---|---|---|
| Layers | 2 to 10+; no fixed limit; 6L fine | OK |
| Vias | through-hole only (blind/buried in development) | OK (we planned through vias) |
| Size / complexity | best at 100-1,000 components, 2,000-5,000 pins, pin density < 20 % | **we have ~1,120 parts / ~3,960 pads → at/above the top of the sweet spot**; expect several iterations or split work |
| Board size | no published limit found (284 x 198 mm not checked with them) | unverified |
| Differential pairs | yes, microstrip only, 100 Ω or 85 Ω diff only; nets must be in a diff-pair netclass and named +/−, P/N etc.; no multi-drop | DSI, LVDS, Ethernet (100 Ω) OK; **USB 90 Ω not offered** → choose 85 or 100 Ω, or pre-route USB |
| Length matching | "coming soon / in development" (Length-Mismatch PRC exists as a check) | pre-route DSI/LVDS or tune after |
| Single-ended impedance | manual only, 50/75 Ω | fine |
| BGA fan-out | beta | SN65DSI83 nFBGA: pre-fan-out ourselves |
| High voltage | **not supported: "low-voltage designs (48 V or less)… does not manage dielectric breakdown, creepage and arcing"; recommends separating HV before submitting** | **pre-place AND pre-route the entire 600 V metering side + barrier**, keepouts over it |
| High current | ≤ 10 A recommended; use power pours ("attempt power pour") | outputs/crank: pre-route or pour |
| Signals | < 6 GHz | fine |
| Runtime | 15 min to 24 h, first results usually < 1 h; email on first and final results | |

## Pricing / licence (as published)
- **Free tier**: same engine, unlimited iterations; "personal, academic and eligible professional exploratory R&D"; **uploads are used to train their models**; not intended for production/commercial boards.
  Blackstart is open-source, so training use is probably acceptable to Ethan, but if he plans to sell boards the free tier terms say use the commercial tier — his call.
- Commercial: per project, priced by number of **unrouted pins at upload** (pre-routed pins are free); unlimited iterations, parallel jobs, 10 % BOM change allowed within a project. **No public prices — "Talk to Sales".**

## Exact steps
Prep (I can do on the box once the schematic is final):
1. Copy the final project; `kicad-cli sch export netlist`; build the linked board (pcbnew Update-from-Schematic, then `place.py --pcb … --quilter`).
2. Hand-place + pre-route: 600 V metering + isolators + slot area (and add a keepout over it), CM5 connectors, DSI83 + LVDS to J14, USB/Ethernet pairs if wanted, crank/fuel high-current paths.
3. Netclasses: `DIFF100` (DSI, LVDS, ETH; names ending _P/_N), `DIFF85`/`DIFF100` for USB; power nets named V*/+12V etc.
4. Save without the Edge.Cuts slot (re-add after).
Ethan must do himself (needs his account / acceptance of terms):
5. Sign up at quilter.ai ("Signup for Free") with his own login; accept free-tier terms (training use) or talk to sales.
6. New project → upload `genctl.kicad_pcb`, `genctl.kicad_sch` (+ sub-sheets if the uploader asks — **unverified whether hierarchical sheets must be uploaded individually**), `genctl.kicad_pro`. Check the parse preview (component/pin count, outline).
7. Stackup step: choose JLCPCB 6-layer (or "detected from input files").
8. Circuit Comprehension: confirm power nets/currents, diff pairs (set 100 Ω, carrier frequency), bypass caps, crystals (Y1/Y2/Y4), switchers (LM5176, TPS56637, LMR36506, TPS61500); associate refs to placement regions.
9. Submit; wait for email; review candidates/PRCs; download KiCad file; run our DRC (`kicad-cli pcb drc`); iterate.
10. Bring the candidate back into the repo board (I can merge/verify on the box).

## Honest assessment
Quilter is a plausible way to route the low-voltage bulk (inputs/outputs/MCU/power), but this board is large for it, the most critical
parts (600 V isolation, DSI/LVDS length matching, BGA fan-out) are exactly what it says it does not do yet, and the free tier
licence is for non-production use. Expect to do HV + high-speed by hand regardless.
