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

## Phase 7: line-by-line flush variants, with corrections (2026-10-25; no quotes, no accounts)
Price sources read on 2026-10-25 (MEASURED):
- ATS distributor tables:
  - https://www.qats.com/Search/Distributor/ATS-EXL424-288-R0
  - https://www.qats.com/Search/Distributor/ATS-EXL1-254-R0
  - https://www.qats.com/Search/Distributor/ATS-EXL77-300-R0
  - https://www.qats.com/Search/Distributor/ATS-EXL115-300-R0
  - https://www.qats.com/Search/Distributor/ATS-EXL117-300-R0
- Profile sizes and R per inch: ATS catalogue R15_0121 on media.digikey.com.

**EXL424 is sold only as a 288 x 188 x 16.5 mm stick (or 1220 mm).** Neither the Digi-Key nor the Mouser listing offers cut-to-length. ATS lists cutting and machining services but publishes no price, so that would need a quote.
- V1 uses one 188 x 177 mm piece with the fins vertical.
- That wastes 111 mm (39 %), and the offcut is too short for a second unit. The whole stick is counted.

| V1-flush line | @1 | @10 | Label / source | Replaces in baseline |
|---|---|---|---|---|
| (a) EXL424-288 stick, Digi-Key ATS2208-ND | 79.37 | 70.23 | MEASURED (lowest offer in the ATS table: $54.28 / $51.76, distributor not named) | the closed PA12 rear wall |
| (c) saw cut, 4 holes, 8 mm port notch | 30 | 15 | ESTIMATED (shop rate; about $0 if done in-house) | - |
| (b) PA12 ring 93 cm3 + 8.6 cm3 sleeve, about 104 g x $0.275/g + dye | 32 | 28 | rate MEASURED (JLC MJF 2025-08), mass ESTIMATED | - |
| (b) flush finish: SLA ring or CNC face-skim (±0.15 mm) | 40 | 20 | ESTIMATED; **missing from the phase 6 totals** | - |
| (d) heat pillar, now stacked laser-cut plates (was a $25/$12 block) | 12 | 7 | ESTIMATED | CM5-to-bezel heat bar |
| (d) gap pads + foam VHB display tape | 8 | 5 | ESTIMATED | - |
| (d) light pipe + silicone bead | 4 | 2 | ESTIMATED | - |
| (d) ring retention: 8 M3 heat-set inserts + screws (pips are printed) | 4 | 3 | ESTIMATED; newly counted | - |
| (e) shell 312 -> 203 cm3 (about 110 g x $0.275/g) | -30 | -30 | rate MEASURED, volume from CAD | shell baseline $90 / $90 |
| **V1-flush total delta** | **+179** | **+120** | | |

Baseline for comparison (f): PA12 shell $90 / $90 and CNC bezel $450 / $220, both ESTIMATED. The bezel is unchanged in every variant.

Corrections:
- **D fin plate: $190 / $100 -> $120 / $65 (ESTIMATED).** The old figure assumed CNC-milled slots in the base. Laser-cut tab slots with bonded slats remove the milling.
- **Heat pillar: $25 / $12 -> $12 / $7 (ESTIMATED).** The old figure was a solid machined block; it is now a stack of laser-cut plates.
- Two items were missing and are now added: the flush finish (+$40 / +$20) and the ring inserts (+$4 / +$3).

Every flush variant carries a common block of ring + finish + pads + pipe + hardware − shell = **+$58 / +$28**. Totals:

| Variant | @1 | @10 | Throttles above (4 W, idle 25 %) |
|---|---|---|---|
| D-flush | +190 | +100 | 136 F |
| V1-flush (Digi-Key) | +179 | +120 | 136 F |
| V1-flush (lowest listed stick $54.28 / $51.76) | +154 | +102 | 136 F |
| V4-flush (4.75 mm plate $35 / $20, ESTIMATED) | +105 | +55 | 126 F |
| **V6: V4 plate + one ATS-EXL1-254 strip over the CM5 (Digi-Key ATS2193-ND $29.61 / $26.21, MEASURED; 177 mm cut, 77 mm waste) + $10 / $5 machining** | **+145** | **+86** | 131 F |
| V4 with a 6.35 mm plate | +115 | +60 | 127 F (1 F gain: not worth it) |

Every ESTIMATED figure above would be replaced by a quote: the SendCutSend plate and slats (price needs an upload), a CNC shop for machining and the face-skim, and ATS for a cut-to-length EXL424.


## Phase 8 options (delta vs baseline, USD qty 1 / qty 10)
| Option | @1 | @10 | Lines | Depth |
|---|---|---|---|---|
| V6 (Phase 7) | +145 | +86 | see Phase 7 | 62.75 mm |
| V6 + display spreader sheet, gap pad, straps | +170 | +101 | +$25 / +$15 ESTIMATED | 62.75 |
| V6 + IP68 40x20 mm fan (Sanyo 109P0405J601, £18.18 at RS UK https://uk.rs-online.com/web/p/axial-fans/1919218, MEASURED; ×1.33 FX INFERRED ≈ $24) + guard, filter, mount $8 / $5 ESTIMATED | +177 | +113 | qty 10 fan price assumed $22 ESTIMATED | 62.75 (fan inside the shell, ESTIMATED fit) |
| Same with a non-IP Vapo fan (Sunon MF40100V1-1000U-A99, "from $2.55", datasheets.com aggregator, MEASURED; 2-wire, no tach) | +156 | +93 | | 62.75 |
| d: V4 flat plate + fan + small CM5 heat sink ($5 / $4 ESTIMATED) | +142 | +86 | | 52.75 + about 10 for the CM5 sink |

## Phase 9: V6 + dual 40 mm fans (Ethan GO, Oct 25 2026). Delta per unit, USD qty 1 / qty 10
| item | qty | qty 1 | qty 10 | label / source |
|---|---|---|---|---|
| V6 (4.75 mm flat plate + ATS-EXL1-254 cut to 177, pad, 4x M3) | 1 | +145 | +86 | from phase 8 (EXL1 Digi-Key ATS2193-ND $29.61/$26.21 MEASURED 2026-10-25) |
| Fan Orion OD4010-05HB10A (5 V, PWM + tach), IP option advertised (not certified) | 2 | 2 x 17 = 34 | 2 x 15 = 30 | ESTIMATED: OD4010-05HB $9.99/$9.59 Mouser and -05HB10A $9.72 @520 MEASURED via aggregator 2026-10-25; IP option +~$5 and qty-1 price not published |
| Washable foam filter + PA12 snap cover with grille | 2 | 8 | 6 | ESTIMATED (cover printed with shell) |
| Fan gaskets (closed-cell 1 mm) + 8x M3x16 screws | 2 | 3 | 2 | ESTIMATED |
| Extra plate machining (2x 38 mm holes, 8 taps) | - | 0 | 0 | ESTIMATED (same laser cut) |
| Harness: 2x JST SH 4-pin 150 mm leads | 2 | 4 | 3 | ESTIMATED |
| **Dual-fan adder** | | **+49** | **+41** | |
| **V6 + dual fans vs V6 passive** | | **+49** | **+41** | |
| **V6 + dual fans vs baseline** | | **+194** | **+127** | (excludes BCR-10 board parts: 2x TPS2553, 2x TMP1075, J4B, ~$6 ESTIMATED) |

## Phase 10 decisions
- Fan pick FINAL: Orion OD4010-05HB10A (standard, 5 V) with gaskets + washable filters; no 12 V Sanyo. Costs above unchanged (IP option not assumed).
- OPTIONAL later change: swap to an IP/sealed-rated fan (Orion IP option, advertised not certified) if salt-air life demands it; ESTIMATED +$5-10 per fan, same 40x40x10.5 envelope and pinout.
- TODO: EXL1 fin height / base / fin thickness stay ASSUMED (8.0 / 2.0 / 1.0 mm) until the ATS drawing or a sample is obtained.

## Phase 11 changes
| item | qty | qty 1 | qty 10 | label |
|---|---|---|---|---|
| PE bond hardware: M4 star washer DIN 6797 J A2, M4 ring terminal (sized in phase 14), flat washer, M4x10 A2 | 1 set | 2 | 1 | ESTIMATED |
| Anodise mask-off M1-M5 on CNC bezel (plugs/caps or post-anodise spot face) | 5 spots | 15 | 5 | ESTIMATED |
| Bond test (operator time, 10 A 4-wire per unit; 25 A type test once) | 1 | 5 | 3 | ESTIMATED |
| PE joint corrosion mitigation (SUGGESTION, optional, not in totals): conversion coat M1-M5 or inhibitor compound | 1 | 3-5 / 0.20 | n/a | ESTIMATED |
| Extra left clamp (PA12 block + M4 insert + thumb screw) | 1 | 4 | 3 | ESTIMATED |
| PP film (Phase 9 hv_sheet) | -1 | 0 | 0 | dropped; it was not in the Phase 9 totals |
| **Phase 11 delta** | | **+26** | **+12** | ESTIMATED |
| Phase 12: third left clamp (PA12 block + M4 insert + nylon-tip thumb screw), see CLAMP_RETENTION.md | 1 | 4 | 3 | ESTIMATED |

## Phase 14 changes
| item | qty | qty 1 | qty 10 | label |
|---|---|---|---|---|
| Left clamp screws: steel nylon-tip -> all-nylon PA66 M4x35 thumb screws (delta) | 3 | +0.5 | +0.3 | ESTIMATED (nylon ≈ $1.00 / $0.60 each vs ≈ $0.83 / $0.50) |
| PE ring terminal correction: M4 insulated ring, blue 1.5-2.5 mm² + yellow 4-6 mm² (ship both; replaces unsized lug) | 2 | +0.40 | +0.25 | ESTIMATED ($0.15 blue, $0.25 yellow) |
| PE boss moved H4 -> PE_NEW (12.3, -7.5); H4 boss deleted; membrane notch | 1 | 0 | 0 | ESTIMATED (same CNC ops) |
| PE access window cover with grommet (OPTIONAL, not in totals) | 1 | 1 | 0.6 | ESTIMATED |
| **Phase 14 delta** | | **+0.9** | **+0.55** | ESTIMATED |

## Phase 15 changes (USD per unit, qty 1 / qty 10, all ESTIMATED; no quotes)
| item | qty | qty 1 | qty 10 | label |
|---|---|---|---|---|
| PA12 SLS window covers: PE 20×23, LEFT_HV 23.5×161, TOP 226×19, BOTTOM 226×20, RIGHT 25.5×154, 3 mm | 5 | +30 | +18 | ESTIMATED ($2 / 6 / 8 / 8 / 6 qty 1) |
| Closed-cell EPDM 1.5 mm gasket rings (hand/die cut) | 5 | +5 | +3 | ESTIMATED |
| Slit EPDM membrane grommet strips 1.0 mm | 4 | +6 | +3.2 | ESTIMATED |
| Split rubber grommet, PE hole Ø10 | 1 | +0.5 | +0.3 | ESTIMATED |
| Foam rings at J10/J11 tunnel feet | 2 | +0.6 | +0.3 | ESTIMATED |
| FIP silicone bead on the fin-plate land | 1 | +1 | +0.5 | ESTIMATED |
| Chimney slots deleted | – | 0 | 0 | ESTIMATED |
| Phase 14 "optional PE cover" line (was not in totals) | – | 0 | 0 | superseded by the PE cover above |
| Nylon screw humidity-soak qualification (one-off, NOT per unit) | – | (150–400 once) | – | ESTIMATED |
| **Phase 15 delta** | | **+43.1** | **+25.3** | ESTIMATED |

## Phase 16 changes (USD per unit, qty 1 / qty 10, ESTIMATED; no quotes)
| item | qty | qty 1 | qty 10 | label |
|---|---|---|---|---|
| Wrap lips on LEFT_HV / BOTTOM / RIGHT covers (8 segments, ≈ 1.4 cm³ extra PA12 SLS) | 8 | +1.5 | +0.9 | ESTIMATED |
| Blind lip grooves in the rear shell (8 × 11 mm, in the SLS geometry) | 8 | 0 | 0 | ESTIMATED |
| LEFT_HV slot 7 → 9 mm and a wider membrane | 1 | 0 | 0 | ESTIMATED |
| First print fit test (one-off, not per unit; 1 extra cover set) | – | (≈ 30 once) | – | ESTIMATED |
| **Phase 16 delta** | | **+1.5** | **+0.9** | ESTIMATED |
- The J30 connector change (Phoenix 1720851 + 1996184) cost is not included here; there is no quote (no vendor contact).

## Phase 18 changes (USD per unit, qty 1 / qty 10, ESTIMATED; no quotes)
| item | qty | qty 1 | qty 10 | label |
|---|---|---|---|---|
| Captive PA66 M3 × 10 slotted pan-head screw + nylon retaining washer (J28–J30 cover latch); boss and tab are in the SLS parts | 1 | +0.3 | +0.15 | ESTIMATED |
| Warning labels, UL 969 laminated PET/polyimide, salt-air grade: cover strip 5.5 × 140 + shell 30 × 15 | 2 | +3.0 | +1.2 | ESTIMATED (custom short-run) |
| **Phase 18 delta** | | **+3.3** | **+1.35** | ESTIMATED |

## Phase 19: DIY cleanup + bezel-to-panel bond through the top clamps (USD per unit, qty 1 / qty 10, ESTIMATED; no quotes)
Removed (Ethan's decisions):
| item (row) | qty 1 | qty 10 | label |
|---|---|---|---|
| P11-1 PE bond hardware (star washer, ring terminal, washer, M4x10) | -2 | -1 | ESTIMATED |
| P11-2 anodise mask-off M1-M5 (5 spots) | -15 | -5 | ESTIMATED |
| P11-3 PE bond continuity test | -5 | -3 | ESTIMATED |
| P14-1 all-nylon left clamp screws, back to ordinary steel M4x35 (delta) | -0.5 | -0.3 | ESTIMATED |
| P14-2 PE ring terminals (blue + yellow) | -0.4 | -0.25 | ESTIMATED |
| P15-1 PE window cover (its $2 share of the cover line; qty 10 pro rata 18 x 2/30) | -2 | -1.2 | ESTIMATED |
| P15-2 PE gasket ring (1 of 5) | -1 | -0.6 | ESTIMATED |
| P15-4 PE split grommet | -0.5 | -0.3 | ESTIMATED |
| P16-1 wrap lips | -1.5 | -0.9 | ESTIMATED |
| P18-1 captive nylon latch screw + washer | -0.3 | -0.15 | ESTIMATED |
| P18-2 warning labels, two UL969 laminated -> one simple printed vinyl/polyester label ($0.5 / $0.25) | -2.5 | -0.95 | ESTIMATED |
| Nylon humidity-soak test (one-off, never in the per-unit totals) | 0 | 0 | removed |
| **Removals subtotal** | **-30.7** | **-13.65** | |

Added (bond through TOP clamps x 72.9 / 203.5):
| item | qty | qty 1 | qty 10 | label |
|---|---|---|---|---|
| A2 M4x35 cup-point clamp screw replacing the ordinary steel screw (delta) | 2 | +0.8 | +0.5 | ESTIMATED |
| M3 brass heat-set insert in the clamp block | 2 | +0.4 | +0.2 | ESTIMATED |
| M3x8 A2 through-boss screw + M3x6 A2 landing screw + 2 internal-tooth washers | 2 sets | +0.8 | +0.4 | ESTIMATED |
| Tinned-Cu strip 0.5 x 6: internal strap (~50 mm) + bridge (~15 mm), cut and bent by hand | 2 sets | +2 | +1 | ESTIMATED |
| Bezel: 2 landing bosses + M3 taps (same CNC setup) | 2 | +5 | +2 | ESTIMATED |
| Anodise mask-off: 2 landings + 1 test spot | 3 spots | +9 | +3 | ESTIMATED (same $3/$1 per spot as M1-M5) |
| Ø3.4 holes in shell + clamp blocks (in the SLS geometry) | - | 0 | 0 | ESTIMATED |
| **Bond subtotal** | | **+18.0** | **+7.1** | |
| **Phase 19 net delta** | | **-12.7** | **-6.55** | ESTIMATED |

Rolled-up (ESTIMATED). Delta vs the CNC baseline = Phase 9 V6 + dual fans plus the later phase deltas (P11 +26/+12, P12 +4/+3, P14 +0.9/+0.55, P15 +43.1/+25.3, P16 +1.5/+0.9, P18 +3.3/+1.35):
| | qty 1 | qty 10 |
|---|---|---|
| Delta vs baseline, before Phase 19 (a915be1) | +272.8 | +170.1 |
| Phase 19 net | -12.7 | -6.55 |
| **Delta vs baseline, after Phase 19** | **+260.1** | **+163.55** |
| Rolled-up unit total, before (baseline $660 / $390 + delta) | 932.8 | 560.1 |
| **Rolled-up unit total, after** | **920.1** | **553.55** |
These totals exclude the PCB, display, CM5, shipping and tax (as above), the BCR-10 board parts (~$6) and the J30 Phoenix connector (no quote). Earlier phase sections are left unchanged for history; their PE, nylon, lip, latch and label lines are superseded by this table.

## Phase 20: primary ground stud (USD per unit, qty 1 / qty 10, ESTIMATED; no quotes)
| item | qty | qty 1 | qty 10 | label |
|---|---|---|---|---|
| M4x30 A2 hex bolt (stud) | 1 | +0.3 | +0.15 | ESTIMATED |
| A2 M4 nuts x2, washers x2, internal-tooth washer x1 | 1 set | +0.4 | +0.2 | ESTIMATED |
| EPDM gasket washer 12x12x1.5 | 1 | +0.3 | +0.15 | ESTIMATED |
| Tinned-Cu strap 0.5x6, ~30 mm | 1 | +1.0 | +0.5 | ESTIMATED |
| M3 A2 landing screw + tooth washer | 1 | +0.2 | +0.1 | ESTIMATED |
| Bezel landing boss + M3 tap (same CNC setup) | 1 | +2.5 | +1.0 | ESTIMATED |
| Anodise mask-off, landing spot | 1 | +3.0 | +1.0 | ESTIMATED (same per-spot rate) |
| M4 ring terminal 1.5-2.5 mm² (blue), supplied loose | 1 | +0.15 | +0.1 | ESTIMATED (phase 14 price) |
| Ground-symbol printed sticker | 1 | +0.3 | +0.15 | ESTIMATED |
| Ø4.5 wall hole (in the SLS geometry) | - | 0 | 0 | ESTIMATED |
| **Phase 20 delta** | | **+8.15** | **+3.35** | ESTIMATED |

| | qty 1 | qty 10 |
|---|---|---|
| Delta vs baseline, after Phase 19 (928bbe8) | +260.1 | +163.55 |
| **Delta vs baseline, after Phase 20** | **+268.25** | **+166.9** |
| Rolled-up unit total, after Phase 19 | 920.1 | 553.55 |
| **Rolled-up unit total, after Phase 20** | **928.25** | **556.9** |
