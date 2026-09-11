#!/usr/bin/env bash
set -euo pipefail

REPORTERS=(
  "156:China"    
  "076:Brazil"
  "826:United Kingdom"
  "251:France"
  "276:Germany"
  "784:United Arab Emirates"
  "842:United States"
)

YEARS=(
  2023
  2024
  2025
)

HS_CODES=(
  853620
  853530
  853710
  853210
  850434
)

for reporter in "${REPORTERS[@]}"; do
  reporter_code="${reporter%%:*}"
  reporter_name="${reporter#*:}"

  for year in "${YEARS[@]}"; do
    echo
    echo "============================================================"
    echo "Reporter : ${reporter_name} (${reporter_code})"
    echo "Year     : ${year}"
    echo "Flow     : IMPORT"
    echo "============================================================"

    cmd=(
      python -m app.ingestion.run_comtrade
      --reporter-code "${reporter_code}"
      --period "${year}"
      --flow M
      --max-records 500
    )

    for hs_code in "${HS_CODES[@]}"; do
      cmd+=(--hs-code "${hs_code}")
    done

    "${cmd[@]}"

    echo
    echo "Completed ${reporter_name} ${year}"
    echo
  done
done

echo
echo "Bulk import ingestion completed."
