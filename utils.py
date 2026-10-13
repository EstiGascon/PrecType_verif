"""
Shared utilities for precipitation type verification
=====================================================
Used by both Block A (verification) and Block B (frequency-bias analysis).

Nearest-gridpoint strategy
--------------------------
Metview's ``nearest_gridpoint(fieldset, geopoints)`` combines GRIB geometry
and geopoint coordinates in a single operation but must be called per field.
We replicate this efficiently with earthkit:

  1. ``load_ens_grib()`` reads the entire per-date GRIB file with
     earthkit.data and returns all ptype/prate fields as a single 2-D
     numpy array (n_fields × n_grid_points) alongside per-field step and
     member metadata.  The grid geometry (lats, lons) is extracted once.

  2. ``build_station_batch_index()`` collects the union of all station
     lat/lon pairs that will be needed across *all* steps for one forecast
     date, then calls ``KDTree.query()`` a **single time** for the full
     batch.  The returned ``inverse_idx`` array maps each per-step station
     back to its position in the batch result.

  3. Per-step extraction is then pure numpy fancy-indexing — no further
     tree queries, no python loops over members.

This reduces the number of KDTree queries from  N_steps (56)  to  1  per
forecast date, and avoids loading the same GRIB metadata field-by-field.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree as KDTree


# ── Date / time helpers ───────────────────────────────────────────────────────

def valid_date_hour(fdate: int, step: int) -> tuple[int, int]:
    """Return (valid_date as YYYYMMDD int, valid_hour 0-23) for a forecast step."""
    fdate_dt = datetime.strptime(str(fdate), "%Y%m%d")
    valid_dt = fdate_dt + timedelta(hours=step)
    return int(valid_dt.strftime("%Y%m%d")), valid_dt.hour


def yyyymmdd_to_hyphen(d: int) -> str:
    """20241112 → '2024-11-12'"""
    s = str(d)
    return f"{s[:4]}-{s[4:6]}-{s[6:]}"


# ── SYNOP file lookup ─────────────────────────────────────────────────────────

def find_synop_bufr(path_synop: Path, valid_date: int) -> Optional[Path]:
    """
    Locate BUFR file for valid_date.
    Supports new naming (SYNOP_YYYY-MM-DD.bufr) and legacy (SYNOP_mannual_YYYYMMDD.bufr).
    """
    vd_str    = str(valid_date)
    vd_hyphen = yyyymmdd_to_hyphen(valid_date)
    candidates = [
        path_synop / f"SYNOP_{vd_hyphen}.bufr",
        path_synop / f"SYNOP_mannual_{vd_str}.bufr",
        path_synop / f"SYNOP_mannual_{vd_hyphen}.bufr",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


# ── GRIB loading (earthkit.data) ─────────────────────────────────────────────

# Old GRIB files may store precip rate under a different paramId (228219)
_PRATE_PARAM_ALIASES = {260048, 228219}


def _fieldlist_from_path(path: Path):
    """Return an earthkit FieldList from a file path."""
    import earthkit.data as ekd
    return ekd.from_source("file", str(path)).to_fieldlist()


def _filter_by_param(fl, param_ids) -> list:
    """Filter a FieldList to fields whose paramId is in param_ids (a set/list)."""
    param_ids = set(param_ids)
    return [f for f in fl if f.metadata("paramId") in param_ids]


def _grid_lats_lons(field) -> tuple[np.ndarray, np.ndarray]:
    """Extract 1-D lat/lon arrays from an earthkit Field using geography methods."""
    lats = np.array(field.geography.latitudes()).flatten()
    lons = np.array(field.geography.longitudes()).flatten()
    return lats, lons


def load_ens_grib(
    grib_path: Path,
    param_ptype: int,
    param_prate: int,
    prate_path: Optional[Path] = None,
) -> tuple[
    np.ndarray,   # ptype_vals  : (n_fields, n_grid)
    np.ndarray,   # prate_vals  : (n_fields, n_grid)  – normalized to mm/h
    np.ndarray,   # steps       : (n_fields,)
    np.ndarray,   # grid_lats   : (n_grid,)
    np.ndarray,   # grid_lons   : (n_grid,)
]:
    """
    Load one per-date ENS GRIB file using earthkit.data.

    Supports two layouts:
    - Combined: both ptype and prate in grib_path (new pipeline output).
    - Split:    ptype in grib_path, prate in prate_path (old archive format).

    The prate paramId can be either 260048 (new) or 228219 (old alias).

    Returns
    -------
    ptype_vals  : float32 array  (n_fields, n_grid)
    prate_vals  : float32 array  (n_fields, n_grid), normalized to mm/h
                 regardless of source paramId (see conversion note below)
    steps       : int16  array   (n_fields,) – forecast step for each field
    grid_lats   : float64 array  (n_grid,)
    grid_lons   : float64 array  (n_grid,)
    """
    fl_main = _fieldlist_from_path(grib_path)

    # Extract ptype fields (always in grib_path)
    ptype_fields = _filter_by_param(fl_main, {param_ptype})
    if not ptype_fields:
        raise ValueError(f"GRIB file {grib_path} missing paramId={param_ptype}")

    # Extract prate fields – from prate_path if given, otherwise from grib_path
    prate_src = _fieldlist_from_path(prate_path) if prate_path else fl_main
    prate_fields = _filter_by_param(prate_src, _PRATE_PARAM_ALIASES | {param_prate})
    if not prate_fields:
        raise ValueError(
            f"No prate field (paramIds {_PRATE_PARAM_ALIASES | {param_prate}}) "
            f"found in {'prate_path' if prate_path else 'grib_path'}"
        )

    if len(ptype_fields) != len(prate_fields):
        raise ValueError(
            f"ptype field count ({len(ptype_fields)}) != "
            f"prate field count ({len(prate_fields)})"
        )

    # Grid geometry from first ptype field
    grid_lats, grid_lons = _grid_lats_lons(ptype_fields[0])

    # 2-D arrays: (n_fields, n_grid_points)
    ptype_vals = np.array([f.to_numpy(flatten=True) for f in ptype_fields],
                          dtype=np.float32)
    prate_vals = np.array([f.to_numpy(flatten=True) for f in prate_fields],
                          dtype=np.float32)

    # Normalize prate to mm/h.
    # paramId 260048 (tprate, current MARS retrieval) is genuinely native
    # kg m-2 s-1 (e.g. max ~0.003 for a realistic rain event) -> x3600 = mm/h.
    # paramId 228219 (lsrr, old archive alias) was retrieved via a MARS-derived
    # field with formula="...*3600" baked in at retrieval time, so its raw
    # values are already mm/h (e.g. max ~15-20) despite carrying kg m-2 s-1
    # units metadata. Do NOT convert those again.
    prate_pids = {int(f.metadata("paramId")) for f in prate_fields}
    if len(prate_pids) != 1:
        raise ValueError(f"Mixed prate paramIds within one GRIB file: {prate_pids}")
    prate_pid = next(iter(prate_pids))
    if prate_pid == 260048:
        prate_vals = prate_vals * 3600.0

    # Step metadata
    steps_pt = np.array([int(f.metadata("step")) for f in ptype_fields], dtype=np.int16)
    steps_pr = np.array([int(f.metadata("step")) for f in prate_fields], dtype=np.int16)

    if not np.array_equal(steps_pt, steps_pr):
        raise ValueError("ptype and prate fields have mismatched step sequences")

    return ptype_vals, prate_vals, steps_pt, grid_lats, grid_lons


# ── Batch nearest-gridpoint index ─────────────────────────────────────────────

def build_station_batch_index(
    grid_lats: np.ndarray,
    grid_lons: np.ndarray,
    step_obs: dict,            # { step: pd.DataFrame with columns lat, lon, ... }
) -> tuple[
    np.ndarray,   # grid_idx_for_unique : (n_unique_stations,) grid indices
    np.ndarray,   # inverse_idx         : maps concat-of-all-stations → unique row
    list,         # n_per_step          : number of stations per step (same order as step_obs)
]:
    """
    Replicate Metview's ``nearest_gridpoint(fieldset, geopoints)`` for the
    full set of stations across *all* steps in a single KDTree query.

    Strategy
    --------
    1. Concatenate the (lat, lon) coordinates of every station from every
       step into one array.
    2. Call ``np.unique(..., return_inverse=True)`` to deduplicate:
       unique_coords has  n_unique ≤ total  rows;
       inverse_idx maps each row of the concatenated array back to its
       position in unique_coords.
    3. Query the forecast KDTree **once** for the n_unique locations.
    4. The caller reconstructs per-step grid indices with:

           cursor = 0
           for step, n_st in zip(step_obs, n_per_step):
               step_inv  = inverse_idx[cursor:cursor + n_st]
               grid_idx  = grid_idx_for_unique[step_inv]   # (n_st,)
               cursor   += n_st

    Parameters
    ----------
    grid_lats, grid_lons : 1-D arrays matching the GRIB grid layout
    step_obs             : ordered dict {step: obs_df}, same order used later

    Returns
    -------
    grid_idx_for_unique : array(n_unique,) of flat GRIB grid indices
    inverse_idx         : array(n_total,)  mapping concat positions → unique row
    n_per_step          : list(int)        number of stations in each step entry
    """
    n_per_step = [len(df) for df in step_obs.values()]

    all_lats = np.concatenate([df["lat"].values for df in step_obs.values()])
    all_lons = np.concatenate([df["lon"].values for df in step_obs.values()])
    all_coords = np.column_stack([all_lats, all_lons])

    # Deduplicate station locations across all steps.
    # unique_coords[k] corresponds EXACTLY to every row i where
    # inverse_idx[i] == k (this is the documented np.unique guarantee) --
    # do NOT reorder unique_coords afterwards without recomputing
    # inverse_idx to match, or the two will silently go out of sync and
    # every station will be paired with the WRONG grid point.
    unique_coords, inverse_idx = np.unique(all_coords, axis=0, return_inverse=True)
    inverse_idx = inverse_idx.reshape(-1)  # some numpy versions return (n,1)

    # ONE KDTree query for all unique station locations
    tree = KDTree(np.column_stack([grid_lats, grid_lons]))
    _, grid_idx_for_unique = tree.query(unique_coords)

    return grid_idx_for_unique, inverse_idx, n_per_step


# ── Orography filter ──────────────────────────────────────────────────────────

def build_orog_filter(orog_path: Path) -> tuple[KDTree, np.ndarray]:
    """
    Load orography GRIB and build a KDTree for fast model-elevation lookup.

    Returns:
        tree:        KDTree built from grid lat/lon pairs
        orog_values: 1-D array of model surface elevation (m) at each grid point
    """
    import earthkit.data as ekd

    ds = _fieldlist_from_path(orog_path)
    field = ds[0]
    grid_lats, grid_lons = _grid_lats_lons(field)
    orog_values = field.to_numpy(flatten=True).flatten()

    coords = np.column_stack([grid_lats, grid_lons])
    tree = KDTree(coords)
    return tree, orog_values


# ── BUFR reading (via Metview Python API) ────────────────────────────────────

def _mv():
    """Import metview with batch-mode env vars set before first import."""
    import os
    os.environ.setdefault("METVIEW_BATCH_MODE", "1")
    os.environ.setdefault("METVIEW_NO_CHECK_HOME", "1")
    import metview as mv
    return mv


def read_synop_raw(bufr_path: Path):
    """Load SYNOP BUFR file as a Metview data object (cached by caller)."""
    try:
        mv = _mv()
        return mv.read(str(bufr_path))
    except Exception:
        return None


# ── SYNOP parquet cache (eccodes BUFR decode) ────────────────────────────────
#
# pdbufr only decodes BUFR subsets that contain ALL requested columns, so it
# misses stations whose ww lives in a different message template.  eccodes
# iterates every message regardless of template and recovers all stations.
# The result is cached as a parquet for instant reuse.
#
# Station identification: the old Metview macro's obsfilter() does NOT filter
# by dataSubCategory -- it processes every BUFR message with the requested
# WMO parameter, regardless of subcategory (verified empirically: obsfilter
# extracts valid stations even from subcat=178-only data).  So all 6
# subcategories retrieved by MARS (1, 2, 170, 172, 176, 178) are read here.
# The same physical station is often reported redundantly across subcats
# (e.g. international GTS exchange vs regional exchange vs automated feed)
# with slightly different lat/lon rounding, so rows are deduplicated by a
# station identifier rather than by lat/lon -- classic WMO block+station
# number where available (subcats 1, 2, 170, 172, 176), falling back to the
# WIGOS identifier for automated stations (subcat 178) that lack a classic
# WMO number, mirroring how Metview's obsfilter resolves stations via its
# WMO/WIGOS database.
KEEP_SUBCAT = {1, 2, 170, 172, 176}
#
# Workflow:
#   read_synop_df(bufr_path)             → DataFrame (all hours, global)
#   extract_synop_arrays_df(df, hour, area) → dict of numpy arrays (QC applied)
#   apply_orog_filter(arrays, ...)       → final DataFrame (orog-filtered)


def synop_parquet_path(bufr_path: Path) -> Path:
    """Return the parquet cache path for a given BUFR file."""
    return bufr_path.with_name(bufr_path.stem + "_v2.parquet")


def read_synop_df(bufr_path: Path) -> Optional[pd.DataFrame]:
    """
    Load full-day SYNOP observations as a DataFrame via eccodes.

    Reads all BUFR messages whose dataSubCategory is in KEEP_SUBCAT (manual /
    WMO-registered stations only: subcats 1, 2, 170, 172, 176 -- automated
    stations, subcat 178, are deliberately excluded).  The same physical
    station is often reported redundantly across several subcats with
    slightly different lat/lon rounding, so rows are deduplicated by a
    station identifier (classic WMO block+station number) rather than by
    lat/lon.  When duplicates exist for the same (station_id, hour), the row
    with a valid present-weather value is kept in preference to a missing
    one, and among those, the row with a valid station height is preferred
    (a stable sort is used so this tie-break is deterministic regardless of
    how many rows are in the table).  Result is cached as a parquet file
    alongside the BUFR.

    Returns a DataFrame with columns: lat, lon, hour (int16), ht, ww (float32).
    Returns None on failure.
    """
    import eccodes

    cache = synop_parquet_path(bufr_path)
    if cache.exists():
        return pd.read_parquet(cache)

    MISS = 1e10
    MISS_INT = 2147483647
    all_lat, all_lon, all_hr, all_ht, all_ww = [], [], [], [], []
    all_wmo = []

    def _get(buf, key, n):
        try:
            v = eccodes.codes_get_array(buf, key).astype(float)
            return v if len(v) == n else np.full(n, v[0], dtype=float)
        except Exception:
            return np.full(n, np.nan)

    try:
        with open(bufr_path, "rb") as f:
            while True:
                buf = eccodes.codes_bufr_new_from_file(f)
                if buf is None:
                    break
                try:
                    subcat = eccodes.codes_get(buf, "dataSubCategory")
                    if subcat not in KEEP_SUBCAT:
                        eccodes.codes_release(buf)
                        continue
                    eccodes.codes_set(buf, "unpack", 1)
                    lats = eccodes.codes_get_array(buf, "latitude").astype(float)
                    lons = eccodes.codes_get_array(buf, "longitude").astype(float)
                except Exception:
                    eccodes.codes_release(buf)
                    continue

                n = len(lats)
                hrs  = _get(buf, "hour", n)
                hts  = _get(buf, "heightOfStationGroundAboveMeanSeaLevel", n)
                wws  = _get(buf, "presentWeather", n)
                blk  = _get(buf, "blockNumber", n)
                stn  = _get(buf, "stationNumber", n)
                eccodes.codes_release(buf)

                for arr in (lats, lons, hts, wws):
                    arr[np.abs(arr) > MISS] = np.nan
                for arr in (blk, stn):
                    arr[(np.isnan(arr)) | (arr >= MISS_INT)] = np.nan

                wmo_id = blk * 1000 + stn  # NaN propagates if either missing

                all_lat.append(lats); all_lon.append(lons)
                all_hr.append(hrs);   all_ht.append(hts)
                all_ww.append(wws);   all_wmo.append(wmo_id)
    except Exception:
        return None

    if not all_lat:
        return None

    df = pd.DataFrame({
        "lat":      np.concatenate(all_lat).astype("float32"),
        "lon":      np.concatenate(all_lon).astype("float32"),
        "hour":     np.concatenate(all_hr).astype("float32"),
        "ht":       np.concatenate(all_ht).astype("float32"),
        "ww":       np.concatenate(all_ww).astype("float32"),
        "wmo_id":   np.concatenate(all_wmo),
    })
    df = df.dropna(subset=["lat", "lon", "hour", "wmo_id"])
    df["hour"] = df["hour"].astype("int16")
    # Prefer rows with a valid present-weather value when the same station
    # (wmo_id, hour) is reported redundantly across multiple subcats
    # (e.g. subcat=1 national-exchange copies often lack station height,
    # while subcat=170/172/176 regional copies of the same station have it).
    # Sort on both flags together with a stable sort so the "best" row is
    # picked deterministically regardless of how many other rows are in the
    # table (an unstable sort's tie-break order can otherwise depend on
    # array size, silently flipping which duplicate survives).
    df["_has_ww"] = (df["ww"].notna() & (df["ww"] <= 100)).astype("int8")
    df["_has_ht"] = df["ht"].notna().astype("int8")
    df = df.sort_values(
        ["_has_ww", "_has_ht"], ascending=False, kind="mergesort"
    ).drop_duplicates(subset=["wmo_id", "hour"], keep="first")
    df = df.drop(columns=["_has_ww", "_has_ht", "wmo_id"])
    df.to_parquet(cache, index=False)
    return df


def extract_synop_arrays_df(
    synop_df: pd.DataFrame,
    valid_hour: int,
    area: list,
) -> Optional[dict]:
    """
    Filter a pre-loaded SYNOP DataFrame to one (hour, area) and apply QC.

    Parameters
    ----------
    synop_df   : DataFrame returned by read_synop_df
    valid_hour : UTC hour to select (0-23)
    area       : [N, W, S, E]

    Returns
    -------
    dict with keys 'lat', 'lon', 'ww', 'ht' (1-D float64 numpy arrays)
    or None if no valid observations.
    """
    N, W, S, E = area
    sub = synop_df[
        (synop_df["hour"] == valid_hour) &
        (synop_df["lat"]  >= S) & (synop_df["lat"]  <= N) &
        (synop_df["lon"]  >= W) & (synop_df["lon"]  <= E)
    ]
    if sub.empty:
        return None

    ww   = sub["ww"].to_numpy(dtype=float)
    ht   = sub["ht"].to_numpy(dtype=float)
    lats = sub["lat"].to_numpy(dtype=float)
    lons = sub["lon"].to_numpy(dtype=float)

    # Quality control: keep valid SYNOP present weather codes (0–100).
    # ww > 100 are BUFR extended/automated station codes; Metview obsfilter
    # removes these via obs_ > 100 → Miss.
    valid_mask = (
        ~np.isin(ww, [508, 509, 510, 511]) &
        np.isfinite(ww) & (ww <= 100) &
        np.isfinite(ht)
    )
    lats, lons, ww, ht = lats[valid_mask], lons[valid_mask], ww[valid_mask], ht[valid_mask]
    if len(ww) == 0:
        return None

    return {"lat": lats, "lon": lons, "ww": ww, "ht": ht}


def extract_synop_arrays(
    synop_raw,
    valid_hour: int,
    area: list,
) -> Optional[dict]:
    """
    Run Metview obsfilter and extract raw arrays for one (BUFR, hour, area).

    This is the METVIEW-ONLY phase — call this for all dates/hours BEFORE
    touching any GRIB files with earthkit.  The orography filter is applied
    separately via ``apply_orog_filter`` once the earthkit KDTree is ready.

    Parameters
    ----------
    synop_raw  : Metview BUFR object (from read_synop_raw)
    valid_hour : UTC hour to extract (0-23)
    area       : [N, W, S, E]

    Returns
    -------
    dict with keys 'lat', 'lon', 'ww', 'ht' (all 1-D float64 numpy arrays)
    or None if no valid observations found.
    """
    mv = _mv()

    try:
        obs_ww = mv.obsfilter(
            output="geopoints",
            parameter=20003,            # present weather (WMO descriptor 020003)
            time=valid_hour,
            location_filter="area",
            area=area,
            data=synop_raw,
        )
        obs_ht = mv.obsfilter(
            output="geopoints",
            parameter=7001,             # station height (WMO descriptor 007001)
            time=valid_hour,
            location_filter="area",
            area=area,
            data=synop_raw,
        )
    except Exception:
        return None

    # Align heights to the same stations as ww
    obs_ht = mv.subsample(obs_ht, obs_ww)

    try:
        ww   = np.asarray(mv.values(obs_ww),    dtype=float)
        ht   = np.asarray(mv.values(obs_ht),    dtype=float)
        lats = np.asarray(mv.latitudes(obs_ww),  dtype=float)
        lons = np.asarray(mv.longitudes(obs_ww), dtype=float)
    except Exception:
        return None

    if len(ww) == 0:
        return None

    # Quality control: remove BUFR missing codes and out-of-range values
    valid = ~np.isin(ww, [508, 509, 510, 511]) & (ww <= 100) & np.isfinite(ht)
    lats, lons, ww, ht = lats[valid], lons[valid], ww[valid], ht[valid]
    if len(ww) == 0:
        return None

    return {"lat": lats, "lon": lons, "ww": ww, "ht": ht}


def apply_orog_filter(
    raw_arrays: dict,
    orog_threshold_m: float,
    orog_tree: KDTree,
    orog_values: np.ndarray,
) -> Optional[pd.DataFrame]:
    """
    Apply orography filter to pre-extracted SYNOP arrays (pure numpy).

    Call this AFTER the earthkit KDTree has been built from the orography GRIB.

    Parameters
    ----------
    raw_arrays       : dict returned by extract_synop_arrays
    orog_threshold_m : max |station_elev – model_elev| (m)
    orog_tree        : KDTree of model grid lat/lon pairs
    orog_values      : model surface elevation at each grid point (m)

    Returns
    -------
    DataFrame with columns lat, lon, elevation, ww  or  None.
    """
    lats = raw_arrays["lat"]
    lons = raw_arrays["lon"]
    ww   = raw_arrays["ww"]
    ht   = raw_arrays["ht"]

    _, grid_idx = orog_tree.query(np.column_stack([lats, lons]))
    orog_ok = np.abs(ht - orog_values[grid_idx]) < orog_threshold_m
    lats, lons, ww, ht = lats[orog_ok], lons[orog_ok], ww[orog_ok], ht[orog_ok]
    if len(ww) == 0:
        return None

    return pd.DataFrame({"lat": lats, "lon": lons, "elevation": ht, "ww": ww.astype(int)})


def filter_synop_obs(
    synop_raw,
    valid_hour: int,
    area: list,
    orog_threshold_m: float,
    orog_tree: KDTree,
    orog_values: np.ndarray,
) -> Optional[pd.DataFrame]:
    """
    Combined Metview obsfilter + orography filter (legacy single-call interface).

    Prefer using extract_synop_arrays + apply_orog_filter separately to avoid
    the earthkit/metview eccodes conflict (metview must not be called after
    earthkit has loaded a GRIB file in the same process).
    """
    raw = extract_synop_arrays(synop_raw, valid_hour, area)
    if raw is None:
        return None
    return apply_orog_filter(raw, orog_threshold_m, orog_tree, orog_values)


# ── SYNOP classification ──────────────────────────────────────────────────────

def classify_synop(obs_values: np.ndarray, synop_codes: dict) -> dict[str, np.ndarray]:
    """
    Binary classification of SYNOP ww codes into precipitation types.

    Returns a dict {ptype: np.int8 array of 0/1 for each observation}.
    """
    result: dict[str, np.ndarray] = {}
    for ptype, codes in synop_codes.items():
        if len(codes) == 0:
            result[ptype] = np.zeros(len(obs_values), dtype=np.int8)
        else:
            result[ptype] = np.isin(obs_values, np.asarray(codes, dtype=int)).astype(np.int8)
    return result
