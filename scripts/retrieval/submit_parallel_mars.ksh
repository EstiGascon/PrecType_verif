#!/bin/ksh
# Submit ENS forecast MARS retrieval jobs – one SLURM job per monthly chunk.
# Usage: submit_parallel_mars.ksh [SEASON] [EXPVER] [STREAM]
# Example: submit_parallel_mars.ksh 2024_2025 0001 enfo

SEASON=${1:-"2024_2025"}
EXPVER=${2:-"0001"}
STREAM=${3:-"enfo"}
RUN_TAG="${SEASON}_${STREAM}_${EXPVER}"

mkdir -p logs

case "${SEASON}_${EXPVER}" in
    "2023_2024_0001")
        BaseDateS_arr=(20231015 20231101 20231201 20240101 20240201 20240301)
        BaseDateF_arr=(20231031 20231130 20231231 20240131 20240229 20240331)
        ;;
    "2024_2025_0001")
        BaseDateS_arr=(20241112 20241201 20250101 20250201 20250301 20250401)
        BaseDateF_arr=(20241130 20241231 20250131 20250228 20250331 20250415)
        ;;
    "2025_2026_0080")
        # IFS 50r1 research experiment – no CF in ENFO; mars_retrieve.ksh handles this
        BaseDateS_arr=(20251203 20260101 20260201 20260301 20260401)
        BaseDateF_arr=(20251231 20260131 20260228 20260331 20260415)
        ;;
    "2025_2026_0001")
        # Operational IFS – winter 2025-2026, Oct 2025 to Mar 2026
        BaseDateS_arr=(20251001 20251101 20251201 20260101 20260201 20260301)
        BaseDateF_arr=(20251031 20251130 20251231 20260131 20260228 20260331)
        ;;
    *)
        echo "Unknown season/expver combination '${SEASON}_${EXPVER}'. Edit this script to add date arrays."
        exit 1
        ;;
esac

let len=${#BaseDateS_arr[@]}-1
echo "Submitting $((len+1)) MARS jobs for run tag: ${RUN_TAG} ..."

for ind in $(seq 0 ${len}); do
    BaseDateS=${BaseDateS_arr[${ind}]}
    BaseDateF=${BaseDateF_arr[${ind}]}
    echo "  Job $((ind+1)): ${BaseDateS} → ${BaseDateF}"
    sbatch mars_retrieve.ksh "${BaseDateS}" "${BaseDateF}" "${SEASON}" "${EXPVER}" "${STREAM}"
done

echo ""
echo "Run tag : ${RUN_TAG}"
echo "Monitor : squeue -u \$USER"
echo "Logs    : logs/"
