# M7 Power Front End — SPICE Verification (`m7-modular`)

Simulated in `ngspice 44.2` across five decks (`s1_short.py`, `s1b_recover.py`, `s2_start.py` / `s2_c601.py`, `s3_holdoff.py`, `s4_efuse.py`, `s5_ride.py`) built from the committed KiCad netlists (`a8b475f` / `b261e1e`).

## 1. Models Used

- **Vendor models (`models/OptiMOS5_100V_Spice.lib`):** Infineon **BSC070N10NS5** (`Q1`, `Q2`) with its full dynamic thermal RC network (`Zthtype=1` max RthJC/ZthJC, `Tcase = 149 °F (65 °C)`). TI's **TPS48100-Q1** (`TPS48100-Q1_TRANS.lib`, SLUM908 unencrypted) is also present in `models/` for the `m7-split-p7` crank/fuel checks (`U110` bank switch on `m7-modular` is 466 µs+ behind the slot eFuses and modeled as `Lbank = 60/150 nH` + `10 mΩ`).
- **Transistor-level small parts (`models/small.lib`):** vendor-equivalent ON Semi SPICE models for `Q121` (`MMBT5401` / `2N5401`), `Q122` (`MMBT3904` / `2N3904`), `D401` (`1N4148W` / `1N4148`), `D402` (`BAT54C` fitted Vf/Cjo), and `SS310B` (`DSS310`).
- **Behavioral models (`models/behav.lib`):** TI's `LM74800` and `TPS16630` PSpice models are encrypted, so `U1` (`LM74800B`, charge pump `39/75 µA`, `3.98 µs` OV deglitch at `56 V`, reverse-current DGATE comparator), `TPS16630B`/`TPS16630OL` (slot eFuses: `R_ILIM = 3.09 kΩ` → `I_OL 5.36–6.30 A`, `1.0/1.5 µs` SCP trip, `SS310B` freewheel), `TVSCA` (`D1 SMDJ40CA` `Vbr = 49.1 V, rd = 0.331 Ω`; `D2 SMBJ40CA` `rd = 1.66 Ω`), `U2LOAD` (`LM5176` `70 W / ≤3.56 A` constant-power load, `1.17 V` EN/UVLO), and `U5LOAD` (`LMR36506` `2.1 W` constant-power load, `1.16–1.36 V` EN) are behavioral.

## 2. Sim vs Hand-Calc Comparison

| Check | Metric | Hand Calc (`kick_calc` / `pass6_fix_calc` / `MOD §19.1`) | SPICE (`ngspice 44.2`) | Status |
|---|---|---|---|---|
| **Sim 1: Slot Dead Short** (32 V pess, 384/384) | `VBAT_P` max | `47.1 V` (`47.3 V` quoted) | **`45.4 V`** (`≤ 60 V` U2 rating) | **PASS** |
| | `BAT_IN` max | `57.6 V` (`57.2 V` quoted) | **`58.3 V`** (17% below `70 V` U1 max) | **PASS** |
| | `VBAT_SLOTS` max | `56.9 V` (`57.0 V` quoted) | **`53.8 V`** (10.3% below `60 V` SI2309) | **PASS** |
| | eFuse / harness peak | `363 A` / `103 A` | **`372 A`** / **`97 A`** | **PASS** |
| | `F1` I²t / `U65 IN` | `0.053 A²s` / `≤ 40 V` | **`0.0536 A²s`** / **`31.8 V`** | **PASS** |
| | `Q2` Tj max | — | **`151 °F (66 °C)`** (`0.4 mJ`) | **PASS** |
| **Sim 1b: Post-Short Recovery** (loaded, 384/384) | `VBAT_P` min (12 V pess) | — | `3.20 V` (`<4 V` ≤ `1.01 µs`), `Q2` gate `>8 V` in **`7–37 µs`**, MCU **alive**, `SOA ≤ 0.06` | **PASS** |
| **Sim 2/2b: Cold Start** (`C601 = 22 nF` as-drawn) | `Q2` worst SOA (60–110% X7R band) | `0.89` (nominal `22 nF` assumed) | **`1.34 EXCEEDED`** (`Tj 166 °F / 74 °C`) | **FIXED (`a8b475f`)** |
| **Sim 2/2b: Cold Start** (`C601 = 100 nF` fixed) | `Q2` worst SOA (nom / 60–110% band) | — | **`0.58`** nom / **`0.80`** band (`Tj ≤ 162 °F / 72 °C`), U2 start `19–51 ms` (12 V) / `47–99 ms` (32 V) | **PASS** |
| **Sim 3: Q2 Hold-Off** | DC engage (`−40 / 77 / 185 °F`) | `3.79 / 3.09 / 2.47 V` | **`3.33 / 2.54 / 1.78 V`** (conservative; ~7× above `0.25 V` load drop) | **PASS** |
| | 6 V step `Q122` on (32 V) / U2 off | `46–58 µs` / `≤ 0.25 ms` after | **`41–61 µs`** / **`0.09–0.39 ms`** | **PASS** |
| | U5 EN turn-on (`1.16–1.36 V`) | `3.63–4.25 V` | **`3.63–4.25 V`** (`3.68–4.30 V` at `185 °F`) | **PASS** |
| **Sim 4: Slot eFuse** (`R_ILIM = 3.09 kΩ`, 0 fail) | Healthy slot 2 back-feed (`2.6 µF` real `60 A`) | No healthy-slot false trip | **`-13.4 / +21.2 A`**, card `≥ 6.4 / 18.3 / 26.3 V`, **0 trips** (`22 µF` trips at 24–32 V!) | **PASS** (keep cards `≤ 2.6 µF`) |
| | `2 A → 8 A` overload | Regulate `5.36–6.30 A` | Regulates to **`I_OL` in `19–23 µs`**, `VBAT_SLOTS` dips ~1 V | **PASS** |
| **Sim 5: Ride-Through As-Is** (288/288, 0 fail) | Longest break w/ MCU alive | `0.15–0.35 ms` (`MOD §19.1`) | **`0.2 ms` (O) / `0.1 ms` (G)** @ 12 V; **`1 ms` (O) / `0.1 ms` (G)** @ 24/32 V; SOA **`0.41`** | **PASS** (matches hand calc) |

## 3. Schematic Changes Applied

- **`C601` (`U1` HGATE dV/dt cap, `power.kicad_sch`) — commit `a8b475f`:** changed `22 nF 100 V` (`CC0603KRX7R0BB223`, `C313105`) to **`100 nF 100 V`** (`CL10B104KC8NNNC`, `C15725`, same `0603` pad, already on BOM, `-$0.003`).
  - **Why:** X7R bias, cold (`−40 °F / −40 °C`), and tolerance reduce an as-drawn `22 nF` part to `60–85 %` effective capacitance (`13.2–18.7 nF`), pushing `Q2` cold-start SOA to **`1.34` (exceeded)** at `32 V / 75 µA`. `100 nF` lowers `Q2` worst-case SOA across the full `60–110 %` effective band to **`0.80`** (`0.58` nominal) while keeping `U2` startup at `19–99 ms` (well inside the `250 ms` cold-crank budget).
  - **Gates re-run (`a8b475f`):** ERC `0/0` across all 7 projects, BOM `0` mismatches (`true_cost` `$332.86` / `$122.75`), `note_lint` `0` findings (509 notes), `pass6_fix_calc` value check OK.

## 4. Ride-Through Options & Option B Applied (`137bf01`..`e03d2e7`)

Sim 5 (`results/s5_ride_mod_asis_A_B.txt`, 288/288 converged, `0` failed) tested open-circuit breaks (`O`) and battery-side dead shorts (`G`, e.g., starter/harness fault) at `12 / 24 / 32 V`:

- **As-is (`asis`):** survives **`0.2 ms` (O) / `0.1 ms` (G)** at `12 V` and **`1 ms` (O) / `0.1 ms` (G)** at `24/32 V` (Type `G` pulls `BAT_IN` low, clamping `VBAT_P` through `Q1/Q2` body/reverse recovery and collapsing `VBAT_P < U5_EN` even before `Q2` hold-off finishes). Worst `Q2` SOA `0.41`.
- **Option A — Hold-off lockout on `U5_EN` while `+3V3_BK` is up** (**+5 parts, +$0.03/board**, all existing Basic/BOM parts: 2× `MMBT3904` `C20526` + 3× `0603` resistors): extends Type `G` survival to **`0.2 ms` (`12 V`)** and **`1 ms` (`24/32 V`)**; worst `Q2` SOA **`0.51`**.
- **Option B — Option A + `U5` input hold-up** (**+10 parts, +$1.23/board qty 1 / +$0.99 qty 10**: Option A + 2× `SS110` `C2482`, 2× `EEETG1J101UP` `100 µF 63 V` `C178628`, 1× `0603` resistor): extends survival to **`10 ms` (O & G) at `24 V`** and **`20 ms` (O & G) at `32 V`**, and **`0.5 ms` (O) / `0.2 ms` (G) at `12 V`**; worst `Q2` SOA **`0.79`** (note `12 V` is limited because `Q2`'s `20–40 ms` re-ramp outlasts `200 µF` at `2.1 W` `U5` load).

## 5. Key Commits (`m7-modular`, local only)

- `2a8367e`: Initial SPICE decks (`s1_short`, `s2_start`, `s3_holdoff`) and vendor/behavioral models.
- `a5f0a99`: Sim 2b `C601` effective-capacitance band study + Sim 2 rerun with `100 nF`.
- `a8b475f`: **Schematic fix (`C601` 22 nF → 100 nF `C15725`) + full ERC/BOM/note_lint/calc gates**.
- `4f2809e`, `39f38ba`, `ec3bc93`, `9f8e121`: Sim 1 loaded, Sim 1b recovery, Sim 4 eFuse (`0` failed), Sim 5 robustness.
- `7538506`, `b261e1e`: `LM74800B` `DGATE` smoothing + Sim 5 ride-through complete (`288/288` converged, `0` failed).

### 4.1 As-Drawn Option B Verification (`optB_verify.py`, `137bf01`..`e03d2e7`)
Option B (+10 parts on mainboard: `Q123, Q124, R1127-R1129` on `estop` + `D417, D418, R1130, C1122, C1123` on `power`; `+$1.24` qty 1 / `+$0.99` qty 10 -> `$236.47 / $197.07`) was applied and re-verified from the as-drawn values:
- **Sim 2b (`s2_c601_mod_optB.txt`, `C601 = 100 nF`, `60–110%`):** worst `Q2 SOA = 0.81` (`0.8069` at `60 nF, 75 µA, 32 V`, `Tj 162 °F / 72 °C`) vs `0.80` pre-Option B; `70–110%` all `≤ 0.74` (`0.59` nom).
- **Sim 5 (`s5_ride_mod_optB.txt`):** `12 V` `0.5 ms (O) / 0.2 ms (G)` (`SOA ≤ 0.06`); `24 V` `5 ms (O/G)` at `-20%` `160 µF + 1.4 µF` (`75 µA` survives `10 ms`; `170 µF` and nominal `200 µF` survive `10 ms` across all corners, `SOA 0.44`); `32 V` `20 ms (O/G)` (`SOA 0.87`). `1/96` unconverged after retry (`32 V G 0.2 ms 39 µA`).
- **Sim 1/1b (`s1_short_mod_optB.txt`, `32 V` worst-L loaded):** kick/recovery unchanged (`VBAT_P 41.5 V`, `BAT_IN 55.6 V`, `Q2 45 A`, `Tj 151 °F / 66 °C`, `SOA ≤ 0.06`, `U5_EN min` improved `4.08 V -> 9.95 V`).

**Verdict (`m7-modular`):** Power front end + Option B ride-through is **CLEARED FOR PLACEMENT** (keep card input capacitance `≤ 2.6 µF` per card as drawn).
