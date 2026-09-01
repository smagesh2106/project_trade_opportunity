from app.integrations.trade.comtrade import ComtradeProvider


def test_comtrade_request_validation():
    provider = ComtradeProvider()

    invalid_cases = [
        {
            "reporter_code": 0,
            "period": "2025",
            "flow_code": "M",
            "cmd_codes": ["853710"],
        },
        {
            "reporter_code": 699,
            "period": "2025",
            "flow_code": "BAD",
            "cmd_codes": ["853710"],
        },
        {
            "reporter_code": 699,
            "period": "20XX",
            "flow_code": "M",
            "cmd_codes": ["853710"],
        },
        {"reporter_code": 699, "period": "2025", "flow_code": "M", "cmd_codes": []},
    ]

    for case in invalid_cases:
        try:
            provider.fetch_trade_data(**case)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected validation failure: {case}")


def test_comtrade_flow_is_canonical():
    provider = ComtradeProvider()

    record = provider._parse_record(
        {
            "period": "2025",
            "cmdCode": "853710",
            "reporterCode": 699,
            "reporterISO": "IND",
            "reporterDesc": "India",
            "partnerCode": 276,
            "partnerISO": "DEU",
            "partnerDesc": "Germany",
            "flowCode": "M",
            "primaryValue": 123.45,
        }
    )

    assert record is not None
    assert record.trade_flow == "import"


def test_comtrade_aggregate_flag():
    provider = ComtradeProvider()

    aggregate = provider._parse_record(
        {
            "period": "2025",
            "cmdCode": "853710",
            "reporterCode": 699,
            "reporterISO": "IND",
            "reporterDesc": "India",
            "partnerCode": 276,
            "partnerISO": "DEU",
            "partnerDesc": "Germany",
            "flowCode": "M",
            "primaryValue": 165477057.548,
            "isAggregate": True,
            "partner2Code": 0,
            "customsCode": "C00",
            "motCode": 0,
            "typeCode": "C",
            "classificationCode": "H6",
        }
    )

    detail = provider._parse_record(
        {
            "period": "2025",
            "cmdCode": "853710",
            "reporterCode": 699,
            "reporterISO": "IND",
            "reporterDesc": "India",
            "partnerCode": 276,
            "partnerISO": "DEU",
            "partnerDesc": "Germany",
            "flowCode": "M",
            "primaryValue": 5310.936,
            "isAggregate": False,
            "partner2Code": 20,
            "customsCode": "C00",
            "motCode": 0,
            "typeCode": "C",
            "classificationCode": "H6",
        }
    )

    assert aggregate is not None
    assert detail is not None

    assert aggregate.is_aggregate is True
    assert detail.is_aggregate is False
    assert aggregate.source_record_id != detail.source_record_id


if __name__ == "__main__":
    test_comtrade_request_validation()
    print("PASS request validation")

    test_comtrade_flow_is_canonical()
    print("PASS flow normalization")

    test_comtrade_aggregate_flag()
    print("PASS aggregate/detail detection")

    print("Comtrade provider tests passed.")
