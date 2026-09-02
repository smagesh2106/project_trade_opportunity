#!/usr/bin/env bash
set -euo pipefail

# Run from the backend directory regardless of the cron working directory.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_PYTHON="${VENV_PYTHON:-$SCRIPT_DIR/.venv/bin/python}"

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "ERROR: Python executable not found: $VENV_PYTHON" >&2
    exit 1
fi

REPORTER_CODE="${REPORTER_CODE:-699}"
FLOW="${FLOW:-M}"
HS_CODE="${HS_CODE:-853710}"
MAX_RECORDS="${MAX_RECORDS:-500}"

LOG_DIR="${LOG_DIR:-$SCRIPT_DIR/logs}"
mkdir -p "$LOG_DIR"

TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
LOG_FILE="$LOG_DIR/incremental_ingestion.log"

{
    echo "============================================================"
    echo "[$TIMESTAMP] Starting incremental UN Comtrade ingestion"
    echo "Reporter     : $REPORTER_CODE"
    echo "Flow         : $FLOW"
    echo "HS code      : $HS_CODE"
    echo "Max records  : $MAX_RECORDS"
    echo "============================================================"

    "$VENV_PYTHON" -m app.ingestion.run_comtrade \
        --reporter-code "$REPORTER_CODE" \
        --incremental \
        --flow "$FLOW" \
        --hs-code "$HS_CODE" \
        --max-records "$MAX_RECORDS"

    status=$?

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Completed with exit status $status"
    echo

    exit "$status"
} >>"$LOG_FILE" 2>&1
