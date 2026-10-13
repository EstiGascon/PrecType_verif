"""
Compute frequency bias (FBI) from the old-methodology reproduction .gpt
files across the FULL 5-threshold sweep (BIAS_THRESHOLDS), for the
2025_2026_enfo_0080 dataset.

Counterpart of compute_freqbias_from_gpt_2025_2026.py (single operational
threshold per type) -- this version sweeps all 5 candidate thresholds
(0.02/0.05/0.07/0.10/0.12 mm/h) for every type, using the model-side .gpt
files produced by compute_model_gpt_5thresh.py
(PATH_PREVERIF/ENS_Europe/ENS<thr_code>_Europe/Loc_<type>_<fdate>_<step>.gpt).

The observation side is threshold-independent, so the same
SYNOP_<type>_<vdate>_<vhour>.gpt files (keyed by valid date/hour) are reused
for every threshold.

Output CSV has the same schema as compute_freqbias.py's freqbias_results.csv
(type, threshold_mmh, lead_time_group, sum_prob, sum_obs, n, mean_prob,
obs_freq, fbi), so plot_freqbias.py can be pointed at it directly via
--input to produce the standard FBI-vs-threshold line plots.

Usage:
    python compute_freqbias_from_gpt_2025_2026_5thresh.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from config import (
    BIAS_GROUPS, PTYPE_CODES, SYNOP_CODES, BIAS_THRESHOLDS,
    PATH_PREVERIF, START_DATE, END_DATE,
)
from utils import valid_date_hour

MODEL_BASE = PATH_PREVERIF / "ENS_Europe"
OBS_DIR    = PATH_PREVERIF

ACTIVE_TYPES = [t for t in PTYPE_CODES if SYNOP_CODES.get(t)]

BIAS_STEPS = sorted({s for grp in BIAS_GROUPS.values() for s in grp})

THR_CODES = {0.02: "002", 0.05: "005", 0.07: "007", 0.10: "01", 0.12: "012"}


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
    print(f"Thresholds: {BIAS_THRESHOLDS} mm/h")
    print(f"Types: {ACTIVE_TYPES}\n")

    rows = []

    for thr in BIAS_THRESHOLDS:
        thr_code = THR_CODES[thr]
        model_dir = MODEL_BASE / f"ENS{thr_code}_Europe"

        for ptype in ACTIVE_TYPES:
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

                        mfile = model_dir / f"Loc_{ptype}_{fdate}_{step}.gpt"
                        ofile = OBS_DIR   / f"SYNOP_{ptype}_{vdate}_{vhour}.gpt"

                        mvals = read_gpt_values(mfile)
                        ovals = read_gpt_values(ofile)

                        if mvals is None or ovals is None:
                            n_missing += 1
                            continue

                        # SYNOP present weather can't distinguish dry snow
                        # from wet snow -- combine both GRIB ptype codes.
                        if ptype == "snow":
                            wfile = model_dir / f"Loc_wetsnow_{fdate}_{step}.gpt"
                            wvals = read_gpt_values(wfile)
                            if wvals is None or len(wvals) != len(mvals):
                                n_missing += 1
                                continue
                            mvals = np.minimum(mvals + wvals, 100.0)

                        if len(mvals) != len(ovals):
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
                    "threshold_mmh":   thr,
                    "lead_time_group": grp,
                    "sum_prob":  round(sum_prob, 4),
                    "sum_obs":   int(sum_obs),
                    "n":         n,
                    "mean_prob": round(mean_prob, 6) if np.isfinite(mean_prob) else np.nan,
                    "obs_freq":  round(obs_freq,  6) if np.isfinite(obs_freq)  else np.nan,
                    "fbi":       round(fbi,       4) if np.isfinite(fbi)      else np.nan,
                })

            print(f"  thr={thr:.2f}  type={ptype:12s} done", flush=True)

    df_out = pd.DataFrame(rows)
    out_path = Path(__file__).resolve().parent / "freqbias_results_from_gpt_2025_2026_5thresh.csv"
    df_out.to_csv(out_path, index=False, float_format="%.4f")
    print(f"\nResults saved to {out_path}")

    print("\nFBI summary (threshold -> day1 group):")
    summary = df_out[df_out["lead_time_group"] == "day1"].pivot(
        index="type", columns="threshold_mmh", values="fbi"
    )
    print(summary.to_string(float_format="{:.4f}".format))


if __name__ == "__main__":
    main()
