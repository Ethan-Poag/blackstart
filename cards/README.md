# cards/ — swappable card schematics (Phase 2, m7-modular)

Each card is its own KiCad 9 project on ONE flat sheet, no hierarchy. Sheets are drawn by `tools/schdraw.py` as framed functional blocks: parts that connect directly are wired to each other, and labels are used only between blocks, on slot-connector pins and for rails (rails and GND are power symbols).
Schematics are generated from the locked baseline (tag `baseline-2026-11-23-locked`) by MOVING
the existing parts: values, footprints and LCSC numbers are unchanged; refs are renumbered per card
and the original ref is kept in the `BaselineRef` field (`refmap.json`).

| card | sheet | ERC | parts | files |
|---|---|---|---|---|
| engine (keyed ENGINE slot) | **A2**, 1 page | 0 err / 0 warn | 158 (150 moved + 8 new) | `engine/engine.kicad_sch`, `engine.png`, `engine.pdf`, `engine_slot_pinout.csv`, `net_accounting.csv`, `unaccounted_nets.txt` (empty) |
| di8 (DI-8, type 0x0010) | A3, 1 page | 0 err / 0 warn | 82 | `di8/di8.kicad_sch`, `.png`, `.pdf`, `di8_bom.csv`, `net_changes.csv`, `net_accounting.csv` |
| ai4 (AI-4, type 0x0011) | **A2**, 1 page (Pass 1 grew past A3) | 0 err / 0 warn | 119 | `ai4/…` (same set) |
| hso5 (HSO-5, type 0x0012; fitted twice) | **A2**, 1 page (Pass 1 grew past A3) | 0 err / 0 warn | 97 | `hso5/…` (same set) |
| brk4 (BRK-4, type 0x0013) | **A2**, 1 page (Pass 1 grew past A3) | 0 err / 0 warn | 83 | `brk4/…` (same set) |

Pass 1 (Nov 23, 2026 HST): every LV card has Ioff slot buffers (Nexperia 74LVC125A + 1G125 + 1G07), boot-safe 47k pulls, and an OUT_EN_N pull-up on +3V3_ID. HSO-5/BRK-4 also get 100 nF/100 V per driver VS, a 2.2 µF/100 V bulk cap, ILIM 33.2k, R_SNS 910 and a 4.7k clamp resistor. The engine card gets 100 nF/100 V at the glow VS and 2.2 µF/100 V on VBAT_ESTOP. See `docs/MODULAR_ARCHITECTURE.md` §13.

Rebuild + check: `python3 tools/mklib.py && python3 tools/card_engine.py && for c in di8 ai4 hso5 brk4; do python3 tools/lvcards.py $c; done && python3 tools/mainboard.py`, then `tools/render.sh <card>` and `sh tools/bom.sh <card>`.

`tools/verify_card.py` re-exports the card netlist and checks (1) every moved pin is on the same net
as in the baseline (documented overrides only: glow driver VS VBAT_P -> VBAT_ESTOP), (2) every baseline net
touching the card is internal, on a slot-connector pin, or on a card field header; anything else lands in
`unaccounted_nets.txt` (must be empty), (3) no duplicate refs.

`lib/cards.kicad_sym` + `lib/cards.pretty/`: DIN 41612 C96 (WingTAT 9001-11961 / 9001-12961) and AT24CS32 SOT-23-5.
Footprints are drawn from the LCSC datasheet drawings and are marked VERIFY before layout.
