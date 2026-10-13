#!/bin/bash
# ============================================================================
# build_obs_gpt.sh
# SLURM array wrapper for extract_obs_gpt.mv (old-pipeline observation-side
# .gpt extraction, reproduced with the new valid-date-batched Metview macro).
#
# One task per VALID_DATE (not forecast date/step) — each task runs Metview
# once, looping internally over the 8 synoptic hours, producing:
#   STATIONS_<vdate>_<hour>.gpt                 (master station list)
#   SYNOP_<type>_<vdate>_<hour>.gpt   x6 types  (present-weather indicators)
#
# Usage:
#   sbatch build_obs_gpt.sh <DATES_FILE> <SYNOP_DIR> <OROG_FILE> <OUT_DIR>
#
# <DATES_FILE> is a plain text file, one YYYYMMDD valid date per line.
#
# Each task costs ~10-15 min (16 obsfilter calls @ ~50-100s each), so large
# date lists must be chunked to respect the SLURM QOS MaxSubmit=100 limit —
# submit in waves of <=100 and poll `squeue -u $USER -r -h | wc -l` between
# waves (see build_synop_cache.sh for the same pattern).
# ============================================================================
#SBATCH --job-name=obs_gpt
#SBATCH --time=00:30:00
#SBATCH --mem=8G
#SBATCH --output=/home/moeg/PrecType_verif/logs/obs_gpt_%A_%a.out
#SBATCH --error=/home/moeg/PrecType_verif/logs/obs_gpt_%A_%a.err

set -euo pipefail

DATES_FILE="${1:-}"
SYNOP_DIR="${2:-}"
OROG_FILE="${3:-}"
OUT_DIR="${4:-}"

if [[ -z "$DATES_FILE" || -z "$SYNOP_DIR" || -z "$OROG_FILE" || -z "$OUT_DIR" ]]; then
    echo "Usage: sbatch build_obs_gpt.sh <DATES_FILE> <SYNOP_DIR> <OROG_FILE> <OUT_DIR>" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"

mapfile -t DATES < "$DATES_FILE"
N_DATES=${#DATES[@]}

if [[ $N_DATES -eq 0 ]]; then
    echo "ERROR: no dates found in $DATES_FILE" >&2
    exit 1
fi

if [[ -n "${SLURM_ARRAY_TASK_ID:-}" ]]; then
    IDX=$((SLURM_ARRAY_TASK_ID - 1))
    VDATE="${DATES[$IDX]}"
else
    VDATE="${DATES[0]}"
fi

# Skip if already done (last of the 6 SYNOP type files as a completion marker)
MARKER="${OUT_DIR}/SYNOP_sleet_${VDATE}_21.gpt"
if [[ -f "$MARKER" ]]; then
    echo "$(date -u): already done — $VDATE"
    exit 0
fi

echo "$(date -u): extracting obs .gpt for VALID_DATE=$VDATE ..."

export VALID_DATE="$VDATE"
export SYNOP_DIR="$SYNOP_DIR"
export OROG_FILE="$OROG_FILE"
export OUT_DIR="$OUT_DIR"

SCRIPT_DIR="/home/moeg/PrecType_verif/scripts/prectype_freqbias/mv"
time metview -b "${SCRIPT_DIR}/extract_obs_gpt.mv"

echo "$(date -u): done — $VDATE"
