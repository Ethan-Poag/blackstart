# Failure modes: single-fault notes (schematic level)
The Design Reviewer's table (review/schematic_audit/reviewer.md, Re-audit tables) is the full list. This file carries the faults that were accepted as documented notes by ruling.

| # | Fault | Effect | Detection | Accepted? | Source |
|---|---|---|---|---|---|
| R3-N5 | R627 open, or D137 (BZT52C15) short, on the E-stop reverse-protection pair Q70/Q71 (SQD40P10-40L) | Q70/Q71 stay off; the VBAT_ESTOP load runs through the body diodes: about 0.8 V x 6 A = 4.8 W total, about 2.4 W per FET, a rise of about 216 °F (+120 °C) at 50 °C/W (INFERRED, sqd40p10 DS p1-p2). E-stop still cuts the feed. | None on board (no Vds sense) | **Yes: documented single-fault note, no schematic change** (team-lead ruling 2026-10-28; fixes_safety.md CLOSING C6 and documented-assumptions item 3) | reviewer.md R3-N5 |
