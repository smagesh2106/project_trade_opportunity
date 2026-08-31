#!/usr/bin/env bash

# ============================================================
# Trade Opportunity Explorer
# HTTP/API black-box regression tests
#
# Prerequisites:
#   1. FastAPI backend running on port 8000
#   2. curl
#   3. jq
#
# Start backend:
#   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
#
# Run:
#   chmod +x test_trade_api_curl.sh
#   ./test_trade_api_curl.sh
#
# Override API URL:
#   BASE_URL=http://127.0.0.1:8000 ./test_trade_api_curl.sh
# ============================================================

set -u

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
ENDPOINT="${BASE_URL}/api/v1/trade/analyze"

PASS_COUNT=0
FAIL_COUNT=0
TEST_COUNT=0

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "============================================================"
echo "Trade Opportunity Explorer - HTTP API Test Suite"
echo "============================================================"
echo "Endpoint: $ENDPOINT"
echo

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

run_test() {
    local name="$1"
    local expected_status="$2"
    local body="$3"

    TEST_COUNT=$((TEST_COUNT + 1))

    local response_file="${TMP_DIR}/response_${TEST_COUNT}.txt"
    local status

    status=$(curl -sS \
        -o "$response_file" \
        -w "%{http_code}" \
        -X POST "$ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$body")

    if [ "$status" = "$expected_status" ]; then
        echo "PASS [$TEST_COUNT] $name (HTTP $status)"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "FAIL [$TEST_COUNT] $name"
        echo "      Expected HTTP: $expected_status"
        echo "      Actual HTTP:   $status"
        echo "      Response:"
        sed 's/^/        /' "$response_file"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

run_test_and_check() {
    local name="$1"
    local expected_status="$2"
    local body="$3"
    local check="$4"

    TEST_COUNT=$((TEST_COUNT + 1))

    local response_file="${TMP_DIR}/response_${TEST_COUNT}.json"
    local status

    status=$(curl -sS \
        -o "$response_file" \
        -w "%{http_code}" \
        -X POST "$ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$body")

    if [ "$status" != "$expected_status" ]; then
        echo "FAIL [$TEST_COUNT] $name"
        echo "      Expected HTTP: $expected_status"
        echo "      Actual HTTP:   $status"
        echo "      Response:"
        sed 's/^/        /' "$response_file"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return
    fi

    if jq -e "$check" "$response_file" >/dev/null 2>&1; then
        echo "PASS [$TEST_COUNT] $name (HTTP $status)"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "FAIL [$TEST_COUNT] $name"
        echo "      HTTP status passed: $status"
        echo "      JSON check failed: $check"
        echo "      Response:"
        jq . "$response_file" 2>/dev/null || cat "$response_file"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

# ------------------------------------------------------------
# Prerequisite checks
# ------------------------------------------------------------

if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: curl is required."
    exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "ERROR: jq is required."
    echo "Install with:"
    echo "  sudo apt install jq"
    exit 2
fi

echo "Checking API availability..."

analyze_status=$(curl -sS -o /dev/null -w "%{http_code}" \
    -X POST "$ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{"query":"Find suppliers of electrical panels to India"}' 2>/dev/null || true)

if [ "$analyze_status" != "200" ]; then
    echo "ERROR: $ENDPOINT returned HTTP ${analyze_status}"
    echo "Make sure FastAPI is running and BASE_URL is correct."
    exit 2
else
    echo "Trade analyze endpoint availability: PASS"
    echo
fi

# ============================================================
# POSITIVE TESTS
# ============================================================

echo "============================================================"
echo "POSITIVE TESTS"
echo "============================================================"

run_test_and_check \
    "Supplier search - India" \
    "200" \
    '{"query":"Find suppliers of electrical panels to India"}' \
    '.opportunities | length == 4 and .[0].country_name == "Germany"'

run_test_and_check \
    "Global supplier search" \
    "200" \
    '{"query":"Find suppliers of electrical panels"}' \
    '.opportunities | length == 5 and .[0].country_name == "India"'

run_test_and_check \
    "Global buyer search" \
    "200" \
    '{"query":"Who imports electrical panels?"}' \
    '.opportunities | length >= 1'

run_test_and_check \
    "Buyer search - India" \
    "200" \
    '{"query":"Who imports electrical panels in India?"}' \
    '.opportunities | length >= 1 and .[0].country_name == "India"'

run_test_and_check \
    "Buyers of Indian exports" \
    "200" \
    '{"query":"Who buys electrical panels from India?"}' \
    '.opportunities | length == 4 and .[0].country_name == "Germany"'

run_test_and_check \
    "Import opportunity - India" \
    "200" \
    '{"query":"Which countries should India source electrical panels from?"}' \
    '.opportunities | length == 4 and .[0].country_name == "Germany"'

run_test_and_check \
    "Export opportunity - India" \
    "200" \
    '{"query":"Which countries should India target for exporting electrical panels?"}' \
    '.opportunities | length == 4 and .[0].country_name == "Germany"'

run_test_and_check \
    "Market analysis - India imports" \
    "200" \
    '{"query":"How are electrical panel imports into India trending?"}' \
    'type == "object" and .trade_flow == "import" and .country_name == "India" and (.history | type == "array")'

run_test_and_check \
    "Country comparison - Germany vs UAE" \
    "200" \
    '{"query":"Compare Germany and United Arab Emirates for electrical panels to India"}' \
    '.comparison.country_a_name == "Germany" and .comparison.country_b_name == "United Arab Emirates" and .comparison.trade_value_winner_name == "Germany" and .comparison.market_share_winner_name == "Germany" and .comparison.yoy_growth_winner_name == "United Arab Emirates" and .comparison.opportunity_score_winner_name == "Germany" and .comparison.overall_winner_name == "Germany"'

run_test_and_check \
    "Explicit valid period" \
    "200" \
    '{"query":"Find suppliers of electrical panels to India","period_start":"2025-01-01","period_end":"2025-12-31"}' \
    '.period_start == "2025-01-01" and .period_end == "2025-12-31"'

run_test_and_check \
    "Period - start only" \
    "200" \
    '{"query":"Find suppliers of electrical panels to India","period_start":"2025-01-01"}' \
    '.period_start == "2025-01-01"'

run_test_and_check \
    "Period - end only" \
    "200" \
    '{"query":"Find suppliers of electrical panels to India","period_end":"2025-12-31"}' \
    '.period_end == "2025-12-31"'

# ============================================================
# NEGATIVE TESTS
# ============================================================

echo
echo "============================================================"
echo "NEGATIVE TESTS"
echo "============================================================"

run_test_and_check \
    "Empty query" \
    "400" \
    '{"query":""}' \
    '.detail | type == "string" and length > 0'

run_test_and_check \
    "Whitespace-only query" \
    "400" \
    '{"query":"   "}' \
    '.detail | type == "string" and length > 0'

run_test_and_check \
    "Missing query" \
    "422" \
    '{}' \
    '.detail | type == "array"'

run_test_and_check \
    "Null query" \
    "422" \
    '{"query":null}' \
    '.detail | type == "array"'

run_test_and_check \
    "Numeric query" \
    "422" \
    '{"query":12345}' \
    '.detail | type == "array"'

run_test_and_check \
    "Unknown product" \
    "400" \
    '{"query":"Find suppliers of solar powered bananas"}' \
    '.detail | type == "string" and length > 0'

run_test_and_check \
    "Unsupported supplier location search" \
    "400" \
    '{"query":"Find suppliers of electrical panels in India"}' \
    '.detail | type == "string" and length > 0'

run_test_and_check \
    "Invalid start date" \
    "422" \
    '{"query":"Find suppliers of electrical panels to India","period_start":"not-a-date"}' \
    '.detail | type == "array"'

run_test_and_check \
    "Invalid end date" \
    "422" \
    '{"query":"Find suppliers of electrical panels to India","period_end":"not-a-date"}' \
    '.detail | type == "array"'

run_test_and_check \
    "Start date after end date" \
    "400" \
    '{"query":"Find suppliers of electrical panels to India","period_start":"2025-12-31","period_end":"2025-01-01"}' \
    '.detail | type == "string" and length > 0'

run_test_and_check \
    "Same-country comparison" \
    "400" \
    '{"query":"Compare Germany and Germany for electrical panels"}' \
    '.detail | type == "string" and length > 0'

run_test_and_check \
    "One-country comparison" \
    "400" \
    '{"query":"Compare Germany for electrical panels"}' \
    '.detail | type == "string" and length > 0'

run_test_and_check \
    "Malformed JSON" \
    "422" \
    '{"query":"Find suppliers of electrical panels to India"' \
    '.detail | type == "array"'

# ============================================================
# SUMMARY
# ============================================================

echo
echo "============================================================"
echo "TEST SUMMARY"
echo "============================================================"
echo "Total : $TEST_COUNT"
echo "Passed: $PASS_COUNT"
echo "Failed: $FAIL_COUNT"
echo "============================================================"

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "ALL HTTP API TESTS PASSED"
    exit 0
else
    echo "HTTP API TEST SUITE FAILED"
    exit 1
fi
