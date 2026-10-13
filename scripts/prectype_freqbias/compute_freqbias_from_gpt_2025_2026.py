"""
Compute frequency bias (FBI) directly from the old-methodology reproduction
.gpt files, for the 2025_2026_enfo_0080 dataset (Dec 3 2025 -> Apr 15 2026).

This is the 2025_2026 counterpart of compute_freqbias_from_gpt.py (which was
written for the 2023 48r1 esuite reference dataset). Differences from that
script:

  - Only ONE precipitation-rate threshold per type is used (the operational
    value from config.PRECIP_THRESHOLD), not the full 5-threshold sweep --
    the model-side .gpt files were already generated at that single threshold
    by compute_model_gpt.py, so there is nothing to sweep over here.
  - Model files are keyed by (fdate, step): Loc_{type}_{fdate}_{step}.gpt
    (scripts/prectype_freqbias/compute_model_gpt.py, under
    config.PATH_PREVERIF/ENS_Europe/).
  - Obs files are keyed by (valid_date, valid_hour), NOT (fdate, step):
    SYNOP_{type}_{vdate}_{vhour}.gpt (scripts/prectype_freqbias/mv/extract_obs_gpt.mv,
    under config.PATH_PREVERIF/) -- converted via utils.valid_date_hour(fdate, step)
    to avoid physically duplicating the obs files per forecast date/step.

FBI = mean(forecast_prob / 100) / observed_frequency
    = sum(forecast_prob_i / 100) / sum(obs_i)   [same n on both sides,
                                                   station-by-station match]

Usage:
    python compute_freqbias_from_gpt_2025_2026.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from config import (
    BIAS_GROUPS, PTYPE_CODES, SYNOP_CODES, PRECIP_THRESHOLD,
    PATH_PREVERIF, START_DATE, END_DATE,
)
from utils import valid_date_hour

MODEL_DIR = PATH_PREVERIF / "ENS_Europe"
OBS_DIR   = PATH_PREVERIF

ACTIVE_TYPES = [t for t in PTYPE_CODES if SYNOP_CODES.get(t)]

BIAS_STEPS = sorted({s for grp in BIAS_GROUPS.values() for s in grp})


def date_range(start: str, end: str) -> list[int]:
    d0 = pd.Timestamp(start)
    d1 = pd.Timestamp(end)
    return [int(d.strftime("%Y%m%d")) for d in pd.date_range(d0, d1, freq="D")]


def read_gpt_values(path: Path) -> np.ndarray | None:
    """Read the 6th whitespace-separated column (value) from a .gpt file."""
    if not path.exists():
        return None
    vals = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 6:
                continue
            try:
                vals.append(float(parts[5]))
            except ValueError:
                continue
    if not vals:
        return None
    return np.array(vals, dtype=float)


def main() -> None:
    fdates = date_range(START_DATE, END_DATE)
    print(f"Forecast dates: {START_DATE} -> {END_DATE} ({len(fdates)} days)")
    print(f"Types: {ACTIVE_TYPES}\n")

    rows = []

    for ptype in ACTIVE_TYPES:
        thr_val = PRECIP_THRESHOLD.get(ptype, 0.02)

        for grp, steps in BIAS_GROUPS.items():
            sum_prob  = 0.0
            sum_obs   = 0.0
            n         = 0
            n_missing = 0

            for fdate in fdates:
                for step in steps:
                    if step not in BIAS_STEPS:
                        continue
                    vdate, vhour = valid_date_hour(fdate, step)

                    mfile = MODEL_DIR / f"Loc_{ptype}_{fdate}_{step}.gpt"
                    ofile = OBS_DIR   / f"SYNOP_{ptype}_{vdate}_{vhour}.gpt"

                    mvals = read_gpt_values(mfile)
                    ovals = read_gpt_values(ofile)

                    if mvals is None or ovals is None:
                        n_missing += 1
                        continue

                    # SYNOP present weather can't distinguish dry snow from
                    # wet snow, so the model "snow" probability combines both
                    # GRIB ptype codes (matches old R script and
                    # compute_freqbias_from_gpt.py: perc_snow + perc_wetsnow).
                    if ptype == "snow":
                        wfile = MODEL_DIR / f"Loc_wetsnow_{fdate}_{step}.gpt"
                        wvals = read_gpt_values(wfile)
                        if wvals is None or len(wvals) != len(mvals):
                            n_missing += 1
                            continue
                        mvals = np.minimum(mvals + wvals, 100.0)

                    if len(mvals) != len(ovals):
                        # Mismatched station count -- skip (shouldn't happen,
                        # both derived from the same STATIONS_<vdate>_<vhour>.gpt)
                        n_missing += 1
                        continue

                    sum_prob += (mvals / 100.0).sum()
                    sum_obs  += ovals.sum()
                    n        += len(mvals)

            mean_prob = sum_prob / n if n > 0 else np.nan
            obs_freq  = sum_obs  / n if n > 0 else np.nan
            fbi       = mean_prob / obs_freq if obs_freq > 0 else np.nan

            rows.append({
                "type":            ptype,
                "threshold_mmh":   thr_val,
                "lead_time_group": grp,
                "sum_prob":  round(sum_prob, 4),
                "sum_obs":   int(sum_obs),
                "n":         n,
                "n_missing_pairs": n_missing,
                "mean_prob": round(mean_prob, 6) if np.isfinite(mean_prob) else np.nan,
                "obs_freq":  round(obs_freq,  6) if np.isfinite(obs_freq)  else np.nan,
                "fbi":       round(fbi,       4) if np.isfinite(fbi)      else np.nan,
            })

            print(f"  {ptype:12s}  thr={thr_val:.2f}  {grp}  "
                  f"n={n}  n_missing={n_missing}  fbi={fbi:.4f}" if np.isfinite(fbi)
                  else f"  {ptype:12s}  thr={thr_val:.2f}  {grp}  n={n}  n_missing={n_missing}  fbi=NaN",
                  flush=True)

    df_out = pd.DataFrame(rows)
    out_path = Path(__file__).resolve().parent / "freqbias_results_from_gpt_2025_2026.csv"
    df_out.to_csv(out_path, index=False, float_format="%.4f")
    print(f"\nResults saved to {out_path}")

    print("\nFBI summary (day1 group):")
    summary = df_out[df_out["lead_time_group"] == "day1"][["type", "threshold_mmh", "fbi"]]
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
