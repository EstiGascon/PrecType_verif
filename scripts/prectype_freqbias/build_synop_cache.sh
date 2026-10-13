#!/bin/bash
# ============================================================================
# build_synop_cache.sh
# Pre-build parquet caches for all SYNOP BUFR files in a season directory.
#
# Each BUFR file (~170 MB) is decoded once with pdbufr and stored as a parquet
# file (~1-2 MB) alongside the BUFR.  Future reads by compute_freqbias.py take
# < 10 ms instead of ~400 s.
#
# Usage:
#   sbatch build_synop_cache.sh <SYNOP_DIR>
#
# Example:
#   cd /home/moeg/PrecType_verif
#   sbatch scripts/prectype_freqbias/build_synop_cache.sh \
#       /ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/SYNOP/2023_48r1esuite
#
# This submits a SLURM array (one task per BUFR file).  All tasks run in
# parallel so the total wall-clock time is roughly equal to one file (~8 min).
# ============================================================================
#SBATCH --job-name=synop_cache
#SBATCH --time=00:15:00
#SBATCH --mem=8G
#SBATCH --output=/home/moeg/PrecType_verif/logs/synop_cache_%A_%a.out
#SBATCH --error=/home/moeg/PrecType_verif/logs/synop_cache_%A_%a.err

set -euo pipefail

SYNOP_DIR="${1:-}"
if [[ -z "$SYNOP_DIR" ]]; then
    echo "ERROR: SYNOP_DIR argument required" >&2
    exit 1
fi

# Build list of BUFR files (supports both legacy SYNOP_mannual_YYYYMMDD.bufr
# and new SYNOP_YYYY-MM-DD.bufr naming conventions).
mapfile -t BUFR_FILES < <(ls "${SYNOP_DIR}"/SYNOP_*.bufr 2>/dev/null | sort)
N_FILES=${#BUFR_FILES[@]}

if [[ $N_FILES -eq 0 ]]; then
    echo "ERROR: No SYNOP_*.bufr files found in ${SYNOP_DIR}" >&2
    exit 1
fi

# If running as an array job, process the file for this task index
if [[ -n "${SLURM_ARRAY_TASK_ID:-}" ]]; then
    IDX=$((SLURM_ARRAY_TASK_ID - 1))
    BUFR="${BUFR_FILES[$IDX]}"
    PARQUET="${BUFR%.bufr}_v2.parquet"

    if [[ -f "$PARQUET" ]]; then
        echo "$(date -u): already cached — $BUFR"
        exit 0
    fi

    echo "$(date -u): decoding $BUFR ..."
    python3 -u -c "
import sys, time
sys.path.insert(0, '/home/moeg/PrecType_verif')
from utils import read_synop_df
from pathlib import Path

bufr = Path('$BUFR')
t0 = time.time()
df = read_synop_df(bufr)
if df is None:
    print('FAILED: could not decode', bufr, flush=True)
    sys.exit(1)
print(f'Done in {time.time()-t0:.0f}s: {len(df)} rows -> {bufr.with_suffix(\".parquet\")}', flush=True)
"
    exit 0
fi

# Submitted without a task ID: re-submit as an array job
echo "Submitting array job for ${N_FILES} files in ${SYNOP_DIR} ..."
sbatch --array="1-${N_FILES}" "$0" "$SYNOP_DIR"
