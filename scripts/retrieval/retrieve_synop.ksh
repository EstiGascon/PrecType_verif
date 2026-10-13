#!/bin/ksh
# ============================================================================
# retrieve_synop.ksh  –  SYNOP BUFR retrieval via MARS
# ============================================================================
# Retrieves daily BUFR files (OBSTYPE 1/2/170/172/176/178) for Europe.
# Replaces SYNOP_retrieval.ksh and SYNOP_mannual.ksh.
#
# Usage:
#   retrieve_synop.ksh SEASON [START_DATE] [END_DATE]
#
# Examples:
#   retrieve_synop.ksh 2024_2025
#   retrieve_synop.ksh 2024_2025 2024-11-12 2025-04-15
#   retrieve_synop.ksh 2025_2026 2025-11-01 2026-04-15
# ============================================================================

SEASON=${1}

if [[ -z "${SEASON}" ]]; then
    echo "ERROR: SEASON argument required (e.g. 2024_2025)"
    echo "Usage: retrieve_synop.ksh SEASON [START_DATE] [END_DATE]"
    exit 1
fi

# Default date ranges per known season; override with explicit arguments
case ${SEASON} in
    "2023_2024")
        START_DATE=${2:-"2023-10-15"}
        END_DATE=${3:-"2024-03-30"}
        ;;
    "2024_2025")
        START_DATE=${2:-"2024-11-12"}
        END_DATE=${3:-"2025-04-15"}
        ;;
    *)
        if [[ -z "${2}" || -z "${3}" ]]; then
            echo "ERROR: Unknown season '${SEASON}'. Provide START_DATE and END_DATE."
            exit 1
        fi
        START_DATE=${2}
        END_DATE=${3}
        ;;
esac

OUTDIR="/ec/vol/enscal/VERIF_PrecipType/VERIF_ptype_all/SYNOP/${SEASON}"
mkdir -p "${OUTDIR}"

echo "=================================="
echo "SYNOP BUFR retrieval"
echo "Season    : ${SEASON}"
echo "Period    : ${START_DATE} to ${END_DATE}"
echo "Output    : ${OUTDIR}"
echo "=================================="

i="${START_DATE}"
until [[ $i > "${END_DATE}" ]]; do

    TARGET="${OUTDIR}/SYNOP_${i}.bufr"

    if [[ -f "${TARGET}" ]]; then
        echo "  Skipping (already exists): ${i}"
        i=$(date -I -d "$i + 1 day")
        continue
    fi

    cat > mars_synop_tmp.txt << EOF
RETRIEVE,
  REPRES  = BUFR,
  TYPE    = OB,
  OBSTYPE = 1/2/170/172/176/178,
  DATE    = $i,
  TIME    = 00,
  RANGE   = 1439,
  AREA    = 71/-11/33/35,
  TARGET  = "${TARGET}"
EOF

    mars mars_synop_tmp.txt
    echo "  Retrieved: ${i}"

    i=$(date -I -d "$i + 1 day")
done

rm -f mars_synop_tmp.txt
echo "Done."
