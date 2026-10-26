"""Phase 15 CAD test-finger access check (MODELLED; not a substitute for the NRTL probe test).
Probe: STRAIGHT RIGID finger, dia 12.0 mm, max penetration 80 mm (stop face dia 50 x 20 mm cannot pass any window, all < 50 mm
in one dimension). Dimensions from vendor pages describing IEC 61032 Fig. 2 test probe B (SECONDARY, standard not read):
  bndtestequipment.com/test-finger-probe/iec61032-iec60529-ip2x-test-probe-b-test-finger/  (12 mm, 80 mm, stop face 50 x 20)
  merhein.com/products/iec61032-figure-2-test-probe-b  (12 mm, 80 mm, 50 mm stop face, joints 90 deg)
  ormity.com/product-page/jointed-finger-probe-iec-61032  (12 x 80 mm, 50 mm stop face, 10 N)
Joint section lengths and tip radius NOT verified -> articulation NOT modelled; tip modelled FLAT (reaches deeper than the
real rounded tip = conservative for depth). The jointed finger can reach further sideways than any straight line: lateral
'articulation margin' reported = min straight-line distance minus nothing is credited; see doc.
Method: all rigid CAD parts tessellated; for each opening the finger axis is swept on a 1 mm grid of entry points over the
opening and 9 directions (normal + 30/45 deg tilted toward +-x, +-y); the finger advances until any of 25 rays on its
cross-section hits a solid. Distance = straight 3D distance from the finger body (segment, r 6) to hazardous-live outer-layer
copper (hv_copper.json, read-only pcbnew export, pad half-diagonal subtracted). Grommet membranes are NOT rigid -> ignored.
PASS criterion used here (ASSUMED, Compliance to confirm): finger does not touch live copper and >= 8.0 mm (reinforced
clearance) from it; touching a J28/J29/J30 plug body is reported separately (the plug's own finger safety is unverified)."""
import json, math, os, sys, numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import enclosure_v3 as E
R, LMAX, GRID = 6.0, 80.0, 1.0
RIGID_SKIP = {"customer_panel", "grommets"}
def mesh(wp):
    v, t = wp.val().tessellate(0.2, 0.5)
    V = np.array([[p.x, -p.y, -p.z] for p in v]); return V, np.array(t)
def scene(names, parts):
    Vs, Fs, ids, off = [], [], [], 0
    for i, n in enumerate(names):
        V, F = mesh(parts[n][0]); Vs.append(V); Fs.append(F + off); ids += [i] * len(F); off += len(V)
    m = trimesh.Trimesh(np.vstack(Vs), np.vstack(Fs), process=False)
    return m, np.array(ids)
def dirs():
    out = [("normal", np.array([0, 0, -1.0]))]
    for a in (30, 45):
        s, c = math.sin(math.radians(a)), math.cos(math.radians(a))
        for lab, (dx, dy) in {"+x": (1, 0), "-x": (-1, 0), "+y": (1, 1), "-y": (-1, -1)}.items():
            v = np.array([dx * s if "x" in lab else 0, (1 if lab == "+y" else -1) * s if "y" in lab else 0, -c]); out.append((f"{a}deg{lab}", v))
    return out
def disk(d):
    a = np.cross(d, [1, 0, 0] if abs(d[0]) < 0.9 else [0, 1, 0]); a /= np.linalg.norm(a); b = np.cross(d, a)
    pts = [np.zeros(3)] + [r * (math.cos(t) * a + math.sin(t) * b) for r, n in ((R, 16), (R / 2, 8)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]
    return np.array(pts)
def seg_dist(P, A, B):
    AB = B - A; t = np.clip(((P - A) @ AB) / max(AB @ AB, 1e-9), 0, 1); return np.linalg.norm(P - (A + np.outer(t, AB)), axis=1)

def run(case, parts, live, openings):
    names = [n for n in parts if n not in RIGID_SKIP and not (case == "bare" and n in ("window_covers", "cover_gaskets"))]
    m, ids = scene(names, parts); rp = names.index("rear_parts")
    plugs = {r: E.FP[r]["bbox"] for r in ("J28", "J29", "J30")}
    res = {}
    for on, (shape, zs) in openings.items():
        best = {"min_dist_to_live_copper_mm": 1e9}
        if shape[0] == "rect":
            x0, y0, x1, y1 = shape[1:]; xs = np.arange(x0 + R, x1 - R + 1e-6, GRID) if x1 - x0 >= 2 * R else np.array([]); ys = np.arange(y0 + R, y1 - R + 1e-6, GRID) if y1 - y0 >= 2 * R else np.array([])
            ent = [(x, y) for x in xs for y in ys]
        else:
            cx, cy, D = shape[1:]; ent = [(cx, cy)] if D >= 2 * R else []
        if not ent:
            res[on] = {"entry": "NO ENTRY: opening smaller than the 12 mm finger", "result": "PASS"}; continue
        touched_plug, n_try = set(), 0
        for lab, d in dirs():
            dk = disk(d)
            for (x, y) in ent:
                p0 = np.array([x, y, zs]) - d * 40.0             # start 40 mm outside along the axis, crossing the outer plane at (x, y)
                O = p0 + dk; D = np.tile(d, (len(O), 1))
                loc, ri, tri = m.ray.intersects_location(O, D, multiple_hits=False)
                s = np.full(len(O), 1e9)
                for L, r_, t_ in zip(loc, ri, tri):
                    s[r_] = min(s[r_], np.linalg.norm(L - O[r_]))
                k = int(np.argmin(s)); smin = s[k]
                pen = smin - 40.0
                if pen <= 0.05: continue                           # finger blocked at/outside the outer face
                pen = min(pen, LMAX); n_try += 1
                A = np.array([x, y, zs]); tip = A + d * pen
                dd = seg_dist(live[:, :3], A, tip) - R - live[:, 3]
                j = int(np.argmin(dd))
                hit_part = names[ids[tri[list(ri).index(k)]]] if k in list(ri) and pen < LMAX else None
                if hit_part == "rear_parts":
                    for r, (bx0, by0, bx1, by1) in plugs.items():
                        if bx0 - 1 <= tip[0] <= bx1 + 1 and by0 - 1 <= tip[1] <= by1 + 1: touched_plug.add(r)
                if dd[j] < best["min_dist_to_live_copper_mm"]:
                    best = {"min_dist_to_live_copper_mm": round(float(dd[j]), 2), "entry_xy": [round(x, 2), round(y, 2)], "direction": lab,
                            "penetration_mm": round(float(pen), 2), "tip_xyz": [round(float(v), 2) for v in tip], "stopped_by": hit_part,
                            "nearest_live": {"xy": live_meta[j][:2], "layer": live_meta[j][2], "ref": live_meta[j][4], "net": live_meta[j][5]}}
        if n_try == 0:
            res[on] = {"entry": "finger fits the outline but is blocked at the outer face", "result": "PASS"}; continue
        best["finger_positions_entering"] = n_try
        best["touches_plug_body"] = sorted(touched_plug)
        best["result"] = "FAIL (touches live copper)" if best["min_dist_to_live_copper_mm"] <= 0 else ("PASS" if best["min_dist_to_live_copper_mm"] >= 8.0 else "MARGINAL (< 8.0 mm)")
        res[on] = best
    return res

if __name__ == "__main__":
    parts = E.build()
    LJ = json.load(open(os.path.join(HERE, "finger", "hv_copper.json")))["points"]
    live_meta = LJ
    live = np.array([[p[0], p[1], E.Z_PCB if p[2] == "F" else E.ZR, p[3]] for p in LJ])
    z_out = E.SHELL_DEPTH; z_cov = E.SHELL_DEPTH + E.COV_GSK + E.COV_T
    bare = {f"{n}_window": (("rect",) + tuple(w), z_out) for n, (w, c, g) in E.COVERS.items()}
    for n, (cx, cy, w, h, zt) in E.REAR_PORTS.items(): bare[f"{n}_port_tunnel"] = (("rect", cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), z_out)
    for n, (x, y) in E.FANS.items(): bare[f"fan_{n}_through_filter_cover_slots(3mm)"] = (("rect", x - 17, y - 1.5, x + 17, y + 1.5), z_out + 30)
    cov = {}
    for n, (w, c, g) in E.COVERS.items():
        cov[f"{n}_cover_grommet"] = ((("hole", g[1], g[2], g[3]) if g[0] == "hole" else ("rect",) + tuple(g[1:])), z_cov)
    for n, (cx, cy, w, h, zt) in E.REAR_PORTS.items(): cov[f"{n}_port_tunnel"] = (("rect", cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), z_out)
    out = {"probe": "straight rigid finger d12 x 80 mm, flat tip (MODELLED; IEC 61032 probe B dims SECONDARY via vendor pages; articulation not modelled)",
           "live_set": "outer-layer copper of all '/AC metering' nets + GND_AC + +3V3_AC + U22/U23 CT (ASSUMED conservative), %d points" % len(live),
           "pass_rule": "no contact and >= 8.0 mm to live copper (ASSUMED; Compliance to set)",
           "bare_no_covers": run("bare", parts, live, bare), "covers_fitted": run("covered", parts, live, cov)}
    json.dump(out, open(os.path.join(HERE, "finger_check.json"), "w"), indent=1)
    for case in ("bare_no_covers", "covers_fitted"):
        print(case)
        for k, v in out[case].items(): print(" ", k, v.get("result"), v.get("min_dist_to_live_copper_mm"), v.get("direction"), v.get("touches_plug_body"), v.get("entry", ""))
