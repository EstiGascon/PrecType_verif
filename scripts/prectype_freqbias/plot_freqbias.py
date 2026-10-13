"""
Block B – Step 2: Plot frequency bias vs. precipitation rate threshold
======================================================================
Loads the CSV produced by compute_freqbias.py and generates one figure per
lead-time group showing FBI vs. threshold for all precipitation types.

The horizontal reference line at FBI = 1 marks perfect frequency calibration.
The threshold where each type's curve crosses FBI = 1 is the optimal threshold
to pass to prectype_verif's PRECIP_THRESHOLD dictionary.

Replaces:
  - Scripts_freqbias/old_code/BIAS_prates_thewholeperiod_48r1.r  (plotting)

Usage:
    python plot_freqbias.py [--input PATH] [--output DIR]
"""

import sys
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from config import (
    BIAS_THRESHOLDS, BIAS_GROUPS, COLORS, NICE_NAMES,
    PTYPE_CODES, SYNOP_CODES,
    SEASON as _CFG_SEASON, EXPVER as _CFG_EXPVER, STREAM as _CFG_STREAM,
)
import config as _cfg

ACTIVE_TYPES = [t for t in PTYPE_CODES if SYNOP_CODES.get(t)]

LEAD_LABELS = {
    "day1": "Lead time 0–24 h (day 1)",
    "day2": "Lead time 24–48 h (day 2)",
    "day5": "Lead time 96–120 h (day 5)",
}


def load_results(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Frequency bias results not found: {csv_path}\n"
            "Run compute_freqbias.py first."
        )
    return pd.read_csv(csv_path)


def plot_group(df: pd.DataFrame, grp: str, out_dir: Path, ymax: float | None = None) -> None:
    """One figure per lead-time group: FBI vs threshold for all types.

    ymax : if given, use this fixed upper y-axis limit instead of one derived
           from this dataframe alone (useful for side-by-side comparisons).
    """
    sub = df[df["lead_time_group"] == grp]
    if sub.empty:
        return

    fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)

    x = BIAS_THRESHOLDS
    for ptype in ACTIVE_TYPES:
        row = sub[sub["type"] == ptype].sort_values("threshold_mmh")
        if row.empty:
            continue
        fbi_vals = row["fbi"].values
        ax.plot(x, fbi_vals, marker="o", linewidth=2.5,
                color=COLORS[ptype], label=NICE_NAMES[ptype])

        # Mark the threshold closest to FBI = 1 (optimal)
        diff = np.abs(fbi_vals - 1.0)
        if np.isfinite(diff).any():
            best_idx = int(np.nanargmin(diff))
            ax.scatter(x[best_idx], fbi_vals[best_idx],
                       s=120, color=COLORS[ptype], zorder=5,
                       edgecolors="black", linewidths=1.5)

    ax.axhline(1.0, color="black", linestyle="--", linewidth=2,
               label="FBI = 1 (unbiased)")
    ax.set_xlabel("Precipitation rate threshold (mm h$^{-1}$)", fontsize=12)
    ax.set_ylabel("Frequency Bias Index (FBI)", fontsize=12)
    ax.set_title(LEAD_LABELS.get(grp, grp), fontsize=13, fontweight="bold")
    ax.set_xlim(min(x) * 0.9, max(x) * 1.05)
    if ymax is None:
        col_max = sub["fbi"].replace([np.inf, -np.inf], np.nan).max()
        ymax = max(2.5, col_max * 1.1) if np.isfinite(col_max) else 2.5
    ax.set_ylim(0, ymax)
    ax.xaxis.set_minor_locator(MultipleLocator(0.01))
    ax.legend(fontsize=10, loc="upper right")
    ax.grid(True, alpha=0.35)

    fig.savefig(out_dir / f"freqbias_{grp}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: freqbias_{grp}.png")


def plot_combined(df: pd.DataFrame, out_dir: Path, ymax: float | None = None) -> None:
    """3-panel figure with all lead-time groups side by side.

    ymax : if given, use this fixed upper y-axis limit for every panel.
    """
    groups = list(BIAS_GROUPS.keys())
    fig, axes = plt.subplots(1, len(groups), figsize=(6 * len(groups), 6),
                             constrained_layout=True)
    fig.suptitle("Frequency Bias vs. Precipitation Rate Threshold",
                 fontsize=14, fontweight="bold")

    for ax, grp in zip(axes, groups):
        sub = df[df["lead_time_group"] == grp]
        for ptype in ACTIVE_TYPES:
            row = sub[sub["type"] == ptype].sort_values("threshold_mmh")
            if row.empty:
                continue
            fbi_vals = row["fbi"].values
            ax.plot(BIAS_THRESHOLDS, fbi_vals, marker="o", linewidth=2,
                    color=COLORS[ptype], label=NICE_NAMES[ptype])
        ax.axhline(1.0, color="black", linestyle="--", linewidth=2)
        ax.set_xlabel("Threshold (mm h$^{-1}$)", fontsize=11)
        ax.set_ylabel("FBI" if ax == axes[0] else "", fontsize=11)
        ax.set_title(LEAD_LABELS.get(grp, grp), fontsize=11, fontweight="bold")
        if ymax is None:
            col_max = sub["fbi"].replace([np.inf, -np.inf], np.nan).max()
            panel_ymax = max(2.5, col_max * 1.1) if np.isfinite(col_max) else 2.5
        else:
            panel_ymax = ymax
        ax.set_ylim(0, panel_ymax)
        ax.grid(True, alpha=0.35)
        if ax == axes[-1]:
            ax.legend(fontsize=9, loc="upper right")

    fig.savefig(out_dir / "freqbias_combined.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  Saved: freqbias_combined.png")


def print_optimal_thresholds(df: pd.DataFrame) -> None:
    """Print the threshold that minimises |FBI - 1| per type and lead-time group."""
    print("\n" + "=" * 55)
    print("Optimal threshold (FBI closest to 1) per type")
    print("=" * 55)
    print(f"{'Type':<20}", end="")
    for grp in BIAS_GROUPS:
        print(f"  {grp:>8}", end="")
    print()
    print("-" * 55)

    for ptype in ACTIVE_TYPES:
        print(f"{NICE_NAMES[ptype]:<20}", end="")
        for grp in BIAS_GROUPS:
            sub = df[(df["type"] == ptype) & (df["lead_time_group"] == grp)]
            if sub.empty:
                print(f"  {'N/A':>8}", end="")
                continue
            sub = sub.sort_values("threshold_mmh")
            fbi_vals = sub["fbi"].values
            diff = np.abs(fbi_vals - 1.0)
            if np.isfinite(diff).any():
                best_thr = sub["threshold_mmh"].values[int(np.nanargmin(diff))]
                best_fbi = fbi_vals[int(np.nanargmin(diff))]
                print(f"  {best_thr:.2f}({best_fbi:.2f})", end="")
            else:
                print(f"  {'N/A':>8}", end="")
        print()
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Plot frequency bias results.")
    parser.add_argument("--season",  default=_CFG_SEASON,
                        help="Season string, e.g. 2024_2025  (overrides config.py)")
    parser.add_argument("--expver",  default=_CFG_EXPVER,
                        help="MARS expver, e.g. 0001  (overrides config.py)")
    parser.add_argument("--stream",  default=_CFG_STREAM,
                        help="MARS stream, e.g. enfo  (overrides config.py)")
    parser.add_argument("--input",  type=Path, default=None,
                        help="CSV from compute_freqbias.py (auto-derived if omitted)")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output directory for plots (auto-derived if omitted)")
    parser.add_argument("--ymax", type=float, default=None,
                        help="Fixed upper y-axis limit for all FBI panels "
                             "(useful for side-by-side comparisons between runs)")
    args = parser.parse_args()

    run_tag = f"{args.season}_{args.stream}_{args.expver}"
    _cfg.RUN_TAG       = run_tag
    _cfg.PATH_FREQBIAS = _cfg._BASE / "VERIF_ptype_all" / "DATA_freqbias" / run_tag
    _cfg.PATH_RESULTS  = Path("/home/moeg/PrecType_verif/verification_results") / run_tag

    csv_in  = args.input  if args.input  else _cfg.PATH_FREQBIAS / "freqbias_results.csv"
    out_dir = args.output if args.output else _cfg.PATH_RESULTS  / "freqbias"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 55)
    print("Precip Type Freq-Bias – Step 2: Plot frequency bias")
    print("=" * 55)
    print(f"Run tag : {run_tag}")
    print(f"Input   : {csv_in}")
    print(f"Output  : {out_dir}\n")

    df = load_results(csv_in)
    print(f"Loaded {len(df)} rows covering {df['type'].nunique()} types, "
          f"{df['threshold_mmh'].nunique()} thresholds, "
          f"{df['lead_time_group'].nunique()} lead-time groups.\n")

    for grp in BIAS_GROUPS:
        plot_group(df, grp, out_dir, ymax=args.ymax)

    plot_combined(df, out_dir, ymax=args.ymax)
    print_optimal_thresholds(df)
    print(f"All plots saved to {out_dir}")


if __name__ == "__main__":
    main()
