# Real Trade Data Ingestion

## First vertical slice

The first end-to-end flow is:

    UN Comtrade API
        -> ComtradeProvider
        -> TradeDataRecord
        -> TradeIngestionService
        -> TradeData
        -> existing analytics/API

The first live example is:

    Reporter: India (UN M49 699)
    Partner: Germany (UN M49 276)
    HS code: 853710
    Year: 2025
    Flow: imports

UN Comtrade's current documentation provides preview APIs without a key, with
a 500-record preview limit. Registered users can obtain an API subscription
key; authenticated APIs provide larger access. For larger-scale extraction,
UN Comtrade documents bulk APIs for premium users.

## Run tests

No network:

    python -m tests.integration.test_comtrade_provider
    python -m tests.integration.test_comtrade_ingestion_service

Live API read-only:

    python -m tests.integration.test_comtrade_provider_live

Live API -> PostgreSQL:

    ./run_real_comtrade_demo.sh

Optional subscription key:

    export COMTRADE_SUBSCRIPTION_KEY="your-key"

## Important design choices

- Provider-neutral interface keeps ingestion independent of UN Comtrade.
- Trade flow is normalized from M/X to import/export because the canonical
  TradeData model already uses import/export.
- Existing country and HS master rows are required.
- Unknown countries/HS codes are rejected rather than invented.
- IngestionRun records every attempt.
- DataQualityResult records validation outcome.
- Existing TradeData rows are updated idempotently for the same
  source/reporter/partner/HS/period/flow dimensions.

Country-master synchronization is intentionally the next milestone. It is
needed before enabling unrestricted all-partner ingestion.
