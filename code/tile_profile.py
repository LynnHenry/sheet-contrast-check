"""Blattkontrast nach rodriguescarson/eligible-scroll-atlas scripts/analysis/profile.py (0c0566c):
pro 64-px-Kachel (>= 80 % gültig) das mittlere Tiefenprofil; Kontrast = (max - min) / mittel,
Peak-Schicht relativ zur Mitte. Zusätzlich das Ganzflächen-Profil wie screen.py:surface_check.

usage: tile_profile.py <out.json> name=render.zarr ...
"""
import json, sys
from pathlib import Path
import numpy as np, zarr
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sheet_contrast import measure  # noqa: E402  (gemeinsame Implementierung mit screen.py)

if __name__ == "__main__":
    out = {}
    for arg in sys.argv[2:]:
        n, z = arg.split("=", 1); g = zarr.open(z, mode="r"); a = g["0"] if "0" in g else g
        out[n] = measure(np.asarray(a[:])); print(n, json.dumps(out[n]), flush=True)
    json.dump(out, open(sys.argv[1], "w"), indent=1)
