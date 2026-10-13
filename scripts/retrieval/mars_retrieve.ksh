#!/bin/ksh
#SBATCH --job-name=mars_ptype
#SBATCH --output=logs/mars_%A_%a.out
#SBATCH --error=logs/mars_%A_%a.err
#SBATCH --time=2-00:00:00
#SBATCH --mem=32G

# Arguments
BaseDateS=$1
BaseDateF=$2
SEASON=${3:-"2024_2025"}
EXPVER=${4:-"0001"}
STREAM=${5:-"enfo"}

RUN_TAG="${SEASON}_${STREAM}_${EXPVER}"

if [[ -z "${BaseDateS}" || -z "${BaseDateF}" ]]; then
    echo "Usage: mars_retrieve.ksh START_YYYYMMDD END_YYYYMMDD [SEASON] [EXPVER] [STREAM]"
    exit 1
fi

DirDB="/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/raw/${RUN_TAG}"
mkdir -p "${DirDB}"

echo "Processing : ${BaseDateS} to ${BaseDateF}"
echo "Season     : ${SEASON}"
echo "Expver     : ${EXPVER}"
echo "Stream     : ${STREAM}"
echo "Run tag    : ${RUN_TAG}"
echo "Output     : ${DirDB}"
echo "Start time : $(date)"

# ── IFS 50r1 check ────────────────────────────────────────────────────────────
# From 12 May 2026, the CF was removed from the ENFO stream (IFS cycle 50r1).
# The same applies to any run using expver=0080 (the 50r1 research experiment).
# When NO_CF=1 the CF retrieve block is omitted; only the 50 PF are retrieved.
NO_CF=0
[[ "${EXPVER}" == "0080" ]] && NO_CF=1
[[ ${NO_CF} -eq 0 && "${BaseDateS}" > "20260511" ]] && NO_CF=1
echo "50r1 mode (no CF): ${NO_CF}"

# ── Build MARS request in a temp file ─────────────────────────────────────────
# Writing to a temp file lets us conditionally include the CF block while still
# passing both blocks to a SINGLE mars call (→ one tape staging for CF + PF).
MARS_REQ=$(mktemp /tmp/mars_ptype_XXXXXX.req)
trap "rm -f ${MARS_REQ}" EXIT

STEPS="0/3/6/9/12/15/18/21/24/27/30/33/36/39/42/45/48/51/54/57/60/63/66/69/72/75/78/81/84/87/90/93/96/99/102/105/108/111/114/117/120/123/126/129/132/135/138/141/144/150/156/162/168"

if [[ ${NO_CF} -eq 0 ]]; then
    cat >> "${MARS_REQ}" << EOF
# ── Control forecast (CF): precip type + precip rate ─────────────────────────
retrieve,
    class   = od,
    stream  = ${STREAM},
    expver  = ${EXPVER},
    type    = cf,
    date    = ${BaseDateS}/to/${BaseDateF},
    time    = 00,
    levtype = sfc,
    area    = 71/-11/33/35,
    step    = ${STEPS},
    accuracy = 16,
    param   = 260015/260048,
    target  = "${DirDB}/raw_{date}.grib"

EOF
fi

cat >> "${MARS_REQ}" << EOF
# ── Perturbed forecasts (PF, members 1-50) ────────────────────────────────────
retrieve,
    class   = od,
    stream  = ${STREAM},
    expver  = ${EXPVER},
    number  = 1/to/50,
    type    = pf,
    date    = ${BaseDateS}/to/${BaseDateF},
    time    = 00,
    levtype = sfc,
    area    = 71/-11/33/35,
    step    = ${STEPS},
    accuracy = 16,
    param   = 260015/260048,
    target  = "${DirDB}/raw_{date}.grib"

EOF

export MARS_MULTITARGET_STRICT_FORMAT=1
mars "${MARS_REQ}"

echo "End time : $(date)"
