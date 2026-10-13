"""
Plot reliability diagrams for ALL precipitation types on a single axes, for
one run, so relative calibration across types is directly comparable.
Reliability is computed over ALL forecast steps combined.

Usage:
    python plot_reliability_all_types.py \\
        --data-dir DATA_preVerif/2025_2026_enfo_0001 --label "2025-2026" \\
        --out verification_results/2025_2026_enfo_0001/reliability_all_types.png
"""

import argparse
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from compare_seasons_aroc import load_data, PRECIP_TYPES
from compare_seasons_reliability import reliability_overall
from config import COLORS, NICE_NAMES


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    print(f"Loading {args.label} from {args.data_dir} ...")
    rel = reliability_overall(load_data(args.data_dir))

    fig, ax = plt.subplots(figsize=(10, 10), constrained_layout=True)
    fig.suptitle(f"Reliability — all types — {args.label}",
                 fontsize=20, fontweight="bold")

    ax.plot([0, 100], [0, 100], "k--", linewidth=1.5, alpha=0.5, label="Perfect")
    for ptype in PRECIP_TYPES:
        if ptype not in rel:
            continue
        mean_p, obs_f = rel[ptype]
        valid = np.isfinite(mean_p) & np.isfinite(obs_f)
        ax.plot(mean_p[valid], obs_f[valid], marker="o", markersize=8,
                 linewidth=2.5, color=COLORS[ptype], label=NICE_NAMES[ptype])

    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.set_xlabel("Forecast probability (%)", fontsize=15)
    ax.set_ylabel("Observed frequency (%)", fontsize=15)
    ax.tick_params(axis="both", labelsize=13)
    ax.legend(fontsize=14, loc="upper left")
    ax.grid(True, alpha=0.3)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
