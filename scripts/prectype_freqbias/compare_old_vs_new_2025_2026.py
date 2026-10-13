"""
Compare old-methodology FBI (freqbias_results_from_gpt_2025_2026.csv) against
the new eccodes-based pipeline (freqbias_results.csv), for the same dataset
(2025_2026_enfo_0080), at each type's single operational threshold
(config.PRECIP_THRESHOLD).

Produces a grouped bar chart (old vs new) per lead-time group.

Usage:
    python compare_old_vs_new_2025_2026.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from config import (
    PTYPE_CODES, SYNOP_CODES, PRECIP_THRESHOLD, BIAS_GROUPS,
    COLORS, NICE_NAMES, PATH_RESULTS,
)

ACTIVE_TYPES = [t for t in PTYPE_CODES if SYNOP_CODES.get(t)]

OLD_CSV = Path(__file__).resolve().parent / "freqbias_results_from_gpt_2025_2026.csv"
NEW_CSV = Path("/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/DATA_freqbias/2025_2026_enfo_0080/freqbias_results.csv")
OUT_DIR = PATH_RESULTS / "freqbias_from_gpt"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LEAD_LABELS = {
    "day1": "Lead time 0-24h (day 1)",
    "day2": "Lead time 24-48h (day 2)",
    "day5": "Lead time 96-120h (day 5)",
}


def main() -> None:
    df_old = pd.read_csv(OLD_CSV).rename(columns={"fbi": "fbi_old"})
    df_new = pd.read_csv(NEW_CSV).rename(columns={"fbi": "fbi_new"})

    rows = []
    for ptype in ACTIVE_TYPES:
        thr = PRECIP_THRESHOLD.get(ptype, 0.02)
        for grp in BIAS_GROUPS:
            old_row = df_old[(df_old["type"] == ptype) & (df_old["lead_time_group"] == grp)]
            new_row = df_new[(df_new["type"] == ptype) &
                              (df_new["lead_time_group"] == grp) &
                              (np.isclose(df_new["threshold_mmh"], thr))]
            fbi_old = float(old_row["fbi_old"].iloc[0]) if not old_row.empty else np.nan
            fbi_new = float(new_row["fbi_new"].iloc[0]) if not new_row.empty else np.nan
            rows.append({"type": ptype, "threshold_mmh": thr, "lead_time_group": grp,
                         "fbi_old": fbi_old, "fbi_new": fbi_new})

    df = pd.DataFrame(rows)
    table_path = OUT_DIR / "comparison_old_vs_new.csv"
    df.to_csv(table_path, index=False, float_format="%.4f")
    print(f"Comparison table saved -> {table_path}\n")
    print(df.to_string(index=False))

    # ── Grouped bar chart per lead-time group ────────────────────────────────
    for grp in BIAS_GROUPS:
        sub = df[df["lead_time_group"] == grp]
        fig, ax = plt.subplots(figsize=(9, 5.5), constrained_layout=True)

        x = np.arange(len(ACTIVE_TYPES))
        width = 0.35
        old_vals = [sub[sub["type"] == t]["fbi_old"].iloc[0] for t in ACTIVE_TYPES]
        new_vals = [sub[sub["type"] == t]["fbi_new"].iloc[0] for t in ACTIVE_TYPES]

        ax.bar(x - width / 2, old_vals, width, label="Old (Metview obsfilter + Python model)",
               color=[COLORS[t] for t in ACTIVE_TYPES], alpha=0.55, edgecolor="black")
        ax.bar(x + width / 2, new_vals, width, label="New (eccodes pipeline)",
               color=[COLORS[t] for t in ACTIVE_TYPES], alpha=1.0, edgecolor="black")

        ax.axhline(1.0, color="black", linestyle="--", linewidth=1.5, label="FBI = 1 (unbiased)")
        ax.set_xticks(x)
        ax.set_xticklabels([NICE_NAMES[t] for t in ACTIVE_TYPES], rotation=20, ha="right")
        ax.set_ylabel("Frequency Bias Index (FBI)")
        ax.set_title(f"Old vs New FBI (operational thresholds) - {LEAD_LABELS.get(grp, grp)}\n"
                     f"2025_2026_enfo_0080", fontsize=12, fontweight="bold")
        ax.legend(fontsize=9)
        ax.grid(True, axis="y", alpha=0.35)

        out_png = OUT_DIR / f"compare_old_vs_new_{grp}.png"
        fig.savefig(out_png, dpi=150)
        plt.close(fig)
        print(f"  Saved -> {out_png}")


if __name__ == "__main__":
    main()
