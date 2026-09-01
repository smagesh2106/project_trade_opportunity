from __future__ import annotations

import argparse
import os
from unittest import result

from app.db.session import SessionLocal
from app.ingestion.trade_ingestion import TradeIngestionService
from app.integrations.trade.comtrade import ComtradeProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest UN Comtrade trade data.")
    parser.add_argument("--reporter-code", type=int, required=True)
    parser.add_argument("--partner-code", type=int)
    parser.add_argument("--period", required=True, help="YYYY or YYYYMM")
    parser.add_argument("--flow", choices=["M", "X"], required=True)
    parser.add_argument(
        "--hs-code",
        action="append",
        dest="hs_codes",
        required=True,
    )
    parser.add_argument("--max-records", type=int, default=500)
    parser.add_argument(
        "--subscription-key",
        default=os.getenv("COMTRADE_SUBSCRIPTION_KEY"),
    )
    args = parser.parse_args()

    provider = ComtradeProvider(
        subscription_key=args.subscription_key,
    )
    db = SessionLocal()

    try:
        result = TradeIngestionService(
            db=db,
            provider=provider,
        ).ingest(
            reporter_code=args.reporter_code,
            period=args.period,
            flow_code=args.flow,
            cmd_codes=args.hs_codes,
            partner_code=args.partner_code,
            max_records=args.max_records,
        )

        print("UN Comtrade ingestion completed.")
        print(f"Ingestion run ID : {result.ingestion_run_id}")
        print(f"Status           : {result.status}")
        print(f"Records received : {result.records_received}")
        print(f"Records inserted : {result.records_inserted}")
        print(f"Records updated  : {result.records_updated}")
        print(f"Records rejected : {result.records_rejected}")
        print(f"Aggregate records: {result.aggregate_records}")
        print(f"Detail records skipped: {result.detail_records_skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
