# Blackstart (genctl) enclosure: low-volume, minimum-part-count concept. Rev C (2026-10-24)

## Scope and rules
- **Who it's for:** prototype-first, built for Ethan's own use (1-5 units). A later sold version is possible; production changes are noted briefly in §7.
- **No hard tooling and no mould setup:** CNC, SLS/MJF/SLA printing, laser/knife/water-jet cutting, and catalogue parts only.
- **Kept from rev B:**
  - The unit is self-contained.
  - Its rear body slides in from the front through the cutout.
  - The customer panel sits behind the bezel rim and gasket, held by 6 rear hook clamps.
  - Keys: 24 mm caps, one switch per key, no schematic change.
- **Rev C changes:**
  1. **Plastic rear shell** (SLS PA12), so a loose wire can't short to it. Thermal, earth, clamp and screw joints are redone to suit.
  2. **Keypad with zero setup cost**, made from cut sheet and printed caps.

**Files:**
- `enclosure.py`: parametric CadQuery; it imports `../geometry.py`.
- `render.py`
- `step/*.step|stl`: one per part.
- `enclosure_assembly.step`
- `exploded_view.png`
- `section_view.png` and `section_view_detail.png`: cut at x = 72.6 through key 2 and a top clamp.

Rebuild with `/workspace/cqenv/bin/python enclosure.py && /workspace/cqenv/bin/python render.py`. The script also includes an interference check: in the final model, none of shell/PCB, bezel/display, shell/clamps or shell/panel overlap.

## 1. Part count and BOM (rev C)

| # | Part | Qty | Process | 1-5 units, $/unit (rough) | 100 units, $/unit (rough) |
|---|---|---|---|---|---|
| 1 | Bezel 329x255, 6061-T6, black anodise. It includes the key pockets, display ledge, gasket rim, 3 PCB bosses, the PE boss (H4) and blind M4 taps | 1 | 3-axis CNC from 12.7 mm plate | 300-700 (1 pc is the high end) | 100-190 |
| 2 | Key caps 24x12, head 26x14, clear | 12 | SLA clear resin (on-demand), frosted rear face; UV clear-coat | 10-25 (set) | 6-12 |
| 3 | Seal/return strips, 1.0 mm translucent silicone, 50A, 268 x 15 mm | 2 | laser-cut (Ethan's laser) from a 300x300 sheet; about 8 strips per sheet | 3-8 (pair) | 2-4 |
| 4 | Nib discs, Ø4 x 1.5 mm translucent silicone | 12 | laser-cut | ~0.5 | ~0.3 |
| 5 | Rear shell, 294x220x58, 3 mm walls (373 cm³). It includes the flange, ribs, clamp pads, 600 V barrier rib, 4 anti-flex posts, vents and drip hoods | 1 | SLS PA12, dyed black (or FR grade, see §3) | 120-250 (FR grade: x1.5-2) | 70-140 |
| 6 | Panel gasket, 2 mm closed-cell silicone sponge, PSA one side | 1 | knife/laser-cut | 10-25 | 3-8 |
| 7 | Hook clamp bracket, 2 mm 304 SS, with a PEM M4 nut | 6 | laser-cut + bent (on-demand sheet metal) | 15-35 (set) | 6-12 |
| 8 | M4x8 flanged button head (ISO 7380-2), bezel to shell | 8 | catalogue | 2 | 1 |
| 9 | M4x10, PCB to bezel (3) + PE stud screw (1) | 4 | catalogue | 1 | 0.5 |
| 10 | M4x16 clamp screws, cup or nylon tip | 6 | catalogue | 2 | 1 |
| 11 | M4 serrated (external-tooth) washer, PE | 1 | catalogue | 0.2 | 0.1 |
| 12 | CM5 passive heatsink (off-the-shelf) + pad | 1 | catalogue | 5-10 | 4-8 |
| 13 | Neutral-cure silicone (DOWSIL 7091 class) + VHB spacers | - | catalogue | 5 | 3 |
| | **Total** | **13 kinds of part, 55 pieces (+6 PEM nuts)** | | **about 475-1065** (5 units: about 475-800) | **about 200-380** |

- **Versus V2:** about 156 pieces.
- **Versus rev B:** 30 pieces. The difference is the keypad: one cast item has become 12 caps + 2 strips + 12 nibs.
- **Every screw is M4**, in 3 lengths.
- **No set-up or mould cost at all.** Rev B's $300-800 keypad mould is gone.

## 2. Keys and keypad (rev C, no mould)

Unchanged:
- Cap 24.0 x 12.0 mm, at a pitch of 43.52 mm.
- Each cap slides in its own 8 mm deep machined pocket.
- Hard stop: the head flange lands on the face at 1.3 mm travel.
- One CTS 228E per key.

Guide clearance is now **0.10 mm per side**. SLA caps are about ±0.05-0.1, so machine the pockets, measure the caps, and sand them to fit. Even with 0.2 mm total play, the "drawer" anti-jam rule still holds: the press point must stay within L/(2µ) = 8/0.6 = 13.3 mm of centre, and the cap corner is at 12 mm. Rest tilt is about 1.4°, roughly ±0.15 mm at a corner.

| Option | Seal | Feel/return | Light | Setup | $/unit (12 keys) | Verdict |
|---|---|---|---|---|---|---|
| **A. SLA clear caps + laser-cut 1 mm silicone strip per row (bonded to the key-band rear and to each cap's rear centre) + laser-cut silicone nib discs** | good: a continuous membrane behind every pocket | the switch's own spring + a light membrane assist | LED → translucent nib → membrane → frosted cap | none | **~15-35** | **chosen** |
| B. Laser-cut clear acrylic caps (2 stacked layers to make the head) + same membrane | good | same | good, and brighter | none | 10-20 | no: CO2 laser kerf taper (0.1-0.3 mm) spoils the 0.1 mm guide fit; the glued 2-layer head is weak |
| C. No membrane; an O-ring/X-ring around each cap body in a groove; switch return only | fair: dirt and ice wear the seal | sticky and draggy (friction) | ok | none | 8-15 | no: rain sealing relies on a moving seal |

**How option A works:**
1. **Bonding the strips:** apply the same neutral silicone used for the display, in the same fixture and cure.
   - Each strip is bonded to the band rear in a ring around each pocket. There is ≥ 1.5 mm of land top and bottom and about 19 mm between keys.
   - Each strip is bonded to the cap's rear only over a central 16 x 4 mm patch. That leaves a ~4 mm free annulus, so the membrane can deflect 1.3 mm without tearing (about 20 % strain).
2. **Nibs:** laser-cut Ø4 discs of 1.5 mm silicone, bonded behind the membrane at the cap centre, with a 0.1 mm free gap to the plunger.
   - The switch's own 200 gf spring returns the cap through the nib, membrane and bond.
3. **Light:** frost (sand or bead-blast) the cap's rear face and sides.
   - Optionally paint the sides black, so light doesn't bleed into the pocket walls.

**Is $20-50 achievable? Yes.** Estimated $15-35 per unit for all 12 keys:
- SLA caps: $10-25.
- Silicone: $3-8.
- Bonding: about $2.
- Plus about 20 min of labour.

**Risks:**
| Risk | Detail / mitigation |
|---|---|
| UV yellowing and brittleness of SLA clear resin | Clear-coat the caps, or move to CNC PC caps later at about $5-10 each |
| Hot spot in light spread | Test one cap |
| Bond-line peel on the 1.5 mm lands | Inspect; the fallback is a laser-cut 1.5 mm aluminium or acrylic clamp strip per row with 4 M4 screws |
| Ice in the 0.1 mm gap | Test at -20 °C; fallback is acetal caps or 0.15 mm clearance |
| Softer feel than V2 | Expected; validate on the 2-key test piece first |

## 3. Rear shell in plastic (SLS PA12)

**Material:**
- **Standard SLS/MJF PA12 is about UL94 HB** (slow burn), and so is PA11. That is fine for Ethan's own units: the 600 V circuits sit behind fuses or current-limited dividers, and the internal barrier helps.
- **For a sold product**, the enclosure of parts at hazardous voltage normally needs **V-1 or better** (V-0 preferred; IEC 61010-1 §9 / UL 6200 enclosure rules — confirm with the test lab).
- **FR options without tooling:**
  - **FR-grade SLS PA12** (EOS and others make PA12 FR grades rated V-0 at a stated thickness; confirm the UL yellow card at the wall thickness used).
  - **FDM ULTEM 9085 or PC-ABS FR.**
  - **Bent aluminium with an internal insulating liner.**
- **FR risks:**
  - Higher cost (x1.5-2).
  - Fewer bureaus stock it.
  - Lower impact strength and elongation.
  - The rating only holds at the certified thickness and colour.
  - Sanding or dyeing can void claims.
- **PA11** has better impact and hinge toughness, but is not FR unless an FR grade is chosen.

**Joints and loads:**
- **Bezel to shell:**
  - The shell flange is 8 mm wide and 2.5 mm thick.
  - 8 x M4x8 **flanged** button heads go from the rear into blind taps in the aluminium (thread in metal, not plastic), so no heat-set inserts are needed.
  - The flange under the head spreads the load on the PA12.
  - Torque 0.8 N·m. PA12 creeps slightly at 60 °C, which the gasket doesn't care about. Re-check the torque after the first heat soak.
  - The heads sit below the rim face: Z 6.5-8.7 vs the rim at Z 9.5.
- **Hook clamps:**
  - 6 clamps, each with 2 hooks (6 x 2.5 mm) that engage **blind pockets** 3.5 mm deep in 2.5 mm external pads on a 3 mm wall. Nothing enters the shell, so no steel sits near the PCB or the 600 V terminals.
  - Load: 40-80 N per clamp to compress the 2 mm gasket to 1.4 mm (allow 150 N for overtightening).
  - Hook bearing stress: about 150 N / (2 x 6 x 2.5 mm²) ≈ 5 MPa.
  - Shear-out of the pocket lip: 2 hooks x 2 sides x 6 mm x 2.5 mm, giving > 2 kN at 40 MPa.
  - Margin is > 10x. Clamp screw torque is ≤ 0.6 N·m.
- **Board stiffness:** 4 shell-integral posts (Ø6, 0.3 mm off the PCB rear, at (100,60), (100,140), (240,60), (240,140)) stop board flex and hold the board when it is pressed. Each needs a Ø10 keep-out pad on the B side.

**600 V barrier and touch checks:**
- **Barrier rib:**
  - The shell has an integral 2 mm rib at x = 12.3, running full height down to 1 mm from the PCB rear, plus a cross rib at y ≈ 125.
  - It encloses the metering terminal strip, so stray LV wires can't reach the HV terminals.
  - A creepage path still exists under the rib through the 1 mm gap. The PCB's own 8 mm creepage and slot remain the primary isolation; the rib is a mechanical wire guard.
- **Clearance checks:**
  - **Shell:** 2.0 mm all round from the board edge to the shell wall.
  - **Clamp hooks:** stay outside the shell.
  - **Joint screws:** sit outside the PCB outline.
  - **PE boss:** at H4, bottom right, far (> 200 mm) from the HV strip.
  - **CM5 heatsink top:** about 35 mm from the shell rear (Z 33.6 vs 59).

**Rear-wall I/O openings (rev D, 2026-10-25):**
- Ethernet and USB-C now mate **through the rear wall**, perpendicular to the board. There is **no side-wall opening** any more.
- J10: HanRun HR963380AE (LCSC C19724763), vertical RJ45 with magnetics, on B.Cu at PCB (214.0, 53.1). Body 16.2 x 16.5 mm, 16.85 mm tall. Its top is at Z ≈ 34.5.
- J11: HRO TYPE-C-31-D-06B (LCSC C47817619), vertical USB-C, on B.Cu at PCB (240.0, 50.0). About 10 mm tall, so its top is at Z ≈ 27.6.
- Rear-wall cut-outs in `enclosure.py` (`REAR_PORTS`):
  - RJ45: 20 x 24 mm well. That is the plug plus room for a finger on the latch.
  - USB-C: 13 x 7 mm. It leaves a 1 mm web to the (240,60) post boss.
- **Height budget behind the board:**
  - PCB rear is at Z 17.6, the inner rear wall at Z 59 and the outer face at Z 62. That leaves about 41.4 mm clear.
  - The jacks do **not** reach the wall. The RJ45 face sits about 27.5 mm in from the outer face, and the USB-C face about 34 mm in.
  - Plugs therefore go into a deep well. That works for a standard RJ45 patch lead, but latch release needs a finger or a tool. A USB-C plug overmold is usually 15 mm or more long, so it **cannot** seat with 34 mm of wall in front of it unless the well is open the whole depth (this cut does that).
  - Decision for Ethan:
    - (a) keep the deep wells;
    - (b) add a raised boss on the shell interior or a small rear daughterboard to bring the jacks to the wall;
    - (c) use panel-mount RJ45/USB-C extension leads in the rear wall.
- The STEP was **not** regenerated: cadquery isn't installed on the build box. Run `python3 enclosure.py` locally.

**Rear protection, IP2X:**
- Pluggable terminals through rear windows.
- Vent slots, top and bottom, each under a 6 mm drip hood.
- The HV window is behind the barrier rib.
- A finger probe can't reach live parts: the terminals themselves are finger-safe and recessed ≥ 10 mm.

## 4. Thermal and earth (the shell no longer spreads heat or bonds earth)

**Thermal:**
- **What does reach the aluminium bezel:**
  - **Display backlight** (~9 W at full brightness). The display is bonded to the bezel ledge over its whole perimeter, so this heat goes into the bezel, which acts as the heatsink.
  - **Power copper**, via the 3 PCB bosses plus the PE boss (thermal vias to the boss pads).
- **Why gap pads from the CM5 to the bezel are not possible:**
  - The CM5 sits on the B side, behind the display, so the display is between it and the bezel.
  - The key bands are filled with switches and edge terminals.
- **CM5 cooling instead:**
  - An off-the-shelf CM5 heatsink.
  - Shell chimney vents: bottom intake and top exhaust, each with a drip hood.
  - Firmware: thermal throttle, plus a backlight dimming rule above 50 °C.
- **Expected margin is thin:** at 60 °C ambient the internal air is about +10-15 K, so the SoC runs at about 90 °C and will throttle. Test it in a chamber.
- **If too hot:** move the CM5 to a board zone outside the display footprint, or add a laser-cut aluminium heat-strap to the bezel rim.
- **Output FETs and buck converters:** keep them on 2 oz copper pours tied to the boss pads.

**Earth/PE:**
- **Dedicated PE boss on the bezel at H4** (274.56, 188.71): a Ø8 boss rises through a **Ø9.5 PCB clearance hole** to Z 18.6. The customer PE ring lug goes on top with an M4x10 + serrated washer, metal to metal with no PCB in the stack.
- **Access:** through the right rear wiring window.
- **Electrical continuity of the bezel:**
  - Anodising insulates, so mask the PE boss top, the 3 PCB boss faces and the M4 taps (spot-face after anodising).
  - The PCB's chassis/shield ground connects to the bezel through the H1-H3 boss pads (plated pads, star washers optional).
  - CAN/RS-485/Ethernet shields go to that chassis copper.
- **Label** the PE stud with the earth symbol (a sticker on the shell).

## 5. Board / hole impact (for the layout owner)

| Item | Change |
|---|---|
| Mounting | **H1-H3 stay M4 screw holes** (Ø4.3, 9 mm pad) at (2.0, -9.25), (274.56, -9.25), (2.0, 188.71). **H4 becomes a Ø9.5 NPTH PE-boss clearance hole** with a chassis-ground keep-out ring. The **2 mid holes are dropped**: there is no bezel behind the display to screw into, which also removes the HV-strip conflict. **4 Ø10 B-side keep-outs** for the shell posts at (100,60), (100,140), (240,60), (240,140) (adjustable in `SHELL_POSTS`). |
| Edges | 2.0 mm from the board edge to the shell. Clamp hooks no longer enter the shell, so the rev B height limit at the clamp positions is lifted. |
| Earth | Chassis-ground pads on the H1-H3 bosses; PE wire to the bezel boss, not to the board. |
| Schematic | No change (one 228E per key). |
| F side | 13 x 16 mm clear around each switch (nib and membrane). |

## 6. Assembly and install

| # | Factory step (per unit) | Min |
|---|---|---|
| 0 | One time per batch: laser-cut the strips, nibs and gasket; frost and fit the caps to the pockets | ~20 (per unit, the first time) |
| 1 | Bezel face-down on a flat plate. Silicone on the display ledge and in rings round each pocket on the band rear; dab silicone on the cap rear centres. Drop the 12 caps in from the front side of the fixture, lay the 2 strips, press on the 12 nibs, place the display on VHB spacers, and tool the glass bead | 15 (+24 h cure) |
| 2 | Plug in the LVDS FFC, backlight and touch connectors; lower the PCB; fit 3 x M4x10 at 1.2 N·m | 6 |
| 3 | Functional test | 5 |
| 4 | Shell over the PCB; 8 x M4x8 flanged screws from the rear at 0.8 N·m | 3 |
| 5 | Stick the gasket on; bag with the 6 clamps and the template | 2 |
| | **Total** | **about 31 min + 20 min one-time prep** |

Field install:
1. Cut the cutout: **295.0 x 221.0 mm, +1.0/-0, R ≤ 3**. Panel **1-5 mm**.
2. Insert the unit from the front.
3. Hook on the 6 clamps.
4. Tighten crosswise to ≤ 0.6 N·m (gasket ≈ 1.4 mm).
5. PE lug onto the bezel stud (M4x10 + serrated washer).
6. Plug in the terminals.

About 10 min, plus the cutout.

## 7. For a later sold version (brief)

- FR-rated shell material (V-0 at the wall thickness used), or a moulded PC/ABS-FR shell.
- CNC PC or LSR keypad (an LSR keypad needs a mould, at about 500+ units).
- Bezel moved to die-cast or a thinner CNC with a bought gasket.
- Agency testing (§8).
- The clamp brackets could become a bought DIN-style clip.

## 8. What else is needed for a real product (prioritised)

1. **Mechanical proof first (this week)**: print and machine 2 keys plus the pocket coupon, and check the 24 mm cap feel, wobble, -20 °C ice behaviour and the light spread.
   Check the Riverdi STEP for the ledge, the notches, and the touch-tail and backlight exits.
2. **Prototype plan**:
   - Spin 1 (3-5 boards): bring up power, CM5, display, keys, metering. Fix the BOM and footprints.
   - Spin 2 (5-10): EMC, thermal and environmental pre-compliance. The mechanics should be final by then.
   - Spin 3 or pilot (20-50): certification samples. Expect 2-3 spins.
3. **Power-input robustness**: 12/24 V battery transients, crank dips, load dump. Pre-test to ISO 16750-2 / ISO 7637-2 pulses (or the IEC 60255-26 equivalent), including reverse polarity and an alternator without a battery.
4. **EMC/ESD/surge** (IEC 61000-6-2 immunity / 6-4 emission; -4-2 ESD ±8 kV on the front and keys; -4-4 EFT; -4-5 surge on the supply and I/O; -4-6):
   - Bond the bezel to PE/chassis via the H4 PE boss (the shell is plastic now).
   - Ground the CAN/RS-485/Ethernet shields.
   - Pre-scan at a test lab before spin 2.
5. **Safety and isolation for 600 V metering**:
   - Verify creepage and clearance against IEC 61010-1 / IEC 60255-27 (CAT III 600 V, PD2). The 8 mm figure is still unverified.
   - Add a hi-pot test at end of line.
   - Certification path: UL 6200 (genset controllers) for North America (confirm its creepage and clearance clauses with a test lab); CE via the LVD (IEC 61010-1 or 60255-27) plus the EMC Directive, with UKCA in parallel.
   - UL 508A applies to the panel builder, not to us.
6. **Thermal**: chamber runs at -30 / +60 °C ambient (+70 °C storage), full I/O load, display at full brightness. Check CM5 throttling and the display's operating range.
   The Riverdi display is rated -20 to +70 °C, so check whether a low-temperature heater or start-up rule is needed.
7. **Firmware safety**:
   - The STM32 owns all engine-protection shutdowns (overspeed, oil pressure, temperature, E-stop readback), independent of the CM5/Linux. Fit an independent watchdog, and make outputs fail safe on reset.
   - Do an FMEA and a fault-injection test list, IEC 61508-style (SIL is not claimed).
   - The E-stop stays hardwired (external).
8. **Field updates**:
   - CM5: A/B rootfs (RAUC or Mender), signed images, update over USB-C or the LAN.
   - STM32: signed dual-bank update via the CM5, with rollback, plus a recovery path over SWD/USB.
9. **Environmental**: conformal coat (acrylic or silicone, with masks on connectors, switches and the CM5 sockets); salt fog and humidity (IEC 60068-2-30/-52); vibration (IEC 60068-2-6, genset 2-4 g); IP65 spray test of the front.
10. **Production test and programming**: pogo-pin bed-of-nails fixture (SWD, CM5 eMMC via USB boot, I/O loop-back, metering calibration against a reference source, hi-pot), with serial number and calibration stored in FRAM.
11. **JLC assembly**:
    - Check the BOM against JLC stock (CM5, ADE9000, isolators and THT terminals are likely consigned or hand-placed).
    - Send THT terminals to wave or hand soldering.
    - Plan order lead times and an alternates list.
    - Panelisation is not possible at 284 x 210: check the size limits.
12. **Connector strain relief and wiring**: pluggable terminals with screw flanges, a ferrule spec, cable-tie points printed into the shell rear, and labelling.
13. **Documentation**: installation manual (cutout template 292 x 218 +1/-0, panel 1-5 mm, clamp torque, torque, wiring, fusing, PE bond), safety instructions, datasheet, Modbus/CAN maps, declaration of conformity file.
14. **Licences (recommendation)**: hardware **CERN-OHL-S v2** (strong reciprocal: keeps derivatives open); firmware **Apache-2.0** (patent grant, easy for integrators), or GPL-3.0 if you want copyleft on the firmware too.
    Use CC-BY-SA 4.0 for the docs. Keep CE/UL marks and the trademark separate (a trademark policy).


## 9. Open points
- Fit test: SLA cap tolerance against the 0.10 mm pocket clearance (test piece first).
- Thermal: CM5 at 60 °C ambient with the heatsink + vents. Decide on moving the CM5 or adding a heat-strap.
- Check the layout for the H4 PE clearance hole: it is 1 mm from the board edge at Ø9.5, so a slightly smaller boss or a move inward may be needed.
- Shell FR grade decision before any unit leaves Ethan's own use.
- Verify the Riverdi STEP against the ledge.

## 10. Metal cap option (ALTERNATIVE; baseline remains the SLA clear caps)

Files: `cap_metal.py` (imports the baseline parameters from `enclosure.py`; it changes nothing in the baseline), `step/metal_cap_*.step`, and `metal_cap.png`, which shows an exploded view plus 2 sections.
**Unchanged:** key positions (`geometry.py`), pocket size and depth (8 mm guide), the enclosure outline, the hard stop (head on the face at 1.3 mm travel), and the switch.

**Design (M1, clip-in light piece):**
- **Cap:** 6061-T6, 24 x 12 mm body, head 26 x 14 x 1.0 mm.
  - Rear cavity 21 x 9 mm (walls 1.5 mm); the front wall is 2.0 mm, including the head.
  - A **16 x 1.6 mm through-slot** in the face lets the LED light out as a light bar.
- **Light piece:** clear **SLA** resin (MJF/SLS nylon is opaque grey, so it is not suitable for light).
  - A rib fills the slot flush with the face, with 0.05 mm clearance per side; a body fills the cavity.
  - The rear is cored out so the LED light enters right behind the slot.
- **Snap clip:**
  - Two cantilever tabs on the long sides, each 1.0 mm thick, 4.5 mm long and 5 mm wide.
  - Each has a **0.35 mm barb** that engages a **0.40 mm deep x 1.0 mm wide undercut groove**, machined 2.0 mm from the cap rear with a T-slot cutter or a side-milled undercut.
  - Bending strain is about 1.5·t·y/L² = 1.5·1.0·0.35/4.5² ≈ 2.6 %. That is fine for tough/durable SLA resins (elongation > 6 %), but marginal for standard clear (about 6 %).
  - Put a 30° lead-in on the barb and a 90° catch face. **Print in Formlabs Clear or a tough clear grade, oriented with the tabs vertical.**
- **M2, simpler:** no clip. A **laser-cut 1.5 mm clear acrylic strip**, 15.9 x 5 mm (cut on Ethan's laser), is glued edge-on into the slot with clear UV or cyanoacrylate glue, then sanded flush.
  - The cavity behind it stays empty, and the LED shines through the open cavity into the strip.
  - It needs no snap features and no undercut machining, so the cap is about 20 % cheaper to make. **Recommended for the first metal caps.**
- **Mass:** about 3.8 g for an aluminium cap (11.3 g in stainless) plus a 1.5 g light piece, versus about 3 g for the SLA cap. That is no concern for the 200 gf switch or the silicone return. The heavier stainless cap may rattle slightly under genset vibration, but the silicone bond damps it.

**Sliding and galling in the 8 mm pocket (anodised Al on anodised Al)**
- Plain anodised aluminium on anodised aluminium has µ ≈ 0.4-0.6 dry. At that friction, a cap 24 mm wide must stay within L/(2µ) = 8/1.0 ≈ 8 mm of centre to slide without jamming, but the cap corner is 12 mm from centre, so the cap **would jam** on an end press.
- **Chosen: PTFE-impregnated hard anodise** (Type III, 25-40 µm, black, PTFE-sealed) on the caps only. The bezel stays Type II.
  - µ ≈ 0.1-0.2, so the limit becomes 8/0.4 = 20 mm or more, with good margin over the 12 mm corner.
  - Galling is no longer an issue (hard oxide on oxide).
  - Spec the cap size **after the finish**: 24.00 x 12.00 -0.03/-0.06. Hard anodise grows about 50 % of its thickness outward, so pre-machine the caps about 0.03 mm under per side.
  - Pocket clearance stays **0.10 mm per side**.
  - Not chosen: an acetal/PTFE sleeve per pocket (12 extra parts, thinner pocket walls) and a looser 0.2 mm clearance (more wobble, still µ-limited).
- **Stainless (303/304) alternative:**
  - Bead-blasted, no anodise.
  - Stainless on Type II Al has µ ≈ 0.3-0.4, which still fails the anti-jam rule, so it needs a PTFE (Xylan-type) coating on the cap.
  - About 3x the mass.
  - Machining costs about 1.3-1.8x more.

**Light leakage**
- The black hard-anodised cap is opaque, so light exits only through the slot.
- Avoid leaks around the rib (0.05 mm fit, plus a black paint pen on the light piece's side faces except the rib), or bond with black silicone.
- The LED's spill into the pocket gap is absorbed by the black pocket. Optionally add a black mask ring on the silicone nib.

**Silicone seal bonding**
- Anodised aluminium needs a **silicone primer** (DOWSIL 1200 OS or equivalent), wiped on the cap's rear rim and allowed to dry 30-60 min, before the 7091 bond to the silicone strip.
- For M1, bond the strip to the primed cap rim and the light piece rear together.
- PTFE-sealed anodise bonds poorly. **Mask the cap rear face during PTFE sealing**, or lightly abrade and prime it.

**Hard stop and travel:** unchanged. The head flange lands on the face at 1.3 mm, the switch makes at 0.8 ± 0.2, and the silicone nib takes up the overtravel. Metal-on-metal at the stop is fine for hail and glove punches.

**Manufacturing routes and cost (ROUGH estimates, typical online-service ranges, not quotes)**

| Route | 12 pcs (1 unit) | 100+ pcs (8+ units) |
|---|---|---|
| A. Online CNC, 6061, M1 with undercut groove, or M2 (no groove, ~20 % less), black PTFE hard anodise | $10-25 per cap (set-up and minimum lot charges dominate) | $3-7 per cap |
| B. Online laser/water-jet cut from 10 mm 6061 plate (24 x 12 profile + slot), then a vendor's batch hard anodise. **No head flange is possible** (a 2D profile), so the hard stop moves to 2 printed stop legs on the light piece landing on the PCB at 1.3 mm. Profile tolerance ±0.1 and edge taper mean the guide must be opened to 0.15-0.2 per side (still OK at µ 0.15). The cap is retained only by the bond | $2-4 per cap cut, plus an anodise lot charge of $60-150 per batch, so effectively $8-15 per cap at 12 | $1-2.5 per cap |
| Light pieces: SLA clear (M1) or laser-cut acrylic (M2, Ethan's laser) | $0.5-1.5 per piece / ~$0.1 | $0.3-0.8 / ~$0.05 |

**Per-unit key cost (12 caps + light pieces + silicone strips and nibs at $3-8) vs the $20-50 target:**

| | 1 unit (12 pcs) | 100+ pcs (8+ units) |
|---|---|---|
| CNC route | about $130-320: **over target** | about $40-95: **target met only at the low end** |
| Laser-cut route | about $100-190: over target, because of the anodise lot charge | about $20-45: **within target**, but with a looser guide and a bond-retained cap |

The SLA baseline stays at $15-35.

**Recommendation:**
- Keep SLA caps for the first build.
- If metal is wanted, order one CNC M2 set (12 caps, PTFE hard anodise, acrylic strips glued in) for evaluation, accepting about $150-300 for that one set.
- Move to M1 or batch CNC at 100+ pieces if it's adopted.

## Panel jacks — recommendation (not implemented)
The panel jacks stay on the main board for v4. We recommend moving them to a small daughterboard joined by a ribbon cable or board-to-board connector. That would decouple panel geometry from the main PCB, free routing space, and let the jacks be revised without a main-board respin.
