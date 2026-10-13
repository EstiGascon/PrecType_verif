#!/bin/ksh
#SBATCH --job-name=mars_pf_retry
#SBATCH --output=logs/mars_pf_retry_%A_%a.out
#SBATCH --error=logs/mars_pf_retry_%A_%a.err
#SBATCH --time=12:00:00
#SBATCH --mem=8G

# ============================================================================
# retry_pf_day.ksh  –  SLURM array worker: retrieves PF (50 members) for ONE
# forecast date and appends it to the existing CF-only raw_YYYYMMDD.grib file.
#
# Used to recover from a grouped monthly MARS request that failed outright
# (e.g. a damaged tape blocking the whole month). Each array task handles a
# single date independently, so one day's failure never stops the others.
#
# Not meant to be run directly — use submit_retry_pf_daily.ksh.
# Actual date processed = BASE_DATE + SLURM_ARRAY_TASK_ID days.
# ============================================================================

BaseDate=$1
SEASON=${2:-"2025_2026"}
EXPVER=${3:-"0001"}
STREAM=${4:-"enfo"}
RUN_TAG="${SEASON}_${STREAM}_${EXPVER}"

TASK_ID=${SLURM_ARRAY_TASK_ID:-0}
DAY=$(date -I -d "${BaseDate:0:4}-${BaseDate:4:2}-${BaseDate:6:2} + ${TASK_ID} day" | tr -d '-')

DirDB="/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/raw/${RUN_TAG}"
TARGET_FINAL="${DirDB}/raw_${DAY}.grib"
GRIB_COUNT="/usr/local/apps/ecmwf-toolbox/2026.07.0.0/GNU/8.5/bin/grib_count"

STEPS="0/3/6/9/12/15/18/21/24/27/30/33/36/39/42/45/48/51/54/57/60/63/66/69/72/75/78/81/84/87/90/93/96/99/102/105/108/111/114/117/120/123/126/129/132/135/138/141/144/150/156/162/168"
EXPECTED_PF_MSGS=5300   # 50 members * 2 params * 53 steps

echo "Day        : ${DAY}  (array task ${TASK_ID}, base ${BaseDate})"
echo "Target     : ${TARGET_FINAL}"
echo "Start time : $(date)"

if [[ ! -f "${TARGET_FINAL}" ]]; then
    echo "ERROR: ${TARGET_FINAL} does not exist (expected the CF-only file already in place) – skipping."
    exit 1
fi

TARGET_PF=$(mktemp "/tmp/mars_pf_${DAY}_XXXXXX.grib")
MARS_REQ=$(mktemp "/tmp/mars_pf_req_${DAY}_XXXXXX.req")
trap "rm -f ${TARGET_PF} ${MARS_REQ}" EXIT

cat > "${MARS_REQ}" << EOF
retrieve,
    class   = od,
    stream  = ${STREAM},
    expver  = ${EXPVER},
    number  = 1/to/50,
    type    = pf,
    date    = ${DAY},
    time    = 00,
    levtype = sfc,
    area    = 71/-11/33/35,
    step    = ${STEPS},
    accuracy = 16,
    param   = 260015/260048,
    target  = "${TARGET_PF}"
EOF

mars "${MARS_REQ}"
MARS_RC=$?
echo "mars exit code: ${MARS_RC}"

NMSG=0
if [[ -s "${TARGET_PF}" ]]; then
    NMSG=$(${GRIB_COUNT} "${TARGET_PF}" 2>/dev/null)
fi
echo "Messages retrieved: ${NMSG} (expected ${EXPECTED_PF_MSGS})"

# A damaged-tape error can leave mars_rc=0 with zero fields written, so the
# message count is checked in addition to the exit code before trusting the file.
if [[ "${MARS_RC}" -eq 0 && "${NMSG}" -eq "${EXPECTED_PF_MSGS}" ]]; then
    cat "${TARGET_FINAL}" "${TARGET_PF}" > "${TARGET_FINAL}.tmp" && mv "${TARGET_FINAL}.tmp" "${TARGET_FINAL}"
    echo "RESULT: OK - PF appended for ${DAY}"
    echo "End time   : $(date)"
    exit 0
else
    echo "RESULT: FAILED for ${DAY} - mars_rc=${MARS_RC} messages=${NMSG}/${EXPECTED_PF_MSGS} (likely damaged tape or transient error; ${DAY} remains CF-only)"
    echo "End time   : $(date)"
    exit 1
fi
