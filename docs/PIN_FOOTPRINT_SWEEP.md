# Pin / footprint sweep (batch 6 item 3)

Base: 90c4879. Method: (a) every netlist libpart pin number vs footprint pad numbers (KiCad stock + genctl.pretty), 1309 parts;
(b) cross-check of review/schematic_audit/mechanical_parts_fp_vs_sym.csv; (c) every SOT-23/SOT-223/TO-252 semiconductor
pin-name mapping vs its LCSC datasheet (fetched live 2026-10-28 HST).

## Counts
- Parts checked (pin/pad numbers): 1309. Datasheet-verified 3-pin semis: 19 LCSC codes / 114 parts.
- Mismatches found: 11 (D3/D4 BAS70 counted as one family, plus 10 numeric pin/pad cases below).
- Fixed: 1 family (D3/D4 BAS70, commit 90c4879). Left: 10 (all benign or known, below). No further pin-name errors found.

## Datasheet-verified mappings (all MATCH symbol)
| Parts | LCSC | Datasheet pinout | Symbol |
|---|---|---|---|
| MMBT3904 x35 | C20526 JSCJ | 1 B, 2 E, 3 C | 1 B 2 E 3 C |
| MMBT3906 x6 | C2143 JSCJ | 1 B, 2 E, 3 C | same |
| BSS84 x6 | C8492 LRC LBSS84LT1G | 1 G, 2 S, 3 D | 1 G 2 S 3 D |
| IRLML0100TRPBF x8 (Batch 28; was DMN6075S C155242) | C53658 Infineon | G S / D (top view) | 1 G 2 S 3 D (same SOT-23 pinout) |
| AO3401A Q68 | C347476 UMW | 1 G, 2 S, 3 D | same |
| SI2309CDS Q36/39/42 | C10493 Vishay | 1 G, 2 S, 3 D | same (AO3401A symbol) |
| SQD40P10-40L Q70/71 | C141570 Vishay TO-252 | G D S, D = tab | 1 G 2 D 3 S |
| BCP56-16 Q72 | C426787 Nexperia | 1 B, 2 C, 3 E, 4 C (tab) | same (pin 4 = pad 2, same net) |
| BAT54C D7/D8/D121 | C2135 JSCJ | 1,2 A; 3 common K | same (pin names blank in symbol) |
| BAT54C D128-D135 | C37704 Nexperia | 1 A1, 2 A2, 3 K | same |
| BAT54S D65/67/125 | C8592 JSCJ | 1 A, 2 K, 3 common | 1 A 2 K 3 COM |
| NUP2105L D12/13 | C14486 onsemi | 1,2 lines, 3 common (bidir) | 3 = GND_CAN1 |
| SM712 D16 | C12067 Semtech | 3 = ground | 3 = GND_485 |
| LM4040A25 D23 | C9421 TI DBZ | 1 K, 2 A, 3 NC/substrate | 1 K 2 A 3 NC (open) |
| BAS70 D3/D4 | C77297 JSCJ | 1 A, 2 NC, 3 K | FIXED 90c4879 |
| USBLC6-2SC6, SMBJ/SMDJ/SMAJ, 1N4148W, BAT54WS | various | pad 1 = K / stock | match |

## Left (with reason)
1. BZ1 MLT-8530: fp pads 3/4 unconnected (numbered mechanical pads). Need buzzer datasheet decision on tying; no change.
2. J14 FPC 40p pads 41/42, J15 FPC 10p pads 11/12: numbered anchor pads, unconnected. Tie to GND is a design choice; not changed.
3. J16 SM02B-BHSS pads 3/4: mechanical anchors, unconnected; not changed.
4. J4/J12/J13 JST SH: MP pad unconnected; KiCad stock, benign.
5. J30: placeholder, no pads (known D-m7-9).
6. Q72 BCP56: symbol pin 4 has no pad (stock pairing); pin 4 and pad 2 = VBAT_P; benign.
7. U87 74LVC1GU04 SOT-23-5 pad 1 has no symbol pin (NC on part); benign.
8. H1-H4: schematic M3 pad fp vs PCB M4 fp; RV1-RV6: schematic TMOV20RP_P7.5mm_inline vs PCB RV_Disc_D21.5mm. PCB-sync item (PCB untouched).
9. D23 LM4040 anode on AI_VSET (not GND): pin mapping correct; circuit intent not reviewed here.
10. NOT_IN_PCB in audit csv (C286-C292, R531-R533, U77-U79, Y4): PCB update pending.
