#!/bin/ksh
# ============================================================================
# run_freqbias.sh  –  prectype_freqbias SLURM orchestrator
# ============================================================================
# Submits compute_freqbias.py (slow, parallel) and then plot_freqbias.py.
#
# Usage:
#   ksh run_freqbias.sh [SEASON] [EXPVER] [STREAM]
#
# Examples:
#   ksh run_freqbias.sh 2024_2025
#   ksh run_freqbias.sh 2024_2025 xxxx enfo        # research experiment
# ============================================================================

SEASON=${1:-"2024_2025"}
EXPVER=${2:-"0001"}
STREAM=${3:-"enfo"}
RUN_TAG="${SEASON}_${STREAM}_${EXPVER}"
WORKERS=4
RAW_PATH=""
PRATE_PATH=""

SCRIPT_DIR=$(dirname "$0")
ROOT_DIR="${SCRIPT_DIR}/../.."

mkdir -p "${ROOT_DIR}/logs"

case ${SEASON} in
    "2023_2024")
        START="20231015"
        END="20240331"
        ;;
    "2024_2025")
        START="20241112"
        END="20250415"
        ;;
    "2023_48r1esuite")
        # Old 48r1 esuite validation period: Feb 16 – Apr 15 2023
        # (matches old R-script reference gpt files)
        START="20230216"
        END="20230415"
        RAW_PATH="/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/raw/raw_esuite48r1_2023"
        PRATE_PATH="/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/raw/raw_esuite48r1_2023"
        ;;
    "2025_2026")
        # IFS 50r1 research experiment (expver=0080): Dec 3 2025 - Apr 15 2026
        START="20251203"
        END="20260415"
        ;;
    *)
        echo "Unknown season '${SEASON}'. Edit START/END."
        exit 1
        ;;
esac

echo "Submitting prectype_freqbias pipeline: run tag = ${RUN_TAG} ..."

# Build optional --raw-path / --prate-path flags
EXTRA_ARGS=""
[[ -n "${RAW_PATH}"   ]] && EXTRA_ARGS="${EXTRA_ARGS} --raw-path ${RAW_PATH}"
[[ -n "${PRATE_PATH}" ]] && EXTRA_ARGS="${EXTRA_ARGS} --prate-path ${PRATE_PATH}"

# ── Step 1: compute_freqbias ──────────────────────────────────────────────────
COMP_JID=$(sbatch --parsable \
           --job-name="freqbias_${RUN_TAG}" \
           --output="${ROOT_DIR}/logs/freqbias_%j.out" \
           --error="${ROOT_DIR}/logs/freqbias_%j.err" \
           --time=2-00:00:00 --mem=16G \
           --export=ALL,METVIEW_BATCH_MODE=1 \
           --wrap="cd ${ROOT_DIR} && python3 -u scripts/prectype_freqbias/compute_freqbias.py \
                   ${START} ${END} --season ${SEASON} --expver ${EXPVER} --stream ${STREAM} ${EXTRA_ARGS}")

echo "  Compute job: JID=${COMP_JID}"

# ── Step 2: plot_freqbias (runs after compute finishes) ───────────────────────
PLOT_JID=$(sbatch --parsable \
           --job-name="freqbias_plot_${RUN_TAG}" \
           --output="${ROOT_DIR}/logs/freqbias_plot_%j.out" \
           --error="${ROOT_DIR}/logs/freqbias_plot_%j.err" \
           --time=00:30:00 --mem=4G \
           --dependency=afterok:${COMP_JID} \
           --wrap="cd ${ROOT_DIR} && python3 scripts/prectype_freqbias/plot_freqbias.py --expver ${EXPVER} --stream ${STREAM} --season ${SEASON}")

echo "  Plot job: JID=${PLOT_JID} (depends on ${COMP_JID})"
echo ""
echo "Run tag : ${RUN_TAG}"
echo "Results : ${ROOT_DIR}/verification_results/${RUN_TAG}/freqbias/"
echo "Monitor : squeue -u \$USER"
echo "Logs    : ${ROOT_DIR}/logs/"
