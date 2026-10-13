"""
Block A – Step 1: Prepare matched pairs dataset
================================================
Reads raw ENS GRIB (param 260015 = precip type, 260048 = precip rate)
and SYNOP BUFR observations, computes per-type ensemble probabilities
using per-type precipitation rate thresholds, and saves matched
obs/forecast pairs to Parquet format (one file per forecast date).

Nearest-gridpoint design
------------------------
Instead of querying the forecast grid KDTree once per step (56×/date),
we collect all station locations across all steps for a date, deduplicate
them, and run a single batch KDTree query.  Values are then extracted with
numpy fancy-indexing — no Python loop over members or grid-dimension
iteration.  See utils.build_station_batch_index() for details.

Replaces:
  - ProbPrecType_calculate_all*.mv  (probability computation from raw ENS)
  - Prepare_dataset_ptype*.ipynb    (obs matching + parquet export)
  - point_ptype_pandas.ipynb

Usage:
    python 01_prepare_dataset.py START_YYYYMMDD END_YYYYMMDD [--workers N]

Output:
    {PATH_PREVERIF}/matched_pairs_{YYYYMMDD}.parquet  (one per forecast date)
"""

import sys
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from config import (
    AREA, OROG_THRESHOLD_M, N_MEMBERS, STEPS,
    PARAM_PTYPE, PARAM_PRATE,
    PTYPE_CODES, PRECIP_THRESHOLD, SYNOP_CODES,
    PATH_SYNOP, PATH_OROG, EXCLUDE_DATES,
    SEASON as _CFG_SEASON, EXPVER as _CFG_EXPVER, STREAM as _CFG_STREAM,
)
import config as _cfg
from utils import (
    valid_date_hour, find_synop_bufr,
    build_orog_filter, read_synop_raw, filter_synop_obs,
    read_synop_df, extract_synop_arrays_df, extract_synop_arrays, apply_orog_filter,
    classify_synop, load_ens_grib, build_station_batch_index,
)


# ── Per-date processing ───────────────────────────────────────────────────────

def process_date(
    fdate: int,
    orog_tree,
    orog_values: np.ndarray,
    obs_cache: dict | None = None,
) -> tuple:
    """
    Process one forecast date in four phases:

    Phase 1 – Load GRIB
        earthkit.data reads the entire file once; both parameters are
        extracted as 2-D arrays (n_fields × n_grid) via FieldList.sel()
        and FieldList.to_numpy(flatten=True).

    Phase 2 – Collect all SYNOP observations
        If obs_cache is given (pre-built in main() BEFORE any earthkit GRIB
        loading, to avoid the earthkit/metview eccodes conflict), obs are
        looked up from it by (valid_date, valid_hour). Otherwise falls back
        to the legacy per-call Metview obsfilter path.

    Phase 3 – Batch nearest-gridpoint
        All station locations across all steps are deduplicated and the
        forecast grid KDTree is queried *once* for the full batch.
        utils.build_station_batch_index() returns a mapping array that
        the per-step loop uses for O(1) index look-up.

    Phase 4 – Per-step probability computation
        Pure numpy fancy-indexing; no tree queries, no member loops.
    """
    grib_path = _cfg.PATH_RAW / f"raw_{fdate}.grib"
    if not grib_path.exists():
        return fdate, 0, len(STEPS), f"GRIB missing: {grib_path}"

    # ── Phase 1: Load GRIB with earthkit.data ─────────────────────────────────
    try:
        ptype_vals, prate_vals, field_steps, grid_lats, grid_lons = load_ens_grib(
            grib_path, PARAM_PTYPE, PARAM_PRATE
        )
    except Exception as exc:
        return fdate, 0, len(STEPS), f"GRIB read error: {exc}"

    # ── Phase 2: Collect SYNOP obs for every step ─────────────────────────────
    step_obs: dict    = {}   # ordered: step → obs_df

    if obs_cache is not None:
        # Fast path: obs already decoded (eccodes) + orog-filtered in main()
        # BEFORE any earthkit GRIB loading happened, avoiding the
        # earthkit/metview same-process conflict entirely.
        for step in STEPS:
            if not np.any(field_steps == step):
                continue
            valid_date, valid_hour = valid_date_hour(fdate, step)
            obs_df = obs_cache.get((valid_date, valid_hour))
            if obs_df is not None and len(obs_df) > 0:
                step_obs[step] = obs_df
    else:
        # Legacy path: per-call Metview obsfilter (slow, and must not be
        # mixed with earthkit GRIB loading in the same process).
        synop_cache: dict = {}
        for step in STEPS:
            if not np.any(field_steps == step):
                continue
            valid_date, valid_hour = valid_date_hour(fdate, step)

            if valid_date not in synop_cache:
                bufr = find_synop_bufr(_cfg.PATH_SYNOP, valid_date)
                synop_cache[valid_date] = read_synop_raw(bufr) if bufr else None

            if synop_cache[valid_date] is None:
                continue

            obs_df = filter_synop_obs(
                synop_cache[valid_date], valid_hour, AREA, OROG_THRESHOLD_M,
                orog_tree, orog_values,
            )
            if obs_df is not None and len(obs_df) > 0:
                step_obs[step] = obs_df

    if not step_obs:
        return fdate, 0, len(STEPS), "No observations"

    # ── Phase 3: Single batch nearest-gridpoint for all unique stations ────────
    # build_station_batch_index() queries the KDTree exactly once, returning:
    #   grid_idx_for_unique[i]  = flat GRIB grid index for unique station i
    #   inverse_idx[j]          = index into unique stations for concat position j
    #   n_per_step[k]           = number of stations in the k-th step_obs entry
    grid_idx_for_unique, inverse_idx, n_per_step = build_station_batch_index(
        grid_lats, grid_lons, step_obs
    )

    # ── Phase 4: Per-step probability computation (numpy fancy-indexing only) ──
    records = []
    n_ok    = 0
    n_fail  = len(STEPS) - len(step_obs)   # steps skipped in Phase 2
    cursor  = 0

    for (step, obs_df), n_st in zip(step_obs.items(), n_per_step):
        # Recover the grid indices for this step's stations from the batch result
        step_inv = inverse_idx[cursor : cursor + n_st]
        grid_idx = grid_idx_for_unique[step_inv]   # (n_st,) grid indices
        cursor  += n_st

        # Select all member fields for this step from the pre-loaded 2-D arrays
        mask        = field_steps == step
        ptype_step  = ptype_vals[mask]             # (n_members, n_grid)
        prate_step  = prate_vals[mask]             # (n_members, n_grid)

        # Extract at station grid points: pure numpy fancy-indexing
        ptype_at_st = ptype_step[:, grid_idx]      # (n_members, n_st)
        prate_at_st = prate_step[:, grid_idx]      # (n_members, n_st)

        # Per-type ensemble probability
        # Divide by the actual member count in the loaded data so this is
        # correct for both 51-member (pre-50r1) and 50-member (50r1+) runs.
        n_members_actual = ptype_step.shape[0]
        probs: dict = {}
        for ptype_name, ptype_code in PTYPE_CODES.items():
            thr = PRECIP_THRESHOLD.get(ptype_name, 0.02)
            matched = (ptype_at_st == ptype_code) & (prate_at_st >= thr)
            probs[f"prob_{ptype_name}"] = matched.sum(axis=0) / n_members_actual * 100.0

        # Binary observed classification from SYNOP ww codes
        obs_bins = classify_synop(obs_df["ww"].values, SYNOP_CODES)

        valid_date, valid_hour = valid_date_hour(fdate, step)
        row: dict = {
            "forecast_date": np.full(n_st, fdate,       dtype=np.int32),
            "valid_date":    np.full(n_st, valid_date,  dtype=np.int32),
            "forecast_step": np.full(n_st, step,        dtype=np.int16),
            "valid_hour":    np.full(n_st, valid_hour,  dtype=np.int8),
            "lat":           obs_df["lat"].values,
            "lon":           obs_df["lon"].values,
            "elevation":     obs_df["elevation"].values,
            "synop_code":    obs_df["ww"].values,
        }
        for ptype_name in PTYPE_CODES:
            row[f"obs_{ptype_name}"]  = obs_bins.get(
                ptype_name, np.zeros(n_st, dtype=np.int8)
            )
        row.update(probs)

        records.append(pd.DataFrame(row))
        n_ok += 1

    if not records:
        return fdate, n_ok, n_fail, "No data after filtering"

    date_df  = pd.concat(records, ignore_index=True)
    out_path = _cfg.PATH_PREVERIF / f"matched_pairs_{fdate}.parquet"
    date_df.to_parquet(out_path, compression="snappy", index=False)

    return fdate, n_ok, n_fail, "OK"


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare matched obs/forecast pairs for verification."
    )
    parser.add_argument("start_date", help="First forecast date  YYYYMMDD")
    parser.add_argument("end_date",   help="Last  forecast date  YYYYMMDD")
    parser.add_argument("--workers",  type=int, default=4,
                        help="Number of parallel worker processes (default 4)")
    parser.add_argument("--season",  default=_CFG_SEASON,
                        help="Season string, e.g. 2024_2025  (overrides config.py)")
    parser.add_argument("--expver",  default=_CFG_EXPVER,
                        help="MARS expver, e.g. 0001  (overrides config.py)")
    parser.add_argument("--stream",  default=_CFG_STREAM,
                        help="MARS stream, e.g. enfo  (overrides config.py)")
    parser.add_argument("--obs-source", choices=["eccodes", "metview"], default="eccodes",
                        help="SYNOP obs decoder: 'eccodes' (fast, parquet-cached, no WMO "
                             "station dedup) or 'metview' (obsfilter – matches the "
                             "original reference pipeline exactly, but much slower and "
                             "cannot be mixed with earthkit GRIB loading in the same "
                             "process, so it is done per-date inside each worker).")
    args = parser.parse_args()

    # Rebuild RUN_TAG-dependent paths from CLI args so different runs
    # never overwrite each other's data.
    run_tag = f"{args.season}_{args.stream}_{args.expver}"
    _cfg.RUN_TAG      = run_tag
    _cfg.PATH_RAW     = _cfg._BASE / "VERIF_ptype_all" / "raw"           / run_tag
    _cfg.PATH_PREVERIF= _cfg._BASE / "VERIF_ptype_all" / "DATA_preVerif" / run_tag
    _cfg.PATH_SYNOP   = _cfg._BASE / "VERIF_ptype_all" / "SYNOP"         / args.season

    start_dt = datetime.strptime(args.start_date, "%Y%m%d")
    end_dt   = datetime.strptime(args.end_date,   "%Y%m%d")
    fdates   = []
    excluded_in_range = []
    d = start_dt
    while d <= end_dt:
        datestr = d.strftime("%Y%m%d")
        if datestr in EXCLUDE_DATES:
            excluded_in_range.append(datestr)
        else:
            fdates.append(int(datestr))
        d += timedelta(days=1)

    if excluded_in_range:
        print(f"Excluding dates (config.EXCLUDE_DATES): {excluded_in_range}")

    _cfg.PATH_PREVERIF.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("Precip Type Verification – Step 1: Prepare matched pairs")
    print("=" * 65)
    print(f"Run tag : {run_tag}")
    print(f"Dates   : {args.start_date} → {args.end_date} ({len(fdates)} days)")
    print(f"Workers : {args.workers}")
    print(f"Output  : {_cfg.PATH_PREVERIF}")
    print()

    print("Loading orography ...")
    orog_tree, orog_values = build_orog_filter(PATH_OROG)
    print(f"  Grid points: {len(orog_values):,}\n")

    # ── Pre-build SYNOP obs cache (eccodes fast path) BEFORE any earthkit ─────
    # GRIB loading happens in the worker processes, to avoid the documented
    # earthkit/metview same-process conflict and the ~100s/obsfilter-call
    # cost (see utils.extract_synop_arrays docstring).
    obs_cache: dict | None = None
    if args.obs_source == "eccodes":
        needed: set[tuple[int, int]] = set()
        for fdate in fdates:
            for step in STEPS:
                needed.add(valid_date_hour(fdate, step))
        needed_dates = sorted({vd for vd, _ in needed})

        print(f"Loading SYNOP obs (eccodes / parquet cache) for {len(needed_dates)} dates ...")
        synop_df_cache: dict = {}
        for k, vd in enumerate(needed_dates, 1):
            bufr = find_synop_bufr(_cfg.PATH_SYNOP, vd)
            df   = read_synop_df(bufr) if bufr else None
            synop_df_cache[vd] = df
            status = "OK" if df is not None else "MISSING"
            print(f"  {k}/{len(needed_dates)}: {vd} {status}", flush=True)
        n_loaded = sum(1 for v in synop_df_cache.values() if v is not None)
        print(f"  {n_loaded}/{len(needed_dates)} SYNOP dates loaded\n")

        print("Extracting + orog-filtering SYNOP obs arrays ...")
        obs_cache = {}
        for vd, vh in sorted(needed):
            df = synop_df_cache.get(vd)
            raw = extract_synop_arrays_df(df, vh, AREA) if df is not None else None
            obs_cache[(vd, vh)] = (
                apply_orog_filter(raw, OROG_THRESHOLD_M, orog_tree, orog_values)
                if raw is not None else None
            )
        n_obs = sum(1 for v in obs_cache.values() if v is not None and len(v) > 0)
        print(f"  {n_obs}/{len(obs_cache)} (date, hour) pairs have valid obs\n")

    t0 = datetime.now()
    results = []

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(process_date, fdate, orog_tree, orog_values, obs_cache): fdate
            for fdate in fdates
        }
        for fut in as_completed(futures):
            fdate, n_ok, n_fail, status = fut.result()
            results.append((fdate, n_ok, n_fail, status))
            print(f"  {fdate}: {n_ok:3d} ok  {n_fail:3d} failed  [{status}]")

    elapsed = (datetime.now() - t0).total_seconds()
    n_success = sum(1 for *_, s in results if s == "OK")
    print()
    print(f"Completed {n_success}/{len(fdates)} dates in {elapsed / 60:.1f} min")


if __name__ == "__main__":
    main()

