"""Shared front-panel / board geometry for Blackstart (genctl).
Coordinates: mm, KiCad convention (x right, y DOWN), origin = top-left corner
of the display cover glass, viewed FROM THE FRONT. KiCad F side = toward the
display/front panel; B side = rear (wiring side).
Source: Riverdi DR_RVT121HVLNWCA0-B Rev 1.1 (2025-02-03)."""

# --- display (Riverdi RVT121HVLNWCA0-B) ---
GLASS_W, GLASS_H = 276.56, 179.46          # CG/TFT outline, tol +-0.3 typ
AA_W, AA_H = 261.12, 163.20                # TFT active area
AA_LEFT, AA_TOP = 7.32, 8.03               # derived: 276.56-261.12-8.12 ; given 8.03
AA_RIGHT_BORDER, AA_BOTTOM_BORDER = 8.12, 8.23
VA_W, VA_H = 261.92, 163.30                # cover-glass viewing (unprinted) area
VA_LEFT, VA_TOP = 276.56 - 261.92 - 7.72, 7.63
MODULE_DEPTH_MAX = 12.68                   # incl. TFT source-PCB band on rear
# rear features expressed in FRONT-view coords (rear view is mirrored in x)
SRC_PCB_BAND = (276.56 - 20.95 - 235.0, GLASS_H - 29.52, 276.56 - 20.95, GLASS_H)  # x0,y0,x1,y1 (+-1)
LVDS_ZIF_PIN1 = (118.38, GLASS_H - 14.57)  # 40p 0.5mm ZIF, down-contact; +-0.5
TOUCH_TAIL_X = (276.56 - 59.53, 276.56 - 32.03)  # stiffener region, +-1, exits bottom edge (VERIFY vs STEP)
BACKLIGHT_EXIT = (5.0, 3.0)                 # cable exits top-left (front view), 200+-5 mm, BHSR-02VS-1

# --- buttons CTS 228EMVxxx (body 6.8 wide x 7.2 tall, 5.5 high, plunger ~3.8, travel 0.7+-0.2, 200+-50 gf) ---
BTN_BODY_W, BTN_BODY_H, BTN_HEIGHT = 6.8, 7.2, 5.5
BTN_N = 6
BTN_PITCH = AA_W / BTN_N                    # 43.52: one key per 1/6 of active area (soft-key labels)
# PANEL V2 (2026-10-24): wide caps spanning the TFT active width edge to edge, 6 above + 6 below
WINDOW_GAP = 0.5                            # glass edge -> window wall, per side (glass tol +-0.3)
CAP_GAP = 0.5                               # gap between adjacent caps (only what the slot/seal needs)
CAP_W = BTN_PITCH - CAP_GAP                 # 43.02 (outer caps flush with AA edges: row = 261.12 exactly)
CAP_H = 12.0                                # finger/glove height
CAP_SLOT_CLR = 0.25                         # cap -> panel slot wall, per side
WEB = 2.5                                   # aluminium web between display window and key slot
CAP_PROUD = 0.5                             # cap face stands 0.5 proud of panel face
CAP_TOP_Y0 = -(WINDOW_GAP + WEB + CAP_SLOT_CLR + CAP_H)       # -15.25
BTN_Y_TOP = CAP_TOP_Y0 + CAP_H / 2                            # -9.25
BTN_Y_BOT = GLASS_H + WINDOW_GAP + WEB + CAP_SLOT_CLR + CAP_H / 2   # 188.71
BTN_X = [AA_LEFT + (i + 0.5) * BTN_PITCH for i in range(BTN_N)]
GUIDE_DX = 17.0                             # guide stems at cap centre +-17 (span 34 of 43.02)
GUIDE_D, GUIDE_BORE = 3.0, 3.15

def caps():
    """[(ref, x0, y0, x1, y1)] cap faces, front view."""
    out = []
    for ref, x, y in buttons():
        out.append((ref, x - CAP_W / 2, y - CAP_H / 2, x + CAP_W / 2, y + CAP_H / 2))
    return out

def buttons():
    """[(ref, x, y)] SW9..SW14 top row L->R, SW15..SW20 bottom row L->R (switch = cap centre)."""
    out = [(f"SW{9+i}", x, BTN_Y_TOP) for i, x in enumerate(BTN_X)]
    out += [(f"SW{15+i}", x, BTN_Y_BOT) for i, x in enumerate(BTN_X)]
    return out

# key-row slots in the panel (one long slot per row; caps separated by CAP_GAP)
SLOT_TOP = (AA_LEFT - CAP_SLOT_CLR, CAP_TOP_Y0 - CAP_SLOT_CLR, AA_LEFT + AA_W + CAP_SLOT_CLR, CAP_TOP_Y0 + CAP_H + CAP_SLOT_CLR)
SLOT_BOT = (AA_LEFT - CAP_SLOT_CLR, BTN_Y_BOT - CAP_H / 2 - CAP_SLOT_CLR, AA_LEFT + AA_W + CAP_SLOT_CLR, BTN_Y_BOT + CAP_H / 2 + CAP_SLOT_CLR)

# --- front panel (CNC 6061-T6, 4.0 plate field, 12.5 deep rim round the display window) ---
PANEL_T = 4.0
LEDGE_Z = 9.5                               # panel face -> ledge face (8.51+-0.5 CTP+TFT + 1.0 bond line)
LEDGE_W = 4.0                               # ledge overlap on TFT rear border (top/left/right; bottom = corners only)
RIM_DEPTH = 12.5                            # ledge 3.0 thick
PANEL_BORDER_LR = 12.0
PANEL_MARGIN_TB = 8.0                       # slot edge -> panel edge
WINDOW = (-WINDOW_GAP, -WINDOW_GAP, GLASS_W + WINDOW_GAP, GLASS_H + WINDOW_GAP)
PANEL = (-PANEL_BORDER_LR, SLOT_TOP[1] - PANEL_MARGIN_TB, GLASS_W + PANEL_BORDER_LR, SLOT_BOT[3] + PANEL_MARGIN_TB)
PANEL_CORNER_R = 3.0
# M4 panel-to-housing screws (blind PEM studs / tapped from rear, no through-holes in the face)
PANEL_SCREWS = [(x, y) for x in (PANEL[0] + 6, GLASS_W / 2, PANEL[2] - 6) for y in (PANEL[1] + 5, PANEL[3] - 5)] + \
               [(PANEL[0] + 6, GLASS_H / 2), (PANEL[2] - 6, GLASS_H / 2)]

# --- stack (Z = mm behind panel face) ---
Z_BOARD_FRONT = 16.0                        # PCB F side; switch plunger top = 16.0 - 5.5 = 10.5

# --- PCB outline (behind display) ---
BOARD_W, BOARD_H = 284.0, 210.0             # V2: 198 -> 210 (key rows moved out ~5 mm each)
BOARD_X0 = (GLASS_W - BOARD_W) / 2          # -3.72
BOARD_Y0 = (BTN_Y_TOP + BTN_Y_BOT) / 2 - BOARD_H / 2   # centred on key rows: -15.27
BOARD = (BOARD_X0, BOARD_Y0, BOARD_X0 + BOARD_W, BOARD_Y0 + BOARD_H)
BOARD_CORNER_R = 2.0

# M3 standoff holes in the key rows outside the caps' switch/guide area
MOUNT_HOLES = [("H1", 2.0, BTN_Y_TOP), ("H2", GLASS_W - 2.0, BTN_Y_TOP),
               ("H3", 2.0, BTN_Y_BOT), ("H4", GLASS_W - 2.0, BTN_Y_BOT)]
