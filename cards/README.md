# cards/ — swappable card schematics (Phase 2, m7-modular)

Each card is its own KiCad 9 project on ONE flat sheet (A3), nets by local label, no hierarchy.
Schematics are generated from the locked baseline (tag `baseline-2026-11-23-locked`) by MOVING
the existing parts: values, footprints and LCSC numbers are unchanged; refs are renumbered per card
and the original ref is kept in the `BaselineRef` field (`refmap.json`).

| card | sheet | ERC | parts | files |
|---|---|---|---|---|
| engine (keyed ENGINE slot) | A3, 1 page | 0 err / 0 warn | 156 (150 moved + 6 new) | `engine/engine.kicad_sch`, `engine.png`, `engine.pdf`, `engine_slot_pinout.csv`, `net_accounting.csv`, `unaccounted_nets.txt` (empty) |

Rebuild + check: `python3 tools/card_engine.py && tools/render.sh engine`

`tools/verify_card.py` re-exports the card netlist and checks (1) every moved pin is on the same net
as in the baseline (documented overrides only: glow driver VS VBAT_P -> VBAT_ESTOP), (2) every baseline net
touching the card is internal, on a slot-connector pin, or on a card field header; anything else lands in
`unaccounted_nets.txt` (must be empty), (3) no duplicate refs.

`lib/cards.kicad_sym` + `lib/cards.pretty/`: DIN 41612 C96 (WingTAT 9001-11961 / 9001-12961) and AT24CS32 SOT-23-5.
Footprints are drawn from the LCSC datasheet drawings and are marked VERIFY before layout.
