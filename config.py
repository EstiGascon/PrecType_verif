"""
Central configuration for Precipitation Type Verification
==========================================================
Edit the variables in the "Run identity" block below to adapt to a new
season, experiment version, or model stream.  All paths and output
directories are derived automatically from those values, so results from
different runs never overwrite each other.
"""

from pathlib import Path

# ── Run identity ──────────────────────────────────────────────────────────────
# These four values together uniquely identify one verification run.
# They are embedded in every data/output path so runs for different seasons,
# experiment versions, or streams can coexist on disk.

SEASON     = "2025_2026"    # e.g. "2023_2024", "2024_2025", "2025_2026"
START_DATE = "20251001"     # YYYYMMDD – first forecast date to retrieve/process
END_DATE   = "20260331"     # YYYYMMDD – last  forecast date to retrieve/process
EXPVER     = "0001"         # MARS expver (operational IFS = "0001"; research = "xxxx")
STREAM     = "enfo"         # MARS stream ("enfo" = ensemble forecast)

# Forecast dates to skip entirely during 01_prepare_dataset.py (no parquet
# produced, so 02_compute_scores.py never sees them). Use this for dates whose
# ensemble data is permanently incomplete and would bias the scores.
EXCLUDE_DATES = [
    "20251010",  # PF members unavailable: MARS tape F0091600 damaged (CF only)
]

# Compact tag used in directory names: e.g. "2024_2025_enfo_0001"
RUN_TAG = f"{SEASON}_{STREAM}_{EXPVER}"

# ── Remote storage (all raw / intermediate data goes here) ────────────────────
_BASE = Path("/ec/vol/enscal/VERIF_PrecipType")

PATH_RAW      = _BASE / "VERIF_ptype_all" / "raw"           / RUN_TAG
PATH_SYNOP    = _BASE / "VERIF_ptype_all" / "SYNOP"         / SEASON   # shared across expvers
PATH_PREVERIF = _BASE / "VERIF_ptype_all" / "DATA_preVerif" / RUN_TAG
PATH_FREQBIAS = _BASE / "VERIF_ptype_all" / "DATA_freqbias" / RUN_TAG

# Orography field – deterministic NWP surface elevation on the ENS grid
PATH_OROG = _BASE / "VERIF_ptype_all" / "orog.grib"

# ── Local results (plots, score tables) ───────────────────────────────────────
# Each run gets its own sub-directory so plots from different seasons/expvers
# can be compared side by side without risk of overwriting.
PATH_RESULTS = Path("/home/moeg/PrecType_verif/verification_results") / RUN_TAG

# ── Spatial domain ────────────────────────────────────────────────────────────
AREA = [71, -11, 33, 35]   # [North, West, South, East] – Europe
OROG_THRESHOLD_M = 200     # max |station_elev – model_elev| (m)

# ── Ensemble ──────────────────────────────────────────────────────────────────
# IFS cycle 50r1 (operational from 12 May 2026): the CF was removed from the
# ENFO stream.  Only 50 PF members are available.  This applies to any run
# with EXPVER="0080" and to all operational runs on or after 20260512.
_IFS_50R1_DATE = "20260512"
N_MEMBERS = 50 if (EXPVER == "0080" or START_DATE >= _IFS_50R1_DATE) else 51

# ── Forecast steps (hours) ────────────────────────────────────────────────────
STEPS = list(range(0, 145, 3)) + [150, 156, 162, 168]

# Lead-time day groups used for aggregated scores
DAY_GROUPS = {
    1: list(range(  0,  24, 3)),
    2: list(range( 24,  48, 3)),
    3: list(range( 48,  72, 3)),
    4: list(range( 72,  96, 3)),
    5: list(range( 96, 120, 3)),
    6: list(range(120, 144, 3)),
    7: list(range(144, 169, 6)),   # 144, 150, 156, 162, 168
}

# ── GRIB parameter IDs ────────────────────────────────────────────────────────
PARAM_PTYPE = 260015   # Precipitation type (categorical integer)
PARAM_PRATE = 260048   # Total precipitation rate  (kg m-2 s-1 → ×3600 = mm/h)

# GRIB code for each precipitation type (param 260015)
PTYPE_CODES = {
    "rain":         1,
    "freezrain":    3,
    "snow":         5,
    "wetsnow":      6,
    "sleet":        7,
    "icepellets":   8,
    "freezdrizzle": 12,
}

# ── Precipitation rate thresholds (mm/h) – Block A fixed, operationally chosen
# These come from the Block B frequency-bias analysis.
PRECIP_THRESHOLD = {
    "rain":         0.07,
    "freezrain":    0.05,
    "snow":         0.05,
    "wetsnow":      0.05,
    "sleet":        0.05,
    "icepellets":   0.05,
    "freezdrizzle": 0.02,
}

# ── SYNOP present-weather (ww) codes per type  ────────────────────────────────
SYNOP_CODES = {
    "rain": [
        51, 52, 53, 54, 55, 58, 59,
        60, 61, 62, 63, 64, 65, 68, 69,
        80, 81, 82, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 99,
    ],
    "snow": [70, 71, 72, 73, 74, 75, 76, 77, 78, 85, 86, 93, 94, 95, 97],
    "icepellets":   [79, 87, 77],
    "freezrain":    [66, 67],
    "freezdrizzle": [56, 57],
    "sleet":        [68, 69, 83, 84, 87, 88, 89, 90, 93, 94, 95, 97],
    "wetsnow":      [],   # no direct SYNOP code
}

# SYNOP present weather cannot distinguish dry snow from wet snow, so both
# GRIB ptype codes must be combined into the model's "snow" probability before
# comparing against the SYNOP snow indicator.  Matches the old R script:
#   MOD_man_snow = round(perc_snow, 2) + round(perc_wetsnow, 2)
PTYPE_COMBINE_CODES = {
    "snow": [PTYPE_CODES["snow"], PTYPE_CODES["wetsnow"]],
}

# ── Block B – precipitation rate threshold candidates (mm/h) ──────────────────
BIAS_THRESHOLDS = [0.02, 0.05, 0.07, 0.10, 0.12]

# Lead-time groups used for frequency-bias plots (matching old R script)
BIAS_GROUPS = {
    "day1":  list(range(  0, 24, 3)),
    "day2":  list(range( 24, 48, 3)),
    "day5":  list(range( 96, 120, 3)),
}

# ── Plot styling ──────────────────────────────────────────────────────────────
COLORS = {
    "rain":         "#00CC00",
    "snow":         "#0000FF",
    "sleet":        "#00CCCC",
    "freezrain":    "#FF0000",
    "freezdrizzle": "#FF1493",
    "icepellets":   "#FF9900",
    "wetsnow":      "#8B4513",
}

NICE_NAMES = {
    "rain":         "Rain",
    "snow":         "Snow",
    "sleet":        "Sleet",
    "freezrain":    "Freezing Rain",
    "freezdrizzle": "Freezing Drizzle",
    "icepellets":   "Ice Pellets",
    "wetsnow":      "Wet Snow",
}
