# M7 WIP (branch m7-wip, NOT master)
Board here = work board t20 (2026-10-25). Worse than d151ff7 on HV opens (20 vs 17) and unconnected (1280 vs 1277; routed 56.40% vs 56.51%). Do not merge.
Changes vs d151ff7: R297/R303 BOM fields; neutral silkscreen; 6 divider resistors re-placed (hvplace); J28/J29 slots extended to x 13.5 (outline edit);
RV1-RV6 -> TMOV20RP_P7.5mm_inline (RV6 moved to 18.4,85.8); J28/J29 PTH pads restored to all copper layers (locked HV parts);
HV re-route (0 HV pair violations by my hvrules), 24 locked F.Cu HV segments kept (HV_ACCEPTED_DEVIATIONS.md). BCR-11 reverted. m7.kicad_dru NOT yet applied.
Known router bug: own stale copper near target counted as connected -> 0.1 mm stubs reported as OK. Fix pending (M7 step 1).
