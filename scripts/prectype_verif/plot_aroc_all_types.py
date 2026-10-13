"""
Plot AROC by forecast day for ALL precipitation types on a single axes, for
one run, so relative skill across types is directly comparable.

Usage:
    python plot_aroc_all_types.py \\
        --data-dir DATA_preVerif/2025_2026_enfo_0001 --label "2025-2026" \\
        --out verification_results/2025_2026_enfo_0001/aroc_by_day_all_types.png
"""

import sys
import argparse
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from config import DAY_GROUPS, COLORS, NICE_NAMES
from compare_seasons_aroc import PRECIP_TYPES, load_data, aroc_by_day


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    print(f"Loading {args.label} from {args.data_dir} ...")
    aroc = aroc_by_day(load_data(args.data_dir))

    days = sorted(DAY_GROUPS.keys())
    fig, ax = plt.subplots(figsize=(12, 8), constrained_layout=True)
    fig.suptitle(f"AROC by Forecast Day — all types — {args.label}",
                 fontsize=20, fontweight="bold")

    for ptype in PRECIP_TYPES:
        vals = [aroc.get((ptype, d), np.nan) for d in days]
        if all(np.isnan(v) for v in vals):
            continue
        ax.plot(days, vals, marker="o", markersize=8, linewidth=2.5,
                 color=COLORS[ptype], label=NICE_NAMES[ptype])

    ax.axhline(0.5, color="k", linestyle="--", linewidth=1, alpha=0.4)
    ax.axhline(1.0, color="k", linestyle=":",  linewidth=1, alpha=0.4)
    ax.set_ylim(0.4, 1.05)
    ax.set_xticks(days)
    ax.set_xlabel("Forecast day", fontsize=15)
    ax.set_ylabel("AROC", fontsize=15)
    ax.tick_params(axis="both", labelsize=13)
    ax.legend(fontsize=14, loc="lower left")
    ax.grid(True, alpha=0.3)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
