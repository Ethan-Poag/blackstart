# pcb_v4 low-voltage layout rules (Milestone 6)

Compiled 2026-10-25. Each rule cites a document that was **actually fetched and read** in this session. Local copies are in `/workspace/refs/lr` (box only, not committed). Sources that could **not** be obtained are listed at the end and are *not* relied on.

## 0. Locked / never relaxed
- Locked: board outline, holes, 12 keys, display connectors, CM5 DF40 connectors, the whole 600 V box, the 13 mm barrier, isolators and slots, edge terminals and keep-outs, and hand-routed HV copper.
- 600 V creepage rules stay at 3 mm outer / 1.5 mm inner. Anything that would touch them is flagged, not relaxed. HV parts stay on B.
- Vias: 0.3/0.15 (annular ring 0.075) are allowed only inside the U21 courtyard (`.dru`); 0.4/0.2/0.1 everywhere else.

## 1. Generic rules applied to every LV part (derived from the sources below)
| Rule | Target used by the audit | Source |
|---|---|---|
| HF decap at the supply pin, on the same side or directly underneath on B; via to the plane placed outside the cap-to-pin path | ≤ 5 mm pad-to-pad (most ≤ 2 mm) | AN4938, SN65DSI83 §10.1.1, CA-IS2092 §10.4 / UG016, TCA9555 §12.1, TPS2553 §12.1 |
| Bulk caps and inductors inside the regulator hot loop | bulk < 15 mm | TPS56637 §10.1, LM5176 §10.1, TPS61500 §10.1 |
| Series / termination R at the driver | at driver | SN65DSI83 pin table (REFCLK "series resistor near the source") |
| Pull-ups near the receiver; LED resistors by their LED/driver | — | engineering practice; no specific source |
| Signal passives > 10 mm only where the function requires it | — | audit target set by owner |

## 2. Per-device rules
**TPS56637 buck (TI SLVSEG1A)**
- Use ≥ 2 vias each on VIN and GND at the pins.
- 0.1 µF CHF plus ≥ 10 µF ceramic from VIN to PGND, right at the pins.
- 0.1 µF from BOOT to SW.
- Join AGND to PGND at one point.
- Put CIN/COUT as close to the device as possible, with multiple vias.
- Keep SW short and wide; switching current must not flow under the IC.
- Take VOUT sense to the upper FB resistor separately; Kelvin the FB ground to GND.
- Keep the FB node small and away from SW.

**LM5176 buck-boost (TI SNVSAI1D)**
- Two hot loops: CIN–QH1–QL1–RSENSE (buck) and COUT–QH2–QL2–RSENSE (boost). Keep both tight, with small ceramics closest to the IC.
- Minimise the SW1/SW2 areas. Run gate-drive and return paths parallel or stacked.
- Kelvin CS/CSG to RSENSE, with the filter cap at the IC.
- VCC 1 µF and BIAS 0.1 µF go close to the IC. BOOT caps connect directly between BOOTx and SWx.
- Place the FB divider at the FB pin and tie it to the COUT+ terminal.

**LM74800 ideal diode (TI SNOSD95C, LM7480x-Q1)**
- The exposed pad (RTN) must stay **floating**, with no GND pour or vias. Tying it to GND disables reverse-polarity protection (SNOSD95C pin table and §10.4). U1 pad 13 has been checked: it is `unconnected-(U1-RTN-Pad13)`.
- Keep A/DGATE/C short to the MOSFET S/G/D, and HGATE/OUT short to the load-disconnect FET.
- Place TVS and CVS close to the IC.
- Keep the CAP charge-pump cap away from the FETs (thermal).

**TPS2116 power mux (TI SLVSFG1A)**
- Put input/output caps close to the device, with wide VIN1/VIN2/VOUT/GND traces.

**TPS2553 load switch (TI SLVS841F)**
- 100 nF at IN/GND with a low-inductance connection; bulk plus 100 nF on OUT.
- Keep RILIM as short as possible.
- Tie the PowerPAD to the GND plane.

**TPS61500 backlight boost (TI SLVS893F)**
- Minimise the SW node area. Keep the switch–Schottky–COUT loop as short as possible.
- CIN goes close to VIN and GND. Keep a ground plane under the regulator.

**STM32H743 (ST AN4938 Rev 7)**
- Supplies:
  - 100 nF per VDD plus 4.7 µF per package.
  - VDDA: 100 nF + 1 µF.
  - VCAP: 2.2 µF with ESR < 100 mΩ.
  - VDDLDO: 4.7 µF.
  - VBAT: 100 nF.
- Decap placement: as close as possible to, or under, the pins (opposite side for BGA), with a short, wide via to the planes.
- Put the HSE crystal and load caps as close as possible to the MCU.
- Space clocks ≥ 3× trace width from other signals and use few vias. Separate noisy circuits.
- Crystal: AN2867 Rev 24 (keep load caps tight, with a local ground). From teammate notes in /workspace/research/layout_notes.md, which mark every mm value there as inference.
- AN4488 is the F4 note and AN5419 covers H72x/73x; AN4938 is the applicable H74x/75x note.

**SN65DSI83 (TI SLLSEC1I)**
- Decoupling: ≥ 1×0.1 µF + 1×0.01 µF (ideally 2+2) near the power balls; under the BGA on B is recommended.
- Pairs:
  - 100 Ω differential (±20 %), same layer, matched to 5 mil, with matching applied near the mismatch.
  - Pair-to-pair spacing ≥ 3 W; at most 2 vias per pair; bends ≥ 135°.
  - Route adjacent to ground and never over a plane split. Test points only in series and symmetric.
- Use one ground plane; stitch the thermal pad with vias.
- REFCLK: series R near the source.

**CM5 (Raspberry Pi CM5 datasheet, rel. 3; CM4 datasheet rel. 4)**
- MIPI DSI/CSI: 100 Ω differential, intra-pair match ≤ 0.15 mm.
- USB2 / USB3 / PCIe: 90 Ω.
- Ethernet / HDMI: 100 Ω; between pairs ≤ 25 mm is sufficient.
- PCIe RX needs external 220 nF AC caps near the source.
- The CM4/CM5 IO-board datasheets were fetched; they contain mechanical and reference schematics only, with no additional layout rules.

**ADE9000 (ADI datasheet Rev B)**
- VDD: 0.1 µF ∥ 10 µF. DVDDOUT and AVDDOUT: each 0.1 µF ∥ 4.7 µF. REF: 0.1 µF ∥ 4.7 µF to REFGND. All at the pins.
- Join all grounds at a single point (the EPAD).
- Place the 24.576 MHz crystal at CLKIN/CLKOUT.

**CA-IS2092W isolated RS-485 (Chipanalog datasheet v1.07 §10.4, UG016 Rev 1.0)**
- VCC/GNDA and VISO/GNDB: 0.1 µF ∥ 10 µF within 2 mm, same layer as the IC, with no vias between cap and pin (vias go outside the cap).
- VCCL/VISOIN: 1 µF.
- Keep an isolation channel under the package free of planes.
- Optional stitching capacitance; edge ground vias at ≤ 3–4 mm pitch.

**TCA9555 (TI SCPS200E)**
- VCC bulk + HF caps as close as possible, with vias directly next to the pads.
- No impedance concerns at I²C speed.

## 3. Sources NOT obtained
- **AN4488 and AN5419:** not fetched. They don't apply to this part (see AN4938 above).
- **CM5 "design guide":** no separate document was found or fetched. CM5 datasheet rel. 3 was used instead.
- **ADE9000 and AN4938:** curl downloads failed, so they were read via web fetch. There are no local PDF copies.


## 4. 600 V HV rules (Milestone 7, BINDING)
Source: hv_layout_rules_600V.md (compliance sheet, /workspace/compliance/hv_layout_rules_600V.md, 2026-10-25). Not certified; needs professional safety review.
- Phase-phase (incl. GEN vs BUS): 6.6 mm outer / 1.5 mm inner. Phase-N: 5.5 mm outer / 1.5 mm inner.
- HOT to SELV: 8.0 mm clearance, 12.6 mm creepage, and >=12.6 mm copper-free on every inner layer.
- Slots >=2.0 mm wide; where HOT to SELV, >=12.6 mm path around each slot end.
- Hot copper >=8.0 mm from the board edge and >=12.6 mm from H1-H4. Solder mask never counts.
- Exempt: same-chain adjacent divider nodes (>=1.5 mm) and tap nodes (>=0.2 mm). J30 (CT inputs) is treated as HOT.
- J28/J29: >=2.0 mm slots between pins (done in M7: 2.0 x 10.5 mm, x 2.0-12.5).
- Checker: hvrules.py (node-voltage aware, credits creepage around slots). DRU carries the sheet rules at severity warning; no existing error rule was relaxed.
