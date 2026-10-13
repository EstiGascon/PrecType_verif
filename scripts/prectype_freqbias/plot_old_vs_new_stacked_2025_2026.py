"""
Stacked panel comparison: old-code (Metview obsfilter + Python model reimpl.)
FBI-vs-threshold curves on top, new-pipeline (eccodes) curves below, for the
2025_2026_enfo_0080 dataset. Same y-axis scale across all 6 panels for a
fair visual comparison.

Usage:
    python plot_old_vs_new_stacked_2025_2026.py
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
    BIAS_THRESHOLDS, BIAS_GROUPS, COLORS, NICE_NAMES,
    PTYPE_CODES, SYNOP_CODES, PATH_RESULTS,
)

ACTIVE_TYPES = [t for t in PTYPE_CODES if SYNOP_CODES.get(t)]

OLD_CSV = Path(__file__).resolve().parent / "freqbias_results_from_gpt_2025_2026_5thresh.csv"
NEW_CSV = Path("/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/DATA_freqbias/2025_2026_enfo_0080/freqbias_results.csv")
OUT_DIR = PATH_RESULTS / "freqbias_from_gpt_5thresh"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LEAD_LABELS = {
    "day1": "Lead time 0-24h (day 1)",
    "day2": "Lead time 24-48h (day 2)",
    "day5": "Lead time 96-120h (day 5)",
}


def plot_row(ax_row, df: pd.DataFrame, row_label: str, ymax: float) -> None:
    x = BIAS_THRESHOLDS
    for ax, grp in zip(ax_row, BIAS_GROUPS):
        sub = df[df["lead_time_group"] == grp]
        for ptype in ACTIVE_TYPES:
            row = sub[sub["type"] == ptype].sort_values("threshold_mmh")
            if row.empty:
                continue
            fbi_vals = row["fbi"].values
            ax.plot(x, fbi_vals, marker="o", linewidth=2,
                    color=COLORS[ptype], label=NICE_NAMES[ptype])
        ax.axhline(1.0, color="black", linestyle="--", linewidth=1.5)
        ax.set_title(LEAD_LABELS.get(grp, grp), fontsize=11, fontweight="bold")
        ax.set_xlabel("Threshold (mm h$^{-1}$)", fontsize=10)
        ax.set_xticks(x)
        ax.set_ylim(0, ymax)
        ax.grid(True, alpha=0.35)

    ax_row[0].set_ylabel(f"{row_label}\nFBI", fontsize=11, fontweight="bold")
    ax_row[-1].legend(fontsize=8, loc="upper right")


def main() -> None:
    df_old = pd.read_csv(OLD_CSV)
    df_new = pd.read_csv(NEW_CSV)

    # Common y-axis scale across both rows for fair comparison
    col_max = max(
        df_old["fbi"].replace([np.inf, -np.inf], np.nan).max(),
        df_new["fbi"].replace([np.inf, -np.inf], np.nan).max(),
    )
    ymax = max(2.5, col_max * 1.1) if np.isfinite(col_max) else 2.5

    fig, axes = plt.subplots(2, len(BIAS_GROUPS), figsize=(6 * len(BIAS_GROUPS), 11),
                             constrained_layout=True)
    fig.suptitle("Frequency Bias vs. Precipitation Rate Threshold — Old vs New\n"
                 "2025_2026_enfo_0080", fontsize=14, fontweight="bold")

    plot_row(axes[0], df_old, "OLD CODE\n(Metview obs + Python model)", ymax)
    plot_row(axes[1], df_new, "NEW PIPELINE\n(eccodes)", ymax)

    out_png = OUT_DIR / "compare_old_vs_new_stacked.png"
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    print(f"Saved -> {out_png}")


if __name__ == "__main__":
    main()
