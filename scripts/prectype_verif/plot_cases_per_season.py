"""
Plot the number of freezing rain, sleet, and/or ice pellet "cases" per winter
season. Supports two metrics: total observation counts, or distinct days with
at least one observed case.

Usage:
    python plot_cases_per_season.py \\
        --series DATA_preVerif/2020_2021          "2020-2021" \\
        --series DATA_preVerif/2021_2022          "2021-2022" \\
        --series DATA_preVerif/2023_2024          "2023-2024" \\
        --series DATA_preVerif/2024_2025_49r1     "2024-2025" \\
        --series DATA_preVerif/2025_2026_enfo_0001 "2025-2026" \\
        --types freezrain --metric days \\
        --out verification_results/2025_2026_enfo_0001/freezrain_days_per_season.png
"""

import argparse
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from compare_seasons_aroc import load_data
from config import COLORS, NICE_NAMES

DEFAULT_TYPES = ["freezrain", "sleet", "icepellets"]


def total_cases(df, ptype: str) -> int:
    obs_col = f"obs_{ptype}"
    if obs_col not in df.columns:
        return 0
    return int(df[obs_col].sum())


def case_days(df, ptype: str) -> int:
    obs_col = f"obs_{ptype}"
    if obs_col not in df.columns:
        return 0
    pos = df[df[obs_col] == 1]
    return pos["valid_date"].nunique()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--series", nargs=2, action="append", metavar=("DIR", "LABEL"),
        required=True, help="Data directory + label for one season. Repeat in "
                            "chronological order.",
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--types", default=",".join(DEFAULT_TYPES),
                        help="Comma-separated precip type codes to plot (default: "
                             + ",".join(DEFAULT_TYPES))
    parser.add_argument("--metric", choices=["total", "days"], default="total",
                        help="'total' = sum of observations; "
                             "'days' = distinct days with >=1 observed case")
    args = parser.parse_args()
    types = args.types.split(",")
    count_fn = case_days if args.metric == "days" else total_cases

    labels = [label for _, label in args.series]
    counts = {t: [] for t in types}
    for data_dir, label in args.series:
        print(f"Loading {label} from {data_dir} ...")
        df = load_data(Path(data_dir))
        for t in types:
            counts[t].append(count_fn(df, t))

    x = np.arange(len(labels))
    width = 0.8 / len(types)
    fig, ax = plt.subplots(figsize=(12, 7), constrained_layout=True)
    metric_label = "total cases" if args.metric == "total" else "days with >=1 case"
    fig.suptitle(
        " / ".join(NICE_NAMES[t] for t in types) + f" — {metric_label} per season",
        fontsize=18, fontweight="bold",
    )

    for i, t in enumerate(types):
        offset = (i - (len(types) - 1) / 2) * width
        bars = ax.bar(x + offset, counts[t], width, color=COLORS[t], label=NICE_NAMES[t])
        ax.bar_label(bars, fontsize=11)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=14)
    ylabel = "Total number of observed cases" if args.metric == "total" else "Number of days with >=1 observed case"
    ax.set_ylabel(ylabel, fontsize=15)
    ax.tick_params(axis="y", labelsize=13)
    ax.legend(fontsize=14)
    ax.grid(True, axis="y", alpha=0.3)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
