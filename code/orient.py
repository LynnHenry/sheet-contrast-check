"""Geometrische Richtungsregel (NOTES.md, 25.10.2026): Wächst der Schichtindex eines Renders zur Rollenmitte hin?

usage: orient.py --render R.zarr --mesh M.tifxyz --volume URL [--umbilicus U.json] [--render-scale 1] [--n 120] [--out o.json]

1. d = empirische Richtung wachsender Schichtindizes: Render-Tiefenprofil gegen Volumen-Stichproben entlang ±n.
2. c(z) = Umbilicus (interpoliert) oder Schwerpunkt der Papyrusmaske auf Stufe 3.
3. s = Anteil der Stichproben mit d·(c − p)_xy > 0.
"""
import argparse, json
import numpy as np, tifffile, zarr
from scipy import ndimage


def load_mesh(path):
    xyz = np.stack([tifffile.imread(f"{path}/{c}.tif").astype(np.float64) for c in "xyz"], -1)
    meta = json.load(open(f"{path}/meta.json"))
    return xyz, float(meta["scale"][0])


def bilinear(grid, gy, gx):
    y0, x0 = int(np.floor(gy)), int(np.floor(gx)); fy, fx = gy - y0, gx - x0
    q = grid[y0:y0 + 2, x0:x0 + 2]
    if q.shape[:2] != (2, 2) or (q <= -1).any():
        return None
    return (q[0, 0] * (1 - fy) * (1 - fx) + q[0, 1] * (1 - fy) * fx + q[1, 0] * fy * (1 - fx) + q[1, 1] * fy * fx)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", required=True); ap.add_argument("--mesh", required=True)
    ap.add_argument("--volume", required=True); ap.add_argument("--umbilicus")
    ap.add_argument("--render-scale", type=float, default=1.0); ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--slice-step", type=float, default=1.0, help="Schichtabstand in Volumen-Voxeln")
    ap.add_argument("--out")
    a = ap.parse_args()
    rng = np.random.default_rng(42)
    g = zarr.open(a.render, mode="r"); R = g["0"] if "0" in g else g
    L = R.shape[0]; c0 = (L - 1) / 2
    mesh, ms = load_mesh(a.mesh)
    root = zarr.open(a.volume, mode="r"); V = root["0"]
    # gültige Pixel aus der mittleren Schicht (verkleinert gesucht)
    mid = np.asarray(R[L // 2, ::8, ::8]); ys, xs = np.nonzero(mid > 0)
    corr_p, corr_m, pts, dirs = [], [], [], []
    tries = 0
    while len(pts) < a.n and tries < a.n * 20:
        tries += 1
        k = rng.integers(len(ys)); py, px = ys[k] * 8, xs[k] * 8
        gy, gx = py * ms / a.render_scale, px * ms / a.render_scale
        p = bilinear(mesh, gy, gx); pr = bilinear(mesh, gy + 1, gx); pc = bilinear(mesh, gy, gx + 1)
        if p is None or pr is None or pc is None:
            continue
        n = np.cross(pc - p, pr - p); nn = np.linalg.norm(n)
        if nn == 0:
            continue
        n /= nn
        prof = np.asarray(R[:, py, px]).astype(np.float64)
        if prof.std() == 0:
            continue
        t = (np.arange(L) - c0) * a.slice_step
        res = {}
        for sgn in (1, -1):
            q = p[None, :] + sgn * t[:, None] * n[None, :]          # (L, 3) in xyz
            zi, yi, xi = (np.round(q[:, 2]).astype(int), np.round(q[:, 1]).astype(int), np.round(q[:, 0]).astype(int))
            if zi.min() < 0 or yi.min() < 0 or xi.min() < 0 or zi.max() >= V.shape[0] or yi.max() >= V.shape[1] or xi.max() >= V.shape[2]:
                res = None; break
            z0, z1, y0, y1, x0, x1 = zi.min(), zi.max() + 1, yi.min(), yi.max() + 1, xi.min(), xi.max() + 1
            blk = np.asarray(V[z0:z1, y0:y1, x0:x1]).astype(np.float64)
            s = blk[zi - z0, yi - y0, xi - x0]
            res[sgn] = np.corrcoef(prof, s)[0, 1] if s.std() > 0 else np.nan
        if res is None or np.isnan(res[1]) or np.isnan(res[-1]):
            continue
        corr_p.append(res[1]); corr_m.append(res[-1]); pts.append(p); dirs.append(n)
    corr_p, corr_m = np.array(corr_p), np.array(corr_m)
    sign = 1 if np.nanmean(corr_p) > np.nanmean(corr_m) else -1
    d = np.array(dirs) * sign; P = np.array(pts)
    # Rollenmitte
    if a.umbilicus:
        cp = json.load(open(a.umbilicus))["control_points"]
        cp = sorted(cp, key=lambda q: q["z"]); zs = np.array([q["z"] for q in cp], float)
        cx = np.interp(P[:, 2], zs, [q["x"] for q in cp]); cy = np.interp(P[:, 2], zs, [q["y"] for q in cp])
        centre_src = "umbilicus"
    else:
        V3 = root["3"]; f = V.shape[1] / V3.shape[1]
        cx, cy = [], []
        for zz in P[:, 2]:
            sl = np.asarray(V3[int(zz / f)]) > 0
            sl = ndimage.binary_fill_holes(ndimage.binary_closing(sl, iterations=3))
            yy, xx = np.nonzero(sl); cy.append(yy.mean() * f); cx.append(xx.mean() * f)
        cx, cy = np.array(cx), np.array(cy); centre_src = "papyrus_centroid_L3"
    toc = np.stack([cx - P[:, 0], cy - P[:, 1]], 1)
    dot = (d[:, :2] * toc).sum(1)
    s = float((dot > 0).mean())
    out = {"render": a.render, "mesh": a.mesh, "n_samples": len(P), "corr_plus_n": float(np.nanmean(corr_p)),
           "corr_minus_n": float(np.nanmean(corr_m)), "layer_dir_sign_vs_mesh_normal": sign, "centre": centre_src,
           "s_fraction_index_grows_inward": s,
           "orientation": "innen_hoch" if s >= 0.8 else ("innen_niedrig" if s <= 0.2 else "unklar"),
           "median_radius_vox": float(np.median(np.linalg.norm(toc, axis=1)))}
    print(json.dumps(out, indent=1))
    if a.out:
        json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
