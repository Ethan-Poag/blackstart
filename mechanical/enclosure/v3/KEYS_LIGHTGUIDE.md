# Keys and light guide v3: 12 keys, 24 x 12 mm caps, one CTS 228EMVARGBFR per key
Cost interpretation: Ethan's "key assemblies about $20-50 per unit" is read as **the whole set of 12 keys per controller unit** (caps + light path + seal + switches). Per-key that is $1.7-4.2. (INFERRED interpretation; if he meant per key, both options pass easily.)
Switch (both options, MEASURED Digi-Key UK page 228EMVARGBFR, checked 2026-10-25): 5.5 mm actuator height, 0.7 mm travel, 200 gf, 100k cycles, IP67, RGB; GBP 2.08 @1, 1.749 @10, 1.4448 @100.
Geometry (both): pitch 43.52 (board, MEASURED), plunger top Z 10.5 (PCB F Z 16.0 INFERRED - 5.5 MEASURED).

| | **A (chosen): SLA clear cap in CNC/laser pocket + laser-cut silicone strip + silicone nib** | B: SLS PA12 key carrier (one per row) with guide bores + SLA cap with 2 guide pins + laser-cut acrylic diffuser |
|---|---|---|
| Parts / key | cap (SLA 8001 clear, frosted rear), share of 1.0 mm translucent silicone strip (bonded), D4 x 1.4 silicone nib | cap with 2 x D3 pins (span 16), PA12 carrier row (bores D3.2, 8 mm engagement), 2 mm acrylic diffuser disc, silicone O-ring or membrane for seal |
| Anti-wobble | cap body is guided by the 8 mm pocket, 0.10/side clr (INFERRED fit, sanded). "Drawer" rule: no jam if press offset e < L/(2 mu) = 8/(2*0.3) = 13.3 mm; cap half-width 12 -> OK | pins 8 mm engagement in PA12, 16 mm span -> tilt ~ (0.2 clr)/16 = 0.7 deg; better on long axis, pocket still needed for appearance |
| Even light | LED -> translucent nib -> membrane -> frosted cap; hot spot likely at centre; fix with white print / bead-blast | acrylic diffuser + white PA12 carrier walls act as a light box -> more even (INFERRED) |
| Seal | continuous bonded membrane behind every pocket (good) | needs separate membrane; carrier adds a leak path |
| Fab | SLA + laser-cut sheet, no tooling | SLS + SLA + laser, no tooling |
| Cost, set of 12 @1 unit | caps ~$12 (36.5 cm3 x ~1.1 g/cm3 x $0.30/g JLC 8001, ESTIMATED) + silicone ~$4 (ESTIMATED) + switches GBP 20.99 (~$28, FX 1.33 INFERRED) = **~$44** | caps ~$12 + 2 carriers ~$12 (ESTIMATED ~40 g PA12 @ $0.275/g + min) + acrylic $5 + switches $28 = **~$57** |
| Cost, set of 12 @10 units | ~$12 + $3 + GBP 1.4448 x 12 (~$23) = **~$38** | ~$50 |
| Verdict | **chosen**: within $20-50, simplest, sealed | over budget at 1 unit, better light; keep as fallback if hot spot is unacceptable |

Risks: JLC 8001 resin page (MEASURED) says "not suitable for outdoor use ... UV" -> caps need a UV clear coat or a UV-stable resin (e.g. a clear PC-like resin from another service); SLA tolerance +-0.2 mm (MEASURED, JLC page) is larger than the 0.10 mm pocket clearance -> caps must be printed and sanded/fitted, or pockets cut after measuring caps (see TOLERANCE_STACK.md).
