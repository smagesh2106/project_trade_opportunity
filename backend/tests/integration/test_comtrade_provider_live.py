from app.integrations.trade.comtrade import ComtradeProvider


def main():
    provider = ComtradeProvider()

    records = provider.fetch_trade_data(
        reporter_code=699,
        period="2025",
        flow_code="M",
        cmd_codes=["853710"],
        partner_code=276,
        max_records=50,
    )

    print(f"Received {len(records)} live Comtrade records.")

    for record in records[:10]:
        value = (
            f"${record.trade_value_usd:,.2f}"
            if record.trade_value_usd is not None
            else "value=None"
        )
        print(
            f"{record.reporter_iso3} -> {record.partner_iso3} | "
            f"{record.hs_code} | {record.period_start} | "
            f"{record.trade_flow} | {value}"
        )


if __name__ == "__main__":
    main()
