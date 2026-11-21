# Isolation / creepage check: 600 V metering barrier (2026-10-24)

## 1. Which parts sit on which barrier
| Ref | Part | Barrier | Rating (datasheet) | Package creepage/clearance | Mold CTI / material group |
|---|---|---|---|---|---|
| ISOW7841DWER | data + DC-DC isolator | **600 V metering (GND_AC hot) <-> SELV** | 5 kVrms reinforced, VIORM 1414 Vpk, VIOWM 1000 Vrms (TDDB) | CLR >8 mm, CPG >8 mm | CTI >600 V, group I |
| ISO7741DWR | 4-ch isolator | **600 V metering <-> SELV** | 5 kVrms reinforced, VIORM 2121 Vpk, VIOWM 1500 Vrms | CLR >8, CPG >8 mm (DW-16) | CTI >600 V, group I |
| AC1005 x8 | current transformers | 600 V side (secondary on GND_AC) <-> external CT loop (J9) | **no insulation rating in datasheets/ac1005.txt** | - | - |
| CA-IS3062W x2 | isolated CAN | SELV <-> CAN field bus (SELV) - functional only | VIORM 849 Vpk | 8 / 8 mm | CTI >400, group I |
| CA-IS2092W | isolated RS-485 | SELV <-> RS-485 field bus (SELV) - functional only | VIORM 560 Vpk (objective DS) | 8 / 8 mm | CTI >400, group II |
| HR963380AE (was HR911131A) | magjack | SELV <-> Ethernet, 2250 VDC/60 s (≈1500 Vrms) functional | - | - | - |
Only ISOW7841 and ISO7741 (and the AC1005 CTs) bridge the 600 V barrier. The CAN/RS-485 isolators are SELV-to-SELV and do not need reinforced spacing; they keep the stock footprint.

## 2. Why "8 mm" on a package whose footprint gap is 7.25 mm
- The datasheet CLR/CPG (TI Table 5.6 / 7.6, Chipanalog 隔离特性) is **terminal-to-terminal of the bare package**: shortest path through air / over the moulded body between a lead on side 1 and a lead on side 2. Body width is 7.4-7.6 mm; the leads leave the body side, bend down, and the solder feet sit 0.4-1.27 mm long at a lead span of 9.97-10.63 mm (TI DW0016B). Over the body plus the lead shoulders the path is >8 mm.
- The PCB pads are not the leads. An IPC-7351 pad is deliberately longer than the foot and extends **inward under the body** (heel fillet), so copper from the two sides gets closer than the leads ever do. TI's own DW0016B drawing says exactly this: "IPC-7351 NOMINAL: 7.3 mm CLEARANCE/CREEPAGE" (2.0 mm pads, 9.3 mm row pitch) vs "HV / ISOLATION OPTION: 8.1 mm CLEARANCE/CREEPAGE" (1.65 mm pads, 9.75 mm row pitch). Datasheet note (1) under the insulation table: "care should be taken ... that the mounting pads of the isolator on the printed-circuit board do not reduce this distance ... grooves and/or ribs on a PCB are used to increase these specifications."
- So the manufacturer is not contradicting itself: 8 mm is the part; 7.25 mm was our (stock KiCad) copper.

## 3. Measured distances (footprint geometry)
| Footprint | Pad size | Row centre pitch | Pad inner edge | **Copper gap side-to-side** | Pad outer span |
|---|---|---|---|---|---|
| old: Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm (KiCad stock) | 2.05 x 0.6 | 9.30 | +/-3.625 | **7.25 mm** | 11.35 |
| TI IPC nominal / Chipanalog recommended | 2.00 x 0.6 | 9.30 | +/-3.65 | 7.30 mm | 11.30 |
| **new: genctl:SOIC-16W_7.5x10.3mm_P1.27mm_HV_Slot** (TI HV option) | 1.65 x 0.6 | 9.75 | +/-4.05 | **8.10 mm** | 11.40 |
Foot fit check (new): foot inner edge 3.7-4.6 mm from centre, foot tip <=5.32 mm; pad covers 4.05-5.70 mm -> toe fillet always on pad, heel fillet slightly reduced (TI-approved option).

New footprint also contains:
- **Routed slot 2.0 mm wide x 21.0 mm long** (Edge.Cuts, obround), centred under the body between the rows; ends 5.75 mm beyond the outermost pad edges. Creepage over the board surface from a corner pad around the slot end to the opposite corner pad ~= 14.4 mm (2 x 6.17 mm tangent + 2.05 mm arc). Under the body the path is broken by the slot (2.0 mm >= X = 1.0 mm for PD2, so the groove counts).
- An all-copper-layer keep-out (rule area "ISO_BARRIER") between the pad rows (no tracks, vias, pours).
Pin numbering is unchanged; netlist identical (tools/netcompare.py: 1030/1030 nets, 0 differences); ERC 0/0.

## 4. What the standard asks for (our case)
Assumptions: metering inputs 347/600 V (like DSE 8610, 600 V ph-ph), measuring at a generator/distribution board = **overvoltage category III**, **pollution degree 2** (enclosed controller; PD3 if condensation is expected - then everything below grows), altitude <= 2000 m, reinforced insulation to accessible SELV (CM5/USB/Ethernet/front panel).
Values from **IEC 60664-1** (the basis IEC 61010-1 and IEC 62368-1 build on). I am confident in the 60664-1 table values below; I did **not** have IEC 61010-1 Annex K or IEC 62368-1 Tables at hand - they must be checked by whoever certifies, as 61010-1 adds its own values for CAT III mains circuits.
- Table F.1: line-to-neutral 347 V falls in the "up to 600 V" row -> rated impulse **6 kV (OVC III)**. Reinforced = next step up = **8 kV**.
- Table F.2 (case A, inhomogeneous, PD2): 6 kV -> 5.5 mm; 8 kV -> **8.0 mm clearance (reinforced)**. (OVC II would give 4 kV/6 kV -> 3.0 / 5.5 mm.)
- Table F.4 creepage, PD2, basic: 400 V row: group I 2.0 / II 2.8 / III 4.0 mm; 630 V row: I 3.2 / II 4.5 / III 6.3 mm. Reinforced = 2 x basic.
  - Working voltage 347 V (solidly earthed star, worst conductor to earth): group IIIa FR-4 **8.0 mm**; CTI>=400 laminate 5.6 mm.
  - Working voltage 600 V (corner-earthed delta / IT system, or if we want one design for all systems): group IIIa **12.6 mm**; CTI>=400 (group II) 9.0 mm; CTI>=600 (group I) 6.4 mm.
  - Creepage may never be less than clearance -> at least 8.0 mm everywhere.
- Isolator body: group I mould (CTI>600): 2 x 3.2 = 6.4 mm needed vs >8 mm offered; clearance >8 mm vs 8.0 needed -> **the isolators themselves are just adequate for 600 V reinforced CAT III** (no margin; not CAT IV). Component certifications (VDE 0884-17 reinforced, IEC 61010-1/62368-1 via TUV/CSA) back this; check the certificates' working voltage for 61010-1.

## 5. Board-level verdict
| Item | Now | Needed (reinforced, CAT III, PD2) | Verdict / action |
|---|---|---|---|
| Isolator pad gap | 7.25 mm (stock) | clearance 8.0, creepage 8.0-12.6 | **Fixed**: HV pads 8.1 mm + 2 x 21 mm slot (creepage ~14 mm) |
| Planned layout barrier 8 mm | 8 mm | 8.0 clr / 12.6 cpg (600 V working on FR-4 IIIa) | **Not enough** for creepage at 600 V working |
| Planned layout barrier 12 mm | 12 mm | 12.6 mm | **Slightly short** on plain FR-4. Use **>=13 mm copper-free barrier** on all layers, or specify **CTI>=400 laminate** (then 9 mm), or extend the slot along the whole barrier |
| J7/J8 Phoenix 1720819 L-L | 5.62 mm copper gap | functional/basic between phases at 600 V: clr 5.5 mm, cpg 6.3 mm (IIIa) | clearance OK, creepage **short by 0.7 mm** on FR-4 -> add a 1.5 mm slot between potentials under the header, or CTI>=400 laminate (4.5 mm). Header itself rated 630 V III/2. Header to any SELV copper: >=13 mm |
| MOVs TMOV20RP460E (M7; was V20E385P at 10 mm) | 7.5 mm lead pitch (genctl:TMOV20RP_P7.5mm_inline), L-N; pad edge gap 5.6 mm (reviewer measurement, not re-measured here) | basic 6.3 mm | Clearance: 5.6 mm vs 5.5 mm rule. Creepage across the MOV pads (5.6 mm vs 6.3 mm) is UNVERIFIED: it may be short unless treated as the component's own functional gap. Safety-engineer item. Keep MOV bodies/leads >=13 mm from SELV; add a fuse/thermal protection upstream (external fused terminals per spec) |
| HV dividers 4 x 1M 1206 | ~87-150 V per resistor | 1206 rated 200 V working | OK if laid out as straight chains; keep whole chain in the hot zone |
| **AC1005 CTs / J9** | CT loop pads 4/5 are 4.6 mm from the AC1005 secondary pins (GND_AC = hot); J9 is a 5.08 mm header on the board | external 5 A CT circuits are normally earthed -> at least **basic** (5.5 mm clr / 6.3 mm cpg); if not earthed, **reinforced** | **Not adequate as drawn.** The AC1005 datasheet gives no insulation rating, so the primary-wire/secondary barrier is unproven. Options: (a) move loop pads >=8 mm (or 13 mm) from the secondary pins and use 600 V+ rated insulated wire with sleeve through the window; (b) better: replace AC1005 with a PCB CT that has a stated reinforced rating, or bring the external CT secondaries in on the hot side and treat J9 as hot (finger-safe plug, hot-zone placement) |
| Ethernet/USB/CM5 etc. | SELV | - | Must all be on the SELV side of the barrier |

Solder mask and conformal coating: solder mask is **not** counted as insulation by 60664-1. A coating qualified per IEC 60664-3 (type 1/2) would let PD1 values apply under the coating (much smaller), but needs process control and test; not recommended as the primary means here. A slot/groove is cheaper and robust.

## 5a. Pollution degree ruling (Enginerd, 2026-11-21, m7-sch Batch 14)
Stay at **PD2 plus conformal coat**; no PD3 re-layout. The sealed fanless enclosure supports PD2; the conformal coat (HEAT_PATH.md: acrylic, HV section, not IEC 60664-3 qualified) is extra protection and takes no creepage credit. No distance or rule in this file changes. A site with condensation or conductive dust is outside the PD2 basis (see review/bom_final/BOM_notes.md "PD3 creepage").

## 5b. J28/J29 (J7/J8) constraints, Safety R7-N12 (m7-sch Batch 16, 2026-11-21)
J28/J29 stay Phoenix PC 5/4-GF-7,62 1720819. No isolation number in this file is relaxed.
1. Milled slot between every adjacent pin pair (L1-L2, L2-L3, L3-N), not only L-N; >=8 mm surface path pad-to-pad is the design target. As built (MEASURED): 3 slots per header, 2.0 mm wide, x 1.98-13.53; J28 y 26.17-28.22 / 33.79-35.84 / 41.41-43.46, J29 y 75.99-78.04 / 83.61-85.66 / 91.23-93.28; pads 2.0 mm round on a 7.62 mm pitch. Path INFERRED ~8.97 mm (high-x end) / ~7.15 mm (low-x end). Safety ruling 2026-11-21: 6.3 mm required (table row above), 7.15 mm clears it, slots acceptable as built; extend low-x ends to x <= 1.3 mm at the next revision (NICE TO HAVE, D-m7-22).
2. Header >=13 mm from SELV: MEASURED read-only (pcbnew on the frozen board, nets classified by connectivity with U69/U70 as the only barrier parts): J28 nearest SELV copper 23.64 mm (GEN_N pad 4 to the GND / VBAT_P / +3V3_SAFE inner-layer zones), J29 59.47 mm (slot to GND zone). PASS.
3. No creepage credit for conformal coat (§5a).
4. JLC minimum slot width >=1.0 mm: still to verify (drawn slots are 2.0 mm).
5. "Do not plug or unplug live" at J28/J29: schematic text (ac_metering sheet), INSTALL_SAFETY, README; silkscreen is deferred (D-m7-22).

## 6. To do at layout
1. Draw the barrier: >=13 mm copper keep-out on every layer between the GND_AC zone and everything else (or 9 mm with CTI>=400 laminate called out in fab notes).
2. Isolator slot comes with the footprint; join it to a board barrier slot if the two isolators sit next to each other (one long slot is fine).
3. Slot of >=1.5 mm between the three potentials of J7/J8 (L1/L2/L3/N), or CTI>=400 laminate.
4. Resolve the AC1005 insulation question before the board goes out.
5. Hi-pot test values come from the end-product standard (IEC 61010-1 Table for reinforced, CAT III 600 V); not computed here. The isolators are vendor-tested at 5 kVrms (UL 1577).
