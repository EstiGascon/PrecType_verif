#!/bin/ksh
# ============================================================================
# submit_retry_pf_daily.ksh  –  submit a SLURM array job to retry PF-only
# retrieval day-by-day for a date range whose grouped monthly request failed
# (e.g. the whole month blocked by a single damaged tape).
#
# Each array task retrieves exactly one day's 50 PF members and appends them
# to the existing CF-only raw_YYYYMMDD.grib file. Array tasks run independently
# in SLURM, so one day's failure never stops or delays the others.
#
# Usage:
#   submit_retry_pf_daily.ksh START_YYYYMMDD END_YYYYMMDD [SEASON] [EXPVER] [STREAM]
#
# Example (October 2025 retry):
#   ksh submit_retry_pf_daily.ksh 20251001 20251031 2025_2026 0001 enfo
# ============================================================================

BaseDateS=$1
BaseDateF=$2
SEASON=${3:-"2025_2026"}
EXPVER=${4:-"0001"}
STREAM=${5:-"enfo"}

if [[ -z "${BaseDateS}" || -z "${BaseDateF}" ]]; then
    echo "Usage: submit_retry_pf_daily.ksh START_YYYYMMDD END_YYYYMMDD [SEASON] [EXPVER] [STREAM]"
    exit 1
fi

mkdir -p logs

S=$(date -d "${BaseDateS:0:4}-${BaseDateS:4:2}-${BaseDateS:6:2}" +%s)
F=$(date -d "${BaseDateF:0:4}-${BaseDateF:4:2}-${BaseDateF:6:2}" +%s)
NDAYS=$(( (F - S) / 86400 + 1 ))

if [[ ${NDAYS} -le 0 ]]; then
    echo "ERROR: END_DATE must not be before START_DATE."
    exit 1
fi

echo "Submitting PF retry array job: ${BaseDateS} to ${BaseDateF} (${NDAYS} days)"
echo "Run tag: ${SEASON}_${STREAM}_${EXPVER}"

JID=$(sbatch --parsable --array=0-$((NDAYS-1)) retry_pf_day.ksh "${BaseDateS}" "${SEASON}" "${EXPVER}" "${STREAM}")

echo "Array job submitted (JID=${JID})"
echo "Monitor  : squeue -u \$USER"
echo "Logs     : logs/mars_pf_retry_${JID}_<TASKID>.out  (one per day, TASKID 0-$((NDAYS-1)))"
echo "Per-day result line looks like: RESULT: OK - ... / RESULT: FAILED for ..."
