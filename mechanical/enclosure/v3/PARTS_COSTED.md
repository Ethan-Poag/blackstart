# Costed on-demand parts list v3 (per controller unit, USD, excl. PCB/display/CM5, shipping, tax)
No quotes requested, no accounts, no uploads. Only two figures are read directly as part prices (switch price breaks; JLC per-gram/minimum rates). Everything that needs a CAD upload is **ESTIMATED** from published per-gram rates or site examples. Qty 100 breaks: only the switch has one (GBP 1.4448, MEASURED).
**Tooling: no item needs hard tooling** (no moulds, dies or fixtures beyond a flat bonding plate and a printed glass-centring jig).

| # | Part | Qty/unit | Process / service | $/unit @1 | $/unit @10 | Label | Tooling? | Source (checked 2026-10-25) |
|---|---|---|---|---|---|---|---|---|
| 1 | Bezel 329x261 CNC 6061-T6 black anodise (baseline) | 1 | 3-axis CNC / any CNC shop (no public price) | 450 | 220 | ESTIMATED | no | n/a (no public instant price without upload/account) |
| 1alt | Bezel as laser-cut 6061 stack (3.18 face + 4.75 + 3.18 ledge) bonded | 3 plates | laser cut / SendCutSend | 200 | 110 | ESTIMATED | no | https://sendcutsend.com/materials/6061-aluminum/ (tolerance +-0.005in and thickness list MEASURED; price needs upload) |
| 2 | Rear shell SLS/MJF PA12 312 cm3 (~315 g) | 1 | SLS PA12, priced as MJF stand-in / JLC3DP | 90 | 90 | ESTIMATED | no | https://jlc3dp.com/news/drastic-material-price-cuts-and-adjusted-post-processing-service-fees (MJF-PA12 $0.275/g (MEASURED rate 2025-08-13) x ~315 g; dyeing extra) |
| 3 | Rear clamp blocks PA12 15.4 cm3 total | 6 | SLS PA12, priced as MJF stand-in / JLC3DP | 8 | 6 | ESTIMATED | no | same ($0.275/g x ~16 g + per-part minimum $1 (MEASURED 'from $1.00')) |
| 4 | Key caps 24x12 SLA clear 36.5 cm3 total | 12 | SLA / JLC3DP 8001 | 12 | 12 | ESTIMATED | no | https://jlc3dp.com/help/article/photosensitive-8001-resin ('from $0.3' (MEASURED) ~$0.30/g x ~40 g) |
| 5 | Silicone strip 1.0 mm translucent 50A + nibs (laser/knife cut) | 2 strips + 12 nibs | cut sheet / McMaster/any | 5 | 3 | ESTIMATED | no | https://www.mcmaster.com/ (page blocked to fetcher) |
| 6 | Switch CTS 228EMVARGBFR | 12 | catalogue / Digi-Key | 27.9 | 23.1 | MEASURED price (FX INFERRED) | no | https://www.digikey.co.uk/en/products/detail/cts-electrocomponents/228EMVARGBFR/17052476 (GBP 1.749 @10 / 1.4448 @100 (MEASURED) x FX 1.33 (INFERRED)) |
| 7 | Heat bar 6061 4.75 mm laser cut ~75x62 | 1 | laser cut / SendCutSend | 20 | 12 | ESTIMATED | no | https://sendcutsend.com/pricing/ (site example small Al part $19.51 (MEASURED example) ; Reddit SCS post qty-break -35% @10) |
| 8 | Thermal pad 1.5 mm 6 W/mK ~50x30 + pad on boss | 2 | catalogue / any | 8 | 6 | ESTIMATED | no | n/a () |
| 9 | Panel gasket 2 mm closed-cell silicone sponge PSA cut ring | 1 | knife/laser / any | 20 | 10 | ESTIMATED | no | n/a () |
| 10 | M4 brass heat-set inserts (clamps) | 6 | catalogue / McMaster 94180A353 class | 3 | 2 | ESTIMATED | no | https://www.mcmaster.com/94180A353/ (page blocked to fetcher) |
| 11 | M4x8 button head (bezel-shell 8) + M4x10 (PCB 3 + PE 1 + heat bar 2) | 14 | catalogue / any | 3 | 2 | ESTIMATED | no | n/a () |
| 12 | M4x35 nylon-tip clamp screws | 6 | catalogue / any | 5 | 3 | ESTIMATED | no | n/a () |
| 13 | Neutral-cure silicone (DOWSIL 7091 class) + VHB spacers | - | catalogue / any | 6 | 4 | ESTIMATED | no | n/a () |

**Phase 4 adders: thermal option D and the ALS (all ESTIMATED; PA12 priced as the MJF $0.275/g stand-in; SendCutSend and CNC prices need an upload, so these are not measured):**

| Part | qty1 $ | qty10 $ | basis |
|---|---|---|---|
| PA12 front ring 93 cm3 (~95 g), light grey dye | 30 | 26 | $0.275/g stand-in + dye |
| 6061 fin plate: 4.75 mm base with milled slots + 29 laser-cut 2 mm slats, bonded | 190 | 100 | ESTIMATED CNC + laser |
| 6061 heat pillar 40 x 28 x 19.7 | 25 | 12 | ESTIMATED |
| Gap pad 6 W/mK pillar/plate + foam VHB display tape | 8 | 5 | ESTIMATED |
| PMMA light pipe Ø4 x 19, frosted face, + seal bead | 4 | 2 | ESTIMATED |
| Rear shell lighter (312 -> 203 cm3) | -30 | -30 | stand-in rate |
| **Delta for option D** | **+227** | **+115** | |
| D' instead: + 2 internal 6061 tie bars | +20 | +10 | ESTIMATED |
| Plastic touch-surface alternatives: SLA painted ring instead of PA12 | +40 | +20 | ESTIMATED; glass front ring (chemically strengthened, printed) about +80/+40, needs supplier tooling-free cutting, ESTIMATED |

**Totals (ESTIMATED):** CNC bezel baseline **~$660 @1, ~$390 @10** per unit. Laser-cut bezel stack alternative **~$410 @1, ~$280 @10**. Bezel is >60 % of cost either way.
Key set (items 4+5+6): ~$45 @1, ~$38 @10 -> inside the $20-50 per-set target (interpretation in KEYS_LIGHTGUIDE.md).
**PRICE STAND-IN: every PA12 price here is JLC MJF PA12 ($0.275/g) used as a proxy for SLS PA12. No SLS PA12 price was measured.**

Notes: JLC3DP's July 2026 price update page (MEASURED) lists cuts on PAC-HP/PA12-CF etc. but no new PA12 per-gram figure, so the Aug-2025 $0.275/g MJF-PA12 rate is used. JLC3DP SLS line is 3021PA-F/3301PA/1172Pro (MEASURED home page); MJF PA12 is used as the cost proxy for "SLS PA12" - same material family, check that Ethan accepts MJF. JLC MJF max build 370x276x360 (MEASURED PA12-HP page) fits the 310x242x48 shell. McMaster pages are blocked to the fetch tool -> fastener/sheet prices ESTIMATED.
