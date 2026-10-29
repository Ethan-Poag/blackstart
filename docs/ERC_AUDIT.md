# ERC audit: why the result is 0 errors / 0 warnings (m7-sch batch 4, item 8)
Scope: the batch-4 HEAD (from 1074b13 onward), KiCad 9 kicad-cli. The per-commit json is review/schematic_audit/out/m7sch_<hash>_erc.json.

## 1. Nothing is suppressed in the project
- genctl.kicad_pro has `"erc": {"rule_severities": {}}`: no severity overrides, no `erc_exclusions`, and no custom `pin_map`. KiCad's built-in defaults apply.
- No sheet contains any ERC exclusion marker.
- check.sh and audit.sh both run `kicad-cli sch erc --severity-all`, so errors, warnings and exclusions are all reported. check.sh prints only the first 40 lines of the listing, but the TOTAL line comes from the full json.

## 2. Deliberate suppressors in the schematic (counted, not hidden)
- no_connect flags: 220 total. ac_metering 26, cm5 76, comms 14, display 41, estop 2, frontpanel 6, inputs 12, mcu 11, outputs 28, power 4. They sit on unused IC pins (CM5 module, display bridge, MCU spare pins, unused BAV99/ADE pins).
- PWR_FLAGs (#FLG): 23 unique references. Each sits on a rail driven only by passive parts, connectors or FET channels, so KiCad cannot see a driver. Examples: VBAT_P, VBAT_AI (new in 4-1), VBAT_ESTOP, BAT_IN, ISO rails.
- Hazard: a PWR_FLAG makes ERC accept a rail that has no real source. Each flagged rail still needs a source in the design review. This audit did not re-prove each one.

## 3. Checks KiCad ignores by default: scratch run with every rule set to "error"
Run on a scratch copy (/tmp/ercx) with all 45 rule keys forced to error: **75 violations**, all from two rules that are off by default.
- **four_way_junction (17):** Q1-Q6 and Q45-Q48 (stacked or hidden FET pins on one node), U7, J11, #PWR0157 and #PWR0339, plus a few very short wire stubs (0.025-0.37 mm). These are benign drawing-style items with no connectivity effect. The short stubs could be cleaned up cosmetically.
- **footprint filter mismatch (58, reported as type footprint_link_issues):** the assigned footprint does not match the symbol's generic filter. Groups:
  - J1/J23/J28/J29 Phoenix 1720819 on generic Conn_01x04;
  - J2, J3/J5, J4/J12/J13, J6-J9, J14/J15/J16, J17-J22, J24-J27 (vendor connector footprints on generic connector symbols);
  - J30 (DO-NOT-FAB placeholder, deferred D-m7-9);
  - RV1-RV6 (varistors);
  - U32-U34 74HC14 SOIC-14;
  - U84 74LVC1G74DP (TSSOP-8; the DP package is TSSOP-8, so this matches);
  - **D3/D4**: see section 4.
  All of these were checked by eye: the footprint matches the MPN for everything except D3/D4.

## 4. Real finding (NOT fixed; needs a ruling)
- **D3/D4 BAS70 (LCSC C77297, SOT-23) are drawn with the 2-pin Device:D_Schottky symbol (pin 1 = K, pin 2 = A) on a SOT-23 footprint.**
- The standard BAS70 SOT-23 pinout (Nexperia) is 1 = anode, 2 = n.c., 3 = cathode. The C77297 maker's pinout is UNVERIFIED.
- As drawn, pad 1 carries BB_BOOT1/2 (intended cathode) and pad 2 carries Net-(D3-A) (intended anode). Pad 3, the real cathode, is unconnected.
- With the Nexperia pinout, the diode is not in circuit at all: pad 2 is n.c.
- Fix options: a 3-pin BAS70 symbol, or pad remapping after the C77297 datasheet is opened. This needs a decision from the lead.

## 5. Conclusion
ERC 0/0 is genuine for the default rule set. Nothing is excluded or downgraded. The 75 default-ignored items are benign apart from D3/D4.

## D23 LM4040A25 polarity check (m7-sch Batch 7, 2026-10-28 ~5:35 PM HST)
- Datasheet: TI LM4040, SLOS456Q (rev. April 2026), ti.com/lit/ds/symlink/lm4040.pdf, opened this session. **Table 5-1 Pin Functions, p4:** DBZ (SOT-23) pin 1 = CATHODE ("Shunt Current/Voltage input"), pin 2 = ANODE ("Common pin, normally connected to ground"), pin 3 = "*" ("Must float or connect to anode"; TI recommends tying it to the anode in high-EMI / high-switching-noise applications). IZ max 15 mA (abs max table, p4-5). §8.2.2.2 "Cathode and Load Currents" p27.
- Netlist (MEASURED, kicad-cli export of the committed schematic): D23.1 (K) = VBAT_AI; D23.2 (A) = AI_VSET together with R129.1; R129 (10k) pin 2 = GND; D23.3 unconnected; C131 100n across VBAT_AI / AI_VSET.
- Circuit intent: D23 is a "floating" shunt reference for the high-side PNP 1 mA current sources. Bias current flows VBAT_AI -> D23 K -> A -> R129 10k -> GND, so AI_VSET = VBAT_AI - 2.5 V, and each LM2904B forces 2.5 V across its 2.49k emitter resistor (~1 mA). The bias resistor is on the anode (low) side, which is valid for a shunt reference: the anode does not need to be at ground, only K must be 2.5 V above A with IZ in range. IZ = (VBAT_AI - 2.5)/10k ≈ 0.45 mA at a 7 V rail to ≈ 3.2 mA at the 34.5 V hot maximum (INFERRED), within the 15 mA rating and above the LM4040A25 minimum operating current (tens of µA, datasheet; exact figure not re-quoted here).
- **Conclusion: polarity is correct and intended. No change.** Optional (not done, needs lead ruling): tie pin 3 to the anode (AI_VSET) per the Table 5-1 note for a noisy genset environment; this is a wiring change, so it is only listed.
