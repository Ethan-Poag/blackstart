"""Lumped nodal thermal model for enclosure v3 (phase 4). Every conductance is ESTIMATED unless noted; see HEAT_PATH.md.
Nodes: S=CM5 SoC, G=display/cover glass, B=metal bezel, I=interior air+PCB, F=rear Al fin plate (D options only).
Front air at Ta, cabinet air behind the panel at Tc = Ta + DTC."""
import numpy as np, json, itertools, os
A_GLASS = 0.27656 * 0.17946          # m2, MEASURED from geometry (glass 276.56 x 179.46)
A_FRONT = 0.329 * 0.261              # m2, bezel outline (model)
A_RING = A_FRONT - A_GLASS
H_FRONT = 9.0                        # W/m2K natural conv + radiation, vertical, ESTIMATED
BL_W = 9.22                          # W backlight at 100 %, MEASURED DS_RVT121HVLNWCA0-B Rev1.1 p.6 (8.28-9.54)
LOGIC_W = 3.3 * 0.210 + 3.3 * 0.100  # TFT logic 210 mA + CTP 100 mA @3.3 V, MEASURED same datasheet -> 1.02 W
LIGHT_OUT = 0.05                     # fraction of backlight leaving as light, ESTIMATED (LED ~35 % radiant x LCD ~5-8 % transmission)
DTC = 5.0                            # cabinet air above front ambient, ESTIMATED
def misc(bl): return 0.14 + 0.5 + 0.10 * BL_W * bl   # DSI83 0.14 W (MEASURED ICC 77 mA@1.8 V, sn65dsi83 ds) + other 0.5 (EST) + LED driver loss 10 % (EST)

OPTS = {
 # name: G_GB, G_BTa, R_chain(S->sink), sink, G_IF, G_ITc, G_FTc, ring, G_BF
 "none": dict(gb=2.0, bta=H_FRONT * A_RING, rc=5.80, sink="B", gf=0, gtc=0.47, ftc=0, ring=False, bf=0),
 "A":    dict(gb=2.0, bta=H_FRONT * A_RING, rc=4.41, sink="B", gf=0, gtc=0.47, ftc=0, ring=False, bf=0),
 "B":    dict(gb=2.0, bta=H_FRONT * A_RING + 0.56, rc=4.41, sink="B", gf=0, gtc=0.47, ftc=0, ring=False, bf=0),
 "D (rear fin plate + PA12 ring, recommended)": dict(gb=0.1, bta=0, rc=3.30, sink="F", gf=0.25, gtc=0.25, ftc=0.85, ring=True, bf=0),
 "E = D + display-rear Al spreader strapped to a bigger fin plate": dict(gb=0.1, bta=0, rc=3.30, sink="F", gf=0.25, gtc=0.25, ftc=1.2, ring=True, bf=0, gfp=0.55),
 "E' = D' + display-rear spreader (keeps boss)": dict(gb=0.1, bta=0, rc=4.41, sink="B", gf=0.25, gtc=0.25, ftc=1.2, ring=True, bf=2.0, gfp=0.55),
 "D' (keeps CM5->bezel boss, PA12 ring, bezel->fin plate bars)": dict(gb=0.1, bta=0, rc=4.41, sink="B", gf=0.25, gtc=0.25, ftc=0.85, ring=True, bf=2.0),
}
G_GTA = H_FRONT * A_GLASS            # glass front to air
G_GI = 0.69                          # display rear -> PCB/interior, air gap + radiation, ESTIMATED (value kept from pre-flush 3.27 mm gap; flush gap 11.44 mm, conservative)
G_BI = 0.20                          # bezel inner faces -> interior air, ESTIMATED
R_RING_COND = 0.001 / (0.026 * A_RING) + 0.003 / (0.22 * A_RING)   # 1 mm air break + 3 mm PA12
R_RING_SURF = 1 / (H_FRONT * A_RING)

def solve(o, P, bl, Ta=40.0, sun=0.0, a_glass=0.9, a_face=0.9):
    Tc = Ta + DTC
    n = ["S", "G", "B", "I", "F"]; ix = {k: i for i, k in enumerate(n)}
    M = np.zeros((5, 5)); q = np.zeros(5)
    def link(a, b, g):
        if g <= 0: return
        i, j = ix[a], ix[b]; M[i, i] += g; M[j, j] += g; M[i, j] -= g; M[j, i] -= g
    def amb(a, g, T):
        if g <= 0: return
        M[ix[a], ix[a]] += g; q[ix[a]] += g * T
    link("S", o["sink"], 1 / o["rc"]); q[ix["S"]] += P
    Qd = bl * BL_W * (1 - LIGHT_OUT) + LOGIC_W
    q[ix["G"]] += Qd + sun * a_glass * A_GLASS
    q[ix["I"]] += misc(bl)
    amb("G", G_GTA, Ta); link("G", "B", o["gb"]); link("G", "I", G_GI); link("B", "I", G_BI)
    if o["ring"] and o.get("grg", 0) > 0:
        # phase 6 flush glass: ring is a real node coupled to the glass edge (silicone bead + PA12 sleeve)
        g1, g2 = 1 / R_RING_COND, 1 / R_RING_SURF; qs = sun * a_face * A_RING
        n.append("R"); ix["R"] = 5
        M2 = np.zeros((6, 6)); M2[:5, :5] = M; q2 = np.zeros(6); q2[:5] = q; M, q = M2, q2
        link("B", "R", g1); amb("R", g2, Ta); q[5] += qs; link("G", "R", o["grg"])
    elif o["ring"]:
        # ring: sun absorbed on ring surface; bezel->ring->air series, with solar source at the ring surface node (solved analytically)
        g1, g2 = 1 / R_RING_COND, 1 / R_RING_SURF
        qs = sun * a_face * A_RING
        geq = g1 * g2 / (g1 + g2); amb("B", geq, Ta + qs / g2 * 0 + qs / g2)  # approx: sun lifts the ring's effective ambient
    else:
        amb("B", o["bta"], Ta); q[ix["B"]] += sun * a_face * A_RING
    amb("I", o["gtc"], Tc); link("I", "F", o["gf"]); amb("F", o["ftc"], Tc); link("B", "F", o["bf"]); link("G", "F", o.get("gfp", 0))
    if o["ftc"] == 0: M[ix["F"], ix["F"]] += 1; q[ix["F"]] += Tc
    T = dict(zip(n, np.linalg.solve(M, q)))
    if "R" in T:
        T["ring"] = T["R"]; touch = max(T["G"], T["R"])
    elif o["ring"]:
        g1, g2 = 1 / R_RING_COND, 1 / R_RING_SURF; qs = sun * a_face * A_RING
        T["ring"] = (g1 * T["B"] + g2 * Ta + qs) / (g1 + g2)
        touch = max(T["G"], T["ring"])
    else:
        touch = max(T["G"], T["B"])
    T["touch"] = touch
    T["throttle_Ta"] = 80 - (T["S"] - Ta)
    return T

if __name__ == "__main__":
    rows = []
    for name, o in OPTS.items():
        for P, bl in [(4.0, 1.0), (4.0, 0.7), (4.0, 0.4), (2.5, 0.7), (8.5, 1.0)]:
            T = solve(o, P, bl); rows.append((name, P, bl, "no sun", T))
        T = solve(o, 8.5, 1.0, sun=500, a_face=0.5 if o["ring"] else 0.9); rows.append((name, 8.5, 1.0, "sun 500 W/m2", T))
    out = []
    for name, P, bl, sun, T in rows:
        r = dict(option=name, cm5_W=P, backlight=bl, case=sun, glass=round(T["G"], 1), bezel_metal=round(T["B"], 1),
                 ring=round(T.get("ring", float("nan")), 1), touch_max=round(T["touch"], 1), SoC=round(T["S"], 1), throttle_Ta=round(T["throttle_Ta"], 1))
        out.append(r); print(name[:6], P, bl, sun, r['glass'], r['bezel_metal'], r['ring'], r['SoC'], r['throttle_Ta'])
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "thermal_results.json"), "w"), indent=1)


# =====================================================================================================================
# PHASE 23 (Ethan, Oct 25): PA12 front ring REMOVED. The black-anodised 6061 bezel face is the exposed front (touch surface).
# Current design: V6 flat 4.75 mm fin plate + ATS-EXL1 strip + TWO 40 mm fans push-pull in series, flush glass, bare bezel.
# Nodes: S SoC, H heat bar, G display/glass, B bezel (bare face to front air), I interior air, F fin plate.
# Fan conductances are ESTIMATED (phase 9 values, reproduced to within 1 F). Everything else ESTIMATED as in phases 4-9.
# Results are MODELLED (lumped steady state, ~+-5 F touch, +-15 F throttle ambient).
R_JC_PAD = 2.2          # SoC junction->case 2.0 + pad 0.2 (phase 4 D chain, ESTIMATED)
R_H_F = 1.1             # heat bar -> pillar -> fin plate (0.8 + joint 0.3, ESTIMATED)
# AS IN THE CAD: the heat bar tab is screwed (2x A2 M4) onto the bezel heat boss through a 0.5 mm pad (heat_pad part).
# Bar tab 0.8 + pad on boss 0.6 + boss 0.65 + spreading in the field 0.7 = 2.75 K/W (ESTIMATED; phase-1 table values).
# Earlier phases (D/V1/V6) assumed this boss carried no heat; with a bare bezel that assumption matters, so both are run.
R_H_B = {"as CAD (bar screwed to bezel boss, pad)": 2.75,
         "fix: G10 spacers + nylon M4 at the boss (no pad)": 50.0,   # 2x G10 1.5 mm washers ~52 K/W || nylon screws (ESTIMATED)
         "old assumption (boss carries no heat)": 1e9}
G_GB_BARE = 0.1 + 0.3   # VHB tape to ledge 0.1 + glass edge -> PA12 sleeve/silicone bead -> metal window 0.3 (ESTIMATED; was glass->ring)
G_BTA_BARE = H_FRONT * A_RING   # bare black-anodised face (emissivity ~0.85-0.9), h 9 W/m2K, ESTIMATED
FANS_P23 = {"both fans": dict(gtc=2.2, gi=1.5, ftc=0.8), "one fan failed": dict(gtc=1.3, gi=1.2, ftc=0.65),
            "both fans failed": dict(gtc=0.2, gi=0.69, ftc=0.45)}

def solve_p23(fan, rhb, P=4.0, bl=0.325, Ta=40.0, dtc=0.0, sun=0.0, a_face=0.9):
    Tc = Ta + dtc; n = ["S", "H", "G", "B", "I", "F"]; ix = {k: i for i, k in enumerate(n)}
    M = np.zeros((6, 6)); q = np.zeros(6)
    def link(a, b, g):
        i, j = ix[a], ix[b]; M[i, i] += g; M[j, j] += g; M[i, j] -= g; M[j, i] -= g
    def amb(a, g, T): M[ix[a], ix[a]] += g; q[ix[a]] += g * T
    q[ix["S"]] += P; q[ix["G"]] += bl * BL_W * (1 - LIGHT_OUT) + LOGIC_W + sun * 0.9 * A_GLASS; q[ix["I"]] += misc(bl)
    q[ix["B"]] += sun * a_face * A_RING
    link("S", "H", 1 / R_JC_PAD); link("H", "F", 1 / R_H_F); link("H", "B", 1 / rhb)
    amb("G", G_GTA, Ta); link("G", "B", G_GB_BARE); link("G", "I", fan["gi"]); link("B", "I", G_BI)
    amb("B", G_BTA_BARE, Ta); amb("I", fan["gtc"], Tc); link("I", "F", 0.25); amb("F", fan["ftc"], Tc)
    T = dict(zip(n, np.linalg.solve(M, q))); T["throttle_Ta"] = 80 - (T["S"] - Ta); return T

def run_p23():
    F = lambda c: round(c * 9 / 5 + 32)
    FC = lambda c: f"{F(c)} F ({c:.1f} C)"
    out = {"note": "PHASE 23 MODELLED; fan conductances ESTIMATED; Ta 104 F (40 C); CM5 4 W; idle cases = 90 % idle + 10 % full (average backlight); "
                   "alarm = continuous 100 %; cabinet air = ambient (ASSUMPTION, plus cab-9F column)", "cases": {}}
    for hb_name, rhb in R_H_B.items():
        for fn, fan in FANS_P23.items():
            for dtc, cn in ((0.0, "cab=amb"), (-5.0, "cab-9F")):
                r = {}
                for lab, bl in (("idle10", 0.19), ("idle25", 0.325), ("idle40", 0.46), ("alarm100", 1.0)):
                    T = solve_p23(fan, rhb, 4.0, bl, dtc=dtc); r[lab] = {"bezel_face": FC(T["B"]), "glass": FC(T["G"]), "SoC": FC(T["S"])}
                T25 = solve_p23(fan, rhb, 4.0, 0.325, dtc=dtc); r["throttle_ambient_4W_idle25"] = FC(40 + T25["throttle_Ta"] - 40 + 0) if False else FC(T25["throttle_Ta"])
                r["throttle_ambient_8p5W_idle25"] = FC(solve_p23(fan, rhb, 8.5, 0.325, dtc=dtc)["throttle_Ta"])
                out["cases"].setdefault(hb_name, {}).setdefault(fn, {})[cn] = r
    return out

if __name__ == "__main__":
    res = run_p23()
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "thermal_bare_bezel_p23.json"), "w"), indent=1)
    for h, d in res["cases"].items():
        for fn, c in d.items():
            r = c["cab=amb"]
            print(h[:12], "|", fn, "| bezel", [r[k]["bezel_face"] for k in ("idle10", "idle25", "idle40", "alarm100")], "| glass", [r[k]["glass"].split(" ")[0] for k in ("idle10", "idle25", "idle40", "alarm100")], "| thr", r["throttle_ambient_4W_idle25"], r["throttle_ambient_8p5W_idle25"], "| cab-9F bezel", [c["cab-9F"][k]["bezel_face"].split(" ")[0] for k in ("idle10", "idle25", "idle40", "alarm100")])
