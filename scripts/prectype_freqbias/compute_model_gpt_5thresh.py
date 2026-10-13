"""
Model-side ".gpt" extraction for the old-methodology FBI reproduction
(2025_2026_enfo_0080 dataset) -- FULL 5-THRESHOLD SWEEP variant.

This is the threshold-sweep counterpart of compute_model_gpt.py (which only
computes each type's single operational threshold from config.PRECIP_THRESHOLD).
Here we compute ensemble probabilities at ALL 5 BIAS_THRESHOLDS
(0.02/0.05/0.07/0.10/0.12 mm/h) for every type, so the old-code reproduction
can be compared against the new pipeline's full FBI-vs-threshold curve
(the "typical line plots"), not just a single point.

The observation side is threshold-independent (present-weather codes don't
change with precip rate threshold), so the existing SYNOP_<type>_<vdate>_<vhour>.gpt
files (from scripts/prectype_freqbias/mv/extract_obs_gpt.mv) are reused as-is --
only the model side needs to be recomputed per threshold.

Output layout mirrors the historical reference structure (compute_freqbias_from_gpt.py):
    PATH_PREVERIF/ENS_Europe/ENS<thr_code>_Europe/Loc_<type>_<fdate>_<step>.gpt

Usage:
    python compute_model_gpt_5thresh.py START_YYYYMMDD END_YYYYMMDD [--workers N]
"""

import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from config import (
    PARAM_PTYPE, PARAM_PRATE, PTYPE_CODES, BIAS_THRESHOLDS, BIAS_GROUPS,
    PATH_RAW, PATH_PREVERIF,
)
from utils import valid_date_hour, load_ens_grib, build_station_batch_index

BIAS_STEPS = sorted({s for grp in BIAS_GROUPS.values() for s in grp})

OUT_BASE = PATH_PREVERIF / "ENS_Europe"

THR_CODES = {0.02: "002", 0.05: "005", 0.07: "007", 0.10: "01", 0.12: "012"}


def read_gpt_stations(path: Path):
    """Read lat/lon columns (in file row order) from a STATIONS_*.gpt file."""
    if not path.exists():
        return None
    lats, lons = [], []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 6:
                continue
            lats.append(float(parts[0]))
            lons.append(float(parts[1]))
    if not lats:
        return None
    return np.array(lats, dtype=float), np.array(lons, dtype=float)


def write_gpt(path: Path, lats: np.ndarray, lons: np.ndarray, values: np.ndarray,
              date: int, time: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write("#GEO\n")
        f.write("# lat\tlon\theight\tdate\t\ttime\tvalue\n")
        f.write("#DATA\n")
        for lat, lon, val in zip(lats, lons, values):
            f.write(f"{lat}\t{lon}\t0\t{date}\t{time}\t{val:.4f}\n")


def process_date(fdate: int) -> tuple[int, int]:
    """Returns (n_steps_written, n_steps_skipped) for this forecast date."""
    grib_path = PATH_RAW / f"raw_{fdate}.grib"
    if not grib_path.exists():
        return (0, len(BIAS_STEPS))

    # ── Phase 1: load per-step station lists (lat/lon), from STATIONS files ──
    step_obs: dict = {}      # step -> DataFrame(lat, lon)
    step_valid: dict = {}    # step -> (valid_date, valid_hour)
    for step in BIAS_STEPS:
        vdate, vhour = valid_date_hour(fdate, step)
        stations_path = PATH_PREVERIF / f"STATIONS_{vdate}_{vhour}.gpt"
        stations = read_gpt_stations(stations_path)
        if stations is None:
            continue
        lats, lons = stations
        step_obs[step] = pd.DataFrame({"lat": lats, "lon": lons})
        step_valid[step] = (vdate, vhour)

    n_skipped = len(BIAS_STEPS) - len(step_obs)
    if not step_obs:
        return (0, n_skipped)

    # ── Phase 2: load GRIB (once per date, regardless of threshold count) ───
    try:
        ptype_vals, prate_vals, field_steps, grid_lats, grid_lons = load_ens_grib(
            grib_path, PARAM_PTYPE, PARAM_PRATE
        )
    except Exception as e:
        print(f"  WARNING {fdate}: {e}", flush=True)
        return (0, len(BIAS_STEPS))

    # ── Phase 3: batch nearest-gridpoint index ──────────────────────────────
    grid_idx_for_unique, inverse_idx, n_per_step = build_station_batch_index(
        grid_lats, grid_lons, step_obs
    )

    # ── Phase 4: per-step, per-threshold probability computation + write ───
    cursor = 0
    n_written = 0
    for step, n_st in zip(step_obs.keys(), n_per_step):
        step_inv = inverse_idx[cursor: cursor + n_st]
        grid_idx = grid_idx_for_unique[step_inv]
        cursor += n_st

        mask = field_steps == step
        if not np.any(mask):
            n_skipped += 1
            continue

        ptype_st = ptype_vals[mask][:, grid_idx]   # (n_members, n_st)
        prate_st = prate_vals[mask][:, grid_idx]   # (n_members, n_st)

        vdate, vhour = step_valid[step]
        lats = step_obs[step]["lat"].values
        lons = step_obs[step]["lon"].values

        for thr in BIAS_THRESHOLDS:
            thr_code = THR_CODES[thr]
            thr_dir = OUT_BASE / f"ENS{thr_code}_Europe"

            for ptype_name, ptype_code in PTYPE_CODES.items():
                hits = (ptype_st == ptype_code) & (prate_st >= thr)
                pct = hits.mean(axis=0) * 100.0   # (n_st,)

                out_path = thr_dir / f"Loc_{ptype_name}_{fdate}_{step}.gpt"
                write_gpt(out_path, lats, lons, pct, fdate, step)

        n_written += 1

    return (n_written, n_skipped)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Model-side .gpt extraction (5-threshold sweep) for the old-methodology FBI reproduction."
    )
    parser.add_argument("start_date", help="Start forecast date YYYYMMDD")
    parser.add_argument("end_date", help="End forecast date YYYYMMDD")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    d0 = datetime.strptime(args.start_date, "%Y%m%d")
    d1 = datetime.strptime(args.end_date, "%Y%m%d")
    dates = []
    d = d0
    while d <= d1:
        dates.append(int(d.strftime("%Y%m%d")))
        d += timedelta(days=1)

    print(f"Model-side .gpt extraction (5-threshold sweep): {args.start_date} -> {args.end_date} "
          f"({len(dates)} dates), steps={BIAS_STEPS}, thresholds={BIAS_THRESHOLDS}")
    print(f"Output base dir: {OUT_BASE}")

    if args.workers <= 1:
        for i, fdate in enumerate(dates, 1):
            n_written, n_skipped = process_date(fdate)
            print(f"  {i}/{len(dates)}: {fdate} written={n_written} skipped={n_skipped}", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(process_date, fdate): fdate for fdate in dates}
            for i, fut in enumerate(as_completed(futs), 1):
                fdate = futs[fut]
                n_written, n_skipped = fut.result()
                print(f"  {i}/{len(dates)}: {fdate} written={n_written} skipped={n_skipped}", flush=True)

    print("Done.")


if __name__ == "__main__":
    main()
