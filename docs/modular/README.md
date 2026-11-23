# docs/modular: supporting files for ../MODULAR_ARCHITECTURE.md (Phase 1, docs only)
- card_layout.png: slot diagram. img/connector_options.png: connector pictures (A = DIN 41612 C96 recommended, B = Samtec PCIe x1, C = Molex Micro-Fit, kept for HV).
- img/A_din41612_C96_male_RA_9001-11961C00A_C5173361.jpg, img/A_din41612_C96_female_vertical_9001-12961C00A_C5173363.jpg, img/B_samtec_PCIE-036-02-F-D-TH_C194068.jpg, img/C_molex_microfit_43045-1600_header.jpg, img/C_molex_microfit_43025-1600_plug.jpg: LCSC product photos (fetched Nov 23, 2026 HST; Micro-Fit photos copied from review/split/pics).
- img/A_din41612_female_datasheet_drawing_9001-12xxx.png, img/B_samtec_PCIE_datasheet_page.png: datasheet pages (LCSC datasheet PDFs).
- cards.csv, slot_pinout_LV.csv, cost_delta.csv, card_assignment_baseline.json.
- tools/: classify_cards.py (needs /tmp/blk/genctl.net from kicad-cli 9 at 5bac9fe and review/springy/blocks), cost_delta.py, card_layout.py.
