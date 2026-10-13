"""
Block A – Step 2: Compute all verification scores and plots
===========================================================
Loads matched-pairs Parquet files produced by 01_prepare_dataset.py and
computes the full set of probabilistic verification scores:

  1. AROC (Area under ROC curve)          – by forecast day and type
  2. Reliability diagram                  – calibration of probabilities
  3. Brier Score + Brier Skill Score      – overall probabilistic accuracy
  4. Contingency metrics (POD/FAR/CSI/ETS/FBI) – at multiple thresholds
  5. Sharpness                            – histogram of forecast probabilities
  6. Cost-loss value                      – economic value
  7. Confusion matrix                     – multi-category type assignment

Replaces:
  ROC_ptype_all.ipynb, Reliability_ptype_all.ipynb, OtherScores_ptype_all.ipynb
  and their *_compare2 / *_NOfreezdrizzle variants.

Usage:
    python 02_compute_scores.py [--season SEASON]
"""

import sys
import argparse
import glob
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from config import (
    SEASON as _CFG_SEASON, DAY_GROUPS, PTYPE_CODES, SYNOP_CODES,
    EXPVER as _CFG_EXPVER, STREAM as _CFG_STREAM,
    COLORS, NICE_NAMES,
)
import config as _cfg

PRECIP_TYPES = [t for t in PTYPE_CODES if SYNOP_CODES.get(t)]  # skip wetsnow
PROB_BINS    = np.arange(0, 101, 10)
THRESHOLDS   = [10, 20, 30, 40, 50, 60, 70, 80, 90]
CL_RATIOS    = np.linspace(0.01, 0.99, 50)


# ── Data loading ──────────────────────────────────────────────────────────────

def load_data(data_path: Path) -> pd.DataFrame:
    files = sorted(data_path.glob("matched_pairs_*.parquet"))
    if not files:
        raise FileNotFoundError(f"No parquet files found in {data_path}")
    print(f"  Loading {len(files)} files ...")
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    print(f"  Loaded {len(df):,} matched pairs\n")
    return df


def day_label(day: int) -> str:
    return f"Day {day}"


# ── Score functions ───────────────────────────────────────────────────────────

def compute_aroc(obs: np.ndarray, prob: np.ndarray) -> float:
    """Area under ROC curve. Returns NaN if class not represented."""
    if obs.sum() == 0 or obs.sum() == len(obs):
        return np.nan
    valid = np.isfinite(prob)
    if valid.sum() < 10:
        return np.nan
    try:
        return roc_auc_score(obs[valid], prob[valid])
    except Exception:
        return np.nan


def compute_brier(obs: np.ndarray, prob: np.ndarray) -> float:
    valid = np.isfinite(prob)
    if valid.sum() == 0:
        return np.nan
    return float(np.mean((prob[valid] / 100.0 - obs[valid]) ** 2))


def compute_bss(obs: np.ndarray, prob: np.ndarray) -> float:
    """Brier Skill Score vs. sample climatology."""
    bs      = compute_brier(obs, prob)
    clim    = obs.mean()
    bs_clim = clim * (1.0 - clim)
    if np.isnan(bs) or bs_clim == 0:
        return np.nan
    return 1.0 - bs / bs_clim


def compute_reliability_bins(
    obs: np.ndarray, prob: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute reliability diagram data.

    Returns bin_centres (%), mean_forecast_prob (%), observed_freq (%).
    """
    bin_edges   = PROB_BINS
    bin_centres = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    obs_freq    = np.full(len(bin_centres), np.nan)
    mean_prob   = np.full(len(bin_centres), np.nan)
    counts      = np.zeros(len(bin_centres))

    valid = np.isfinite(prob)
    p = prob[valid]
    o = obs[valid]

    for i, (lo, hi) in enumerate(zip(bin_edges[:-1], bin_edges[1:])):
        mask = (p >= lo) & (p < hi)
        if mask.sum() > 0:
            obs_freq[i]  = o[mask].mean() * 100
            mean_prob[i] = p[mask].mean()
            counts[i]    = mask.sum()

    return mean_prob, obs_freq, counts


def compute_contingency(
    obs: np.ndarray, prob: np.ndarray, threshold: float
) -> dict:
    fcst = (prob >= threshold).astype(int)
    H  = ((fcst == 1) & (obs == 1)).sum()
    FA = ((fcst == 1) & (obs == 0)).sum()
    M  = ((fcst == 0) & (obs == 1)).sum()
    CN = ((fcst == 0) & (obs == 0)).sum()
    n  = H + FA + M + CN

    pod = H / (H + M)          if (H + M)    > 0 else np.nan
    far = FA / (H + FA)        if (H + FA)   > 0 else np.nan
    csi = H / (H + FA + M)     if (H+FA+M)   > 0 else np.nan
    fbi = (H + FA) / (H + M)   if (H + M)    > 0 else np.nan
    hr  = (H + FA) * (H + M) / n if n > 0 else 0
    ets = (H - hr) / (H + FA + M - hr) if (H + FA + M - hr) > 0 else np.nan
    return {"pod": pod, "far": far, "csi": csi, "ets": ets, "fbi": fbi,
            "H": H, "FA": FA, "M": M, "CN": CN}


def compute_cost_loss_value(
    obs: np.ndarray, prob: np.ndarray, threshold: float, cl_ratio: float
) -> float:
    fcst = (prob >= threshold).astype(int)
    FA = ((fcst == 1) & (obs == 0)).sum()
    M  = ((fcst == 0) & (obs == 1)).sum()
    n  = len(obs)
    n_events = obs.sum()
    expense_fcst  = FA * cl_ratio + M
    expense_clim  = min(n_events, n * cl_ratio)
    return (expense_clim - expense_fcst) / n if n > 0 else np.nan


# ── Aggregate over day groups ─────────────────────────────────────────────────

def scores_by_day(df: pd.DataFrame) -> dict:
    """Compute all scores per (type, day_group)."""
    results = {
        "aroc":        {},
        "brier":       {},
        "bss":         {},
        "contingency": {},
        "reliability": {},
        "sharpness":   {},
        "cost_loss":   {},
    }

    days = sorted(DAY_GROUPS.keys())

    for ptype in PRECIP_TYPES:
        obs_col  = f"obs_{ptype}"
        prob_col = f"prob_{ptype}"
        if obs_col not in df.columns:
            continue

        for day in days:
            key  = (ptype, day)
            mask = df["forecast_step"].isin(DAY_GROUPS[day])
            sub  = df[mask]
            obs  = sub[obs_col].values.astype(float)
            prob = sub[prob_col].values.astype(float)

            results["aroc"][key]  = compute_aroc(obs, prob)
            results["brier"][key] = compute_brier(obs, prob)
            results["bss"][key]   = compute_bss(obs, prob)

            results["reliability"][key] = compute_reliability_bins(obs, prob)

            ct = {}
            for thr in THRESHOLDS:
                ct[thr] = compute_contingency(obs, prob, thr)
            results["contingency"][key] = ct

            valid = np.isfinite(prob)
            results["sharpness"][key] = prob[valid]

            cl_vals = {thr: [] for thr in [30, 50, 70]}
            for thr in [30, 50, 70]:
                cl_vals[thr] = [
                    compute_cost_loss_value(obs, prob, thr, cl) for cl in CL_RATIOS
                ]
            results["cost_loss"][key] = cl_vals

        # Climatological frequency (over whole dataset)
        results[f"clim_{ptype}"] = df[obs_col].mean()

    return results


# ── Plotting ──────────────────────────────────────────────────────────────────

def _setup_fig(ncols: int, nrows: int, title: str, figsize: tuple):
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, constrained_layout=True)
    fig.suptitle(title, fontsize=13, fontweight="bold")
    return fig, axes.flatten() if nrows * ncols > 1 else [axes]


def plot_aroc(results: dict, out: Path) -> None:
    days = sorted(DAY_GROUPS.keys())
    fig, axes = _setup_fig(3, 2, "AROC by Forecast Day", (16, 10))
    for ax, ptype in zip(axes, PRECIP_TYPES):
        vals = [results["aroc"].get((ptype, d), np.nan) for d in days]
        ax.plot(days, vals, marker="o", linewidth=2, color=COLORS[ptype])
        ax.axhline(0.5,  color="k", linestyle="--", linewidth=1, alpha=0.4)
        ax.axhline(1.0,  color="k", linestyle=":",  linewidth=1, alpha=0.4)
        ax.set_ylim(0.4, 1.05)
        ax.set_xticks(days)
        ax.set_xlabel("Forecast day")
        ax.set_ylabel("AROC")
        ax.set_title(NICE_NAMES[ptype], fontweight="bold")
        ax.grid(True, alpha=0.3)
    for ax in axes[len(PRECIP_TYPES):]:
        ax.set_visible(False)
    fig.savefig(out / "aroc_by_day.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_brier(results: dict, out: Path) -> None:
    days = sorted(DAY_GROUPS.keys())
    fig, axes = _setup_fig(3, 2, "Brier Score (solid) and Brier Skill Score (dashed)", (16, 10))
    for ax, ptype in zip(axes, PRECIP_TYPES):
        bs  = [results["brier"].get((ptype, d), np.nan) for d in days]
        bss = [results["bss"].get((ptype, d),   np.nan) for d in days]
        ax.plot(days, bs,  marker="o", linewidth=2, color=COLORS[ptype], label="BS")
        ax.plot(days, bss, marker="s", linewidth=2, color=COLORS[ptype],
                linestyle="--", label="BSS")
        ax.axhline(0, color="k", linestyle="--", linewidth=1, alpha=0.4)
        ax.set_xticks(days)
        ax.set_xlabel("Forecast day")
        ax.set_title(NICE_NAMES[ptype], fontweight="bold")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    for ax in axes[len(PRECIP_TYPES):]:
        ax.set_visible(False)
    fig.savefig(out / "brier_scores_by_day.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_reliability(results: dict, out: Path) -> None:
    days_to_plot = [1, 3, 5, 7]
    for ptype in PRECIP_TYPES:
        fig, axes = plt.subplots(2, 2, figsize=(10, 10), constrained_layout=True)
        fig.suptitle(f"Reliability – {NICE_NAMES[ptype]}", fontsize=13, fontweight="bold")
        for ax, day in zip(axes.flatten(), days_to_plot):
            key = (ptype, day)
            if key not in results["reliability"]:
                ax.set_visible(False)
                continue
            mean_p, obs_f, counts = results["reliability"][key]
            valid = np.isfinite(mean_p) & np.isfinite(obs_f)
            ax.plot([0, 100], [0, 100], "k--", linewidth=1, alpha=0.5, label="Perfect")
            ax.plot(mean_p[valid], obs_f[valid], marker="o", linewidth=2,
                    color=COLORS[ptype], label=f"Day {day}")
            clim = results.get(f"clim_{ptype}", 0)
            ax.axhline(clim * 100, color="gray", linestyle=":", linewidth=1,
                       label=f"Climatology ({clim*100:.1f}%)")
            ax.set_xlim(0, 100); ax.set_ylim(0, 100)
            ax.set_xlabel("Forecast probability (%)"); ax.set_ylabel("Observed frequency (%)")
            ax.set_title(f"Forecast day {day}", fontweight="bold")
            ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
        fig.savefig(out / f"reliability_{ptype}.png", dpi=150, bbox_inches="tight")
        plt.close(fig)


def plot_contingency(results: dict, out: Path) -> None:
    days_to_plot = [1, 3, 5, 7]
    fig, axes = _setup_fig(3, 2, "Contingency Metrics at 50 % Threshold", (16, 10))
    for ax, ptype in zip(axes, PRECIP_TYPES):
        for day in days_to_plot:
            key = (ptype, day)
            if key not in results["contingency"]:
                continue
            ct = results["contingency"][key]
            pods = [ct[t]["pod"] for t in THRESHOLDS]
            fars = [ct[t]["far"] for t in THRESHOLDS]
            csis = [ct[t]["csi"] for t in THRESHOLDS]
            ax.plot(THRESHOLDS, pods, marker="o", linewidth=1.5,
                    linestyle="-",  alpha=0.6 + day * 0.05, color="green",
                    label=f"POD d{day}" if ptype == PRECIP_TYPES[0] else "")
            ax.plot(THRESHOLDS, fars, marker="s", linewidth=1.5,
                    linestyle="--", alpha=0.6 + day * 0.05, color="red")
            ax.plot(THRESHOLDS, csis, marker="^", linewidth=1.5,
                    linestyle="-.", alpha=0.6 + day * 0.05, color="blue")
        ax.set_xlabel("Probability threshold (%)"); ax.set_ylabel("Score")
        ax.set_title(NICE_NAMES[ptype], fontweight="bold")
        ax.set_ylim(-0.05, 1.05); ax.grid(True, alpha=0.3)
        from matplotlib.lines import Line2D
        ax.legend(handles=[
            Line2D([0], [0], color="green", label="POD"),
            Line2D([0], [0], color="red",   linestyle="--", label="FAR"),
            Line2D([0], [0], color="blue",  linestyle="-.", label="CSI"),
        ], fontsize=9)
    for ax in axes[len(PRECIP_TYPES):]:
        ax.set_visible(False)
    fig.savefig(out / "contingency_metrics.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_sharpness(results: dict, out: Path) -> None:
    fig, axes = _setup_fig(3, 2, "Sharpness (Forecast Probability Histogram)", (16, 10))
    for ax, ptype in zip(axes, PRECIP_TYPES):
        probs_all = np.concatenate(
            [results["sharpness"].get((ptype, d), np.array([])) for d in DAY_GROUPS]
        )
        if len(probs_all) == 0:
            ax.set_visible(False); continue
        clim = results.get(f"clim_{ptype}", 0)
        ax.hist(probs_all, bins=50, color=COLORS[ptype], alpha=0.7,
                edgecolor="black", linewidth=0.4, density=True)
        ax.axvline(clim * 100, color="red", linestyle="--", linewidth=2,
                   label=f"Clim {clim*100:.1f}%")
        sharpness = float(np.var(probs_all / 100.0))
        ax.set_title(NICE_NAMES[ptype], fontweight="bold")
        ax.set_xlabel("Forecast probability (%)"); ax.set_ylabel("Density")
        ax.text(0.97, 0.97, f"Sharpness={sharpness:.4f}", transform=ax.transAxes,
                ha="right", va="top", fontsize=9,
                bbox=dict(boxstyle="round", fc="lightyellow", alpha=0.8))
        ax.legend(fontsize=9); ax.grid(True, alpha=0.3, axis="y")
    for ax in axes[len(PRECIP_TYPES):]:
        ax.set_visible(False)
    fig.savefig(out / "sharpness_analysis.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_cost_loss(results: dict, out: Path) -> None:
    fig, axes = _setup_fig(3, 2, "Cost-Loss Economic Value", (16, 10))
    for ax, ptype in zip(axes, PRECIP_TYPES):
        for day in [1, 3, 5, 7]:
            key = (ptype, day)
            if key not in results["cost_loss"]:
                continue
            for thr, ls in zip([30, 50, 70], ["-", "--", "-."]):
                vals = results["cost_loss"][key][thr]
                ax.plot(CL_RATIOS, vals, linewidth=1.5, linestyle=ls,
                        alpha=min(0.4 + day * 0.1, 1.0), label=f"{thr}% d{day}")
        ax.axhline(0, color="k", linestyle="--", linewidth=1, alpha=0.4)
        ax.set_xlabel("Cost/Loss ratio"); ax.set_ylabel("Forecast value")
        ax.set_title(NICE_NAMES[ptype], fontweight="bold")
        ax.set_xlim(0, 1); ax.grid(True, alpha=0.3)
    for ax in axes[len(PRECIP_TYPES):]:
        ax.set_visible(False)
    fig.savefig(out / "cost_loss_analysis.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_confusion(df: pd.DataFrame, out: Path) -> None:
    from sklearn.metrics import confusion_matrix
    import seaborn as sns

    prob_cols = [f"prob_{t}" for t in PRECIP_TYPES]
    obs_cols  = [f"obs_{t}"  for t in PRECIP_TYPES]

    tmp = df.copy()
    tmp["pred_type"] = tmp[prob_cols].idxmax(axis=1).str.replace("prob_", "")

    def get_obs_type(row):
        for t in PRECIP_TYPES:
            if row[f"obs_{t}"] == 1:
                return t
        return "none"

    tmp["obs_type"] = tmp.apply(get_obs_type, axis=1)
    events = tmp[tmp["obs_type"] != "none"]
    events = events[events[prob_cols].max(axis=1) > 20]

    if len(events) < 10:
        return

    cm = confusion_matrix(events["obs_type"], events["pred_type"], labels=PRECIP_TYPES)
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)
    labels_nice = [NICE_NAMES[t] for t in PRECIP_TYPES]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), constrained_layout=True)
    fig.suptitle("Confusion Matrix (precipitation events, max prob > 20%)",
                 fontsize=13, fontweight="bold")
    sns.heatmap(cm,      annot=True, fmt="d",    cmap="Blues",
                xticklabels=labels_nice, yticklabels=labels_nice, ax=ax1)
    sns.heatmap(cm_norm, annot=True, fmt=".2f",  cmap="RdYlGn",
                xticklabels=labels_nice, yticklabels=labels_nice, ax=ax2,
                vmin=0, vmax=1)
    for ax, ttl in zip([ax1, ax2], ["Counts", "Row-normalised"]):
        ax.set_xlabel("Predicted type"); ax.set_ylabel("Observed type")
        ax.set_title(ttl, fontweight="bold")
    fig.savefig(out / "confusion_matrix.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def save_summary(results: dict, out: Path) -> None:
    """Save tabular summary of key scores to CSV."""
    rows = []
    for ptype in PRECIP_TYPES:
        for day in sorted(DAY_GROUPS.keys()):
            key = (ptype, day)
            ct50 = results["contingency"].get(key, {}).get(50, {})
            rows.append({
                "type":  ptype,
                "day":   day,
                "aroc":  results["aroc"].get(key),
                "brier": results["brier"].get(key),
                "bss":   results["bss"].get(key),
                "pod":   ct50.get("pod"),
                "far":   ct50.get("far"),
                "csi":   ct50.get("csi"),
                "ets":   ct50.get("ets"),
                "fbi":   ct50.get("fbi"),
            })
    pd.DataFrame(rows).to_csv(out / "summary_scores.csv", index=False, float_format="%.4f")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Compute verification scores.")
    parser.add_argument("--season", default=_CFG_SEASON,
                        help="Season string, e.g. 2024_2025  (overrides config.py)")
    parser.add_argument("--expver", default=_CFG_EXPVER,
                        help="MARS expver, e.g. 0001  (overrides config.py)")
    parser.add_argument("--stream", default=_CFG_STREAM,
                        help="MARS stream, e.g. enfo  (overrides config.py)")
    args = parser.parse_args()

    # Rebuild RUN_TAG-dependent paths
    run_tag = f"{args.season}_{args.stream}_{args.expver}"
    _cfg.RUN_TAG       = run_tag
    _cfg.PATH_PREVERIF = _cfg._BASE / "VERIF_ptype_all" / "DATA_preVerif" / run_tag
    _cfg.PATH_RESULTS  = Path("/home/moeg/PrecType_verif/verification_results") / run_tag

    data_path = _cfg.PATH_PREVERIF
    out_path  = _cfg.PATH_RESULTS
    out_path.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("Precip Type Verification – Step 2: Compute verification scores")
    print("=" * 65)
    print(f"Run tag : {run_tag}")
    print(f"Data    : {data_path}")
    print(f"Output  : {out_path}\n")

    df = load_data(data_path)

    print("Computing scores ...")
    t0 = datetime.now()
    results = scores_by_day(df)
    elapsed = (datetime.now() - t0).total_seconds()
    print(f"  Done in {elapsed:.1f} s\n")

    print("Plotting ...")
    plot_aroc(results,        out_path)
    plot_brier(results,       out_path)
    plot_reliability(results, out_path)
    plot_contingency(results, out_path)
    plot_sharpness(results,   out_path)
    plot_cost_loss(results,   out_path)
    plot_confusion(df,        out_path)
    save_summary(results,     out_path)

    print(f"\nAll outputs saved to {out_path}")


if __name__ == "__main__":
    main()
