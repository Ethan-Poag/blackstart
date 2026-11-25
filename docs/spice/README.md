# M7 Power Front End & Crank Channel — SPICE Verification (`m7-split-p7`)

Simulated in `ngspice 44.2` (`s1_split.py`, `s2_start.py` / `s2_c601.py`, `s3_holdoff.py`, `s5_ride.py`) built from the committed KiCad netlists (`fcfd095` .. `edbae88`).

## 1. Models Used

- **Vendor models:**
  - Infineon **BSC070N10NS5** (`models/OptiMOS5_100V_Spice.lib`, with `Zthtype=1` dynamic thermal RC network, `Tcase = 149 °F (65 °C)`): `Q1`, `Q2` (front end) and `Q47`, `Q48` (crank channel).
  - TI **TPS48100-Q1** (`models/TPS48100-Q1_TRANS.lib`, SLUM908 unencrypted): `U45` (`CRANK`, `INP1` switched on at `18 ms`, short at `25 ms`).
- **Transistor-level small parts (`models/small.lib`):** vendor-equivalent ON Semi models for `Q121` (`MMBT5401` / `2N5401`), `Q122` (`MMBT3904` / `2N3904`), `D401` (`1N4148W` / `1N4148`), `D402` (`BAT54C` fitted), and `D72` (`SK1010C` / `DSS310`).
- **Behavioral models (`models/behav.lib`):** `LM74800B` (`U1`), `TVSCA` (`D1`, `D69`, `D126 SMDJ40CA` `Vbr = 49.1 V, rd = 0.331 Ω`; `D2 SMBJ40CA` `rd = 1.66 Ω`), `U2LOAD` (`LM5176` `70 W / ≤3.56 A`), and `U5LOAD` (`LMR36506` `2.1 W`). (`s4_efuse.py` applies only to `m7-modular`'s `TPS16630` slot eFuses; `m7-split-p7` uses `TPS1HTC30A` `2.8 A` current-limited switches).

## 2. Sim vs Hand-Calc Comparison

| Check | Metric | Hand Calc (`p7_calc` / `MOD §19.1` / `Rev 3 H2`) | SPICE (`ngspice 44.2`) | Status |
|---|---|---|---|---|
| **Sim 1: Crank Dead Short** (`C201 = 4.7 nF` as-drawn, 8/12 conv.) | `VBAT_ESTOP` max / `Ipk` / `toff` | `tSC ~65 µs` INFERRED (kick unmodelled) | **`110.8 V`** (**> 100 V abs max**), `260.5–330.9 A`, `71.8 µs` (`84.4 V` even at 12 V) | **FIXED (`edbae88`)** |
| **Sim 1: Crank Dead Short** (`C201 = DNP` fixed, 10 R G1PU) | `VBAT_ESTOP` max / `Ipk` / `toff` | Open `TMR` fastest setting (`SLUSEW1C`) | **`≤ 51.0 V`** first trip, `5.8–19.6 A`, `0.4–1.8 µs` | **PASS** (superseded: 22 k + latch-off) |
| **Sim 1 follow-up: EMI-cap nuisance** (`C201` DNP, `R301` 22 k, `R651` 100 k) | Stay-on vs 470 nF / 1 µF + 2.8 A / 10 mH | 10 Ω false-trips (~250 A hand calc) | **PASS_ON** all 6 corners 12/24/32 V, `Ipk ≤ 2.47 A`, SOA **`0.006`**, FLT stays high | **PASS** |
| **Sim 1 follow-up: Dead short with 22 k G1PU, TMR open (auto-retry)** | Kick on auto-retry | `tRETRY ≈ 22.7e6 × CTMR` ~ 0.4 ms | 12 V / 2 µH: **80.6 V**, 104 A, SOA 0.064; 24 V staged retry **111 V**, ~249 A (**> 100 V abs max**) | **FIXED (latch-off)** |
| **Sim 1 follow-up: Dead short with 22 k G1PU + 100 k TMR latch-off** | `VBAT_ESTOP` max / retry | Latch-off per `SLUSEW1C` 7.3.3.2 | 24 V: **45.6 V**, 15 A, 0.7 µs, no retry; 32 V: **50.1 V**, 17 A, no retry. 12 V / 2 µH can still retrigger if VS rings below POR: **80.6 V**, SOA 0.064 (under 85 V target) | **PASS** |
| **Sim 2/2b: Cold Start** (`C601 = 22 nF` as-drawn) | `Q2` worst SOA (60–110% X7R band) | `0.91` (`p7_calc`, nominal `22 nF` assumed) | **`1.35 EXCEEDED`** (`Tj 166 °F / 74 °C`) | **FIXED (`fcfd095`)** |
| **Sim 2/2b: Cold Start** (`C601 = 100 nF` fixed) | `Q2` worst SOA (nom / 60–110% band) | — | **`0.58`** nom / **`0.80`** band (`Tj ≤ 162 °F / 72 °C`), U2 start `19–51 ms` (12 V) / `47–99 ms` (32 V) | **PASS** |
| **Sim 3: Q2 Hold-Off** | DC engage (`−40 / 77 / 185 °F`) | `3.79 / 3.09 / 2.47 V` | **`3.33 / 2.54 / 1.78 V`** (conservative; ~7× above `0.25 V` load drop) | **PASS** |
| | 6 V step `Q122` on (32 V) / U2 off | `46–58 µs` / `≤ 0.25 ms` | **`41–61 µs`** / **`0.09–0.39 ms`**; U5 EN `3.63–4.30 V` | **PASS** |
| **Sim 5: Ride-Through As-Is** (286/288 conv.**) | Longest break w/ MCU alive | `0.15–0.35 ms` (`FW_REQ_BATCH34`) | **`0.2 ms` (O) / `0.1 ms` (G)** @ 12 V; **`1 ms` (O) / `0.1 ms` (G)** @ 24/32 V; SOA **`0.41`** | **PASS** |

\* `s1_short_split_crank.txt` (`C201 = DNP`, `10 pF` stray): 11/12 corners converged; `(32 V, 0.5 µH feed, 2.0 µH out)` aborted during `INP1` turn-on at `18.009 ms`.
\*\* `s5_ride_split_asis_A_B.txt`: 286/288 converged; 2 failed runs in `B` (`12 V G 1 ms 75 µA` bounded by `0.5/2 ms` resets; `24 V G 10 ms 39 µA` bounded by `75 µA` alive and `m7-modular` `39 µA` alive).

## 3. Schematic Changes Applied

1. **`C601` (`U1` HGATE dV/dt cap, `power.kicad_sch`) — commit `fcfd095` (ported from `m7-modular` `a8b475f`):** `22 nF 100 V` (`C313105`) → **`100 nF 100 V`** (`CL10B104KC8NNNC`, `C15725`, same `0603` pad, already on BOM). Eliminates `Q2` cold-start SOA exceedance (`1.35` → `0.80` worst across `60–110 %` X7R band; `0.58` nominal).
2. **`C197` (`U43` FUEL TMR) and `C201` (`U45` CRANK TMR) (`outputs.kicad_sch`) — commit `edbae88`:** `4.7 nF` (`CC0603KRX7R9BB472`, `C106218`) → **DNP** (keeps `0603` pads as placeholder; open `TMR` per TI `SLUSEW1C` Pin 9 *"Leave it open for fastest response setting"*).
   - **Why:** As-drawn `4.7 nF` (`~71.8 µs`) let a `CRANK_OUT` dead short ramp to `260.5–330.9 A`, kicking **`VBAT_ESTOP` to `110.8 V`** (> `100 V` abs max of `U43`/`U45` `TPS48100-Q1`, `Q70`/`Q71` `SQD40P10-40L`, `Q45`–`Q48` `BSC070N10NS5`, and `C199`/`C203`). Even `220 pF` (`C1603`) hit `90.2 V` at `32 V / 0.5 µH` (`9.8 %` margin). Setting `C197`/`C201` to **DNP** trips in `0.4–1.8 µs`, holding **`VBAT_ESTOP ≤ 51.0 V`** (`49 %` margin below `100 V`) and `F2 I²t ≤ 0.0008 A²s` (down from `5.79 A²s`). Also drops an Extended BOM line (`C106218`, `-$0.01`).
   - **Gates re-run (`edbae88`):** ERC `0/0` (`genctl`, `genctl_meter`), BOM `0` mismatches (`1,154` main / `218` meter refs; main board `$266.51` qty 1 / `$226.09` qty 10), `p7_calc.py` OK.
3. **`R295`/`R301` (G1PU) 10 Ω → 22 k `C31850`, and new `R650`/`R651` 100 k `C25803` TMR latch-off (`outputs.kicad_sch`) — Batch 34c.** Needed once `C197`/`C201` are DNP: 10 Ω false-trips a 470 nF EMI cap, and open-TMR auto-retry plus the 22 k slew kicked `VBAT_ESTOP` to 111 V on a 24 V / 2 µH short. Latch-off holds 24/32 V to ≤ 50.1 V with no retry. 12 V / 2 µH can still retrigger through a VS POR dip (80.6 V, under 85 V). Cost about +$0.01 / board. Reset the latch by toggling INP1 or EN, or by VS below POR.

## 4. Ride-Through Options (Recommended Only — Not Applied to Schematic)

Identical to `m7-modular` (`results/s5_ride_split_asis_A_B.txt`, 286/288 converged):
- **As-is (`asis`):** `0.2 ms` (O) / `0.1 ms` (G) @ `12 V`; `1 ms` (O) / `0.1 ms` (G) @ `24/32 V`; worst `Q2` SOA `0.41`.
- **Option A — Hold-off lockout on `U5_EN` while `+3V3_BK` is up** (**+5 parts, +$0.03/board**: 2× `MMBT3904` `C20526` + 3× `0603` R): `0.2 ms` (O & G) @ `12 V`; **`1 ms` (O & G) @ `24/32 V`**; worst `Q2` SOA **`0.51`**.
- **Option B — Option A + `U5` input hold-up** (**+10 parts, +$1.23/board qty 1 / +$0.99 qty 10**: Option A + 2× `SS110` `C2482`, 2× `EEETG1J101UP` `100 µF 63 V` `C178628`, 1× `0603` R): `0.5 ms` (O) / `0.2 ms` (G) @ `12 V`; **`10 ms` (O & G) @ `24 V`**; **`20 ms` (O & G) @ `32 V`**; worst `Q2` SOA **`0.79`**.

## 5. Key Commits (`m7-split-p7`, local only)

- `fcfd095`: **Schematic fix (`C601` 22 nF → 100 nF `C15725`) + ERC/BOM/`p7_calc` gates**.
- `6cbcff1`, `efc8dd1`, `0083b85`, `8170cca`, `34948ec`, `6372b69`: SPICE decks, Sim 2/2b (`1.35` → `0.80`), Sim 5 (`286/288`).
- `edbae88`: **Schematic fix (`C197`/`C201` 4.7 nF → DNP) + ERC/BOM/`p7_calc` gates**.
- Batch 34c: **`R295`/`R301` 22 k + `R650`/`R651` 100 k TMR latch-off** + ERC/BOM/`p7_calc` gates.

**Verdict (`m7-split-p7`):** Power front end and `VBAT_ESTOP` crank/fuel channels are **CLEARED FOR PLACEMENT** (Option A/B ride-through deferred for Ethan's decision). 22 k G1PU plus 100 k TMR latch-off is required with the DNP TMR capacitors.
