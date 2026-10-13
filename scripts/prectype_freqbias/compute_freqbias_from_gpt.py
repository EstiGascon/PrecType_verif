"""
Compute frequency bias (FBI) directly from the old Metview reference gpt
files, for the exact same 59 dates (2023-02-16 -> 2023-04-15) used by
compute_freqbias.py.

This bypasses BUFR decoding entirely (Metview's obsfilter + WMO-station
dedup already happened when the gpt files were generated in 2023) so it
gives an authoritative reference value.  Any remaining difference from
compute_freqbias.py's output is due to our own code, not to differences
in the observation data.

Files used (per threshold code 002/005/007/01/012):
  Model: DATA_verif/2023_48r1_esuite/ENS_Europe/ENS{thr}_Europe/Loc_{type}_{date}_{step}.gpt
  Obs:   DATA_verif/2023_48r1_esuite/SYN_Europe/SYN{thr}_Europe/SYNOP_{type}_{date}_{step}.gpt

Each gpt file has one row per station, column 6 (0-indexed 5) is the value:
  Model file: forecast probability (0-100)
  Obs file:   0/1 indicator for that precip type

FBI = mean(forecast_prob/100) / mean(obs_indicator)
    = sum(forecast_prob/100) / sum(obs_indicator)   [same n on both sides,
                                                       station-by-station match]

Usage:
    python compute_freqbias_from_gpt.py
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from config import BIAS_GROUPS, PTYPE_CODES, SYNOP_CODES

BASE = Path("/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_bias/DATA_verif/2023_48r1_esuite")

THRESHOLDS = {
    "002": 0.02,
    "005": 0.05,
    "007": 0.07,
    "01":  0.10,
    "012": 0.12,
}

ACTIVE_TYPES = [t for t in PTYPE_CODES if SYNOP_CODES.get(t)]

START_DATE = "20230216"
END_DATE   = "20230415"


def date_range(start: str, end: str) -> list[str]:
    d0 = pd.Timestamp(start)
    d1 = pd.Timestamp(end)
    return [d.strftime("%Y%m%d") for d in pd.date_range(d0, d1, freq="D")]


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
    dates = date_range(START_DATE, END_DATE)
    print(f"Dates: {START_DATE} -> {END_DATE} ({len(dates)} days)")
    print(f"Thresholds: {list(THRESHOLDS.values())} mm/h")
    print(f"Types: {ACTIVE_TYPES}\n")

    rows = []

    for thr_code, thr_val in THRESHOLDS.items():
        model_dir = BASE / "ENS_Europe" / f"ENS{thr_code}_Europe"
        obs_dir   = BASE / "SYN_Europe" / f"SYN{thr_code}_Europe"

        for ptype in ACTIVE_TYPES:
            for grp, steps in BIAS_GROUPS.items():
                sum_prob = 0.0
                sum_obs  = 0.0
                n        = 0
                n_missing = 0

                for d in dates:
                    for step in steps:
                        mfile = model_dir / f"Loc_{ptype}_{d}_{step}.gpt"
                        ofile = obs_dir   / f"SYNOP_{ptype}_{d}_{step}.gpt"

                        mvals = read_gpt_values(mfile)
                        ovals = read_gpt_values(ofile)

                        if mvals is None or ovals is None:
                            n_missing += 1
                            continue

                        # SYNOP present weather can't distinguish dry snow from
                        # wet snow, so the model "snow" probability combines
                        # both GRIB ptype codes (matches old R script:
                        # MOD_man_snow = round(perc_snow,2) + round(perc_wetsnow,2)).
                        if ptype == "snow":
                            wfile = model_dir / f"Loc_wetsnow_{d}_{step}.gpt"
                            wvals = read_gpt_values(wfile)
                            if wvals is None or len(wvals) != len(mvals):
                                n_missing += 1
                                continue
                            mvals = np.minimum(mvals + wvals, 100.0)

                        if len(mvals) != len(ovals):
                            # Mismatched station count -- skip (shouldn't happen)
                            n_missing += 1
                            continue

                        sum_prob += (mvals / 100.0).sum()
                        sum_obs  += ovals.sum()
                        n        += len(mvals)

                mean_prob = sum_prob / n if n > 0 else np.nan
                obs_freq  = sum_obs  / n if n > 0 else np.nan
                fbi       = mean_prob / obs_freq if obs_freq > 0 else np.nan

                rows.append({
                    "type": ptype,
                    "threshold_mmh": thr_val,
                    "lead_time_group": grp,
                    "sum_prob": round(sum_prob, 4),
                    "sum_obs": int(sum_obs),
                    "n": n,
                    "n_missing_pairs": n_missing,
                    "mean_prob": round(mean_prob, 6) if np.isfinite(mean_prob) else np.nan,
                    "obs_freq": round(obs_freq, 6) if np.isfinite(obs_freq) else np.nan,
                    "fbi": round(fbi, 4) if np.isfinite(fbi) else np.nan,
                })

            print(f"  thr={thr_val}  type={ptype:12s} done", flush=True)

    df_out = pd.DataFrame(rows)
    out_path = Path(__file__).resolve().parent / "freqbias_results_from_gpt.csv"
    df_out.to_csv(out_path, index=False, float_format="%.4f")
    print(f"\nResults saved to {out_path}")

    print("\nFBI summary (threshold -> day1 group):")
    summary = df_out[df_out["lead_time_group"] == "day1"].pivot(
        index="type", columns="threshold_mmh", values="fbi"
    )
    print(summary.to_string(float_format="{:.4f}".format))

    print("\nStation counts (n) per (threshold, group) -- rain only:")
    rain = df_out[df_out["type"] == "rain"][["threshold_mmh", "lead_time_group", "n", "n_missing_pairs"]]
    print(rain.to_string(index=False))


if __name__ == "__main__":
    main()
