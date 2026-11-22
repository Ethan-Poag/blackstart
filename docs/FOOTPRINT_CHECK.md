# Footprint verification — rev f (2026-10-24)

Method:
1. Every `genctl:` footprint was compared pad by pad with a fresh LCSC/EasyEDA land pattern pulled by LCSC code (`easyeda2kicad`). The comparison covered pad number, position relative to the centroid, size, drill and shape (rotation allowed).
2. The hand-drawn or ambiguous parts were then checked against the manufacturer drawing (pdftoppm render of the datasheet page).
3. The netlist was checked symbol pin ↔ footprint pad for every reference (`/tmp/fpc/check.py` on a fresh `kicad-cli` netlist).

**Result:** after the fixes, every symbol pin has a pad. The only pads with no pin are mechanical (listed below).

| Part (refs) | Footprint | Checked against | Result | Fix |
|---|---|---|---|---|
| CM5 conn B (U10) | genctl:DF40C-100DS-0.4V | CM5 symbol pins 101-200 vs pads 1-100 | **WRONG**: all 100 conn-B pins had no pad | New `DF40C-100DS-0.4V_B` (pads n+100, same geometry); RPi_CM5_B uses it |
| CM5 conn A (U9) | genctl:DF40C-100DS-0.4V | LCSC C597931 | identical (0.4 mm pitch, 2×50, 0.2×0.7) | – |
| 10 field I/O headers J17–J22, J24–J27 | fell back to WJ15EDGRC-3.81-6P | BOM (KF2EDGRM-5.08-6P C441292) | **WRONG** pitch (3.81 vs 5.08) | n==6 fallback → genctl:KF2EDGRM-5.08-6P |
| J7/J8 GEN/BUS voltage | was KF2EDGRM-5.08-6P (4 of 6) | BOM = Phoenix PC 5/4-GF-7,62 1720819 | **WRONG** part; 2.6 mm L-L copper gap at 600 V | → new footprint below |
| J0 battery, J4 E-stop/fuel/crank, J7, J8 (1720819) | was KiCad GMSTB_2,5_4-GF-7,62 (1 pin/pos, 1.4 drill) | Phoenix 1720819 drilling diagram | **WRONG**: PC 5 has 3 solder pins per potential, Ø1.3 holes, Ø3.2 flange holes | New `genctl:PhoenixContact_PC5_4-GF-7.62_1720819`: rows R+1.83/R+5.08/R+7.62, flange holes at R+12.25, 8.06 mm outboard. Pad Ø2.0 → 5.62 mm copper gap between potentials (Phoenix III/2 creepage 5.5 mm). Body outline is approximate |
| HR911131A RJ45 (J) | genctl:HR911131A_RJ45 | LCSC C5184934 + HanRun drawing | geometry identical (pads renumbered 1-16 from P1..). The two Ø3.25 locating holes were *plated* with zero annular ring | Changed to NPTH |
| CTS 228E RGB switch (SW) | genctl:CTS_228E_RGB (hand-drawn) | CTS 228E Rev F Fig.1 PCB layout | OK: pads 2.2×1.0 at x±4.5 (6.8 inner / 11.2 outer), rows ±0.9/±2.5 (0.8/2.8/4.0/6.0 dims), pegs Ø1.0 at ±1.75, y−1.7. Pin map B,B,A,L1..L4 matches the pad legend | – |
| ZMCT103C window CT (meter T1-T4, Batch 29; Batch 30 doc fix) | genctl:Transformer_Zeming_ZMCT103C | Zeming ZMCT103C datasheet (LCSC C94571) | 2 pins Ø0.9 at 11.8 ±0.2 mm, drill 1.2, pin 1 = S1 (dot, rect pad), body 18.2 × 10.2 mm, **19.2 mm tall**, Ø5 mm window (axis along footprint Y): OK (pass-4). No primary pads: only the external 5 A CT loop pigtail passes the window, never a phase or neutral cable | –
| ~~AC1005 CT (T1-T8)~~ superseded Batch 29 | genctl:AC1005_CT (footprint still in genctl.pretty, unused) | Talema AC1005 drawing + LCSC C6117861 | historic: pins 1/2 15.24 apart, pads 4/5 = loop pads. Not used by either schematic | –
| Keystone 3557-2 ATO clips | genctl:Keystone_3557-2_ATO_clips | LCSC C352820 | geometry identical; 2 legs per clip share a pad number (intentional) | – |
| ACT45B, ADE9000 LFCSP-40 EP4.6, BS-CR2032-8, DSHP02TSGER, FPC 10P/40P, FTSH-105, KF2EDGRM 6P/8P, LM74800 WSON-12, LMR36506 VQFN-HR-9, inductors FNR5020S/MWSA0503S/MWSA1004S/SPM10065/SWPA6045S, MLT-8530, PZ254 2×5, RClamp0524P, SM02B-BHSS, SN65DSI83 nFBGA-64, TPS1H200 MSOP-8-EP, TPS1HTC30 HTSSOP-14, TPS2121 VQFN-HR-12, TPS3431 VSON-8, TPS48100 VSSOP-19, TPS56637 VQFN-HR-10, TPS61500 HTSSOP-14, WJ15EDGRC 2/3/4/6P | genctl:* | LCSC/EasyEDA land pattern by LCSC code | identical pad for pad | – |
| Stock KiCad footprints (TO-252-2 LM317M, D_SMA/SMB/SMC, SOT-23/-5/-6, SOT-563 TPS61023, SOT-583-8 TPS2116, TDSON-8-1 BSC070N10NS5, SOIC-16W isolators, HTSSOP-28 LM5176, LQFP-100, USB-C HRO 31-M-12, TS-1187A, CP_Elec_10x10.5, CP_Radial_D10 P5.0 HV1030, RV_Disc_D21.5 P10) | KiCad 8 lib | package code in the MPN / datasheet package name | package matches MPN | – |
| Unused after rev e (M.2 MDT420B03001, NANO-SIM XG6P, USB3-A HC-USB3.0) | – | – | – | Deleted from genctl.pretty |

Pads with no symbol pin (mechanical, intentional):
- FPC 41/42 and 11/12 (solder tabs).
- SM02B 3/4 (tabs).
- MLT-8530 3/4 (NC legs).

Tie the FPC and SM02B tabs to GND copper at layout if you want them for shielding.

**3D/silk:** EasyEDA-derived footprints carry F.SilkS/F.Fab/courtyard from LCSC. The 228E, PC5 and DF40_B footprints have silk, fab and courtyard rectangles. There are no 3D models (none are referenced, so there are no broken paths).

**Creepage / isolation (from footprints; final check at layout):**
- J7/J8 (600 V L-L): 7.62 mm pitch, 5.62 mm copper gap. Phoenix rates the header 630 V (III/2) with 5.5 mm creepage.
- Hot ↔ SELV barrier (ISOW7841 / ISO7741 / CA-IS on SOIC-16W): the datasheet gives 8 mm package creepage. **The stock KiCad SOIC-16W_7.5x10.3 land pattern leaves only 7.25 mm copper-to-copper between the pad rows (pads at ±4.65, 2.05 long), so it is below 8 mm.** At layout: (a) route a ≥1 mm slot under each isolator body between the rows, which takes the surface creepage path above 8 mm, or (b) use a 'creepage' land pattern trimmed to ≥8 mm. Keep no copper on either domain inside the 8 mm barrier strip. Flagged open: there is no slot or keep-out in the schematic.
- MOVs (RV_Disc P10): 10 mm lead spacing.
- The divider resistor strings must be laid out as series 1206/2512 chains so that each part sees ≤ its rated working voltage (layout item).

## Rev: rear-facing connectors (2026-10-25)
| Part | Footprint | Source | Check |
|---|---|---|---|
| HR963380AE vertical RJ45 magjack (J10), LCSC C19724763 | genctl:HR963380AE_RJ45 | EasyEDA/LCSC land pattern via easyeda2kicad, checked against HanRun DS p.3 (10 pads 0.85x2.9 @1.35, LED pads 1.1x4.2 @ ±4.01/±6.55, shield pad 15 2.5x2.6, 2x Ø1.40 NPTH @ ±7.00) | locating holes set to NPTH; LED pinout differs from HR911131A: orange 11A/12K, green 13A/14K |
| TYPE-C-31-D-06B vertical USB-C 16P (J11), LCSC C47817619 | genctl:USB_C_Receptacle_HRO_TYPE-C-31-D-06B_Vertical | EasyEDA/LCSC land pattern; 4 shell THT tabs renamed S1; 2 NPTH pegs | VERIFY against HRO drawing (only the D-06 drawing was read; D-06B is the 10 mm tall variant, same land pattern per EasyEDA) |
