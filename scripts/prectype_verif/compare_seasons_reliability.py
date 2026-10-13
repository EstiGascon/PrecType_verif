"""
Compare reliability diagrams across two or more seasons/runs, one subplot per
precipitation type (same layout as compare_seasons_aroc.py). Reliability is
computed over ALL forecast steps combined (not split by forecast day), so
each season contributes a single curve per type.

Usage:
    python compare_seasons_reliability.py \\
        --series DATA_preVerif/2021_2022            "2021-2022" \\
        --series DATA_preVerif/2025_2026_enfo_0001   "2025-2026" \\
        --out verification_results/2025_2026_enfo_0001/reliability_season_comparison.png
"""

import argparse
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from compare_seasons_aroc import PRECIP_TYPES, load_data, _style_for
from config import COLORS, NICE_NAMES

PROB_BINS = np.arange(0, 101, 10)


def compute_reliability_bins(obs: np.ndarray, prob: np.ndarray):
    bin_edges   = PROB_BINS
    bin_centres = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    obs_freq    = np.full(len(bin_centres), np.nan)
    mean_prob   = np.full(len(bin_centres), np.nan)

    valid = np.isfinite(prob)
    p, o = prob[valid], obs[valid]
    for i, (lo, hi) in enumerate(zip(bin_edges[:-1], bin_edges[1:])):
        mask = (p >= lo) & (p < hi)
        if mask.sum() > 0:
            obs_freq[i]  = o[mask].mean() * 100
            mean_prob[i] = p[mask].mean()
    return mean_prob, obs_freq


def reliability_overall(df) -> dict:
    """Reliability curve per type, aggregated over all forecast steps."""
    out: dict = {}
    for ptype in PRECIP_TYPES:
        obs_col, prob_col = f"obs_{ptype}", f"prob_{ptype}"
        if obs_col not in df.columns or prob_col not in df.columns:
            continue
        out[ptype] = compute_reliability_bins(
            df[obs_col].values.astype(float), df[prob_col].values.astype(float)
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--series", nargs=2, action="append", metavar=("DIR", "LABEL"),
        required=True,
        help="Data directory + label for one run. Repeat in chronological "
             "order (oldest first); the last one is treated as 'current'.",
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--type", choices=PRECIP_TYPES,
                        help="If given, plot only this precip type on a single "
                             "axes instead of the full grid of all types.")
    args = parser.parse_args()

    series_rel = []
    for data_dir, label in args.series:
        print(f"Loading {label} from {data_dir} ...")
        series_rel.append((label, reliability_overall(load_data(Path(data_dir)))))

    n = len(series_rel)

    if args.type:
        ptype = args.type
        fig, ax = plt.subplots(figsize=(10, 10), constrained_layout=True)
        fig.suptitle(
            f"Reliability — {NICE_NAMES[ptype]} — " +
            " vs ".join(label for label, _ in series_rel),
            fontsize=18, fontweight="bold",
        )
        ax.plot([0, 100], [0, 100], "k--", linewidth=1.5, alpha=0.5)
        for idx, (label, rel) in enumerate(series_rel):
            if ptype not in rel:
                continue
            mean_p, obs_f = rel[ptype]
            valid = np.isfinite(mean_p) & np.isfinite(obs_f)
            linestyle, marker, alpha = _style_for(idx, n)
            ax.plot(mean_p[valid], obs_f[valid], marker=marker, markersize=12,
                     linewidth=3, linestyle=linestyle, color=COLORS[ptype], alpha=alpha)
        ax.set_xlim(0, 100); ax.set_ylim(0, 100)
        ax.set_xlabel("Forecast probability (%)", fontsize=16)
        ax.set_ylabel("Observed frequency (%)", fontsize=16)
        ax.tick_params(axis="both", labelsize=14)
        ax.grid(True, alpha=0.3)

        labels = ["Perfect"] + [label for label, _ in series_rel]
        handles = [Line2D([0, 1], [0, 1], color="k", linestyle="--", linewidth=1.5, alpha=0.5)] + [
            Line2D([0], [0], color="0.25", linewidth=4,
                   linestyle=_style_for(idx, n)[0], marker=_style_for(idx, n)[1],
                   markersize=14, alpha=_style_for(idx, n)[2])
            for idx in range(n)
        ]
        fig.legend(handles, labels, loc="lower center", ncol=len(labels), fontsize=18,
                   markerscale=1.3, handlelength=4, bbox_to_anchor=(0.5, -0.1))

        args.out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved {args.out}")
        return
    fig, axes = plt.subplots(3, 2, figsize=(18, 12), constrained_layout=True)
    fig.suptitle(
        "Reliability — " + " vs ".join(label for label, _ in series_rel),
        fontsize=20, fontweight="bold",
    )
    axes = axes.flatten()
    for ax, ptype in zip(axes, PRECIP_TYPES):
        ax.plot([0, 100], [0, 100], "k--", linewidth=1.5, alpha=0.5, label="Perfect")
        for idx, (label, rel) in enumerate(series_rel):
            if ptype not in rel:
                continue
            mean_p, obs_f = rel[ptype]
            valid = np.isfinite(mean_p) & np.isfinite(obs_f)
            linestyle, marker, alpha = _style_for(idx, n)
            ax.plot(mean_p[valid], obs_f[valid], marker=marker, markersize=8,
                     linewidth=2.5, linestyle=linestyle, color=COLORS[ptype],
                     alpha=alpha, label=label)
        ax.set_xlim(0, 100); ax.set_ylim(0, 100)
        ax.set_xlabel("Forecast probability (%)", fontsize=15)
        ax.set_ylabel("Observed frequency (%)", fontsize=15)
        ax.set_title(NICE_NAMES[ptype], fontweight="bold", fontsize=17)
        ax.tick_params(axis="both", labelsize=13)
        ax.legend(fontsize=13)
        ax.grid(True, alpha=0.3)
    for ax in axes[len(PRECIP_TYPES):]:
        ax.set_visible(False)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
