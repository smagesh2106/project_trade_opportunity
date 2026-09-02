from app.integrations.trade.comtrade import ComtradeProvider


REPORTER_CODE = 699  # India
PERIOD = "2025"
FLOW_CODE = "M"
HS_CODE = "853710"


def test_all_partner_request():
    provider = ComtradeProvider()

    partner_codes = [
        36,   # Australia
        40,   # Austria
        48,   # Bahrain
        50,   # Bangladesh
        56,   # Belgium
        76,   # Brazil
        100,  # Bulgaria
        124,  # Canada
        156,  # China
        191,  # Croatia
        208,  # Denmark
        276,  # Germany
        356,  # India
        376,  # Israel
        392,  # Japan
        410,  # Korea
        458,  # Malaysia
        554,  # New Zealand
        578,  # Norway
        586,  # Pakistan
        608,  # Philippines
        616,  # Poland
        620,  # Portugal
        682,  # Saudi Arabia
        702,  # Singapore
        710,  # South Africa
        724,  # Spain
        752,  # Sweden
        756,  # Switzerland
        784,  # UAE
        792,  # Turkey
        826,  # United Kingdom
        840,  # United States
        858,  # Uruguay
        862,  # Venezuela
    ]

    records = provider.fetch_all_partner_trade_data(
        reporter_code=REPORTER_CODE,
        period=PERIOD,
        flow_code=FLOW_CODE,
        cmd_codes=[HS_CODE],
        partner_codes=partner_codes,
        partner_batch_size=10,
        max_records=500,
    )

    assert records, (
        "Expected Comtrade to return records for "
        "the explicit partner batches."
    )

    assert len(records) <= len(partner_codes), (
        "Expected no more than one canonical record per "
        "requested partner."
    )

    distinct_partners = {
        record.partner_iso3
        for record in records
        if record.partner_iso3
    }

    assert len(distinct_partners) > 1
    assert len(distinct_partners) == len(records)

    for record in records:
        assert record.reporter_iso3 == "IND"
        assert record.hs_code == HS_CODE
        assert record.period_start.year == 2025
        assert record.trade_flow == "import"
        assert record.partner_code > 0
        assert record.partner_iso3
        assert len(record.partner_iso3) == 3
        assert record.partner_iso3.isalpha()
        assert record.is_country_level_aggregate
        assert record.trade_value_usd is not None

    germany = next(
        (
            record
            for record in records
            if record.partner_iso3 == "DEU"
        ),
        None,
    )

    assert germany is not None
    assert float(germany.trade_value_usd) > 0

    print("PASS batched all-partner request")
    print(f"Partners requested : {len(partner_codes)}")
    print(f"Records returned   : {len(records)}")
    print(f"Distinct partners  : {len(distinct_partners)}")
    print(
        "Germany aggregate  : "
        f"${float(germany.trade_value_usd):,.2f}"
    )


if __name__ == "__main__":
    test_all_partner_request()
    print("\nBatched all-partner Comtrade test passed.")
