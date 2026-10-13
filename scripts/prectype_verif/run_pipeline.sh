#!/bin/ksh
#SBATCH --job-name=ptype_verif
#SBATCH --output=logs/verif_%A_%a.out
#SBATCH --error=logs/verif_%A_%a.err
#SBATCH --time=4-00:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4

# ============================================================================
# run_pipeline.sh  –  prectype_verif end-to-end SLURM orchestrator
# ============================================================================
# Submits prepare_dataset jobs (one per monthly chunk) and then a follow-up
# compute_scores job once all dataset jobs have finished.
#
# Usage:
#   ksh run_pipeline.sh [SEASON] [EXPVER] [STREAM]
#
# Examples:
#   ksh run_pipeline.sh 2024_2025
#   ksh run_pipeline.sh 2024_2025 0001 enfo        # operational IFS
#   ksh run_pipeline.sh 2024_2025 xxxx enfo        # research experiment
# ============================================================================

SEASON=${1:-"2024_2025"}
EXPVER=${2:-"0001"}
STREAM=${3:-"enfo"}
RUN_TAG="${SEASON}_${STREAM}_${EXPVER}"
WORKERS=4

SCRIPT_DIR=$(dirname "$0")
ROOT_DIR="${SCRIPT_DIR}/../.."

mkdir -p "${ROOT_DIR}/logs"

case "${SEASON}_${EXPVER}" in
    "2023_2024_0001")
        ChunkS_arr=(20231015 20231101 20231201 20240101 20240201 20240301)
        ChunkF_arr=(20231031 20231130 20231231 20240131 20240229 20240331)
        ;;
    "2024_2025_0001")
        ChunkS_arr=(20241112 20241201 20250101 20250201 20250301 20250401)
        ChunkF_arr=(20241130 20241231 20250131 20250228 20250331 20250415)
        ;;
    "2025_2026_0080")
        # IFS 50r1 research experiment (expver=0080): Dec 3 2025 - Apr 15 2026
        ChunkS_arr=(20251203 20260101 20260201 20260301 20260401)
        ChunkF_arr=(20251231 20260131 20260228 20260331 20260415)
        ;;
    "2025_2026_0001")
        # Operational IFS – winter 2025-2026, Oct 2025 to Mar 2026
        ChunkS_arr=(20251001 20251101 20251201 20260101 20260201 20260301)
        ChunkF_arr=(20251031 20251130 20251231 20260131 20260228 20260331)
        ;;
    *)
        echo "Unknown season/expver combination '${SEASON}_${EXPVER}'. Edit ChunkS/ChunkF arrays."
        exit 1
        ;;
esac

echo "Submitting prectype_verif pipeline: run tag = ${RUN_TAG} ..."

# ── Step 1: prepare_dataset – one SLURM job per monthly chunk ─────────────────
let len=${#ChunkS_arr[@]}-1
PREP_JOBS=""

for ind in $(seq 0 ${len}); do
    START=${ChunkS_arr[${ind}]}
    END=${ChunkF_arr[${ind}]}

    JID=$(sbatch --parsable \
          --job-name="verif_prep_${ind}" \
          --output="${ROOT_DIR}/logs/verif_prep_%j.out" \
          --error="${ROOT_DIR}/logs/verif_prep_%j.err" \
          --time=1-00:00:00 --mem=128G --cpus-per-task=${WORKERS} \
           --wrap="cd ${ROOT_DIR} && python3 scripts/prectype_verif/01_prepare_dataset.py \
                  ${START} ${END} --workers ${WORKERS} --expver ${EXPVER} --stream ${STREAM}")

    echo "  Prep job ${ind}: ${START}→${END}  (JID=${JID})"
    PREP_JOBS="${PREP_JOBS}:${JID}"
done

PREP_JOBS="${PREP_JOBS#:}"   # strip leading colon

# ── Step 2: compute_scores – runs only after all prep jobs have finished ───────
SCORE_JID=$(sbatch --parsable \
            --job-name="verif_scores_${RUN_TAG}" \
            --output="${ROOT_DIR}/logs/verif_scores_%j.out" \
            --error="${ROOT_DIR}/logs/verif_scores_%j.err" \
            --time=02:00:00 --mem=32G \
            --dependency=afterok:${PREP_JOBS} \
            --wrap="cd ${ROOT_DIR} && python3 scripts/prectype_verif/02_compute_scores.py --expver ${EXPVER} --stream ${STREAM} --season ${SEASON}")

echo ""
echo "Score job submitted (JID=${SCORE_JID}), depends on: ${PREP_JOBS}"
echo "Run tag : ${RUN_TAG}"
echo "Results : ${ROOT_DIR}/verification_results/${RUN_TAG}/"
echo "Monitor : squeue -u \$USER"
echo "Logs    : ${ROOT_DIR}/logs/"
