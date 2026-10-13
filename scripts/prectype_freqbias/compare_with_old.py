"""
Compare new freqbias_results.csv with old R-script .gpt-based results.

Old pipeline (R script):
    FBI_old = sum(round(p_i * N / 100)) / (N * sum(obs_i))
            ≈ mean_forecast_probability / (100 * obs_frequency)
    where p_i = ensemble probability (0-100%) per station,
          N   = 51 members,
          obs = 0/1.
    ENS  files: /ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_bias/DATA_verif/
                2023_48r1_esuite/ENS_Europe/ENS{thr}_Europe/Loc_{type}_{date}_{step}.gpt
    SYNOP files: .../SYN_Europe/SYN{thr}_Europe/SYNOP_{type}_{date}_{step}.gpt

New pipeline (this work):
    FBI_new = (H + FA) / (H + M)
    where forecast = 1 if any member forecasts ptype AND prate >= threshold.
    Results: freqbias_results.csv
"""

import sys
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, timedelta

# ── Paths ──────────────────────────────────────────────────────────────────────
OLD_BASE   = Path("/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_bias/DATA_verif/2023_48r1_esuite")
NEW_CSV    = Path("/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/DATA_freqbias/2023_48r1esuite_enfo_0001/freqbias_results.csv")
OUT_DIR    = Path("/home/moeg/PrecType_verif/verification_results/2023_48r1esuite_enfo_0001/freqbias")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Constants ─────────────────────────────────────────────────────────────────
N_MEMBERS = 51      # old pipeline always used 51
THRESHOLDS = [0.02, 0.05, 0.07, 0.10, 0.12]
THR_CODES  = {0.02: "002", 0.05: "005", 0.07: "007", 0.10: "01", 0.12: "012"}
TYPES      = ["rain", "snow", "freezrain", "freezdrizzle", "icepellets", "sleet"]

# Step patterns per group
GROUPS = {
    "day1": list(range(  0, 24, 3)),
    "day2": list(range( 24, 48, 3)),
    "day5": list(range( 96, 120, 3)),
}

COLORS = {
    "rain":         "#00CC00",
    "snow":         "#0000FF",
    "sleet":        "#00CCCC",
    "freezrain":    "#FF0000",
    "freezdrizzle": "#FF1493",
    "icepellets":   "#FF9900",
}
NICE = {
    "rain": "Rain", "snow": "Snow", "sleet": "Sleet",
    "freezrain": "Frz Rain", "freezdrizzle": "Frz Drizzle", "icepellets": "Ice Pellets",
}

# Forecast dates (Feb 16 – Apr 15 2023)
fdates = []
d = datetime(2023, 2, 16)
while d <= datetime(2023, 4, 15):
    fdates.append(d.strftime("%Y%m%d"))
    d += timedelta(days=1)


# ── Read one .gpt file → column 6 values ──────────────────────────────────────
def read_gpt(path: Path) -> np.ndarray:
    vals = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 6:
                    vals.append(float(parts[5]))
    except Exception:
        pass
    return np.array(vals, dtype=float)


# ── Compute old FBI (R-script method) ─────────────────────────────────────────
def compute_old_fbi(thr: float, ptype: str, group: str) -> float:
    thr_code = THR_CODES[thr]
    ens_dir  = OLD_BASE / "ENS_Europe" / f"ENS{thr_code}_Europe"
    syn_dir  = OLD_BASE / "SYN_Europe" / f"SYN{thr_code}_Europe"
    steps    = GROUPS[group]

    all_p, all_obs = [], []
    for fdate in fdates:
        for step in steps:
            ens_f  = ens_dir  / f"Loc_{ptype}_{fdate}_{step}.gpt"
            syn_f  = syn_dir  / f"SYNOP_{ptype}_{fdate}_{step}.gpt"
            if not ens_f.exists() or not syn_f.exists():
                continue
            p   = read_gpt(ens_f)
            obs = read_gpt(syn_f)
            if len(p) == 0 or len(obs) == 0 or len(p) != len(obs):
                continue
            # R-script filter: remove p > 100
            mask = p <= 100
            all_p.append(p[mask])
            all_obs.append(obs[mask])

    if not all_p:
        return np.nan
    all_p   = np.concatenate(all_p)
    all_obs = np.concatenate(all_obs)

    # Expand probabilities → binary votes (N_MEMBERS expansion)
    n_yes  = np.round(all_p * N_MEMBERS / 100.0).astype(int)
    H_plus_FA = n_yes.sum()
    H_plus_M  = N_MEMBERS * all_obs.sum()

    if H_plus_M == 0:
        return np.nan
    return float(H_plus_FA / H_plus_M)


# ── Main ──────────────────────────────────────────────────────────────────────
print("Computing old FBI from .gpt files …")
old_rows = []
for ptype in TYPES:
    for thr in THRESHOLDS:
        for grp in GROUPS:
            fbi = compute_old_fbi(thr, ptype, grp)
            old_rows.append({"type": ptype, "threshold_mmh": thr, "lead_time_group": grp, "fbi_old": fbi})
            print(f"  {ptype:12s}  thr={thr:.2f}  {grp}  FBI_old={fbi:.3f}")

df_old = pd.DataFrame(old_rows)

print("\nLoading new FBI from CSV …")
df_new = pd.read_csv(NEW_CSV)
df_new = df_new.rename(columns={"fbi": "fbi_new"})

df = df_old.merge(df_new[["type","threshold_mmh","lead_time_group","fbi_new"]],
                  on=["type","threshold_mmh","lead_time_group"], how="left")

# ── Save comparison table ──────────────────────────────────────────────────────
table_path = OUT_DIR / "comparison_old_vs_new.csv"
df.to_csv(table_path, index=False, float_format="%.4f")
print(f"\nComparison table saved → {table_path}")

# ── Print summary ──────────────────────────────────────────────────────────────
print("\n=== day1 comparison ===")
d1 = df[df["lead_time_group"] == "day1"][["type","threshold_mmh","fbi_old","fbi_new"]]
print(d1.to_string(index=False))

# ── Plot: old vs new for each lead-time group ──────────────────────────────────
print("\nGenerating comparison plots …")
x = np.array(THRESHOLDS)

for grp in GROUPS:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)
    fig.suptitle(
        f"Frequency Bias – {grp.upper()}  |  48r1 esuite 2023-02-16→2023-04-15",
        fontsize=12, fontweight="bold"
    )

    for ax, (col, label, note) in zip(axes, [
        ("fbi_old", "Old (R script: mean prob / obs freq)", ""),
        ("fbi_new", "New (Python: any-member binary)",      ""),
    ]):
        sub = df[df["lead_time_group"] == grp]
        for ptype in TYPES:
            row = sub[sub["type"] == ptype].sort_values("threshold_mmh")
            vals = row[col].values
            ax.plot(x, vals, "o-", color=COLORS[ptype], lw=2, label=NICE[ptype])

        ax.axhline(1.0, color="black", lw=1.5, ls="--", label="FBI = 1 (unbiased)")
        ax.set_xlabel("Precipitation rate threshold (mm/h)")
        ax.set_ylabel("Frequency Bias Index")
        ax.set_title(f"{label}{note}")
        ax.set_xticks(x)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_png = OUT_DIR / f"compare_old_vs_new_{grp}.png"
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"  Saved → {out_png}")

print("\nDone.")
