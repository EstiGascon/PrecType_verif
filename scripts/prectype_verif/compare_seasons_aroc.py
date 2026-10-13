"""
Compare AROC by forecast day across two or more seasons/runs in a single plot.

Loads matched_pairs_*.parquet for each given run (any directory under
DATA_preVerif/, regardless of naming convention), computes AROC by
forecast-day group per precipitation type (same logic as 02_compute_scores.py),
and overlays all of them on one figure per type so season-over-season
evolution is directly visible. The last --series given is treated as the
"current" run and drawn solid/bold; earlier ones are drawn progressively
more faded/dashed.

Usage:
    python compare_seasons_aroc.py \\
        --series DATA_preVerif/2021_2022            "2021-2022" \\
        --series DATA_preVerif/2024_2025_49r1        "2024-2025" \\
        --series DATA_preVerif/2025_2026_enfo_0001   "2025-2026" \\
        --out verification_results/2025_2026_enfo_0001/aroc_by_day_season_comparison.png
"""

import sys
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from sklearn.metrics import roc_auc_score

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from config import DAY_GROUPS, PTYPE_CODES, SYNOP_CODES, COLORS, NICE_NAMES

PRECIP_TYPES = [t for t in PTYPE_CODES if SYNOP_CODES.get(t)]  # skip wetsnow

# Oldest → newest styling; the LAST series is always solid/full-opacity.
_STYLES = [
    {"linestyle": (0, (1, 1)), "marker": "v", "alpha": 0.3},
    {"linestyle": ":",  "marker": "^", "alpha": 0.42},
    {"linestyle": "--", "marker": "D", "alpha": 0.55},
    {"linestyle": "-.", "marker": "s", "alpha": 0.7},
    {"linestyle": "-",  "marker": "o", "alpha": 1.0},
]


def compute_aroc(obs: np.ndarray, prob: np.ndarray) -> float:
    if obs.sum() == 0 or obs.sum() == len(obs):
        return np.nan
    valid = np.isfinite(prob)
    if valid.sum() < 10:
        return np.nan
    try:
        return roc_auc_score(obs[valid], prob[valid])
    except Exception:
        return np.nan


def load_data(data_path: Path) -> pd.DataFrame:
    files = sorted(data_path.glob("matched_pairs_*.parquet"))
    if not files:
        raise FileNotFoundError(f"No parquet files found in {data_path}")
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def aroc_by_day(df: pd.DataFrame) -> dict:
    days = sorted(DAY_GROUPS.keys())
    out: dict = {}
    for ptype in PRECIP_TYPES:
        obs_col, prob_col = f"obs_{ptype}", f"prob_{ptype}"
        if obs_col not in df.columns or prob_col not in df.columns:
            continue
        for day in days:
            mask = df["forecast_step"].isin(DAY_GROUPS[day])
            sub = df[mask]
            out[(ptype, day)] = compute_aroc(
                sub[obs_col].values.astype(float), sub[prob_col].values.astype(float)
            )
    return out


def _style_for(index: int, n_series: int) -> tuple[str, str, float]:
    """Map a series position (0=oldest) to (linestyle, marker, alpha).

    Always picks styles from the END of _STYLES, so the last series (index
    n_series - 1) is guaranteed solid/full-opacity regardless of n_series.
    """
    styles = _STYLES[-n_series:] if n_series <= len(_STYLES) else (
        [_STYLES[0]] * (n_series - len(_STYLES)) + _STYLES
    )
    s = styles[index]
    return s["linestyle"], s["marker"], s["alpha"]


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
    args = parser.parse_args()

    series_aroc = []
    for data_dir, label in args.series:
        print(f"Loading {label} from {data_dir} ...")
        series_aroc.append((label, aroc_by_day(load_data(Path(data_dir)))))

    days = sorted(DAY_GROUPS.keys())
    n = len(series_aroc)
    fig, axes = plt.subplots(3, 2, figsize=(18, 12), constrained_layout=True)
    fig.suptitle(
        "AROC by Forecast Day — " + " vs ".join(label for label, _ in series_aroc),
        fontsize=20, fontweight="bold",
    )
    axes = axes.flatten()
    for ax, ptype in zip(axes, PRECIP_TYPES):
        for idx, (label, aroc) in enumerate(series_aroc):
            vals = [aroc.get((ptype, d), np.nan) for d in days]
            linestyle, marker, alpha = _style_for(idx, n)
            ax.plot(days, vals, marker=marker, markersize=8, linewidth=2.5,
                     linestyle=linestyle, color=COLORS[ptype], alpha=alpha, label=label)
        ax.axhline(0.5, color="k", linestyle="--", linewidth=1, alpha=0.4)
        ax.axhline(1.0, color="k", linestyle=":",  linewidth=1, alpha=0.4)
        ax.set_ylim(0.4, 1.05)
        ax.set_xticks(days)
        ax.set_xlabel("Forecast day", fontsize=15)
        ax.set_ylabel("AROC", fontsize=15)
        ax.set_title(NICE_NAMES[ptype], fontweight="bold", fontsize=17)
        ax.tick_params(axis="both", labelsize=13)
        ax.grid(True, alpha=0.3)
    for ax in axes[len(PRECIP_TYPES):]:
        ax.set_visible(False)

    # One shared legend for the whole figure (season labels are the same for
    # every subplot) instead of a per-subplot legend, which tended to overlap
    # the data lines.
    labels = [label for label, _ in series_aroc]
    handles = [
        Line2D([0], [0], color="0.25", linewidth=4,
               linestyle=_style_for(idx, n)[0], marker=_style_for(idx, n)[1],
               markersize=14, alpha=_style_for(idx, n)[2])
        for idx in range(n)
    ]
    fig.legend(handles, labels, loc="lower center", ncol=n, fontsize=22,
               markerscale=1.5, handlelength=4, bbox_to_anchor=(0.5, -0.08))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
