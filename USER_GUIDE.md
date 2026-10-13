# Precipitation Type Verification – User Guide

## Overview

This tool verifies probabilistic precipitation type forecasts from the IFS
ensemble system (ENS) against SYNOP surface observations, and produces
forecast products (point meteograms and maps) for case studies.  It is
structured in two verification pipelines, a set of season-comparison plots,
and a product-plotting folder, all sharing one configuration file:

```
PrecType_verif/
│
├── config.py                    ← single place to change season / expver / paths / thresholds
├── utils.py                     ← shared GRIB/BUFR/interpolation helpers
├── USER_GUIDE.md
│
├── scripts/
│   ├── retrieval/               ← Step 0 – retrieve raw data from MARS
│   │   ├── retrieve_synop.ksh
│   │   ├── mars_retrieve.ksh
│   │   ├── submit_parallel_mars.ksh
│   │   ├── submit_retry_pf_daily.ksh   (recovery of failed monthly requests)
│   │   └── retry_pf_day.ksh            (SLURM array worker for the above)
│   │
│   ├── prectype_verif/          ← Probabilistic verification pipeline
│   │   ├── 01_prepare_dataset.py
│   │   ├── 02_compute_scores.py
│   │   ├── run_pipeline.sh      (SLURM orchestrator)
│   │   ├── compare_seasons_aroc.py         ┐
│   │   ├── compare_seasons_reliability.py  │ season comparisons and
│   │   ├── plot_aroc_all_types.py          │ extra diagnostic plots
│   │   ├── plot_reliability_all_types.py   │ (section 6)
│   │   └── plot_cases_per_season.py        ┘
│   │
│   └── prectype_freqbias/       ← Precipitation rate threshold calibration
│       ├── compute_freqbias.py
│       ├── plot_freqbias.py
│       └── run_freqbias.sh      (SLURM orchestrator)
│
├── Products_plotting/           ← forecast products for case studies (section 7)
│   ├── ptype_probability_meteogram.ipynb
│   ├── ptype_most_likely_map.ipynb
│   └── run_case_20170216.py     (example: map → hotspot → meteogram)
│
├── verification_results/
│   └── <RUN_TAG>/               ← e.g. 2024_2025_enfo_0001/
│       ├── aroc_by_day.png
│       ├── reliability_*.png
│       ├── summary_scores.csv
│       └── freqbias/
├── logs/                        ← SLURM stdout / stderr
└── archive/                     ← superseded scripts (read-only reference)
    ├── old_notebooks/
    ├── old_ksh/
    └── old_metview_r/
```

All raw and intermediate data is stored under `/ec/vol/enscal/VERIF_PrecipType/`
and **must not** be placed in this folder.

### Run tag

Every run is identified by a **RUN_TAG** of the form:

    {SEASON}_{STREAM}_{EXPVER}    e.g.  2024_2025_enfo_0001

This tag is embedded in every data path and output directory.  Runs for
different seasons, experiment versions, or streams therefore **never
overwrite each other's data or results**.

---

## Quick start for a new season / experiment

### 1. Edit `config.py`

Change the four lines in the "Run identity" block:

```python
SEASON     = "2025_2026"    # season to verify
START_DATE = "20251101"     # first forecast date
END_DATE   = "20260415"     # last  forecast date
EXPVER     = "0001"         # "0001" for operational; "xxxx" for research
STREAM     = "enfo"         # "enfo" for ensemble forecast
```

All paths and output directories are derived automatically.  Nothing else
needs editing for a standard seasonal run.

Two more settings in the same file may need attention:

- `EXCLUDE_DATES` — forecast dates skipped by `01_prepare_dataset.py`, e.g.
  dates whose ensemble could not be retrieved completely (damaged tape).
- `N_MEMBERS` — set automatically to 50 from IFS Cycle 50r1 (12 May 2026),
  when the control forecast was removed from the ENFO stream, and 51 before.

---

### 2. Retrieve SYNOP observations

```bash
ksh scripts/retrieval/retrieve_synop.ksh 2025_2026
```

Downloads daily BUFR files to
`.../VERIF_ptype_all/SYNOP/2025_2026/SYNOP_YYYY-MM-DD.bufr`.
Already-existing files are skipped automatically.
SYNOP files are shared across all expvers of the same season.

---

### 3. Retrieve ENS forecast GRIB

```bash
ksh scripts/retrieval/submit_parallel_mars.ksh 2025_2026 0001 enfo
```

Usage: `submit_parallel_mars.ksh [SEASON] [EXPVER] [STREAM]`

Submits one SLURM job per monthly chunk. Each job writes one GRIB file per
forecast date to:
`.../VERIF_ptype_all/raw/2025_2026_enfo_0001/raw_YYYYMMDD.grib`

Both parameters — **precip type (260015)** and **precip rate (260048)** — are
retrieved in a single MARS session per chunk to minimise tape staging time.

Monitor with `squeue -u $USER`.

---

### 4. `prectype_verif` – Probabilistic verification pipeline

```bash
ksh scripts/prectype_verif/run_pipeline.sh 2025_2026 0001 enfo
```

Usage: `run_pipeline.sh [SEASON] [EXPVER] [STREAM]`

This submits:

1. **`01_prepare_dataset.py`** — one SLURM job per monthly chunk.  
   For each forecast date it:
   - Loads raw ENS GRIB with earthkit.data (single batch read per date).
   - Reads SYNOP BUFR and filters stations by area + orography (±200 m).
   - Interpolates all 51 members to station locations in **one** batch KDTree query per date.
   - Applies per-type precipitation rate thresholds (from `PRECIP_THRESHOLD` in `config.py`).
   - Saves matched obs/forecast pairs to  
     `.../DATA_preVerif/2025_2026_enfo_0001/matched_pairs_YYYYMMDD.parquet`

2. **`02_compute_scores.py`** — runs after all prepare jobs finish.  
   Produces in `verification_results/2025_2026_enfo_0001/`:

   | File | Contents |
   |---|---|
   | `aroc_by_day.png` | AROC curves vs forecast day |
   | `reliability_<type>.png` | Reliability diagrams, days 1/3/5/7 |
   | `brier_scores_by_day.png` | Brier score + Brier Skill Score |
   | `contingency_metrics.png` | POD / FAR / CSI / ETS vs probability threshold |
   | `sharpness_analysis.png` | Forecast probability histograms |
   | `cost_loss_analysis.png` | Economic value curves |
   | `confusion_matrix.png` | Multi-category type assignment |
   | `summary_scores.csv` | All scores as a table |

Run interactively (e.g. for testing a short period):

```bash
cd /home/moeg/PrecType_verif
python scripts/prectype_verif/01_prepare_dataset.py 20251101 20251130 \
    --season 2025_2026 --expver 0001 --stream enfo --workers 4
python scripts/prectype_verif/02_compute_scores.py \
    --season 2025_2026 --expver 0001 --stream enfo
```

---

### 5. `prectype_freqbias` – Precipitation rate threshold calibration

Run this **once per model cycle** to determine the optimal precipitation rate
threshold for each type (the threshold where FBI ≈ 1).

```bash
ksh scripts/prectype_freqbias/run_freqbias.sh 2025_2026 0001 enfo
```

Usage: `run_freqbias.sh [SEASON] [EXPVER] [STREAM]`

This submits:

1. **`compute_freqbias.py`** — computes Frequency Bias Index (FBI) for five
   threshold candidates (0.02, 0.05, 0.07, 0.10, 0.12 mm/h) at three
   lead-time groups (day 1, day 2, day 5).  
   Output: `.../DATA_freqbias/2025_2026_enfo_0001/freqbias_results.csv`

2. **`plot_freqbias.py`** — plots FBI vs threshold per lead-time group and
   prints the optimal threshold per type.  
   Output: `verification_results/2025_2026_enfo_0001/freqbias/`

After running, update `PRECIP_THRESHOLD` in `config.py` with the printed
values, then re-run `prectype_verif`.

---

### 6. Season comparisons and extra diagnostic plots

These scripts read the `matched_pairs_*.parquet` files of one or more runs
(any directory under `DATA_preVerif/`) and do not need the pipeline to be
re-run.  Pass seasons in chronological order; the last one is drawn as the
"current" run.

```bash
D=/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/DATA_preVerif
OUT=verification_results/2025_2026_enfo_0001

# AROC by forecast day, one curve per season
python3 scripts/prectype_verif/compare_seasons_aroc.py \
    --series $D/2021_2022 "2021-2022" \
    --series $D/2024_2025_49r1 "2024-2025" \
    --series $D/2025_2026_enfo_0001 "2025-2026" \
    --out $OUT/aroc_by_day_season_comparison.png

# Reliability (all steps combined), one curve per season; --type for a single type
python3 scripts/prectype_verif/compare_seasons_reliability.py \
    --series $D/2021_2022 "2021-2022" --series $D/2025_2026_enfo_0001 "2025-2026" \
    --out $OUT/reliability_season_comparison.png

# All precipitation types on one axes, for one run
python3 scripts/prectype_verif/plot_aroc_all_types.py \
    --data-dir $D/2025_2026_enfo_0001 --label "2025-2026" --out $OUT/aroc_by_day_all_types.png
python3 scripts/prectype_verif/plot_reliability_all_types.py \
    --data-dir $D/2025_2026_enfo_0001 --label "2025-2026" --out $OUT/reliability_all_types.png

# Number of observed cases per season (--metric total) or days with >=1 case (--metric days)
python3 scripts/prectype_verif/plot_cases_per_season.py \
    --series $D/2020_2021 "2020-2021" --series $D/2025_2026_enfo_0001 "2025-2026" \
    --types freezrain --metric days --out $OUT/freezrain_days_per_season.png
```

Before interpreting season-to-season differences, read
[Model cycle changes that affect results](#model-cycle-changes-that-affect-results).

---

### 7. `Products_plotting` – forecast products for case studies

Two Jupyter notebooks, ported from the original Metview macros, retrieve ENS
data directly from MARS with `earthkit.data` and plot with `earthkit.plots`.
They do **not** depend on the verification pipeline.  Open a notebook, edit
the *User parameters* cell, and run all cells.

Both notebooks:

- cache the downloaded GRIB in `OUT_DIR` (default `/perm/moeg/Products_plotting/`),
  so re-running with the same date/area only redraws the plot;
- split the MARS request into parallel chunks (`N_PARALLEL`, default 8);
- detect the number of members from the data (51 before 50r1, 50 after);
- use the total precipitation rate (260048) when it is archived and otherwise
  the sum of its four components (see
  [Model cycle changes](#model-cycle-changes-that-affect-results)).

#### `ptype_probability_meteogram.ipynb` — point meteogram

For one location and one ENS run: at each step, the percentage of members
forecasting each precipitation type, split into three rate classes
(type threshold–0.2, 0.2–1, >1 mm/h), as stacked bars.

| Parameter | Meaning |
|---|---|
| `FDATE`, `TIME`, `EXPVER` | ENS run (default: yesterday 00 UTC, operational) |
| `DAYS`, `MIN_STEP` | forecast length and finest step (1/3/6/12 h); ENS is hourly to T+90, 3-hourly to T+144, 6-hourly after |
| `LAT`, `LON`, `CITY`, `COUNTRY` | location and title labels |
| `AREA` | download box; `None` = 1° around the point. A larger box costs the same MARS time and allows several cities from one download |
| `THRESHOLDS` | lower rate limit (mm/h) of the "low" class per type |

Output: `OUT_DIR/Prob_prec_type_<CITY>_<date><time>_e<expver>_<days>d_<step>s.png`,
plus a table of the probabilities shown in the notebook.

#### `ptype_most_likely_map.ipynb` — most likely precipitation type map

For each step: colours show the most probable type and its probability
(<50, 50–70, >70 %) where the probability of precipitation is ≥ 50 %; greys
show a probability of precipitation of 10–30 % and 30–50 %.  The tie-breaking
rules between types are those of the original macro.

| Parameter | Meaning |
|---|---|
| `FDATE`, `TIME`, `EXPVER`, `STEPS` | ENS run and list of steps (one PNG per step) |
| `MAP_CORNERS` | polar-stereographic map given by lower-left / upper-right `[lat, lon, lat, lon]`; the download area is derived from it |
| `GRID` | regular grid (°) to which ENS is interpolated by nearest neighbour (default 0.1) |
| `THRESHOLDS` | minimum rate (mm/h) for a member to count for each type |

Output: `OUT_DIR/Prob_prec_type_map<date>_<time>_<step>.png`.

The last section of the notebook, *Find locations with the highest probability
of a precipitation type*, ranks grid points by the probability of
`TARGET_TYPE` at `TARGET_STEP`, keeps points at least `MIN_SEPARATION_KM` apart
and names the nearest town.  Copy the chosen `lat`/`lon` into the meteogram
notebook.

#### Running a full case without opening the notebooks

`Products_plotting/run_case_20170216.py` shows how to chain both notebooks
from a script: it draws the T+24 map for 16 Feb 2017 00 UTC, picks the
freezing-rain hotspot and draws the 3-hourly meteogram there.  Copy it and
change the parameter replacements for another case.  For archived (tape)
dates run it in the background, as retrieval can take a long time:

```bash
nohup python3 Products_plotting/run_case_20170216.py > logs/products_case.log 2>&1 &
```

---

## Comparing two runs

Because each run has a unique output directory, you can compare them directly:

```bash
ls verification_results/
# 2023_2024_enfo_0001/
# 2024_2025_enfo_0001/
# 2024_2025_enfo_xxxx/   ← research experiment
```

To load both into a notebook for comparison:

```python
import pandas as pd
df_op  = pd.read_csv("verification_results/2024_2025_enfo_0001/summary_scores.csv")
df_exp = pd.read_csv("verification_results/2024_2025_enfo_xxxx/summary_scores.csv")
```

---

## Dependencies

| Library | Purpose |
|---|---|
| `earthkit-data` | GRIB reading and MARS retrieval (uses the local `mars` client) |
| `earthkit-plots`, `cartopy` | Product plots (meteogram, maps) |
| `metview` (Python API) | BUFR reading (`obsfilter`) |
| `scipy` | KDTree (nearest-gridpoint batch query) |
| `numpy`, `pandas` | Array and tabular data processing |
| `matplotlib`, `seaborn` | Plotting |
| `scikit-learn` | AROC, Brier score, confusion matrix |

---

## Changing the verification area or period

All spatial and temporal settings are in `config.py`:

```python
AREA = [71, -11, 33, 35]   # [N, W, S, E] – change to restrict the domain
OROG_THRESHOLD_M = 200     # reject stations differing from model orography by more than this
STEPS = list(range(0, 145, 3)) + [150, 156, 162, 168]  # forecast steps to process
```

---

## Adding a new precipitation type

1. Add the GRIB code to `PTYPE_CODES` in `config.py`.
2. Add the corresponding SYNOP `ww` codes to `SYNOP_CODES`.
3. Set an initial precipitation rate threshold in `PRECIP_THRESHOLD`.
4. Add colour and display name to `COLORS` and `NICE_NAMES`.
5. Run `prectype_freqbias` to calibrate the threshold, then `prectype_verif`.

---

## Recovering failed MARS retrievals

- A SLURM retrieval job can finish with state `COMPLETED` even if MARS failed
  (e.g. `Expected N, got 0`).  Always check the number of GRIB messages with
  `grib_count` (in `/usr/local/apps/ecmwf-toolbox/<version>/GNU/8.5/bin/`).
- `AccessError: Requested data is on one or more damaged tape` is permanent:
  retrying the same request does not help, and it blocks the whole grouped
  request.
- If a monthly request failed but the control forecast was retrieved, re-fetch
  the perturbed members one day at a time:

  ```bash
  ksh scripts/retrieval/submit_retry_pf_daily.ksh 20251001 20251031 2025_2026 0001 enfo
  ```

  Each day is an independent SLURM array task, so a day on a damaged tape
  does not block the others and is easy to identify.  Add any day that still
  cannot be retrieved to `EXCLUDE_DATES` in `config.py`.
- Large grouped multi-day requests can wait 10–35 h in the tape queue;
  day-sized requests usually finish sooner overall.

---

## Model cycle changes that affect results

| Change | Date | Consequence |
|---|---|---|
| Total precipitation rate `tprate` (260048) not archived in older ENS (e.g. 2017) | — | Products notebooks sum convective/large-scale rain and snowfall rates (228218 `crr` + 228219 `lsrr` + 228220 `csfr` + 228221 `lssfr`), which is equivalent to `tprate` |
| IFS **48r1**: freezing drizzle added to the model and to `ptype` (code 12) | 27 Jun 2023 | Before 48r1 the model cannot forecast freezing drizzle, and the older verification datasets (2020–2021, 2021–2022) count freezing drizzle observations (`ww` 56/57) as freezing rain. From 2023–2024 freezing rain uses only `ww` 66/67 and freezing drizzle is a separate type. Freezing-rain case counts are therefore **not comparable** across this change; compare freezing rain + freezing drizzle instead |
| IFS **50r1**: control forecast removed from ENFO | 12 May 2026 | 50 members instead of 51; handled by `N_MEMBERS` in `config.py` and automatically in the notebooks |

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `01_prepare_dataset.py` killed with `EC_MEMKILL` | One date of ENS data needs ~33 GB in memory; the prepare job uses `--mem=128G` (QOS `nf` maximum) |
| `sbatch --dependency=afterok:<JID>` fails with "Job dependency problem" | The upstream job has already finished and left the queue; only list jobs that are still pending/running |
| `scontrol update ... TimeLimit` gives "Access/permission denied" | Users cannot extend running jobs; cancel and resubmit (e.g. as a per-day array) |
| Notebook retrieval for an old date seems stuck | The data is on tape; MARS prints `Request cost: … on 1 tape` and waits. Let it run in the background |
| Notebook stops with `Incomplete data` / `Incomplete fields for member` | Some members or steps are missing from the cached GRIB; delete the cache file in `OUT_DIR` and run again |
