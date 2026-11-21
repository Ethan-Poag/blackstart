"""Phase 24 (Nov 21 2026, Enginerd/Ethan: keep CM5 touchscreen, design FANLESS). Reuses thermal_v3.solve_p23 unchanged.
Fanless = fan conductances of the phase-23 'both fans failed' case (sealed interior, natural convection only), then:
  - fins: rear fin plate to cabinet air G_FTc 0.45 (V6 flat plate, no fan) -> 0.85 (Design D 30 mm slats, phase 4) -> 1.2 (Design E bigger plate)
  - thermal break: heat bar to bezel boss 2.75 K/W (as CAD, pad) -> 50 K/W (G10 spacers + nylon M4)
  - CM5 power cap 4.0 W typ / 3.5 W cap (firmware: arm_freq cap + governor); 8.5 W stress shown for reference only
All conductances ESTIMATED (phase 4-23 values); results MODELLED, about +-5 F surfaces, +-15 F throttle ambient. No sun."""
import json, os
from thermal_v3 import solve_p23
F = lambda c: round(c * 9 / 5 + 32)
FINS = {"V6 flat plate (as CAD)": 0.45, "30 mm slats, D plate": 0.85, "bigger plate + slats (E)": 1.2}
BREAK = {"as CAD pad to boss": 2.75, "G10 + nylon thermal break": 50.0}
out = []
for fn, ftc in FINS.items():
    for bn, rhb in BREAK.items():
        fan = dict(gtc=0.2, gi=0.69, ftc=ftc)
        for P in (3.5, 4.0, 8.5):
            r = dict(fins=fn, brk=bn, cm5_W=P)
            for lab, bl in (("idle25", 0.325), ("alarm100", 1.0)):
                T = solve_p23(fan, rhb, P, bl)
                r[lab] = dict(bezel_F=F(T["B"]), glass_F=F(T["G"]), soc_F=F(T["S"]))
            r["throttle_ambient_F_idle25"] = F(solve_p23(fan, rhb, P, 0.325)["throttle_Ta"])
            out.append(r)
json.dump(dict(note=__doc__, ta_F=104, rows=out), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "thermal_fanless_p24.json"), "w"), indent=1)
print("fins | break | CM5 W | bezel idle/alarm F | glass idle/alarm F | SoC idle F | throttle ambient F")
for r in out:
    print(f"{r['fins']} | {r['brk']} | {r['cm5_W']} | {r['idle25']['bezel_F']}/{r['alarm100']['bezel_F']} | {r['idle25']['glass_F']}/{r['alarm100']['glass_F']} | {r['idle25']['soc_F']} | {r['throttle_ambient_F_idle25']}")
