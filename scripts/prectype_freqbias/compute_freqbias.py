"""
Block B – Step 1: Compute frequency bias at multiple precipitation rate thresholds
===================================================================================
For each candidate threshold (0.02, 0.05, 0.07, 0.10, 0.12 mm/h) and each
precipitation type, computes the Frequency Bias Index (FBI):

    FBI = mean(forecast_prob / 100) / observed_frequency

FBI = 1 means the forecast frequency equals the observed frequency (unbiased).
FBI > 1 means over-forecasting; FBI < 1 means under-forecasting.

Results are grouped into three lead-time bands:
  day1  = steps  0-21 h    (0-24 h range)
  day2  = steps 24-45 h   (24-48 h range)
  day5  = steps 96-117 h  (96-120 h range)

Nearest-gridpoint design
------------------------
Same batch approach as prectype_verif (see utils.build_station_batch_index):
the forecast-grid KDTree is queried once per date for the union of all
station locations across all steps, rather than once per step.

This script replaces:
  - Scripts_freqbias/old_code/ProbPrecType_calculate_all*.mv  (5 threshold variants)
  - Scripts_freqbias/old_code/Metview_preVerif*.mv            (pre-verification)
  - The bias-calculation sections of BIAS_prates_thewholeperiod_48r1.r

Usage:
    python compute_freqbias.py START_YYYYMMDD END_YYYYMMDD [--workers N]

Output:
    {PATH_FREQBIAS}/freqbias_results.csv
"""

import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from config import (
    AREA, OROG_THRESHOLD_M, N_MEMBERS, STEPS,
    PARAM_PTYPE, PARAM_PRATE,
    PTYPE_CODES, SYNOP_CODES, PTYPE_COMBINE_CODES, BIAS_THRESHOLDS, BIAS_GROUPS,
    PATH_SYNOP, PATH_OROG,
    SEASON as _CFG_SEASON, EXPVER as _CFG_EXPVER, STREAM as _CFG_STREAM,
)
import config as _cfg
from utils import (
    valid_date_hour, find_synop_bufr,
    build_orog_filter, read_synop_df, extract_synop_arrays_df, apply_orog_filter,
    read_synop_raw, extract_synop_arrays,
    classify_synop, load_ens_grib, build_station_batch_index,
)

ACTIVE_TYPES = [t for t in PTYPE_CODES if SYNOP_CODES.get(t)]

# Pre-compute which steps belong to each lead-time group
_STEP_TO_GROUP: dict[int, str] = {
    s: grp for grp, grp_steps in BIAS_GROUPS.items() for s in grp_steps
}


# ── Probabilistic accumulation ───────────────────────────────────────────────
#
# FBI = mean_forecast_probability / obs_frequency
#     = (sum of per-station member fractions) / (sum of obs)
#
# This matches the old R script exactly:
#   - per station, compute fraction of members that forecast ptype AND prate>=thr
#   - FBI = sum(fractions) / sum(obs)
#
def _empty_counts() -> dict:
    return {
        (ptype, thr, grp): {"sum_prob": 0.0, "sum_obs": 0, "n": 0}
        for ptype in ACTIVE_TYPES
        for thr in BIAS_THRESHOLDS
        for grp in BIAS_GROUPS
    }


def process_date(
    fdate: int,
    orog_tree,
    orog_values: np.ndarray,
    raw_path_override: Path | None = None,
    prate_path_override: Path | None = None,
    obs_cache: dict | None = None,
) -> dict:
    """
    Process one forecast date using the same 4-phase approach as prectype_verif.

    raw_path_override:   if given, use this directory instead of _cfg.PATH_RAW.
    prate_path_override: if given, prate is in a separate file in this directory
                         (old archive: total_prec_VERIF_{date}.grib).
    obs_cache:           pre-computed obs DataFrames keyed by (valid_date, valid_hour),
                         built in main() BEFORE any earthkit GRIB loading to avoid the
                         earthkit/metview eccodes conflict.
    """
    raw_dir = raw_path_override if raw_path_override else _cfg.PATH_RAW
    # Try new naming first (raw_{fdate}.grib), then old (Prectype_raw_VERIF_{fdate}.grib)
    grib_path = raw_dir / f"raw_{fdate}.grib"
    if not grib_path.exists():
        grib_path = raw_dir / f"Prectype_raw_VERIF_{fdate}.grib"
    if not grib_path.exists():
        return {}

    # Separate prate file (old archive format)
    prate_path: Path | None = None
    if prate_path_override:
        candidate = prate_path_override / f"total_prec_VERIF_{fdate}.grib"
        prate_path = candidate if candidate.exists() else None

    # ── Phase 1 ──────────────────────────────────────────────────────────────
    print(f"    {fdate}: loading GRIB ...", flush=True)
    try:
        ptype_vals, prate_vals, field_steps, grid_lats, grid_lons = load_ens_grib(
            grib_path, PARAM_PTYPE, PARAM_PRATE, prate_path=prate_path
        )
    except Exception as e:
        print(f"  WARNING {fdate}: {e}", flush=True)
        return {}
    print(f"    {fdate}: GRIB loaded, building step_obs ...", flush=True)

    # ── Phase 2 ──────────────────────────────────────────────────────────────
    # obs_cache holds pre-extracted+orog-filtered DataFrames keyed by
    # (valid_date, valid_hour).  These were built before any earthkit GRIB
    # loading to avoid the metview/eccodes conflict.
    local_obs: dict = obs_cache if obs_cache is not None else {}
    step_obs: dict  = {}

    bias_steps = set(_STEP_TO_GROUP)
    for step in STEPS:
        if step not in bias_steps or not np.any(field_steps == step):
            continue
        valid_date, valid_hour = valid_date_hour(fdate, step)
        key = (valid_date, valid_hour)
        obs_df = local_obs.get(key)
        if obs_df is not None and len(obs_df) > 0:
            step_obs[step] = obs_df

    if not step_obs:
        return {}

    # ── Phase 3 ──────────────────────────────────────────────────────────────
    grid_idx_for_unique, inverse_idx, n_per_step = build_station_batch_index(
        grid_lats, grid_lons, step_obs
    )

    # ── Phase 4 ──────────────────────────────────────────────────────────────
    counts  = _empty_counts()
    cursor  = 0

    for (step, obs_df), n_st in zip(step_obs.items(), n_per_step):
        grp = _STEP_TO_GROUP[step]

        step_inv = inverse_idx[cursor : cursor + n_st]
        grid_idx = grid_idx_for_unique[step_inv]   # (n_st,)
        cursor  += n_st

        mask        = field_steps == step
        ptype_st    = ptype_vals[mask][:, grid_idx]   # (n_members, n_st)
        prate_st    = prate_vals[mask][:, grid_idx]   # (n_members, n_st)

        obs_bins = classify_synop(obs_df["ww"].values, SYNOP_CODES)

        n_mem = ptype_st.shape[0]   # number of members for this step

        for ptype_name, ptype_code in PTYPE_CODES.items():
            if ptype_name not in ACTIVE_TYPES:
                continue
            obs_vec = obs_bins[ptype_name].astype(np.float32)   # (n_st,)

            # SYNOP present weather can't distinguish dry snow from wet snow,
            # so the model "snow" probability combines both GRIB ptype codes
            # (matches old R script: perc_snow + perc_wetsnow).
            combine_codes = PTYPE_COMBINE_CODES.get(ptype_name, [ptype_code])

            for thr in BIAS_THRESHOLDS:
                # Fraction of members that forecast this ptype AND prate >= thr
                # Shape: (n_st,), values 0.0–1.0
                member_hits = (np.isin(ptype_st, combine_codes) & (prate_st >= thr)).astype(np.float32)
                fractions   = member_hits.mean(axis=0)   # (n_st,)

                key = (ptype_name, thr, grp)
                counts[key]["sum_prob"] += float(fractions.sum())
                counts[key]["sum_obs"]  += int(obs_vec.sum())
                counts[key]["n"]        += len(obs_vec)

    return counts


def merge_counts(all_counts: list[dict]) -> dict:
    total = _empty_counts()
    for c in all_counts:
        for key, vals in c.items():
            if key in total:
                total[key]["sum_prob"] += vals["sum_prob"]
                total[key]["sum_obs"]  += vals["sum_obs"]
                total[key]["n"]        += vals["n"]
    return total


def counts_to_dataframe(counts: dict) -> pd.DataFrame:
    rows = []
    for (ptype, thr, grp), v in counts.items():
        sum_prob = v["sum_prob"]
        sum_obs  = v["sum_obs"]
        n        = v["n"]
        # FBI = mean_forecast_probability / obs_frequency
        mean_prob   = sum_prob / n        if n > 0           else np.nan
        obs_freq    = sum_obs  / n        if n > 0           else np.nan
        fbi         = mean_prob / obs_freq if obs_freq > 0   else np.nan
        rows.append({
            "type":           ptype,
            "threshold_mmh":  thr,
            "lead_time_group":grp,
            "sum_prob": round(sum_prob, 4),
            "sum_obs":  sum_obs,
            "n":        n,
            "mean_prob":  round(mean_prob,  6) if np.isfinite(mean_prob)  else np.nan,
            "obs_freq":   round(obs_freq,   6) if np.isfinite(obs_freq)   else np.nan,
            "fbi":        round(fbi,        4) if np.isfinite(fbi)        else np.nan,
        })
    return pd.DataFrame(rows)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute frequency bias at multiple precip rate thresholds."
    )
    parser.add_argument("start_date", help="Start forecast date YYYYMMDD")
    parser.add_argument("end_date",   help="End   forecast date YYYYMMDD")
    parser.add_argument("--season",   default=_CFG_SEASON,
                        help="Season string, e.g. 2024_2025  (overrides config.py)")
    parser.add_argument("--expver",   default=_CFG_EXPVER,
                        help="MARS expver, e.g. 0001  (overrides config.py)")
    parser.add_argument("--stream",   default=_CFG_STREAM,
                        help="MARS stream, e.g. enfo  (overrides config.py)")
    parser.add_argument("--raw-path", type=Path, default=None,
                        help="Explicit raw GRIB directory (overrides config PATH_RAW). "
                             "Supports both raw_{date}.grib and "
                             "Prectype_raw_VERIF_{date}.grib naming.")
    parser.add_argument("--prate-path", type=Path, default=None,
                        help="Directory containing separate prate GRIB files "
                             "(total_prec_VERIF_{date}.grib). Used for old archive "
                             "data where prate is stored separately from ptype.")
    parser.add_argument("--obs-source", choices=["eccodes", "metview"], default="eccodes",
                        help="SYNOP obs decoder: 'eccodes' (fast, all subcats, no WMO "
                             "station dedup) or 'metview' (obsfilter – matches the "
                             "original reference pipeline exactly, but slower and uses "
                             "whatever WMO station database is installed now).")
    args = parser.parse_args()

    # Rebuild RUN_TAG-dependent paths from CLI args
    run_tag = f"{args.season}_{args.stream}_{args.expver}"
    _cfg.RUN_TAG       = run_tag
    _cfg.PATH_RAW      = _cfg._BASE / "VERIF_ptype_all" / "raw"           / run_tag
    _cfg.PATH_FREQBIAS = _cfg._BASE / "VERIF_ptype_all" / "DATA_freqbias" / run_tag
    _cfg.PATH_SYNOP    = _cfg._BASE / "VERIF_ptype_all" / "SYNOP"         / args.season
    _cfg.PATH_FREQBIAS.mkdir(parents=True, exist_ok=True)

    # If an explicit raw dir was given, use it; otherwise fall back to derived PATH_RAW
    raw_dir   = args.raw_path   if args.raw_path   else _cfg.PATH_RAW
    prate_dir = args.prate_path if args.prate_path else None

    start_dt = datetime.strptime(args.start_date, "%Y%m%d")
    end_dt   = datetime.strptime(args.end_date,   "%Y%m%d")
    fdates   = []
    d = start_dt
    while d <= end_dt:
        fdates.append(int(d.strftime("%Y%m%d")))
        d += timedelta(days=1)

    print("=" * 65)
    print("Precip Type Freq-Bias – Step 1: Frequency bias analysis")
    print("=" * 65)
    print(f"Run tag    : {run_tag}")
    print(f"Raw GRIB   : {raw_dir}")
    if prate_dir:
        print(f"Prate dir  : {prate_dir}")
    print(f"Dates      : {args.start_date} → {args.end_date} ({len(fdates)} days)")
    print(f"Thresholds : {BIAS_THRESHOLDS} mm/h\n")

    # ── Phase A: Load SYNOP obs ────────────────────────────────────────────────
    # obs-source=eccodes: decode via eccodes + parquet cache (fast, no metview
    #   involved → no earthkit/metview conflict).  Reads ALL BUFR subcategories
    #   and deduplicates by exact (lat, lon, hour) — does NOT replicate
    #   Metview's WMO-station-database dedup, so station counts differ from
    #   the original Metview-based reference pipeline.
    # obs-source=metview: use mv.obsfilter exactly as the original reference
    #   Metview macros did.  Slower (no caching) but matches the original
    #   pipeline's station selection (modulo any WMO database drift).

    bias_steps = set(_STEP_TO_GROUP)
    needed: set[tuple[int, int]] = set()
    for fdate in fdates:
        for step in STEPS:
            if step not in bias_steps:
                continue
            needed.add(valid_date_hour(fdate, step))

    needed_dates = sorted({vd for vd, _ in needed})
    raw_arrays_cache: dict = {}

    if args.obs_source == "eccodes":
        print("Loading SYNOP obs (eccodes / parquet cache) ...")
        synop_df_cache: dict = {}   # {valid_date: DataFrame or None}
        for k, vd in enumerate(needed_dates, 1):
            bufr = find_synop_bufr(_cfg.PATH_SYNOP, vd)
            df   = read_synop_df(bufr) if bufr else None
            synop_df_cache[vd] = df
            status = "OK" if df is not None else "MISSING"
            print(f"  {k}/{len(needed_dates)}: {vd} {status}", flush=True)
        n_loaded = sum(1 for v in synop_df_cache.values() if v is not None)
        print(f"  {n_loaded}/{len(needed_dates)} SYNOP dates loaded\n")

        print("Extracting SYNOP obs arrays ...")
        for vd, vh in sorted(needed):
            df = synop_df_cache.get(vd)
            raw_arrays_cache[(vd, vh)] = (
                extract_synop_arrays_df(df, vh, AREA) if df is not None else None
            )
        n_extracted = sum(1 for v in raw_arrays_cache.values() if v is not None)
        print(f"  {n_extracted}/{len(needed)} (date, hour) pairs extracted\n")

    else:  # metview
        print("Loading SYNOP obs (metview obsfilter) ...")
        synop_raw_cache: dict = {}   # {valid_date: metview BUFR object or None}
        for k, vd in enumerate(needed_dates, 1):
            bufr = find_synop_bufr(_cfg.PATH_SYNOP, vd)
            raw  = read_synop_raw(bufr) if bufr else None
            synop_raw_cache[vd] = raw
            status = "OK" if raw is not None else "MISSING"
            print(f"  {k}/{len(needed_dates)}: {vd} {status}", flush=True)
        n_loaded = sum(1 for v in synop_raw_cache.values() if v is not None)
        print(f"  {n_loaded}/{len(needed_dates)} SYNOP dates loaded\n")

        print("Extracting SYNOP obs arrays (obsfilter) ...")
        for k, (vd, vh) in enumerate(sorted(needed), 1):
            raw = synop_raw_cache.get(vd)
            raw_arrays_cache[(vd, vh)] = (
                extract_synop_arrays(raw, vh, AREA) if raw is not None else None
            )
            if k % 50 == 0:
                print(f"  {k}/{len(needed)} pairs extracted ...", flush=True)
        n_extracted = sum(1 for v in raw_arrays_cache.values() if v is not None)
        print(f"  {n_extracted}/{len(needed)} (date, hour) pairs extracted\n")

    # ── Phase B: earthkit — orography ────────────────────────────────────────
    print("Loading orography ...")
    orog_tree, orog_values = build_orog_filter(PATH_OROG)
    print("  orog: OK\n")

    # ── Phase C: apply orog filter (pure numpy) ───────────────────────────────
    print("Applying orography filter to SYNOP obs ...")
    obs_cache: dict = {}   # {(valid_date, hour): DataFrame or None}
    for key, raw in raw_arrays_cache.items():
        if raw is None:
            obs_cache[key] = None
        else:
            obs_cache[key] = apply_orog_filter(raw, OROG_THRESHOLD_M, orog_tree, orog_values)
    n_obs = sum(1 for v in obs_cache.values() if v is not None and len(v) > 0)
    print(f"  {n_obs}/{len(obs_cache)} (date, hour) pairs have valid obs\n")

    t0 = datetime.now()
    all_counts = []

    for i, fdate in enumerate(fdates, 1):
        print(f"  [{i}/{len(fdates)}] processing {fdate} ...", flush=True)
        try:
            result = process_date(fdate, orog_tree, orog_values, raw_dir, prate_dir, obs_cache)
            if result:
                all_counts.append(result)
        except Exception as e:
            print(f"  WARNING {fdate}: {e}", flush=True)
        print(f"  [{i}/{len(fdates)}] done {fdate}", flush=True)

    print("\nAggregating counts ...")
    total_counts = merge_counts(all_counts)
    df_out = counts_to_dataframe(total_counts)

    suffix = "" if args.obs_source == "eccodes" else f"_{args.obs_source}"
    out_path = _cfg.PATH_FREQBIAS / f"freqbias_results{suffix}.csv"
    df_out.to_csv(out_path, index=False, float_format="%.4f")

    elapsed = (datetime.now() - t0).total_seconds()
    print(f"Results saved to {out_path}")
    print(f"Total time: {elapsed / 60:.1f} min")

    # Quick summary to stdout
    print("\nFBI summary (threshold → day1 group):")
    summary = df_out[df_out["lead_time_group"] == "day1"].pivot(
        index="type", columns="threshold_mmh", values="fbi"
    )
    print(summary.to_string(float_format="{:.3f}".format))


if __name__ == "__main__":
    main()
