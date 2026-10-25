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
G_GI = 0.69                          # display rear -> PCB/interior, 3.27 mm air + radiation, ESTIMATED
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
    if o["ring"]:
        # ring: sun absorbed on ring surface; bezel->ring->air series, with solar source at the ring surface node (solved analytically)
        g1, g2 = 1 / R_RING_COND, 1 / R_RING_SURF
        qs = sun * a_face * A_RING
        geq = g1 * g2 / (g1 + g2); amb("B", geq, Ta + qs / g2 * 0 + qs / g2)  # approx: sun lifts the ring's effective ambient
    else:
        amb("B", o["bta"], Ta); q[ix["B"]] += sun * a_face * A_RING
    amb("I", o["gtc"], Tc); link("I", "F", o["gf"]); amb("F", o["ftc"], Tc); link("B", "F", o["bf"]); link("G", "F", o.get("gfp", 0))
    if o["ftc"] == 0: M[ix["F"], ix["F"]] += 1; q[ix["F"]] += Tc
    T = dict(zip(n, np.linalg.solve(M, q)))
    if o["ring"]:
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
