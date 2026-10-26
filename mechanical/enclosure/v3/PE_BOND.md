# PE_BOND: removed in Phase 19 (Ethan's decision, Oct 25 2026, via Enginerd)
DIY open-source project, not a certified product.

- There is **no PE wire, no PE boss, no rear PE window, no PE grommet or cover, and no ring terminal, star washer, lug or screw**. The bond-test masks M1-M5 and the bond-test procedure are removed too. The phase 11-18 content is in git history (last at a915be1).
- **The bezel is now bonded to the customer's metal panel through the clamp hardware.** See README "Phase 19". In short: the two TOP clamps (x 72.9 and 203.5) are metal-path clamps. An A2 cup-point M4 screw bites the rear panel face. A tinned-Cu bridge goes to an M3 insert, then an M3 A2 screw through the shell boss web, then an internal tinned-Cu strap, then an M3 screw into a bare (masked) landing boss on the bezel. There is no wire out the back, no screw through the panel, and nothing passes through H1-H3, any PCB pad, or the PCB.
- H1-H3 stay M4 bezel bosses on the CHASSIS pads (unchanged). H4 stays a plain NPTH.
- BCR-11 (the PE_NEW NPTH) is **WITHDRAWN** (BOARD_CHANGE_REQUESTS.md).
