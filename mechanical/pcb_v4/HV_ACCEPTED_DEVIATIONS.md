# HV accepted deviations (lead/Enginerd, 2026-10-25)

1. Locked HV F.Cu segments at the J28/J29 pins (pre-M7 hand-routed, locked). Accepted by lead even where closer than 7.1 mm to a slot-end corner. Excluded from the failing slot-corner count and reported separately. No board change.

| # | Net | Start (mm) | End (mm) | Width |
|---|---|---|---|---|
| 1 | BUS_L1 | (8.76, 96.31) | (8.86, 96.21) | 0.50 |
| 2 | BUS_L1 | (8.06, 96.31) | (8.76, 96.31) | 0.50 |
| 3 | BUS_L1 | (7.86, 96.51) | (8.06, 96.31) | 0.50 |
| 4 | BUS_L1 | (8.86, 96.21) | (8.96, 96.21) | 0.50 |
| 5 | BUS_L1 | (5.76, 96.11) | (5.16, 96.11) | 0.50 |
| 6 | BUS_L2 | (7.46, 89.11) | (7.36, 89.01) | 0.50 |
| 7 | BUS_L3 | (20.76, 87.71) | (20.76, 87.81) | 0.50 |
| 8 | BUS_L3 | (5.16, 80.81) | (5.76, 80.81) | 0.50 |
| 9 | BUS_L3 | (4.86, 81.51) | (4.76, 81.41) | 0.50 |
| 10 | BUS_L3 | (7.66, 80.81) | (8.96, 80.81) | 0.50 |
| 11 | BUS_N | (4.86, 73.91) | (4.76, 73.81) | 0.50 |
| 12 | BUS_N | (5.16, 73.21) | (5.76, 73.21) | 0.50 |
| 13 | GEN_L1 | (7.66, 46.20) | (8.96, 46.20) | 0.50 |
| 14 | GEN_L2 | (7.66, 38.61) | (8.96, 38.61) | 0.50 |
| 15 | GEN_L3 | (7.66, 31.01) | (8.96, 31.01) | 0.50 |
| 16 | GEN_N | (7.66, 23.41) | (8.96, 23.41) | 0.50 |
| 17 | GEN_N | (10.96, 23.01) | (11.36, 23.01) | 0.50 |
| 18 | GEN_N | (19.76, 19.51) | (22.36, 19.51) | 0.50 |
| 19 | GEN_N | (11.36, 23.01) | (14.76, 19.61) | 0.50 |
| 20 | GEN_N | (5.16, 23.41) | (5.76, 23.41) | 0.50 |
| 21 | GEN_N | (19.66, 19.61) | (19.76, 19.51) | 0.50 |
| 22 | GEN_N | (14.76, 19.61) | (19.66, 19.61) | 0.50 |
| 23 | GEN_N | (47.66, 18.81) | (47.56, 18.71) | 0.50 |
| 24 | GEN_N | (22.36, 19.51) | (22.66, 19.21) | 0.50 |

2. J28/J29 pads 6.94 mm from the routed board edge (Ethan, accepted). Condition: no edge plating on the outline there.

3. RV3 (GEN-side MOV) stays at (25.26, 154.08) mm on B.Cu, inside the BUS area (lead decision, 2026-10-25 6:00 PM HST). Condition: every HV spacing rule passes against its pads and traces. On the m7-wip board of this commit, the reviewer's hvsheet.py finds 0 pairs and my hvrules finds only the accepted J28/J29 edge items. RV3.1 (GEN_L3) and RV3.2 (GEN_N) are still unrouted, so this must be re-checked once their copper exists. A separate read-only RV3 placement study (rv3study) has not reported yet. Growth for RV3 is conditional on Mechanical, and none is committed.
