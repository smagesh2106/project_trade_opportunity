from __future__ import annotations

import argparse
import os

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.ingestion.periods import (
    is_current_or_future_year,
    next_annual_period,
    parse_annual_period,
)
from app.ingestion.trade_ingestion import TradeIngestionService
from app.integrations.trade.comtrade import ComtradeProvider
from app.models import Country, DataSource, HSCode, TradeData

SOURCE_NAME = "UN Comtrade"


class NoEligiblePeriod(Exception):
    """Raised when incremental ingestion has no eligible annual period."""


def _get_source_id(db) -> int:
    source_id = db.scalar(select(DataSource.id).where(DataSource.name == SOURCE_NAME))

    if source_id is None:
        raise RuntimeError(
            "UN Comtrade data source is not configured. "
            "Run a normal ingestion first."
        )

    return source_id


def _get_hs_code_id(db, code: str) -> int:
    hs_code = db.scalar(
        select(HSCode).where(
            HSCode.code == code.strip(),
            HSCode.active.is_(True),
        )
    )

    if hs_code is None:
        raise RuntimeError(f"HS code {code} is not present in the HS master.")

    return hs_code.id


def _get_latest_annual_period(
    db,
    *,
    source_id: int,
    reporter_code: int,
    hs_code_id: int,
    trade_flow: str,
):
    return db.scalar(
        select(func.max(TradeData.period_start)).where(
            TradeData.source_id == source_id,
            TradeData.reporter_country_id
            == (
                select(Country.id)
                .where(
                    Country.comtrade_code == reporter_code,
                    Country.active.is_(True),
                )
                .scalar_subquery()
            ),
            TradeData.hs_code_id == hs_code_id,
            TradeData.trade_flow == ("import" if trade_flow == "M" else "export"),
            TradeData.period_type == "annual",
        )
    )


def _resolve_incremental_period(
    db,
    *,
    reporter_code: int,
    hs_code: str,
    flow: str,
    start_period: str | None,
    include_current_year: bool,
) -> str:
    source_id = _get_source_id(db)
    hs_code_id = _get_hs_code_id(db, hs_code)

    latest = _get_latest_annual_period(
        db,
        source_id=source_id,
        reporter_code=reporter_code,
        hs_code_id=hs_code_id,
        trade_flow=flow,
    )

    if latest is None:
        if start_period is None:
            raise RuntimeError(
                "No existing annual data was found for this dataset. "
                "Provide --start-period YYYY for the first incremental run."
            )

        period = str(parse_annual_period(start_period))
    else:
        period = next_annual_period(latest)

    if not include_current_year and is_current_or_future_year(period):
        raise NoEligiblePeriod(
            f"Next period is {period}, which is the current/future year. "
            "Annual data may be incomplete."
        )

    return period


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest UN Comtrade trade data.")

    parser.add_argument(
        "--reporter-code",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--partner-code",
        type=int,
        help=(
            "UN Comtrade partner M49 code. Omit this argument "
            "to ingest all active country partners."
        ),
    )

    parser.add_argument(
        "--period",
        help="Explicit period: YYYY or YYYYMM.",
    )

    parser.add_argument(
        "--incremental",
        action="store_true",
        help=(
            "For annual ingestion, select the next year after "
            "the latest stored year for this reporter/HS/flow dataset."
        ),
    )

    parser.add_argument(
        "--start-period",
        help=(
            "Initial YYYY period for --incremental when no annual " "data exists yet."
        ),
    )

    parser.add_argument(
        "--include-current-year",
        action="store_true",
        help=(
            "Allow --incremental to ingest the current/future annual "
            "period. Use only when partial-year data is intended."
        ),
    )

    parser.add_argument(
        "--flow",
        choices=["M", "X"],
        required=True,
    )

    parser.add_argument(
        "--hs-code",
        action="append",
        dest="hs_codes",
        required=True,
    )

    parser.add_argument(
        "--max-records",
        type=int,
        default=500,
    )

    parser.add_argument(
        "--subscription-key",
        default=os.getenv("COMTRADE_SUBSCRIPTION_KEY"),
    )

    args = parser.parse_args()

    if args.incremental:
        if args.period is not None:
            parser.error("--period and --incremental cannot be used together.")

        if len(args.hs_codes) != 1:
            parser.error("--incremental currently requires exactly one --hs-code.")

    elif args.period is None:
        parser.error("--period is required unless --incremental is specified.")

    db = SessionLocal()

    try:
        period = args.period

        if args.incremental:
            try:
                period = _resolve_incremental_period(
                    db,
                    reporter_code=args.reporter_code,
                    hs_code=args.hs_codes[0],
                    flow=args.flow,
                    start_period=args.start_period,
                    include_current_year=args.include_current_year,
                )
            except NoEligiblePeriod as exc:
                print("Incremental ingestion checked.")
                print(f"Result           : NOTHING TO INGEST")
                print(f"Reason           : {exc}")
                print("Exit status      : 0")
                return

            print(f"Incremental period selected: {period}")

        provider = ComtradeProvider(
            subscription_key=args.subscription_key,
        )

        result = TradeIngestionService(
            db=db,
            provider=provider,
        ).ingest(
            reporter_code=args.reporter_code,
            period=period,
            flow_code=args.flow,
            cmd_codes=args.hs_codes,
            partner_code=args.partner_code,
            max_records=args.max_records,
        )

        scope = (
            "ALL PARTNERS"
            if args.partner_code is None
            else f"PARTNER {args.partner_code}"
        )

        mode = "INCREMENTAL" if args.incremental else "EXPLICIT"

        print("UN Comtrade ingestion completed.")
        print(f"Mode             : {mode}")
        print(f"Scope            : {scope}")
        print(f"Period           : {period}")
        print(f"Ingestion run ID : {result.ingestion_run_id}")
        print(f"Status           : {result.status}")
        print(f"Records received : {result.records_received}")
        print(f"Records inserted : {result.records_inserted}")
        print(f"Records updated  : {result.records_updated}")
        print(f"Records rejected : {result.records_rejected}")
        print(f"Aggregate records: {result.aggregate_records}")
        print("Detail records skipped: " f"{result.detail_records_skipped}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
