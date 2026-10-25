"""Blattkontrast eines Surface-Volume-Renders (Methode rodriguescarson/eligible-scroll-atlas
scripts/analysis/profile.py, Commit 0c0566c): pro 64-px-Kachel (>= 80 % gültig) das mittlere Tiefenprofil;
Kontrast = (max - min) / mittel, Median über die Kacheln; peak_within3 = Anteil der Kacheln, deren hellste
Schicht höchstens 3 Schichten von der Mitte liegt. Schwellen je Scan-Protokoll in config.yaml (sheet_check)."""
import numpy as np


def measure(v):
    valid = v.max(0) > 0          # v bleibt uint8: Mittelwerte rechnen in float64, keine Kopie des ganzen Renders
    T = 64; c = v.shape[0] // 2; peaks, contr = [], []
    for i in range(valid.shape[0] // T):
        for j in range(valid.shape[1] // T):
            if valid[i*T:(i+1)*T, j*T:(j+1)*T].mean() < 0.8: continue
            p = v[:, i*T:(i+1)*T, j*T:(j+1)*T].reshape(v.shape[0], -1).mean(1, dtype=np.float64)
            peaks.append(int(p.argmax())); contr.append(float((p.max() - p.min()) / (p.mean() + 1e-6)))
    if not peaks: return {"tiles": 0}
    peaks = np.array(peaks)
    prof = np.array([float(v[i][valid].mean()) for i in range(v.shape[0])])
    return {"shape": list(v.shape), "tiles": len(peaks), "contrast_median": float(np.median(contr)),
            "contrast_p25": float(np.percentile(contr, 25)), "contrast_p75": float(np.percentile(contr, 75)),
            "peak_within3": float((abs(peaks - c) <= 3).mean()),
            "peak_edge": float(((peaks <= 1) | (peaks >= v.shape[0] - 2)).mean()),
            "whole_contrast": float((prof.max() - prof.min()) / max(prof.max(), 1e-6))}


def passes(m, threshold):
    """threshold: {"contrast_median": …, "peak_within3": …} des passenden Scan-Protokolls."""
    return m.get("tiles", 0) > 0 and m["contrast_median"] >= threshold["contrast_median"] \
        and m["peak_within3"] >= threshold["peak_within3"]
