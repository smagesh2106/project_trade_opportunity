#!/usr/bin/env bash
set -euo pipefail

cd /home/magesh/02_Projects/project_trade_opportunity/backend

python -m app.ingestion.run_comtrade   --reporter-code 699   --partner-code 276   --period 2025   --flow M   --hs-code 853710   --max-records 50

echo
echo "=== India <- Germany, HS 853710 ==="

docker exec hanjes-postgres   psql -U trade_user -d hanjes_technologies   -c "
SELECT
    td.id,
    r.iso3 AS reporter,
    p.iso3 AS partner,
    h.code AS hs_code,
    td.period_start,
    td.trade_flow,
    td.trade_value_usd,
    td.quantity,
    td.source_record_id,
    td.data_version
FROM trade_opportunity.trade_data td
JOIN trade_opportunity.countries r
  ON r.id = td.reporter_country_id
JOIN trade_opportunity.countries p
  ON p.id = td.partner_country_id
JOIN trade_opportunity.hs_codes h
  ON h.id = td.hs_code_id
WHERE r.iso3 = 'IND'
  AND p.iso3 = 'DEU'
  AND h.code = '853710'
  AND td.period_start = DATE '2025-01-01'
  AND td.trade_flow = 'import'
ORDER BY td.id;
"
